"""Kaggriculture agent: priority-job dispatch over all units, drip selling.

Every turn we scan the farm for work, sort it by urgency, and hand each job to the
nearest idle unit. Market orders are emitted in the order that money flows:
hire -> sell -> restock seeds -> expand land.
"""

# Only the fields the policy actually reads. Mirrors CROPS in kaggriculture.py.
CROPS = {
    "WHEAT":      {"seed":  10, "first":  2, "maxday":  4, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed":  20, "first":  2, "maxday":  3, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed":  50, "first":  8, "maxday":  8, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first": 10, "maxday": 10, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed":  80, "first": 10, "maxday": 12, "max_yield": 6, "ongoing": False},
}

LAST_DAY = 29
LAND_PRICES = [1000, 2000, 4000]

# Crops we plant, most preferred first. Wheat's glut curve (log, target 0.20) barely
# moves under volume; melon's (sq, 3.60) collapses, so melon is capped by MELON_FRAC
# and sold on a drip rather than dumped.
CROP_PREF = ["MELON", "WHEAT"]
MELON_FRAC = 0.6

# Per-turn sell cap and price floor per product. Wheat absorbs any volume, so it
# sells uncapped; the premium goods leak out slowly to keep the price up.
SELL_RULES = {
    "WHEAT":      (999, 0),
    "CARROT":     (999, 0),
    "MELON":      (1, 60),
    "TOMATO":     (4, 20),
    "STRAWBERRY": (1, 40),
    "FERTILIZER": (2, 40),
}

# A plant must be watered EVERY day or it weeds out, so tending capacity -- not
# land and not cash -- is what caps how much we may plant. A unit gets 24 actions
# a day and spends roughly half of them walking, so it can keep about this many
# tiles alive. Planting past it doesn't grow more food, it grows weeds.
PLANTS_PER_UNIT = 3
# Hands are hired per day at fib(n) = 1,1,2,3,5,8,13,21,... so the marginal hand
# is trivial until it suddenly isn't. Cap the *marginal* cost at a slice of the
# bank rather than fixing a headcount -- crew is what land and seeds are worth
# having, so it should grow with income.
HIRE_FRAC = 0.003
MAX_HANDS = 18
# Cash never committed to seeds or land: a full day of hires plus slack. Hitting
# $0 is unrecoverable -- with no cash there are no hands, and with no hands the
# whole farm weeds out.
CASH_FLOOR = 250
LAND_RESERVE = 1500


def _fib(n):
    """Cost of the n-th hire of the day: 1, 1, 2, 3, 5, 8, 13, ..."""
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _harvest_day(crop):
    """First day the plant hits max yield under daily watering.

    Yield starts at 1 and gains 1 per watered day inside [window_start, maxday],
    so it caps at window_start + max_yield - 2 -- which for melon (day 10) is two
    days before max_yield_day. Harvesting later just risks decay.
    """
    c = CROPS[crop]
    window_start = (c["maxday"] + 1) // 2
    return min(c["maxday"], window_start + c["max_yield"] - 2)


def _step_toward(ux, uy, tx, ty):
    """One greedy step. Locked tiles are passable, so there are no obstacles."""
    if ux < tx:
        return ["EAST"]
    if ux > tx:
        return ["WEST"]
    if uy < ty:
        return ["SOUTH"]  # y grows downward
    if uy > ty:
        return ["NORTH"]
    return None


def _shed_tiles(size):
    h = size // 2
    return [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]


def _pick_crop(x, y, seeds, day):
    """Choose a crop for an empty tile from what's in the seed slot.

    The (x, y) hash spreads melon over a fixed fraction of tiles deterministically,
    so the mix holds without tracking state across turns.
    """
    wants_melon = ((x * 7 + y * 3) % 10) < MELON_FRAC * 10
    order = CROP_PREF if wants_melon else [c for c in CROP_PREF if c != "MELON"]
    for crop in order:
        if seeds.get(crop, 0) <= 0:
            continue
        if day + _harvest_day(crop) > LAST_DAY:  # would not ripen before the season ends
            continue
        return crop
    return None


def _scan(tiles, day, seeds, plant_budget):
    """Return (jobs, empty_tiles). Jobs are (priority, x, y, op); lower is more urgent.

    `plant_budget` is how many more tiles the current crew can keep watered; PLANT
    jobs stop there even when seeds and empty land are available.
    """
    jobs = []
    empty = []
    size = len(tiles)
    for y in range(size):
        row = tiles[y]
        for x in range(size):
            t = row[x]
            if t == "LOCKED":
                continue
            if t is None:
                empty.append((x, y))
                continue
            kind = t.get("kind")
            if kind == "PLANT":
                crop = t["crop"]
                age = day - t["planted_day"]
                if not t["watered_today"]:
                    # Priority 0: two dry days turns the tile into a weed, and
                    # watering inside the bonus window is where the yield comes from.
                    jobs.append((0, x, y, ["WATER"]))
                elif t["yield_units"] > 0:
                    c = CROPS[crop]
                    if age >= (c["first"] if c["ongoing"] else _harvest_day(crop)):
                        jobs.append((1, x, y, ["HARVEST"]))
            elif "animal" in t:
                if not t.get("fed_today"):
                    jobs.append((0, x, y, ["FEED"]))
                elif t.get("yield_units", 0) > 0:
                    jobs.append((1, x, y, ["HARVEST"]))
            elif kind == "WEED":
                jobs.append((3, x, y, ["DIG"]))

    # PLANT is validated atomically: if more units request a crop than we hold
    # seeds for, the env drops *every* PLANT for that crop. So decrement a local
    # copy of the seed counts as we queue.
    seeds = dict(seeds)
    for (x, y) in empty:
        if plant_budget <= 0:
            break
        crop = _pick_crop(x, y, seeds, day)
        if crop is None:
            continue
        seeds[crop] -= 1
        plant_budget -= 1
        jobs.append((2, x, y, ["PLANT", crop]))
    return jobs, empty


