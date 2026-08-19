"""Per-item nightfall discards + shed occupancy + pressure turns, both intervals."""
import importlib.util
import sys
import os
import collections
import json
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _one(args):
    seed, interval, over = args
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as K

    disc = collections.Counter()
    occ = []
    _orig = K._drop_inventories_to_shed

    def drop(private, capacity):
        shed = private["shed"]
        for inv in private["inventories"]:
            for item, n in list(inv.items()):
                if n <= 0:
                    del inv[item]
                    continue
                room = max(0, capacity - sum(shed.values()))
                take = min(n, room)
                if take > 0:
                    shed[item] = shed.get(item, 0) + take
                if n - take:
                    disc[item] += n - take
                del inv[item]

    K._drop_inventories_to_shed = drop

    def load(name):
        spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "main.py"))
        m = importlib.util.module_from_spec(spec)
        sys.modules[name] = m
        spec.loader.exec_module(m)
        for k, v in over.items():
            setattr(m, k, v)
        return m

    ma, mb = load("ma"), load("mb")
    press = [0, 0]
    prices_at_discard = collections.Counter()

    def wrap(mod, pid):
        def a(obs):
            if pid == 0 and sum(obs["private"]["shed"].values()) > mod.SHED_PRESSURE:
                press[0] += 1
            return mod.agent(obs)
        return a

    env = make("kaggriculture", configuration={"seed": seed, "townCenterSellInterval": interval})
    env.run([wrap(ma, 0), wrap(mb, 1)])
    # discards counted for BOTH farms; halve for a per-farm number
    px = env.steps[-1][0].observation["market"]["prices"]
    val = sum(n * px.get(i, 0) for i, n in disc.items()) / 2.0
    return {"seed": seed, "score": env.steps[-1][0].reward,
            "disc": {k: v / 2.0 for k, v in disc.items()},
            "disc_total": sum(disc.values()) / 2.0,
            "disc_value_at_final_px": round(val),
            "pressure_turns": press[0]}


if __name__ == "__main__":
    interval = int(sys.argv[1])
    lo, hi = int(sys.argv[2]), int(sys.argv[3])
    over = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
    with ProcessPoolExecutor(max_workers=11) as ex:
        res = list(ex.map(_one, [(s, interval, over) for s in range(lo, hi)]))
    agg = collections.Counter()
    for r in res:
        for k, v in r["disc"].items():
            agg[k] += v
    n = len(res)
    print("interval", interval, "seeds", lo, hi)
    for r in res:
        print("  seed %2d score %7d discard %5.1f ($%d) press %d %s" % (
            r["seed"], r["score"], r["disc_total"], r["disc_value_at_final_px"],
            r["pressure_turns"], {k: round(v) for k, v in sorted(r["disc"].items(), key=lambda kv: -kv[1])}))
    print("MEAN per farm per game:", {k: round(v / n, 1) for k, v in agg.most_common()},
          "total %.1f" % (sum(agg.values()) / n),
          "value $%d" % (sum(r["disc_value_at_final_px"] for r in res) / n))
