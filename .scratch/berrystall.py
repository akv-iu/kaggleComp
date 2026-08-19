"""Why does the berry field stall? Log per day: seeds, slots, budget, plant jobs queued."""
import importlib.util, sys, collections
from kaggle_environments import make
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m
path, seed, tci = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
A = load(path, "ca"); B = load(path, "cb")
orig_scan = A._scan
log = collections.defaultdict(lambda: collections.Counter())
cur = {}
def scan(tiles, day, hour, seeds, slots, money, stock):
    jobs, want, grown = orig_scan(tiles, day, hour, seeds, slots, money, stock)
    d = log[day]
    d["scans"] += 1
    d["slots_sum"] += slots
    d["berryjobs"] += sum(1 for j in jobs if j[3][0] == "PLANT" and j[3][1] == "STRAWBERRY")
    d["wheatjobs"] += sum(1 for j in jobs if j[3][0] == "PLANT" and j[3][1] == "WHEAT")
    d["build"] += sum(1 for j in jobs if j[3][0].startswith("BUILD"))
    cur[day] = (seeds.get("STRAWBERRY", 0), grown.get("STRAWBERRY", 0), money)
    return jobs, want, grown
A._scan = scan
orig = A.agent
plants = collections.Counter()
def agent(obs):
    r = orig(obs)
    for a in [r["farmer"]] + list(r["hands"]):
        if a[0] == "PLANT": plants[(obs["day"], a[1])] += 1
    return r
A.agent = agent
env = make("kaggriculture", configuration={"seed": seed, "townCenterSellInterval": tci})
env.run([A.agent, B.agent])
print("rewards", env.steps[-1][0].reward, env.steps[-1][1].reward)
for d in sorted(log):
    if d > 20: break
    c = log[d]; s = cur.get(d, (0,0,0))
    print("day %2d seeds %2d grown %2d $%7.0f  avg slots %5.1f  berryjobs/turn %5.2f wheatjobs %5.2f build %4.1f | PLANTED %s" % (
        d, s[0], s[1], s[2], c["slots_sum"]/max(1,c["scans"]), c["berryjobs"]/max(1,c["scans"]),
        c["wheatjobs"]/max(1,c["scans"]), c["build"]/max(1,c["scans"]),
        {k[1]: v for k, v in plants.items() if k[0] == d}))
