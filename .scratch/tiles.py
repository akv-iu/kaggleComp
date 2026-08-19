"""Tiles under each crop per day, and bare tiles, for player 0 of a mirror.

argv: seed interval SHED_TILE_RESERVE
"""
import importlib.util
import json
import sys
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path, name, res):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    m.SHED_TILE_RESERVE = res
    return m


def main(seed, interval, res):
    from kaggle_environments import make
    a = load(os.path.join(ROOT, "main.py"), "ax", res)
    b = load(os.path.join(ROOT, "main.py"), "bx", res)
    census = {}
    planted = Counter()

    def wrapped(obs):
        me = obs["farms"][obs["player"]]
        c = Counter()
        for row in me["tiles"]:
            for t in row:
                if t == "LOCKED":
                    c["LOCKED"] += 1
                elif t is None:
                    c["BARE"] += 1
                elif t.get("kind") == "PLANT":
                    c[t["crop"]] += 1
                elif "animal" in t:
                    c["ANIMAL"] += 1
                else:
                    c[t.get("kind", "?")] += 1
        census[obs["day"]] = dict(c)
        r = a.agent(obs)
        for act in [r["farmer"]] + r["hands"]:
            if act and act[0] == "PLANT":
                planted[act[1]] += 1
        return r

    env = make("kaggriculture", configuration={"seed": seed,
                                               "townCenterSellInterval": interval})
    env.run([wrapped, b.agent])
    print(json.dumps({
        "seed": seed, "interval": interval, "reserve": res,
        "reward": [s.reward for s in env.steps[-1]],
        "plant_orders": dict(planted),
        "days": {d: {k: v for k, v in census[d].items() if k != "LOCKED"}
                 for d in (6, 10, 13, 17, 22, 27) if d in census},
    }))


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
