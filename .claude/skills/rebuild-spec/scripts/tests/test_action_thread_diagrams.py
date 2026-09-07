"""Phase 03 (rule bins + diagram contract) — the 3 new
`FeatureSpec.diagram_required_missing`/`diagram_cites_file_line`/`diagram_over_cap`
checks wired into `validate_feature_spec._check_rule_bins_and_diagrams`, plus unit
tests for the parsing they're built on (`_action_thread_diagram_lib`).

Integration tests mirror `test_action_index_validation.py`'s pattern: call
`vfs._check_technical_spec` directly against a hand-built, action-thread-shaped
technical-spec.md, scoped to this phase's own rule_ids (`_diagram_rule_ids`) rather
than the full issues list. Phase 10 closed the `REQUIRED_H2_TECH`/mapping-table gap
this note used to name (`required_sections` now accepts the thread shape;
`mapping_table_missing`/`sysdesign_subsections` are retired outright) — the scoped
assertion is kept here regardless, since it is this file's own established pattern.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import _action_thread_diagram_lib as diagram_lib  # noqa: E402
import validate_feature_spec as vfs  # noqa: E402

_DIAGRAM_PREFIX = "FeatureSpec.diagram_"


def _diagram_rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in issues if i["rule_id"].startswith(_DIAGRAM_PREFIX)]


def _diagram_issues(issues: list[dict]) -> list[dict]:
    return [i for i in issues if i["rule_id"].startswith(_DIAGRAM_PREFIX)]


# ---------------------------------------------------------------------------
# Lib unit tests — `_action_thread_diagram_lib`
# ---------------------------------------------------------------------------

class TestMermaidFences:
    def test_extracts_one_fence_with_line_bounds(self):
        lines = [
            "prose before",
            "```mermaid",
            "sequenceDiagram",
            "    A->>B: hi",
            "```",
            "prose after",
        ]
        fences = diagram_lib.mermaid_fences(lines)
        assert len(fences) == 1
        assert fences[0]["start"] == 1
        assert fences[0]["end"] == 5
        assert fences[0]["body"] == ["sequenceDiagram", "    A->>B: hi"]

    def test_non_mermaid_fence_is_not_extracted(self):
        """SILENT input for every diagram check downstream: a plain ```text```
        or ```ruby``` fence is not a mermaid fence and must never be scanned."""
        lines = ["```ruby", "listing.update!(open: false)", "```"]
        assert diagram_lib.mermaid_fences(lines) == []


class TestCountArrowsAndAlts:
    def test_counts_arrow_and_alt_lines(self):
        body = [
            "actor Ad as Admin",
            "Ad->>C: click",
            "alt state = approved",
            "C-->>Ad: ok",
            "else state = rejected",
            "C-->>Ad: no",
            "end",
        ]
        arrows, alts = diagram_lib.count_arrows_and_alts(body)
        assert arrows == 3  # Ad->>C, C-->>Ad, C-->>Ad
        assert alts == 1  # only the `alt` opener line, not `else`/`end`

    def test_no_arrows_or_alts_is_silent(self):
        body = ["actor Ad as Admin", "Note over Ad: just a note"]
        assert diagram_lib.count_arrows_and_alts(body) == (0, 0)


class TestFileLineTokens:
    def test_finds_path_colon_line_token(self):
        body = ["Note over C: see widgets_controller.rb:12 for details"]
        tokens = diagram_lib.file_line_tokens(body)
        assert tokens, tokens

    def test_ordinary_prose_is_silent(self):
        """SILENT input: a `Note over` line describing behavior, with no
        `path:line`-shaped substring — the normal case for every legitimate
        sequenceDiagram (order/branching, never facts-with-citations)."""
        body = ["Note over V: DEC-001 decides whether the menu renders"]
        assert diagram_lib.file_line_tokens(body) == []


class TestIsOverThreshold:
    def test_two_or_more_tables_is_over(self):
        assert diagram_lib.is_over_threshold({"tables": ["a", "b"], "method": "PATCH", "key": "`X#y`"})

    def test_queue_method_is_over_regardless_of_tables(self):
        assert diagram_lib.is_over_threshold({"tables": ["a"], "method": "queue", "key": "`X#y`"})

    def test_background_suffix_is_over_regardless_of_tables(self):
        row = {"tables": [], "method": "GET", "key": "`X#y` *(background, no FE)*"}
        assert diagram_lib.is_over_threshold(row)

    def test_one_table_synchronous_non_background_is_under(self):
        """SILENT input for `diagram_required_missing`: a synchronous action
        writing exactly one table (F011's real A3/A4 shape) never crosses the
        threshold, diagram or not."""
        row = {"tables": ["a"], "method": "PATCH", "key": "`X#y`"}
        assert not diagram_lib.is_over_threshold(row)

    def test_zero_tables_read_only_is_under(self):
        row = {"tables": [], "method": "GET", "key": "`X#y`"}
        assert not diagram_lib.is_over_threshold(row)


class TestIsFillPending:
    """`diagram_required_missing`'s fill-pending degradation window (this
    follow-up) — same `[UNVERIFIED]` tag `_doc_migration_action_thread_step_lib.
    _UNVERIFIED_MARKER` counts into the rollback sidecar."""

    def test_true_when_applies_to_sentence_present(self):
        """The BR-rule sentence `compose_action_thread` emits when an
        `**Applies to:**` field fails to resolve."""
        text = ("**FR-601** applies globally. [UNVERIFIED] carried from "
                "**Applies to:** — needs a researcher pass")
        assert diagram_lib.is_fill_pending(text) is True

    def test_true_when_no_resolvable_owner_sentence_present(self):
        """The DEC-rule sentence (C11/C14: every DEC block in the real corpus
        is unresolved by construction and carries THIS sentence, never the
        `**Applies to:**` one — counting only the first sentence would blind
        the window to every DEC-only feature)."""
        text = "**DEC-001** decides X. [UNVERIFIED] no resolvable owner — needs a researcher pass"
        assert diagram_lib.is_fill_pending(text) is True

    def test_false_when_marker_absent(self):
        assert diagram_lib.is_fill_pending("every rule bound to an action, no markers") is False


class TestCapabilityBuckets:
    def test_partitions_by_h3_heading(self):
        headings = [
            (0, "## 3. Actions"),
            (1, "### 3.1 CAP-01 — A"),
            (5, "#### A1 · foo"),
            (10, "### 3.2 CAP-02 — B"),
            (15, "#### A2 · bar"),
        ]
        buckets = diagram_lib.capability_buckets(headings, (0, 20))
        assert buckets == [(1, 10), (10, 20)]

    def test_no_h3_headings_yields_no_buckets(self):
        headings = [(0, "## 3. Actions"), (1, "#### A1 · foo")]
        assert diagram_lib.capability_buckets(headings, (0, 5)) == []


# ---------------------------------------------------------------------------
# Integration fixture — CAP-01 (A1, under threshold, no diagram), CAP-02 (A2,
# over threshold via 2 tables, diagram inside its OWN § 3 block), CAP-03 (A3/A4,
# under threshold, no diagram — mirrors F011's real A3/A4 shape; A9, over
# threshold via background/async, diagram shared at the CAPABILITY BUCKET level
# ahead of A3's own heading — mirrors F011's real A5/A6/A9 shared-diagram shape).
# ---------------------------------------------------------------------------

_GOOD_SPEC = """\
# F902_Test — Diagram Test

