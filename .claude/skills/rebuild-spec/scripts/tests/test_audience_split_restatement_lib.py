"""Direct unit tests for `_audience_split_restatement_lib.py` (phase-10, B4d) --
`is_restatement_body` and `synthesize_restatement_content` in isolation from the heading
regex in `_audience_split_parse_old_blocks_lib.py` (covered by
test_audience_split_parse_old_blocks_legacy_heading.py at the integration level).
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _audience_split_restatement_lib import (  # noqa: E402
    is_restatement_body, synthesize_restatement_content,
)


def _blk(code, prefix, body_text, is_restatement=None):
    body_lines = body_text.splitlines()
    blk = {
        "code": code, "prefix": prefix, "slug": "X", "level": 3,
        "start": 0, "end": len(body_lines) + 1,
        "body_lines": body_lines, "body_text": body_text,
        "annotation": None,
    }
    blk["is_restatement"] = (
        is_restatement_body(body_lines) if is_restatement is None else is_restatement
    )
    return blk


def test_is_restatement_body_true_for_empty_body():
    assert is_restatement_body([]) is True


def test_is_restatement_body_true_for_italic_cross_reference_only():
    assert is_restatement_body(["*(see Cross-Cutting Logic)*"]) is True


def test_is_restatement_body_true_for_bare_linked_fr_placeholder():
    assert is_restatement_body(["**Linked FR:** —"]) is True


def test_is_restatement_body_false_when_any_other_field_present():
    assert is_restatement_body(["**Source:** `a.rb:1-2`"]) is False


def test_synthesize_is_noop_for_non_restatement_blocks():
    canonical = _blk("BR-001", "BR", "**Linked FR:** FR-001\n**Rule:** x.", is_restatement=False)
    before = dict(canonical)
    synthesize_restatement_content([canonical])
    assert canonical["body_text"] == before["body_text"]


def test_synthesize_skips_dec_prefix_even_when_restatement():
    dec = _blk("DEC-001", "DEC", "*(see Cross-Cutting Logic)*", is_restatement=True)
    synthesize_restatement_content([dec])
    assert dec["body_text"] == "*(see Cross-Cutting Logic)*"


def test_synthesize_copies_canonical_body_into_matching_restatement():
    canonical = _blk(
        "BR-001", "BR",
        "**Linked FR:** FR-001\n**Source:** `a.rb:1-2`\n**Rule:** x.",
        is_restatement=False,
    )
    restatement = _blk("BR-001", "BR", "*(see Cross-Cutting Logic)*", is_restatement=True)
    synthesize_restatement_content([canonical, restatement])
    assert "**Source:** `a.rb:1-2`" in restatement["body_text"]
    assert "*(see Cross-Cutting Logic)*" in restatement["body_text"]
    # Canonical itself must be left untouched.
    assert canonical["body_text"] == "**Linked FR:** FR-001\n**Source:** `a.rb:1-2`\n**Rule:** x."


def test_synthesize_falls_back_to_placeholder_when_no_canonical_present():
    orphan = _blk("BR-999", "BR", "*(see Cross-Cutting Logic)*", is_restatement=True)
    synthesize_restatement_content([orphan])
    assert "**Linked FR:**" in orphan["body_text"]
    assert "*(see Cross-Cutting Logic)*" in orphan["body_text"]
