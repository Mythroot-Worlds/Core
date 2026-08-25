#!/usr/bin/env python3
"""Extract conservative information units for semantic comparison."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
SKIP={'.git','.github','TOOLS','07_ARCHIVE','node_modules','__pycache__'}
HEAD_RE=re.compile(r'^\s{0,3}#{1,6}\s+(.+?)\s*$')
def files(root):
 for p in root.rglob('*.md'):
  if any(x in SKIP for x in p.parts):continue
  yield p
def normalize(text):
 text=re.sub(r'[`*_>#\[\]()]',' ',text.lower());return re.sub(r'\s+',' ',text).strip()
def units(path,root):
 try:body=path.read_text(encoding='utf-8',errors='replace')[:160000]
 except Exception:return []
 section='DOCUMENT';out=[];source=path.relative_to(root).as_posix()
 for line_no,raw in enumerate(body.splitlines(),1):
  s=raw.strip()
  if not s:continue
  hm=HEAD_RE.match(raw)
  if hm:section=hm.group(1).strip();continue
  if len(s)<30 or s.startswith('|') or s.startswith('```') or s.startswith('---'):continue
  if not (s.startswith(('-', '*', '+')) or re.search(r'[.!?:;]',s)):continue
  text=re.sub(r'^[-*+]\s+','',s).strip()
  if len(text)<30:continue
  norm=normalize(text)
  if not norm:continue
  out.append({'source':source,'line':line_no,'section':section,'text':text[:1000],'normalized':norm,'fingerprint':hashlib.sha1(norm.encode()).hexdigest()[:16]})
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--out',default='REPORTS');a=ap.parse_args();root=Path(a.root).resolve();out=root/a.out;out.mkdir(parents=True,exist_ok=True);all_units=[]
 for p in files(root):all_units.extend(units(p,root))
 report={'engine':'CORE Information Unit Extraction','schema_version':'1.1','mode':'READ_ONLY','units':all_units,'summary':{'documents_with_units':len({u['source'] for u in all_units}),'information_units':len(all_units)},'safety':{'final_relationship_decision':False,'automatic_canon_change':False,'provenance_required':True},'source_path_contract':'repository-relative POSIX paths'};(out/'CORE_INFORMATION_UNITS.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(f"CORE information units: {len(all_units)} across {report['summary']['documents_with_units']} documents.")
if __name__=='__main__':main()
