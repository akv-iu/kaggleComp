import importlib.util, sys, collections
import kaggle_environments.envs.kaggriculture.kaggriculture as K
from kaggle_environments import make
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m; spec.loader.exec_module(m); return m
A=load("main.py","s2a"); B=load("main.py","s2b")
disc=collections.Counter(); perday=collections.Counter(); day={"d":0}; nfarm={"i":0}
predump=[]
orig_drop=K._drop_inventories_to_shed
def patched(private, capacity):
    shed=private["shed"]; before=sum(shed.values())
    carried=collections.Counter()
    for inv in private["inventories"]:
        for it,n in inv.items():
            if n>0: carried[it]+=n
    room=max(0,capacity-before)
    predump.append((day["d"],nfarm["i"],before,sum(carried.values())))
    # replicate the greedy order to attribute losses
    rem=room
    for inv in private["inventories"]:
        for it,n in list(inv.items()):
            if n<=0: continue
            take=min(n,rem); rem-=take
            if n-take>0: disc[it]+=n-take; perday[day["d"]]+=n-take
    nfarm["i"]^=1
    return orig_drop(private,capacity)
K._drop_inventories_to_shed=patched
orig_eod=K._end_of_day
def eod(state,env,d):
    day["d"]=d; return orig_eod(state,env,d)
K._end_of_day=eod
tci=int(sys.argv[2]); seed=int(sys.argv[1])
env=make("kaggriculture",configuration={"seed":seed,"townCenterSellInterval":tci})
env.run([A.agent,B.agent])
prices=env.steps[-1][0]['observation']['market']['prices']
print("seed",seed,"tci",tci,"rewards",env.steps[-1][0].reward,env.steps[-1][1].reward)
print("discarded per item (BOTH farms):",dict(disc.most_common()))
val=sum(n*prices.get(it,0) for it,n in disc.items())
print("total units",sum(disc.values()),"~end-price value $%d (both farms)"%val)
print("by day:",dict(sorted(perday.items())))
print("\nshed-at-dusk / carried, days 16+:")
for d,f,b,c in predump:
    if d>=16 and f==0: print("  day %2d shed %3d carried %3d overflow %3d"%(d,b,c,max(0,b+c-100)))
