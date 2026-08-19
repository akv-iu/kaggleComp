"""Fast regression checks for the evidence-first automation infrastructure."""

import json
import tempfile
from pathlib import Path

import loop


ROOT = Path(__file__).parent


def test_replay_selection():
    with tempfile.TemporaryDirectory() as directory:
        paths = []
        for index in range(5):
            path = Path(directory) / f"{index}.json"
            path.touch()
            paths.append(str(path))
        rows = [
            {"episode": "1", "submission": "10", "file": paths[0], "result": "LOSS", "delta": -9000, "them": 10000},
            {"episode": "2", "submission": "10", "file": paths[1], "result": "LOSS", "delta": -100, "them": 9000},
            {"episode": "3", "submission": "10", "file": paths[2], "result": "WIN", "delta": 50, "them": 12000},
            {"episode": "4", "submission": "11", "file": paths[3], "result": "LOSS", "delta": -20000, "them": 30000},
            {"episode": "5", "submission": "10", "file": paths[4], "result": "LOSS", "delta": -8000, "them": 11000},
        ]
        assert [row["episode"] for row in loop.select(rows, "10")] == ["1", "2", "3"]


def test_attempt_migration_and_relevance():
    original = loop.ATTEMPTS
    try:
        with tempfile.TemporaryDirectory() as directory:
            loop.ATTEMPTS = str(Path(directory) / "attempts.jsonl")
            rows = loop.migrate_attempts()
            assert len(rows) == 108
            assert len({row["id"] for row in rows}) == 108
            assert all(row["history"] for row in rows)
            relevant = loop._relevant_attempts(rows)
            text = " ".join(row["hypothesis"] for row in relevant).lower()
            assert "wheat" in text and "shed" in text and "melon" in text
    finally:
        loop.ATTEMPTS = original


def test_evaluator_fingerprint():
    verifier = (ROOT / "verify.py").read_text(encoding="utf-8")
    assert 'CONFIGURATION = {"townCenterSellInterval": 24}' in verifier
    assert 'EVALUATOR_VERSION = "competition-v2"' in verifier
    assert '"fingerprint": _fingerprint()' in verifier
    assert 'shop_rng.choice(sorted(game.SHOPS))' in verifier


def test_automation_contract():
    script = (ROOT / "automation.ps1").read_text(encoding="utf-8")
    poll = script.split("function Invoke-Poll", 1)[1].split("function Proposal-Data", 1)[0]
    arm = script.split("function Invoke-ArmPlan", 1)[1].split("function Evaluate-Json", 1)[0]
    assert "claude " not in poll.lower()
    assert "main.py" not in poll
    assert "claude -p --model sonnet --effort medium" in arm
    assert "--tools=" in arm
    assert "num_turns -gt 6" in arm
    assert "--permission-mode plan" in arm
    assert "decision.md" not in script
    assert "function Recover-InterruptedPlanning" in script
    assert 'state -ne "AWAITING_REVIEW"' in script
    assert 'state -notin @("READY_TO_SUBMIT", "SUBMIT_FAILED")' in script
    assert 'Evaluate-Json $baselinePath 4 16' in script
    assert 'Evaluate-Json $baselinePath 12 0' in script
    for state in ("IDLE", "EVIDENCE_READY", "PLAN_RUNNING", "AWAITING_REVIEW",
                  "EVALUATING", "REJECTED", "READY_TO_SUBMIT", "SUBMITTED",
                  "SUBMIT_FAILED", "CAP_REACHED"):
        assert f'"{state}"' in script


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    attempts = [json.loads(line) for line in (ROOT / "attempts.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(attempts) == 108
    print(f"{len(tests)} infrastructure tests passed; {len(attempts)} attempts indexed")
