# Kaggriculture optimizer

An agent for the Kaggle [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture)
competition, developed with an evidence-first, manually-approved optimization loop.
See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the workflow and its commands.

The agent itself is a single file: [`main.py`](main.py).

## Reproducing the results

Python 3.13. The only dependency is `kaggle_environments`, which ships the
Kaggriculture environment.

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install "kaggle-environments==1.32.4"
```

Version 1.32.4 is the version every recorded result in this repository was
produced against. Environment behaviour has changed between releases, so results
from another version are not comparable.

### Check the agent runs and beats the built-in baseline

```bash
.venv/Scripts/python.exe test_agent.py
```

Asserts the internal yield/scheduling helpers and plays a full 720-turn episode.

### Score a candidate against a baseline

```bash
.venv/Scripts/python.exe verify.py <baseline.py> <seed-count> <first-seed> <candidate.py>
```

For example, twelve seeds starting at 0, scoring `main.py` against a saved baseline:

```bash
.venv/Scripts/python.exe verify.py baseline_main.py 12 0 main.py
```

Prints one JSON object: per-seed mirror deltas, head-to-head results, the medians,
and the evaluator/configuration fingerprint plus both code hashes. Runs both seats
for every seed.

Note that `verify.py` defaults its baseline argument to `.automation/baseline_main.py`,
which is generated at runtime and is not committed. Pass an explicit baseline path
when running from a fresh clone.

`verify.py` mirrors observed competition behaviour rather than reimplementing it;
its calibration against real replays, and the seed-sensitivity caveat that comes
with it, are recorded in [`EVALUATOR_BACKTEST.md`](EVALUATOR_BACKTEST.md).

## Repository layout

| Path | Contents |
| --- | --- |
| [`main.py`](main.py) | The submitted agent |
| [`verify.py`](verify.py) | Local evaluator — mirror and head-to-head scoring |
| [`test_agent.py`](test_agent.py) | Runnable check: helpers plus one full episode |
| [`loop.py`](loop.py) | Replay polling and evidence construction |
| [`automation.ps1`](automation.ps1) | The manually-gated automation loop |
| [`attempts.jsonl`](attempts.jsonl) | Machine-readable index of every attempt and its outcome |
| [`decision.md`](decision.md) | Frozen historical archive of strategy reasoning |
| [`memory.md`](memory.md) | Working notes carried between planning runs |
| [`.scratch/`](.scratch/) | Experiment scripts and candidate variants |

Files under `.automation/`, `replays/`, and `kagglehub/` are runtime or
competition-provided artifacts and are deliberately not tracked.

## License

Not yet chosen — pending the license type the competition rules require for
shared and winning submissions. Until a `LICENSE` file is added here, treat this
code as licensed on whatever terms the Kaggriculture competition rules impose on
publicly shared submissions, and not otherwise.
