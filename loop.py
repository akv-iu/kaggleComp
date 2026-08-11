"""Loop maintenance: index replays, pick the informative ones, prune, list attempts.

The point of all four subcommands is to stop the improvement loop from reading
everything. A season of replays is ~17MB each and the ledgers are append-only, so
"analyse every replay and read both ledgers" gets more expensive every run while
telling us less -- 20 wins mostly confirm what we already know.

    python loop.py index      rebuild .automation/replay_index.json (fast, all replays)
    python loop.py select     print the replay files worth reading this run
    python loop.py prune      delete raw replays outside the keep set
    python loop.py attempts   rebuild attempts.jsonl from decision.md

`index` never parses a replay. `rewards` and `info` are serialised before `steps`,
so the first 64KB of a 17MB file already carries the score line and the team names.
"""

import glob
import json
import os
import re
import sys

ME = "akshay"
# Version-controlled on purpose. Once a raw replay is pruned its scores exist
# nowhere else, so this is the only artefact here that cannot be regenerated --
# losing it costs a ~1.3GB re-download. `.automation/` is gitignored; this is not.
INDEX = "replay_index.json"
ATTEMPTS = "attempts.jsonl"

# What each run actually reads. Losses carry the signal; the ceiling games say
# what the score could be if we played a different game.
N_WORST_LOSSES = 3
N_TOP_OPPONENT = 2
N_CLOSE_LOSSES = 2
# What survives on disk. Everything else stays in the index and is re-downloadable
# from Kaggle with `competitions replay <episode>`.
KEEP_LOSSES = 6
KEEP_TOP = 6
KEEP_RECENT = 4

HEAD_BYTES = 65536


def _head_fields(path):
    """Scores, team names and the replay URL, without parsing the file."""
    with open(path, "rb") as fh:
        head = fh.read(HEAD_BYTES).decode("utf-8", "ignore")
    rewards = re.search(r'"rewards":\s*\[([^\]]*)\]', head)
    names = re.search(r'"TeamNames":\s*\[([^\]]*)\]', head)
    if not (rewards and names):
        return None
    video = re.search(r'"LiveVideoPath":\s*"([^"]*)"', head)
    seed = re.search(r'"seed":\s*(\d+)', head)
    try:
        scores = [float(x) for x in rewards.group(1).split(",")]
    except ValueError:
        return None
    teams = [t.strip().strip('"') for t in names.group(1).split(",")]
    if len(scores) != 2 or len(teams) != 2:
        return None
    return scores, teams, (video.group(1) if video else None), (seed.group(1) if seed else None)


