import importlib.util, sys, collections
import kaggle_environments.envs.kaggriculture.kaggriculture as K
from kaggle_environments import make
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m; spec.loader.exec_module(m); return m
P=sys.argv[1]; seed=int(sys.argv[2]); tci=int(sys.argv[3])
A=load(P,"ea"); B=load(P,"eb")
disc=collections.Counter()
orig=K._drop_inventories_to_shed
def patched(private, capacity):
    rem=max(0,capacity-sum(private["shed"].values()))
    for inv in private["inventories"]:
        for it,n in list(inv.items()):
            if n<=0: continue
            take=min(n,rem); rem-=take
            if n-take>0: disc[it]+=n-take
    return orig(private,capacity)
K._drop_inventories_to_shed=patched
env=make("kaggriculture",configuration={"seed":seed,"townCenterSellInterval":tci})
env.run([A.agent,B.agent])
last=env.steps[-1]
pr=last[0]['observation']['market']['prices']
print(P,"seed",seed,"tci",tci,"rewards",last[0].reward,last[1].reward)
print("  discards(both):",dict(disc),"total",sum(disc.values()))
for pl in (0,1):
    priv=last[pl]['observation']['private']
    carried=collections.Counter()
    for inv in priv.get('inventories',[]):
        for it,n in inv.items():
            if n>0: carried[it]+=n
    shed=priv.get('shed',{})
    v=sum(n*pr.get(it,0) for it,n in carried.items())
    print("  farm%d unsold-in-packs %s ($%d)  shed-left %s"%(pl,dict(carried),v,{k:v2 for k,v2 in shed.items() if v2}))