def _assign(units, jobs, size, invs):
    """Greedy: walk jobs by priority, give each to the nearest still-idle unit."""
    acts = [["PASS"] for _ in units]
    idle = set(range(len(units)))
    jobs.sort(key=lambda j: j[0])
    for _prio, jx, jy, op in jobs:
        if not idle:
            break
        best = min(idle, key=lambda i: abs(units[i][0] - jx) + abs(units[i][1] - jy))
        ux, uy = units[best]
        acts[best] = op if (ux, uy) == (jx, jy) else _step_toward(ux, uy, jx, jy)
        idle.discard(best)

    # Nothing to do but holding produce: run it to the shed so it can be sold today
    # instead of waiting for the end-of-day drop.
    sheds = _shed_tiles(size)
    for i in idle:
        if i < len(invs) and sum(invs[i].values()) > 0:
            ux, uy = units[i]
            tx, ty = min(sheds, key=lambda s: abs(ux - s[0]) + abs(uy - s[1]))
            acts[i] = ["DROP"] if (ux, uy) == (tx, ty) else _step_toward(ux, uy, tx, ty)
    return acts


def _market(me, priv, obs, n_empty, plant_budget):
    day, hour = obs["day"], obs["hour"]
    money = me["money"]
    seeds = priv.get("seeds", {})
    shed = priv.get("shed", {})
    prices = obs["market"]["prices"]
    orders = []

    # 1. Hire, before anything else can spend the cash. Hands are the cheapest
    # throughput there is (fib: 1,1,2,3,5,8,...), they only work for the rest of
    # the day, and every other spend depends on having crew to tend what it buys.
    n_tiles = sum(1 for row in me["tiles"] for t in row if t != "LOCKED")
    if hour <= 1 and day < LAST_DAY:
        n = me["hires_today"]
        crew_cap = -(-n_tiles // PLANTS_PER_UNIT)  # no point staffing past the land
        while len(orders) < 8 and n < min(MAX_HANDS, crew_cap):
            if _fib(n) > max(2, money * HIRE_FRAC):
                break
            orders.append(["HIRE"])
            n += 1

    # 2. Sell. Drip the crash-prone goods, dump everything on the final day.
    endgame = day >= LAST_DAY
    for item, (cap, floor) in SELL_RULES.items():
        have = shed.get(item, 0)
        if have <= 0 or len(orders) >= 10:
            continue
        if endgame:
            orders.append(["SELL", item, have])
        elif prices.get(item, 0) >= floor:
            orders.append(["SELL", item, min(have, cap)])

    # 3. Restock seeds -- only as many as the crew can actually keep watered, and
    # only with cash above the floor.
    if not endgame and len(orders) < 10:
        budget = money - CASH_FLOOR
        for crop in CROP_PREF:
            if len(orders) >= 10 or budget <= 0:
                break
            if day + _harvest_day(crop) > LAST_DAY:
                continue
            share = MELON_FRAC if crop == "MELON" else 1 - MELON_FRAC
            cost = CROPS[crop]["seed"]
            need = min(int(plant_budget * share) - seeds.get(crop, 0), int(budget // cost))
            if need > 0:
                orders.append(["BUY_SEED", crop, need])
                budget -= need * cost

    # 4. Expand once the crew can tend more than the land can hold. Requiring the
    # farm to be *fully* planted never fires, because a crew that outgrows its
    # land leaves tiles empty by construction.
    n_extra = len(me["unlocked_quadrants"]) - 1
    if (not endgame and len(orders) < 10 and n_extra < len(LAND_PRICES)
            and day < LAST_DAY - 8 and plant_budget > n_empty
            and money >= LAND_PRICES[n_extra] + LAND_RESERVE):
        orders.append(["BUY_LAND"])

    return orders[:10]


def agent(obs):
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    tiles = me["tiles"]
    size = len(tiles)

    units = [list(me["farmer"])] + [list(p) for p in me["hands"]]
    invs = priv.get("inventories", []) or []

    # Crew size we've actually paid for today (hands spawn a turn after the HIRE
    # order lands, so hires_today leads the hands list at dawn).
    crew = 1 + max(len(me["hands"]), me["hires_today"])
    growing = sum(1 for row in tiles for t in row
                  if isinstance(t, dict) and (t.get("kind") == "PLANT" or "animal" in t))
    plant_budget = max(0, crew * PLANTS_PER_UNIT - growing)

    jobs, empty = _scan(tiles, obs["day"], priv.get("seeds", {}), plant_budget)
    acts = _assign(units, list(jobs), size, invs)
    market = _market(me, priv, obs, len(empty), plant_budget)

    return {"farmer": acts[0], "hands": acts[1:], "market": market}
