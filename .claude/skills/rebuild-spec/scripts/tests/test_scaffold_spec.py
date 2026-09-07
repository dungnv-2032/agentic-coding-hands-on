"""Tests for scaffold_spec.py.

Pattern mirrors test_structural_fixer.py: subprocess via sys.executable.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "scaffold_spec.py"
VALIDATOR = SCRIPTS_DIR / "validate_feature_spec.py"
REPO_ROOT = Path(__file__).resolve().parents[5]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(cwd or REPO_ROOT),
    )


def _run_validator(spec_dir: Path, project_root: Path | None = None) -> subprocess.CompletedProcess:
    # project_root must contain spec_dir for the validator's assert_under check.
    # When spec_dir is in /tmp, pass the tmp root (plan_dir = spec_dir.parent.parent).
    root = project_root or spec_dir.parent.parent
    return subprocess.run(
        [sys.executable, str(VALIDATOR),
         "--spec", str(spec_dir),
         "--project-root", str(root)],
        capture_output=True,
        text=True,
        timeout=30,
    )


def _make_plan_dir(tmp_path: Path, *, mode: str = "single",
                   intents: list | None = None, justification: str = "",
                   rp_sentinel: bool = False) -> Path:
    """Set up a minimal plan dir with .intent-enum.json."""
    plan_dir = tmp_path / "plan"
    spec_dir = plan_dir / "spec"
    spec_dir.mkdir(parents=True)
    intent_data: dict = {
        "mode": mode,
        "intents": intents if intents is not None else ["feature-a"],
        "justification": justification,
    }
    (spec_dir / ".intent-enum.json").write_text(
        json.dumps(intent_data), encoding="utf-8"
    )
    if rp_sentinel:
        (plan_dir / ".rp-1.5a-pending").touch()
    return plan_dir


def _base_single_args(plan_dir: Path, slug: str = "my-feature",
                      fcode: str | None = None) -> list[str]:
    args = [
        "--plan-dir", str(plan_dir),
        "--mode", "single",
        "--lang", "en",
        "--slug", slug,
    ]
    if fcode:
        args += ["--fcode", fcode]
    return args


def _base_system_args(plan_dir: Path, feature_names: str) -> list[str]:
    return [
        "--plan-dir", str(plan_dir),
        "--mode", "system",
        "--lang", "en",
        "--feature-names", feature_names,
    ]


# ---------------------------------------------------------------------------
# Chokepoint tests
# ---------------------------------------------------------------------------

class TestChokepoint:
    def test_missing_intent_enum_exits_2(self, tmp_path):
        plan_dir = tmp_path / "plan"
        (plan_dir / "spec").mkdir(parents=True)
        # No .intent-enum.json written
        result = _run(_base_single_args(plan_dir))
        assert result.returncode == 2

    def test_missing_intent_enum_creates_no_files(self, tmp_path):
        plan_dir = tmp_path / "plan"
        (plan_dir / "spec").mkdir(parents=True)
        _run(_base_single_args(plan_dir))
        assert not (plan_dir / "spec" / "my-feature").exists()

    def test_single_mode_over1_intent_no_justification_exits_2(self, tmp_path):
        plan_dir = _make_plan_dir(
            tmp_path, mode="single",
            intents=["feat-a", "feat-b"], justification=""
        )
        result = _run(_base_single_args(plan_dir))
        assert result.returncode == 2
        assert "under-decomposition" in result.stderr
        assert "2 intents" in result.stderr
        assert "mode=single" in result.stderr
        assert "no justification" in result.stderr

    def test_single_mode_over1_intent_with_justification_proceeds(self, tmp_path):
        plan_dir = _make_plan_dir(
            tmp_path, mode="single",
            intents=["feat-a", "feat-b"],
            justification="tightly coupled, same deployment unit"
        )
        result = _run(_base_single_args(plan_dir))
        assert result.returncode == 0

    def test_system_mode_rp_sentinel_present_exits_2(self, tmp_path):
        plan_dir = _make_plan_dir(
            tmp_path, mode="system",
            intents=["feat-a", "feat-b"],
            rp_sentinel=True,
        )
        result = _run(_base_system_args(plan_dir, "feat-a,feat-b"))
        assert result.returncode == 2
        assert "RP1.5a" in result.stderr or "rp-1.5a" in result.stderr.lower()

    def test_system_mode_less_than_2_intents_exits_2(self, tmp_path):
        plan_dir = _make_plan_dir(
            tmp_path, mode="system",
            intents=["only-one"],
        )
        result = _run(_base_system_args(plan_dir, "feat-a,feat-b"))
        assert result.returncode == 2

    def test_consistent_artifact_single_proceeds(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        result = _run(_base_single_args(plan_dir))
        assert result.returncode == 0

    def test_consistent_artifact_system_proceeds(self, tmp_path):
        plan_dir = _make_plan_dir(
            tmp_path, mode="system", intents=["feat-a", "feat-b"]
        )
        result = _run(_base_system_args(plan_dir, "feat-a,feat-b"))
        assert result.returncode == 0

    def test_dry_run_still_runs_chokepoint(self, tmp_path):
        plan_dir = tmp_path / "plan"
        (plan_dir / "spec").mkdir(parents=True)
        result = _run(_base_single_args(plan_dir) + ["--dry-run"])
        assert result.returncode == 2
        assert not (plan_dir / "spec" / "my-feature").exists()

    def test_mode_mismatch_exits_2(self, tmp_path):
        # .intent-enum.json says system, --mode says single
        plan_dir = _make_plan_dir(tmp_path, mode="system", intents=["a", "b"])
        result = _run(_base_single_args(plan_dir))
        assert result.returncode == 2


# ---------------------------------------------------------------------------
# SINGLE mode tests
# ---------------------------------------------------------------------------

class TestSingleMode:
    def test_exit_code_zero(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        result = _run(_base_single_args(plan_dir))
        assert result.returncode == 0, result.stderr

    def test_creates_exactly_2_spec_files_and_marker(self, tmp_path):
        """v27.0.0 (audience split): feature dir 4 files -> 2."""
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        feature_dir = plan_dir / "spec" / "my-feature"
        assert (feature_dir / "technical-spec.md").is_file()
        assert (feature_dir / "functional-spec.md").is_file()
        assert (feature_dir / ".scaffold-complete").is_file()

    def test_stdout_is_json_list_of_paths(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        result = _run(_base_single_args(plan_dir))
        paths = json.loads(result.stdout)
        assert isinstance(paths, list)
        assert len(paths) >= 2

    def test_frontmatter_status_draft(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        tech = (plan_dir / "spec" / "my-feature" / "technical-spec.md").read_text()
        assert "status: draft" in tech

    def test_frontmatter_authored_by_takumi(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        tech = (plan_dir / "spec" / "my-feature" / "technical-spec.md").read_text()
        assert "authored_by: takumi" in tech

    def test_frontmatter_lang(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        tech = (plan_dir / "spec" / "my-feature" / "technical-spec.md").read_text()
        assert "lang: en" in tech

    def test_frontmatter_no_fcode_when_not_given(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        tech = (plan_dir / "spec" / "my-feature" / "technical-spec.md").read_text()
        assert "fcode:" not in tech

    def test_technical_spec_h2_sections_in_order(self, tmp_path):
        """rebuild-spec 27.7.0 (action-thread reshape, phase 04): scaffold_spec.py now
        renders the thread shape (REQUIRED_H2_TECH_THREAD), not the legacy 5-bucket shape
        (`_LEGACY_TECH_H2_5BUCKET` as of phase 10's rename — see _spec_constants.py's own
        notes on both constants)."""
        from _spec_constants import REQUIRED_H2_TECH_THREAD
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        tech = (plan_dir / "spec" / "my-feature" / "technical-spec.md").read_text()
        positions = [tech.find(h2) for h2 in REQUIRED_H2_TECH_THREAD]
        assert all(p != -1 for p in positions), f"Missing H2s in: {tech[:500]}"
        assert positions == sorted(positions), "H2s are out of order"

    def test_technical_spec_no_longer_contains_a3_or_b4_skeletons(self, tmp_path):
        """RETIRED direction of F3 (v26.0.0): A3/B4 retired from technical-spec.md
        this release (phase 08, self-sufficiency v27.8) -- `scaffold_spec.py` no
        longer appends either skeleton after the REQUIRED_H2_TECH_THREAD loop,
        matching `templates/technical-spec-template.md`'s own retirement
        (`test_scaffold_matches_template.py` pins the two staying in agreement)."""
        from _spec_constants import A3_HEADING, B4_HEADING
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        tech = (plan_dir / "spec" / "my-feature" / "technical-spec.md").read_text()
        assert A3_HEADING not in tech
        assert B4_HEADING not in tech

    def test_a3_absence_classifies_as_pre_migration_warn_not_critical(self, tmp_path):
        """A fresh scaffold no longer carries A3 at all (retired, phase 08) --
        `check_source_walkthrough` must grade that absence WARN
        `reading_guide.pre_migration`, never CRITICAL. B4 (`check_db_impact`)
        retired entirely this release; nothing validates it any more."""
        import validate_reading_guide_db_impact as rg
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        tech = (plan_dir / "spec" / "my-feature" / "technical-spec.md").read_text()
        issues = rg.check_source_walkthrough(tech, "f")
        assert all(i["severity"] != "critical" for i in issues), issues
        rids = {i["rule_id"] for i in issues}
        assert rids == {"reading_guide.pre_migration"}

    def test_functional_spec_h2_sections_in_order(self, tmp_path):
        """v27.0.0: business-context.md/screens.md are retired — functional-spec.md's
        REQUIRED_H2_FUNC list replaces both (13 sections as of the P07 human-readable
        SOT renumber — see test_functional_spec_sot_sections.py for the dedicated
        renumber/degradation coverage)."""
        from _spec_constants import REQUIRED_H2_FUNC
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        func = (plan_dir / "spec" / "my-feature" / "functional-spec.md").read_text()
        positions = [func.find(h2) for h2 in REQUIRED_H2_FUNC]
        assert all(p != -1 for p in positions), f"Missing H2s in: {func[:500]}"
        assert positions == sorted(positions), "H2s are out of order"

    def test_scaffold_complete_marker_present(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        marker = plan_dir / "spec" / "my-feature" / ".scaffold-complete"
        assert marker.is_file()

    def test_idempotent_noop_when_marker_present(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        # Mutate a file after first scaffold
        tech = plan_dir / "spec" / "my-feature" / "technical-spec.md"
        original = tech.read_text()
        tech.write_text(original + "\n# extra", encoding="utf-8")
        # Re-run without --force — should be no-op (marker present)
        _run(_base_single_args(plan_dir))
        assert tech.read_text() == original + "\n# extra"


# ---------------------------------------------------------------------------
# --fcode tests
# ---------------------------------------------------------------------------

class TestFcode:
    def test_fcode_included_in_frontmatter(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir, fcode="F001"))
        tech = (plan_dir / "spec" / "my-feature" / "technical-spec.md").read_text()
        assert "fcode: F001" in tech

    def test_fcode_and_feature_names_mutually_exclusive(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        result = _run([
            "--plan-dir", str(plan_dir),
            "--mode", "single",
            "--lang", "en",
            "--slug", "my-feature",
            "--fcode", "F001",
            "--feature-names", "feat-a",
        ])
        assert result.returncode == 1

    def test_fcode_invalid_shape_exits_1(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        result = _run(_base_single_args(plan_dir, fcode="F1"))
        assert result.returncode == 1

    def test_fcode_requires_single_mode(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="system", intents=["a", "b"])
        result = _run([
            "--plan-dir", str(plan_dir),
            "--mode", "system",
            "--lang", "en",
            "--feature-names", "feat-a,feat-b",
            "--fcode", "F001",
        ])
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# SYSTEM mode tests
# ---------------------------------------------------------------------------

class TestSystemMode:
    def _make_system_plan(self, tmp_path: Path, intents: list | None = None) -> Path:
        return _make_plan_dir(
            tmp_path, mode="system",
            intents=intents or ["feat-a", "feat-b"],
        )

    def test_exit_code_zero(self, tmp_path):
        plan_dir = self._make_system_plan(tmp_path)
        result = _run(_base_system_args(plan_dir, "feat-a,feat-b"))
        assert result.returncode == 0, result.stderr

    def test_feature_list_stub_created(self, tmp_path):
        plan_dir = self._make_system_plan(tmp_path)
        _run(_base_system_args(plan_dir, "feat-a,feat-b"))
        fl = plan_dir / "spec" / "feature-list.md"
        assert fl.is_file()

    def test_feature_list_has_no_lang_or_fcode(self, tmp_path):
        plan_dir = self._make_system_plan(tmp_path)
        _run(_base_system_args(plan_dir, "feat-a,feat-b"))
        fl = (plan_dir / "spec" / "feature-list.md").read_text()
        assert "lang:" not in fl
        assert "fcode:" not in fl

    def test_n_feature_dirs_created(self, tmp_path):
        plan_dir = self._make_system_plan(tmp_path, intents=["a", "b", "c"])
        _run(_base_system_args(plan_dir, "feat-a,feat-b,feat-c"))
        spec_root = plan_dir / "spec"
        dirs = [d for d in spec_root.iterdir() if d.is_dir()]
        assert len(dirs) == 3

    def test_each_feature_dir_has_2_files_and_marker(self, tmp_path):
        """v27.0.0 (audience split): feature dir 4 files -> 2."""
        plan_dir = self._make_system_plan(tmp_path)
        _run(_base_system_args(plan_dir, "feat-a,feat-b"))
        for slug in ("feat-a", "feat-b"):
            feature_dir = plan_dir / "spec" / slug
            for fname in ("technical-spec.md", "functional-spec.md", ".scaffold-complete"):
                assert (feature_dir / fname).is_file(), \
                    f"{fname} missing in {slug}"

    def test_system_no_fcode_in_feature_frontmatter(self, tmp_path):
        plan_dir = self._make_system_plan(tmp_path)
        _run(_base_system_args(plan_dir, "feat-a,feat-b"))
        tech = (plan_dir / "spec" / "feat-a" / "technical-spec.md").read_text()
        assert "fcode:" not in tech

    def test_stdout_json_paths_include_feature_list(self, tmp_path):
        plan_dir = self._make_system_plan(tmp_path)
        result = _run(_base_system_args(plan_dir, "feat-a,feat-b"))
        paths = json.loads(result.stdout)
        assert any("feature-list.md" in p for p in paths)

    def test_existing_feature_list_preserved_without_force(self, tmp_path):
        """Researcher's rich feature-list.md (Step 0a) MUST survive the scaffolder."""
        plan_dir = self._make_system_plan(tmp_path)
        spec_root = plan_dir / "spec"
        _make_feature_list_md(spec_root, ["F001", "F002"])
        original = (spec_root / "feature-list.md").read_text()
        result = _run(_base_system_args(plan_dir, "feat-a,feat-b"))
        assert result.returncode == 0, result.stderr
        assert (spec_root / "feature-list.md").read_text() == original
        # A preserved file is not a created path
        paths = json.loads(result.stdout)
        assert not any("feature-list.md" in p for p in paths)

    def test_existing_feature_list_overwritten_with_force(self, tmp_path):
        plan_dir = self._make_system_plan(tmp_path)
        spec_root = plan_dir / "spec"
        _make_feature_list_md(spec_root, ["F001", "F002"])
        _run(_base_system_args(plan_dir, "feat-a,feat-b") + ["--force"])
        # Stub has no | F### | rows
        assert "| F001 |" not in (spec_root / "feature-list.md").read_text()

    def test_empty_feature_names_exits_1(self, tmp_path):
        plan_dir = self._make_system_plan(tmp_path)
        result = _run(_base_system_args(plan_dir, ", ,"))
        assert result.returncode == 1
        assert "no non-empty names" in result.stderr


