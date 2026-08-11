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
# What survives on disk, in priority order, under a hard budget. Everything else
# is deleted as soon as it has been indexed -- a replay is ~17MB and its scores,
# which are the durable part, are already in the index. Anything deleted is still
# re-downloadable with `kaggle competitions replay <episode>`.
KEEP_TOP = 6      # the ceiling: what the best farms in the field actually scored
KEEP_LOSSES = 6   # where we lose, which is where the next hypothesis comes from
KEEP_RECENT = 4   # fresh material for the next run
MAX_RAW_MB = 250

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


def keep_priority(rows):
    """Most worth keeping first. `prune` trims from the tail until it fits."""
    rows = _existing(rows)
    losses = sorted((r for r in rows if r["result"] == "LOSS"), key=lambda r: r["delta"])
    top = sorted(rows, key=lambda r: -r["them"])
    newest = sorted(rows, key=lambda r: -int(r["episode"]) if r["episode"].isdigit() else 0)
    ordered, seen = [], set()
    # Whatever this run was told to analyse comes first: it must outlive this
    # run's own prune. Then the ceiling, then the losses, then fresh material.
    for r in (select(rows) + top[:KEEP_TOP] + losses[:KEEP_LOSSES]
              + newest[:KEEP_RECENT]):
        if r["file"] not in seen:
            seen.add(r["file"])
            ordered.append(r)
    return ordered


def keep_set(rows):
    keep, used, budget = set(), 0, MAX_RAW_MB * 1_000_000
    for r in keep_priority(rows):
        size = os.path.getsize(r["file"])
        if keep and used + size > budget:
            break
        keep.add(r["file"])
        used += size
    return keep


def prune(dry_run=False):
    """Delete every raw replay outside the keep set.

    Walks the disk rather than the index on purpose. Games against our own
    submissions are deliberately absent from the index, so an index-driven sweep
    would never delete them and they would pile up forever.
    """
    keep = keep_set(load_index())
    freed = 0
    for path in glob.glob("replays/**/*-replay.json", recursive=True):
        if path.replace("\\", "/") in keep:
            continue
        freed += os.path.getsize(path)
        if not dry_run:
            os.remove(path)
    if not dry_run:
        for stale in glob.glob("replays/*"):
            if os.path.isdir(stale) and not os.listdir(stale):
                os.rmdir(stale)
    held = sum(os.path.getsize(f) for f in keep if os.path.exists(f))
    return freed, len(keep), held


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
        freed, kept, held = prune("--dry-run" in sys.argv)
        print(f"kept {kept} replays ({held / 1e6:.0f} of {MAX_RAW_MB} MB), "
              f"freed {freed / 1e6:.0f} MB")
    elif cmd == "attempts":
        rows = attempts()
        print(f"{len(rows)} attempts -> {ATTEMPTS}")
    else:
        sys.exit(__doc__)
