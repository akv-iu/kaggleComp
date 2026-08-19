import importlib.util, sys, collections
from kaggle_environments import make
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m; spec.loader.exec_module(m); return m
A=load("main.py","ca"); B=load("main.py","cb")
seen={}
orig=A.agent
def agent(obs):
    d,h=obs["day"],obs["hour"]
    if h==0:
        me=obs["farms"][obs["player"]]
        c=collections.Counter(); bare=0
        for row in me["tiles"]:
            for t in row:
                if t=="LOCKED": continue
                if t is None: bare+=1
                elif t.get("kind")=="PLANT": c[t["crop"]]+=1
                elif "animal" in t: c[t["animal"]]+=1
                else: c[t.get("kind")]+=1
        seen[d]=(me["money"],bare,dict(c),dict(obs["private"].get("seeds",{})),sum(obs["private"].get("shed",{}).values()))
    return orig(obs)
A.agent=agent
env=make("kaggriculture",configuration={"seed":int(sys.argv[1]),"townCenterSellInterval":24})
env.run([A.agent,B.agent])
print("rewards",env.steps[-1][0].reward,env.steps[-1][1].reward)
for d in range(30):
    if d in seen:
        m,bare,c,s,sh=seen[d]
        print("day %2d $%7.0f bare %2d shed %3d %s seeds=%s"%(d,m,bare,sh,c,s))
