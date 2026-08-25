#!/usr/bin/env python3
"""CORE identity resolver: structural identity before semantic comparison.

Topology (entity anchor, known regions, filename->role keywords) is
Mythroot/ARUUN-specific configuration, supplied by a profile module rather
than hardcoded here, per the engine/profile separation this repo exists to
establish. Defaults to mythroot_profile.WORLD_TOPOLOGY so existing call
sites (resolve_identity(root, rel)) keep working unchanged; pass a
different topology dict to resolve identity for a different world.
"""
from __future__ import annotations
import re
from pathlib import Path
from mythroot_profile import WORLD_TOPOLOGY as _MYTHROOT_TOPOLOGY


def normalize_name(value):
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") if value else None


def _front_context(path):
    try:
        body = path.read_text(encoding="utf-8", errors="replace")[:30000]
    except Exception:
        return {}
    out = {}
    for line in body.splitlines()[:120]:
        m = re.match(r"^\s*[-#]*\s*(subject|scope|population|region|subregion|entity|purpose|role|document\s*role|type)\s*[:=-]\s*(.+?)\s*$", line, re.I)
        if not m:
            continue
        key = re.sub(r"\s+", "_", m.group(1).lower())
        if key in ("document_role", "type"):
            key = "role"
        out[key] = m.group(2).strip()
    return out


def resolve_identity(root, rel, topology=None):
    """Return a conservative identity tuple; structural scope is authoritative.

    Every resolved field carries an evidence entry (value/source/confidence)
    in identity_evidence, and the overall identity_confidence is the mean
    confidence across fields that actually resolved to a value. Fields that
    never resolved stay None and are excluded from the average -- an absent
    field is not evidence of anything, and is handled by identity_match()'s
    UNCERTAIN state rather than by silently lowering confidence here.

    identity_confidence is currently a hand-set weighting (path match = 1.0,
    frontmatter = 0.85-0.95, filename keyword guess = 0.55-0.6, fallback
    inference = 0.3), not a learned model. A Fellegi-Sunter-style learned
    version becomes possible once core_adjudication_queue.py has accumulated
    enough human-reviewed match/non-match decisions to train weights against
    -- there isn't a labeled set for that yet, so hand-set weights are the
    honest starting point rather than a fake-precision guess.
    """
    topology = topology or _MYTHROOT_TOPOLOGY
    entity_anchor = topology["entity_anchor"]
    regions = topology["regions"]
    role_keywords = topology["role_keywords"]

    path = Path(rel)
    parts = [p.upper() for p in path.parts]
    stem = path.stem.upper()
    evidence = {}
    entity = None
    region = None
    subregion = None

    if entity_anchor in parts:
        entity = entity_anchor
        evidence["entity"] = {"value": entity, "source": "path", "confidence": 1.0}
        i = parts.index(entity_anchor)
        if i + 1 < len(parts) and parts[i + 1] in regions:
            region = parts[i + 1]
            evidence["region"] = {"value": region, "source": "path", "confidence": 1.0}
            if i + 2 < len(parts) and parts[i + 2] != path.name.upper():
                subregion = parts[i + 2]
                evidence["subregion"] = {"value": subregion, "source": "path", "confidence": 0.9}

    subject = normalize_name(re.sub(r"_V\d+(?:\.\d+)?$", "", stem))
    evidence["subject"] = {"value": subject, "source": "filename", "confidence": 0.6}

    role = None
    for keyword, role_value in role_keywords:
        if keyword in stem:
            role = role_value
            evidence["role"] = {"value": role, "source": "filename", "confidence": 0.55}
            break
    if role is None:
        role = subject
        evidence["role"] = {"value": role, "source": "inferred", "confidence": 0.3}
    purpose = role

    front = _front_context(root / path)
    if front.get("region"):
        fr = front["region"].upper()
        if fr in regions:
            prior = evidence.get("region")
            if prior and prior["value"] == fr:
                # Path and frontmatter agree -- strongest possible evidence.
                evidence["region"] = {"value": fr, "source": "path+frontmatter", "confidence": 1.0}
            else:
                # Frontmatter is the only or overriding source for region.
                # Previously this was parsed by _front_context and then
                # silently discarded -- a declared region never made it
                # into the identity tuple unless the path also encoded it.
                evidence["region"] = {"value": fr, "source": "frontmatter", "confidence": 0.85}
            region = fr
    if front.get("subject"):
        subject = normalize_name(front["subject"])
        evidence["subject"] = {"value": subject, "source": "frontmatter", "confidence": 0.95}
    if front.get("role"):
        role = normalize_name(front["role"])
        evidence["role"] = {"value": role, "source": "frontmatter", "confidence": 0.95}
    if front.get("purpose"):
        purpose = normalize_name(front["purpose"])
        evidence["purpose"] = {"value": purpose, "source": "frontmatter", "confidence": 0.9}

    population = region
    fields = {"entity": entity, "population": population, "region": region, "subregion": subregion,
              "subject": subject, "role": role, "purpose": purpose, "scope": region}

    resolved_confidences = [v["confidence"] for k, v in evidence.items() if fields.get(k) is not None]
    identity_confidence = round(sum(resolved_confidences) / len(resolved_confidences), 3) if resolved_confidences else 0.0

    return {**fields, "identity_confidence": identity_confidence, "identity_evidence": evidence}


