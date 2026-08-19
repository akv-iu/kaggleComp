"""Competition-faithful candidate evaluation.

Run: .venv/Scripts/python.exe verify.py BASELINE [N_SEEDS] [START_SEED] [CANDIDATE]

The installed environment differs from observed Kaggle replays in two material
ways: the town centre drains every 12 turns instead of 24, and shops are sampled
without replacement.  This verifier fixes both in-process and fingerprints the
harness in every JSON result.
"""

import importlib.util
import hashlib
import json
import random
import statistics
import sys

import kaggle_environments
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as game


EVALUATOR_VERSION = "competition-v2"
CONFIGURATION = {"townCenterSellInterval": 24}


def _competition_end_of_day(state, env, day):
    """Installed implementation with only the observed shop draw corrected."""
    obs0 = state[0].observation
    cfg = env.configuration
    board_size = int(game.get(cfg, "boardSize", 10))
    turns_per_day = max(1, int(game.get(cfg, "turnsPerDay", 24)))
    weed_chance = float(game.get(cfg, "weedSpawnChance", 0.005))
    shed_cap = int(game.get(cfg, "shedCapacity", 100))
    shop_interval = max(1, int(game.get(cfg, "townShopUnlockInterval", 3)))
    seed = env.info.get("seed", 0)
    rng = random.Random((seed * 1_000_003) ^ day)

    for player_id, farm in enumerate(obs0.farms):
        private = state[player_id].observation.private
        game._daily_refresh_plants(farm, day, turns_per_day)
        game._daily_refresh_animals(farm, day)
        game._spawn_weeds(farm, board_size, weed_chance, rng)
        game._drop_inventories_to_shed(private, shed_cap)
        farm["farmer"] = list(game._default_spawn(board_size))
        farm["hands"] = []
        farm["hires_today"] = 0
        private["inventories"] = [{}]

    next_day = day + 1
    if next_day > 0 and next_day % shop_interval == 0:
        # Kaggle replays contain duplicates, so every unlock samples the full
        # set. Keep this exogenous draw independent of policy-dependent weed RNG
        # consumption so baseline and candidate see the same shop lottery.
        shop_rng = random.Random((seed * 1_000_003) ^ day)
        obs0.town["unlocked_shops"].append(shop_rng.choice(sorted(game.SHOPS)))


# interpreter resolves this global on every end-of-day call, so one patch covers
# every environment constructed below without modifying site-packages.
game._end_of_day = _competition_end_of_day


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.agent


def _env(seed):
    return make("kaggriculture", configuration=dict(CONFIGURATION, seed=seed))


def _sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _fingerprint():
    facts = {
        "version": EVALUATOR_VERSION,
        "configuration": CONFIGURATION,
        "shopSampling": "with-replacement deterministic seed/day draw",
    }
    return hashlib.sha256(json.dumps(facts, sort_keys=True).encode()).hexdigest()


def run(baseline_path, seeds, candidate_path="main.py"):
    candidate = _load(candidate_path, "candidate_main")
    baseline = _load(baseline_path, "baseline_main")
    games = []
    for seed in seeds:
        for seat in (0, 1):
            env = _env(seed)
            env.run([candidate, baseline] if seat == 0 else [baseline, candidate])
            mine, theirs = env.steps[-1][seat], env.steps[-1][1 - seat]
            games.append({
                "seed": seed, "seat": seat,
                "candidate": mine.reward, "baseline": theirs.reward,
                "candidate_status": str(mine.status),
                "baseline_status": str(theirs.status),
            })
    return games


def mirror(path, tag, seeds):
    first, second = _load(path, tag + "_a"), _load(path, tag + "_b")
    scores, by_seed, done = [], [], True
    for seed in seeds:
        env = _env(seed)
        env.run([first, second])
        pair = [state.reward for state in env.steps[-1]]
        scores.extend(pair)
        by_seed.append(sum(pair) / len(pair))
        done = done and all(str(state.status) == "DONE" for state in env.steps[-1])
    return {"scores": scores, "by_seed": by_seed,
            "mean": sum(scores) / len(scores), "all_done": done}


def evaluate(baseline_path, seeds, candidate_path="main.py"):
    games = run(baseline_path, seeds, candidate_path)
    candidate = mirror(candidate_path, "mirror_candidate", seeds)
    baseline = mirror(baseline_path, "mirror_baseline", seeds)
    seed_deltas = [a - b for a, b in zip(candidate["by_seed"], baseline["by_seed"])]
    head_deltas = [game_row["candidate"] - game_row["baseline"] for game_row in games]
    all_done = all(row["candidate_status"] == "DONE" and row["baseline_status"] == "DONE"
                   for row in games) and candidate["all_done"] and baseline["all_done"]
    mirror_result = {
        "candidate": candidate, "baseline": baseline,
        "delta": candidate["mean"] - baseline["mean"],
        "seed_deltas": seed_deltas,
    }
    return {
        "evaluator": {
            "version": EVALUATOR_VERSION,
            "fingerprint": _fingerprint(),
            "kaggleEnvironments": getattr(kaggle_environments, "__version__", "unknown"),
            "configuration": CONFIGURATION,
            "shopSampling": "with-replacement deterministic seed/day draw",
            "seeds": list(seeds),
            "candidateSha256": _sha256(candidate_path),
            "baselineSha256": _sha256(baseline_path),
        },
        "games": games,
        "mirror": mirror_result,
        "summary": {
            "allDone": all_done,
            "headToHeadMean": sum(head_deltas) / len(head_deltas),
            "headToHeadWins": sum(delta > 0 for delta in head_deltas),
            "mirrorDelta": mirror_result["delta"],
            "mirrorMedianSeedDelta": statistics.median(seed_deltas),
        },
    }


if __name__ == "__main__":
    baseline_path = sys.argv[1] if len(sys.argv) > 1 else ".automation/baseline_main.py"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    candidate_path = sys.argv[4] if len(sys.argv) > 4 else "main.py"
    print(json.dumps(evaluate(baseline_path, range(start, start + count), candidate_path)))
