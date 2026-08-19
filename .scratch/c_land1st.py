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

# `last` is the last day it is worth *buying* one. For cow and sheep that is just
# the deadline to reach one production (LAST_DAY - first - interval). A goose
# clears that on day 24 and still loses money: it yields one egg a day from
# day+4 at ~$45 while eating one wheat a day from the moment it lands, and by
# then wheat quotes $50+, so the $300 never comes back. Its real deadline is the
# day the feed bill overtakes the egg -- measured at ~20, not 24.
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first": 4, "interval": 1, "last": 20},
    "COW":   {"cost": 400, "structure": "PASTURE", "first": 8, "interval": 2, "last": 19},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first": 6, "interval": 3, "last": 20},
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
# The opening rush. Measured on the baseline: the herd sits at 3-4 head from day 2
# to day 11 while every farm above $120k runs 12 by day 8. Two separate throttles
# hold it there and neither moves without the other. Days 0-1 it is the
# one-head-at-a-time pipeline plus `slots` (cash is fine -- $1,584 unspent at
# nightfall on day 0). Days 2-10 it is purely cash: `budget` is *negative* every
# one of those days, because ten days of feed money for four animals is $1,280
# against a bank of $1,300.
# Inside the window the herd may grow in parallel and ignore `slots`, because an
# empty structure already counts in `load` and the crew catches up next turn.
HERD_RUSH_DAY = 8
# ... but not without a ceiling. Unbounded, the rush paves all 25 opening tiles
# with pasture, never reaches the $1,000 land purchase, and the berry farm falls
# to 8 tiles: milk and wool +$16,492, strawberry -$27,914. Eight is where the two
# stop fighting -- screened at 6/8/10/12, mirror +6,245/+12,910/+9,843/lower, and
# only 8 keeps full berry revenue while milk rises.
HERD_RUSH_SIZE = 8
# ...and the first four head of it are sheep. See `_next_animal`.
RUSH_SHEEP = 4
# Days up to here take only the bird that pays fastest. Off (-1), and it has to
# be off for the rush. The rule was written for a pipeline that bought one head
# every two days, where the first head should obviously be the one that pays on
# day 4; the rush buys the whole opening herd on day 0, and gating that day to
# geese fills eight of sixteen slots with them -- $16,896 of egg, the dump
# product, in place of milk and wool (milk 23,835 against 36,956 with this off).
# The old warning stands for what it was about: *delaying* cow and sheep past
# day 0 cost two thirds of the score. Buying them on day 0 is the opposite.
POOR_UNTIL_DAY = -1

# Melon funds the opening: $80 of seed becomes ~$1500 on day 10. Eight tiles at a
# time, no more -- twelve measured a third worse, because early melon competes for
# exactly the labour and cash the herd is trying to grow on.
MELON_TILES = 8
MELON_LAST_DAY = 14
# Four of the eight shops list STRAWBERRY (ICE_CREAM, SMOOTHIE, BRUNCH,
# FARMERS_MARKET) against one for WOOL and none for MELON, so the town drains
# ~500-600 units a season and the price ends at $217-311 against a $120 base in
# every replay -- including ones where nobody grew it. Every opponent above $120k
# plays the same farm: 36-42 berry tiles planted day 7-12 beside a herd the same
# size as ours. Reconstructing wenjinyang's $175,862 against our $69,326 in the
# same episode, their milk, wool and fertilizer are roughly equal to ours; the
# whole gap is a product we have never sold one unit of.
BERRY_TILES = 40
BERRY_FIRST_DAY = 6
# Wheat tiles per animal owned. A tile yields four wheat every five days, so 1.25
# would feed the herd outright -- but a plant costs more slots than the animal it
# feeds, so cover part of the bill and buy the rest.
WHEAT_PER_ANIMAL = 0.75
ENDGAME_WHEAT_TILES = 10

