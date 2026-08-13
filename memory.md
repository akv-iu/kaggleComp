# Strategy Memory

This is the durable evidence ledger for the optimizer. Read it before choosing an experiment and update it after every attempt. A rejected strategy is not permanently bad: preserve the context, missing pairing, and condition that would justify testing it again.

## Strategies that worked best

### Keep livestock growth synchronized with capacity

- **Strategy:** Buy an animal only when one matching structure slot is ready, plan capacity at 9 animals per structure, and reserve 8 hands for feed transport.
- **Why it works:** It prevents the previous pattern of buying 33–46 animals while finishing with only 13–18, and avoids building 31–37 empty structures.
- **Evidence:** The repaired v5 agent beat the exact v4 baseline in 8/8 local games, averaging 78,578 versus 39,723 (+38,855). A representative game bought and kept 19 animals with no empty structures; the old agent bought 42, kept 6, and left 44 structures empty.
- **Required pairing:** Workload-based hiring, nearby placement, enough feed carriers, and no speculative construction.
- **Amended 2026-08-12:** the synchronisation is right for days 9-29 and wrong for days 0-8, where it costs more in production days than it saves in waste - see "Buy the herd in an opening rush" below. Capacity planning still governs after the window; the rush is bounded by cash and by `HERD_RUSH_SIZE` precisely so it cannot become the old overbuying.
- **Reconsider if:** A crop-heavy plan can prove that temporarily unused capacity returns more money than the synchronized pipeline.

### Minimize walking and protect the final day

- **Strategy:** Place new structures near the shed, hire for measured workload, stop FEED/CARE work on the final day, and reserve a cleanup crew for harvesting and selling.
- **Why it works:** Productive actions and end inventory matter more than theoretical capacity; row-major far-away construction consumed too many turns and left no hands available at the end.
- **Evidence:** This was part of the v5 package that improved public rating from 554.1 to 608.6 and passed the 8/8 local comparison above.
- **Required pairing:** The synchronized livestock pipeline; placement alone cannot fix overbuying.
- **Reconsider if:** A future path planner measures that travel is no longer the binding cost.

### Exploit wheat scarcity without displacing the herd

- **Strategy:** Maintain about 0.75 wheat tiles per animal, target 10 wheat tiles late, keep a feed reserve of `animal count + FEED_BUFFER`, and sell only true surplus (up to 12 units when price is at least 20).
- **Why it works:** Strong opponents both produce and trade wheat while livestock agents must buy it for feed. The 0.75 ratio captures crop value while preserving the reliable herd economy.
- **Evidence:** The 0.75 candidate won 8/8 against v5 and averaged 78,591 versus 70,656 (+7,934). Public v6 submission 55413328 then improved the rating from 608.8 to 660.2, validating the direction against the real field.
- **Required pairing:** Conservative field size, feed reserve, surplus-only selling, and the existing livestock labor model.
- **Reconsider if:** Replay prices, animal count, or feed demand shift enough to change wheat's opportunity cost.

### Water only when the expected crop return justifies the action

- **Strategy:** Water every other day before the crop bonus window, then water daily during bonus/production periods.
- **Why it works:** It saves low-value early actions while retaining mature crop output.
- **Evidence:** Watering alone was only marginal, but paired with the wheat loop it contributed to the 8/8, +7,934 v6 result.
- **Required pairing:** A profitable crop plan. Water optimization without crop economics is not a full strategy.
- **Reconsider if:** Crop timing or scoring rules change.

### Use a hard evidence gate before spending a submission

- **Strategy:** Compare candidate and exact baseline over at least four deterministic seeds in both seats; require 7/8 wins, at least +100 mean final money, all agents DONE, and passing tests. Before submission, the wrapper independently reruns a frozen verifier instead of trusting the agent's reported scores. A rejection must immediately feed a distinct next hypothesis rather than end the improvement loop.
- **Why it works:** It filters seat luck and attractive one-seed results while preserving the five-push budget, then converts failure evidence into the next experiment.
- **Evidence:** Several plausible crop variants were rejected locally; only the measured v6 improvement was submitted. The later two-quadrant cap won 7/8 but gained only +1,327.9, proving that the gate protected the submission budget while its routing diagnosis supplied the next search direction.
- **Required pairing:** Exact pre-run code and verifier snapshots, honest logging of rejected attempts, removal of rejected code, and a persistent `needsImprovement` state so the next three-hour run continues even without new replays.
- **Reconsider if:** The simulator becomes nondeterministic enough to require a larger sample.

### Never put a price floor on a product the town does not drain

- **Strategy:** Sell fertilizer as it is collected (`SELL_RULES["FERTILIZER"] = (3, 5)`) instead of holding it for a $50 quote that never returns.
- **Why it works:** A floor is a bet on price recovery. Fertilizer is the one good this farm gluts - 292 units a game against milk's 135 - and no shop drains it, so its price falls all season and ends near $1. The floor did not avoid selling into a crash, it guaranteed selling at the very bottom on day 29. It also freed about half the 100-item shed, which had been sitting under 45-53 fertilizer from day 20 and tipping the farm into `SHED_PRESSURE`, where the emergency rule dumps milk and wool at four times cap and ignores their floors.
- **Evidence:** Won 7/8 against the exact baseline, averaging $76,529.9 versus $75,026.0 (+$1,503.9), every status DONE; only loss was -$56. Measured revenue table for one game: MILK $226.1/unit ending at $238, WOOL $246.5 ending at $247, MELON $223.2 ending at $223, FERTILIZER $45.7 ending at $1.
- **Required pairing:** Keep collecting the fertilizer. The complementary attempt that gated *collection* on the same $50 floor lost 0/8 at -$8,435.6; the waste was the hoarding, never the production.
- **Reconsider if:** A shop unlock starts draining fertilizer, or its price stops decaying across the season.

### Local self-play overvalues racing an opponent to a shared pool

- **Lesson:** `verify.py` plays the candidate against a copy of the baseline in the same market. Any change that simply acts *sooner* than the opponent on a shared, finite resource wins locally by beating a slower copy of itself, and that edge does not exist against a field that already acts promptly.
- **Evidence:** v7 dropped the fertilizer sell floor from $50 to $5 and won 7/8 locally at +$1,503.9. Its public rating settled at **649.0, below v6's 665.4**. Fertilizer is the clearest case in the game: nothing anywhere drains it, so its price is a strictly decreasing shared pool, and selling faster only moves who gets the top of a curve both farms are pushing down.
- **The detector, now in `verify.py` and gated by the wrapper:** `mirror` plays each agent against *itself* and reports its absolute score. Racing gains vanish in a mirror because both sides act at the same moment; production gains survive. The wrapper requires a mirror gain of at least 500.
- **How to apply:** Before trusting a local win, ask whether the gain comes from *producing or saving more* or merely from *getting there first*. More seeds do not fix this - it is a bias in the benchmark's design, not its sample size.
- **Reconsider if:** A racing change ever clears the mirror gate; then raise the threshold.

