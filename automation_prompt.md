Work autonomously on the Kaggriculture agent in this workspace.

Read `memory.md` and `decision.md` first. Then read
`.automation/run_context.json`, `.automation/submissions.txt`, the new replay
files it names, `main.py`, `test_agent.py`, and the competition rules before
changing anything. `.automation/baseline_main.py` and
`.automation/baseline_test_agent.py` are exact pre-run snapshots.

Analyze both players in every replay listed under `analysisReplayFiles`: score
and money curve, purchases and sales by product, surviving versus purchased
animals, crops, farm hands, movement and productive actions, unsold inventory,
market prices, and unlocked shops. Identify one measured bottleneck and make the
smallest root-cause change.

A failed quality gate is evidence for the next attempt, not completion. Run this
cycle until a candidate passes or three distinct full-benchmark attempts have
been rejected in this invocation:

1. Form a hypothesis that has not already failed under the same pairing.
2. Make the smallest change and benchmark it against the exact pre-run baseline.
3. Log the evidence in both ledgers.
4. If it fails, remove the rejected code, explain what the failure teaches, and
   immediately choose the next evidence-backed hypothesis.

Cheap screening runs may prune weak ideas, but they do not count as a passing
benchmark. Do not stop after the first failed experiment. If all three attempts
fail, leave `main.py` and `test_agent.py` identical to their pre-run snapshots,
write no submission request, and record the best distinct next hypothesis so the
next scheduled run can continue instead of repeating an old pairing.

For every evaluated attempt, including rejected experiments, append one entry to
`decision.md` with the state, exact change, pre-test reasoning, evidence, verdict,
and the pairing or condition that would justify trying it again. Never rewrite
old entries. After every attempt, update `memory.md` while keeping exactly its
two main strategy sections: merge duplicate lessons, preserve evidence, and
explain why a failed strategy may only be a bad pairing rather than universally
bad.

`run_context.json` also carries `scoreHistory`: the public rating of every
submission, newest first. Check whether the last submission's rating rose or fell
before choosing an experiment. A change that won locally but lowered the public
rating is evidence about the real field, and belongs in both ledgers.

Benchmark every serious candidate with `.venv/Scripts/python.exe verify.py
.automation/baseline_main.py 4`, which plays four deterministic seeds in both
seats and prints the games as JSON. Run `test_agent.py` and `py_compile`. Reject
an experiment unless it wins at least 7 of 8 games, improves mean final money by
at least 100, and every agent status is DONE. Remove rejected experiment code
before starting the next attempt. The wrapper re-runs `verify.py` itself and
applies the same gate to its own numbers, so a request backed by anything other
than a real measured run is rejected and rolled back.
Never modify `verify.py`; the wrapper freezes it before analysis and uses that
snapshot for the final independent gate.

You have no network access and must not call Kaggle or GitHub. The wrapper owns
downloads and submissions. If and only if the candidate passes, write
`.automation/submit_request.json` with this exact shape:

```
{
  "approved": true,
  "message": "short Kaggle submission description",
  "games": [
    {
      "seed": 0,
      "seat": 0,
      "candidate": 80000,
      "baseline": 70000,
      "candidate_status": "DONE",
      "baseline_status": "DONE"
    }
  ]
}
```

Include every benchmark game. Do not create the request for ambiguous or failed
results, and do not create it until both `memory.md` and `decision.md` reflect
the selected attempt. Never use destructive git commands, never overwrite
unrelated changes, and never submit unchanged code. End with a concise report of
evidence and work.
