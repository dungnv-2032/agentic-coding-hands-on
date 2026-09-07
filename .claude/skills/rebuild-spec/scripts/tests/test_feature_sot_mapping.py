"""Tests for `_feature_sot_mapping_lib.py` -- `## 2. Functional -> Technical Mapping`
row building (T-02/T-03/T-11/T-13/T-16) and `### 3.4 API & Endpoints` (T-16/T-26),
including the completeness pass that keeps
`validate_feature_spec.FeatureSpec.mapping_table_missing` from CRITICALing on a
twin-declared BR-###/SM-### the Requirements table/Decision Logic never happened to
cover (found the hard way against the real 66-feature corpus -- see phase-10 report).
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _action_thread_handler_lib import is_job_class  # noqa: E402
from _feature_sot_extract_lib import (  # noqa: E402
    ExtractedThreadPieces, ThreadIntBlock, ThreadRuleBlock, UsBlock,
)
from _feature_sot_mapping_lib import (  # noqa: E402
    assign_codes, build_action_records, build_api_endpoints, build_mapping_rows, build_mapping_table,
    build_title_index,
)

REQUIREMENTS_BODY = """
| Code | Description | Endpoint/Handler | Verifiable |
|------|-------------|------------------|------------|
| FR-001 | Sample requirement one | `POST /sample` via `SampleController#create` | yes |

**Source:** `app/controllers/sample_controller.rb:1-10`
"""

DEC_BLOCKS = [
    ("#### Sample decision statement. (DEC-001)",
     "**subtype:** render\n**Source:** `app/models/sample.rb:20-25`"),
]

BR_BLOCKS = [
    ("### Sample business rule statement. (BR-001)",
     "**Linked FR:** FR-001\n**Source:** `app/models/sample.rb:1-5`"),
    ("### Orphan rule statement not in FR table. (BR-099)",
     "**Source:** `app/models/orphan.rb:1-5`"),
]
SM_BLOCKS = [
    ("### Tracks the sample state machine (SM-001)", "**Source:** `app/models/sample.rb:9-9`"),
]

US_BLOCKS = [
    UsBlock(
        code="US001_SampleStory", title="Sample story", priority="P1",
        fields={
            "Why this priority": "Core to the sample flow.",
            "Requirements fulfilled": (
                "- **FR-001** Sample requirement one — `POST /sample` via "
                "`SampleController#create`\n  **Source:** `app/controllers/sample_controller.rb:1-10`"
            ),
        },
    ),
]

TWIN_TEXT = """
## 5. Business Rules

- Sample rule text. (BR-001)
- Orphan rule text. (BR-099)
- Sample state machine tracked. (SM-001)

## 7. User Stories

### US001_SampleStory — Sample story (Priority: P1)
"""

# Defect 1 (p14-migration-report.md § Risks, item 1): § 10 Edge Behaviours to Verify
# uses the identical `- **FR-###** ...` bullet shape as § 4 Requirements. FR-001 and
# FR-002 are deliberately duplicated in BOTH sections below so a section-unaware,
# last-match-wins scan is forced down the exact buggy branch -- if the index were
# built without section boundaries, the § 10 sentence (scanned after § 4 in document
# order) would silently overwrite the real § 4 title.
TWIN_TEXT_WITH_FR_SECTION10_COLLISION = """
## 4. Requirements

- **FR-001** Redirect already-logged-in visitors away from login/signup
- **FR-002** Require a valid session to view protected pages

## 5. Business Rules

- Sample rule text. (BR-001)

## 7. User Stories

### US001_SampleStory — Sample story (Priority: P1)

## 10. Edge Behaviours to Verify

