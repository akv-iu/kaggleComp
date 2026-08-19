import importlib.util, sys, collections, json
from kaggle_environments import make
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m; spec.loader.exec_module(m); return m
A=load("main.py","ia"); B=load("main.py","ib")
stats=collections.Counter()
dropinv=collections.Counter()
passday=collections.Counter()
jobs_offered=collections.Counter(); jobs_served=collections.Counter()
def wrap(mod, tag, active):
    orig_assign=mod._assign
    def assign(units, jobs, tiles, invs):
        if active:
            for j in jobs: jobs_offered[j[3][0]]+=1
        acts=orig_assign(units,jobs,tiles,invs)
        if active:
            for i,a in enumerate(acts):
                v=a[0]
                if v in ("NORTH","SOUTH","EAST","WEST"): stats["MOVE"]+=1
                elif v=="PASS": stats["PASS"]+=1
                else:
                    stats[v]+=1; jobs_served[v]+=1
                if v=="DROP" and i<len(invs):
                    for it,n in invs[i].items():
                        if n>0: dropinv[it]+=n
        return acts
    mod._assign=assign
wrap(A,"a",True); wrap(B,"b",False)
seed=int(sys.argv[1]) if len(sys.argv)>1 else 0
tci=int(sys.argv[2]) if len(sys.argv)>2 else 24
env=make("kaggriculture",configuration={"seed":seed,"townCenterSellInterval":tci})
env.run([A.agent,B.agent])
print("seed",seed,"tci",tci,"rewards",env.steps[-1][0].reward,env.steps[-1][1].reward)
tot=sum(stats.values())
print("unit-turns",tot)
for k,v in stats.most_common(): print("   %-20s %5d  %5.1f%%"%(k,v,100*v/tot))
print("items in inventory at DROP:", dict(dropinv))
print("\noffered vs served:")
for k in sorted(jobs_offered, key=lambda k:-jobs_offered[k]):
    print("   %-20s offered %6d served %5d"%(k,jobs_offered[k],jobs_served.get(k,0)))
