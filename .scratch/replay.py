"""Per-day tile census, money and action histogram for one player in a replay."""
import json
import sys
from collections import Counter


def census(farm):
    c = Counter()
    for row in farm["tiles"]:
        for t in row:
            if t is None:
                c["EMPTY"] += 1
            elif t == "LOCKED":
                c["LOCK"] += 1
            elif isinstance(t, dict):
                c[t.get("crop") or t.get("animal") or t.get("kind")] += 1
    return c


def main(path, p):
    d = json.load(open(path))
    steps = d["steps"]
    seen = {}
    verbs = Counter()
    orders = Counter()
    order_qty = Counter()
    for i, st in enumerate(steps):
        obs = st[0]["observation"]
        farms = obs.get("farms")
        if not farms:
            continue
        day = obs.get("day", 0)
        if day not in seen:
            c = census(farms[p])
            c["money"] = int(farms[p]["money"])
            c["hands"] = len(farms[p]["hands"])
            c["quads"] = len(farms[p]["unlocked_quadrants"])
            seen[day] = c
        if i + 1 < len(steps):
            act = steps[i + 1][p].get("action")
            if isinstance(act, dict):
                for a in [act.get("farmer")] + list(act.get("hands") or []):
                    if isinstance(a, list) and a:
                        verbs[a[0]] += 1
                for o in (act.get("market") or []):
                    if isinstance(o, list) and o:
                        k = o[0] + ":" + (str(o[1]) if len(o) > 1 else "")
                        orders[k] += 1
                        if len(o) > 2:
                            try:
                                order_qty[k] += int(o[2])
                            except (TypeError, ValueError):
                                pass
    print("final money", steps[-1][p]["reward"])
    print("verbs", json.dumps(verbs.most_common()))
    print("orders", json.dumps(orders.most_common()))
    print("order_qty", json.dumps(order_qty.most_common()))
    for day in sorted(seen):
        c = seen[day]
        print("day %2d $%-7d h%-3d q%d %s" % (
            day, c["money"], c["hands"], c["quads"],
            " ".join("%s=%d" % (k, v) for k, v in sorted(c.items())
                     if k not in ("money", "hands", "quads", "LOCK"))))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
