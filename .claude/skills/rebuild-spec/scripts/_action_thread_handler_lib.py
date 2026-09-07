"""Action-thread handler helpers shared by `_feature_sot_mapping_lib.py` and (phase
05) `_feature_sot_structure_lib.py`. New module rather than growing either sibling
further -- both are already near/at the repo's 200-line guidance
(development-rules.md "Consider Modularization").

Phase 04 (defect 2, plans/260825-1010-rebuild-spec-action-thread-migration-defects)
seeds this module with `is_job_class`. Phase 05 (defect 3, same plan) extends it
with `parse_handler_cell`/`render_handler` (a handler cell's backticked span and
its trailing annotation, parsed and rendered by exactly one shared pair of
functions so `_context_lines` and `build_action_index_table` can never disagree)
and `humanize_method`/`humanize_class`/`sanitize_title` (the `_action_title`
ladder's building blocks -- see that function's own docstring in
`_feature_sot_structure_lib.py` for the ladder itself).
"""
from __future__ import annotations

import re

# Measured against the real 43-feature sharetribe corpus (phase 04 baseline): of
# the 75 class-name tokens `_feature_sot_mapping_lib._extract_class_name` pulled
# from the DB-Impact FALLBACK path (i.e. `_resolve_db_event` found no join), this
# predicate keeps exactly the 11 real classes and drops exactly the 64 that are not
# classes at all -- zero false positives, zero false negatives:
#
#   KEPT (11): CommunityMailer x3, DownloadListingImageJob x2, StripePayoutJob,
#   CreateMemberEmailBatchJob, CreateSquareImagesJob, PageLoadedJob,
#   ReprocessListingImageJob, PersonMailer
#
#   DROPPED (64): PATCH x11, DELETE x11, POST x8, Any x5, OAuth x4, PUT x4,
#   Scheduled x3, Admin x3, GET x3, Authenticated, Legacy, Accept, Reject, Confirm,
#   Cancel, PayPal, Commission, Email, Add, N, All
#
# Two weaker candidates were measured and rejected (see phase-04's plan file "Key
# Insights" for the corpus evidence): "an internal second uppercase hump" accepts
# `OAuth` (a false positive); "must have been backticked in the source" drops real
# jobs the corpus states unbackticked. Widening this set is a decision that needs a
# number attached, not a guess -- see the module docstring above.
_JOB_SUFFIXES = ("Job", "Worker", "Service", "Mailer")


def is_job_class(token: str) -> bool:
    """True when *token* plausibly names a real background-job/service/mailer
    class, not an English word or HTTP verb the DB-Impact fallback path
    mis-extracted from prose.

    The predicate: *token* contains a Ruby namespace separator (`::`, e.g.
    `Delayed::Job`), OR its final CamelCase segment (after the last `::`) ends in
    one of Job/Worker/Service/Mailer.

    ONLY for the DB-Impact FALLBACK path
    (`_feature_sot_mapping_lib.build_action_records`'s `## DB Impact per Event`
    loop, when `_resolve_db_event` returns no join). Never apply this to the
    INT-block `**Type:** queue-job` path -- that path is already gated by an
    explicit source declaration ("this is a job") and legitimately names real jobs
    with none of these suffixes (e.g. `SendWelcomeEmail`); filtering it through this
    predicate would silently drop them.
    """
    if not token:
        return False
    if "::" in token:
        return True
    final_segment = token.rsplit("::", 1)[-1]
    return final_segment.endswith(_JOB_SUFFIXES)


# ---------------------------------------------------------------------------
# Phase 05 (defect 3) -- handler cell parsing/rendering.
# ---------------------------------------------------------------------------
_HANDLER_SPAN_RE = re.compile(r"`([^`]+)`")


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_handler_cell(raw: str) -> tuple[str, str]:
    """`(handler, annotation)` from a `### 3.4 API & Endpoints` Handler cell.

    The handler is the FIRST backticked span; the annotation is everything else
    in the cell, whitespace-normalised, with a leading `-`/`--`/`--`-style
    connector stripped (it is punctuation joining the two clauses, not content).
    A cell with no backticked span at all returns `("", raw.strip())` -- no
    handler; the caller (`_ActionBuilder.from_endpoint`) then has nothing to
    treat as a `Class#method` identity for this row.

    Measured against all 43 `.bak` corpus features (phase 05's Key Insights):
    four shapes. Three are lossless and correct: a bare handler (no annotation);
    handler + plain-text parenthetical (`` `devise/sessions#new` (stock,
    SCR123) ``); handler + a `[UNVERIFIED -- ...]` bracketed note. The fourth, a
    COMPOUND handler (two backticked spans, e.g. `` `#new`/`#create` ``), is an
    ACKNOWLEDGED PARTIAL WIN: only the first span becomes the identity; the
    second stays inside the annotation string verbatim (still backtick-wrapped,
    so `render_handler`'s output stays balanced) rather than being silently
    dropped or silently promoted to a second action. Widening this to model both
    handlers is future work with its own measured cost, not a guess made here.
    """
    text = raw.strip()
    m = _HANDLER_SPAN_RE.search(text)
    if not m:
        return "", _normalize_ws(text)
    handler = m.group(1).strip()
    remainder = _normalize_ws(text[: m.start()] + text[m.end() :])
    remainder = remainder.lstrip("-–— ").strip()
    return handler, remainder


