"""Tests for locate_synthesis_artifacts.py — the Phase-01 doc-locator."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import locate_synthesis_artifacts as loc  # noqa: E402


def _mk_single_lang(tmp_path: Path) -> Path:
    """Build a single-lang (en) docs tree with user-stories + feature-list."""
    docs = tmp_path / "docs"
    (docs / "generated").mkdir(parents=True)
    (docs / "system").mkdir(parents=True)
    (docs / "generated" / "user-stories.md").write_text("# US", encoding="utf-8")
    (docs / "generated" / "feature-list.md").write_text("# FL", encoding="utf-8")
    (docs / "system" / "glossary.md").write_text("# G", encoding="utf-8")
    feat = docs / "features" / "F001_Login"
    feat.mkdir(parents=True)
    (feat / "technical-spec.md").write_text("# spec", encoding="utf-8")
    return tmp_path


def _mk_multi_lang(tmp_path: Path) -> Path:
    """Build a per-lang tree: primary vi, docs under docs/vi/."""
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    (docs / ".rebuild-state.json").write_text(
        json.dumps({"primary_lang": "vi", "translations": {"en": {}}}), encoding="utf-8")
    vi = docs / "vi"
    (vi / "generated").mkdir(parents=True)
    (vi / "generated" / "user-stories.md").write_text("# US vi", encoding="utf-8")
    return tmp_path


class TestSingleLang:
    def test_user_stories_present(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        res = loc.locate(root, "user-stories", None, None)
        us = [a for a in res["artifacts"] if a["kind"] == "user-stories"]
        assert len(us) == 1 and us[0]["present"] is True

    def test_feature_specs_globbed(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        res = loc.locate(root, "feature-list", None, None)
        specs = [a for a in res["artifacts"] if a["kind"] == "feature-spec"]
        assert any(a["present"] for a in specs)

    def test_all_scope_includes_system(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        res = loc.locate(root, "all", None, None)
        kinds = {a["kind"] for a in res["artifacts"]}
        assert {"user-stories", "feature-list", "glossary"} <= kinds

    def test_absent_artifact_recorded_not_error(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        res = loc.locate(root, "system", None, None)
        entities = [a for a in res["artifacts"] if a["kind"] == "entities"]
        assert entities and entities[0]["present"] is False


class TestFunctionalSpecLocator:
    """phase 09 (capability-map): functional-spec.md registered in _SCOPE_ARTIFACTS rather than
    globbed by judgment_engine.py directly, so it inherits resolve_docs_root's per-language
    fallback — the exact case a private glob bypass would silently miss."""

    def test_functional_spec_globbed_present(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        feat = root / "docs" / "features" / "F001_Login"
        (feat / "functional-spec.md").write_text("# fspec", encoding="utf-8")
        res = loc.locate(root, "feature-list", None, None)
        fspecs = [a for a in res["artifacts"] if a["kind"] == loc.KIND_FEATURE_SPEC_FUNCTIONAL]
        assert any(a["present"] for a in fspecs)

    def test_absent_for_v26_shape_recorded_not_error(self, tmp_path):
        # v26 corpus: technical-spec.md only, no functional-spec.md anywhere.
        root = _mk_single_lang(tmp_path)
        res = loc.locate(root, "feature-list", None, None)
        fspecs = [a for a in res["artifacts"] if a["kind"] == loc.KIND_FEATURE_SPEC_FUNCTIONAL]
        assert len(fspecs) == 1 and fspecs[0]["present"] is False

    def test_resolves_under_non_en_primary_language(self, tmp_path):
        # The shape a `docs_root.glob(...)` bypass would silently miss: primary lang vi, so
        # the real content lives at docs/vi/features/*/functional-spec.md, not docs/features/*.
        root = _mk_multi_lang(tmp_path)
        feat = root / "docs" / "vi" / "features" / "F001_DangNhap"
        feat.mkdir(parents=True)
        (feat / "functional-spec.md").write_text("# fspec vi", encoding="utf-8")
        res = loc.locate(root, "feature-list", None, None)
        assert res["docs_root"].endswith("/docs/vi")
        fspecs = [a for a in res["artifacts"] if a["kind"] == loc.KIND_FEATURE_SPEC_FUNCTIONAL]
        assert any(a["present"] and a["path"].endswith("/docs/vi/features/F001_DangNhap/functional-spec.md")
                   for a in fspecs)


class TestBehaviorLogic:
    """v27.0.0: system/business-rules.md is deleted; the locator row must resolve to the
    merged generated/behavior-logic.md instead (docs-canonical-mapping.md Disambiguation note)."""

    def test_behavior_logic_resolves_on_v27_tree(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        (root / "docs" / "generated" / "behavior-logic.md").write_text(
            "# Behavior Logic\n\n## BL001\n", encoding="utf-8")
        res = loc.locate(root, "system", None, None)
        bl = [a for a in res["artifacts"] if a["kind"] == "behavior-logic"]
        assert len(bl) == 1
        assert bl[0]["present"] is True
        assert Path(bl[0]["path"]).is_file()
        assert bl[0]["path"].endswith("generated/behavior-logic.md")

    def test_business_rules_kind_no_longer_emitted(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        res = loc.locate(root, "system", None, None)
        kinds = {a["kind"] for a in res["artifacts"]}
        assert "business-rules" not in kinds


class TestMultiLang:
    def test_docs_root_resolves_to_primary(self, tmp_path):
        root = _mk_multi_lang(tmp_path)
        res = loc.locate(root, "user-stories", None, None)
        assert res["docs_root"].endswith("/docs/vi")
        us = [a for a in res["artifacts"] if a["kind"] == "user-stories"]
        assert us[0]["present"] is True


class TestPlanDirIsInert:
    """Every artifact now resolves under the docs root. `--plan-dir` survives for
    `coverage_engine.py`'s plan-dir validator subset, but the locator must ignore it — a plan dir
    is no longer a place any artifact can be read from."""

    def test_plan_dir_changes_nothing(self, tmp_path):
        root = _mk_single_lang(tmp_path)
        pd = root / "plans" / "260721-1043-foo" / "artifacts"
        pd.mkdir(parents=True)
        (pd / "user-stories.md").write_text("# planted", encoding="utf-8")
        without = loc.locate(root, "all", None, None)
        with_pd = loc.locate(root, "all", None, "plans/260721-1043-foo")
        assert without == with_pd
        assert all("/plans/" not in (a["path"] or "") for a in with_pd["artifacts"])
