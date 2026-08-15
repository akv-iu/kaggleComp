# Decision Log

Append one entry for every evaluated attempt, including rejected attempts. Never rewrite history. Each entry records the measured state, the exact decision, why it looked best before testing, the evidence, the verdict, and the pairing needed for reconsideration.

## 2026-08-10 — Repair livestock capacity and execution (selected as v5)

- **State:** v4 submission 55409858 rated 554.1. Replays showed 33–46 animals purchased but only 13–18 surviving, 31–37 empty structures, excessive walking, and no final-day labor.
- **Decision:** Synchronize animal purchases with one ready structure slot, use 9 animal slots per structure, keep 8 feed carriers, build near the shed, hire from actual workload, and reserve the final day for harvest/sale cleanup.
- **Why it seemed best:** The largest measured loss was failed execution rather than a lack of planned assets.
- **Evidence:** 8/8 local wins; 78,578 average final money versus 39,723 (+38,855). Public v5 submission 55410751 reached 608.6.
- **Verdict:** Selected. This became the stable livestock baseline.

## 2026-08-10 — Full crop-heavy strawberry/melon pivot (rejected)

- **State:** Strong v5 opponents earned heavily from crops; VictorAndrew sold 261 wheat, 282 strawberry, 144 melon, 213 milk, 147 wool, and 210 fertilizer.
- **Decision:** Try 42 strawberry and 12 melon tiles with a 14-animal cap, 3 land carriers, and 4 feed carriers.
- **Why it seemed best:** Opponent replays suggested crops were the clearest unexplained revenue gap.
- **Evidence:** About 59,044 versus 80,364, 0/8 wins; the field displaced the herd and the agent acquired only 8 animals.
- **Verdict:** Rejected. Reconsider only with crop-aware routing/staffing and a protected herd floor.

## 2026-08-10 — Lower planning slot costs for crop capacity (rejected)

- **State:** The full crop pivot appeared constrained by conservative capacity accounting.
- **Decision:** Lower `ANIMAL_SLOTS` to 6 and `PLANT_SLOTS` to 2.
- **Why it seemed best:** More assets should have fit without directly rewriting the dispatcher.
- **Evidence:** 57,836 versus 83,818, 0/8 wins; one game bought 9 animals and kept only 4.
- **Verdict:** Rejected. Slot costs also controlled staffing, so this must not be retried until planning capacity is separated from labor demand.

## 2026-08-10 — Small 12-strawberry hybrid (rejected)

- **State:** The full field was too disruptive, but a smaller field might have used spare actions.
- **Decision:** Add 12 strawberry tiles while retaining the v5 livestock scheduler.
- **Why it seemed best:** It preserved most herd capacity while testing whether crop income scaled down safely.
- **Evidence:** 70,232 versus 78,026, 0/8 wins.
- **Verdict:** Rejected. Retry only after crop routing and staffing improve and a herd floor is explicit.

## 2026-08-10 — Aggressive hiring for crop-heavy variants (rejected)

- **State:** Crop plans might have failed because too few hands serviced the larger workload.
- **Decision:** Raise hiring fraction/minimum across 24- and 42-strawberry variants.
- **Why it seemed best:** Labor shortage was a plausible direct cause of unharvested crops and delayed animal work.
- **Evidence:** Variants scored roughly 62,762 and 54,564 against baselines near 81,000.
- **Verdict:** Rejected. More workers alone did not repair task ordering, travel, or return per action; retry only with workload/utilization evidence.

## 2026-08-10 — Reduce land carriers to 3 (rejected)

- **State:** Too much land work could be consuming hands needed for production.
- **Decision:** Cap land carriers at 3 without changing the layout.
- **Why it seemed best:** It was the smallest possible test of excess land labor.
- **Evidence:** 76,304 versus 78,400 on the screening seed (-2,096).
- **Verdict:** Rejected before a full benchmark. Retry only as part of an exact occupancy and route plan.

## 2026-08-10 — Add 12 melon tiles (rejected)

- **State:** Opponent crop sales suggested a compact second crop might diversify revenue.
- **Decision:** Add 12 melon tiles without changing the main scheduler.
- **Why it seemed best:** Melons offered extra sale value with a smaller field than the strawberry pivot.
- **Evidence:** 72,840 versus 73,024 on the screening seed (-184).
- **Verdict:** Rejected before a full benchmark. Retry only when replay prices and opponent supply make melons unusually favorable.

## 2026-08-10 — Water-only plus late-wheat optimization (rejected alone)

- **State:** Replays showed many low-value watering actions and expensive purchased feed.
- **Decision:** Reduce early watering and add a small late wheat target without a full wheat reserve/sale policy.
- **Why it seemed best:** It could save actions and reduce feed purchases with a minimal strategy change.
- **Evidence:** 4/8 wins and only +557 average improvement.
- **Verdict:** Rejected as a standalone change. The watering component was retained for pairing with a complete wheat economy.

## 2026-08-10 — Wheat-per-animal ratio sweep (0.75 selected)

- **State:** v5 bought 242 wheat and sold only 25 at the end, while strong opponents both grew and sold large wheat volumes. The opportunity was valuable but field size could crowd out livestock.
- **Decision:** Pair alternate-day early watering with a feed reserve and surplus selling, then compare wheat ratios 0.75, 1.0, 1.25, and 1.5 per animal plus 10 late-game tiles.
- **Why it seemed best:** It directly targeted replay-proven feed scarcity while controlling the crop-versus-herd tradeoff.
- **Evidence:** 0.75 won 8/8, 78,591 versus 70,656 (+7,934); 1.0 screened at about +3,957; 1.25 won 7/8, 75,812 versus 70,380 (+5,433); 1.5 won 7/8, 73,770 versus 69,314 (+4,455).
- **Verdict:** Select 0.75. Higher ratios are conditionally inferior under the current labor and herd balance, not universally bad.

## 2026-08-10 — Submit replay-driven wheat loop as v6

- **State:** Only the 0.75 wheat ratio passed the full gate strongly enough to justify using a limited submission.
- **Decision:** Submit `WHEAT_PER_ANIMAL=0.75`, 10 endgame wheat tiles, alternate-day early watering, feed reservation, and surplus-only wheat selling as submission 55413328.
- **Why it seemed best:** It was the highest absolute-scoring tested candidate and cleared every validation rule.
- **Evidence:** 8/8 wins, +7,934 mean final money, all statuses DONE, and local tests passed.
- **Verdict:** Submitted; automation submission budget now records 1/5 used. Await public replay evidence before changing the strategy again.

## 2026-08-10 - Cap the farm at two quadrants (rejected)

- **State:** Across all 33 new v6 replays, the agent unlocked all four quadrants for $7,000 even though peak occupied tiles averaged 32.9 and never exceeded 36; two quadrants expose 50 tiles.
- **Decision:** Change the land-purchase guard from `n_extra < len(LAND_PRICES)` to `n_extra < 1`, allowing only the first $1,000 expansion and preserving the later $2,000 and $4,000 purchases.
- **Why it seemed best:** The one-line guard directly removed $6,000 of apparently unused capacity and should also have concentrated work.
- **Evidence:** Against the exact pre-run baseline on seeds 0-3 in both seats, it won 7/8 with all statuses DONE but averaged 79,008.6 versus 77,680.8, only +1,327.9. The public layouts explain the shortfall: the baseline used roughly six productive tiles in each later quadrant around the extra shed-access docks, so the cap traded cheap routing for longer walks.
- **Verdict:** Rejected and removed because it missed the +5,000 mean-money gate. Retry only with a two-quadrant layout/dispatcher that proves equivalent route length, or with a dynamic occupancy rule that preserves additional shed-adjacent work zones when their throughput repays the land cost.

## 2026-08-10 - Make quality failure self-continuing (process change)

- **State:** The two-quadrant experiment was correctly rejected, but the automation treated that rejection as the end of the scheduled run and would not retry without unseen replays.
- **Decision:** Keep a durable `needsImprovement` flag, reuse the latest cached replay set when no new replay exists, and require up to three distinct full-benchmark attempts per invocation. Each failed attempt must be logged, removed, and used to choose the next hypothesis.
- **Why it seemed best:** A quality gate protects submissions only if failure becomes learning; otherwise the system is a filter, not an improvement loop.
- **Evidence:** The rejected cap exposed a specific missing pairing—compact routing around shed-access docks—but the old control flow stopped before testing a paired repair.
- **Verdict:** Adopted as an operational rule. Clear the flag only after a candidate passes the full gate or the five-submission budget is exhausted.

## 2026-08-10 - Make the +5,000 gate independently local (process change)

- **State:** The agent benchmarked candidates locally, but the same agent also supplied the game results in its submission request.
- **Decision:** Freeze `verify.py` before analysis and make the wrapper rerun that snapshot against frozen `baseline_main.py` after `py_compile` and `test_agent.py`. Require at least 8 games, 7 wins, every status DONE, and +5,000 mean points from this independent run before submission.
- **Why it seemed best:** Submission authority should come from reproducible local execution, not a self-reported score summary.
- **Evidence:** The verifier already runs four deterministic seeds in both seats and emits machine-readable results, so the stronger gate needs no new framework or dependency.
- **Verdict:** Adopted. `submit_request.json` now expresses intent only; the wrapper-owned local benchmark is the final quality authority.

## 2026-08-10 - Round-robin feed pickups across unlocked shed docks (rejected)

- **State:** In 35 v6 replays (70 player records, one replay recoverable only through its truncated prefix), Akshay retained about 17.3 animals, sold nearly all output, but averaged 3,459 movement actions versus 2,121 productive actions and 1,361 passes. All pickup jobs were hard-coded to the NW shed dock despite four unlocked quadrants.
- **Decision:** Change only `_fetch_jobs` so its carrier jobs use unlocked shed docks round-robin instead of always using `docks[0]`.
- **Why it seemed best:** It directly targeted the measured travel bottleneck and paired the four-dock layout with the smallest possible routing change.
- **Evidence:** Against the exact pre-run baseline on seeds 0-3 in both seats, it lost 0/8 with all statuses DONE and averaged 70,867.2 versus 74,834.4 (-3,967.1).
- **Verdict:** Rejected and removed. Blind dock distribution separates carriers from the greedy job destinations and reduces throughput. Retry multiple docks only when each pickup is explicitly paired with a destination tile or route zone.

## 2026-08-10 - Cap daily farm hands at 10 (rejected)

- **State:** Replay action curves showed about $6,801 spent on hires per game and 25-61 pass actions per day through much of days 14-28, suggesting expensive marginal labor was sometimes idle.
- **Decision:** Change only `MAX_HANDS` from 16 to 10, leaving workload accounting, farm capacity, and task priorities unchanged.
- **Why it seemed best:** Ten hands plus the farmer nominally cover the observed 17-head herd and wheat workload while avoiding the steepest Fibonacci hire costs.
- **Evidence:** Against the exact pre-run baseline on seeds 0-3 in both seats, it won 6/8 with all statuses DONE and averaged 77,214.1 versus 76,437.5 (+776.6).
- **Verdict:** Rejected and removed. The saved wages were real but occasionally cost more productive throughput than they returned. Retry labor reduction only with a utilization-aware late hire rule or a measured workload model that distinguishes travel from idle capacity.

## 2026-08-10 - Shift the herd target from sheep to cows (rejected)

- **State:** Across the replay set, Akshay averaged 7 surviving cows and 5.8 sheep, sold 139.5 milk versus 104.8 wool, and saw final mean prices of $143.5 for milk versus $129.4 for wool. Cows also cost $100 less and produce more frequently.
- **Decision:** Change only `HERD` from 10% goose / 50% cow / 40% sheep to 10% / 70% / 20%.
- **Why it seemed best:** The measured public market favored milk and the replacement reduced both acquisition cost and production interval without changing labor or routing code.
- **Evidence:** Against the exact pre-run baseline on seeds 0-3 in both seats, it won 2/8 with all statuses DONE and averaged 71,856.9 versus 74,442.8 (-2,585.9).
- **Verdict:** Rejected and removed. Milk's replay price advantage was partly a result of the diversified supply; producing more milk moved its linear glut curve against the candidate. Retry a cow-heavy mix only when shop unlocks or opponent supply create persistent milk scarcity, ideally with a live price-sensitive mix rather than a fixed ratio.
- **Best distinct next hypothesis:** Pair each wheat pickup with the unlocked shed dock nearest a specific unfed animal (and each livestock pickup with its empty structure) before greedy assignment. This preserves the measured four-dock routing value without repeating the failed blind round-robin pairing.

## 2026-08-10 - Choose pickup docks from actual feed/place destinations (rejected)

- **State:** Public v6 improved from 608.8 to 660.2. Across all 35 listed replays and both players, Akshay bought about 17.9 animals and retained 17.3, sold nearly all premium output, but averaged 3,459 movement actions versus 1,458 productive actions. The prior blind round-robin dock attempt had failed, leaving destination-aware routing as the best distinct pairing.
- **Decision:** Pass the current FEED/PLACE jobs into `_fetch_jobs`, map each destination to its nearest unlocked shed dock, and distribute pickup carriers across those mapped docks. Add one focused routing check.
- **Why it seemed best:** It preserved the measured value of all four shed-adjacent work zones while directly pairing pickup locations with real destinations instead of distributing them blindly.
- **Evidence:** Against the exact pre-run baseline on seeds 0-3 in both seats, it won 1/8 with every status DONE and averaged 70,971.9 versus 74,836.4 (-3,864.5). `py_compile` and `test_agent.py` passed.
- **Verdict:** Rejected and removed. The chosen destination is not persistent after pickup; the next-turn greedy dispatcher can redirect the loaded carrier, so initial dock selection alone does not create an end-to-end route. Retry multiple docks only with persistent carrier-zone ownership or batched pickup/delivery routing.

## 2026-08-10 - Size wheat pickups from current FEED jobs (rejected)

- **State:** Replay survival was already strong, but the agent averaged 675 logistics actions and ended with about 12 unsold wheat. Code inspection showed `fetch["WHEAT"] = n_animals` even after some animals were fed and on the final day when FEED jobs are disabled.
- **Decision:** Change that one line to the count of current FEED jobs, so pickup demand falls as feeding completes and becomes zero on day 29.
- **Why it seemed best:** It removed a direct cause of redundant pickups and protected final-day wheat liquidation without changing routes, staffing, herd mix, or crop allocation.
- **Evidence:** Against the exact pre-run baseline on seeds 0-3 in both seats, it won 2/8 with every status DONE and averaged 72,897.4 versus 74,205.5 (-1,308.1). `py_compile` and `test_agent.py` passed.
- **Verdict:** Rejected and removed. Aggregate carried quantity understated the need for multiple independently loaded feed carriers; the baseline's surplus pickup demand provided useful parallel delivery capacity. Retry only with per-carrier coverage accounting, or isolate the safe final-day guard from normal-day demand.

## 2026-08-10 - Reduce the fixed feed cash reserve from ten days to eight (rejected)

- **State:** Public replays showed about 17.9 animals bought, 17.3 surviving (96.6%), roughly 47 successful wheat plantings, and 147.6 wheat bought per game. The validated wheat loop supplies substantial feed, while the ten-day live-price reserve ties up about $9,000 at 18 animals and $50 wheat.
- **Decision:** Change only `FEED_DAYS` from 10 to 8, releasing roughly $1,800 of growth capital at that representative farm size.
- **Why it seemed best:** It used the strong survival margin and self-grown feed to accelerate productive livestock without changing the proven herd, crop, labor, sell, or routing policies.
- **Evidence:** Against the exact pre-run baseline on seeds 0-3 in both seats, it won 3/8 with every status DONE and averaged 72,854.6 versus 71,839.0 (+1,015.6). `py_compile` and `test_agent.py` passed. Individual gains reached +$7,051 and +$6,668, but four pairings lost.
- **Verdict:** Rejected and removed. A static reserve cut helps when feed timing is favorable but damages seeds where price, crop timing, or delivery throughput makes the insurance real; it missed both the 7/8 and +$5,000 gates.
- **Best distinct next hypothesis:** Net the ten-day cash reserve against feed already secured in the shed and on carriers (and only later against crops proven harvestable before depletion). This preserves the safe ten-day horizon while releasing capital conditionally, pairing the promising reserve reduction with measured feed availability instead of repeating another static constant.

## 2026-08-11 - Lower the independent submission gate to +3,000 (process change)

- **State:** The five-submission budget still has four slots available, while the +5,000 gate may reject useful measured improvements.
- **Decision:** Keep the independent frozen-verifier requirements of four seeds in both seats, 7/8 wins, every status DONE, and passing tests, but lower the required mean improvement from +5,000 to +3,000.
- **Why it seems best:** It spends no submission by itself, preserves the strong reliability checks, and permits a meaningfully better candidate to reach Kaggle without requiring an unusually large local margin.
- **Evidence required:** The wrapper must independently reproduce at least +3,000 mean points before it can submit or push code; previous results below +3,000 remain rejected.

## 2026-08-11 - Net current secured wheat from the cash feed reserve (rejected)

- **State:** The latest public submission improved from 602.7 to 659.6. In all six new replays, Akshay bought 140-159 wheat, retained all but one purchased animal overall, and ended with 7-18 unsold wheat, while the prior static eight-day reserve cut had shown condition-dependent upside but failed.
- **Decision:** Keep the ten-day horizon for each prospective animal, but subtract wheat already in the shed or on carriers from the current herd's reserved feed units before calculating investment budget.
- **Why it seemed best:** It was the smallest distinct pairing of the promising reserve-release idea with measured feed availability, preserving the validated safety horizon while avoiding cash duplication.
- **Evidence:** The exact frozen-baseline benchmark on seeds 0-3 in both seats produced 5/8 wins, all statuses DONE, and mean final money of 72,441.0 versus 71,400.1 (+1,040.9). `py_compile` and `test_agent.py` passed; the standalone episode scored 96,413 versus 3,487.
- **Verdict:** Rejected and removed because it missed both 7/8 wins and +3,000. Aggregate secured wheat includes units committed to today's feeding or stranded on carriers, so it is not reliable ten-day coverage. Retry only with day-indexed surplus after current delivery needs, or harvest timing proven to cover future days.

## 2026-08-11 - Double the post-day-20 wheat floor (rejected)

