"""Tests for the '## Document Map' crosswalk (FR-1, phase-01, rebuild-spec 27.11.0).

Covers: full-corpus rendering (all 4 buckets + trace pointer), sparse/core-only corpus
(only populated buckets render, no dangling heading when nothing is present at all),
per-lang layout-mode correctness (FR-2 — no Document Map at a bare per-lang root that v18
deliberately leaves without a README), hand-written user-content preservation across
regeneration, and locale skeleton identity (link targets identical across en/vi/ja; only
prose differs).
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _nav_docmap_lib import build_document_map  # noqa: E402
from _nav_strings import get_strings  # noqa: E402
from build_navigation import run  # noqa: E402


def _write(path: Path, content: str = "# x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _core_tree(base: Path) -> Path:
    docs = base / "docs"
    for rel in (
        "system/overview.md", "system/architecture.md",
        "generated/entities.md", "generated/feature-list.md",
        "generated/user-stories.md", "generated/screen-list.md",
        "generated/screen-flow.md", "generated/route-list.md",
        "generated/api-map.md", "generated/behavior-logic.md",
        "generated/permissions-matrix.md",
    ):
        _write(docs / rel)
    return docs


class TestFullCorpus:
    def test_all_four_buckets_render_in_waterfall_order(self, tmp_path):
        docs = _core_tree(tmp_path)
        feat = docs / "features" / "F001_Login"
        _write(feat / "functional-spec.md")
        _write(feat / "technical-spec.md")
        _write(feat / "test-cases.md")
        _write(docs / "generated" / "api-contracts.md")
        _write(docs / "generated" / "crud-matrix.md")

        block = build_document_map(str(docs), "en")
        headings = [h for h in block.splitlines() if h.startswith("### ")]
        assert headings == ["### Requirements", "### External Design",
                            "### Internal Design", "### Test Spec"]

    def test_trace_pointer_appears_only_when_matrix_present(self, tmp_path):
        docs = _core_tree(tmp_path)
        _write(docs / "features" / "F001_Login" / "functional-spec.md")
        assert "traceability-matrix" not in build_document_map(str(docs), "en")
        _write(docs / "generated" / "traceability-matrix.md")
        assert "generated/traceability-matrix.md" in build_document_map(str(docs), "en")


class TestSparseCorpus:
    def test_core_only_omits_requirements_internal_test_buckets(self, tmp_path):
        docs = _core_tree(tmp_path)  # no features/, no api-contracts, no crud-matrix
        block = build_document_map(str(docs), "en")
        assert "### External Design" in block
        assert "### Requirements" not in block
        assert "### Test Spec" not in block
        assert "generated/api-contracts.md" not in block

    def test_nothing_present_yields_empty_block(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        assert build_document_map(str(docs), "en") == ""

    def test_run_omits_empty_document_map_no_dangling_heading(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        run(str(docs), pass_complete=False)
        readme = (docs / "README.md")
        if readme.is_file():
            assert "## Document Map" not in readme.read_text()


class TestLayoutModeCorrectness:
    def test_per_lang_bare_root_gets_no_document_map(self, tmp_path):
        """FR-2: v18 deliberately leaves NO README at the bare per-lang docs/ root — the
        Document Map must never appear there either. The orchestrator runs
        build_navigation.py ONCE per resolved docs root in real usage (bare root for
        cleanup, docs/<primary>/ for the actual index) — mirrored here as two calls."""
        docs = tmp_path / "docs"
        primary = docs / "vi"
        _core_tree_at(primary)
        (docs / ".rebuild-state.json").write_text(
            '{"primary_lang": "vi", "translations": {"en": {}}}', encoding="utf-8")
        run(str(docs), pass_complete=False)  # bare root pass — removes/never writes root README
        assert not (docs / "README.md").is_file()

        run(str(primary), pass_complete=False, lang="vi")  # the actual resolved docs root
        assert (primary / "README.md").is_file()
        assert "## " + get_strings("vi")["document_map"]["heading"] in \
            (primary / "README.md").read_text()

    def test_single_lang_root_gets_document_map(self, tmp_path):
        docs = _core_tree(tmp_path)
        run(str(docs), pass_complete=False)
        assert "## Document Map" in (docs / "README.md").read_text()


def _core_tree_at(docs: Path) -> None:
    for rel in (
        "system/overview.md", "system/architecture.md",
        "generated/entities.md", "generated/feature-list.md",
        "generated/user-stories.md", "generated/screen-list.md",
        "generated/screen-flow.md", "generated/route-list.md",
        "generated/api-map.md", "generated/behavior-logic.md",
        "generated/permissions-matrix.md",
    ):
        _write(docs / rel)


class TestUserContentPreservation:
    def test_hand_written_tail_survives_regeneration(self, tmp_path):
        docs = _core_tree(tmp_path)
        run(str(docs), pass_complete=False)
        readme = docs / "README.md"
        original = readme.read_text()
        readme.write_text(original + "\n## My Own Notes\n\nDo not delete this.\n",
                          encoding="utf-8")
        # add a new artifact so the generated zone (incl. Document Map) actually changes
        _write(docs / "features" / "F001_Login" / "functional-spec.md")
        run(str(docs), pass_complete=False)
        regenerated = readme.read_text()
        assert "Do not delete this." in regenerated
        assert "### Requirements" in regenerated  # generated zone did change


class TestLocaleSkeletonIdentity:
    def test_link_targets_identical_across_locales(self, tmp_path):
        docs = _core_tree(tmp_path)
        _write(docs / "features" / "F001_Login" / "functional-spec.md")
        en = build_document_map(str(docs), "en")
        vi = build_document_map(str(docs), "vi")
        ja = build_document_map(str(docs), "ja")
        import re
        targets = lambda s: re.findall(r"\]\(([^)]+)\)", s)  # noqa: E731
        assert targets(en) == targets(vi) == targets(ja)
        assert en != vi and en != ja  # prose actually differs

    def test_every_locale_has_document_map_key(self):
        for lang in ("en", "vi", "ja"):
            dm = get_strings(lang)["document_map"]
            assert set(dm["buckets"]) == {
                "requirements", "external_design", "internal_design", "test_spec"}
