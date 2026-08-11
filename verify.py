"""Head-to-head benchmark: candidate main.py vs a baseline copy, plus a mirror.

Run: .venv/Scripts/python.exe verify.py [baseline.py] [n_seeds]
Prints one JSON line: {"games": [...], "mirror": {...}}

The head-to-head asks "does it beat the previous agent". That question rewards
acting *sooner* than the opponent on anything shared, because the opponent is a
slower copy of ourselves -- and the market here is shared. v7 dropped the
fertilizer sell floor, won 7/8 head-to-head at +$1,504, and lost 36 points of
public rating: nothing drains fertilizer, so selling faster only decides which
farm gets the top of a curve both are pushing down.

So `mirror` plays each agent against *itself* and reports its absolute score. A
change that genuinely produces or saves more raises the mirror score; a change
that merely gets there first does not, because in a mirror both sides get there
at the same time. Judge a candidate on both numbers.
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


def mirror(path, tag, n_seeds):
    """Absolute score with both seats played by the same agent.

    Loaded twice under different module names on purpose: an agent that keeps
    state between turns would otherwise share one copy of it across both farms.
    """
    a, b = _load(path, tag + "_a"), _load(path, tag + "_b")
    scores, done = [], True
    for seed in range(n_seeds):
        env = make("kaggriculture", configuration={"seed": seed})
        env.run([a, b])
        for s in env.steps[-1]:
            scores.append(s.reward)
            done = done and str(s.status) == "DONE"
    return {"scores": scores, "mean": sum(scores) / len(scores), "all_done": done}


def run_mirror(baseline_path, n_seeds):
    cand = mirror("main.py", "mcand", n_seeds)
    base = mirror(baseline_path, "mbase", n_seeds)
    return {"candidate": cand, "baseline": base,
            "delta": cand["mean"] - base["mean"]}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else ".automation/baseline_main.py"
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    print(json.dumps({"games": run(path, seeds),
                      "mirror": run_mirror(path, seeds)}))
