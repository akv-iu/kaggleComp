import json,sys,collections
p=sys.argv[1]
d=json.load(open(p))
print("keys",list(d.keys()))
cfg=d.get('configuration',{})
print("cfg",{k:v for k,v in cfg.items() if k in ('townCenterSellInterval','townShopSellInterval','townShopUnlockInterval','turnsPerDay','shedCapacity','startingMoney','episodeSteps','boardSize')})
steps=d['steps']
print("steps",len(steps))
last=steps[-1]
for i,s in enumerate(last):
    o=s['observation']
    print(i,"reward",s.get('reward'),"status",s.get('status'))
o=last[0]['observation']
print("day",o['day'],"hour",o['hour'])
print("shops",o['town']['unlocked_shops'])
print("money",[f['money'] for f in o['farms']])
print("prices",o['market']['prices'])
print("inv",o['market']['inventory'])
