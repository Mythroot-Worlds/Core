#!/usr/bin/env python3
"""CORE contextual skimmer: cheap indicators -> provisional context."""
from __future__ import annotations
from pathlib import Path
import re
INDICATORS={'POPULATION':['people','peoples','population','lineage','clan','family','house','houses'],'LOCALITY':['local','village','settlement','district','house','houses','hamlet'],'REGIONAL':['regional','region','river','mountain','mountains','plains','wetlands','coast','desert'],'BROAD':['continent','continental','hearth-wide','all peoples','general','broad'],'FAMILY':['family','birth','childhood','marriage','kin','household','partnership'],'GOVERNANCE':['governance','authority','leadership','council','leader','head','chief'],'SPECIALIST':['specialist','lineage','craft','guild','keeper'],'SUPPORT':['checklist','audit','guide','reference','framework','supporting'],'HISTORICAL':['archive','revision','former','obsolete','historical','legacy']}
def skim(path,root,limit=140):
    p=Path(path);full=(root/p) if not p.is_absolute() else p
    try:text=full.read_text(encoding='utf-8',errors='ignore')
    except Exception:text=''
    lines=text.splitlines();headings=[x.strip() for x in lines[:limit] if x.strip().startswith('#')];sample=' '.join(lines[:limit]);return sample,headings
def indicators(path,root):
    sample,headings=skim(path,root);text=((path or '')+' '+sample).lower();found={k:sorted({w for w in words if re.search(r'(?<![a-z])'+re.escape(w)+r'(?![a-z])',text)}) for k,words in INDICATORS.items()};return {k:v for k,v in found.items() if v},headings
def context(path,root):
    found,headings=indicators(path,root);scope=[]
    if 'BROAD' in found:scope.append('BROAD')
    if 'REGIONAL' in found:scope.append('REGIONAL')
    if 'LOCALITY' in found:scope.append('LOCAL_OR_SETTLEMENT')
    if 'FAMILY' in found:scope.append('NARROW_SUBJECT')
    return {'indicators':found,'headings':headings[:12],'scope_signals':scope}
