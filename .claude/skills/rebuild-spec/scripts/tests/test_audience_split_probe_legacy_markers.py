"""Tests for phase-02 (B1): legacy generation markers as a clean provenance signal in
`_audience_split_probe_lib.py` / `_audience_split_provenance_lib.py`.

Why this file exists (phase-00 CORRECTION 2 / phase-00 U2): rebuild-spec's own generator
has NEVER written `authored_by:` -- only takumi's promote path does -- so a real
rebuild-spec-generated v26 corpus carries zero YAML frontmatter anywhere. The existing
fixtures in `test_migrate_feature_audience_split.py` all synthesize `authored_by:
rebuild-spec` via `_write_v26_feature()`'s hard-coded default, which is exactly the
signal the real producer never emits -- so every test there passed on a script that could
not migrate any real corpus. This file's fixtures are built WITHOUT frontmatter, using a
sibling helper (`_write_v26_legacy_feature`) instead of touching that existing helper.

Matrix reference: plans/260817-1420-rebuild-spec-v27-migrate-legacy-docs/
phase-02-legacy-provenance-markers.md, cases T1-T14.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _audience_split_probe_lib as probe_lib  # noqa: E402

_V26_FILES = ("technical-spec.md", "business-context.md", "screens.md", "edge-cases.md")


def _init_git_repo(d: Path) -> None:
    subprocess.run(["git", "init", str(d)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.email", "test@test.com"],
                    capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.name", "Test"],
                    capture_output=True, check=True)


def _commit_all(d: Path, message: str = "commit") -> None:
    subprocess.run(["git", "-C", str(d), "add", "-A"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "commit", "-q", "-m", message],
                    capture_output=True, check=True)


def _fm(*lines: str) -> str:
    if not lines:
        return ""
    return "---\n" + "\n".join(lines) + "\n---\n"


def _write_v26_legacy_feature(
    feature_dir: Path,
    *,
    tech_extra_lines: tuple[str, ...] = ("**Generated**: 2026-06-04",),
    satellite_extra_lines: dict[str, tuple[str, ...]] | None = None,
) -> None:
    """A v26 4-file feature dir with NO frontmatter anywhere -- the shape rebuild-spec's
    own generator actually emits (measured: the real sharetribe corpus has zero YAML
    frontmatter in any of its 264 feature files). `tech_extra_lines` are inserted after
    the H1 in `technical-spec.md` (never at line 0 -- position varies in the real corpus:
    line 4, 5, and 7 all occur). `satellite_extra_lines` optionally injects extra lines
    into a named satellite file, for markers that live outside `technical-spec.md`
    (e.g. the `FORBIDDEN TOKENS` marker on `business-context.md`)."""
    feature_dir.mkdir(parents=True, exist_ok=True)
    satellite_extra_lines = satellite_extra_lines or {}

    tech_body = ["# F001_Auth", "", *tech_extra_lines, "", "## Overview", "",
                 "Old v26 technical spec placeholder."]
    (feature_dir / "technical-spec.md").write_text("\n".join(tech_body) + "\n", encoding="utf-8")

    for name, title in (("business-context.md", "Business Context"),
                        ("screens.md", "Screens"), ("edge-cases.md", "Edge Cases")):
        body = [f"# {title}", "", *satellite_extra_lines.get(name, ()), "", "Placeholder."]
        (feature_dir / name).write_text("\n".join(body) + "\n", encoding="utf-8")


def _feature_paths(feature_dir: Path) -> list[Path]:
    return [feature_dir / n for n in _V26_FILES]


# --------------------------------------------------------------------------- #
# T1 -- marker-only unit (no frontmatter anywhere) probes CLEAN_LEGACY
# --------------------------------------------------------------------------- #
def test_t1_marker_only_unit_is_clean_legacy(tmp_path):
    _init_git_repo(tmp_path)
    feature_dir = tmp_path / "docs" / "features" / "F001_Auth"
    _write_v26_legacy_feature(feature_dir)
    _commit_all(tmp_path)

    result = probe_lib.probe_feature(_feature_paths(feature_dir), tmp_path)
    assert result.verdict == probe_lib.CLEAN_LEGACY
    assert "generated-date" in result.reason


# --------------------------------------------------------------------------- #
# T2 -- marker + corroborating Contract header, still CLEAN_LEGACY
# --------------------------------------------------------------------------- #
def test_t2_marker_plus_contract_header_is_clean_legacy(tmp_path):
    _init_git_repo(tmp_path)
    feature_dir = tmp_path / "docs" / "features" / "F001_Auth"
    _write_v26_legacy_feature(
        feature_dir,
        tech_extra_lines=(
            "**Generated**: 2026-06-04",
            "<!-- Contract: references/feature-spec-researcher-contract.md -->",
        ),
    )
    _commit_all(tmp_path)

    result = probe_lib.probe_feature(_feature_paths(feature_dir), tmp_path)
    assert result.verdict != probe_lib.HAND_EDITED
    assert result.verdict == probe_lib.CLEAN_LEGACY


# --------------------------------------------------------------------------- #
# T3 -- integrity is not relaxed for a markerless sibling: an uncommitted hand-edit
# on edge-cases.md (which never carries a marker in the real corpus) still poisons
# the whole unit.
# --------------------------------------------------------------------------- #
def test_t3_uncommitted_edit_on_markerless_sibling_poisons_unit(tmp_path):
    _init_git_repo(tmp_path)
    feature_dir = tmp_path / "docs" / "features" / "F001_Auth"
    _write_v26_legacy_feature(feature_dir)
    _commit_all(tmp_path)

    (feature_dir / "edge-cases.md").write_text(
        "# Edge Cases\n\nHAND-EDITED, uncommitted.\n", encoding="utf-8",
    )

    result = probe_lib.probe_feature(_feature_paths(feature_dir), tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert "HEAD" in result.reason or "uncommitted" in result.reason


# --------------------------------------------------------------------------- #
# T4 -- no file in the unit bears any marker -> fails closed
# --------------------------------------------------------------------------- #
def test_t4_no_marker_anywhere_is_hand_edited(tmp_path):
    _init_git_repo(tmp_path)
    feature_dir = tmp_path / "docs" / "features" / "F001_Auth"
    _write_v26_legacy_feature(feature_dir, tech_extra_lines=())
    _commit_all(tmp_path)

    result = probe_lib.probe_feature(_feature_paths(feature_dir), tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert "no generator marker" in result.reason


# --------------------------------------------------------------------------- #
# T5 -- doc_lock: user wins over a valid marker
# --------------------------------------------------------------------------- #
def test_t5_doc_lock_user_wins_over_valid_marker(tmp_path):
    _init_git_repo(tmp_path)
    feature_dir = tmp_path / "docs" / "features" / "F001_Auth"
    _write_v26_legacy_feature(feature_dir)
    (feature_dir / "screens.md").write_text(
        _fm("doc_lock: user") + "# Screens\n\nPlaceholder.\n", encoding="utf-8",
    )
    _commit_all(tmp_path)

    result = probe_lib.probe_feature(_feature_paths(feature_dir), tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert result.doc_lock is True


# --------------------------------------------------------------------------- #
# T6 -- a foreign authored_by: wins over a valid marker
# --------------------------------------------------------------------------- #
def test_t6_foreign_authored_by_wins_over_valid_marker(tmp_path):
    _init_git_repo(tmp_path)
    feature_dir = tmp_path / "docs" / "features" / "F001_Auth"
    _write_v26_legacy_feature(feature_dir)
    (feature_dir / "technical-spec.md").write_text(
        _fm("authored_by: human") + "# F001_Auth\n\n**Generated**: 2026-06-04\n\n"
        "## Overview\n\nPlaceholder.\n",
        encoding="utf-8",
    )
    _commit_all(tmp_path)

    result = probe_lib.probe_feature(_feature_paths(feature_dir), tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert "human" in result.reason


# --------------------------------------------------------------------------- #
# T7 -- git corroboration is still mandatory even with a valid marker: untracked
# --------------------------------------------------------------------------- #
def test_t7_untracked_unit_is_hand_edited(tmp_path):
    _init_git_repo(tmp_path)
    feature_dir = tmp_path / "docs" / "features" / "F001_Auth"
    _write_v26_legacy_feature(feature_dir)
    # deliberately never `git add`/`git commit`ed

    result = probe_lib.probe_feature(_feature_paths(feature_dir), tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert "git trail" in result.reason


# --------------------------------------------------------------------------- #
# T8 -- git corroboration is still mandatory even with a valid marker: no .git dir
# --------------------------------------------------------------------------- #
def test_t8_no_git_directory_is_hand_edited(tmp_path):
    feature_dir = tmp_path / "docs" / "features" / "F001_Auth"
    _write_v26_legacy_feature(feature_dir)
    # no `git init` at all under tmp_path

    result = probe_lib.probe_feature(_feature_paths(feature_dir), tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert ".git directory" in result.reason


# --------------------------------------------------------------------------- #
# T9 -- the existing authored_by: rebuild-spec happy path stays green, with the new
# `provenance` field correctly attributed to "authored_by" (not a marker).
# --------------------------------------------------------------------------- #
def test_t9_authored_by_present_provenance_is_authored_by(tmp_path):
    _init_git_repo(tmp_path)
    path = tmp_path / "docs" / "features" / "F001_Auth" / "technical-spec.md"
    path.parent.mkdir(parents=True)
    path.write_text(_fm("authored_by: rebuild-spec") + "# F001_Auth\n\nContent.\n", encoding="utf-8")
    _commit_all(tmp_path)

    result = probe_lib.probe_file(path, tmp_path)
    assert result.verdict == probe_lib.CLEAN
    assert result.provenance == "authored_by"


# --------------------------------------------------------------------------- #
# T10 -- single-file probe (Mode C path): a screen spec with only the marker
# --------------------------------------------------------------------------- #
def test_t10_single_screen_spec_marker_only_is_clean_legacy(tmp_path):
    _init_git_repo(tmp_path)
    path = tmp_path / "docs" / "screens" / "SCR001_Login" / "spec.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "# SCR001_Login — Screen Spec\n\n**Generated**: 2026-06-04\n\n"
        "## Purpose\n\nPlaceholder.\n",
        encoding="utf-8",
    )
    _commit_all(tmp_path)

    result = probe_lib.probe_file(path, tmp_path)
    assert result.verdict == probe_lib.CLEAN_LEGACY
    assert result.provenance == "generated-date"


# --------------------------------------------------------------------------- #
# T11 -- single-file probe (Mode B path): business-rules.md with only the marker
# --------------------------------------------------------------------------- #
def test_t11_single_business_rules_marker_only_is_clean_legacy(tmp_path):
    _init_git_repo(tmp_path)
    path = tmp_path / "docs" / "system" / "business-rules.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "# Business Rules\n\n**Generated**: 2026-06-04\n\n### Some Rule\n\nPlaceholder.\n",
        encoding="utf-8",
    )
    _commit_all(tmp_path)

    result = probe_lib.probe_file(path, tmp_path)
    assert result.verdict == probe_lib.CLEAN_LEGACY


# --------------------------------------------------------------------------- #
# T12 -- v27's own "migrated" sentinel value must NOT be mistaken for the strict
# ISO-date marker (guards against the date rule quietly loosening).
# --------------------------------------------------------------------------- #
def test_t12_generated_migrated_literal_does_not_match_strict_date_marker(tmp_path):
    _init_git_repo(tmp_path)
    path = tmp_path / "docs" / "features" / "F001_Auth" / "technical-spec.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "# F001_Auth\n\n**Generated**: migrated\n\n## Overview\n\nPlaceholder.\n",
        encoding="utf-8",
    )
    _commit_all(tmp_path)

    result = probe_lib.probe_file(path, tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert "no generator marker" in result.reason


# --------------------------------------------------------------------------- #
# T13 -- marker position varies (line 4 vs line 7); never hardcode a line index
# --------------------------------------------------------------------------- #
def test_t13_marker_position_varies_line4_and_line7(tmp_path):
    _init_git_repo(tmp_path)

    p4 = tmp_path / "docs" / "features" / "F001_Auth" / "technical-spec.md"
    p4.parent.mkdir(parents=True)
    p4_lines = ["# F001_Auth", "", "", "**Generated**: 2026-06-04", "",
                "## Overview", "", "Placeholder."]
    assert p4_lines[3] == "**Generated**: 2026-06-04"  # index 3 (0-based) == file line 4
    p4.write_text("\n".join(p4_lines) + "\n", encoding="utf-8")

    p7 = tmp_path / "docs" / "features" / "F002_Search" / "technical-spec.md"
    p7.parent.mkdir(parents=True)
    p7_lines = ["# F002_Search", "", "", "", "", "", "**Generated**: 2026-06-04", "",
                "## Overview", "", "Placeholder."]
    assert p7_lines[6] == "**Generated**: 2026-06-04"  # index 6 (0-based) == file line 7
    p7.write_text("\n".join(p7_lines) + "\n", encoding="utf-8")

    _commit_all(tmp_path)

    assert probe_lib.probe_file(p4, tmp_path).verdict == probe_lib.CLEAN_LEGACY
    assert probe_lib.probe_file(p7, tmp_path).verdict == probe_lib.CLEAN_LEGACY


# --------------------------------------------------------------------------- #
# T14 -- an unterminated multi-line `FORBIDDEN TOKENS` opener still matches
# (prefix-anchored deliberately; 10 of 31 real occurrences never close the comment)
# --------------------------------------------------------------------------- #
def test_t14_unterminated_forbidden_tokens_marker_matches(tmp_path):
    _init_git_repo(tmp_path)
    feature_dir = tmp_path / "docs" / "features" / "F001_Auth"
    _write_v26_legacy_feature(
        feature_dir,
        tech_extra_lines=(),  # technical-spec carries no marker in this fixture
        satellite_extra_lines={
            "business-context.md": ("<!-- FORBIDDEN TOKENS — do not leak paths below",),
        },
    )
    _commit_all(tmp_path)

    result = probe_lib.probe_file(feature_dir / "business-context.md", tmp_path)
    assert result.verdict == probe_lib.CLEAN_LEGACY
    assert result.provenance == "forbidden-tokens"
