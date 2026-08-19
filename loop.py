"""Deterministic maintenance for the evidence-first Kaggriculture loop.

Commands: index, evidence, select, prune, migrate-attempts, attempt-upsert.
The scheduled poll calls these commands; none invokes a model or edits main.py.
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
import hashlib
import json
import os
import re
import sys

ME = "akshay"
INDEX = "replay_index.json"
ATTEMPTS = "attempts.jsonl"
MAX_RAW_MB = 250
HEAD_BYTES = 65536
EVIDENCE_MAX_BYTES = 20_000


def _submission(path):
    match = re.search(r"submission-(\d+)", path.replace("\\", "/"))
    return match.group(1) if match else None


def _head_fields(path):
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
    teams = [team.strip().strip('"') for team in names.group(1).split(",")]
    if len(scores) != 2 or len(teams) != 2:
        return None
    return scores, teams, (video.group(1) if video else None), (seed.group(1) if seed else None)


def _normalise_row(row):
    row = dict(row)
    row["submission"] = row.get("submission") or _submission(row.get("file", ""))
    return row


def load_index():
    if not os.path.exists(INDEX):
        return []
    with open(INDEX, encoding="utf-8") as fh:
        return [_normalise_row(row) for row in json.load(fh)]


def build_index():
    """Merge on-disk replay headers into the durable index; never shrink it."""
    rows = {row["episode"]: row for row in load_index()}
    for path in sorted(glob.glob("replays/**/*-replay.json", recursive=True)):
        fields = _head_fields(path)
        if not fields:
            continue
        scores, teams, video, seed = fields
        seat = next((i for i, team in enumerate(teams) if ME in team.lower()), None)
        if seat is None or ME in teams[1 - seat].lower():
            continue
        match = re.search(r"episode-(\d+)-replay", path)
        episode = match.group(1) if match else os.path.basename(path)
        path = path.replace("\\", "/")
        rows[episode] = {
            "episode": episode, "submission": _submission(path), "file": path,
            "seat": seat, "me": scores[seat], "them": scores[1 - seat],
            "delta": scores[seat] - scores[1 - seat], "opponent": teams[1 - seat],
            "result": "WIN" if scores[seat] > scores[1 - seat] else "LOSS",
            "seed": seed,
            "watch": video or ("https://www.kaggle.com/competitions/kaggriculture/"
                               "leaderboard?dialog=episodes-episode-" + episode),
        }
    output = sorted(rows.values(), key=lambda row: row["delta"])
    with open(INDEX, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=1, ensure_ascii=False)
    return output


def _existing(rows):
    return [row for row in rows if os.path.exists(row["file"])]


def select(rows=None, submission=None):
    """At most three useful replays: worst, ceiling, and closest loss."""
    rows = _existing(rows if rows is not None else load_index())
    if submission:
        rows = [row for row in rows if str(row.get("submission")) == str(submission)]
    losses = [row for row in rows if row["result"] == "LOSS"]
    candidates = []
    if losses:
        candidates.extend((min(losses, key=lambda row: row["delta"]),
                           max(losses, key=lambda row: row["delta"])))
    if rows:
        candidates.append(max(rows, key=lambda row: row["them"]))
    picked, seen = [], set()
    for row in candidates:
        if row["episode"] not in seen:
            picked.append(row)
            seen.add(row["episode"])
    return picked[:3]


def _tile_counts(farm):
    counts = collections.Counter()
    for row in farm.get("tiles", []):
        for tile in row:
            if tile is None:
                counts["EMPTY"] += 1
            elif tile == "LOCKED":
                counts["LOCKED"] += 1
            elif isinstance(tile, dict):
                if tile.get("kind") == "PLANT":
                    counts[tile.get("crop", "PLANT")] += 1
                elif tile.get("animal"):
                    counts[tile["animal"]] += 1
                else:
                    counts[tile.get("kind", "OTHER")] += 1
    return dict(sorted(counts.items()))


def _player_summary(data, seat):
    action_counts = collections.Counter()
    market_counts = collections.Counter()
    market_units = collections.Counter()
    milestones, seen_days, last_obs = [], set(), None
    for step in data["steps"]:
        agent = step[seat]
        action = agent.get("action") or {}
        for item in [action.get("farmer")] + list(action.get("hands") or []):
            if item:
                action_counts[item[0]] += 1
        for order in action.get("market") or []:
            if not order:
                continue
            key = order[0] + (":" + str(order[1]) if len(order) > 1 else "")
            market_counts[key] += 1
            if len(order) > 2 and isinstance(order[2], (int, float)):
                market_units[key] += order[2]
        obs = agent.get("observation") or {}
        if not obs:
            continue
        last_obs = obs
        day = obs.get("day")
        if day in {0, 5, 10, 15, 20, 25, 29} and day not in seen_days:
            farm, private = obs["farms"][seat], obs.get("private") or {}
            milestones.append({
                "day": day, "money": farm.get("money"),
                "hands": len(farm.get("hands") or []),
                "land": len(farm.get("unlocked_quadrants") or []),
                "tiles": _tile_counts(farm),
                "shed": dict(sorted((private.get("shed") or {}).items())),
            })
            seen_days.add(day)
    final = data["steps"][-1][seat]
    names = data.get("info", {}).get("TeamNames", [str(seat), str(1 - seat)])
    return {
        "team": names[seat], "reward": final.get("reward"), "status": final.get("status"),
        "actions": dict(action_counts.most_common()),
        "marketOrders": dict(market_counts.most_common()),
        "marketUnits": dict(market_units.most_common()), "milestones": milestones,
        "finalPrices": dict(sorted(((last_obs or {}).get("market", {}).get("prices") or {}).items())),
    }


def summarize_replay(row):
    with open(row["file"], encoding="utf-8") as fh:
        data = json.load(fh)
    final_obs = data["steps"][-1][0].get("observation") or {}
    return {
        "episode": row["episode"], "result": row["result"], "delta": row["delta"],
        "opponent": row["opponent"], "watch": row["watch"],
        "configuration": {key: data.get("configuration", {}).get(key) for key in
                          ("townCenterSellInterval", "townShopSellInterval",
                           "townShopUnlockInterval", "turnsPerDay")},
        "players": [_player_summary(data, 0), _player_summary(data, 1)],
        "shops": final_obs.get("town", {}).get("unlocked_shops", []),
    }


def load_attempts():
    if not os.path.exists(ATTEMPTS):
        return []
    with open(ATTEMPTS, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _compact_attempt(row):
    return {
        "id": row.get("id"),
        "hypothesis": str(row.get("hypothesis") or row.get("title", ""))[:220],
        "verdict": row.get("verdict"),
        "metrics": row.get("metrics") or {"wins": row.get("wins"), "mean": row.get("mean")},
        "retryCondition": str(row.get("retryCondition") or "")[:240],
    }


def _relevant_attempts(rows):
    """Prefer attempts that bear on the three deliberately queued hypotheses."""
    groups = (("wheat",), ("shed", "carried", "inventory", "pressure"), ("melon",))
    terms = tuple(term for group in groups for term in group)
    scored = []
    for position, row in enumerate(rows):
        text = " ".join(str(row.get(key) or "") for key in
                        ("hypothesis", "title", "retryCondition")).lower()
        score = sum(term in text for term in terms)
        if score:
            scored.append((score, position, row))
    chosen = []
    for group in groups:
        matches = [item for item in scored if any(term in " ".join(
            str(item[2].get(key) or "") for key in ("hypothesis", "title", "retryCondition")
        ).lower() for term in group)]
        added = 0
        for _, _, row in sorted(matches, reverse=True):
            if row not in chosen:
                chosen.append(row)
                added += 1
            if added == 2:
                break
    for _, _, row in sorted(scored, reverse=True):
        if row not in chosen and len(chosen) < 8:
            chosen.append(row)
    for row in rows[-4:]:
        if row not in chosen:
            chosen.append(row)
    return [_compact_attempt(row) for row in chosen[:12]]


def _record(rows):
    if not rows:
        return {"games": 0, "wins": 0, "losses": 0, "ourMean": None,
                "fieldMean": None, "ourBest": None, "fieldBest": None}
    return {
        "games": len(rows), "wins": sum(row["result"] == "WIN" for row in rows),
        "losses": sum(row["result"] == "LOSS" for row in rows),
        "ourMean": round(sum(row["me"] for row in rows) / len(rows), 1),
        "fieldMean": round(sum(row["them"] for row in rows) / len(rows), 1),
        "ourBest": max(row["me"] for row in rows), "fieldBest": max(row["them"] for row in rows),
    }


def build_evidence(submission, output, new_episode_ids=()):
    rows = load_index()
    current = [row for row in rows if str(row.get("submission")) == str(submission)]
    chosen = select(rows, submission)
    ceiling = max(rows, key=lambda row: row["them"]) if rows else None
    stable = {
        "submissionId": str(submission), "newEpisodeIds": list(new_episode_ids),
        "selectedEpisodeIds": [row["episode"] for row in chosen],
        "currentRecord": _record(current), "fieldRecord": _record(rows),
        "fieldCeiling": ({key: ceiling.get(key) for key in
                           ("episode", "them", "me", "opponent", "watch")} if ceiling else None),
        "configurationFacts": {
            "competitionTownCenterSellInterval": 24,
            "installedDefaultTownCenterSellInterval": 12,
            "competitionShopSampling": "with replacement",
            "installedShopSampling": "without replacement",
        },
        "candidateBacklog": [
            "WHEAT_PER_ANIMAL 0.75->0.5 with ENDGAME_WHEAT_TILES 10->0",
            "shed pressure based on shed plus carried inventory",
            "MELON_TILES 8->12 without changing purchase priority",
        ],
        "relevantAttempts": _relevant_attempts(load_attempts()),
        "replays": [summarize_replay(row) for row in chosen],
    }
    fingerprint = hashlib.sha256(json.dumps(
        stable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    packet = dict(stable, evidenceFingerprint=fingerprint,
                  createdAt=dt.datetime.now(dt.timezone.utc).isoformat())

    def encoded():
        return json.dumps(packet, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    if len(encoded()) > EVIDENCE_MAX_BYTES:
        for replay in packet["replays"]:
            for player in replay["players"]:
                player["milestones"] = [m for m in player["milestones"] if m["day"] in (0, 10, 20, 29)]
        packet["relevantAttempts"] = packet["relevantAttempts"][-6:]
    if len(encoded()) > EVIDENCE_MAX_BYTES:
        for replay in packet["replays"]:
            for player in replay["players"]:
                player.pop("marketOrders", None)
    raw = encoded()
    if len(raw) > EVIDENCE_MAX_BYTES:
        raise ValueError(f"evidence packet is {len(raw)} bytes; limit is {EVIDENCE_MAX_BYTES}")
    with open(output, "wb") as fh:
        fh.write(raw)
    return packet


def _verdict(title, block):
    low = (title + "\n" + block).lower()
    if any(term in low for term in ("verdict: rejected", "**verdict:** rejected",
                                    "(rejected", "screened, pruned", "all rejected")):
        return "rejected"
    if "selected" in title.lower():
        return "selected"
    if any(term in low for term in ("process change", "analysis, no code", "evidence, no code")):
        return "process"
    return "unknown"


def _legacy_record(parent, title, block):
    date_match = re.search(r"\d{4}-\d{2}-\d{2}", parent + " " + title)
    wins = re.search(r"(?:won|lost|gate:?|evidence[^\n]*?)\D(\d+)\s*/\s*(\d+)", block, re.I)
    means = re.findall(r"[-+]?\$[\d,]+(?:\.\d+)?", block)
    retry = re.search(r"(?:Test again only with|Condition to try again|Reconsider if):?\s*(.*)", block, re.I)
    name = re.sub(r"^(?:Attempt|Experiment)\s*\d+[^-—]*[-—]\s*", "", title).strip()
    stable = (parent + "\n" + title).encode("utf-8")
    submission_match = re.search(r"submission\s+(\d+)", parent, re.I)
    verdict = _verdict(title, block)
    return {
        "id": "legacy-" + hashlib.sha1(stable).hexdigest()[:12],
        "createdAt": date_match.group(0) if date_match else None,
        "hypothesis": name,
        "changeFingerprint": hashlib.sha256(re.sub(r"\W+", " ", name.lower()).strip().encode()).hexdigest()[:16],
        "baselineSubmission": submission_match.group(1) if submission_match else None,
        "evaluatorVersion": "legacy", "evidenceIds": [],
        "metrics": {"wins": f"{wins.group(1)}/{wins.group(2)}" if wins else None,
                    "mean": means[-1] if means else None},
        "verdict": verdict,
        "retryCondition": retry.group(1).strip()[:500] if retry else None,
        "history": [{"state": verdict, "at": date_match.group(0) if date_match else None,
                     "detail": "Imported from frozen decision.md archive."}],
    }


def migrate_attempts():
    """One-time import of both legacy ## entries and hidden ### attempts."""
    with open("decision.md", encoding="utf-8") as fh:
        text = fh.read()
    headings = list(re.finditer(r"^(##|###)\s+(.+)$", text, re.M))
    records, parent = [], ""
    for index, match in enumerate(headings):
        level, title = match.group(1), match.group(2).strip()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        block = text[match.end():end]
        if level == "##":
            parent = title
            records.append(_legacy_record(parent, title, block))
        elif re.match(r"(?:Attempt|Experiment)\s*\d+", title, re.I):
            records.append(_legacy_record(parent, title, block))
    unique = {record["id"]: record for record in records}
    with open(ATTEMPTS, "w", encoding="utf-8") as fh:
        for record in unique.values():
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return list(unique.values())


