"""Regression pin for the `action-thread-shapes/` corpus (phase 10, action-thread
reshape, plans/260824-1128-rebuild-spec-action-thread-v27-7).

FIXTURE PROVENANCE — real corpus, never hand-authored (the repo's own precedent:
a hand-authored fixture once produced 2785 green tests over a script that could never
run). All four `technical-spec.md` files are the REAL output of
`_feature_sot_technical_lib.compose_action_thread`, run against real, unedited
5-bucket-shaped `functional-spec.md`/`technical-spec.md` pairs:

- `F950_CleanMigrated`      <- sharetribe corpus `F022_AdminDashboardAndAnalytics`
- `F951_UnresolvedRules`    <- sharetribe corpus `F024_AnalyticsIntegration`
- `F952_NoActionsData`      <- already-committed `tests/fixtures/action_thread/
                               F017_technical-spec.md` (renamed F017 -> F952)
- `F953_MissingDiagram`     <- already-committed `tests/fixtures/action_thread/
                               F011_technical-spec.md` (renamed F011 -> F953)

Mechanical edits only, applied identically to all four (never content-authoring):
(1) internal `F0##_Name`/`F0##` self-references renamed to each variant's own
    `F95#`/`F95#_Name` slug, same convention `sot-shapes/` already uses; (2) the
    sharetribe corpus's own title-line shape (`# Technical Spec — F0##_Name`) rewritten
    to this repo's `FCODE_HEADING_RE` shape (`# F0##_Name — Technical Spec`) — a
    pre-existing, out-of-scope cross-repo format mismatch (same class as C8) that would
    otherwise make EVERY fixture fail `FeatureSpec.f_code_format` regardless of which
    of the four scenarios it is meant to demonstrate.

Every assertion below calls the real `validate_feature_spec._check_technical_spec`
against the committed fixture files on disk — no hand-computed expectations.

A note on realism: scanning the full 43-feature sharetribe corpus through the real
composer (implementer's own measurement, not asserted here) found that EVERY feature
with at least one real action fires `rung_order` on raw, un-reviewed composer output —
a mechanical-composition limitation the researcher pass phase 11 exists to close, not
a phase-10 defect. (A second finding from that same scan, `action_double_claimed`
firing 127 times across 31/43 features, turned out to be a modelling error in the
check itself — legitimate one-requirement-to-many-actions fan-out, not a composer
defect — and the check was retired; see `test_action_index_validation.py`.)
`F950_CleanMigrated` is the feature with the fewest such findings in the whole corpus
(one `rung_order`); it demonstrates a
normal successful migration, not a fictional zero-finding one. It is "clean" relative to
the other three fixtures' DELIBERATE distinguishing defects (heavy unresolved-rule
count, zero actions, a missing diagram) — asserted below as absence of THOSE specific
signals, not as an empty issue list.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import validate_feature_spec as vfs  # noqa: E402

_TESTS_DIR = Path(__file__).resolve().parent
_CORPUS = _TESTS_DIR / "fixtures" / "corpora" / "action-thread-shapes"


def _fixture(name: str) -> Path:
    return _CORPUS / name


def _issues(name: str) -> list[dict]:
    return vfs._check_technical_spec(_fixture(name) / "technical-spec.md", SCRIPTS_DIR)


def _rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in issues]


def _critical_rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in issues if i["severity"] == "critical"]


class TestF950CleanMigrated:
    """A normal, successfully action-thread-migrated feature: real actions, a
    populated Action Index, no zero-action shape, no over-threshold diagram gap.
    Contrasts with F952 (zero actions) and F953 (diagram gap) by NOT exhibiting
    either of those specific signals."""

    def test_action_index_has_real_data_rows(self):
        text = (_fixture("F950_CleanMigrated") / "technical-spec.md").read_text(encoding="utf-8")
        assert "| **A1** |" in text, "expected at least one real (non-A0) action row"

    def test_action_index_missing_does_not_fire(self):
        assert "FeatureSpec.action_index_missing" not in _rule_ids(_issues("F950_CleanMigrated"))

    def test_diagram_required_missing_does_not_fire(self):
        assert "FeatureSpec.diagram_required_missing" not in _rule_ids(_issues("F950_CleanMigrated"))

    def test_unresolved_rule_count_is_far_below_f951(self):
        """Both fixtures carry SOME unresolved [UNVERIFIED] markers (C11: every DEC
        block is unresolved by construction, corpus-wide) — the distinguishing fact
        is F950's count is small relative to F951's, not zero."""
        f950_text = (_fixture("F950_CleanMigrated") / "technical-spec.md").read_text(encoding="utf-8")
        f951_text = (_fixture("F951_UnresolvedRules") / "technical-spec.md").read_text(encoding="utf-8")
        f950_count = f950_text.count("[UNVERIFIED] carried from **Applies to:**") + \
            f950_text.count("[UNVERIFIED] no resolvable owner")
        f951_count = f951_text.count("[UNVERIFIED] carried from **Applies to:**") + \
            f951_text.count("[UNVERIFIED] no resolvable owner")
        assert f950_count < f951_count


class TestF951UnresolvedRules:
    """A real feature whose `**Applies to:**` free text mostly does not resolve to a
    declared action by handler/path match (D2's own binding limitation, measured
    corpus-wide at 26% resolution for BR, 0% for DEC per C11) — 8 distinct
    `[UNVERIFIED]` rule markers survive into the composed output, each explicitly
    naming the original `Applies to:` text so a later researcher pass can resolve it
    by hand. Proves the composer's own 'never guess an owner' discipline (merge
    blocker #2 of phase 05) rather than silently dropping the unresolved rule."""

    def test_eight_unverified_markers_present(self):
        text = (_fixture("F951_UnresolvedRules") / "technical-spec.md").read_text(encoding="utf-8")
        applies_to = text.count("[UNVERIFIED] carried from **Applies to:**")
        no_owner = text.count("[UNVERIFIED] no resolvable owner")
        assert applies_to == 7, f"expected 7 unresolved Applies-to markers, found {applies_to}"
        assert no_owner == 1, f"expected 1 unresolved DEC (no Applies-to field at all), found {no_owner}"

    def test_unverified_markers_name_the_original_text(self):
        """Proves the marker carries the SOURCE text, not a bare stub — the input
        genuinely reached the unresolved branch rather than merely being absent."""
        text = (_fixture("F951_UnresolvedRules") / "technical-spec.md").read_text(encoding="utf-8")
        assert '(original: "`PATCH (/:locale)/admin/analytics/google-analytics/update_google`")' in text

    def test_no_check_silently_swallows_the_unresolved_rules(self):
        """[UNVERIFIED] is informational (no dedicated validator rule_id keys on it —
        a later researcher pass, not a machine check, resolves it), but the file must
        still validate as a well-formed action-thread document otherwise: the Action
        Index itself must be present with real rows, not reported missing."""
        assert "FeatureSpec.action_index_missing" not in _rule_ids(_issues("F951_UnresolvedRules"))


