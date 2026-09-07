"""Tests for the reading-order JSON sidecar emitter (plan
`260826-1601-package-reading-layers-index-pager`, phase-01, rebuild-spec 28.2.0).

Covers: the Success Criteria equality test (sidecar entries == docs/README.md's
numbered rows), that the presence prune is the SAME shared function _nav_index
uses (not a re-derived copy), ROLES/QUICK_PATH pruning, vi/ja localization
(real string literals, not just "!= en"), schemaVersion, determinism across two
runs, the empty-corpus / no-layer-1-artifacts guard, write-safety route
(_resolve_guarded + _atomic_write), and module constraints (<200 lines, stdlib
only).
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _nav_aggregate_render import compute_present_nums as _shared_compute_present_nums  # noqa: E402
from _nav_index import build_index_readme  # noqa: E402
import _nav_index as _nav_index_mod  # noqa: E402
from _nav_sidecar_lib import (  # noqa: E402
    SIDECAR_FILENAME, build_reading_sidecar, write_reading_sidecar,
)
import _nav_sidecar_lib as _nav_sidecar_lib_mod  # noqa: E402
from _nav_strings import get_strings  # noqa: E402
from _nav_strings_en import STRINGS as _EN_STRINGS  # noqa: E402
from _nav_strings_ja import STRINGS as _JA_STRINGS  # noqa: E402
from _nav_strings_vi import STRINGS as _VI_STRINGS  # noqa: E402
from build_navigation import _write_index_readme, run  # noqa: E402

_SIDECAR_SRC_PATH = SCRIPTS / "_nav_sidecar_lib.py"


def _write(path: Path, content: str = "# x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _full_docs_tree(base: Path) -> Path:
    """A docs tree covering every non-glob READING_ORDER entry (layers 1-3)
    plus a features/*/ glob and a flows/*.md glob (layer 4) — enough surface
    for the presence-prune to have real work to do. screens/*/ and the
    traceability matrix (both conditional) are deliberately left absent."""
    docs = base / "docs"
    for rel in (
        "system/overview.md", "system/architecture.md", "system/glossary.md",
        "generated/entities.md", "generated/feature-list.md",
        "generated/user-stories.md", "generated/screen-list.md",
        "generated/screen-flow.md", "generated/route-list.md",
        "generated/api-map.md", "generated/api-contracts.md",
        "generated/behavior-logic.md", "generated/permissions-matrix.md",
    ):
        _write(docs / rel)
    _write(docs / "features" / "F001_Login" / "spec.md")
    _write(docs / "flows" / "checkout.md")
    return docs


def _index_rows(content: str) -> list[tuple[int, str]]:
    """Extract (number, link_target) tuples from docs/README.md table rows."""
    rows = []
    for line in content.splitlines():
        m = re.match(r"^\| (\d+) \| \[[^\]]+\]\(([^)]+)\) \|", line)
        if m:
            rows.append((int(m.group(1)), m.group(2)))
    return rows


def _sidecar_rows(payload: dict) -> list[tuple[int, str]]:
    """(num, target) pairs using the SAME formula the README renderer uses:
    target = link when kind == 'glob', else path (_nav_index.py:171)."""
    rows = []
    for layer in payload["layers"]:
        for e in layer["entries"]:
            target = e["link"] if e["kind"] == "glob" else e["path"]
            rows.append((e["num"], target))
    return rows


# ---------------------------------------------------------------------------
# Success Criteria: sidecar entries == docs/README.md numbered rows
# ---------------------------------------------------------------------------

class TestEqualityWithReadme:
    def test_sidecar_matches_readme_rows_full_corpus(self, tmp_path):
        docs = _full_docs_tree(tmp_path)
        readme = build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        payload = build_reading_sidecar(str(docs), "en")
        sidecar_rows = _sidecar_rows(payload)
        readme_rows = _index_rows(readme)
        assert set(sidecar_rows) == set(readme_rows)
        assert len(sidecar_rows) == len(readme_rows)  # no dupes on either side

    def test_sidecar_matches_readme_rows_sparse_corpus(self, tmp_path):
        docs = tmp_path / "docs"
        for rel in ("system/overview.md", "system/architecture.md",
                    "generated/entities.md"):
            _write(docs / rel)
        readme = build_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        payload = build_reading_sidecar(str(docs), "en")
        assert set(_sidecar_rows(payload)) == set(_index_rows(readme))


# ---------------------------------------------------------------------------
# Shared presence-prune helper — reused, not duplicated (phase-01 step 1)
# ---------------------------------------------------------------------------

class TestSharedPruneHelper:
    def test_both_callers_use_the_same_function_object(self):
        """_nav_index and _nav_sidecar_lib must call the IDENTICAL function —
        not two implementations that happen to agree today."""
        assert _nav_index_mod.compute_present_nums is _shared_compute_present_nums
        assert _nav_sidecar_lib_mod.compute_present_nums is _shared_compute_present_nums

    def test_absent_artifact_omitted_from_entries(self, tmp_path):
        docs = _full_docs_tree(tmp_path)
        (docs / "system" / "glossary.md").unlink()  # num 3, conditional
        payload = build_reading_sidecar(str(docs), "en")
        nums = {e["num"] for layer in payload["layers"] for e in layer["entries"]}
        assert 3 not in nums

    def test_absent_artifact_dropped_from_role_and_quickpath_nums(self, tmp_path):
        docs = _full_docs_tree(tmp_path)
        (docs / "generated" / "entities.md").unlink()  # num 4: in QUICK_PATH + new_dev role
        payload = build_reading_sidecar(str(docs), "en")
        assert 4 not in payload["quickPath"]["nums"]
        new_dev = next(r for r in payload["roles"] if r["key"] == "new_dev")
        assert 4 not in new_dev["nums"]
        pm = next(r for r in payload["roles"] if r["key"] == "pm")
        assert 4 not in pm["nums"]  # pm role never listed 4 anyway; guards no false positive
        # entities.md itself must be gone from the layer-2 entries too
        layer2 = next(l for l in payload["layers"] if l["layer"] == 2)
        assert 4 not in {e["num"] for e in layer2["entries"]}


# ---------------------------------------------------------------------------
# Localization — real vi/ja string literals, not just "differs from en"
# ---------------------------------------------------------------------------

class TestLocalization:
    def test_vi_produces_real_vietnamese_strings(self, tmp_path):
        docs = _full_docs_tree(tmp_path)
        payload = build_reading_sidecar(str(docs), "vi")
        assert payload["lang"] == "vi"
        assert payload["title"] == get_strings("vi")["title"]
        assert "Mục lục tài liệu" in payload["title"]
        layer1 = next(l for l in payload["layers"] if l["layer"] == 1)
        assert "Định hướng" in layer1["label"]
        assert payload["quickPath"]["label"] == "Đọc nhanh tối thiểu"

    def test_ja_produces_real_japanese_strings(self, tmp_path):
        docs = _full_docs_tree(tmp_path)
        payload = build_reading_sidecar(str(docs), "ja")
        assert payload["lang"] == "ja"
        assert payload["title"] == get_strings("ja")["title"]
        assert "ドキュメント索引" in payload["title"]
        layer1 = next(l for l in payload["layers"] if l["layer"] == 1)
        assert "全体像" in layer1["label"]
        assert payload["quickPath"]["label"] == "最短の通読"

    def test_en_is_the_default_and_differs_from_vi_ja(self, tmp_path):
        docs = _full_docs_tree(tmp_path)
        en = build_reading_sidecar(str(docs), "en")
        vi = build_reading_sidecar(str(docs), "vi")
        ja = build_reading_sidecar(str(docs), "ja")
        assert en["title"] != vi["title"] != ja["title"]
        # but the skeleton (nums/paths/kinds) is locale-independent
        assert _sidecar_rows(en) == _sidecar_rows(vi) == _sidecar_rows(ja)


# ---------------------------------------------------------------------------
# package_ui — sidecar `ui` block (phase-03b): identical key sets across
# en/vi/ja, real (non-ASCII) translations, and required wiring into
# build_reading_sidecar(). schemaVersion stays 1 (no format bump needed —
# emitter and consumer ship together in 28.2.0).
# ---------------------------------------------------------------------------

def _flatten_keys(d: dict, prefix: str = "") -> set[str]:
    """Recursively flatten a nested dict's keys into dotted paths, so a key
    added to one locale's `package_ui` and forgotten in another is caught
    regardless of nesting depth (e.g. `pager.prev`)."""
    keys: set[str] = set()
    for k, v in d.items():
        path = f"{prefix}{k}"
        keys.add(path)
        if isinstance(v, dict):
            keys |= _flatten_keys(v, prefix=f"{path}.")
    return keys


class TestPackageUiParity:
    _LOCALES = {"en": _EN_STRINGS, "vi": _VI_STRINGS, "ja": _JA_STRINGS}

    def test_present_in_every_locale(self):
        for lang, strings in self._LOCALES.items():
            assert "package_ui" in strings, f"{lang}: package_ui block missing"

    def test_identical_key_sets_across_locales(self):
        """The drift guard this phase exists to add: a key added to one
        locale and forgotten in another must fail loudly, not leak English."""
        key_sets = {lang: _flatten_keys(s["package_ui"]) for lang, s in self._LOCALES.items()}
        assert key_sets["en"] == key_sets["vi"] == key_sets["ja"], (
            f"package_ui key set drift across locales: {key_sets}"
        )

    def test_vi_values_are_real_vietnamese_literals(self):
        """Real non-ASCII Vietnamese text — not just asserted `!= en`."""
        vi = _VI_STRINGS["package_ui"]
        assert "Bắt đầu" in vi["start_here"]
        assert "Phụ lục" in vi["appendix"]
        assert "Trước" in vi["pager"]["prev"]
        assert "Tiếp" in vi["pager"]["next"]
        assert "Đang đọc" in vi["pager"]["reading"]
        assert "mục lục" in vi["pager"]["back_to_index"]
        for label in vi["drill_labels"].values():
            assert any(ord(c) > 127 for c in label), f"drill label {label!r} looks like an English placeholder"

    def test_ja_values_are_real_japanese_literals(self):
        """Real non-ASCII Japanese text — not just asserted `!= en`."""
        ja = _JA_STRINGS["package_ui"]
        assert "開始" in ja["start_here"]
        assert "付録" in ja["appendix"]
        assert "前へ" in ja["pager"]["prev"]
        assert "次へ" in ja["pager"]["next"]
        assert "閲覧中" in ja["pager"]["reading"]
        assert "索引" in ja["pager"]["back_to_index"]
        for label in ja["drill_labels"].values():
            assert any(ord(c) > 127 for c in label), f"drill label {label!r} looks like an English placeholder"

    def test_all_leaf_values_non_empty_str(self):
        for lang, strings in self._LOCALES.items():
            for dotted in _flatten_keys(strings["package_ui"]):
                node = strings["package_ui"]
                for part in dotted.split("."):
                    node = node[part]
                if isinstance(node, dict):
                    continue  # container node; only leaves must be non-empty strings
                assert isinstance(node, str) and node.strip(), f"{lang}: package_ui.{dotted} is not a non-empty string"


class TestSidecarUiField:
    def test_ui_emitted_as_top_level_object(self, tmp_path):
        docs = _full_docs_tree(tmp_path)
        payload = build_reading_sidecar(str(docs), "en")
        assert payload["ui"] == get_strings("en")["package_ui"]

    def test_ui_localized_per_lang(self, tmp_path):
        docs = _full_docs_tree(tmp_path)
        vi_payload = build_reading_sidecar(str(docs), "vi")
        ja_payload = build_reading_sidecar(str(docs), "ja")
        assert vi_payload["ui"] == get_strings("vi")["package_ui"]
        assert ja_payload["ui"] == get_strings("ja")["package_ui"]
        assert vi_payload["ui"] != ja_payload["ui"]

    def test_ui_present_even_on_empty_corpus(self, tmp_path):
        """The sidecar is ALWAYS written with `ui` — an empty corpus still
        gets real chrome strings, mirroring the `layers: []` always-write
        decision from phase-01."""
        docs = tmp_path / "docs"
        docs.mkdir()
        payload = build_reading_sidecar(str(docs), "en")
        assert payload["ui"] == get_strings("en")["package_ui"]


# ---------------------------------------------------------------------------
# schemaVersion
# ---------------------------------------------------------------------------

class TestSchemaVersion:
    def test_schema_version_is_1(self, tmp_path):
        docs = _full_docs_tree(tmp_path)
        payload = build_reading_sidecar(str(docs), "en")
        assert payload["schemaVersion"] == 1


# ---------------------------------------------------------------------------
# Determinism — two consecutive runs, byte-identical, no timestamp
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_two_runs_byte_identical(self, tmp_path):
        docs = _full_docs_tree(tmp_path)
        write_reading_sidecar(str(docs), "en")
        first = (docs / SIDECAR_FILENAME).read_bytes()
        write_reading_sidecar(str(docs), "en")
        second = (docs / SIDECAR_FILENAME).read_bytes()
        assert first == second

    def test_no_timestamp_field_in_payload(self, tmp_path):
        docs = _full_docs_tree(tmp_path)
        payload = build_reading_sidecar(str(docs), "en")
        assert "timestamp" not in payload
        assert "generatedAt" not in payload
        assert "generated" not in payload


# ---------------------------------------------------------------------------
# Empty-corpus / no-layer-1-artifacts guard
# ---------------------------------------------------------------------------

class TestEmptyCorpusGuard:
    def test_no_layer1_artifacts_layer_omitted_no_crash(self, tmp_path):
        docs = tmp_path / "docs"
        _write(docs / "generated" / "entities.md")  # layer-2 only, no system/*
        payload = build_reading_sidecar(str(docs), "en")  # must not raise
        layer_nums = {l["layer"] for l in payload["layers"]}
        assert 1 not in layer_nums
        assert 2 in layer_nums

    def test_build_navigation_run_does_not_crash_on_fully_empty_docs(self, tmp_path):
        """Decision (phase-01): the sidecar is ALWAYS written (mirrors
        _write_index_readme's "always regenerated" behavior) — an empty corpus
        gets `"layers": []`, not a missing file."""
        docs = tmp_path / "docs"
        docs.mkdir()
        rc = run(str(docs), pass_complete=True)
        assert rc == 0
        sidecar_path = docs / SIDECAR_FILENAME
        assert sidecar_path.is_file()
        payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
        assert payload["layers"] == []
        assert payload["roles"] == []
        assert payload["quickPath"]["nums"] == []
        assert payload["schemaVersion"] == 1


# ---------------------------------------------------------------------------
# Wiring into build_navigation.run()
# ---------------------------------------------------------------------------

class TestWiring:
    def test_run_writes_sidecar_alongside_readme(self, tmp_path):
        docs = _full_docs_tree(tmp_path)
        run(str(docs), pass_complete=True)
        assert (docs / "README.md").is_file()
        assert (docs / SIDECAR_FILENAME).is_file()


# ---------------------------------------------------------------------------
# Sidecar gating (Q2/Q3 fix): written exactly where the full non-aggregate
# index README is written — never on an aggregate root, never on a bare
# per-lang root.
# ---------------------------------------------------------------------------

def _aggregate_docs_tree(base: Path) -> Path:
    """A minimal aggregate (system-of-systems) root: system/component-catalog.md
    present is the unique aggregate signal _is_aggregate_root checks for."""
    docs = base / "docs"
    _write(docs / "system" / "component-catalog.md")
    _write(docs / "system" / "overview.md")
    return docs


def _bare_perlang_docs_tree(base: Path) -> Path:
    """A bare docs/ root in per-lang mode: primary_lang != 'en' plus a second
    registered translation is the per-lang signal detect_layout_mode reads."""
    docs = base / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    _write(docs / ".rebuild-state.json",
           '{"primary_lang": "vi", "translations": {"en": {}}}')
    return docs


class TestSidecarGating:
    def test_aggregate_root_writes_no_sidecar(self, tmp_path):
        docs = _aggregate_docs_tree(tmp_path)
        wrote = _write_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        assert wrote is False
        assert not (docs / SIDECAR_FILENAME).is_file()
        # the thin aggregate pointer README still renders
        assert (docs / "README.md").is_file()

    def test_aggregate_root_via_run_writes_no_sidecar(self, tmp_path):
        docs = _aggregate_docs_tree(tmp_path)
        run(str(docs), pass_complete=True)
        assert not (docs / SIDECAR_FILENAME).is_file()
        assert (docs / "README.md").is_file()

    def test_bare_perlang_root_writes_no_sidecar(self, tmp_path):
        docs = _bare_perlang_docs_tree(tmp_path)
        wrote = _write_index_readme(str(docs), None, "2026-01-01T00:00:00Z")
        assert wrote is False
        assert not (docs / SIDECAR_FILENAME).is_file()

    def test_bare_perlang_root_via_run_writes_no_sidecar(self, tmp_path):
        docs = _bare_perlang_docs_tree(tmp_path)
        run(str(docs), pass_complete=True)
        assert not (docs / SIDECAR_FILENAME).is_file()

    def test_non_aggregate_single_lang_root_still_writes_sidecar(self, tmp_path):
        """The positive case: an ordinary single-lang, non-aggregate corpus
        still gets both README and sidecar through the gated run() path, and
        the equality invariant from TestEqualityWithReadme still holds."""
        docs = _full_docs_tree(tmp_path)
        wrote = _write_index_readme(str(docs), "en", "2026-01-01T00:00:00Z")
        assert wrote is True  # the gate's own return value, checked directly

        docs2 = _full_docs_tree(tmp_path.parent / (tmp_path.name + "_run"))
        run(str(docs2), pass_complete=True)
        assert (docs2 / SIDECAR_FILENAME).is_file()
        payload = json.loads((docs2 / SIDECAR_FILENAME).read_text(encoding="utf-8"))
        readme = (docs2 / "README.md").read_text(encoding="utf-8")
        assert set(_sidecar_rows(payload)) == set(_index_rows(readme))


# ---------------------------------------------------------------------------
# Write-safety route: _resolve_guarded() + _atomic_write()
# ---------------------------------------------------------------------------

class TestWriteSafety:
    def test_write_route_uses_resolve_guarded_and_atomic_write(self):
        src = _SIDECAR_SRC_PATH.read_text(encoding="utf-8")
        assert "_resolve_guarded(" in src
        assert "_atomic_write(" in src

    def test_write_produces_valid_json_file(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        write_reading_sidecar(str(docs), "en")
        payload = json.loads((docs / SIDECAR_FILENAME).read_text(encoding="utf-8"))
        assert payload["schemaVersion"] == 1


# ---------------------------------------------------------------------------
# Module constraints: < 200 lines, stdlib + project-local imports only
# ---------------------------------------------------------------------------

class TestModuleConstraints:
    def test_under_200_lines(self):
        lines = _SIDECAR_SRC_PATH.read_text(encoding="utf-8").splitlines()
        assert len(lines) < 200, f"{len(lines)} lines"

    def test_stdlib_and_local_imports_only(self):
        src = _SIDECAR_SRC_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src)
        stdlib_ok = {"json", "os", "sys"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert mod in stdlib_ok or mod.startswith("_"), f"non-stdlib import: {mod}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top in stdlib_ok or top.startswith("_"), f"non-stdlib import: {alias.name}"

    def test_not_inlined_into_build_navigation(self):
        """build_navigation.py imports + calls the emitter — one import, one
        call — never inlines the emitter's own logic."""
        src = (SCRIPTS / "build_navigation.py").read_text(encoding="utf-8")
        assert "from _nav_sidecar_lib import write_reading_sidecar" in src
        assert src.count("write_reading_sidecar(") == 1  # import line uses `import`, not a call
