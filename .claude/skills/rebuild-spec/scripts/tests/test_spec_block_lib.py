"""Tests for scripts/_spec_block_lib.py.

v27.0.0: heading form changed from `### BR-001_NameSlug` (anchored prefix) to
`### {plain sentence} (BR-001)` (trailing tag). DEC blocks are H4 and follow the same
trailing-tag shape: `#### {plain sentence} (DEC-001)`.
"""
from pathlib import Path
import sys

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _spec_block_lib import (
    LEGACY_BLOCK_HEADING_RE, find_blocks, has_linked_fr, find_blocks_missing_linked_fr,
)


class TestBlockBoundaryDetection:
    def test_finds_br_block(self):
        text = "### Some rule about order minimums (BR-001)\nsome content\n"
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["prefix"] == "BR"
        assert blocks[0]["code"] == "BR-001"

    def test_finds_sm_block(self):
        text = "### The order lifecycle state machine (SM-001)\nsome content\n"
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["prefix"] == "SM"

    def test_finds_alg_block(self):
        text = "### Pricing calculation algorithm (ALG-001)\nsome content\n"
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["prefix"] == "ALG"

    def test_finds_int_block(self):
        text = "### Payment gateway integration (INT-001)\nsome content\n"
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["prefix"] == "INT"

    def test_block_end_is_next_h3(self):
        text = (
            "### First rule (BR-001)\nline a\nline b\n"
            "### Second rule (BR-002)\nline c\n"
        )
        blocks = find_blocks(text)
        assert len(blocks) == 2
        # First block ends where second begins
        assert blocks[0]["block_end"] == blocks[1]["heading_line"]

    def test_last_block_end_is_total_lines(self):
        text = "### The only rule (BR-001)\nline a\nline b\n"
        blocks = find_blocks(text)
        assert blocks[0]["block_end"] == len(text.splitlines())

    def test_heading_line_zero_based(self):
        text = "preamble\n### A rule (BR-001)\ncontent\n"
        blocks = find_blocks(text)
        assert blocks[0]["heading_line"] == 1

    def test_ignores_non_block_headings(self):
        text = "## Overview\nsome text\n### Not A Block\nmore text\n"
        blocks = find_blocks(text)
        assert len(blocks) == 0

    def test_ignores_old_heading_form(self):
        """v27.0.0: the retired '### BR-001_NameSlug' form no longer counts as a block —
        LEGACY_BLOCK_HEADING_RE is the dedicated detector for that shape instead."""
        text = "### BR-001_OrderMinItems\nsome content\n"
        blocks = find_blocks(text)
        assert len(blocks) == 0

    def test_skips_block_heading_inside_backtick_fence(self):
        text = (
            "Some intro\n"
            "```\n"
            "### Rule inside fence (BR-001)\n"
            "content inside fence\n"
            "```\n"
            "### Rule outside fence (BR-002)\nreal content\n"
        )
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["code"] == "BR-002"

    def test_skips_block_heading_inside_tilde_fence(self):
        text = (
            "~~~\n"
            "### Integration inside tilde (INT-001)\n"
            "code here\n"
            "~~~\n"
            "### State machine outside (SM-001)\ncontent\n"
        )
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["code"] == "SM-001"

    def test_fence_with_language_tag_is_skipped(self):
        text = (
            "```markdown\n"
            "### Algorithm example (ALG-001)\ncode\n"
            "```\n"
            "### Real rule (BR-001)\nreal block\n"
        )
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["code"] == "BR-001"

    def test_matches_heading_with_extra_parens_in_sentence(self):
        """The trailing-tag regex must anchor on the LAST parenthesized code at end of
        line, even when the plain-language sentence itself contains parens."""
        text = "### Handle two-factor (TOTP) verification (BR-001)\nsome content\n"
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["code"] == "BR-001"


class TestHasLinkedFr:
    def test_returns_true_when_linked_fr_present(self):
        text = "### A rule (BR-001)\n**Linked FR:** FR-001\nmore content\n"
        blocks = find_blocks(text)
        assert has_linked_fr(text, blocks[0]["heading_line"], blocks[0]["block_end"])

    def test_returns_false_when_linked_fr_absent(self):
        text = "### A rule (BR-001)\nsome content without linked fr\n"
        blocks = find_blocks(text)
        assert not has_linked_fr(text, blocks[0]["heading_line"], blocks[0]["block_end"])

    def test_does_not_cross_block_boundary(self):
        # Linked FR in second block should not count for first
        text = (
            "### First rule (BR-001)\nno linked fr here\n"
            "### Second rule (BR-002)\n**Linked FR:** FR-002\n"
        )
        blocks = find_blocks(text)
        assert not has_linked_fr(text, blocks[0]["heading_line"], blocks[0]["block_end"])
        assert has_linked_fr(text, blocks[1]["heading_line"], blocks[1]["block_end"])


class TestFindBlocksMissingLinkedFr:
    def test_returns_missing_blocks(self):
        text = "### A rule (BR-001)\nno linked fr\n"
        missing = find_blocks_missing_linked_fr(text)
        assert len(missing) == 1
        assert missing[0]["code"] == "BR-001"

    def test_skips_blocks_with_linked_fr(self):
        text = "### A rule (BR-001)\n**Linked FR:** FR-001\ncontent\n"
        missing = find_blocks_missing_linked_fr(text)
        assert len(missing) == 0

    def test_multi_block_partial_missing(self):
        text = (
            "### Rule with it (BR-001)\n**Linked FR:** FR-001\ncontent\n"
            "### Rule missing it (BR-002)\nno linked fr\n"
        )
        missing = find_blocks_missing_linked_fr(text)
        assert len(missing) == 1
        assert missing[0]["code"] == "BR-002"

    def test_empty_file_returns_empty_list(self):
        assert find_blocks_missing_linked_fr("") == []

    def test_multi_block_all_missing(self):
        text = (
            "### Rule A (BR-001)\ncontent a\n"
            "### State machine A (SM-001)\ncontent b\n"
            "### Calc A (ALG-001)\ncontent c\n"
        )
        missing = find_blocks_missing_linked_fr(text)
        assert len(missing) == 3


class TestLegacyBlockHeadingRe:
    """LEGACY_BLOCK_HEADING_RE recognizes the retired '### CODE-NNN_Slug' form so
    validate_feature_spec.py can reject it explicitly instead of silently ignoring it."""

    def test_matches_old_br_heading(self):
        assert LEGACY_BLOCK_HEADING_RE.match("### BR-001_MaxLoginAttempts")

    def test_matches_old_sm_heading(self):
        assert LEGACY_BLOCK_HEADING_RE.match("### SM-001_SessionLifecycle")

    def test_matches_old_alg_heading(self):
        assert LEGACY_BLOCK_HEADING_RE.match("### ALG-001_PricingCalc")

    def test_matches_old_int_heading(self):
        assert LEGACY_BLOCK_HEADING_RE.match("### INT-001_PaymentGateway")

    def test_matches_old_dec_heading_h4(self):
        assert LEGACY_BLOCK_HEADING_RE.match("#### DEC-001_LoginRedirect")

    def test_does_not_match_new_form(self):
        assert not LEGACY_BLOCK_HEADING_RE.match("### Max login attempts rule (BR-001)")

    def test_does_not_match_unrelated_heading(self):
        assert not LEGACY_BLOCK_HEADING_RE.match("### Overview")
