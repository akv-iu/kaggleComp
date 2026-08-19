
## 2026-08-17 (v14 baseline, submission 55507562, rating 846.0 IMPROVED) — the queued fetch hypothesis answered no, and the mirror's fourth blind spot: the opponent's policy is worth ±$4,500

### State at the start of the run

`main.py` and `test_agent.py` byte-identical to `.automation/baseline_main.py` and
`.automation/baseline_test_agent.py` (v14: sheep-first opening rush, 40 berry
tiles, closest-pair dispatch, `HIRE_MAX_WAGE = 89`). Submission 55507562 read
**846.0, up from 839.8, IMPROVED**. Field record over the whole index **160-159 in
319 games**; over v14's own 77 games **36-41**, our mean $87,563 against the
field's $93,191, our best game $138,163 against the field's $175,862.

### The measurement the run started from

`.scratch/crops.py` audits every crop's whole lifecycle on a baseline mirror.
Seed 0, `townCenterSellInterval: 24`, per farm:

- **MELON 12 plantings -> 12 harvests -> 72 units = 6.0 a tile, exactly the cap.**
- **WHEAT 38 plantings -> 36 harvests -> 216 units = 6.0 a tile, exactly the
  fertilized cap.**
- **STRAWBERRY 34 plantings -> 133 harvests -> 233 units = 6.85 a tile** against a
  ceiling of 8 (four productions of +2).
- Deaths: **1 wheat tile to thirst, 0 strawberry, 0 melon**; the 30 strawberry
  "decay" deaths are spent tiles that have already given their fourth production.
- Action histogram: WATER 551, PICKUP 462, COLLECT_FERTILIZER 305, CARE 302,
  FEED 298, HARVEST 282, FERTILIZE 93, PLANT 84, DROP 63, DIG 33, PLACE 14,
  BUILD 14; PASS 714; moves 3,742.

**There is no execution leak left anywhere in the crop engine.** Two of the three
crops run at their exact yield cap and the third at 86% of a ceiling whose last
14% is the fertilize-contention leak the ledger has already refused five times.

### The arithmetic that framed every hypothesis: marginal, not average, revenue

Every per-action valuation in this ledger has been computed at the *average* price
a product realises. That is the wrong price for a decision about one more unit,
because we are a large fraction of our own market. Differentiating `market_price`
at our own volume at interval 24 (own units sold in brackets):

| product | price | d(price)/d(unit) | marginal revenue |
|---|---|---|---|
| MILK (sqrt, amp 8.69) | $235 | $0.51 | **$159** (150u) |
| STRAWBERRY (sqrt, amp 8.4) | $210 | $0.39 | **$99** (233u) |
| MELON (sq, amp 0.01) | $189 | $1.56 | **$77** (72u) |
| WHEAT (sqrt, amp 1.0, depth 797) | $53 | **$0.018** | **$50** (flat) |
| EGG (linear, amp 0.06) | $60 | $0.06 | $58 |
| FERTILIZER (linear, amp 0.2) | $27 | $0.20 | **-$12** (197u) |
| WOOL (sq, amp 0.058, 38 above I0) | $116 | **$4.40** | **strongly negative** |

Per action, at marginal revenue: **wheat $41, strawberry $44, melon $46, a cow
$42, a sheep ~$0.** Every activity on this farm returns $41-46 an action once the
price impact of its own output is charged to it, and the one outlier is the sheep.
**That is what an interior optimum looks like**, and it is the reason twenty-five
constant experiments have moved nothing: the constants are already at the point
where the margins are equal. It also re-derives, from the price curves alone, the
whole `townCenterSellInterval` story — at interval 12 wool is 56 units *below* I0
on a `log` curve (amp 8.58, d = $0.15/unit) and its marginal unit is worth **$214**,
the best on the farm; at 24 it is 38 units *above* I0 on a `sq` curve and worth
less than nothing. Nothing about the sheep changed; the side of `I0` did.

