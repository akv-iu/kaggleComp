"""What the opponent's visible farm looks like at day 12 in real replays vs the mirror."""
import json,glob,os,collections
for p in sorted(glob.glob('replays/*/episode-*-replay.json')):
    d=json.load(open(p)); steps=d['steps']
    r=d['rewards']
    # we are the seat matching replay_index; just report both farms at day 12 and 20
    for day in (12,):
        o=steps[day*24][0]['observation']
        line=[]
        for f in o['farms']:
            c=collections.Counter()
            for row in f['tiles']:
                for t in row:
                    if isinstance(t,dict):
                        c[t.get('crop') or t.get('animal') or t.get('kind')]+=1
            line.append("%s $%d %s"%(len(f['unlocked_quadrants']),f['money'],dict(c.most_common(5))))
        print("%s d%d rewards=%s\n    A: %s\n    B: %s"%(os.path.basename(p)[8:16],day,r,line[0],line[1]))
