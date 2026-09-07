"""Phase 08 (self-sufficiency v27.8) — `FeatureSpec.retired_section_present`,
wired into `validate_feature_spec._check_technical_spec` directly (no bespoke
`would_fire` helper, D7) — the deletion-direction twin of C1.

A3 (`## Source Walkthrough`) and B4 (`## DB Impact per Event`) retired from
technical-spec.md this release; this check fires (warning) when either heading
is still present, feeding `_action_thread_reopen_lib.REOPEN_RULE_IDS` so
`compose_action_thread`'s one-shot strip (`test_doc_migration_action_thread_
step.py::TestRetiredSectionStripReopen`, `test_action_thread_composer.py`) has
something to reopen. This file only proves the DETECTOR; the STRIP is proven
elsewhere (D7: firing and remediation are two different concerns, never one
re-implemented predicate).

Same pattern as `test_action_ref_unglossed.py`: every test calls
`vfs._check_technical_spec` directly against a hand-built technical-spec.md,
scoped to this check's own rule_id.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import validate_feature_spec as vfs  # noqa: E402

_RULE_ID = "FeatureSpec.retired_section_present"


def _matching(issues: list[dict]) -> list[dict]:
    return [i for i in issues if i["rule_id"] == _RULE_ID]


# ---------------------------------------------------------------------------
# Clean, action-thread-shaped baseline — carries neither retired heading.
# ---------------------------------------------------------------------------

_GOOD_SPEC = """\
# F906_Test — Retired Section Present Test

## 1. Technical Overview

Overview text.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-601 | — | § 4.4 |
| **A1** | `WidgetsController#index` | `GET` `.../widgets` | FR-101 | — *(read-only)* | § 3.1 |

## 3. Actions

### 3.1 CAP-01 — Manage widgets

#### A1 · List widgets

`GET .../widgets` → `WidgetsController#index`
`FR-101`

**Who** · Anyone
**Result** · read-only — **no DB write**.
**Source:** `widgets_controller.rb:5-10`

## 4. Shared Foundation

### 4.1 Components

None.

### 4.2 Data Model

None.

### 4.3 State Management

None.

### 4.4 Shared Rules

None.

### 4.5 Algorithms & Integrations

None.

### 4.6 Configuration

None.

## 5. Verification & Technical Notes

### 5.1 Technical Verification

None.

### 5.2 Assumptions

None.

### 5.3 Unresolved Questions

None.

### 5.4 Source References

**Source:** `widgets_controller.rb:5-10`

### 5.5 Artifact References

None.
"""

_A3_BLOCK = (
    "\n\n## Source Walkthrough\n\n"
    "1. **File:** `app/controllers/widgets_controller.rb:1-10` — start here.\n"
)
_B4_BLOCK = (
    "\n\n## DB Impact per Event\n\n"
    "N/A — read-only feature, no DB writes.\n"
)


def _write_spec(tmp_path: Path, text: str, feature: str = "F906_Test") -> Path:
    feat_dir = tmp_path / "docs" / "features" / feature
    feat_dir.mkdir(parents=True)
    spec = feat_dir / "technical-spec.md"
    spec.write_text(text, encoding="utf-8")
    return spec


class TestBaselineIsCleanForRetiredSectionPresent:
    def test_good_fixture_fires_no_retired_section_code(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _matching(issues) == [], issues


# ---------------------------------------------------------------------------
# Firing tests — one per heading, and both together.
# ---------------------------------------------------------------------------

class TestRetiredSectionPresentFires:
    def test_a3_alone_fires_once_as_warning(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_SPEC + _A3_BLOCK, feature="F907_Test")
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = _matching(issues)
        assert len(matching) == 1, issues
        assert matching[0]["severity"] == "warning"
        assert "Source Walkthrough" in matching[0]["message"]

    def test_b4_alone_fires_once_as_warning(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_SPEC + _B4_BLOCK, feature="F908_Test")
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = _matching(issues)
        assert len(matching) == 1, issues
        assert matching[0]["severity"] == "warning"
        assert "DB Impact per Event" in matching[0]["message"]

    def test_both_present_fire_twice_one_per_heading(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_SPEC + _A3_BLOCK + _B4_BLOCK, feature="F909_Test")
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = _matching(issues)
        assert len(matching) == 2, issues
        messages = " ".join(i["message"] for i in matching)
        assert "Source Walkthrough" in messages
        assert "DB Impact per Event" in messages

    def test_message_names_the_remediation_command(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_SPEC + _A3_BLOCK, feature="F910_Test")
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = _matching(issues)
        assert matching, issues
        assert "--migrate --only action-thread" in matching[0]["message"]


# ---------------------------------------------------------------------------
# Fires regardless of shape ("no transition window", mirrors
# `legacy_artifact_sections`) — proven against a pre-SOT (old 9-section) shape,
# not just the action-thread shape above.
# ---------------------------------------------------------------------------

_PRE_SOT_SPEC = """\
# F911_Test — Retired Section Present Pre-SOT Test

## Overview

Some overview text.

## Cross-Cutting Logic

### Requirements

- **FR-001** Some requirement.

## Source Walkthrough

1. **File:** `app/models/widget.rb:1-5` — start here.

## DB Impact per Event

N/A — read-only feature, no DB writes.
"""


class TestFiresRegardlessOfShape:
    def test_fires_on_the_old_pre_sot_nine_section_shape_too(self, tmp_path):
        spec = _write_spec(tmp_path, _PRE_SOT_SPEC, feature="F911_Test")
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = _matching(issues)
        assert len(matching) == 2, issues
        # The pre-SOT degradation window also fires (its own, unrelated warning) —
        # proving retired_section_present is NOT muted by that early return, the
        # same "no transition window" property `legacy_artifact_sections` has.
        assert "FeatureSpec.tech_sections_pre_sot" in [i["rule_id"] for i in issues]

    def test_silent_on_the_pre_sot_shape_when_neither_heading_present(self, tmp_path):
        clean_pre_sot = _PRE_SOT_SPEC.replace(
            "## Source Walkthrough\n\n"
            "1. **File:** `app/models/widget.rb:1-5` — start here.\n\n"
            "## DB Impact per Event\n\n"
            "N/A — read-only feature, no DB writes.\n",
            "",
        )
        spec = _write_spec(tmp_path, clean_pre_sot, feature="F912_Test")
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _matching(issues) == [], issues
