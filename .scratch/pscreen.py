"""Parallel mirror screen: candidate vs baseline at both intervals.

argv: <cand.py> <base.py> <lo> <hi> [intervals csv]
Prints one line per interval. Uses a process pool (games are independent).
"""
import importlib.util, json, os, sys, statistics as st
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
    return (seed, tci, env.steps[-1][0].reward, env.steps[-1][1].reward)

if __name__ == "__main__":
    cand, base = sys.argv[1], sys.argv[2]
    lo, hi = int(sys.argv[3]), int(sys.argv[4])
    tcis = [int(x) for x in (sys.argv[5] if len(sys.argv) > 5 else "24,12").split(",")]
    jobs = [(p, s, t) for t in tcis for s in range(lo, hi) for p in (cand, base)]
    with ProcessPoolExecutor(max_workers=11) as ex:
        res = list(ex.map(_one, jobs))
    for t in tcis:
        for tag, p in (("cand", cand), ("base", base)):
            pass
        c = {}; b = {}
        for (path, seed, tci) , r in zip(jobs, res):
            pass
        cs = {}; bs = {}
        for j, r in zip(jobs, res):
            (path, seed, tci) = j
            if tci != t: continue
            (cs if path == cand else bs)[seed] = (r[2] + r[3]) / 2
        seeds = sorted(cs)
        cm = st.mean(cs[s] for s in seeds); bm = st.mean(bs[s] for s in seeds)
        print("tci %2d  cand %9.1f  base %9.1f  delta %+9.1f   per-seed %s" % (
            t, cm, bm, cm - bm, " ".join("%+.0f" % (cs[s] - bs[s]) for s in seeds)), flush=True)
