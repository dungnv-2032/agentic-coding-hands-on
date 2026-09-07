"""Tests for phase-10 (B4d): `_OLD_BLOCK_HEADING_RE` trailing-annotation tolerance +
restatement-stub classification in `_audience_split_parse_old_blocks_lib.py`.

Why this file exists: `find_old_blocks()`'s heading regex anchored `\\s*$` immediately
after the slug, so any real-corpus heading carrying a trailing parenthetical annotation
(`### INT-001_MessageSentEmailNotification (see Cross-Cutting Logic)`) never matched --
it passed through unmigrated and tripped the v27 `FeatureSpec.legacy_block_heading`
validator post-compose. Separately, `find_old_blocks()` returns EVERY physical occurrence
of a code, including lightweight per-user-story restatement stubs whose body carries no
substantive field at all -- these get spliced to the same canonical heading form as the
real definition and then trip `FeatureSpec.linked_fr_missing` for a field they were never
meant to carry. See plans/260817-1420-rebuild-spec-v27-migrate-legacy-docs/
evidence/critical-taxonomy.md Notes 2 and 6, and phase-10's own file, for the root-cause
evidence (F022_Messaging, F024_Reviews, F026_StripeConnect real-corpus headings).
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _audience_split_parse_old_blocks_lib as old_blocks_lib  # noqa: E402
from _audience_split_parse_old_blocks_lib import find_old_blocks  # noqa: E402


# --------------------------------------------------------------------------------- #
# Regression guard: unannotated old-form blocks must keep parsing exactly as before.
# --------------------------------------------------------------------------------- #
def test_unannotated_canonical_block_still_parses():
    text = (
        "## Cross-Cutting Logic\n\n"
        "### Business Rules\n\n"
        "### BR-001_LoginRequiredForInbox\n"
        "**Linked FR:** FR-001, FR-002\n"
        "**Source:** `app/x.rb:1-2`\n"
        "**Applies to:** all routes\n"
        "**Rule:** must be logged in.\n\n"
        "### Decision Logic\n"
    )
    blocks = find_old_blocks(text)
    assert len(blocks) == 1
    blk = blocks[0]
    assert blk["code"] == "BR-001"
    assert blk["slug"] == "LoginRequiredForInbox"
    assert blk["annotation"] is None
    assert blk["is_restatement"] is False
    assert "**Rule:** must be logged in." in blk["body_text"]


def test_unannotated_dec_block_still_parses_h4():
    text = (
        "#### DEC-001_SkipResponseFormat\n"
        "**subtype:** flow\n"
        "**user_visible_outcome:** user sees a redirect\n"
        "**Source:** `app/y.rb:1-2`\n\n"
        "### State Machines\n"
    )
    blocks = find_old_blocks(text)
    assert len(blocks) == 1
    assert blocks[0]["code"] == "DEC-001"
    assert blocks[0]["level"] == 4
    assert blocks[0]["annotation"] is None


# --------------------------------------------------------------------------------- #
# Fix 1: annotated headings must now be recognized, and the slug must not swallow the
# annotation (real corpus headings from F022_Messaging / F024_Reviews).
# --------------------------------------------------------------------------------- #
def test_annotated_heading_is_recognized_and_slug_not_swallowed():
    text = (
        "### INT-001_MessageSentEmailNotification (see Cross-Cutting Logic)\n"
        "**Linked FR:** —\n\n"
        "### Edge Cases\n"
    )
    blocks = find_old_blocks(text)
    assert len(blocks) == 1
    blk = blocks[0]
    assert blk["code"] == "INT-001"
    # The slug must be exactly the identifier -- the annotation must not leak into it.
    assert blk["slug"] == "MessageSentEmailNotification"
    assert blk["annotation"] == "(see Cross-Cutting Logic)"


def test_annotated_heading_body_already_has_linked_fr_is_not_double_synthesized():
    """F022/F024 shape in isolation (no canonical occurrence of the same code present
    in this snippet): the restatement heading carries the annotation, and its own
    content is JUST a `**Linked FR:** —` placeholder line -- structurally still a
    restatement (Linked FR carries no distinguishing signal, since it is present on
    both shapes). With no canonical to copy from, synthesis falls back to the bare
    placeholder, replacing (not doubling) the redundant own placeholder line."""
    text = (
        "### BR-002_MustBeTransactionParticipant (see Cross-Cutting Logic)\n"
        "**Linked FR:** —\n\n"
        "### BR-003_OnlyOneReviewPerPartyPerTransaction (see Cross-Cutting Logic)\n"
        "**Linked FR:** —\n\n"
        "### Edge Cases\n"
    )
    blocks = find_old_blocks(text)
    assert len(blocks) == 2
    for blk in blocks:
        assert blk["is_restatement"] is True
        assert blk["body_text"].count("**Linked FR:**") == 1


def test_heading_with_non_cross_reference_annotation_still_recognized():
    """The regex must tolerate ANY trailing annotation, not just the literal English
    'see Cross-Cutting Logic' string -- a differently-worded corpus must not silently
    fall back to the old failure mode."""
    text = (
        "### BR-009_SomeNewRule (needs review)\n"
        "**Linked FR:** FR-009\n"
        "**Source:** `app/z.rb:9-9`\n"
        "**Applies to:** everything\n"
        "**Rule:** something.\n\n"
        "### Decision Logic\n"
    )
    blocks = find_old_blocks(text)
    assert len(blocks) == 1
    assert blocks[0]["slug"] == "SomeNewRule"
    assert blocks[0]["annotation"] == "(needs review)"
    # Has a substantive Rule: field -- must NOT be misclassified as a restatement just
    # because it carries a trailing annotation.
    assert blocks[0]["is_restatement"] is False


# --------------------------------------------------------------------------------- #
# Fix 2: restatement stubs (F026_StripeConnect shape) -- body has NO substantive field
# at all, only the italic cross-reference marker. Must be classified as a restatement
# and get a synthesized **Linked FR:** placeholder so the spliced canonical heading
# form doesn't trip FeatureSpec.linked_fr_missing, while PRESERVING (not dropping) the
# original cross-reference line.
# --------------------------------------------------------------------------------- #
def test_fieldless_restatement_stub_is_classified_and_synthesized():
    text = (
        "#### BR-001_StripeMustBeEnabledByCommunity\n"
        "**Linked FR:** FR-003\n"
        "**Source:** `app/a.rb:1-2`\n"
        "**Applies to:** all\n"
        "**Rule:** must be enabled.\n\n"
        "### Decision Logic\n\n"
        "### US097_ConnectStripeAccount\n\n"
        "**Rules enforced:**\n\n"
        "#### BR-001_StripeMustBeEnabledByCommunity\n"
        "*(see Cross-Cutting Logic)*\n\n"
        "#### BR-002_SellerAccountMustExistBeforeRedirect\n"
        "*(see Cross-Cutting Logic)*\n\n"
        "### Edge Cases\n"
    )
    blocks = find_old_blocks(text)
    br001_blocks = [b for b in blocks if b["code"] == "BR-001"]
    assert len(br001_blocks) == 2
    canonical, restatement = br001_blocks[0], br001_blocks[1]

    assert canonical["is_restatement"] is False
    assert "**Linked FR:** FR-003" in canonical["body_text"]

    assert restatement["is_restatement"] is True
    # The synthesized content must satisfy `has_linked_fr` (any value after the label)
    # AND `block_source_missing` (a `**Source:**` line) -- copied from the canonical
    # occurrence found elsewhere in the same document, not invented.
    assert "**Linked FR:** FR-003" in restatement["body_text"]
    assert "**Source:** `app/a.rb:1-2`" in restatement["body_text"]
    # The original cross-reference marker line is PRESERVED, not dropped.
    assert "*(see Cross-Cutting Logic)*" in restatement["body_text"]


def test_restatement_source_line_copied_from_canonical_satisfies_block_source_missing():
    """Real-corpus shape (F022_Messaging/F024_Reviews): the restatement's OWN content
    is just `**Linked FR:** —` (no Source line at all) -- `FeatureSpec.block_source_missing`
    scans EVERY canonical-form heading doc-wide, so this restatement would trip it too
    unless the canonical's Source line is copied forward. The duplicate own Linked FR
    placeholder must be dropped (not doubled) once the real one is copied in."""
    text = (
        "### BR-002_MustBeTransactionParticipant\n"
        "**Linked FR:** FR-002, FR-003\n"
        "**Source:** `app/models/testimonial.rb:12-30`\n"
        "**Applies to:** review submission\n"
        "**Rule:** only a transaction participant may review.\n\n"
        "### Decision Logic\n\n"
        "### US096_WriteTestimonial\n\n"
        "**Rules enforced:**\n\n"
        "### BR-002_MustBeTransactionParticipant (see Cross-Cutting Logic)\n"
        "**Linked FR:** —\n\n"
        "### Edge Cases\n"
    )
    blocks = find_old_blocks(text)
    restatement = [b for b in blocks if b["is_restatement"]][0]
    assert restatement["body_text"].count("**Linked FR:**") == 1
    assert "**Linked FR:** FR-002, FR-003" in restatement["body_text"]
    assert "**Source:** `app/models/testimonial.rb:12-30`" in restatement["body_text"]


def test_restatement_mermaid_fence_copied_from_canonical_satisfies_sm_mermaid():
    """Real-corpus shape (F066_AdminTransactionConfig SM-001): the restatement's own
    content is empty (boundary bleed absorbs unrelated trailing narrative, not a
    stateDiagram-v2 fence) -- `FeatureSpec.sm_mermaid` requires a mermaid fence between
    this heading and the next SM heading (or EOF), doc-wide. The canonical's fence must
    be copied forward so the restatement's spliced heading satisfies it too."""
    text = (
        "#### SM-001_FormSubmitStatus\n"
        "**Linked FR:** FR-001\n"
        "**Source:** `app/models/form.rb:1-2`\n"
        "**States:** `idle`, `submitting`, `done`\n\n"
        "```mermaid\n"
        "stateDiagram-v2\n"
        "  [*] --> idle\n"
        "```\n\n"
        "### Algorithms\n\n"
        "#### SM-001_FormSubmitStatus (see Cross-Cutting Logic)\n\n"
        "**Verification:**\n"
        "- **SC-001** something\n\n"
        "### Edge Cases\n"
    )
    blocks = find_old_blocks(text)
    restatement = [b for b in blocks if b["is_restatement"]][0]
    assert "```mermaid" in restatement["body_text"]
    assert "stateDiagram-v2" in restatement["body_text"]
    # The trailing narrative (not this block's own content) is still preserved.
    assert "**Verification:**" in restatement["body_text"]