### The mirror has a second blind spot: mutual restraint

- **Lesson:** the mirror was built to catch *racing* - a change that only beats a slower copy of itself - and it does. But it plays **two copies of the candidate**, so a change that **reduces supply** reduces it on both sides of a shared market, prices rise for both farms, and the change credits itself with revenue that exists only because the opponent restrained too. Against a field that keeps flooding the market, those prices never appear.
- **Evidence (2026-08-13):** the land utilisation gate (`empty_owned < 8` before buying a quadrant) scored **8/16 wins, mean +$70.2, mirror +$3,118.4** - a coin flip against a real opponent while clearing the mirror threshold six times over. Its mirror mean, $122,640, is the highest number this project has ever measured, and it is an artefact.
- **How to apply - the direction of the disagreement names the artefact:**
  - head-to-head **up**, mirror **flat** -> racing. v7: +$1,504 and +$84, shipped, **-36 rating**.
  - head-to-head **flat**, mirror **up** -> mutual restraint. This entry.
  - both up -> evidence. v9 +$10,041/+$11,235, v10 +$9,648/+$9,671, v11 +$18,552/+$18,468, v12 +$17,391/+$5,533 - every shipped winner agrees on both.
- **Required pairing:** read them as a pair, always. A candidate that clears one gate and not the other has told you *which* artefact it is, which is worth more than the number.
- **Reconsider if:** never. Both blind spots follow from the mirror being two copies of one agent; neither is fixable by more seeds.

### Submitting retires an older agent, so do not submit faster than ratings settle

- **Lesson:** Only the two most recent submissions keep playing episodes; Kaggle retires the rest, and the competition page shows only the live ones. A retired agent's rating freezes wherever it happened to be. The binding constraint on submitting is therefore **not** the five-a-day budget - it is that a new submission replaces an agent that may not have finished converging, so you never learn whether it was good.
- **Evidence (2026-08-12 00:45 UTC):** eight submissions exist in the API; only v8 (31 episodes, last 00:15) and v7 (30, last 23:15) were still playing. v6's final episode was 17:33, two minutes before v8 was submitted at 17:35. Everything from v5 back had stopped hours to days earlier.
- **Not established:** the exact retirement rule. v5 kept playing long after v6 landed, so it is not a strict "newest two". Do not assume a rule; check `kaggle competitions episodes <id>` for the most recent episode timestamp.
- **How to apply:** Before spending a submission, check that the current agent has stopped moving (roughly 30+ episodes and a stable score). Shipping a marginal candidate costs the evidence for the one already in flight.

### Never read a public rating before it has converged

- **Lesson:** A fresh submission's rating swings wildly for its first dozen episodes and means nothing. Wait for roughly 25-30 episodes (`kaggle competitions episodes <id>`) before treating a rating as evidence.
- **Evidence:** v8 has read **777.0 at 7 episodes**, **653.7 at 28**, and **682.8 at 31**. A conclusion was drawn and written into this ledger off the 7-episode number, then corrected off the 28-episode number, and both were premature: the score swung 124 points and was still moving at 31 games.
- **Standings at 2026-08-12 00:45 UTC:** v8 682.8 (31 games, live), v6 665.4 (42, retired), v7 651.6 (30, live), v5 602.7 (38, retired). v8 is probably the best agent shipped so far, but "probably" is the honest word until it stops moving.
- **The uncomfortable implication:** the local benchmark reported +$1,504 for v7 and +$3,567 for v8; the mirror reported +84 and +3,903. The mirror's *ordering* has held up - v7 flat-to-down, v8 up - but the magnitudes do not map onto rating at all, and the field still contains farms scoring twice our best. Chasing the field ceiling remains worth more than another local delta.
- **How to apply:** Record the episode count beside every rating in these ledgers, and say "still moving" rather than picking a number. A rating without its episode count is not evidence. See also the entry above on retirement: a rating stops converging the moment its agent is retired.

### Read the environment source, not the agent's own comments

- **Strategy:** `.venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py` is the ground truth for every economic constant. Read it before reasoning about prices, yields, or actions.
- **Why it works:** Twenty-plus experiments in this ledger tuned constants inside a model taken from `main.py`'s own docstring, and that model was wrong in three ways that matter. The whole `FERTILIZE` action existed unused for the entire project.
- **Evidence — the facts that changed the strategy:**
  - `TOWN_CENTER_PRODUCTS` excludes FERTILIZER and no shop lists it, so **nothing anywhere drains fertilizer**. Its market inventory can only rise, so its price can only fall. It is not a normal good.
  - `TOWN_CENTER_DEMAND_SCHEDULE = [(20, 4), (10, 2), (0, 1)]`: town demand **quadruples after day 20**.
  - Almost every other product sits in *scarcity*, not glut, because the town drains faster than two farms supply. Final versus base price: STRAWBERRY 318/120, WOOL 247/200, MILK 238/160, TOMATO 101/60, WHEAT **55/25**. The agent's floors and drip caps are glut protection for a glut that never arrives.
  - `FERTILIZE` (one action, one fertilizer) sets `fertilized_until_day = day + 2` and doubles what each watering adds. Wheat's watering window is exactly 3 days wide.
  - Ongoing crops accrue yield whether or not they are watered; watering only prevents the weed death and gates the fertilizer bonus.
- **Required pairing:** Nothing. This is free and should precede every future hypothesis.
- **Reconsider if:** Never.

### Spend fertilizer on wheat instead of selling it

- **Strategy:** Emit a priority-0 `FERTILIZE` job for any wheat tile inside its watering window that is not already fertilized.
- **Why it works:** It converts the one product with zero market demand into the one input the farm buys most. Wheat is the only crop with yield headroom (plain watering reaches 4 of a cap of 6; fertilized reaches the cap), and one fertilize covers wheat's entire 3-day window. Measured effect: wheat purchases fall from ~140 units a game to ~90 while the herd stays the same size, and the farm stops bidding up a price it is itself pushing into scarcity.
- **Evidence:** 14/16 wins over seeds 0-7 in both seats, averaging +$3,566.5, every status DONE. Standalone episode $94,714 to $100,010. 48 FERTILIZE actions a game, drawn from the 292 the farm already collects.
- **Required pairing:** Priority 0. Demoting it is worse than not doing it at all (2/8 at priority 1, 1/8 at priority 2) because the bonus is credited by waterings inside a 3-day window, so a late fertilize is pure walking. Also pairs with selling the remainder promptly - see the fertilizer floor entry.
- **Reconsider if:** A shop ever drains fertilizer, or wheat stops being bought.