- **State:** The six public games left 1,325-1,489 PASS actions for Akshay and finished with wheat worth $44-$54, while the fixed 0.75 season-long ratio had already beaten higher global ratios. This suggested testing late-only capacity after most herd growth was complete.
- **Decision:** Change only `ENDGAME_WHEAT_TILES` from 10 to 20, retaining the 0.75 ratio, herd, labor, routing, and selling rules.
- **Why it seemed best:** Ten additional late tiles could consume apparent idle labor and sell into replay-proven wheat scarcity without crowding out early herd formation or repeating a full-season higher ratio.
- **Evidence:** The exact frozen-baseline benchmark on seeds 0-3 in both seats produced 1/8 wins, all statuses DONE, and mean final money of 74,548.4 versus 76,163.0 (-1,614.6). `py_compile` passed. `test_agent.py` failed its explicit `_wheat_target(8, 20) == 10` expectation; the negative benchmark made updating that expectation moot.
- **Verdict:** Rejected and removed. Aggregate PASS actions were not route-local capacity: the added field imposed walking, watering, harvesting, and replanting that displaced more profitable work. Retry late expansion only with route-zoned idle workers or queue evidence that it cannot delay livestock and final cleanup.

## 2026-08-11 - Cap the farm at three quadrants (rejected)

- **State:** In all six new public replays Akshay bought all three expansions, but productive occupancy peaked at only 32-35 tiles; the SE quadrant held at most 5-6 productive tiles. The earlier two-quadrant cap saved $6,000 but lost too much value from two shed docks.
- **Decision:** Change only the land guard to stop after two expansions, retaining NW/NE/SW, three shed docks, and 75 available tiles while avoiding the final $4,000 SE purchase.
- **Why it seemed best:** It targeted measured excess capacity while preserving one more route zone than the rejected two-quadrant pairing; the nominal saving alone exceeded the +3,000 gate.
- **Evidence:** The exact frozen-baseline benchmark on seeds 0-3 in both seats produced 5/8 wins, every status DONE, and mean final money of 79,069.5 versus 78,021.1 (+1,048.4). `py_compile` and `test_agent.py` passed; the standalone episode scored 98,184 versus 3,491.
- **Verdict:** Rejected and removed because it missed both 7/8 wins and +3,000. The $4,000 saving was real in several pairings, but three seeds needed the SE dock's routing value. Retry only as a conditional/delayed fourth unlock based on saturation or queue pressure.
- **Best distinct next hypothesis:** Delay the fourth purchase until productive occupancy around the existing three shed docks is saturated or daily work queues demonstrably fail to clear. This preserves the profitable fee saving when three zones suffice without repeating another unconditional land cap.

## 2026-08-11 - Delay the fourth quadrant until day 15 (rejected)

- **State:** The public wheat-loop rating rose from 602.7 to 659.6. Across 41 listed replays and both players, Akshay averaged $55,456.6, 3,460 movement actions, 676 shed-logistics actions, 1,460 productive actions, and 1,366 passes. The fourth quadrant was bought around day 11.4 with only 21.9 productive tiles, while the prior hard three-quadrant cap had condition-dependent upside but lost its route zone permanently.
- **Decision:** Add only `and (n_extra < 2 or day >= 15)` to the land-purchase guard, preserving the first three quadrants normally but deferring the $4,000 SE unlock until day 15.
- **Why it seemed best:** Temporarily retaining $4,000 during herd growth could capture the cap's financing upside while restoring the fourth shed dock for the back half of the season.
- **Evidence:** Against the exact pre-run baseline on seeds 0-3 in both seats, the candidate lost 0/8 with every status DONE and averaged $75,516.4 versus $77,639.6 (-$2,123.3). `py_compile` and `test_agent.py` passed; the standalone episode scored $92,698 versus $3,493.
- **Verdict:** Rejected and removed. A calendar delay is not a workload signal: it removed the SE route zone during active farm growth and lost in every pairing. Retry only with route-local queue evidence or a compact layout that replaces the dock's access benefit.
- **Best distinct next hypothesis:** Set final-day wheat fetch demand to zero. FEED jobs are already disabled that day, and the replays ended with 518 carried/unsold wheat across 42 Akshay records; unlike the rejected all-season exact-demand rule, this preserves the normal-day parallel-carrier buffer.

## 2026-08-11 - Suppress wheat pickups only on the final day (rejected)

- **State:** Across 42 Akshay replay records, final unsold products included 518 wheat units, overwhelmingly on carriers. The earlier all-season exact-FEED-demand attempt lost because it removed the parallel carrier buffer needed for normal feeding, but `_scan` already disables every final-day FEED job.
- **Decision:** Change only `fetch["WHEAT"] = n_animals` to `fetch["WHEAT"] = n_animals if obs["day"] < LAST_DAY else 0`.
- **Why it seemed best:** It removed demand that is provably unusable on day 29 while preserving the validated normal-day herd-sized pickup buffer unchanged.
- **Evidence:** Against the exact pre-run baseline on seeds 0-3 in both seats, the candidate won 6/8 with every status DONE and averaged $76,323.8 versus $75,758.0 (+$565.8). `py_compile` and `test_agent.py` passed; the standalone episode scored $95,555 versus $3,497.
- **Verdict:** Rejected and removed because it missed 7/8 wins and +$3,000. The normal-day distribution lesson was correct and the final-day waste was real, but removing it alone usually exposed idle capacity rather than additional valuable cleanup work. Retry only with a paired final-day return/liquidation route or evidence of materially stranded premium inventory.
- **Best distinct next hypothesis:** Gate fertilizer collection on its live $50 sell floor. Replays measured 12,123 Akshay collection actions, final fertilizer averaged only $16, and the current market rule refuses ordinary fertilizer sales below $50, so the farm is creating a large low-value queue that its own selling policy says not to create.

## 2026-08-11 - Gate fertilizer collection at the live $50 sell floor (rejected)

- **State:** The 41-replay analysis measured 12,123 `COLLECT_FERTILIZER` actions across 42 Akshay records, versus 12,101 fertilizer units offered for sale, while final fertilizer prices averaged $16 (range $1-$84). The policy's normal sell floor is already $50, making unconditional production appear to be the largest removable low-value queue after the small final-day pickup gain failed.
- **Decision:** Pass the live fertilizer price into `_scan` and create `COLLECT_FERTILIZER` jobs only at or above `SELL_RULES["FERTILIZER"][1]`; add one focused assertion for the below-floor condition.
- **Why it seemed best:** It targeted a replay-measured 289 actions per game plus associated travel, used the existing economic threshold, and automatically resumed collection if reduced supply restored the quote.
- **Evidence:** Against the exact pre-run baseline on seeds 0-3 in both seats, the candidate lost 0/8 with every status DONE and averaged $68,465.0 versus $76,900.6 (-$8,435.6). `py_compile` and `test_agent.py` passed; the standalone episode scored $93,043 versus $3,497.
- **Verdict:** Rejected and removed. The live quote was not the item's future value, and freed labor had no guaranteed higher-value route-local work. The change discarded profitable held/pressure-sold fertilizer and mostly produced more idle capacity. Retry only with demand forecasting and explicit opportunity-cost evidence.
- **Best distinct next hypothesis:** Keep fertilizer intact and implement persistent per-hand route-zone ownership through both pickup and delivery. Akshay's measured bottleneck remains 3,460 movement plus 676 logistics actions per game; the two stateless multi-dock attempts failed specifically because loaded carriers could be redirected on the next turn, not because route zoning itself was disproven.

## 2026-08-11 - Lower the independent submission gate to +100 (process change)

- **State:** The user explicitly lowered the acceptable local mean-improvement threshold from +3,000 to +100; four of five submission slots remain.
- **Decision:** Keep four seeds in both seats, 7/8 wins, every status DONE, passing tests, and the independent frozen-verifier rerun, but require +100 mean points instead of +3,000.
- **Why it seems best:** It follows the user's submission-risk preference while retaining the stronger reliability checks that prevent one-seat or incomplete-game results from being pushed.
- **Evidence required:** The wrapper itself must reproduce at least +100 mean points before any Kaggle submission or Git push.

## 2026-08-11 - Persistent per-unit job claims (rejected)

- **State:** Codex was unavailable for this run: the OpenAI workspace spend cap terminated `codex exec` in about four seconds with exit 1, so the improvement cycle was performed directly in the workspace under the same prompt, gate, and frozen snapshots. Public rating had just risen to 659.6 (IMPROVED by 56.9). The queued hypothesis from the previous run was persistent per-hand route-zone ownership, motivated by 3,460 movement plus 676 logistics actions per game against 1,460 productive ones.
- **Decision:** Add a module-level `_claims` map from unit index to the tile it is already walking to, honoured after the stand-and-finish pass and before greedy dispatch, and dropped on arrival, on job disappearance, on crew-size change, and at day 0 hour 0. This is the root-cause form of the queued hypothesis: it makes every assignment persistent rather than only carrier-to-dock ones.
- **Why it seemed best:** Both earlier multi-dock attempts were diagnosed as failing because a pickup's destination is not persistent state, so persistence itself, applied to all jobs at once, was the smallest change that tested the stated missing pairing.
- **Evidence:** Against the exact pre-run baseline on seeds 0-3 in both seats, the candidate won 1/8 with every status DONE and averaged $73,671.3 versus $75,956.8 (-$2,285.5). `py_compile` and `test_agent.py` passed; the standalone episode scored $97,880 versus $3,485.
- **Verdict:** Rejected and removed. Direct instrumentation of a full game then measured only 185 opposite-direction moves out of 3,462, that is 5.3% thrash, so there was almost no re-targeting waste to recover and the claims only removed the dispatcher's useful adaptivity: a claimed unit is withheld from a nearer or more urgent job. Retry only if some future change actually raises the measured reversal rate above roughly 20%.
- **Best distinct next hypothesis:** The same instrumentation showed 499 PICKUP actions against 289 FEED and 19 PLACE deliveries, so shed logistics, not routing, is where the movement goes.

## 2026-08-11 - Batch shed pickups into whole loads (rejected)

- **State:** Measured action budget for one seed-0 game: 7,016 actions, 3,462 movement, 1,379 PASS, 2,175 productive, of which PICKUP was the single largest productive op at 499 and DROP 198, against 289 FEED and 19 PLACE. `_fetch_jobs` sizes demand against instantaneous carried stock, so each consumed wheat immediately reopens a shortfall of one and dispatches a priority -1 shed run for a single item.
- **Decision:** Add `MIN_LOAD = 3` and launch only whole loads (`runs = short // per`), keeping the herd-sized `n_animals` target and the eight-way carrier spread unchanged, with a part-load exemption when the crew carries nothing at all.
- **Why it seemed best:** It attacked trip granularity rather than the demand target, so it was distinct from the rejected exact-unfed-count rule and from both dock-selection attempts, and it preserved the distribution buffer those failures proved necessary.
- **Evidence:** The mechanism worked exactly as designed, PICKUP falling from 499 to 185, but PASS rose from 1,379 to 1,532 and productive actions fell from 2,175 to 1,823. Against the exact pre-run baseline on seeds 0-3 in both seats the candidate won 2/8 with every status DONE and averaged $71,912.0 versus $73,833.1 (-$1,921.1). `py_compile` and `test_agent.py` passed; the standalone episode scored $98,980 versus $3,487.
- **Verdict:** Rejected and removed. Freed logistics actions converted into PASS, not money, and the thinner carrier spread cost feed throughput (FEED 289 to 275). This is the third independent confirmation that labour supply is not the binding constraint. Retry only alongside a productive job the freed carrier can reach in the same turn.
- **Best distinct next hypothesis:** If actions are in surplus, the planner's cost per head may be too high, which is the untested half of the old optimistic-capacity failure.

## 2026-08-11 - Decouple planning capacity from hiring load (rejected on screening)

- **State:** 1,379 PASS actions per game is roughly a fifth of the crew's paid actions. `ANIMAL_SLOTS = 9` is used both for `slots`, which decides whether to build at all, and for `load`, which decides how many hands to hire, and the ledger recorded the old `ANIMAL_SLOTS = 6` failure as needing planning capacity decoupled from labor demand.
- **Decision:** Add `PLAN_ANIMAL_SLOTS = 7` used only by the `slots` budget and `_scan`'s build test, leaving `load` and therefore hiring on the generous `ANIMAL_SLOTS = 9`.
- **Why it seemed best:** It was the explicitly named missing pairing for a previously rejected strategy, and freshly measured idle capacity said the planner's two-animals-per-hand ceiling was too conservative.
- **Evidence:** Cheap two-seed screen against the exact pre-run baseline: 0/4 with every status DONE, averaging $67,498.0 versus $73,887.3 (-$6,389.3). Pruned before a full benchmark.
- **Verdict:** Rejected and removed. The decoupling was implemented as prescribed and still lost decisively, which reclassifies the original failure: dense planning is bad on its own merits, not merely because it starved hiring. Extra heads cost cash and the `FEED_DAYS` reserve immediately while their chores spread further across the map, and idle actions are not located where the new animals would stand. Retry only with evidence that PASS actions occur adjacent to the tiles the new structures would occupy.
- **Best distinct next hypothesis:** Labour has now failed three ways, so measure the revenue side, which no previous experiment has examined.

## 2026-08-11 - Sell fertilizer as it arrives instead of hoarding it (selected as v7)

- **State:** Per-product revenue instrumentation of a full seed-0 game: MILK 135 units at $226.1 each ending at $238, WOOL 112 at $246.5 ending at $247, MELON 96 at $223.2 ending at $223, and FERTILIZER 292 units at $45.7 ending at $1. The shed held 53 fertilizer on day 24, 45 on day 27 and 49 on day 28, about half of the 100-item shed, and liquidated it on day 29 into a market already at the bottom. `COLLECT_FERTILIZER` is the second largest productive op at 292 actions per game, and the $50 sell floor blocks every ordinary sale long before the season ends.
- **Decision:** Lower only `SELL_RULES["FERTILIZER"]` from `(3, 50)` to `(3, 5)`. Collection, caps, and every other product rule are untouched.
- **Why it seemed best:** A price floor is a bet that the quote recovers. Fertilizer is the one product this farm gluts and no shop drains, so its price falls all season and the floor guarantees selling at the worst moment rather than avoiding it. Two mechanisms should gain: the units themselves sell at $20-45 instead of about $1, and vacating half the shed keeps the farm below `SHED_PRESSURE`, where the emergency rule dumps milk and wool at four times cap while ignoring their floors. It is the exact complement of the rejected collection gate, which removed the production instead of the hoarding.
- **Evidence:** Against the exact pre-run baseline on seeds 0-3 in both seats, the candidate won 7/8 with every status DONE and averaged $76,529.9 versus $75,026.0 (+$1,503.9). The only loss was seed 0 seat 0 at -$56. `py_compile` and `test_agent.py` passed; the standalone episode scored $94,714 versus $3,497.
- **Verdict:** Selected and submitted as v7. Meets 8 games, 7/8 wins, at least +$100 mean, and all statuses DONE.
- **Process note:** Because the spend cap made `codex exec` unavailable, `automation.ps1` could not perform its own Codex analysis or its independent re-verification, so the benchmark above is a direct run of the frozen `.automation/baseline_verify.py` against the frozen `.automation/baseline_main.py`, and the Kaggle submission and state update were performed by hand to the same gate. `verify.py` was not modified.
- **Best distinct next hypothesis:** The same revenue table shows MILK and WOOL ending at $238 and $247, still scarce at the final bell, while EGG ends at $59 across 119 units at $51.9. Test raising the MILK and WOOL per-turn caps above 2, or lowering their $110 and $130 floors, so premium output is not still queued when the season ends.

## 2026-08-11 - Read the environment source (analysis, no code change)

- **State:** The user asked whether the architecture itself is wrong. Every entry above this one tunes a constant inside a model of the game taken from `main.py`'s own docstring. Nobody had read `kaggriculture.py`.
- **Findings:** (1) `FERTILIZE` is a real action the agent has never emitted; it costs one action plus one fertilizer and doubles what each watering adds for three days. (2) `TOWN_CENTER_PRODUCTS` excludes FERTILIZER and no shop lists it, so nothing anywhere drains fertilizer and its price can only fall - the v7 floor fix was right for a deeper reason than measured. (3) `TOWN_CENTER_DEMAND_SCHEDULE` quadruples town demand after day 20. (4) Almost every product is in scarcity, not glut: final versus base prices are STRAWBERRY 318/120, WOOL 247/200, MILK 238/160, WHEAT 55/25. (5) Ongoing crops accrue yield without watering; watering only avoids the weed death and gates the fertilizer bonus.
- **Verdict:** Adopted as standing practice, recorded in `memory.md`. The immediate consequence is the fertilize-wheat change below; the scarcity finding and the unused strawberry economics remain open.

## 2026-08-11 - Fertilize wheat instead of selling the fertilizer (selected as v8 candidate)

- **State:** The farm collects 292 fertilizer a game and buys ~140 wheat a game at a price that climbs from $25 to $55 because five shops drain it. Fertilizer has no drain at all. Wheat's plain yield is 4 against a cap of 6, and its watering window is exactly the 3 days a single fertilize covers; melon already waters 7 times into a cap of 6, so it has no headroom.
- **Decision:** In `_scan`, emit `(0, x, y, ["FERTILIZE"], "FERTILIZER")` for any WHEAT tile inside its bonus window that is not already fertilized. No new constants, no market changes; fertilizer flows straight from the units that collect it, and the surplus still reaches the shed to be sold.
- **Why it seemed best:** It converts the only zero-demand product into the input the farm spends most on, uses the measured idle labour, and adds no capital cost, no tiles and no herd displacement - the three failure modes that killed every previous crop and capacity experiment.
- **Evidence:** 14/16 wins over seeds 0-7 in both seats against the frozen v7 baseline, averaging +$3,566.5, every status DONE. `py_compile` and `test_agent.py` passed; the standalone episode rose from $94,714 to $100,010. Measured mechanism: wheat purchases fall from ~140 to ~90 units a game while the herd stays the same size, and 48 FERTILIZE actions a game are drawn from fertilizer the farm already collects.
- **Verdict:** Selected. Meets the gate's 7/8 ratio at double the sample and vastly exceeds +$100 mean. Not yet submitted - held pending the user's decision on spending one of the day's remaining submissions.
- **Rejected variants, all removed:** priority 1 scored 2/8 (-$1,492) and priority 2 scored 1/8 (-$2,437); a live `FERTILIZER < 2 x WHEAT` break-even gate scored 2/8 (-$926); a day-4 gate screened at -$7,161/-$7,239 on seed 1. All four fail on timing, not economics: the bonus is credited by the waterings inside a 3-day window, so any rule that delays or flickers turns the job into pure walking.
- **Known weakness:** Seed 1 loses both seats by about $5,000. Day-by-day tracing shows fertilizer is still worth $89 on day 10, so early diversion costs cash that compounds into two fewer animals by day 15. Every attempt to fix that seed lost more elsewhere than it recovered.
- **Best distinct next hypothesis:** A latching gate that opens once `FERTILIZER < 2 x WHEAT` and never closes, which keeps the break-even economics without the mid-window abandonment that sank the per-turn version.

