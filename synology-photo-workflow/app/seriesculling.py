from __future__ import annotations
import numpy as np
def ratingforscore(score,bands):
    return max((int(k) for k,v in bands.items() if score>=float(v)),default=0)
def clusterseries(rows, eps=.18, minsamples=2):
    parent=list(range(len(rows)))
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[b]=a
    for i in range(len(rows)):
        a=np.array(rows[i]['embedding'])
        for j in range(i):
            b=np.array(rows[j]['embedding']);d=1-float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-12))
            if d<=eps:union(i,j)
    groups={}
    for i in range(len(rows)):groups.setdefault(find(i),[]).append(i)
    return [x for x in groups.values() if len(x)>=minsamples]
def applyseriesculling(rows,cfg):
    s=cfg['seriesdetection']; groups=clusterseries(rows,float(s['clustereps']),int(s['minsamples'])) if s.get('enabled',True) else []
    for n,g in enumerate(groups,1):
        g.sort(key=lambda i:rows[i]['finalscore'],reverse=True);best=rows[g[0]]
        for rank,i in enumerate(g,1):
            r=rows[i];r.update(seriesid=f'S{n:03}',seriessize=len(g),seriesrank=rank,seriesbest=rank==1,seriesmargintobest=best['finalscore']-r['finalscore'])
            if rank==1 and r['decision']=='reject':r['decision']='review';r['decisionreason']='series-best-rescue'
            elif rank>1:
                r['decisionreason']='series-nonbest'
                if r['finalscore']<best['finalscore']-float(s['reviewmargin']):r['decision']='review' if s.get('demotenonbestto')=='review' else 'reject'
            if r.get('protectedbyfamilyrule') and r['decision']=='reject':r['decision']='review'
    for r in rows:r.setdefault('seriesid',None);r.setdefault('seriessize',0);r.setdefault('seriesrank',0);r.setdefault('seriesbest',False);r.setdefault('seriesmargintobest',None)
    return rows
