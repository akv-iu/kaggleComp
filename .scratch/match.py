"""How far is the greedy closest-pair matching from optimal, per band?"""
import importlib.util, sys, collections
import numpy as np
from scipy.optimize import linear_sum_assignment
from kaggle_environments import make
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m; spec.loader.exec_module(m); return m
A=load("main.py","ma"); B=load("main.py","mb")
tot=collections.Counter()
def instrument(mod):
    orig=mod._assign
    def assign(units, jobs, tiles, invs):
        js=sorted(jobs,key=lambda j:j[0])
        idle=set(range(len(units)))
        # replicate pass 1
        at={}
        for j in js: at.setdefault((j[1],j[2]),[]).append(j)
        done=set()
        def _can(i,need): return need is None or (i<len(invs) and invs[i].get(need,0)>0)
        for i in range(len(units)):
            for j in at.get(tuple(units[i]),()):
                if id(j) not in done and _can(i,j[4]):
                    done.add(id(j)); idle.discard(i); break
        lo=0
        while lo<len(js) and idle:
            hi=lo
            while hi<len(js) and js[hi][0]==js[lo][0]: hi+=1
            band=[j for j in js[lo:hi] if id(j) not in done]; lo=hi
            if not band or not idle: continue
            ids=sorted(idle)
            BIG=10**6
            C=np.array([[ (abs(units[i][0]-j[1])+abs(units[i][1]-j[2])) if _can(i,j[4]) else BIG
                          for j in band] for i in ids],dtype=float)
            # greedy
            g=0.0; av=set(range(len(ids))); bv=set(range(len(band))); npair=0
            while av and bv:
                best=None
                for bi in sorted(bv):
                    for ai in sorted(av):
                        if C[ai,bi]>=BIG: continue
                        if best is None or C[ai,bi]<best[0]: best=(C[ai,bi],ai,bi)
                if best is None: break
                g+=best[0]; av.discard(best[1]); bv.discard(best[2]); npair+=1
            r,c=linear_sum_assignment(C)
            o=sum(C[i,j] for i,j in zip(r,c) if C[i,j]<BIG)
            nopt=sum(1 for i,j in zip(r,c) if C[i,j]<BIG)
            if npair:
                tot["greedy"]+=g; tot["opt"]+=min(o,g); tot["pairs"]+=npair; tot["bands"]+=1
                tot["optpairs"]+=nopt
            # simulate: units matched greedily become busy
            idle -= set(ids[i] for i in range(len(ids)) if i not in av)
        return orig(units,jobs,tiles,invs)
    mod._assign=assign
instrument(A)
env=make("kaggriculture",configuration={"seed":0,"townCenterSellInterval":24})
env.run([A.agent,B.agent])
print(dict(tot))
print("greedy total dist %.0f  optimal(lb) %.0f  saving %.1f%%"%(tot["greedy"],tot["opt"],100*(tot["greedy"]-tot["opt"])/tot["greedy"]))
