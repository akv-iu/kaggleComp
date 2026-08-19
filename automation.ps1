param(
    [switch]$Poll,
    [switch]$ArmPlan,
    [switch]$ConfirmUsageAbove50,
    [string]$ApprovePlan,
    [string]$RejectPlan,
    [string]$SubmitCandidate,
    [switch]$InstallTask,
    [switch]$DryRun,
    [switch]$NoNotify
)

$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtime = Join-Path $workspace ".automation"
$proposalDir = Join-Path $runtime "proposals"
$candidateDir = Join-Path $runtime "candidates"
$python = Join-Path $workspace ".venv\Scripts\python.exe"
$kaggle = Join-Path $workspace ".venv\Scripts\kaggle.exe"
$statusPath = Join-Path $runtime "status.json"
$statePath = Join-Path $runtime "state.json"
$evidencePath = Join-Path $runtime "evidence.json"
$logPath = Join-Path $runtime "automation.log"
$runLog = Join-Path $runtime "run_output.log"
$inFlightPath = Join-Path $runtime "evaluation_in_flight.json"
$evaluatorVersion = "competition-v2"

New-Item -ItemType Directory -Path $runtime, $proposalDir, $candidateDir -Force | Out-Null
Set-Location -LiteralPath $workspace

function Native([scriptblock]$Block) {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { & $Block } finally { $ErrorActionPreference = $previous }
}

function Write-Log([string]$Message) {
    Add-Content -LiteralPath $logPath -Encoding utf8 -Value ("{0} {1}" -f (Get-Date -Format o), $Message)
}

