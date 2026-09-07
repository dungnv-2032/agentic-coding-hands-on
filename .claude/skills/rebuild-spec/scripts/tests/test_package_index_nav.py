"""Tests for phase-04 of the reading-order plan
(`260826-1601-package-reading-layers-index-pager`): the layered index
(`lib/package-index-body.cjs`) and grouped sidebar (`lib/package-nav.cjs`)
that replaced the old FR-7 4-bucket index (`classifyBucket`/`BUCKET_ORDER`/
`BUCKET_LABELS`, deleted from `package-html-template.cjs` — see
`TestFR7BucketDeletion` in `test_build_client_package.py`).

Sibling of `test_build_client_package.py` and `test_reading_spine.py` (same
justification as those files: this phase's own surface — pure-render unit
tests via a generated Node driver, plus real-corpus link-integrity and
localization proofs — doesn't touch either file's own concerns).

Three layers:
1. Pure-render unit tests of `renderIndexBody()`/`renderNavList()` via a
   small generated Node driver, against a synthetic model built through the
   REAL `buildReadingModel()` (not a hand-rolled model shape).
2. End-to-end proofs through the real `build_client_package.cjs` wiring on
   the real sharetribe corpus: no "Other" section, layer/appendix counts,
   every page reachable from `index.html`, zero broken relative `.html`
   links across every rendered page.
3. A real Vietnamese sidecar (built through the actual `write_reading_sidecar`
   Python emitter, not a hand-authored fixture) proving the vi bundle
   renders real Vietnamese chrome, not English.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]  # agent-kit/
SCRIPTS_DIR = REPO_ROOT / "claude" / "skills" / "rebuild-spec" / "scripts"
LIB_DIR = REPO_ROOT / "claude" / "skills" / "rebuild-spec" / "extensions" / "scripts" / "lib"
READING_SPINE = LIB_DIR / "reading-spine.cjs"
PACKAGE_NAV = LIB_DIR / "package-nav.cjs"
PACKAGE_INDEX_BODY = LIB_DIR / "package-index-body.cjs"
BUILD_SCRIPT = REPO_ROOT / "claude" / "skills" / "rebuild-spec" / "extensions" / "scripts" / "build_client_package.cjs"

SHARETRIBE_REPO = Path("/home/pham.van.duc@sun-asterisk.com/github/sharetribe")
SHARETRIBE_DOCS = SHARETRIBE_REPO / "docs"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not available on PATH")

requires_sharetribe = pytest.mark.skipif(
    not SHARETRIBE_DOCS.is_dir(), reason="real sharetribe corpus not present on this machine"
)


# ---------------------------------------------------------------------------
# Fixture data + Node driver for the pure-render unit tests
# ---------------------------------------------------------------------------

_UI = {
    "start_here": "Start Here",
    "appendix": "Appendix — Repo Docs",
    "drill_labels": {"flows": "Flows", "features": "Features", "screens": "Screens", "traceability_matrix": "Traceability"},
    "pager": {"prev": "‹ Previous", "next": "Next ›", "reading": "Reading", "back_to_index": "back to index", "end_of_spine": "End of the reading order"},
}


def _page(rel_md: str, title: str) -> dict:
    return {"relMd": rel_md, "relHtml": re.sub(r"\.md$", ".html", rel_md), "title": title}


def _layers() -> list[dict]:
    return [
        {
            "layer": 1,
            "label": "1. Orientation",
            "intro": "Start here.",
            "entries": [
                {"num": 1, "kind": "file", "path": "system/overview.md", "key": "system_overview", "what": "desc"},
                {"num": 2, "kind": "file", "path": "generated/screen-list.md", "key": "screen_list", "what": "inventory"},
            ],
        },
        {
            "layer": 4,
            "label": "4. Deep dives",
            "intro": "Drill-downs.",
            "entries": [
                {"num": 10, "kind": "glob", "glob": "features/*/", "link": "features/", "key": "features", "what": "per-feature"},
                {"num": 11, "kind": "glob", "glob": "screens/*/spec.md", "link": "screens/", "key": "screens", "what": "per-screen"},
                {"num": 12, "kind": "file", "path": "generated/traceability-matrix.md", "key": "traceability_matrix", "what": "trace"},
            ],
        },
    ]


def _pages() -> list[dict]:
    return [
        _page("README.md", "Reading Guide"),
        _page("system/overview.md", "Overview <script>alert(1)</script>"),
        _page("generated/screen-list.md", "Screen List"),
        _page("features/README.md", "Features Index"),
        _page("features/F001_Login/functional-spec.md", "F001 Functional Spec"),
        _page("features/F001_Login/technical-spec.md", "F001 Technical Spec"),
        _page("screens/SCR001/spec.md", "Screen One"),
        _page("screens/SCR002/spec.md", "Screen Two"),
        _page("generated/traceability-matrix.md", "Traceability Matrix"),
        _page("decisions/ADR-0001.md", "ADR 0001"),
    ]


def _sidecar(ui=_UI) -> dict:
    return {
        "schemaVersion": 1,
        "lang": "en",
        "title": "Documentation Index — Reading Order",
        "quickPath": {"label": "Minimum fast read", "nums": [1, 2]},
        "roles": [{"key": "dev", "label": "New developer", "nums": [1]}],
        "layers": _layers(),
        "ui": ui,
    }


def _render(tmp_path: Path, sidecar, pages: list[dict], current_rel_html: str, project_name: str = "Demo") -> dict:
    """Build the model via the REAL `buildReadingModel()`, then render both
    the index body and the nav via the REAL `renderIndexBody()`/
    `renderNavList()` — never a re-implementation of either."""
    driver = tmp_path / "render-driver.cjs"
    driver.write_text(
        f"""'use strict';
