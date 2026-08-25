#!/usr/bin/env python3
"""Apply evidence-gated VARIANT arbitration using structural identity + information evidence."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from core_variant_arbitration import assess_variant
from core_semantic_comparator import compare_units
from core_identity_resolver import resolve_identity, identity_match

SKIP={'.git','.github','TOOLS','07_ARCHIVE','node_modules','__pycache__'}
def load(p,d):
    try:return json.loads(p.read_text(encoding='utf-8')) if p.exists() else d
    except:return d
def for_source(source,report,key):return [x for x in report.get(key,[]) if x.get('source')==source]
def doc_context(root,rel,claims,units):
    identity=resolve_identity(root,rel)
    return {**identity,'claims':for_source(rel,claims,'claims'),'information_units':for_source(rel,units,'units')}
def discover_same_scope_pairs(root):
    files=[];base=root/'03_PEOPLES/CULTURES/HEARTH'
    if not base.exists(): return files
    for p in base.rglob('*.md'):
        rel=p.relative_to(root).as_posix()
        if any(part in SKIP for part in p.parts): continue
        files.append(rel)
    return files
def candidate_key(identity):
    subject_tokens=set(re.findall(r'[a-z0-9]+',identity.get('subject') or ''));role_tokens=set(re.findall(r'[a-z0-9]+',identity.get('role') or ''))
    return subject_tokens | role_tokens
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--out',default='TOOLS/REPOSITORY/REPORTS');x=ap.parse_args();root=Path(x.root).resolve();out=root/x.out
    discovery=load(out/'CORE_RELATIONSHIP_DISCOVERY.json',{'relationships':[]});claims=load(out/'CORE_SEMANTIC_CLAIMS.json',{'claims':[]});units=load(out/'CORE_INFORMATION_UNITS.json',{'units':[]})
    rows=[];seen=set();eligible=rejected=0
    def assess_pair(left_rel,right_rel,source='relationship_discovery'):
        nonlocal eligible,rejected
        key=tuple(sorted((left_rel,right_rel)))
        if key in seen or left_rel==right_rel:return
        seen.add(key);left=doc_context(root,left_rel,claims,units);right=doc_context(root,right_rel,claims,units)
        same_identity,identity_reasons=identity_match(left,right);comparison=compare_units(left['information_units'],right['information_units']);assessment=assess_variant(left,right)
        if not same_identity: assessment.eligible=False
        x={'relationship_id':f'VAR-{abs(hash(key)) & 0xffffffff:08x}','left':left_rel,'right':right_rel,'source':source,'left_identity':{k:left[k] for k in ('entity','population','region','subregion','subject','role','purpose','scope')},'right_identity':{k:right[k] for k in ('entity','population','region','subregion','subject','role','purpose','scope')},'identity_match':same_identity,'identity_reasons':identity_reasons,'pairwise_semantic_comparison':comparison.as_dict(),'variant_arbitration':assessment.as_dict()}
        x['variant_status']='ELIGIBLE' if assessment.eligible else 'REJECTED';eligible+=int(assessment.eligible);rejected+=int(not assessment.eligible);rows.append(x)
    for r in discovery.get('relationships',[]): assess_pair(r['left'],r['right'])
    files=discover_same_scope_pairs(root);ctx={f:doc_context(root,f,claims,units) for f in files};by_scope={}
    for f,c in ctx.items(): by_scope.setdefault(c.get('scope'),[]).append(f)
    for scope,items in by_scope.items():
        for i,left in enumerate(items):
            for right in items[i+1:]:
                if candidate_key(ctx[left]) & candidate_key(ctx[right]): assess_pair(left,right,'same_scope_identity_candidate')
    result={'engine':'CORE VARIANT Gate','schema_version':'4.0','mode':'READ_ONLY','definition':'VARIANT means near-equivalent informational content for the same structural identity, scope, document role, purpose, and applicable time. Wording, presentation, formatting, and modest detail may differ. Similar information across different regions or roles is not VARIANT.','candidate_count':len(rows),'variant_candidates':eligible,'rejected_variant_candidates':rejected,'relationships':rows,'identity_gate':{'authoritative':True,'fields':['entity','population','region','subregion','subject','role','purpose','scope'],'semantic_similarity_cannot_override':True},'safety':{'automatic_variant_acceptance':False,'automatic_canon_change':False,'provenance_required':True}}
    (out/'CORE_VARIANT_GATE.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(out/'CORE_VARIANT_GATE.md').write_text(f'# CORE VARIANT Gate\n\nCandidates assessed: **{len(rows)}**\n\nEligible VARIANT candidates: **{eligible}**\n\nRejected VARIANT candidates: **{rejected}**\n\nIdentity is authoritative: semantic similarity cannot override a structural identity mismatch.\n',encoding='utf-8');print(f'CORE VARIANT gate: {len(rows)} assessed; {eligible} eligible; {rejected} rejected.')
if __name__=='__main__':main()