# Fields that actually decide whether two documents occupy the same slot.
# subregion, population, and purpose are informational/derived (population
# just mirrors region; purpose just mirrors role unless explicitly declared)
# and are sparse by design -- most real documents never resolve subregion at
# all. Gating on them caused nearly every comparison to land on UNCERTAIN
# regardless of whether the fields that actually matter (region/subject/role)
# were clean matches. Found by testing against a fully-resolved identical
# pair, which should have returned MATCH and instead returned UNCERTAIN
# because of subregion alone.
GATING_FIELDS = (("entity", "entity"), ("region", "region"), ("subject", "subject"), ("role", "document role"))
CONTEXT_FIELDS = (("population", "population"), ("subregion", "subregion"), ("purpose", "purpose"))


def identity_match(left, right):
    """Return (verdict, reasons). verdict is one of MATCH / MISMATCH / UNCERTAIN.

    Semantic similarity is never considered here -- only structural identity
    fields. Previously this returned a bare boolean and treated two
    unresolved fields (both None) as agreement by default, since the
    comparison `a is not None and b is not None and a != b` only fires when
    BOTH sides have a value. That meant two documents that both failed to
    resolve, say, region would silently pass the identity gate as if they
    agreed on region -- an absence was being read as evidence of sameness.

    Now: for the GATING_FIELDS (the ones that actually define "same slot"),
    both resolved and equal counts toward MATCH; both resolved and different
    is a hard MISMATCH; either side unresolved makes that field UNCERTAIN.
    A genuine MISMATCH always wins over UNCERTAIN. CONTEXT_FIELDS are still
    evidence-tracked in the reasons for a mismatch (never silently ignored)
    but do not by themselves push an otherwise-clean match into UNCERTAIN,
    since their absence is normal and expected for most documents.
    """
    reasons = []
    uncertain_fields = []
    for key, label in GATING_FIELDS:
        a = left.get(key)
        b = right.get(key)
        if a is None or b is None:
            uncertain_fields.append(label)
            continue
        if a != b:
            reasons.append(f"{label} mismatch: {a} != {b}")
    for key, label in CONTEXT_FIELDS:
        a = left.get(key)
        b = right.get(key)
        if a is not None and b is not None and a != b:
            reasons.append(f"{label} mismatch: {a} != {b}")
    if reasons:
        return ("MISMATCH", reasons)
    if uncertain_fields:
        return ("UNCERTAIN", [f"identity could not be confirmed for: {', '.join(uncertain_fields)}"])
    return ("MATCH", [])
