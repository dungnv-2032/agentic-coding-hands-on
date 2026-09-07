"""Regression tests for the silent Mode B re-fold bug (found while fixing the adjacent
SHAPE_V27_HYBRID gap that `test_audience_split_hybrid_shape.py` covers for Mode A).

`migrate_business_rules()` guarded re-entry ONLY on `has_feature_sentinel()` -- the
per-unit sentinel under `docs/.migrate-v27/`. It never checked whether the fold had
already landed in the LIVE `behavior-logic.md`. If that dot-directory is lost (a
realistic loss: it is a dot-directory under `docs/` a consumer may gitignore or clean),
a second run re-parses `business-rules.md` (never deleted -- Mode B's delete gate is
`--reviewed`-only) and APPENDS a second `## Business Rules (folded from...)` section --
cumulative, exit 0, sentinel WRITTEN, nothing warns. This file proves the fix makes
re-entry depend on the ARTIFACT (the fold marker actually present in the live file),
never on the sentinel alone, mirroring the fix `test_audience_split_hybrid_shape.py`
already proved for Mode A's SHAPE_V27_HYBRID path.

Also covers Mode C (`migrate_screen`): empirically, its existing `"## Screen Layout"
not in old_text` guard is ALREADY artifact-derived (content-based, not sentinel-based)
-- the reorder unwraps and removes that heading, so a second run over already-reordered
content takes the `confirmed-v27` branch regardless of sentinel state. The tests here
prove that empirically (run, wipe staging, re-run, byte-diff) rather than assuming it.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _audience_split_migrate_lib as mig_lib  # noqa: E402
import _audience_split_mode_b_lib as mode_b_lib  # noqa: E402
import _audience_split_orchestrate_bc_lib as orchestrate_bc_lib  # noqa: E402
import _audience_split_tally_lib as tally_lib  # noqa: E402


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


def _write_business_rules_corpus(docs_root: Path) -> None:
    """Same shape as `test_integration_mode_b_fold_retains_bl_codes` in
    `test_migrate_feature_audience_split.py` -- a real business-rules.md that parses to
    one rule block, plus a behavior-logic.md carrying two BL### fragments the fold must
    never drop."""
    (docs_root / "system").mkdir(parents=True, exist_ok=True)
    (docs_root / "generated").mkdir(parents=True, exist_ok=True)
    (docs_root / "system" / "business-rules.md").write_text(
        _fm("authored_by: rebuild-spec") + (
            "# Business Rules\n\n### Password Complexity\n"
            "**Applies when:** a user sets or changes their password\n"
            "**Says:** the system requires at least 8 characters\n"
            "**Source artifact:** [architecture.md](../../docs/system/architecture.md)\n"
        ),
        encoding="utf-8",
    )
    bl_text = (
        "## Behavior Logic Index\n\ntable\n\n## Dev Appendix\n\n### Cardinality Contract\n\n"
        "rules\n\n## BL001: SendWelcomeMail\n\n**Type**: mail\n"
        "**Source File**: app/Mail/WelcomeMail.php\n**Source Symbol**: WelcomeMail\n\n"
        "## BL002: AuditLog\n\n**Type**: observer\n"
        "**Source File**: app/Observers/AuditObserver.php\n"
        "**Source Symbol**: AuditObserver::created\n"
    )
    (docs_root / "generated" / "behavior-logic.md").write_text(bl_text, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Mode B -- the actual reproduction: fold once, lose the staging dir, fold again.
# --------------------------------------------------------------------------- #
def test_mode_b_second_fold_after_staging_loss_is_byte_identical_not_duplicated(tmp_path):
    docs_root = tmp_path / "docs"
    _write_business_rules_corpus(docs_root)
    bl_path = docs_root / "generated" / "behavior-logic.md"
    _init_git_repo(tmp_path)
    _commit_all(tmp_path)

    before_text = bl_path.read_text(encoding="utf-8")
    assert before_text.count(mode_b_lib.FOLD_H2_HEADING) == 0

    first = orchestrate_bc_lib.migrate_business_rules(docs_root, tmp_path)
    assert first.exit_ok, first.message
    assert first.action == "migrated"

    after_first_text = bl_path.read_text(encoding="utf-8")
    assert after_first_text.count(mode_b_lib.FOLD_H2_HEADING) == 1

    # Simulate the realistic loss: docs/.migrate-v27/ (sentinel + backups) is gone
    # entirely -- e.g. a consumer's .gitignore/clean wiped the dot-directory.
    shutil.rmtree(mig_lib.staging_root(docs_root))
    assert not mig_lib.has_feature_sentinel(
        mig_lib.staging_unit_dir(docs_root, "system", "business-rules")
    )

    second = orchestrate_bc_lib.migrate_business_rules(docs_root, tmp_path)
    assert second.exit_ok, second.message
    # Assert on the CATEGORY (ALREADY), not merely the literal action string -- an
    # action-string-only assertion is exactly what would have missed this class of bug.
    assert tally_lib.categorize(second.action) == tally_lib.ALREADY

    after_second_text = bl_path.read_text(encoding="utf-8")
    # The artifact proof: exactly one fold section, byte-identical to after run 1.
    assert after_second_text.count(mode_b_lib.FOLD_H2_HEADING) == 1
    assert after_second_text == after_first_text


def test_mode_b_third_run_after_repeated_staging_loss_stays_stable(tmp_path):
    """Cumulative-duplication guard: the original bug appends a NEW copy on every run
    with no sentinel present. Prove a third run is just as stable as the second."""
    docs_root = tmp_path / "docs"
    _write_business_rules_corpus(docs_root)
    bl_path = docs_root / "generated" / "behavior-logic.md"
    _init_git_repo(tmp_path)
    _commit_all(tmp_path)

    orchestrate_bc_lib.migrate_business_rules(docs_root, tmp_path)
    after_first = bl_path.read_text(encoding="utf-8")
    shutil.rmtree(mig_lib.staging_root(docs_root))

    orchestrate_bc_lib.migrate_business_rules(docs_root, tmp_path)
    shutil.rmtree(mig_lib.staging_root(docs_root))

    third = orchestrate_bc_lib.migrate_business_rules(docs_root, tmp_path)
    after_third = bl_path.read_text(encoding="utf-8")

    assert tally_lib.categorize(third.action) == tally_lib.ALREADY
    assert after_third.count(mode_b_lib.FOLD_H2_HEADING) == 1
    assert after_third == after_first


def test_mode_b_marker_detected_path_rewrites_sentinel_for_cheap_resume(tmp_path):
    """Correctness must not DEPEND on the sentinel, but a subsequent run should still be
    cheap -- the marker-detected no-op path re-writes the per-unit sentinel."""
    docs_root = tmp_path / "docs"
    _write_business_rules_corpus(docs_root)
    unit_dir = mig_lib.staging_unit_dir(docs_root, "system", "business-rules")
    _init_git_repo(tmp_path)
    _commit_all(tmp_path)

    orchestrate_bc_lib.migrate_business_rules(docs_root, tmp_path)
    shutil.rmtree(mig_lib.staging_root(docs_root))
    assert not mig_lib.has_feature_sentinel(unit_dir)

    outcome = orchestrate_bc_lib.migrate_business_rules(docs_root, tmp_path)
    assert outcome.exit_ok
    assert mig_lib.has_feature_sentinel(unit_dir)


def test_mode_b_absent_business_rules_still_noop(tmp_path):
    """Regression guard: the pre-existing 'business-rules.md absent' no-op path (a repo
    that never had the file, or a --reviewed run that already deleted it) must be
    unaffected by the new artifact check."""
    docs_root = tmp_path / "docs"
    (docs_root / "generated").mkdir(parents=True)
    (docs_root / "generated" / "behavior-logic.md").write_text("## BL001: X\n", encoding="utf-8")

    outcome = orchestrate_bc_lib.migrate_business_rules(docs_root, tmp_path)
    assert outcome.action == "no-op"
    assert outcome.exit_ok is True
    assert "absent" in outcome.message


def test_mode_b_missing_target_still_skipped_no_target(tmp_path):
    """Regression guard: 'behavior-logic.md not found' must still short-circuit BEFORE
    the new marker check (there is nothing to read a marker from)."""
    docs_root = tmp_path / "docs"
    (docs_root / "system").mkdir(parents=True)
    (docs_root / "system" / "business-rules.md").write_text(
        "# Business Rules\n\n### R\n**Says:** x\n", encoding="utf-8",
    )
    outcome = orchestrate_bc_lib.migrate_business_rules(docs_root, tmp_path)
    assert outcome.action == "skipped-no-target"
    assert outcome.exit_ok is False


# --------------------------------------------------------------------------- #
# Mode C -- empirical idempotency check for migrate_screen() across staging loss.
# --------------------------------------------------------------------------- #
_OLD_SCREEN_SPEC = """---
authored_by: rebuild-spec
---
# SCR001_Login — Screen Spec

