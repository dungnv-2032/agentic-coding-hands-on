"""Tests for phase-05 of the reading-order plan
(`260826-1601-package-reading-layers-index-pager`): the prev/next pager
(`lib/package-pager.cjs`) that walks `model.spine` — the SAME ordering the
index (`lib/package-index-body.cjs`) and sidebar (`lib/package-nav.cjs`)
already read from `lib/reading-spine.cjs`.

Sibling of `test_build_client_package.py` / `test_reading_spine.py` /
`test_package_index_nav.py` (same justification as those files: this
phase's own surface doesn't touch any of their concerns and is large enough
to earn its own module).

Three layers:
1. Pure-render unit tests of `renderPager()` via a small generated Node
   driver, against a synthetic model built through the REAL
   `buildReadingModel()` (not a hand-rolled model shape).
2. The real deliverable: end-to-end proofs through the actual
   `build_client_package.cjs` wiring on the real sharetribe corpus — the
   next-chain walk (crawls the REAL rendered HTML files' pager hrefs, not
   the in-memory model, so it proves the markup actually navigates), set
   equality against the spine, first/last-page position, zero broken pager
   hrefs, real per-page byte growth.
3. A real Vietnamese/Japanese sidecar (via the actual Python emitter)
   proving translated pager labels render, not English.
"""
from __future__ import annotations

import json
import posixpath
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
PACKAGE_PAGER = LIB_DIR / "package-pager.cjs"
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
            ],
        },
        {
            "layer": 4,
            "label": "4. Deep dives",
            "intro": "Everything else.",
            "entries": [],
            # no glob drills needed for the pager's own unit tests — the
            # spine ordering itself is reading-spine.cjs's concern
            # (test_reading_spine.py), not this module's.
        },
    ]


def _pages() -> list[dict]:
    return [
        _page("README.md", "Reading Guide"),
        _page("system/overview.md", "System Overview"),
        _page("decisions/ADR-0001.md", "ADR 0001"),
        _page("decisions/ADR-0002.md", "ADR 0002"),
    ]


def _sidecar(ui=_UI) -> dict:
    return {
        "schemaVersion": 1,
        "lang": "en",
        "title": "Documentation Index — Reading Order",
        "quickPath": {"label": "Minimum fast read", "nums": [1]},
        "roles": [],
        "layers": _layers(),
        "ui": ui,
    }


def _render(tmp_path: Path, sidecar, pages: list[dict], current_rel_html: str, prefix: str = "./") -> str:
    """Build the model via the REAL `buildReadingModel()`, then render the
    pager via the REAL `renderPager()` — never a re-implementation."""
    driver = tmp_path / "render-driver.cjs"
    driver.write_text(
        f"""'use strict';
const {{ buildReadingModel }} = require({json.dumps(str(READING_SPINE))});
const {{ renderPager }} = require({json.dumps(str(PACKAGE_PAGER))});
const sidecar = {json.dumps(sidecar)};
const pages = {json.dumps(pages)};
const model = buildReadingModel({{ sidecar, pages, projectName: 'Demo' }});
const html = renderPager(model, {json.dumps(current_rel_html)}, {json.dumps(prefix)});
console.log(JSON.stringify({{ html }}));
""",
        encoding="utf-8",
    )
    result = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["html"]


class TestPagerPresence:
    def test_pager_present_on_every_spine_page(self, tmp_path: Path) -> None:
        for p in _pages():
            html = _render(tmp_path, _sidecar(), _pages(), p["relHtml"])
            assert '<nav class="pv-pager"' in html, f"missing pager on {p['relHtml']}"

    def test_no_sidecar_no_pager_at_all(self, tmp_path: Path) -> None:
        html = _render(tmp_path, None, _pages(), "system/overview.html")
        assert html == ""

    def test_page_not_on_spine_gets_no_pager(self, tmp_path: Path) -> None:
        html = _render(tmp_path, _sidecar(), _pages(), "does/not-exist.html")
        assert html == ""