const {{ buildReadingModel }} = require({json.dumps(str(READING_SPINE))});
const {{ renderNavList }} = require({json.dumps(str(PACKAGE_NAV))});
const {{ renderIndexBody }} = require({json.dumps(str(PACKAGE_INDEX_BODY))});
const sidecar = {json.dumps(sidecar)};
const pages = {json.dumps(pages)};
const model = buildReadingModel({{ sidecar, pages, projectName: {json.dumps(project_name)} }});
const navHtml = renderNavList(model, {json.dumps(current_rel_html)}, './');
const indexHtml = renderIndexBody({{
  model,
  quickPath: sidecar ? sidecar.quickPath : null,
  roles: sidecar ? sidecar.roles : null,
  projectName: {json.dumps(project_name)},
  pageCount: pages.length,
}});
console.log(JSON.stringify({{ navHtml, indexHtml }}));
""",
        encoding="utf-8",
    )
    result = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Pure-render unit tests
# ---------------------------------------------------------------------------


class TestNoOtherSection:
    def test_synthetic_index_has_no_other_heading(self, tmp_path: Path) -> None:
        out = _render(tmp_path, _sidecar(), _pages(), "system/overview.html")
        assert ">Other<" not in out["indexHtml"]
        assert ">Other<" not in out["navHtml"]

    def test_fallback_ui_null_index_still_has_no_other_heading(self, tmp_path: Path) -> None:
        """No sidecar at all -> ui is null -> the module falls back to its own
        literal labels, never the deleted bucket system's 'Other' catch-all."""
        out = _render(tmp_path, None, _pages(), "system/overview.html")
        assert ">Other<" not in out["indexHtml"]
        assert "Appendix" in out["indexHtml"]  # fallback label, still present


class TestGateLines:
    def test_screens_gate_points_at_screen_list(self, tmp_path: Path) -> None:
        out = _render(tmp_path, _sidecar(), _pages(), "system/overview.html")
        assert 'href="generated/screen-list.html"' in out["indexHtml"]
        assert "Gate:" in out["indexHtml"]

    def test_features_gate_points_at_features_index(self, tmp_path: Path) -> None:
        out = _render(tmp_path, _sidecar(), _pages(), "system/overview.html")
        assert 'href="features/README.html"' in out["indexHtml"]

    def test_screens_gate_absent_when_screen_list_unclaimed(self, tmp_path: Path) -> None:
        sidecar = _sidecar()
        sidecar["layers"][0]["entries"] = [sidecar["layers"][0]["entries"][0]]  # drop the screen_list entry
        pages = [p for p in _pages() if p["relMd"] != "generated/screen-list.md"]
        out = _render(tmp_path, sidecar, pages, "system/overview.html")
        assert 'href="generated/screen-list.html"' not in out["indexHtml"]


class TestEscaping:
    def test_page_title_html_is_escaped_in_both_views(self, tmp_path: Path) -> None:
        out = _render(tmp_path, _sidecar(), _pages(), "system/overview.html")
        assert "<script>alert(1)</script>" not in out["indexHtml"]
        assert "<script>alert(1)</script>" not in out["navHtml"]
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in out["indexHtml"]
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in out["navHtml"]