def test_restatement_with_no_canonical_elsewhere_falls_back_to_bare_placeholder():
    """Defensive fallback: if no canonical occurrence of the code exists anywhere in
    the document (should not happen in practice -- a restatement backlinks to
    something), synthesis falls back to a bare Linked FR placeholder rather than
    crashing or leaving the field missing."""
    text = (
        "### US001_Foo\n\n"
        "**Rules enforced:**\n\n"
        "#### BR-999_OrphanedRestatement\n"
        "*(see Cross-Cutting Logic)*\n\n"
        "### Edge Cases\n"
    )
    blocks = find_old_blocks(text)
    assert len(blocks) == 1
    assert blocks[0]["is_restatement"] is True
    assert "**Linked FR:**" in blocks[0]["body_text"]
    assert "*(see Cross-Cutting Logic)*" in blocks[0]["body_text"]


def test_restatement_synthesis_only_touches_prefixes_the_validator_checks():
    """DEC blocks are H4-rendered and never matched by BLOCK_HEADING_RE (H3-only), so
    `find_blocks_missing_linked_fr` never checks them -- a fieldless DEC restatement
    must still be classified as a restatement (for callers that want it) but must NOT
    get a synthesized Linked FR line it doesn't need."""
    text = (
        "#### DEC-001_SkipResponseFormat\n"
        "*(see Cross-Cutting Logic)*\n\n"
        "### Edge Cases\n"
    )
    blocks = find_old_blocks(text)
    assert len(blocks) == 1
    assert blocks[0]["is_restatement"] is True
    assert "**Linked FR:**" not in blocks[0]["body_text"]