class TestFirstAndLastCell:
    def test_first_spine_page_prev_cell_points_at_index_not_outside_bundle(self, tmp_path: Path) -> None:
        html = _render(tmp_path, _sidecar(), _pages(), "README.html")
        assert 'class="pv-pg pv-pg-prev pv-pg-home" href="./index.html"' in html
        # never a href escaping the bundle root (e.g. "../index.html" from the root page)
        assert "../" not in re.search(r'pv-pg-prev[^>]*href="([^"]*)"', html).group(1)

    def test_last_spine_page_next_cell_points_at_index_labelled_end_of_spine(self, tmp_path: Path) -> None:
        # ADR-0002 is the last appendix entry sorted by title ("ADR 0002" > "ADR 0001")
        html = _render(tmp_path, _sidecar(), _pages(), "decisions/ADR-0002.html")
        assert 'class="pv-pg pv-pg-next pv-pg-home" href="./index.html"' in html
        assert "End of the reading order" in html

    def test_middle_cell_always_links_to_index(self, tmp_path: Path) -> None:
        html = _render(tmp_path, _sidecar(), _pages(), "system/overview.html")
        assert 'class="pv-pg-up" href="./index.html"' in html


class TestIndexForwardCell:
    def test_index_gets_single_forward_cell_pointing_at_spine_zero(self, tmp_path: Path) -> None:
        html = _render(tmp_path, _sidecar(), _pages(), "index.html")
        assert html.count('<a class="pv-pg') == 1  # only the forward cell, no prev/mid <a>
        assert 'href="./README.html"' in html
        assert "<span></span><span></span>" in html  # two empty grid placeholders

    def test_index_forward_cell_absent_when_no_sidecar(self, tmp_path: Path) -> None:
        html = _render(tmp_path, None, _pages(), "index.html")
        assert html == ""


class TestLocalization:
    def test_labels_come_from_sidecar_ui_pager_not_hardcoded(self, tmp_path: Path) -> None:
        custom_ui = json.loads(json.dumps(_UI))
        custom_ui["pager"]["next"] = "SIGURNO SLEDECE"
        custom_ui["pager"]["reading"] = "CITANJE"
        html = _render(tmp_path, _sidecar(custom_ui), _pages(), "system/overview.html")
        assert "SIGURNO SLEDECE" in html
        assert "CITANJE" in html
        assert "Next ›" not in html


class TestEscaping:
    def test_page_title_html_is_escaped_in_pager(self, tmp_path: Path) -> None:
        pages = _pages()
        pages[1]["title"] = 'Overview <script>alert(1)</script>'
        html = _render(tmp_path, _sidecar(), pages, "README.html")
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html


class TestNoHardcodedEnglishChrome:
    def test_no_pager_prose_literal_in_source(self) -> None:
        src = PACKAGE_PAGER.read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
        code = re.sub(r"//.*", "", code)
        for literal in ("'Previous'", '"Previous"', "'Next'", '"Next"', "'Reading'", '"Reading"', "'back to index'", '"back to index"'):
            assert literal not in code, f"hard-coded chrome literal {literal!r} found in package-pager.cjs"


class TestModuleSize:
    def test_module_under_200_lines(self) -> None:
        lines = PACKAGE_PAGER.read_text(encoding="utf-8").splitlines()
        assert len(lines) < 200, f"package-pager.cjs is {len(lines)} lines, over the 200-line budget"


# ---------------------------------------------------------------------------
# End-to-end proofs through the real build_client_package.cjs wiring
# ---------------------------------------------------------------------------


