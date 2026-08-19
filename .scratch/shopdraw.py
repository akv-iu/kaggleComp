import json,glob,os,collections
tot=collections.Counter(); dist=[]
for p in sorted(glob.glob('replays/*/episode-*-replay.json')):
    d=json.load(open(p)); steps=d['steps']
    sh=steps[-1][0]['observation']['town']['unlocked_shops']
    c=collections.Counter(sh)
    dist.append((os.path.basename(p)[8:16], len(sh), len(c), sorted(c.items(),key=lambda kv:-kv[1])))
for e in dist:
    print("%s draws=%d distinct=%d %s"%e)
print()
print("YARN_STORE present in", sum(1 for e in dist if any(k=='YARN_STORE' for k,_ in e[3])), "of", len(dist))
print("mean distinct %.2f (theory 8*(1-(7/8)^8)=%.2f)"%(sum(e[2] for e in dist)/len(dist), 8*(1-(7/8)**8)))