## 1. Technical Overview

Overview text.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-601 | — | § 4.4 |
| **A1** | `WidgetsController#index` | `GET` `.../widgets` | FR-101, US101 | — *(read-only)* | § 3.1 |
| **A2** | `WidgetsController#update` | `PATCH` `.../update` | FR-102, BR-001 | `widgets, widget_logs` | § 3.2 ▸ **diagram** |
| **A3** | `WidgetsController#close` | `PATCH` `.../close` | FR-103 | `widgets` | § 3.3 |
| **A4** | `WidgetsController#delete` | `DELETE` `.../delete` | FR-104 | `widgets` | § 3.3 |
| **A9** | `ExportWidgetsJob#perform` *(background, no FE)* | queue · `Delayed::Job` | FR-105, US105 | `export_task_results` | § 3.3 ▸ **diagram** |

## 3. Actions

### 3.1 CAP-01 — Browse widgets

#### A1 · List widgets

`GET .../widgets` → `WidgetsController#index`
`FR-101` `US101`

**Who** · Admin
**Result** · read-only — **no DB write**.
**Source:** `widgets_controller.rb:5-10`

### 3.2 CAP-02 — Update widgets

#### A2 · Update a widget

`PATCH .../update` → `WidgetsController#update`
`FR-102`

**Who** · Admin
**Result** · updates `widgets.state` and `widget_logs.entry`.

```mermaid
sequenceDiagram
    actor Ad as Admin
    participant C as "#update"
    Ad->>C: PATCH .../update
    C-->>Ad: 200 OK
```

**Source:** `widgets_controller.rb:12-18`

### 3.3 CAP-03 — Close, delete, export widgets

```mermaid
sequenceDiagram
    actor Ad as Admin
    participant C as "#export"
    participant J as ExportWidgetsJob
    Ad->>C: GET .../export
    C->>J: enqueue
    J->>J: perform
```

#### A3 · Close a widget

`PATCH .../close` → `WidgetsController#close`
`FR-103`

