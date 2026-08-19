"""Per-crop lifecycle audit for player 0 of a mirror.

Plantings, harvest units, weed deaths and the whole action histogram.
argv: seed interval [path]
"""
import importlib.util
import json
import sys
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = {"farm": None}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main(seed, interval, path):
    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
    a = load(path, "ax")
    b = load(path, "bx")

    plants = Counter(); harv = Counter(); hcount = Counter()
    deaths = Counter(); decayed = Counter(); acts = Counter()
    animal_units = Counter()

    orig_apply = K._apply_unit_action

    def apply(farm, private, idx, action, board_size, day, tpd, cap=100):
        if farm is not H["farm"] or not (isinstance(action, list) and action):
            return orig_apply(farm, private, idx, action, board_size, day, tpd, cap)
        acts[action[0]] += 1
        pos = K._farmer_position(farm, idx)
        t = farm["tiles"][pos[1]][pos[0]] if pos else None
        if action[0] == "HARVEST" and isinstance(t, dict):
            if t.get("kind") == "PLANT":
                harv[t["crop"]] += t.get("yield_units", 0)
                hcount[t["crop"]] += 1
            elif "animal" in t:
                animal_units[t["animal"]] += t.get("yield_units", 0)
                hcount[t["animal"]] += 1
        r = orig_apply(farm, private, idx, action, board_size, day, tpd, cap)
        if action[0] == "PLANT" and pos:
            nt = farm["tiles"][pos[1]][pos[0]]
            if isinstance(nt, dict) and nt.get("kind") == "PLANT":
                plants[nt["crop"]] += 1
        return r

    K._apply_unit_action = apply

    def wrap_kill(orig, bucket):
        def f(farm, *args):
            if farm is not H["farm"]:
                return orig(farm, *args)
            before = {(x, y): t["crop"]
                      for y, row in enumerate(farm["tiles"])
                      for x, t in enumerate(row)
                      if isinstance(t, dict) and t.get("kind") == "PLANT"}
            r = orig(farm, *args)
            for (x, y), crop in before.items():
                nt = farm["tiles"][y][x]
                if isinstance(nt, dict) and nt.get("kind") == "WEED":
                    bucket[crop] += 1
            return r
        return f

    K._daily_refresh_plants = wrap_kill(K._daily_refresh_plants, deaths)
    K._decay_plants = wrap_kill(K._decay_plants, decayed)

    orig_interp = K.interpreter

    def interp(state, env_):
        farms = state[0].observation.get("farms")
        if farms:
            H["farm"] = farms[0]
        return orig_interp(state, env_)

    K.interpreter = interp
    env = make("kaggriculture", configuration={"seed": seed,
                                               "townCenterSellInterval": interval})
    env.interpreter = interp
    env.run([a.agent, b.agent])
    print(json.dumps({
        "seed": seed, "interval": interval,
        "reward": [s.reward for s in env.steps[-1]],
        "planted": dict(plants), "crop_harvest_units": dict(harv),
        "harvests": dict(hcount), "animal_units": dict(animal_units),
        "thirst_deaths": dict(deaths), "decay_deaths": dict(decayed),
        "actions": dict(acts.most_common()),
    }, indent=1))


if __name__ == "__main__":
    p = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "main.py")
    main(int(sys.argv[1]), int(sys.argv[2]), p)