- **FR-001** → Registration with duplicate email shows "email_is_in_use" flash; no new records
- **FR-002** → Visiting a protected page while logged out redirects to login
"""


def test_build_title_index_reads_fr_br_us_titles_from_twin():
    index = build_title_index(TWIN_TEXT)
    assert index["BR-001"] == "Sample rule text."
    assert index["SM-001"] == "Sample state machine tracked."
    assert index["US001_SampleStory"] == "Sample story"


def test_build_title_index_fr_title_comes_from_section_4_not_section_10():
    """Reaches the § 4 vs § 10 collision branch directly (see fixture comment above).
    Pre-fix this asserted the § 10 verification sentence (last-match-wins); post-fix
    it must read the real § 4 requirement title, per target-shape-spec.md § 3's
    "Name MUST NOT restate the story" rule."""
    index = build_title_index(TWIN_TEXT_WITH_FR_SECTION10_COLLISION)
    assert index["FR-001"] == "Redirect already-logged-in visitors away from login/signup"
    assert index["FR-002"] == "Require a valid session to view protected pages"
    assert "email_is_in_use" not in index["FR-001"]
    assert "redirects to login" not in index["FR-002"]


def test_mapping_rows_seeded_from_requirements_dec_and_us():
    title_index = build_title_index(TWIN_TEXT)
    rows = build_mapping_rows(
        REQUIREMENTS_BODY, DEC_BLOCKS, BR_BLOCKS, SM_BLOCKS, US_BLOCKS, title_index, TWIN_TEXT,
    )
    codes = [r[0] for r in rows]
    assert "FR-001" in codes
    assert "DEC-001" in codes
    assert "US001_SampleStory" in codes


def test_mapping_completeness_pass_adds_every_other_twin_declared_code():
    """The Requirements table only names FR-001; the twin also declares BR-001,
    BR-099, and SM-001 (§ 5) -- all three MUST still get a row, or
    `mapping_table_missing` CRITICALs on real corpora exactly as measured."""
    title_index = build_title_index(TWIN_TEXT)
    rows = build_mapping_rows(
        REQUIREMENTS_BODY, DEC_BLOCKS, BR_BLOCKS, SM_BLOCKS, US_BLOCKS, title_index, TWIN_TEXT,
    )
    codes = {r[0] for r in rows}
    assert {"BR-001", "BR-099", "SM-001"} <= codes
    # exactly one row per code -- no duplicates from double-seeding
    assert len(codes) == len([r[0] for r in rows])


def test_completeness_row_uses_matching_block_source_when_available():
    title_index = build_title_index(TWIN_TEXT)
    rows = build_mapping_rows(
        REQUIREMENTS_BODY, DEC_BLOCKS, BR_BLOCKS, SM_BLOCKS, US_BLOCKS, title_index, TWIN_TEXT,
    )
    row = next(r for r in rows if r[0] == "BR-099")
    assert row[4] == "`app/models/orphan.rb:1-5`"  # Source column


def test_no_codes_at_all_yields_the_na_sentinel():
    table = build_mapping_table([])
    assert table.startswith("N/A — no FR/BR/US/AC")


def test_api_endpoints_extracted_from_requirements_and_requirements_fulfilled():
    text = build_api_endpoints(REQUIREMENTS_BODY, US_BLOCKS)
    assert "POST" in text and "/sample" in text


def test_api_endpoints_deduplicated_across_sources():
    text = build_api_endpoints(REQUIREMENTS_BODY, US_BLOCKS)
    assert text.count("/sample") == 1


def test_api_endpoints_na_when_nothing_found():
    text = build_api_endpoints("", [])
    assert text.startswith("N/A — no HTTP/RPC surface")


# ---------------------------------------------------------------------------
# rebuild-spec 27.7.0 (action-thread reshape, phase 05) -- `resolve_rule_owners`
# unit coverage. Full end-to-end corpus coverage lives in
# test_action_thread_composer.py; these are the resolver's own decision-tree
# branches in isolation, with small synthetic action lists (not a corpus fixture
# concern -- the "never hand-author a fixture" rule targets the composer's real-
# document pipeline, not a pure-function's own unit tests).
# ---------------------------------------------------------------------------
from _feature_sot_mapping_lib import ActionRecord, resolve_rule_owners  # noqa: E402

_A2 = ActionRecord(id="A2", handler="Ctrl#update", handler_norm="ctrl#update",
                    handler_class_norm="ctrl", method_norm="update", http_method="PATCH",
                    path="/update")
_A7 = ActionRecord(id="A7", handler="Ctrl#approve", handler_norm="ctrl#approve",
                    handler_class_norm="ctrl", method_norm="approve", http_method="PUT",
                    path="/:id/approve")
_A9 = ActionRecord(id="A9", handler="Job#perform", handler_norm="job#perform",
                    handler_class_norm="job", method_norm="perform", is_background=True)


def test_resolve_rule_owners_empty_text_is_unresolved():
    assert resolve_rule_owners("", [_A2, _A7]) == []
    assert resolve_rule_owners("   ", [_A2, _A7]) == []


def test_resolve_rule_owners_bare_method_unique_match():
    assert resolve_rule_owners("`#update` action", [_A2, _A7]) == ["A2"]


def test_resolve_rule_owners_compound_bare_methods_resolve_to_both():
    assert resolve_rule_owners("`#update`/`#approve` action", [_A2, _A7]) == ["A2", "A7"]


def test_resolve_rule_owners_exact_classmethod_match():
    assert resolve_rule_owners("Ctrl#update", [_A2, _A7]) == ["A2"]


def test_resolve_rule_owners_classmethod_falls_back_to_unique_class_match():
    """A background job's `Applies to:` sometimes names an INTERNAL method
    (`Job#generate_csv_content`) that differs from the Action Index's own entry
    point (`Job#perform`) -- resolved via the class name alone, ONLY when exactly
    one action carries that class (never ambiguous, never a guess between
    candidates)."""
    assert resolve_rule_owners("Job#generate_csv_content", [_A2, _A7, _A9]) == ["A9"]


def test_resolve_rule_owners_ambiguous_class_match_stays_unresolved():
    """Two actions share a class (e.g. a controller with many actions) -- a
    class-only match must NEVER pick one of them; that would be exactly the
    guessed ownership merge blocker #2 forbids."""
    a_index = ActionRecord(id="A1", handler="Ctrl#index", handler_norm="ctrl#index",
                            handler_class_norm="ctrl", method_norm="index")
    assert resolve_rule_owners("Ctrl#nonexistent_method", [_A2, a_index]) == []