### Unblock the herd pipeline, but cap the wage curve in the same change

- **Strategy:** Three edits that only work together. `PLACE` at priority **-1**, ahead of watering and feeding. A per-species `last` buy-day in `ANIMALS` (GOOSE **20**, COW 19, SHEEP 20) replacing the generic "must reach one production" deadline. And a flat `HIRE_MAX_WAGE = 144` in place of `max(HIRE_MIN, money * HIRE_FRAC)`.
- **Why it works:** the farm grows one head at a time, so one animal still riding in a carrier's pack blocks the next structure *and* the next purchase - measured 288 consecutive turns stuck on `want pending (COW)`, days 14-25, purely because the carrier stayed eligible for priority-0 water jobs. Unblocking it buys 21 head instead of 16 and raises every productive action (CARE 377 v 282, FEED 354 v 278, HARVEST 217 v 182). But the extra herd raises `load`, `load` raises `crew_cap`, and the crew walks into the exponential tail of `fib`: hands 13-16 cost $2,207 a day, 85% of the wage bill for 25% of the crew. Because the old ceiling was proportional to the bank, it bought that tail hardest in the final week, when a hand has fewest days left to repay it. **A hand-day is not worth more because the bank is fuller.**
- **Evidence:** 8/8 at 4 seeds, +$10,041.0, **mirror +$11,234.8**, all DONE; 15/16 at 8 seeds, +$7,649.5, mirror +$8,422.0. Mirror games reach $95,972, above our best public game ever. The leak that made this necessary was measured, not guessed: on the losing seed, revenue rose $16,745 (milk +$10,222, wool +$6,029) while hire spend rose $5,110 to $21,101.
- **Required pairing - all three, and the attribution is unusually clean.** Wage cap alone: **1/8, +$32, mirror +$431**. `PLACE` + goose deadline, no wage cap: **4/8, +$1,765, mirror +$553**. `PLACE` + wage cap, geese left at day 24: **7/8, +$5,722, mirror +$6,680**. All three: 8/8. The pipeline fix creates the herd, the goose deadline decides what the freed cash buys, the wage cap stops the crew that herd justifies from costing more than the herd earns.
- **Reconsider if:** anything raises `load` a lot - a large crop area in particular - because `HIRE_MAX_WAGE` is a hard ceiling on the crew. It came from a three-point screen (89 -> 3/4; 144 -> 4/4 +$9,122; 233 -> 4/4 +$7,420); re-screen it rather than assume 144 travels. **Re-screened 2026-08-13 under the 40-tile berry farm it was fitted before: it travelled.** 233 scored 113,472 and 377 scored 108,206 against 144's 114,172 mirror mean. This also supersedes the old "static 10-hand cap" refusal: capping the crew *by headcount* failed (6/8, +$777) because it removed profitable throughput along with idle labour; capping it **by marginal wage** works because the fib curve, not the headcount, is what makes the last hands unprofitable.

### Grow the crop the town actually drains, and stop the crop stealing the herd's carriers

- **Strategy:** 40 strawberry tiles planted from day 6 behind melon and the structure branch, seed bought out of the investment budget, sold at `(2, 100)`, `FERTILIZE` extended from wheat to any ongoing crop on its production night - **and `FEED` moved from priority 0 to -1**, beside `PLACE` and `PICKUP`.
- **Why it works:** four of the eight shops list STRAWBERRY against one for WOOL and none for MELON, so the town drains ~500-600 units a season and the price ends at $217-311 against a $120 base *in replays where neither farm grew any*. It is the one market we can enter in scarcity rather than glut. Every opponent above $120k plays this farm and nothing else explains the gap: reconstructing wenjinyang's $175,862 against our $69,326 in the same episode, their milk, wool and fertilizer are roughly *equal* to ours.
- **Evidence:** 7/8 at 4 seeds, mean $100,283.8 versus $94,265.5 (**+$6,018.3**), **mirror +$5,336.8**, every status DONE; mirror games reach $106,086 against our best-ever public game of $90,642, and the standalone episode scores $123,166 against v9's $107,873. Re-run at 8 seeds: **15/16, +$9,647.8, mirror +$9,670.8**, mirror mean **$100,001.6** - the first configuration whose average game is six figures.
- **Required pairing - the two halves are worth nothing apart.** Berries alone on the v9 baseline: **2/8, -$4,038.6, mirror -$2,526.3**. The same candidate with `BERRY_TILES = 0` but every other edit kept, including `FEED` at -1: **1/4, -$1,049, mirror -$3,398.8**. Together: +$6,018.
- **The mechanism, and it generalises past strawberry.** Only three jobs can be done exclusively by a unit already carrying the goods - `PICKUP`, `PLACE`, `FEED` - and `_assign` gives every job to the nearest able unit. Forty berry tiles put twenty-odd priority-0 `WATER` jobs a day on the board that *any* unit can serve, so the wheat carrier walking to a pasture is the nearest body to a dry tile and waters it instead. Measured: **18 animals bought, 8 alive at the last bell, four empty pastures, FEED down to 193 actions from 354.** The farm did not run out of cash - it ended at $78,140 with 200 berries sold - it ran out of animals. This is the same bug v9 fixed by moving `PLACE` to -1 after measuring a 288-turn deadlock. `FEED` was the third case and it only binds once something puts enough any-unit work on the board.
- **Also fixed here, and load-bearing:** `production_day` was off by one. The nightly refresh computes `next_day - planted_day - first`, so an ongoing crop produces on the night of `age + 1 - first`, and it stops after `max_yield` productions and marks the tile to decay - visiting it later buys nothing. And `PLANT_SLOTS` is split into `PLANT_SLOTS = 2` (crew capacity a tile consumes) and `PLANT_LOAD = 4` (hiring demand it creates); sharing one number meant making room for crops also halved the crew that tends them.
- **Amended 2026-08-13: `BERRY_TILES = 40` is now screened, and the crop was only ever running at 63% of itself.** Under v11 a mirror game lost **27 of 40 berry tiles to thirst** - 6 at age 1, 10 on their first production night - and landed 101 of a possible 160 production nights. Trimming the field is the wrong repair: 26 tiles scored 109,550 and 32 scored 109,663 against 40's 114,172, because a tile that dies stops consuming water. So is watering harder: watering every ongoing tile daily halved the deaths and scored 105,646, taking the extra waterings out of harvesting. The deaths were a dispatcher symptom and vanished entirely with the closest-pair fix above (160 of 160, 0 deaths). `BERRY_FIRST_DAY = 6` screened near-neutral at 4 (113,162) and is still unsettled.
- **Reconsider if:** the field stops planting berries, or a shop rotation drops STRAWBERRY.

