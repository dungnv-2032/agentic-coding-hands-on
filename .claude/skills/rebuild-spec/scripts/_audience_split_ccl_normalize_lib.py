"""Mode A -- `## Cross-Cutting Logic` H3 backfill + provenance stamp for the
reshaped `technical-spec.md` (phase-04, B4b). Split out of
`_audience_split_compose_a_lib.py` to keep each module under the repo's
200-line guidance; `render_technical_spec` calls `normalize_ccl` then
`stamp_frontmatter`, strictly after its own heading-splice loop.

Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _spec_parse import parse_headings_and_blocks  # noqa: E402

_CCL_H2 = "## Cross-Cutting Logic"

# v27.x (P09, D7 -- plans/260818-1332-rebuild-spec-human-readable-sot/plan.md
# "Orchestrator decisions"): this module is the G1->G2 hop for FEATURE specs
# (v26 old-shape -> v27.0 intermediate), symmetric with `_audience_split_mode_c_lib.py`
# for SCREEN specs. It is NOT dead code and NOT retired alongside the retaxonomy --
# `_spec_constants.REQUIRED_CCL_H3` was deleted by P08 because the CURRENT target
# shape (technical-spec.md's 5-bucket retaxonomy) has no `## Cross-Cutting Logic`
# H2 at all. This composer does not target the current shape -- it targets the
# v27.0 INTERMEDIATE shape, which still legitimately has one, and which the second
# hop (`compose_technical_sot`, P10) then carries forward into the 5-bucket shape.
# `LEGACY_CCL_H3` is that v27.0 intermediate's own H3 list, frozen here as this
# composer's own historical constant -- deliberately NOT the current target shape,
# and deliberately never migrated to point at `REQUIRED_SYSDESIGN_H3`/
# `REQUIRED_VERIF_H3`. Re-pointing this composer at the new shape would collapse
# the two migration hops into one and give v26 and v27.0 repos different targets,
# the exact drift the plan's single-composer rule exists to prevent.
LEGACY_CCL_H3 = [
    "### Requirements",
    "### Business Rules",
    "### Decision Logic",
    "### State Machines",
    "### Algorithms",
    "### External Integrations",
    "### Verification",
]


def _h2_bounds(lines: list[str], name: str) -> tuple[int, int] | None:
    """Body bounds `[start, end)` of H2 *name* -- start is the line right after the
    heading, end is the next H2 (or `len(lines)`). Recomputed locally (rather than
    imported from the validator) so this module carries no runtime dependency on
    `validate_feature_spec.py`; the contract mirrors its own `_bounds` helper."""
    headings, _ = parse_headings_and_blocks(lines)
    h2 = [(i, h) for i, h in headings if h.startswith("## ") and not h.startswith("### ")]
    for i, (idx, h) in enumerate(h2):
        if h == name:
            return idx + 1, (h2[i + 1][0] if i + 1 < len(h2) else len(lines))
    return None


def _ensure_ccl_h3(lines: list[str], heading: str) -> list[str]:
    """*heading* is a full `LEGACY_CCL_H3` entry (e.g. `'### Business Rules'`).
    Backfill a `None.` body if it is blank; insert heading + `None.` at the correct
    ordinal position if it is missing outright. See `normalize_ccl` for what "blank"
    means and why this must run after the heading splice."""
    b_ccl = _h2_bounds(lines, _CCL_H2)
    if b_ccl is None:
        return lines  # no Cross-Cutting Logic section at all -- nothing to normalize
    headings, _ = parse_headings_and_blocks(lines)
    h3 = [(i, h) for i, h in headings if b_ccl[0] <= i < b_ccl[1] and h.startswith("### ")]
    names = [h for _, h in h3]
    if heading in names:
        pos = names.index(heading)
        start = h3[pos][0]
        end = h3[pos + 1][0] if pos + 1 < len(h3) else b_ccl[1]
        if "\n".join(lines[start + 1:end]).strip():
            return lines  # already has content (or already `None.`) -- untouched
        out = list(lines)
        out[start + 1:end] = ["", "None.", ""]
        return out
    # Missing outright -- insert right before the first OTHER required container that
    # canonically follows it; if none of those are present either, at the section end.
    order = LEGACY_CCL_H3.index(heading)
    insert_at = b_ccl[1]
    for idx, h in h3:
        if h in LEGACY_CCL_H3 and LEGACY_CCL_H3.index(h) > order:
            insert_at = idx
            break
    out = list(lines)
    out[insert_at:insert_at] = [heading, "", "None.", ""]
    return out


def normalize_ccl(lines: list[str]) -> list[str]:
    """Ensure every `LEGACY_CCL_H3` container heading inside `## Cross-Cutting
    Logic` has a non-blank immediate body.

    Splicing a BR/SM/ALG/INT block (see `render_technical_spec`) promotes its heading
    to the SAME `###` level as its own parent container -- that promotion is exactly
    why the parent goes blank: its former child is now a sibling H3, not its body
    anymore. "Blank" is defined identically to the validator's own `ccl_blank` check
    (`validate_feature_spec.py` -- whitespace-only content strictly between the
    container heading and whatever H3-level heading comes next, whether that is a
    promoted sibling block heading or another required container; NOT comment-aware,
    matching the actual pass/fail gate byte-for-byte). Idempotent: a body that
    already has content -- including a prior `None.` backfill -- is left alone. Runs
    strictly after the heading splice, on the already-spliced line list, so the
    splice loop's bottom-up index arithmetic is unaffected."""
    lines = list(lines)
    for heading in LEGACY_CCL_H3:
        lines = _ensure_ccl_h3(lines, heading)
    return lines


def stamp_frontmatter(text: str) -> str:
    """Prepend `authored_by: rebuild-spec` frontmatter at byte 0 if *text* does not
    already open with one -- brings `technical-spec.md` to the same provenance
    parity `functional-spec.md` already has (`render_functional_spec`). A migrated
    corpus then resolves CLEAN via `authored_by:` on re-probe instead of relying on
    `CLEAN_LEGACY` markers forever (closes B1 for good)."""
    if text.startswith("---"):
        return text
    return "---\nauthored_by: rebuild-spec\n---\n" + text
