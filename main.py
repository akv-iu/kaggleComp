"""Kaggriculture agent: livestock-first farm with priority-job dispatch.

Every turn we scan the farm for work, sort it by urgency, and hand each job to the
nearest idle unit that can do it. Market orders are emitted in the order that money
flows: hire -> sell -> feed -> stock -> expand.

The farm is mostly animals, and the reason is CARE. `pending_care_bonus` is banked
every fed-and-cared day and only spent on a production day, so a cared cow gives
three $160 milks every second day rather than one, and a cared sheep four $200
wools every third. Add the fertilizer every beast drops nightly and a head is
~4 actions a day for $200-370, forever. The best crop, melon, is 13 actions for
six units and then the tile is bare again -- it is a cash injection, not a
business, and it is capped at MELON_TILES at a time for that reason.

Feed is part grown, part bought. Per action an animal beats a wheat tile easily,
so the first call on land and labour is livestock -- but livestock costs $300-500
a head and wheat seed costs $10, and this farm spends most of the season short of
cash rather than short of hands. So tiles we cannot afford to stock go under
wheat, which also stops us bidding up the feed we are about to buy: BUY_PRODUCT
takes stock out of the market and wheat rises on a sqrt curve below I0, so a farm
that buys all its feed pays $54 a head by day 15 for what cost $25 on day 0.

Sell caps come from the price curve, not from taste. price(inv) = base -+ amp*f(),
and the town only drains what its shops consume. Egg is `log` (480 sold still
fetches $39) so it is the dump product; wool is `sq` with amp 0.058 (59 units and
the price is zero) so it leaks out one per turn. Melon appears in no shop at all,
which makes it a fixed ~$26k pool shared with the opponent -- take a slice early,
never build a farm on it.
"""

