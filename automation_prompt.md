Work autonomously on the Kaggriculture agent in this workspace.

## The situation you are in

Excluding games against our own submissions, this agent is **losing**: 33 wins
to 40 losses across the indexed public field. Our best game ever is $82,876. The
top of the field scores **$175,862**. Four opponents have beaten our best-ever
game. That gap is not a tuning gap, and roughly twenty-five experiments spent on
constants inside the current architecture have moved it very little.

So the standing question for every run is: **what is the top of the field doing
that we are not?** Prefer a hypothesis drawn from a game we lost badly over one
drawn from our own averages.

## Read this much, and no more

Read in this order and stop when you have what you need:

1. `memory.md` — the curated ledger. Always read in full. It is the durable
   record of what works, what does not, and why.
2. `attempts.jsonl` — one line per past experiment: title, verdict, record.
   Check a new idea against this before proposing it. It exists so you never
   have to read `decision.md` just to ask "was this tried?"
3. `.automation/run_context.json` — this run's evidence, including
   `fieldRecord`, `selectedReplays` and `scoreHistory`.
4. The replay files named in `analysisReplayFiles`. There are only a handful and
   they are chosen for you: the worst losses, the highest-scoring opponent games,
   and the near-misses. Do not go looking for more — the raw corpus is pruned to a
   250MB budget after every run, so most episodes exist only as rows in
   `replay_index.json`. That index holds every game ever scored, with opponent,
   both scores and a replay URL, and it is the right place to ask questions about
   the field as a whole. Only the selected files can be opened.
5. `main.py`, `test_agent.py`, and the competition rules.
6. `decision.md` only if you need the full reasoning behind a specific past
   attempt. **Grep it for the entry you want; do not read it end to end.** It is
   an append-only archive and it grows every run.

`.automation/baseline_main.py` and `.automation/baseline_test_agent.py` are exact
pre-run snapshots.

The environment source is at
`.venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py`.
It is the ground truth for every price, yield and action. Read it rather than
trusting `main.py`'s own comments about the game; those have been wrong before.

## Analysing a loss

For each selected replay, reconstruct what the *winner* did and contrast it with
what we did: what they built and when, their money curve, what they sold and at
what price, how many animals and crops they carried, how their actions divided
between production, logistics and movement. The question is never "what did we
do slightly wrong" but "what is their plan, and is ours worse in kind?"

Write throwaway analysis scripts rather than reading raw JSON; a replay is ~17MB
and 720 steps.

## Making a change

Identify one bottleneck you can point at with a number, then make the smallest
change that addresses its cause. Run this cycle until a candidate passes or three
distinct full-benchmark attempts have been rejected in this invocation:

1. Form a hypothesis that is not already in `attempts.jsonl` under the same
   pairing.
2. Make the smallest change and benchmark it against the exact pre-run baseline.
3. Log the evidence in both ledgers.
4. If it fails, remove the rejected code, explain what the failure teaches, and
   immediately choose the next evidence-backed hypothesis.

Cheap screening runs may prune weak ideas, but they do not count as a passing
benchmark. Do not stop after the first failed experiment. If all three attempts
fail, leave `main.py` and `test_agent.py` identical to their pre-run snapshots,
write no submission request, and record the best distinct next hypothesis.

## The two gates

Benchmark with `.venv/Scripts/python.exe verify.py .automation/baseline_main.py 4`,
which prints `games` and `mirror` as JSON. Run `test_agent.py` and `py_compile`.

- **Head-to-head:** at least 7 of 8 games won, mean final money up at least 100,
  every status DONE.
- **Mirror:** the candidate's mirror mean must beat the baseline's by at least
  500.

The mirror exists because the head-to-head plays you against a slower copy of
yourself, which rewards merely *acting sooner* on anything shared. Submission v7
won the head-to-head 7/8 at +$1,504, showed **+84** in the mirror, and lost 36
points of public rating. Nothing drains the fertilizer market, so selling faster
only decided which farm got the top of a curve both were pushing down. Before you
believe a local win, ask whether the gain survives the opponent making the same
move at the same time. If it does not, the mirror will say so.

The wrapper re-runs `verify.py` itself and applies both gates to its own numbers,
so a request backed by anything other than a real measured run is rejected and
rolled back. Never modify `verify.py` or `loop.py`; the wrapper freezes the
verifier before analysis and uses that snapshot for the independent gate.

## Ledgers

For every evaluated attempt, including rejected experiments, append one entry to
`decision.md` with the state, exact change, pre-test reasoning, evidence, verdict,
and the pairing or condition that would justify trying it again. Never rewrite old
entries.

After every attempt, update `memory.md` while keeping exactly its two main
sections: merge duplicate lessons, preserve evidence, and explain why a failed
strategy may only be a bad pairing rather than universally bad. Keep it curated —
it is read in full every run, so a lesson that is now superseded should be merged
into the entry that supersedes it rather than left to accumulate.

`attempts.jsonl` is regenerated from `decision.md` by the wrapper. Do not edit it.

`run_context.json` carries `scoreHistory`: the public rating of every submission,
newest first. Check whether the last submission's rating rose or fell before
choosing an experiment. A change that won locally but lowered the public rating is
evidence about the real field and belongs in both ledgers.

## Rules

You have no network access and must not call Kaggle or GitHub. The wrapper owns
downloads and submissions. If and only if the candidate passes both gates, write
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
results, and do not create it until both `memory.md` and `decision.md` reflect the
selected attempt. Never use destructive git commands, never overwrite unrelated
changes, and never submit unchanged code. End with a concise report of evidence
and work.
