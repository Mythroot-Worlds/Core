#!/usr/bin/env python3
"""Lightweight pairwise semantic comparison for CORE/Robin.

Dependency-free comparator: normalized lexical overlap, small synonym families,
section alignment, and bidirectional coverage. It produces evidence; it never
makes a final canon or relationship decision.
"""
from __future__ import annotations
import argparse,json,re
from dataclasses import dataclass,asdict
from pathlib import Path
from typing import Iterable

STOP={"the","and","that","with","from","this","their","they","are","for","into","have","has","its","was","were","been","being","than","then","only","also","often","typically","generally","through","about","very","more","most"}
SYNONYMS={"children":"youth","child":"youth","young":"youth","youngpeople":"youth","families":"family","households":"family","household":"family","learn":"teach","learns":"teach","learning":"teach","taught":"teach","rotate":"cycle","rotates":"cycle","rotation":"cycle","rotating":"cycle","community":"communal","communities":"communal","communal":"communal","region":"regional","regional":"regional","village":"settlement","villages":"settlement","settlements":"settlement"}

def tokens(text):
    raw=re.findall(r"[a-z0-9]+",text.lower());return {SYNONYMS.get(x,x) for x in raw if len(x)>2 and x not in STOP}

def jaccard(a,b):return len(a&b)/len(a|b) if a and b else 0.0

def best_coverage(a,b):
    if not a or not b:return 0.0,[]
    out=[]
    for x in a:
        xt=tokens(x.get('text',''));best=(0.0,None)
        for y in b:
            yt=tokens(y.get('text',''));score=jaccard(xt,yt);same_section=bool(x.get('section') and y.get('section') and x.get('section','').strip().lower()==y.get('section','').strip().lower())
            if same_section:score=min(1.0,score+.10)
            if score>best[0]:best=(score,y)
        if best[1] is not None:out.append({'a':x.get('text',''),'b':best[1].get('text',''),'score':round(best[0],4),'same_section':bool(x.get('section') and best[1].get('section') and x.get('section','').strip().lower()==best[1].get('section','').strip().lower())})
    return (sum(x['score'] for x in out)/len(out) if out else 0.0),out

@dataclass
class Comparison:
    score:float;a_to_b:float;b_to_a:float;same_information:bool;contradiction_signal:bool;unmatched_a:int;unmatched_b:int;alignments:list[dict];explanation:list[str]
    def as_dict(self):return asdict(self)

def compare_units(units_a:Iterable[dict],units_b:Iterable[dict],threshold=.72):
    a=list(units_a);b=list(units_b);a2b,ab=best_coverage(a,b);b2a,ba=best_coverage(b,a);score=round((a2b+b2a)/2,4)
    unmatched_a=sum(x['score']<threshold for x in ab);unmatched_b=sum(x['score']<threshold for x in ba)
    pa={'not','never','no','without','cannot'}&tokens(' '.join(x.get('text','') for x in a));pb={'not','never','no','without','cannot'}&tokens(' '.join(x.get('text','') for x in b));contradiction=bool(pa!=pb and score>=threshold)
    same=score>=threshold and a2b>=threshold and b2a>=threshold and not contradiction
    explanation=[]
    explanation.append('bidirectional information coverage is above threshold' if same else 'bidirectional information coverage is insufficient for equivalence')
    if a2b>=threshold:explanation.append('A is substantially covered by B')
    if b2a>=threshold:explanation.append('B is substantially covered by A')
    if contradiction:explanation.append('polarity mismatch requires contradiction review')
    return Comparison(score,round(a2b,4),round(b2a,4),same,contradiction,unmatched_a,unmatched_b,ab+ba,explanation)

def load(p,d):
    try:return json.loads(p.read_text(encoding='utf-8')) if p.exists() else d
    except:return d

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--out',default='TOOLS/REPOSITORY/REPORTS');x=ap.parse_args();root=Path(x.root).resolve();out=root/x.out
    units=load(out/'CORE_INFORMATION_UNITS.json',{'units':[]});discovery=load(out/'CORE_RELATIONSHIP_DISCOVERY.json',{'relationships':[]});by={}
    for u in units.get('units',[]):by.setdefault(u.get('source'),[]).append(u)
    rows=[]
    for r in discovery.get('relationships',[]):
        c=compare_units(by.get(r.get('left'),[]),by.get(r.get('right'),[]));rows.append({'relationship_id':r.get('relationship_id'),'left':r.get('left'),'right':r.get('right'),'comparison':c.as_dict()})
    summary={'candidate_pairs':len(rows),'same_information_candidates':sum(r['comparison']['same_information'] for r in rows),'mean_score':round(sum(r['comparison']['score'] for r in rows)/len(rows),4) if rows else 0.0,'contradiction_signals':sum(r['comparison']['contradiction_signal'] for r in rows)}
    payload={'engine':'CORE Pairwise Semantic Comparator','schema_version':'1.0','mode':'READ_ONLY','purpose':'high-precision information equivalence evidence for Robin and VARIANT arbitration','summary':summary,'comparisons':rows,'safety':{'final_relationship_decision':False,'automatic_canon_change':False,'provenance_required':True}}
    out.mkdir(parents=True,exist_ok=True);(out/'CORE_SEMANTIC_COMPARATOR.json').write_text(json.dumps(payload,indent=2),encoding='utf-8');(out/'CORE_SEMANTIC_COMPARATOR.md').write_text('# CORE Pairwise Semantic Comparator\n\n'+json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
