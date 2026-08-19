"""Melon at the competition vs at the benchmark: depth above I0 at the last bell."""
import json,glob,os
print("%-12s %-10s %8s %8s"%("episode","who","melon-I0","price"))
for p in sorted(glob.glob('replays/*/episode-*-replay.json')):
    d=json.load(open(p)); o=d['steps'][-1][0]['observation']
    print("%-12s %-10s %8d %8d"%(os.path.basename(p)[8:16],"real",o['market']['inventory']['MELON']-10000,o['market']['prices']['MELON']))