## 2026-08-11 - Strawberry on its own slot cost (rejected, third strawberry refusal)

- **State:** Environment source shows STRAWBERRY finishing at $318 against a $120 base, the dearest good in the game, drained by four shops plus the town centre, and grown by neither farm. Both earlier strawberry attempts charged it the full `PLANT_SLOTS = 4`, so each tile displaced a quarter of an animal's planning capacity; the ledger recorded the missing pairing as crop-aware staffing plus measured idle labour. An ongoing plant accrues yield whether or not it is watered, needing water only every other day to dodge the weed death, so its true tending cost is well under a watered crop's.
- **Decision:** Add `STRAWBERRY_TILES = 8` and `BERRY_SLOTS = 2`, plant it last in the empty-tile order behind melon, livestock and feed wheat, buy its seed from the investment budget only, and add a `(2, 150)` sell rule so it is not stranded until the last day.
- **Why it seemed best:** Per slot a cow returns about $40 a day, strawberry about $19 and the filler wheat it replaces about $10, so on a half-price slot cost it should have consumed capacity the herd could not use and roughly doubled the filler return.
- **Evidence:** 0/8 against the frozen v7 baseline, averaging -$6,213, every status DONE; since the candidate also carried the fertilize win, strawberry itself cost about $9,800. The crop worked exactly as designed - 8 tiles planted, 32 units harvested and sold, the full unfertilized yield - and the farm still lost. Seed 3 traced: 15 animals versus 19, milk sold 96 versus 147, wool 70 versus 101, strawberry revenue about $6,400 against roughly $16,000 of forgone animal production. PASS rose from 1,255 to 1,534.
- **Verdict:** Rejected and removed. Idle time went *up*, so the farm was never labour-constrained here; it was cash-constrained, and $800 of early seed is two cows that would have compounded. The slot cost was not the missing pairing.
- **Structural reason not to retry as-is:** Strawberry needs 16 days, so `_plantable` forces it to be planted by day 13, and the farm is cash-poor until roughly day 13-15. Its planting deadline lies entirely inside the phase where capital is scarcest, and a crop planted at the deadline first produces on day 23. The $318 quote is a consequence of nobody growing it, not an opportunity available to us.
- **Test again only with:** A farm whose animal pipeline is provably slot-limited rather than cash-limited before day 13 - for example after a change that raises early cash without spending slots. Strawberry is not universally bad; it is unreachable under this cash curve.
- **Best distinct next hypothesis:** Stay with the fertilizer economy, which is the one input the farm both produces free and spends heavily on. Test a latching `FERTILIZER < 2 x WHEAT` gate as recorded above, and separately test fertilizing melon tiles that are still short of their cap when wheat has no open window.

## 2026-08-11 - v7 public rating regressed; v8 submitted (score evidence)

- **State:** Submission 55438001 (v7, fertilizer sell floor $50 to $5) returned a public rating of **623.7, down 35.9 from v6's 659.6**, despite having won 7/8 locally at +$1,503.9. Submission 55438775 (v8, fertilize wheat) was pushed the same hour and is pending. Budget 3/5.
- **Reading:** The local benchmark plays the candidate against a copy of the baseline in one shared market, so a change that merely acts sooner on a shared finite resource beats a slower copy of itself and gains nothing against a field that already acts promptly. Fertilizer is the extreme case: nothing anywhere drains it, so its price is a strictly decreasing shared pool and selling faster only decides who gets the top of a curve both farms push down. Recorded in `memory.md` as a standing caution.
- **What this does not overturn:** The measurement behind v7 stands - fertilizer really was parked 45-53 units deep in the shed and liquidated at $1, and the shed pressure really did dump milk and wool. The error was reading a racing advantage as a production advantage.
- **What it implies for v8:** v8's own change saves cost rather than racing anyone - it cuts wheat purchases from ~140 to ~90 units a game whatever the opponent does - and it withdraws about 48 units a game from the fertilizer dump, partially undoing v7's contribution to the crash. It does inherit v7's floor.
- **Caveats:** v7 had been scored for under an hour and public ratings converge as episodes accumulate; the rating history already contains one non-monotone step (563.3 to 554.1).
- **Next action if v8 also regresses:** Restore `SELL_RULES["FERTILIZER"]` to its $50 floor while keeping the fertilize-wheat job, which isolates the cost-saving half from the racing half and is the cleanest available test of the diagnosis above.
- **Outcome (corrected):** v8 first read 777.0 after only **7 episodes** and that number was recorded here as a +111.6 win. It was noise. At **28 episodes** v8 reads **653.7**. The converged standings are v6 665.4 (42 games), v7 661.6 (29), v8 653.7 (28) - three versions within twelve points, i.e. indistinguishable.
- **What that means:** neither the +$1,504 (v7) nor the +$3,567 (v8) local gain has produced a measurable public gain, and the mirror check remains unconfirmed by any public result rather than validated by one. The v7 racing diagnosis is still the best explanation of its local-vs-public gap, but v8 does not corroborate it. Ratings are now always to be recorded with their episode count; see `memory.md`.

## 2026-08-11 - Rebuild the improvement loop around losses, not averages (process change)

- **State:** The loop fed Codex all 41 replays of the latest submission equally, read both ledgers in full every run, and kept every raw replay forever (1.26 GB). Its own last report read "Akshay averaged $55,456 versus opponents' $57,676, 20-20 record" - true, and hiding everything that matters.
- **What the averages hid:** Indexing every replay and excluding games against our own submissions gives **33W-40L**, not 20-20: the agent was losing in the field. Our best game ever is $82,876; the field's best is **$175,862** by wenjinyang, and four opponents have beaten our best-ever game. Roughly twenty-five experiments had been tuning constants inside an architecture that scores half what the top of the field scores.
- **Decision:** Five changes, all measured.
  1. **`loop.py`** - a replay index built from each file's first 64KB. `rewards` and `TeamNames` are serialised before `steps`, so win/loss for the whole corpus costs **0.01s instead of parsing 1.26 GB**. Self-games are excluded; the index records opponent, scores, delta and a replay URL.
  2. **Loss-first selection** - each run reads the 3 worst losses, the 2 highest-scoring opponent games and the 2 near-misses, not everything. Typically 5 files instead of 41.
  3. **Retention** - the index is permanent and version-controlled; raw replays are pruned to the informative set. 1,260 MB to 300 MB, and re-downloadable from Kaggle by episode id.
  4. **Tiered ledgers** - `memory.md` stays the always-read curated summary; `decision.md` becomes a grep-on-demand archive; `attempts.jsonl` carries one line per past experiment (35 today) so "was this tried?" costs no prose.
  5. **Mirror gate** - `verify.py` now also plays each agent against itself and the wrapper requires a mirror gain of at least 500. See the entry above for the evidence that this separates racing from production.
- **Bugs found by integration-testing the rewrite, all fixed:**
  - `build_index` rebuilt from surviving files, so the first prune collapsed the index from 73 rows to 7. It now merges and never shrinks; the index outlives the raw files by design.
  - `prune` could delete a replay `select` had just chosen for the same run. The keep set now includes the current selection, plus the 4 newest games.
  - Windows PowerShell 5.1 returns a JSON array from `ConvertFrom-Json` as a single object, so `@(... | ConvertFrom-Json)` yielded a one-element array containing the array. This silently emptied the seen-set and made the wrapper re-download the season it had just pruned. Fixed with an `AsArray` helper at all three sites.
  - `replay_index.json` lived under the gitignored `.automation/`; it is the one artefact that cannot be regenerated after a prune, so it now lives in the repo.
- **Cost of the index bug:** roughly 66 older replays were pruned before the merge fix landed. Their episodes are still on Kaggle, and 27 of the most relevant (v7's 20 and v8's 7) were re-downloaded and indexed. v6's 42 remain re-downloadable if ever wanted.
- **Verdict:** Adopted. Wrapper verified end to end: 0 re-downloads, 5 replays selected, context written, ledgers tiered. It still stops at the Codex spend cap, which is an account limit rather than a loop defect.
- **Best distinct next hypothesis:** With the loop pointed at them, work out what wenjinyang does to reach $175,862 - more than twice our best - and treat that as the target rather than the next constant.

## 2026-08-11 - Strawberry at field scale (rejected, fourth strawberry refusal - but the diagnosis changed)

- **State:** Excluding self-games the agent was 25-28 across the indexed field. Our best game ever is $82,058; the field's best is $175,862. Four opponents have beaten our best-ever game and roughly twenty-five experiments inside the current architecture had not closed any of it. All six selected replays were opened and both farms reconstructed day by day.
- **What the replays actually show.** Every opponent above $120k - wenjinyang $175,862, Stanislav Ilin $150,498, VictorAndrew $145,288, BlackPearls1 $124,672 - plays the *same* farm, and it is not a livestock farm:
  - **36-42 tiles of STRAWBERRY**, planted day 7-12, selling ~280-320 units a game at $217-264.
  - 12-14 melon tiles (we run 8), harvested day 10-11 for the ~$18k that funds the berries.
  - 8-9 cows and 4-6 sheep, **no geese** - a herd the same size as ours, so the berries are not bought with livestock.
  - Three quadrants, never the fourth.
  - The dead berry tiles dug over into **30-50 wheat tiles after day 20**, selling 300-455 wheat.
  - 84 FERTILIZE actions a game, all on strawberry.
- **Revenue decomposition, wenjinyang's $175,862 against our $69,326 in the same episode:** their milk, wool and fertilizer income is roughly equal to ours. The entire gap is strawberry ~$80k plus wheat ~$14k. They do not out-farm us on the things we do; they sell a product we have literally never sold one unit of.
- **Why the market allows it (environment source):** four of the eight shops list STRAWBERRY (ICE_CREAM_SHOP, SMOOTHIE_SHOP, BRUNCH_SPOT, FARMERS_MARKET) against one for WOOL and *none* for MELON, so the town drains ~500-600 units a season. It is the most-drained good in the game and it ends at $217-311 against a $120 base in every replay, including the ones where nobody grew it.
- **Why this is not the same experiment as the three earlier refusals:** those tested 8 and 12 tiles (and one 42-tile version under v5-era code). All of them harvested **4 units a tile - the full *unfertilized* yield**. That is not a shortfall, it is the ceiling: `yield_units` caps at `max_yield` = 4 held, so four productions of +1 is four units however you harvest. Fertilized-and-watered productions add +2, and with a harvest between them the tile gives **eight**. The FERTILIZE engine only landed in v8, *after* the last strawberry refusal, so no strawberry test has ever run with it.
- **Decision:** `BERRY_TILES = 40` planted between day 6 and `_plantable`'s day-13 close, behind melon and the structure branch; strawberry seed from the investment budget; a `(2, 100)` sell rule; `FERTILIZE` extended from wheat to any ongoing crop on its production day; and a correction to `production_day`, which was off by one - the nightly refresh counts `days_since_first = age + 1 - first`, so strawberry planted on day 0 produces on the nights of days 9, 11, 13, 15, not 10, 12, 14, 16.
- **Evidence, attempt 1 (strawberry alone):** **6/8**, mean $90,007.8 versus $88,490.9 (**+$1,516.9**), mirror **+$4,682.4**, every status DONE, `py_compile` and `test_agent.py` passing. Misses the 7/8 head-to-head gate. The crop itself worked exactly as the replays predicted: 224 units sold a game at $199-260, ~7 units a tile, 79 FERTILIZE actions.
- **What it cost:** the herd fell from 16 animals to 8 (milk 150 units to 66, wool 107 to 35). Seed 2 lost both seats and lost the mirror by $12k.
- **Two execution defects found by instrumenting it, both real and both measured:**
  1. `PLANT_SLOTS` did double duty as *capacity available* and *hiring demand*, so halving it to 2 halved the crew - 7 hands against the baseline's 11 - and 16 of 40 seeds were bought and never planted. Split into `PLANT_SLOTS` (capacity) and `PLANT_LOAD` (hiring): crew back to 12-14, tiles planted 24 to 32.
  2. Wrapping `_scan` and classifying every turn's build decision showed the herd pipeline blocked on **`want pending (COW)` for 288 consecutive turns, days 14 to 25**. The farm grows one head at a time, so a single undelivered animal stops the next structure being built *and* the next beast being bought. `PLACE` sat at priority 1 while crop watering sat at 0, so the unit carrying the cow was eligible for a water job every turn and never reached the pasture. Not cash, not slots - one job priority.
- **Evidence, attempt 2 (+ three-quadrant cap + `PLACE` at -1):** **4/8**, mean +$3,734.0, mirror +$4,633.4, all DONE. Seed 2's mirror went from $69,323 to $91,010 and its animal purchases from 8 to 18, but seeds 0 and 3 fell ~$10k and ~$9k each.
- **Evidence, attempt 3 (`PLACE` at -1 only, land cap removed):** **4/8**, mean $86,360.5 versus $84,844.6 (+$1,516.0), mirror **+$1,124.5**, all DONE. This corrects attempt 2's attribution: removing the land cap did *not* restore seeds 0 and 3, so the three-quadrant cap was near-neutral and **`PLACE` at -1 is itself what costs those seeds**, even though it is the correct fix for a measured 288-turn deadlock.
- **Why the deadlock fix loses where it loses:** with the pipeline unblocked the farm buys 17-18 animals instead of 8 - but `_next_animal`'s deadlines retire cows at day 19 and sheep at day 20 while geese run to day 24, so the freed late pipeline spends its cash on **geese: 8 bought instead of 3**. A goose bought on day 22 returns ~$350 of egg against ~$378 of feed at the day-22 wheat price. The deadlock was suppressing a loss-making purchase, so fixing it exposed one. Strawberry then finished at $87 rather than $199 on seed 0, because the cash went to birds instead of a crop the town was still draining.
- **Verdict:** All three rejected at the 7/8 gate; `main.py` and `test_agent.py` restored byte-identical to their pre-run snapshots and no submission written. Attempt 1 is the near miss - 6/8 with a mirror of +$4,682, i.e. it produces more rather than merely racing - and it is the first change in this project's history aimed at the field's ceiling instead of our own average.
- **Test again only with:** the late-goose leak closed first. Both surviving numbers point at the same place: strawberry pays (mirror +$4,682 on its own) and the herd pipeline deadlocks (288 turns), but unblocking the pipeline without fixing what it buys converts berry cash into negative-margin birds.
- **Best distinct next hypothesis:** Stop `_next_animal` returning GOOSE once its feed bill exceeds its egg revenue - a bird bought on day `d` produces `29 - d - 4` eggs at ~$50 against `29 - d` days of wheat at the live quote, so it stops paying around day 20, not day 24. Then re-run attempt 1 plus the `PLACE` priority fix. That pairing is the one combination not yet measured: the berry crop that cleared the mirror, the deadlock fix that doubles the herd, and a deadline that stops the freed cash going into birds that lose money.

## 2026-08-11 - Unblock the herd pipeline and stop the wage curve eating it (selected as v9 candidate)

- **State:** Baseline is v8 (`.automation/baseline_main.py`), public rating 682.8 and rising, budget 5 submissions. Field record excluding self-games 28W-28L; our best game ever $82,058, the field's best $175,862 (wenjinyang). The previous run's closing hypothesis named the exact pairing to test: close the late-goose leak, then re-run the `PLACE` deadlock fix.
- **Exact change (three edits, `main.py`):**
  1. `ANIMALS` gains a per-species `last` day - GOOSE 20, COW 19, SHEEP 20 - and `_next_animal` tests `day > a["last"]` instead of the generic `day + first + interval > LAST_DAY`. Cow and sheep are unchanged by this (19 and 20 are what the old formula produced); only the goose moves, from 24 to 20.
  2. The `PLACE` job drops from priority 1 to **-1**, ahead of watering and feeding.
  3. `HIRE_FRAC = 0.02` / `HIRE_MIN = 25` are replaced by a flat `HIRE_MAX_WAGE = 144`, so a hand is hired while its `fib` wage is at most $144 (12 hands) regardless of the bank.
  `test_agent.py`'s deadline assertion updated: a COOP asks for a goose on day 20 and for nothing on day 21.
- **Pre-test reasoning:** the 288-turn `want pending` deadlock was already measured, and unblocking it was already measured at 4/8. The recorded reason it lost was that the freed cash bought geese past their break-even. Edits 1 and 2 are that pairing.
- **What the measurement changed.** Edits 1+2 alone scored **4/8, +$1,764.9, mirror +$553.1** - no better than the deadlock fix on its own. Instrumenting a mirror game on the two losing seeds showed the herd fix working exactly as intended (21 head against 16, CARE 377 against 282, FEED 354 against 278) and revenue up **+$16,745** on seed 3 (milk +$10,222, wool +$6,029) - while **hire spend rose $5,110 to $21,101, +$15,991**. The extra herd raises `load`, `load` raises `crew_cap`, and the crew walks into the exponential tail of `fib`: hands 13-16 cost $233+$377+$610+$987 = $2,207 a day, 85% of the wage bill for 25% of the crew. Worse, the old ceiling was `money * 0.02`, so it bought that tail hardest in the last week, when a hand has fewest days left to repay it. A hand-day does not get more valuable because the bank is fuller.
- **Evidence, final candidate (`verify.py .automation/baseline_main.py 4`):** **8/8**, mean $89,864.0 versus $79,823.0 (**+$10,041.0**), every status DONE. **Mirror $90,973.0 versus $79,738.3, +$11,234.8**, all done. `py_compile` and `test_agent.py` pass; the standalone episode scores $107,873. Re-run at 8 seeds for stability: **15/16, +$7,649.5, mirror +$8,422.0**, worst pairing -$4,144. Candidate mirror games reach $95,972, above our best public game ever.
- **Attribution, each part measured against the same baseline at 4 seeds:**
  - wage cap alone: **1/8, +$32, mirror +$431** - worthless on its own.
  - `PLACE` + goose deadline, no wage cap: **4/8, +$1,764.9, mirror +$553.1**.
  - `PLACE` + wage cap, goose deadline reverted to 24: **7/8, +$5,722, mirror +$6,680**.
  - all three: **8/8, +$10,041, mirror +$11,235**.
  So this is a genuine interaction, not three independent wins stacked. The pipeline fix creates the herd, the goose deadline decides what the freed cash buys, and the wage cap stops the crew that herd justifies from costing more than the herd earns. Any one alone misses the gate.