function Write-Utf8([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
}

function Write-Json([string]$Path, $Value) {
    Write-Utf8 $Path ($Value | ConvertTo-Json -Depth 20 -Compress)
}

function Read-Json([string]$Path, $Default) {
    if (-not (Test-Path -LiteralPath $Path)) { return $Default }
    return Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
}

function Put($Object, [string]$Name, $Value) {
    if ($Object -is [hashtable]) { $Object[$Name] = $Value; return }
    if ($null -eq $Object.PSObject.Properties[$Name]) {
        $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
    } else { $Object.$Name = $Value }
}

function File-Hash([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Send-Notification([string]$Title, [string]$Body) {
    if ($NoNotify) { return }
    try {
        [void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]
        [void][Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime]
        [void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
        $titleText = [Security.SecurityElement]::Escape($Title)
        $bodyText = [Security.SecurityElement]::Escape($Body)
        $xml = [Windows.Data.Xml.Dom.XmlDocument]::new()
        $xml.LoadXml("<toast><visual><binding template='ToastGeneric'><text>$titleText</text><text>$bodyText</text></binding></visual></toast>")
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        $app = Get-StartApps | Where-Object { $_.Name -eq "Windows PowerShell" } | Select-Object -First 1
        $appId = if ($app) { $app.AppID } else { "Microsoft.Windows.PowerShell" }
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)
    } catch { Write-Log "Notification failed: $($_.Exception.Message)" }
}

function Publish-Status([string]$StateName, [string]$Message, [string]$Title = "Kaggriculture loop") {
    $status = Read-Json $statusPath ([pscustomobject]@{})
    Put $status "state" $StateName
    Put $status "message" $Message
    Put $status "updatedAt" (Get-Date -Format o)
    Write-Json $statusPath $status
    Write-Log "$StateName`: $Message"
    Send-Notification $Title $Message
    return $status
}

function Assert-Id([string]$Id) {
    if ($Id -notmatch '^[A-Za-z0-9._-]+$') { throw "Invalid plan id: $Id" }
}

function Proposal-Path([string]$Id, [string]$Extension = "json") {
    Assert-Id $Id
    return Join-Path $proposalDir "$Id.$Extension"
}

function Validate-Patch([string]$Patch) {
    if (-not $Patch.Trim()) { throw "Proposal contains no patch." }
    if ($Patch -match '(?m)^GIT binary patch|^rename (?:from|to)|^deleted file mode|^new file mode') {
        throw "Proposal patch may only modify existing main.py text."
    }
    $files = [regex]::Matches($Patch, '(?m)^diff --git a/(.+) b/(.+)$')
    if ($files.Count -gt 0) {
        if ($files.Count -ne 1 -or $files[0].Groups[1].Value -ne "main.py" -or $files[0].Groups[2].Value -ne "main.py") {
            throw "Proposal patch may only modify main.py."
        }
    }
    if ($Patch -notmatch '(?m)^--- a/main\.py\s*$' -or $Patch -notmatch '(?m)^\+\+\+ b/main\.py\s*$') {
        throw "Proposal must be a git-compatible unified diff for main.py."
    }
}

function Save-Attempt($Proposal, [string]$Verdict, $Metrics = $null) {
    $recordPath = Join-Path $runtime "attempt-$($Proposal.id).json"
    $record = [ordered]@{
        id = $Proposal.id
        createdAt = $Proposal.createdAt
        hypothesis = $Proposal.hypothesis
        changeFingerprint = $Proposal.changeFingerprint
        baselineSubmission = $Proposal.baselineSubmission
        evaluatorVersion = $evaluatorVersion
        evidenceIds = @($Proposal.evidenceIds)
        metrics = $Metrics
        verdict = $Verdict
        retryCondition = $Proposal.retryCondition
        history = @($Proposal.history)
    }
    Write-Json $recordPath $record
    Native { & $python loop.py attempt-upsert $recordPath *>> $runLog }
    if ($LASTEXITCODE -ne 0) { throw "Could not update attempts.jsonl." }
}

function Add-ProposalHistory($Proposal, [string]$StateName, [string]$Detail = "") {
    $history = @($Proposal.history)
    $history += [pscustomobject][ordered]@{
        state = $StateName
        at = (Get-Date -Format o)
        detail = $Detail
    }
    Put $Proposal "history" $history
}

function Clear-ActivePlan($Status) {
    Put $Status "currentProposalId" $null
    Put $Status "currentCandidateId" $null
    Put $Status "queuedEvidenceCount" 0
}

function Restore-Evaluation($Flight) {
    if ($null -ne $Flight -and (Test-Path -LiteralPath $Flight.baselinePath)) {
        Copy-Item -LiteralPath $Flight.baselinePath -Destination (Join-Path $workspace "main.py") -Force
    }
    if (Test-Path -LiteralPath $inFlightPath) { Remove-Item -LiteralPath $inFlightPath -Force }
}

function Recover-InterruptedEvaluation {
    if (-not (Test-Path -LiteralPath $inFlightPath)) { return }
    $flight = Read-Json $inFlightPath $null
    Restore-Evaluation $flight
    if ($flight.id) {
        $proposal = Read-Json (Proposal-Path $flight.id) $null
        if ($proposal) {
            Put $proposal "status" "rejected"
            Put $proposal "verdict" "rejected"
            Add-ProposalHistory $proposal "rejected" "Interrupted evaluation was restored on the next run."
            Write-Json (Proposal-Path $flight.id) $proposal
            Save-Attempt $proposal "rejected" $null
        }
    }
    $status = Publish-Status "REJECTED" "Interrupted evaluation was rolled back to its recorded baseline."
    Clear-ActivePlan $status
    Write-Json $statusPath $status
}

function Recover-InterruptedPlanning {
    $status = Read-Json $statusPath ([pscustomobject]@{ state = "IDLE" })
    if ($status.state -ne "PLAN_RUNNING") { return }
    $status = Publish-Status "CAP_REACHED" "An interrupted planning run was closed without changing code."
    Clear-ActivePlan $status
    Write-Json $statusPath $status
}

function Cached-Or-Run([string]$CachePath, [scriptblock]$Command) {
    if ($DryRun) {
        if (-not (Test-Path -LiteralPath $CachePath)) { throw "Dry-run cache missing: $CachePath" }
        return Get-Content -Raw -LiteralPath $CachePath
    }
    $text = Native { & $Command | Out-String }
    if ($LASTEXITCODE -ne 0) { throw "External command failed: $text" }
    Write-Utf8 $CachePath $text
    return $text
}

function Invoke-Poll {
    $submissionsPath = Join-Path $runtime "submissions.txt"
    $submissionsText = Cached-Or-Run $submissionsPath { & $kaggle competitions submissions kaggriculture -v 2>&1 }
    $submissions = @($submissionsText | ConvertFrom-Csv | Where-Object { $_.ref -match '^\d+$' })
    if (-not $submissions) { throw "Could not identify the latest submission." }
    $submissionId = [string]$submissions[0].ref

    $state = Read-Json $statePath ([pscustomobject]@{ submissionLimit = 5 })
    Put $state "lastSubmissionId" $submissionId
    Put $state "lastPollAt" (Get-Date -Format o)
    $todayUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
    Put $state "submissionDayUtc" $todayUtc
    Put $state "submissionsUsed" @($submissions | Where-Object { $_.date -like "$todayUtc*" }).Count
    $scored = @($submissions | Where-Object { $_.publicScore })
    if ($scored) { Put $state "lastScore" ([double]$scored[0].publicScore) }

    $episodesPath = Join-Path $runtime "episodes.csv"
    $episodesText = Cached-Or-Run $episodesPath { & $kaggle competitions episodes $submissionId -v 2>&1 }
    $episodes = @($episodesText | ConvertFrom-Csv | Where-Object { $_.id -match '^\d+$' })
    $seen = @{}
    if (Test-Path -LiteralPath (Join-Path $workspace "replay_index.json")) {
        foreach ($row in (Get-Content -Raw replay_index.json | ConvertFrom-Json)) { $seen[[string]$row.episode] = $true }
    }
    $newIds = [Collections.Generic.List[string]]::new()
    if (-not $DryRun) {
        $replayDir = Join-Path $workspace "replays\submission-$submissionId"
        New-Item -ItemType Directory -Path $replayDir -Force | Out-Null
        foreach ($episode in $episodes) {
            if ($seen.ContainsKey([string]$episode.id)) { continue }
            $download = Native { & $kaggle competitions replay $episode.id -p $replayDir 2>&1 | Out-String }
            if ($LASTEXITCODE -eq 0) {
                $newIds.Add([string]$episode.id)
                $seen[[string]$episode.id] = $true
            }
            else { Write-Log "Replay $($episode.id) failed: $download" }
        }
    }

    Native { & $python loop.py index *>> $runLog }
    if ($LASTEXITCODE -ne 0) { throw "Replay indexing failed." }
    Native { & $python loop.py evidence $submissionId $evidencePath ($newIds -join ',') *>> $runLog }
    if ($LASTEXITCODE -ne 0) { throw "Evidence generation failed." }
    if ($DryRun) { Native { & $python loop.py prune --dry-run *>> $runLog } }
    else { Native { & $python loop.py prune *>> $runLog } }

    $evidence = Read-Json $evidencePath $null
    Put $evidence "scoreHistory" @($submissions | Select-Object -First 5 ref, publicScore)
    Write-Json $evidencePath $evidence
    if ((Get-Item -LiteralPath $evidencePath).Length -gt 20000) { throw "Evidence packet exceeded 20KB after score history." }
    Put $state "lastEvidenceFingerprint" $evidence.evidenceFingerprint
    Write-Json $statePath $state

    $status = Read-Json $statusPath ([pscustomobject]@{ state = "IDLE" })
    Put $status "lastPollAt" (Get-Date -Format o)
    Put $status "lastEvidenceFingerprint" $evidence.evidenceFingerprint
    Put $status "latestSubmissionId" $submissionId
    Put $status "newReplayCount" $newIds.Count
    $busy = @("AWAITING_REVIEW", "EVALUATING", "READY_TO_SUBMIT", "SUBMIT_FAILED") -contains $status.state
    if ($busy) {
        $queued = 0
        if ($status.currentProposalId) {
            $proposal = Read-Json (Proposal-Path $status.currentProposalId) $null
            if ($proposal) { $queued = [Math]::Max(0, [int]$evidence.currentRecord.games - [int]$proposal.evidenceGameCount) }
        }
        Put $status "queuedEvidenceCount" $queued
        Write-Json $statusPath $status
        if ($status.state -in @("READY_TO_SUBMIT", "SUBMIT_FAILED")) {
            $pendingMessage = "Candidate $($status.currentCandidateId) awaits submission approval; $queued newer games queued."
        } elseif ($status.state -eq "EVALUATING") {
            $pendingMessage = "Plan $($status.currentProposalId) is evaluating; $queued newer games queued."
        } else {
            $pendingMessage = "Plan $($status.currentProposalId) awaits review; $queued newer games queued."
        }
        Send-Notification "Kaggriculture loop" $pendingMessage
        Write-Log "Poll complete; $pendingMessage"
    } elseif ([int]$evidence.currentRecord.games -ge 25 -and
              $evidence.evidenceFingerprint -ne $status.lastPlannedFingerprint) {
        Put $status "state" "EVIDENCE_READY"
        Put $status "message" "New evidence ready - check /usage, then arm planning."
        Put $status "updatedAt" (Get-Date -Format o)
        Write-Json $statusPath $status
        Write-Log "EVIDENCE_READY: $($status.message)"
        Send-Notification "Kaggriculture evidence ready" $status.message
    } else {
        Put $status "state" "IDLE"
        Put $status "message" "Poll complete - nothing actionable."
        Put $status "updatedAt" (Get-Date -Format o)
        Write-Json $statusPath $status
        Write-Log "IDLE: $($status.message)"
        Send-Notification "Kaggriculture loop" $status.message
    }
}

function Proposal-Data($Envelope) {
    if ($null -ne $Envelope.structured_output) { return $Envelope.structured_output }
    if ($Envelope.result -is [string]) {
        try { return $Envelope.result | ConvertFrom-Json } catch { throw "Claude returned no structured proposal." }
    }
    if ($null -ne $Envelope.status) { return $Envelope }
    throw "Claude returned no structured proposal."
}

function Write-ProposalMarkdown($Proposal) {
    $evidenceLines = @($Proposal.evidence | ForEach-Object { "- $_" }) -join "`n"
    $text = @"
# $($Proposal.title)

**Plan ID:** `$($Proposal.id)`
**Status:** $($Proposal.status)
**Baseline:** submission $($Proposal.baselineSubmission), hash `$($Proposal.baselineHash)`

## Hypothesis

$($Proposal.hypothesis)

## Evidence

$evidenceLines

## Exact patch

~~~diff
$($Proposal.patch)
~~~

## Retry condition

$($Proposal.retryCondition)

Approve implementation and testing with:

~~~powershell
.\automation.ps1 -ApprovePlan $($Proposal.id)
~~~
"@
    Write-Utf8 (Proposal-Path $Proposal.id "md") $text
}

function Invoke-ArmPlan {
    if (-not $ConfirmUsageAbove50) { throw "Check /usage first, then pass -ConfirmUsageAbove50." }
    $status = Read-Json $statusPath ([pscustomobject]@{ state = "IDLE" })
    if ($status.state -ne "EVIDENCE_READY") { throw "No unconsumed evidence is ready (state=$($status.state))." }
    $evidence = Read-Json $evidencePath $null
    if (-not $evidence) { throw "Evidence packet is missing." }
    Put $status "lastPlannedFingerprint" $evidence.evidenceFingerprint
    Write-Json $statusPath $status
    Publish-Status "PLAN_RUNNING" "One capped Sonnet planning run is in progress." | Out-Null

    $memory = Get-Content -Raw -LiteralPath (Join-Path $workspace "memory.md")
    if ([Text.Encoding]::UTF8.GetByteCount($memory) -gt 12000) { throw "memory.md exceeds the 12KB planning limit." }
    $input = @"
$(Get-Content -Raw -LiteralPath (Join-Path $workspace "automation_prompt.md"))

## Evidence packet
~~~json
$(Get-Content -Raw -LiteralPath $evidencePath)
~~~

## Curated strategy memory
$memory

## Current main.py
~~~python
$(Get-Content -Raw -LiteralPath (Join-Path $workspace "main.py"))
~~~
"@
    $inputPath = Join-Path $runtime "plan_input.md"
    Write-Utf8 $inputPath $input
    if ([Text.Encoding]::UTF8.GetByteCount($input) -gt 80000) { throw "Planner input exceeds the 80KB (~20K token) limit." }

    $schema = '{"type":"object","properties":{"status":{"type":"string","enum":["proposal","wait"]},"title":{"type":"string"},"hypothesis":{"type":"string"},"evidence":{"type":"array","items":{"type":"string"}},"patch":{"type":"string"},"message":{"type":"string"},"retryCondition":{"type":"string"}},"required":["status","title","hypothesis","evidence","patch","message","retryCondition"],"additionalProperties":false}'
    $reply = Native {
        Get-Content -Raw -LiteralPath $inputPath | & claude -p --model sonnet --effort medium `
            --safe-mode --no-session-persistence --permission-mode plan --tools= `
            --output-format json --json-schema $schema `
            2>&1 | Out-String
    }
    $exitCode = $LASTEXITCODE
    Write-Utf8 (Join-Path $runtime "last_plan_result.json") $reply
    if ($exitCode -ne 0) {
        Publish-Status "CAP_REACHED" "Planning stopped or failed before producing a valid plan." | Out-Null
        return
    }
    try { $envelope = $reply | ConvertFrom-Json; $data = Proposal-Data $envelope }
    catch { Publish-Status "CAP_REACHED" "Planning returned invalid structured output; code was untouched." | Out-Null; return }
    if ($null -ne $envelope.num_turns -and [int]$envelope.num_turns -gt 6) {
        Publish-Status "CAP_REACHED" "Planning exceeded the six-turn cap; code was untouched." | Out-Null
        return
    }

    $id = "plan-{0}-{1}" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $evidence.evidenceFingerprint.Substring(0, 8)
    $patchPath = Proposal-Path $id "patch"
    if ($data.status -eq "proposal") {
        $data.patch = ([string]$data.patch).Replace("`r`n", "`n")
        try { Validate-Patch $data.patch } catch {
            Publish-Status "CAP_REACHED" "Plan patch was invalid: $($_.Exception.Message)" | Out-Null
            return
        }
        Write-Utf8 $patchPath $data.patch
        $changeFingerprint = File-Hash $patchPath
    } else { $changeFingerprint = "wait-$($evidence.evidenceFingerprint.Substring(0, 16))" }

    $proposal = [pscustomobject][ordered]@{
        id = $id; createdAt = (Get-Date -Format o); status = $data.status
        title = $data.title; hypothesis = $data.hypothesis; evidence = @($data.evidence)
        patch = $data.patch; patchPath = $patchPath; message = $data.message
        retryCondition = $data.retryCondition; changeFingerprint = $changeFingerprint
        baselineHash = File-Hash (Join-Path $workspace "main.py")
        baselineSubmission = [string]$evidence.submissionId
        evidenceFingerprint = $evidence.evidenceFingerprint
        evidenceIds = @($evidence.selectedEpisodeIds)
        evidenceGameCount = [int]$evidence.currentRecord.games
        usage = $envelope.usage; turns = $envelope.num_turns
        verdict = if ($data.status -eq "proposal") { "queued" } else { "wait" }
        history = @()
    }
    Add-ProposalHistory $proposal $proposal.verdict $data.message
    Write-Json (Proposal-Path $id) $proposal
    Write-ProposalMarkdown $proposal
    Save-Attempt $proposal $proposal.verdict $null
    $status = Read-Json $statusPath ([pscustomobject]@{})
    Put $status "lastPlannedFingerprint" $evidence.evidenceFingerprint
    Put $status "currentProposalId" $id
    if ($data.status -eq "wait") {
        Clear-ActivePlan $status
        Put $status "state" "REJECTED"; Put $status "message" "Plan $id concluded that more evidence is needed."
        Put $status "updatedAt" (Get-Date -Format o)
        Write-Json $statusPath $status
        Write-Log "REJECTED: $($status.message)"
        Send-Notification "Kaggriculture plan complete" $status.message
    } else {
        Put $status "state" "AWAITING_REVIEW"; Put $status "message" "Strategy plan $id is ready for review."
        Put $status "updatedAt" (Get-Date -Format o)
        Write-Json $statusPath $status
        Write-Log "AWAITING_REVIEW: $($status.message)"
        Send-Notification "Kaggriculture plan ready" "$($status.message) Saved to $((Proposal-Path $id 'md'))."
    }
}

function Evaluate-Json([string]$Baseline, [int]$Count, [int]$Start, [string]$Output) {
    $raw = Native { & $python verify.py $Baseline $Count $Start 2>$null | Out-String }
    if ($LASTEXITCODE -ne 0) { throw "verify.py failed." }
    Write-Utf8 $Output $raw
    return $raw | ConvertFrom-Json
}

function Reject-Evaluation($Proposal, $Flight, [string]$Reason, $Metrics = $null) {
    Restore-Evaluation $Flight
    Put $Proposal "status" "rejected"
    Put $Proposal "verdict" "rejected"
    Add-ProposalHistory $Proposal "tested" $Reason
    Add-ProposalHistory $Proposal "rejected" $Reason
    Put $Proposal "rejectionReason" $Reason
    if ($Metrics) { Put $Proposal "metrics" $Metrics }
    Write-Json (Proposal-Path $Proposal.id) $Proposal
    Save-Attempt $Proposal "rejected" $Metrics
    $status = Publish-Status "REJECTED" "Plan $($Proposal.id) was rolled back: $Reason"
    Clear-ActivePlan $status
    Write-Json $statusPath $status
}

function Invoke-Approve([string]$Id) {
    $status = Read-Json $statusPath ([pscustomobject]@{ state = "IDLE" })
    if ($status.state -ne "AWAITING_REVIEW" -or $status.currentProposalId -ne $Id) {
        throw "Plan $Id is not the currently reviewable plan."
    }
    $proposal = Read-Json (Proposal-Path $Id) $null
    if (-not $proposal -or $proposal.status -ne "proposal") { throw "Plan $Id is not awaiting approval." }
    if ((File-Hash (Join-Path $workspace "main.py")) -ne $proposal.baselineHash) {
        throw "main.py changed after the plan was created; refusing a stale patch."
    }
    Validate-Patch (Get-Content -Raw -LiteralPath $proposal.patchPath)
    $dir = Join-Path $candidateDir $Id
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    $baselinePath = Join-Path $dir "baseline_main.py"
    Copy-Item -LiteralPath (Join-Path $workspace "main.py") -Destination $baselinePath -Force
    $flight = [pscustomobject]@{ id = $Id; baselinePath = $baselinePath; baselineHash = $proposal.baselineHash }
    Write-Json $inFlightPath $flight
    Put $proposal "status" "evaluating"
    Put $proposal "verdict" "approved"
    Add-ProposalHistory $proposal "approved" "User approved exact patch and local evaluation."
    Write-Json (Proposal-Path $Id) $proposal
    Save-Attempt $proposal "approved" $null
    Publish-Status "EVALUATING" "Applying and testing plan $Id." | Out-Null
    try {
        Native { & git apply --check --whitespace=nowarn $proposal.patchPath *>> $runLog }
        if ($LASTEXITCODE -ne 0) { throw "Patch no longer applies cleanly." }
        Native { & git apply --whitespace=nowarn $proposal.patchPath *>> $runLog }
        if ($LASTEXITCODE -ne 0) { throw "Patch application failed." }
        Native { & $python -m py_compile main.py test_agent.py verify.py loop.py *>> $runLog }
        if ($LASTEXITCODE -ne 0) { throw "py_compile failed." }
        Native { & $python test_agent.py *>> $runLog }
        if ($LASTEXITCODE -ne 0) { throw "test_agent.py failed." }

        $smoke = Evaluate-Json $baselinePath 4 16 (Join-Path $dir "smoke.json")
        if (-not $smoke.summary.allDone -or [double]$smoke.summary.mirrorDelta -lt -1000 -or
            [double]$smoke.summary.headToHeadMean -lt -1000) {
            Reject-Evaluation $proposal $flight "smoke gate failed" $smoke.summary
            return
        }
        $final = Evaluate-Json $baselinePath 12 0 (Join-Path $dir "final.json")
        $passed = $final.summary.allDone -and [double]$final.summary.mirrorDelta -ge 1000 -and
                  [double]$final.summary.mirrorMedianSeedDelta -gt 0 -and
                  [double]$final.summary.headToHeadMean -ge -500
        if (-not $passed) {
            Reject-Evaluation $proposal $flight "final competition gate failed" $final.summary
            return
        }
        if (Test-Path -LiteralPath $inFlightPath) { Remove-Item -LiteralPath $inFlightPath -Force }
        Put $proposal "status" "ready"
        Put $proposal "verdict" "ready"
        Add-ProposalHistory $proposal "tested" "Smoke and final competition gates passed."
        Add-ProposalHistory $proposal "ready" "Waiting for separate Kaggle submission approval."
        Put $proposal "candidateHash" (File-Hash (Join-Path $workspace "main.py"))
        Put $proposal "metrics" $final.summary
        Write-Json (Proposal-Path $Id) $proposal
        Save-Attempt $proposal "ready" $final.summary
        $status = Read-Json $statusPath ([pscustomobject]@{})
        Put $status "currentCandidateId" $Id
        Put $status "currentProposalId" $Id
        Write-Json $statusPath $status
        Publish-Status "READY_TO_SUBMIT" "Plan $Id passed; Kaggle submission still requires separate approval." "Kaggriculture candidate ready" | Out-Null
    } catch {
        Reject-Evaluation $proposal $flight $_.Exception.Message $null
    }
}

function Invoke-Reject([string]$Id) {
    $status = Read-Json $statusPath ([pscustomobject]@{ state = "IDLE" })
    $activeId = if ($status.state -in @("READY_TO_SUBMIT", "SUBMIT_FAILED")) {
        $status.currentCandidateId
    } else { $status.currentProposalId }
    if ($status.state -notin @("AWAITING_REVIEW", "READY_TO_SUBMIT", "SUBMIT_FAILED") -or $activeId -ne $Id) {
        throw "Plan $Id is not the current unresolved plan or candidate."
    }
    $proposal = Read-Json (Proposal-Path $Id) $null
    if (-not $proposal) { throw "Plan $Id does not exist." }
    if ($proposal.status -eq "ready") {
        if ((File-Hash (Join-Path $workspace "main.py")) -ne $proposal.candidateHash) {
            throw "main.py no longer matches the ready candidate; refusing to overwrite it."
        }
        $baseline = Join-Path (Join-Path $candidateDir $Id) "baseline_main.py"
        Copy-Item -LiteralPath $baseline -Destination (Join-Path $workspace "main.py") -Force
    } elseif ($proposal.status -ne "proposal") { throw "Plan $Id is not rejectable (status=$($proposal.status))." }
    Put $proposal "status" "rejected_by_user"; Put $proposal "verdict" "rejected_by_user"
    Add-ProposalHistory $proposal "rejected_by_user" "User rejected the unresolved plan or candidate."
    Write-Json (Proposal-Path $Id) $proposal
    Save-Attempt $proposal "rejected_by_user" $proposal.metrics
    $status = Publish-Status "REJECTED" "Plan $Id was rejected; future evidence may now be planned."
    Clear-ActivePlan $status
    Write-Json $statusPath $status
}

function Query-Submissions {
    $text = Native { & $kaggle competitions submissions kaggriculture -v 2>&1 | Out-String }
    if ($LASTEXITCODE -ne 0) { throw "Kaggle submissions query failed: $text" }
    return @($text | ConvertFrom-Csv | Where-Object { $_.ref -match '^\d+$' })
}

function Invoke-Submit([string]$Id) {
    $status = Read-Json $statusPath ([pscustomobject]@{ state = "IDLE" })
    if ($status.state -notin @("READY_TO_SUBMIT", "SUBMIT_FAILED") -or $status.currentCandidateId -ne $Id) {
        throw "Candidate $Id is not awaiting separate submission approval."
    }
    $proposal = Read-Json (Proposal-Path $Id) $null
    if (-not $proposal -or $proposal.status -ne "ready") { throw "Candidate $Id is not ready to submit." }
    if ((File-Hash (Join-Path $workspace "main.py")) -ne $proposal.candidateHash) {
        throw "main.py no longer matches candidate $Id."
    }
    if ($DryRun) { Publish-Status "READY_TO_SUBMIT" "Dry run: candidate $Id was not submitted." | Out-Null; return }
    $before = Query-Submissions
    $today = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
    if (@($before | Where-Object { $_.date -like "$today*" }).Count -ge 5) { throw "Daily Kaggle submission budget is exhausted." }
    $message = [string]$proposal.message
    if ($message.Length -gt 200) { $message = $message.Substring(0, 200) }
    $reply = Native { & $kaggle competitions submit kaggriculture -f main.py -m $message 2>&1 | Out-String }
    if ($LASTEXITCODE -ne 0 -or $reply -notmatch "Successfully submitted") {
        Publish-Status "SUBMIT_FAILED" "Kaggle rejected candidate $Id; the local candidate was retained." | Out-Null
        return
    }
    $beforeIds = @{}; foreach ($row in $before) { $beforeIds[[string]$row.ref] = $true }
    $observed = $null
    for ($attempt = 0; $attempt -lt 3 -and -not $observed; $attempt++) {
        if ($attempt -gt 0) { Start-Sleep -Seconds 5 }
        $after = Query-Submissions
        $observed = $after | Where-Object { -not $beforeIds.ContainsKey([string]$_.ref) } | Select-Object -First 1
    }
    if (-not $observed) {
        Publish-Status "SUBMIT_FAILED" "Upload reported success but no new submission ID was observed; candidate retained." | Out-Null
        return
    }
    $state = Read-Json $statePath ([pscustomobject]@{})
    Put $state "lastSubmissionId" ([string]$observed.ref)
    Put $state "lastSubmittedAt" (Get-Date -Format o)
    Put $state "lastMessage" $message
    Put $state "lastCandidateHash" $proposal.candidateHash
    Write-Json $statePath $state
    Put $proposal "status" "submitted"; Put $proposal "verdict" "submitted"
    Add-ProposalHistory $proposal "submitted" "Observed Kaggle submission $($observed.ref)."
    Put $proposal "submissionId" ([string]$observed.ref); Put $proposal "submittedAt" (Get-Date -Format o)
    Write-Json (Proposal-Path $Id) $proposal
    Save-Attempt $proposal "submitted" $proposal.metrics
    $status = Publish-Status "SUBMITTED" "Candidate $Id was confirmed as Kaggle submission $($observed.ref)." "Kaggriculture submitted"
    Clear-ActivePlan $status
    Write-Json $statusPath $status
}

function Invoke-InstallTask {
    $scriptPath = (Resolve-Path -LiteralPath (Join-Path $workspace "automation.ps1")).Path
    $matches = @()
    try {
        $matches = @(Get-ScheduledTask | Where-Object {
            @($_.Actions | Where-Object { ($_.Execute + ' ' + $_.Arguments) -like "*$scriptPath*" }).Count -gt 0
        })
    } catch { Write-Log "Could not enumerate all scheduled tasks: $($_.Exception.Message)" }
    if ($matches.Count -gt 1) { throw "Multiple scheduled tasks already target automation.ps1; refusing to create another." }
    $taskName = if ($matches.Count -eq 1) { $matches[0].TaskName } else { "Kaggriculture Replay Optimizer" }
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Poll"
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Hours 4) -RepetitionDuration (New-TimeSpan -Days 3650)
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -StartWhenAvailable -Hidden
    $principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    Publish-Status "IDLE" "Scheduled task '$taskName' now polls every four hours." | Out-Null
}

$modeCount = @($Poll.IsPresent, $ArmPlan.IsPresent, -not [string]::IsNullOrWhiteSpace($ApprovePlan),
               -not [string]::IsNullOrWhiteSpace($RejectPlan), -not [string]::IsNullOrWhiteSpace($SubmitCandidate),
               $InstallTask.IsPresent) | Where-Object { $_ }
if ($modeCount.Count -eq 0) { $Poll = $true }
elseif ($modeCount.Count -gt 1) { throw "Choose exactly one mode." }

$mutex = [Threading.Mutex]::new($false, "Local\KaggricultureEvidenceLoop")
try { $held = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $held = $true }
if (-not $held) { exit 0 }
try {
    Recover-InterruptedEvaluation
    Recover-InterruptedPlanning
    if ($Poll) { Invoke-Poll }
    elseif ($ArmPlan) { Invoke-ArmPlan }
    elseif ($ApprovePlan) { Invoke-Approve $ApprovePlan }
    elseif ($RejectPlan) { Invoke-Reject $RejectPlan }
    elseif ($SubmitCandidate) { Invoke-Submit $SubmitCandidate }
    elseif ($InstallTask) { Invoke-InstallTask }
} catch {
    $failedStatus = Read-Json $statusPath ([pscustomobject]@{})
    if ($failedStatus.state -eq "PLAN_RUNNING") {
        Publish-Status "CAP_REACHED" "Planning failed before producing a valid plan; code was untouched." | Out-Null
    }
    Write-Log "ERROR: $($_.Exception.Message)"
    Send-Notification "Kaggriculture loop error" $_.Exception.Message
    throw
} finally {
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
