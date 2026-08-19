"""Run several screen cells and print one JSON line each. argv: cells.json"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import screen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    cells = json.load(open(sys.argv[1]))
    out = []
    for c in cells:
        path = c.get("path") or os.path.join(ROOT, "main.py")
        m, res = screen.mirror(path, c.get("over") or {},
                               range(c["lo"], c["hi"]), c["interval"])
        row = {"label": c["label"], "interval": c["interval"],
               "seeds": [c["lo"], c["hi"]], "mean": round(m, 1),
               "per_seed": [round((a + b) / 2) for a, b in res]}
        out.append(row)
        print("CELL " + json.dumps(row), flush=True)
    json.dump(out, open(sys.argv[1] + ".out", "w"), indent=1)