### Buy the herd in an opening rush; an animal's value is the days left on the calendar

- **Strategy:** Until day 8 and up to 8 head, grow the herd in parallel and ignore `slots` (`HERD_RUSH_DAY`, `HERD_RUSH_SIZE`); hold only three days of feed money rather than ten while that window is open (`FEED_DAYS_EARLY`); let day 0 buy cows and sheep rather than geese (`POOR_UNTIL_DAY = -1`); and never make a *free* structure wait on the bank when the animal is already in the shed.
- **Why it works:** `pending_care_bonus` triples every production, so a cow is worth its production days times three - and delay is the only thing that destroys production days. Two throttles held the herd at 3-4 head from day 2 to day 11. Days 0-1 it was the one-head-at-a-time pipeline plus `slots`, with **$1,584 unspent at nightfall on day 0**. Days 2-10 it was purely the feed reserve: `budget` was *negative* on seven of those nine days, because ten days of feed money for four animals is $1,280 against a bank of $1,300, and the next head needs `cost + keep` on top. Early animals also pay for themselves immediately: fertilizer is near its $100 base before day 10, so a head drops $90-100 a night against ~$30 of wheat.
- **Evidence:** 8/8 at 4 seeds, mean $113,476.0 versus $94,924.0 (**+$18,552.0**), worst pairing +$8,694, all DONE. **Mirror +$18,468.1**, mean $114,778 - every mirror game six figures, and the mirror mean now beats our best public game ever ($109,836). The mechanism in an instrumented game: milk $30,262 -> $36,956, wool $19,522 -> $22,511, strawberry **unchanged**, on a herd that is *smaller* (12 head against 14) but earlier. Re-run at 8 seeds: **16/16, +$16,710.6, mirror +$10,602.5**, worst pairing +$8,694 - no losing pairing at either sample size, which this project has never recorded before.
- **Where it came from:** Suda's $165,925 against our $89,417 (episode 92421750). Their care coverage is *worse* than ours (82% of animal-days against our 92%) and their final herd is the same size (13 against 10-11). The only difference is timing - **321 animal-days against 215** - and it is most of a $58,000 milk gap.
- **Required pairing - all four, and each fails alone.** Parallel growth on its own: 0/4 to 3/4, mirror **-$4,551**, with +52 animal-days and milk *flat*, because the freed slots bought heads on days 14-18 that never reach production. The rush uncapped: milk and wool +$16,492 but strawberry **-$27,914**, because it paves all 25 opening tiles with pasture and never reaches the $1,000 land purchase. Day 0 left goose-only: 8 of 16 head are geese and $16,896 of milk and wool becomes egg. And the free-structure fix is load-bearing - without it the rush deadlocks outright with seven geese crated and no cash to authorise a $0 coop.
- **Reconsider if:** `HERD_RUSH_DAY = 8` and `FEED_DAYS_EARLY = 3` were never screened independently; only the size was (6/8/10/12 -> mirror +6,245/+12,910/+9,843/worse). This also supersedes the two rejected feed-reserve entries below: the reserve *is* a throttle, but only in the opening, and cutting it season-long is noise.

### Match the closest (unit, job) pair, not the nearest unit to each job

- **Strategy:** in `_assign` pass 2, inside one priority band, repeatedly take the globally closest (unit, job) pair instead of walking the job list in sorted order and handing each job its nearest able unit. Priority order is untouched; a band is only entered once the band above it has taken every unit it can use.
- **Why it works:** scan order let a tile on the far edge claim the nearest body and shove the unit already standing beside the next job across the map. The farm was not short of labour or badly laid out - it was walking its labour to the wrong jobs. Field leader in episode 92507094: 0.82 moves per productive action. v11: **1.86**, on a farm that is *more* compact than theirs (mean 3.15 tiles from a dock against 4.01) with a *larger* crew (7,291 unit-turns against 6,647) doing 1,159 fewer productive actions.
- **Evidence:** 8/8 at 4 seeds, mean $126,507.5 against $109,116.3 (**+$17,391.2**), worst pairing +$10,782, all DONE. **Mirror +$5,533.1**, mean 120,311. Re-run at 8 seeds: **16/16, +$14,980.2, mirror +$8,917.6**, mirror mean 119,522, worst pairing +$5,937 - no losing pairing at either sample size. Standalone episode **$175,559** against a field best of $175,862. Mechanism on an instrumented seed-0 mirror: berry production nights **101 -> 160 of a possible 160**, all watered, thirst deaths **27 -> 0**, `DIG` offers 2,414 -> 707, movement 4,302 -> 3,871, productive actions 2,309 -> 2,525, WATER 504 -> 640, HARVEST 242 -> 315, PASS 680 -> **935**. PASS rising while score rises is the point: the farm finishes its work and then idles, instead of starving its far tiles all season.
- **This reframes four earlier refusals.** "Labour supply is not the binding constraint" was measured correctly and diagnosed wrongly. Freeing actions failed three times (final-day pickup suppression, fertilizer-collection gating, `MIN_LOAD` batching) and a fourth (carrier-count fetch demand) because the freed actions became PASS. They became PASS because the dispatcher could not *route* them, not because there was no work: 2,414 `DIG` offers and 5,500 `WATER` offers were standing unserved at the time. Shorten the actions being taken before trying to free more of them.
- **Required pairing:** none. It is a pure reordering and it costs nothing at the market, which is why it clears a mirror that racing changes do not.
- **Reconsider if:** the job list grows a lot - the pass is O(band x idle) per assignment, ~30 jobs against ~14 units today. Greedy pair matching is also not *optimal* matching; a constructed 2x2 case is worse than the old rule (14 steps against 12) because ties resolve to the lowest unit index. Hungarian assignment is the upgrade path if this binds again.

### Measure the farm before theorising about it

