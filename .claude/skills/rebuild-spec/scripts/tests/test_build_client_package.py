"""Tests for build_client_package.cjs — the `--package` EXPORT-tier pass engine.

Shells out to `node` against a tiny synthetic docs/ corpus built under `tmp_path`.
Skips (rather than fails) if `node` is unavailable on PATH — this pass is
Node-based (it reuses markdown-novel-viewer's renderer), unlike every other
rebuild-spec validator in this suite which is pure-Python stdlib.
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

BUILD_SCRIPT = (
    REPO_ROOT / "claude" / "skills" / "rebuild-spec" / "extensions" / "scripts" / "build_client_package.cjs"
)

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not available on PATH")


def _run_build(repo_root: Path, docs_root: str, out: Path, *extra_args: str) -> subprocess.CompletedProcess:
    cmd = [
        "node",
        str(BUILD_SCRIPT),
        "--repo-root",
        str(repo_root),
        "--docs-root",
        docs_root,
        "--out",
        str(out),
        *extra_args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_corpus(repo_root: Path, docs_dirname: str = "docs") -> Path:
    """A minimal-but-representative docs/ corpus: overview + a feature spec with
    a mermaid fence + every internal-sidecar shape the denylist must exclude."""
    docs = repo_root / docs_dirname
    _write(
        docs / "system" / "overview.md",
        "# System Overview\n\n**Project**: DemoApp\n\nOverview body.\n",
    )
    _write(
        docs / "generated" / "feature-list.md",
        "# Feature List\n\n| Code | Name |\n|---|---|\n| F001 | Login |\n",
    )
    _write(
        docs / "features" / "F001_Login" / "technical-spec.md",
        "# F001 Login\n\n```mermaid\nsequenceDiagram\n  User->>App: Login\n```\n",
    )
    # Denylist targets — every shape from research/researcher-02-package-mechanics.md Q3.
    _write(docs / "generated" / "confidence-report_feature-list.md", "# internal sidecar\n")
    _write(docs / "system" / "overview.draft.md", "# pre-promotion draft\n")
    _write(docs / ".rebuild-state.json", "{}")
    _write(docs / ".nav-metadata.json", "{}")
    _write(docs / ".layout-migrated", "")
    _write(docs / "component_profile.json", "{}")
    _write(docs / "generated" / "shard-manifest-01.json", "{}")
    return docs


class TestExclusionDenylist:
    def test_internal_sidecars_absent_from_bundle(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        html_files = {p.relative_to(out).as_posix() for p in out.rglob("*.html")}
        assert "system/overview.html" in html_files
        assert "features/F001_Login/technical-spec.html" in html_files
        assert "generated/feature-list.html" in html_files

        # None of the denylisted sources produced a page.
        assert not any("confidence-report" in f for f in html_files)
        assert not any("overview.draft" in f for f in html_files)
        # Only the 3 legitimate docs + index.html were emitted (4 total).
        assert len(html_files) == 4

    def test_json_and_sentinel_files_never_globbed(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        all_files = [p.name for p in out.rglob("*") if p.is_file()]
        assert ".rebuild-state.json" not in all_files
        assert ".nav-metadata.json" not in all_files
        assert ".layout-migrated" not in all_files
        assert "component_profile.json" not in all_files


class TestPathScopedDenylist:
    """Phase-02: `system/README.md` and `generated/README.md` are per-directory
    nav indexes whose entire job the bundle's own sidebar already does. The
    basename denylist (`isDenylisted`) can't express "drop these two files but
    not other README.md files" — a `README.md` pattern would also kill
    `docs/README.md` (Start Here) and every `features/*/README.md` reading
    guide. `isDenylistedPath` is path-scoped (root-relative, POSIX, exact
    match) so only the two named locations are dropped."""

    def _make_readme_corpus(self, repo_root: Path, feature_count: int = 43) -> Path:
        docs = repo_root / "docs"
        _write(docs / "README.md", "# Start Here\n\nRoot reading guide.\n")
        _write(docs / "system" / "README.md", "# System docs index\n\nPer-directory nav.\n")
        _write(docs / "system" / "overview.md", "# System Overview\n\n**Project**: DemoApp\n")
        _write(docs / "generated" / "README.md", "# Generated docs index\n\nPer-directory nav.\n")
        _write(docs / "generated" / "feature-list.md", "# Feature List\n")
        for i in range(1, feature_count + 1):
            code = f"F{i:03d}"
            _write(docs / "features" / f"{code}_Feature" / "README.md", f"# {code} reading guide\n")
        return docs

    def test_system_and_generated_readme_absent_from_bundle(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        self._make_readme_corpus(repo)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        html_files = {p.relative_to(out).as_posix() for p in out.rglob("*.html")}
        assert "system/README.html" not in html_files
        assert "generated/README.html" not in html_files

    def test_root_readme_survives(self, tmp_path: Path) -> None:
        """Negative test — this is the one that would silently break if a
        basename pattern were used as a shortcut instead of a path-scoped one."""
        repo = tmp_path / "repo"
        self._make_readme_corpus(repo)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        html_files = {p.relative_to(out).as_posix() for p in out.rglob("*.html")}
        assert "README.html" in html_files

    def test_all_43_feature_readmes_survive(self, tmp_path: Path) -> None:
        """Assert the count, not a spot check — a basename shortcut would drop
        all 43 silently and a spot check on one or two would miss it."""
        repo = tmp_path / "repo"
        self._make_readme_corpus(repo, feature_count=43)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        html_files = {p.relative_to(out).as_posix() for p in out.rglob("*.html")}
        feature_readmes = [
            f for f in html_files if f.startswith("features/") and f.endswith("/README.html")
        ]
        assert len(feature_readmes) == 43, (
            f"expected 43 feature README pages, got {len(feature_readmes)}: {sorted(feature_readmes)}"
        )

    def test_isdenylistedpath_exact_match_unit(self) -> None:
        """Unit-level pin on the fix itself, independent of a full build.
        Exact-match semantics: only the two named root-relative paths are
        denied; the same basename elsewhere (root, or inside a feature dir)
        is untouched."""
        denylist_path = str(
            REPO_ROOT
            / "claude"
            / "skills"
            / "rebuild-spec"
            / "extensions"
            / "scripts"
            / "lib"
            / "package-denylist.cjs"
        )
        script = (
            "const {isDenylistedPath} = require(process.argv[1]); "
            "const paths = process.argv.slice(2); "
            "console.log(JSON.stringify(paths.map(isDenylistedPath)));"
        )
        result = subprocess.run(
            [
                "node",
                "-e",
                script,
                denylist_path,
                "system/README.md",
                "generated/README.md",
                "README.md",
                "features/F001_Login/README.md",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        matches = json.loads(result.stdout)
        assert matches == [True, True, False, False]


def _make_perlang_corpus(repo_root: Path, primary_lang: str = "en", secondary_langs: tuple[str, ...] = ("jp", "vi")) -> Path:
    """A per-lang corpus matching the REAL on-disk convention (verified against
    a real sharetribe-shaped repo, not the `resolve_docs_root(..., multilang=True)`
    formula): `.rebuild-state.json` registers `primary_lang` + `translations{}`
    at the OUTER `docs/` root; primary content lives at `docs/<primary>/` if that
    directory exists, else at bare `docs/`; every secondary lives at `docs/<lang>/`
    nested inside that same outer root."""
    docs = repo_root / "docs"
    translations = {lang: {"last_translate_run_sha": "deadbeef"} for lang in secondary_langs}
    _write(
        docs / ".rebuild-state.json",
        json.dumps({"primary_lang": primary_lang, "translations": translations}),
    )
    primary_dir = docs if primary_lang == "en" else docs / primary_lang
    _write(
        primary_dir / "system" / "overview.md",
        f"# System Overview\n\n**Project**: DemoApp\n\nPRIMARY_{primary_lang.upper()}_MARKER\n",
    )
    _write(
        primary_dir / "generated" / "feature-list.md",
        "# Feature List\n\n| Code | Name |\n|---|---|\n| F001 | Login |\n",
    )
    for lang in secondary_langs:
        _write(
            docs / lang / "system" / "overview.md",
            f"# System Overview ({lang})\n\n**Project**: DemoApp\n\n{lang.upper()}_MARKER\n",
        )
    return docs


class TestLangResolution:
    def test_default_docs_root_used_when_flag_omitted(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo, docs_dirname="docs")
        out = tmp_path / "out"

        cmd = ["node", str(BUILD_SCRIPT), "--repo-root", str(repo), "--out", str(out)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stderr
        assert (out / "system" / "overview.html").exists()

    def test_lang_en_bundles_primary_only_zero_secondary_pages(self, tmp_path: Path) -> None:
        """Sharetribe-shaped regression: en-primary per-lang corpus, primary content
        at BARE docs/ (docs/en/ never exists), secondaries nested at docs/jp/, docs/vi/
        — `--lang en` must exclude both secondary trees entirely."""
        repo = tmp_path / "repo"
        _make_perlang_corpus(repo, primary_lang="en", secondary_langs=("jp", "vi"))
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out, "--lang", "en")
        assert result.returncode == 0, result.stderr
        assert "lang: en" in result.stdout
        assert "excluded: jp, vi" in result.stdout

        html_files = {p.relative_to(out).as_posix() for p in out.rglob("*.html")}
        assert "system/overview.html" in html_files
        assert not any(f.startswith("jp/") or f.startswith("vi/") for f in html_files)

        overview = (out / "system" / "overview.html").read_text(encoding="utf-8")
        assert "PRIMARY_EN_MARKER" in overview
        assert "JP_MARKER" not in overview
        assert "VI_MARKER" not in overview

    def test_lang_omitted_defaults_to_primary_same_as_explicit_en(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_perlang_corpus(repo, primary_lang="en", secondary_langs=("jp", "vi"))
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)  # no --lang
        assert result.returncode == 0, result.stderr
        assert "lang: en" in result.stdout

        html_files = {p.relative_to(out).as_posix() for p in out.rglob("*.html")}
        assert not any(f.startswith("jp/") or f.startswith("vi/") for f in html_files)
        overview = (out / "system" / "overview.html").read_text(encoding="utf-8")
        assert "PRIMARY_EN_MARKER" in overview

    def test_lang_jp_resolves_nested_secondary_root(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_perlang_corpus(repo, primary_lang="en", secondary_langs=("jp", "vi"))
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out, "--lang", "jp")
        assert result.returncode == 0, result.stderr
        assert "lang: jp" in result.stdout

        overview = (out / "system" / "overview.html").read_text(encoding="utf-8")
        assert "JP_MARKER" in overview
        assert "PRIMARY_EN_MARKER" not in overview
        assert "VI_MARKER" not in overview

    def test_unregistered_lang_errors_cleanly(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_perlang_corpus(repo, primary_lang="en", secondary_langs=("jp", "vi"))
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out, "--lang", "de")
        assert result.returncode != 0
        assert "unknown language 'de'" in result.stderr
        assert "en" in result.stderr and "jp" in result.stderr and "vi" in result.stderr

    def test_non_en_primary_resolves_nested_primary_root(self, tmp_path: Path) -> None:
        """Verified convention also covers a non-en primary: docs/vi/ IS the
        primary root (already nested), `en` is the lone secondary."""
        repo = tmp_path / "repo"
        _make_perlang_corpus(repo, primary_lang="vi", secondary_langs=("en",))
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out, "--lang", "vi")
        assert result.returncode == 0, result.stderr
        assert "lang: vi" in result.stdout

        overview = (out / "system" / "overview.html").read_text(encoding="utf-8")
        assert "PRIMARY_VI_MARKER" in overview


class TestLangPathTraversalGuard:
    """Security regression: every language code this pass touches (`--lang`,
    `.rebuild-state.json`'s `primary_lang`, every `translations` key) is
    untrusted input fed into `path.join(docsRoot, code)` inside
    lib/resolve-lang-root.cjs. A crafted code containing `/`, `\\`, or `.`
    (e.g. `"../secret"`) must never reach `path.join`/`isDir` — it must be
    rejected up front with a named error, mirroring the Python side's guard
    (`_lang_lib.py` `normalize_lang`'s `_PATH_UNSAFE_RE`, Sec-F1)."""

    def test_malicious_primary_lang_traversal_is_rejected_and_never_read(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        docs = repo / "docs"
        # ".." + "/secret" resolves to a sibling of docs/ — still inside tmp_path
        # so the test can prove the traversal target was never touched, without
        # escaping the whole tmp tree.
        _write(
            docs / ".rebuild-state.json",
            json.dumps({"primary_lang": "../secret", "translations": {"jp": {}}}),
        )
        _write(docs / "system" / "overview.md", "# Overview\n\n**Project**: DemoApp\n")
        secret = repo / "secret"
        _write(secret / "system" / "overview.md", "# SECRET_MARKER — must never be bundled\n")
        out = tmp_path / "out"

        # Default invocation — no --lang needed: primary_lang alone drives the
        # vulnerable path.join in the buggy version of this code.
        result = _run_build(repo, "docs", out)
        assert result.returncode != 0
        assert "path-unsafe language code" in result.stderr
        assert "primary_lang" in result.stderr
        assert "../secret" in result.stderr
        # The traversal target must never have been read or bundled, and no
        # output must have been written at all.
        assert not out.exists()

    def test_malicious_translations_key_traversal_is_rejected(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        docs = repo / "docs"
        _write(
            docs / ".rebuild-state.json",
            json.dumps({"primary_lang": "en", "translations": {"../y": {}}}),
        )
        _write(docs / "system" / "overview.md", "# Overview\n\n**Project**: DemoApp\n")
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode != 0
        assert "path-unsafe language code" in result.stderr
        assert "translations key" in result.stderr
        assert "../y" in result.stderr
        assert not out.exists()

    def test_slash_containing_translations_key_traversal_is_rejected(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        docs = repo / "docs"
        _write(
            docs / ".rebuild-state.json",
            json.dumps({"primary_lang": "en", "translations": {"a/b": {}}}),
        )
        _write(docs / "system" / "overview.md", "# Overview\n\n**Project**: DemoApp\n")
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode != 0
        assert "path-unsafe language code" in result.stderr
        assert "a/b" in result.stderr
        assert not out.exists()

    def test_absolute_path_lang_flag_is_rejected(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out, "--lang", "/etc")
        assert result.returncode != 0
        assert "path-unsafe language code" in result.stderr
        assert "--lang" in result.stderr
        assert not out.exists()

    def test_translations_as_array_is_treated_as_malformed_single_lang(self, tmp_path: Path) -> None:
        """Fix 4: `typeof [] === 'object'` in JS — without an explicit
        Array.isArray guard, a `translations` array would leak its numeric
        indices as bogus "language codes". Treated the same as any other
        malformed state: ignored, falls back to single-lang."""
        repo = tmp_path / "repo"
        docs = repo / "docs"
        _write(
            docs / ".rebuild-state.json",
            json.dumps({"primary_lang": "en", "translations": ["jp", "vi"]}),
        )
        _write(docs / "system" / "overview.md", "# Overview\n\n**Project**: DemoApp\n")
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr
        assert "lang: en" in result.stdout
        assert "excluded:" not in result.stdout
        assert (out / "system" / "overview.html").exists()


class TestMermaidRendering:
    def test_mermaid_fence_becomes_pre_mermaid(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        spec_html = (out / "features" / "F001_Login" / "technical-spec.html").read_text(encoding="utf-8")
        assert '<pre class="mermaid">' in spec_html
        assert "sequenceDiagram" in spec_html
        # marked's fenced code block must NOT survive as a plain <pre><code> for mermaid content.
        assert "<code class=\"hljs language-mermaid\">" not in spec_html


class TestSelfContainedOutput:
    def test_every_page_is_relative_and_offline_safe(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        assert (out / "assets" / "mermaid.min.js").exists()
        assert (out / "assets" / "package-shell.css").exists()
        # Vendored classic UMD bundle: no bare `import` statements, exposes a global.
        mermaid_js = (out / "assets" / "mermaid.min.js").read_text(encoding="utf-8")
        assert not mermaid_js.lstrip().startswith("import ")
        assert "mermaid" in mermaid_js[:200].lower()

        html_files = list(out.rglob("*.html"))
        assert html_files, "expected at least one generated page"
        for html_file in html_files:
            text = html_file.read_text(encoding="utf-8")
            assert 'type="module"' not in text
            assert "http://" not in text
            assert "https://" not in text
            assert "cdn.jsdelivr.net" not in text
            assert "assets/mermaid.min.js" in text
            assert "assets/package-shell.css" in text

    def test_index_lists_every_page(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        index_html = (out / "index.html").read_text(encoding="utf-8")
        assert "system/overview.html" in index_html
        assert "features/F001_Login/technical-spec.html" in index_html
        assert "generated/feature-list.html" in index_html


class TestIdempotentRerun:
    def test_rerun_overwrites_and_drops_stale_pages(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"

        first = _run_build(repo, "docs", out)
        assert first.returncode == 0, first.stderr
        stale_file = out / "features" / "F001_Login" / "technical-spec.html"
        assert stale_file.exists()

        # Remove the source doc, then re-run: the stale generated page must not survive.
        (repo / "docs" / "features" / "F001_Login" / "technical-spec.md").unlink()

        second = _run_build(repo, "docs", out)
        assert second.returncode == 0, second.stderr
        assert not stale_file.exists()
        assert (out / "system" / "overview.html").exists()

    def test_rerun_is_stable_when_corpus_unchanged(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"

        first = _run_build(repo, "docs", out)
        assert first.returncode == 0, first.stderr
        first_html = (out / "system" / "overview.html").read_text(encoding="utf-8")

        second = _run_build(repo, "docs", out)
        assert second.returncode == 0, second.stderr
        second_html = (out / "system" / "overview.html").read_text(encoding="utf-8")

        assert first_html == second_html


class TestNoMarkdownCorpus:
    def test_empty_corpus_after_exclusions_errors_cleanly(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        docs = repo / "docs"
        _write(docs / "confidence-report_only.md", "# only a sidecar\n")
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode != 0
        assert "no markdown files found" in result.stderr


class TestXssSanitization:
    """CRITICAL regression coverage: renderMarkdownFile() does not sanitize raw
    HTML in markdown PROSE (only fenced-code content gets escaped by its own
    mermaid/hljs handling) — --package closes that gap itself, at the boundary
    in lib/sanitize-markdown-source.cjs + lib/render-sanitized.cjs. These tests
    prove the fix with the exact attack shapes the reviewer reproduced."""

    XSS_DOC = """# XSS Fixture

**Project**: DemoApp

Normal prose with an ampersand: AT&T. Also 1 < 2 and 3 > 2.

<script>alert(1)</script>

<img src=x onerror=alert(1)>

> A blockquote with <b>raw html</b> inside it.

## A Table

| Col A | Col B |
|-------|-------|
| 1     | 2     |

A [normal link](https://example.com) and a heading below.

## Another Heading

```mermaid
flowchart TD
  A --> B
```
"""

    def _build_fixture(self, tmp_path: Path) -> Path:
        repo = tmp_path / "repo"
        _write(repo / "docs" / "system" / "overview.md", self.XSS_DOC)
        _write(
            repo / "docs" / "generated" / "feature-list.md",
            "# Feature List\n\n| Code | Name |\n|---|---|\n| F001 | Login |\n",
        )
        out = tmp_path / "out"
        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr
        return out / "system" / "overview.html"

    def test_script_tag_in_prose_never_survives_executable(self, tmp_path: Path) -> None:
        html = self._build_fixture(tmp_path).read_text(encoding="utf-8")
        assert "<script>alert" not in html
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html

    def test_img_onerror_in_prose_never_survives_executable(self, tmp_path: Path) -> None:
        html = self._build_fixture(tmp_path).read_text(encoding="utf-8")
        # No live <img> tag exists at all — the whole thing was neutralized to
        # literal text, so there is no element for a real `onerror` handler to
        # attach to (the substring "onerror=" legitimately still appears, but
        # only inside the escaped `&lt;img ...&gt;` text below, never as a real
        # HTML attribute).
        assert "<img" not in html
        assert "&lt;img src=x onerror=alert(1)&gt;" in html

    def test_raw_html_inside_blockquote_is_neutralized_but_blockquote_still_renders(
        self, tmp_path: Path
    ) -> None:
        html = self._build_fixture(tmp_path).read_text(encoding="utf-8")
        assert "<blockquote>" in html
        assert "<b>raw html</b>" not in html
        assert "&lt;b&gt;raw html&lt;/b&gt;" in html

    def test_normal_markdown_constructs_still_render_correctly(self, tmp_path: Path) -> None:
        html = self._build_fixture(tmp_path).read_text(encoding="utf-8")
        # Headings
        assert "<h1" in html and "XSS Fixture" in html
        assert "<h2" in html and "A Table" in html
        # Table
        assert "<table>" in html and "<th>Col A</th>" in html and "<td>1</td>" in html
        # Link
        assert '<a href="https://example.com">normal link</a>' in html
        # Ampersand and angle-bracket prose still escaped exactly as marked itself would
        assert "AT&amp;T" in html
        assert "1 &lt; 2 and 3 &gt; 2" in html

    def test_mermaid_fence_unaffected_by_sanitization(self, tmp_path: Path) -> None:
        html = self._build_fixture(tmp_path).read_text(encoding="utf-8")
        assert '<pre class="mermaid">flowchart TD\n  A --&gt; B</pre>' in html

    def test_doc_without_raw_html_is_byte_identical_to_unsanitized_render(self, tmp_path: Path) -> None:
        """When there's nothing to neutralize, the sanitize-then-render path
        must not alter output (no accidental double-escaping of clean docs)."""
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"
        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        html = (out / "system" / "overview.html").read_text(encoding="utf-8")
        assert "Overview body." in html
        assert "&amp;amp;" not in html
        assert "&lt;" not in html  # nothing to escape in this clean fixture


class TestStrayTempFileSweep:
    """Reviewer round-2 regression: render-sanitized.cjs's sanitized temp copy
    (`.rebuild-package-tmp.<hex>.md`) is written inside the real docs/ source
    tree, and Node's try/finally is not guaranteed to run on a hard process
    kill mid-render — a crash can strand that temp file where it is not yet
    denylisted-away and would get bundled as a bogus extra page on the next
    run. Belt: build_client_package.cjs sweeps and deletes any stray copies
    before the walk. Suspenders: package-denylist.cjs also denies the pattern
    outright, in case a stray somehow survives the sweep."""

    def test_stray_temp_file_is_swept_and_absent_from_bundle(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo)
        stray = repo / "docs" / "features" / "F001_Login" / ".rebuild-package-tmp.deadbeef.md"
        _write(stray, "# Stray sanitized copy from a crashed prior run\n")
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        # (i) swept from docsRoot itself
        assert not stray.exists()
        # (ii) never bundled as a bogus extra page
        html_files = {p.relative_to(out).as_posix() for p in out.rglob("*.html")}
        assert not any("rebuild-package-tmp" in f for f in html_files)
        assert len(html_files) == 4  # unchanged from the plain _make_corpus() count


class TestProjectNameTraversalGuard:
    """M1 regression pin. `**Project**:` is repo CONTENT, not a CLI flag, so its value is
    untrusted input. sanitizeProjectName strips `/` and `\\` but deliberately KEEPS `.`, so
    a value of exactly "." or ".." used to survive as a live path segment. It was harmless
    only because path.join(repoRoot, 'client-package', '..') collapses to exactly repoRoot,
    which safe-rimraf refuses by exact equality — a coincidence of today's path shape, not a
    boundary. Insert one more segment between 'client-package' and the project name and the
    same input would target a sibling directory instead. Pinned here so a future edit cannot
    silently reintroduce the gap.
    """

    def _sanitize(self, value: str) -> str:
        lib = (
            REPO_ROOT / "claude" / "skills" / "rebuild-spec" / "extensions"
            / "scripts" / "lib" / "resolve-project-name.cjs"
        )
        result = subprocess.run(
            [
                "node",
                "-e",
                "const {sanitizeProjectName} = require(process.argv[1]); "
                "process.stdout.write(sanitizeProjectName(process.argv[2]));",
                str(lib),
                value,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr
        return result.stdout

    def test_dotdot_is_rejected(self) -> None:
        assert self._sanitize("..") == "Project"

    def test_single_dot_is_rejected(self) -> None:
        assert self._sanitize(".") == "Project"

    def test_padded_dotdot_is_rejected(self) -> None:
        """Trimmed before the segment check, so whitespace cannot smuggle it through."""
        assert self._sanitize("  ..  ") == "Project"

    def test_traversal_path_collapses_to_one_safe_segment(self) -> None:
        """A multi-segment traversal is not rejected outright — the separators are stripped,
        which is sufficient: the result is a single directory name containing dots, which
        cannot walk anywhere."""
        out = self._sanitize("../../etc")
        assert "/" not in out and "\\" not in out
        assert out == ".._.._etc"

    def test_ordinary_name_is_untouched(self) -> None:
        """Guards against over-correction — the fix must not mangle legitimate names."""
        assert self._sanitize("VerifyProject-1.2") == "VerifyProject-1.2"


class TestSafeRimrafGuard:
    """Fix 5: the idempotent-rebuild wipe refuses catastrophic delete targets."""

    def test_refuses_when_out_equals_repo_root(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo)

        result = _run_build(repo, "docs", repo)  # --out == --repo-root
        assert result.returncode != 0
        assert "refusing to delete" in result.stderr
        # The repo (and its docs/) must survive the refused delete.
        assert (repo / "docs" / "system" / "overview.md").exists()

    def test_allows_explicit_out_outside_repo_root(self, tmp_path: Path) -> None:
        # Every other test in this file already exercises this path (--out is a
        # tmp_path sibling of --repo-root), but assert it explicitly here too.
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "elsewhere" / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr
        assert (out / "index.html").exists()


# ---------------------------------------------------------------------------
# RW-1 / RW-2 (phase-00 D-a, phase-04 plan) — the api-doc-semantic-review-report
# leak and the docs-sweep method fix that catches the *next* one.
# ---------------------------------------------------------------------------

API_DOC_SEMANTIC_REVIEW_FIXTURE = """---
passed: 3
failed: 1
warnings: 2
---
# API Doc Semantic Review Report

## Passed Checks
- SR-1 field types match schema
- SR-2 required fields documented
- SR-4 response codes complete

## Issues
- SR-3: description mismatch at src/routes/users.ts:42
- SR-5: missing example at src/routes/orders.ts:117
"""


class TestRW1ApiDocSemanticReviewReportLeak:
    """RW-1 (phase-00 D-a): `docs/api/api-doc-semantic-review-report.md` is an
    internal QA artifact (frontmatter passed/failed/warnings, check IDs
    SR-1..SR-5, findings with file:line evidence) written by the `--api-doc`
    pass. It is a `.md` under `docs/` so a whole-corpus glob walks it, and
    pre-RW-1 it matched none of the three reachable denylist patterns — a
    real client-facing leak. This is the leak proof: build a bundle with this
    exact artifact present and assert it never reaches the output by any means
    (no page written for it, and none of its distinguishing internal content
    — check IDs, file:line evidence — appears anywhere in the bundle)."""

    def _corpus_with_leak(self, tmp_path: Path) -> Path:
        repo = tmp_path / "repo"
        docs = _make_corpus(repo)
        _write(docs / "api" / "api-doc-semantic-review-report.md", API_DOC_SEMANTIC_REVIEW_FIXTURE)
        return repo

    def test_no_page_generated_for_the_leak_artifact(self, tmp_path: Path) -> None:
        repo = self._corpus_with_leak(tmp_path)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        html_files = {p.relative_to(out).as_posix() for p in out.rglob("*.html")}
        assert not any("api-doc-semantic-review-report" in f for f in html_files)
        # Unchanged from the plain _make_corpus() count (index + 3 legit docs) —
        # the leak artifact contributes zero pages.
        assert len(html_files) == 4

    def test_internal_evidence_never_appears_anywhere_in_bundle(self, tmp_path: Path) -> None:
        repo = self._corpus_with_leak(tmp_path)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        all_text = "\n".join(
            p.read_text(encoding="utf-8", errors="ignore") for p in out.rglob("*") if p.is_file()
        )
        assert "SR-1" not in all_text
        assert "SR-3" not in all_text
        assert "src/routes/users.ts:42" not in all_text
        assert "API Doc Semantic Review" not in all_text

    def test_denylist_matches_the_exact_basename(self) -> None:
        """Unit-level pin on the fix itself, independent of a full build."""
        result = subprocess.run(
            [
                "node",
                "-e",
                "const {isDenylisted} = require(process.argv[1]); "
                "console.log(isDenylisted('api-doc-semantic-review-report.md'));",
                str(
                    REPO_ROOT
                    / "claude"
                    / "skills"
                    / "rebuild-spec"
                    / "extensions"
                    / "scripts"
                    / "lib"
                    / "package-denylist.cjs"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "true"


# Every `.md` basename this skill is documented to ever write UNDER a target
# project's `docs/` (i.e. an artifact `--package` could plausibly bundle),
# swept live from the pass reference docs rather than hand-copied — see
# TestRW2DocsSweepDenylistCoverage below for why a hardcoded snapshot alone
# would not fix the method gap RW-2 exists to close.
_DOCS_MD_PATH_RE = re.compile(r"docs/([A-Za-z0-9_./-]*\.md)")

# Names that ARE swept up by the naive `docs/...\.md` grep below but are not
# live rebuild-spec write targets in a target project's docs/ corpus — each
# documented so removal is a deliberate, reviewable act, not silent filtering:
_SWEEP_EXCLUDE_BASENAMES = {
    # This repo's OWN meta changelog (docs/project-changelog.md), referenced
    # from confidence-report-contract.md for cross-linking prose — not an
    # artifact rebuild-spec writes into a TARGET project's docs/ corpus.
    "project-changelog.md",
    # Retired in v15.0.0 ("DOCUMENT-MAP no longer written" — SKILL.md:429-431,
    # pipeline-w7-w9.md:496, pipeline-translate.md:399). Mentioned only
    # historically; build_navigation.py no longer writes either file.
    "DOCUMENT-MAP.md",
    "DOCUMENT-MAP.draft.md",
    # Legacy pre-v4.0.0 layout, referenced only as a bootstrap-detection READ
    # path for migrating an old corpus (SKILL.md:162) — rebuild-spec v4+
    # never WRITES docs/specs/system-overview.md.
    "system-overview.md",
}

# Basenames confirmed client-facing by the phase-00 verdict + this plan's gate
# decisions (ADR-*.md kept in; no confidence page). Patterns, not a flat list,
# so `<ProjectName>_System_Overview.md` and `ADR-####.md` match their whole
# family without enumerating every possible project name / ADR number.
_CLIENT_FACING_PATTERNS = [
    re.compile(p)
    for p in [
        r"^overview\.md$",
        r"^architecture\.md$",
        r"^business-rules\.md$",
        r"^glossary\.md$",
        r"^permissions\.md$",
        r"^permissions-matrix\.md$",
        r"^feature-list\.md$",
        r"^screen-list\.md$",
        r"^screen-flow\.md$",
        r"^entities\.md$",
        r"^api-map\.md$",
        r"^api-contracts\.md$",
        r"^behavior-logic\.md$",
        r"^crud-matrix\.md$",
        r"^db-objects\.md$",
        r"^route-list\.md$",
        r"^user-stories\.md$",
        r"^traceability-matrix\.md$",
        r"^system-flow\.md$",
        r"^functional-spec\.md$",
        r"^technical-spec\.md$",
        r"^test-cases\.md$",
        r"^README\.md$",
        r"^ADR-\d+\.md$",
        r".*_System_Overview\.md$",
    ]
]


def _sweep_docs_md_basenames() -> set[str]:
    """Regex-sweep every `references/*.md` + SKILL.md for a literal
    `docs/....md` path mention, filtering out templated placeholders
    (`<...>`, `{...}`, `[...]`) which are not concrete filenames. This mirrors
    exactly how phase-00's D-a investigation found the leak in the first
    place — grepping the reference docs for what the skill is documented to
    write — so the *next* new artifact someone documents there gets swept up
    here too, not just the ones known today."""
    rebuild_spec_dir = REPO_ROOT / "claude" / "skills" / "rebuild-spec"
    sources = list((rebuild_spec_dir / "references").glob("*.md")) + [rebuild_spec_dir / "SKILL.md"]
    basenames: set[str] = set()
    for src in sources:
        text = src.read_text(encoding="utf-8", errors="ignore")
        for match in _DOCS_MD_PATH_RE.finditer(text):
            rel = match.group(1)
            if any(c in rel for c in "<>{}[]"):
                continue  # templated placeholder, not a concrete filename
            basenames.add(rel.rsplit("/", 1)[-1])
    return basenames


class TestRW2DocsSweepDenylistCoverage:
    """RW-2 (accepted into phase-04 scope): the original denylist was built by
    enumerating two lists instead of sweeping `docs/` for every report-class
    artifact this skill can write — which is exactly why RW-1's leak existed
    despite the artifact predating the denylist. This test performs that
    sweep for real (see `_sweep_docs_md_basenames`) and asserts every
    concrete `.md` basename it finds is either denylisted or on the
    documented client-facing allowlist — so the next new report-class
    artifact someone adds to a reference doc without updating the denylist
    fails THIS test instead of shipping to a client."""

    def test_every_documented_artifact_is_classified(self) -> None:
        swept = _sweep_docs_md_basenames() - _SWEEP_EXCLUDE_BASENAMES
        assert len(swept) >= 20, f"sweep found suspiciously few artifacts ({len(swept)}) — check the regex"

        denylist_path = str(
            REPO_ROOT
            / "claude"
            / "skills"
            / "rebuild-spec"
            / "extensions"
            / "scripts"
            / "lib"
            / "package-denylist.cjs"
        )
        script = (
            "const {isDenylisted} = require(process.argv[1]); "
            "const names = process.argv.slice(2); "
            "console.log(JSON.stringify(Object.fromEntries(names.map(n => [n, isDenylisted(n)]))));"
        )
        result = subprocess.run(
            ["node", "-e", script, denylist_path, *sorted(swept)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        denylisted = json.loads(result.stdout)

        unclassified = []
        for name in sorted(swept):
            is_denied = denylisted.get(name, False)
            is_allowed = any(p.match(name) for p in _CLIENT_FACING_PATTERNS)
            if not is_denied and not is_allowed:
                unclassified.append(name)

        assert not unclassified, (
            f"{len(unclassified)} docs/ artifact(s) are neither denylisted nor on the "
            f"client-facing allowlist — classify each in package-denylist.cjs (internal) "
            f"or _CLIENT_FACING_PATTERNS above (client-facing): {unclassified}"
        )

    def test_api_doc_semantic_review_report_is_in_the_swept_set(self) -> None:
        """Sanity check on the sweep mechanism itself: the RW-1 leak artifact
        must actually be discoverable by the sweep (it's documented in
        api-pass.md), otherwise the coverage test above would pass for the
        wrong reason (never seeing it) rather than the right one (seeing it
        and confirming it's denylisted)."""
        assert "api-doc-semantic-review-report.md" in _sweep_docs_md_basenames()


class TestFR7BucketDeletion:
    """Phase-04 (`260826-1601-package-reading-layers-index-pager`) deleted the
    FR-7 4-bucket index (`classifyBucket`/`BUCKET_ORDER`/`BUCKET_LABELS`/
    `BUCKET_PATTERNS`/`TRACEABILITY_MATRIX_REL_MD`) that used to live in
    `package-html-template.cjs` and dropped 64% of pages into a trailing
    "Other" section. It's replaced by a layered index driven by the
    reading-order sidecar (`lib/reading-spine.cjs` + `lib/package-nav.cjs` +
    `lib/package-index-body.cjs`) — see `test_package_index_nav.py` for that
    surface's own coverage (no-"Other" on the real corpus, link integrity,
    localization, sidebar open/active state). This class only guards the
    deletion itself: the old symbols must not resurface, and a corpus with
    no sidecar (this fixture has none) must still degrade to a complete,
    "Other"-free listing rather than reintroducing the old bucket catch-all."""

    def test_deleted_bucket_symbols_gone_from_template(self) -> None:
        src = (
            REPO_ROOT
            / "claude"
            / "skills"
            / "rebuild-spec"
            / "extensions"
            / "scripts"
            / "lib"
            / "package-html-template.cjs"
        ).read_text(encoding="utf-8")
        # Strip comments first — the module's own header prose names these
        # symbols to explain why they're gone (same convention as
        # test_reading_spine.py's TestNoHardcodedEnglishChrome).
        code_only = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
        code_only = re.sub(r"//.*", "", code_only)
        for symbol in (
            "classifyBucket",
            "BUCKET_ORDER",
            "BUCKET_LABELS",
            "BUCKET_PATTERNS",
            "TRACEABILITY_MATRIX_REL_MD",
            "renderIndexBody",
            "renderNavList",
        ):
            assert symbol not in code_only, f"{symbol} still present in package-html-template.cjs"

    def test_sidecarless_corpus_index_has_no_other_heading(self, tmp_path: Path) -> None:
        """No sidecar at all (the fallback path) must still list every page,
        without resurrecting an "Other" catch-all heading."""
        repo = tmp_path / "repo"
        docs = repo / "docs"
        _write(docs / "system" / "overview.md", "# Overview\n\n**Project**: DemoCo\n")
        _write(docs / "decisions" / "ADR-0001.md", "# ADR-0001\n")
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr
        index_html = (out / "index.html").read_text(encoding="utf-8")
        assert ">Other<" not in index_html
        assert 'href="system/overview.html"' in index_html
        assert 'href="decisions/ADR-0001.html"' in index_html


class TestDiagramZoom:
    """Click-to-zoom diagram viewer (plan `260827-0811-package-html-diagram-zoom`).

    Mermaid scales every diagram down to the content column, so a large one
    arrives unreadable and `overflow-x: auto` cannot help — the SVG was shrunk,
    not clipped. The bundle now ships a vendored viewer that opens a diagram
    full-screen with wheel zoom and drag pan.
    """

    ASSET = (
        REPO_ROOT / "claude" / "skills" / "rebuild-spec" / "extensions" / "assets" / "package-zoom.js"
    )

    def test_viewer_asset_is_vendored_into_the_bundle(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        vendored = out / "assets" / "package-zoom.js"
        assert vendored.is_file()
        assert vendored.read_text(encoding="utf-8") == self.ASSET.read_text(encoding="utf-8")

    def test_every_page_loads_the_viewer_and_stays_offline_safe(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        html_files = list(out.rglob("*.html"))
        assert html_files
        for html_file in html_files:
            text = html_file.read_text(encoding="utf-8")
            assert "assets/package-zoom.js" in text
            # The offline contract from TestSelfContainedOutput must still hold
            # for the script tag this feature added.
            assert 'type="module"' not in text
            assert "http://" not in text
            assert "https://" not in text

    def test_mermaid_is_driven_by_run_not_start_on_load(self, tmp_path: Path) -> None:
        """`startOnLoad: true` is fire-and-forget: it gives the viewer no signal
        for when SVGs exist, so attachment could only be guessed at on a timer."""
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        text = (out / "index.html").read_text(encoding="utf-8")
        assert "startOnLoad: false" in text
        assert "startOnLoad: true" not in text
        assert "mermaid.run()" in text
        assert "pkgZoom.attach()" in text

    def test_attach_still_runs_when_a_diagram_fails_to_render(self, tmp_path: Path) -> None:
        """One bad fence must not cost the page every OTHER zoomable diagram —
        so the rejection path attaches too, not only `.then`."""
        repo = tmp_path / "repo"
        _make_corpus(repo)
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        text = (out / "index.html").read_text(encoding="utf-8")
        catch_clause = text.split(".catch(", 1)
        assert len(catch_clause) == 2, "expected a .catch() on the mermaid.run() chain"
        assert "pkgZoom.attach()" in catch_clause[1].split("</script>", 1)[0]

    def test_viewer_source_is_dependency_free(self) -> None:
        """The bundle opens from `file://` with no build step — the viewer must
        load as a classic script with no module syntax and no network call."""
        src = self.ASSET.read_text(encoding="utf-8")
        code_only = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
        code_only = re.sub(r"//.*", "", code_only)
        assert "require(" not in code_only
        assert not re.search(r"^\s*(import|export)\s", code_only, flags=re.M)
        assert "http://" not in code_only
        assert "https://" not in code_only

    def test_viewer_source_parses_under_node(self) -> None:
        result = subprocess.run(
            ["node", "--check", str(self.ASSET)], capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, result.stderr

    def test_i18n_island_carries_localized_chrome(self, tmp_path: Path) -> None:
        """Viewer labels come from the sidecar's `ui.zoom`, like every other
        piece of package chrome — not from English baked into the asset."""
        sys.path.insert(0, str(REPO_ROOT / "claude" / "skills" / "rebuild-spec" / "scripts"))
        from _nav_sidecar_lib import write_reading_sidecar  # noqa: E402 (test-local import)

        repo = tmp_path / "repo"
        docs = repo / "docs"
        _write(docs / "system" / "overview.md", "# Overview\n\n**Project**: DemoCo\n")
        _write(docs / "generated" / "feature-list.md", "# Feature List\n")
        write_reading_sidecar(str(docs), "vi")

        out = tmp_path / "out"
        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        text = (out / "index.html").read_text(encoding="utf-8")
        assert 'id="pkg-zoom-i18n"' in text
        island = text.split('id="pkg-zoom-i18n">', 1)[1].split("</script>", 1)[0]
        payload = json.loads(island)
        assert set(payload) == {
            "title",
            "open",
            "close",
            "zoom_in",
            "zoom_out",
            "fit",
            "actual_size",
            "hint",
        }
        assert payload["fit"] == "Vừa màn hình", payload["fit"]

    def test_i18n_island_absent_without_a_sidecar(self, tmp_path: Path) -> None:
        """No sidecar means no locale to read from — the island is omitted and
        the viewer falls back to its built-in English, not to a broken tag."""
        repo = tmp_path / "repo"
        docs = repo / "docs"
        _write(docs / "a.md", "# A\n\nBody.\n")
        out = tmp_path / "out"

        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr
        assert 'id="pkg-zoom-i18n"' not in (out / "index.html").read_text(encoding="utf-8")

    def test_sidecar_without_zoom_block_still_validates(self, tmp_path: Path) -> None:
        """NEGATIVE CONTROL for the optionality decision recorded in
        `isUsableUi`. A sidecar written before `ui.zoom` existed must keep its
        pager — if `zoom` were required, the whole corpus would silently drop to
        the alphabetical, pager-less fallback. Asserting the pager is present is
        what proves the sidecar was accepted, not merely that the build exited 0.
        """
        sys.path.insert(0, str(REPO_ROOT / "claude" / "skills" / "rebuild-spec" / "scripts"))
        from _nav_sidecar_lib import write_reading_sidecar  # noqa: E402 (test-local import)

        repo = tmp_path / "repo"
        docs = repo / "docs"
        _write(docs / "system" / "overview.md", "# Overview\n\n**Project**: DemoCo\n")
        _write(docs / "generated" / "feature-list.md", "# Feature List\n")
        write_reading_sidecar(str(docs), "en")

        sidecar_path = docs / ".reading-order.json"
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        assert "zoom" in sidecar["ui"], "precondition: the emitter writes ui.zoom"
        del sidecar["ui"]["zoom"]
        sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")

        out = tmp_path / "out"
        result = _run_build(repo, "docs", out)
        assert result.returncode == 0, result.stderr

        text = (out / "system" / "overview.html").read_text(encoding="utf-8")
        assert '<nav class="pv-pager"' in text, "sidecar was rejected — ui.zoom is not optional"
        assert 'id="pkg-zoom-i18n"' not in text
        assert "assets/package-zoom.js" in text

    def test_open_scale_has_a_legibility_floor(self) -> None:
        """A real corpus holds ~10000px-wide flowcharts. Fitting one to a laptop
        stage lands at 12% — the same hairline the viewer exists to fix — so a
        diagram opens no smaller than the floor, anchored top-left, and the fit
        button still reaches the true whole-diagram overview.
        """
        src = self.ASSET.read_text(encoding="utf-8")
        match = re.search(r"var MIN_OPEN_SCALE = ([0-9.]+);", src)
        assert match, "MIN_OPEN_SCALE not found"
        floor = float(match.group(1))
        assert 0.25 <= floor <= 1.0, floor
        assert "topLeftOffset" in src
        # The fit button must still reach true fit, not the floored open scale.
        assert re.search(r"function applyFit\(\)\s*\{\s*setView\(view\.fitScale", src)