# Only the fields the policy actually reads. Mirrors kaggriculture.py.
CROPS = {
    "WHEAT":      {"seed":  10, "first":  2, "maxday":  4, "max_yield": 6, "interval": 0, "ongoing": False},
    "CARROT":     {"seed":  20, "first":  2, "maxday":  3, "max_yield": 4, "interval": 0, "ongoing": False},
    "TOMATO":     {"seed":  50, "first":  8, "maxday":  8, "max_yield": 4, "interval": 1, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first": 10, "maxday": 10, "max_yield": 4, "interval": 2, "ongoing": True},
    "MELON":      {"seed":  80, "first": 10, "maxday": 12, "max_yield": 6, "interval": 0, "ongoing": False},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first": 4, "interval": 1},
    "COW":   {"cost": 400, "structure": "PASTURE", "first": 8, "interval": 2},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first": 6, "interval": 3},
}
BUILD = {"COOP": ["BUILD_COOP"], "PASTURE": ["BUILD_PASTURE"]}

LAST_DAY = 29
LAND_PRICES = [1000, 2000, 4000]
SHED_CAP = 100

# Herd mix. Sheep and cow earn more per action than goose, but wool and milk are
# the two products whose price falls off a cliff (sq/0.058 and linear/2.10) while
# egg barely moves under any volume we can produce. So the mix is a hedge against
# the shop unlock order: YARN_STORE may not exist until day 24, and 8 sheep with
# no yarn store is 250 wool into a market that absorbs 140.
HERD = {"GOOSE": 0.10, "COW": 0.50, "SHEEP": 0.40}
# Day 0 only takes the bird that pays fastest. It is tempting to extend this --
# a goose pays on day 4, a cow not until day 8, and the opening is short of cash
# rather than short of patience -- but measured, every extra day of it costs:
# holding it to day 5 drops the score by two thirds. Cheap animals bought early
# are still cheap animals, and a farm that leans on geese sells nothing but eggs
# and fertilizer, which is exactly how the egg price ends at $39 and fertilizer
# at $30. Milk and wool ride their own curves; that is the point of three species.
POOR_UNTIL_DAY = 0

# Melon funds the opening: $80 of seed becomes ~$1500 on day 10. Eight tiles at a
# time, no more -- twelve measured a third worse, because early melon competes for
# exactly the labour and cash the herd is trying to grow on.
MELON_TILES = 8
MELON_LAST_DAY = 14
# Wheat tiles per animal owned. A tile yields four wheat every five days, so 1.25
# would feed the herd outright -- but a plant costs more slots than the animal it
# feeds, so cover part of the bill and buy the rest.
WHEAT_PER_ANIMAL = 0.3

# Tending capacity, in slots. A unit gets 24 actions a day and burns roughly a
# third of them walking, so ~16 useful actions: four animals (feed, care, harvest,
# collect fertilizer) or three plants plus the walking between them.
SLOTS_PER_UNIT = 18
ANIMAL_SLOTS = 3
PLANT_SLOTS = 4
# Hands are hired per day at fib(n) = 1,1,2,3,5,8,13,21,... and are refunded
# nightly, so the crew is an operating cost, not an investment: 12 hands is $143 a
# day, 16 is $2583. Cap the daily wage bill as a fraction of the bank.
HIRE_FRAC = 0.02
# ...but never below this, or a bad week compounds: a thin bank buys a thin crew,
# a thin crew cannot feed the herd, and the herd walks off.
HIRE_MIN = 25
MAX_HANDS = 16
# How many units may be sent to the shed for the same item in one turn.
MAX_CARRIERS = 4

# Per-turn sell cap and price floor, richest first -- only 10 market orders fit in
# a turn. Caps are per turn, so cap 1 still moves 24 units a day. WHEAT is missing
# on purpose: we buy it as feed and only dump the remainder on the last day.
SELL_RULES = {
    "MILK":       (2, 110),
    "WOOL":       (2, 130),
    "FERTILIZER": (3,  50),
    "MELON":      (1, 120),
    "EGG":        (99, 25),
}
# The shed holds 100 items total and silently discards the overflow at nightfall.
# Past this, floors and caps stop mattering more than the goods do.
SHED_PRESSURE = 70

CASH_FLOOR = 200
LAND_RESERVE = 800
LAND_LAST_DAY = 18
FEED_BUFFER = 4
# Days of feed money held back per animal owned, and charged on top of the price
# of every animal we are about to buy, so the herd can never outrun the feed bill
# that comes with it. Priced off the live wheat quote rather than a constant: we
# are the ones bidding it up (BUY_PRODUCT takes stock out of the market, and wheat
# rises on a sqrt curve below I0), so by day 15 a head costs $54/day to keep, not
# the $25 it did on day 0. A flat reserve looks fine right up to the day the whole
# herd walks off at once.
FEED_DAYS = 10


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
    if c["ongoing"]:
        return c["first"] + (c["max_yield"] - 1) * c["interval"]
    window_start = (c["maxday"] + 1) // 2
    return min(c["maxday"], window_start + c["max_yield"] - 2)


def _next_animal(counts, day, structure=None, stock=None):
    """Which animal the herd is most short of, among those still worth buying.

    An animal bought today must reach at least its first production, hence the
    deadline: cows stop at day 19, sheep at 20, geese at 24.

    A beast already paid for and sitting in the shed overrules all of that. It
    earns nothing in there, and the reasons not to buy one -- too late, too dear
    -- are not reasons to leave the one we own standing in a crate.
    """
    total = sum(counts.values()) + 1
    if stock:
        held = [n for n in ANIMALS if stock.get(n, 0) > 0
                and (structure is None or ANIMALS[n]["structure"] == structure)]
        if held:
            return max(held, key=lambda n: stock[n])
    best = best_score = None
    for name, a in ANIMALS.items():
        if structure is not None and a["structure"] != structure:
            continue
        if day + a["first"] + a["interval"] > LAST_DAY:
            continue
        if day <= POOR_UNTIL_DAY and name != "GOOSE":
            continue
        score = HERD[name] * total - counts[name]
        if best_score is None or score > best_score:
            best, best_score = name, score
    return best


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


def _plantable(crop, seeds, day):
    return seeds.get(crop, 0) > 0 and day + _harvest_day(crop) <= LAST_DAY


def _scan(tiles, day, hour, seeds, slots, money, stock):
    """Return (jobs, want, grown).

    Jobs are (priority, x, y, op, needs_item); lower priority runs first.
    `needs_item` means only a unit carrying that item can take the job.
    `want` is the animals the market has to buy to fill structures standing empty
    right now; `grown` counts the tiles under each crop, including ones planted
    this turn, so the market does not buy the same seed twice.
    `slots` is how much more the current crew can keep alive; new plantings and new
    structures stop there even when seeds, cash and land are all available.
    """
    jobs = []
    empty = []
    counts = {a: 0 for a in ANIMALS}
    want = {}
    grown = {}
    for y, row in enumerate(tiles):
        for x, t in enumerate(row):
            if t == "LOCKED":
                continue
            if t is None:
                empty.append((x, y))
                continue
            kind = t.get("kind")
            if kind == "PLANT":
                crop = t["crop"]
                age = day - t["planted_day"]
                grown[crop] = grown.get(crop, 0) + 1
                if not t["watered_today"]:
                    # Two dry days turns the tile into a weed, and watering inside
                    # the bonus window is where the yield actually comes from.
                    jobs.append((0, x, y, ["WATER"], None))
                elif t["yield_units"] > 0:
                    c = CROPS[crop]
                    if age >= (c["first"] if c["ongoing"] else _harvest_day(crop)):
                        jobs.append((1, x, y, ["HARVEST"], None))
            elif "animal" in t:
                # Every pending chore is offered at once, not chained behind the
                # one before it. An `elif` ladder here silently buries CARE: the
                # night refills `fertilizer_available` on every animal, so the
                # collect branch matches first, every single day, forever -- and
                # CARE is the difference between a cow giving 1 milk and 3.
                counts[t["animal"]] += 1
                if not t.get("fed_today"):
                    jobs.append((0, x, y, ["FEED"], "WHEAT"))
                if t.get("yield_units", 0) > 0:
                    jobs.append((1, x, y, ["HARVEST"], None))
                if t.get("fertilizer_available"):
                    # One action for a $100 good the town never buys, so nobody
                    # else is selling it either. Outranks caring for a goose.
                    jobs.append((2, x, y, ["COLLECT_FERTILIZER"], None))
                if not t.get("cared_today"):
                    # CARE banks +1 on the next production, and the bank is not
                    # cleared until then: a cow cared on both days between
                    # productions yields 3 milk instead of 1.
                    jobs.append((2 if t["animal"] != "GOOSE" else 3,
                                 x, y, ["CARE"], None))
            elif kind in ("COOP", "PASTURE"):
                a = _next_animal(counts, day, kind, stock)
                if a:
                    counts[a] += 1
                    want[a] = want.get(a, 0) + 1
                    stock[a] = stock.get(a, 0) - 1
                    jobs.append((1, x, y, ["PLACE", a], a))
            elif kind == "WEED":
                jobs.append((3, x, y, ["DIG"], None))

    # PLANT is validated atomically: if more units request a crop than we hold
    # seeds for, the env drops *every* PLANT for that crop. So decrement a local
    # copy of the seed counts as we queue.
    seeds = dict(seeds)
    can_plant = hour < 23  # hour 23 has no following turn in which to water
    # Only break ground on structures we could plausibly stock. A farm of 29 empty
    # coops looks like 29 units of work to the hiring rule and like a farm with no
    # room to the land rule, and it is neither -- it is just an unpaid intention.
    budget = money - CASH_FLOOR
    want_wheat = round(sum(counts.values()) * WHEAT_PER_ANIMAL)
    for (x, y) in empty:
        if (grown.get("MELON", 0) < MELON_TILES and day <= MELON_LAST_DAY
                and can_plant and slots >= PLANT_SLOTS
                and _plantable("MELON", seeds, day)):
            seeds["MELON"] -= 1
            slots -= PLANT_SLOTS
            grown["MELON"] = grown.get("MELON", 0) + 1
            jobs.append((2, x, y, ["PLANT", "MELON"], None))
            continue
        if slots >= ANIMAL_SLOTS and budget >= ANIMALS["GOOSE"]["cost"]:
            a = _next_animal(counts, day)
            if a is not None:
                budget -= ANIMALS[a]["cost"]
                slots -= ANIMAL_SLOTS
                counts[a] += 1
                jobs.append((2, x, y, BUILD[ANIMALS[a]["structure"]], None))
                continue
        # Land we cannot stock goes under wheat. Feed is the herd's only running
        # cost and we are the ones bidding it up, so a $10 seed that yields four
        # wheat is buying $200 of feed with labour we already own -- and labour is
        # what this farm has spare once the cash runs out.
        if (grown.get("WHEAT", 0) < want_wheat and can_plant
                and slots >= PLANT_SLOTS and _plantable("WHEAT", seeds, day)):
            seeds["WHEAT"] -= 1
            slots -= PLANT_SLOTS
            grown["WHEAT"] = grown.get("WHEAT", 0) + 1
            jobs.append((2, x, y, ["PLANT", "WHEAT"], None))
    return jobs, want, grown


def _fetch_jobs(tiles, invs, shed, wanted):
    """Shed runs for items the field needs but nobody is carrying.

    FEED and PLACE consume from the acting unit's own inventory, so wheat and
    livestock have to be walked out from the shed before those jobs can fire.
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
        # Spread the load over many carriers rather than loading one up. FEED and
        # PLACE can only be done by a unit holding the goods, so the number of
        # units carrying wheat *is* the number of animals that can be fed per
        # turn: one carrier hauling twelve feeds one animal a turn and the rest of
        # the herd starves next to a full shed.
        per = max(1, -(-short // MAX_CARRIERS))
        for _ in range(min(MAX_CARRIERS, -(-short // per))):
            x, y = docks[0]
            jobs.append((-1, x, y, ["PICKUP", item, per], None))
    return jobs


def _assign(units, jobs, tiles, invs):
    """Stand-and-finish first, then greedy nearest-able-unit by priority."""
    acts = [["PASS"] for _ in units]
    idle = set(range(len(units)))
    jobs.sort(key=lambda j: j[0])

    def _can(i, need):
        return need is None or (i < len(invs) and invs[i].get(need, 0) > 0)

    # Pass 1: a unit already standing on work does that work. Walking is two
    # thirds of every action this farm takes, and an animal wants four visits a
    # day -- feed, harvest, collect, care -- so finishing the tile underfoot beats
    # sending the nearest body to the loudest job and walking back tomorrow.
    at = {}
    for j in jobs:
        at.setdefault((j[1], j[2]), []).append(j)
    done = set()
    for i in range(len(units)):
        for j in at.get(tuple(units[i]), ()):
            if id(j) not in done and _can(i, j[4]):
                acts[i] = j[3]
                done.add(id(j))
                idle.discard(i)
                break

    for j in jobs:
        if not idle:
            break
        if id(j) in done:
            continue
        _prio, jx, jy, op, need = j
        able = [i for i in idle if _can(i, need)]
        if not able:
            continue
        best = min(able, key=lambda i: abs(units[i][0] - jx) + abs(units[i][1] - jy))
        ux, uy = units[best]
        acts[best] = op if (ux, uy) == (jx, jy) else _step_toward(ux, uy, jx, jy)
        idle.discard(best)

    # Nothing to do but holding produce: run it to the shed so it can be sold today
    # instead of waiting for the end-of-day drop (which discards past the cap).
    # Feed and livestock stay on the unit -- they are on their way out, not back.
    docks = _shed_tiles(tiles)
    keep = set(ANIMALS) | {"WHEAT"}
    for i in idle:
        if not docks or i >= len(invs):
            continue
        if any(n > 0 for item, n in invs[i].items() if item not in keep):
            ux, uy = units[i]
            tx, ty = min(docks, key=lambda s: abs(ux - s[0]) + abs(uy - s[1]))
            acts[i] = ["DROP"] if (ux, uy) == (tx, ty) else _step_toward(ux, uy, tx, ty)
    return acts


def _market(me, priv, obs, load, n_animals, want, carried, grown):
    day, hour = obs["day"], obs["hour"]
    money = me["money"]
    shed = priv.get("shed", {})
    prices = obs["market"]["prices"]
    orders = []
    endgame = day >= LAST_DAY
    shed_used = sum(shed.values())
    # Every animal on the farm is a standing bill: miss two days of feed and the
    # bird walks off for good. Spending down to the last dollar on livestock and
    # then having nothing left to feed it is the one way to lose this game
    # outright, so the herd's next few days of wheat are not part of the budget.
    keep = max(1, prices.get("WHEAT", 25)) * FEED_DAYS
    budget = money - CASH_FLOOR - n_animals * keep
    # Crew and feed are what the reserve is *for*, so they spend against the whole
    # bank. Gating them on the reserve deadlocks the farm: a herd it cannot afford
    # to hire for is a herd nobody carries wheat to, and it is gone in two days.
    upkeep = money - CASH_FLOOR

    # 1. Hire, before anything else can spend the cash. Hands are the cheapest
    # throughput there is, they only work for the rest of the day, and everything
    # else we might buy is worthless without crew to tend it.
    if hour <= 2 and day < LAST_DAY:
        n = me["hires_today"]
        crew_cap = -(-load // SLOTS_PER_UNIT)
        while len(orders) < 8 and n < min(MAX_HANDS, crew_cap):
            cost = _fib(n)
            if cost > max(HIRE_MIN, money * HIRE_FRAC) or cost > upkeep:
                break
            orders.append(["HIRE"])
            upkeep -= cost
            budget -= cost
            n += 1

    # 2. Sell. Drip the crash-prone goods, hold the feed wheat, dump on the last
    # day. A full shed discards its overflow at nightfall, so once it is nearly
    # full the floors stop being worth defending.
    pressure = shed_used > SHED_PRESSURE
    for item, (cap, floor) in SELL_RULES.items():
        have = shed.get(item, 0)
        if have <= 0 or len(orders) >= 9:
            continue
        if endgame:
            orders.append(["SELL", item, have])
        elif pressure:
            orders.append(["SELL", item, min(have, cap * 4)])
        elif prices.get(item, 0) >= floor:
            orders.append(["SELL", item, min(have, cap)])
    if endgame:
        if shed.get("WHEAT", 0) > 0:
            orders.append(["SELL", "WHEAT", shed["WHEAT"]])
        return orders[:10]

    # 3. Feed. An animal unfed two days running is gone for good, and the shed is
    # the only place feed can wait, so keep a day of it there plus a small buffer.
    want_wheat = min(n_animals + FEED_BUFFER, SHED_CAP - SHED_PRESSURE)
    short = want_wheat - shed.get("WHEAT", 0) - carried.get("WHEAT", 0)
    price = max(1, prices.get("WHEAT", 25))
    starving = shed.get("WHEAT", 0) + carried.get("WHEAT", 0) < n_animals
    if short > 0 and len(orders) < 10 and upkeep > price and (starving or price <= 90):
        n = min(short, 12, int(upkeep // price), SHED_CAP - shed_used)
        if n > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", n])
            budget -= n * price

    # 4. Livestock for any structure standing empty. Payback is measured in days
    # on the calendar, so the same bird is worth several times more on day 2 than
    # on day 20 -- buy every one the crew can tend, as early as the cash allows.
    for name, n_want in sorted(want.items(), key=lambda kv: ANIMALS[kv[0]]["cost"]):
        if len(orders) >= 10:
            break
        cost = ANIMALS[name]["cost"]
        room = min(n_want - shed.get(name, 0) - carried.get(name, 0),
                   SHED_CAP - shed_used)
        n = 0
        while n < room and budget >= cost + keep:
            budget -= cost + keep
            n += 1
        if n > 0:
            orders.append(["BUY_ANIMAL", name, n])

    # 5. Melon seed, for the opening only. Count the tiles already carrying a
    # melon, or the same eight seeds get bought again the turn after they are
    # planted -- $1280 of the $3000 opening, spent on nothing.
    seeds = priv.get("seeds", {})
    if (day <= MELON_LAST_DAY and len(orders) < 10
            and budget >= CROPS["MELON"]["seed"]):
        n = min(MELON_TILES - grown.get("MELON", 0) - seeds.get("MELON", 0),
                int(budget // CROPS["MELON"]["seed"]))
        if n > 0:
            orders.append(["BUY_SEED", "MELON", n])
            budget -= n * CROPS["MELON"]["seed"]

    # Feed wheat. Seed is $10 against a market price north of $50 a head per day,
    # so this is the cheapest cash on the board -- it comes out of upkeep, not the
    # investment budget, for the same reason the feed itself does.
    n_wheat = round(n_animals * WHEAT_PER_ANIMAL) - grown.get("WHEAT", 0)
    if (len(orders) < 10 and n_wheat > seeds.get("WHEAT", 0)
            and day + _harvest_day("WHEAT") <= LAST_DAY):
        n = min(n_wheat - seeds.get("WHEAT", 0),
                int(max(0, upkeep) // CROPS["WHEAT"]["seed"]))
        if n > 0:
            orders.append(["BUY_SEED", "WHEAT", n])
            budget -= n * CROPS["WHEAT"]["seed"]

    # 6. Expand, last, out of what the herd did not want. $1000 for 25 tiles that
    # each carry an animal earning ~$200 a day is the best trade on the board, and
    # since livestock is bought first, money still here is money the farm has no
    # room for. The only real limit is the crew: land nobody can tend is a weed
    # patch.
    n_extra = len(me["unlocked_quadrants"]) - 1
    if (len(orders) < 10 and n_extra < len(LAND_PRICES) and day <= LAND_LAST_DAY
            and load < (MAX_HANDS + 1) * SLOTS_PER_UNIT
            and budget >= LAND_PRICES[n_extra] + LAND_RESERVE):
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
    n_plants = n_animals = n_struct = n_empty_tiles = 0
    for row in tiles:
        for t in row:
            if t is None:
                n_empty_tiles += 1
            elif not isinstance(t, dict):
                continue
            elif t.get("kind") == "PLANT":
                n_plants += 1
            elif "animal" in t:
                n_animals += 1
            elif t.get("kind") in ("COOP", "PASTURE"):
                n_struct += 1
    slots = max(0, crew * SLOTS_PER_UNIT
                - n_plants * PLANT_SLOTS - n_animals * ANIMAL_SLOTS)
    # What the crew will have to cover once the empty structures and bare tiles
    # are stocked -- an empty coop is a day away from being work, and hiring one
    # day at a time is how the farm ends up with one hand and a dead herd.
    load = (n_plants * PLANT_SLOTS
            + (n_animals + n_struct + n_empty_tiles) * ANIMAL_SLOTS)

    carried = {}
    for inv in invs:
        for item, n in inv.items():
            carried[item] = carried.get(item, 0) + n
    shed = priv.get("shed", {})
    stock = {a: shed.get(a, 0) + carried.get(a, 0) for a in ANIMALS}

    jobs, want, grown = _scan(tiles, obs["day"], obs["hour"],
                              priv.get("seeds", {}), slots, me["money"], stock)
    fetch = dict(want)
    fetch["WHEAT"] = n_animals
    jobs += _fetch_jobs(tiles, invs, shed, fetch)

    acts = _assign(units, jobs, tiles, invs)
    market = _market(me, priv, obs, load, n_animals, want, carried, grown)

    return {"farmer": acts[0], "hands": acts[1:], "market": market}