- **Strategy:** Instrument a real game - action histogram, direction reversals, PASS causes, per-product revenue - before choosing a hypothesis.
- **Why it works:** Three consecutive plausible efficiency changes failed because the diagnosis was inherited rather than measured. One 30-second instrumented game replaced "movement is the bottleneck" with the actual numbers and pointed straight at the revenue side, where no experiment had ever looked.
- **Evidence:** The queued route-ownership hypothesis assumed re-targeting waste; measurement found 185 reversals in 3,462 moves (5.3%). PASS analysis found 71% of idle units were empty-handed with open jobs available, so idleness was a carrying constraint, not a work shortage. The revenue table then produced the +$1,503.9 winner on the first try.
- **Required pairing:** Throwaway instrumentation outside the agent (wrap `_assign` or `_market`), never edits to `main.py` or `verify.py` for measurement.
- **Reconsider if:** Never. This is cheaper than one rejected benchmark.

## Strategies that did not work (yet)

### Strawberry: five attempts, and the diagnosis was wrong for the first four (resolved)

- **Superseded by the worked entry above.** Kept for the shape of the mistake, which is worth more than the result. Four refusals blamed cash - "berry seed and livestock draw on the same money between days 6 and 13" - and every retry varied tile counts, slot costs, planting order or sell rules. None of those was ever the problem. The fifth attempt instrumented the failing game instead of theorising about it and found the farm ending at $78,140 with 200 berries sold and **ten of its eighteen animals starved to death**: the crop was stealing the wheat carriers, not the cash. One job priority.
- **The other thing the first three refusals missed:** they tested 8 and 12 tiles and all harvested exactly 4 units a tile, which is the *unfertilized* ceiling, and read that as the crop underperforming. `yield_units` caps at `max_yield` = 4 held, so four productions of +1 is four units however you harvest; a fertilized *and watered* production adds +2, and with a harvest between them the tile gives eight. The FERTILIZE engine only landed in v8, after the last refusal, so no strawberry test had ever run with it.
- **How to apply:** a repeatedly-failing hypothesis with a plausible story is where instrumentation pays best, not worst. Four rejected benchmarks cost more than the one 30-second probe that ended the argument.
- **The front-loaded-herd hypothesis this entry queued is now resolved and worked** - see "Buy the herd in an opening rush" in the worked section, +$18,552 with mirror +$18,468. It was, as suspected, about *when* the herd is bought and not about its species mix.
- **Best distinct next hypothesis: wheat as a late cash crop.** Suda sells **473 wheat for $20,648** against our 112 for $4,768, and Octavi Grau 455, both by digging the expired berry tiles over into ~57 wheat tiles between days 20 and 26 and selling into a market the town drains to $44-55. We hold `ENDGAME_WHEAT_TILES = 10`, treat wheat purely as feed, and `SELL_RULES` has no WHEAT entry at all. The refusal on record ("Doubling the late wheat floor", 1/8) raised that number to 20 under the *pre-berry* farm, where there were no expiring berry tiles to convert and no spare late crew; both conditions have changed.
- **Resolved 2026-08-12: tested at 60 tiles from day 16 and rejected, 2/16 at -$5,846.8, mirror -$4,846.7.** See "Wheat as a late cash crop" below. The tiles and the sales are real; they are paid for out of the berries.

### Wheat as a late cash crop (three variants, all rejected)

- **Attempt:** the field's late game. Suda sells 473 wheat for $20,648 and Octavi Grau 455 by breaking the tiles their expired berries vacate into ~57 wheat tiles on days 20-26; we sell 112 for $4,768. Raised `ENDGAME_WHEAT_TILES` from 10 to 60 and opened the window on day 16 instead of 20, so every tile berry decay frees goes back under wheat.
- **Evidence:** **2/16 at 8 seeds, -$5,846.8, mirror -$4,846.7**, all DONE. Demoting wheat's `WATER` job to priority 1 to protect the berries, on its own: 2/8, -$1,237.0, mirror -$3,518.5. Both together: 3/8, -$1,991.2, mirror -$3,761.8.
- **Why it failed in this pairing, measured on seed 6:** the mechanism works and is still a loss. PLANT 87 -> 122, wheat revenue $4,991 -> $7,537, feed purchases 142 -> 125 orders - against strawberry $45,598 -> $36,504 with `HARVEST` **flat at 257 against 258**. The same number of berry harvests carrying far fewer units each: 35 more priority-0 `WATER` jobs a day, on top of 527 `WATER` actions already, means berry tiles miss the watering on their production night and yield +1 rather than +2. **This farm is action-saturated, and an action spent on wheat returns about a fifth of the same action spent on a berry.**
- **And the fix for that is worse, which is the load-bearing half.** Protecting the berries by demoting wheat's water job loses on its own (mirror -$3,518.5): half-watered wheat dies into weeds and the feed bill returns as `BUY_PRODUCT`. Both directions lose, so `WHEAT_PER_ANIMAL = 0.75` beside `BERRY_TILES = 40` is a local optimum, not an accident.
- **Ruled out as the constraint while testing this:** the shed. Instrumented across a full v11 game it peaks at 77 of 100 (day 21), crosses `SHED_PRESSURE` twice, never overflows, and strands only 12 strawberry and 22 wheat at the last bell. Nothing is being silently discarded.
- **Test again only with:** actions that do not come out of the herd or the berries. The farm spends ~4,400 of ~7,000 actions a game walking and passes 535-680 times; a late crew with measured idle time, or a layout change that shortens the routes, is the missing pairing. Do not re-test this by adding tiles.

### Capacity and hiring demand are different questions (`PLANT_SLOTS`)

- **Lesson:** `PLANT_SLOTS` was read both as *how much of the crew a tile consumes* and as *how many hands to hire*. Halving it to make room for crops therefore halved the crew: 7 hands against the baseline's 11, and 16 of 40 strawberry seeds bought and never planted.
- **Fix that worked:** split into `PLANT_SLOTS` (capacity, 2) and `PLANT_LOAD` (hiring, 4). Crew back to 12-14, tiles planted 24 to 32. The field settles the capacity number: the leaders keep 14 animals and 54 plants on 11 hands, which is 2 slots a plant, not 4.
- **Note:** this is *not* the rejected "denser planning capacity" result. That one lowered `ANIMAL_SLOTS`, and animals cost $300-500 plus a `FEED_DAYS` reserve the moment they are planned. A plant costs $10-100.

### A fix that unblocks a constraint has to pay for what the constraint was suppressing

- **Lesson:** three times now, removing a limit has released spending the limit was quietly preventing, and the released spending cost more than the freed throughput earned. Unblocking `PLACE` doubled the herd and sent the freed cash into geese bought past their break-even (4/8 alone), and then into the exponential tail of the hire curve (still 4/8 with the geese fixed). Only when both downstream leaks were priced did it clear the gate at 8/8. See the worked entry above for the numbers.
- **How to apply:** before removing a bottleneck, ask what the farm will buy with the capacity, and check that purchase's margin at the day it will happen. Then measure the *spend* side of the instrumented game, not only the revenue side - both losing seeds here showed revenue up $16,745 and would have looked like wins on any revenue-only reading.