# ---------------------------------------------------------------------------
# MED-2: non-Latin feature names
# ---------------------------------------------------------------------------

class TestNonLatinSlug:
    def _make_system_plan(self, tmp_path: Path) -> Path:
        return _make_plan_dir(tmp_path, mode="system", intents=["feat-a", "feat-b"])

    def test_accented_latin_folds_to_ascii(self, tmp_path):
        """VI/diacritic names transliterate instead of dropping accents silently."""
        plan_dir = self._make_system_plan(tmp_path)
        result = _run(_base_system_args(plan_dir, "Café,Nâng cấp hồ sơ"))
        assert result.returncode == 0, result.stderr
        spec_root = plan_dir / "spec"
        assert (spec_root / "cafe").is_dir()
        assert (spec_root / "nang-cap-ho-so").is_dir()

    def test_pure_cjk_name_targeted_error(self, tmp_path):
        """A name with no ASCII representation fails loudly with a targeted,
        non-blaming message pointing to --slug — not 'not valid kebab-case'."""
        plan_dir = self._make_system_plan(tmp_path)
        result = _run(_base_system_args(plan_dir, "日本語機能,feat-b"))
        assert result.returncode == 1
        assert "no ASCII representation" in result.stderr
        assert "--slug" in result.stderr


# ---------------------------------------------------------------------------
# RT-4: partial-write recovery
# ---------------------------------------------------------------------------

