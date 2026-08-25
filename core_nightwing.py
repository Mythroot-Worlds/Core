#!/usr/bin/env python3
"""CORE Nightwing: independent synthesis of multiple evidence perspectives."""
from __future__ import annotations
import argparse,json
from pathlib import Path
def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8')) if p.exists() else d
 except:return d
def synth(case,oracle):
 dims=case.get('dimensions',[]);out=[]
 for d in dims:
  state=d.get('state');verdict='CONVERGENT' if state=='AGREE' else ('DIVERGENT' if state in {'BATMAN_ONLY','ROBIN_ONLY'} else 'UNRESOLVED');out.append({'dimension':d.get('dimension'),'verdict':verdict,'basis':{'batman_answered':d.get('batman_answered',False),'robin_semantic_support':d.get('robin_semantic_support',False),'oracle_context':bool(oracle.get('oracle',{}).get('association_candidates'))}})
 return {'relationship_id':case.get('relationship_id'),'dimensions':out,'independent_synthesis':'Nightwing does not overwrite Batman or Robin; it evaluates convergence/divergence and records unresolved dimensions'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--out',default='REPORTS');x=ap.parse_args();root=Path(x.root).resolve();out=root/x.out;cross=load(out/'CORE_CROSSCHECK_REPORT.json',{'cases':[]});oracle=load(out/'CORE_ORACLE_REPORT.json',{'cases':[]});omap={c.get('case_id'):c for c in oracle.get('cases',[])};cases=[synth(c,omap.get(c.get('relationship_id'),{})) for c in cross.get('cases',[])];summary={'cases':len(cases),'convergent_dimensions':sum(sum(x['verdict']=='CONVERGENT' for x in c['dimensions']) for c in cases),'divergent_dimensions':sum(sum(x['verdict']=='DIVERGENT' for x in c['dimensions']) for c in cases),'unresolved_dimensions':sum(sum(x['verdict']=='UNRESOLVED' for x in c['dimensions']) for c in cases)};payload={'engine':'CORE A.C.E. Nightwing','schema_version':'1.0','mode':'READ_ONLY','purpose':'independent synthesis and verification of investigator perspectives','cases':cases,'summary':summary};out.mkdir(parents=True,exist_ok=True);(out/'CORE_NIGHTWING_REPORT.json').write_text(json.dumps(payload,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
