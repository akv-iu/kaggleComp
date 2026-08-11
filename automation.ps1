param([switch]$DryRun)

$ErrorActionPreference = "Stop"

$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtime = Join-Path $workspace ".automation"
$kaggle = Join-Path $workspace ".venv\Scripts\kaggle.exe"
$python = Join-Path $workspace ".venv\Scripts\python.exe"
$promptPath = Join-Path $workspace "automation_prompt.md"
$statePath = Join-Path $runtime "state.json"
$logPath = Join-Path $runtime "automation.log"
# `*>>` writes UTF-16 while Add-Content writes UTF-8; mixing them in one file makes
# it unreadable, so raw command transcripts get their own.
$runLog = Join-Path $runtime "run_output.log"
$requestPath = Join-Path $runtime "submit_request.json"
$mutex = [Threading.Mutex]::new($false, "Local\KaggricultureReplayOptimizer")

# A run that crashed while holding the mutex leaves it abandoned, and WaitOne then
# throws instead of returning false.
try { $held = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $held = $true }
if (-not $held) { exit 0 }

function Write-Log([string]$message) {
    $line = "{0} {1}" -f (Get-Date -Format o), $message
    Add-Content -LiteralPath $logPath -Value $line -Encoding utf8
}

# kaggle and kaggle_environments both write to stderr in normal operation (progress
# bars, OpenSpiel "unknown game" warnings). Under $ErrorActionPreference=Stop a
# single stderr line -- even a blank one -- is a terminating error that kills the run
# before its exit code is ever checked, so every external command goes through here
# and is judged by $LASTEXITCODE instead.
function Native([scriptblock]$block) {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { & $block } finally { $ErrorActionPreference = $previous }
}

