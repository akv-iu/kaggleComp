"""Kaggriculture agent: priority-job dispatch over all units, drip selling.

Every turn we scan the farm for work, sort it by urgency, and hand each job to the
nearest idle unit that can do it. Market orders are emitted in the order that money
flows: hire -> sell -> restock -> expand.

The farm runs a mixed portfolio on purpose. Sell price is a per-product curve, so
each product saturates independently: melon pays hugely per action but collapses
after ~150 units (sq, above_target 3.60), while egg and wheat barely move under any
volume we can produce (log, 0.20). Melon funds the opening; geese carry the endgame.
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
GOOSE_COST = 300

# Tile mix, as fractions of the farm. The rest goes to wheat, which exists mostly
# to feed the geese -- a goose eats 1 wheat/day and a wheat tile yields ~0.8/day.
#
# Tuned in SELF-PLAY, not against the built-in starter. Starter sells carrots and
# never touches melon, which makes melon look like a private goldmine worth 60% of
# the farm; against an opponent who also sells melon the price collapses twice as
# fast and both players fall from ~$57k to ~$24k. This mix wins 16/16 (both seats,
# 8 seeds, +4272) over the melon-heavy config that starter preferred, while scoring
# *lower* against starter itself. Believe the self-play number.
#
# Caveat: these are requested fractions, not realised ones -- see _tile_role.
MELON_FRAC = 0.4
GOOSE_FRAC = 0.2

# A plant must be watered EVERY day or it weeds out, so tending capacity -- not
# land and not cash -- is what caps how much we may take on. A unit gets 24 actions
# a day and spends roughly half walking. Animals cost more per day than plants
# (feed + harvest + care + fertilizer vs. one watering), hence ANIMAL_WORK.
PLANTS_PER_UNIT = 3
ANIMAL_WORK = 3
# Geese are what surplus cash converts into, never an opening move. A $300 bird
# bought on day 3 starves the melon seed money and the hiring that melon depends
# on, and a farm with no crew cannot tend the birds either. Wait for a real bank.
GOOSE_MIN_CASH = 15000
# Hands are hired per day at fib(n) = 1,1,2,3,5,8,13,21,... so the marginal hand
# is trivial until it suddenly isn't. Lean hiring measured far better than eager.
HIRE_FRAC = 0.003
MAX_HANDS = 18

# Per-turn sell cap and price floor per product. Wheat and egg absorb any volume
# we can produce; the premium goods leak out slowly to keep their price up.
SELL_RULES = {
    "WHEAT":      (999, 0),
    "EGG":        (999, 0),
    "CARROT":     (999, 0),
    "MELON":      (1, 60),
    "TOMATO":     (4, 20),
    "STRAWBERRY": (1, 40),
    "FERTILIZER": (4, 40),
}

# Days of feed kept in the shed rather than sold. Starving a goose two days running
# loses the bird permanently, which costs far more than the wheat is worth.
FEED_RESERVE_DAYS = 3
# Cash never committed to seeds, birds or land. Hitting $0 is unrecoverable: no
# cash means no hands, and no hands means the whole farm weeds out.
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
    return ["PASS"]


def _shed_tiles(tiles):
    """Unlocked shed-access tiles. Only these can PICKUP/DROP."""
    h = len(tiles) // 2
    return [(x, y) for (x, y) in ((h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h))
            if tiles[y][x] != "LOCKED"]


def _tile_role(x, y):
    """Fixed spatial split of the farm, so the mix holds without carrying state.

    ponytail: the (7x+3y)%10 hash is uniform over the full 10x10 board but NOT
    over a single 5x5 quadrant, which is where the whole opening is played. Only
    5 of the 10 residues occur there, so requested fractions do not survive: 0.5
    and 0.6 melon both realise as 60% in the opening quadrant, making those two
    configs byte-identical until the second quadrant is bought. Any sweep over
    these knobs is therefore lumpy and partly measuring the hash. Replace with an
    exact per-quadrant quota (row-major index vs. cumulative fractions) if the mix
    needs tuning further -- that also clusters same-role tiles, which cuts walking.
    """
    h = (x * 7 + y * 3) % 10
    if h < MELON_FRAC * 10:
        return "MELON"
    if h < (MELON_FRAC + GOOSE_FRAC) * 10:
        return "COOP"
    return "WHEAT"


def _plantable(crop, seeds, day):
    return seeds.get(crop, 0) > 0 and day + _harvest_day(crop) <= LAST_DAY


def _scan(tiles, day, seeds, work_budget, money):
    """Return (jobs, empty, n_empty_coops).

    Jobs are (priority, x, y, op, needs_item); lower priority runs first.
    `needs_item` means only a unit carrying that item can take the job.
    `work_budget` is how much more the current crew can keep alive; new plantings
    and new coops stop there even when seeds, birds and land are all available.
    """
    jobs = []
    empty = []
    n_empty_coops = 0
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
                    # Two dry days turns the tile into a weed, and watering inside
                    # the bonus window is where the yield actually comes from.
                    jobs.append((0, x, y, ["WATER"], None))
                elif t["yield_units"] > 0:
                    c = CROPS[crop]
                    if age >= (c["first"] if c["ongoing"] else _harvest_day(crop)):
                        jobs.append((1, x, y, ["HARVEST"], None))
            elif "animal" in t:
                if not t.get("fed_today"):
                    jobs.append((0, x, y, ["FEED"], "WHEAT"))
                elif t.get("yield_units", 0) > 0:
                    jobs.append((1, x, y, ["HARVEST"], None))
                elif not t.get("cared_today"):
                    # CARE banks +1 on the next production: for a goose that is a
                    # second egg every day, for one action.
                    jobs.append((2, x, y, ["CARE"], None))
                elif t.get("fertilizer_available"):
                    jobs.append((3, x, y, ["COLLECT_FERTILIZER"], None))
            elif kind in ("COOP", "PASTURE"):
                n_empty_coops += 1
                jobs.append((1, x, y, ["PLACE", "GOOSE"], "GOOSE"))
            elif kind == "WEED":
                jobs.append((3, x, y, ["DIG"], None))

    # PLANT is validated atomically: if more units request a crop than we hold
    # seeds for, the env drops *every* PLANT for that crop. So decrement a local
    # copy of the seed counts as we queue.
    seeds = dict(seeds)
    can_start_animals = day < LAST_DAY - 8 and money >= GOOSE_MIN_CASH
    for (x, y) in empty:
        role = _tile_role(x, y)
        if role == "COOP" and can_start_animals:
            if work_budget >= ANIMAL_WORK:
                work_budget -= ANIMAL_WORK
                jobs.append((2, x, y, ["BUILD_COOP"], None))
            continue
        if work_budget < 1:
            continue
        for crop in ([role, "WHEAT"] if role != "COOP" else ["WHEAT"]):
            if _plantable(crop, seeds, day):
                seeds[crop] -= 1
                work_budget -= 1
                jobs.append((2, x, y, ["PLANT", crop], None))
                break
    return jobs, empty, n_empty_coops


def _fetch_jobs(tiles, invs, shed, wanted):
    """Shed runs for items the field needs but nobody is carrying.

    FEED and PLACE consume from the acting unit's own inventory, so wheat and
    geese have to be walked out from the shed before those jobs can fire at all.
    """
    jobs = []
    docks = _shed_tiles(tiles)
    if not docks:
        return jobs
    for item, need in wanted.items():
        carried = sum(inv.get(item, 0) for inv in invs)
        short = min(need - carried, shed.get(item, 0))
        if short <= 0:
            continue
        for _ in range(min(2, -(-short // 4))):  # a couple of carriers is plenty
            x, y = docks[0]
            jobs.append((-1, x, y, ["PICKUP", item, min(short, 8)], None))
    return jobs


def _assign(units, jobs, tiles, invs):
    """Greedy: walk jobs by priority, give each to the nearest able, idle unit."""
    acts = [["PASS"] for _ in units]
    idle = set(range(len(units)))
    jobs.sort(key=lambda j: j[0])
    for _prio, jx, jy, op, need in jobs:
        if not idle:
            break
        able = [i for i in idle
                if need is None or (i < len(invs) and invs[i].get(need, 0) > 0)]
        if not able:
            continue
        best = min(able, key=lambda i: abs(units[i][0] - jx) + abs(units[i][1] - jy))
        ux, uy = units[best]
        acts[best] = op if (ux, uy) == (jx, jy) else _step_toward(ux, uy, jx, jy)
        idle.discard(best)

    # Nothing to do but holding produce: run it to the shed so it can be sold today
    # instead of waiting for the end-of-day drop (which discards past the cap).
    docks = _shed_tiles(tiles)
    for i in idle:
        if docks and i < len(invs) and sum(invs[i].values()) > 0:
            ux, uy = units[i]
            tx, ty = min(docks, key=lambda s: abs(ux - s[0]) + abs(uy - s[1]))
            acts[i] = ["DROP"] if (ux, uy) == (tx, ty) else _step_toward(ux, uy, tx, ty)
    return acts


def _market(me, priv, obs, n_empty, work_budget, n_animals, n_empty_coops, carried):
    day, hour = obs["day"], obs["hour"]
    money = me["money"]
    seeds = priv.get("seeds", {})
    shed = priv.get("shed", {})
    prices = obs["market"]["prices"]
    orders = []
    endgame = day >= LAST_DAY

    # 1. Hire, before anything else can spend the cash. Hands are the cheapest
    # throughput there is, they only work for the rest of the day, and everything
    # else we might buy is worthless without crew to tend it.
    n_tiles = sum(1 for row in me["tiles"] for t in row if t != "LOCKED")
    if hour <= 1 and day < LAST_DAY:
        n = me["hires_today"]
        crew_cap = -(-n_tiles // PLANTS_PER_UNIT)  # no point staffing past the land
        while len(orders) < 8 and n < min(MAX_HANDS, crew_cap):
            if _fib(n) > max(2, money * HIRE_FRAC):
                break
            orders.append(["HIRE"])
            n += 1

    # 2. Sell. Drip the crash-prone goods, hold back feed wheat, dump on the last day.
    feed_reserve = 0 if endgame else n_animals * FEED_RESERVE_DAYS
    for item, (cap, floor) in SELL_RULES.items():
        have = shed.get(item, 0) - (feed_reserve if item == "WHEAT" else 0)
        if have <= 0 or len(orders) >= 10:
            continue
        if endgame:
            orders.append(["SELL", item, have])
        elif prices.get(item, 0) >= floor:
            orders.append(["SELL", item, min(have, cap)])

    if endgame:
        return orders[:10]

    budget = money - CASH_FLOOR

    # 3. Emergency feed. A goose starved two days running is gone for good, so
    # buying wheat at any price beats losing a $300 bird.
    short_feed = n_animals - shed.get("WHEAT", 0) - carried.get("WHEAT", 0)
    if short_feed > 0 and len(orders) < 10 and budget > 0:
        n = min(short_feed, int(budget // max(1, prices.get("WHEAT", 25))))
        if n > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", n])
            budget -= n * prices.get("WHEAT", 25)

    # 4. Birds for any coop standing empty. A goose lays daily and forever, so the
    # payback is in days on the calendar -- early birds are worth far more.
    if day < LAST_DAY - 8 and len(orders) < 10 and money >= GOOSE_MIN_CASH:
        want = n_empty_coops - shed.get("GOOSE", 0) - carried.get("GOOSE", 0)
        n = min(want, int(budget // GOOSE_COST))
        if n > 0:
            orders.append(["BUY_ANIMAL", "GOOSE", n])
            budget -= n * GOOSE_COST

    # 5. Restock seeds -- only as many as the crew can keep watered.
    for crop in ("MELON", "WHEAT"):
        if len(orders) >= 10 or budget <= 0:
            break
        if day + _harvest_day(crop) > LAST_DAY:
            continue
        share = MELON_FRAC if crop == "MELON" else 1 - MELON_FRAC - GOOSE_FRAC
        cost = CROPS[crop]["seed"]
        need = min(int(work_budget * share) - seeds.get(crop, 0), int(budget // cost))
        if need > 0:
            orders.append(["BUY_SEED", crop, need])
            budget -= need * cost

    # 6. Expand once the crew can tend more than the land can hold. Requiring the
    # farm to be *fully* planted never fires: a crew that outgrows its land leaves
    # tiles empty by construction.
    n_extra = len(me["unlocked_quadrants"]) - 1
    if (len(orders) < 10 and n_extra < len(LAND_PRICES) and day < LAST_DAY - 8
            and work_budget > n_empty
            and money >= LAND_PRICES[n_extra] + LAND_RESERVE):
        orders.append(["BUY_LAND"])

    return orders[:10]


def agent(obs):
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    tiles = me["tiles"]

    units = [list(me["farmer"])] + [list(p) for p in me["hands"]]
    invs = priv.get("inventories", []) or []

    # Crew size we've actually paid for today (hands spawn a turn after the HIRE
    # order lands, so hires_today leads the hands list at dawn).
    crew = 1 + max(len(me["hands"]), me["hires_today"])
    n_plants = n_animals = 0
    for row in tiles:
        for t in row:
            if not isinstance(t, dict):
                continue
            if t.get("kind") == "PLANT":
                n_plants += 1
            elif "animal" in t:
                n_animals += 1
    work_budget = max(0, crew * PLANTS_PER_UNIT - n_plants - ANIMAL_WORK * n_animals)

    jobs, empty, n_empty_coops = _scan(tiles, obs["day"], priv.get("seeds", {}),
                                       work_budget, me["money"])
    carried = {}
    for inv in invs:
        for item, n in inv.items():
            carried[item] = carried.get(item, 0) + n
    jobs += _fetch_jobs(tiles, invs, priv.get("shed", {}),
                        {"WHEAT": n_animals, "GOOSE": n_empty_coops})

    acts = _assign(units, jobs, tiles, invs)
    market = _market(me, priv, obs, len(empty), work_budget,
                     n_animals, n_empty_coops, carried)

    return {"farmer": acts[0], "hands": acts[1:], "market": market}
