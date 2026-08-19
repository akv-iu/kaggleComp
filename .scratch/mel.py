import json,glob,os
files=sorted(glob.glob('replays/*/episode-*-replay.json'))
for p in files:
    d=json.load(open(p)); steps=d['steps']; r=d['rewards']
    print("\n==",os.path.basename(p),r)
    hdr="day: "+" ".join("%3d"%dd for dd in range(0,30,2))
    rows={}
    for item in ('MELON','STRAWBERRY','MILK','WOOL','FERTILIZER','WHEAT'):
        rows[item]=[]
    sheds=[[],[]]
    for dd in range(0,30,2):
        i=min(dd*24, len(steps)-1)
        o=steps[i][0]['observation']
        for item in rows: rows[item].append(o['market']['prices'][item])
        for pl in (0,1):
            sh=steps[i][pl]['observation'].get('private',{}).get('shed',{})
            sheds[pl].append(sh.get('MELON',0))
    print(hdr)
    for item,v in rows.items():
        print("%-11s"%item," ".join("%3d"%x for x in v))
    print("melonShed0  "," ".join("%3d"%x for x in sheds[0]))
    print("melonShed1  "," ".join("%3d"%x for x in sheds[1]))
