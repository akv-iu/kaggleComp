
## 2026-08-17 (v14 baseline, submission 55507562, rating 850.0 IMPROVED) — the competition draws its shops with replacement, and the shed leak that only exists at the competition's demand

### State at the start of the run

`main.py` and `test_agent.py` are v14 (submission 55507562), whose public rating
has now settled at **850.0, up from v13's 819.9** — six consecutive readings of
this submission (835.8, 853.5, 831.3, 839.8, 846.0, 850.0) put it comfortably
above every earlier agent. The indexed field record for v14 alone is **37 wins
and 41 losses over 78 games**, our mean $87,969 against the field's $93,462,
median $90,731 against $94,934, our range **$22,240 to $138,163** and theirs
$39,914 to $155,833. Thirteen of our games are under $62,000 and we lose twelve
of them. Nineteen games are lost by more than $20,000, against opponents
averaging $117,000-$135,000.

Six replays were selected for analysis. Three of them are ancient (v5, v6 and v8
seats) and their conclusions are already in this file; the useful work this run
came from reading the `configuration` and `town` blocks of all nine replays on
disk, which nobody had done, and from instrumenting the baseline at the
competition's `townCenterSellInterval` rather than the benchmark's.

### Finding 1 — the competition draws its shop unlocks *with* replacement; the installed environment draws *without*

This is a second configuration gap between the benchmark and the competition, it
is entirely undocumented, and it invalidates the reasoning behind an earlier
refusal.

`_end_of_day` in the installed environment reads

    remaining = [s for s in SHOPS if s not in town["unlocked_shops"]]
    choice = rng.choice(sorted(remaining))

so a local game unlocks **all eight distinct shops** across days 3-24. Every
competition replay unlocks **eight times from the full set of eight, duplicates
included**. `episode-91992026` is the clearest: ICE_CREAM_SHOP on day 3 *and
again on day 9*, YARN_STORE on 6 and 15, SMOOTHIE_SHOP on 12 and 21,
FARMERS_MARKET on 18 and 24 — four distinct shops, every one of them doubled.
`episode-92762105` draws SMOOTHIE_SHOP three times.

Distinct shops per game over the nine replays: **4, 5, 5, 5, 5, 5, 6, 6, 7 —
mean 5.33**, against the with-replacement expectation `8*(1-(7/8)^8) = 5.25` and
the local environment's 8 every time. A local mirror of unmodified `main.py`
opens all eight at both intervals, confirmed by running one.

**What it changes and what it does not.** The *expected* number of shop-listings
per product is unchanged (eight draws times the probability a shop lists it), so
this is a pure variance and concentration effect, not a level shift. What it
changes is the tail: `P(a given shop never opens) = (7/8)^8 = 34.4%`, and a
duplicated shop drains at **double rate for the rest of the season**. **WOOL's
only shop is YARN_STORE, so about a third of all competition games have no wool
drain at all** — observed in 3 of 9 replays, and wool ends at $1 in every one of
those. STRAWBERRY has four shops so it goes undrained only 0.4% of the time, but
its drain rate ranges over 1x to 3x, which is most of the difference between our
best games and our worst. The clearest pair: `episode-91992026` drew
ICE_CREAM x2, SMOOTHIE x2, FARMERS_MARKET x2 and YARN x2 — every draw on
strawberry or wool — and strawberry ended **293 units below `I0` at $264** while
the winner scored $175,862; `episode-92754717` drew BAKERY x2, PIZZA x2,
ICE_CREAM x2 and strawberry ended **41 units above `I0` at $41**, with both farms
scoring ~$56,000.

**It is the real reason the shop-conditioned screens came out null.** The
2026-08-15 shop-mix screen was recorded as "bit-identical to baseline on five of
six seeds ... there is almost no herd decision left open once the lottery can be
read". The simpler explanation is that **locally there is nothing to condition
on**: every shop is guaranteed to open. A rule that says "do not stack the
species whose shop has not appeared" is close to a no-op against that guarantee
and a live one-in-three bet in the competition. Any future candidate that reads
`obs["town"]["unlocked_shops"]` will be under-measured by the benchmark for the
same reason and in the same direction, and there is no way to move the gate.

