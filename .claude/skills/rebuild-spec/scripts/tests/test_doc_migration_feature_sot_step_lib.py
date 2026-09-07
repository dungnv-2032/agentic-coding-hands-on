"""Tests for `_doc_migration_feature_sot_step_lib.py` -- the `feature-sot` registry
step (phase-10, plans/260818-1332-rebuild-spec-human-readable-sot). Isolated from the
CLI (`run_doc_migrations.py`'s own suite covers `--only feature-sot`, prerequisite
refusal, and the `_TECH_SPEC_STEPS` membership) -- this file exercises `count_pending`/
`run` directly against `tmp_path` fixtures, plus the write-both-or-neither
transaction guarantee via a simulated mid-write failure.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _doc_migration_feature_sot_step_lib as lib  # noqa: E402
from _audience_split_tally_lib import ALREADY, FAILED, PROGRESS  # noqa: E402

OLD_FUNC = """---
authored_by: rebuild-spec
---
# F001_Sample

## 1. Overview

**Problem:** p.
**Solution:** s.

## 2. Open Decisions

None.

## 3. Requirements

- **FR-001** req.

## 4. Business Rules

- rule. (BR-001)

## 5. Screens

N/A.

## 6. User Stories

### US001_Story — Story (Priority: P1)

Narrative.

## 7. Scenarios

Given a, When b, Then c.

## 8. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| X | Y | "Z." |

## 9. Edge Behaviours to Verify

Verified.

## 10. Configuration

None.
"""

OLD_TECH = """---
authored_by: rebuild-spec
---
# F001_Sample — Technical Spec

## Overview

Overview text.

## Polymorphic Behavior

N/A.

## Cross-Cutting Logic

### Requirements

| Code | Description | Endpoint/Handler | Verifiable |
|------|-------------|------------------|------------|
| FR-001 | req | `POST /x` via `XController#create` | yes |

### Business Rules

None.

### Decision Logic

None.

### State Machines

None.

### Algorithms

None.

### External Integrations

None.

### Verification

- **SC-001** — check.

## User Stories

### US001_Story — Story (Priority: P1)

**What happens:** it happens.

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| X | Y |

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| X | `xs` | id | p |

## Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| Feature List | [feature-list.md](../../feature-list.md) | F001 | [x] |

## Assumptions

- a.

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| X | `x.rb:1` | p |

## Unresolved Questions

1. **T**: q.

## Source Walkthrough

1. **File:** `x.rb:1` — start.

## DB Impact per Event

| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |
|---|---|---|---|---|---|
| POST /x | `xs` | id | INSERT | literal | `x.rb:1` |
"""


def _make_feature_dir(docs_root: Path, name: str, func_text: str = OLD_FUNC,
                       tech_text: str | None = OLD_TECH) -> Path:
    feature_dir = docs_root / "features" / name
    feature_dir.mkdir(parents=True)
    (feature_dir / "functional-spec.md").write_text(func_text, encoding="utf-8")
    if tech_text is not None:
        (feature_dir / "technical-spec.md").write_text(tech_text, encoding="utf-8")
    return feature_dir


def test_count_pending_counts_a_not_yet_composed_pair(tmp_path):
    docs_root = tmp_path / "docs"
    _make_feature_dir(docs_root, "F001_Sample")
    assert lib.count_pending(docs_root, tmp_path, None) == 1


def test_count_pending_zero_once_both_files_are_sot_shaped(tmp_path):
    docs_root = tmp_path / "docs"
    _make_feature_dir(docs_root, "F001_Sample")
    lib.run(docs_root, tmp_path, None)
    assert lib.count_pending(docs_root, tmp_path, None) == 0


def test_features_filter_scopes_to_named_feature_dirs(tmp_path):
    docs_root = tmp_path / "docs"
    _make_feature_dir(docs_root, "F001_Sample")
    _make_feature_dir(docs_root, "F002_Other")
    assert lib.count_pending(docs_root, tmp_path, frozenset({"F001_Sample"})) == 1
    assert lib.count_pending(docs_root, tmp_path, frozenset({"F999_NoSuchFeature"})) == 0


def test_run_composes_both_files_and_reports_progress(tmp_path):
    docs_root = tmp_path / "docs"
    feature_dir = _make_feature_dir(docs_root, "F001_Sample")
    result = lib.run(docs_root, tmp_path, None)
    assert result.category == PROGRESS
    assert result.needs_llm_fill is True
    func_text = (feature_dir / "functional-spec.md").read_text(encoding="utf-8")
    tech_text = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")
    assert "## 2. Functional Capabilities" in func_text
    assert "## 2. Functional → Technical Mapping" in tech_text


def test_run_second_time_reports_already_and_writes_nothing(tmp_path):
    docs_root = tmp_path / "docs"
    feature_dir = _make_feature_dir(docs_root, "F001_Sample")
    lib.run(docs_root, tmp_path, None)
    before_func = (feature_dir / "functional-spec.md").read_bytes()
    before_tech = (feature_dir / "technical-spec.md").read_bytes()

    result = lib.run(docs_root, tmp_path, None)

    assert result.category == ALREADY
    assert (feature_dir / "functional-spec.md").read_bytes() == before_func
    assert (feature_dir / "technical-spec.md").read_bytes() == before_tech


def test_run_reports_failed_for_functional_spec_with_no_sibling_technical_spec(tmp_path):
    docs_root = tmp_path / "docs"
    _make_feature_dir(docs_root, "F002_Broken", tech_text=None)
    result = lib.run(docs_root, tmp_path, None)
    assert result.category == FAILED
    assert "F002_Broken" in result.message


def test_run_isolates_a_broken_feature_dir_and_still_composes_the_rest(tmp_path):
    docs_root = tmp_path / "docs"
    _make_feature_dir(docs_root, "F001_Sample")
    _make_feature_dir(docs_root, "F002_Broken", tech_text=None)

    result = lib.run(docs_root, tmp_path, None)

    assert result.category == FAILED
    assert "1 composed before" in result.message
    good_func = (docs_root / "features" / "F001_Sample" / "functional-spec.md").read_text(
        encoding="utf-8"
    )
    assert "## 2. Functional Capabilities" in good_func


# --------------------------------------------------------------------------- #
# Write-both-or-neither transaction guarantee
# --------------------------------------------------------------------------- #
def test_atomic_write_pair_writes_both_files(tmp_path):
    path_a = tmp_path / "a.md"
    path_b = tmp_path / "b.md"
    path_a.write_text("old a", encoding="utf-8")
    path_b.write_text("old b", encoding="utf-8")

    lib._atomic_write_pair(path_a, "new a", path_b, "new b")

    assert path_a.read_text(encoding="utf-8") == "new a"
    assert path_b.read_text(encoding="utf-8") == "new b"


def test_atomic_write_pair_leaves_neither_file_touched_on_a_simulated_second_write_failure(
    tmp_path, monkeypatch,
):
    """Simulates a failure writing the SECOND file's temp file (disk full, etc.) --
    the FIRST file's temp write already succeeded but neither real file must be
    replaced (phase-10 Requirements: "write both or neither, per feature dir")."""
    path_a = tmp_path / "a.md"
    path_b = tmp_path / "b.md"
    path_a.write_text("old a", encoding="utf-8")
    path_b.write_text("old b", encoding="utf-8")

    real_mkstemp = lib.tempfile.mkstemp
    calls = {"n": 0}

    def _flaky_mkstemp(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("simulated disk-full on the 2nd temp file")
        return real_mkstemp(*args, **kwargs)

    monkeypatch.setattr(lib.tempfile, "mkstemp", _flaky_mkstemp)

    with __import__("pytest").raises(OSError):
        lib._atomic_write_pair(path_a, "new a", path_b, "new b")

    assert path_a.read_text(encoding="utf-8") == "old a", "first file must stay untouched"
    assert path_b.read_text(encoding="utf-8") == "old b", "second file must stay untouched"
    # no leftover .tmp files from the aborted first write
    assert list(tmp_path.glob("*.tmp")) == []


def test_atomic_write_pair_cleans_up_tmp_b_when_the_second_replace_raises(tmp_path, monkeypatch):
    """M1 (reviewer-260819-0858-inspection.md): the two `os.replace` calls are
    independent syscalls, not one shared transaction -- `path_a`'s rename can
    succeed while `path_b`'s then raises (cross-device rename, a permission change
    mid-run, disk full exactly between the two calls). Pre-fix, that second
    `os.replace` call has no `try`/`except` around it at all, so `tmp_b`'s now-
    orphaned temp file is never cleaned up. Reaches that exact branch: both
    mkstemp calls and both temp writes succeed, the FIRST `os.replace` succeeds
    (real rename, not simulated), and `os.replace` is made to raise ONLY on its
    second invocation (the `tmp_b -> path_b` rename)."""
    path_a = tmp_path / "a.md"
    path_b = tmp_path / "b.md"
    path_a.write_text("old a", encoding="utf-8")
    path_b.write_text("old b", encoding="utf-8")

    real_replace = lib.os.replace
    calls = {"n": 0}

    def _flaky_replace(src, dst):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("simulated failure renaming the second file")
        return real_replace(src, dst)

    monkeypatch.setattr(lib.os, "replace", _flaky_replace)

    with __import__("pytest").raises(OSError):
        lib._atomic_write_pair(path_a, "new a", path_b, "new b")

    assert path_a.read_text(encoding="utf-8") == "new a", "first file's rename already succeeded"
    assert path_b.read_text(encoding="utf-8") == "old b", "second file's rename failed, untouched"
    # the orphaned tmp_b temp file must not be left behind on disk forever
    assert list(tmp_path.glob("*.tmp")) == []


def test_run_leaves_originals_untouched_when_the_second_write_fails(tmp_path, monkeypatch):
    """End-to-end version of the same guarantee through `run()` itself: a write
    failure on the pair must not leave a renumbered functional-spec.md behind."""
    docs_root = tmp_path / "docs"
    feature_dir = _make_feature_dir(docs_root, "F001_Sample")
    before_func = (feature_dir / "functional-spec.md").read_bytes()
    before_tech = (feature_dir / "technical-spec.md").read_bytes()

    def _always_fail(*_a, **_k):
        raise OSError("simulated failure")

    monkeypatch.setattr(lib, "_atomic_write_pair", _always_fail)

    result = lib.run(docs_root, tmp_path, None)

    assert result.category == FAILED
    assert (feature_dir / "functional-spec.md").read_bytes() == before_func
    assert (feature_dir / "technical-spec.md").read_bytes() == before_tech
