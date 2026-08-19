import importlib.util, sys, os, collections
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from kaggle_environments import make
seed=int(sys.argv[1]); interval=int(sys.argv[2])
def load(n):
    s=importlib.util.spec_from_file_location(n,os.path.join(ROOT,"main.py"))
    m=importlib.util.module_from_spec(s); sys.modules[n]=m; s.loader.exec_module(m); return m
ma,mb=load("ma"),load("mb")
rows=[]
def wrap(mod,pid):
    def a(obs):
        out=mod.agent(obs)
        if pid==0 and 9<=obs["day"]<=14 and obs["hour"] in (0,6,12,18,23):
            me=obs["farms"][obs["player"]]; priv=obs["private"]
            n_p=n_a=n_s=n_e=0; crops=collections.Counter()
            for row in me["tiles"]:
                for t in row:
                    if t is None: n_e+=1
                    elif not isinstance(t,dict): continue
                    elif t.get("kind")=="PLANT": n_p+=1; crops[t["crop"]]+=1
                    elif "animal" in t: n_a+=1
                    elif t.get("kind") in ("COOP","PASTURE"): n_s+=1
            crew=1+max(len(me["hands"]),me["hires_today"])
            slots=max(0,crew*mod.SLOTS_PER_UNIT-n_p*mod.PLANT_SLOTS-n_a*mod.ANIMAL_SLOTS)
            px=obs["market"]["prices"]
            keep=max(1,px.get("WHEAT",25))*(mod.FEED_DAYS_EARLY if obs["day"]<=mod.HERD_RUSH_DAY else mod.FEED_DAYS)
            budget=me["money"]-mod.CASH_FLOOR-n_a*keep
            rows.append((obs["day"],obs["hour"],round(me["money"]),round(budget),slots,
                         priv["seeds"].get("STRAWBERRY",0),crops["STRAWBERRY"],n_e,n_a,n_s,crew,
                         [o for o in out["market"] if o[0] in("BUY_SEED","BUY_ANIMAL","BUY_LAND")]))
        return out
    return a
env=make("kaggriculture",configuration={"seed":seed,"townCenterSellInterval":interval})
env.run([wrap(ma,0),wrap(mb,1)])
print("score",env.steps[-1][0].reward)
print("day hr  money  budget slots seed berry empty anim str crew orders")
for r in rows: print("d%02d h%02d %7d %7d %5d %4d %5d %5d %4d %3d %4d %s"%r)