# Tending capacity, in slots. A unit gets 24 actions a day but also spends time
# walking and hauling feed, so it can reliably cover two animals or four plants.
SLOTS_PER_UNIT = 18
# Replays show that one unit can reliably service about two animals once walking,
# shed runs, and the four daily chores are included. The old value (3) planned
# for six animals per unit and bought replacements as the excess herd escaped.
ANIMAL_SLOTS = 9
# Two numbers that used to be one. `PLANT_SLOTS` is how much of the crew a tile
# consumes; `PLANT_LOAD` is how much hiring demand it creates. Sharing one value
# meant lowering it to make room for crops also halved the crew that tends them:
# 7 hands against 11, and 16 of 40 berry seeds bought and never planted. The
# field settles the capacity number -- the leaders keep 14 animals and 54 plants
# on 11 hands, which is 2 slots a plant, not 4.
PLANT_SLOTS = 2
PLANT_LOAD = 4
# Hands are hired per day at fib(n) = 1,1,2,3,5,8,13,21,... and are refunded
# nightly, so the crew is an operating cost, not an investment: 12 hands is $376 a
# day, 16 is $2583 -- hands 13-16 are 85% of that bill for 25% of the crew.
# A hand-day is worth roughly what a hand-day is worth, all season; it does not
# get more valuable because the bank is fuller. Tying the wage ceiling to the bank
# (the old `max(25, money * 0.02)`) therefore bought the exponential tail of the
# curve exactly when it had fewest days left to pay back: measured $21,101 of wages
# on a seed where the whole herd's extra milk and wool came to $16,745.
# Re-screened on v12. The pair matching cut movement 4,399 -> 3,885 on seed 6 but
# turned the saving into idleness, not work: PASS 621 -> 1,013 while productive
# actions rose only 2,293 -> 2,411. A farm with a thousand idle unit-turns is
# paying the exponential tail of the hire curve for hands that stand still, and
# it cuts a cost rather than supply - verified rather than assumed, since fewer
# hands could also mean fewer goods: on seed 6 revenue moves $140,463 -> $139,826
# (-0.5%) while hire orders fall 290 -> 275, so the mirror's +$1,406.7 is wages
# saved and not the mutual-restraint artefact that inflated the land gate.
# The effect is ~1.2% of a game against +-$4,000 of seed variance, which is why
# it reads 9/16 head-to-head: small and real, not large and lucky. The 144 came
# from a three-point screen on v9, before berries and before pair matching.
HIRE_MAX_WAGE = 89
MAX_HANDS = 16
# How many units may be sent to the shed for the same item in one turn.
MAX_CARRIERS = 8

