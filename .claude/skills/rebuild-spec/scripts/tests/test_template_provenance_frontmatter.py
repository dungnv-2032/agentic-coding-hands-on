"""Phase 07 — B1 forward fix guard: rebuild-spec's own templates and the researcher
contracts that govern them must emit/require `authored_by: rebuild-spec` frontmatter
at byte 0.

Root cause this guards against (see plans/260817-1420-rebuild-spec-v27-migrate-legacy-docs/
phase-00-verified-context.md): `references/feature-spec-researcher-contract.md` never
mentioned `authored_by`, so every real corpus rebuild-spec ever produced had zero
frontmatter — the audience-split migration probe (`_audience_split_probe_lib.py`) then
fails closed to HAND_EDITED on every file, unconditionally. This test file is the
negative-probe guard: the requirement must be visible in both the templates (T1/T2/T3/T6)
and the contracts that instruct researchers to follow them (T4), and the change must not
break the existing F### heading proximity check (T5).
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
_SKILL_DIR = _SCRIPTS_DIR.parent
_TEMPLATES_DIR = _SKILL_DIR / "templates"
_REFERENCES_DIR = _SKILL_DIR / "references"

if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _audience_split_probe_lib as probe_lib  # noqa: E402
import _slug_lib  # noqa: E402
import validate_feature_spec as vfs  # noqa: E402

TEMPLATES = [
    "functional-spec-template.md",
    "technical-spec-template.md",
    "screen-spec-template.md",
    "behavior-logic-template.md",
]

CONTRACTS = [
    "feature-spec-researcher-contract.md",
    "screen-spec-researcher-contract.md",
]

FRONTMATTER_BLOCK = "---\nauthored_by: rebuild-spec\n---"


def _load_check_layout_paths():
    spec = importlib.util.spec_from_file_location(
        "check_layout_paths", _SCRIPTS_DIR / "check_layout_paths.py"
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _init_git_repo(d: Path) -> None:
    subprocess.run(["git", "init", str(d)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.email", "test@test.com"],
                    capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.name", "Test"],
                    capture_output=True, check=True)


def _commit_all(d: Path) -> None:
    subprocess.run(["git", "-C", str(d), "add", "-A"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "commit", "-q", "-m", "commit"], capture_output=True, check=True)


# --------------------------------------------------------------------------- #
# T1 — each template's literal first three lines are the authored_by block
# --------------------------------------------------------------------------- #
class TestTemplatesStartWithProvenanceFrontmatter:
    @pytest.mark.parametrize("name", TEMPLATES)
    def test_template_starts_with_frontmatter(self, name):
        content = (_TEMPLATES_DIR / name).read_text(encoding="utf-8")
        assert content.startswith(FRONTMATTER_BLOCK), (
            f"{name} must open with {FRONTMATTER_BLOCK!r} at byte 0, "
            f"found: {content[:60]!r}"
        )


# --------------------------------------------------------------------------- #
# T2 — proves byte-0 placement is functionally correct, not just visually correct
# --------------------------------------------------------------------------- #
class TestReadFrontmatterSeesAuthoredBy:
    @pytest.mark.parametrize("name", TEMPLATES)
    def test_read_frontmatter_contains_authored_by(self, name):
        path = _TEMPLATES_DIR / name
        fm = _slug_lib._read_frontmatter(path)
        assert "authored_by" in fm, f"{name}: _read_frontmatter() found no frontmatter block"
        assert _slug_lib.read_authored_by(path) == "rebuild-spec"


# --------------------------------------------------------------------------- #
# T3 — end-to-end: probe_file resolves CLEAN via the presence check, not
# HAND_EDITED, once a template is committed to a git tree.
# --------------------------------------------------------------------------- #
class TestProbeFileAcceptsTemplatesAsClean:
    @pytest.mark.parametrize("name", TEMPLATES)
    def test_probe_file_clean_via_authored_by(self, tmp_path, name):
        _init_git_repo(tmp_path)
        dest = tmp_path / name
        dest.write_text((_TEMPLATES_DIR / name).read_text(encoding="utf-8"), encoding="utf-8")
        _commit_all(tmp_path)

        result = probe_lib.probe_file(dest, tmp_path)
        assert result.verdict == probe_lib.CLEAN, (
            f"{name}: expected CLEAN, got {result.verdict} ({result.reason})"
        )
        assert "authored_by" in result.reason


# --------------------------------------------------------------------------- #
# T4 — negative-probe guard: the requirement is stated in the contracts, not
# just satisfied incidentally in the templates. This is the literal fix for the
# root cause (feature-spec-researcher-contract.md never mentioned authored_by).
# --------------------------------------------------------------------------- #
class TestResearcherContractsRequireAuthoredBy:
    @pytest.mark.parametrize("name", CONTRACTS)
    def test_contract_states_authored_by_rebuild_spec(self, name):
        content = (_REFERENCES_DIR / name).read_text(encoding="utf-8")
        assert "authored_by: rebuild-spec" in content, (
            f"{name} must literally state the 'authored_by: rebuild-spec' requirement"
        )


# --------------------------------------------------------------------------- #
# T5 — validate_feature_spec's F### heading check (validate_feature_spec.py,
# "first 5 lines after any leading YAML frontmatter fence") must still pass
# once the provenance block is prepended ahead of the technical-spec.md heading.
# --------------------------------------------------------------------------- #
class TestValidateFeatureSpecStillFindsHeading:
    def test_f_code_heading_found_after_frontmatter_block(self, tmp_path):
        content = (
            "---\nauthored_by: rebuild-spec\n---\n"
            "<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths -->\n"
            "<!-- Contract: references/feature-spec-researcher-contract.md -->\n\n"
            "# F001_Test\n\n## Overview\n\nContent.\n"
        )
        spec_path = tmp_path / "legacy-spec.md"  # not "technical-spec.md" -> standalone branch
        spec_path.write_text(content, encoding="utf-8")

        result = vfs.validate(plan_dir=tmp_path, root=tmp_path, single=spec_path, docs_root=None)
        issues = next(iter(result["specs"].values()))["issues"]
        heading_issues = [i for i in issues if i["rule_id"] == "FeatureSpec.f_code_format"]
        assert heading_issues == [], f"F### heading check regressed: {heading_issues}"


# --------------------------------------------------------------------------- #
# T6 — check_layout_paths.py must still treat each template as exempt now that
# the layout-exempt marker sits at line 4 (or is absent, for screen-spec-template.md
# which has no hardcoded docs/ paths) instead of line 1. U3 (phase-00): the
# exemption scan already covers the first 50 lines of the file, so this is a
# confirming test, not a risk to design around.
# --------------------------------------------------------------------------- #
class TestLayoutValidatorAcceptsTemplates:
    def test_check_layout_paths_scan_finds_no_offences_in_templates(self):
        mod = _load_check_layout_paths()
        offences = mod.scan(_TEMPLATES_DIR)
        offences_in_scope = [o for o in offences if o[0].name in TEMPLATES]
        assert offences_in_scope == [], f"unexpected layout offences: {offences_in_scope}"