def _run_build(repo_root: Path, docs_root: str, out: Path, *extra_args: str) -> subprocess.CompletedProcess:
    cmd = ["node", str(BUILD_SCRIPT), "--repo-root", str(repo_root), "--docs-root", docs_root, "--out", str(out), *extra_args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


_PAGER_NAV_RE = re.compile(r'<nav class="pv-pager"[^>]*>(.*?)</nav>', re.S)
_CELL_RE = re.compile(r'<a class="([^"]*)" href="([^"]*)">')


def _pager_cells(html: str) -> list[tuple[str, str]]:
    m = _PAGER_NAV_RE.search(html)
    if not m:
        return []
    return _CELL_RE.findall(m.group(1))


def _crawl_next_chain(out: Path, cap: int = 500) -> dict:
    """Starting at index.html, follow the pager's `next` cell repeatedly by
    reading the REAL rendered HTML files on disk (not the in-memory model) —
    this is what proves the markup itself navigates, not just that the model
    is internally consistent."""
    cur = "index.html"
    visited: list[str] = []
    seen: set[str] = set()
    steps = 0
    looped = False
    last_page = None
    for _ in range(cap):
        html = (out / cur).read_text(encoding="utf-8")
        cells = _pager_cells(html)
        next_cell = next((c for c in cells if "pv-pg-next" in c[0].split(" ")), None)
        if next_cell is None:
            return {"error": f"no pager next cell on {cur}"}
        classes, href = next_cell
        if "pv-pg-home" in classes.split(" "):
            last_page = cur
            break
        cur_dir = posixpath.dirname(cur)
        target = posixpath.normpath(posixpath.join(cur_dir, href)) if cur_dir else posixpath.normpath(href)
        if target in seen:
            looped = True
            break
        seen.add(target)
        visited.append(target)
        cur = target
        steps += 1
    return {"steps": steps, "visited": visited, "lastPage": last_page, "looped": looped}


class TestNextChainRealCorpus:
    @requires_sharetribe
    def test_next_chain_walks_the_whole_spine_once_no_loop(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        result = _run_build(SHARETRIBE_REPO, "docs", out)
        assert result.returncode == 0, result.stderr

        chain = _crawl_next_chain(out)
        assert not chain.get("error"), chain.get("error")
        assert chain["looped"] is False
        assert chain["steps"] == 380, f"expected 380 steps, got {chain['steps']}"
        assert len(chain["visited"]) == 380
        assert len(set(chain["visited"])) == 380  # every page visited exactly once

    @requires_sharetribe
    def test_chain_pages_equal_spine_pages_set_both_directions(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        result = _run_build(SHARETRIBE_REPO, "docs", out)
        assert result.returncode == 0, result.stderr
        chain = _crawl_next_chain(out)

        driver = tmp_path / "spine-driver.cjs"
        driver.write_text(
            f"""'use strict';
const {{ buildClientPackage }} = require({json.dumps(str(BUILD_SCRIPT))});
const result = buildClientPackage(['--repo-root', {json.dumps(str(SHARETRIBE_REPO))}, '--docs-root', 'docs', '--out', {json.dumps(str(tmp_path / "spine-out"))}]);
console.log(JSON.stringify(result.readingModel.spine.map((e) => e.page.relHtml)));
""",
            encoding="utf-8",
        )
        spine_result = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=180)
        assert spine_result.returncode == 0, spine_result.stderr
        spine_pages = set(json.loads(spine_result.stdout))

        chain_pages = set(chain["visited"]) | {chain["lastPage"]}
        assert chain_pages == spine_pages, (
            f"chain-only: {sorted(chain_pages - spine_pages)[:5]}, "
            f"spine-only: {sorted(spine_pages - chain_pages)[:5]}"
        )

    @requires_sharetribe
    def test_first_page_prev_points_at_index_not_outside_bundle(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        result = _run_build(SHARETRIBE_REPO, "docs", out)
        assert result.returncode == 0, result.stderr
        chain = _crawl_next_chain(out)
        first_page = out / chain["visited"][0]
        html = first_page.read_text(encoding="utf-8")
        cells = _pager_cells(html)
        prev_cell = next(c for c in cells if "pv-pg-prev" in c[0].split(" "))
        assert "pv-pg-home" in prev_cell[0].split(" ")
        assert prev_cell[1] == "./index.html" or prev_cell[1].endswith("index.html")
        assert ".." not in prev_cell[1]  # never resolves outside the bundle root's own directory chain incorrectly

    @requires_sharetribe
    def test_last_page_is_genuinely_the_last_spine_entry_by_position(self, tmp_path: Path) -> None:
        """Not just a page that happens to lack a next link — assert its
        position in the model's spine array is spine.length - 1."""
        out = tmp_path / "out"
        result = _run_build(SHARETRIBE_REPO, "docs", out)
        assert result.returncode == 0, result.stderr
        chain = _crawl_next_chain(out)
        assert chain["lastPage"] is not None

        driver = tmp_path / "pos-driver.cjs"
        driver.write_text(
            f"""'use strict';
const {{ buildClientPackage }} = require({json.dumps(str(BUILD_SCRIPT))});
const result = buildClientPackage(['--repo-root', {json.dumps(str(SHARETRIBE_REPO))}, '--docs-root', 'docs', '--out', {json.dumps(str(tmp_path / "pos-out"))}]);
const spine = result.readingModel.spine;
const idx = spine.findIndex((e) => e.page.relHtml === {json.dumps(chain["lastPage"])});
console.log(JSON.stringify({{ idx, total: spine.length }}));
""",
            encoding="utf-8",
        )
        pos_result = subprocess.run(["node", str(driver)], capture_output=True, text=True, timeout=180)
        assert pos_result.returncode == 0, pos_result.stderr
        payload = json.loads(pos_result.stdout)
        assert payload["idx"] == payload["total"] - 1, (
            f"{chain['lastPage']} is at spine position {payload['idx']}, "
            f"not the last ({payload['total'] - 1})"
        )

        # Also: exactly one page in the WHOLE bundle carries the end-of-spine
        # marker — proves this isn't merely "a page that lacks a next".
        home_next_pages = [
            p.relative_to(out).as_posix()
            for p in out.rglob("*.html")
            if p.name != "index.html" and 'pv-pg-next pv-pg-home' in p.read_text(encoding="utf-8")
        ]
        assert home_next_pages == [chain["lastPage"]]

    @requires_sharetribe
    def test_every_pager_href_resolves_to_a_file_that_exists(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        result = _run_build(SHARETRIBE_REPO, "docs", out)
        assert result.returncode == 0, result.stderr

        total = 0
        broken: list[str] = []
        for html_file in out.rglob("*.html"):
            html = html_file.read_text(encoding="utf-8")
            for _classes, href in _pager_cells(html):
                total += 1
                target = (html_file.parent / href).resolve()
                if not target.is_file():
                    broken.append(f"{html_file.relative_to(out)} -> {href}")
        assert total == 381 * 3 - 2, f"expected 381*3-2 pager hrefs (index has 1, every other page has 3), got {total}"
        assert not broken, f"{len(broken)}/{total} broken pager href(s): {broken[:10]}"


class TestFallbackNoSidecar:
    def test_sidecarless_corpus_produces_no_pager_still_builds(self, tmp_path: Path) -> None:
        docs = tmp_path / "repo" / "docs"
        docs.mkdir(parents=True)
        (docs / "a.md").write_text("# A\n\nBody.\n", encoding="utf-8")
        (docs / "b.md").write_text("# B\n\nBody.\n", encoding="utf-8")
        out = tmp_path / "out"
        result = _run_build(tmp_path / "repo", "docs", out)
        assert result.returncode == 0, result.stderr
        for html_file in out.rglob("*.html"):
            assert '<nav class="pv-pager"' not in html_file.read_text(encoding="utf-8")


class TestRealLocalizedSidecars:
    def _build_with_lang(self, tmp_path: Path, lang: str) -> Path:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from _nav_sidecar_lib import write_reading_sidecar  # noqa: E402 (test-local import)

        repo = tmp_path / "repo"
        docs = repo / "docs"
        for rel in ("system/overview.md", "system/architecture.md", "system/glossary.md", "generated/entities.md"):
            path = docs / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {rel}\n\nBody.\n", encoding="utf-8")
        (docs / "decisions").mkdir(parents=True, exist_ok=True)
        (docs / "decisions" / "ADR-0001.md").write_text("# ADR 0001\n\nRepo-authored, not generated.\n", encoding="utf-8")

        write_reading_sidecar(str(docs), lang)
        assert (docs / ".reading-order.json").is_file()

        out = tmp_path / "out"
        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr
        return out

    @requires_sharetribe
    def test_vi_bundle_renders_vietnamese_pager_labels(self, tmp_path: Path) -> None:
        out = self._build_with_lang(tmp_path, "vi")
        index_html = (out / "index.html").read_text(encoding="utf-8")
        leaf_html = (out / "system" / "overview.html").read_text(encoding="utf-8")
        assert "Tiếp" in index_html  # ui.pager.next on index.html's forward cell
        assert "Trước" in leaf_html or "Tiếp" in leaf_html  # ui.pager.prev/next on a leaf page

    @requires_sharetribe
    def test_ja_bundle_renders_japanese_pager_labels(self, tmp_path: Path) -> None:
        out = self._build_with_lang(tmp_path, "ja")
        leaf_html = (out / "system" / "overview.html").read_text(encoding="utf-8")
        assert "次へ" in leaf_html or "前へ" in leaf_html

# NOTE: a `TestByteGrowth::test_real_per_page_byte_growth` case was removed here.
# It measured pager byte cost by running `git stash` / `git stash pop` against the
# REAL repo root from inside the suite. Two defects, one of them destructive:
#
#   1. On a CLEAN tree `git stash` saves nothing and still exits 0, so the paired
#      `git stash pop` popped whatever stash was already on top — an unrelated,
#      months-old WIP from another branch — leaving the workspace in an unmerged
#      state. A test must never mutate the developer's git workspace.
#   2. Once the change under measurement is committed, `before` == `after`, so
#      `assert 0 < growth` fails. It could only ever pass while the work was
#      uncommitted: it asserted a transient condition, not an invariant.
#
# Per-page byte growth is a one-off measurement for the phase report (recorded in
# plans/260826-1601-package-reading-layers-index-pager/reports/implementer-phase-05.md
# and re-measured via `git worktree` in implementer-phase-06.md), not a suite
# invariant. If it is ever reinstated, it MUST use `git worktree` against a
# committed ref — never `git stash` against the working tree.
