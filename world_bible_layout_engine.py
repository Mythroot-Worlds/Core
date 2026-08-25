#!/usr/bin/env python3
"""Canon-status vocabulary shared across CORE tools.

Minimal stub: core_version_diff.py only needs CANON_MARKERS from this module.
The full layout/formatting engine this filename implies does not exist yet --
add it here if/when CORE needs to render or lay out world-bible pages.
"""
from __future__ import annotations

CANON_MARKERS = (
    "LOCKED CANON",
    "FLEXIBLE",
    "PROVISIONAL",
    "OPEN",
    "UNKNOWN",
    "WORKING INFERENCE",
    "RETIRED",
)
