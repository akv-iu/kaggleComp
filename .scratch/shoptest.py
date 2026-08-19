import importlib.util, sys
from kaggle_environments import make
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m; spec.loader.exec_module(m); return m.agent
a=load("main.py","a"); b=load("main.py","b")
for tci in (12,24):
    env = make("kaggriculture", configuration={"seed": 0, "townCenterSellInterval": tci})
    env.run([a,b])
    o=env.steps[-1][0]['observation']
    print("tci",tci,"shops:", o['town']['unlocked_shops'])
    print("  prices:", o['market']['prices'])
    print("  inv-I0:", {k:v-10000 for k,v in o['market']['inventory'].items()})
    print("  rewards:", env.steps[-1][0].reward, env.steps[-1][1].reward)
