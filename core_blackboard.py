#!/usr/bin/env python3
"""CORE shared investigation blackboard.

A small, append-only, typed workspace for observations, hypotheses, gaps and
mediation decisions. Agents do not directly mutate one another's conclusions.
"""
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone

SCHEMA_VERSION = "1.0"
KINDS = {"observation", "hypothesis", "gap", "association", "decision"}

def now(): return datetime.now(timezone.utc).isoformat()

def observation(observer, subject, relation, object_, source, passage, confidence=0.0, **extra):
    return {"id":str(uuid.uuid4()),"kind":"observation","observer":observer,"subject":subject,"relation":relation,"object":object_,"source":source,"passage":passage,"confidence":float(confidence),"created_at":now(),"metadata":extra}

def add(board, item):
    if item.get("kind") not in KINDS: raise ValueError("invalid blackboard item kind")
    board.setdefault("items", []).append(item); return item

def new_board(case_id):
    return {"schema_version":SCHEMA_VERSION,"case_id":case_id,"created_at":now(),"items":[],"conflicts":[],"status":"OPEN"}

def save(path, board): path.write_text(json.dumps(board,indent=2),encoding="utf-8")
