import importlib.util, sys, collections
from kaggle_environments import make
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m; spec.loader.exec_module(m); return m
A=load("main.py","pa"); B=load("main.py","pb")
byday=collections.Counter(); byhour=collections.Counter(); units_by_day={}
standing=collections.Counter(); passjobs=[]
cur={"day":0,"hour":0}
origagent=A.agent
def agent(obs):
    cur["day"]=obs["day"]; cur["hour"]=obs["hour"]
    return origagent(obs)
A.agent=agent
orig=A._assign
def assign(units,jobs,tiles,invs):
    acts=orig(units,jobs,tiles,invs)
    d,h=cur["day"],cur["hour"]
    np_=sum(1 for a in acts if a[0]=="PASS")
    byday[d]+=np_; byhour[h]+=np_
    units_by_day[d]=len(units)
    if np_:
        # how many jobs were left unassigned & item-free
        standing[d]+=sum(1 for j in jobs if j[4] is None)
        passjobs.append((d,h,np_,len(units),len(jobs)))
    return acts
A._assign=assign
env=make("kaggriculture",configuration={"seed":0,"townCenterSellInterval":24})
env.run([A.agent,B.agent])
print("PASS by day (units, pass, pass/unitturn):")
for d in range(30):
    u=units_by_day.get(d,0)
    print("  day %2d units %2d PASS %4d  %.0f%%"%(d,u,byday[d],100*byday[d]/max(1,u*24)))
print("total PASS",sum(byday.values()))
print("\nPASS by hour:",[byhour[h] for h in range(24)])
print("\nsample turns with PASS (day,hour,npass,nunits,njobs):")
for r in passjobs[:5]+passjobs[len(passjobs)//2:len(passjobs)//2+5]+passjobs[-5:]: print("  ",r)
