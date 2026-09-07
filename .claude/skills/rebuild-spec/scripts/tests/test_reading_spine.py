"""Tests for reading-spine.cjs — phase 03 of the reading-order plan
(`260826-1601-package-reading-layers-index-pager`).

Sibling of `test_build_client_package.py` (already 1047 lines before this
file) rather than an addition to it — this phase's own surface (pure-model
unit tests + per-lang sidecar-location proofs + two full end-to-end bundler
runs) is large enough to earn its own module, and none of it touches the
denylist/lang-traversal/XSS concerns that file already owns.

Two layers:
1. Direct unit tests of `buildReadingModel()` / `loadSidecar()` via a small
   generated Node driver script — fast, precise assertions on the pure
   ordering/claiming logic, independent of the (slow) markdown renderer.
2. End-to-end proofs through the REAL `build_client_package.cjs` wiring: the
   real sharetribe corpus (measured spine/appendix counts) and a synthetic
   sidecar-less fixture (fallback path), both via the actual `--package`
   entry point, not a mock.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]  # agent-kit/
LIB_DIR = REPO_ROOT / "claude" / "skills" / "rebuild-spec" / "extensions" / "scripts" / "lib"
READING_SPINE = LIB_DIR / "reading-spine.cjs"
RESOLVE_LANG_ROOT = LIB_DIR / "resolve-lang-root.cjs"
BUILD_SCRIPT = REPO_ROOT / "claude" / "skills" / "rebuild-spec" / "extensions" / "scripts" / "build_client_package.cjs"

# The real, already-promoted sharetribe corpus this plan was measured against
# (see plans/260826-1601-package-reading-layers-index-pager/reports/
# orchestrator-scouting-phase-03.md "Confirmed environment"). Real-corpus
# tests skip (not fail) when this machine doesn't have that checkout.
SHARETRIBE_REPO = Path("/home/pham.van.duc@sun-asterisk.com/github/sharetribe")
SHARETRIBE_DOCS = SHARETRIBE_REPO / "docs"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not available on PATH")

requires_sharetribe = pytest.mark.skipif(
    not SHARETRIBE_DOCS.is_dir(), reason="real sharetribe corpus not present on this machine"
)


# ---------------------------------------------------------------------------
# Node driver helpers — call the real .cjs modules, print JSON, parse back.
# ---------------------------------------------------------------------------


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run_model(tmp_path: Path, sidecar, pages, project_name: str = "Demo") -> dict:
    """Call `buildReadingModel({sidecar, pages, projectName})` directly and
    return a JSON-safe summary (page objects reduced to their `relMd`)."""
    driver = tmp_path / "model-driver.cjs"
    driver.write_text(
        f"""'use strict';
const {{ buildReadingModel }} = require({json.dumps(str(READING_SPINE))});
const sidecar = {json.dumps(sidecar)};
const pages = {json.dumps(pages)};
const model = buildReadingModel({{ sidecar, pages, projectName: {json.dumps(project_name)} }});
const ref = (p) => (p ? p.relMd : null);
console.log(JSON.stringify({{
  startHere: ref(model.startHere),
  trace: ref(model.trace),
  spine: model.spine.map((s) => [s.page.relMd, s.section]),
  appendix: model.appendix.map((p) => p.relMd),
  ui: model.ui,
  layers: model.layers.map((l) => ({{
    layer: l.layer,
    entries: l.entries.map((e) => e.page.relMd),
    drills: l.drills.map((d) => ({{
      key: d.key,
      index: ref(d.index),
      items: d.items.map((p) => p.relMd),
      groups: d.groups && d.groups.map((g) => ({{ key: g.key, items: g.items.map((p) => p.relMd) }})),
    }})),
  }})),
}}));
""",
        encoding="utf-8",
    )
    result = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _run_lang_sidecar_probe(tmp_path: Path, docs_root_outer: Path, lang: str | None) -> dict:
    """Resolve `lang`'s root the real way (`resolveLangRoot`) and load the
    sidecar the real way (`loadSidecar`) — proves F1 end to end using the
    two actual production modules, not a re-derivation of their logic."""
    driver = tmp_path / "lang-probe.cjs"
    lang_js = json.dumps(lang) if lang is not None else "null"
    driver.write_text(
        f"""'use strict';
