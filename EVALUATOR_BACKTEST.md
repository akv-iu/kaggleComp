# Competition-v2 evaluator calibration

Calibration date: 2026-08-18. Evaluator fingerprint:
`434ad4d76298b0545a2ebeb78ca3bf5ae4e020785a4802661bc03c8e30b915c1`.

The harness uses `townCenterSellInterval=24`. Shop unlocks sample the full shop
set with replacement and use a seed/day-only random stream, so policy-dependent
weed RNG cannot give the compared versions different shop lotteries.

Historical agents were verified against their exact Git blobs. The v6 fixture is
the frozen v7 agent with only the submitted fertilizer sell floor restored from
$5 to $50; the v7 commit also bundled earlier uncommitted work, so its Git parent
is not the baseline used by the original v7 experiment.

## Calibrated seed blocks

The smoke screen uses seeds 16–19. The final gate uses the disjoint seeds 0–11
across both seats.

| Transition | Smoke H2H | Smoke mirror | Final H2H | Final mirror | Median seed mirror | Expected result |
|---|---:|---:|---:|---:|---:|---|
| identical v14 → v14 | $0 | $0 | $0 | $0 | $0 | fail |
| v6 → public-regressing v7 | +$1,164 | +$900 | +$1,140 | **+$795** | +$562 | fail: mirror < $1,000 |
| v12 → known-good v13 | +$1,741 | +$3,831 | +$1,717 | +$2,474 | +$3,087 | pass |
| v13 → known-good v14 | +$7,442 | +$2,145 | +$5,380 | +$2,835 | +$2,156 | pass |

Every recorded status was `DONE`. The final pass rule used here is exactly the
automation rule: mirror delta at least $1,000, positive median per-seed mirror
delta, and head-to-head mean no worse than -$500.

An additional sensitivity run on seeds 4–15 put v7 at +$1,346 mirror, narrowly
above the gate. This is why the calibrated blocks are fixed and fingerprinted,
and why local simulation remains a high-concern proxy rather than submission
authority. Kaggle upload still requires separate human approval.
