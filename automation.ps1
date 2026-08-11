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
$indexPath = Join-Path $workspace "replay_index.json"
# Mirror gain below this is indistinguishable from a change that merely acts
# sooner than a slower copy of itself. Calibrated on two submissions: v7 won the
# head-to-head 7/8 at +$1,504, showed +84 in the mirror, and lost 36 points of
# public rating; v8 showed +3,903. Raise it if a racing change ever slips past.
$mirrorMin = 500
$mutex = [Threading.Mutex]::new($false, "Local\KaggricultureReplayOptimizer")

# A run that crashed while holding the mutex leaves it abandoned, and WaitOne then
# throws instead of returning false.
try { $held = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $held = $true }
if (-not $held) { exit 0 }

# Windows PowerShell 5.1 hands a JSON array back from ConvertFrom-Json as a single
# object instead of enumerating it, so `@($json | ConvertFrom-Json)` yields a
# one-element array *containing* the array. That silently turned the replay index
# into one row -- the seen-set matched nothing and every run re-downloaded the
# season it had just pruned.
function AsArray($value) {
    if ($null -eq $value) { return @() }
    if ($value -is [array]) { return $value }
    return @($value)
}

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
        & git add -- main.py test_agent.py verify.py loop.py memory.md decision.md `
            attempts.jsonl automation.ps1 automation_prompt.md *>> $runLog
        & git diff --cached --quiet
        if ($LASTEXITCODE -eq 0) { return }
        & git commit -q -m $message *>> $runLog
        & git -c credential.interactive=false push -q origin HEAD *>> $runLog
        if ($LASTEXITCODE -ne 0) { Write-Log "git push failed; commit kept locally." }
    }
}

# The agent edits main.py in place, so a rejected experiment must be rolled back or it
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
    # the agent so it can weigh what public play actually rewarded.
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

    # The index, not the disk, is the record of what we have already seen. Raw
    # replays are ~17MB each and get pruned once they have been indexed, so
    # testing for the file would re-download the whole season every run.
    $seen = @{}
    if (Test-Path -LiteralPath $indexPath) {
        foreach ($row in (AsArray (Get-Content -Raw -LiteralPath $indexPath | ConvertFrom-Json))) {
            $seen[[string]$row.episode] = $true
        }
    }

    $newFiles = [Collections.Generic.List[string]]::new()
    foreach ($episode in $episodes) {
        $target = Join-Path $replayDir ("episode-{0}-replay.json" -f $episode.id)
        if ($seen.ContainsKey([string]$episode.id) -or (Test-Path -LiteralPath $target)) { continue }
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

    if ($downloadedReplayCount -eq 0 -and -not $state.needsImprovement) {
        Write-Log "No unseen replays and the latest candidate passed quality; waiting for new evidence."
        exit 0
    }

    # Index every replay from its first 64KB -- `rewards` and `TeamNames` are
    # serialised before `steps`, so this never parses a 17MB file -- then keep
    # only the handful worth reading and delete the rest of the raw corpus.
    # Reading all 41 replays equally is what let "20W-20L on average" hide that
    # the top of the field scores 175,862 against our best-ever 82,876.
    Native { & $python loop.py index *>> $runLog }
    Native { & $python loop.py attempts *>> $runLog }
    $selected = AsArray ((Native { & $python loop.py select | Out-String }) | ConvertFrom-Json)
    Native { & $python loop.py prune *>> $runLog }

    if ($selected.Count -eq 0) {
        Write-Log "Improvement remains active, but no replay evidence is available."
        exit 0
    }
    $analysisFiles = @($selected | ForEach-Object { $_.file })
    Write-Log ("Analysing {0} selected replay(s): {1} new this run." -f $selected.Count, $downloadedReplayCount)

    Copy-Item -LiteralPath (Join-Path $workspace "main.py") -Destination (Join-Path $runtime "baseline_main.py") -Force
    Copy-Item -LiteralPath (Join-Path $workspace "test_agent.py") -Destination (Join-Path $runtime "baseline_test_agent.py") -Force
    Copy-Item -LiteralPath (Join-Path $workspace "verify.py") -Destination (Join-Path $runtime "baseline_verify.py") -Force
    Copy-Item -LiteralPath (Join-Path $workspace "memory.md") -Destination (Join-Path $runtime "baseline_memory.md") -Force
    Copy-Item -LiteralPath (Join-Path $workspace "decision.md") -Destination (Join-Path $runtime "baseline_decision.md") -Force
    if (Test-Path -LiteralPath $requestPath) { Remove-Item -LiteralPath $requestPath -Force }

    $index = AsArray (Get-Content -Raw -LiteralPath $indexPath | ConvertFrom-Json)
    $losses = @($index | Where-Object { $_.result -eq "LOSS" })
    $ourBest = ($index | Measure-Object -Property me -Maximum).Maximum
    $fieldBest = $index | Sort-Object -Property them -Descending | Select-Object -First 1

    @{
        submissionId = $submissionId
        downloadedAt = (Get-Date -Format o)
        newReplayCount = $downloadedReplayCount
        # Only these are worth opening. Self-games are excluded from the index:
        # our own submissions meet in the public field and teach nothing about it.
        analysisReplayCount = $selected.Count
        analysisReplayFiles = $analysisFiles
        selectedReplays = $selected
        fieldRecord = @{
            games = $index.Count
            wins = @($index | Where-Object { $_.result -eq "WIN" }).Count
            losses = $losses.Count
            ourBestGame = $ourBest
            fieldBestGame = $fieldBest.them
            fieldBestBy = $fieldBest.opponent
            fieldBestWatch = $fieldBest.watch
        }
        attemptsFile = "attempts.jsonl"
        continuation = ($downloadedReplayCount -eq 0)
        scoreHistory = $scoreHistory
        state = $state
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runtime "run_context.json")

    Write-Log "Starting analysis for $($selected.Count) replay(s), submission $submissionId."
    # `-p` is non-interactive, so nothing can answer a permission prompt: a denied
    # tool call would look like a failed experiment rather than a blocked one.
    # Web tools are denied outright instead -- the wrapper owns every Kaggle call,
    # and the agent is told it has no network.
    $reply = Native {
        Get-Content -Raw -LiteralPath $promptPath |
            & claude -p --model opus --effort high `
                --permission-mode bypassPermissions `
                --disallowed-tools WebFetch WebSearch 2>&1 | Out-String
    }
    $exit = $LASTEXITCODE
    Set-Content -LiteralPath (Join-Path $runtime "last_message.txt") -Value $reply
    if ($exit -ne 0) { Reject "Analysis agent exited with code $exit." }
    if (-not (Test-Path -LiteralPath $requestPath)) { Reject "No candidate was approved." }

    $request = Get-Content -Raw -LiteralPath $requestPath | ConvertFrom-Json
    if (-not $request.approved) { Reject "Submission request was not approved." }

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

    # Re-run the benchmark here instead of trusting the numbers the agent reported. Eight
    # games cost about 40 seconds, so the gate is measured rather than self-graded.
    $benchmark = Native { & $python (Join-Path $runtime "baseline_verify.py") `
        (Join-Path $runtime "baseline_main.py") 4 2>$null }
    if ($LASTEXITCODE -ne 0) { Reject "verify.py failed to run." }
    Set-Content -LiteralPath (Join-Path $runtime "verified.json") -Value $benchmark
    $verified = @($benchmark) | Where-Object { $_ } | Select-Object -Last 1 | ConvertFrom-Json
    $games = @($verified.games)
    $mirrorDelta = [double]$verified.mirror.delta
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
    # The head-to-head alone cannot tell production from racing, so require the
    # mirror -- each agent against itself -- to gain too. See verify.py.
    if (-not $verified.mirror.candidate.all_done -or $mirrorDelta -lt $mirrorMin) {
        Reject "Failed mirror gate: mirrorDelta=$mirrorDelta (need $mirrorMin). Beats the old agent without producing more."
    }
    Write-Log "Verified gate: wins=$wins/$($games.Count), meanDelta=$meanDelta, mirrorDelta=$mirrorDelta."

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