def upsert_attempt(record_path):
    with open(record_path, encoding="utf-8") as fh:
        record = json.load(fh)
    required = {"id", "hypothesis", "changeFingerprint", "evaluatorVersion",
                "evidenceIds", "metrics", "verdict"}
    missing = sorted(required - set(record))
    if missing:
        raise ValueError("attempt record missing: " + ", ".join(missing))
    rows = load_attempts()
    for index, row in enumerate(rows):
        if row.get("id") == record["id"]:
            rows[index] = record
            break
    else:
        rows.append(record)
    temporary = ATTEMPTS + ".tmp"
    with open(temporary, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(temporary, ATTEMPTS)
    return record


def keep_set(rows):
    existing = _existing(rows)
    latest = max((int(row["submission"]) for row in existing if row.get("submission")), default=None)
    losses = sorted((row for row in existing if row["result"] == "LOSS"), key=lambda row: row["delta"])
    top = sorted(existing, key=lambda row: -row["them"])
    newest = sorted(existing, key=lambda row: -int(row["episode"]) if row["episode"].isdigit() else 0)
    ordered = select(existing, str(latest) if latest else None) + top[:6] + losses[:6] + newest[:4]
    keep, seen, used, budget = set(), set(), 0, MAX_RAW_MB * 1_000_000
    for row in ordered:
        path = row["file"]
        if path in seen:
            continue
        seen.add(path)
        size = os.path.getsize(path)
        if keep and used + size > budget:
            break
        keep.add(path)
        used += size
    return keep


def prune(dry_run=False):
    keep, freed = keep_set(load_index()), 0
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
    held = sum(os.path.getsize(path) for path in keep if os.path.exists(path))
    return freed, len(keep), held


def _summary(rows):
    record = _record(rows)
    if not rows:
        return "0 indexed"
    best = max(rows, key=lambda row: row["them"])
    return (f"{record['games']} indexed, {record['wins']}W-{record['losses']}L, "
            f"our best {record['ourBest']:.0f}, field best {best['them']:.0f} ({best['opponent']})")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "index"
    if command == "index":
        print(_summary(build_index()))
    elif command == "select":
        print(json.dumps(select(submission=sys.argv[2] if len(sys.argv) > 2 else None),
                         indent=1, ensure_ascii=False))
    elif command == "evidence":
        if len(sys.argv) < 4:
            raise SystemExit("evidence requires SUBMISSION_ID OUTPUT [NEW_IDS]")
        new_ids = tuple(filter(None, sys.argv[4].split(","))) if len(sys.argv) > 4 else ()
        packet = build_evidence(sys.argv[2], sys.argv[3], new_ids)
        print(f"{len(packet['replays'])} replay summaries -> {sys.argv[3]}")
    elif command == "prune":
        freed, kept, held = prune("--dry-run" in sys.argv)
        print(f"kept {kept} replays ({held / 1e6:.0f} of {MAX_RAW_MB} MB), freed {freed / 1e6:.0f} MB")
    elif command == "migrate-attempts":
        print(f"{len(migrate_attempts())} attempts -> {ATTEMPTS}")
    elif command == "attempt-upsert":
        upsert_attempt(sys.argv[2])
        print(sys.argv[2])
    elif command == "attempts":
        print(f"{len(load_attempts())} authoritative attempts in {ATTEMPTS}")
    else:
        raise SystemExit(__doc__)
