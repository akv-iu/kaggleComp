import json,glob,os
for p in sorted(glob.glob('replays/*/episode-*-replay.json')):
    d=json.load(open(p))
    print(os.path.basename(p), "module_version",d.get('module_version'),"version",d.get('version'),"schema",d.get('schema_version'))
    steps=d['steps']
    prev=[]
    for i in range(0,len(steps)):
        sh=steps[i][0]['observation'].get('town',{}).get('unlocked_shops')
        if sh is None: continue
        if sh!=prev:
            print("   step %4d day %2d -> %s"%(i,steps[i][0]['observation']['day'],sh))
            prev=list(sh)
    break
