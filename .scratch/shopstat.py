"""Local env draws shops without replacement; the competition draws with."""
import importlib.util, sys, collections
from kaggle_environments import make
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m; spec.loader.exec_module(m); return m
A=load("main.py","qa"); B=load("main.py","qb")
import kaggle_environments.envs.kaggriculture.kaggriculture as K
import inspect
src=inspect.getsource(K._end_of_day)
print("local _end_of_day shop draw:")
for line in src.splitlines():
    if "remaining" in line or "choice" in line: print("   ",line.strip())
