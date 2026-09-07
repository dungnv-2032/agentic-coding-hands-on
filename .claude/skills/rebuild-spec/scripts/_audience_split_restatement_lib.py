"""Restatement classification + content synthesis for `_audience_split_parse_old_blocks_lib.py`'s
`find_old_blocks()` -- split out to keep that module under the repo's 200-line guidance
(phase-10, B4d).

A v26 `technical-spec.md` can restate a CCL (Cross-Cutting Logic) block's heading a
second time, per-user-story, as a lightweight backlink (`technical-spec-template.md`'s
older per-US shape) -- its own content carries no bold `**Field:**` line at all (aside
from `**Linked FR:**`, which one real-corpus shape carries as a bare `--` placeholder on
BOTH the canonical and the restatement, so it is not distinguishing). This is the
structural test; it does not depend on any particular English wording (a heading
annotation like `(see Cross-Cutting Logic)`, when present, only corroborates it).

Once `find_old_blocks()` recognizes a restatement heading, the (unowned) renderer
splices it into the IDENTICAL canonical trailing-tag heading form as a real definition --
and every per-occurrence structural check the validator runs
(`FeatureSpec.linked_fr_missing`, `FeatureSpec.block_source_missing`,
`FeatureSpec.sm_mermaid`; none of them CCL-scoped, none of them ours to change, none of
them aware a restatement even exists as a concept) then demands fields a lightweight
backlink was never meant to carry. Chasing each one field-by-field is a whack-a-mole
against a validator this module doesn't own and can't predict the next addition to.
Instead, when a genuinely-canonical occurrence of the same code exists elsewhere in the
same document, `synthesize_restatement_content()` copies that occurrence's own content in
front of the restatement's own (preserved, never dropped) content -- honest (same rule,
same implementation facts, restated, not invented) and durable against any future
per-occurrence check the validator grows, not just the ones known today. Only when no
canonical occurrence can be found (defensive fallback) does it fall back to a bare
`**Linked FR:** -- ...` placeholder, mirroring an existing convention already used
elsewhere in this skill (`migrate-feature-screen-ids.py`'s unresolved-SCR placeholder) and
already present in this exact corpus for one restatement shape.
"""
from __future__ import annotations

import re

# A canonical block ALWAYS carries at least one bold `**Field:**` line OTHER than
# Linked FR (Source, Rule, Description, Type, ...) -- see the module docstring for why
# Linked FR itself is excluded from this test.
_SUBSTANTIVE_FIELD_RE = re.compile(r"^\*\*(?!Linked FR:\*\*)[^*\n]+:\*\*", re.MULTILINE)
_LINKED_FR_FIELD_RE = re.compile(r"^\*\*Linked FR:\*\*", re.MULTILINE)
# Prefixes `FeatureSpec.linked_fr_missing` / `.block_source_missing` / `.sm_mermaid`
# actually check (all H3-only in validate_feature_spec.py / _spec_block_lib.py) -- DEC
# always renders H4, so it is never in scope for any of them.
LINKED_FR_REQUIRED_PREFIXES = frozenset({"BR", "SM", "ALG", "INT"})
_RESTATEMENT_LINKED_FR_PLACEHOLDER = "**Linked FR:** — (see Cross-Cutting Logic above)"


def _own_paragraph(body_lines: list[str]) -> str:
    """The lines belonging to THIS heading's own content -- up to (not including) the
    first blank line. `find_old_blocks`'s [start, end) window is bounded by the next
    heading of level <= this one's, which for the LAST restatement in a per-US
    "Rules enforced:"/"State transitions:" list can legitimately extend past unrelated
    free-form template narrative (`**State transitions:**`, `**Verification:**`) that
    sits between this heading and the next one. That narrative is not this occurrence's
    own content and must not count toward the substantive-field test -- every real block
    body in this corpus (canonical or restatement) starts its own content on the line
    immediately after the heading, with no blank line first."""
    own: list[str] = []
    for ln in body_lines:
        if not ln.strip():
            break
        own.append(ln)
    return "\n".join(own)


def is_restatement_body(body_lines: list[str]) -> bool:
    """True when this heading's own paragraph carries no bold `**Field:**` line at all
    -- the structural signature of a per-user-story restatement stub rather than a
    canonical CCL definition."""
    return not _SUBSTANTIVE_FIELD_RE.search(_own_paragraph(body_lines))


def synthesize_restatement_content(blocks: list[dict]) -> None:
    """Mutate restatement blocks in place so the canonical-form heading they get
    spliced into satisfies every per-occurrence structural check the validator runs for
    their prefix -- see the module docstring for why this copies the canonical
    occurrence's content rather than chasing individual fields. `blocks` is the list
    `find_old_blocks()` is building, each already carrying `is_restatement`."""
    canonical_body: dict[str, list[str]] = {}
    for blk in blocks:
        if not blk["is_restatement"] and blk["code"] not in canonical_body:
            canonical_body[blk["code"]] = blk["body_lines"]

    for blk in blocks:
        if not blk["is_restatement"] or blk["prefix"] not in LINKED_FR_REQUIRED_PREFIXES:
            continue
        source = canonical_body.get(blk["code"])
        synthesized = list(source) if source else [_RESTATEMENT_LINKED_FR_PLACEHOLDER]
        # Preserve the restatement's own content -- prepend, never replace or drop it --
        # except its own `**Linked FR:**` line (one real-corpus shape carries a bare
        # `--` placeholder there), which would otherwise duplicate the one the
        # synthesized content above already supplies.
        own = [ln for ln in blk["body_lines"] if not _LINKED_FR_FIELD_RE.match(ln)]
        blk["body_lines"] = synthesized + [""] + own
        blk["body_text"] = "\n".join(blk["body_lines"])