# Per-turn sell cap and price floor, richest first -- only 10 market orders fit in
# a turn. Caps are per turn, so cap 1 still moves 24 units a day. WHEAT is missing
# on purpose: we buy it as feed and only dump the remainder on the last day.
SELL_RULES = {
    "STRAWBERRY": (2, 100),
    "MILK":       (2, 110),
    "WOOL":       (2, 130),
    # Fertilizer is the one good we glut: ~292 units a game against milk's 135,
    # and no shop drains it, so its price falls all season and ends near $1. A
    # floor is a bet on recovery, and there is none to wait for -- it just parked
    # 45-53 units in the shed from day 20 and sold them on the last day at the
    # bottom, while filling half the shed and tipping the rest of the farm into
    # pressure dumping. Keep collecting it (removing that lost 8/8, -$8,435) and
    # sell it as it arrives instead.
    "FERTILIZER": (3,   5),
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
# Inside the rush the reserve is cut to three days. It insures against a cash
# drought that cannot happen there: a head bought before day 8 drops a fertilizer
# every night worth $90-100 while the market is still near its $100 base, against
# ~$30 of wheat, so it repays its own feed from day one and its purchase price
# inside a week. Ten days of it is the throttle, not the insurance.
FEED_DAYS_EARLY = 3


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

    An animal bought today must earn back its cost and its feed, hence the
    per-species `last` day above.

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
    # The opening buys sheep before cows, whatever the target mix says. Days 2-10
    # are the farm's cash desert -- the bank sits at $200-1,500 and `budget` is
    # negative on most of them, so the herd freezes at 5-6 head until the melon
    # harvest lands on day 9. What breaks that is the first product to reach the
    # market: a sheep placed on day 0 produces on day 6, a cow not until day 8,
    # and 3 cared wools at $200 is $600 two days before the first $480 of milk.
    # Suda's $165,925 opens with exactly this -- four sheep and one cow on day 0,
    # then six cows on days 7-9 out of the day-6 wool, reaching twelve head by
    # day 9 against our six. Four is the number, and it is narrow: three screened
    # at -$12,447 of mirror mean and five at -$13,018, because a fifth $500 sheep
    # is the melon seed and the first cow. The target mix is untouched -- this
    # only reorders the opening, so nothing extra reaches the market.
    if (day <= HERD_RUSH_DAY and counts.get("SHEEP", 0) < RUSH_SHEEP
            and structure in (None, "PASTURE")):
        return "SHEEP"
    best = best_score = None
    for name, a in ANIMALS.items():
        if structure is not None and a["structure"] != structure:
            continue
        if day > a["last"]:
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


def _wheat_target(n_animals, day):
    return max(round(n_animals * WHEAT_PER_ANIMAL),
               ENDGAME_WHEAT_TILES if day >= 20 else 0)


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
                c = CROPS[crop]
                bonus_window = not c["ongoing"] and age >= (c["maxday"] + 1) // 2
                # The nightly refresh counts days_since_first from *tomorrow*
                # (`next_day - planted_day - first`), so a strawberry planted on
                # day 0 produces on the nights of days 9, 11, 13 and 15, not 10,
                # 12, 14, 16. It also stops after `max_yield` productions and
                # marks the tile for decay, so a later visit buys nothing.
                since = age + 1 - c["first"]
                production_day = (c["ongoing"] and since >= 0
                                  and since % c["interval"] == 0
                                  and since // c["interval"] < c["max_yield"])
                # Fertilizer doubles what a watering adds and lasts three days --
                # exactly wheat's window (age 2,3,4) -- so one action takes the
                # tile from 4 units to its cap of 6. Wheat is the only crop with
                # headroom; melon already waters 7 times into a cap of 6. Selling
                # it instead is the losing side of the trade: nothing drains the
                # fertilizer market so it only falls, while five shops drain wheat
                # so feed only climbs. Priority 0 despite forgoing a bonus rather
                # than preventing a loss -- the yield is credited by the waterings
                # inside the window, so a late fertilize is pure walking (measured
                # 2/8 at priority 1, 1/8 at priority 2, against 14/16 here).
                # An ongoing crop takes the same trade on its production night:
                # the refresh adds +2 instead of +1 when the tile is watered and
                # fertilized, and `fertilized_until_day = day + 2` is exactly
                # strawberry's interval, so one action covers two productions and
                # a 4-unit tile yields 8.
                fertilize = (production_day if c["ongoing"] else
                             crop == "WHEAT" and bonus_window and age <= c["maxday"])
                if fertilize and t.get("fertilized_until_day", -1) < day:
                    jobs.append((0, x, y, ["FERTILIZE"], "FERTILIZER"))
                if (not t["watered_today"]
                        and (t.get("consecutive_unwatered", 0) > 0
                             or bonus_window or production_day)):
                    # Two dry days turns the tile into a weed, and watering inside
                    # the bonus window is where the yield actually comes from.
                    jobs.append((0, x, y, ["WATER"], None))
                elif t["yield_units"] > 0:
                    if age >= (c["first"] if c["ongoing"] else _harvest_day(crop)):
                        jobs.append((1, x, y, ["HARVEST"], None))
            elif "animal" in t:
                # Every pending chore is offered at once, not chained behind the
                # one before it. An `elif` ladder here silently buries CARE: the
                # night refills `fertilizer_available` on every animal, so the
                # collect branch matches first, every single day, forever -- and
                # CARE is the difference between a cow giving 1 milk and 3.
                counts[t["animal"]] += 1
                if day < LAST_DAY and not t.get("fed_today"):
                    # Ahead of watering, for the same reason PLACE is. Only a unit
                    # already carrying wheat can feed, so a wheat carrier handed a
                    # water job on the way to the pasture strands the whole load:
                    # measured 10 of 18 head walking off a berry farm because 40
                    # crop tiles kept out-bidding the herd for the same carriers.
                    jobs.append((-1, x, y, ["FEED"], "WHEAT"))
                if t.get("yield_units", 0) > 0:
                    jobs.append((1, x, y, ["HARVEST"], None))
                if t.get("fertilizer_available"):
                    # One action for a $100 good the town never buys, so nobody
                    # else is selling it either. Outranks caring for a goose.
                    jobs.append((2, x, y, ["COLLECT_FERTILIZER"], None))
                if day < LAST_DAY and not t.get("cared_today"):
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
                    # Ahead of everything. The farm grows one head at a time, so
                    # an animal still riding around in someone's pack stops the
                    # next structure being built *and* the next beast bought:
                    # measured 288 consecutive turns blocked on `want pending`,
                    # days 14-25, because the carrier kept being handed water
                    # jobs at priority 0 and never reached the pasture.
                    jobs.append((-1, x, y, ["PLACE", a], a))
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
    want_wheat = _wheat_target(sum(counts.values()), day)
    docks = _shed_tiles(tiles)
    if docks:
        empty.sort(key=lambda p: min(abs(p[0] - x) + abs(p[1] - y)
                                    for x, y in docks))
    for (x, y) in empty:
        if (grown.get("MELON", 0) < MELON_TILES and day <= MELON_LAST_DAY
                and can_plant and slots >= PLANT_SLOTS
                and _plantable("MELON", seeds, day)):
            seeds["MELON"] -= 1
            slots -= PLANT_SLOTS
            grown["MELON"] = grown.get("MELON", 0) + 1
            jobs.append((2, x, y, ["PLANT", "MELON"], None))
            continue
        # The opening herd in a rush, then one head at a time. After the window
        # an empty structure is already the next animal in the pipeline, and
        # building dozens more only creates walking jobs and a misleading hiring
        # load -- but inside it, that caution is what leaves the farm on four
        # head at day 11 against a field that runs twelve from day 8.
        rush = day <= HERD_RUSH_DAY and sum(counts.values()) < HERD_RUSH_SIZE
        if rush or (not want and slots >= ANIMAL_SLOTS):
            # `stock` first: a structure is free, so an animal already paid for
            # and standing in the shed must never wait on the bank. Without this
            # the farm can deadlock outright -- six geese in the crate and a
            # budget too thin to authorise the $0 coop that would let them out.
            a = _next_animal(counts, day, stock=stock)
            if a is not None and (stock.get(a, 0) > 0
                                  or budget >= ANIMALS[a]["cost"]):
                if stock.get(a, 0) > 0:
                    stock[a] -= 1
                else:
                    budget -= ANIMALS[a]["cost"]
                slots -= ANIMAL_SLOTS
                counts[a] += 1
                want[a] = want.get(a, 0) + 1
                jobs.append((2, x, y, BUILD[ANIMALS[a]["structure"]], None))
                continue
        # Berries, once melon and the herd pipeline have had their pick of the
        # tile. They are the town's most-drained good and the only crop with a
        # season-long price above its base, but the seed is $100 against wheat's
        # $10, so they go in after the opening has paid for itself.
        if (grown.get("STRAWBERRY", 0) < BERRY_TILES and day >= BERRY_FIRST_DAY
                and can_plant and slots >= PLANT_SLOTS
                and _plantable("STRAWBERRY", seeds, day)):
            seeds["STRAWBERRY"] -= 1
            slots -= PLANT_SLOTS
            grown["STRAWBERRY"] = grown.get("STRAWBERRY", 0) + 1
            jobs.append((2, x, y, ["PLANT", "STRAWBERRY"], None))
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

    # Pass 2: inside one priority band, take the globally closest (unit, job)
    # pairs first. Walking the band in scan order lets a tile on the far edge
    # claim the nearest body and shove the unit already standing beside the next
    # job across the map. Measured against the field leader in episode 92507094:
    # 1.86 moves per productive action here against 0.82 there, on a farm that is
    # *more* compact than theirs (mean 3.15 tiles from a dock against 4.01), so
    # the walking is the dispatcher's, not the layout's. Priority order is
    # untouched: a band is only entered once the band above it has taken every
    # unit it can use.
    lo = 0
    while lo < len(jobs) and idle:
        hi = lo
        while hi < len(jobs) and jobs[hi][0] == jobs[lo][0]:
            hi += 1
        band = [j for j in jobs[lo:hi] if id(j) not in done]
        lo = hi
        while idle and band:
            pick = None
            for j in band:
                for i in idle:
                    if not _can(i, j[4]):
                        continue
                    d = abs(units[i][0] - j[1]) + abs(units[i][1] - j[2])
                    if pick is None or d < pick[0]:
                        pick = (d, j, i)
            if pick is None:
                break
            _d, j, i = pick
            ux, uy = units[i]
            acts[i] = j[3] if (ux, uy) == (j[1], j[2]) else _step_toward(ux, uy, j[1], j[2])
            idle.discard(i)
            band.remove(j)

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
    keep = max(1, prices.get("WHEAT", 25)) * (
        FEED_DAYS_EARLY if day <= HERD_RUSH_DAY else FEED_DAYS)
    budget = money - CASH_FLOOR - n_animals * keep
    # Crew and feed are what the reserve is *for*, so they spend against the whole
    # bank. Gating them on the reserve deadlocks the farm: a herd it cannot afford
    # to hire for is a herd nobody carries wheat to, and it is gone in two days.
    upkeep = money - CASH_FLOOR

    # 1. Hire, before anything else can spend the cash. Hands are the cheapest
    # throughput there is, they only work for the rest of the day, and everything
    # else we might buy is worthless without crew to tend it.
    if hour <= 2 and day <= LAST_DAY:
        n = me["hires_today"]
        crew_cap = -(-load // SLOTS_PER_UNIT)
        while len(orders) < 8 and n < min(MAX_HANDS, crew_cap):
            cost = _fib(n)
            if cost > HIRE_MAX_WAGE or cost > upkeep:
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
    if not endgame and len(orders) < 9:
        surplus = shed.get("WHEAT", 0) - n_animals - FEED_BUFFER
        if surplus > 0 and prices.get("WHEAT", 0) >= 20:
            orders.append(["SELL", "WHEAT", min(surplus, 12)])
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

    # Land before seed: a seed with no tile to go on is dead capital, and land is
    # what makes the tile. Measured on the baseline, days 7-9 hold 31-34 unplanted
    # strawberry seeds ($3,400) on a farm with zero bare tiles, while the third
    # quadrant -- the thing that actually ends the stall -- waits on the same cash.
    n_extra = len(me["unlocked_quadrants"]) - 1
    if (len(orders) < 10 and n_extra < len(LAND_PRICES) and day <= LAND_LAST_DAY
            and load < (MAX_HANDS + 1) * SLOTS_PER_UNIT
            and budget >= LAND_PRICES[n_extra] + LAND_RESERVE):
        orders.append(["BUY_LAND"])
        budget -= LAND_PRICES[n_extra]

    # Berry seed, out of what the herd did not want -- $4,000 for the ~$80k of
    # strawberry revenue that separates this farm from the top of the field.
    if (day >= BERRY_FIRST_DAY and len(orders) < 10
            and day + _harvest_day("STRAWBERRY") <= LAST_DAY):
        n = min(BERRY_TILES - grown.get("STRAWBERRY", 0) - seeds.get("STRAWBERRY", 0),
                int(max(0, budget) // CROPS["STRAWBERRY"]["seed"]))
        if n > 0:
            orders.append(["BUY_SEED", "STRAWBERRY", n])
            budget -= n * CROPS["STRAWBERRY"]["seed"]

    # Feed wheat. Seed is $10 against a market price north of $50 a head per day,
    # so this is the cheapest cash on the board -- it comes out of upkeep, not the
    # investment budget, for the same reason the feed itself does.
    n_wheat = _wheat_target(n_animals, day) - grown.get("WHEAT", 0)
    if (len(orders) < 10 and n_wheat > seeds.get("WHEAT", 0)
            and day + _harvest_day("WHEAT") <= LAST_DAY):
        n = min(n_wheat - seeds.get("WHEAT", 0),
                int(max(0, upkeep) // CROPS["WHEAT"]["seed"]))
        if n > 0:
            orders.append(["BUY_SEED", "WHEAT", n])
            budget -= n * CROPS["WHEAT"]["seed"]

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
    # Empty structures are work already committed; untouched land is not.
    load = (n_plants * PLANT_LOAD + (n_animals + n_struct) * ANIMAL_SLOTS)
    # Hire one unit ahead of the current workload so the farm can grow without
    # paying a crew for every untouched square of unlocked land.
    if n_empty_tiles and obs["day"] < LAST_DAY:
        load += SLOTS_PER_UNIT

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