def test_resolve_rule_owners_no_actions_at_all_is_always_unresolved():
    """Merge blocker #1's other half: on a zero-action feature, even a `Applies
    to:` that WOULD resolve on a normal feature must come back empty -- there is
    nothing to bind to, and the caller (assign_codes) must route it to A0."""
    assert resolve_rule_owners("`#update` action", []) == []
    assert resolve_rule_owners("Ctrl#update", []) == []


# ---------------------------------------------------------------------------
# rebuild-spec 27.7.1 -- `assign_codes`'s SM-###/ALG-###/INT-### fallback.
# Real-corpus defect (F026_TransactionalEmailSettings, `FeatureSpec.
# action_unclaimed`): SM-###/ALG-### blocks live under § 3.3 State Management /
# § 3.5 Algorithms -- OUTSIDE any `### 4.N` capability bucket -- so they never had
# a structured home before (`_feature_sot_extract_lib.ExtractedThreadPieces.
# sm_blocks`/`alg_blocks`), and when a feature's § 2 mapping table also happens
# not to carry a completeness row for one (F026's SM-001 didn't), the code was
# invisible to `assign_codes` end to end. `int_blocks` (§ 3.6) shares the exact
# same "no capability parent" shape and was already structurally extracted but
# never fed to `assign_codes` either -- same latent gap, just not yet surfaced by
# the validator's family scope. Full end-to-end corpus coverage (real F026
# fixture) lives in test_action_thread_composer.py; these are `assign_codes`'s
# own fallback-loop branches in isolation.
# ---------------------------------------------------------------------------