const {{ resolveLangRoot }} = require({json.dumps(str(RESOLVE_LANG_ROOT))});
const {{ loadSidecar }} = require({json.dumps(str(READING_SPINE))});
const {{ root }} = resolveLangRoot({{ docsRoot: {json.dumps(str(docs_root_outer))}, lang: {lang_js} }});
const sidecar = loadSidecar(root);
console.log(JSON.stringify({{ root, title: sidecar ? sidecar.title : null }}));
""",
        encoding="utf-8",
    )
    result = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _page(rel_md: str, title: str | None = None) -> dict:
    return {"relMd": rel_md, "title": title or rel_md}


# Minimal, well-formed `ui` block matching the real _nav_strings_*.package_ui
# shape (phase-03b) — used by `_sidecar()` so every pre-existing pure-model
# fixture stays a REALISTIC valid sidecar rather than one loadSidecar() would
# now reject for missing `ui`.
_UI = {
    "start_here": "Start Here",
    "appendix": "Appendix — Repo Docs",
    "drill_labels": {"flows": "Flows", "features": "Features", "screens": "Screens", "traceability_matrix": "Traceability"},
    "pager": {"prev": "‹ Previous", "next": "Next ›", "reading": "Reading", "back_to_index": "back to index", "end_of_spine": "End of the reading order"},
}


def _sidecar(layers, title: str = "Documentation Index — Reading Order", schema_version: int = 1, ui=_UI) -> dict:
    return {"schemaVersion": schema_version, "lang": "en", "title": title, "layers": layers, "ui": ui}


# ---------------------------------------------------------------------------
# Pure-model unit tests
# ---------------------------------------------------------------------------


class TestClaimedModel:
    def test_every_page_claimed_exactly_once_in_spine(self, tmp_path: Path) -> None:
        pages = [
            _page("README.md"),
            _page("system/overview.md"),
            _page("generated/feature-list.md"),
            _page("flows/b.md"),
            _page("flows/a.md"),
            _page("generated/traceability-matrix.md"),
        ]
        sidecar = _sidecar(
            [
                {
                    "layer": 1,
                    "label": "Orientation",
                    "intro": "start",
                    "entries": [{"num": 1, "kind": "file", "path": "system/overview.md", "key": "overview", "what": "x"}],
                },
                {
                    "layer": 2,
                    "label": "Domain",
                    "intro": "domain",
                    "entries": [
                        {"num": 2, "kind": "file", "path": "generated/feature-list.md", "key": "feature_list", "what": "x"}
                    ],
                },
                {"layer": 3, "label": "Behavior", "intro": "behavior", "entries": []},
                {
                    "layer": 4,
                    "label": "Deep dives",
                    "intro": "deep",
                    "entries": [
                        {"num": 3, "kind": "glob", "glob": "flows/*.md", "link": "flows/", "key": "flows", "what": "x"},
                        {
                            "num": 4,
                            "kind": "file",
                            "path": "generated/traceability-matrix.md",
                            "key": "traceability_matrix",
                            "what": "x",
                        },
                    ],
                },
            ]
        )
        model = _run_model(tmp_path, sidecar, pages)
        assert len(model["spine"]) == len(pages)
        assert len({relmd for relmd, _section in model["spine"]}) == len(pages)  # no duplicates
        assert model["appendix"] == []

    def test_traceability_excluded_from_layer_entries_present_as_trace(self, tmp_path: Path) -> None:
        pages = [_page("README.md"), _page("generated/traceability-matrix.md")]
        sidecar = _sidecar(
            [
                {
                    "layer": 4,
                    "label": "Deep dives",
                    "intro": "d",
                    "entries": [
                        {
                            "num": 1,
                            "kind": "file",
                            "path": "generated/traceability-matrix.md",
                            "key": "traceability_matrix",
                            "what": "x",
                        }
                    ],
                }
            ]
        )
        model = _run_model(tmp_path, sidecar, pages)
        assert model["trace"] == "generated/traceability-matrix.md"
        assert model["layers"][0]["entries"] == []  # not a numbered row

    def test_features_grouped_by_feature_then_file_role(self, tmp_path: Path) -> None:
        # Scrambled input order on purpose — the model must impose the order,
        # not preserve input order.
        pages = [
            _page("features/F002_Second/test-cases.md"),
            _page("features/F001_First/technical-spec.md"),
            _page("features/F001_First/README.md"),
            _page("features/F002_Second/README.md"),
            _page("features/F001_First/test-cases.md"),
            _page("features/F002_Second/technical-spec.md"),
            _page("features/F001_First/functional-spec.md"),
            _page("features/F002_Second/functional-spec.md"),
        ]
        sidecar = _sidecar(
            [
                {
                    "layer": 4,
                    "label": "Deep dives",
                    "intro": "d",
                    "entries": [
                        {"num": 1, "kind": "glob", "glob": "features/*/", "link": "features/", "key": "features", "what": "x"}
                    ],
                }
            ]
        )
        model = _run_model(tmp_path, sidecar, pages)
        drill = model["layers"][0]["drills"][0]
        assert [g["key"] for g in drill["groups"]] == ["F001_First", "F002_Second"]
        assert drill["groups"][0]["items"] == [
            "features/F001_First/README.md",
            "features/F001_First/functional-spec.md",
            "features/F001_First/technical-spec.md",
            "features/F001_First/test-cases.md",
        ]
        assert drill["groups"][1]["items"] == [
            "features/F002_Second/README.md",
            "features/F002_Second/functional-spec.md",
            "features/F002_Second/technical-spec.md",
            "features/F002_Second/test-cases.md",
        ]
        assert drill["index"] is None  # no top-level features/README.md in this fixture

    def test_flows_and_screens_sorted_by_path_not_input_order(self, tmp_path: Path) -> None:
        pages = [_page("flows/zeta.md"), _page("flows/alpha.md"), _page("flows/mid.md")]
        sidecar = _sidecar(
            [
                {
                    "layer": 4,
                    "label": "Deep dives",
                    "intro": "d",
                    "entries": [{"num": 1, "kind": "glob", "glob": "flows/*.md", "link": "flows/", "key": "flows", "what": "x"}],
                }
            ]
        )
        model = _run_model(tmp_path, sidecar, pages)
        assert model["layers"][0]["drills"][0]["items"] == ["flows/alpha.md", "flows/mid.md", "flows/zeta.md"]

    def test_glob_index_pulled_out_only_when_glob_does_not_already_match_it(self, tmp_path: Path) -> None:
        """`features/*/` never matches the top-level `features/README.md` (no
        nesting) so it becomes a separate `index`; `flows/*.md` DOES match
        `flows/README.md`, so that page stays a plain item, not an index —
        matches the real sharetribe corpus's measured shape exactly."""
        pages = [
            _page("features/README.md"),
            _page("features/F001_X/README.md"),
            _page("flows/README.md"),
            _page("flows/a.md"),
        ]
        sidecar = _sidecar(
            [
                {
                    "layer": 4,
                    "label": "Deep dives",
                    "intro": "d",
                    "entries": [
                        {"num": 1, "kind": "glob", "glob": "features/*/", "link": "features/", "key": "features", "what": "x"},
                        {"num": 2, "kind": "glob", "glob": "flows/*.md", "link": "flows/", "key": "flows", "what": "x"},
                    ],
                }
            ]
        )
        model = _run_model(tmp_path, sidecar, pages)
        feat_drill, flows_drill = model["layers"][0]["drills"]
        assert feat_drill["index"] == "features/README.md"
        assert "features/README.md" not in feat_drill["items"]
        assert flows_drill["index"] is None
        assert "flows/README.md" in flows_drill["items"]

    def test_appendix_is_unclaimed_pages_sorted_by_title(self, tmp_path: Path) -> None:
        pages = [_page("z.md", title="Zulu"), _page("a.md", title="Alpha"), _page("README.md", title="Start")]
        sidecar = _sidecar([])
        model = _run_model(tmp_path, sidecar, pages)
        # README.md is always claimed as startHere, so only z.md/a.md remain,
        # sorted by title (Alpha before Zulu).
        assert model["appendix"] == ["a.md", "z.md"]

    def test_sidecar_entry_pointing_at_absent_page_dropped_silently(self, tmp_path: Path) -> None:
        pages = [_page("README.md")]
        sidecar = _sidecar(
            [
                {
                    "layer": 1,
                    "label": "L1",
                    "intro": "i",
                    "entries": [{"num": 1, "kind": "file", "path": "system/overview.md", "key": "overview", "what": "x"}],
                }
            ]
        )
        model = _run_model(tmp_path, sidecar, pages)  # overview.md is not a real page
        assert model["layers"][0]["entries"] == []
        assert len(model["spine"]) == len(pages)  # startHere only — nothing lost, nothing invented