### Aggressive hiring as the sole repair for crop-heavy plans

- **Evidence:** Crop-heavy variants with higher hiring fractions/minimums still scored roughly 62,762 and 54,564 versus baselines around 81,000.
- **Why it failed in this pairing:** More hands did not fix poor task ordering, travel, or crop economics; labor was added without ensuring useful actions.
- **Test again only with:** A measured workload queue and utilization evidence showing the additional hands remove a specific bottleneck.

### Lower land-carrier cap by itself

- **Attempt:** Reduce land carriers to 3.
- **Evidence:** Scored 76,304 versus 78,400 on the screening seed (-2,096).
- **Why it failed in this pairing:** A global cap did not repair occupancy, route length, or task priority.
- **Test again only with:** An exact layout/route plan that demonstrates which land actions are unnecessary.

### Melon expansion by itself

- **Attempt:** Add 12 melon tiles.
- **Evidence:** Scored 72,840 versus 73,024 on the screening seed (-184), too small and negative to justify a full run.
- **Why it failed in this pairing:** The extra crop did not overcome its labor and space cost.
- **Test again only with:** Favorable replay market prices, low opponent melon supply, and idle crop labor.

### Water-only and late-wheat tweaks without the complete wheat economy

- **Evidence:** The best early screen won 4/8 and improved only +557 on average.
- **Why it failed in this pairing:** Action savings alone did not create enough revenue, and late wheat without a reserve/surplus policy was incomplete.
- **What changed later:** Alternate-day watering became useful when paired with 0.75 wheat tiles per animal, feed reservation, and surplus selling.

### Higher wheat ratios under the current herd balance

- **Attempts:** Ratios of 1.0, 1.25, and 1.5 wheat tiles per animal.
- **Evidence:** 1.0 produced about +3,957 in screening; 1.25 won 7/8 at +5,433 but averaged only 75,812; 1.5 won 7/8 at +4,455 and averaged 73,770. The 0.75 ratio won 8/8 and averaged 78,591 at +7,934.
- **Why they lost this pairing:** Extra wheat increasingly displaced the stronger stable herd/labor allocation.
- **Test again only with:** Replay evidence of higher wheat prices or feed demand, or a scheduler that can add crop throughput without reducing herd output.

### Doubling the late wheat floor under the greedy dispatcher

- **Attempt:** Raise only `ENDGAME_WHEAT_TILES` from 10 to 20 after day 20, leaving the validated season-long 0.75 ratio unchanged.
- **Evidence:** Won 1/8 and averaged 74,548.4 versus 76,163.0 (-1,614.6), with all benchmark statuses DONE. `py_compile` passed; the existing target assertion correctly failed because the candidate changed the expected late target without updating the test.
- **Why it failed in this pairing:** Replay PASS volume was aggregate slack, not ten tiles of route-local crop capacity. Extra watering, harvesting, replanting, and walking displaced more valuable cleanup and livestock work even though wheat ended at $44-$54 publicly.
- **Test again only with:** Route-zoned idle workers or a measured late queue showing crop jobs fit without displacing animal/cleanup actions. Late wheat is not universally bad; the current dispatcher cannot turn aggregate idleness into profitable field expansion.

### Hard two-quadrant cap without a compact layout

- **Attempt:** Stop after the first land expansion, saving the nominal $2,000 and $4,000 later purchases.
- **Evidence:** The agent occupied only 32.9 tiles on average (36 maximum) across 33 public replays, but the cap won 7/8 locally and improved just +1,327.9 rather than the required +5,000.
- **Why it failed in this pairing:** Later quadrants supplied additional shed-adjacent work zones; the baseline placed about six productive tiles in each, and concentrating the same farm in two quadrants increased travel enough to consume most of the $6,000 saving.
- **Test again only with:** A compact two-quadrant route plan, task zoning/batching, or a dynamic land rule whose measured travel savings repay each expansion. The capacity thesis was sound, but the existing greedy dispatcher was the wrong pairing.

### Hard three-quadrant cap without a conditional SE unlock

- **Attempt:** Retain NW/NE/SW and their three shed docks but never buy the $4,000 SE quadrant; six new public games peaked at only 32-35 productive tiles and used at most 5-6 productive SE tiles.
- **Evidence:** Won 5/8 and averaged 79,069.5 versus 78,021.1 (+1,048.4), with every status DONE and all local checks passing. Several pairings gained over $4,000, but three losses erased most of the fee saving.
- **Why it failed in this pairing:** Even a sparsely occupied fourth quadrant can be valuable as a shed-adjacent route zone. The hard cap saves cash in some market/layout conditions but cannot distinguish them from seeds where the SE dock repays its fee.
- **Test again only with:** A conditional or delayed fourth unlock based on measured occupancy around the first three docks and queued route pressure. Fewer quadrants are not universally bad; unconditional removal is too coarse.
- **Confirmed again 2026-08-11:** re-tested inside the 40-tile strawberry farm, where $4,000 is exactly the berry seed bill and the farm still ends with 89 bare tiles. Removing the cap did not restore the seeds it appeared to have damaged, so it is near-neutral there too - the fourth quadrant is neither the waste nor the fix it looks like.
- **Best distinct next hypothesis:** Delay the fourth land purchase until the existing three dock neighborhoods are saturated or measured work queues cannot clear, preserving the SE dock only in seeds where its throughput can repay $4,000.

### Multi-dock pickups without persistent route ownership

- **Attempts:** First send pickups round-robin across unlocked docks; later choose each pickup dock from the nearest actual FEED/PLACE destinations.
- **Evidence:** Blind round-robin lost 0/8 and averaged -3,967.1. Destination-selected docks still won only 1/8 and averaged 70,971.9 versus 74,836.4 (-3,864.5); every status was DONE.
- **Why they failed in this pairing:** A pickup's destination is not persistent state. On the next turn the greedy dispatcher can give that loaded carrier a different target, so even a correct initial dock does not create a stable end-to-end route.
- **Test again only with:** Nothing yet. The persistence half of this diagnosis was implemented and measured (see "Persistent per-unit job claims" below) and the re-targeting waste it assumed does not exist: 5.3% of moves reverse direction. Both dock failures are better explained by the single-dock layout being adequate than by missing route state, so do not queue another routing experiment without a measurement showing otherwise.

### Static 10-hand cap under the livestock scheduler (superseded)

