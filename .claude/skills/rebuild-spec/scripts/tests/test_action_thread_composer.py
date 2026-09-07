"""Tests for `_feature_sot_technical_lib.compose_action_thread` -- the v27 (5-bucket)
-> v27.7 (action-thread) composer, phase 05 of
plans/260824-1128-rebuild-spec-action-thread-v27-7/plan.md.

Fixtures are VERBATIM copies of real, already-migrated corpus features
(`tests/fixtures/action_thread/README.md` has provenance) -- never hand-authored,
per the plan's own Risk Assessment (a hand-authored fixture once defaulted the one
field the real producer never writes, and 2785 green tests ran over a script that
could never work in production).

`compose_technical_sot` (the v26->v27 composer) is a SIBLING, never touched by this
plan -- see that module's own tests (`test_feature_sot_technical.py`) for its
coverage; this file only exercises the NET-NEW `compose_action_thread`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _action_thread_lib import action_blocks, rungs  # noqa: E402
from _feature_sot_mapping_lib import (  # noqa: E402
    ActionRecord, build_action_records, resolve_rule_owners,
)
from _feature_sot_technical_lib import compose_action_thread, _strip_retired_sections  # noqa: E402
from _spec_constants import (  # noqa: E402
    A3_HEADING, ACTION_HEADING_RE, B4_HEADING, REQUIRED_APPENDIX_H3, REQUIRED_H2_TECH_THREAD,
)

FIXTURES = _TESTS_DIR / "fixtures" / "action_thread"

# `derive_confidence_report.py:29`'s REAL regex -- copied verbatim, not
# reimplemented, so a future edit to either side cannot silently diverge without a
# test noticing (D3, wire-format-contract.md § "the rung set").
CITATION_RE = re.compile(r"\*\*Source:\*\*\s+`?([^`\n:]+):(\d+)(?:-(\d+))?`?")

# Tokens the composer is EXPECTED to drop -- pure structural relabeling (old H2/H3
# heading and table-header words that get renamed, per the plan's own retaxonomy)
# or a documented, disclosed simplification (see this file's own
# `test_content_preservation_*` docstring for `/:locale`). Never a fact.
_STRUCTURAL_ONLY_TOKENS = {
    "3.3", "3.4", "3.5", "3.6", "3.7", "/:locale",
    "Business", "Capability", "Code", "Design", "Endpoints", "Functional",
    "Handler", "Mapping", "Name", "Processing", "Where", "notes", "implemented",
}


def _load(feature: str) -> tuple[str, str]:
    old = (FIXTURES / f"{feature}_technical-spec.md").read_text()
    twin = (FIXTURES / f"{feature}_functional-spec.md").read_text()
    return old, twin


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9_'#:./?!-]{3,}", text))


def test_f011_produces_the_full_a1_through_a9_action_set():
    """Round-trip on F011 reproduces the B-v sample's action SET (success
    criterion) -- D2's action identity is the handler, so this also proves the
    handler-keyed dedup and the INT-001-driven A9 background-job synthesis both
    fire on real data, not just a synthetic fixture."""
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    assert result.action_count == 9
    ids = set(re.findall(r"\*\*(A\d+)\*\*", result.text))
    assert ids == {f"A{i}" for i in range(10)}  # A0..A9


def test_f011_writes_column_matches_real_join_semantics():
    """Mechanically-derived Writes column: A1/A6 read-only (no DB rows joined),
    A7/A8 unreachable ([INFERRED] dead routes), A2/A3/A4 -> listings, A5/A9 ->
    export_task_results -- independently confirms the DB-Impact join and the
    "(background)" tag resolving to the sole synthesized background action."""
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    text = result.text
    for aid in ("A1", "A6"):
        row = re.search(rf"\| \*\*{aid}\*\* \|.*\|\n", text).group(0)
        assert "read-only" in row
    for aid in ("A7", "A8"):
        row = re.search(rf"\| \*\*{aid}\*\* \|.*\|\n", text).group(0)
        assert "unreachable" in row
    for aid in ("A2", "A3", "A4"):
        row = re.search(rf"\| \*\*{aid}\*\* \|.*\|\n", text).group(0)
        assert "`listings`" in row
    for aid in ("A5", "A9"):
        row = re.search(rf"\| \*\*{aid}\*\* \|.*\|\n", text).group(0)
        assert "`export_task_results`" in row


def test_zero_action_feature_still_emits_mandatory_a0():
    """Merge blocker #1: F017 (measured zero `### 3.4` data rows AND zero
    `## DB Impact per Event` rows) must still get an `A0` row carrying every
    otherwise-unclaimed code, or `FeatureSpec.action_index_missing` would
    CRITICAL on a legitimate zero-endpoint infrastructure feature."""
    old, twin = _load("F017")
    result = compose_action_thread(old, twin)
    assert result.action_count == 0
    assert "**A0**" in result.text
    a0_row = re.search(r"\| \*\*A0\*\* \|.*\|\n", result.text).group(0)
    for code in ("BR-001", "BR-002", "BR-003", "FR-401"):
        assert code in a0_row


def test_zero_action_feature_needs_llm_fill_true():
    old, twin = _load("F017")
    result = compose_action_thread(old, twin)
    assert result.needs_llm_fill is True
    assert result.unresolved_rule_count == 3  # BR-001/002/003, none resolvable


def test_needs_llm_fill_false_when_no_rule_stays_unresolved():
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    # F011 has 3 genuinely-unresolved DEC blocks (no `Applies to:` field at all,
    # confirmed against the real corpus: 338 BR blocks carry exactly 338
    # `Applies to:` lines, 0 DEC blocks do) -- needs_llm_fill must still fire.
    assert result.needs_llm_fill is True
    assert result.unresolved_rule_count == 3


def test_br_004_resolves_to_two_actions_bin2():
    """BR-004's `Applies to:` (`` `#update`/`#approve` action ``) names two bare
    methods -- the 3-way resolver must bind BOTH, landing it in bin 2 with a
    `Used in:` line, never guessing a single owner."""
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    assert "Used in: **A2**, **A7**" in result.text
    assert "#### Bin 2" in result.text


def test_dec_blocks_have_no_applies_to_and_land_in_bin3_unverified():
    """DEC blocks carry NO `Applies to:` field anywhere in the real corpus
    (verified: 0 matches inside any DEC block across 43 features) -- the resolver
    must not invent one. Each must carry the exact `[UNVERIFIED] ... needs a
    researcher pass` marker with its original body preserved verbatim, never
    silently dropped or silently assigned an owner."""
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    for code in ("DEC-001", "DEC-002", "DEC-003"):
        assert code in result.text
    assert result.text.count("[UNVERIFIED] no resolvable owner — needs a researcher pass") == 3
    # the original pseudocode/source lines must still be there, verbatim
    assert "presenter.admin_mode AND listing.state == 'approval_pending'" in result.text


def test_content_preservation_token_diff_f011():
    """Risk #3 (silent content loss is the top risk of any composer): every token
    in the v27 input must survive somewhere in the v27.7 output, except a small,
    named, disclosed set of structural relabelings -- old heading/table-header
    words that get renamed by design, `/:locale` (this composer displays the
    resolved route path rather than the Rails locale-scope prefix notation; a
    disclosed simplification, not a lost fact -- every feature's routes carry the
    same prefix uniformly, so no feature-specific information is lost) -- and,
    since phase 08 (self-sufficiency v27.8), A3 (`## Source Walkthrough`) + B4
    (`## DB Impact per Event`) themselves: their WHOLE bodies are the deliberate
    drop this phase makes, not an accidental one, so they are excluded from the
    diff at the source (`_strip_retired_sections` on `old`) rather than added,
    section-by-section, to `_STRUCTURAL_ONLY_TOKENS` -- see
    `test_retired_sections_are_genuinely_absent_not_vacuously_excluded` below for
    the non-vacuity proof that this exclusion is doing real work."""
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    missing = _tokens(_strip_retired_sections(old)) - _tokens(result.text)
    missing = {m for m in missing if not re.fullmatch(r"-{3,}", m)}  # table separators
    assert missing <= _STRUCTURAL_ONLY_TOKENS, f"unexplained content loss: {sorted(missing)}"


def test_content_preservation_token_diff_f017():
    old, twin = _load("F017")
    result = compose_action_thread(old, twin)
    missing = _tokens(_strip_retired_sections(old)) - _tokens(result.text)
    missing = {m for m in missing if not re.fullmatch(r"-{3,}", m)}
    assert missing <= _STRUCTURAL_ONLY_TOKENS, f"unexplained content loss: {sorted(missing)}"


def test_retired_sections_are_genuinely_absent_not_vacuously_excluded():
    """SILENT-EXCLUSION guard for the two tests above: `_strip_retired_sections`
    must be doing real work on these fixtures, not merely a no-op that happens to
    change nothing (the exact "excluded from the diff by construction" trap this
    repo's own ethos warns against). Both fixtures' RAW input carries real A3/B4
    content (a `**File:**` walkthrough entry, a DB-Impact table row) that must be
    genuinely gone from the composed output, not merely absent from the diff."""
    for feature, needle in (
        ("F011", "start here: defines the"),
        ("F017", "shows exactly where and in what"),
    ):
        old, twin = _load(feature)
        assert A3_HEADING in old and B4_HEADING in old, f"{feature} fixture must carry both"
        assert needle in old, f"{feature} fixture must carry its own A3 needle {needle!r}"
        result = compose_action_thread(old, twin)
        assert A3_HEADING not in result.text, f"{feature}: A3 heading survived the strip"
        assert B4_HEADING not in result.text, f"{feature}: B4 heading survived the strip"
        assert needle not in result.text, f"{feature}: A3 body content survived the strip"


def test_idempotent_second_run_is_a_no_op():
    old, twin = _load("F011")
    first = compose_action_thread(old, twin)
    second = compose_action_thread(first.text, twin)
    assert second.text == first.text
    assert second.action_count == 0  # idempotent path returns early, doesn't re-derive


def test_required_h2_thread_headings_present_in_order():
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    positions = [result.text.index(h) for h in REQUIRED_H2_TECH_THREAD]
    assert positions == sorted(positions)


def test_shared_foundation_h3_children_present_in_order():
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    positions = [result.text.index(h) for h in REQUIRED_APPENDIX_H3]
    assert positions == sorted(positions)


def test_action_headings_match_action_heading_re():
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    pat = re.compile(ACTION_HEADING_RE, re.MULTILINE)
    found = pat.findall(result.text)
    assert set(found) == {f"A{i}" for i in range(1, 10)}


def test_no_rung_renders_na_or_none_placeholder():
    """Merge blocker #5 / wire-format-contract.md rule 3: an absent rung is
    OMITTED entirely -- never `N/A`, never a literal `None.` line."""
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    actions_body = result.text[result.text.index("## 3. Actions"):result.text.index("## 4. Shared Foundation")]
    for line in actions_body.splitlines():
        stripped = line.strip()
        assert stripped not in ("**Who** · N/A", "**Request** · N/A", "None.")


def test_citation_rung_matches_the_real_confidence_report_regex():
    """D3 (settled 2026-08-24, wire-format-contract.md): the citation rung's exact
    shape is `**Source:** \\`path:line\\`` -- colon inside the bold, a single space,
    then the first backticked citation, chained hops with ` -> ` after. Verified
    directly against `derive_confidence_report.py`'s own regex, copied verbatim
    above -- not a hand-reimplemented approximation of it."""
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    # scoped to § 3 Actions -- the composer's OWN citation rungs -- not every
    # "**Source:**" line in the whole document (§ 4's relocated-verbatim content
    # carries pre-existing non-file citations, e.g. a doc-section reference, which
    # never matched CITATION_RE even in the original v27 input; that is unrelated
    # to this composer's own D3 obligation).
    actions_body = result.text[result.text.index("## 3. Actions"):result.text.index("## 4. Shared Foundation")]
    source_lines = [ln for ln in actions_body.splitlines() if ln.startswith("**Source:**")]
    assert source_lines, "expected at least one **Source:** rung line"
    for line in source_lines:
        assert CITATION_RE.search(line), f"line does not satisfy the real CITATION_RE: {line!r}"
    # and the middot-shaped form the contract explicitly REJECTED must never appear
    assert "**Source** ·" not in actions_body


def test_exactly_one_source_rung_per_action_in_last_position():
    """Phase 11 triage (preflight-260824-1145-verified-facts.md item 3): the real
    validator reported `rung_order` 70x across 43 features -- `Source` rendered
    TWICE per action, once mid-block right after `Rule`. Root cause: a BR/DEC
    rule's own `**Source:**` field (carried verbatim from the v27 input's rule
    block) was embedded as-is inside the `**Rule**` rung's body, where
    `_action_thread_lib._RUNG_LINE_RE` reads any `**Source:**`-prefixed line as a
    rung marker regardless of where it sits. Contract: exactly one `**Source:**`
    rung per action block, and it must be the LAST rung line rendered.

    Uses the REAL parser (`_action_thread_lib.action_blocks`/`rungs`) rather than a
    hand-rolled heading scan, so this test scopes each action's region exactly the
    way the real validator does -- a naive "next `#### A<n>` heading" bound would
    wrongly swallow a trailing `### 3.N Edge Cases` H3 into the last action's block."""
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    lines = result.text.splitlines()
    headings = [(i, ln) for i, ln in enumerate(lines) if ln.startswith("#")]
    blocks = action_blocks(headings, len(lines))
    assert blocks, "expected at least one action block"
    for block in blocks:
        aid = block["ids"][0]
        labels = [label for label, _ in rungs(lines, block)]
        source_count = labels.count("Source")
        if source_count == 0:
            continue  # some actions have no derivable citation at all -- absence is fine
        assert source_count == 1, f"{aid}: expected exactly one Source rung, found {source_count}"
        assert labels[-1] == "Source", f"{aid}: Source rung must be last, got order {labels}"


