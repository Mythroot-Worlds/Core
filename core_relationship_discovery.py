#!/usr/bin/env python3
"""CORE relationship discovery: conservative, read-only candidate generation."""
from __future__ import annotations
import argparse,hashlib,json,re
from collections import defaultdict
from pathlib import Path
STOP=set('about after again against all also and are because been being but can could each for from have into its more most not other our over same should some than that their there these they this those through under was were what when where which while with would your'.split())
def words(t):return {w for w in re.findall(r'[a-z][a-z0-9_]{3,}',t.lower()) if w not in STOP}
def read(p):return p.read_text(encoding='utf-8',errors='replace')
def stable(a,b):return 'REL-'+hashlib.sha1((a+'|'+b).encode()).hexdigest()[:16]
def match_strength(j):return 5 if j>=.30 else 4 if j>=.22 else 3 if j>=.16 else 2 if j>=.11 else 1
def strength_label(n):return ['Minimal','Weak','Moderate','Strong','Near Certain'][n-1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--out',default='REPORTS');ap.add_argument('--scope',default='.');ap.add_argument('--min-overlap',type=int,default=8);a=ap.parse_args();root=Path(a.root).resolve();base=(root/a.scope).resolve();docs=[]
 if base.exists():
  for p in base.rglob('*.md'):
   if any(x in {'.git','.github','node_modules','__pycache__'} for x in p.parts):continue
   ws=words(read(p))
   if ws:docs.append((p.relative_to(root).as_posix(),ws))
 inv=defaultdict(set)
 for i,(_,ws) in enumerate(docs):
  for w in ws:inv[w].add(i)
 pairs=set()
 for ids in inv.values():
  ids=list(ids)
  if len(ids)>80:continue
  for i in range(len(ids)):
   for j in range(i+1,len(ids)):pairs.add(tuple(sorted((ids[i],ids[j]))))
 candidates=[]
 for i,j in pairs:
  pa,wa=docs[i];pb,wb=docs[j];inter=wa&wb
  if len(inter)<a.min_overlap:continue
  jac=len(inter)/max(1,len(wa|wb))
  if jac<.08:continue
  rid=stable(min(pa,pb),max(pa,pb));strength=match_strength(jac);candidates.append({'relationship_id':rid,'left':pa,'right':pb,'shared_terms':len(inter),'jaccard':round(jac,4),'match_strength':strength,'match_strength_label':strength_label(strength),'classification':'UNCLASSIFIED','status':'DISCOVERED_UNREVIEWED','review_required':True})
 candidates.sort(key=lambda x:(x['match_strength'],x['jaccard'],x['shared_terms']),reverse=True);out=root/a.out;out.mkdir(parents=True,exist_ok=True);data={'engine':'CORE Relationship Discovery','mode':'READ_ONLY','scope':a.scope,'documents_analyzed':len(docs),'relationships_discovered':len(candidates),'relationships':candidates[:500],'safety':{'automatic_merge':False,'automatic_canon_change':False,'provenance_required':True}};(out/'CORE_RELATIONSHIP_DISCOVERY.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(f'CORE discovery: {len(docs)} docs, {len(candidates)} candidate relationships.')
if __name__=='__main__':main()