def _pieces(**overrides) -> ExtractedThreadPieces:
    base = dict(
        preamble="", overview_body="", sysdesign_verbatim={}, endpoints=[],
        endpoints_note="", int_blocks=[], mapping_rows=[], capability_buckets=[],
        verif_body="", source_walkthrough="", db_impact_body="", unknown_h2=[],
        sm_blocks=[], alg_blocks=[],
    )
    base.update(overrides)
    return ExtractedThreadPieces(**base)


def test_assign_codes_sm_block_with_no_applies_to_lands_on_a0():
    """The real-corpus shape: 0 of 62 SM/ALG/INT blocks across the 43-feature
    corpus carry an `Applies to:` field, so this is the common case, not the
    exception -- must claim the code (never leave it absent from `owner`), and
    must never guess a specific action."""
    sm = [ThreadRuleBlock(code="SM-001", heading="### Lifecycle (SM-001)", body="**States:** a, b")]
    owner, _ = assign_codes(_pieces(sm_blocks=sm), actions=[])
    assert owner["SM-001"] == "A0"


def test_assign_codes_alg_and_int_blocks_also_claimed():
    alg = [ThreadRuleBlock(code="ALG-001", heading="### Reconcile (ALG-001)", body="no applies-to here")]
    intb = [ThreadIntBlock(code="INT-001", heading="### Sync (INT-001)", body="no applies-to here",
                            kind="queue-job", target="SyncJob")]
    owner, _ = assign_codes(_pieces(alg_blocks=alg, int_blocks=intb), actions=[])
    assert owner["ALG-001"] == "A0"
    assert owner["INT-001"] == "A0"


def test_assign_codes_sm_block_resolves_to_named_action_when_applies_to_present():
    """Not observed anywhere in the real corpus today, but the fallback must use
    the SAME deterministic resolver as BR/DEC -- a future corpus feature that DOES
    carry an `Applies to:` field on an SM/ALG block must bind to it, not fall back
    to A0 just because this is the fallback path."""
    a2 = ActionRecord(id="A2", handler="Ctrl#update", handler_norm="ctrl#update",
                       handler_class_norm="ctrl", method_norm="update")
    sm = [ThreadRuleBlock(code="SM-001", heading="### Lifecycle (SM-001)",
                           body="**Applies to:** `Ctrl#update`\n**States:** a, b")]
    owner, _ = assign_codes(_pieces(sm_blocks=sm), actions=[a2])
    assert owner["SM-001"] == "A2"


def test_assign_codes_mapping_row_resolution_wins_over_sm_fallback():
    """F011's real shape: SM-001 already has a § 2 mapping-table completeness row
    whose 'Where it is implemented' text resolves to a real handler -- the
    fallback must never override an already-resolved owner (`code in owner:
    continue`), or a currently-correct feature would regress to A0."""
    a9 = ActionRecord(id="A9", handler="ListingsService#approve", handler_norm="listingsservice#approve",
                       handler_class_norm="listingsservice", method_norm="approve")
    mapping_rows = [["SM-001", "Listing moderation lifecycle",
                      "`Admin2::ListingsService#approve`", "—", "—"]]
    sm = [ThreadRuleBlock(code="SM-001", heading="### Lifecycle (SM-001)", body="no applies-to here")]
    owner, _ = assign_codes(_pieces(mapping_rows=mapping_rows, sm_blocks=sm), actions=[a9])
    assert owner["SM-001"] == "A9"


# ---------------------------------------------------------------------------
# Phase 04 (defect 2, plans/260825-1010-rebuild-spec-action-thread-migration-
# defects): `build_action_records`'s DB-Impact FALLBACK path now gates a class
# extraction through `_action_thread_handler_lib.is_job_class` before treating it
# as a real background job -- the INT-block `**Type:** queue-job` path stays
# UNGATED (it already has an explicit source declaration).
# ---------------------------------------------------------------------------

