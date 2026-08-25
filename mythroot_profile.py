#!/usr/bin/env python3
"""Mythroot-specific reasoning profile for CORE's ARUUN proving ground.

This profile supplies domain principles; it does not rewrite canon or override evidence.
"""
from __future__ import annotations
MYTHROOT_PROFILE={"name":"Mythroot Worldbuilding","version":"0.1","principles":{"purpose_before_inventory":"Information matters when it changes or supports a worldbuilding decision; completeness is not measured by filling every possible field.","scope_and_scale_matter":"The same subject may legitimately exist at continental, regional, settlement, group, or individual scale.","depth_follows_importance":"Depth should follow story importance, world importance, and intended application rather than uniform detail everywhere.","coherence_is_systemic":"Geography, settlement, economy, politics, law, history, culture, daily life, and ecology can constrain or explain one another.","canon_has_states":"Hard canon, flexible canon, open space, and unknown are different information states.","absence_is_not_automatically_error":"An undocumented area may be intentionally open, genuinely unknown, or actually missing; these states must be distinguished.","relationship_requires_deciding_factors":"A relationship label is justified by the factors that explain why the relationship exists, not by lexical overlap alone.","evidence_has_provenance":"Claims should remain traceable to their source and context.","human_validation_is_authoritative":"CORE may identify, compare, infer, and escalate, but it does not silently alter canon or promote hypotheses to canon."},"decision_factors":{"subject":"What is actually being described?","scope":"Where and at what breadth does the information apply?","scale":"At what world/story level does it operate?","function":"Why does this document or passage exist?","depth":"Is the treatment deep enough for its intended importance and use?","canon_status":"Is the claim established, flexible, open, or unknown?","importance":"How consequential is this information to the world or its intended use?","development_state":"Is it developed, partial, intentionally open, or genuinely unresolved?","relationship":"What relationship is actually supported between the compared information objects?","dependency":"What does this information rely upon or inform?","consequence":"What other systems or decisions does it affect?","provenance":"Where did the claim originate and what version/status does it have?","intentionality":"Is an apparent absence deliberate or a documentation gap?","coherence":"Does it fit the surrounding world systems?","usability":"Can another creator use the information correctly?","story_relevance":"Does the information generate meaningful creative consequences?"}}
RELATIONSHIP_GATES={"VARIANT":("same underlying subject","meaningful scope/context difference","functional continuity"),"SUPPORTING":("one source supplies context/evidence needed by another","complementary function","traceable support relationship"),"HISTORICAL":("related subject","temporal distinction","evidence of precedence/revision/state change"),"CONFLICT":("comparable subject/scope","incompatible claims","conflict survives contextual explanation"),"MISPLACED":("information is relevant somewhere","current document/scope is not the appropriate home","a more appropriate placement exists"),"DUPLICATE":("same substantive information","no meaningful scope/function distinction","no additional contextual value"),"RELATED":("meaningful connection","no stronger relationship gate established")}

# WORLD_TOPOLOGY is the Mythroot/ARUUN-specific vocabulary that core_identity_resolver.py
# needs to place a document structurally (entity anchor, known regions, filename->role
# keywords). This is exactly the kind of "Mythroot canon" the README says should be
# configuration consumed by the engine, not hardcoded inside it. A future non-ARUUN
# profile would supply its own WORLD_TOPOLOGY with different values; the shape
# (entity_anchor / regions / role_keywords) is the only part the engine assumes.
WORLD_TOPOLOGY={
    "entity_anchor":"HEARTH",
    "regions":{"HEARTH","PLAINS","MOUNTAINS","RIVER","WETLANDS","DESERT","COAST"},
    # Ordered; first keyword found in the filename stem wins. Mirrors the prior
    # inline if/elif chain in core_identity_resolver.py so behavior is unchanged,
    # just relocated.
    "role_keywords":(
        ("SPECIALIST_HOUSES","specialist_houses"),
        ("SPECIALIST_LINEAGES","specialist_lineages"),
        ("GOVERNANCE","governance_authority"),
        ("PARTNERSHIP","family_partnership"),
        ("BIRTH_CHILDHOOD","family_birth_childhood"),
        ("AUDIT","audit_support"),
        ("CHECKLIST","audit_support"),
    ),
}

def profile_snapshot():return {"name":MYTHROOT_PROFILE["name"],"version":MYTHROOT_PROFILE["version"],"principles":MYTHROOT_PROFILE["principles"],"decision_factors":MYTHROOT_PROFILE["decision_factors"],"relationship_gates":RELATIONSHIP_GATES}
def topology_snapshot():return WORLD_TOPOLOGY