### Attempt 1 (screened, rejected) — exempt the berry seed from the herd's feed reserve

**Exact change:** in `_market`, the `BUY_SEED STRAWBERRY` quantity is sized off
`max(budget, money - CASH_FLOOR - n_animals * wheat_price * FEED_DAYS_EARLY)`
instead of off `budget`. Nothing else moves; animals, land and wheat seed keep the
full ten-day reserve.

**Pre-test reasoning:** the field reaches **34 of its 40-tile target** (measured
above). The ledger traces the cause exactly: `budget = money - CASH_FLOOR -
n_animals * keep` with `keep` the live wheat quote times `FEED_DAYS`, which at day
12 with 10 head and wheat at $35 holds back **$3,500 — thirty-five berry seeds —
on the days the field stalls**. `FEED_DAYS = 6` and `= 3` were both screened and
lost, but those release the reserve for *animals and land as well*, which is the
failure the earlier entry diagnoses ("capital into a herd the farm cannot feed
through the day-15 wheat squeeze"). Releasing it for a $100 seed and nothing else
is the untried half of a named channel, and it buys tiles *earlier* rather than
raising the target, so it is not the `BERRY_TILES = 48` experiment.

**Evidence (12 seeds, 24 games a cell; baseline 129,416.8 at interval 12 and
104,737.5 at 24):** interval 12 **129,416.8 — bit-identical to baseline on all
twelve seeds.** Interval 24 **106,149.3 (+$1,412)**, and identical on nine of
twelve seeds; the whole gain is seeds 7 (+$3,179) and 8 (+$13,764).

**Why it failed:** the reserve is a **dead constant at the benchmark's demand**.
At interval 12 the farm is rich enough (mirror mean $129k against $105k) that
`budget` already exceeds the seed price on every turn a berry job is live, so the
exemption never fires — the third dead constant found this way, after
`BERRY_FIRST_DAY` and `ENDGAME_WHEAT_TILES`. A candidate that is bit-identical on
twelve seeds of twelve cannot win a single head-to-head game, so this is
unshippable regardless of its merit at interval 24. **Check a constant is live at
*both* intervals before spending anything on it; "live at 24" and "live at 12" are
different questions.**

**Test again only with:** a gate at the competition's demand. The +$1,412 at
interval 24 is 0.6 SE and rests on two seeds.

### Attempt 2 (screened, rejected) — drain the shed into the carriers at dawn

**Exact change:** `fetch["WHEAT"] = n_animals + FETCH_SLACK` with
`FETCH_SLACK = 8`.

**Pre-test reasoning:** the ledger's four feed-logistics refusals are *monotone in
the size of the distribution buffer* — every repair that cut carriers, loads or
demand lost, and the least bad was the one with the biggest buffer. Nobody had
tried the direction monotonicity actually points. Because `short = min(need -
carried, shed)`, raising `need` above the shed's whole stock makes the dawn run
empty the shed in one pass, after which `short` stays at 0 until the market
restocks — the top-up churn disappears *without* cutting the carrier count, and
total wheat in the system is unchanged, since `_market` still sizes purchases off
`want_wheat = n_animals + FEED_BUFFER` over shed **plus** carried.

**Evidence:** **101,040.6 (-$3,697) at interval 24 and 120,090.8 (-$9,326) at 12.**

**Why it failed:** `per = max(1, ceil(short / MAX_CARRIERS))`, so a larger `short`
buys a *bigger load on fewer backs*: 17 units become 6 carriers of 3 where the
baseline sends 7 carriers of 2. Parallel delivery capacity is the carrier count,
not the unit count, and this trades it away — the same wall as `PICKUP_LOAD = 3`,
reached from the opposite side.

### Attempt 3 (screened, rejected) — the queued hypothesis: fetch demand in loaded carriers

**Exact change:** exactly the form this ledger queued on 2026-08-17. In
`_fetch_jobs`, for WHEAT only, `carried` counts *units holding at least one wheat*
rather than total wheat carried, and `need` is `min(n_animals, MAX_CARRIERS)`.

**Pre-test reasoning:** as filed — preserve parallel delivery capacity exactly
while refusing to re-fetch for a carrier that is already loaded. Predicted PICKUP
falling toward 300 with FEED and the holder count flat.

**Evidence:** **104,325.6 (-$412) at interval 24 and 123,447.8 (-$5,969) at 12**,
12 seeds a cell. The instrumented seed-0 game: **PICKUP 462 -> 678**, FEED 298 ->
295, WATER 551 -> 555, CARE 302 -> 300, PASS 714 -> 649.

**Why it failed, and this closes the family.** The mechanism ran **backwards**:
pickups rose 47%. Counting demand in carriers forces `short <= MAX_CARRIERS = 8`,
which forces `per = ceil(8/8) = 1`, and a carrier holding one wheat can serve
exactly **one** FEED before it needs another trip. The baseline's unit-denominated
demand is what produces `per = 2` on the dawn run and lets a carrier feed twice.
**The top-up churn is not waste sitting beside the load size — it *is* the load
size.** `short = n_animals - units_carried` is simultaneously the demand signal
and the batch-size signal, and every repair that touches one damages the other.
That is now the single mechanism behind all six refusals in this family (fewer
carriers, `per = 1`, bigger loads, unfed-count demand, dock choice, and this),
and it is why the 3:1 PICKUP gap against the field leaders is not reclaimable
inside this dispatcher. **Do not queue a seventh.**

### Attempt 4 (screened, rejected) — offer HARVEST beside WATER instead of behind it

**Exact change:** in `_scan`'s plant branch, `elif t["yield_units"] > 0:` becomes
`if t["yield_units"] > 0:`, so a tile that needs watering *and* holds units offers
both jobs in the same turn.

**Pre-test reasoning:** the animal branch carries a comment saying an `elif` ladder
there "silently buries CARE", and it was a real bug when it existed. The plant
branch still has exactly that shape: on a strawberry production morning the tile
holds last night's units and also wants today's water, and only WATER is offered.
Strawberry's hold cap is `max_yield = 4` and two fertilized productions fill it, so
a harvest deferred twice is a whole production lost.

**Evidence:** **107,369.2 (+$2,632) at interval 24 and 122,485.1 (-$6,932) at 12.**

**Why it failed:** the `elif` is load-bearing and the animal analogy does not
transfer. HARVEST is priority **1** and CARE is priority **2**, so every extra
harvest job offered outbids a CARE — and CARE triples the next production of a
$223 cow. The animal branch could afford parallel offers because its chores sit at
-1, 1, 2 and 2 and do not stack inside one band. -$6,932 at interval 12 is ~2.9 SE:
this is a real loss, not noise, and the +$2,632 at 24 is 1.1 SE and worthless. The
audit above also shows there was nothing to fix — 0 thirst deaths, 0 clipped
strawberry, 6.85 units a tile.

### Attempt 5 (screened, rejected) — `SLOTS_PER_UNIT`, the last unscreened capacity constant

**Exact change:** `SLOTS_PER_UNIT` 18 -> 20 and -> 16. It is the only capacity
number never screened; `PLANT_SLOTS`, `ANIMAL_SLOTS` and `HIRE_MAX_WAGE` have each
been screened alone, but `SLOTS_PER_UNIT` moves the tile budget and `crew_cap =
ceil(load / SLOTS_PER_UNIT)` in *opposite* directions and is therefore a different
point in the space, not a rescaling.

**Evidence:** 20: **99,843.9 (-$4,894) at 24 and 121,658.5 (-$7,758) at 12.**
16: **99,695.5 (-$5,042) / 122,901.2 (-$6,516).**

**Why it failed:** two-sided and about $5,000-$7,800 down in all four cells. Like
`PLANT_SLOTS = 2`, this is a measured peak rather than a modelling convenience.
Together the two constants say the capacity model is not approximately right, it is
*sharply* right, which is the same conclusion the marginal-revenue table reaches
from the price side.

### The run's real finding — the mirror has a fourth blind spot, and it is the biggest

The ledger names two blind spots (racing, mutual restraint) and one benchmark
distortion (`townCenterSellInterval`). All three are about *what the mirror does to
a change*. There is a fourth, about what the mirror does to the **baseline**: it
scores our agent against exactly one opponent policy, its own, and our absolute
score is a strong function of which policy the opponent runs.

Measured with `.scratch/vs.py` — our unmodified agent in both seats against three
opponents, the *same six seeds*, `townCenterSellInterval: 24`:

| opponent | our mean | their mean |
|---|---|---|
| a copy of ourselves (the mirror) | **99,419** | 99,419 |
| all-feed-buyer (`WHEAT_PER_ANIMAL = 0`) | **103,902 (+$4,483)** | 98,297 |
| herd-only (`BERRY_TILES = 0`, 16-head rush, no geese) | **95,332 (-$4,087)** | 71,653 |

**Our own score swings $8,570 — 8.6% — on identical seeds, with our own code
unchanged, purely on the opponent's policy.** And the swing is not bounded by that
average: on seed 5 the same two farms that score 90,153 and 91,445 in a mirror
score **65,891 and 69,377** against the herd-only opponent. That is a $24,000
per-game swing caused by nothing we do.

**This is the missing explanation for the field record.** Our 24-seed mirror at
interval 24 runs **84,071 to 132,076, mean 108,189, with no low tail at all**,
while v14's 77 real games run **$22,240 to $138,163, mean $87,563, with thirteen
games under $62,000 — and we lose twelve of those thirteen.** Self-play cannot
produce that tail because self-play contains one opponent. The direction is also
counter-intuitive and worth keeping: we score *better* against the farm that bids
our feed price up and *worse* against the farm that abandons strawberry to us,
because the herd-only farm floods milk and wool, which is where our own herd's
revenue lives. **What the opponent competes with us for matters more than what
they leave us.**

### Outcome

`main.py` and `test_agent.py` are byte-identical to their pre-run snapshots
(`diff` clean against both `.automation` baselines); every candidate lived in
`.scratch/cand_*.py` and was screened through `.scratch/screen.py`, which loads an
arbitrary path. `py_compile` passes on both files and `test_agent.py` passes
("unit checks ok", episode me=169467). `verify.py` and `loop.py` untouched. Five
distinct hypotheses were screened at both `townCenterSellInterval` values, 24
games a cell; **all five are negative or exactly tied at interval 12, which is the
configuration the gate runs at**, so none justified spending a full benchmark.
**No `.automation/submit_request.json` was written.**

### Best distinct next hypothesis

**Select on a panel of opponents, not on a mirror.** `.scratch/vs.py` already
does this: it plays unmodified `main.py` in both seats against a constant-override
variant and reports our absolute score. Three opponent policies move our score by
$8,570 of mean and $24,000 on a single seed, which is larger than any candidate
effect this project has measured except the v11/v12 winners — so the *first* thing
to establish about any future candidate is whether it is robust across opponents,
not whether it beats a copy of itself. Concretely: fix a panel of four opponents
(mirror, all-feed-buyer, herd-only, berry-only), run each candidate against all
four at six seeds, and require it to be non-negative against every one. That is
the same number of games as the current six-seed mirror screen and it measures a
different, larger axis. The specific question to ask first, because it is where
the panel already says we are weakest: **against the herd-only opponent we lose
$4,087 and our herd's own products are what they flood — is there a rule that
reads `obs["farms"][1 - player]["tiles"]`, which `main.py` has never opened, and
tilts our marginal head away from the species the opponent is visibly stacking?**
The herd mix has been refused seven times as a *constant* and twice as a function
of the shop lottery; it has never been tested as a function of the opponent's
visible pasture count, and the panel is the only instrument that can score it.
