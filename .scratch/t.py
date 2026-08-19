import time, sys, importlib.util
from kaggle_environments import make
def load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s)
    sys.modules[n]=m; s.loader.exec_module(m); return m.agent
a=load("main.py","a"); b=load("main.py","b")
t=time.time()
env=make("kaggriculture", configuration={"seed":0})
env.run([a,b])
print("interval12", [s.reward for s in env.steps[-1]], "%.1fs"%(time.time()-t))
t=time.time()
env=make("kaggriculture", configuration={"seed":0,"townCenterSellInterval":24})
env.run([a,b])
print("interval24", [s.reward for s in env.steps[-1]], "%.1fs"%(time.time()-t))
