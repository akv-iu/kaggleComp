import json, collections, statistics as st
rows=json.load(open('replay_index.json'))
# which submission dirs
subs=collections.Counter(r['file'].split('/')[1] for r in rows)
print("submissions:", subs)
# v14 = 55507562
for tag in ['submission-55507562','submission-55490581']:
    v=[r for r in rows if tag in r['file']]
    if not v: continue
    print("\n===",tag,"n=",len(v))
    mine=[r['me'] for r in v]; theirs=[r['them'] for r in v]
    print(" our mean %.0f median %.0f min %.0f max %.0f"%(st.mean(mine),st.median(mine),min(mine),max(mine)))
    w=sum(1 for r in v if r['result']=='WIN'); print(" W/L", w, len(v)-w)
    # correlation between me and them
    print(" opp mean %.0f"%st.mean(theirs))
    lo=[r for r in v if r['me']<62000]
    print(" games under 62k:",len(lo))
    for r in sorted(lo,key=lambda r:r['me'])[:20]:
        print("   me %7.0f them %7.0f %s %s seat%s"%(r['me'],r['them'],r['result'],r['opponent'],r['seat']))