class TestFallback:
    def test_schema_version_2_takes_fallback_path(self, tmp_path: Path) -> None:
        pages = [_page("a.md"), _page("b.md")]
        sidecar = _sidecar([], schema_version=2)
        model = _run_model(tmp_path, sidecar, pages)
        assert model["spine"] == []
        assert sorted(model["appendix"]) == ["a.md", "b.md"]

    def test_null_sidecar_lists_every_page_no_pager(self, tmp_path: Path) -> None:
        pages = [_page("a.md"), _page("b.md"), _page("README.md")]
        model = _run_model(tmp_path, None, pages)
        assert model["spine"] == []  # no pager
        assert sorted(model["appendix"]) == ["README.md", "a.md", "b.md"]  # nothing lost
        assert model["startHere"] is None
        assert model["trace"] is None
        assert model["layers"] == []

    def test_malformed_glob_entry_falls_back_instead_of_throwing(self, tmp_path: Path) -> None:
        """A glob entry missing its own `glob` field throws inside
        `globTest()` — proves the internal try/catch in `buildReadingModel`
        actually degrades to the fallback rather than merely being unreached
        dead code."""
        pages = [_page("a.md"), _page("b.md")]
        sidecar = _sidecar(
            [{"layer": 4, "label": "L4", "intro": "i", "entries": [{"num": 1, "kind": "glob", "key": "broken", "what": "x"}]}]
        )
        model = _run_model(tmp_path, sidecar, pages)
        assert model["spine"] == []
        assert sorted(model["appendix"]) == ["a.md", "b.md"]