- **Attempt:** Reduce `MAX_HANDS` from 16 to 10 after replays measured about $6,801 in hire costs and substantial daily PASS volume.
- **Evidence:** Won 6/8 but improved only +776.6 on average (77,214.1 versus 76,437.5), with all statuses DONE.
- **Why it failed in this pairing:** Aggregate idle actions did not identify which individual late hires were disposable; on some seeds the hard cap removed profitable throughput along with idle labor.
- **Superseded by `HIRE_MAX_WAGE = 144`** in the worked section above. The control was wrong, not the thesis: headcount is not what makes the last hands unprofitable, the `fib` wage is. Capping the marginal *wage* prices each hand instead of banning it, and it needed the herd-pipeline fix beside it to be worth anything at all (1/8 on its own).

### Exact unfed-count pickup demand under aggregate inventory accounting

- **Attempt:** Replace herd-sized wheat pickup demand with the number of current FEED jobs, also eliminating final-day phantom feed pickups.
- **Evidence:** Won 2/8 and averaged 72,897.4 versus 74,205.5 (-1,308.1), with every status DONE.
- **Why it failed in this pairing:** Total carried wheat is not the same as delivery capacity. A few distant units can hold enough wheat in aggregate while too few independently loaded carriers remain to feed the herd in parallel; the baseline's apparent overfill acts as a distribution buffer.
- **Test again only with:** Per-carrier route/coverage accounting or a final-day-only guard that preserves normal-day carrier parallelism. Exact item count is not universally bad; aggregate carrier state is the missing pairing.

### Static reduction of the cash feed reserve

- **Attempt:** Reduce `FEED_DAYS` from 10 to 8 because public replays retained 96.6% of purchased animals and the wheat loop supplies part of feed demand.
- **Evidence:** Won 3/8 and averaged 72,854.6 versus 71,839.0 (+1,015.6), with every status DONE; two pairings gained more than $6,600 while four lost, so the effect was strongly condition-dependent and far below the gate overall.
- **Why it failed in this pairing:** A fixed reserve cut releases useful growth capital when wheat supply is secure, but removes necessary insurance when timing, prices, or carrier throughput are worse. High aggregate survival does not identify which seed-level reserves are redundant.
- **Resolved 2026-08-12, and the answer was the calendar, not the inventory.** Both this and the "secured wheat" attempt below were season-long rules, and season-long is the wrong axis: cutting `FEED_DAYS` to 3 or 5 for the whole game swings a single seed by +$5k and -$17k, i.e. noise. The reserve only ever binds in the opening, where it is the sole thing freezing the herd - see the worked entry "Buy the herd in an opening rush" above, which cuts it to three days for days 0-8 only and is worth +$18,552. Do not re-test a season-long reserve rule.

### Treating all secured wheat as cash-reserve replacement

- **Attempt:** Keep the ten-day horizon but subtract every wheat unit already in the shed or on a carrier from the current herd's cash reserve; retain the full ten-day marginal reserve for new animals.
- **Evidence:** Won 5/8 and averaged 72,441.0 versus 71,400.1 (+1,040.9), with all statuses DONE. The public wheat-loop rating still rose from 602.7 to 659.6, and six new replays ended with 7-18 wheat, so the underlying wheat strategy remains validated even though this capital rule missed the gate.
- **Why it failed in this pairing:** A stored or carried unit is not equivalent to reliable future feed: it may already be committed to today's animals, stranded on a carrier, or unavailable when the next day's route begins. The change accelerated growth in favorable pairings but lost three games and stayed far below +3,000.
- **Test again only with:** Day-indexed feed coverage that deducts only wheat beyond current-day delivery needs, or harvest timing proven to cover the reserve horizon. Conditional reserve release is not universally bad; raw aggregate inventory is too coarse.

### Fixed cow-heavy herd under shared dynamic prices

- **Attempt:** Shift the herd target from 10% goose / 50% cow / 40% sheep to 10% / 70% / 20% because public replays showed higher final milk prices and more milk sold than wool.
- **Evidence:** Won 2/8 and averaged 71,856.9 versus 74,442.8 (-2,585.9), with every status DONE.
- **Why it failed in this pairing:** The observed milk advantage was endogenous to diversified supply; extra cows pushed the linear milk glut curve down, while removing sheep surrendered the wool hedge.
- **Test again only with:** Persistent replay-proven milk scarcity, favorable milk-shop unlocks, or a live price-sensitive species choice. A cow-heavy farm is not universally bad, but a fixed ratio ignores the shared market response.
- **Queued next hypothesis:** Destination-aware dock zoning: bind feed pickups to the dock nearest specific unfed animals and livestock pickups to the dock nearest their empty structures. This is distinct from the rejected blind round-robin dock change.

### Time-delayed fourth quadrant without a workload trigger

- **Attempt:** Keep three quadrants through day 14, then allow the normal $4,000 fourth-quadrant purchase from day 15 onward.
- **Evidence:** Public replays bought the fourth quadrant around day 11.4 with only 21.9 productive tiles, but the delayed candidate lost 0/8 and averaged $75,516.4 versus $77,639.6 (-$2,123.3); all statuses were DONE and local checks passed.
- **Why it failed in this pairing:** Calendar delay preserved cash but removed the SE shed dock precisely while the farm was growing. The lost early routing throughput exceeded the financing benefit in every deterministic pairing.
- **Test again only with:** A live, route-local workload signal that proves three docks can clear the queue, or a layout that supplies equivalent shed access. A delayed unlock is not universally bad; time alone is not evidence that the dock is dispensable.
- **Best distinct next hypothesis:** Disable wheat pickup jobs only on the final day, when FEED is already intentionally disabled. This isolates the safe condition from the rejected all-season exact-demand change and directly targets the 518 units of final unsold wheat carried across 42 Akshay replay records.

### Final-day-only wheat pickup suppression

- **Attempt:** Set wheat fetch demand to zero only on day 29, when the scheduler already creates no FEED jobs.
- **Evidence:** Won 6/8 with all statuses DONE and averaged $76,323.8 versus $75,758.0 (+$565.8). Local checks passed, but the result missed both gate thresholds.
- **Why it failed in this pairing:** The removed work was genuinely useless and usually beneficial, but the baseline already liquidated almost every premium product. Freed carriers often had no valuable reachable cleanup job, so the isolated gain was too small and two pairings still lost.
- **Test again only with:** A paired final-day liquidation/return route that can convert the freed carriers into at least $3,000, or stronger evidence of stranded premium inventory. Final-day suppression is not harmful in general; it is incomplete by itself.
- **Best distinct next hypothesis:** Stop collecting fertilizer while its live price is below the existing $50 sell floor. Akshay spent 12,123 collection actions across 42 replay records, while fertilizer finished at a mean $16 and the policy already refuses normal sales below $50; a live price gate can remove the larger self-created low-value queue and resume automatically if scarcity restores value.

