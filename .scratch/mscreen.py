"""Screen several candidate files against one baseline, both intervals, one pass.
argv: <base.py> <lo> <hi> <intervals csv> <cand1.py> [cand2.py ...]"""
import importlib.util, sys, statistics as st
from concurrent.futures import ProcessPoolExecutor

def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m.agent

def _one(args):
    path, seed, tci = args
    from kaggle_environments import make
    a = _load(path, "a%d%d" % (seed, tci)); b = _load(path, "b%d%d" % (seed, tci))
    env = make("kaggriculture", configuration={"seed": seed, "townCenterSellInterval": tci})
    env.run([a, b])
    return (r for r in ())._ if False else (env.steps[-1][0].reward + env.steps[-1][1].reward) / 2

if __name__ == "__main__":
    base = sys.argv[1]; lo, hi = int(sys.argv[2]), int(sys.argv[3])
    tcis = [int(x) for x in sys.argv[4].split(",")]
    cands = sys.argv[5:]
    paths = [base] + cands
    jobs = [(p, s, t) for t in tcis for p in paths for s in range(lo, hi)]
    with ProcessPoolExecutor(max_workers=11) as ex:
        res = list(ex.map(_one, jobs))
    tab = {}
    for (p, s, t), v in zip(jobs, res):
        tab[(p, s, t)] = v
    for t in tcis:
        bm = [tab[(base, s, t)] for s in range(lo, hi)]
        print("tci %2d  BASE %9.1f  %s" % (t, st.mean(bm), " ".join("%.0f" % v for v in bm)), flush=True)
        for c in cands:
            cm = [tab[(c, s, t)] for s in range(lo, hi)]
            print("        %-22s %9.1f  delta %+8.1f   per-seed %s" % (
                c.split("/")[-1], st.mean(cm), st.mean(cm) - st.mean(bm),
                " ".join("%+.0f" % (a - b) for a, b in zip(cm, bm))), flush=True)
