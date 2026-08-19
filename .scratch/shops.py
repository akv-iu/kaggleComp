import json,glob,os
for p in sorted(glob.glob('replays/*/episode-*-replay.json')):
    try:
        d=json.load(open(p))
    except Exception as e:
        print(p,"ERR",e); continue
    steps=d['steps']; cfg=d['configuration']
    o=steps[-1][0]['observation']
    r=d['rewards']
    # shop unlock day
    seen={}
    for i in range(0,len(steps),24):
        sh=steps[i][0]['observation'].get('town',{}).get('unlocked_shops',[])
        day=steps[i][0]['observation']['day']
        for s in sh:
            seen.setdefault(s,day)
    pr=o['market']['prices']; inv=o['market']['inventory']
    print("%s tci=%s rewards=%s"%(os.path.basename(p),cfg.get('townCenterSellInterval'),r))
    print("   shops:", steps[-1][0]['observation']['town']['unlocked_shops'])
    print("   first-seen:", sorted(seen.items(), key=lambda kv: kv[1]))
    print("   end price STRAW %s MILK %s WOOL %s MELON %s EGG %s WHEAT %s FERT %s"%(pr['STRAWBERRY'],pr['MILK'],pr['WOOL'],pr['MELON'],pr['EGG'],pr['WHEAT'],pr['FERTILIZER']))
    print("   end inv-I0 STRAW %d MILK %d WOOL %d MELON %d EGG %d"%(inv['STRAWBERRY']-10000,inv['MILK']-10000,inv['WOOL']-10000,inv['MELON']-10000,inv['EGG']-10000))