class TestF952NoActionsData:
    """A real feature (sharetribe F017_TransportAndCookieSecurity, C2's own
    zero-action example: zero declared HTTP/RPC endpoints AND zero DB-Impact rows) —
    § 2 Action Index carries ONLY the mandatory A0 cross-cutting row. Proves C2's fix
    end-to-end on real content: `FeatureSpec.action_index_missing` (critical, 'zero
    data rows') must NOT fire on a legitimate zero-action infrastructure feature."""

    def test_action_index_has_only_the_a0_row(self):
        text = (_fixture("F952_NoActionsData") / "technical-spec.md").read_text(encoding="utf-8")
        assert "| **A0** |" in text
        assert "| **A1** |" not in text

    def test_action_index_missing_does_not_fire(self):
        assert "FeatureSpec.action_index_missing" not in _rule_ids(_issues("F952_NoActionsData"))

    def test_validates_with_zero_criticals(self):
        """The cleanest fixture in the whole corpus (confirmed by scanning all 43
        real sharetribe features through the composer): a genuinely zero-action
        feature has nothing left for a mechanical composer to get wrong."""
        assert _critical_rule_ids(_issues("F952_NoActionsData")) == []


class TestF953MissingDiagram:
    """A real feature (sharetribe F011_ListingModeration, the plan's own acceptance
    fixture) whose A9 (`ExportListingsJob#perform`, background/queue-driven — over
    the diagram threshold per `_action_thread_diagram_lib.is_over_threshold`) has no
    `sequenceDiagram` fence anywhere in its own capability bucket. Proves
    `FeatureSpec.diagram_required_missing` fires on a genuine real-corpus gap, not a
    synthesized one — the raw composer never generates diagrams itself (a researcher/
    LLM fill concern), so any over-threshold action in freshly composed output
    legitimately lacks one until that pass runs.

    This same fixture also carries 3 `[UNVERIFIED] no resolvable owner` markers (its
    3 DEC blocks — C11: unresolved by construction, every one of them) — it IS the
    "legitimately mid-pipeline" file the fill-pending degradation window
    (`_action_thread_diagram_lib.is_fill_pending`) exists for. Updated from the
    pre-window `critical` expectation to `warning` once that window landed; the
    corpus-wide before/after measurement (117 criticals -> 117 warnings, 0 other
    rule_id counts changed) is reported in the implementer handback, not re-proven
    per-fixture here."""

    def test_diagram_required_missing_fires_as_warning_while_fill_pending(self):
        issues = _issues("F953_MissingDiagram")
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.diagram_required_missing"]
        assert len(matching) == 1, issues
        assert matching[0]["severity"] == "warning"
        assert matching[0]["rule_id"] == "FeatureSpec.diagram_required_missing"
        assert "A9" in matching[0]["message"]
        assert "_pre_fill" in matching[0]["message"]

    def test_fixture_genuinely_carries_the_fill_pending_marker(self):
        """SILENT input for the test above: reaches the branch only because this
        real file carries >=1 `[UNVERIFIED]` marker (never asserted, only measured)."""
        text = (_fixture("F953_MissingDiagram") / "technical-spec.md").read_text(encoding="utf-8")
        assert text.count("[UNVERIFIED]") == 3

    def test_a9_is_genuinely_over_threshold_and_reaches_the_branch(self):
        """Proves the input actually reaches the branch (merge blocker #4): A9 is
        background/queue-driven, one of `is_over_threshold`'s two OR'd signals."""
        text = (_fixture("F953_MissingDiagram") / "technical-spec.md").read_text(encoding="utf-8")
        assert "**A9** | `ExportListingsJob#perform` *(background, no FE)*" in text
        assert "queue" in text

    def test_a9_bucket_carries_no_mermaid_fence(self):
        """The negative half of the proof: A9's own capability bucket (`### 3.1`,
        the only bucket in this fixture) has zero ```mermaid``` fences — the finding
        is not a false positive from a misdrawn bucket boundary."""
        from _spec_parse import parse_headings_and_blocks
        from _action_thread_diagram_lib import mermaid_fences, capability_buckets

        lines = (_fixture("F953_MissingDiagram") / "technical-spec.md").read_text(
            encoding="utf-8").splitlines()
        headings, _ = parse_headings_and_blocks(lines)
        h2 = [(i, h) for i, h in headings if h.startswith("## ") and not h.startswith("### ")]
        b_actions = next(
            (idx + 1, (h2[i + 1][0] if i + 1 < len(h2) else len(lines)))
            for i, (idx, h) in enumerate(h2) if h == "## 3. Actions"
        )
        buckets = capability_buckets(headings, b_actions)
        fences = mermaid_fences(lines)
        assert not any(b[0] <= f["start"] < b[1] for b in buckets for f in fences)