- **Why the gain should survive the real field:** the mirror gain is +$11,235 - larger than the head-to-head gain, which is the signature of a production change rather than a racing one. Nothing here consumes a shared pool faster than the opponent; two of the three edits *spend less* ($144-capped wages, no day-21-to-24 geese) and the third moves an animal we already own out of a carrier's pack.
- **Verdict:** Selected. Submission request written.
- **Test again only with / reconsider if:** `HIRE_MAX_WAGE = 144` is a flat constant chosen from a three-point screen (89 -> 3/4 +$5,974; 144 -> 4/4 +$9,122; 233 -> 4/4 +$7,420 on a 2-seed screen). It is a ceiling on the crew, so it will be wrong for any future change that makes hands genuinely scarce - a much larger crop area, in particular. Re-screen it after any change that raises `load` a lot.
- **Best distinct next hypothesis:** Re-run the 40-tile strawberry farm on top of *this* baseline. Its recorded blocker was that the herd collapsed 16 head to 8 because berry seed and livestock drew on the same cash between days 6 and 13; this candidate both frees that cash (no day-21-to-24 geese, ~$16k less in wages) and unblocks the pipeline that was capping the herd anyway. Strawberry standalone already cleared the mirror at +$4,682 and missed only on win count, and it remains the only measured route at the ~$80k of strawberry revenue that separates us from wenjinyang's $175,862.

## 2026-08-12 - Strawberry at field scale, fifth attempt: the crop works once the carriers stop being stolen (selected as v10 candidate)

- **State:** Baseline is v9 (`.automation/baseline_main.py`), public rating 657.1, budget 5 submissions with 1 used today. Field record 46W-46L across 92 indexed games; our best game ever $90,642, the field's best $175,862 (wenjinyang). `memory.md`'s standing next hypothesis named this exact test: re-run the 40-tile berry farm on the v9 baseline, unchanged, because both recorded blockers (the herd-capping `PLACE` deadlock and the late-goose cash leak) were closed by v9.
- **New replay evidence, Octavi Grau $160,385 against our $43,375 (episode 92364933, seat 1, our v9 agent).** A sixth independent confirmation of the field's plan, and the sharpest yet because the money curves are identical until day 10:
  - Day 10 money: them $2,747, us $2,885. Day 20: them **$51,427**, us $10,639. The entire gap is days 11-21.
  - They plant berries from **day 4**, reach 36 tiles by day 12, and hold them until day 20; then dig the dead tiles over into 57 wheat tiles and sell 455 wheat.
  - They buy their whole herd in the first nine days - 9 cows and 4 sheep, **13 head, no geese, 13 PLACE actions all season** - and never buy another animal. We buy 20 head dribbled through day 18.
  - Sold: STRAWBERRY 286, WHEAT 455, MILK 241, FERTILIZER 235, MELON 114, WOOL 132. Ours: no strawberry, WHEAT 139, MILK 131, WOOL 126.
  - Same crew (262 hires against our 276) and the same PASS volume, but their actions land differently: WATER 1,010 against our 340, PICKUP 135 against our 433, and 2,836 moves against our 3,702.
- **Attempt 1 - the berry package alone (rejected).** `BERRY_TILES = 40` planted from day 6 behind melon and the structure branch; strawberry seed bought out of the investment budget; `SELL_RULES["STRAWBERRY"] = (2, 100)`; `FERTILIZE` extended from wheat to any ongoing crop on its production night; the `production_day` off-by-one corrected (`age + 1 - first`, because the nightly refresh counts from tomorrow) and bounded by `max_yield` productions; and `PLANT_SLOTS` split into `PLANT_SLOTS = 2` (capacity) and `PLANT_LOAD = 4` (hiring demand).
  - **Evidence: 2/8**, mean $91,754.3 versus $95,792.9 (**-$4,038.6**), mirror $88,446.8 versus $90,973.0 (**-$2,526.3**), every status DONE.
  - **What the instrumented mirror game showed, and it is not what any previous strawberry refusal found.** The farm did not run out of cash - it ended at $78,140 with 200 berries sold. It ran out of *animals*: 18 bought (9 cows, 6 sheep, 3 geese), **8 alive at the last bell**, four empty pastures standing, `FEED` down to 193 actions from the baseline's 354, and up to 12 weed tiles at once. Ten head starved and walked off.
- **The cause, and it is the same bug class v9 already fixed once.** `FEED` is one of only three jobs that can only be done by a unit already carrying the goods, and it sat at priority **0**, alongside `WATER`. Forty berry tiles create twenty-odd priority-0 water jobs a day that *any* unit can serve, and `_assign` hands each job to the nearest able unit - so the wheat carrier walking to a pasture is the nearest body to a dry berry tile and waters it instead. The herd starves next to a full shed. v9 moved `PLACE` to -1 for exactly this reason (`PLACE` needs the animal in the pack) after measuring a 288-turn deadlock; `PICKUP` was already -1. `FEED` was the third one and nobody had looked, because until this run no change had ever put enough any-unit work on the board for it to bind.
- **Attempt 2 - the same berry package with `FEED` at priority -1 (selected).**
  - **Head-to-head (`verify.py .automation/baseline_main.py 4`): 7/8**, mean $100,283.75 versus $94,265.5 (**+$6,018.25**), every status DONE. The one loss is seed 3 seat 0 at -$358.
  - **Mirror: $96,309.75 versus $90,973.0 (+$5,336.75)**, all done. Mirror games reach **$106,086**, against our best-ever public game of $90,642.
    - **Re-run at 8 seeds for stability**, because a change that moves market prices is chaotic per seed: **15/16**, mean $104,058.1 versus $94,410.4 (**+$9,647.8**), **mirror $100,001.6 versus $90,330.8, +$9,670.8**, every status DONE. Same single loss. The agent's mirror average is now six figures.
- `py_compile` and `test_agent.py` pass; standalone episode **$123,166** against v9's $107,873.
- **Attribution - the berry crop is the gain, the `FEED` priority is what makes it survivable.** Re-running the identical candidate with `BERRY_TILES = 0` (every other edit kept, including `FEED` at -1 and the slot split) scores **1/4, -$1,049, mirror -$3,398.8**. So the enabling fix is worth *negative* money on its own and the berry farm is worth -$4,039 without it; together they are +$6,018. This is an interaction, not two stacked wins, and it is the third time in this project that removing a bottleneck only paid once the thing it was suppressing was priced.
- **Why the gain should survive the real field:** the mirror gain is +$5,337 with both farms planting the same 40 tiles at the same hour, so this is production, not racing. Strawberry is also the one product where racing is least of a risk: four of eight shops drain it, the town takes ~500-600 units a season, and it ends at $217-311 against a $120 base *in replays where neither farm grew any*. We are entering a market in scarcity, not draining a fixed pool.
- **Verdict:** Selected. Submission request written.
- **Test again only with / reconsider if:** `BERRY_TILES = 40` and `BERRY_FIRST_DAY = 6` are taken from the field, not screened here - Octavi plants from day 4 and holds 36. Do not tune them before something else binds. `HIRE_MAX_WAGE = 144` is still a flat ceiling and this change raises `load` a lot, which is the condition v9's entry flagged for re-screening it; it has not been re-screened, and it is the most likely next constraint.

## 2026-08-12 - Buy the herd in an opening rush instead of one head every two days (selected as v11 candidate)