### Live-price gating of fertilizer collection

- **Attempt:** Schedule `COLLECT_FERTILIZER` only while the live fertilizer quote is at least the existing $50 normal-sale floor.
- **Evidence:** Lost 0/8 with all statuses DONE and averaged $68,465.0 versus $76,900.6 (-$8,435.6). Both local checks passed.
- **Why it failed in this pairing:** The current quote undervalues inventory that can be held and sold after town demand or under shed pressure. More importantly, deleting the collection job did not manufacture another route-local productive job; it discarded a major revenue stream and exposed idle capacity.
- **Test again only with:** A forecast of future fertilizer demand and an immediately available higher-value job for the same worker. Low current price does not make collection universally bad; the missing pairing is opportunity cost plus future-value accounting.
- **Best distinct next hypothesis:** Preserve fertilizer production and attack the measured 3,460 movements plus 676 logistics actions directly with persistent per-hand route-zone ownership: a carrier that picks up at one dock must remain eligible only for FEED/PLACE jobs in that dock's zone for the rest of the day. This is the missing pairing identified by both failed multi-dock attempts and is distinct from stateless dock selection. **Resolved 2026-08-11:** implemented, measured, and rejected - see below. The fertilizer half of the diagnosis was right, but the fix was to stop hoarding it, not to reroute the crew.

### Persistent per-unit job claims

- **Attempt:** Keep each unit walking to the tile it claimed until it arrives or the job disappears, instead of rebuilding every assignment from scratch each turn. This is the root-cause form of the queued route-ownership hypothesis, applied to all jobs rather than only carriers.
- **Evidence:** Won 1/8 and averaged $73,671.3 versus $75,956.8 (-$2,285.5), every status DONE. Instrumentation then showed only 185 opposite-direction moves out of 3,462 (5.3%), so there was almost no thrash to recover.
- **Why it failed in this pairing:** The premise was wrong, not the implementation. Recomputing assignments every turn is adaptivity, not waste: a claimed unit is withheld from a nearer or more urgent job that appeared after it set off.
- **Test again only with:** A measured reversal rate above roughly 20%. Persistence is not universally bad; there is simply nothing here for it to fix.

### Removing logistics waste without a job to replace it

- **Attempt:** Batch shed pickups into whole loads (`MIN_LOAD = 3`) after measuring 499 PICKUP actions against 308 actual deliveries, caused by demand being recomputed against instantaneous carried stock so every consumed wheat reopens a one-item shortfall.
- **Evidence:** The mechanism worked - PICKUP fell 499 to 185 - but PASS rose 1,379 to 1,532 and productive actions fell 2,175 to 1,823. Won 2/8, averaging $71,912.0 versus $73,833.1 (-$1,921.1), every status DONE.
- **Why it failed in this pairing:** Freed actions became PASS, not money, and a thinner carrier spread cost feed throughput (FEED 289 to 275). This was read for four experiments as **labour supply is not the binding constraint on this farm**. That reading was wrong and is corrected by the closest-pair dispatch entry above: the freed actions became PASS because the dispatcher could not route them, while 5,500 `WATER` and 2,414 `DIG` offers a game stood unserved. Shorten the actions already being taken before trying to free more of them.
- **Test again only with:** A productive job the freed carrier can reach in the same turn.

### Denser planning capacity, even with hiring left alone

- **Attempt:** Add `PLAN_ANIMAL_SLOTS = 7` used only by the build decision, leaving `load` and hiring on `ANIMAL_SLOTS = 9`. This was the explicitly named missing pairing for the old optimistic-capacity failure, backed by 1,379 measured PASS actions a game.
- **Evidence:** Cheap two-seed screen lost 0/4, averaging $67,498.0 versus $73,887.3 (-$6,389.3), every status DONE. Pruned before a full benchmark.
- **Why it failed in this pairing:** This reclassifies the earlier `ANIMAL_SLOTS = 6` result. Dense planning is bad on its own merits, not merely because it starved the crew: extra heads cost cash and the `FEED_DAYS` reserve immediately, their chores spread further across the map, and the idle actions are not located where the new structures would stand.
- **Test again only with:** Evidence that PASS actions occur adjacent to the tiles the new structures would occupy. Aggregate idleness has now failed as a signal four separate times.
- **Best distinct next hypothesis:** Stay on the revenue side, which paid immediately. MILK and WOOL still end at $238 and $247, i.e. scarce at the final bell, under a 2-per-turn cap and $110/$130 floors. Test raising those caps or lowering those floors so premium output is not still queued when the season ends.

### Gating the fertilize decision, by price or by calendar

- **Attempts:** Fertilize only while `FERTILIZER < 2 x WHEAT` (the exact break-even, since one fertilizer yields two wheat); and separately, only from day 4 onward.
- **Evidence:** The live-price gate scored 2/8 at -$926; the day-4 gate screened at +$464/+$4,033 on seed 0 and -$7,161/-$7,239 on seed 1. Ungated scores 14/16 at +$3,566.5.
- **Why they failed in this pairing:** The break-even arithmetic is right and still loses. A live comparison flickers across the threshold as prices move, and a fertilize job abandoned mid-window is walking that buys nothing - the same timing sensitivity that makes priorities 1 and 2 lose. The day gate is monotone but blocks the early tiles where the compounding starts.
- **Test again only with:** A latching gate that never switches back off once it opens. Do not re-test a per-turn recomputed condition on `FERTILIZE`; three separate variants have now failed on timing rather than on economics.

### Reading single-seed differences between variants as signal

- **Attempt:** Diagnosing seed 1, the one seed where fertilizing loses (both seats, about -$5,000), by comparing variants seed by seed.
- **Evidence:** Day-by-day tracing showed a real mechanism - fertilizer is still worth $89 on day 10, so early diversion costs cash that compounds into two fewer animals by day 15 and never recovers. But every fix aimed at seed 1 lost more elsewhere than it recovered there, and variants reshuffled which seeds won.
- **Why it misleads:** Both agents trade into one shared market, so any perturbation moves the whole price path and the opponent's behaviour with it. Individual seeds are chaotic; only the aggregate over many seeds is stable. Four seeds gave 6/8 (+$2,441) for a change that eight seeds scored at 14/16 (+$3,566.5).
- **Test again only with:** Eight seeds or more before believing a per-seed story. The 4-seed benchmark is a screen, not a verdict, for changes that move market prices.