function Save-Work([string]$message) {
    Native {
        & git add -- main.py test_agent.py verify.py memory.md decision.md `
            automation.ps1 automation_prompt.md *>> $runLog
        & git diff --cached --quiet
        if ($LASTEXITCODE -eq 0) { return }
        & git commit -q -m $message *>> $runLog
        & git -c credential.interactive=false push -q origin HEAD *>> $runLog
        if ($LASTEXITCODE -ne 0) { Write-Log "git push failed; commit kept locally." }
    }
}

# Codex edits main.py in place, so a rejected experiment must be rolled back or it
# silently becomes the next run's baseline. The ledgers keep their record of the
# rejected attempt on purpose.
function Reject([string]$reason) {
    Write-Log "$reason Improvement remains active."
    Copy-Item -LiteralPath (Join-Path $runtime "baseline_main.py") -Destination (Join-Path $workspace "main.py") -Force
    Copy-Item -LiteralPath (Join-Path $runtime "baseline_test_agent.py") -Destination (Join-Path $workspace "test_agent.py") -Force
    exit 0
}

try {
    Set-Location -LiteralPath $workspace
    New-Item -ItemType Directory -Path $runtime -Force | Out-Null

    if (-not (Test-Path -LiteralPath $statePath)) {
        @{ submissionsUsed = 1; submissionLimit = 5; lastSubmissionId = "55413328"; needsImprovement = $true } |
            ConvertTo-Json | Set-Content -LiteralPath $statePath
    }
    $state = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
    if ($null -eq $state.PSObject.Properties["needsImprovement"]) {
        $state | Add-Member -NotePropertyName needsImprovement -NotePropertyValue $true
    }

    $submissionsCsv = Native { & $kaggle competitions submissions kaggriculture -v 2>&1 | Out-String }
    if ($LASTEXITCODE -ne 0) { throw "Kaggle submissions query failed: $submissionsCsv" }
    Set-Content -LiteralPath (Join-Path $runtime "submissions.txt") -Value $submissionsCsv
    $submissions = @($submissionsCsv | ConvertFrom-Csv | Where-Object { $_.ref -match '^\d+$' })
    if (-not $submissions) { throw "Could not identify latest submission." }
    $submissionId = $submissions[0].ref

    # Public rating is the leaderboard signal. Log its direction every run so a change
    # that won locally but scored worse publicly is visible, and hand the history to
    # Codex so it can weigh what public play actually rewarded.
    $scoreHistory = @($submissions | Select-Object ref, description, publicScore)
    $scored = @($scoreHistory | Where-Object { $_.publicScore })
    if ($scored) {
        $latestScore = [double]$scored[0].publicScore
        $trend = ($scored | Select-Object -First 5 | ForEach-Object { $_.publicScore }) -join " <- "
        $delta = if ($scored.Count -gt 1) { $latestScore - [double]$scored[1].publicScore } else { 0 }
        $verdict = if ($delta -gt 0) { "IMPROVED" } elseif ($delta -lt 0) { "REGRESSED" } else { "FLAT" }
        Write-Log "Rating $latestScore ($verdict by $delta vs previous submission). Trend: $trend"
        $state | Add-Member -NotePropertyName lastScore -NotePropertyValue $latestScore -Force
        $state | Add-Member -NotePropertyName lastScoreVerdict -NotePropertyValue $verdict -Force
    }

    $episodesText = Native { & $kaggle competitions episodes $submissionId -v 2>&1 | Out-String }
    if ($LASTEXITCODE -ne 0) { throw "Kaggle episodes query failed: $episodesText" }
    Set-Content -LiteralPath (Join-Path $runtime "episodes.csv") -Value $episodesText
    $episodes = @($episodesText | ConvertFrom-Csv | Where-Object { $_.id -match '^\d+$' })
    if ($DryRun) {
        Write-Log "Dry run succeeded for submission $submissionId with $($episodes.Count) episode(s); needsImprovement=$($state.needsImprovement)."
        exit 0
    }

    $replayDir = Join-Path $workspace "replays\submission-$submissionId"
    New-Item -ItemType Directory -Path $replayDir -Force | Out-Null
    $newFiles = [Collections.Generic.List[string]]::new()
    foreach ($episode in $episodes) {
        $target = Join-Path $replayDir ("episode-{0}-replay.json" -f $episode.id)
        if (Test-Path -LiteralPath $target) { continue }
        $download = Native { & $kaggle competitions replay $episode.id -p $replayDir 2>&1 | Out-String }
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Replay $($episode.id) failed: $download"
            continue
        }
        if (Test-Path -LiteralPath $target) { $newFiles.Add($target) }
    }

    $downloadedReplayCount = $newFiles.Count
    if ($downloadedReplayCount -gt 0) { $state.needsImprovement = $true }
    $state | ConvertTo-Json | Set-Content -LiteralPath $statePath

    if ($downloadedReplayCount -eq 0) {
        if (-not $state.needsImprovement) {
            Write-Log "No unseen replays and the latest candidate passed quality; waiting for new evidence."
            exit 0
        }
        Get-ChildItem -LiteralPath $replayDir -Filter "*-replay.json" -File |
            Sort-Object Name | ForEach-Object { $newFiles.Add($_.FullName) }
        if ($newFiles.Count -eq 0) {
            Write-Log "Improvement remains active, but no replay evidence is available for submission $submissionId."
            exit 0
        }
        Write-Log "No unseen replays; continuing improvement with $($newFiles.Count) cached replay(s)."
    }

    Copy-Item -LiteralPath (Join-Path $workspace "main.py") -Destination (Join-Path $runtime "baseline_main.py") -Force
    Copy-Item -LiteralPath (Join-Path $workspace "test_agent.py") -Destination (Join-Path $runtime "baseline_test_agent.py") -Force
    Copy-Item -LiteralPath (Join-Path $workspace "verify.py") -Destination (Join-Path $runtime "baseline_verify.py") -Force
    Copy-Item -LiteralPath (Join-Path $workspace "memory.md") -Destination (Join-Path $runtime "baseline_memory.md") -Force
    Copy-Item -LiteralPath (Join-Path $workspace "decision.md") -Destination (Join-Path $runtime "baseline_decision.md") -Force
    if (Test-Path -LiteralPath $requestPath) { Remove-Item -LiteralPath $requestPath -Force }

    @{
        submissionId = $submissionId
        downloadedAt = (Get-Date -Format o)
        newReplayCount = $downloadedReplayCount
        newReplayFiles = if ($downloadedReplayCount) { @($newFiles | Select-Object -First $downloadedReplayCount) } else { @() }
        analysisReplayCount = $newFiles.Count
        analysisReplayFiles = @($newFiles)
        continuation = ($downloadedReplayCount -eq 0)
        scoreHistory = $scoreHistory
        state = $state
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runtime "run_context.json")

    Write-Log "Starting Codex analysis for $($newFiles.Count) replay(s), submission $submissionId."
    Native {
        Get-Content -Raw -LiteralPath $promptPath |
            codex exec - -C $workspace -s workspace-write --ephemeral --color never `
                -o (Join-Path $runtime "last_message.txt") *>> $runLog
    }
    if ($LASTEXITCODE -ne 0) { Reject "Codex exited with code $LASTEXITCODE." }
    if (-not (Test-Path -LiteralPath $requestPath)) { Reject "Codex did not approve a candidate." }

    $request = Get-Content -Raw -LiteralPath $requestPath | ConvertFrom-Json
    if (-not $request.approved) { Reject "Codex request was not approved." }

    $baselineHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $runtime "baseline_main.py")).Hash
    $candidateHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $workspace "main.py")).Hash
    if ($baselineHash -eq $candidateHash) { Reject "Rejected unchanged main.py." }

    foreach ($ledger in @("memory.md", "decision.md")) {
        $before = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $runtime "baseline_$ledger")).Hash
        $after = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $workspace $ledger)).Hash
        if ($before -eq $after) { Reject "Rejected candidate because $ledger was not updated." }
    }

    Native { & $python -m py_compile main.py test_agent.py verify.py *>> $runLog }
    if ($LASTEXITCODE -ne 0) { Reject "py_compile failed." }
    Native { & $python test_agent.py *>> $runLog }
    if ($LASTEXITCODE -ne 0) { Reject "test_agent.py failed." }

    # Re-run the benchmark here instead of trusting the numbers Codex reported. Eight
    # games cost about 40 seconds, so the gate is measured rather than self-graded.
    $benchmark = Native { & $python (Join-Path $runtime "baseline_verify.py") `
        (Join-Path $runtime "baseline_main.py") 4 2>$null }
    if ($LASTEXITCODE -ne 0) { Reject "verify.py failed to run." }
    Set-Content -LiteralPath (Join-Path $runtime "verified.json") -Value $benchmark
    $games = @((@($benchmark) | Where-Object { $_ } | Select-Object -Last 1 | ConvertFrom-Json).games)
    $allDone = @($games | Where-Object {
        $_.candidate_status -eq "DONE" -and $_.baseline_status -eq "DONE"
    }).Count
    $wins = @($games | Where-Object { [double]$_.candidate -gt [double]$_.baseline }).Count
    $meanDelta = if ($games.Count) {
        ($games | ForEach-Object { [double]$_.candidate - [double]$_.baseline } |
            Measure-Object -Average).Average
    } else { 0 }

    if ($games.Count -lt 8 -or $allDone -ne $games.Count -or $wins -lt 7 -or $meanDelta -lt 100) {
        Reject "Failed measured gate: games=$($games.Count), wins=$wins, meanDelta=$meanDelta, done=$allDone."
    }
    Write-Log "Verified gate: wins=$wins/$($games.Count), meanDelta=$meanDelta."

    if ([int]$state.submissionsUsed -ge [int]$state.submissionLimit) {
        $state | ConvertTo-Json | Set-Content -LiteralPath $statePath
        Write-Log "Automation submission budget exhausted; verified candidate retained locally."
        exit 0
    }

    $message = ([string]$request.message).Trim()
    if (-not $message) { $message = "Automated replay-tested improvement" }
    $submit = Native { & $kaggle competitions submit kaggriculture -f main.py -m $message 2>&1 | Out-String }
    Add-Content -LiteralPath $logPath -Value $submit
    if ($LASTEXITCODE -eq 0 -and $submit -match 'Successfully submitted') {
        $state | Add-Member -NotePropertyName submissionsUsed -NotePropertyValue ([int]$state.submissionsUsed + 1) -Force
        $state | Add-Member -NotePropertyName lastSubmittedAt -NotePropertyValue (Get-Date -Format o) -Force
        $state | Add-Member -NotePropertyName lastMessage -NotePropertyValue $message -Force
        $state.needsImprovement = $false
        $state | ConvertTo-Json | Set-Content -LiteralPath $statePath
        Write-Log "Submitted candidate; budget $($state.submissionsUsed)/$($state.submissionLimit)."
        Save-Work "automation: $message (+$([int]$meanDelta) mean money, $wins/$($games.Count) wins)"
    } else {
        Write-Log "Kaggle submission failed; budget unchanged."
    }
} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
} finally {
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}

