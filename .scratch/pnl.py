"""Per-product units and revenue for player 0, plus tiles-by-crop per day."""
import importlib.util
import json
import sys
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main(path, seed, interval):
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as K

    a = load(path, "ax")
    b = load(path, "bx")

    units = Counter()
    rev = Counter()
    spend = Counter()
    tiles_by_day = {}
    key = {}

    orig = K._commit_unit

    def commit(op, item, price, farm, private, market, shed_capacity=100):
        ok = orig(op, item, price, farm, private, market, shed_capacity)
        if ok and key.get("f") is farm:
            if op == "SELL":
                units[item] += 1
                rev[item] += price
            else:
                spend[op + ":" + item] += price
        return ok

    K._commit_unit = commit
    orig_pm = K._process_market

    def pm(state, env):
        key["f"] = state[0].observation.farms[0]
        return orig_pm(state, env)

    K._process_market = pm

    def wrapped(obs):
        me = obs["farms"][obs["player"]]
        key["f"] = me
        d = obs["day"]
        if d not in tiles_by_day:
            c = Counter()
            for row in me["tiles"]:
                for t in row:
                    if t is None:
                        c["EMPTY"] += 1
                    elif isinstance(t, dict):
                        c[t.get("crop") or t.get("animal") or t.get("kind")] += 1
            c["money"] = int(me["money"])
            sd = obs["private"].get("seeds", {})
            c["seeds"] = {k: v for k, v in sd.items() if v}
            tiles_by_day[d] = dict(c)
        return a.agent(obs)

    env = make("kaggriculture", configuration={"seed": seed,
                                               "townCenterSellInterval": interval})
    env.run([wrapped, b.agent])
    K._commit_unit = orig
    print(json.dumps({
        "path": os.path.basename(path), "seed": seed, "interval": interval,
        "reward": [s.reward for s in env.steps[-1]],
        "units": dict(units), "rev": dict(rev),
        "unit_price": {k: round(rev[k] / units[k]) for k in units},
        "spend": dict(spend),
        "tiles": {str(d): tiles_by_day[d] for d in sorted(tiles_by_day)},
    }))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