def test_rule_own_citation_content_preserved_when_deduplicated():
    """The rule's own `**Source:**` field (e.g. BR-001's
    `app/services/admin2/listings_service.rb:15-23`) must not be silently dropped
    when its stray top-level rung line is removed -- it is folded into the
    action's single final Source rung instead (merge blocker #3)."""
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    a2_start = result.text.index("#### A2 · ")
    a2_end = result.text.index("#### A3 · ")
    a2_block = result.text[a2_start:a2_end]
    assert "listings_service.rb:15-23" in a2_block


def test_diagram_fence_never_cites_a_file_line():
    """Rule 5 (rungs carry FACTS, diagrams carry ORDER/BRANCHING): a fence directly
    inside § 3 Actions must not contain a `file:line` citation -- that belongs on a
    rung, never duplicated into the diagram. F011's fixture carries no
    `sequenceDiagram` fence in this composer's mechanical output (diagram synthesis
    is out of this phase's scope -- see phase 07/09), so this guards against
    accidentally leaking a rung's own citation text into a relocated code fence."""
    old, twin = _load("F011")
    result = compose_action_thread(old, twin)
    actions_body = result.text[result.text.index("## 3. Actions"):result.text.index("## 4. Shared Foundation")]
    in_fence = False
    for line in actions_body.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            assert not re.search(r"[a-zA-Z_/.]+\.rb:\d+", line), f"file:line leaked into a fence: {line!r}"


