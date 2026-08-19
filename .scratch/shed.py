import importlib.util, sys, collections
import kaggle_environments.envs.kaggriculture.kaggriculture as K
from kaggle_environments import make
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m; spec.loader.exec_module(m); return m
A=load("main.py","sa"); B=load("main.py","sb")
disc=collections.Counter(); day={"d":0}
orig_drop=K._drop_inventories_to_shed
def patched(private, capacity):
    before=sum(private["shed"].values())
    carried=collections.Counter()
    for inv in private["inventories"]:
        for it,n in inv.items():
            if n>0: carried[it]+=n
    orig_drop(private,capacity)
    after=sum(private["shed"].values())
    lost=sum(carried.values())-(after-before)
    if lost>0:
        disc["TOTAL"]+=lost; disc["day%d"%day["d"]]+=lost
    return
K._drop_inventories_to_shed=patched
orig_eod=K._end_of_day
def eod(state,env,d):
    day["d"]=d; return orig_eod(state,env,d)
K._end_of_day=eod
comp={}
origagent=A.agent
def agent(obs):
    if obs["hour"]==0: comp[obs["day"]]=dict(obs["private"].get("shed",{}))
    return origagent(obs)
A.agent=agent
tci=int(sys.argv[2]) if len(sys.argv)>2 else 24
env=make("kaggriculture",configuration={"seed":int(sys.argv[1]),"townCenterSellInterval":tci})
env.run([A.agent,B.agent])
print("rewards",env.steps[-1][0].reward,env.steps[-1][1].reward,"tci",tci)
for d in sorted(comp):
    s=comp[d]
    if sum(s.values())>0:
        print("day %2d tot %3d  %s"%(d,sum(s.values()),{k:v for k,v in sorted(s.items(),key=lambda kv:-kv[1]) if v}))
print("\nDISCARDED at nightfall (both farms):",dict(disc))