**Screen**: SCR001: Login
**Feature**: F001_Auth
**Type**: atomic
**Route**: /login
**Generated**: 2026-01-01

## Purpose

Lets a user sign in.

## Screen Layout

The screen has a header and a centered form (login.vue:1).

### Layout Sketch

```
box
```

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components | Responsive Behavior |
|-----------|------|----------|------------|----------------|---------------------|
| R1 | Header | fixed-top | no | Header | always |

## User Flow

### Happy Path

1. User submits the form.

## Data Inventory

N/A — screen displays no dynamic data (static marketing/error page)

## UI States

N/A — no async ops

## Validation & Error Feedback

N/A

## Interaction Patterns

N/A

## Accessibility

N/A

## Conditional Rendering

N/A

## Component Variants

N/A

## Security Surface

N/A

## Source References

1. Page/View: `login.vue:1`

## Source Walkthrough

1. **File:** `login.vue:1` — start here

### Call Hierarchy

```text
Login -> Form -> Store
```
"""


def test_mode_c_reorder_idempotent_after_staging_loss_byte_identical(tmp_path):
    docs_root = tmp_path / "docs"
    screen_dir = docs_root / "screens" / "SCR001_Login"
    screen_dir.mkdir(parents=True)
    spec_path = screen_dir / "spec.md"
    spec_path.write_text(_OLD_SCREEN_SPEC, encoding="utf-8")
    _init_git_repo(tmp_path)
    _commit_all(tmp_path)

    first = orchestrate_bc_lib.migrate_screen(screen_dir, tmp_path, docs_root)
    assert first.exit_ok, first.message
    assert first.action == "migrated"
    after_first_text = spec_path.read_text(encoding="utf-8")
    assert "## Screen Layout" not in after_first_text

    shutil.rmtree(mig_lib.staging_root(docs_root))
    assert not mig_lib.has_feature_sentinel(
        mig_lib.staging_unit_dir(docs_root, "screens", "SCR001_Login")
    )

    second = orchestrate_bc_lib.migrate_screen(screen_dir, tmp_path, docs_root)
    assert second.exit_ok, second.message
    # migrate_screen's existing content guard ("## Screen Layout" not in old_text) is
    # ALREADY artifact-derived, not sentinel-derived -- prove it empirically: the
    # second run must fall into the confirmed-v27/ALREADY branch, not re-run
    # compose_mode_c, and the live file must come out byte-identical.
    assert second.action == "confirmed-v27"
    assert tally_lib.categorize(second.action) == tally_lib.ALREADY

    after_second_text = spec_path.read_text(encoding="utf-8")
    assert after_second_text == after_first_text
    assert after_second_text.count("### Layout Sketch") == 1
    assert after_second_text.count("### Layout Regions") == 1