def test_int_block_queue_job_path_is_never_gated_by_is_job_class():
    """Regression guard, not a coincidence-of-current-code test: `SendWelcomeEmail`
    is chosen specifically BECAUSE `is_job_class("SendWelcomeEmail")` is False (it
    ends in "Email", none of Job/Worker/Service/Mailer) -- a real corpus job (F026)
    with no qualifying suffix. This test fails the moment someone "simplifies" by
    routing the INT-block loop through the same `is_job_class` gate the DB-Impact
    fallback uses; the INT block's own declaration is evidence enough on its own."""
    assert is_job_class("SendWelcomeEmail") is False  # the whole premise of this test
    intb = [ThreadIntBlock(code="INT-001", heading="### Welcome (INT-001)",
                            body="no applies-to here", kind="queue-job", target="SendWelcomeEmail")]
    actions = build_action_records(_pieces(int_blocks=intb))
    assert len(actions) == 1
    assert actions[0].handler == "SendWelcomeEmail#perform"
    assert actions[0].is_background is True


def test_db_impact_fallback_drops_http_verb_but_keeps_suffixed_class():
    """Direct unit-level check on the fallback loop itself (complements the
    F002-fixture-level tests in test_action_thread_composer.py): an event naming
    only an HTTP verb becomes a raw, non-background action (the honest
    `action_key_not_handler` shape -- no content dropped, just no invented class
    or queue label); an event naming a real suffixed class is unaffected."""
    db_impact_body = (
        "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
        "|---|---|---|---|---|---|\n"
        "| Any successful sign-in | `people` | x | UPDATE | - | `app/x.rb:1` |\n"
        "| NotifyFollowersJob enqueued (retry) | `listings` | y | UPDATE | - | `app/y.rb:1` |\n"
    )
    actions = build_action_records(_pieces(db_impact_body=db_impact_body))
    by_handler = {a.handler: a for a in actions}
    assert by_handler["Any successful sign-in"].is_background is False
    assert by_handler["NotifyFollowersJob#perform"].is_background is True


def test_db_impact_fallback_dedupes_identical_raw_events_by_key():
    """`ensure_raw`'s norm-key must be the SAME shape `_new` stores under, or two
    DB-Impact rows naming the identical raw event (real corpus shape: F002's
    "Scheduled cleanup" appears twice, against two different tables) silently fork
    into two actions instead of merging their write_tables into one -- duplicating
    an action identity the wire contract treats as singular."""
    db_impact_body = (
        "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
        "|---|---|---|---|---|---|\n"
        "| Scheduled cleanup | `active_sessions` | x | DELETE | - | `app/x.rb:1` |\n"
        "| Scheduled cleanup | `auth_tokens` | y | DELETE | - | `app/y.rb:1` |\n"
    )
    actions = build_action_records(_pieces(db_impact_body=db_impact_body))
    matches = [a for a in actions if a.handler == "Scheduled cleanup"]
    assert len(matches) == 1, f"expected one merged action, got {len(matches)}"
    assert matches[0].write_tables == ["active_sessions", "auth_tokens"]


# ---------------------------------------------------------------------------
# Finding 1 (plans/260825-1010-rebuild-spec-action-thread-migration-defects,
# reports/reviewer-*): `_resolve_db_event`'s `has_bg` branch -- a `(background)`-
# tagged DB-Impact event that names no known handler and no GET/POST+path join
# point falls through to "there is exactly one background action, so it must be
# that one." Phase 04 shrinking the fallback-created background population makes
# this branch's `len(bg) == 1` precondition MORE likely to hold by coincidence,
# and a wrong join here silently attributes one action's DB write to a different,
# unrelated background job. Reviewer-measured on the real 43-feature corpus: this
# branch fires once pre-fix (F011, `ExportListingsJob#perform`) and zero times
# post-fix -- the risk did not materialise, but that measurement was never
# codified. These two tests pin: (a) the branch still fires correctly when the
# shape genuinely calls for it (one real background job, F011's own shape), and
# (b) its `len(bg) == 1` guard -- the ONLY thing standing between an ambiguous
# event and a wrong join -- holds once more than one real background action
# exists. A future `is_job_class` suffix-set change that collapses a real second
# job back down to a raw (non-background) fallback would silently restore the
# preconditions for (b) to misfire; these tests fail the moment that happens
# (confirmed by hand: dropping the `len(bg) == 1` check reproduces exactly a
# wrong join in test (b) -- the ambiguous event's table lands on the WRONG job
# and its own honest raw-fallback action disappears).
# ---------------------------------------------------------------------------

