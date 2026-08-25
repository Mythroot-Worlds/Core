#!/usr/bin/env python3
"""CORE Version Diff: compare two candidate files for the same canon slot.

Point this at two files that might be duplicate/competing versions of the
same subject (e.g. an old flat file and a newer regional file, or a v1/v2
draft pair). It answers three questions:

  1. What's confirmed in both (safe either way)?
  2. What's only in one side (possible missing, extra, or outdated info)?
  3. For anything only-in-one-side: does the REST of canon already say the
     same thing elsewhere? If so, dropping it silently loses established
     canon, not just an internal disagreement between these two files.

This never edits or merges anything. It produces a read-only report so a
human makes the final call on which file becomes the single canonical file.

Reuses the existing extraction/comparison primitives rather than
reimplementing them:
  - core_information_units.units()      -> per-file information units
  - core_semantic_comparator.best_coverage() / tokens() -> matching
  - world_bible_layout_engine.CANON_MARKERS -> correct, current canon-status
    vocabulary (LOCKED CANON / FLEXIBLE / PROVISIONAL / OPEN / UNKNOWN /
    WORKING INFERENCE / RETIRED). core_oracle.py's canonical_status() checks
    for the pre-v1.5 term "HARD CANON", which no longer appears in active
    content, so it is NOT used here.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

from core_information_units import units as extract_units
from core_semantic_comparator import best_coverage, tokens
from world_bible_layout_engine import CANON_MARKERS

SKIP = {".git", ".github", "node_modules", "__pycache__"}
ARCHIVE = "07_ARCHIVE/"
REPORTS = "TOOLS/REPOSITORY/REPORTS/"
DEFAULT_THRESHOLD = 0.72


def canon_markers_in(body: str):
    u = body.upper()
    return [m for m in CANON_MARKERS if m in u]


def load_corpus_units(root: Path, scope: Path, exclude: set[str]):
    """Extract information units for the rest of canon under `scope`,
    excluding the two files being compared and non-canon directories."""
    out = []
    for p in scope.rglob("*.md"):
        if any(x in SKIP for x in p.parts):
            continue
        rel = p.relative_to(root).as_posix()
        if rel in exclude or rel.startswith(REPORTS) or rel.startswith(ARCHIVE):
            continue
        out.extend(extract_units(p, root))
    return out


def corroboration(unit_text: str, corpus_units: list[dict], threshold=DEFAULT_THRESHOLD):
    """Does the rest of canon already assert this? Returns best match or None."""
    ut = tokens(unit_text)
    if not ut or not corpus_units:
        return None
    best = (0.0, None)
    for cu in corpus_units:
        score = len(ut & tokens(cu.get("text", ""))) / len(ut | tokens(cu.get("text", ""))) if (ut or tokens(cu.get("text", ""))) else 0.0
        if score > best[0]:
            best = (score, cu)
    if best[0] >= threshold and best[1] is not None:
        return {"path": best[1]["source"], "line": best[1]["line"], "score": round(best[0], 4), "text": best[1]["text"]}
    return None


def side_only(source_units, other_units, threshold, corpus_units):
    """Units in `source_units` with no adequate match in `other_units`,
    each checked against the rest of canon for corroboration."""
    _, alignments = best_coverage(source_units, other_units)
    out = []
    for a in alignments:
        if a["score"] < threshold:
            corrob = corroboration(a["a"], corpus_units, threshold)
            out.append({
                "text": a["a"],
                "best_internal_match_score": a["score"],
                "corroborated_elsewhere_in_canon": corrob,
            })
    return out


def confirmed_both(source_units, other_units, threshold):
    _, alignments = best_coverage(source_units, other_units)
    return [{"left_text": a["a"], "right_text": a["b"], "score": a["score"]} for a in alignments if a["score"] >= threshold]


def contradiction_check(left_units, right_units, threshold):
    NEG = {"not", "never", "no", "without", "cannot"}
    flags = []
    _, alignments = best_coverage(left_units, right_units)
    for a in alignments:
        if a["score"] >= threshold * 0.85:  # near-alignment on same topic
            pa = NEG & tokens(a["a"]); pb = NEG & tokens(a["b"])
            if pa != pb:
                flags.append({"left": a["a"], "right": a["b"], "score": a["score"]})
    return flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--left", required=True, help="First candidate file, repo-relative or absolute")
    ap.add_argument("--right", required=True, help="Second candidate file, repo-relative or absolute")
    ap.add_argument("--canon-scope", default=None, help="Directory to search for corroborating canon (default: shared parent domain of the two files)")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--out", default="TOOLS/REPOSITORY/REPORTS")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    def resolve(p):
        p = Path(p)
        return p if p.is_absolute() else (root / p)

    left_path, right_path = resolve(a.left), resolve(a.right)
    left_rel = left_path.relative_to(root).as_posix()
    right_rel = right_path.relative_to(root).as_posix()

    left_units = extract_units(left_path, root)
    right_units = extract_units(right_path, root)

    if a.canon_scope:
        scope = resolve(a.canon_scope)
    else:
        # Shared parent directory of both files, walked up until it differs.
        lp, rp = left_path.parts, right_path.parts
        i = 0
        while i < min(len(lp), len(rp)) and lp[i] == rp[i]:
            i += 1
        scope = Path(*lp[:i]) if i else root

    corpus_units = load_corpus_units(root, scope, {left_rel, right_rel})

    threshold = a.threshold
    confirmed = confirmed_both(left_units, right_units, threshold)
    left_only = side_only(left_units, right_units, threshold, corpus_units)
    right_only = side_only(right_units, left_units, threshold, corpus_units)
    contradictions = contradiction_check(left_units, right_units, threshold)

    left_status = canon_markers_in(left_path.read_text(encoding="utf-8", errors="replace"))
    right_status = canon_markers_in(right_path.read_text(encoding="utf-8", errors="replace"))

    left_corrob_count = sum(1 for x in left_only if x["corroborated_elsewhere_in_canon"])
    right_corrob_count = sum(1 for x in right_only if x["corroborated_elsewhere_in_canon"])

    if contradictions:
        recommendation = "CONTRADICTIONS found — do not auto-merge. Resolve conflicting statements first."
    elif left_corrob_count == 0 and right_corrob_count == 0:
        recommendation = "No unmatched content is corroborated elsewhere in canon. Either file is likely safe as the sole canonical file; the unmatched items are just wording/detail differences to review by eye."
    else:
        parts = []
        if left_corrob_count:
            parts.append(f"{left_corrob_count} item(s) only in LEFT are independently confirmed elsewhere in canon — dropping LEFT would silently lose established canon")
        if right_corrob_count:
            parts.append(f"{right_corrob_count} item(s) only in RIGHT are independently confirmed elsewhere in canon — dropping RIGHT would silently lose established canon")
        recommendation = "; ".join(parts) + ". Recommend restoring those specific items into whichever file you keep, rather than picking one file wholesale."

    result = {
        "engine": "CORE Version Diff",
        "mode": "READ_ONLY",
        "left": {"path": left_rel, "canon_markers": left_status, "information_units": len(left_units)},
        "right": {"path": right_rel, "canon_markers": right_status, "information_units": len(right_units)},
        "canon_scope_searched": scope.relative_to(root).as_posix() if scope != root else "ALL_ACTIVE_NON_GENERATED_CONTENT",
        "corpus_units_checked": len(corpus_units),
        "threshold": threshold,
        "confirmed_in_both": confirmed,
        "only_in_left": left_only,
        "only_in_right": right_only,
        "contradictions": contradictions,
        "recommendation": recommendation,
        "safety": {"automatic_merge": False, "automatic_canon_change": False, "human_decision_required": True},
    }

    out_dir = root / a.out
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "CORE_VERSION_DIFF.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    md = [f"# CORE Version Diff: `{left_rel}` vs `{right_rel}`", "", "**Mode:** READ-ONLY — no files were changed.", ""]
    md.append(f"- LEFT canon markers: {left_status or 'none found'}")
    md.append(f"- RIGHT canon markers: {right_status or 'none found'}")
    md.append(f"- Canon scope searched for corroboration: `{result['canon_scope_searched']}` ({len(corpus_units)} information units checked)")
    md.append("")
    md.append(f"## Recommendation\n\n{recommendation}\n")
    md.append(f"## Confirmed in both ({len(confirmed)})")
    for c in confirmed:
        md.append(f"- \"{c['left_text'][:100]}...\" (match {c['score']})")
    md.append(f"\n## Only in LEFT — `{left_rel}` ({len(left_only)})")
    for x in left_only:
        tag = f"⚠ CORROBORATED elsewhere: `{x['corroborated_elsewhere_in_canon']['path']}`" if x["corroborated_elsewhere_in_canon"] else "not found elsewhere in scanned canon"
        md.append(f"- \"{x['text'][:140]}\" — {tag}")
    md.append(f"\n## Only in RIGHT — `{right_rel}` ({len(right_only)})")
    for x in right_only:
        tag = f"⚠ CORROBORATED elsewhere: `{x['corroborated_elsewhere_in_canon']['path']}`" if x["corroborated_elsewhere_in_canon"] else "not found elsewhere in scanned canon"
        md.append(f"- \"{x['text'][:140]}\" — {tag}")
    if contradictions:
        md.append(f"\n## Contradictions ({len(contradictions)})")
        for c in contradictions:
            md.append(f"- LEFT: \"{c['left'][:100]}\"\n  RIGHT: \"{c['right'][:100]}\"")
    (out_dir / "CORE_VERSION_DIFF.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Confirmed in both: {len(confirmed)} | Only in left: {len(left_only)} ({left_corrob_count} corroborated) | Only in right: {len(right_only)} ({right_corrob_count} corroborated) | Contradictions: {len(contradictions)}")


if __name__ == "__main__":
    main()