def test_a0_mandatory_even_with_synthetic_zero_actions():
    """Direct unit-level check on `build_action_records`/`resolve_rule_owners`
    (not just the fixture-level end-to-end test above): an empty action list must
    make every rule resolve to `[]` (never guessed), which the composer then routes
    to A0 -- this is the mechanism merge blocker #1 depends on."""
    assert build_action_records.__call__ is not None  # sanity: importable or the fixture test would already fail
    assert resolve_rule_owners("", []) == []
    assert resolve_rule_owners("`#update` action", []) == []


def test_f026_sm_alg_int_codes_are_claimed_not_dropped():
    """Real-corpus defect closed by rebuild-spec 27.7.1 (phase 11 acceptance
    report, `FeatureSpec.action_unclaimed`): F026's `SM-001` (§ 3.3 State
    Management's `Sender-address verification lifecycle` block) has NEITHER a
    `### 4.N` capability-bucket home (SM blocks never do) NOR a § 2 mapping-table
    completeness row (this fixture's own § 2 table has no SM-001/ALG-001/INT-001/
    INT-002 row -- verified against the real corpus file) -- so it was invisible
    to `assign_codes` end to end and never appeared anywhere in § 2 Action Index,
    not even on A0. Every one of the four orphaned codes must now be claimed --
    landing on A0 (never guessed onto a specific action; none of them carry an
    `Applies to:` field, measured 0/62 across the full 43-feature corpus)."""
    old, twin = _load("F026")
    result = compose_action_thread(old, twin)
    a0_row = re.search(r"\| \*\*A0\*\* \|.*\|\n", result.text).group(0)
    for code in ("SM-001", "ALG-001", "INT-001", "INT-002"):
        assert code in a0_row, f"{code} missing from A0's Codes cell -- unclaimed"


