#!/usr/bin/env python3
"""CORE Oracle: read-only information, provenance, and canonical context."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from core_blackboard import new_board,add,observation
from core_foundations import factor_snapshot
def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8')) if p.exists() else d
 except:return d
def read(p,root):
 try:return (root/p).read_text(encoding='utf-8')[:60000]
 except:return ''
def terms(text):return sorted(set(re.findall(r'\b[A-Za-z][A-Za-z0-9_-]{3,}\b',text.lower())))
def canonical_status(text):
 u=text.upper()
 if 'HARD CANON' in u:return 'HARD_CANON'
 if 'FLEXIBLE CANON' in u:return 'FLEXIBLE_CANON'
 if 'INTENTIONALLY OPEN' in u or 'DELIBERATELY OPEN' in u or 'CREATOR-EXPANDABLE' in u:return 'OPEN'
 if re.search(r'\bUNKNOWN\b',u):return 'UNKNOWN'
 return 'UNSPECIFIED'
def source_role(path):
 u=(path or '').upper()
 if any(x in u for x in ('REPORTS/','/TOOLS/','CHECKLIST','AUDIT')):return 'TOOLING'
 if any(x in u for x in ('ARCHIVE','HISTORICAL','REVISION')):return 'HISTORICAL'
 if any(x in u for x in ('STANDARD','PROFILE','TEMPLATE','PROJECT_MAP')):return 'METHODOLOGY'
 return 'CANONICAL_CANDIDATE'
def meaningful_shared_terms(a,b):
 A=set(terms(a));B=set(terms(b));shared=sorted(A&B,key=lambda x:(-len(x),x));return [x for x in shared if len(x)>=5 and x not in {'about','there','which','these','those','their','where','could','would','should'}][:25]
def case_oracle(case,root):
 docs=case.get('documents',{});a=docs.get('a','');b=docs.get('b','');ta,tb=read(a,root),read(b,root);shared=meaningful_shared_terms(ta,tb);board=new_board(case.get('relationship_id','unknown'));obs=[]
 for t in shared[:12]:add(board,observation('oracle',t,'retrieval_clue',t,a,'shared lexical term; retrieval clue only',.15,association_type='lexical_clue',semantic_status='UNVERIFIED'))
 candidates=[];files=[p for p in root.rglob('*.md') if '.git' not in p.parts and 'REPORTS' not in p.parts];focus=set(shared)
 for p in files:
  rel=str(p.relative_to(root)).replace('\\','/');
  if rel in {a,b}:continue
  overlap=len(focus & set(terms(read(rel,root))))
  if overlap>=3:candidates.append((overlap,rel))
 candidates=sorted(candidates,key=lambda x:(-x[0],x[1]))[:15];factor=factor_snapshot(ta,tb);board['oracle']={'shared_terms':shared,'retrieval_clues':len(board['items']),'association_candidates':[{'path':p,'overlap':s,'source_role':source_role(p),'canonical_status':canonical_status(read(p,root))} for s,p in candidates],'deciding_factor_snapshot':factor['dimensions'],'strategy':'broad retrieval clue -> factor-aware narrowing -> provenance/canon inspection','semantic_associations_created':0};return board
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--out',default='REPORTS');x=ap.parse_args();root=Path(x.root).resolve();out=root/x.out;det=load(out/'CORE_DETECTIVE_REPORT.json',{'cases':[]});boards=[case_oracle(c,root) for c in det['cases']];payload={'engine':'CORE A.C.E. Oracle','schema_version':'2.0','mode':'READ_ONLY','purpose':'canonical/context retrieval, provenance, and information relay; Oracle does not decide semantic relationships','cases':boards,'summary':{'cases':len(boards),'retrieval_clues':sum(len(b['items']) for b in boards),'cases_with_repository_candidates':sum(bool(b['oracle']['association_candidates']) for b in boards),'semantic_associations_created':0},'safety':{'human_validation_required':True,'automatic_canon_change':False,'automatic_rule_promotion':False,'lexical_overlap_is_not_semantic_evidence':True}};out.mkdir(parents=True,exist_ok=True);(out/'CORE_ORACLE_REPORT.json').write_text(json.dumps(payload,indent=2),encoding='utf-8');print(json.dumps(payload['summary'],indent=2))
if __name__=='__main__':main()
