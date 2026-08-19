import json, collections, statistics as st
rows=[r for r in json.load(open('replay_index.json')) if 'submission-55507562' in r['file']]
rows.sort(key=lambda r:r['delta'])
print("n",len(rows))
import math
me=[r['me'] for r in rows]; th=[r['them'] for r in rows]
mm,mt=st.mean(me),st.mean(th)
cov=sum((a-mm)*(b-mt) for a,b in zip(me,th))/len(me)
print("corr %.3f"%(cov/(st.pstdev(me)*st.pstdev(th))))
# seat effect
for s in (0,1):
    v=[r for r in rows if r['seat']==s]
    print("seat",s,"n",len(v),"W",sum(1 for r in v if r['result']=='WIN'),"mean me %.0f them %.0f"%(st.mean([r['me'] for r in v]),st.mean([r['them'] for r in v])))
# margin buckets
for lo,hi in [(-10**9,-50000),(-50000,-20000),(-20000,-5000),(-5000,0),(0,5000),(5000,20000),(20000,10**9)]:
    v=[r for r in rows if lo<=r['delta']<hi]
    print("delta [%8d,%8d) n=%2d  our mean %7.0f their mean %7.0f"%(lo if lo>-10**8 else -99999,hi if hi<10**8 else 99999,len(v),st.mean([r['me'] for r in v]) if v else 0,st.mean([r['them'] for r in v]) if v else 0))
print()
print("close losses (within 8000):")
for r in rows:
    if -8000<r['delta']<0: print("  me %7.0f them %7.0f %s"%(r['me'],r['them'],r['opponent']))
print()
print("their score distribution: min %.0f p25 %.0f med %.0f p75 %.0f max %.0f"%(min(th),sorted(th)[len(th)//4],st.median(th),sorted(th)[3*len(th)//4],max(th)))
print("our   score distribution: min %.0f p25 %.0f med %.0f p75 %.0f max %.0f"%(min(me),sorted(me)[len(me)//4],st.median(me),sorted(me)[3*len(me)//4],max(me)))
# how many opponents beat our best
opp=collections.defaultdict(list)
for r in rows: opp[r['opponent']].append(r)
print("\nopponents with >=2 games, by their mean:")
for k,v in sorted(opp.items(), key=lambda kv:-st.mean([r['them'] for r in kv[1]])):
    if len(v)>=2: print("  %-24s n=%d theirs %7.0f ours %7.0f  W%d L%d"%(k,len(v),st.mean([r['them'] for r in v]),st.mean([r['me'] for r in v]),sum(1 for r in v if r['result']=='WIN'),sum(1 for r in v if r['result']!='WIN')))