def build_index():
    """Merge what is on disk into the existing index; never shrink it.

    The index outlives the raw replays on purpose -- it is the record of every
    episode we have ever scored, and the wrapper's "already seen" test reads it
    to decide what to download. Rebuilding it from the surviving files would
    make every prune schedule its own re-download.
    """
    rows = {r["episode"]: r for r in load_index()} if os.path.exists(INDEX) else {}
    for path in sorted(glob.glob("replays/**/*-replay.json", recursive=True)):
        fields = _head_fields(path)
        if not fields:
            continue
        scores, teams, video, seed = fields
        seat = next((i for i, t in enumerate(teams) if ME in t.lower()), None)
        if seat is None:
            continue
        other = 1 - seat
        # Our own submissions get paired against each other in the public field.
        # Those games say nothing about how the field plays, and averaging them in
        # is how "20-20 overall" hid that the top of the field scores twice us.
        if ME in teams[other].lower():
            continue
        episode = re.search(r"episode-(\d+)-replay", path)
        key = episode.group(1) if episode else os.path.basename(path)
        rows[key] = {
            "episode": key,
            "file": path.replace("\\", "/"),
            "seat": seat,
            "me": scores[seat],
            "them": scores[other],
            "delta": scores[seat] - scores[other],
            "opponent": teams[other],
            "result": "WIN" if scores[seat] > scores[other] else "LOSS",
            "seed": seed,
            # The replay viewer, for watching a loss rather than aggregating it.
            "watch": video or ("https://www.kaggle.com/competitions/kaggriculture"
                               "/leaderboard?dialog=episodes-episode-" + key),
        }
    out = sorted(rows.values(), key=lambda r: r["delta"])
    with open(INDEX, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return out


def load_index():
    if not os.path.exists(INDEX):
        return build_index()
    with open(INDEX, encoding="utf-8") as fh:
        return json.load(fh)


def _existing(rows):
    return [r for r in rows if os.path.exists(r["file"])]


def select(rows=None):
    """Worst losses, the field's best games, and the near-misses. Deduplicated."""
    rows = _existing(rows or load_index())
    losses = [r for r in rows if r["result"] == "LOSS"]
    picked, seen = [], set()
    for r in (sorted(losses, key=lambda r: r["delta"])[:N_WORST_LOSSES]
              + sorted(rows, key=lambda r: -r["them"])[:N_TOP_OPPONENT]
              + sorted(losses, key=lambda r: -r["delta"])[:N_CLOSE_LOSSES]):
        if r["file"] not in seen:
            seen.add(r["file"])
            picked.append(r)
    return picked


def keep_set(rows):
    rows = _existing(rows)
    losses = sorted((r for r in rows if r["result"] == "LOSS"), key=lambda r: r["delta"])
    top = sorted(rows, key=lambda r: -r["them"])
    newest = sorted(rows, key=lambda r: -int(r["episode"]) if r["episode"].isdigit() else 0)
    keep = {r["file"] for r in
            losses[:KEEP_LOSSES] + top[:KEEP_TOP] + newest[:KEEP_RECENT]}
    # Whatever this run was told to analyse must outlive this run's prune.
    return keep | {r["file"] for r in select(rows)}


def prune(dry_run=False):
    rows = load_index()
    keep = keep_set(rows)
    freed = 0
    for r in _existing(rows):
        if r["file"] in keep:
            continue
        freed += os.path.getsize(r["file"])
        if not dry_run:
            os.remove(r["file"])
    return freed, len(keep)


def attempts():
    """One line per recorded experiment, so 'has this been tried?' costs no prose."""
    if not os.path.exists("decision.md"):
        return []
    text = open("decision.md", encoding="utf-8").read()
    out = []
    blocks = re.split(r"^## ", text, flags=re.M)[1:]
    for block in blocks:
        title = block.splitlines()[0].strip()
        verdict = "unknown"
        low = block.lower()
        if "(rejected" in title.lower() or "**verdict:** rejected" in low:
            verdict = "rejected"
        elif "selected" in title.lower():
            verdict = "selected"
        elif "process change" in title.lower() or "analysis" in title.lower():
            verdict = "process"
        wins = re.search(r"(?:won|lost)\s+(\d+)/(\d+)", block)
        mean = re.search(r"([-+]?\$[\d,]+(?:\.\d+)?)\)", block)
        out.append({
            "title": re.sub(r"^\d{4}-\d{2}-\d{2}\s*[-—]\s*", "", title),
            "verdict": verdict,
            "wins": f"{wins.group(1)}/{wins.group(2)}" if wins else None,
            "mean": mean.group(1) if mean else None,
        })
    with open(ATTEMPTS, "w", encoding="utf-8") as fh:
        for row in out:
            fh.write(json.dumps(row) + "\n")
    return out


def _summary(rows):
    mine = [r["me"] for r in rows]
    wins = sum(1 for r in rows if r["result"] == "WIN")
    best = max(rows, key=lambda r: r["them"])
    return (f"{len(rows)} indexed, {wins}W-{len(rows) - wins}L, "
            f"our best {max(mine):.0f}, field best {best['them']:.0f} ({best['opponent']})")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "index"
    if cmd == "index":
        print(_summary(build_index()))
    elif cmd == "select":
        print(json.dumps(select(), indent=1))
    elif cmd == "prune":
        freed, kept = prune("--dry-run" in sys.argv)
        print(f"kept {kept} replays, freed {freed / 1e6:.0f} MB")
    elif cmd == "attempts":
        rows = attempts()
        print(f"{len(rows)} attempts -> {ATTEMPTS}")
    else:
        sys.exit(__doc__)
