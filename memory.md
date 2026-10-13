# Strategy Memory

This is the compact current strategy state. `decision.md` is the frozen historical
archive and `attempts.jsonl` is the authoritative experiment index.

## Current baseline

- Production agent: v14 + shed/carried pressure + price-responsive late herd,
  Kaggle submission `55660052`, scored 891.2 over 40 episodes; prior submission
  `55633392` currently reads 861.6.
- The durable progression was: synchronized livestock (v5), wheat economy (v6),
  wheat fertilization (v8), unblocked herd pipeline (v9), 40 berries (v10), opening
  herd rush (v11), closest-pair dispatch (v12), wage cap 89 (v13), then four early
  sheep to escape the cash desert (v14).
- The field ceiling is $175,862. Strong farms commonly reach 14-15 pasture animals,
  40-46 strawberries, 12-14 opening melons, and either buy large quantities of feed
  or run a much smaller wheat field.

## Evaluator facts

- Kaggle replays use `townCenterSellInterval=24`; the installed environment default
  is 12. The competition therefore drains 70 town-centre units per product per
  season versus 140 in the old local harness.
- Kaggle shops are sampled with replacement. The installed environment samples
  without replacement. Wool has a 34% chance of receiving no YARN_STORE; duplicated
  shops create much wider product-price tails than the old harness.
- The repository verifier now models interval 24 and with-replacement shops. Shop
  draws are keyed only by seed/day so policy-dependent weed RNG cannot give the
  two versions different lotteries. Every result must carry evaluator version
  `competition-v2` and its configuration fingerprint.
- Self-play still has blind spots. Head-to-head rewards racing a shared market;
  mirror play rewards mutual restraint and cannot reproduce an arbitrary field
  opponent's supply. Treat local evaluation as a regression/production gate, not a
  perfect leaderboard oracle.
- Four seeds are only a smoke test. Final evaluation uses twelve untouched seeds.

## What currently works

- Keep livestock purchases synchronized with matching structures after the opening
  rush. Empty structures and crated animals are expensive unfinished intentions.
- Buy the early herd in parallel: production days matter more than small opening
  efficiencies. The shipped sheep-first order is a cash-timing result, not a claim
  that wool is the best late product.
- Build near shed access, match the globally closest unit/job pair within priority,
  and stop FEED/CARE on the final day. Walking and unfinished delivery dominate
  theoretical capacity.
- Grow 40 strawberries only after the opening melon/herd cash cycle. Protect berry
  watering and fertilization; extra low-value wheat work displaces berry yield.
- Keep a wage cap of 89. The v12 dispatcher turned the most expensive late hands
  into idle time; v13 removed those hires without reducing revenue.
- Use fertilizer on wheat rather than selling into a product with no town drain.
- Submit slowly. Ratings need roughly 25-30 external episodes to become useful.

## Binding measurements

- The opening is cash-bound, not labor-bound: most PASS turns occur on days 2-9,
  while the bank is only a few hundred dollars. Filler crops fail because the feed
  reserve and herd already own that cash.
- Days 20-28 are action-saturated. Extra late wheat loses berry watering/production;
  freeing actions without a valuable replacement merely converts work to PASS.
- Greedy closest-pair dispatch is within 1.1% of Hungarian assignment over measured
  priority bands. Do not add an assignment dependency.
- In competition-like interval-24 games, nightly shed overflow can destroy about 87
  goods per farm because units carry more than the available shed room. Spending
  worker turns to haul those goods home loses; pricing pressure on shed plus carried
  stock is the only promising zero-action repair.
- Melon's first crop funds the opening and remains valuable. The second crop is
  usually worth $1-90 in real games because opponents also flood a product with no
  shop demand; local self-play badly overvalues it.

## Ordered candidate backlog

Empty as of 2026-08-20. All three prior items are now closed:

1. `WHEAT_PER_ANIMAL: 0.75 -> 0.5` / `ENDGAME_WHEAT_TILES: 10 -> 0` -- retested
   under the real 12-seed competition-v2 gate on 2026-08-19 (plan-20260819-171304):
   mirrorDelta -$2,371, median -$2,518. Rejected.
2. Shed pressure on `shed_used + carried_total > SHED_CAP` -- tested, passed,
   submitted as `55633392` (plan-20260819-172153). Already live in `main.py`.
3. `MELON_TILES: 8 -> 12` -- `main.py`'s own inline comment already records this
   measured "a third worse" (see the `MELON_TILES` constant); not a fresh test.

No new backlog item has cleared a screen since. 2026-08-20: raising the wheat
surplus sell cap 12->24/turn (reasoned from replay 95015910's shed WHEAT piling to
42 against an ~18 target) screened at -$219 median / +$235 mean over 16 fresh
seeds -- below the gate, despite 27/32 head-to-head wins. See `attempts.jsonl`
`manual-9377055b5416`. Two new losses (95015910 vs GG-bond, -$46,030; 94731597 vs
WarRusher, -$579) both show the opponent as a net wheat *seller* while we are a
net buyer, but this exact mechanism ("wheat as a late cash crop") is already
closed below and the two replays disagree on how one-sided the effect is -- not
enough to reopen it without evidence of idle crew capacity.

2026-08-21: fresh submission `55660052` evidence confirmed the price-responsive
herd improvement (891.2). Four follow-ups all failed the competition-v2 gate:
forced opening sheep 4->2 and 4->3 lost $3,698/$2,241 mirror; conditional no-yarn
wool liquidation was flat over 12 seeds (-$28, median $0); stopping wheat
fertilization lost $3,867; and the berry feed-reserve exemption was a four-seed
no-op. Keep the live code; do not spend a submission on these variants.

## Closed or conditional paths

- Do not retune constant livestock mixes. Cow-heavy, sheep-heavy, zero-goose, and
  higher-goose variants have all failed; shop-conditioned mixes act after most of
  the herd is already purchased.
- Do not add late wheat, reduce plant slot costs, raise hiring alone, or add filler
  tomato/carrot. They consume actions or opening cash already assigned to higher
  return work.
- Do not revisit multi-dock routing, persistent job claims, priority-distance blends,
  or Hungarian assignment without a new route-local measurement.
- Do not raise price floors or hold products merely because a mirror gains. The
  opponent may keep selling while we wait.
- Do not expand berries beyond 40 without a one-sided field model: mirror supply
  crashes the same strawberry market for both farms.
- Do not read one seed as signal. Require the same mechanism across a wider panel.
