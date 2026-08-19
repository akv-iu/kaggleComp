"""Attribute movement to the productive action each walk ends in.

One mirror game. For player 0, log every unit's action verb each turn; a "run"
is consecutive move actions by the same unit slot ending in a non-move action.
Credit the run length to that terminal verb.
"""
import importlib.util
import json
import sys
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main(seed, interval):
    from kaggle_environments import make
    a = load(os.path.join(ROOT, "main.py"), "ax")
    b = load(os.path.join(ROOT, "main.py"), "bx")

    log = []            # per turn: list of verbs for player 0
    per_day_moves = Counter()
    per_day_prod = Counter()

    def wrapped(obs):
        r = a.agent(obs)
        verbs = [r["farmer"][0]] + [h[0] for h in r["hands"]]
        log.append((obs["day"], verbs))
        return r

    env = make("kaggriculture", configuration={"seed": seed,
                                               "townCenterSellInterval": interval})
    env.run([wrapped, b.agent])

    # attribute
    walk_to = Counter()      # verb -> moves spent walking to it
    count = Counter()        # verb -> times done
    pending = defaultdict(int)
    last_day = None
    for day, verbs in log:
        if day != last_day:
            pending.clear()
            last_day = day
        for i, v in enumerate(verbs):
            if v in MOVES:
                pending[i] += 1
                per_day_moves[day] += 1
            else:
                walk_to[v] += pending[i]
                pending[i] = 0
                count[v] += 1
                if v != "PASS":
                    per_day_prod[day] += 1
    total_turns = sum(len(v) for _, v in log)
    total_moves = sum(per_day_moves.values())
    rows = []
    for v, n in count.most_common():
        rows.append({"verb": v, "n": n, "walk": walk_to[v],
                     "per": round(walk_to[v] / n, 2) if n else 0})
    print(json.dumps({
        "seed": seed, "interval": interval,
        "reward": [s.reward for s in env.steps[-1]],
        "unit_turns": total_turns, "moves": total_moves,
        "move_share": round(total_moves / total_turns, 3),
        "rows": rows,
        "moves_by_day": [per_day_moves[d] for d in range(30)],
        "prod_by_day": [per_day_prod[d] for d in range(30)],
    }, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