class TestActiveAndOpenState:
    def test_current_page_gets_active_class(self, tmp_path: Path) -> None:
        out = _render(tmp_path, _sidecar(), _pages(), "screens/SCR001/spec.html")
        assert 'href="./screens/SCR001/spec.html" class="active"' in out["navHtml"]
        # No other link carries the active class.
        assert out["navHtml"].count('class="active"') == 1

    def test_group_containing_current_page_is_open_sibling_group_is_not(self, tmp_path: Path) -> None:
        out = _render(tmp_path, _sidecar(), _pages(), "screens/SCR001/spec.html")
        nav = out["navHtml"]
        deep_dives_start = nav.index("4. Deep dives")
        # The <details> wrapping "4. Deep dives" (layer 4, which contains the
        # screens drill) must be open; walk back to its own opening tag.
        details_open_idx = nav.rindex("<details", 0, deep_dives_start)
        assert nav[details_open_idx : details_open_idx + len("<details open>")] == "<details open>"
        # The sibling "1. Orientation" group (does not contain the current
        # page) stays closed.
        orientation_start = nav.index("1. Orientation")
        orientation_details_idx = nav.rindex("<details", 0, orientation_start)
        assert nav[orientation_details_idx : orientation_details_idx + len("<details open>")] != "<details open>"

    def test_index_page_home_link_gets_active_class(self, tmp_path: Path) -> None:
        out = _render(tmp_path, _sidecar(), _pages(), "index.html")
        assert 'href="./index.html" class="active"' in out["navHtml"]


class TestStartHereBlock:
    def test_quick_path_and_roles_rendered_as_plain_numeric_paths(self, tmp_path: Path) -> None:
        out = _render(tmp_path, _sidecar(), _pages(), "system/overview.html")
        assert "1 → 2" in out["indexHtml"]
        assert "New developer" in out["indexHtml"]

    def test_start_here_heading_comes_from_sidecar_ui_not_hardcoded(self, tmp_path: Path) -> None:
        custom_ui = json.loads(json.dumps(_UI))
        custom_ui["start_here"] = "CUSTOM_START_HERE_LABEL"
        out = _render(tmp_path, _sidecar(ui=custom_ui), _pages(), "system/overview.html")
        assert "CUSTOM_START_HERE_LABEL" in out["indexHtml"]

    def test_fallback_no_sidecar_start_here_omits_quick_path(self, tmp_path: Path) -> None:
        out = _render(tmp_path, None, _pages(), "system/overview.html")
        assert "Start Here" in out["indexHtml"]  # fallback literal, no crash


class TestModuleSize:
    @pytest.mark.parametrize("module", ["package-nav.cjs", "package-index-body.cjs", "package-html-template.cjs"])
    def test_module_under_200_lines(self, module: str) -> None:
        lines = (LIB_DIR / module).read_text(encoding="utf-8").splitlines()
        assert len(lines) < 200, f"{module} is {len(lines)} lines, over the 200-line budget"

    def test_no_script_tag_added_beyond_mermaid_init(self) -> None:
        for module in ("package-nav.cjs", "package-index-body.cjs"):
            src = (LIB_DIR / module).read_text(encoding="utf-8")
            assert "<script" not in src


# ---------------------------------------------------------------------------
# End-to-end proofs through the real build_client_package.cjs wiring
# ---------------------------------------------------------------------------