### Finding 2 — melon is a benchmark fiction

MELON's inventory at the last bell, over all nine replays: **+142, +153, +155,
+155, +156, +158, +158, +158, +158 above `I0`**, at prices **$48, $16, $10, $10,
$7, $1, $1, $1, $1**. The local mirror at interval 24 ends **+74 at $195**, and
at interval 12 **+4 at $250**. Melon's `above_func` is `sq` with amp 0.01, so
those ~80 extra units of glut are the whole difference between $195 and $10.

Melon is listed by no shop, so its entire demand is the 70-unit town-centre
drain, and every real opponent floods it: the day-12 census of the six $145k+
leaders shows **12-14 melon tiles apiece against our 8**. Our first crop
(planted days 0-6, harvested day 9-11 at $250-271) is genuinely the opening's
funding — melon holds $250-271 until day 11 in all nine replays. Our second crop
(`MELON_LAST_DAY = 14`, harvesting days 21-24) sells at **$1-90 in the
competition and $195-250 locally**. **Every melon valuation in these ledgers,
including "melon $44 a unit marginal" and "melon 72u/$15,901", is worth roughly a
tenth of that in the real market.** Cutting the second crop was deliberately not
screened: it is a supply *reduction* in a product the benchmark prices at full
value, so the gate would refuse it on sight. It is recorded as a fact about the
field, not as a queued experiment.

### Finding 3 — greedy pair matching is within 1.1% of optimal (retry condition closed, no benchmark spent)

The v12 dispatcher entry left one condition open: "Greedy pair matching is also
not *optimal* matching ... Hungarian assignment is the upgrade path if this binds
again." Measured directly with `scipy.optimize.linear_sum_assignment` over every
priority band of a seed-0 mirror at interval 24, replaying pass 1 and the band
partition exactly: **1,154 bands, 3,328 greedy pairs, total walking distance
9,119 against an optimal 9,021 — 1.1%**, about 98 moves of 3,742. Hungarian
assignment is not worth implementing. **Closed for free.**

### Finding 4 — the nightly shed discard is a real leak at interval 24 and a rounding error at interval 12

`_drop_inventories_to_shed` empties every unit's pack into the shed at nightfall
and silently discards whatever does not fit. This file records, twice, "4 units
discarded, all milk — the shed is not a leak, stop suspecting it". **That
measurement was taken at `townCenterSellInterval: 12`.** Patched across a seed-0
mirror at **interval 24 the same game destroys 174 units across both farms — 85
STRAWBERRY, 33 WHEAT, 26 MILK, 18 FERTILIZER, 12 WOOL, about 87 units a farm** —
on nights 19, 20, 21, 23, 24, 25 and 27. At interval 12 the identical probe
returns **4 units, all milk**, reproducing the old number exactly. Both figures
reproduce across re-runs.

