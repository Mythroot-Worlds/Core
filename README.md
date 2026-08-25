# CORE

CORE is the general-purpose investigation, evidence, identity, semantic comparison, provenance, and human-adjudication engine being developed by Mythroot Worlds.

This repository is the standalone home of CORE. Mythroot-specific worldbuilding rules and canon remain in ARUUN; CORE should consume those as configuration/profile inputs rather than treating Mythroot canon as part of the engine.

## Origin

The initial implementation is being separated from the ARUUN repository so CORE can evolve independently while ARUUN remains a Mythroot implementation and test environment.

## Current architecture

- Identity before semantic comparison
- Layered evidence and cross-checking
- Batman: investigation/detection
- Robin: semantic/syntax relationship analysis
- Oracle: read-only information and provenance relay
- Nightwing: independent reconstruction/cross-check
- Alfred: mediation and human-review boundary
- Existing execution remains sequential for now; an opportunistic blackboard controller is future work.