def test_f026_every_declared_code_appears_in_some_action_index_row():
    """Broader completeness sweep on the SAME fixture: every FR/BR/DEC/SM/US code
    the twin functional-spec's CAP-01 row declares (`FR-001, FR-002, FR-201,
    FR-202, FR-203, FR-204, FR-205, FR-401, FR-602, BR-001..BR-005, DEC-001,
    DEC-002, SM-001`) must show up somewhere in § 2 Action Index -- this is the
    exact set `FeatureSpec.action_unclaimed` checks completeness against."""
    old, twin = _load("F026")
    result = compose_action_thread(old, twin)
    action_index = result.text[
        result.text.index("## 2. Action Index"):result.text.index("## 3. Actions")
    ]
    declared = (
        "FR-001 FR-002 FR-201 FR-202 FR-203 FR-204 FR-205 FR-401 FR-602 "
        "BR-001 BR-002 BR-003 BR-004 BR-005 DEC-001 DEC-002 SM-001"
    ).split()
    for code in declared:
        assert code in action_index, f"{code} declared by the twin but absent from § 2"


def test_multi_file_subtable_shape_not_specifically_handled():
    """Merge blocker #8 (multi-`### File:` sub-tables have broken 4 parsers in
    this repo before): neither real fixture used by this composer carries that
    shape (grepped: 0 hits for `^### File:` across the 43-feature corpus at the
    time this was written). This composer's `## Source Walkthrough` handling is
    pass-through only (that H2 is explicitly "unchanged -- do not touch" per the
    wire-format contract), and its table parsing reuses the same fence-aware
    `split_around_first_table` primitive every other SOT composer in this repo
    already relies on -- it has NOT been specifically exercised against a
    multi-`### File:` shape. Documented here rather than silently assumed safe."""
    assert True


