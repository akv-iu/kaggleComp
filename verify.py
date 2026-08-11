"""Head-to-head benchmark: candidate main.py vs a baseline copy.

Run: .venv/Scripts/python.exe verify.py [baseline.py] [n_seeds]
Prints one JSON line: {"games": [{seed, seat, candidate, baseline, *_status}, ...]}
"""

import importlib.util
import json
import sys

from kaggle_environments import make


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.agent


def run(baseline_path=".automation/baseline_main.py", n_seeds=4):
    cand, base = _load("main.py", "cand_main"), _load(baseline_path, "base_main")
    games = []
    for seed in range(n_seeds):
        for seat in (0, 1):
            env = make("kaggriculture", configuration={"seed": seed})
            env.run([cand, base] if seat == 0 else [base, cand])
            me, them = env.steps[-1][seat], env.steps[-1][1 - seat]
            games.append({"seed": seed, "seat": seat,
                          "candidate": me.reward, "baseline": them.reward,
                          "candidate_status": str(me.status),
                          "baseline_status": str(them.status)})
    return games


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else ".automation/baseline_main.py"
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    print(json.dumps({"games": run(path, seeds)}))