**Who** · Admin
**Result** · updates `widgets.state`.
**Source:** `widgets_controller.rb:20-25`

#### A4 · Delete a widget

`DELETE .../delete` → `WidgetsController#delete`
`FR-104`

**Who** · Admin
**Result** · updates `widgets.deleted`.
**Source:** `widgets_controller.rb:27-30`

#### A9 · Export widgets *(background, no FE)*

`Delayed::Job` → `ExportWidgetsJob#perform`
`FR-105` `US105`

**Who** · *no human actor* — background job
**Result** · writes `export_task_results.status`.
**Source:** `export_widgets_job.rb:1-40`

## 4. Shared Foundation

### 4.1 Components

None.

### 4.2 Data Model

None.

### 4.3 State Management

None.

### 4.4 Shared Rules

#### Bin 3 — cross-cutting, belongs to no single action

**FR-601** applies globally: every widget action requires an admin session.

### 4.5 Algorithms & Integrations

None.

### 4.6 Configuration

None.
"""


def _write_spec(tmp_path: Path, tech_text: str, feature: str = "F902_Test") -> Path:
    feat_dir = tmp_path / "docs" / "features" / feature
    feat_dir.mkdir(parents=True)
    spec = feat_dir / "technical-spec.md"
    spec.write_text(tech_text, encoding="utf-8")
    return spec


class TestBaselineIsCleanForDiagramCodes:
    def test_good_fixture_fires_no_diagram_code(self, tmp_path):
        """Exercises all three under/over-threshold shapes at once: A1 (0
        tables, no diagram), A3/A4 (1 table each, no diagram — F011's real
        A3/A4 shape), A2 (2 tables, own-block diagram), A9 (background,
        bucket-shared diagram trailing the CAP-03 heading, not A9's own H4)."""
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _diagram_rule_ids(issues) == [], _diagram_issues(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.diagram_required_missing
# ---------------------------------------------------------------------------

class TestDiagramRequiredMissing:
    def test_over_threshold_background_action_without_bucket_diagram_fires(self, tmp_path):
        """Reaches: `has_fence` False for A9's bucket once the CAP-03 shared
        fence is deleted entirely. A9 is over threshold via `method == "queue"`
        (background/async), independent of its 1-table write. SILENT input:
        every over-threshold action's bucket carries >=1 mermaid fence."""
        broken = _GOOD_SPEC.replace(
            '```mermaid\n'
            'sequenceDiagram\n'
            '    actor Ad as Admin\n'
            '    participant C as "#export"\n'
            '    participant J as ExportWidgetsJob\n'
            '    Ad->>C: GET .../export\n'
            '    C->>J: enqueue\n'
            '    J->>J: perform\n'
            '```\n\n'
            '#### A3',
            '#### A3',
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.diagram_required_missing"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert "A9" in matching[0]["message"]
        assert _diagram_rule_ids(issues) == ["FeatureSpec.diagram_required_missing"]

    def test_over_threshold_via_two_tables_without_fence_fires(self, tmp_path):
        """Same check, the OTHER threshold branch: A2 (writes 2 tables, no
        async/background signal at all) loses its own diagram and CAP-02 has no
        other fence to share — must still fire."""
        broken = _GOOD_SPEC.replace(
            '```mermaid\n'
            'sequenceDiagram\n'
            '    actor Ad as Admin\n'
            '    participant C as "#update"\n'
            '    Ad->>C: PATCH .../update\n'
            '    C-->>Ad: 200 OK\n'
            '```\n\n',
            '',
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.diagram_required_missing"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert "A2" in matching[0]["message"]
        assert _diagram_rule_ids(issues) == ["FeatureSpec.diagram_required_missing"]

    def test_under_threshold_action_without_diagram_is_silent(self, tmp_path):
        """Merge-blocker two-sided test, other side: A3/A4 write exactly one
        table each, are fully synchronous, and carry no diagram of their own —
        this must NEVER fire, matching F011's real A3/A4."""
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.diagram_required_missing" not in _diagram_rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.diagram_required_missing — fill-pending degradation window
# (plans/260824-1128-rebuild-spec-action-thread-v27-7 follow-up: "add a
# degradation window so a legitimately mid-pipeline file is not reported as
# critical"). Reuses `_thread_sev_msg` (D4), a DIFFERENT boolean
# (`_action_thread_diagram_lib.is_fill_pending`) from the same-named function's
# existing `is_pre_thread` window — the two are independent and this class
# exercises only the new one, on a file that is otherwise fully action-thread
# shaped (never carries `_TECH_PRE_THREAD_SENTINEL`).
# ---------------------------------------------------------------------------

class TestDiagramRequiredMissingFillPendingWindow:
    """Merge blocker #1: the SAME over-threshold action with no diagram is a
    `warning` pre-fill and a `critical` post-fill — asserted with strict
    severity/rule_id equality, never a bare exit code."""

    # Same starting point as `test_over_threshold_via_two_tables_without_
    # fence_fires` above: A2's own diagram deleted, CAP-02 has no other fence
    # to share, so A2 (2-table write) is over threshold with nothing covering it.
    _BROKEN = _GOOD_SPEC.replace(
        '```mermaid\n'
        'sequenceDiagram\n'
        '    actor Ad as Admin\n'
        '    participant C as "#update"\n'
        '    Ad->>C: PATCH .../update\n'
        '    C-->>Ad: 200 OK\n'
        '```\n\n',
        '',
    )
    # SAME `[UNVERIFIED]` tag `_doc_migration_action_thread_step_lib.
    # _UNVERIFIED_MARKER` counts — placed in § 4.4 Bin 3, exactly where
    # `compose_action_thread` leaves a rule it could not bind to an action.
    _BROKEN_FILL_PENDING = _BROKEN.replace(
        "**FR-601** applies globally: every widget action requires an admin session.",
        "**FR-601** applies globally: every widget action requires an admin session. "
        "[UNVERIFIED] carried from **Applies to:** — needs a researcher pass",
    )

    def test_critical_once_fill_is_resolved(self, tmp_path):
        """No `[UNVERIFIED]` marker anywhere in the file — every rule is bound,
        so a real missing diagram is a hard critical, unsuffixed. Confirms the
        window does not weaken the check once the researcher pass is done."""
        spec = _write_spec(tmp_path, self._BROKEN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.diagram_required_missing"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert "_pre_fill" not in matching[0]["message"]

    def test_warning_while_fill_pending(self, tmp_path):
        """SAME missing diagram, only the `[UNVERIFIED]` marker added — the
        file is legitimately mid-pipeline (composed, not yet researcher-filled)
        — degrades to warning with the `(_pre_fill)` suffix, distinct from the
        unrelated `(_pre_thread)` shape-migration window."""
        spec = _write_spec(tmp_path, self._BROKEN_FILL_PENDING)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.diagram_required_missing"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "_pre_fill" in matching[0]["message"]

    def test_other_codes_unaffected_by_fill_pending(self, tmp_path):
        """Merge blocker #2: the window is scoped to `diagram_required_missing`
        alone — adding the marker must not silence or degrade any other
        diagram/action-thread rule_id into a wider amnesty."""
        spec = _write_spec(tmp_path, self._BROKEN_FILL_PENDING)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _diagram_rule_ids(issues) == ["FeatureSpec.diagram_required_missing"]


# ---------------------------------------------------------------------------
# FeatureSpec.diagram_cites_file_line
# ---------------------------------------------------------------------------

class TestDiagramCitesFileLine:
    def test_file_line_token_inside_fence_fires(self, tmp_path):
        """Reaches: `_action_thread_diagram_lib.file_line_tokens` returning a
        non-empty list for A2's fence — a `Note over` line leaks a real
        `path:line`. SILENT input: no mermaid fence in the document contains a
        `path:line`-shaped token anywhere."""
        broken = _GOOD_SPEC.replace(
            "    Ad->>C: PATCH .../update\n",
            "    Ad->>C: PATCH .../update\n"
            "    Note over C: see widgets_controller.rb:12 for details\n",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.diagram_cites_file_line"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert _diagram_rule_ids(issues) == ["FeatureSpec.diagram_cites_file_line"]

    def test_no_file_line_token_in_any_fence_is_silent(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.diagram_cites_file_line" not in _diagram_rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.diagram_over_cap
# ---------------------------------------------------------------------------

class TestDiagramOverCap:
    def test_over_twelve_arrows_fires_warning_not_critical(self, tmp_path):
        """Reaches: `arrows > 12` in A2's fence. Stays a WARNING even though
        every other diagram check here is critical — arrow counting is a
        heuristic (`Note over`/wrapped-arrow miscounts), so it must never block
        a build on its own. SILENT input: every fence stays at <=12 arrows and
        <=2 `alt` blocks."""
        extra_arrows = "\n".join(f"    Ad->>C: step {n}" for n in range(20))
        broken = _GOOD_SPEC.replace(
            "    Ad->>C: PATCH .../update\n    C-->>Ad: 200 OK\n",
            f"    Ad->>C: PATCH .../update\n{extra_arrows}\n    C-->>Ad: 200 OK\n",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.diagram_over_cap"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert _diagram_rule_ids(issues) == ["FeatureSpec.diagram_over_cap"]

    def test_under_cap_fence_is_silent(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.diagram_over_cap" not in _diagram_rule_ids(issues)