# --------------------------------------------------------------------------------- #
# Boundary-bleed guard: the LAST restatement in a "Rules enforced:"/"State
# transitions:" list is not followed by another BR/SM/etc heading -- the next real
# heading is further away, past unrelated free-form template narrative
# (`**State transitions:**`, `**Verification:**`). That narrative sits inside
# `find_old_blocks`'s [start, end) window (by design -- it must pass through
# untouched) but must NOT count as "this occurrence's own substantive field" and
# suppress restatement classification (real corpus: F026_StripeConnect BR-005,
# F066_AdminTransactionConfig BR-006 + SM-001).
# --------------------------------------------------------------------------------- #
def test_last_restatement_in_list_not_fooled_by_trailing_narrative():
    text = (
        "### US001_Foo\n\n"
        "**Rules enforced:**\n\n"
        "#### BR-005_LastRuleInList\n"
        "*(see Cross-Cutting Logic)*\n\n"
        "**State transitions:** SM-001 — some transition note.\n\n"
        "**Verification:**\n"
        "- **SC-001** something (covers FR-001)\n\n"
        "### Edge Cases\n"
    )
    blocks = find_old_blocks(text)
    assert len(blocks) == 1
    blk = blocks[0]
    assert blk["is_restatement"] is True
    assert "**Linked FR:**" in blk["body_text"]
    # The trailing narrative must still be preserved byte-for-byte in the body (it is
    # NOT this block's own content, but it must not be dropped either).
    assert "**State transitions:** SM-001" in blk["body_text"]
    assert "**Verification:**" in blk["body_text"]


