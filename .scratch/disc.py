import importlib.util, sys, collections
import kaggle_environments.envs.kaggriculture.kaggriculture as K
from kaggle_environments import make
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m; spec.loader.exec_module(m); return m
P=sys.argv[1]
A=load(P,"da"); B=load(P,"db")
disc=collections.Counter()
orig=K._drop_inventories_to_shed
def patched(private, capacity):
    shed=private["shed"]; room=max(0,capacity-sum(shed.values())); rem=room
    for inv in private["inventories"]:
        for it,n in list(inv.items()):
            if n<=0: continue
            take=min(n,rem); rem-=take
            if n-take>0: disc[it]+=n-take
    return orig(private,capacity)
K._drop_inventories_to_shed=patched
acts=collections.Counter()
o=A._assign
def assign(*a,**k):
    r=o(*a,**k)
    for x in r: acts[x[0] if x[0] in ("PASS","DROP","NORTH","SOUTH","EAST","WEST") else "OTHER"]+=1
    return r
A._assign=assign
env=make("kaggriculture",configuration={"seed":int(sys.argv[2]),"townCenterSellInterval":int(sys.argv[3])})
env.run([A.agent,B.agent])
print(P,"seed",sys.argv[2],"tci",sys.argv[3],"rewards",env.steps[-1][0].reward,env.steps[-1][1].reward)
print("discarded both farms:",dict(disc),"total",sum(disc.values()))
print("acts(one farm):",dict(acts))