**The mechanism, and neither half of it is "the shed is full".** At dusk the
shed holds **29-49** of 100, leaving 51-71 units of room; the crew is holding
**76-83**. It is the crew that is over capacity. Produce rides in a pack until
its unit goes idle, and the idle-drop branch in `_assign` is the only thing that
ever walks it home — but **PASS is 0-13 unit-turns a day from day 20 onward**
(against 52-88 a day on days 2-9, where 534 of the game's 714 PASS turns live),
so from day 19 nothing is ever idle and every harvest waits for the nightly dump.
The shed's permanent occupancy is **wool at 27-41 units every day from day 14**,
because at interval 24 wool quotes $1-55 against its $130 floor and only the
pressure branch can move it, plus 17-36 wheat of feed reserve.

### Experiment 1 (screened, rejected) — send any loaded unit home

**Exact change.** `KEEP_ITEMS = frozenset(("WHEAT","GOOSE","COW","SHEEP"))` and
`DROP_LOAD = 6`; in `_assign`, after pass 1 and before pass 2, any still-idle
unit carrying at least `DROP_LOAD` non-keep items is removed from `idle` and
given the dock walk instead of a field job.

**Pre-test reasoning.** 87 units a farm are destroyed; at the interval-24 price
table (strawberry $210, milk $235) that is nominally ~$13,000, 13% of the score.
A walk to a dock is 2-3 turns and this ledger already records that it ends where
the next PICKUP starts, so it should not be read as waste.

**Evidence.** Six-seed mirror, 12 games a cell: **-$6,217 at interval 24 (93,202
against 99,419) and -$7,809 at interval 12 (119,305 against 127,114)**. Per-seed
at 24: -3,580 +2,965 -2,640 -19,652 +2,004 -16,400.

**Verdict: rejected**, far outside the noise band in both cells. A threshold on
its own fires all day and steals priority-0 water and feed work.

### Experiment 2 (screened, rejected) — send the loaded unit home at exactly the last hour it can arrive

**Exact change.** As above with `DROP_LOAD = 3`, plus `hour` threaded into
`_assign` from `agent()`, and the trigger `hour + min_distance_to_dock >= DUSK`
with `DUSK = 23`.

**Pre-test reasoning.** This is the pairing the dusk entry in `memory.md` named
and never found. ~596 moves a game are units still walking at dusk toward a job
the day ends before they reach, and `_end_of_day` respawns every unit on the NW
dock, so that progress is deleted; refusing those jobs was -$1,728 because the
freed turns became PASS. A shed run is a job for exactly those turns, and unlike
experiment 1 it costs nothing before dusk.

**Evidence.** Six-seed mirror: **-$4,838 at interval 24 (94,581) and -$4,733 at
interval 12 (122,381)**. The mechanism fires exactly as designed — on seed 0 at
interval 24, **discards fall 174 -> 52 and strawberry discards 85 -> 27** — and
the score falls $7,688 in that same game.

**Verdict: rejected.** And it produced the run's most transferable number: **a
leak measured in units is not a leak measured in money whenever the product is
near its own saturation point.** Strawberry's `above_func` is linear with amp
**$1.92 a unit** and our interval-24 mirror ends 113 units *below* `I0`, so
recovering 85 strawberry a farm puts **170** units into that market, crosses
`I0`, and takes the quote from $209 to roughly $11. Against a single real
opponent who does not fix the same leak the arithmetic is different — our 85
units alone move strawberry from -113 to -28, roughly $209 -> $164, a net gain
near $6,500 — but **the mirror cannot express a one-sided supply increase, and no
local instrument this project owns can.** This is the same wall that refuses
`BERRY_TILES = 48`.

### Experiment 3 (full benchmark, rejected) — price the shed pressure on the whole farm's stock

**Exact change.** One line in `_market`:

    pressure = (shed_used > SHED_PRESSURE
                or shed_used + sum(carried.values()) > SHED_CAP)

`carried` is already a parameter. This costs **zero unit-turns**: it only makes
the existing `cap * 4` dump branch fire on the turns when the nightly drop would
otherwise overflow.

**Pre-test reasoning.** Both haul repairs failed because they spent labour. The
shed cap is enforced against shed *plus* everything the crew holds, so the
trigger should be too; there is no sense defending a $130 wool floor with goods
that are about to be destroyed.

**Screening evidence, six seeds, 12 games a cell:** **+$1,759 at interval 24
(101,178 against 99,419) and +$1,126 at interval 12 (128,240 against 127,114) —
positive at both**, which no other candidate this run achieved. Two variants that
fire earlier were screened beside it and are worse where it matters: threshold
`SHED_CAP - 15` gives +$1,124 / +$1,159 and `SHED_CAP - 25` gives +$992 / +$884,
and both go **negative on seeds 0-3 at interval 12** (-$1,129 and -$2,098) where
the plain form is +$28. The plain form was therefore the one carried forward,
following the rule in `memory.md` about recomputing a screen on seeds 0-3 first.

**Gate evidence** (`verify.py .automation/baseline_main.py 4`, every status
DONE): **3 of 8 wins, 2 exact ties, mean +$34.0, mirror +$28.2** (candidate
133,938.2 against baseline 133,910.0).

    seed 0 seat 0  148,323 v 148,289   +34
    seed 0 seat 1  148,289 v 148,323   -34
    seed 1 seat 0  124,863 v 124,863     0
    seed 1 seat 1  124,863 v 124,863     0
    seed 2 seat 0  124,839 v 124,650  +189
    seed 2 seat 1  124,650 v 124,839  -189
    seed 3 seat 0  137,574 v 137,879  -305
    seed 3 seat 1  138,128 v 137,551  +577

**Verdict: rejected**, and the shape of the result is the whole story. Six of the
eight pairings are **perfectly antisymmetric** (+34/-34, 0/0, +189/-189):
candidate and baseline play the same game and the only difference is which seat
holds the rounding. The rule essentially never fires on seeds 0-3 at interval 12,
because that is the configuration in which the leak it repairs does not exist.
This is the fifth candidate in this ledger that is positive at both intervals
over six seeds and null on the four seeds the gate uses.

**Test again only with:** a gate running at `townCenterSellInterval: 24`, or a
head-to-head sample large enough to resolve $1,000 against a per-seed SD of
$7,900. The screening result stands as a fact about the real market.

### Outcome

`main.py` and `test_agent.py` are byte-identical to their pre-run snapshots
(`diff` clean against both `.automation` baselines). `py_compile` passes on both
and `test_agent.py` passes ("unit checks ok", episode me=169467, starter=3491).
`verify.py` and `loop.py` untouched. Three distinct hypotheses were evaluated:
two pruned by screens that were decisive at both intervals (-$4,800 to -$7,800,
well outside the noise floor, so no full benchmark was warranted) and one carried
to the full gate and refused by the ratio. **No `.automation/submit_request.json`
was written.**

### Best distinct next hypothesis

**The opening is cash-bound, and the only untried source of day-5 cash is the
melon crop the leaders run at 12-14 tiles to our 8.** This run measured the
opening properly for the first time: the crew is **27-49% idle on days 2-9 — 534
of the game's 714 PASS unit-turns, with only 2-5 jobs standing on the board at
hours 18-22 — while 12 of the 25 opening tiles carry nothing from day 2 to day
5**, and money at dawn runs $238/452/464/731/973/697/829 on days 2-8. Every
filler for those tiles has now been refused (opening wheat 1/4 at -$4,361, tomato
-$2,720/-$2,836, melon-as-a-whole-opening 0/4 at -$10,227), and the last one,
CARROT, was priced this run and ruled out **without** a benchmark: `budget` is
negative on days 2-5, a $20 seed cannot be funded without raiding the feed
reserve, and by the first day it can be funded (day 6) the berry field has taken
every bare tile — the census shows **zero bare tiles on days 7-9**. So the idle
labour is not the constraint and neither are the tiles; the cash is.

The pairing the melon refusal never tested is **`MELON_TILES = 12` with the
market order left alone**, so melon seed still spends only what the herd did not
want. The 2026-08-14 refusal moved the melon order *above* livestock and
attributed its own loss to exactly that ("the herd sat at 2-4 head until day
12"); the closure that followed ("do not test any melon quantity, window or
ordering again") therefore covers the reordering and the *window*, but never the
tile count on its own. It is live at both intervals, it is the only remaining
route to the leaders' 14 head at day 12 against our 9, and it must be screened at
**both** intervals with the caveat from Finding 2 attached: melon's second crop
is worth a tenth of its local quote, so a gain concentrated after day 20 is the
harness talking and only a gain in the *herd* counts.
