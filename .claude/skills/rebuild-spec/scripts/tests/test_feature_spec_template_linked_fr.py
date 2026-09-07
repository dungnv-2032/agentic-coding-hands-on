"""Snapshot test: feature-spec-template.md SM/ALG/INT blocks contain **Linked FR:** line.

v27.0.0: heading form changed from an anchored prefix (`### BR-001_NameSlug`) to a
trailing tag on a plain-language sentence (`### {plain sentence} (BR-001)`).

rebuild-spec 27.7.0 (action-thread reshape): BR is no longer a heading-shaped block at
all — see `TestFeatureSpecTemplateLinkedFr.test_br_no_longer_a_heading_block` for the
retirement note. SM/ALG/INT are unaffected (still H3, still carry **Linked FR:**).
"""
import re
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
TEMPLATE = TEMPLATES_DIR / "technical-spec-template.md"

BLOCK_HEADING_RE = re.compile(r"^### .+\((BR|SM|ALG|INT)-\d{3}\)\s*$", re.MULTILINE)
LINKED_FR_RE = re.compile(r"^\*\*Linked FR:\*\*", re.MULTILINE)


def _block_code(heading: str) -> str:
    """Extract the trailing `(PREFIX-NNN)` tag, e.g. 'BR-001', from a block heading."""
    m = re.search(r"\((BR|SM|ALG|INT)-(\d{3})\)\s*$", heading)
    return f"{m.group(1)}-{m.group(2)}" if m else ""


def _blocks_with_linked_fr(content: str) -> dict[str, bool]:
    """Return {heading: has_linked_fr} for every BR/SM/ALG/INT block."""
    lines = content.splitlines()
    total = len(lines)
    results: dict[str, bool] = {}

    headings: list[tuple[int, str]] = [
        (i, ln) for i, ln in enumerate(lines)
        if BLOCK_HEADING_RE.match(ln)
    ]

    for idx, (line_no, heading) in enumerate(headings):
        end = headings[idx + 1][0] if idx + 1 < len(headings) else total
        block_lines = lines[line_no + 1: end]
        has_it = any(LINKED_FR_RE.match(bl) for bl in block_lines)
        results[heading] = has_it

    return results


class TestFeatureSpecTemplateLinkedFr:
    def _content(self) -> str:
        return TEMPLATE.read_text(encoding="utf-8")

    def test_template_file_exists(self):
        assert TEMPLATE.is_file(), f"template not found: {TEMPLATE}"

    def test_br_no_longer_a_heading_block(self):
        """RETIRED (rebuild-spec 27.7.0, action-thread reshape), not deleted — this
        documents WHY the old `test_br_block_has_linked_fr` no longer applies, rather
        than silently dropping BR coverage.

        Under the wire-format contract's three-bin rule (§ 4.4), a BR rule is either
        Bin 1 (inline in the one action's own **Rule** rung, § 3 — a fact that action
        already owns) or Bin 2 (an inline `**BR-NNN — one plain sentence.**` paragraph
        under § 4.4, carrying `Used in: A#, A#` instead of a per-block **Linked FR:**
        line). Neither shape is an H3 heading, so `BLOCK_HEADING_RE` (H3-only — this
        file's local copy of the canonical `_spec_block_lib.BLOCK_HEADING_RE`) never
        finds a BR block to check a **Linked FR:** line inside in the first place —
        there is no heading left to carry one.

        This is not a silently dropped requirement: the FR<->BR binding the old
        per-block field asserted now lives at § 2 Action Index's Codes column instead
        — every FR-###/BR-### declared in § 3/§ 4 must be claimed by exactly one row
        (`FeatureSpec.action_unclaimed`), a stronger, machine-checked binding than the
        old free-text `**Applies to:**` field ever was (measured at 26% resolution on
        the 43-feature corpus — see ADR-0006). SM/ALG/INT are unaffected: they stay H3
        headings and still require **Linked FR:** (see the sibling tests below).

        This test proves the premise rather than just asserting an absence: the
        template still carries real BR-### mentions, and none of them are H3 headings.
        """
        content = self._content()
        assert re.search(r"BR-\d{3}", content), "expected at least one BR-### mention in the template"
        blocks = _blocks_with_linked_fr(content)
        br_blocks = {h: v for h, v in blocks.items() if _block_code(h).startswith("BR-")}
        assert br_blocks == {}, (
            "a BR-### H3 heading block reappeared in the template — if BR is meant to "
            "be heading-shaped again, this retirement note (and the wire-format-"
            "contract.md three-bin rule) needs revisiting, not just this test"
        )

    def test_sm_block_has_linked_fr(self):
        content = self._content()
        blocks = _blocks_with_linked_fr(content)
        sm_blocks = {h: v for h, v in blocks.items() if _block_code(h).startswith("SM-")}
        assert sm_blocks, "No SM- blocks found in template"
        for heading, has_it in sm_blocks.items():
            assert has_it, f"Missing **Linked FR:** in {heading}"

    def test_alg_block_has_linked_fr(self):
        content = self._content()
        blocks = _blocks_with_linked_fr(content)
        alg_blocks = {h: v for h, v in blocks.items() if _block_code(h).startswith("ALG-")}
        assert alg_blocks, "No ALG- blocks found in template"
        for heading, has_it in alg_blocks.items():
            assert has_it, f"Missing **Linked FR:** in {heading}"

    def test_int_block_has_linked_fr(self):
        content = self._content()
        blocks = _blocks_with_linked_fr(content)
        int_blocks = {h: v for h, v in blocks.items() if _block_code(h).startswith("INT-")}
        assert int_blocks, "No INT- blocks found in template"
        for heading, has_it in int_blocks.items():
            assert has_it, f"Missing **Linked FR:** in {heading}"

    def test_all_blocks_have_linked_fr(self):
        """Aggregate check: every BR/SM/ALG/INT block must have **Linked FR:**."""
        content = self._content()
        blocks = _blocks_with_linked_fr(content)
        missing = [h for h, has_it in blocks.items() if not has_it]
        assert missing == [], f"Blocks missing **Linked FR:**: {missing}"
