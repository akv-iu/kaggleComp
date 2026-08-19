import importlib.util, sys, os, collections
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as K
seed=int(sys.argv[1]); interval=int(sys.argv[2])
lost=collections.Counter(); died=collections.Counter()
_o=K._decay_plants
def dec(farm, step):
    b=len(farm["tiles"])
    for y in range(b):
        for x in range(b):
            t=farm["tiles"][y][x]
            if not isinstance(t,dict) or t.get("kind")!="PLANT": continue
            mls=t["max_lifespan_step"]
            if mls<0 or step<mls or (step-mls)%2!=0: continue
            lost[t["crop"]]+=1
            if t["yield_units"]-1<=0: died[t["crop"]]+=1
    return _o(farm,step)
K._decay_plants=dec
# also count weed deaths from thirst
thirst=collections.Counter()
_r=K._daily_refresh_plants
def ref(farm,d,tpd):
    b=len(farm["tiles"])
    for y in range(b):
        for x in range(b):
            t=farm["tiles"][y][x]
            if isinstance(t,dict) and t.get("kind")=="PLANT" and not t["watered_today"] and t["consecutive_unwatered"]+1>=2:
                thirst[t["crop"]]+=1
    return _r(farm,d,tpd)
K._daily_refresh_plants=ref
def load(n):
    s=importlib.util.spec_from_file_location(n,os.path.join(ROOT,"main.py"))
    m=importlib.util.module_from_spec(s); sys.modules[n]=m; s.loader.exec_module(m); return m
env=make("kaggriculture",configuration={"seed":seed,"townCenterSellInterval":interval})
env.run([load("ma").agent,load("mb").agent])
print("score",[s.reward for s in env.steps[-1]])
print("units lost to decay (both farms):",dict(lost),"tiles killed by decay:",dict(died))
print("tiles killed by thirst:",dict(thirst))