class TestPartialWriteRecovery:
    def test_missing_file_and_marker_rescaffolds(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        feature_dir = plan_dir / "spec" / "my-feature"
        # Delete one spec file AND the marker to simulate partial write
        (feature_dir / "functional-spec.md").unlink()
        (feature_dir / ".scaffold-complete").unlink()
        # Re-run — should re-scaffold missing file
        result = _run(_base_single_args(plan_dir))
        assert result.returncode == 0
        assert (feature_dir / "functional-spec.md").is_file()
        assert (feature_dir / ".scaffold-complete").is_file()

    def test_complete_run_rerun_is_noop(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        feature_dir = plan_dir / "spec" / "my-feature"
        tech = feature_dir / "technical-spec.md"
        content_before = tech.read_text()
        # Re-run without --force (marker present)
        _run(_base_single_args(plan_dir))
        assert tech.read_text() == content_before

    def test_force_overwrites(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        tech = plan_dir / "spec" / "my-feature" / "technical-spec.md"
        tech.write_text("# mutated\n", encoding="utf-8")
        _run(_base_single_args(plan_dir) + ["--force"])
        assert "# mutated" not in tech.read_text()


# ---------------------------------------------------------------------------
# RT-9: slug collision and over-length
# ---------------------------------------------------------------------------

class TestSlugValidation:
    def test_system_slug_collision_exits_1(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="system", intents=["a", "b"])
        # "User Profile" and "user profile" both kebab to "user-profile"
        result = _run(_base_system_args(plan_dir, "User Profile,user profile"))
        assert result.returncode == 1
        assert "collision" in result.stderr.lower()

    def test_system_over64_char_slug_exits_1(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="system", intents=["a", "b"])
        long_name = "a" * 70
        result = _run(_base_system_args(plan_dir, f"{long_name},feat-b"))
        assert result.returncode == 1

    def test_single_over64_char_slug_exits_1(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        long_slug = "a" * 65
        result = _run(_base_single_args(plan_dir, slug=long_slug))
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# RT-3: path traversal rejection
# ---------------------------------------------------------------------------

class TestPathTraversal:
    def test_slug_with_dotdot_rejected(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["escape"])
        result = _run([
            "--plan-dir", str(plan_dir),
            "--mode", "single",
            "--lang", "en",
            "--slug", "../escape",
        ])
        assert result.returncode != 0
        # No files created outside spec dir
        assert not (plan_dir / "escape").exists()

    def test_plan_dir_with_dotdot_rejected(self, tmp_path):
        result = _run([
            "--plan-dir", "../../x",
            "--mode", "single",
            "--lang", "en",
            "--slug", "feat",
        ])
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# KEY acceptance: scaffolded dir passes validate_feature_spec.py
# ---------------------------------------------------------------------------

class TestValidatorAcceptance:
    # rebuild-spec 27.7.0 (action-thread reshape, phase 10): a fresh, thread-shaped
    # scaffold now passes the validator with ZERO criticals — no allowlist.
    #
    # The two PRE-EXISTING critical checks that used to fire here
    # (`FeatureSpec.required_sections`, `FeatureSpec.mapping_table_missing`) were both
    # keyed on the OLD, layer-first `REQUIRED_H2_TECH` shape (phase 04/preflight C9+C15).
    # Phase 10 repointed `required_sections` at `REQUIRED_H2_TECH_THREAD` (accepting
    # either the current thread shape or the legacy 5-bucket shape — see
    # validate_feature_spec.py's own note) and retired `mapping_table_missing` outright
    # (`FeatureSpec.action_index_missing` is its successor, shipped in phase 02). A
    # correctly thread-shaped scaffold now satisfies both.
    #
    # `capability_buckets_missing` (re-homed to `## 3. Actions` in phase 03c) does NOT
    # fire here because scaffold_spec.py's own `### 3.1 CAP-01 — {label}` placeholder
    # already carries the required `CAP-NN` token (see scaffold_spec.py's own comment
    # next to that line) — see `test_scaffolded_single_has_no_action_thread_critical`
    # below for the full accounting of what phases 02/03 own.
    def test_scaffolded_single_passes_validator_no_critical(self, tmp_path):
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        feature_dir = plan_dir / "spec" / "my-feature"
        vresult = _run_validator(feature_dir)
        data = json.loads(vresult.stdout)
        criticals = [
            i for s in data.get("specs", {}).values()
            for i in s.get("issues", [])
            if i["severity"] == "critical"
        ]
        assert criticals == [], f"fresh scaffold must validate with zero criticals: {criticals}"

    def test_scaffolded_single_has_no_action_thread_critical(self, tmp_path):
        """The actual phase 04 merge blocker: every rule_id phases 02/03 own
        (action_*/rung_*/rule_bin_misplaced/crosscutting_unlabelled/diagram_*/dec_*)
        must be silent on a fresh scaffold — proven directly, not merely inferred from
        the allowlist above being exactly 2 items."""
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        feature_dir = plan_dir / "spec" / "my-feature"
        vresult = _run_validator(feature_dir)
        data = json.loads(vresult.stdout)
        issues = [i for s in data.get("specs", {}).values() for i in s.get("issues", [])]
        action_thread_owned_prefixes = (
            "FeatureSpec.action_", "FeatureSpec.rung_", "FeatureSpec.rule_bin_",
            "FeatureSpec.crosscutting_", "FeatureSpec.diagram_", "FeatureSpec.dec_",
        )
        offenders = [
            i for i in issues
            if i["rule_id"].startswith(action_thread_owned_prefixes)
        ]
        assert offenders == [], f"phase 02/03-owned findings on a fresh scaffold: {offenders}"

    def test_edge_cases_passes_no_warning(self, tmp_path):
        """v27.0.0: functional-spec.md § 9 Edge Cases' 3-row skeleton must produce no
        func.edge_cases_few_rows warning (retired edge_cases.few_rows renamed)."""
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        feature_dir = plan_dir / "spec" / "my-feature"
        vresult = _run_validator(feature_dir)
        data = json.loads(vresult.stdout)
        issues = [
            i for s in data.get("specs", {}).values()
            for i in s.get("issues", [])
            if i.get("rule_id") == "func.edge_cases_few_rows"
        ]
        assert issues == [], f"func.edge_cases_few_rows warning fired: {issues}"


# ---------------------------------------------------------------------------
# RT-14: SYSTEM folder-count machine check
# ---------------------------------------------------------------------------

def _make_feature_list_md(spec_root: Path, feature_codes: list[str]) -> None:
    """Write a minimal feature-list.md with one | F### | row per code."""
    lines = [
        "---",
        "status: draft",
        "authored_by: takumi",
        "created: 2026-01-01",
        "---",
        "",
        "| Code | Name | Type | Language | Workspace | Priority |",
        "| ---- | ---- | ---- | -------- | --------- | -------- |",
    ]
    for code in feature_codes:
        lines.append(f"| {code} | Feature | new | en | default | high |")
    (spec_root / "feature-list.md").write_text("\n".join(lines), encoding="utf-8")


def _make_scaffolded_dir(spec_root: Path, name: str) -> Path:
    """Create a feature dir carrying the `.scaffold-complete` marker the scaffolder
    writes last — this is what check_folder_count counts. [H1]"""
    d = spec_root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / ".scaffold-complete").write_text("", encoding="utf-8")
    return d


def _run_check_folder_count(plan_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT),
         "--plan-dir", str(plan_dir),
         "--mode", "system",
         "--lang", "en",
         "--check-folder-count"],
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestFolderCount:
    def test_match_exits_0(self, tmp_path):
        plan_dir = tmp_path / "plan"
        spec_root = plan_dir / "spec"
        spec_root.mkdir(parents=True)
        _make_feature_list_md(spec_root, ["F001", "F002"])
        # Create 2 scaffolded feature dirs to match
        _make_scaffolded_dir(spec_root, "feat-a")
        _make_scaffolded_dir(spec_root, "feat-b")
        result = _run_check_folder_count(plan_dir)
        assert result.returncode == 0
        assert "OK" in result.stdout
        assert "2" in result.stdout

    def test_mismatch_exits_1(self, tmp_path):
        plan_dir = tmp_path / "plan"
        spec_root = plan_dir / "spec"
        spec_root.mkdir(parents=True)
        _make_feature_list_md(spec_root, ["F001", "F002", "F003"])
        # Only 2 scaffolded dirs, 3 rows in feature-list
        _make_scaffolded_dir(spec_root, "feat-a")
        _make_scaffolded_dir(spec_root, "feat-b")
        result = _run_check_folder_count(plan_dir)
        assert result.returncode == 1
        assert "MISMATCH" in result.stderr

    def test_missing_feature_list_exits_2(self, tmp_path):
        plan_dir = tmp_path / "plan"
        (plan_dir / "spec").mkdir(parents=True)
        # No feature-list.md written
        result = _run_check_folder_count(plan_dir)
        assert result.returncode == 2

    def test_no_files_created(self, tmp_path):
        """--check-folder-count must not create any files."""
        plan_dir = tmp_path / "plan"
        spec_root = plan_dir / "spec"
        spec_root.mkdir(parents=True)
        _make_feature_list_md(spec_root, ["F001"])
        _make_scaffolded_dir(spec_root, "feat-a")
        files_before = set(spec_root.rglob("*"))
        _run_check_folder_count(plan_dir)
        files_after = set(spec_root.rglob("*"))
        assert files_before == files_after, "check-folder-count must not create files"

    def test_after_system_scaffold_match(self, tmp_path):
        """After a SYSTEM scaffold, folder count matches feature-list rows."""
        plan_dir = _make_plan_dir(
            tmp_path, mode="system",
            intents=["feat-a", "feat-b"],
        )
        # Scaffold creates feature-list.md stub + 2 feature dirs
        scaffold_result = _run(_base_system_args(plan_dir, "feat-a,feat-b"))
        assert scaffold_result.returncode == 0, scaffold_result.stderr
        # But scaffold's feature-list.md stub has no | F### | rows — replace with real one
        spec_root = plan_dir / "spec"
        _make_feature_list_md(spec_root, ["F001", "F002"])
        result = _run_check_folder_count(plan_dir)
        assert result.returncode == 0, result.stderr

    def test_stray_non_feature_dir_ignored(self, tmp_path):
        """[H1/T1] Stray dirs (research/, flows/, .review-archive/) lack the
        `.scaffold-complete` marker and MUST NOT inflate the count → no false
        MISMATCH. 2 scaffolded dirs + 3 stray dirs vs 2 rows → still OK exit 0."""
        plan_dir = tmp_path / "plan"
        spec_root = plan_dir / "spec"
        spec_root.mkdir(parents=True)
        _make_feature_list_md(spec_root, ["F001", "F002"])
        _make_scaffolded_dir(spec_root, "feat-a")
        _make_scaffolded_dir(spec_root, "feat-b")
        # Stray non-feature dirs that previously inflated the count
        (spec_root / "research").mkdir()
        (spec_root / "flows").mkdir()
        (spec_root / ".review-archive").mkdir()
        result = _run_check_folder_count(plan_dir)
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout
        assert "2" in result.stdout


class TestScaffoldConfidenceInterplay:
    def test_fresh_draft_yields_zero_claims_null_confidence(self, tmp_path):
        """v26.0.0 rework regression: a freshly scaffolded technical-spec contains ONLY
        placeholder/instructional text, so derive_confidence_report must see 0 claims and
        confidence_derived null — never fake △ rows from B4's own guidance tokens."""
        from derive_confidence_report import compute_stats, extract_claims
        plan_dir = _make_plan_dir(tmp_path, mode="single", intents=["my-feature"])
        _run(_base_single_args(plan_dir))
        tech = (plan_dir / "spec" / "my-feature" / "technical-spec.md").read_text()
        claims = extract_claims(tech)
        total, with_evidence, cd = compute_stats(claims)
        assert claims == [], claims
        assert (total, with_evidence, cd) == (0, 0, None)