def test_db_impact_background_tag_joins_the_sole_background_action():
    """F011's real shape: one `queue-job` INT block (`ExportListingsJob`) plus a
    `(background)`-tagged DB-Impact event that names neither a known handler
    (no `#`) nor a GET/POST+path join point (`Generate CSV` has no HTTP verb).
    Reaches the `has_bg` branch specifically -- and ONLY that branch: without it,
    `_extract_class_name` would pull `Generate` out of the prose, `is_job_class`
    would reject it (no Job/Worker/Service/Mailer suffix), and the event would
    fall to `ensure_raw` as a SECOND, separate action instead of merging into the
    one real job -- so `len(actions) == 1` below is the branch's fingerprint."""
    intb = [ThreadIntBlock(code="INT-001", heading="### Export (INT-001)",
                            body="no applies-to here", kind="queue-job", target="ExportListingsJob")]
    db_impact_body = (
        "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
        "|---|---|---|---|---|---|\n"
        "| Generate CSV (background) | `export_task_results` | file_file_name | UPDATE | - "
        "| `app/jobs/export_listings_job.rb:22` |\n"
    )
    actions = build_action_records(_pieces(int_blocks=intb, db_impact_body=db_impact_body))
    assert len(actions) == 1, f"expected the background event to merge into the sole job, got {actions}"
    job = actions[0]
    assert job.handler == "ExportListingsJob#perform"
    assert job.write_tables == ["export_task_results"]


def test_db_impact_background_tag_does_not_join_when_multiple_background_actions_exist():
    """Two real, distinct background jobs (two `queue-job` INT blocks) plus one
    `(background)`-tagged event that belongs to NEITHER -- `len(bg) == 2` must
    keep the `has_bg` branch from picking either one; the event has to fall
    through to its own honest raw-fallback action instead of guessing. This is
    exactly the guard a future `is_job_class` suffix-set change could erode: if
    it ever demotes one of these two real jobs back to a non-background raw
    action, `len(bg)` collapses to 1 and this event would silently misjoin onto
    whichever job survived (verified by hand against a deliberately-broken copy
    of `_resolve_db_event` with the `len(bg) == 1` check removed: the event's
    `unrelated_table` write lands on `ExportListingsJob#perform` and its own raw
    action vanishes -- exactly the wrong join this test exists to catch)."""
    intb = [
        ThreadIntBlock(code="INT-001", heading="### A (INT-001)", body="no applies-to here",
                        kind="queue-job", target="ExportListingsJob"),
        ThreadIntBlock(code="INT-002", heading="### B (INT-002)", body="no applies-to here",
                        kind="queue-job", target="CleanupJob"),
    ]
    db_impact_body = (
        "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
        "|---|---|---|---|---|---|\n"
        "| Something happens (background) | `unrelated_table` | x | UPDATE | - | `app/x.rb:1` |\n"
    )
    actions = build_action_records(_pieces(int_blocks=intb, db_impact_body=db_impact_body))
    by_handler = {a.handler: a for a in actions}
    assert by_handler["ExportListingsJob#perform"].write_tables == []
    assert by_handler["CleanupJob#perform"].write_tables == []
    raw = by_handler["Something happens (background)"]
    assert raw.is_background is False
    assert raw.write_tables == ["unrelated_table"]
