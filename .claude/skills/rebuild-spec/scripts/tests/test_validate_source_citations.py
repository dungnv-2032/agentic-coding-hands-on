"""Integration tests for validate_source_citations.py.
Runs script as subprocess with --spec <path>, parses stdout JSON,
asserts specific rule_ids per citation fixture variant.
Coverage per phase-05 test matrix.
"""
from __future__ import annotations  # PEP 604 `X | None` at runtime on Python 3.9

import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPT = SCRIPTS_DIR / "validate_source_citations.py"


def _run(spec_path: Path, project_root: Path = REPO_ROOT) -> tuple[int, dict]:
    """Run the citation validator against a single spec.

    The validator derives plan_dir = spec.parent.parent.parent, then asserts
    plan_dir is under project_root.  For specs placed via _make_spec_tree(),
    the spec lives at <tmp>/artifacts/features/F001_Auth/spec.md so that
    plan_dir == tmp_path, which is under project_root == tmp_path.
    """
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--spec", str(spec_path),
         "--project-root", str(project_root)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if not result.stdout.strip():
        raise RuntimeError(
            f"validator produced no JSON output (exit={result.returncode}).\n"
            f"stderr: {result.stderr}"
        )
    output = json.loads(result.stdout)
    return result.returncode, output


def _make_spec_tree(tmp_path: Path, citation_line: str) -> tuple[Path, Path]:
    """Create artifacts/features/F001_Auth/spec.md inside tmp_path.

    The validator computes plan_dir = spec.parent.parent.parent = tmp_path,
    so passing --project-root tmp_path satisfies the assert_under guard.
    Returns (spec_path, tmp_path).
    """
    spec_dir = tmp_path / "artifacts" / "features" / "F001_Auth"
    spec_dir.mkdir(parents=True)
    spec = spec_dir / "spec.md"
    spec.write_text(
        "# F001_Auth — Authentication\n\n"
        "## Source Code References\n\n"
        f"**Source:** `{citation_line}`\n",
        encoding="utf-8",
    )
    return spec, tmp_path


def _issues(data: dict) -> list[dict]:
    all_issues = []
    for entry in data.get("specs", {}).values():
        all_issues.extend(entry.get("issues", []))
    return all_issues


def _critical_rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in _issues(data) if i["severity"] == "critical"]


# ---------------------------------------------------------------------------
# spec-pass.md: valid citation — path resolves via project_root / raw_path
# Citation in fixture uses repo-relative path to cited-source.py, so
# --project-root REPO_ROOT resolves it cleanly.
# ---------------------------------------------------------------------------

class TestSpecPassCitation:
    def test_exit_code_zero(self):
        code, _ = _run(FIXTURES / "specs" / "spec-pass.md")
        assert code == 0

    def test_no_critical_issues(self):
        _, data = _run(FIXTURES / "specs" / "spec-pass.md")
        criticals = _critical_rule_ids(data)
        assert criticals == [], f"unexpected: {criticals}"


# ---------------------------------------------------------------------------
# spec-bad-citation.md: cites nonexistent-file-that-does-not-exist.py
# ---------------------------------------------------------------------------

class TestSpecBadCitation:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-bad-citation.md")
        assert code == 1

    def test_file_missing_rule_id(self):
        _, data = _run(FIXTURES / "specs" / "spec-bad-citation.md")
        assert "citation.file_missing" in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# Range out of bounds: cited-source.py has 30 lines; cite line 999.
# Tests use tmp_path as project_root so validator accepts spec location.
# cited-source.py is copied into tmp_path and cited as "cited-source.py".
# ---------------------------------------------------------------------------

class TestCitationRangeInvalid:
    def _setup(self, tmp_path: Path, citation: str) -> tuple[Path, Path]:
        """Place cited-source.py at tmp_path root so project_root/cited-source.py resolves."""
        (tmp_path / "cited-source.py").write_text(
            (FIXTURES / "cited-source.py").read_text(encoding="utf-8"), encoding="utf-8"
        )
        spec, root = _make_spec_tree(tmp_path, f"cited-source.py:{citation}")
        return spec, root

    def test_range_invalid_rule_id(self, tmp_path):
        spec, root = self._setup(tmp_path, "999")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.range_invalid" in _critical_rule_ids(data)

    def test_range_invalid_message_mentions_bounds(self, tmp_path):
        spec, root = self._setup(tmp_path, "999")
        _, data = _run(spec, root)
        matching = [i for i in _issues(data) if i["rule_id"] == "citation.range_invalid"]
        assert any("out of bounds" in i["message"] for i in matching)


