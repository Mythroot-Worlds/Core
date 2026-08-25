#!/usr/bin/env python3
"""CORE A.C.E. Robin: independent syntax/word-relation cross-checker."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
MAX_WINDOW=3
RELATIONS={'authority':['govern','rule','lead','oversee','command','authority','governance','council','head'],'support':['support','inform','reference','derive','based','build','expand','adapt','source'],'temporal':['revise','replace','supersede','previous','former','earlier','current','older','version'],'scope':['continent','regional','region','settlement','village','local','hearth','mountain','river','plains']}
def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8')) if p.exists() else d
 except:return d
def read(path,root,limit=60000):
 try:return (root/path).read_text(encoding='utf-8')[:limit]
 except:return ''
def sentences(text):return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+',text) if s.strip()]
def relation_hits(sentence,dimension):
 u=sentence.lower();return [w for w in RELATIONS.get(dimension,[]) if re.search(r'\b'+re.escape(w)+r'\w*\b',u)]
def named_spans(sentence):
 vals=[]
 for m in re.finditer(r'\b([A-Z][A-Za-z0-9_-]{2,}(?:\s+[A-Z][A-Za-z0-9_-]{2,}){0,4})\b',sentence):
  v=m.group(1).strip(' .,;:()[]')
  if v not in vals and v.upper() not in {'THE','THIS','THAT','WHICH','DOCUMENT','SOURCE','CURRENT','FORMER'}:vals.append(v)
 return vals[:10]
def local_analysis(path,root,dimension):
 ss=sentences(read(path,root));out=[]
 for i,s in enumerate(ss):
  hits=relation_hits(s,dimension)
  if not hits:continue
  lo=max(0,i-MAX_WINDOW);hi=min(len(ss),i+MAX_WINDOW+1);window=ss[lo:hi];entities=named_spans(s);syntax_signal=bool(re.search(r'\b(?:is|are|has|have|governs?|rules?|leads?|supports?|informs?|derives?|replaces?|supersedes?|belongs?|contains?|within|under|from|for)\b',s,re.I));out.append({'source':path,'dimension':dimension,'sentence':s,'window':window,'relation_terms':hits,'entities':entities,'syntax_signal':syntax_signal,'subject_candidate':entities[0] if entities else None,'object_candidates':entities[1:] if len(entities)>1 else [],'relation_candidate':hits[0],'context_depth':len(window)})
 return out[:12]
def robin_case(case,root):
 docs=[case.get('documents',{}).get('a',''),case.get('documents',{}).get('b','')];dims=[q.get('dimension','general') for q in case.get('questions',[])] or ['authority','support','temporal'];analyses=[]
 for d in dict.fromkeys(dims):
  for p in docs:analyses.extend(local_analysis(p,root,d))
 by={d:[a for a in analyses if a['dimension']==d] for d in dims};results={}
 for d,items in by.items():
  explicit=[x for x in items if x['syntax_signal'] and x['relation_candidate']];entities=sum(len(x['entities']) for x in explicit);ambiguity=sum(1 for x in items if len(x['relation_terms'])>1 or len(x['entities'])>3);results[d]={'relation_observations':len(items),'syntax_supported':len(explicit),'entity_observations':entities,'ambiguity_signals':ambiguity,'supports_semantic_relation':bool(explicit and entities>0),'confidence':'high' if explicit and entities>0 and ambiguity==0 else ('medium' if explicit else 'low')}
 return {'relationship_id':case.get('relationship_id'),'documents':case.get('documents',{}),'robin_results':results,'observations':analyses,'method':'local syntax + contextual window + conservative entity/relation candidates','independence':'Robin analyzes source text independently'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--out',default='REPORTS');x=ap.parse_args();root=Path(x.root).resolve();out=root/x.out;report=load(out/'CORE_DETECTIVE_REPORT.json',{'cases':[]});cases=[robin_case(c,root) for c in report.get('cases',[])];summary={'cases':len(cases),'semantic_relation_cases':sum(any(v['supports_semantic_relation'] for v in c['robin_results'].values()) for c in cases),'high_confidence_dimensions':sum(sum(v['confidence']=='high' for v in c['robin_results'].values()) for c in cases),'ambiguity_signals':sum(sum(v['ambiguity_signals'] for v in c['robin_results'].values()) for c in cases)};payload={'engine':'CORE A.C.E. Robin','schema_version':'1.0','mode':'READ_ONLY','purpose':'independent syntax/context semantic cross-check','cases':cases,'summary':summary};out.mkdir(parents=True,exist_ok=True);(out/'CORE_ROBIN_REPORT.json').write_text(json.dumps(payload,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
