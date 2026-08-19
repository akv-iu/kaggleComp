"""Reconstruct an opponent's season from a replay: tile census, actions, P&L."""
import json, sys, collections

path, seat = sys.argv[1], int(sys.argv[2])
rep = json.load(open(path))
steps = rep["steps"]
cfg = rep.get("configuration", {})
print("config:", {k: cfg[k] for k in cfg if k in
      ("townCenterSellInterval","townShopSellInterval","townShopUnlockInterval",
       "shedCapacity","turnsPerDay","episodeSteps","weedSpawnChance")})

acts = collections.Counter()
market_ops = collections.Counter()
moves = 0
census = {}
prev_hires = 0
hire_cost = 0
def fib(n):
    a,b=1,1
    for _ in range(n): a,b=b,a+b
    return a

land = 0
seed_buy = collections.Counter()
animal_buy = collections.Counter()
shops = None
for i in range(1, len(steps)):
    obs = steps[i-1][0]["observation"]
    farms = obs["farms"]
    farm = farms[seat]
    day, hour = obs["day"], obs["hour"]
    act = steps[i][seat].get("action") or {}
    if not isinstance(act, dict): continue
    ua = [act.get("farmer", ["PASS"])] + list(act.get("hands", []) or [])
    for a in ua:
        if not isinstance(a, list) or not a: continue
        if a[0] in ("NORTH","SOUTH","EAST","WEST"): moves += 1
        else: acts[a[0]] += 1
    for o in (act.get("market") or []):
        if not isinstance(o, list) or not o: continue
        market_ops[o[0]] += 1
        if o[0] == "BUY_SEED" and len(o) >= 3: seed_buy[o[1]] += int(o[2])
        if o[0] == "BUY_ANIMAL" and len(o) >= 3: animal_buy[o[1]] += int(o[2])
    if hour == 0:
        c = collections.Counter(); bare = 0
        for row in farm["tiles"]:
            for t in row:
                if t == "LOCKED": continue
                if t is None: bare += 1
                elif isinstance(t, dict) and t.get("kind") == "PLANT": c[t["crop"]] += 1
                elif isinstance(t, dict) and "animal" in t: c[t["animal"]] += 1
                elif isinstance(t, dict): c[t.get("kind")] += 1
        census[day] = (farm["money"], bare, dict(c), len(farm["unlocked_quadrants"]),
                       sum((steps[i-1][seat]["observation"].get("private") or {}).get("shed", {}).values()))
    h = farm["hires_today"]
    if h > prev_hires:
        for n in range(prev_hires, h): hire_cost += fib(n)
    prev_hires = h if hour != 23 else 0

last = steps[-1][0]["observation"]
print("final money", [f["money"] for f in last["farms"]])
print("shops", last["town"]["unlocked_shops"])
print("actions", dict(acts.most_common()), "moves", moves,
      "unit-turns", moves + sum(acts.values()))
print("market ops", dict(market_ops))
print("seeds bought", dict(seed_buy), "animals bought", dict(animal_buy))
print("hire cost ~", hire_cost)
print("final market prices", {k: v for k, v in last["market"]["prices"].items()})
print("final market inv-I0", {k: v-10000 for k, v in last["market"]["inventory"].items()})
for d in sorted(census):
    m, bare, c, q, sh = census[d]
    print("day %2d $%8.0f q%d bare %2d shed %3d %s" % (d, m, q, bare, sh, dict(c)))