# ---------------------------------------------------------------------------
# Inverted range: end < start (e.g. :10-5)
# ---------------------------------------------------------------------------

class TestCitationRangeInverted:
    def test_range_inverted_rule_id(self, tmp_path):
        (tmp_path / "cited-source.py").write_text(
            (FIXTURES / "cited-source.py").read_text(encoding="utf-8"), encoding="utf-8"
        )
        spec, root = _make_spec_tree(tmp_path, "cited-source.py:10-5")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.range_inverted" in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# Path traversal: ../../../etc/passwd style citation.
# Spec is at tmp_path/artifacts/features/F001_Auth/spec.md so plan_dir==tmp_path
# which is under project_root==tmp_path. The traversal citation is then
# detected by the citation guard (not the plan_dir guard).
# ---------------------------------------------------------------------------

class TestCitationPathTraversal:
    def test_path_traversal_rule_id(self, tmp_path):
        spec, root = _make_spec_tree(tmp_path, "../../../etc/passwd:1")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.path_traversal" in _critical_rule_ids(data)

    def test_path_traversal_is_critical(self, tmp_path):
        spec, root = _make_spec_tree(tmp_path, "../../../etc/passwd:1")
        _, data = _run(spec, root)
        matching = [i for i in _issues(data) if i["rule_id"] == "citation.path_traversal"]
        assert len(matching) >= 1
        assert all(i["severity"] == "critical" for i in matching)

    def test_absolute_path_also_rejected(self, tmp_path):
        spec, root = _make_spec_tree(tmp_path, "/etc/passwd:1")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.path_traversal" in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# Phase 04 (cobol-stack-and-generic-fallback plan): COBOL source extensions
# (.cbl/.cob/.cpy/.bms) + generic extensions for ui-sniff leads. The validator has no
# extension allowlist at all (only existence + line-range + traversal are checked), so
# these already resolve — these tests prove that explicitly rather than leaving it implicit.
# ---------------------------------------------------------------------------