def test_last_restatement_immediately_followed_by_next_block_heading_no_bleed():
    """The F066 shape where the restatement's own line is blank and the very next
    heading (of the same level) is another restatement -- no narrative in between at
    all, so classification must still see an empty own-paragraph."""
    text = (
        "#### BR-006_AdminOnlyAccess (see Cross-Cutting Logic)\n\n"
        "**State transitions:**\n\n"
        "#### SM-001_FormSubmitStatus (see Cross-Cutting Logic)\n\n"
        "**Verification:**\n"
        "- **SC-001** something\n\n"
        "### Edge Cases\n"
    )
    blocks = find_old_blocks(text)
    assert len(blocks) == 2
    br006, sm001 = blocks[0], blocks[1]
    assert br006["code"] == "BR-006" and br006["is_restatement"] is True
    assert "**Linked FR:**" in br006["body_text"]
    assert sm001["code"] == "SM-001" and sm001["is_restatement"] is True
    assert "**Linked FR:**" in sm001["body_text"]


def test_restatement_flag_is_additive_and_ignorable():
    """Existing keys on the block dict must remain present and unchanged in shape so a
    caller that doesn't know about `is_restatement`/`annotation` keeps working."""
    text = "### BR-001_Foo\n**Rule:** x.\n\n### Decision Logic\n"
    blk = find_old_blocks(text)[0]
    for key in ("code", "prefix", "slug", "level", "start", "end", "body_lines", "body_text"):
        assert key in blk
