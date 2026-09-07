"""Tests for _flow_sm_lib.py (scan_entity_state_machines — B3 SM/FLOW DRY cross-ref source).

v27.0.0 silent-pass regression guard: SM heading detection must use the CANONICAL trailing-tag
heading form (`### {plain sentence} (SM-001)`, via _spec_block_lib.find_blocks), not the retired
anchored-slug form (`### SM-001_Slug` / `#### SM-001_Slug`). Before the Phase 04 fix, the old local
regex (`^#{3,4}\\s+(SM-\\d{3})[^\\n]*`) matched ONLY the retired form — a technical-spec.md written
entirely in the canonical new form produced ZERO detected SM blocks, so validate_process_flow.py's
sm_crossref_missing warning silently never fired, even when a FLOW### genuinely duplicated an
entity's state machine. These tests use ONLY new-form headings so they fail again immediately if
that regression is reintroduced.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _flow_sm_lib import scan_entity_state_machines  # noqa: E402

NEW_FORM_ENTITY_SM = """\
# F050 — Job Admin

### Job status lifecycle (SM-001)
**kind:** entity
**States:** open, processing, closed

```mermaid
stateDiagram-v2
  [*] --> open
```
"""

NEW_FORM_UI_SM_ONLY = """\
# F060 — Checkout

### Checkout form submission status (SM-002)
**kind:** ui
**States:** idle, submitting, error
"""

NEW_FORM_ENTITY_ONE_STATE = """\
# F070 — Singleton

### Singleton lifecycle (SM-003)
**kind:** entity
**States:** active
"""

LEGACY_FORM_ENTITY_SM = """\
# F080 — Legacy

#### SM-004_Legacy
**kind:** entity
**States:** open, closed
"""


def _write(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


class TestNewFormHeadingDetected:
    def test_entity_kind_new_form_sm_is_detected(self, tmp_path):
        _write(tmp_path, "features/F050_JobAdmin/technical-spec.md", NEW_FORM_ENTITY_SM)
        results = scan_entity_state_machines(tmp_path / "features")
        assert len(results) == 1
        assert results[0]["code"] == "SM-001"
        assert results[0]["feature"] == "F050_JobAdmin"
        assert results[0]["states"] == {"open", "processing", "closed"}

    def test_ui_kind_sm_excluded(self, tmp_path):
        _write(tmp_path, "features/F060_Checkout/technical-spec.md", NEW_FORM_UI_SM_ONLY)
        results = scan_entity_state_machines(tmp_path / "features")
        assert results == []

    def test_entity_kind_with_fewer_than_2_states_excluded(self, tmp_path):
        _write(tmp_path, "features/F070_Singleton/technical-spec.md", NEW_FORM_ENTITY_ONE_STATE)
        results = scan_entity_state_machines(tmp_path / "features")
        assert results == []

    def test_multiple_features_all_scanned(self, tmp_path):
        _write(tmp_path, "features/F050_JobAdmin/technical-spec.md", NEW_FORM_ENTITY_SM)
        _write(tmp_path, "features/F060_Checkout/technical-spec.md", NEW_FORM_UI_SM_ONLY)
        results = scan_entity_state_machines(tmp_path / "features")
        assert [r["code"] for r in results] == ["SM-001"]

    def test_missing_features_dir_returns_empty(self, tmp_path):
        assert scan_entity_state_machines(tmp_path / "nope") == []


class TestLegacyFormRegression:
    """The retired anchored-slug form must NOT be detected (it is out of scope for this scanner —
    validate_feature_spec.py's LEGACY_BLOCK_HEADING_RE is the dedicated migration-miss flag for it).
    This proves the fix is genuinely using the canonical parser, not accidentally matching both
    forms via a broadened regex that would mask the very migration gap this change exists to
    surface."""

    def test_legacy_anchored_slug_form_is_not_detected(self, tmp_path):
        _write(tmp_path, "features/F080_Legacy/technical-spec.md", LEGACY_FORM_ENTITY_SM)
        results = scan_entity_state_machines(tmp_path / "features")
        assert results == []
