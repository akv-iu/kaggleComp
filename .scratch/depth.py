"""Market depth (I0 - inventory) and price per product, per day, on a mirror."""
import importlib.util
import json
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL",
     "FERTILIZER"]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main(path, seed, interval):
    from kaggle_environments import make
    a = load(path, "ax")
    b = load(path, "bx")
    rows = {}

    def wrapped(obs):
        d = obs["day"]
        if d not in rows:
            mk = obs["market"]
            rows[d] = {p: (10000 - mk["inventory"][p], mk["prices"][p]) for p in P}
            rows[d]["shops"] = list(obs["town"]["unlocked_shops"])
        return a.agent(obs)

    env = make("kaggriculture", configuration={"seed": seed,
                                               "townCenterSellInterval": interval})
    env.run([wrapped, b.agent])
    print("interval %d seed %d reward %s" % (interval, seed,
                                             [s.reward for s in env.steps[-1]]))
    print("day " + " ".join("%-14s" % p[:12] for p in P))
    for d in sorted(rows):
        cells = " ".join("%6d/%-7d" % rows[d][p] for p in P)
        print("%3d %s" % (d, cells))
    print("shops:", json.dumps({str(d): rows[d]["shops"] for d in sorted(rows)
                                if d % 3 == 0}))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