def _run_build(repo_root: Path, docs_root: str, out: Path, *extra_args: str) -> subprocess.CompletedProcess:
    cmd = ["node", str(BUILD_SCRIPT), "--repo-root", str(repo_root), "--docs-root", docs_root, "--out", str(out), *extra_args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


_HREF_RE = re.compile(r'href="([^"]+)"')


def _relative_html_hrefs(html: str) -> list[str]:
    out = []
    for href in _HREF_RE.findall(html):
        if href.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = href.split("#", 1)[0]
        if target.endswith(".html"):
            out.append(target)
    return out


class TestRealCorpusLayeredIndex:
    @requires_sharetribe
    def test_no_other_section_on_real_corpus(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        result = _run_build(SHARETRIBE_REPO, "docs", out)
        assert result.returncode == 0, result.stderr
        index_html = (out / "index.html").read_text(encoding="utf-8")
        assert ">Other<" not in index_html

    @requires_sharetribe
    def test_layer_and_appendix_counts_match_measured_shape(self, tmp_path: Path) -> None:
        """3 / 3 / 7 numbered entries in layers 1-3; layer 4 totals 343
        (0 numbered entries + 342 drill items [flows 4, features 172 + its
        own README index, screens 165] + the 1 traceability page it carries
        conceptually); appendix 23 — matches
        reports/orchestrator-scouting-phase-03.md's F5 measurement exactly."""
        driver = tmp_path / "counts-driver.cjs"
        driver.write_text(
            f"""'use strict';
const {{ buildClientPackage }} = require({json.dumps(str(BUILD_SCRIPT))});
const result = buildClientPackage([
  '--repo-root', {json.dumps(str(SHARETRIBE_REPO))},
  '--docs-root', 'docs',
  '--out', {json.dumps(str(tmp_path / "out"))},
]);
const m = result.readingModel;
const byLayer = {{}};
for (const l of m.layers) {{
  const drillCount = l.drills.reduce((s, d) => s + d.items.length + (d.index ? 1 : 0), 0);
  byLayer[l.layer] = {{ entries: l.entries.length, drillCount }};
}}
console.log(JSON.stringify({{ byLayer, appendix: m.appendix.length, hasTrace: m.trace !== null }}));
""",
            encoding="utf-8",
        )
        result = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=180)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["byLayer"]["1"]["entries"] == 3
        assert payload["byLayer"]["2"]["entries"] == 3
        assert payload["byLayer"]["3"]["entries"] == 7
        assert payload["byLayer"]["4"]["entries"] == 0
        assert payload["byLayer"]["4"]["drillCount"] == 342
        assert payload["hasTrace"] is True
        assert payload["byLayer"]["4"]["drillCount"] + 1 == 343  # + the trace page
        assert payload["appendix"] == 23

    @requires_sharetribe
    def test_every_built_page_reachable_from_index_except_denylisted(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        result = _run_build(SHARETRIBE_REPO, "docs", out)
        assert result.returncode == 0, result.stderr

        index_html = (out / "index.html").read_text(encoding="utf-8")
        reachable = {href for href in _relative_html_hrefs(index_html)}
        # Resolve relative to the out root (index.html lives at the root, so
        # its hrefs need no prefix stripping).
        built_pages = {p.relative_to(out).as_posix() for p in out.rglob("*.html") if p.name != "index.html"}

        missing = built_pages - reachable
        assert not missing, f"{len(missing)} built page(s) unreachable from index.html: {sorted(missing)[:10]}"
        # The 2 path-scoped denylist targets (phase-02) never got built at all.
        assert not (out / "system" / "README.html").exists()
        assert not (out / "generated" / "README.html").exists()

    @requires_sharetribe
    def test_link_integrity_zero_broken_across_every_page(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        result = _run_build(SHARETRIBE_REPO, "docs", out)
        assert result.returncode == 0, result.stderr

        total = 0
        broken: list[str] = []
        for html_file in out.rglob("*.html"):
            html = html_file.read_text(encoding="utf-8")
            for href in _relative_html_hrefs(html):
                total += 1
                target = (html_file.parent / href).resolve()
                if not target.is_file():
                    broken.append(f"{html_file.relative_to(out)} -> {href}")
        assert total > 100000, f"suspiciously few hrefs parsed: {total}"
        assert not broken, f"{len(broken)}/{total} broken relative .html link(s): {broken[:10]}"


class TestRealVietnameseSidecar:
    @requires_sharetribe
    def test_vi_bundle_renders_vietnamese_chrome(self, tmp_path: Path) -> None:
        """Builds a REAL Vietnamese sidecar via the actual
        `write_reading_sidecar()` Python emitter (not a hand-authored
        fixture) against a small synthetic docs/ tree, then runs the real
        node bundler and asserts real Vietnamese literals in the rendered
        index and a leaf page's nav — not just `!= english`."""
        sys.path.insert(0, str(SCRIPTS_DIR))
        from _nav_sidecar_lib import write_reading_sidecar  # noqa: E402  (test-local import)

        repo = tmp_path / "repo"
        docs = repo / "docs"
        for rel in ("system/overview.md", "system/architecture.md", "system/glossary.md", "generated/entities.md"):
            path = docs / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {rel}\n\nBody.\n", encoding="utf-8")
        (docs / "decisions").mkdir(parents=True, exist_ok=True)
        (docs / "decisions" / "ADR-0001.md").write_text("# ADR 0001\n\nRepo-authored, not generated.\n", encoding="utf-8")

        write_reading_sidecar(str(docs), "vi")
        assert (docs / ".reading-order.json").is_file()

        out = tmp_path / "out"
        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        index_html = (out / "index.html").read_text(encoding="utf-8")
        leaf_html = (out / "system" / "overview.html").read_text(encoding="utf-8")

        assert "Bắt đầu tại đây" in index_html  # ui.start_here (vi)
        assert "Phụ lục — Tài liệu trong kho mã" in index_html  # ui.appendix (vi)
        assert "Định hướng — hệ thống là gì và tại sao" in index_html  # layer 1 label (vi)
        assert "Định hướng — hệ thống là gì và tại sao" in leaf_html  # same label in the leaf's own sidebar
        assert ">Other<" not in index_html
