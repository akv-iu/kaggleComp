"""Did the dusk-reach guard fire, and what did the freed unit-turns become?

argv: seed interval DUSK_REACH. Reports the action histogram, total moves, and
the moves that are still pending at the end of a day -- the walks that arrive
nowhere, which is exactly what the guard is supposed to delete.
"""
import importlib.util
import json
import sys
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}


def load(path, name, reach):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    exec("m.%s = %s" % (os.environ["OV_K"], reach))
    return m


def main(seed, interval, reach):
    from kaggle_environments import make
    a = load(os.path.join(ROOT, "main.py"), "ax", reach)
    b = load(os.path.join(ROOT, "main.py"), "bx", reach)

    log = []

    def wrapped(obs):
        r = a.agent(obs)
        log.append((obs["day"], [r["farmer"][0]] + [h[0] for h in r["hands"]]))
        return r

    env = make("kaggriculture", configuration={"seed": seed,
                                               "townCenterSellInterval": interval})
    env.run([wrapped, b.agent])

    walk_to, count = Counter(), Counter()
    pending = defaultdict(int)
    orphan = moves = 0
    last_day = None
    for day, verbs in log:
        if day != last_day:
            orphan += sum(pending.values())
            pending.clear()
            last_day = day
        for i, v in enumerate(verbs):
            if v in MOVES:
                pending[i] += 1
                moves += 1
            else:
                walk_to[v] += pending[i]
                pending[i] = 0
                count[v] += 1
    orphan += sum(pending.values())
    turns = sum(len(v) for _, v in log)
    print(json.dumps({
        "seed": seed, "interval": interval, "reach": reach,
        "reward": [s.reward for s in env.steps[-1]],
        "unit_turns": turns, "moves": moves, "orphan_moves": orphan,
        "pass": count["PASS"],
        "productive": sum(n for v, n in count.items() if v != "PASS"),
        "hist": {v: [n, walk_to[v]] for v, n in count.most_common()},
    }))


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