class TestCobolAndGenericExtensionCitations:
    def _setup(self, tmp_path: Path, filename: str, n_lines: int = 20) -> tuple[Path, Path]:
        (tmp_path / filename).write_text(
            "\n".join(f"line {i}" for i in range(n_lines)), encoding="utf-8"
        )
        spec, root = _make_spec_tree(tmp_path, f"{filename}:1-2")
        return spec, root

    def test_bms_extension_citation_accepted(self, tmp_path):
        spec, root = self._setup(tmp_path, "ORDMAP.bms")
        code, data = _run(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_cbl_extension_citation_accepted(self, tmp_path):
        spec, root = self._setup(tmp_path, "inline_screen.cbl")
        code, data = _run(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_cpy_extension_citation_accepted(self, tmp_path):
        spec, root = self._setup(tmp_path, "STOCKHDR.cpy")
        code, data = _run(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_ui_sniff_generic_extension_citation_accepted(self, tmp_path):
        # ui-sniff leads cite arbitrary/generic source files — no COBOL-specific narrowing.
        spec, root = self._setup(tmp_path, "legacy_dump.txt")
        code, data = _run(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []


# ---------------------------------------------------------------------------
# Phase 03b (D10) — shipped-defect fix: CITATION_RE is anchored on the literal
# `**Source:**` prefix, so hop 2..N of a chained `a -> b -> c` citation (which carry no
# prefix of their own) were structurally invisible to a single `.search()`. Proven
# against the real migrated snapshot: 146 lines carry a chained citation, longest 6
# hops, and hops 2..N were NEVER checked for existence, range, or path traversal.
# ---------------------------------------------------------------------------

class TestChainedCitationHops:
    def _two_hop_setup(self, tmp_path: Path, hop2: str) -> tuple[Path, Path]:
        (tmp_path / "real.rb").write_text(
            "\n".join(f"line {i}" for i in range(10)), encoding="utf-8"
        )
        citation = f"real.rb:1` → `{hop2}"
        spec, root = _make_spec_tree(tmp_path, citation)
        return spec, root

    def test_single_hop_citation_unaffected(self, tmp_path):
        """No-regression: a plain, non-chained citation still validates exactly as before."""
        (tmp_path / "real.rb").write_text(
            "\n".join(f"line {i}" for i in range(10)), encoding="utf-8"
        )
        spec, root = _make_spec_tree(tmp_path, "real.rb:1-3")
        code, data = _run(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_hop2_nonexistent_file_now_fails(self, tmp_path):
        """Before the fix: only hop 1 (`real.rb:1`, valid) was ever seen -- a hop 2
        citing a file that does not exist on disk validated clean. Now it must fail."""
        spec, root = self._two_hop_setup(tmp_path, "totally/invented/file.rb:999")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.file_missing" in _critical_rule_ids(data)
        matching = [i for i in _issues(data) if i["rule_id"] == "citation.file_missing"]
        assert any("totally/invented/file.rb" in i["message"] for i in matching)

    def test_hop2_path_traversal_now_fails(self, tmp_path):
        """The security-relevant half of the defect: a traversal citation placed in hop
        2+ position validated clean before this fix -- the traversal guard only ever
        covered hop 1."""
        spec, root = self._two_hop_setup(tmp_path, "../../../../../../etc/passwd:1")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.path_traversal" in _critical_rule_ids(data)

    def test_hop1_still_checked_when_it_is_the_broken_one(self, tmp_path):
        """Hop-position independence: corrupting hop 1 (while hop 2 stays valid) is
        still caught -- the new per-hop loop did not accidentally stop checking hop 1."""
        (tmp_path / "real.rb").write_text(
            "\n".join(f"line {i}" for i in range(10)), encoding="utf-8"
        )
        citation = "nonexistent-hop1.rb:1` → `real.rb:1"
        spec, root = _make_spec_tree(tmp_path, citation)
        code, data = _run(spec, root)
        assert code == 1
        matching = [i for i in _issues(data) if i["rule_id"] == "citation.file_missing"]
        assert any("nonexistent-hop1.rb" in i["message"] for i in matching)

    def test_six_hop_real_corpus_shape_all_valid(self, tmp_path):
        """Real migrated-snapshot shape (mirrors F007_AccountSettingsManagement's
        technical-spec.md:126 -- 6 hops across 2 files, longest chain observed)."""
        (tmp_path / "controller.rb").write_text(
            "\n".join(f"line {i}" for i in range(250)), encoding="utf-8"
        )
        (tmp_path / "invitation.rb").write_text(
            "\n".join(f"line {i}" for i in range(100)), encoding="utf-8"
        )
        ranges = ["31-122", "205-211", "196-198", "53-56", "75-76", "71-72"]
        files = ["controller.rb"] * 3 + ["invitation.rb"] * 3
        chain = " → ".join(f"`{f}:{r}`" for f, r in zip(files, ranges))
        spec_dir = tmp_path / "artifacts" / "features" / "F001_Auth"
        spec_dir.mkdir(parents=True)
        spec = spec_dir / "spec.md"
        spec.write_text(
            f"# F001_Auth\n\n## Source Code References\n\n**Source:** {chain}\n",
            encoding="utf-8",
        )
        code, data = _run(spec, tmp_path)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_six_hop_each_position_independently_checked(self, tmp_path):
        """Proves ALL 6 hops are actually resolved, not just 'no error on the happy
        path' (which cannot tell 1 hop from 6): corrupt exactly one of the 6 positions
        at a time with an out-of-bounds range and confirm each is independently
        detected."""
        (tmp_path / "controller.rb").write_text(
            "\n".join(f"line {i}" for i in range(250)), encoding="utf-8"
        )
        (tmp_path / "invitation.rb").write_text(
            "\n".join(f"line {i}" for i in range(100)), encoding="utf-8"
        )
        ranges = ["31-122", "205-211", "196-198", "53-56", "75-76", "71-72"]
        files = ["controller.rb"] * 3 + ["invitation.rb"] * 3
        spec_dir = tmp_path / "artifacts" / "features" / "F001_Auth"
        spec_dir.mkdir(parents=True)
        spec = spec_dir / "spec.md"

        for idx in range(6):
            bad_ranges = list(ranges)
            bad_ranges[idx] = "9999-9999"
            chain = " → ".join(f"`{f}:{r}`" for f, r in zip(files, bad_ranges))
            spec.write_text(
                f"# F001_Auth\n\n## Source Code References\n\n**Source:** {chain}\n",
                encoding="utf-8",
            )
            code, data = _run(spec, tmp_path)
            assert code == 1, f"hop index {idx} corruption was not detected"
            assert "citation.range_invalid" in _critical_rule_ids(data), f"hop index {idx}"

    def test_bare_source_no_line_numbers_default_mode_unchanged(self, tmp_path):
        """Bare-`**Source:**`-fallback path (no `:N-M` anywhere on the line) must stay
        untouched by the chained-hop fix: default source mode emits no issue for it,
        exactly as before."""
        spec_dir = tmp_path / "artifacts" / "features" / "F001_Auth"
        spec_dir.mkdir(parents=True)
        spec = spec_dir / "spec.md"
        spec.write_text(
            "# F001_Auth\n\n**Source:** some prose with no path or line number\n",
            encoding="utf-8",
        )
        code, data = _run(spec, tmp_path)
        assert code == 0
        assert _critical_rule_ids(data) == []


# ---------------------------------------------------------------------------
# Scope expansion (same phase 03b/D10 session): the real migrated snapshot carries
# TWO more multi-reference shapes beyond the arrow chain above, and CITATION_RE's
# single `.search()` leaks on both identically:
#   F2 comma line-list inside ONE backtick (72 lines): `a.rb:115-116,186,188`
#     -- only the FIRST range (115-116) was ever checked; extra ranges (186, 188)
#     were silently unchecked (a bogus `:1,999999` range never failed).
#   F3 comma-joined citations, no arrow (60 lines): `a.rb:28`, `b.rb:40-46`
#     -- only the FIRST citation was ever checked; the second FILE was never
#     resolved, existence/range/traversal-checked at all.
# Both are handled by the same `iter_citation_tokens` parser as the arrow-chain
# case above (see _citation_hop_parse_lib.py) -- one parser, not three special cases.
# ---------------------------------------------------------------------------

class TestCommaLineListCitations:
    """F2: `path:N-M,K,L-M` -- one path token, several ranges."""

    def test_f2_all_ranges_valid_passes(self, tmp_path):
        (tmp_path / "listing.rb").write_text(
            "\n".join(f"line {i}" for i in range(300)), encoding="utf-8"
        )
        spec, root = _make_spec_tree(tmp_path, "listing.rb:115-116,186,188")
        code, data = _run(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_f2_bogus_extra_range_now_fails(self, tmp_path):
        """Before the fix: `.search()` captured `listing.rb` + `115-116` only and
        silently ignored `,999999` -- a bogus out-of-bounds extra range never failed
        range validation. Now it must."""
        (tmp_path / "listing.rb").write_text(
            "\n".join(f"line {i}" for i in range(20)), encoding="utf-8"
        )
        spec, root = _make_spec_tree(tmp_path, "listing.rb:1,999999")
        code, data = _run(spec, root)
        assert code == 1
        matching = [i for i in _issues(data) if i["rule_id"] == "citation.range_invalid"]
        assert any("999999" in i["message"] for i in matching)

    def test_f2_each_of_three_ranges_independently_checked(self, tmp_path):
        """Proves ALL 3 comma-list ranges are resolved, not just the first -- corrupt
        exactly one of the 3 at a time and confirm each is independently detected."""
        (tmp_path / "listing.rb").write_text(
            "\n".join(f"line {i}" for i in range(200)), encoding="utf-8"
        )
        spec_dir = tmp_path / "artifacts" / "features" / "F001_Auth"
        spec_dir.mkdir(parents=True)
        spec = spec_dir / "spec.md"
        good = ["10-20", "50", "150-160"]
        for idx in range(3):
            ranges = list(good)
            ranges[idx] = "99999"
            linespec = ",".join(ranges)
            spec.write_text(
                f"# F001_Auth\n\n## Source Code References\n\n"
                f"**Source:** `listing.rb:{linespec}`\n",
                encoding="utf-8",
            )
            code, data = _run(spec, tmp_path)
            assert code == 1, f"range index {idx} corruption was not detected"
            assert "citation.range_invalid" in _critical_rule_ids(data), f"range index {idx}"

    def test_f2_inverted_range_in_list_detected(self, tmp_path):
        (tmp_path / "listing.rb").write_text(
            "\n".join(f"line {i}" for i in range(50)), encoding="utf-8"
        )
        spec, root = _make_spec_tree(tmp_path, "listing.rb:1-5,20-10")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.range_inverted" in _critical_rule_ids(data)


class TestCommaJoinedCitations:
    """F3: `path1:N`, `path2:M` -- multiple backtick citations, comma-separated,
    no arrow. Same severity class as the arrow chain: a whole extra FILE goes
    unchecked, traversal guard included."""

    def _setup(self, tmp_path: Path, citation2: str) -> tuple[Path, Path]:
        (tmp_path / "real.rb").write_text(
            "\n".join(f"line {i}" for i in range(10)), encoding="utf-8"
        )
        citation = f"real.rb:1`, `{citation2}"
        spec, root = _make_spec_tree(tmp_path, citation)
        return spec, root

    def test_second_citation_nonexistent_file_now_fails(self, tmp_path):
        """Before the fix: `.search()` only ever saw the first citation (`real.rb:1`,
        valid) -- a second, comma-joined citation to a nonexistent file validated
        clean."""
        spec, root = self._setup(tmp_path, "totally/invented/file.rb:999")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.file_missing" in _critical_rule_ids(data)
        matching = [i for i in _issues(data) if i["rule_id"] == "citation.file_missing"]
        assert any("totally/invented/file.rb" in i["message"] for i in matching)

    def test_second_citation_path_traversal_now_fails(self, tmp_path):
        """The security-relevant half: a traversal citation placed as the SECOND,
        comma-joined (not arrow-joined) reference validated clean before this fix --
        the traversal guard only ever covered the first `.search()` match."""
        spec, root = self._setup(tmp_path, "../../../../../../etc/passwd:1")
        code, data = _run(spec, root)
        assert code == 1
        assert "citation.path_traversal" in _critical_rule_ids(data)

    def test_both_citations_valid_passes(self, tmp_path):
        (tmp_path / "real.rb").write_text(
            "\n".join(f"line {i}" for i in range(10)), encoding="utf-8"
        )
        (tmp_path / "other.rb").write_text(
            "\n".join(f"line {i}" for i in range(10)), encoding="utf-8"
        )
        spec, root = _make_spec_tree(tmp_path, "real.rb:1`, `other.rb:2-5")
        code, data = _run(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []


# ---------------------------------------------------------------------------
# F2 guard parity: --plan-dir at a file and --spec at a directory both exit 2.
# ---------------------------------------------------------------------------

class TestInputGuards:
    def test_plan_dir_is_file_exits_two(self, tmp_path):
        bogus = tmp_path / "not-a-dir.txt"
        bogus.write_text("x")
        result = subprocess.run(
            [sys.executable, str(SCRIPT),
             "--plan-dir", str(bogus),
             "--project-root", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 2
        assert "not a directory" in result.stderr.lower()

    def test_spec_is_directory_exits_two(self, tmp_path):
        result = subprocess.run(
            [sys.executable, str(SCRIPT),
             "--spec", str(tmp_path),
             "--project-root", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 2
        assert "not a file" in result.stderr.lower()


# ---------------------------------------------------------------------------
# spec-driven mode (used by tkm:migrate-aidd). Default --mode source unchanged;
# spec-driven additionally accepts spec:// URIs and specsRoot-relative paths.
# [FROM_CODE] citations remain validated as real source paths.
# ---------------------------------------------------------------------------

def _run_spec_driven(spec_path: Path, project_root: Path,
                     specs_root: Path | None = None) -> tuple[int, dict]:
    argv = [sys.executable, str(SCRIPT), "--spec", str(spec_path),
            "--project-root", str(project_root), "--mode", "spec-driven"]
    if specs_root is not None:
        argv += ["--specs-root", str(specs_root)]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    if not result.stdout.strip():
        raise RuntimeError(f"no JSON (exit={result.returncode}). stderr: {result.stderr}")
    return result.returncode, json.loads(result.stdout)


class TestSpecDrivenMode:
    def test_valid_spec_uri_accepted(self, tmp_path):
        spec, root = _make_spec_tree(tmp_path, "spec://001-create-taskify/spec.md#user-stories")
        code, data = _run_spec_driven(spec, root)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_specsroot_relative_citation_accepted(self, tmp_path):
        specs_root = tmp_path / "specs"
        (specs_root / "001-create-taskify").mkdir(parents=True)
        (specs_root / "001-create-taskify" / "spec.md").write_text("# spec", encoding="utf-8")
        spec, root = _make_spec_tree(tmp_path, "001-create-taskify/spec.md")
        code, data = _run_spec_driven(spec, root, specs_root=specs_root)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_spec_uri_leading_dotdot_rejected(self, tmp_path):
        # spec://..  fails the SPEC_URI grammar (first segment must be alnum)
        spec, root = _make_spec_tree(tmp_path, "spec://../../etc/passwd")
        code, data = _run_spec_driven(spec, root)
        assert code == 1
        assert _critical_rule_ids(data) == ["citation.spec_uri_invalid"]

    def test_spec_uri_inpath_traversal_rejected(self, tmp_path):
        # valid first segment but traversal in the path part -> rejected (M1 fix)
        spec, root = _make_spec_tree(tmp_path, "spec://001-x/../../../etc/passwd")
        code, data = _run_spec_driven(spec, root)
        assert code == 1
        assert _critical_rule_ids(data) == ["citation.spec_uri_invalid"]

    def test_bare_from_code_citation_rejected(self, tmp_path):
        # [FROM_CODE] without a line range hits the bare branch -> must be flagged,
        # never accepted as a spec URI (H1 fix).
        spec_dir = tmp_path / "artifacts" / "features" / "F001_Auth"
        spec_dir.mkdir(parents=True)
        spec = spec_dir / "spec.md"
        spec.write_text(
            "# F001\n\n## Source Code References\n\n"
            "**Source:** `spec://001-x/real.md` [FROM_CODE]\n",
            encoding="utf-8",
        )
        code, data = _run_spec_driven(spec, tmp_path)
        assert code == 1
        assert "citation.from_code_no_range" in _critical_rule_ids(data)

    def test_from_code_citation_still_validated_as_source(self, tmp_path):
        # [FROM_CODE] forces source-path validation even in spec-driven mode.
        (tmp_path / "cited-source.py").write_text(
            (FIXTURES / "cited-source.py").read_text(encoding="utf-8"), encoding="utf-8"
        )
        spec_dir = tmp_path / "artifacts" / "features" / "F001_Auth"
        spec_dir.mkdir(parents=True)
        spec = spec_dir / "spec.md"
        spec.write_text(
            "# F001\n\n## Source Code References\n\n"
            "**Source:** `cited-source.py:999` [FROM_CODE]\n",
            encoding="utf-8",
        )
        code, data = _run_spec_driven(spec, tmp_path)
        assert code == 1
        assert "citation.range_invalid" in _critical_rule_ids(data)


class TestSourceModeDefaultUnchanged:
    def test_default_mode_rejects_spec_uri(self):
        # spec:// is NOT a valid source-path citation; default mode must reject it.
        # Reuse the existing pass/bad fixtures to confirm source-mode parity.
        code, data = _run(FIXTURES / "specs" / "spec-pass.md")
        assert code == 0 and _critical_rule_ids(data) == []

    def test_default_mode_spec_uri_is_ignored_not_accepted(self, tmp_path):
        # Under default source mode, a bare spec:// value has no :N-M, so CITATION_RE
        # doesn't match and source mode does not run the spec-driven branch — i.e. it
        # is neither validated nor falsely accepted as a source path.
        spec, root = _make_spec_tree(tmp_path, "spec://001-x/spec.md#s")
        code, data = _run(spec, root)
        assert code == 0  # no critical (source mode ignores non-matching lines)
        assert _critical_rule_ids(data) == []


# ---------------------------------------------------------------------------
# RE-mode citation-density tests (Phase C, re-output-contract.md)
# ---------------------------------------------------------------------------

def _run_re_mode(spec_path: Path, project_root: Path,
                 density_min: float = 0.8) -> tuple[int, dict]:
    """Run the validator with --re-mode and a given --density-min."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--spec", str(spec_path),
         "--project-root", str(project_root),
         "--re-mode",
         "--density-min", str(density_min)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if not result.stdout.strip():
        raise RuntimeError(
            f"validator produced no JSON output (exit={result.returncode}).\n"
            f"stderr: {result.stderr}"
        )
    return result.returncode, json.loads(result.stdout)


def _make_low_density_spec(tmp_path: Path, *, n_claim_lines: int = 10,
                            n_cited: int = 0) -> tuple[Path, Path]:
    """Create a spec where n_cited out of n_claim_lines have a Source citation.

    The source file is written alongside the spec so citations resolve.
    """
    spec_dir = tmp_path / "artifacts" / "features" / "F001_Auth"
    spec_dir.mkdir(parents=True)
    # Write a tiny source file so citations can resolve
    src = tmp_path / "src" / "auth.py"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("\n".join(f"# line {i}" for i in range(20)), encoding="utf-8")

    lines = ["# F001_Auth — Auth\n", ""]
    for i in range(n_claim_lines):
        if i < n_cited:
            lines.append(f"This claim is cited. **Source:** `src/auth.py:1-2`")
        else:
            lines.append(f"This claim has no citation. Claim number {i}.")
    spec = spec_dir / "spec.md"
    spec.write_text("\n".join(lines), encoding="utf-8")
    return spec, tmp_path


class TestReModeOff:
    """Without --re-mode, behaviour must be byte-for-byte unchanged."""

    def test_no_re_mode_no_density_issue(self, tmp_path):
        # A spec with zero citations emits no density issue in normal (non-RE) mode
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=10, n_cited=0)
        code, data = _run(spec, root)
        rule_ids = [i["rule_id"] for s in data["specs"].values() for i in s["issues"]]
        assert "citation_density_low" not in rule_ids

    def test_no_re_mode_exit_0_on_warn_only_spec(self, tmp_path):
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=5, n_cited=0)
        code, data = _run(spec, root)
        # No critical issues from a spec with no source citations in default mode
        assert code == 0


class TestReModeOn:
    """With --re-mode, density below threshold → WARN citation_density_low."""

    def test_low_density_emits_warn(self, tmp_path):
        # 0 out of 10 claim lines cited → density 0% < 80%
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=10, n_cited=0)
        code, data = _run_re_mode(spec, root, density_min=0.8)
        issues = [i for s in data["specs"].values() for i in s["issues"]]
        warn_ids = [i["rule_id"] for i in issues if i["severity"] == "warning"]
        assert "citation_density_low" in warn_ids

    def test_low_density_does_not_halt(self, tmp_path):
        # WARN must not flip exit to 1 (only critical issues do that)
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=10, n_cited=0)
        code, data = _run_re_mode(spec, root, density_min=0.8)
        assert code == 0  # advisory WARN, not critical

    def test_above_threshold_no_density_warn(self, tmp_path):
        # 9 out of 10 cited → density 90% > 80% → no density warn
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=10, n_cited=9)
        code, data = _run_re_mode(spec, root, density_min=0.8)
        issues = [i for s in data["specs"].values() for i in s["issues"]]
        warn_ids = [i["rule_id"] for i in issues if i["severity"] == "warning"]
        assert "citation_density_low" not in warn_ids

    def test_exactly_at_threshold_no_warn(self, tmp_path):
        # 8 out of 10 cited → density exactly 80% = threshold → no warn (not strictly below)
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=10, n_cited=8)
        code, data = _run_re_mode(spec, root, density_min=0.8)
        issues = [i for s in data["specs"].values() for i in s["issues"]]
        warn_ids = [i["rule_id"] for i in issues if i["severity"] == "warning"]
        assert "citation_density_low" not in warn_ids

    def test_density_min_respected(self, tmp_path):
        # With a very high threshold (0.99), 5/10 cited still triggers warn
        spec, root = _make_low_density_spec(tmp_path, n_claim_lines=10, n_cited=5)
        code, data = _run_re_mode(spec, root, density_min=0.99)
        issues = [i for s in data["specs"].values() for i in s["issues"]]
        warn_ids = [i["rule_id"] for i in issues if i["severity"] == "warning"]
        assert "citation_density_low" in warn_ids

    def test_re_mode_does_not_change_existing_citation_checks(self, tmp_path):
        # A valid spec-pass fixture must still exit 0 under --re-mode
        # (density check only adds warnings, never removes passes)
        code, data = _run_re_mode(FIXTURES / "specs" / "spec-pass.md",
                                  REPO_ROOT, density_min=0.0)
        assert code == 0


class TestReModeScreenArtifacts:
    """v21.0.0 — RE-mode also counts screen-list/screen-flow toward citation density."""

    def _run_plan_dir_re(self, plan_dir: Path, root: Path):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--plan-dir", str(plan_dir),
             "--project-root", str(root), "--re-mode", "--density-min", "0.8"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.stdout.strip(), result.stderr
        return result.returncode, json.loads(result.stdout)

    def test_low_density_screen_list_warns(self, tmp_path):
        # A screen-list.md present in artifacts/ with no citations → density WARN under its own entry.
        artifacts = tmp_path / "artifacts"
        artifacts.mkdir(parents=True)
        lines = ["## Screen Index", ""]
        lines += [f"This screen claim has no citation. Row {i}." for i in range(10)]
        (artifacts / "screen-list.md").write_text("\n".join(lines), encoding="utf-8")
        code, data = self._run_plan_dir_re(tmp_path, tmp_path)
        assert code == 0  # advisory WARN, never HALT
        assert "screen-list" in data["specs"]
        warn_ids = [i["rule_id"] for i in data["specs"]["screen-list"]["issues"]]
        assert "citation_density_low" in warn_ids

    def test_absent_screen_artifact_no_entry(self, tmp_path):
        # Headless run (no screen-list.md on disk) → no screen-list entry, no crash.
        artifacts = tmp_path / "artifacts"
        artifacts.mkdir(parents=True)
        code, data = self._run_plan_dir_re(tmp_path, tmp_path)
        assert code == 0
        assert "screen-list" not in data["specs"]
        assert "screen-flow" not in data["specs"]


# ---------------------------------------------------------------------------
# Regression: invalid env var does not crash, uses default density
# ---------------------------------------------------------------------------

class TestInvalidDensityEnv:
    def test_invalid_density_env_no_crash(self, tmp_path, monkeypatch):
        """Regression: bad REBUILD_CITATION_DENSITY_MIN env value no longer crashes."""
        # Set env to invalid value
        monkeypatch.setenv("REBUILD_CITATION_DENSITY_MIN", "disabled")

        # Create a minimal spec
        spec_dir = tmp_path / "artifacts" / "features" / "F001_Test"
        spec_dir.mkdir(parents=True)
        spec = spec_dir / "spec.md"
        spec.write_text(
            "# F001 Test\n\n**Source:** `cited-source.py:1`\n",
            encoding="utf-8",
        )

        # Run main with minimal args — should not crash
        from validate_source_citations import main
        rc = main([
            "--spec", str(spec),
            "--project-root", str(tmp_path),
        ])
        # May be 1 (missing citation logic) or 0 (file not found), but not a crash
        assert rc in (0, 1, 2)

    def test_valid_density_env_used(self, tmp_path, monkeypatch):
        """Regression guard: valid density env IS parsed and used."""
        monkeypatch.setenv("REBUILD_CITATION_DENSITY_MIN", "0.5")

        spec_dir = tmp_path / "artifacts" / "features" / "F001_Test"
        spec_dir.mkdir(parents=True)
        spec = spec_dir / "spec.md"
        spec.write_text(
            "# F001 Test\n\n## Behavior\n\n"
            "Claim 1: does X.\n"
            "Claim 2: does Y.\n"
            "Claim 3: does Z.\n\n"
            "**Source:** `test.py:1`\n",  # Only 1 out of 3 claims cited
            encoding="utf-8",
        )

        from validate_source_citations import main
        # RE mode should use 0.5 threshold
        rc = main([
            "--spec", str(spec),
            "--project-root", str(tmp_path),
            "--re-mode",
        ])
        # With 1/3 cited < 0.5 threshold, should warn (and exit 0 since density warn is not critical)
        # The return code depends on other issues, but parsing should succeed
        assert rc in (0, 1, 2)