def render_handler(handler: str, annotation: str = "") -> str:
    """The one shared rendering of a parsed handler cell -- `_context_lines`
    (§ 3 context line) and `build_action_index_table` (§ 2 index cell) both call
    this rather than each formatting a handler string independently, so the two
    surfaces can never disagree (phase 05 requirement 2, DRY).

    `handler` backtick-wrapped, `annotation` (if any) appended verbatim inside a
    single italic span: `` `devise/sessions#new` *(stock, SCR123)* `` -- the
    same italic-suffix shape the wire-format contract already sanctions for
    `*(background, no FE)*`. `handler=""` (the no-backtick-span shape) renders
    the annotation alone, un-wrapped -- it is usually already-formatted prose
    (e.g. `*(no route declared)*`), and double-wrapping it would mangle it, not
    clarify it."""
    if not handler:
        return annotation
    rendered = f"`{handler}`"
    return f"{rendered} *{annotation}*" if annotation else rendered


# ---------------------------------------------------------------------------
# Phase 05 (defect 3) -- `_action_title` ladder building blocks. `method_norm`
# is lowercased at construction (`_ActionBuilder._new`) and cannot recover case;
# these two humanize the case-preserving `handler`/class strings instead.
# ---------------------------------------------------------------------------
_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_CLASS_WORD_RE = re.compile(r"[A-Z][a-z0-9]*|[A-Z]+(?![a-z])")
_CLASS_DROP_SUFFIXES = ("Job", "Worker")


def _title_case_first(words: list[str]) -> str:
    if not words:
        return ""
    out = [words[0][:1].upper() + words[0][1:]]
    out += [w[:1].lower() + w[1:] if w else w for w in words[1:]]
    return " ".join(out)


def humanize_method(method: str) -> str:
    """A handler's method segment, case-preserving: `new` -> `New`;
    `create_domain_setup` -> `Create domain setup`; `:provider` -> `Provider`;
    `NewSession` -> `New session` (CamelCase split too -- the corpus is
    overwhelmingly snake_case Rails actions, but nothing guarantees it always
    will be, and this is exactly the case-preservation this phase exists for)."""
    text = method.lstrip(":").replace("_", " ")
    text = _CAMEL_BOUNDARY_RE.sub(" ", text)
    words = _normalize_ws(text).split(" ") if text.strip() else []
    return _title_case_first(words)


def humanize_class(cls: str) -> str:
    """A background action's class basename, case-preserving, with a trailing
    `Job`/`Worker` segment dropped: `NotifyFollowersJob` -> `Notify followers`;
    `Delayed::Job` -> `Job` (a single-word basename is never emptied by the
    drop -- there is nothing left to fall back to)."""
    basename = cls.rsplit("::", 1)[-1]
    words = _CLASS_WORD_RE.findall(basename)
    if len(words) > 1 and words[-1] in _CLASS_DROP_SUFFIXES:
        words = words[:-1]
    return _title_case_first(words) if words else basename


_BARE_ACTION_ID_RE = re.compile(r"\bA(\d+)(?!\d)")
_SECOND_ACTION_MARKER_RE = re.compile(r"\s*·\s*")


def sanitize_title(text: str) -> str:
    """Neutralises the two tokens `_action_thread_lib.action_blocks` scans a
    WHOLE heading line for (not just the anchored leading id
    `ACTION_HEADING_RE` itself captures): a bare `A<digits>` token, which would
    forge a phantom action id (`A12` -> `A 12`), and a ` · ` sequence, which
    would forge a second-action marker (`` -> ` - `). Applied to every title
    from every rung of the `_action_title` ladder, not just the raw-fallback
    rung -- an FR/US code's own declared name could in principle carry either
    token too. Measured today: zero corpus titles contain either; this closes
    the hazard before it lands, not after."""
    text = _BARE_ACTION_ID_RE.sub(lambda m: f"A {m.group(1)}", text)
    return _SECOND_ACTION_MARKER_RE.sub(" - ", text)
