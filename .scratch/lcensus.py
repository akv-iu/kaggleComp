"""Per-day census of a local mirror. argv: <agent.py> <seed> <interval>"""
import importlib.util, sys, collections
from kaggle_environments import make
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m
path, seed, tci = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
A = load(path, "ca"); B = load(path, "cb")
seen = {}; orig = A.agent
acts = collections.Counter(); moves = 0
def agent(obs):
    global moves
    d, h = obs["day"], obs["hour"]
    if h == 0:
        me = obs["farms"][obs["player"]]
        c = collections.Counter(); bare = 0
        for row in me["tiles"]:
            for t in row:
                if t == "LOCKED": continue
                if t is None: bare += 1
                elif t.get("kind") == "PLANT": c[t["crop"]] += 1
                elif "animal" in t: c[t["animal"]] += 1
                else: c[t.get("kind")] += 1
        seen[d] = (me["money"], bare, dict(c), sum(obs["private"].get("shed", {}).values()))
    r = orig(obs)
    for a in [r["farmer"]] + list(r["hands"]):
        if a[0] in ("NORTH","SOUTH","EAST","WEST"): moves += 1
        else: acts[a[0]] += 1
    return r
A.agent = agent
env = make("kaggriculture", configuration={"seed": seed, "townCenterSellInterval": tci})
env.run([A.agent, B.agent])
print("rewards", env.steps[-1][0].reward, env.steps[-1][1].reward)
print("actions", dict(acts.most_common()), "moves", moves)
for d in sorted(seen):
    m, bare, c, sh = seen[d]
    print("day %2d $%8.0f bare %2d shed %3d %s" % (d, m, bare, sh, c))
