"""Tests for `_action_thread_handler_lib.is_job_class` -- phase 04 (defect 2,
plans/260825-1010-rebuild-spec-action-thread-migration-defects). The 11-keep/
64-drop cases below are the real 43-feature sharetribe corpus's fallback-path
class-name extractions (`_feature_sot_mapping_lib._extract_class_name` applied to
a `## DB Impact per Event` cell `_resolve_db_event` could not join), not
hand-invented examples -- see the phase file's "Key Insights" table for the full
corpus breakdown this module's own docstring restates.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _action_thread_handler_lib import is_job_class  # noqa: E402

# The 11 real classes kept from the fallback path, corpus-measured (repeats
# collapsed -- `is_job_class` is a pure per-token predicate, count doesn't matter).
_KEPT_REAL_CLASSES = [
    "CommunityMailer",
    "DownloadListingImageJob",
    "StripePayoutJob",
    "CreateMemberEmailBatchJob",
    "CreateSquareImagesJob",
    "PageLoadedJob",
    "ReprocessListingImageJob",
    "PersonMailer",
]

# The 64 non-classes dropped from the fallback path, corpus-measured (repeats
# collapsed to their distinct tokens).
_DROPPED_NON_CLASSES = [
    "PATCH", "DELETE", "POST", "Any", "OAuth", "PUT", "Scheduled", "Admin", "GET",
    "Authenticated", "Legacy", "Accept", "Reject", "Confirm", "Cancel", "PayPal",
    "Commission", "Email", "Add", "N", "All",
]


@pytest.mark.parametrize("token", _KEPT_REAL_CLASSES)
def test_real_job_classes_are_kept(token):
    assert is_job_class(token) is True


@pytest.mark.parametrize("token", _DROPPED_NON_CLASSES)
def test_non_class_tokens_are_dropped(token):
    assert is_job_class(token) is False


def test_delayed_colon_colon_job_kept_via_the_namespace_arm():
    """`Delayed::Job` (the INT-block's own literal queue name, also occasionally
    the DB-Impact fallback's extraction) is the corpus's one `::`-namespaced
    token -- kept via the `::` arm, not the suffix arm (it has no Job/Worker/
    Service/Mailer-ending FINAL segment: `_class_basename` -> `Job`, which DOES
    end in `Job` too, so this also confirms the two arms agree here, not just
    that one of them fires)."""
    assert is_job_class("Delayed::Job") is True


@pytest.mark.parametrize("token", ["ExportTaskResult", "SessionContextSerializer", "OAuth"])
def test_near_misses_are_rejected(token):
    """Three tokens shaped closely enough to a real job class to be worth an
    explicit regression guard: `ExportTaskResult` (ends in "Result", not one of
    the four suffixes -- a real corpus MODEL name, not a job), and
    `SessionContextSerializer` (ends in "Serializer" -- a real corpus class, but
    not a background-job-shaped one). `OAuth` also lives in `_DROPPED_NON_CLASSES`
    above; restated here because it is the specific case the rejected "internal
    uppercase hump" candidate predicate would have wrongly accepted (O, A) --
    this guards against that regression path specifically, not just "OAuth is
    dropped" in general."""
    assert is_job_class(token) is False


def test_empty_and_falsy_input_is_never_a_job_class():
    assert is_job_class("") is False


# ---------------------------------------------------------------------------
# Phase 05 (defect 3) -- `parse_handler_cell` / `render_handler`. Cases are the
# real corpus's own four measured handler-cell shapes (phase-05 plan file "Key
# Insights"), not hand-invented text.
# ---------------------------------------------------------------------------
from _action_thread_handler_lib import (  # noqa: E402
    humanize_class, humanize_method, parse_handler_cell, render_handler, sanitize_title,
)

# F002_AuthenticationAndSession technical-spec.md.bak:148
_HANDLER_PLUS_PARENTHETICAL = "`devise/sessions#new` (stock, SCR123)"
# F002_AuthenticationAndSession technical-spec.md.bak:147
_COMPOUND_HANDLER_WITH_BACKTICKED_ANNOTATION = "`devise/passwords#new`/`#edit` (Devise `:recoverable`)"
# F002_AuthenticationAndSession technical-spec.md.bak:145
_COMPOUND_HANDLER_BARE = "`OmniauthController#:provider`/`#create_omniauth`"
# F008_MessagingAndInbox technical-spec.md.bak:129
_HANDLER_PLUS_UNVERIFIED_NOTE = (
    "`ConversationsController#create` — [UNVERIFIED — see RISK-01, not implemented]"
)
# F043_DeprecatedLegacyAdminConsole technical-spec.md.bak:99
_NO_HANDLER_PROSE_ONLY = "*(no route declared)*"


def test_bare_handler_no_annotation():
    assert parse_handler_cell("`LandingPageController#index`") == ("LandingPageController#index", "")


def test_handler_plus_plain_parenthetical_annotation():
    handler, annotation = parse_handler_cell(_HANDLER_PLUS_PARENTHETICAL)
    assert handler == "devise/sessions#new"
    assert annotation == "(stock, SCR123)"


def test_compound_handler_takes_first_span_second_span_stays_in_annotation():
    """Acknowledged partial win (function docstring): only the FIRST backticked
    span becomes the identity. The second span is not dropped -- it survives
    inside the annotation, still backtick-wrapped, so nothing is lost even
    though only one handler is modelled."""
    handler, annotation = parse_handler_cell(_COMPOUND_HANDLER_BARE)
    assert handler == "OmniauthController#:provider"
    assert "#create_omniauth" in annotation


def test_annotation_containing_its_own_backticks_is_preserved_verbatim():
    handler, annotation = parse_handler_cell(_COMPOUND_HANDLER_WITH_BACKTICKED_ANNOTATION)
    assert handler == "devise/passwords#new"
    assert "#edit" in annotation
    assert ":recoverable" in annotation


def test_bracketed_unverified_note_is_preserved_not_dropped():
    handler, annotation = parse_handler_cell(_HANDLER_PLUS_UNVERIFIED_NOTE)
    assert handler == "ConversationsController#create"
    assert annotation == "[UNVERIFIED — see RISK-01, not implemented]"


def test_no_backtick_span_returns_empty_handler_and_the_prose_verbatim():
    assert parse_handler_cell(_NO_HANDLER_PROSE_ONLY) == ("", _NO_HANDLER_PROSE_ONLY)


@pytest.mark.parametrize(
    "raw",
    [
        _HANDLER_PLUS_PARENTHETICAL,
        _COMPOUND_HANDLER_WITH_BACKTICKED_ANNOTATION,
        _COMPOUND_HANDLER_BARE,
        _HANDLER_PLUS_UNVERIFIED_NOTE,
        "`LandingPageController#index`",
    ],
)
def test_render_handler_output_is_always_backtick_balanced(raw):
    handler, annotation = parse_handler_cell(raw)
    rendered = render_handler(handler, annotation)
    assert rendered.count("`") % 2 == 0, f"unbalanced: {rendered!r}"


def test_render_handler_matches_the_contract_example_exactly():
    """wire-format-contract.md § 2's own italic-suffix shape
    (`*(background, no FE)*`) applied to a real annotation."""
    handler, annotation = parse_handler_cell(_HANDLER_PLUS_PARENTHETICAL)
    assert render_handler(handler, annotation) == "`devise/sessions#new` *(stock, SCR123)*"


def test_render_handler_with_no_annotation_is_just_the_backticked_handler():
    assert render_handler("LandingPageController#index", "") == "`LandingPageController#index`"


def test_render_handler_with_no_handler_renders_the_annotation_alone():
    """No double-wrapping: `` `*(no route declared)*` `` would mangle already-
    formatted prose the source cell already carries."""
    handler, annotation = parse_handler_cell(_NO_HANDLER_PROSE_ONLY)
    assert render_handler(handler, annotation) == _NO_HANDLER_PROSE_ONLY


def test_unverified_tag_count_is_unchanged_by_parse_and_render():
    """Risk Assessment: the annotation carrying `[UNVERIFIED -- ...]` must not
    shift the tag count a downstream rollback-refusal predicate reads -- the tag
    was already in the raw cell before this phase, so parsing+rendering it must
    neither drop it nor duplicate it."""
    handler, annotation = parse_handler_cell(_HANDLER_PLUS_UNVERIFIED_NOTE)
    rendered = render_handler(handler, annotation)
    assert _HANDLER_PLUS_UNVERIFIED_NOTE.count("[UNVERIFIED") == 1
    assert rendered.count("[UNVERIFIED") == 1


# ---------------------------------------------------------------------------
# Phase 05 (defect 3) -- `humanize_method` / `humanize_class` / `sanitize_title`.
# ---------------------------------------------------------------------------
def test_humanize_method_snake_case():
    assert humanize_method("new") == "New"
    assert humanize_method("create_domain_setup") == "Create domain setup"


def test_humanize_method_strips_leading_colon():
    # F002 technical-spec.md.bak:145's `:provider` handler-path segment.
    assert humanize_method(":provider") == "Provider"


def test_humanize_method_case_preserving_camel_split():
    """The exact fixture phase 05 uses to rewrite the two hollow `_action_title`
    tests (test_feature_sot_structure.py) -- proves case survives, unlike
    `method_norm` which is lowercased at construction."""
    assert humanize_method("NewSession") == "New session"


def test_humanize_class_drops_job_suffix():
    # Real corpus class (phase 04's own kept-class list).
    assert humanize_class("DownloadListingImageJob") == "Download listing image"
    assert humanize_class("NotifyFollowersJob") == "Notify followers"


def test_humanize_class_namespaced_basename_only():
    assert humanize_class("Delayed::Job") == "Job"


def test_humanize_class_single_word_suffix_is_not_emptied():
    assert humanize_class("Job") == "Job"


def test_sanitize_title_neutralises_bare_action_id_token():
    assert sanitize_title("Any A12 retry") == "Any A 12 retry"


def test_sanitize_title_neutralises_second_action_marker():
    assert sanitize_title("A10 · second") == "A 10 - second"


def test_sanitize_title_leaves_ordinary_text_untouched():
    assert sanitize_title("Approve a pending listing") == "Approve a pending listing"


def test_sanitize_title_prevents_action_blocks_from_extracting_a_phantom_id():
    """Requirement 6 / step 8: assert against the REAL `action_blocks`, not a
    regex copy of `ACTION_ID_RE` -- a raw title containing a bare `A12` token
    must not let the fill-pass dispatch set believe a second action (`A12`) is
    present in this heading."""
    from _action_thread_lib import action_blocks

    unsafe_heading = "#### A1 · Any A12 retry"
    safe_heading = f"#### A1 · {sanitize_title('Any A12 retry')}"
    unsafe_blocks = action_blocks([(4, unsafe_heading)], total=1)
    safe_blocks = action_blocks([(4, safe_heading)], total=1)
    assert "A12" in unsafe_blocks[0]["ids"], "fixture no longer demonstrates the hazard"
    assert "A12" not in safe_blocks[0]["ids"]
    assert safe_blocks[0]["ids"] == ["A1"]