class TestLoadSidecar:
    def test_absent_file_returns_null(self, tmp_path: Path) -> None:
        result = _run_lang_sidecar_probe(tmp_path, tmp_path / "docs", lang=None)
        assert result["title"] is None

    def test_malformed_json_returns_null(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        _write(docs / ".reading-order.json", "{not valid json")
        result = _run_lang_sidecar_probe(tmp_path, docs, lang=None)
        assert result["title"] is None

    def test_wrong_schema_version_returns_null(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        _write(docs / ".reading-order.json", json.dumps({"schemaVersion": 2, "title": "T", "layers": []}))
        result = _run_lang_sidecar_probe(tmp_path, docs, lang=None)
        assert result["title"] is None

    def test_missing_ui_returns_null(self, tmp_path: Path) -> None:
        """phase-03b hard requirement: `ui` is REQUIRED. A well-formed sidecar
        (valid schemaVersion, valid layers) that simply omits `ui` must be
        rejected exactly like a bad schemaVersion — no English-default
        fallback, straight to the no-sidecar path."""
        docs = tmp_path / "docs"
        _write(docs / ".reading-order.json", json.dumps({"schemaVersion": 1, "title": "T", "layers": []}))
        result = _run_lang_sidecar_probe(tmp_path, docs, lang=None)
        assert result["title"] is None

    def test_non_object_ui_returns_null(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        _write(docs / ".reading-order.json", json.dumps({"schemaVersion": 1, "title": "T", "layers": [], "ui": "nope"}))
        result = _run_lang_sidecar_probe(tmp_path, docs, lang=None)
        assert result["title"] is None


class TestPerLangSidecarLocation:
    """F1: the sidecar lives at the RESOLVED per-language root, never the
    outer docs root, and there is no cross-root fallback."""

    def _make_perlang_corpus_with_sidecars(self, repo_root: Path) -> Path:
        docs = repo_root / "docs"
        _write(
            docs / ".rebuild-state.json",
            json.dumps({"primary_lang": "en", "translations": {"vi": {"last_translate_run_sha": "deadbeef"}}}),
        )
        _write(docs / ".reading-order.json", json.dumps({"schemaVersion": 1, "title": "EN TITLE", "layers": [], "ui": _UI}))
        _write(docs / "vi" / ".reading-order.json", json.dumps({"schemaVersion": 1, "title": "VI TITLE", "layers": [], "ui": _UI}))
        return docs

    def test_secondary_lang_reads_its_own_root_sidecar(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        docs = self._make_perlang_corpus_with_sidecars(repo)
        result = _run_lang_sidecar_probe(tmp_path, docs, lang="vi")
        assert result["root"] == str(docs / "vi")
        assert result["title"] == "VI TITLE"  # not the EN sidecar

    def test_primary_lang_reads_bare_outer_root_sidecar(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        docs = self._make_perlang_corpus_with_sidecars(repo)
        result = _run_lang_sidecar_probe(tmp_path, docs, lang="en")
        assert result["root"] == str(docs)
        assert result["title"] == "EN TITLE"

    def test_no_cross_root_fallback_when_resolved_root_lacks_sidecar(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        docs = self._make_perlang_corpus_with_sidecars(repo)
        # Remove ONLY the vi sidecar — the outer EN sidecar still exists.
        (docs / "vi" / ".reading-order.json").unlink()
        assert (docs / ".reading-order.json").is_file()  # sanity: EN copy is still there to (wrongly) fall back to

        result = _run_lang_sidecar_probe(tmp_path, docs, lang="vi")
        assert result["root"] == str(docs / "vi")
        assert result["title"] is None  # NOT "EN TITLE" — no cross-root read


class TestModuleSize:
    def test_reading_spine_under_200_lines(self) -> None:
        line_count = len(READING_SPINE.read_text(encoding="utf-8").splitlines())
        assert line_count < 200, f"reading-spine.cjs is {line_count} lines, must stay under 200"

    def test_reading_spine_drill_under_200_lines(self) -> None:
        """Glob-entry expansion was extracted here (phase-03b) specifically
        so the `ui` plumbing didn't push reading-spine.cjs over budget."""
        drill = LIB_DIR / "reading-spine-drill.cjs"
        line_count = len(drill.read_text(encoding="utf-8").splitlines())
        assert line_count < 200, f"reading-spine-drill.cjs is {line_count} lines, must stay under 200"


class TestPackageUiOnModel:
    """phase-03b: `ui` is required on a valid sidecar, exposed unmodified on
    the model, and drives the appendix section label reading-spine.cjs used
    to hard-code as the English literal `'Appendix'`."""

    def test_ui_exposed_on_claimed_model(self, tmp_path: Path) -> None:
        pages = [_page("README.md")]
        sidecar = _sidecar([])
        model = _run_model(tmp_path, sidecar, pages)
        assert model["ui"] == _UI

    def test_ui_is_null_on_fallback_model(self, tmp_path: Path) -> None:
        pages = [_page("a.md")]
        model = _run_model(tmp_path, None, pages)  # no sidecar at all -> fallback
        assert model["ui"] is None

    def test_appendix_section_label_comes_from_sidecar_ui_not_hardcoded(self, tmp_path: Path) -> None:
        """A sidecar whose `ui.appendix` differs from the plan's example text
        must show up verbatim in the spine's appendix section labels — proves
        the label is READ from the sidecar, not a fixed English literal."""
        pages = [_page("README.md"), _page("orphan.md", title="Orphan")]
        custom_ui = dict(_UI, appendix="CUSTOM APPENDIX LABEL")
        sidecar = _sidecar([], ui=custom_ui)
        model = _run_model(tmp_path, sidecar, pages)
        appendix_sections = [section for relmd, section in model["spine"] if relmd == "orphan.md"]
        assert appendix_sections == ["CUSTOM APPENDIX LABEL"]


class TestNoHardcodedEnglishChrome:
    """Success criterion: grep for English chrome literals in
    reading-spine.cjs returns empty. Checked against source with comments
    stripped, so this doesn't false-positive on explanatory JSDoc prose."""

    def test_no_appendix_literal_outside_comments(self) -> None:
        src = READING_SPINE.read_text(encoding="utf-8")
        code_only = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
        code_only = re.sub(r"//.*", "", code_only)
        assert "'Appendix'" not in code_only
        assert '"Appendix"' not in code_only
        assert "APPENDIX_SECTION" not in code_only


# ---------------------------------------------------------------------------
# End-to-end proofs through the real build_client_package.cjs wiring
# ---------------------------------------------------------------------------


def _run_build(repo_root: Path, docs_root: str, out: Path, *extra_args: str) -> subprocess.CompletedProcess:
    cmd = ["node", str(BUILD_SCRIPT), "--repo-root", str(repo_root), "--docs-root", docs_root, "--out", str(out), *extra_args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


class TestRealSharetribeCorpus:
    @requires_sharetribe
    def test_spine_equals_page_count_appendix_is_23(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        result = _run_build(SHARETRIBE_REPO, "docs", out)
        assert result.returncode == 0, result.stderr
        assert "380 page(s)" in result.stdout
        assert "sidecar: yes" in result.stdout
        assert "spine: 380" in result.stdout
        assert "appendix: 23" in result.stdout

    @requires_sharetribe
    def test_appendix_holds_the_two_scope_boundary_pages_not_layer_3(self, tmp_path: Path) -> None:
        """F2/F5 regression guard: `system/permissions.md` and
        `generated/job-list.md` (the mockup's dropped `PROPOSED_L3`) must
        land in the Appendix, never in a numbered layer-3 row."""
        driver = tmp_path / "e2e-driver.cjs"
        driver.write_text(
            f"""'use strict';
const {{ buildClientPackage }} = require({json.dumps(str(BUILD_SCRIPT))});
const result = buildClientPackage([
  '--repo-root', {json.dumps(str(SHARETRIBE_REPO))},
  '--docs-root', 'docs',
  '--out', {json.dumps(str(tmp_path / "out"))},
]);
const m = result.readingModel;
const layer3 = m.layers.find((l) => l.layer === 3);
console.log(JSON.stringify({{
  appendixHasPermissions: m.appendix.some((p) => p.relMd === 'system/permissions.md'),
  appendixHasJobList: m.appendix.some((p) => p.relMd === 'generated/job-list.md'),
  layer3Paths: layer3.entries.map((e) => e.page.relMd),
}}));
""",
            encoding="utf-8",
        )
        result = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=180)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["appendixHasPermissions"] is True
        assert payload["appendixHasJobList"] is True
        assert "system/permissions.md" not in payload["layer3Paths"]
        assert "generated/job-list.md" not in payload["layer3Paths"]


class TestFallbackRealBundler:
    def _make_sidecarless_corpus(self, repo_root: Path) -> Path:
        docs = repo_root / "docs"
        _write(docs / "README.md", "# Docs\n\nRoot index, no sidecar next to it.\n")
        _write(docs / "system" / "overview.md", "# Overview\n\nBody.\n")
        _write(docs / "generated" / "feature-list.md", "# Features\n\n| Code | Name |\n|---|---|\n| F001 | Login |\n")
        _write(docs / "flows" / "checkout.md", "# Checkout flow\n\nBody.\n")
        return docs

    def test_sidecarless_corpus_produces_complete_bundle_with_no_pager(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        docs = self._make_sidecarless_corpus(repo)
        assert not (docs / ".reading-order.json").exists()  # sanity: genuinely sidecar-less
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr
        assert "sidecar: no" in result.stdout
        assert "spine: 0" in result.stdout  # fallback -> no pager

        md_count = len(list(docs.rglob("*.md")))
        html_files = [p for p in out.rglob("*.html") if p.name != "index.html"]
        assert len(html_files) == md_count
        assert f"appendix: {md_count}" in result.stdout  # every page listed, nothing lost


class TestMalformedUiShapeTakesFallback:
    """Regression: `loadSidecar()` promised null on a "missing/malformed `ui`
    block" but only checked PRESENCE of an object. A schema-valid but hollow
    `ui: {}` passed the gate, and `package-pager.cjs` then dereferenced
    `model.ui.pager.<key>` unguarded — throwing inside
    `build_client_package.cjs`'s per-page loop and ABORTING the whole bundle
    build, contradicting the documented never-throws fallback contract.

    Phase 03b's original negative test deleted `ui` ENTIRELY, so it never
    reached this branch — a negative test that cannot fail the way the real
    input fails proves nothing. These cases exercise the PARTIAL shapes.
    """

    @staticmethod
    def _probe(tmp_path: Path, ui) -> bool:
        """True when loadSidecar() rejects the payload (returns null)."""
        docs = tmp_path / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        payload = {
            "schemaVersion": 1,
            "lang": "en",
            "title": "T",
            "quickPath": {"label": "Q", "nums": []},
            "roles": [],
            "layers": [],
            "ui": ui,
        }
        (docs / ".reading-order.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
        driver = tmp_path / "ui-probe.cjs"
        driver.write_text(
            f"""'use strict';
const {{ loadSidecar }} = require({json.dumps(str(READING_SPINE))});
console.log(JSON.stringify({{ rejected: loadSidecar({json.dumps(str(docs))}) === null }}));
""",
            encoding="utf-8",
        )
        r = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, r.stderr
        return json.loads(r.stdout)["rejected"]

    _FULL_PAGER = {
        "prev": "p", "next": "n", "reading": "r",
        "back_to_index": "b", "end_of_spine": "e",
    }

    def _valid_ui(self, **over):
        ui = {
            "start_here": "S", "appendix": "A",
            "drill_labels": {}, "pager": dict(self._FULL_PAGER),
        }
        ui.update(over)
        return ui

    def test_hollow_ui_object_is_rejected(self, tmp_path: Path) -> None:
        # The exact payload that shipped the bug: an object, but empty.
        assert self._probe(tmp_path, {}) is True

    def test_ui_without_pager_is_rejected(self, tmp_path: Path) -> None:
        ui = self._valid_ui()
        del ui["pager"]
        assert self._probe(tmp_path, ui) is True

    @pytest.mark.parametrize("missing", sorted(_FULL_PAGER))
    def test_pager_missing_any_single_key_is_rejected(
        self, tmp_path: Path, missing: str
    ) -> None:
        pager = dict(self._FULL_PAGER)
        del pager[missing]
        assert self._probe(tmp_path, self._valid_ui(pager=pager)) is True

    def test_pager_key_of_wrong_type_is_rejected(self, tmp_path: Path) -> None:
        assert self._probe(
            tmp_path, self._valid_ui(pager={**self._FULL_PAGER, "prev": 42})
        ) is True

    def test_non_string_start_here_is_rejected(self, tmp_path: Path) -> None:
        assert self._probe(tmp_path, self._valid_ui(start_here=None)) is True

    def test_fully_shaped_ui_is_ACCEPTED(self, tmp_path: Path) -> None:
        # Positive control — proves the guard rejects for the right reason and
        # is not simply refusing everything (which would make the cases above
        # pass vacuously).
        assert self._probe(tmp_path, self._valid_ui()) is False
