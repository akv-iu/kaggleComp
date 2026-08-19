"""Mirror screen: candidate vs baseline, both intervals, same process."""
import importlib.util, sys, statistics as st
from kaggle_environments import make
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m; spec.loader.exec_module(m); return m
def mirror(path,tag,seeds,tci):
    a=load(path,tag+"_a").agent; b=load(path,tag+"_b").agent
    sc=[]
    for s in seeds:
        env=make("kaggriculture",configuration={"seed":s,"townCenterSellInterval":tci})
        env.run([a,b]); sc += [env.steps[-1][0].reward, env.steps[-1][1].reward]
    return sc
cand=sys.argv[1]; base=sys.argv[2]
seeds=[int(x) for x in sys.argv[3].split(",")]
for tci in (24,12):
    c=mirror(cand,"c%d"%tci,seeds,tci); b=mirror(base,"b%d"%tci,seeds,tci)
    print("tci %2d  cand %9.1f  base %9.1f  delta %+9.1f   (per-seed delta: %s)"%(
        tci, st.mean(c), st.mean(b), st.mean(c)-st.mean(b),
        " ".join("%+.0f"%((c[2*i]+c[2*i+1])/2-(b[2*i]+b[2*i+1])/2) for i in range(len(seeds)))))
