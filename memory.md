# Strategy Memory

This is the compact current strategy state. `decision.md` is the frozen historical
archive and `attempts.jsonl` is the authoritative experiment index.

## Current baseline

- Production agent: v14, Kaggle submission `55507562`; last observed rating was
  about 855 and its indexed best game is $138,163.
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

Test one at a time and never combine them:

1. `WHEAT_PER_ANIMAL: 0.75 -> 0.5` with `ENDGAME_WHEAT_TILES: 10 -> 0`.
   Across 18 seeds it was +$3,723 at interval 12 and +$4,557 at interval 24, but the
   obsolete four-seed gate rejected it. It is the strongest unsubmitted candidate.
2. Trigger shed pressure when `shed_used + sum(carried.values()) > SHED_CAP`.
   It costs zero actions and measured +$1,759 at interval 24 and +$1,126 at 12 over
   six seeds; the old gate used seeds where the overflow did not occur.
3. `MELON_TILES: 8 -> 12` without moving seed purchases ahead of livestock.
   Judge it by earlier herd/cash growth, not late melon revenue. A previous melon
   failure changed purchase priority and therefore did not isolate tile count.

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
