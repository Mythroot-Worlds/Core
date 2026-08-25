#!/usr/bin/env python3
"""CORE A.C.E. Detective: bounded investigation with deciding-factor context."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from core_foundations import factor_snapshot
from mythroot_profile import profile_snapshot, RELATIONSHIP_GATES
DEFAULT_POOL_SIZE=10
MAX_POOL_SIZE=20
FOCUS={'authority':['AUTHORITY','LEADERSHIP','GOVERNANCE','COUNCIL','LEADER','HEAD','HOUSE'],'scope':['CONTINENT','CONTINENTAL','HEARTH-WIDE','REGIONAL','REGION','MOUNTAIN','RIVER','PLAINS','SETTLEMENT','VILLAGE','LOCAL'],'support':['SUPPORT','INFORMS','REFERENCES','DERIVED FROM','BASED ON','BUILDS ON','CHECKLIST','AUDIT','REFERENCE'],'temporal':['REVISED','SUPERSEDES','REPLACED','PREVIOUS','FORMER','EARLIER','CURRENT','OLDER','REVISION','HISTORICAL'],'family':['FAMILY','BIRTH','CHILDHOOD','MARRIAGE','KIN','HOUSEHOLD'],'specialist':['SPECIALIST','LINEAGE','HOUSE','CRAFT','KEEPER'],'identity':['IDENTITY','ENTITY','POPULATION','REGION','SUBREGION','SUBJECT','DOCUMENT ROLE','PURPOSE','SCOPE']}
def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8')) if p.exists() else d
 except:return d
def read(path,root,limit=60000):
 try:return (root/path).read_text(encoding='utf-8')[:limit]
 except:return ''
def terms(text):
 u=text.upper();return {k:sorted({w for w in ws if re.search(r'\b'+re.escape(w)+r'\b',u)}) for k,ws in FOCUS.items()}
def files(root):return [str(p.relative_to(root)).replace('\\','/') for p in root.rglob('*.md') if '.git' not in p.parts and 'REPORTS' not in p.parts]
def candidates(a,b,root,exclude=(),pool=DEFAULT_POOL_SIZE):
 ta,tb=terms(read(a,root)),terms(read(b,root));excluded={a,b,*exclude};rows=[]
 for p in files(root):
  if p in excluded:continue
  t=terms(read(p,root));score=0
  for k in FOCUS: score += 2*len((set(ta[k])|set(tb[k])) & set(t[k]))
  if score:rows.append((score,p))
 return [p for _,p in sorted(rows,key=lambda x:(x[0],x[1]),reverse=True)[:max(1,min(pool,MAX_POOL_SIZE))]]
def question_for(u):
 l=u.lower()
 if 'identity' in l:return ('identity','What evidence establishes the entity, scope, region, subject, role, or purpose of this document, and where does that evidence come from?')
 if 'authority' in l:return ('authority','Which source explicitly establishes the organizational authority, leadership role, and scope of the disputed document?')
 if 'support' in l:return ('support','Which source explicitly establishes that one document supports, informs, references, or derives from the other?')
 if 'temporal' in l:return ('temporal','Which source establishes the temporal relationship, revision, supersession, or historical precedence between these documents?')
 return ('general','What specific source evidence would resolve the remaining uncertainty?')
def investigate(r,root,pool=DEFAULT_POOL_SIZE):
 a,b=r.get('left',''),r.get('right','');factor_map=factor_snapshot(read(a,root),read(b,root));profile=profile_snapshot();unknown=['identity'] if not a or not b else [];questions=[{'unknown':u,'question':question_for(u)[1],'dimension':question_for(u)[0]} for u in unknown];targets=candidates(a,b,root,pool=pool)
 return {'relationship_id':r.get('relationship_id'),'documents':{'a':a,'b':b},'domain_profile':profile['name'],'domain_profile_version':profile['version'],'mythroot_principles':profile['principles'],'deciding_factors':factor_map['dimensions'],'principle_checks':{k:{'gate_factors':list(v),'status':'candidate_only'} for k,v in RELATIONSHIP_GATES.items()},'known':[],'unknown_before':unknown,'questions':questions,'investigation_rounds':1,'investigation_rounds_detail':[{'round':1,'trigger':'initial investigation','evidence_targets':targets,'questions':questions,'unanswered_after_round':unknown,'next_round_justified':bool(unknown)}],'evidence_pool_size':pool,'evidence_targets':targets,'evidence_claims':[],'evidence_updates':[],'unknown_after':unknown,'second_pass':{'attempted':False,'causally_justified':False,'missing_evidence':[],'targets':[],'new_targets_distinct_from_round_one':False},'stop_reason':'standalone CORE requires repository adapter data for full bounded investigation','safety':{'self_training':False,'automatic_rule_promotion':False,'automatic_canon_change':False}}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--out',default='REPORTS');ap.add_argument('--pool-size',type=int,default=DEFAULT_POOL_SIZE);x=ap.parse_args();root=Path(x.root).resolve();out=root/x.out;discovery=load(out/'CORE_RELATIONSHIP_DISCOVERY.json',{'relationships':[]});cases=[investigate(r,root,max(1,min(x.pool_size,MAX_POOL_SIZE))) for r in discovery.get('relationships',[])];report={'engine':'CORE A.C.E. Detective','schema_version':'2.3','mode':'READ_ONLY','cases':cases,'summary':{'cases':len(cases),'focus_dimensions':list(FOCUS)}};out.mkdir(parents=True,exist_ok=True);(out/'CORE_DETECTIVE_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report['summary'],indent=2))
if __name__=='__main__':main()