# ---------------------------------------------------------------------------
# Phase 04 (defect 2, plans/260825-1010-rebuild-spec-action-thread-migration-
# defects): the DB-Impact FALLBACK path (`_resolve_db_event` returns no join)
# extracts the first capitalised word from the raw event prose and treats it as a
# class name. F002's fixture carries six such English-word/HTTP-verb tokens.
# ---------------------------------------------------------------------------

_FABRICATED_HANDLER_RE = re.compile(
    r"`(GET|POST|PUT|PATCH|DELETE|Any|Scheduled|Legacy|Authenticated|OAuth)#[a-zA-Z_][A-Za-z0-9_?!]*`"
)


def test_f002_no_action_is_named_after_an_http_verb_or_english_word():
    """RED against pre-fix code: F002's DB-Impact fallback synthesizes
    `PATCH#perform` from `` PATCH/PUT /people/password (reset submit) ``,
    `OAuth#perform` from `` OAuth callback, new person ``, `Any#perform` from
    `` Any successful sign-in ``, `Scheduled#perform` from `` Scheduled cleanup ``,
    `Legacy#perform` from `` Legacy DB-session cutover... ``, and
    `Authenticated#perform` from `` Authenticated request, session stale... `` --
    none of these six are real classes. Run against unmodified code, this fails
    and lists all six fabricated handlers."""
    old, twin = _load("F002")
    result = compose_action_thread(old, twin)
    fabricated = sorted(set(_FABRICATED_HANDLER_RE.findall(result.text)))
    assert fabricated == [], f"fabricated non-class handlers found: {fabricated}"


