"""Shed composition + pressure turns + discards. argv: <agent.py> <seed> <interval>"""
import importlib.util, sys, collections
from kaggle_environments import make
import kaggle_environments.envs.kaggriculture.kaggriculture as K
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m
path, seed, tci = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
A = load(path, "ca"); B = load(path, "cb")
disc = collections.Counter(); orig_drop = K._drop_inventories_to_shed
def drop(private, cap):
    before = sum(sum(i.values()) for i in private["inventories"])
    room = max(0, cap - sum(private["shed"].values()))
    orig_drop(private, cap)
    if before > room:
        pass
    return
def drop2(private, cap):
    held = collections.Counter()
    for i in private["inventories"]:
        held.update({k: v for k, v in i.items() if v > 0})
    room = max(0, cap - sum(private["shed"].values()))
    orig_drop(private, cap)
    lost = sum(held.values()) - min(sum(held.values()), room)
    if lost: disc["TOTAL"] += lost
    return
K._drop_inventories_to_shed = drop2
seen = {}; press = [0]; orig = A.agent
def agent(obs):
    d, h = obs["day"], obs["hour"]
    shed = obs["private"].get("shed", {})
    if sum(shed.values()) > 70: press[0] += 1
    if h == 0:
        seen[d] = ({k: v for k, v in shed.items() if v}, dict(obs["market"]["prices"]))
    return orig(obs)
A.agent = agent
env = make("kaggriculture", configuration={"seed": seed, "townCenterSellInterval": tci})
env.run([A.agent, B.agent])
print("rewards", env.steps[-1][0].reward, env.steps[-1][1].reward, "pressure turns(seat0)", press[0],
      "discarded units(both farms)", disc["TOTAL"])
for d in sorted(seen):
    s, p = seen[d]
    print("day %2d shed %3d %-70s | WOOL$%-4d STR$%-4d MILK$%-4d FERT$%-3d WHT$%-3d MEL$%-4d EGG$%d" % (
        d, sum(s.values()), s, p["WOOL"], p["STRAWBERRY"], p["MILK"], p["FERTILIZER"], p["WHEAT"], p["MELON"], p["EGG"]))
