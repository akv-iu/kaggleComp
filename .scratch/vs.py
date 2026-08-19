"""Head-to-head of main.py against a variant, both seats, at a given interval.

Answers: does our score depend on what the *opponent* does to the shared market,
in a way a mirror cannot see? argv: json_overrides_for_opponent lo hi interval
"""
import importlib.util
import json
import sys
import os
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, over):
    path = os.path.join(ROOT, "main.py")
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    for k, v in (over or {}).items():
        if not hasattr(m, k):
            raise SystemExit("no such attribute: " + k)
        setattr(m, k, v)
    return m.agent


def _one(args):
    over, seed, interval, seat = args
    from kaggle_environments import make
    me = _load("me%d%d" % (seed, seat), {})
    opp = _load("op%d%d" % (seed, seat), over)
    env = make("kaggriculture", configuration={"seed": seed,
                                               "townCenterSellInterval": interval})
    env.run([me, opp] if seat == 0 else [opp, me])
    r = [s.reward for s in env.steps[-1]]
    return (seed, seat, r[seat], r[1 - seat])


if __name__ == "__main__":
    over = json.loads(sys.argv[1])
    lo, hi, interval = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    jobs = [(over, s, interval, seat) for s in range(lo, hi) for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=11) as ex:
        res = list(ex.map(_one, jobs))
    mine = [r[2] for r in res]
    theirs = [r[3] for r in res]
    print(json.dumps({"opponent": over, "interval": interval,
                      "our_mean": round(sum(mine) / len(mine), 1),
                      "their_mean": round(sum(theirs) / len(theirs), 1),
                      "games": [[r[0], r[1], int(r[2]), int(r[3])] for r in res]}))