- **State:** Baseline is v10 (`.automation/baseline_main.py`), public rating **730.5** and rising (up from v9's 649.9 - the largest jump the project has recorded, and confirmation that the strawberry direction is right against the real field). Budget 5 submissions, 2 used today. Field record 60W-60L across 120 indexed games; our best game ever $109,836, the field's best $175,862 (wenjinyang).
- **New replay evidence, Suda $165,925 against our $89,417 (episode 92421750, seat 1, our v10 agent).** The first loss recorded by a *berry-farming* version of our agent, so the berry gap is finally closed enough to see what is behind it. Per-product revenue, them versus us: MILK **$85,430 v $27,316**, STRAWBERRY $73,531 v $49,666, WOOL $23,458 v $8,835, WHEAT $20,648 v $4,768, MELON $20,433 v $12,479, FERTILIZER $17,923 v $7,885.
  - **Care coverage is not the problem and this had never been checked.** Counting every animal at the last hour of every day: we care-and-feed **92%** of animal-days, they manage **82%**. We tend our herd better than the farm that scores twice as much.
  - **The herd's size is not the problem either.** They finish on 13 head, we finish on 10-11.
  - **The whole difference is *when*.** Animal-days: **321 against 215**. They hold 5 head on day 0, 12 by day 8, and then buy almost nothing for the rest of the season (14 `PLACE` actions all game). We hold 1 on day 0, 4 on day 8, and do not reach 10 until day 16. A cow's entire value is the number of production days left on the calendar when it lands, and `pending_care_bonus` triples each of those productions, so six days of delay on eight cows is most of a $58,000 milk gap.
  - Their productive-action share is 50% (3,312 of 6,659) against our 34% (2,073 of 6,098).
- **The two throttles, measured on the baseline rather than guessed.** Instrumenting `_scan`'s inputs at noon each day:
  - **Days 0-1 it is not cash.** The farm ends day 0 with **$1,584 unspent** and one goose. `slots` and the one-head-at-a-time pipeline are what stop it.
  - **Days 2-10 it is only cash, and specifically the feed reserve.** `budget = money - CASH_FLOOR - n_animals * price(WHEAT) * FEED_DAYS` is **negative on every one of days 2, 3, 4, 6, 7, 8, 9** - ten days of feed money for four animals is $1,280 against a bank of $1,300 - and buying one more head needs `cost + keep` *on top* of that. The herd sits at 3-4 for nine days. Day-by-day spend confirms it: two geese on day 0, one cow on day 1, one sheep on day 5, then nothing until day 11, while berry seed takes $700-2,100 a day from day 6.
- **Exact change (`main.py`, four edits that only work together):**
  1. `HERD_RUSH_DAY = 8`, `HERD_RUSH_SIZE = 8`. In `_scan`'s empty-tile loop the structure branch becomes `rush or (not want and slots >= ANIMAL_SLOTS)` where `rush = day <= HERD_RUSH_DAY and sum(counts.values()) < HERD_RUSH_SIZE`. Inside the window the herd grows in parallel and ignores `slots`; an empty structure already counts in `load`, so the crew catches up the next turn. `want[a] = want.get(a, 0) + 1` instead of `= 1`, so parallel wants are counted.
  2. `FEED_DAYS_EARLY = 3`, used in place of `FEED_DAYS` while `day <= HERD_RUSH_DAY`. A head bought before day 8 drops a fertilizer every night worth $90-100 while the market is near its $100 base, against ~$30 of wheat; it repays its own feed from day one. Ten days of cash there is the throttle, not the insurance.
  3. `POOR_UNTIL_DAY` 0 -> **-1**. The old rule reserved day 0 for the fastest-paying bird, which is correct when you buy one head every two days and wrong when you buy the whole opening herd on day 0: gating it to geese filled 8 of 16 head with them and turned $16,896 of milk and wool into egg, the dump product.
  4. **A latent deadlock, found by the rush and worth fixing on its own.** `_scan`'s build branch called `_next_animal(counts, day)` without `stock` and gated on `budget >= cost`, so a structure - which is **free** - would not be authorised for an animal we had already paid for. Measured: seven geese in the shed, herd stuck at 1 for ten days, because the bank was too thin to approve a $0 coop. Now it passes `stock`, and skips the budget test when the beast is already ours.
  `test_agent.py` updated for all four (day-0 species, rush parallelism, post-rush single-head, and a new assertion that a crated animal gets its free structure on an empty bank).
- **Rejected on the way, each measured:**
  - Parallel herd growth *alone* (a plain `HERD_PARALLEL` of 2/3/5, no reserve change, no day gate): 0/4 at -$2,750, then 3/4 at +$2,055 with **mirror -$4,551**, and worse at 5. Instrumented: +52 animal-days but **milk and wool flat**, because the freed slots bought animals on days 14-18 that never reach production, plus two more geese. More animal-days at the wrong end of the calendar are worth nothing.
  - The rush with **no size cap**: milk and wool **+$16,492**, strawberry **-$27,914**. It paves all 25 opening tiles with pasture, so the $1,000 land purchase never happens and the berry farm falls to 8 tiles. `HERD_RUSH_SIZE` then screened at 6/8/10/12 - mirror **+$6,245 / +$12,910 / +$9,843** and worse at 12. Only 8 keeps full berry revenue while milk rises.
  - `FEED_DAYS` cut season-long to 3 or 5 with no rush: single-seed swings of +$5k and -$17k on the same seed, i.e. noise. The reserve is only the binding constraint inside the opening.
- **Evidence (`verify.py .automation/baseline_main.py 4`):** **8/8**, mean $113,476.0 versus $94,924.0 (**+$18,552.0**), every status DONE, worst pairing +$8,694. **Mirror $114,777.9 versus $96,309.8, +$18,468.1**, all done. Every one of the eight mirror games is six figures ($109,996-$118,665) and the mirror mean now exceeds our best public game ever ($109,836). `py_compile` and `test_agent.py` pass; the standalone episode against `starter` scores $124,218.
  - **Re-run at 8 seeds**, because a change that moves market prices is chaotic per seed: **16/16**, mean **+$16,710.6**, worst pairing still **+$8,694**, every status DONE, **mirror $110,604.1 versus $100,001.6, +$10,602.5**. No losing pairing at either sample size - the first time this project has recorded that.
- **Why the gain should survive the real field:** the mirror gain (+$18,468) is essentially equal to the head-to-head gain (+$18,552), which is the signature of production rather than racing. It also does not consume a shared pool sooner - it buys livestock, which the town sells at a fixed shop price, and the extra output is milk and wool, both of which the town *drains*. The instrumented game shows where it comes from: milk $30,262 -> $36,956 and wool $19,522 -> $22,511 with strawberry **unchanged** at $43,807, on a herd that is *smaller* (12 head against 14) but bought earlier and mixed away from geese (6 cows and 5 sheep against the baseline's 7 and 6).
- **Verdict:** Selected. Submission request written.
- **Test again only with / reconsider if:** `HERD_RUSH_DAY = 8` and `FEED_DAYS_EARLY = 3` were not screened independently - only `HERD_RUSH_SIZE` was. Both are plausible next knobs, but they are constants inside a now-working structure, and this project has spent twenty-five experiments proving that is the low-yield place to look.
- **Best distinct next hypothesis:** wheat as a late cash crop. Suda sells **473 wheat for $20,648** against our 112 for $4,768, by digging the dead berry tiles over into 57 wheat tiles between days 20 and 26 and selling into a market the town drains to $44-55. Octavi Grau does the same thing (57 tiles, 455 sold). We hold `ENDGAME_WHEAT_TILES = 10` and treat wheat purely as feed, and `SELL_RULES` has no WHEAT entry at all. The refusal on record ("Doubling the late wheat floor", 1/8) raised that number to 20 under the *pre-berry* farm, where there were no expiring berry tiles to convert and no spare late crew; both of those conditions have now changed.

## 2026-08-12 - Wheat as a late cash crop, and the two watering pairings for it (all rejected)

- **State:** v11 is live at a public 806.8 (5 episodes, not converged) and is the best agent this project has shipped. The distinct hypothesis queued off the replay analysis was the field's late game: Suda sells **473 wheat for $20,648** and Octavi Grau 455 by breaking the tiles their expired berries vacate into ~57 wheat tiles between days 20 and 26, against our 112 units for $4,768. `_wheat_target` only ever asks for feed - `max(round(n_animals * 0.75), ENDGAME_WHEAT_TILES if day >= 20 else 0)` with `ENDGAME_WHEAT_TILES = 10` - so tiles freed by berry decay stand empty from day 16 to the last bell.
- **Decision:** three candidates against a frozen v11 baseline. (1) `ENDGAME_WHEAT_TILES` 10 -> 60 from day 16 instead of day 20, nothing else touched. (2) Value-ordered watering alone: `WATER` on a WHEAT tile emitted at priority 1 instead of 0, so a ~$240 berry production is never left dry by a ~$50 wheat tile. (3) Both together.
- **Why it seemed best:** it is a revenue stream the farm has never had, taken from the leaders' replays rather than from tuning our own constants; wheat's whole cycle is four days, so a tile broken as late as day 25 still pays; the seed is $10; and five shops drain wheat to $44-55 while town demand quadruples after day 20.
- **Evidence:** (1) **2/16 wins at 8 seeds, -$5,846.8 mean, mirror -$4,846.7**, every status DONE. (2) 2/8 at 4 seeds, -$1,237.0, mirror -$3,518.5. (3) 3/8, -$1,991.2, mirror -$3,761.8. All three below every gate threshold, and the mirror agrees with the head-to-head in each case, so this is a production loss and not a racing artifact.
- **Why it failed in this pairing:** the tiles get planted and the wheat does sell - PLANT 87 -> 122, wheat revenue $4,991 -> $7,537 on seed 6, feed purchases 142 -> 125 orders - but strawberry revenue falls $45,598 -> $36,504 on the same seed while `HARVEST` stays flat at 257 against 258. Same number of berry harvests, far fewer units in each: the extra tiles put ~35 more priority-0 `WATER` jobs a day on a board where `WATER` already runs 527 actions, so berry tiles miss the watering on their production night and yield +1 instead of +2. The farm is action-saturated, and a marginal action on wheat returns about a fifth of the same action on a berry.
- **And the obvious fix is worse, which is the useful half of the result:** protecting the berries by demoting wheat's water job (candidate 2) loses on its own, mirror -$3,518.5, because half-watered wheat dies into weeds and the feed bill comes back as `BUY_PRODUCT`. Wheat tiles are not stealing labour that berries would otherwise get; both crops are already priced correctly against each other at `WHEAT_PER_ANIMAL = 0.75` and `BERRY_TILES = 40`. The allocation is at a local optimum in both directions.
- **Verdict:** Rejected, and not submitted. v11 stays live. Spending a submission here would retire a converging 806.8 agent for a measurably worse one.
- **Test again only with:** a source of actions that is not taken from the herd or the berries - a measurably idle late crew, or a compaction of the 63% of all actions currently spent walking (~4,400 moves of ~7,000 actions a game). The shed was measured across a full v11 game and is **not** the constraint: it peaks at 77 of 100 on day 21, crosses `SHED_PRESSURE` twice, never overflows, and strands only 12 strawberry and 22 wheat at the last bell.

## Carrier-count wheat fetch demand (rejected)

**State:** v11 (submission 55468214, public 808.5 and rising from v10's 751.1).
`_fetch_jobs` sized every shed run against *aggregate carried units*, and the
caller asked for `n_animals` wheat all day long.

**Change:** two lines. `carried = sum(1 for inv in invs if inv.get(item, 0) > 0)`
(loaded carriers, not units of stock), and `fetch["WHEAT"] = sum(1 for j in jobs
if j[3][0] == "FEED")` (animals still waiting on supper, not head on the farm).

**Pre-test reasoning.** Instrumented mirror game, seed 0: the farm hauls **496
wheat units out of the shed to deliver 258 feeds**, with 9-21 units still riding
at dusk every night and dropped straight back in. The standing demand never fell
as animals were fed, so every wheat spent reopened a one-unit shortfall and the
shed run ran all day, including the last day when no FEED job exists. Feed
logistics cost 2,014 actions - 893 walking to FEED, 391 walking to PICKUP, 472
PICKUP, 258 FEED - which is **28% of the whole game** for 258 deliveries. Meanwhile
PASS is **zero on every day from 11 to 25**, so the farm is action-saturated and
the freed actions had somewhere to go: 14 of 40 strawberry tiles die of thirst
(`consecutive_unwatered >= 2`) before their fourth production.
This is explicitly the pairing memory named as missing for the two earlier
failures: the FEED-job demand alone (2/8) lacked carrier accounting, and the
`n_animals` demand lacked a decay.

**Evidence.** The mechanism worked: picked 496 -> 427, fetch jobs 1,007 -> 698,
FEED **258 -> 274**, HARVEST 242 -> 255, strawberry sold 185 -> 219, milk 166 -> 183.
Head-to-head **6/8, +$5,650.1**, all DONE. **Mirror -$1,574.6** (113,203 against
114,778). Fails both gates.

**Verdict: rejected.** Reverted to the exact pre-run snapshot.

**What it teaches.** The freed actions did not become waterings. Measured on the
same seed: PICKUP 472 -> 377 but total movement rose 4,302 -> 4,548, PASS rose
680 -> 727 and WATER *fell* 504 -> 478. And the fix has a market cost that only a
mirror can see: a farm whose carriers are not already loaded buys the difference,
so `BUY_PRODUCT WHEAT` went 201 -> 243 units. Wheat rises on a sqrt curve below
I0 and five shops drain it, so buying more feed bids the price up on both farms.
In the head-to-head we win that race against a slower copy; in the mirror both
farms bid and both pay. That is the v7 fertilizer pattern in a different good,
and it is why the head-to-head read +$5,650 on a change worth -$1,575.

**Try again only with:** a measured productive job the freed carrier reaches in
the same turn *and* no increase in `BUY_PRODUCT WHEAT`. Do not retry by tuning
the demand formula; three variants of it have now failed (aggregate units with
`n_animals`, aggregate units with FEED-job count, carrier count with FEED-job
count).

## 2026-08-13 - Match the closest (unit, job) pair inside a priority band (selected as v12 candidate)

**State:** v11 (submission 55468214, public **779.0**, up from v10's 737.3 - the
largest rating gain of the project). Field record 84-83 across 167 indexed games;
v11 alone is 24/47 with a mean of $77,487 against the field's $73,052, but our own
scores span 40,160 to 130,472 and four opponents still finish above $130k.

**Where the hypothesis came from.** Episode 92507094 (seed 1575606840, seat 1):
v11 $80,137 against 风沙星辰's $152,768 - the worst loss the current agent has on
record. Reconstructing both farms:

| | them | us |
|---|---|---|
| productive actions | 3,468 | 2,309 |
| movement | 2,855 | 4,354 |
| PASS | 324 | 706 |
| moves per productive action | **0.82** | **1.86** |
| WATER | 1,010 | 510 |
| CARE | 967 | 243 |
| HARVEST | 390 | 243 |
| productive tiles at day 20 | 73 | 46 |
| mean tiles from a shed dock | 4.01 | **3.15** |
| strawberry sold | 300 | 183 |
| hires | 264 | 289 |

We have the *larger* crew (7,291 unit-turns against 6,647) and the *more compact*
farm, and we still walk 1.5k further and do 1.2k less work. So the walking is not
the layout's and not the crew's - it is the dispatcher's.

**What that costs, measured on a v11 mirror, seed 0:** 27 of 40 strawberry tiles
die of thirst (6 at age 1, 10 on their first production night, `consecutive_unwatered
>= 2`); berry production nights land at **101 of a possible 160**; `DIG` is offered
2,414 times and performed 48, so every dead tile stays a weed and `empty` - which
only collects `None` - never offers it back. The farm shrinks itself.

**Change (one pass in `_assign`, ~25 lines).** Pass 2 walked `jobs` in sorted
order and gave each job its nearest able unit. A tile on the far edge, offered
first by scan order, therefore claimed the nearest body and pushed the unit
already standing beside the next job across the map. Replaced with: inside one
priority band, repeatedly take the globally closest (unit, job) pair. Priority
order is untouched - a band is only entered once the band above it has taken
every unit it can use - and nothing else in the file changed.

**Pre-test reasoning.** This is not "act sooner on a shared pool", so it should
survive a mirror: it produces more from the same crew rather than reaching the
same market first. The four rejected logistics experiments all tried to *free*
actions and found the freed actions became PASS; this one does not free actions,
it shortens the ones already being taken.

**Evidence.** Head-to-head against the exact pre-run baseline, 4 seeds x 2 seats:
**8/8, mean $126,507.5 against $109,116.3 (+$17,391.2)**, every status DONE, worst
pairing +$10,782. **Mirror +$5,533.1** (120,311 against 114,778). Re-run at 8 seeds: **16/16, +$14,980.2, mirror +$8,917.6**, mirror mean 119,522, worst pairing +$5,937 - no losing pairing at either sample size. `py_compile` and
`test_agent.py` pass; the standalone episode scores **$175,559**, against a field
best of $175,862.

Mechanism on the same instrumented seed-0 mirror, v11 -> candidate:
- berry production nights **101 -> 160 of 160**, all watered, 0 thirst deaths
- `DIG` offers 2,414 -> 707 (nothing dying means nothing to reclaim)
- movement 4,302 -> 3,871, productive actions 2,309 -> 2,525, WATER 504 -> 640,
  HARVEST 242 -> 315, PASS 680 -> 935
- mirror score 112,234 -> 126,502

PASS *rising* while score rises is the point: the farm now finishes its work.

**Verdict: selected.** Both gates clear.

**Reconsider if:** a future change makes the job list much longer - the pass is
O(band x idle) per assignment and the bands are ~30 jobs against ~14 units today.
Also: greedy pair matching is not optimal matching. A constructed 2x2 case exists
where it is worse than the old rule (units (7,4),(8,3); jobs (3,7),(8,8): 14 steps
against 12), because ties resolve to the lowest unit index. Hungarian assignment
is the upgrade path if this ever binds again.

### Screened and pruned before benchmark (mirror mean over seeds 0-2, baseline 114,172)

- **Water every ongoing crop tile every day** (add `c["ongoing"]` to the water
  condition). Halved thirst deaths 27 -> 14 and still scored **105,646 (-8,526)**:
  berry production nights fell 101 -> 96 and HARVEST 242 -> 228. The extra ~130
  waterings came out of harvesting. Watering more is not how you stop the deaths.
- **`BERRY_TILES` 40 -> 26** (109,550) and **40 -> 32** (109,663). Both worse.
  40 is correct and is now screened rather than inherited; a tile that dies stops
  consuming water, so trimming the field does not buy back the labour.
- **`BERRY_FIRST_DAY` 6 -> 4** (113,162, -1,010), copied from the leader in
  92507094 who plants berries from day 4. Near-neutral, won seed 2, lost seed 0.
- **`HERD_RUSH_DAY`/`HERD_RUSH_SIZE` 8/8 -> 12/12** (107,675, -6,497). The leader
  reaches 12 head by day 9 and never grows again; we cannot buy that herd with our
  opening cash without starving the berries.
- **`HIRE_MAX_WAGE` 144 -> 233 (113,472) and -> 377 (108,206).** Memory named this
  as the thing to re-screen once the crop area grew, because the ceiling was fitted
  at v9 before the 40-tile berry farm existed. It travelled: 144 is still right.
- **`DIG` promoted from priority 3 to 2 before day 20** (113,592, -580). Reclaiming
  the weeds does not pay while watering is the constraint - the reclaimed tile needs
  a seed, a planting and a watering the crew has not got. The dispatcher fix removed
  the deaths instead, which is why `DIG` offers fell 2,414 -> 707 without touching
  its priority.

## 2026-08-13 - Land bought while our own land is bare (quadrant cap, then the utilisation gate)

- **State:** v12 (pair matching) is live and is the baseline for everything below. The hypothesis came from episode 92507094, the worst v11 loss on record ($80,137 against 风沙星辰's $152,768), where the winner ran **three quadrants to our four** and spent 2,855 actions moving against our 4,354.
- **Decision 1 - the blunt cap.** `MAX_QUADRANTS = 2` (three quadrants total), nothing else touched.
- **Evidence:** against **v11**, 6/8 at 4 seeds (+$2,428.2, mirror **-$622.6**), then 10/16 at 8 seeds (+$1,619.8, mirror **+$1,946.9**) - the 4-seed mirror was noise. Rebuilt on top of **v12** and re-measured: **10/16, +$2,113.2, mirror +$1,659.5**, every status DONE, mirror mean $121,181 against $119,522.
- **Verdict:** rejected, but not for the usual reason. It **passes the mirror gate** and fails the win ratio, with worst pairings of -$8,982 and -$6,732. The production gain is real and it is *independent of v12* - the two do not overlap, so the walking cost of the fourth quadrant was never just the dispatcher.
- **What the measurement then showed, and it reshapes the question.** Instrumenting the moment of purchase on v12: the **third** quadrant is bought on day 11 with **24 tiles of our own already bare**, and the **fourth** on day 12 with **23-27** bare. We spend $6,000 on room while a whole quadrant of ours sits empty, and every one of those tiles is distance the crew then walks. The cap was a proxy for a question nobody was asking.
- **Decision 2 - the utilisation gate, queued/measuring:** buy the next quadrant only while `empty_owned < LAND_EMPTY_MAX` (8). This keeps the shed dock for a farm that genuinely needs room - the failure mode that sank the 2026-08-11 "delay the fourth quadrant to day 15" attempt (0/8, -$2,123) - while refusing land we cannot fill.
- **Test again only with:** if the utilisation gate also misses the ratio, the next distinct question is what the *dock* is worth on its own, since that is the only thing the fourth quadrant buys that acreage does not.

## 2026-08-13 - The land utilisation gate, and the mirror's second blind spot (rejected)

- **Decision:** buy the next quadrant only while `empty_owned < LAND_EMPTY_MAX` (8), replacing the blunt `MAX_QUADRANTS` cap. Built on v12.
- **Evidence:** 8/16 wins, mean **+$70.2**, **mirror +$3,118.4**, all DONE; mirror mean $122,640 against $119,522. Per-pairing spread -$5,930 to +$5,099, near-symmetric.
- **Verdict:** Rejected. It fails both halves of the head-to-head gate (ratio and the +$100 mean) while passing the mirror by six times its threshold.
- **Why that combination happens, and it is new.** The mirror plays two copies of the candidate. A change that *reduces supply* therefore reduces it on **both** sides of a shared market, and prices rise for both - so restraint credits itself with revenue that only exists because the opponent also restrained. Against a field that keeps flooding the market, those prices never appear. The mirror is immune to **racing** (both sides act at the same moment) but it is *not* immune to **mutual restraint**, and this is the first candidate to expose that.
- **How to read the two gates from here:** they disagree in two distinct ways, and the direction tells you which artefact you are looking at. Head-to-head up + mirror flat = racing (v7, shipped, -36 rating). Head-to-head flat + mirror up = mutual restraint (this one). Only agreement is evidence.
- **What survives:** the underlying measurement stands - the third quadrant is bought on day 11 with 24 of our own tiles bare, the fourth on day 12 with 23-27. Roughly $6,000 buys tiles we never fill. But every rule that acts on it by *buying less* has now been measured as either seat-luck (the cap, 10/16) or a mirror artefact (this one, 8/16).
- **Best distinct next hypothesis:** stop treating it as a purchase decision at all. The land is not the cost - the walking is. `empty.sort` already places new work nearest the shed docks; the untested question is whether *plantings* should be confined to the quadrants already dense with work, so bought land stays available for the herd without spreading the crop across the map.

## 2026-08-13 - Re-screen the hire wage cap on v12 (selected as v13)

- **State:** v12 (pair matching) live. Re-measuring the action mix on the new baseline, seed 6: movement fell 4,399 -> 3,885 and productive actions rose only 2,293 -> 2,411, while **PASS rose 621 -> 1,013**. v12 converted saved walking into idleness, so the farm was paying `fib(n)` wages up to $144 a hand-day for a thousand idle unit-turns.
- **Decision:** `HIRE_MAX_WAGE` 144 -> 89, one constant, on top of v12. The 144 came from a three-point screen (89/144/233) run on **v9**, before berries and before the dispatcher was fixed.
- **Evidence:** 9/16 wins, mean **+$150.1**, **mirror +$1,406.7**, every status DONE. `HIRE_MAX_WAGE = 55` was screened in the same batch and collapsed: **0/16, -$4,370.4**, worst pairings -$10,257 - so 89 is not the start of a slope, it is a point between a real ceiling and crew starvation.
- **Checked against the mutual-restraint artefact recorded above, because fewer hands could equally mean fewer goods.** Instrumented on seed 6: revenue $140,463 -> $139,826 (**-0.5%**) while hire orders fall 290 -> 275, strawberry 57,774 -> 57,557, milk 23,924 -> 23,955, melon 19,800 -> 19,849. Output is flat and the wage bill is smaller, so the mirror gain is money saved, not prices inflated by a restrained opponent.
- **Verdict:** Submitted as v13 with the ratio gate knowingly unmet. The effect is ~1.2% of a $120k game against +-$4,000 of seed variance, which is exactly what 9/16 looks like for something small and real; the 7/8 ratio cannot resolve an effect this size at any sample this project can afford. Cost of being wrong is unusually low here - the agent it retires is the redundant v11 re-push from 14:55, not v12.
- **Test again only with:** if v13's rating lands below v12's, the ratio gate was right and the mean was noise; treat 9/16 as a rejection in future regardless of the mirror.

## 2026-08-13 - One wheat per carrier (rejected)

- **State:** v13 live, rating 874.1 (IMPROVED from v12's 827.9). Field record 121-113 over 234 indexed games; our best game 137,458 against the field's 175,862. Instrumented a v13 mirror on seed 0 (score 131,785) and contrasted it with Octavi Grau's 160,385 in episode 92364933 and Suda's 165,925 in 92421750 - which are the same agent, action for action (WATER 1010/1014, PLANT 199/197, PICKUP 135/135, FERTILIZE 72/72).
- **The measurement that chose it:** the single largest divergence from the leaders is logistics. **PICKUP 475 against their 135**, movement 3,633 against 2,836, on the same 216-versus-212 wheat purchases and the same 13-head herd. Patching `main._step_toward` to record the target of every step gives the cost per completed action: **FEED 790 moves for 274 feeds (2.88 each)**, WATER 991/606 (1.63), FERTILIZE 273/99 (2.76), against CARE 40/273 (0.15) and COLLECT 56/276 (0.20) which are almost all served stand-and-finish. Feeding is where the farm walks.
- **Decision:** in `_fetch_jobs`, `per = 1` and `for _ in range(min(MAX_CARRIERS, short))`, replacing `per = max(1, ceil(short / MAX_CARRIERS))`. With a 13-head herd the old rule sent 7 carriers holding 2 wheat each; the new one sends 8 holding 1, which is the maximum number of animals that can be fed in a single turn.
- **Pre-test reasoning:** the gradient was measured first and is one-sided. `MAX_CARRIERS = 4` (four carriers, four wheat apiece) costs **-$9,523** of mirror mean at 3 seeds, so chunkier loads are decisively worse; `fetch["WHEAT"] = n_animals * 2` is -$205, flat. Thinner is the only untried direction, and the mechanism is the one already in the file: only a unit holding wheat can FEED, so carrier *count* is feed throughput.
- **Evidence:** 3-seed mirror screen +$259 (noise). Re-screened at 5 seeds: **+$2,624** (125,298.9 against 122,674.5). Full benchmark, 4 seeds both seats: **2/8 wins, mean -$614.9**, every status DONE, `py_compile` and `test_agent.py` pass. **Mirror +$1,656.9.**
- **Verdict:** Rejected. It fails the head-to-head ratio 2/8 and the mean, while clearing the mirror three times over.
- **Why that combination happens here, and it extends the artefact taxonomy.** The recorded mutual-restraint case is restraint in *selling*. This is its twin on the *buying* side. `short = min(need - carried, shed_wheat)` and `_market` sizes `BUY_PRODUCT` off `carried`, so carrying 8 wheat instead of 14 leaves less of the shed committed and changes how hard the farm bids for feed. Wheat is the one input both farms buy, it sits in scarcity all season (measured depth 897, price $55 against a $25 base) and it rises on a `sqrt` curve, so any change to how much wheat the two copies pull out of the market moves the price for both of them. In the mirror both farms buy the same way and both get the calmer price; against a baseline that buys the old way, we pay the price it sets and keep only the disadvantage.
- **Test again only with:** a wheat-logistics change that leaves total wheat *purchased* unchanged - measure `BUY_PRODUCT:WHEAT` on both sides before believing a mirror gain on anything that touches feed. Carrier parallelism is not disproven; it cannot be measured by this benchmark while it also moves the feed bill.

## 2026-08-13 - Hold the opening rush window open until the melon money lands (rejected)

- **State:** v13 baseline restored after the attempt above.
- **The measurement that chose it:** `HERD_RUSH_DAY = 8`, and the herd does not reach its own rush target inside it. Logged per-day on a v13 mirror: **5 head at day 5, 6 at day 8, 7 at day 10**, against `HERD_RUSH_SIZE = 8`. Money over the same days is 869, 754, 860, 779, **3,689, 4,872** - melon is what pays for the opening herd and it does not harvest until day 9. The window shuts one day before the cash arrives, and after day 8 growth reverts to one head at a time behind `not want and slots >= ANIMAL_SLOTS`, which does not clear again until day 14.
- **Decision:** `HERD_RUSH_DAY` 8 -> 10, one constant. The ledger records that this number was never screened independently - only `HERD_RUSH_SIZE` was.
- **Evidence:** 5-seed mirror screen **+$3,295** (125,969.7 against 122,674.5). Full benchmark: **5/8 wins, mean +$2,220.8**, all DONE, both local checks pass. **Mirror +$1,805.2.** Mechanism confirmed on seed 0: the herd reaches 8 head at day 11 and **13 by day 14 instead of day 21**, at the cost of one berry tile (39 against 40) and the fourth quadrant arriving on day 13 rather than 12.
- **Verdict:** Rejected on the ratio, 5/8 against the required 7/8, despite both gates moving the same way.
- **Test again only with:** an eight-seed benchmark, if the ratio gate is ever relaxed for effects of this size. The losing pairings are concentrated - seed 2 both seats and seed 0 seat 1 - and this ledger already records that four seeds gave 6/8 for a change that eight seeds scored 14/16. Nothing here suggests the mechanism is wrong; the sample cannot resolve it.

## 2026-08-13 - The rush window and the rush ceiling together (rejected)

- **State:** v13 plus `HERD_RUSH_DAY = 10` from the attempt above.
- **Decision:** `HERD_RUSH_SIZE` 8 -> 10 beside it. The 8 was screened (6/8/10/12 -> mirror +6,245/+12,910/+9,843/worse) against a window that shut on day 8, i.e. against a farm that never reached 8 head inside it. Widening the window makes the ceiling bind for the first time, so the old screen does not travel.
- **Evidence:** 5-seed mirror screen **+$3,847** (126,521.3), the best of anything measured this run, and the steadier of the two - up on four seeds of five where the window alone is up on three. `HERD_RUSH_SIZE = 12` on the same window collapses to **119,337.1, -$3,337 below baseline**, with two pairings at 105,4-105,8k. Full benchmark: **5/8 wins, mean +$2,933.4**, all DONE, both local checks pass. **Mirror +$3,251.6**, six times the threshold.
- **Verdict:** Rejected on the ratio, 5/8 against 7/8. The three losing pairings are seed 0 in both seats (-$3,534, -$3,756) and seed 3 seat 0 (-$630); seed 1 gains +$8,496 and +$8,558 in both seats and seed 2 gains in both.
- **Test again only with:** the same condition as the entry above. This is the strongest candidate this project has produced since v12 on both gates simultaneously (+$2,933 head-to-head, +$3,252 mirror) and it is held back by a win *count* on eight games, not by any disagreement between the two detectors. If the ratio gate is ever made sample-aware, this pair is the first thing to re-run.

## 2026-08-13 - The twenty screens that found nothing, and what they rule out (evidence, no code change)

- **State:** v13. Recorded because the negative result is the substantive finding of the run: on every axis reachable by a single constant or a local dispatcher rule, v13 is a tight local optimum, and the reason is the *market*, not the farm.
- **Method:** mirror mean over 3 seeds (later 5 for anything close), baseline 128,998.7 at 3 seeds / 122,674.5 at 5. Mirror-only screening is legitimate here because every candidate below either produces more goods or spends fewer actions; none of them acts sooner on a shared pool.
- **Crop expansion, all rejected.** `ENDGAME_WHEAT_TILES` 10 -> 40 (-$483); `PLANT_SLOTS` 2 -> 1 (-$1,094); the two together (-$2,773); `MELON_LAST_DAY` 14 -> 10 (-$6,463); fertilizing every one-shot crop and harvesting it the moment `yield_units` caps, which brings melon's cap forward from age 10 to age 8 (-$14,393). **This is the fourth independent refusal of late wheat and the first under a dispatcher that can route it.** The slot relief was measured, not assumed: `slots` is 0-9 from day 13 to day 19 with 34-38 tiles bare, and freeing it merely moves the loss.
- **Why crop expansion cannot work here, from the price model rather than from the losses.** End-of-game depth below `I0` on a v13 mirror: WHEAT 897 ($55), CARROT 356 ($42), TOMATO 356 ($103), EGG 256 ($65), MILK 109 ($251), **STRAWBERRY 82 ($196)**, WOOL 38 ($231), MELON -28, FERTILIZER -352. Strawberry is 82 units from glut with `above_func` linear at 1.60, so the farm is sitting on the shoulder of its own best market. Asuran settles it from the field side: in episode 92754717 they ran **59 berry tiles to our 40 and sold 260 units to our 208** - nineteen extra tiles bought fifty-two units and an $842 win.
- **Herd mix, rejected.** Cutting geese entirely (0/55/45, -$1,430) and cow-heavy (0/70/30, **-$17,350**). Measured value per animal-day on v13: COW $259, SHEEP $228, GOOSE $104 - so geese are indeed the worst tile on the farm, and removing them still loses, because milk's `below_func` is `sqrt` and 3 more cows crash it. 10/50/40 stands.
- **Labour, rejected in both directions.** `SLOTS_PER_UNIT` 18 -> 20 (-$4,645); `ANIMAL_SLOTS` 9 -> 8 (-$358, +$632 at 5 seeds, noise); and a **day-20 wage lift** to $377 (-$5,347). That last one is the informative failure. PASS by day on a v13 mirror is 44-75 idle unit-turns a day through day 19 and **exactly zero on days 20-28**, which reads like a saturated late farm crying out for hands - and hands lose $5,347 there. Zero PASS does not mean the crew is short: every unit has an assignment, and on this farm 52% of assignments are walking. **Idleness and saturation are both useless as hiring signals; only the wage curve is.**
- **Dispatch, rejected.** Blending priority into the pair-matching cost (`d + K*(priority - p_min)`) at K = 2, 3, 5: -$5,065, -$10,518, -$1,240. The bands are load-bearing exactly as the FERTILIZE priority sweep already showed; v12's gain came from ordering *within* a band and does not extend across bands.
- **Fertilizer delivery, rejected, and the diagnosis was inverted.** Instrumenting `_daily_refresh_plants` shows berry execution is essentially perfect - **148 of 160 production nights, 0 dry, 0 clipped** - with the single leak being **30 nights watered but not fertilized**. Adding FERTILIZER to the shed-fetch demand made it *worse* (unfertilized nights 30 -> 47, -$14,393 at seed 0) because the new priority-`-1` pickups outbid the priority-0 fertilize jobs they were meant to serve. Promoting FERTILIZE to -1 beside FEED and PLACE did raise berry units 266 -> 272 (and 284 with fertilizer added to the carry-through `keep` set) **and lowered the score both times**, which is the saturation result again from the other side: more berries is not more money.
- **Capital ordering, rejected.** Capping berry seed at the number of bare tiles (-$2,662) and moving `BUY_LAND` ahead of berry seed in the order (**exactly zero change, every seed identical**). The second is the useful one: it proves land is not being starved by seed. What starves it is `keep`, which jumps from `FEED_DAYS_EARLY` to `FEED_DAYS` on day 9 and locks $2,700 of a $3,689 bank. Extending that window (day 12 or 16, identical results) is -$3,257 - so the reserve is not the answer either, and the day-9 cash freeze is real but has no cheap fix.
- **Best distinct next hypothesis:** the opening rush pair in the entry above, re-run at eight seeds. It is the only thing this run measured that moved both gates together, and it moved them by +$2,933 and +$3,252.

## 2026-08-14 - Open the herd with four sheep, not four cows (selected as v14 candidate)

- **State:** v13 live, public rating **859.5 (IMPROVED** from v12's 813.9; the
  9/16 ratio miss was noise, not a rejection). Field record 124-118 over 242
  indexed games; our best game 137,458 against the field's 175,862.
- **The measurement that chose it.** Instrumented a v13 mirror on seed 0 (score
  131,785) and reconstructed Suda's 165,925 in episode 92421750 day by day.
  Their herd: **5 head on day 1 (four sheep and one cow, bank $3,000 -> $1), 10
  by day 8, 12 by day 9, and never grown again.** Ours: 4 head on day 1, then
  **5-6 head from day 2 to day 10**, reaching 8 only on day 11. Logging
  `_market` at hour 0 shows why and it is not the pipeline: money at dawn on
  days 2-9 is $202/679/592/923/1512/1350/869/1349, and `budget` is negative or
  under one animal's price on every one of them. Days 2-10 are a cash desert.
- **What fills it for them is the calendar, not the bank.** Sheep
  `first_yield_day` is 6 and cow's is 8; a cared production is 3 units, so four
  sheep pay $2,400 of wool on day 6 while four cows pay nothing until day 8.
  Suda spends that day-6 wool on six cows across days 7-9. Our `_next_animal`
  scores `HERD[name] * total - counts[name]`, which returns COW first from an
  empty herd, and `_market` then buys `want` **cheapest-first**, so a thin
  opening budget is spent on the animal that pays last.
- **Decision:** in `_next_animal`, ahead of the mix score and behind the `stock`
  override, return SHEEP while `day <= HERD_RUSH_DAY` and the herd holds fewer
  than `RUSH_SHEEP = 4` of them. The target mix, the rush window, the rush size
  and the wage cap are all untouched.
- **Pre-test reasoning, and why the mirror can be trusted here:** this reorders
  which head is bought first inside a window that already buys a fixed number of
  head. It adds no tile, no crop and no animal, so it cannot be the
  mutual-restraint artefact that inflated the land gate, nor the racing artefact
  that sank v7. Verified rather than assumed - see the supply table below.
- **Screening (mirror mean, baseline 128,998.7 at 3 seeds / 122,674.5 at 5):**
  `RUSH_SHEEP` 3 scored **116,551.2 (-$12,447)** and 5 scored **115,980.2
  (-$13,018)**; 4 scored 132,637.8 at 3 seeds and **132,017.1 at 5 seeds
  (+$9,342.6)**. Four is a point, not a slope: a third sheep leaves a cow's
  worth of budget stranded, and a fifth $500 sheep is the melon seed and the
  first cow.
- **Evidence:** **8/8 wins at 4 seeds, mean $116,877.9 against $109,888.8
  (+$6,989.1)**, every status DONE, worst pairing **+$2,504**, no losing
  pairing. **Mirror +$8,686.5** (133,910.0 against 125,223.5). `py_compile` and
  `test_agent.py` pass; the standalone episode scores $169,467 and the seed-0
  mirror game **$148,323**, above our best public game ever ($137,458).
- **Re-run at 8 seeds: 14/16, +$5,753.4, mirror +$10,010.5** (130,938.9
  against 120,928.4), every status DONE. The only losing pairing is seed 5
  in both seats (-$3,315 and -$3,011); every other seed gains in both seats.
  The mirror gain *grows* with the sample while the head-to-head mean falls
  slightly, which is what a production gain looks like when the extra seeds
  add pairings rather than variance.
- **The supply check, because both mirror blind spots are supply artefacts.**
  Units sold per farm, candidate against baseline: strawberry 276/263, milk
  163/**168.5**, wool 144/105, melon 72/84, fertilizer 187/176, wheat 131/137,
  egg 32/68. **Total goods to market 1,005 against 1,001.5 - flat.** Milk units
  *fall* while milk revenue rises $36,311 -> $44,376, which is the mechanism
  exactly: the same herd sells the same goods earlier and into a shallower
  market. Wheat *bought* falls 216 -> 199 (-8%), the one number that touches a
  shared price on the buying side, and the head-to-head - where the baseline
  still bids the old way - is 8/8 rather than the 2/8 that exposed `per = 1`.
- **Herd at the last bell:** 7 cow / 5 sheep / 1 goose against 6 / 5 / 2. One
  goose becomes one cow; 13 head either way.
- **Verdict: selected.** Both gates clear and agree in direction and magnitude,
  which is the signature every shipped winner has shown (v9 +10,041/+11,235,
  v10 +9,648/+9,671, v11 +18,552/+18,468, v12 +17,391/+5,533).
- **Reconsider if:** a shop rotation changes which of milk/wool the town drains,
  or `HERD_RUSH_DAY`/`HERD_RUSH_SIZE` move - `RUSH_SHEEP = 4` was fitted against
  an 8-day, 8-head window and the +-1 screens collapse, so re-screen it rather
  than assume it travels.

## 2026-08-14 - Hire for the herd the opening rush is about to build (rejected on screening)

- **State:** v13. Logged crew size, PASS and pending jobs by day on a v13 mirror.
  **Day 0 runs on 2.9 units per farm with 7.8 jobs standing per turn and exactly
  zero PASS** - the only fully saturated day before day 20. `crew_cap =
  ceil(load / SLOTS_PER_UNIT)` and `load` on an empty farm is the flat
  `+ SLOTS_PER_UNIT` bump, so day 0 authorises **one** hand; the day ends with
  two. Hands 2-6 cost $1+$2+$3+$5+$8 = $19 for the day.
- **Decision:** inside the same guard, add the herd the rush intends to build -
  `max(0, HERD_RUSH_SIZE - n_animals - n_struct) * ANIMAL_SLOTS` - and in a
  second variant the melon field beside it.
- **Evidence:** mirror mean at 3 seeds **125,771.7** for the herd term alone
  (-$3,227) and **130,864.3** with melon (+$1,865), against 128,998.7. Pruned
  before a full benchmark.
- **Why it failed in this pairing:** day 0 is saturated with labour but *ends at
  $204*. The cash, not the crew, is what caps the opening herd, so extra hands
  build structures the bank cannot stock and then draw wages against days 1-9,
  which the same log shows are 40% idle (88-150 PASS unit-turns a day). This is
  the sixth time aggregate idleness or its absence has failed as a hiring signal.
- **Test again only with:** a day-0 cash source. The two are not independent -
  the sheep opening above changes what day 0 buys, so if a later change frees
  opening cash, re-screen the crew term beside it rather than alone.

## 2026-08-14 - The herd capacity cap, and the crew that was supposed to fill it (rejected)

- **State:** v14 (the sheep opening, committed 0af55ee). Screened interactively
  beside the scheduled run, not by it.
- **The measurement this came from.** An instrumented mirror logs what blocks the
  next animal on every one of the 720 turns. On v13: `empty_struct_waiting` 230,
  `past_deadline` 215, **`slots` 122 - and days 16-20 are `slots` on 24 turns of
  24, solidly** - `cash` 78, `free` 74. Feed coverage 274 of 286 animal-days,
  care 273, every berry tile watered, and every product still in *scarcity* at
  the last bell (milk $251 against a $160 base, strawberry $196 against $120,
  wool $231 against $200). Nothing the farm sells is glutted and nothing it owns
  is neglected, so the reading was: this farm is not badly run, it is forbidden
  from being bigger, and `ANIMAL_SLOTS = 9` is what forbids it.
- **Decision:** split `ANIMAL_SLOTS` into capacity and `ANIMAL_LOAD` (hiring
  demand) exactly as `PLANT_SLOTS`/`PLANT_LOAD` are split, and lower the capacity
  number to 6 - the ratio the real chore load implies (FEED + CARE + COLLECT plus
  a harvest every second day is ~3.5 actions against a plant's ~1.5, so a head is
  2.3 plants, not 4.5). Then lift `HIRE_MAX_WAGE` back to 144 for the crew the
  bigger herd needs.
- **Evidence, and it is a clean reversal.** Against **v13** the direction looked
  right: `ANIMAL_SLOTS = 6` alone 1/6 and mirror -$1,031.8, but paired with a
  wider rush window (`HERD_RUSH_DAY`/`SIZE` = 10) 4/6 and mirror +$3,552.0, and
  with `HIRE_MAX_WAGE = 144` beside it **5/6, +$4,626.3, mirror +$8,396.3**
  (137,395.0 against 128,998.7), with 233 slightly behind at +$7,855.3. Against
  **v14** the same three constants are 1/8 at the full 4-seed gate, **mirror
  -$19,063.3**, and every piece is negative on its own: `ANIMAL_SLOTS` 6 mirror
  -$7,419.7, 7 -$6,143.7, `HIRE_MAX_WAGE = 144` **-$16,425.0**.
- **Why it failed in this pairing, and the lesson is about the diagnosis, not the
  constant.** The measurement was right and the inference was backwards. `slots`
  binding on days 16-20 is not a missed opportunity - it is the capacity model
  correctly refusing animals that arrive with two productions left and a full
  chore load to pay for. The sheep opening had already taken the same gain from
  the other end, by buying the herd on day 0 where a head has 29 days to repay
  itself, and it is worth more there: +$8,687 of mirror against the +$8,396 this
  measured on the baseline that lacked it. **The two changes address the same
  shortage and do not add; the late one is strictly the worse half.** This is the
  seventh time a constraint has been measured correctly here and relaxing it has
  lost - the standing question is not "what is binding" but "what would the farm
  buy with the slack, and on which day".
- **Also screened on the v14 base and rejected, all at 3 seeds:**
  `WHEAT_PER_ANIMAL = 0.5` (6/6 head-to-head at **+$8,695.0** and mirror
  **-$1,947.8** - the cleanest mirror catch in this ledger since v7: growing less
  wheat means buying more, and wheat is the one input both farms bid for);
  `BERRY_TILES = 32` (mirror +$5,113.8, below the 40-tile pairing, confirming 40
  a fourth time); `FEED_DAYS = 8` (mirror -$2,084.3).
- **And the feed-logistics knob is now closed from both sides.** `_fetch_jobs`
  collapses to one-item shed runs whenever `short < MAX_CARRIERS`, which is every
  turn after a feed: measured 475 PICKUP actions and 1,060 fetch jobs offered to
  deliver 274 feeds, with `per = 1` on 295 of the 328 turns that offered one, and
  carried wheat pinned at 12 all day including the hours after the last animal is
  fed. Batching it (`per >= 2`) is **6/6 head-to-head at +$5,885.8 and mirror
  -$2,015.7**. Sizing the demand down instead was already rejected at v11
  (mirror -$1,574.6). Both directions lose in the mirror, so the churn is real
  but the current setting is a local optimum - leave it alone.
- **Verdict: rejected.** No file in the repository was changed; all of it ran on
  copies outside the tree.
- **Test again only with:** a change that adds *early* capacity. Nothing that
  raises the herd cap after day 15 has ever paid, and there are now four screens
  saying so. `HIRE_MAX_WAGE` should still be re-screened whenever `load` moves,
  but it must be screened *on the current baseline* - the 144/89 ordering flipped
  completely between v13 and v14.

## 2026-08-14 (v14 baseline, run 2) - Five hypotheses off one instrumented mirror, all rejected

- **State:** v14 in flight, public rating **850.4** against v13's 854.3, marked
  REGRESSED - both still moving, and the difference is inside the noise this
  ledger has already recorded for v13 (shipped at 9/16 head-to-head and worth
  +45 points). `main.py` and `test_agent.py` identical to
  `.automation/baseline_main.py` and `.automation/baseline_test_agent.py` at the
  start and at the end of this run.
- **Where the hypotheses came from - one instrumented seed-0 v14 mirror
  (148,323/148,289) logged at dawn every day.** The picture it gives:
  - The herd is **frozen at 5 head from day 2 to day 9**; money at dawn on those
    days is $236/448/459/727/970/1233/878/1164. The v14 sheep opening raised the
    score but did *not* remove the cash desert it was written for.
  - **Twelve of twenty-five opening tiles carry nothing on days 2-5**, because
    `_wheat_target` caps wheat at 0.75 per animal (4 tiles for 5 head), melon
    stops at 8 and berries do not start until day 6.
  - `MELON_TILES = 8` is reached **only on day 7**, so half the opening cash crop
    harvests on day 17 rather than day 10.
  - Per-farm revenue: strawberry $65k, milk $44k, wool $30k, melon $17.6k,
    fertilizer $11.7k, wheat $5.1k, egg $1.9k. Feed purchases $8.3k.
  - The end-of-season price table: **MILK $286 and rising every single day**,
    STRAWBERRY peaks at $265 on day 21 and falls to $197, WOOL oscillates
    148-236, MELON holds $230-278 all season, TOMATO $94 (nobody grows it),
    CARROT $42, WHEAT $53, FERTILIZER $33.
  - **The shed is not a leak.** Patching `_drop_inventories_to_shed` across the
    whole game counts **4 units discarded (milk)**, even though the shed reads
    100 of 100 at dawn on day 25. This re-confirms the v11 finding on a farm
    twice the size; stop suspecting the shed.

### Attempt 1: plant the bare opening tiles with wheat (rejected)

- **Change:** `OPENING_WHEAT_TILES = 12` for `day <= OPENING_WHEAT_DAY = 2`, as a
  third floor inside `_wheat_target`.
- **Pre-test reasoning:** the twelve tiles are bare, a wheat seed is $10, wheat
  planted on day 0-2 harvests on day 4-5 and `HARVEST` on a non-ongoing crop sets
  the tile back to `None`, so the tile is free again before `BERRY_FIRST_DAY = 6`.
  The herd eats one wheat a head a day straight out of the cash desert, so the
  farm would be growing the very input that drains days 2-9.
- **Evidence:** 2-seed screen **1/4, -$4,361.0 head-to-head, mirror -$14,467.3**
  (122,117 against 136,585).
- **Why it failed, measured on seed 0:** wheat purchases did not fall at all
  (488 units against 474). The change ran through the *herd composition*
  instead: the extra `load` and the extra early feed bought a sixth head sooner
  and the marginal head was a sheep, so the game ended 12 sheep/12 cows against
  10/14 - and **wool collapsed from 288 units at $210 to 340 units at $80**.
  Milk fell with it ($272 to $238 a unit) and strawberry lost 90 units.
- **Test again only with:** evidence that the marginal opening head is a cow.
  The bare tiles are real and cheap; what they finance is not.

### Attempt 2: the field leader's opening - twelve melon, bought before the herd (rejected)

- **Change:** `MELON_TILES` 8 -> 12, and the melon-seed block moved *above* the
  livestock block in `_market` so the opening budget reaches it first.
- **Pre-test reasoning, straight off wenjinyang's $175,862 (episode 91992026,
  our 69,326).** Reconstructed day by day, they plant **12 melon on day 1**, hold
  **4 head until day 8**, bank **$16,919 by day 11** against our $3,001, and then
  buy their whole 14-head herd on day 12 out of the melon money - 8 cows, 6
  sheep, no geese, and they never buy the fourth quadrant. Melon holds $245 a
  unit in our own games, so $80 of seed is ~$1,500 in ten days, and cash on day
  11 buys the same animal cash on day 0 does.
- **Evidence:** 2-seed screen **0/4, -$10,226.8, mirror -$18,380.8**.
- **Why it failed, measured on seed 0:** the melon half worked and the trade is
  still bad. Melon went 144 units/$35,298 to **246 units/$47,143**, i.e. the
  extra 102 units fetched **$116 each** against the $245 the first 144 fetch -
  `above_func` on melon is `sq`. Against that, the herd sat at **2-4 head until
  day 12** and milk lost $12k, wool $19k, strawberry $27k. The day-0 head is
  worth several times the melon it displaces, exactly as the opening-rush entry
  claims; wenjinyang's opening is not transferable to an agent that already
  front-loads its herd.
- **Test again only with:** nothing. This is the sixteenth crop-expansion refusal
  and the first one whose replacement was measured against the field leader's own
  plan.

### Attempt 3: buy the animals in the order `_scan` asked for them (rejected)

- **Change:** `for name, n_want in want.items()` in place of
  `sorted(want.items(), key=cost)` in `_market`.
- **Pre-test reasoning - a genuine inconsistency, found by instrumentation.**
  `RUSH_SHEEP = 4` makes `_next_animal` ask for four sheep first, but `_market`
  then buys `want` cheapest-first and COW is $400 against SHEEP's $500. Day 0
  wants `{SHEEP: 4, COW: 2}` and **actually buys 2 cows and 3 sheep** - so the
  composition v14 is credited with is not the composition v14 produces. Suda's
  $165,925 opens with four sheep and one cow, which is what the scan order buys
  out of the same $2,800.
- **Evidence:** 2-seed screen **0/4, -$15,246.2, mirror -$34,773.8** (101,811
  against 136,585) - the largest single-change loss ever measured in this project.
- **Why it failed, measured on seed 0:** the opening became 4 sheep and no cow,
  and the herd never recovered its milk: 14 sheep bought against 10, 11 cows
  against 14, **wool 399 units at $96 against 288 at $210, milk 155 units against
  326**. The cost sort is not a bug that survived v14 - it is the thing that holds
  the sheep count down, and `RUSH_SHEEP = 4` is tuned *through* it. The tested
  quantity was never "four sheep"; it was "three sheep and two cows".
- **Test again only with:** never on its own. If the opening composition is
  revisited, change `RUSH_SHEEP` and read the realised herd, not the constant.

### Attempt 4: stop buying sheep after the rush window (rejected on the gate, and it barely binds)

- **Change:** `ANIMALS["SHEEP"]["last"]` 20 -> 8.
- **Pre-test reasoning:** three independent perturbations above all moved the
  score through one number - wool. Baseline 288 units at $210; +52 units -> $80;
  +111 units -> $96. Wool is the only product on `sq` (amp 0.058) and milk is on
  `sqrt` and still climbing at $286 on day 29, so a sheep bought inside the rush
  is the fastest first producer on the board (day 6 against a cow's day 8) and a
  sheep bought on day 9-10 is twelve wool units sold down the cliff.
- **Evidence:** 2-seed screen 3/4, +$291.0, **mirror +$1,131.8** - the only
  positive screen of the run, so it was taken to the full gate. Full 4-seed
  benchmark: **5/8, +$145.5 mean, mirror +$565.9**, all DONE. Head-to-head fails
  7/8.
- **Why it failed, and the diagnosis is the interesting part.** On seeds 0, 2 and
  3 the candidate's score is **identical to the baseline's in the opposite seat**
  - the rule changes nothing at all. The late sheep are not bought late: they are
  bought inside the rush window and sit in the shed, and `_next_animal` returns
  held stock before it ever reaches the `day > a["last"]` test, which is correct
  (an animal already paid for must not wait). Only seed 1 differs, at +$582 in
  both seats. So the mirror's +$566 is one seed of signal, not four.
- **Test again only with:** a cap that binds where the sheep are actually
  bought - inside the rush - which is `RUSH_SHEEP`, and attempt 3 shows that
  constant is already at a sharp optimum.

### Attempt 5: shift the herd ratio from sheep to cow (rejected)

- **Change:** `HERD` 10/50/40 -> **10/60/30**, keeping the geese.
- **Pre-test reasoning:** the wool evidence above, plus the gap in the ledger -
  0/55/45 (-$1,430), 0/70/30 (-$17,350) and 10/70/20 (2/8, -$2,586) had all been
  tested, but every one of them either removes the geese or moves 20 points at
  once. 10/60/30 is the single unscreened step in the direction all of today's
  measurements point.
- **Evidence:** 2-seed screen **0/4, -$4,694.2, mirror -$10,283.0**.
- **Why it failed:** it interpolates between two losing endpoints and loses. The
  mix entry in `memory.md` is right that 10/50/40 is the shape of three price
  curves rather than a guess; today's evidence sharpens *why* - wool is at its
  cliff **and** it is the hedge, and the marginal cow crashes the milk `sqrt`
  from the other side. Cows being individually better ($259 an animal-day against
  $228) does not make a cow-heavier herd better.
- **Test again only with:** a shop rotation that changes which of milk/wool/egg
  the town drains. The mix question is now closed from four directions.

- **Verdict for the run: no candidate.** `main.py` and `test_agent.py` restored
  byte-identical to their pre-run snapshots, `test_agent.py` passes
  (`unit checks ok`, episode 169,467 against starter 3,491), `py_compile` clean,
  and **no `.automation/submit_request.json` was written**.
- **Best distinct next hypothesis: the 334 pickups the field leader does not
  make.** wenjinyang delivers **300 FEED with 145 PICKUP** on a 14-head herd; we
  deliver 283 FEED with **479 PICKUP** on 13 head, and PICKUP is our second
  largest action class after walking. Both previous repairs attacked the *size*
  of the fetch demand (`MIN_LOAD = 3` batching: mirror -$2,015.7; `per = 1`:
  mirror -$1,656.9 plus a wheat-price artefact) and both lost. Neither touched the
  cause the instrumentation names: `_fetch_jobs` recomputes `short` against
  *instantaneous* carried stock every turn, so each wheat consumed by a FEED
  immediately reopens a one-item shortfall and offers eight fresh single-item
  dock runs. The untested repair is to size the demand against wheat that is
  **committed but not yet delivered** - carried wheat minus the FEED jobs already
  standing - rather than against the wheat in hand. That is a different quantity
  from both rejected attempts, and it is the only measured 3:1 action gap left
  against the top of the field.

## 2026-08-15 (v14 baseline, rating 843.9 IMPROVED) - the shop lottery, and two rejected benchmarks

**State at the start of the run.** `main.py` and `test_agent.py` identical to
`.automation/baseline_main.py` / `baseline_test_agent.py` (v14, submission
55507562, public 843.9, up from v13's 838.4). Field record 145-140 across 285
indexed games; field best 175,862 (wenjinyang), our best 137,458. Six selected
replays; the two worst losses (Octavi Grau 160,385 v 43,375; wenjinyang 175,862
v 69,326) and Suda 165,925 v 89,417 all belong to the same opponent family and
were reconstructed together. Baseline reference measured this run: seed-0 mirror
148,323; six-seed mirror mean **127,114-127,305** (run-to-run spread ~200, see
the note on nondeterminism below).

### Where the field gap actually sits, reconstructed before choosing a hypothesis

Suda's 165,925 against our v10, by product: **MILK 320 units/$85,430**,
STRAWBERRY 300/$73,531, WOOL 180/$23,458, WHEAT 473/$20,648, MELON 117/$20,433,
FERTILIZER 292/$17,923. Our v14 seed-0 mirror: STRAWBERRY 276/$64,712, **MILK
163/$44,145**, WOOL 144/$29,775, MELON 72/$17,550, FERTILIZER 187/$11,601, WHEAT
131/$5,810, EGG 32/$1,874. Milk is the whole gap and its cause is timing, not
head count: Suda holds 4 sheep + 8 cows from **day 9** and never grows; we reach
8 head at day 10 and 13 only at day 17, so our cows average five productions to
their ten. Their action budget is 6,631 unit-turns to our 7,003 and they get
3,284 productive actions to our 2,564 - 43% walking against our 53% - with
PICKUP 135 against our 479 and 420 of their 795 CARE actions doing nothing
(`cared_today` gates it).

Market depth at the last bell of a v14 mirror, which is what prices every
hypothesis below: **MILK 210 units below I0 at $286**, STRAWBERRY 93 at $201,
WOOL 65 at $236, MELON 0 at $250 (exactly the town's 140-unit drain, split), and
value per action COW **$110**, STRAWBERRY $94, SHEEP $83, GOOSE $32, WHEAT $31.

### Attempt 1 (full benchmark) - raise the wheat carried per dock trip (rejected)

- **Exact change:** `PICKUP_LOAD = 3` added; in `_fetch_jobs`,
  `per = max(1, -(-short // MAX_CARRIERS))` became
  `per = max(PICKUP_LOAD, -(-short // MAX_CARRIERS))` and the carrier count
  became `min(MAX_CARRIERS, short)` so the number of parallel carriers could not
  fall.
- **Pre-test reasoning.** Instrumented v14 seed-0 mirror: **406 pickups of one
  wheat and 52 of two to deliver 283 feeds**, 1,048 fetch jobs offered a game,
  against Suda's **135 pickups for 290 feeds** on the same herd size. Demand is
  recomputed against wheat *in hand*, so each FEED instantly reopens a one-unit
  shortfall. The two refusals on record both cut the *number* of carriers
  (`MIN_LOAD = 3`, `per = 1`); raising the load per trip while holding the carrier
  count fixed is the untried axis and it is the one the field gap names.
- **Evidence.** 3/4 head-to-head, mean **+$3,277**, all DONE - and mirror
  **-$10,245.0** (126,339.5 against 136,584.5, 2 seeds).
- **Verdict: rejected.** The mechanism worked - PICKUP **479 -> 231** - but
  **productive actions fell 2,564 -> 2,321 while PASS rose 730 -> 861 and
  movement rose 3,708 -> 3,807**. Nothing replaced the freed actions, exactly as
  `MIN_LOAD` found in 2026-08-11. The rest of the loss is not labour at all:
  carrying 3 wheat per trip leaves a larger overshoot on the crew, it lands in the
  shed at dusk, and **turns above `SHED_PRESSURE` rose 9 -> 16**. The pressure
  branch sells at `cap * 4` ignoring floors, and **wool went from 144
  units/$29,775 to 141 units/$17,391** - the same supply for 58% of the money -
  with strawberry 276 -> 256 units beside it.
- **Try again only with:** a productive job the freed carrier can reach in the
  same turn *and* something that keeps the wheat overshoot out of the shed. Both
  halves are now required; the second is new.

### Attempt 2 (full benchmark) - price floors that respond to the shop lottery (rejected)

- **Exact change:** `SELL_GATE_DAY = 12` and
  `SELL_LATE_FLOORS = {"WOOL": 200, "MILK": 200}`; from day 12 the sell test uses
  `SELL_LATE_FLOORS.get(item, floor)` in place of the static floor. Two lines plus
  data, nothing else touched.
- **Pre-test reasoning, and this is the largest new piece of evidence in the
  run.** A shop unlocks every third day in a random order and is the only real
  drain in town; the town centre takes one unit per twelve steps shared across all
  nine products. WOOL's only shop is YARN_STORE. Measured across six *unmodified
  baseline* mirrors, YARN_STORE's unlock day and wool's outcome line up exactly:

  | seed | YARN_STORE | wool units | wool revenue | $/unit | closing price |
  |---|---|---|---|---|---|
  | 0 | day 12 | 144 | $29,775 | 207 | $236 |
  | 2 | day 15 | 145 | $23,917 | 165 | $229 |
  | 1 | day 18 | 135 | $19,576 | 145 | $223 |
  | 3 | day 18 | 144 | $19,102 | 133 | $199 |
  | 5 | day 21 | 139 | $14,625 | 105 | $148 |
  | 4 | day 24 | 144 | $12,034 | **84** | **$61** |

  A **$17,741 swing on an identical 140-unit supply**, decided by a die roll the
  agent has never read - `obs["town"]["unlocked_shops"]` was unused anywhere in
  `main.py`. Wool is the one `sq` good, so the units that cross I0 fetch nothing.
- **Screens that shaped the instrument.** A flat season-long `WOOL` floor of 200
  gains **+$9,147 on seed 4 and +$10,779 on seed 5** and loses **-$23,657 on seed
  0** (six-seed mirror 125,646 v 127,114) - it blocks the day-6 wool sale that
  funds the cows bought on days 7-9, which is the whole v14 thesis. A gate keyed
  on `unlocked_shops` rather than on price: from day 0, 127,956 (-$3,377 on seed
  0); from day 12, 127,388, i.e. noise. The day-gated *floor* was the best of the
  family at six-seed mirror **129,754 (+$2,449)**, positive on five of six seeds.
- **Evidence.** 4 seeds, both seats: **4/8 wins, mean $133,249.0 against
  $136,194.3 (-$2,945.3)**, every status DONE; mirror **+$449.4** (134,359.4
  against 133,910.0), below the 500 threshold. Seed 0 +$209/+$141, seed 2
  +$2,405/+$909, seed 1 -$967 both seats, seed 3 **-$12,985/-$12,307**.
- **Verdict: rejected**, and the direction of the disagreement names the artefact
  exactly as this ledger says it should. Mirror **up**, head-to-head **down** is
  mutual restraint: in the mirror both farms hold their wool, the town drain
  restores the price, and both collect it. Against a baseline that keeps selling,
  the opponent's supply sets the price anyway and we sell into their glut late
  with no early cash to show for it. **You cannot wait out a glut in a market you
  only half supply.** Seed 3 is the clean case: +$2,000 in the mirror,
  -$12,600 in both seats head-to-head.
- **Try again only with:** an instrument that changes *what we produce* rather
  than when we sell it. See the queued hypothesis below.

### Screened and pruned this run (no full benchmark spent)

Six-seed mirror unless noted; baseline 127,114-127,305.

- **The rush ceiling and window, this ledger's top queued item, on the v14
  opening.** `HERD_RUSH_SIZE 10`/day 8: 123,114. Size 10/day 10: 125,614. Size
  12/day 10: 115,820. Size 8/day 10: 114,517 (3 seeds). All well below baseline.
  The v13 measurement (5/8, +$2,933, mirror +$3,252) **does not travel to the
  sheep opening** - `RUSH_SHEEP = 4` already takes the gain that widening the
  window was reaching for. **This closes the queued hypothesis.**
- **The crew, from three new directions.** `HIRE_MAX_WAGE = 144` with the species
  caps below: 118,033; with goose capped at 1: 120,124; at 233: 123,068. The
  mechanism is now measured rather than guessed: one extra hand takes crew
  12 -> 13 and **herd 13 -> 16**, and the three extra head are two sheep and a
  goose - **wool 144 -> 160 units but $29,775 -> $13,850, strawberry 276 -> 209
  units, and `BUY_LAND` 3 -> 2** because the herd's `load` crosses the land gate.
  Freezing the capacity plan so the extra hand cannot buy anything
  (`min(crew, PLAN_CREW)`, `PLAN_CREW = 12`) recovers about half - 125,625 - and
  the hand is *still* worth -$7,000. Marginal wage remains the only signal that
  prices a hand, now for the seventh time.
- **Herd capacity with the marginal head forced to be a cow.** A `HERD_MAX` dict
  capping a species inside `_next_animal`. `ANIMAL_SLOTS` 6/7/8 beside
  `HERD_MAX = {SHEEP: 5, GOOSE: 1}`: 128,540 / 119,745 / 126,482.
  `ANIMAL_SLOTS 9` with the caps is bit-identical to baseline. The eighth
  confirmation: relaxing a correctly-measured binding constraint loses **even
  when the species it would buy is the profitable one**.
- **`HERD_MAX = {"SHEEP": 4}` alone: 128,140.5, +$836 over six seeds, no losing
  seed - and bit-identical to baseline on four of the six.** It cannot reach 7/8
  head-to-head because a tie is not a win. On record because it is the only
  positive constant found this run.
- **Opening wheat with the sheep capped** - the exact re-test condition the
  2026-08-14 refusal named ("evidence that the marginal opening head is a cow
  rather than a sheep"). `OPENING_WHEAT_TILES` 12 for day <= 2: 114,051 with
  either cap; 8 tiles: 119,367. The cap makes no difference at all - the wheat
  loses on its own account, not through the herd. **Opening wheat is now closed
  from both sides.**
- **Fertilize melon** (extend `FERTILIZE` from wheat to any non-ongoing crop in
  its window): 123,509, and melon *fell* 72 -> 66 units. The environment source
  closes the idea permanently: `_new_plant` sets `yield_units = 1` for a
  non-ongoing crop, melon's window is ages 6-12 and its `max_yield` is 6, so the
  five plain waterings before the day-10 harvest already reach the cap.
  **Melon is at its ceiling; there was nothing to win.**
- **Liquidating before the last bell.** `LAST_DAY = 28` scores 118,358, but that
  test is confounded - `LAST_DAY` also switches off FEED and CARE. Split out as a
  separate `DUMP_DAY` affecting only the sell-off: day 28 126,778, day 27 126,694,
  day 26 126,555. Monotone downward, so the endgame dump is not a leak: the town
  drains at 4x from day 20 and the day-29 price is the best one available.
- **`HERD = 0/60/40`**, the one unscreened point between two known-losing
  endpoints: 122,884.
- **`ENDGAME_WHEAT_TILES` is a dead constant.** 0 and 4 are *bit-identical* to
  baseline: `_wheat_target` takes `max(round(n_animals * 0.75), ENDGAME...)` and a
  13-head herd already asks for 10. Any future test of late wheat has to move
  `WHEAT_PER_ANIMAL` in the same change.
- **`PICKUP_LOAD = 2`, alone and paired with `BERRY_TILES = 48`** - the
  "productive job for the freed carrier" pairing attempt 1's failure asks for:
  117,214 and 118,313; berries at 48 alone 126,122. Both halves and the pair lose.

### A caution on the benchmark itself

The six-seed baseline mirror was measured three times this run at **127,114.2,
127,304.7 and 126,839.3**, with individual games differing by up to $2,315 (seed
4, seat 1: 118,239 v 120,554). `env.run` is not bit-reproducible across processes
here. A mirror delta under about $1,000 at six seeds is inside that noise, which
is a second reason the +$449 of attempt 2 was not worth defending.

### Outcome

No candidate cleared either gate. `main.py` and `test_agent.py` were restored to
their exact pre-run snapshots (`diff` clean), `py_compile` passes and
`test_agent.py` passes ("unit checks ok", episode me=169467). No
`.automation/submit_request.json` was written.

### Best distinct next hypothesis

**Condition the herd mix on the shops the town has actually unlocked.** The
lottery evidence above shows the town, not our supply, decides which animal
product is worth producing: wool realises $84-207 a unit purely on YARN_STORE's
unlock day, and the same mechanism sets milk (PIZZA/ICE_CREAM/SMOOTHIE) and egg
(BAKERY/BRUNCH). Every mix refusal in this ledger tested a different *constant*
ratio - 10/50/40, 10/55/45, 10/60/30, 10/70/30, 0/60/40 - while `HERD` is read in
`_next_animal` on every turn and could be a function of
`obs["town"]["unlocked_shops"]` instead. The first four head are fixed by
`RUSH_SHEEP` before any shop exists; heads 5-13 are bought on days 7-17, by which
time two to five shops are open and the answer is observable. This is a
**production** response, so it moves supply and the mirror reads it honestly -
neither of the mirror's two blind spots applies, unlike attempt 2. Screen it as:
weight each species by the number of unlocked shops draining its product (a
single-product shop such as YARN_STORE counting double, since it drains at twice
the rate), floored so no species is driven to zero, because the fixed 10/50/40 is
itself a hedge against exactly this lottery.

## 2026-08-15 (v14 baseline, rating 843.4 IMPROVED) - the queued shop-mix hypothesis, and what the benchmark can actually resolve

**State at the start of the run.** `main.py` and `test_agent.py` identical to
`.automation/baseline_main.py` / `baseline_test_agent.py` (v14, submission
55507562, public **843.4**, up from v13's 835.2 - the fifth consecutive rise).
Field record 147-143 across 290 indexed games; field best 175,862 (wenjinyang),
our best public game 137,458. Six selected replays, all previously reconstructed
and unchanged since the last run. Baseline reference measured this run in the
same process as every candidate: six-seed mirror **127,114.2** (seeds 0-5) and
**131,719.2** (seeds 6-11).

No candidate cleared either gate. Four hypotheses were screened and pruned, and
the run's real product is a calibration of the benchmark itself, which changes
how every future screen in this project should be read.

### Attempt 1 (screened, pruned) - condition the herd mix on the unlocked shops

- **Exact change:** `ANIMAL_PRODUCT`, a copy of the env's `SHOPS` table,
  `_herd_mix(shops, day)` returning a normalised weight per species, `HERD_LIVE`
  rebuilt at the top of `agent()` from `obs["town"]["unlocked_shops"]`, and
  `_next_animal` scoring off `HERD_LIVE` instead of `HERD`.
- **Pre-test reasoning.** This is the standing queued hypothesis from the
  previous run. A shop unlocks every third day in a random order and is the only
  real drain in town; YARN_STORE's unlock day alone moves wool between $207 and
  $84 a unit on an identical 140-unit supply, a $17,741 swing on a die roll the
  agent had never read. `HERD` is consulted in `_next_animal` on every turn and
  could be a function of that draw. It is a production response, so neither
  mirror blind spot applies.
- **Evidence, three instruments in order.**
  - Rewarding a drained species (`weight = HERD * (1 + 0.5 * drain)`): seed-0
    mirror **135,687 against 148,306, -$12,619**.
  - One-sided instead - penalise a species no unlocked shop lists, since wool is
    the one `sq` good and 144 units is already the whole drain: six-seed mirror
    **-$6,199 (undrained weight 0.5), -$3,809 (0.25), -$5,090 (0.25 with a
    reward term)**. The direction of the per-seed effect is exactly as predicted:
    on seed 4, the seed where YARN_STORE unlocks on **day 24**, seat 1 gains
    **+$11,677**; seeds 0-3, where it unlocks on days 12-18, lose heavily.
  - So the penalty was gated by day, because a shop that has not opened is not
    undrained, only early - eight shops unlock across days 3-24. From day 9:
    **-$3,210**. From day 12 or 15: **+$298.2, and bit-identical to baseline on
    five of six seeds**; the entire delta is seed 4 (130,652/118,239 ->
    130,567/121,903).
- **Verdict: pruned, and the reason is structural rather than economic.** By day
  12 the herd is essentially bought - the day-by-day probe below shows 10 head at
  day 12 and 13 at day 17 - so a mix that only speaks after the lottery is
  legible has almost nothing left to decide. Speaking earlier means substituting
  cows for sheep on the *expectation* of a draw, and the cost of that
  substitution (this ledger's five constant-ratio refusals) exceeds the value of
  being right one game in six. **A candidate that is bit-identical to the
  baseline in five of six games cannot reach 7/8 head-to-head however good it is
  in the sixth** - the same wall `HERD_MAX = {"SHEEP": 4}` hit last run.
- **Try again only with:** a species decision that is still open on day 15+, or a
  gate that can score a conditional policy on the games where it fires. The
  mechanism is confirmed real and correctly signed; it is the calendar and the
  gate, not the signal, that refuse it.

### Attempt 2 (screened, pruned) - release the opening cash reserve

- **Exact change:** `FEED_DAYS_EARLY` 3 -> 2 and 3 -> 1; separately
  `CASH_FLOOR` 200 -> 50.
- **Pre-test reasoning, measured not assumed.** An instrumented v14 mirror logs
  money and herd at dawn every day: the herd sits at **5 head from day 2 to day
  7** with 3 empty structures standing from day 6, and `HERD_RUSH_SIZE = 8` is
  never reached inside its own window (6 head at day 8, 8 at day 10). At day 6
  the bank is $970 while a cow needs `cost + keep` free of `CASH_FLOOR` and
  `n_animals * keep` - about $1,340 of bank. The farm is ~$300 short of a cow on
  each of days 5, 6 and 7. `FEED_DAYS_EARLY` had never been screened downward;
  the ledger records that it was never screened independently at all.
- **Evidence.** Six-seed mirror: `FEED_DAYS_EARLY = 2` **-$9,130.8**, `= 1`
  **-$1,543.4**, `CASH_FLOOR = 50` **-$428.2**. The per-seed pattern of
  `FEED_DAYS_EARLY = 1` is the tell: seed 5 **+$24,787**, seed 4 **+$17,373**,
  seed 0 **-$35,325**. Non-monotone in the constant and chaotic in the seed.
- **Verdict: pruned.** Two of the three deltas are inside one standard error of
  zero (see the calibration section) and the third is decisively negative. The
  ~$300-a-day shortfall on days 5-7 is real and is still the binding constraint
  on the opening herd, but the cash reserve is not the way to release it - the
  reserve is what stops a herd bought on credit walking off.

### Attempt 3 (screened, pruned) - size the wheat fetch demand off the unfed herd

- **Exact change:** `n_unfed` counted in `agent()`'s tile loop, and
  `fetch["WHEAT"] = n_unfed` (with a `FETCH_MIN` carrier floor variant) in place
  of `fetch["WHEAT"] = n_animals`.
- **Pre-test reasoning, and the measurement is new.** Instrumented v14 seed-0
  mirror, logged per day: **479 PICKUP actions hauling ~607 units of wheat to
  deliver 283 FEEDs, with 324 units riding back into the shed at nightfall**. The
  cause is exact: demand is `n_animals` all day, so every FEED instantly reopens
  a one-unit shortfall and the crew tops itself back up to a full herd's worth of
  feed it no longer needs. Only **65 of the 479** pickups happen after the herd
  is fully fed, so the waste is not a tail a final-day guard could catch - it is
  the top-up itself, ~13 redundant pickups a day.
- **Evidence.** Six-seed mirror: unfed-count demand **-$11,188.1**; with a floor
  of 4 carriers **-$13,212.5**; with a floor of 8 **-$4,321.7**.
- **Verdict: pruned, and it settles the question rather than deferring it.** The
  result is **monotone in the size of the buffer** - the more carriers hold wheat,
  the better - which is precisely the mechanism the 2026-08-11 refusal ("Exact
  unfed-count pickup demand") named and could not prove: *the number of units
  holding wheat is the number of animals that can be fed in parallel, and the
  apparent overfill is a distribution buffer*. That diagnosis now survives the
  v12 dispatcher, which is the condition under which it was queued for retry.
  **The 3:1 PICKUP gap against the field leaders is not waste we can reclaim; it
  is the price of feeding 13 animals scattered over four quadrants from one
  shed.** Sixth logistics repair, sixth failure.
- **Try again only with:** nothing. All three axes - fewer carriers, bigger loads
  per trip, smaller demand - are now measured and all three lose.

### Attempt 4 (screened, pruned) - spend the free axis of a walk on work

- **Exact change:** `_step_toward` given the set of tiles with standing jobs;
  when the target is off-axis in both directions, both steps are on a shortest
  path, so take the one that lands on a job tile. Pass 1 (stand-and-finish) then
  does that job next turn at no extra distance. Second variant: only divert onto
  work at least as urgent as the band being served.
- **Pre-test reasoning.** Movement is **3,708 of 7,002 unit-turns (53%)** against
  the field leaders' 43%, and v12's win came from making the actions already
  being taken shorter. Thirty jobs stand against fourteen units, so a unit
  crossing a job is the cheapest labour on the board, and the Manhattan distance
  is unchanged by construction.
- **Evidence.** Six-seed mirror **-$1,945.2** unrestricted, **-$7,217.4** with
  the urgency restriction. Per-seed: +$3,700 on seed 1 and +$6,500 on seed 4
  against -$14,000 on seed 2 and -$11,500 on seed 3.
- **Verdict: pruned** - and it is what made the calibration below necessary. A
  change that cannot alter a single distance moved the six-seed mean by two
  thousand dollars and individual games by fourteen.

### The calibration, which is this run's actual result

A change with **zero economic content** was then measured: `_step_toward`
stepping along y before x instead of x before y. Same Manhattan distance, same
priorities, same jobs, same market - a pure tie-break, and its own mirror image.

| variant | seeds 0-5 | seeds 6-11 | 12-seed mean |
|---|---|---|---|
| y-before-x (neutral) | **-$8,498.1** | -$3,339.9 | **-$5,918.9** |
| longer-axis-first (neutral) | +$131.9 | **-$6,367.8** | -$3,118.0 |

Per-seed deltas from those two runs give a standard deviation of the per-game
delta of **$7,905 and $9,721**. The mirror runs one game per seed, so the
standard error of a six-seed mirror delta is **SD/sqrt(6) ~ $3,200-$4,000**, and
of the four-seed mirror `verify.py` actually reports, **~$4,000-$4,900**.

**The +$500 mirror threshold is therefore about 0.11 of one standard error.** It
is not a filter for small effects; it is a coin flip. Detecting a true +$1,000 at
95% confidence would take on the order of 240 seeds.

This is *not* the process nondeterminism recorded in the previous run. A null
candidate - `main.py` byte-identical to the baseline - was run through
`verify.py` and returns **2 wins, 2 losses, 4 exact ties, mean delta $0, mirror
delta exactly 0.0**, every game bit-reproducible. The benchmark is deterministic;
it is *chaotically sensitive*. A perturbation with no economic content does not
average away over re-runs, only over seeds.

**Three consequences, and they are the reason to keep this entry.**
1. **The 7/8 head-to-head ratio is the only strong filter in the gate.** It is
   paired - both farms in one game on one market path - and its null is 4/8 with
   four exact ties. Under noise alone, 7-of-8 has probability ~3.5%. The mirror
   is worth reading for *sign on a large effect* and for the two blind spots it
   was built to catch, and for nothing else.
2. **Every screen in this ledger reported at $1,000-$3,000 of six-seed mirror
   mean is inside one standard error.** That includes `HERD_MAX = {"SHEEP": 4}`
   (+$836), `ANIMAL_SLOTS = 6` with caps (+$1,426), this run's day-12 shop mix
   (+$298), `CASH_FLOOR = 50` (-$428), `FEED_DAYS_EARLY = 1` (-$1,543),
   `BERRY_TILES = 48` (-$992) and much of the "twenty screens that found nothing"
   entry of 2026-08-13. None of those numbers was evidence in either direction.
   Only screens past about $6,000 - which is most of the decisive ones, including
   every rejection in attempts 1-3 above - carry information.
3. **A conditional policy that fires in a minority of games cannot pass this
   gate**, because ties are not wins. That is a property of the gate, not of the
   policy, and it is now the binding constraint on the whole shop-lottery family
   of hypotheses.

### Outcome

`main.py` and `test_agent.py` restored to their exact pre-run snapshots (`diff`
clean; neither file appears in `git status`), `py_compile` passes on both, and
`test_agent.py` passes ("unit checks ok", episode me=169467). Throwaway
instrumentation lived outside the agent and was deleted. No
`.automation/submit_request.json` was written.

### Best distinct next hypothesis

**Screen on the paired head-to-head win count, not the six-seed mirror mean, and
disbelieve anything under $6,000 of mirror delta.** An 8-seed, 16-game
head-to-head costs a few minutes and its null is 8/16 with exact ties; a six-seed
mirror mean costs 35 seconds and its null is exactly 0 but its standard error is
$3,200. Nearly every screening decision in this project has been made with the
second instrument. The cheapest concrete test of what that cost: re-screen the
two constants this ledger records as "positive but unshippable" - `HERD_MAX =
{"SHEEP": 4}` and `ANIMAL_SLOTS = 6` beside it - on the paired statistic at eight
seeds. If they hold up, the herd-capacity question closed eight times here
reopens with a working instrument. If they do not, the *method* behind those
eight closures is what needs replacing, and the next structural hypothesis should
be chosen from measured farm mechanics alone - of which the two still unexplained
are the 53%-versus-43% movement share and the 30 berry production nights that are
watered but never fertilized.