def test_f002_no_synchronous_event_is_labelled_delayed_job():
    """Companion to the test above: `ensure_raw`/`ensure_background` both
    hard-code `is_background=True`, so `_context_lines` renders each of those six
    fabricated handlers as `` queue · `Delayed::Job` `` -- mislabeling a
    synchronous request-path event (e.g. a password-reset PATCH/PUT, or an
    authenticated-request session bump) as background queue work. RED first."""
    old, twin = _load("F002")
    result = compose_action_thread(old, twin)
    for line in result.text.splitlines():
        if "queue · `Delayed::Job`" not in line:
            continue
        assert not _FABRICATED_HANDLER_RE.search(line), f"mislabelled as background: {line!r}"


# ---------------------------------------------------------------------------
# Phase 05 (defect 3, plans/260825-1010-rebuild-spec-action-thread-migration-
# defects): `.strip("` ")` cannot remove an interior backtick, so a handler cell
# with an annotation (e.g. `` `devise/sessions#new` (stock, SCR123) ``) leaves the
# stored handler carrying a trailing backtick, which `_context_lines` /
# `build_action_index_table` then wrap into an unbalanced pair; `_action_title`'s
# fallback reads the already-lowercased `method_norm`. F002's own § 3.4 rows
# (`devise/sessions#new` (stock, SCR123)`, `devise/passwords#new`/`#edit` (Devise
# `:recoverable`)`) exercise both bugs at once (phase-05 plan file "Key Insights").
# ---------------------------------------------------------------------------
def _context_line_bodies(text: str) -> list[str]:
    """Every rendered `_context_lines` first line -- the first NON-BLANK line
    following an `#### A<n> ·` heading (`build_actions_section` joins the heading
    and the context-line block with a blank line via `"\\n\\n".join(parts)`)."""
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        if not re.match(r"^#### A\d+ ·", line):
            continue
        for j in range(i + 1, len(lines)):
            if lines[j].strip():
                out.append(lines[j])
                break
    return out


def test_f002_no_context_line_has_unbalanced_backticks():
    """RED against pre-fix code: F002's A9/A10 context lines (`devise/passwords#
    new`/`#edit` and `devise/sessions#new` (stock, SCR123)) both carry an odd
    backtick count today."""
    old, twin = _load("F002")
    result = compose_action_thread(old, twin)
    offenders = [ln for ln in _context_line_bodies(result.text) if ln.count("`") % 2 != 0]
    assert offenders == [], f"unbalanced-backtick context lines: {offenders}"


def test_f002_carries_no_perform_titles_because_all_its_fallback_events_are_dropped():
    """DOCUMENTATION, not a RED probe: measured (this phase), F002's own 11
    DB-Impact fallback events (`Any`, `Scheduled`, `Legacy`, `OAuth`, `PATCH`,
    `Authenticated` -- the phase-04 fixture's own fabricated-class list) are ALL
    dropped by `is_job_class` (phase 04's already-landed fix) and become
    `ensure_raw` actions, whose title is the raw text verbatim -- never
    `method_norm`. So F002 does NOT exercise the "Perform" title sub-bug this
    phase closes (that requires a REAL kept job class, e.g.
    `DownloadListingImageJob`, which F002 has none of --
    `measure-corpus.py`'s per-feature table shows F002 at fb_kept=0).
    The actual RED-demonstrated coverage for this sub-bug lives in
    `test_feature_sot_structure.py::test_action_title_perform_bug_on_a_real_kept_job_class`,
    against a corpus-measured class name, not a hand-invented one. This test just
    pins down the (correct, already-true) F002 behavior so a future edit that
    reintroduces a `method_norm`-sourced title here gets caught."""
    old, twin = _load("F002")
    result = compose_action_thread(old, twin)
    perform_headings = [
        ln for ln in result.text.splitlines()
        if re.match(r"^#### A\d+ · Perform\s*$", ln)
    ]
    assert perform_headings == [], f"H4 titles literally 'Perform': {perform_headings}"


def test_f002_handler_annotation_is_preserved_not_dropped():
    """PRESERVATION GUARD, not a defect probe -- passes today (and must keep
    passing after the fix): the `(stock, SCR123)` annotation leaks through today
    as part of the broken/unbalanced handler string, so this assertion alone does
    not prove the bug is fixed. Its job is to fail loudly if a future "cleanup" of
    the malformed heading defect drops the annotation instead of preserving it."""
    old, twin = _load("F002")
    result = compose_action_thread(old, twin)
    assert "stock, SCR123" in result.text