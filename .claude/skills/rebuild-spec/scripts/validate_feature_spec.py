#!/usr/bin/env python3
"""Wave 6.5 — feature spec structural validator.
Checks `spec.md` files against verification-checklist.md FeatureSpec rules.
Regex + fence-state tracking; stdlib only.
Exit codes: 0 (no critical), 1 (critical), 2 (internal).
"""
# layout-exempt: rebuild-spec script — all docs/system|features|generated|flows paths are this skill's own managed targets
from __future__ import annotations
import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _slug_lib import (  # noqa: E402
    FEATURE_FILES, assert_under, iter_docs_technical_specs, iter_feature_dirs,
    iter_technical_specs, read_authored_by, read_spec_status, resolve_project_root,
)
from _spec_parse import parse_headings_and_blocks, strip_html_comments  # noqa: E402
from _spec_block_lib import (  # noqa: E402
    BLOCK_HEADING_PREFIX_RE, DEC_BLOCK_RE, LEGACY_BLOCK_HEADING_RE, SM_BLOCK_RE,
    find_blocks_missing_linked_fr,
)
from _file_schema_lib import has_populated_file_schema, is_file_exchange  # noqa: E402
from _summary_lib import (  # noqa: E402
    atomic_write, derive_overall_status, load_summary, merge_validator_result, recalculate_totals,
)
from _spec_constants import (  # noqa: E402
    A3_HEADING, ACTION_ID_RE, B4_HEADING, REQUIRED_H2_FUNC, REQUIRED_H2_TECH_THREAD,
    REQUIRED_VERIF_H3, RUNG_LABELS, _LEGACY_TECH_H2_5BUCKET, _TECH_PRE_THREAD_SENTINEL,
)
from _content_sniff_signals_lib import scrub_generic_secret  # noqa: E402
from _sql_parse_lib import scrub_credentials  # noqa: E402
import _cap_table_lib  # noqa: E402
import _action_thread_lib  # noqa: E402
import _action_thread_diagram_lib  # noqa: E402
import _md_scan_lib  # noqa: E402

VALIDATOR = "feature_spec"
LEGACY_H2 = {"## Related Artifacts", "## Spec Documents"}  # CRITICAL: legacy format no longer accepted
DEPRECATED_H2 = {
    "## Requirements", "## Business Rules", "## State Machines", "## Algorithms",
    "## External Integrations", "## Success Criteria", "## How It Works",
    # v27.x (P09, human-readable SOT retaxonomy): the 8 retired 9-section-shape H2s
    # (full list minus "## Overview" — see the note below). Checked ONLY when the
    # file is NOT in the pre-SOT degradation window (FeatureSpec.tech_sections_pre_sot
    # already reports the file's shape as a single warning in that case; flagging
    # each of these individually on TOP of that would turn "one warning, not thirty"
    # into exactly the flood the degradation window exists to avoid).
    # "## Overview" is deliberately NOT added: its replacement is "## 1. Technical
    # Overview" (a different string, so no literal collision today), but
    # functional-spec.md's own § 1 heading is "## 1. Overview" — one word away from
    # colliding if DEPRECATED_H2 were ever checked against a shared heading set. Kept
    # out defensively; test_deprecated_h2_excludes_overview below pins both facts.
    "## Polymorphic Behavior", "## Cross-Cutting Logic", "## User Stories",
    "## Key Entities", "## Artifact References", "## Assumptions",
    "## Source Code References", "## Unresolved Questions",
}

# ---------------------------------------------------------------------------
# v27.0.0 (audience split) — functional-spec.md checks
#
# Replaces the retired _check_business_context / _check_screens / _check_edge_cases
# (business-context.md / screens.md / edge-cases.md are gone; functional-spec.md is the
# single BA/QA file). Forbidden-token rule inverts: FR/BR/SM/DEC/SCR/US codes are now
# EXPECTED (they are stated here); the forbidden class becomes dev tokens (class names,
# file:line, HTTP verbs, pseudocode) + secret shapes, outside a fence.
# ---------------------------------------------------------------------------

# Dev-token family: HTTP verbs + a `path/like/this.ext:123` file:line shape. FR-###/BR-###/
# SM-###/DEC-###/SCR###/US### are deliberately NOT in this pattern — those codes are allowed
# and expected in functional-spec.md (inverted from the old business-context.md rule).
FUNC_DEV_TOKEN_RE = re.compile(
    r"\bGET\b|\bPOST\b|\bPUT\b|\bDELETE\b|\bPATCH\b"
    r"|\b[\w./-]+\.[A-Za-z]{1,5}:\d+\b"
)

# v27.0.0 (B4a) — inline-code span stripper, used by the func.dev_token check
# ONLY (see its call site in _check_functional_spec). A backtick-delimited
# span on an ordinary prose line (`` `x` ``, or a longer delimiter run like
# ``x`y`` whose content itself contains a literal backtick) is markdown's own
# fence around a quoted token — a dev token wrapped that way is not prose
# leakage, so it must not fire. This is UNRELATED to the line-based ```
# fenced-block handling above (`blocks`/`fenced`): that already suppresses
# whole fenced code blocks; this strips inline spans on the lines that remain.
#
# SCOPE GUARD: do not reuse this for func.secret_shape below — a secret
# inside backticks is still a leaked secret (see the call-site comment there;
# T6 in test_validate_feature_spec.py is the standing regression guard).
_BACKTICK_RUN_RE = re.compile(r"`+")


def strip_inline_code(text: str) -> str:
    """Replace each recognized inline-code span with an equal-length run of
    spaces, so reported line/column positions elsewhere are unaffected.

    Matches CommonMark's own rule for backtick delimiters: an opening run of
    N backticks closes at the NEXT run of exactly N backticks; a run of a
    different length found in between is just more literal backtick content
    and is skipped over (this is what makes a double-backtick span able to
    safely contain a single backtick, e.g. ``` ``a `b` c`` ```).

    Fail-closed on the unterminated case: an opening run with no matching
    same-length close on this line is NOT treated as a span — everything
    from that point on is left untouched (still scanned by the caller).
    Silently exempting an unterminated span would risk masking a real dev
    token; a false positive here is only a nuisance, so ambiguity resolves
    toward still firing.
    """
    runs = list(_BACKTICK_RUN_RE.finditer(text))
    if not runs:
        return text
    chars = list(text)
    i, total = 0, len(runs)
    while i < total:
        open_run = runs[i]
        open_len = len(open_run.group())
        close_idx = next(
            (j for j in range(i + 1, total) if len(runs[j].group()) == open_len),
            None,
        )
        if close_idx is None:
            break  # unterminated on this line — leave the remainder untouched
        start, end = open_run.start(), runs[close_idx].end()
        for k in range(start, end):
            chars[k] = " "
        i = close_idx + 1
    return "".join(chars)


# ---------------------------------------------------------------------------
# v27.0.0 (P11 / class 4) — func.secret_shape placeholder-value exemption.
#
# scrub_generic_secret / scrub_credentials (imported below) are NOT owned by this
# file, so this does not touch either scrubber's regex family. Instead it inspects
# what a scrub pass ACTUALLY rewrote (via a plain textual diff) and asks whether
# that specific VALUE is a placeholder rather than a real secret. Three real
# corpus shapes must NOT fire:
#   - an ellipsis marking a deliberately elided value ("confirmation_token=…")
#   - an angle-bracket placeholder ("?token=<jwt>")
#   - a Ruby-style code-symbol reference, Model.attribute_name ("confirmation
#     token: Email.confirmed_at set, ...") — a dotted ClassName.snake_case token
#     is a citation to a symbol, not a credential.
# A real credential (a DSN password, an API key literal) never reduces to one of
# these shapes, so it is untouched and still fires — see the negative tests.
# SCOPE GUARD: this exemption applies to func.secret_shape ONLY, never to
# func.dev_token (unrelated, see strip_inline_code above).
#
# REWORK round 1 (adversarial review finding 1, CRITICAL): the code-symbol-
# reference shape alone (`^[A-Z][A-Za-z0-9]*\.[a-z_][A-Za-z0-9_]*$`) is NOT a
# structural discriminator between a real attribute citation and an opaque
# secret literal — `Rails.application_secret_20260817abcdef1234567890`, a real
# DSN-style secret assigned via `SECRET_KEY=Rails....`, matches the identical
# shape as `Email.confirmed_at`. "real secrets never take this shape" was an
# assumption about corpus CONTENT, not a property of the STRING SHAPE, and it
# is false — both are `Upper.lower_snake`. Round 1 discriminated on length +
# a 4+-digit-run rule on the post-dot segment.
#
# REWORK round 2 (second adversarial review, CRITICAL): length + digit-run is
# STILL bypassable — a plausible high-entropy token typed as
# `ClassName.<opaque-value>` dodges both by interleaving digits with letters
# (`kX9qM2wR7tY4bN1cL8`, `a1B2c3D4e5F6g7H8i9`), or, in the purest case, needs
# no digits at all (`a1b2c3d4e5f6g7h8i9` still alternates, but a pure
# consonant cluster like `zxcvbnmqwrty` needs none whatsoever). Length and
# digit-run say nothing about English-identifier-ness vs opaque-blob-ness —
# that was the actual flaw both rounds shared.
#
# The discriminator now used is WORD-LIKENESS, a property of the post-dot
# segment's shape, checked in two parts:
#   1. strict lowercase snake_case (`^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$`) — kills
#      any bypass carrying mixed case outright (`kX9qM2wR7tY4bN1cL8`,
#      `a1B2c3D4e5F6g7H8i9`); a hand-typed Ruby attribute name is never
#      camelCase/PascalCase-mixed.
#   2. a run of 3+ consecutive ASCII letters containing a vowel — a cheap
#      word-likeness proxy. Real attribute names are built from readable
#      words (`now`, `confirmed`, `token`, `status`) and always contain such
#      a run; an opaque blob that clears (1) is either digit-interleaved
#      (breaking every letter run below length 3, e.g. `a1b2c3d4e5f6g7h8i9`)
#      or a random consonant cluster (no vowel in any run, e.g.
#      `zxcvbnmqwrty`) — see test_precision_criticals_p11.py's
#      TestSecretShapeWordLikenessQuadrant* for the full matrix, including 3
#      independently-invented secrets proving this isn't overfit to the 3
#      literal review examples.
# A length cap is kept ONLY as defense-in-depth against a *word-like* opaque
# literal padded with real words (`application_secret_<44-char-blob>` reads
# as word-like by property 2 alone) — it is NOT the primary discriminator for
# the round-2 hole; properties 1+2 are. Raised 20 -> 30 chars so it no longer
# collides with the two longest legitimate attribute references measured
# (`approve_pending_membership` = 26, `payment_gateway_reference_id` = 28),
# while staying well under the three real-corpus secrets it still must catch
# (35-44 chars).
# A vocabulary allowlist of attribute names was explicitly rejected (would rot
# as new attributes are added); this checks the shape of what was captured,
# not what it's named.
#
# REWORK round 3 (third adversarial review, CRITICAL): word-likeness alone
# (strict snake_case + 3+-letter vowel-bearing run + 30-char cap) is STILL
# bypassable, in two distinct ways demonstrated by an 8/8 review attack set:
#   - prefixing a real word onto an opaque digit-bearing blob so the
#     word-like run is satisfied by the PREFIX, not the blob attached to it
#     (`token_a1b2c3d4e5f6`, `pass_9f8e7d6c5b4a`, `bearer_abc123def456`,
#     `session_ff00ee11dd22`, `hunter2_seed`) — the run only has to appear
#     SOMEWHERE in the segment, so a legitimate-looking prefix launders an
#     arbitrary digit-bearing suffix riding along with it;
#   - a hex-only blob that happens to read as letters, since every hex
#     digit character is also a lowercase ASCII letter (`deadbeefcafe`,
#     `deadbeefcafebabe`, `facadedecadebead`, `key_deadbeefcafe`) — no
#     digit ever appears, so a digit-based rule alone does nothing for
#     these, and the letters alone satisfy the word-likeness run.
#
# Two additional properties close both, evaluated on the same post-dot
# `attr` segment:
#   4. the segment contains NO digit at all. Every real Rails/Ruby
#      attribute name measured in this corpus (`confirmed_at`, `now`,
#      `status`, `confirmation_token`, `availability`,
#      `approve_pending_membership`, `payment_gateway_reference_id`) is
#      pure `[a-z_]`; every digit-bearing attack above is a real secret
#      fragment (hex or base62-ish) a hand-typed attribute name never
#      contains. This alone kills the digit-bearing half of the attack set.
#   5. no UNDERSCORE-SEPARATED TOKEN inside the segment is hex-only (every
#      character in `[a-f]`) AND >= 8 characters long — evaluated PER
#      TOKEN, not over the whole segment. Checking the whole segment for
#      "not hex-only" does NOT work: a real word prefix
#      (`key_deadbeefcafe` contains `k`/`y`, both outside `[a-f]`) makes
#      the WHOLE string fail a naive hex-only test while the attacker's
#      actual secret token (`deadbeefcafe`) is still sitting right there,
#      unexamined, in the same string. Splitting on `_` and judging each
#      token in isolation is what catches it.
#      The >= 8 floor is deliberate: short real English words composed
#      entirely of `[a-f]` letters exist and must stay exempt — `cafe`,
#      `face`, `feed`, `dead`, `bead`, `facade`, `decade` are all <= 6
#      chars (`cafe_id`, a real attribute reference, depends on this floor
#      protecting its 4-char `cafe` token). Nothing legitimate measured in
#      this corpus's attribute names is an all-`[a-f]` word 8+ characters
#      long, while the attack tokens measured run 12-16 chars — a wide
#      margin above the floor.
#
# See test_precision_criticals_p11.py's TestSecretShapeRound3* for the full
# 8-attack matrix (all die — 5 on rule 4, 3 on rule 5) plus independently
# invented attacks, each asserting the INTERMEDIATE neutralized value, not
# only the final verdict (verdict-only assertions are what let rounds 1 and
# 2 both survive one full adversarial pass apiece).
#
# RESIDUAL LIMITATION — documented, not closed. This is a doc-linting
# heuristic layered on top of scrub_generic_secret/scrub_credentials, not a
# secret scanner: it recognizes ONE specific non-secret shape (a dotted
# code-symbol reference) well enough for this corpus, not every possible
# non-secret string. Concretely, still exempt after this rework:
#   - a secret that is pronounceable, all-lowercase, digit-free, and
#     contains no 8+-char run of only `[a-f]` letters (e.g. a dictionary-
#     word-shaped secret with no hex-looking substring) reads as word-like
#     and passes all five rules;
#   - rule 5 only inspects UNDERSCORE-separated tokens — a hex blob glued
#     directly onto a word with NO underscore in between
#     (`Store.tokendeadbeefcafebabe`) is a single token by that split, and
#     that single token is not hex-only as a whole (the word's non-`[a-f]`
#     letters mask the blob riding on it), so it is not caught;
#   - a hex secret CHUNKED into several pieces each under the 8-char floor
#     and underscore-joined (`Vault.deaf_bead_face_cafe` — four all-`[a-f]`
#     4-char tokens spelling out a 16-char blob) evades rule 5 token-by-
#     token even though the reassembled secret is well past the floor.
# Both of the last two are confirmed surviving in the invented-attack
# matrix in the test suite; they are recorded here rather than patched
# blind, since closing them for real needs a different kind of
# discriminator (a dictionary/entropy check), which is out of scope for
# this rework. Anyone touching this exemption next should start there.
# ---------------------------------------------------------------------------
_PLACEHOLDER_LITERAL_RE = re.compile(r"^(?:\.\.\.|…|x{3,}|redacted)$", re.IGNORECASE)
_PLACEHOLDER_BRACKET_RE = re.compile(r"^<[^<>\n]{0,80}>$")
# Post-dot segment MUST be strict lowercase snake_case — mixed case (a
# camelCase/PascalCase token pretending to be an attribute reference) never
# matches at all, closing the round-2 mixed-case bypasses at the regex level.
_CODE_SYMBOL_REF_RE = re.compile(r"^[A-Z][A-Za-z0-9]*\.([a-z][a-z0-9]*(?:_[a-z0-9]+)*)$")
# Defense-in-depth only (see comment above) — real attribute names measured:
# confirmation_token (18), approve_pending_membership (26),
# payment_gateway_reference_id (28). Real-corpus secrets this fix must still
# catch run 35-44 chars post-dot — a wide margin above the cap.
_CODE_SYMBOL_ATTR_MAX_LEN = 30
# Word-likeness proxy: a maximal run of 3+ ASCII lowercase letters that
# contains at least one vowel. Digits/underscores break a run (so
# `a1b2c3...` never reaches length 3); a run with no vowel at all
# (`zxcvbnmqwrty`) is rejected even though it's long.
_WORD_LIKE_LETTER_RUN_RE = re.compile(r"[a-z]{3,}")
_VOWEL_RE = re.compile(r"[aeiou]")
_VALUE_STRIP_CHARS = "`'\")]}.,;: "
# REWORK round 3 (see the block comment above _PLACEHOLDER_LITERAL_RE):
# rule 4 — a bare digit anywhere in the segment disqualifies it outright.
_SEGMENT_HAS_DIGIT_RE = re.compile(r"\d")
# REWORK round 3, rule 5 — a single underscore-separated TOKEN (not the
# whole segment — see the "trap" note in the block comment above) that is
# entirely `[a-f]` and at least this long reads as a hex blob, not a word.
_HEX_ONLY_TOKEN_MIN_LEN = 8
_HEX_ONLY_TOKEN_RE = re.compile(r"^[a-f]{%d,}$" % _HEX_ONLY_TOKEN_MIN_LEN)


def _has_word_like_run(segment: str) -> bool:
    """True when `segment` contains a run of 3+ consecutive ASCII letters
    that includes a vowel — see the word-likeness rationale above."""
    return any(_VOWEL_RE.search(run) for run in _WORD_LIKE_LETTER_RUN_RE.findall(segment))


def _has_digit(segment: str) -> bool:
    """Round 3 rule 4 — True when `segment` contains any digit at all."""
    return bool(_SEGMENT_HAS_DIGIT_RE.search(segment))


def _has_hex_only_token(segment: str) -> bool:
    """Round 3 rule 5 — True when any underscore-separated token within
    `segment` is composed entirely of `[a-f]` characters and is >= 8 chars
    long. Evaluated PER TOKEN (see the "trap" note above _PLACEHOLDER_LITERAL_RE
    for why checking the whole segment at once does not work)."""
    return any(_HEX_ONLY_TOKEN_RE.match(tok) for tok in segment.split("_"))


def _is_non_secret_value(core: str) -> bool:
    """True when a flagged VALUE is a known non-secret shape (placeholder or
    code-symbol reference), never true for an opaque/real-looking credential."""
    if core == "":
        return True
    if _PLACEHOLDER_LITERAL_RE.match(core) or _PLACEHOLDER_BRACKET_RE.match(core):
        return True
    m = _CODE_SYMBOL_REF_RE.match(core)
    if not m:
        return False
    attr = m.group(1)
    if len(attr) > _CODE_SYMBOL_ATTR_MAX_LEN:
        return False  # too long even by the generous cap — opaque literal padded with words
    if not _has_word_like_run(attr):
        return False  # no vowel-bearing letter run — digit-interleaved or consonant-cluster blob
    if _has_digit(attr):
        return False  # round 3 rule 4 — real attribute names carry no digits at all
    if _has_hex_only_token(attr):
        return False  # round 3 rule 5 — an underscore token that's pure a-f hex, 8+ chars, is a blob
    return True


# Mirrors the value-capture shape both scrub_generic_secret's literal-assignment
# pattern and scrub_credentials' key=value patterns use: one or more chars that
# are not a quote or whitespace, immediately after `=`/`:` (optionally quoted).
# NOT anchored to a specific keyword (api_key/token/secret/password/...) —
# neutralizing an unrelated `x=5`/`10:30` position is harmless, since neither
# scrub pass would have matched there anyway; only a position a scrub pass
# actually keys on can ever change the result below.
_ASSIGNMENT_VALUE_RE = re.compile(r"([=:]\s*[\"']?)([^\s\"']+)")


def _neutralize_placeholder_assignments(line: str) -> str:
    """Erase an ENTIRE `[=:]value` run (operator included, not just the value)
    when the value — once incidental trailing punctuation a greedy scrub regex
    would also swallow (a closing `)`, backtick, quote, etc.) is stripped —
    reduces to a known non-secret shape (see _is_non_secret_value). Used ONLY
    as a pre-pass before func.secret_shape's scrub calls.

    The operator must go too, not just the value: both scrub_generic_secret's
    and scrub_credentials' patterns allow whitespace between the operator and
    the value (`\\s*[=:]\\s*`), so leaving a bare "keyword= " behind would let
    the SAME pattern skip the gap and latch onto the next unrelated word on
    the line as a substitute value. Removing the operator too means no
    assignment shape remains at this position at all — a real (non-empty,
    non-placeholder) secret elsewhere on the line, or a DIFFERENT `[=:]` run,
    is untouched and still fires exactly as before."""
    def _replace(m: re.Match) -> str:
        core = m.group(2).strip(_VALUE_STRIP_CHARS)
        return "" if _is_non_secret_value(core) else m.group(0)
    return _ASSIGNMENT_VALUE_RE.sub(_replace, line)


_FUNC_H2_RE = re.compile(r"^## \d+\. ")
_FUNC_FR_BULLET_RE = re.compile(r"^-\s+\*\*FR-(\d{3})\*\*")
_FUNC_RULE_TAG_RE = re.compile(r"\((BR|DEC|SM)-(\d{3})\)\s*$")
_FUNC_OPEN_DECISIONS_NONE_RE = re.compile(r"^None\s+—\s+no unresolved domain confirmations\.?", re.IGNORECASE)
_FUNC_BACKGROUND_RE = re.compile(r"^N/A\s+—\s+background feature", re.IGNORECASE)
_FUNC_TYPE_RE = re.compile(r"^\*\*Type\*\*:\s*(\w+)", re.MULTILINE)
_FUNC_EDGE_BEHAVIOUR_FR_RE = re.compile(r"\*\*FR-(\d{3})\*\*")

# ---------------------------------------------------------------------------
# P07 (human-readable SOT) — pre-SOT degradation window.
#
# A functional-spec.md still in the OLD 10-section shape (pre this phase's renumber)
# is detected by the presence of its old "## 2. Open Decisions" heading — that exact
# string never appears in the new 13-section shape (Open Decisions moved to "## 3.").
# When detected: emit ONLY func.sections_pre_sot (warning) and skip func.missing_h2
# plus every section-bound-dependent check below (old AND new) — a file mid-migration
# should read as "please migrate," not as a wall of findings keyed on headings that
# do not exist yet. Content-level scans that are unrelated to section shape
# (func.dev_token, func.secret_shape) are NOT part of this muting — they still run.
# ---------------------------------------------------------------------------
_FUNC_PRE_SOT_SENTINEL = "## 2. Open Decisions"

# P07 — § 2 Functional Capabilities: an FR-### code cited in a "Requirements" cell.
_FR_CODE_IN_CELL_RE = re.compile(r"\bFR-\d{3}(?!\d)")

# Phase 05 (capability-map, AD-6/SC-2) — one code-extraction regex per family, used both
# to read a § 2 claim cell (_cap_claims) and to read the § 6 Screens/§ 7 User Stories
# declared-code idioms below (_func_code_sets). "BR" deliberately also matches DEC-###
# and SM-### — those three tag families are already merged into ONE "BR" set everywhere
# else in this file (see `tagged_in_5` in `_check_code_surfacing`); a § 2 Business Rules
# cell citing a DEC-### or SM-### tag is a real claim, not a miss. Never a trailing `\b`
# — `_` is a word character, so `\b` never matches past the digits in a `BR-001_Slug`
# shape (this hazard has recurred 5 times in this repo; see phase 03). `(?!\d)` is the
# correct "end of the numeric code" anchor.
_FAMILY_CODE_RE: dict[str, re.Pattern[str]] = {
    "US": re.compile(r"\bUS\d{3}(?!\d)"),
    "FR": _FR_CODE_IN_CELL_RE,
    "BR": re.compile(r"\b(?:BR|DEC|SM)-\d{3}(?!\d)"),
    "SCR": re.compile(r"\bSCR\d{3}(?!\d)"),
}

# Possessive guard. A code followed by `'s` is PROSE, not a claim — `SCR026's list view`
# in a § 2 Screens cell references a screen another capability owns, and counting it made
# `cap.double_claimed` fire on the mention.
#
# This is a POSITIONAL CHECK, not a trailing `(?!['’]s\b)` in the pattern, and that is the
# whole point. A trailing negative lookahead placed after optional groups is defeated by
# backtracking: against `SCR001/REG002's` the engine matched the `/REG002` group, failed the
# lookahead, then simply backtracked to NOT taking that optional group and succeeded on bare
# `SCR001` — reintroducing the very false `cap.double_claimed` this guard exists to stop.
# `SCR001_List/REG002_Panel's` was worse: `_\w+` backtracked off the final letter and yielded
# the mangled `SCR001_List/REG002_Pane`. Deciding AFTER the match, on the text that actually
# follows it, has no such escape hatch.
#
# Deliberately `'s` and not a bare `['’]`: a bare-apostrophe rule would also suppress a
# legitimately quoted `'SCR026'`, trading a false positive for a false negative.
# Trailing backticks are stepped over before the apostrophe is looked for: codes in these
# cells are routinely backticked, so the possessive shows up as `` `SCR001`'s `` — the
# apostrophe is not adjacent to the match. Case-insensitive for an ALL-CAPS cell's `'S`.
_POSSESSIVE_SUFFIX_RE = re.compile(r"`*['’]s\b", re.IGNORECASE)


def _is_possessive(text: str, end: int) -> bool:
    """True when the match ending at `end` is immediately followed by `'s` — i.e. the token
    is a prose mention, not a claim."""
    return _POSSESSIVE_SUFFIX_RE.match(text, end) is not None

# Composite-aware SCR tokenizer for § 2 claim cells ONLY (`_cap_claims`).
# `references/code-formats.md` § Composite cross-ref parsing is normative: "Grep-style
# validators looking for bare `SCR\d{3}` patterns MUST also match
# `SCR\d{3}(/REG\d{3}_\w+)?`". `verification-checklist-screen-spec.md` CE3 says why it
# matters: "An F### with only SCR###/REG### refs does NOT own the parent SCR" — a region
# ref and a screen-shell ref are DIFFERENT claims. `_FAMILY_CODE_RE["SCR"]` collapses both
# to the bare parent, so two capabilities legitimately owning two regions of one screen
# (`SCR161/REG002`, `SCR161/REG005`) both read as `SCR161` and collided into a false
# `cap.double_claimed` critical. Here the composite keeps its own identity.
# NOT folded into `_FAMILY_CODE_RE`: `_func_code_sets` (the DECLARED half) still collapses
# to the parent, and `cap.code_unclaimed` compares the two halves — see `_claim_parents`.
_SCR_CLAIM_RE = re.compile(
    r"\bSCR\d{3}(?!\d)(?:_\w+)?(?:/REG\d{3}(?!\d)(?:_\w+)?)?")
_SCR_PARENT_RE = re.compile(r"^(SCR\d{3})")
# `_NameSlug` is cosmetic — `code-formats.md` gives the identity as `SCR###` / `REG###` and
# the slug is a readability affordance on top. It MUST be stripped before a claim is keyed:
# leaving it in makes `SCR161_List` and `SCR161` two distinct keys, so two rows claiming one
# screen under different spellings would stop colliding and `cap.double_claimed` would go
# quiet on a real defect. Normalizing here is what keeps this fix from neutering the check.
_SCR_SLUG_RE = re.compile(r"(SCR\d{3}|REG\d{3})_\w+")


def _normalize_scr_claim(token: str) -> str:
    """`SCR161_List/REG002_Panel` -> `SCR161/REG002`. Identity only, slug discarded."""
    return _SCR_SLUG_RE.sub(lambda m: m.group(1), token)


def _claim_parents(claims: dict[str, list[str]]) -> set[str]:
    """Every claim token PLUS the bare parent screen of each composite one — the view
    `cap.code_unclaimed` (a completeness check) consumes.

    The two § 2 checks need two different views of the same dict and this is the trap that
    splits them. `cap.double_claimed` is a CARDINALITY check and must read exact tokens, or
    two regions of one screen collide. `cap.code_unclaimed` is a COMPLETENESS check against
    `_func_code_sets`, which still yields the bare parent (`SCR161`) from a § 6 row — so
    keying claims by composite ALONE would leave a declared `SCR161` looking unclaimed when
    § 2 claims `SCR161/REG002`. That would swap the false positive this fix removes for a
    brand-new one; this function is what stops it."""
    out = set(claims)
    for code in claims:
        m = _SCR_PARENT_RE.match(code)
        if m:
            out.add(m.group(1))
    return out

# P07 — § 11 Risks & Known Issues: the literal none-found fallback (mirrors
# _FUNC_OPEN_DECISIONS_NONE_RE / _FUNC_BACKGROUND_RE's shape).
_FUNC_RISKS_NONE_RE = re.compile(r"^N/A\s+—\s+none found\.?", re.IGNORECASE)

# P07 — func.risk_as_rule: a § 5 Business Rules line that reads like an observed
# DEFECT rather than an intended rule. Deliberately narrow (3 literal phrases) —
# a false negative here just means the researcher's own judgment carries the day;
# a false positive would nag on legitimate rule language ("should not" is common in
# permission rules too), so this stays a warning, never critical.
_FUNC_RISK_LANGUAGE_RE = re.compile(r"should not|incorrectly|\bbug\b", re.IGNORECASE)

# P07 — func.user_story_shape: each § 7 story block must lead with these three
# bold-labeled fields (Actor -> Goal -> Business value), per line so a value on the
# same line as the label is required (a bare "**Actor:**" with nothing after it does
# not count — see the `\s*\S` tail on each pattern).
_FUNC_US_HEADING_RE = re.compile(r"^###\s+(US\d{3}\w*)")
_FUNC_US_ACTOR_RE = re.compile(r"^\*\*Actor:\*\*\s*\S", re.MULTILINE)
_FUNC_US_GOAL_RE = re.compile(r"^\*\*Goal:\*\*\s*\S", re.MULTILINE)
_FUNC_US_VALUE_RE = re.compile(r"^\*\*Business value:\*\*\s*\S", re.MULTILINE)

# ---------------------------------------------------------------------------
# Phase 06 (capability-map plan) — cap.analysis_required / cap.review_advised.
#
# [SA-1] Reproduced empirically by the red team: the naive
# `^\*\*Single-capability rationale:\*\*\s*\S` is defeated by an EMPTY label,
# because `\s` matches `\n` — with `re.MULTILINE` the `\s*\S` walks PAST the end
# of the label's own line and is satisfied by the first non-space character
# further down the document (in a real § 2 that is a pipe char from an
# unrelated later table row). `[ \t]*` cannot cross a newline; `[^\n]*$` binds
# the captured body to the label's own line — an empty label can never match
# this pattern at all, which is exactly what makes the hatch un-rubber-stampable
# (see `_cap_rationale_verdict` below, SC-1).
_FUNC_CAP_RATIONALE_RE = re.compile(
    r"^\*\*Single-capability rationale:\*\*[ \t]*(?P<body>\S[^\n]*)$", re.MULTILINE)

# The background-feature denominator: distinct BL### codes cited anywhere in the
# sibling technical-spec.md (they surface in § 5.5 Artifact References, but
# counting across the WHOLE twin text is more robust than depending on that one
# table cell surviving a future template edit). No trailing `\b` — a real BL code
# is always headed `BL050_SendWelcomeMail`, and `_` is a word character, so `\b`
# never matches past the digits there (this hazard has recurred 5+ times in this
# repo). `(?!\d)` is the correct "end of the numeric code" anchor.
_FUNC_BL_CODE_RE = re.compile(r"\bBL\d{3}(?!\d)")
# NOT `...\b` at the end: BR/DEC/SM codes in technical-spec.md are always headed
# `### BR-001_NameSlug` — `_` is a word char, so a trailing \b would never match past
# the digits there (no boundary between "1" and "_"). `(?!\d)` (not followed by
# another digit) is the correct "end of the numeric code" anchor for both the bare
# `FR-001` form and the `BR-001_NameSlug` form.
_TECH_CODE_RE = re.compile(r"\b(FR|BR|DEC|SM)-(\d{3})(?!\d)")
_NEEDS_DOMAIN_CONFIRMATION_RE = re.compile(r"\[NEEDS_DOMAIN_CONFIRMATION\]")
PLACEHOLDER_RE = re.compile(r"\{[A-Z][A-Z0-9_/|]*\}")
FCODE_HEADING_RE = re.compile(r"^#\s+F\d{3}_[A-Za-z0-9]+")
SCREEN_FLOW_OK_RE = re.compile(r"^\*\*See:\*\*\s+ScreenFlow\s+§\s+F\d{3}_\w+|^N/A —")
NUMBERED_STEP_RE = re.compile(r"^\s*\d+\.\s+\S")
VALID_SUBTYPES = {"render", "interaction", "flow"}
# v27.x (P09): DISC-### subsections nest one level deeper under the new shape —
# `## 3. System Design` > `### 3.2 Data Model` > `#### Polymorphic Behavior` >
# `##### DISC-### — {Entity}.{field}` (technical-spec-template.md § 3.2), vs. the
# old `## Polymorphic Behavior` > `### DISC-###` (2 levels). Widened 3->5 hashes.
DISC_SUBSECTION_RE = re.compile(r"^##### DISC-\d{3}")
BOOLEAN_VALUE_RE = re.compile(r"^\|\s*(true|false|yes|no|1|0)\s*\|", re.IGNORECASE)
_DISC_TABLE_HEADER_RE = re.compile(r"^\|\s*value\b", re.IGNORECASE)
_DISC_TABLE_SEP_RE = re.compile(r"^\|\s*[-:]+\s*\|")


def _disc_boolean_hits(lines: list[str], headings: list, b_poly: tuple[int, int]) -> list[tuple[int, str]]:
    """`(line_idx, heading)` pairs for every DISC-### subsection under `b_poly`
    whose value table documents ONLY boolean values. C15 (phase 03c): factored
    out of `_check_technical_spec` so the SAME predicate backs both the
    old-shape home (`### 3.2 Data Model`, never degraded) and the new-shape home
    (`### 4.2 Data Model`, D4-degraded) — the rule is defined exactly once."""
    poly_headings = [(idx, h) for idx, h in headings
                      if b_poly[0] <= idx < b_poly[1] and DISC_SUBSECTION_RE.match(h)]
    hits: list[tuple[int, str]] = []
    for k, (idx, disc_h) in enumerate(poly_headings):
        end = poly_headings[k + 1][0] if k + 1 < len(poly_headings) else b_poly[1]
        disc_lines = lines[idx:end]
        bool_hits = [ln for ln in disc_lines if BOOLEAN_VALUE_RE.match(ln)]
        non_bool_table = [ln for ln in disc_lines if ln.startswith("|") and not BOOLEAN_VALUE_RE.match(ln)
                          and not _DISC_TABLE_HEADER_RE.match(ln) and not _DISC_TABLE_SEP_RE.match(ln)]
        if bool_hits and not non_bool_table:
            hits.append((idx, disc_h))
    return hits

# Lazy-N/A grep patterns — JSX-ternary and framework conditionals
LAZY_NA_PATTERNS = [
    re.compile(r"\{[^}]*\?[^:]*:[^}]*\}"),   # JSX ternary
    re.compile(r"v-if=|v-else=|v-show="),      # Vue conditionals
    re.compile(r"@if\s*\(|@else"),             # Blade
    re.compile(r"<%\s*if\b|<%\s*else\b"),      # ERB
]


def _bounds(h2, name, total):
    for i, (idx, h) in enumerate(h2):
        if h == name:
            return idx + 1, (h2[i + 1][0] if i + 1 < len(h2) else total)
    return None


def _matches_required_h2(h2_names: list[str], required: list[str]) -> bool:
    """True iff *h2_names*, filtered down to members of *required*, equals *required*
    exactly — every entry present, in order. Used by `FeatureSpec.required_sections` to
    accept either the current action-thread shape or the legacy 5-bucket shape (phase 10)."""
    return [h for h in h2_names if h in required] == required


def _bounds_at(headings: list, prefix: str, name: str, cap: int) -> tuple[int, int] | None:
    """Like `_bounds`, but for a heading level other than H2 (e.g. `### ` or `#### `),
    filtering `headings` (the full, mixed-level list `parse_headings_and_blocks` returns)
    down to siblings at `prefix`'s level first. `cap` bounds the end so a sibling heading
    that is actually far away — in a LATER H2/H3, once this heading's own parent section
    has already ended — never gets pulled in (P09: `## 3. System Design`'s nested `#### `
    headings are not contiguous with `## 4.`'s `#### ` headings, so an uncapped "next H4"
    search would silently cross section boundaries)."""
    siblings = [(idx, h) for idx, h in headings if h.startswith(prefix)]
    for i, (idx, h) in enumerate(siblings):
        if h == name:
            nxt = siblings[i + 1][0] if i + 1 < len(siblings) else cap
            return idx + 1, min(nxt, cap)
    return None


_H2_NUMBER_RE = re.compile(r"^## (\d+)\. ")


def _bounds_by_number(h2: list, n: int, total: int) -> tuple[int, int] | None:
    """Like `_bounds`, but matches an H2 by its LEADING NUMBER (`## 4. `) rather than
    its exact title text — tolerant of the D4 degradation window where an H2's TITLE
    changes shape (old `## 4. Technical Behavior by Capability` -> new `## 4. Shared
    Foundation`) while its ordinal position does not. This is phase 03b's fix for
    C13/P1: `_check_dec_blocks` used to bound its search on the OLD literal only, so
    `b_cap` silently went `None` — and every DEC check with it — the moment a file's
    § 4 was retitled.

    Scoped narrowly to the DEC search space ONLY. Every other `_bounds`/`_bounds_at`
    call in this file still keys on its exact literal title, deliberately unchanged: the
    OLD-shape checks below (`capability_buckets_missing`, `missing_client_behavior_anchor`,
    `polymorphic_behavior_present`/`disc_boolean`, `capability_twin_skew`) test a CONCEPT
    the new action-thread shape does not carry forward structurally, but each one DOES have
    an explicit new-shape home re-homed alongside it (phase 03c, gated on `b_actions`) —
    unlike `decision_logic_section_present`, which has no new-shape home (its concern is
    already fully covered by `_check_dec_blocks`'s per-action DEC row scan) and stays
    RETIRED-in-place for the old shape only. `sysdesign_subsections` and
    `mapping_table_missing` had no specified successor either and are retired outright
    (phase 10 — see their own removal notes below), alongside `REQUIRED_H2_TECH`/
    `REQUIRED_SYSDESIGN_H3`'s retirement as public names in `_spec_constants.py`."""
    for i, (idx, h) in enumerate(h2):
        m = _H2_NUMBER_RE.match(h)
        if m and int(m.group(1)) == n:
            return idx + 1, (h2[i + 1][0] if i + 1 < len(h2) else total)
    return None


# ---------------------------------------------------------------------------
# Phase 03b (C13 fix, P2) — under the action-thread shape a DEC is a 5-column
# table row inside the claiming action's own **Rule** rung (`## 3. Actions`),
# not an H4 block under `## 4.` (wire-format-contract.md § 3, "the rung set").
# `DEC_BLOCK_RE` (an H4 heading regex) matches none of these rows, so even with
# P1's bound fixed, the old scan would still find zero DEC content on a
# migrated file. This second, independent scan validates the row shape for the
# SAME substance the H4 block was: all 5 columns present and non-empty, no
# lazy N/A/TBD/— placeholder in a column that must carry a real value, valid
# subtype, and a Source column carrying a real backticked `path:line`
# citation — reusing the SAME two rule_ids (`dec_blocks_well_formed`,
# `dec_lazy_na`) so nothing downstream needs rewiring.
# ---------------------------------------------------------------------------
_DEC_ROW_ID_RE = re.compile(r"^\*\*(DEC-\d{3})\*\*$")
# Mirrors the `_PLACEHOLDER` shape `validate_feature_api_link.py` /
# `validate_feature_screen_link.py` already use for "cell carries a lazy
# stand-in, not real content" — extended with `tbd` (the wire-format
# contract's own vocabulary for a column that still needs real content)
# rather than inventing a distinct lazy-value vocabulary for this one table.
_DEC_ROW_LAZY_CELL_RE = re.compile(r"^(?:—|-|\{.*\}|n/?a|tbd)$", re.IGNORECASE)
# A DEC row's Source cell must carry a REAL citation — a backticked
# `path:line` or `path:line-line` token, the exact shape the wire-format
# contract's own worked example uses (`` `_actions.haml:4-16` ``).
_DEC_ROW_SOURCE_RE = re.compile(r"`[^`\n]+:\d+(?:-\d+)?`")


def _dec_row_cell_state(cell: str) -> str:
    """`'empty' | 'lazy' | 'ok'` for one DEC row cell."""
    stripped = cell.strip()
    if not stripped:
        return "empty"
    if _DEC_ROW_LAZY_CELL_RE.match(stripped):
        return "lazy"
    return "ok"


def _dec_row_findings(lines: list[str], b_actions: tuple[int, int] | None,
                       is_pre_thread: bool) -> list[dict]:
    """Scan `## 3. Actions` for DEC table rows (`| **DEC-NNN** | subtype |
    Condition | What the user sees | Source |`) and validate each one. Scoped to
    the whole § 3 body rather than re-deriving per-action/per-rung bounds via
    `_action_thread_lib` — the row's own bold `**DEC-NNN**` first cell is a
    distinctive enough signature that no other § 3 table content can be
    mistaken for it, and scanning directly keeps a real source line number for
    every finding. Degraded per D4 (`_thread_sev_msg`) while
    `_TECH_PRE_THREAD_SENTINEL` is present, same as every other action-thread
    check — in practice this is close to a no-op (a file still carrying
    '## 3. System Design' has no '## 3. Actions' to find rows in at all), but
    a hand-built or malformed mid-migration fixture could carry both, and the
    contract calls for consistent treatment regardless."""
    issues: list[dict] = []
    if not b_actions:
        return issues
    start, end = b_actions

    for i in range(start, end):
        raw_line = lines[i].strip()
        if not raw_line.startswith("|"):
            continue
        cells = [c.strip() for c in raw_line.strip("|").split("|")]
        if len(cells) != 5:
            continue
        m = _DEC_ROW_ID_RE.match(cells[0])
        if not m:
            continue
        dec_code = m.group(1)
        subtype_cell, cond_cell, outcome_cell, source_cell = cells[1:5]

        def emit(base_sev: str, rid: str, msg: str, _line: int = i) -> None:
            sev, full_msg = _thread_sev_msg(is_pre_thread, base_sev, msg)
            issues.append({"severity": sev, "rule_id": rid,
                            "location": {"file": None, "line": _line + 1}, "message": full_msg})

        for label, cell in (("subtype", subtype_cell), ("Condition", cond_cell),
                            ("What the user sees", outcome_cell), ("Source", source_cell)):
            state = _dec_row_cell_state(cell)
            if state == "empty":
                emit("critical", "FeatureSpec.dec_blocks_well_formed",
                     f"{dec_code} row: {label!r} column is empty")
            elif state == "lazy":
                emit("warning", "FeatureSpec.dec_lazy_na",
                     f"{dec_code} row: {label!r} column carries a lazy placeholder "
                     f"({cell!r}); needs real content")

        if _dec_row_cell_state(subtype_cell) == "ok":
            declared = {s.strip() for s in subtype_cell.split(",")}
            invalid = declared - VALID_SUBTYPES
            if invalid:
                emit("critical", "FeatureSpec.dec_blocks_well_formed",
                     f"{dec_code} row: invalid subtype(s) {invalid}; valid: render, interaction, flow")

        if _dec_row_cell_state(source_cell) == "ok" and not _DEC_ROW_SOURCE_RE.search(source_cell):
            emit("critical", "FeatureSpec.dec_blocks_well_formed",
                 f"{dec_code} row: Source column {source_cell!r} does not carry a real "
                 f"`path:line` citation")

    return issues


def _check_dec_blocks(lines: list[str], headings: list, blocks: list, b_cap: tuple | None,
                       b_actions: tuple[int, int] | None = None,
                       is_pre_thread: bool = False) -> list[dict]:
    """Check DEC-### structural validity under BOTH shapes: the OLD `#### ... (DEC-NNN)`
    H4 block anywhere under `## 4.` (`b_cap`), and the NEW 5-column table row inside
    `## 3. Actions` (`b_actions`, see `_dec_row_findings`). The two scans are
    independent — a file has one shape or the other during the D4 window, never a
    mix, but nothing here assumes that; each scan simply no-ops when its own bound
    is absent.

    v27.x (P09): the OLD shape was re-homed from `## Cross-Cutting Logic § Decision
    Logic` (one fixed H3 holding every DEC block) to `## 4.`'s DYNAMIC per-capability
    buckets, where each `### 4.N` carries its own **Decision Logic** bold-marker
    sub-section (prose, not a heading — see technical-spec-template.md § 4) followed
    by zero or more `#### ... (DEC-NNN)` blocks. There is no single fixed heading left
    to bound the search on, so DEC blocks are found by DEC_BLOCK_RE match ANYWHERE
    inside `## 4.`'s bounds (`b_cap`) — the locator is heading-name-agnostic by
    design, matching every capability bucket without needing to know how many exist
    or what they're named.

    Phase 03b (C13/P1): `b_cap` is now resolved by the CALLER via
    `_bounds_by_number(h2, 4, ...)` rather than the exact old title, so this scan
    keeps working across the D4 rename ('## 4. Technical Behavior by Capability' ->
    '## 4. Shared Foundation') exactly as it did for the old shape before.
    """
    issues: list[dict] = []

    if b_cap:
        dl_start, dl_end = b_cap
        dec_heads = [(idx, h) for idx, h in headings if DEC_BLOCK_RE.match(h) and dl_start <= idx < dl_end]

        if not dec_heads:
            # No DEC-### block anywhere under ## 4. — lazy-N/A heuristic, scoped to the
            # whole ## 4. body since there is no single "Decision Logic" H3 left to scope
            # it to more tightly. Only worth raising when the body itself claims "no
            # decision logic" (the template's own N/A fallback) while the file ALSO
            # contains JSX-ternary-shaped conditionals — a signal the researcher may have
            # missed real DEC-worthy branching.
            cap_text = "\n".join(lines[dl_start:dl_end])
            if "N/A" in cap_text:
                full_text = "\n".join(lines)
                hits = [pat.pattern for pat in LAZY_NA_PATTERNS if pat.search(full_text)]
                if hits:
                    issues.append({
                        "severity": "warning", "rule_id": "FeatureSpec.dec_lazy_na",
                        "location": {"file": None, "line": dl_start + 1},
                        "message": f"## 4. Decision Logic is N/A but spec contains conditional "
                                   f"patterns matching DEC signatures ({hits[:2]}); reviewer should verify"
                    })
        else:
            for k, (idx, raw) in enumerate(dec_heads):
                nxt = dec_heads[k + 1][0] if k + 1 < len(dec_heads) else dl_end
                block_lines = lines[idx:nxt]
                block_text = "\n".join(block_lines)

                # v27.0.0 (D-f): **user_visible_outcome:** dropped — that 1-sentence
                # business-outcome justification now lives in functional-spec.md § 5
                # (Business Rules) as the BR/DEC-###'s one-liner. A block still
                # carrying the field is forward-compatible (not an error); a block
                # missing **Source:** still fails.
                required_fields = ["**subtype:**", "**Triggers in:**", "**Involved entities:**",
                                   "**Source:**"]
                for field in required_fields:
                    if field not in block_text:
                        issues.append({
                            "severity": "critical", "rule_id": "FeatureSpec.dec_blocks_well_formed",
                            "location": {"file": None, "line": idx + 1},
                            "message": f"{raw} missing required field {field!r}"
                        })

                # Check subtype values
                subtype_match = re.search(r"\*\*subtype:\*\*\s*(.+)", block_text)
                if subtype_match:
                    declared = {s.strip() for s in subtype_match.group(1).split(",")}
                    invalid = declared - VALID_SUBTYPES
                    if invalid:
                        issues.append({
                            "severity": "critical", "rule_id": "FeatureSpec.dec_blocks_well_formed",
                            "location": {"file": None, "line": idx + 1},
                            "message": f"{raw} invalid subtype(s): {invalid}; valid: render, interaction, flow"
                        })

                # Check pseudocode ≤8 lines
                dec_blocks = [(s, e, l) for s, e, l in blocks if idx <= s < nxt]
                for start, end, lang in dec_blocks:
                    if lang != "mermaid" and (end - start - 1) > 8:
                        issues.append({
                            "severity": "warning", "rule_id": "FeatureSpec.dec_blocks_well_formed",
                            "location": {"file": None, "line": start + 1},
                            "message": f"{raw} pseudocode block {end - start - 1} lines > 8"
                        })

    issues.extend(_dec_row_findings(lines, b_actions, is_pre_thread))
    return issues


def _check_linked_fr(spec: Path, root: Path, lines: list[str]) -> list[dict]:
    """Check every BR/SM/ALG/INT block has **Linked FR:** line (rule: FeatureSpec.linked_fr_missing)."""
    text = "\n".join(lines)
    missing = find_blocks_missing_linked_fr(text)
    issues = []
    for blk in missing:
        try:
            loc = str(spec.relative_to(root))
        except ValueError:
            loc = str(spec)
        issues.append({
            "validator": VALIDATOR,
            "severity": "critical",
            "rule_id": "FeatureSpec.linked_fr_missing",
            "location": {"file": loc, "line": blk["heading_line"] + 1},
            "message": f"{blk['code']} block missing required '**Linked FR:**' line"
        })
    return issues


def _issue(sev, rid, spec, root, line, msg):
    try:
        loc = str(spec.relative_to(root))
    except ValueError:
        loc = str(spec)
    return {"validator": VALIDATOR, "severity": sev, "rule_id": rid,
            "location": {"file": loc, "line": line}, "message": msg}


# v27.0.0 (P11 / class 1) — widened from a strict "path:N-M right after
# **Source:**" anchor. The real corpus's block Source lines legitimately use
# THREE shapes the strict anchor rejected:
#   1. a comma-separated multi-path list where an EARLIER citation lacks a
#      line range but a LATER one has it (`` `config/initializers/` (not
#      read — implied by omniauth gem setup), `app/…/omniauth_service.rb:
#      229-270` ``) — the strict anchor only ever inspected the first token;
#   2. a bare file/dir reference with NO line range, honestly annotated as
#      unconfirmed (`` `app/services/listing_form_view_utils.rb` (exact
#      lines unconfirmed — file not read) ``) — still traceable to a real
#      location, which is the rule's actual job;
#   3. a non-path citation naming another concrete artifact or a
#      permission/feature ID (`feature-list.md (PERM051_AdminExportData)`,
#      `PERM029_ManagePaymentSettings (EnsureCanAccessPerson)`).
# A contentless "**Source:**" (nothing, or free-form prose with no locatable
# reference, e.g. "N/A") must still fail — see the negative tests. Widening
# this must NOT accept a line with no real reference at all.
#
# REWORK (adversarial review finding 3, MEDIUM): the bare-filename shape
# (no slash) used to be one alternative scanned for ANYWHERE on the line via
# `.*?` — so any ordinary prose sentence that happened to END in a
# `word.ext`-shaped token matched too (`**Source:** This is fine.txt`,
# `**Source:** ok.md`). It is now split out of the generic scan and matched
# on its own, ANCHORED so it must BE the citation — the entire remainder of
# the line, not a token buried inside a sentence — and its stem must contain
# a hyphen/underscore, the shape of a real repo filename
# (`feature-list.md`), never a plain short English word that merely ends in
# ".ext" (`ok`, `fine`). The real corpus's only non-path bare-filename
# citation, `**Source:** feature-list.md (PERM051_AdminExportData)`, keeps
# passing: anchored start, hyphenated stem, optional trailing parenthetical.
_SOURCE_CITATION_TOKEN_RE = (
    r"[\w./-]+:\d+(?:-\d+)?"          # shape 1: path:N or path:N-M
    r"|[\w.-]{2,}(?:/[\w.-]{2,})+/?"  # shape 2: a multi-segment file/dir path with
                                      # no line range, e.g. `app/services/stripe_service/`
                                      # (each segment >=2 chars — rejects "N/A")
    r"|[A-Z][A-Z0-9]*_[A-Za-z0-9]+"   # shape 4: an ALLCAPS_Snake permission/feature ID
)
# shape 3: a bare filename (no slash), matched separately and ANCHORED (see
# rework note above) — it must be the whole remainder of the line (optional
# backticks, optional trailing "(...)" annotation), and its stem must carry a
# hyphen/underscore, e.g. `feature-list.md`, `some-file.txt`.
_SOURCE_BARE_FILENAME_RE = r"`?[\w]*[_-][\w-]*\.[A-Za-z]{1,8}`?(?:\s*\([^)]*\))?\s*$"
_SOURCE_LINE_RE = re.compile(
    r"^\*\*Source:\*\*\s+(?:\S.*?(?:" + _SOURCE_CITATION_TOKEN_RE + r")"
    r"|" + _SOURCE_BARE_FILENAME_RE + r")",
    re.MULTILINE,
)
# Canonical `## Source Code References` table-row citation: a Markdown table row whose
# cells contain a backtick-wrapped `path:N` / `path:N-M`. This is the format emitted by
# templates/technical-spec-template.md (| Symbol | Path | Purpose |) and parsed for SHA
# tracking (see references/incremental-state-schema.md). Header/separator rows carry no
# backtick path:line and are correctly ignored.
_SOURCE_TABLE_ROW_RE = re.compile(r"^\s*\|.*`[^`\n:]+:\d+", re.MULTILINE)
# v27.0.0 (P11 / class 1) — a `**kind:** ui` State Machine tracks client-local view
# state (useState/ref/signal — never persisted), so it has no single backend file:line
# to cite. This is the CANONICAL shape: templates/technical-spec-template.md's own
# SM-002 example (`kind: ui`) carries no **Source:** line at all, unlike its `entity`
# sibling (SM-001, persisted, DB-backed) which does. Only `ui` is exempt.
_SM_KIND_UI_RE = re.compile(r"^\*\*kind:\*\*\s*ui\s*$", re.MULTILINE)
# v27.0.0: identifies an ALG-### block heading by its trailing `(ALG-NNN)` tag — the
# code no longer sits at the start of the heading (see BLOCK_HEADING_PREFIX_RE).
_ALG_BLOCK_TAG_RE = re.compile(r"\(ALG-\d{3}\)\s*$")

# ---------------------------------------------------------------------------
# P09 (human-readable SOT) — technical-spec.md 5-bucket retaxonomy checks.
#
# Degradation sentinel mirrors _FUNC_PRE_SOT_SENTINEL's design exactly (same
# pattern, not a third one): the OLD shape's own distinguishing heading, never
# present in the new shape, not the absence of a new heading. `## Cross-Cutting
# Logic` is retired outright by the 5-bucket retaxonomy, so its presence
# unambiguously marks a still-old-shaped file.
# ---------------------------------------------------------------------------
_TECH_PRE_SOT_SENTINEL = "## Cross-Cutting Logic"

# ## 4. Technical Behavior by Capability: H3 children are DYNAMIC, one
# `### 4.N {Capability}` per CAP-N row in the twin functional-spec.md § 2.
_CAP_BUCKET_H3_RE = re.compile(r"^### 4\.(\d+) ")
# C15 (phase 03c) — the new shape's capability structure IS `## 3. Actions`
# itself (wire-format-contract.md § 3: `### 3.N CAP-NN — title`). Unlike the old
# heading above, the CAP number is literally embedded in the text, so this
# extracts the ACTUAL capability number (group 1) rather than assuming the
# section-local ordinal `N` in `3.N` lines up with it positionally.
_CAP_BUCKET_H3_NEW_RE = re.compile(r"^### \d+\.\d+ CAP-(\d+)\b")
# functional-spec.md § 2's own ID column (templates/functional-spec-template.md
# § 2: `| CAP-01 | ... |`) — a bare table-cell code, no bold markup.
_CAP_TWIN_ROW_RE = re.compile(r"^\|\s*CAP-(\d+)\s*\|", re.MULTILINE)

_TABLE_SEP_CELL_RE = re.compile(r"^:?-+:?$")
_WHAT_HAPPENS_RE = re.compile(r"\*\*What happens:\*\*")
_GWT_WORD_RE = re.compile(r"\bGiven\b|\bWhen\b|\bThen\b")
_MAPPING_NAME_MAX_LEN = 120


def _table_rows(lines: list[str], start: int, end: int, header_first_cell: str) -> list[list[str]]:
    """Parse `| a | b | c |` content rows in `lines[start:end]`, skipping the header
    row (identified by its first cell, case-insensitively) and any `|---|` separator
    row. Does not assume the header is the first `|`-row seen (defensive against
    stray prose lines that happen to start with `|`)."""
    rows: list[list[str]] = []
    for ln in lines[start:end]:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells:
            continue
        if cells[0].lower() == header_first_cell.lower():
            continue
        if all(_TABLE_SEP_CELL_RE.match(c) for c in cells):
            continue
        rows.append(cells)
    return rows


# ---------------------------------------------------------------------------
# Phase 02 (action-thread reshape, D2/D4) — § 2 Action Index binding + § 3 rung
# structure. Five rule_ids: FeatureSpec.action_index_missing, action_unclaimed,
# action_key_not_handler, rung_order, rung_empty_rendered. A sixth,
# `action_double_claimed`, shipped in phase 02 and was RETIRED (not degraded —
# removed outright, code and tests together) once phase 11's real-corpus run
# showed it modelled a partition ("every code claimed by exactly one row") onto
# a relation that fans out by design (one requirement, several handling
# actions). See `_check_action_thread`'s docstring and ADR-0006's addendum for
# the corpus numbers behind the removal. Parsing lives in `_action_thread_lib`;
# everything here is wiring only (Architecture note, phase-02.md).
#
# Phase 01 (self-sufficiency v27.8) adds a 6th LIVE rule_id here:
# `FeatureSpec.state_rung_missing` — an ordinary batched check exactly like its
# five siblings above, wired into the SAME per-block loop that already computes
# `rung_order`/`rung_empty_rendered` (D7: no second `would_fire`-shaped entry
# point; phase 02's reopen predicate consumes this function's own issue list).
# ---------------------------------------------------------------------------

# D4 — a rendered rung whose body is empty, "N/A", or "None." (any casing/trailing
# period). The wire-format contract requires an ABSENT rung to be omitted entirely,
# never stubbed with one of these — that stub shape is exactly what this fires on.
_RUNG_EMPTY_RE = re.compile(r"^(n/a|none\.?)$", re.IGNORECASE)

# D8 (self-sufficiency v27.8, post-measurement re-anchor, plans/260824-1846-...) —
# `state_rung_missing`'s anchor moved from "this action's own § 2 Codes cell carries
# an SM-### token" (measured firing surface: 1 action in the whole 43-feature
# corpus, HALT — SM-### codes sit overwhelmingly on the cross-cutting A0 row, not on
# individual writing actions) to a DOCUMENT-LEVEL fact: does this feature genuinely
# model a state machine at all? A real `### <sentence> (SM-###)` heading block
# (confirmed on the corpus: § 4.3 State Management's own heading shape, H3) is that
# fact — structural, never inferred, so D3 ("never prose-sniff a FROM state") is
# untouched: D3 forbids inferring the *transition*, not noticing the heading's
# absence. Reuses the ALREADY-IMPORTED `SM_BLOCK_RE` (`_spec_block_lib.py`) rather
# than a second heading-anchored code-family regex — `test_spec_constants_single_
# source.py` enforces exactly one compile site for this shape, and the real corpus
# only ever produces the H3 form `SM_BLOCK_RE` already matches. Measured: 95
# actions across 14 features carry this heading AND write — computed ONCE per spec
# below, never recomputed per action block.


def _thread_sev_msg(is_degraded: bool, base_sev: str, msg: str,
                     *, reason: str = "_pre_thread") -> tuple[str, str]:
    """D4 degradation, applied at the single emit site (`_check_action_thread`'s
    `emit` closure) for all 6 action-thread codes. While the file still carries
    `_TECH_PRE_THREAD_SENTINEL` ('## 3. System Design' — the OLD layer-first shape's
    own distinguishing heading, never present in the new action-thread shape), every
    code degrades from its base severity to `warning` and its message gains a
    `(_pre_thread)` suffix — a 43-feature corpus must not go red all at once
    mid-migration (mirrors `_FUNC_PRE_SOT_SENTINEL`/`_TECH_PRE_SOT_SENTINEL`'s
    WARN-first window). `action_key_not_handler`'s base severity is already
    `warning`, so degradation is a severity no-op for it — but its message still
    gains the suffix, since the signal "this file is mid-migration" applies
    uniformly to all 6 codes regardless of their individual base severity. Past the
    window (sentinel absent): full base severity, unsuffixed message.

    `reason` overrides the message suffix for a DIFFERENT degradation window
    reusing this same mechanism — e.g. `diagram_required_missing`'s fill-pending
    window (`_action_thread_diagram_lib.is_fill_pending`) passes
    `reason="_pre_fill"` so its warning message does not falsely claim the file
    is still shape-pre-thread when it is, in fact, fully reshaped and merely
    awaiting the researcher fill pass. Every existing call site omits it and
    keeps the original `(_pre_thread)` text unchanged."""
    if is_degraded:
        return "warning", msg + f" ({reason})"
    return base_sev, msg


def _check_action_thread(lines: list[str], headings: list, h2: list,
                          spec: Path, root: Path) -> list[dict]:
    """§ 2 Action Index binding + § 3 rung structure (D2/D4). Gated on `## 2. Action
    Index` actually being present: a file still sitting in the legacy 5-bucket shape
    (`_LEGACY_TECH_H2_5BUCKET` — a real state a repo may be in between running the
    `feature-sot` and `action-thread` migrate steps) has no such heading and must see
    NOTHING new from this function. `test_technical_spec_sot_validation.py::
    TestBaselineIsClean` asserts `_check_technical_spec` returns `[]` on today's baseline
    shape; that baseline has no '## 2. Action Index', so this gate is what keeps it at zero.

    FeatureSpec.action_index_missing (critical): '## 2. Action Index' absent, or
      present with zero data rows. SILENT input: >=1 data row — including a feature
      whose ONLY row is the mandatory `A0` (corpus-measured: F016/F017/F029 have zero
      endpoints AND zero DB events; the reserved cross-cutting A0 row is what keeps
      the table non-empty for them). When this fires, the declared-vs-claimed checks
      below are skipped for the file — deliberately NOT the `cap.code_unclaimed`
      SA-2 "compute the reverse check unconditionally" pattern, because unlike § 2
      Functional Capabilities, THIS table has its own "the table itself is missing"
      finding; piling on one `action_unclaimed` per declared code on top of it would
      be redundant noise about the same empty table, not new information.

    FeatureSpec.action_unclaimed (critical, message opens with "family="): a
      US###/FR-###/BR-###|DEC-###|SM-### declared anywhere in § 3 Actions or § 4
      Shared Foundation that is claimed by zero § 2 rows (A0 included). SILENT
      input: every declared code appears in some row's Codes column.

    FeatureSpec.action_double_claimed — RETIRED (was: critical, a code claimed by
      >=2 rows). The wire-format contract's original rule ("every code must appear
      in exactly one row's Codes") copied `cap.double_claimed`'s partition model
      from § 2 Functional Capabilities, where it is correct. Actions are not a
      partition of their codes: one requirement legitimately fans out to several
      handling actions (e.g. an export request/poll/generate triple, or an
      approve/reject pair sharing one requirement) — this is the normal shape,
      not a defect. Measured on the 43-feature/430-action corpus: 127 firings
      across 31/43 features, 85% of them a claim-width of exactly 2, including on
      the plan's own hand-authored B-v reference sample. Removed outright rather
      than demoted to a threshold-gated warning: the real distribution has no
      natural cutoff that separates "implausible fan-out" from "a feature with a
      few more handlers" (widths 2 through 10 form one continuous tail, not two
      populations), so any threshold would be a guess re-introducing the same
      modelling error at one remove. `action_unclaimed` below is unaffected and
      is the check that keeps the § 2 binding real: every declared code must be
      claimed by AT LEAST one row (completeness, not exclusivity).

    FeatureSpec.action_key_not_handler (warning): a non-A0 row's Action (handler)
      cell is the bare `` `METHOD PATH` `` fallback shape (D2: the handler IS the
      action's identity; `` `Class#method` `` is the norm, this fallback is reserved
      for a genuinely unparseable handler). SILENT input: every non-A0 row's handler
      cell is `` `Class#method` `` shaped.

    FeatureSpec.rung_order (critical): rungs inside one action block appear out of
      `RUNG_LABELS` order. SILENT input: whichever rungs a block DOES carry appear in
      that relative order — presence of every rung is never required.

    FeatureSpec.rung_empty_rendered (critical): see `_RUNG_EMPTY_RE`. SILENT input:
      every rendered rung has a real, non-stub body.

    FeatureSpec.state_rung_missing (warning, degrades identically to
      `diagram_required_missing` — BOTH `is_pre_thread` and `is_fill_pending`, D5):
      D8 re-anchor (post phase-00 measurement — the original per-action Codes-cell
      anchor fired on 1 action in the whole 43-feature corpus, HALT). Fires when
      BOTH hold: (1) the feature carries a real `### <sentence> (SM-###)` heading
      block ANYWHERE in the document (`SM_BLOCK_RE`, computed ONCE per
      spec, never per block — a document-level fact, "does this feature model a
      state machine at all"), AND (2) this action block's § 2 row carries a
      non-`—` Writes cell — but the block renders no `**State**` rung. D3:
      structural, never prose-sniffed — the heading's presence is a fact about the
      document, not an inference about the transition; D3 forbids inferring the
      FROM state from a method name or body text, which this still never does.
      SILENT inputs (three, named): (a) a writing action inside an SM-modelled
      feature that ALREADY renders a `**State**` rung; (b) a read-only action
      (Writes cell is `—`), regardless of whether the feature models a state
      machine; (c) **a feature with NO SM heading block at all**, regardless of
      whether this action writes — this is the input that keeps the check off the
      29 of 43 features that model no state machine at all, and is the whole
      reason the measured population is 95, not 180 (the wider "any write in an
      SM-anchored action's own row" reading). Known, accepted miss (not a defect
      to chase): a boolean-flip write like `open: false` in a feature with no SM
      block is never flagged — inferring a state machine from the flip would be
      exactly the prose-sniffing D3 forbids.

    Degradation (D4): see `_thread_sev_msg`.
    """
    issues: list[dict] = []
    h2_names = [h for _, h in h2]
    b_idx = _bounds(h2, "## 2. Action Index", len(lines))
    if not b_idx:
        return issues
    is_pre_thread = _TECH_PRE_THREAD_SENTINEL in h2_names
    # `state_rung_missing` ONLY (D5) — every other rule_id in this function keeps
    # `is_pre_thread` alone, same split `diagram_required_missing` already uses.
    is_fill_pending = _action_thread_diagram_lib.is_fill_pending("\n".join(lines))
    # D8 — document-level fact, computed ONCE per spec (never per action block):
    # does this feature carry a real SM-anchored state-machine heading at all?
    # Reuses `SM_BLOCK_RE` (already imported) rather than a second regex.
    has_sm_block = any(SM_BLOCK_RE.match(h) for _, h in headings)

    def emit(base_sev: str, rid: str, line: int | None, msg: str) -> None:
        sev, full_msg = _thread_sev_msg(is_pre_thread, base_sev, msg)
        issues.append(_issue(sev, rid, spec, root, line, full_msg))

    b_actions = _bounds(h2, "## 3. Actions", len(lines))
    rows = _action_thread_lib.parse_action_index(lines, b_idx)
    if not rows:
        emit("critical", "FeatureSpec.action_index_missing", b_idx[0] + 1,
             "## 2. Action Index has zero data rows — the mandatory A0 row must "
             "always be present, even for a feature that resolves zero actions")
    else:
        for row in rows:
            if row["id"] != "A0" and _action_thread_lib.is_handler_fallback(row["key"]):
                emit("warning", "FeatureSpec.action_key_not_handler", row["line"] + 1,
                     f"{row['id']}'s Action (handler) cell {row['key']!r} is the bare "
                     "`METHOD PATH` fallback shape — reserved for a genuinely "
                     "unparseable handler (D2: the handler IS the action's identity)")

        b_shared = _bounds(h2, "## 4. Shared Foundation", len(lines))
        declared_text = "\n".join(
            (lines[b_actions[0]:b_actions[1]] if b_actions else [])
            + (lines[b_shared[0]:b_shared[1]] if b_shared else [])
        )
        claims: dict[str, list[str]] = {}
        for row in rows:
            codes_text = ", ".join(row["codes"])
            for fam in ("US", "FR", "BR"):
                for m in _FAMILY_CODE_RE[fam].finditer(codes_text):
                    claims.setdefault(m.group(), []).append(row["id"])
        for fam in ("US", "FR", "BR"):
            declared = set(_FAMILY_CODE_RE[fam].findall(declared_text))
            for code in sorted(declared - set(claims)):
                emit("critical", "FeatureSpec.action_unclaimed", b_idx[0] + 1,
                     f"family={fam} {code} is declared in § 3 Actions/§ 4 Shared "
                     "Foundation but claimed by no § 2 Action Index row (nor A0)")
        # `FeatureSpec.action_double_claimed` (a code claimed by >=2 rows) was
        # RETIRED here (not degraded, removed outright — see the docstring above
        # and ADR-0006's addendum). It modelled actions as a PARTITION of their
        # codes, copied from `cap.double_claimed` where § 2 Functional
        # Capabilities genuinely does partition. Actions do not: one requirement
        # fanning out to several handlers (e.g. FR-203 across "request export",
        # "poll status", "generate file") is the normal shape, not a defect.
        # Measured on the 43-feature corpus: 127 firings across 31/43 features,
        # 85% of them width=2 — a fan-out this common is the corpus, not noise.
        # `claims` above still exists solely to feed `action_unclaimed`, which
        # is the check that survives: every declared code must be claimed by AT
        # LEAST one row (or A0). That completeness requirement is unchanged.

    if b_actions:
        rows_by_id = {r["id"]: r for r in rows}
        for block in _action_thread_lib.action_blocks(headings, len(lines)):
            if not (b_actions[0] <= block["heading_line"] < b_actions[1]):
                continue
            ids_label = "/".join(block["ids"]) or "?"
            block_rungs = _action_thread_lib.rungs(lines, block)
            present = [lbl for lbl, _ in block_rungs]
            expected = [lbl for lbl in RUNG_LABELS if lbl in present]
            if present != expected:
                emit("critical", "FeatureSpec.rung_order", block["heading_line"] + 1,
                     f"{ids_label} rungs out of order: have {present}, contract "
                     f"order is {list(RUNG_LABELS)}")
            for label, body in block_rungs:
                if not body or _RUNG_EMPTY_RE.match(body):
                    emit("critical", "FeatureSpec.rung_empty_rendered",
                         block["heading_line"] + 1,
                         f"{ids_label}'s **{label}** rung is rendered {body!r} — an "
                         "absent rung must be omitted, not stubbed")

            # --- state_rung_missing (D3/D8) ----------------------------------
            # D8: anchor is document-level (`has_sm_block`, computed once above)
            # AND this block's own Writes cell — no longer the action's own Codes
            # cell (see the docstring for the corpus reasoning behind the move).
            block_rows = [rows_by_id[i] for i in block["ids"] if i in rows_by_id]
            needs_state = has_sm_block and any(r["tables"] for r in block_rows)
            if needs_state and "State" not in present:
                sev, msg = _thread_sev_msg(
                    is_pre_thread or is_fill_pending, "warning",
                    f"{ids_label} writes (Writes cell non-empty) in a feature that "
                    "models a state machine (§ 4.3 carries a real SM-### heading "
                    "block) but renders no **State** rung",
                    reason="_pre_thread" if is_pre_thread else "_pre_fill")
                issues.append(_issue(sev, "FeatureSpec.state_rung_missing",
                                      spec, root, block["heading_line"] + 1, msg))
    return issues


# ---------------------------------------------------------------------------
# Phase 03 (rule bins + diagram contract) — § 4.4 three-bin placement + the
# diagram-required threshold + the two diagram-hygiene checks. Five new rule_ids:
# FeatureSpec.rule_bin_misplaced, crosscutting_unlabelled, diagram_required_missing,
# diagram_cites_file_line, diagram_over_cap. Parsing lives in
# `_action_thread_diagram_lib`; everything here is wiring, same split as phase 02.
# ---------------------------------------------------------------------------

# `Used in: A2, A3` — the bin-2 marker (wire-format-contract.md § 4.4). Matched
# ANYWHERE in the document (not scoped to a heading first) because the check that
# consumes it cares about WHERE the marker physically sits (§ 3 vs § 4.4), not
# about re-deriving section structure twice.
_USED_IN_RE = re.compile(r"Used in:\s*(.+)")
_ACTION_ID_IN_TEXT_RE = re.compile(ACTION_ID_RE)


def _paragraphs(lines: list[str], start: int, end: int) -> list[tuple[int, int]]:
    """Contiguous non-blank line runs in `lines[start:end]`, as `(p_start, p_end)`
    (end exclusive) — the unit `crosscutting_unlabelled` treats as "one rule
    entry" (bold title line + description + optional `Used in:`/`**Source:**`
    lines, blank-line-terminated, same paragraph shape every § 4.4 entry in the
    wire-format contract uses)."""
    paras: list[tuple[int, int]] = []
    i = start
    while i < end:
        if not lines[i].strip():
            i += 1
            continue
        j = i
        while j < end and lines[j].strip():
            j += 1
        paras.append((i, j))
        i = j
    return paras


def _check_rule_bins_and_diagrams(lines: list[str], headings: list, h2: list,
                                   spec: Path, root: Path) -> list[dict]:
    """§ 4.4 three-bin placement + the diagram contract (phase 03). Gated
    IDENTICALLY to `_check_action_thread` (`## 2. Action Index` present) — a
    separate sibling function rather than an edit to that one, so phase 02's
    landed code stays untouched.

    FeatureSpec.rule_bin_misplaced (warning): a `Used in:` marker naming >=2
      actions found inside § 3 Actions (belongs promoted to § 4.4 Bin 2), OR a
      `Used in:` marker naming exactly 1 action found inside § 4.4 (belongs
      inline in that one action's § 3 block, Bin 1). SILENT input: every
      `Used in:` marker's action count matches the bin its physical section
      implies (>=2 only in § 4.4, exactly 1 only inline in § 3 — never fires on
      one found outside both sections, e.g. § 4.5's own `Used in:` line for an
      algorithm/integration, which is a different marker family entirely).

    FeatureSpec.crosscutting_unlabelled (warning): inside § 4.4, an FR/BR/DEC/SM
      rule paragraph carrying no `Used in:` list, whose enclosing `#### ` bin
      heading (or the absence of one) does not contain the word "cross-cutting".
      SILENT input: every codeless-of-Used-in § 4.4 paragraph sits under a
      heading that says so (Bin 3's own heading always does).

    FeatureSpec.diagram_required_missing (critical, degrades to warning while
      fill-pending — see below): an action over the diagram threshold
      (`_action_thread_diagram_lib.is_over_threshold`) whose CAPABILITY BUCKET
      (not just its own § 3 H4 block — the wire-format contract lets one
      diagram cover a whole bucket's handlers) carries no mermaid fence.
      SILENT input: every over-threshold action's bucket carries at least one
      mermaid fence somewhere in it.

      Fill-pending window (this follow-up): a freshly `compose_action_thread`d
      file cannot carry a diagram yet — diagrams need judgment and are authored
      in the SAME researcher fill pass that resolves rule ownership. While the
      file carries the `[UNVERIFIED]` marker
      (`_action_thread_diagram_lib.is_fill_pending`), this one finding degrades
      to `warning` with an `(_pre_fill)` message suffix; every other finding in
      this function is unaffected. Once the fill pass resolves every rule
      (marker count reaches 0), a missing diagram goes back to a hard critical
      — the window never re-opens on a fully-bound file.

    FeatureSpec.diagram_cites_file_line (critical): a `path:line`-shaped token
      inside any mermaid fence. SILENT input: no mermaid fence in the document
      contains one.

    FeatureSpec.diagram_over_cap (warning, never critical — arrow/`alt` counting
      is a heuristic that can miscount): a single mermaid fence with >12 arrow
      lines or >2 `alt` lines. SILENT input: every fence stays at or under both
      caps.

    Degradation (D4): see `_thread_sev_msg` (reused, not re-derived).
    """
    issues: list[dict] = []
    h2_names = [h for _, h in h2]
    b_idx = _bounds(h2, "## 2. Action Index", len(lines))
    if not b_idx:
        return issues
    is_pre_thread = _TECH_PRE_THREAD_SENTINEL in h2_names
    # Fill-pending window (this follow-up) — `diagram_required_missing` ONLY;
    # every other rule_id in this function keeps `is_pre_thread` alone.
    is_fill_pending = _action_thread_diagram_lib.is_fill_pending("\n".join(lines))

    def emit(base_sev: str, rid: str, line: int | None, msg: str) -> None:
        sev, full_msg = _thread_sev_msg(is_pre_thread, base_sev, msg)
        issues.append(_issue(sev, rid, spec, root, line, full_msg))

    rows = _action_thread_lib.parse_action_index(lines, b_idx)
    b_actions = _bounds(h2, "## 3. Actions", len(lines))
    b_shared = _bounds(h2, "## 4. Shared Foundation", len(lines))
    b_44 = _bounds_at(headings, "### ", "### 4.4 Shared Rules", b_shared[1]) if b_shared else None

    def _in(bounds: tuple[int, int] | None, i: int) -> bool:
        return bounds is not None and bounds[0] <= i < bounds[1]

    # --- rule_bin_misplaced --------------------------------------------------
    used_in_hits: list[tuple[int, list[str]]] = []
    for i, ln in enumerate(lines):
        m = _USED_IN_RE.search(ln)
        if m:
            used_in_hits.append((i, _ACTION_ID_IN_TEXT_RE.findall(m.group(1))))

    for i, ids in used_in_hits:
        if _in(b_actions, i) and len(ids) >= 2:
            emit("warning", "FeatureSpec.rule_bin_misplaced", i + 1,
                 f"'Used in:' names {len(ids)} actions ({', '.join(ids)}) but sits "
                 "inline in § 3 — a rule used by >=2 actions belongs in § 4.4 Bin 2")
        elif _in(b_44, i) and len(ids) == 1:
            emit("warning", "FeatureSpec.rule_bin_misplaced", i + 1,
                 f"'Used in:' names exactly one action ({ids[0]}) but sits in § 4.4 "
                 "— a single-action rule belongs inline in that action's § 3 block")

    # --- crosscutting_unlabelled ---------------------------------------------
    if b_44:
        used_in_lines = {i for i, _ in used_in_hits}
        h4_in_44 = [(idx, h) for idx, h in headings if h.startswith("#### ") and _in(b_44, idx)]
        regions: list[tuple[int, int, str | None]] = []
        first = h4_in_44[0][0] if h4_in_44 else b_44[1]
        if b_44[0] < first:
            regions.append((b_44[0], first, None))
        for k, (idx, h) in enumerate(h4_in_44):
            nxt = h4_in_44[k + 1][0] if k + 1 < len(h4_in_44) else b_44[1]
            regions.append((idx + 1, nxt, h))
        for start, end, heading in regions:
            if heading is not None and "cross-cutting" in heading.lower():
                continue
            for p_start, p_end in _paragraphs(lines, start, end):
                has_code = any(_FAMILY_CODE_RE["FR"].search(lines[k])
                               or _FAMILY_CODE_RE["BR"].search(lines[k])
                               for k in range(p_start, p_end))
                has_used_in = any(k in used_in_lines for k in range(p_start, p_end))
                if has_code and not has_used_in:
                    emit("warning", "FeatureSpec.crosscutting_unlabelled", p_start + 1,
                         "§ 4.4 rule has no 'Used in:' action list and its enclosing "
                         "heading carries no explicit cross-cutting label")

    # --- diagram_required_missing --------------------------------------------
    fences = _action_thread_diagram_lib.mermaid_fences(lines)
    if b_actions:
        rows_by_id = {r["id"]: r for r in rows}
        buckets = _action_thread_diagram_lib.capability_buckets(headings, b_actions)
        for block in _action_thread_lib.action_blocks(headings, len(lines)):
            if not _in(b_actions, block["heading_line"]):
                continue
            block_rows = [rows_by_id[i] for i in block["ids"] if i in rows_by_id]
            if not any(_action_thread_diagram_lib.is_over_threshold(r) for r in block_rows):
                continue
            scope = next(
                (bd for bd in buckets if bd[0] <= block["heading_line"] < bd[1]),
                (block["heading_line"], block["end"]),
            )
            has_fence = any(f["start"] < scope[1] and f["end"] > scope[0] for f in fences)
            if not has_fence:
                ids_label = "/".join(block["ids"]) or "?"
                # Bypasses the shared `emit()` closure deliberately: every other
                # rule_id in this function degrades on `is_pre_thread` alone, but
                # this ONE finding also degrades on `is_fill_pending` (the
                # researcher fill pass legitimately has not authored a diagram
                # yet) — `reason="_pre_fill"` keeps the warning message honest
                # about which window is open when `is_pre_thread` is False.
                sev, msg = _thread_sev_msg(
                    is_pre_thread or is_fill_pending, "critical",
                    f"{ids_label} writes >=2 tables or is background/async — over "
                    "the diagram threshold — but its capability bucket carries no "
                    "mermaid sequenceDiagram",
                    reason="_pre_thread" if is_pre_thread else "_pre_fill")
                issues.append(_issue(sev, "FeatureSpec.diagram_required_missing",
                                      spec, root, block["heading_line"] + 1, msg))

    # --- diagram_cites_file_line / diagram_over_cap --------------------------
    for f in fences:
        for tok in _action_thread_diagram_lib.file_line_tokens(f["body"]):
            emit("critical", "FeatureSpec.diagram_cites_file_line", f["start"] + 1,
                 f"mermaid fence contains a file:line token {tok!r} — rungs carry "
                 "facts (including file:line), diagrams carry order/branching only")
        arrows, alts = _action_thread_diagram_lib.count_arrows_and_alts(f["body"])
        if arrows > 12 or alts > 2:
            emit("warning", "FeatureSpec.diagram_over_cap", f["start"] + 1,
                 f"mermaid fence has {arrows} arrow line(s) / {alts} alt block(s) — "
                 "over the 12-arrow/2-alt cap (heuristic count, never a critical)")

    return issues


# ---------------------------------------------------------------------------
# Phase 03 (self-sufficiency v27.8) — `action_ref_unglossed`: ONE refined bare-
# reference check across six families, warning severity. Same wiring shape as
# `crosscutting_unlabelled`: a sibling function gated identically to
# `_check_action_thread`/`_check_rule_bins_and_diagrams` (`## 2. Action Index`
# present). plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8,
# phase-03-action-ref-unglossed-check.md.
# ---------------------------------------------------------------------------

# Lifted VERBATIM (family set, `(?<![\w-])`/`(?!\d)` boundaries, and the
# gloss-threshold arithmetic below) from phase 00's measurement script
# (m1-m2-m3.py `CODE_RE`/`is_glossed_line`) so this check and the measurement
# that sized it (M1=21 total: BR 20, DEC 1) can never disagree. Six families
# only — BR, DEC, SM, ALG, INT, DISC; FR/US are deliberately excluded, matching
# the research report's own scope (D2, plan.md) and the measurement script's.
# Uses `(?<![\w-])` (not a leading `\b`) at the LEADING edge to byte-match the
# measurement's own regex; `(?!\d)` (never a trailing `\b`) at the TRAILING
# edge is the same hazard already documented at `_FAMILY_CODE_RE` above — a
# trailing `\b` never matches past the digits in a `BR-001_Slug` shape because
# `_` is a word character. This repo has hit this hazard 7 times in 3 variants.
_ACTION_REF_CODE_RE = re.compile(r"(?<![\w-])(BR|DEC|SM|ALG|INT|DISC)-(\d{3})(?!\d)")


def _action_ref_is_glossed(line: str) -> bool:
    """True iff >=12 alphanumeric characters remain on `line` after every
    family-code token (`_ACTION_REF_CODE_RE`) is stripped out and all
    remaining non-alphanumeric characters (markdown noise: backticks,
    asterisks, pipes, punctuation, whitespace) are discarded. Lifted VERBATIM
    from phase 00's `is_glossed_line` (m1-m2-m3.py) — the check and the
    measurement that sized it must apply the identical threshold or they will
    silently drift apart."""
    stripped = _ACTION_REF_CODE_RE.sub("", line)
    alnum = re.sub(r"[^A-Za-z0-9]", "", stripped)
    return len(alnum) >= 12


def _check_action_ref_unglossed(lines: list[str], headings: list, h2: list,
                                 spec: Path, root: Path) -> list[dict]:
    """FeatureSpec.action_ref_unglossed (warning). ONE refined bare-reference
    check spanning six families (BR/DEC/SM/ALG/INT/DISC). Gated identically to
    `_check_action_thread`/`_check_rule_bins_and_diagrams` (`## 2. Action
    Index` present) and further scoped to `## 3. Actions` (mirrors the
    measurement script's own section restriction).

    Unit: one `#### A<n>` block (`_action_thread_lib.action_blocks`), text
    spanning the H4 HEADING LINE ITSELF (the "context line" where 100% of the
    corpus's bare codes physically sat, per phase 00's M3) through the block's
    end — not just the block's body.

    Fires when: a family code appears anywhere in the block, and EVERY
    occurrence of that exact code inside the block is bare (fails
    `_action_ref_is_glossed`) — i.e. no single occurrence of that code, however
    many times it recurs, ever carries a clearing gloss anywhere in the block.

    Naive alternative REJECTED (measured, not assumed — the naive predicate
    does not exist anywhere in this file outside this docstring): flag any bare
    occurrence in the H4 context line alone, ignoring whether the same code is
    glossed elsewhere in the block. On the 43-feature corpus this refined
    predicate flags 21 (BR 20, DEC 1) at 100% precision (all 21 hand-verified
    genuine); the naive predicate flags 99 at a 21% precision floor (21/99) —
    the same low-precision shape (~7-10%) this repo already rejected in
    v27.6.0 (D2, plan.md), only somewhat less severe on this corpus state.

    SILENT inputs (three, named): (a) a block where every cited code has AT
    LEAST ONE occurrence carrying a gloss — the common case, measured at 247 of
    266 code-citations (93%) on the corpus; (b) a block with no family code at
    all; (c) a code that appears ONLY outside any `## 3. Actions` block (a § 4.4
    Shared Rules entry, for instance) — that is `crosscutting_unlabelled`'s
    ground, never this check's.

    Fence-aware: reuses `_md_scan_lib.mask_fenced` (the shared fence-walk
    primitive `derive_confidence_report.py` and four other validators already
    converge on, rather than a second one) to blank every fenced line before
    scanning — a code inside a ```mermaid``` fence is never a citation.

    Degradation: `is_pre_thread or is_fill_pending` — the same fill-pending
    window `diagram_required_missing`/`state_rung_missing` already use (a
    freshly composed, not-yet-researcher-filled file cannot be expected to have
    glossed every bare reference yet).
    """
    issues: list[dict] = []
    h2_names = [h for _, h in h2]
    b_idx = _bounds(h2, "## 2. Action Index", len(lines))
    if not b_idx:
        return issues
    b_actions = _bounds(h2, "## 3. Actions", len(lines))
    if not b_actions:
        return issues
    is_pre_thread = _TECH_PRE_THREAD_SENTINEL in h2_names
    is_fill_pending = _action_thread_diagram_lib.is_fill_pending("\n".join(lines))

    masked_lines = _md_scan_lib.mask_fenced("\n".join(lines)).split("\n")

    for block in _action_thread_lib.action_blocks(headings, len(lines)):
        if not (b_actions[0] <= block["heading_line"] < b_actions[1]):
            continue
        block_lines = masked_lines[block["heading_line"]:block["end"]]
        occurrences: dict[str, list[bool]] = {}
        for ln in block_lines:
            for m in _ACTION_REF_CODE_RE.finditer(ln):
                code = f"{m.group(1)}-{m.group(2)}"
                occurrences.setdefault(code, []).append(_action_ref_is_glossed(ln))
        ids_label = "/".join(block["ids"]) or "?"
        for code in sorted(c for c, glosses in occurrences.items() if not any(glosses)):
            sev, msg = _thread_sev_msg(
                is_pre_thread or is_fill_pending, "warning",
                f"{ids_label} cites {code} but every occurrence in this block is "
                "bare — no occurrence's line carries a clearing gloss (>=12 "
                "non-code alphanumeric characters)",
                reason="_pre_fill_ref")
            issues.append(_issue(sev, "FeatureSpec.action_ref_unglossed",
                                  spec, root, block["heading_line"] + 1, msg))
    return issues


def _check_technical_spec(spec: Path, root: Path) -> list[dict]:
    # F8: draft relaxes source-evidence rules only; all structural rules stay critical for drafts.
    # Relaxation requires BOTH status: draft AND authored_by: takumi — a draft from any other
    # author is anomalous and gets full strict validation.
    is_draft = read_spec_status(spec) == "draft" and read_authored_by(spec) == "takumi"
    lines = spec.read_text(encoding="utf-8", errors="replace").splitlines()
    headings, blocks = parse_headings_and_blocks(lines)
    scrubbed = strip_html_comments(lines)
    h2 = [(i, h) for i, h in headings if h.startswith("## ") and not h.startswith("### ")]
    out: list[dict] = []
    add = lambda s, r, ln, m: out.append(_issue(s, r, spec, root, ln, m))  # noqa: E731

    # F### heading check: look in first 5 lines after any leading YAML frontmatter fence.
    preamble_start = 0
    if lines and lines[0].rstrip() == "---":
        # Skip past the closing ---
        for _fi in range(1, min(len(lines), 30)):
            if lines[_fi].rstrip() == "---":
                preamble_start = _fi + 1
                break
    if not any(FCODE_HEADING_RE.match(lines[i]) for i in range(preamble_start, min(preamble_start + 5, len(lines)))):
        add("critical", "FeatureSpec.f_code_format", 1, "missing/invalid F### heading in preamble")

    # Universal.no_placeholder — content-level, shape-independent. Runs unconditionally,
    # same as f_code_format above: the tech_sections_pre_sot degradation window mutes
    # rules "defined in terms of the new 5-bucket shape" (see the Degradation Contract in
    # references/verification-checklist-feature-spec.md) but explicitly does NOT mute
    # Universal/cross-ref checks.
    fenced = {i for s, e, _ in blocks for i in range(s, e + 1)}
    for i, raw in enumerate(lines):
        if i in fenced or not PLACEHOLDER_RE.search(scrubbed[i]):
            continue
        add("critical", "Universal.no_placeholder", i + 1, f"placeholder literal in line: {raw.strip()[:80]!r}")
        break

    # Legacy two-section format — "no transition window" per the checklist: fires
    # regardless of tech_sections_pre_sot, unlike every other check below.
    for idx, raw in headings:
        if raw in LEGACY_H2:
            add("critical", "FeatureSpec.legacy_artifact_sections", idx + 1,
                f"legacy section {raw!r} — replace both '## Related Artifacts' and '## Spec Documents' with single '## Artifact References' table (no transition window)")

    # FeatureSpec.retired_section_present (warning, phase 08, self-sufficiency v27.8)
    # — A3 (`## Source Walkthrough`) and B4 (`## DB Impact per Event`) are retired
    # from technical-spec.md this release; their own dedicated validator
    # (validate_reading_guide_db_impact.py) dropped its technical-spec.md call sites
    # for both. Fires regardless of shape — same "no transition window" reasoning as
    # `legacy_artifact_sections` above: a heading this retired can appear on an old
    # 9-section file, a 5-bucket file, or an action-thread file alike, and every one
    # of them needs the same reopen signal. This is also the ONE mechanism that
    # drives `compose_action_thread`'s one-shot strip: it is registered into
    # `_action_thread_reopen_lib.REOPEN_RULE_IDS`, so a `technical-spec.md` already
    # migrated under the OLD (A3/B4-carrying) composer keeps firing this warning
    # until the next `--migrate --only action-thread` strips the section out —
    # never left to rot as a heading nothing checks for any more (D7: no second,
    # re-implemented firing predicate — the reopen module consumes this issue list
    # directly). `screens/*/spec.md` is untouched: this function only ever runs
    # against technical-spec.md (`_check_feature_dir`), and A3 remains fully live
    # there via `check_source_walkthrough`.
    for idx, raw in headings:
        if raw in (A3_HEADING, B4_HEADING):
            add("warning", "FeatureSpec.retired_section_present", idx + 1,
                f"{raw!r} was retired from technical-spec.md this release — strip it "
                "via `run_doc_migrations.py --migrate --only action-thread` "
                "(screens/*/spec.md keeps its own A3, unaffected)")

    h2_names = [h for _, h in h2]
    is_pre_sot = _TECH_PRE_SOT_SENTINEL in h2_names

    if is_pre_sot:
        # v27.x (P09): mirrors func.sections_pre_sot's design exactly (same pattern,
        # not a third one) — one warning for the file's shape, not a wall of findings
        # keyed on headings that do not exist yet. Every check below this point is
        # defined in terms of the new 5-bucket shape and is muted for this file.
        add("warning", "FeatureSpec.tech_sections_pre_sot", None,
            "technical-spec.md is still in the pre-SOT 9-section shape "
            "('## Cross-Cutting Logic' present); migrate to the 5-bucket shape "
            "(target-shape-spec.md § 3). Section/block-shape checks are muted for "
            "this file until migrated — Universal checks still apply.")
        return out

    # C15 (phase 03c) — shared prep for the six checks re-homed below. `b_actions`
    # is the definitive "this file is genuinely thread-shaped" signal (`## 3.
    # Actions` only exists post-migration); every RE-HOMED check below is gated
    # on it so it can never ALSO fire on an old-shape file — old shape's own § 4
    # matches `_bounds_by_number` by ordinal too, so gating on the number alone
    # would double-report alongside the untouched old-shape check. `b_h2_4`
    # locates § 4 tolerant of the D4 rename, reusing phase 03b's
    # `_bounds_by_number` helper (not a second one). `is_pre_thread` drives the
    # same `_thread_sev_msg` WARN-first degradation the action-thread checks
    # already use — old-shape findings (keyed on the literal headings below,
    # left untouched) are NEVER passed through it (merge blocker #4).
    b_actions = _bounds(h2, "## 3. Actions", len(lines))
    b_h2_4 = _bounds_by_number(h2, 4, len(lines))
    is_pre_thread = _TECH_PRE_THREAD_SENTINEL in h2_names

    for idx, raw in headings:
        if raw in DEPRECATED_H2:
            add("critical", "FeatureSpec.deprecated_headings", idx + 1, f"deprecated H2 {raw!r}")
        if raw == "## Appendix":
            add("critical", "FeatureSpec.no_appendix", idx + 1, "## Appendix must be removed")
        # v27.0.0: retired `### BR-001_NameSlug` / `#### DEC-001_NameSlug` heading form.
        # The current BLOCK_HEADING_RE/DEC_BLOCK_RE (trailing `(CODE-NNN)` tag) simply does
        # not match this shape — silently treating it as ordinary prose would reproduce the
        # exact silent-pass failure this migration exists to close (a pattern matching zero
        # blocks reports zero issues). Reject it explicitly instead of ignoring it.
        if LEGACY_BLOCK_HEADING_RE.match(raw):
            add("critical", "FeatureSpec.legacy_block_heading", idx + 1,
                f"{raw!r} uses the retired 'CODE-NNN_NameSlug' heading form; "
                f"rewrite as '<plain sentence> ({LEGACY_BLOCK_HEADING_RE.match(raw).group(1)}-NNN)'")

    # FeatureSpec.required_sections (phase 10 repoint) — accepts EITHER shape a real
    # technical-spec.md may legitimately be in: `REQUIRED_H2_TECH_THREAD` (the current,
    # final action-thread shape) or `_LEGACY_TECH_H2_5BUCKET` (the `feature-sot` migrate
    # step's own output shape — a real, inspectable intermediate a repo may sit in before
    # running the `action-thread` migrate step; see `_spec_constants.py`'s note on that
    # constant). Previously this checked ONLY the legacy 5-bucket shape (under the name
    # `REQUIRED_H2_TECH`), which made every freshly-scaffolded or composer-migrated
    # thread-shaped file fail this check outright (preflight C9, phase-10 item 4).
    # Unconditional critical when a file matches NEITHER shape (a garbled or draft file)
    # — no degrade window needed, since a well-formed file in either valid shape already
    # passes cleanly, same as `_FUNC_PRE_SOT_SENTINEL`/`_TECH_PRE_SOT_SENTINEL` accepting
    # either an old or new shape elsewhere in this file's own history.
    if not _matches_required_h2(h2_names, REQUIRED_H2_TECH_THREAD) and \
            not _matches_required_h2(h2_names, _LEGACY_TECH_H2_5BUCKET):
        missing = [h for h in REQUIRED_H2_TECH_THREAD if h not in h2_names]
        add("critical", "FeatureSpec.required_sections", None,
            f"required H2 missing/out-of-order; missing: {missing}" if missing else "required H2 out of order")

    # RETIRED (phase 10, action-thread reshape): FeatureSpec.sysdesign_subsections had NO
    # successor — § 3 is "## 3. Actions" in the new shape, not a System-Design-shaped
    # section with 7 fixed H3 subsections, and no equivalent per-H3 structural check was
    # specified for § 4 Shared Foundation's appendix (C15 verdict: re-homing this one
    # would mean inventing structure the plan never defined — unlike
    # `missing_client_behavior_anchor`/`polymorphic_behavior_present`/`disc_boolean`/
    # `capability_buckets_missing`/`capability_twin_skew` below, which DO have specified
    # new-shape homes and were re-homed in phase 03c). Removed here alongside its 7 tests
    # in test_technical_spec_sot_validation.py (`TestSysdesignSubsections` x3,
    # `TestMappingTable` x4 — see the retirement note on `FeatureSpec.mapping_table_missing`
    # below for the second half). `b_design` itself stays computed — the still-live
    # old-shape `missing_client_behavior_anchor`/`polymorphic_behavior_present`/
    # `disc_boolean` checks below depend on it.
    b_design = _bounds(h2, "## 3. System Design", len(lines))

    # ## 5. Verification & Technical Notes — 5 required H3 subsections (new, no predecessor).
    b_verif = _bounds(h2, "## 5. Verification & Technical Notes", len(lines))
    if b_verif:
        h3_verif = [(idx, h) for idx, h in headings if b_verif[0] <= idx < b_verif[1] and h.startswith("### ")]
        names = [h for _, h in h3_verif]
        present_v = [h for h in names if h in REQUIRED_VERIF_H3]
        if present_v != [h for h in REQUIRED_VERIF_H3 if h in present_v] or set(present_v) != set(REQUIRED_VERIF_H3):
            add("critical", "FeatureSpec.verification_subsections", None,
                f"required Verification H3 missing/out-of-order; have {names}")
        # Same "bound against the next REQUIRED H3" fix as sysdesign_subsections
        # above — ### 5.1 nests #### {US###} sub-blocks (H4, unaffected either way,
        # but kept consistent for the same reason).
        req_h3_verif = [(idx, h) for idx, h in h3_verif if h in REQUIRED_VERIF_H3]
        for i, (idx, h) in enumerate(req_h3_verif):
            end = req_h3_verif[i + 1][0] if i + 1 < len(req_h3_verif) else b_verif[1]
            if not "\n".join(lines[idx + 1:end]).strip():
                add("critical", "FeatureSpec.verification_subsections", idx + 1,
                    f"{h} is blank; write `None.` if empty")

    # Client Behavior Anchor — D8: re-homed to the end of ## 3. System Design (was
    # inside the retired ## Cross-Cutting Logic). Mandatory even when every linked
    # section is N/A. The rule follows the anchor: P08 relocated the paragraph, this
    # is where the check now looks.
    if b_design:
        design_text = "\n".join(lines[b_design[0]:b_design[1]])
        if "**Client behavior:** see" not in design_text:
            add("critical", "FeatureSpec.missing_client_behavior_anchor", None,
                "## 3. System Design missing required '**Client behavior:** see' anchor "
                "block (links behavior-logic.md, permissions.md, architecture.md — "
                "mandatory even when all linked sections are N/A)")

    # FeatureSpec.polymorphic_behavior_present — retained, re-homed under ### 3.2 Data
    # Model (was a standalone ## Polymorphic Behavior H2). disc_boolean re-homed with it.
    b_datamodel = _bounds_at(headings, "### ", "### 3.2 Data Model", b_design[1]) if b_design else None
    b_poly = _bounds_at(headings, "#### ", "#### Polymorphic Behavior", b_datamodel[1]) if b_datamodel else None
    if b_design and not b_poly:
        add("critical", "FeatureSpec.polymorphic_behavior_present", None,
            "#### Polymorphic Behavior missing under ### 3.2 Data Model")
    if b_poly:
        for idx, disc_h in _disc_boolean_hits(lines, headings, b_poly):
            add("warning", "FeatureSpec.disc_boolean",
                idx + 1,
                f"{disc_h}: DISC subsection appears to document a boolean field (true/false values only); "
                f"boolean flags belong in Business Rules, not DISC-### — consider removing this DISC entry")

    # C15 (phase 03c) — RE-HOMED. Old-shape check above (`b_design`) is left
    # completely untouched. New shape: technical-spec-template.md § 4.6 puts the
    # same anchor at the tail of `## 4. Shared Foundation` (after Configuration)
    # — still the shared-foundation appendix, just § 4 instead of § 3. Gated on
    # `b_actions` (not `b_h2_4` alone) so this cannot double-report on an
    # old-shape file: `b_h2_4` matches old shape's § 4 too (same ordinal), which
    # legitimately has no anchor of its own (it lives in § 3 there).
    if b_actions and b_h2_4:
        appendix_text = "\n".join(lines[b_h2_4[0]:b_h2_4[1]])
        if "**Client behavior:** see" not in appendix_text:
            sev, msg = _thread_sev_msg(
                is_pre_thread, "critical",
                "## 4. Shared Foundation missing required '**Client behavior:** see' "
                "anchor block (links behavior-logic.md, permissions.md, "
                "architecture.md — mandatory even when all linked sections are N/A)")
            add(sev, "FeatureSpec.missing_client_behavior_anchor", None, msg)

    # C15 (phase 03c) — RE-HOMED. Old-shape check above (`b_datamodel`/`b_poly`)
    # is left untouched. New shape: the SAME nesting one section down
    # (### 4.2 Data Model > #### Polymorphic Behavior > ##### DISC-###,
    # technical-spec-template.md § 4.2) — a pure renumber, not a redesign.
    # Gated on `b_actions` for the same double-report reason as the anchor
    # check above; the literal "### 4.2 Data Model" sub-search already no-ops
    # on old-shape files in practice (their § 4 holds dynamic ### 4.N capability
    # buckets, never a heading literally named "Data Model"), but `b_actions`
    # is kept as an explicit gate on the "missing" critical specifically, since
    # an absence-based check has no target heading of its own to fail to find.
    b_datamodel_new = (
        _bounds_at(headings, "### ", "### 4.2 Data Model", b_h2_4[1])
        if (b_actions and b_h2_4) else None
    )
    b_poly_new = (
        _bounds_at(headings, "#### ", "#### Polymorphic Behavior", b_datamodel_new[1])
        if b_datamodel_new else None
    )
    if b_actions and b_h2_4 and not b_poly_new:
        sev, msg = _thread_sev_msg(
            is_pre_thread, "critical",
            "#### Polymorphic Behavior missing under ### 4.2 Data Model")
        add(sev, "FeatureSpec.polymorphic_behavior_present", None, msg)
    if b_poly_new:
        for idx, disc_h in _disc_boolean_hits(lines, headings, b_poly_new):
            sev, msg = _thread_sev_msg(
                is_pre_thread, "warning",
                f"{disc_h}: DISC subsection appears to document a boolean field (true/false "
                "values only); boolean flags belong in Business Rules, not DISC-### — "
                "consider removing this DISC entry")
            add(sev, "FeatureSpec.disc_boolean", idx + 1, msg)

    # ## 4. Technical Behavior by Capability — dynamic ### 4.N buckets.
    b_cap = _bounds(h2, "## 4. Technical Behavior by Capability", len(lines))
    cap_ns: set[int] = set()
    if b_cap:
        for idx, h in headings:
            if b_cap[0] <= idx < b_cap[1]:
                m = _CAP_BUCKET_H3_RE.match(h)
                if m:
                    cap_ns.add(int(m.group(1)))
        if not cap_ns:
            add("critical", "FeatureSpec.capability_buckets_missing", None,
                "## 4. Technical Behavior by Capability has no ### 4.N capability bucket")
        # FeatureSpec.decision_logic_section_present — retained, re-homed under ## 4.
        # (was ## Cross-Cutting Logic § Decision Logic). The template's own anchor for
        # this sub-section is the bold marker "**Decision Logic**", not a heading.
        cap_text = "\n".join(lines[b_cap[0]:b_cap[1]])
        if "**Decision Logic**" not in cap_text:
            add("critical", "FeatureSpec.decision_logic_section_present", None,
                "## 4. Technical Behavior by Capability missing required '**Decision "
                "Logic**' sub-section in any capability bucket")

    # C15 (phase 03c) — RE-HOMED. Old-shape check above (`b_cap`/`cap_ns`) is
    # left untouched. New shape: the per-capability structure IS `## 3. Actions`
    # itself now (wire-format-contract.md § 3 — `### 3.N CAP-NN — title` bucket
    # headings) — there is no successor `## 4.` bucket to look for; the bucket
    # and the action body are the same section. Gated on `b_actions` so this
    # cannot also fire on an old-shape file, whose `## 3.` is System Design and
    # legitimately has no CAP-NN bucket in it at all.
    cap_ns_new: set[int] = set()
    if b_actions:
        for idx, h in headings:
            if b_actions[0] <= idx < b_actions[1]:
                m = _CAP_BUCKET_H3_NEW_RE.match(h)
                if m:
                    cap_ns_new.add(int(m.group(1)))
        if not cap_ns_new:
            sev, msg = _thread_sev_msg(
                is_pre_thread, "critical",
                "## 3. Actions has no ### 3.N CAP-NN capability bucket")
            add(sev, "FeatureSpec.capability_buckets_missing", None, msg)

    # FeatureSpec.decision_logic_section_present — RETIRED for the new shape; no
    # new-shape home added (C15 verdict). The old-shape check above stays fully
    # functional and UNDEGRADED — unlike `sysdesign_subsections`/`mapping_table_missing`
    # (phase 10 removed those two outright, old-shape check and all, since they had no
    # test coverage worth preserving beyond the old shape itself), this rule_id's
    # underlying CONCERN — is decision logic present and
    # well-formed? — does have a successor in the new shape, but it is already
    # fully covered by phase 03b's `_check_dec_blocks` new-shape row scan
    # (`dec_blocks_well_formed`/`dec_lazy_na`, see test_dec_rehoming.py), which
    # validates a DEC row exists and is well-formed directly, per-action, inside
    # that action's own **Rule** rung. What this specific check tested — a bold
    # "**Decision Logic**" marker heading text introducing a capability
    # bucket's DEC blocks — has no analogue anywhere in the new template
    # (technical-spec-template.md and wire-format-contract.md: zero hits for
    # that phrase). A DEC-### row now lives inline in one action's Rule rung
    # with no enclosing named subsection at all, so there is nothing left for
    # this rule_id to re-home onto without inventing a marker the template
    # never calls for — that would be guessing at structure, not fixing a bug.

    func_path = spec.parent / "functional-spec.md"
    twin_text = func_path.read_text(encoding="utf-8", errors="replace") if func_path.is_file() else ""
    # Twin-driven checks below (capability_twin_skew) only make
    # sense once the twin itself is on the NEW functional-spec.md shape — a twin still
    # in its own pre-SOT window (func.sections_pre_sot's sentinel, "## 2. Open
    # Decisions") has no "## 2. Functional Capabilities" CAP- rows and no "## 2."/§ 4/
    # § 5 codes organized the way these checks expect, so treat it exactly like an
    # absent twin (nothing to compare against) rather than flag every code the OLD
    # shape happens to declare under a different heading as "missing" here.
    if _FUNC_PRE_SOT_SENTINEL in twin_text:
        twin_text = ""

    # FeatureSpec.capability_twin_skew — only meaningful once the twin actually
    # declares CAP- rows; an isolated fixture (no sibling functional-spec.md) or a
    # fresh scaffold (twin § 2 still header-only) has nothing to skew against.
    if b_cap and cap_ns:
        twin_ns = {int(n) for n in _CAP_TWIN_ROW_RE.findall(twin_text)}
        if twin_ns:
            extra = sorted(cap_ns - twin_ns)
            missing_ns = sorted(twin_ns - cap_ns)
            if extra or missing_ns:
                add("warning", "FeatureSpec.capability_twin_skew", None,
                    f"## 4. buckets {sorted(cap_ns)} vs twin's ## 2. CAP- rows "
                    f"{sorted(twin_ns)}; extra={extra} missing={missing_ns}")

    # C15 (phase 03c) — RE-HOMED. Old-shape check above (`b_cap`/`cap_ns`) is
    # left untouched. New shape compares the SAME twin CAP- rows against
    # `cap_ns_new` (`## 3. Actions`' own CAP-NN buckets) instead of the old
    # `## 4.` buckets — same twin-emptiness exemption (nothing to skew against
    # when the twin itself has no CAP- rows yet).
    if b_actions and cap_ns_new:
        twin_ns = {int(n) for n in _CAP_TWIN_ROW_RE.findall(twin_text)}
        if twin_ns:
            extra = sorted(cap_ns_new - twin_ns)
            missing_ns = sorted(twin_ns - cap_ns_new)
            if extra or missing_ns:
                sev, msg = _thread_sev_msg(
                    is_pre_thread, "warning",
                    f"## 3. Actions buckets {sorted(cap_ns_new)} vs twin's ## 2. CAP- rows "
                    f"{sorted(twin_ns)}; extra={extra} missing={missing_ns}")
                add(sev, "FeatureSpec.capability_twin_skew", None, msg)

    # RETIRED (phase 10, action-thread reshape): FeatureSpec.mapping_table_missing had
    # no meaning once "## 2." became "## 2. Action Index" —
    # FeatureSpec.action_index_missing (`_check_action_thread`) is its successor, shipped
    # in phase 02. Removed here alongside its tests (test_technical_spec_sot_validation.py
    # ::TestMappingTable, 4 tests — the other half of the 7 tests retired with
    # `sysdesign_subsections` above). `FeatureSpec.mapping_restates_story`'s own narrower
    # concern (a Name cell restating the user story as a GWT narrative) has no analogous
    # column in the new § 2 Action Index shape either, but is left running UNCHANGED below
    # for a file still in the legacy 5-bucket shape — `b_map` is simply `None` (and the
    # loop below a no-op) for any thread-shaped file, the same "gated on the old heading's
    # own presence" pattern the surviving old-shape checks above already use.
    b_map = _bounds(h2, "## 2. Functional → Technical Mapping", len(lines))
    if b_map:
        for row in _table_rows(lines, b_map[0], b_map[1], "Code"):
            if len(row) < 2:
                continue
            name = row[1]
            if len(name) > _MAPPING_NAME_MAX_LEN or _GWT_WORD_RE.search(name):
                add("warning", "FeatureSpec.mapping_restates_story", b_map[0] + 1,
                    f"## 2. Name cell reads like a restated story, not a title: {name[:80]!r}")

    # FeatureSpec.us_narrative_present — the same duplication in a different shape:
    # a surviving **What happens:** field anywhere in technical-spec.md.
    what_happens_line = next((i + 1 for i, ln in enumerate(lines) if _WHAT_HAPPENS_RE.search(ln)), None)
    if what_happens_line is not None:
        add("warning", "FeatureSpec.us_narrative_present", what_happens_line,
            "'**What happens:**' narrative field survives in technical-spec.md — that "
            "narrative belongs in functional-spec.md now")

    # Out of P09's stated scope (references/verification-checklist-feature-spec.md:
    # "unaffected by the retaxonomy in predicate, only in section location") — these
    # three headings never existed in either the old 9-section or new 5-bucket shape
    # for a real corpus, so both checks are inert either way; left untouched.
    b_sf = _bounds(h2, "## Screen Flow", len(lines))
    if b_sf:
        for i in range(*b_sf):
            s = lines[i].strip()
            if s and not s.startswith("#") and not s.startswith("<!--"):
                if not SCREEN_FLOW_OK_RE.match(s):
                    add("critical", "FeatureSpec.screen_flow_crossref", i + 1,
                        "Screen Flow first content line must start with '**See:** ScreenFlow § F###_…' or 'N/A —'")
                break

    b_bw = _bounds(h2, "## Business Workflow", len(lines))
    if b_bw:
        steps = sum(1 for i in range(*b_bw) if NUMBERED_STEP_RE.match(lines[i]))
        if steps < 3:
            add("critical", "FeatureSpec.bw_steps", None,
                f"## Business Workflow needs ≥3 numbered steps; found {steps}")

    b_us = _bounds(h2, "## User Stories", len(lines))
    if b_us and not any(h == "### Edge Cases"
                        for idx, h in headings if b_us[0] <= idx < b_us[1] and h.startswith("### ")):
        add("critical", "FeatureSpec.edge_cases", None, "### Edge Cases required under ## User Stories")

    sm_heads = [(idx, raw) for idx, raw in headings if SM_BLOCK_RE.match(raw)]
    for k, (idx, raw) in enumerate(sm_heads):
        nxt = sm_heads[k + 1][0] if k + 1 < len(sm_heads) else len(lines)
        if not any(idx < start < nxt and lang.startswith("mermaid") for start, _e, lang in blocks):
            add("critical", "FeatureSpec.sm_mermaid", idx + 1, f"{raw} block missing stateDiagram-v2 fence")

    for start, end, lang in blocks:
        if lines[start].startswith("```{lang}"):
            add("warning", "FeatureSpec.pseudocode_fence", start + 1, "pseudocode fence uses literal {lang}")
        if end - start - 1 > 20 and lang and lang != "mermaid":
            add("warning", "FeatureSpec.pseudocode_length", start + 1,
                f"pseudocode block {end - start - 1} lines > 20")

    # DEC-### structural checks — re-homed to anywhere under ## 4. (old shape) AND to
    # a table row inside ## 3. Actions (new shape). Phase 03b (C13 fix): `b_cap`
    # itself (used above by capability_buckets_missing/decision_logic_section_present/
    # capability_twin_skew) stays keyed on the exact old literal, untouched; the DEC
    # search gets its OWN bound resolved by heading NUMBER so it survives the § 4
    # rename — see `_bounds_by_number`'s docstring for why the two are not unified.
    # `b_h2_4` / `b_actions` / `is_pre_thread` computed once, earlier in this
    # function (C15/phase 03c prep block) — reused here rather than re-derived.
    for dec_issue in _check_dec_blocks(lines, headings, blocks, b_h2_4,
                                        b_actions, is_pre_thread):
        dec_issue["validator"] = VALIDATOR
        try:
            dec_issue["location"]["file"] = str(spec.relative_to(root))
        except ValueError:
            dec_issue["location"]["file"] = str(spec)
        out.append(dec_issue)

    # Linked FR presence check — every BR/SM/ALG/INT block must declare Linked FR
    out.extend(_check_linked_fr(spec, root, lines))

    # F8: source-evidence checks — critical for implemented, warning for drafts.
    src_ev_sev = "warning" if is_draft else "critical"

    # (a) ### 5.4 Source References body — re-homed from the old ## Source Code
    # References H2 (now nested as an H3 inside ## 5. Verification & Technical Notes).
    # Must have >= 1 citation for implemented specs — either an inline **Source:**
    # path:N-M line OR a canonical table row citing `path:N-M`. Draft specs are
    # allowed to have an empty body (no citations for code not yet written).
    b_src = _bounds_at(headings, "### ", "### 5.4 Source References", b_verif[1]) if b_verif else None
    if b_src:
        src_lines = lines[b_src[0]:b_src[1]]
        src_count = sum(
            1 for ln in src_lines
            if _SOURCE_LINE_RE.match(ln) or _SOURCE_TABLE_ROW_RE.match(ln)
        )
        if src_count == 0:
            add(src_ev_sev, "FeatureSpec.source_refs_empty", b_src[0] + 1,
                "### 5.4 Source References body is empty; implemented specs must have at "
                "least one citation — a **Source:** path:N-M line or a table row citing `path:N-M`")

    # (b) BR/SM/ALG/INT blocks: each must have a **Source:** line.
    block_heads = [(idx, raw) for idx, raw in headings if BLOCK_HEADING_PREFIX_RE.match(raw)]
    fenced_lines = {i for s, e, _ in blocks for i in range(s, e + 1)}
    # Bound each block at the next H1-H4 heading (not only the next block head) so a
    # **Source:** line in a later section cannot satisfy the LAST block's check. v27.x
    # (P09): widened from {1,3} to {1,4} — ## 4.'s capability buckets now interleave
    # H3 BR blocks with H4 DEC blocks (technical-spec-template.md § 4) with no H3
    # sibling between them, so a BR block's own bounds must stop at the very next
    # DEC-### heading too; leaving this at {1,3} would let a BR block missing its own
    # **Source:** line silently "see" the NEXT DEC block's Source citation instead and
    # pass — a false negative introduced by the retaxonomy's interleaved heading
    # levels, not present in the old shape (BR and DEC lived under separate H3s there).
    boundaries = sorted(i for i, h in headings if re.match(r"^#{1,4} ", h))
    for idx, raw in block_heads:
        if idx in fenced_lines:
            continue
        nxt = next((b for b in boundaries if b > idx), len(lines))
        block_text = "\n".join(lines[idx + 1:nxt])
        # v27.0.0 (P11 / class 1): a `**kind:** ui` SM block is exempt — see
        # _SM_KIND_UI_RE above for why. `entity`-kind (or unmarked) SM blocks,
        # and every BR/ALG/INT block, are unaffected and still required.
        if SM_BLOCK_RE.match(raw) and _SM_KIND_UI_RE.search(block_text):
            continue
        if not _SOURCE_LINE_RE.search(block_text):
            add(src_ev_sev, "FeatureSpec.block_source_missing", idx + 1,
                f"{raw} missing required '**Source:** path:N-M' line")

        # ALG-only: file-exchange algorithms must declare a populated **File Schema**
        # table. BR/SM/INT blocks have no such field and are never checked. Warning
        # severity only — does not affect critical count / exit code (see `main()`).
        # v27.0.0: the ALG-### code is now a trailing `(ALG-NNN)` tag, not a heading
        # prefix — `raw.startswith("### ALG-")` would silently never match again.
        if _ALG_BLOCK_TAG_RE.search(raw):
            full_block_text = raw + "\n" + block_text
            if is_file_exchange(full_block_text) and not has_populated_file_schema(block_text):
                add("warning", "FeatureSpec.alg_file_schema_missing", idx + 1,
                    f"{raw} matches file-exchange vocabulary but has no populated "
                    f"'**File Schema**' table")

    # Phase 02 (action-thread reshape, D2/D4) — § 2 Action Index binding + § 3 rung
    # structure. See `_check_action_thread` for the 5 rule_ids and their gating
    # (a 6th, `action_double_claimed`, was retired — see that docstring).
    out.extend(_check_action_thread(lines, headings, h2, spec, root))
    # Phase 03 — § 4.4 rule bins + the diagram contract. See
    # `_check_rule_bins_and_diagrams` for the 5 rule_ids and their gating.
    out.extend(_check_rule_bins_and_diagrams(lines, headings, h2, spec, root))
    # Phase 03 (self-sufficiency v27.8) — the refined bare-reference check. See
    # `_check_action_ref_unglossed` for the rule_id and its gating.
    out.extend(_check_action_ref_unglossed(lines, headings, h2, spec, root))

    return out


def _func_h2_bounds(h2: list, name: str, total: int) -> tuple[int, int] | None:
    return _bounds(h2, name, total)


def _func_type(lines: list[str]) -> str:
    """Read the `**Type**: {ui|background|mixed}` preamble field. Defaults to 'ui'
    (the stricter threshold) when absent/unparseable — never silently relaxes."""
    m = _FUNC_TYPE_RE.search("\n".join(lines[:15]))
    return m.group(1).lower() if m else "ui"


_FCODE_ONLY_RE = re.compile(r"^#\s+(F\d{3})_")
# v27.0.0 (P11 / class 3) — a code mention immediately followed (within a short
# window, same sentence) by "(F0NN_Slug)" or "in F0NN_Slug" names that feature as
# the code's OWNER. When that F-code differs from the current feature, the mention
# is a CROSS-FEATURE REFERENCE, not a local declaration (e.g. "F055 drives the
# following transitions in SM-001 (F051_TransactionStateMachine)" — SM-001 belongs
# to F051, not the feature being validated). Genuine ambiguity (no owner tag, or
# the tag names THIS feature) fails CLOSED as a declaration, so a real unsurfaced
# code is never silently let through.
_OWNING_FEATURE_TAG_RE = re.compile(r"\A\s*(?:\(\s*|in\s+)(F\d{3})_\w+")


def _extract_own_fcode(lines: list[str]) -> str | None:
    for ln in lines[:10]:
        m = _FCODE_ONLY_RE.match(ln.strip())
        if m:
            return m.group(1)
    return None


# REWORK (adversarial review finding 2, HIGH): the original implementation
# excluded a code as "cross-feature" purely because an adjacent tag NAMED a
# different feature — it never checked that the named feature actually OWNS
# the code. A stray or wrong tag from an LLM composition pass could then
# permanently silence func.code_unsurfaced for a real local code, and the
# tagged feature need not even exist. This now verifies the tag before
# trusting it: resolve the named feature's technical-spec.md under the SAME
# features-root the current feature lives in and check the code is actually
# declared there. Unresolvable in ANY way — no features_root, the named
# feature directory doesn't exist (or is ambiguous), its technical-spec.md is
# missing/unreadable, or it exists but does not declare the code — fails
# CLOSED: the code stays a local declaration, exactly as if no tag were
# present at all.
def _other_feature_declares_code(features_root: Path | None, fcode: str, code: str) -> bool:
    """True only when exactly one `{fcode}_*` directory exists under
    `features_root` AND its technical-spec.md contains `code` (e.g. `SM-001`)
    verbatim. False (fail closed) for every other case — no features_root,
    zero or multiple matching directories, unreadable/missing file, or the
    code genuinely absent from that file."""
    if features_root is None or not features_root.is_dir():
        return False
    try:
        candidates = [p for p in features_root.glob(f"{fcode}_*") if p.is_dir()]
    except OSError:
        return False
    if len(candidates) != 1:
        return False  # missing or ambiguous — never guess
    other_spec = candidates[0] / "technical-spec.md"
    if not other_spec.is_file():
        return False
    try:
        other_text = other_spec.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any(
        f"{m.group(1)}-{m.group(2)}" == code for m in _TECH_CODE_RE.finditer(other_text)
    )


def _func_declared_codes(tech_text: str, own_fcode: str | None = None,
                          features_root: Path | None = None) -> dict[str, set[str]]:
    """Every FR-###/BR-###/DEC-###/SM-### token declared anywhere in technical-spec.md,
    grouped by prefix. Conservative (whole-file scan, not fence-excluded) — a code
    mentioned anywhere counts as declared, so this never under-reports what functional-
    spec.md must surface. EXCEPT a code whose adjacent owner tag names a DIFFERENT
    feature than `own_fcode` AND that feature is VERIFIED (via `features_root`) to
    actually declare the code — that is a cross-feature reference, not a declaration
    of this feature's own code (see _OWNING_FEATURE_TAG_RE and
    _other_feature_declares_code). An unverifiable tag (features_root absent, named
    feature missing/ambiguous, or it does not declare the code) fails CLOSED: still a
    local declaration."""
    out: dict[str, set[str]] = {"FR": set(), "BR": set(), "DEC": set(), "SM": set()}
    text = tech_text or ""
    for m in _TECH_CODE_RE.finditer(text):
        tail = text[m.end():m.end() + 40]
        owner = _OWNING_FEATURE_TAG_RE.match(tail)
        code = f"{m.group(1)}-{m.group(2)}"
        if (owner and own_fcode and owner.group(1) != own_fcode
                and _other_feature_declares_code(features_root, owner.group(1), code)):
            continue  # verified cross-feature reference — not a local declaration
        out[m.group(1)].add(code)
    return out


def _check_open_decisions(lines: list[str], bounds: tuple[int, int] | None,
                          func_path: Path, root: Path) -> list[dict]:
    """§ 3 Open Decisions: table with Default proposal + Blocks work columns, OR the
    literal None-fallback. A stray [NEEDS_DOMAIN_CONFIRMATION] marker anywhere in the
    file (not promoted to a row) is also this rule_id."""
    issues: list[dict] = []
    full_text = "\n".join(lines)
    if _NEEDS_DOMAIN_CONFIRMATION_RE.search(full_text):
        issues.append(_issue("critical", "func.open_decisions_shape", func_path, root, None,
                             "[NEEDS_DOMAIN_CONFIRMATION] marker left inline — promote it to a "
                             "§ 3 Open Decisions row"))
    if not bounds:
        return issues
    section_text = "\n".join(lines[bounds[0]:bounds[1]])
    if _FUNC_OPEN_DECISIONS_NONE_RE.search(section_text.strip()):
        return issues
    table_rows = [ln for ln in lines[bounds[0]:bounds[1]] if ln.strip().startswith("|")]
    if not table_rows:
        issues.append(_issue("critical", "func.open_decisions_shape", func_path, root,
                             bounds[0] + 1,
                             "§ 3 Open Decisions has neither a table nor the None-fallback"))
        return issues
    header = table_rows[0].lower()
    if "default proposal" not in header or "blocks work" not in header:
        issues.append(_issue("critical", "func.open_decisions_shape", func_path, root,
                             bounds[0] + 1,
                             "§ 3 Open Decisions table missing 'Default proposal' or "
                             "'Blocks work' column"))
    return issues


def _check_screens_section(lines: list[str], bounds: tuple[int, int] | None,
                           func_type: str, func_path: Path, root: Path) -> list[dict]:
    """§ 6 Screens: 4-column table with a resolvable-shaped SCR### column for UI/mixed
    features, or the N/A background fallback. Full cross-file resolution against
    generated/screen-list.md is validate_feature_screen_link.py's job (link.scr_unresolved);
    this check is the self-contained structural half — carries the old screens.missing_h2
    contract forward, narrowed to "does the SCR### column exist and look well-formed."""
    if not bounds:
        return []
    section_lines = lines[bounds[0]:bounds[1]]
    section_text = "\n".join(section_lines).strip()
    if _FUNC_BACKGROUND_RE.match(section_text):
        return []
    if func_type == "background":
        return []
    table_rows = [ln for ln in section_lines if ln.strip().startswith("|")]
    if not table_rows:
        return [_issue("critical", "func.screens_scr_unresolved", func_path, root,
                       bounds[0] + 1,
                       "§ 6 Screens has no table and no background N/A fallback")]
    header_cells = [c.strip().casefold() for c in table_rows[0].strip().strip("|").split("|")]
    scr_idx = next((i for i, h in enumerate(header_cells) if re.search(r"\bscr(\b|#|\d)", h)), None)
    if scr_idx is None:
        return [_issue("critical", "func.screens_scr_unresolved", func_path, root,
                       bounds[0] + 1, "§ 6 Screens table has no SCR### column")]
    issues: list[dict] = []
    for row in table_rows[2:]:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if not cells or cells[0].startswith("{"):
            continue  # unfilled template placeholder row
        # (?!\d) not \b: a trailing \b never matches "SCR001_Login" because "_" is a
        # word char, so the documented SCR###_Slug form would false-positive. Same
        # boundary fix as _TECH_CODE_RE above.
        if scr_idx >= len(cells) or not re.search(r"\bSCR\d{3}(?!\d)", cells[scr_idx]):
            issues.append(_issue("critical", "func.screens_scr_unresolved", func_path, root,
                                 bounds[0] + 1,
                                 f"§ 6 Screens row {cells[0]!r} has no resolvable SCR### code"))
    return issues


def _check_edge_cases_section(lines: list[str], bounds: tuple[int, int] | None,
                              func_type: str, func_path: Path, root: Path) -> list[dict]:
    """§ 9 Edge Cases: ≥3 rows for UI features, ≥1 for background (direct rename of the
    retired edge_cases.few_rows, now scoped within functional-spec.md)."""
    if not bounds:
        return []
    section_lines = lines[bounds[0]:bounds[1]]
    table_rows = [
        ln for ln in section_lines
        if ln.strip().startswith("|")
        and not re.match(r"^\|\s*[-:]+", ln)
        and not re.match(r"^\|\s*Scenario", ln, re.IGNORECASE)
    ]
    minimum = 1 if func_type == "background" else 3
    if len(table_rows) < minimum:
        return [_issue("warning", "func.edge_cases_few_rows", func_path, root, bounds[0] + 1,
                       f"§ 9 Edge Cases has {len(table_rows)} row(s); need ≥{minimum} for "
                       f"a {func_type} feature")]
    return []


def _check_rule_density(lines: list[str], b4: tuple[int, int] | None,
                        b5: tuple[int, int] | None, func_path: Path, root: Path) -> list[dict]:
    """Success metric #1: avg lines per rule across § 4 + § 5 ≤ 2, measured in LINES
    (Validation Decision V1 — a long single line is an accepted risk on record, not
    itself flagged). A rule starts at a `- ` bullet; its line-span runs to the next
    bullet/section boundary."""
    starts: list[int] = []
    end = None
    for bounds in (b4, b5):
        if not bounds:
            continue
        end = bounds[1]
        for i in range(bounds[0], bounds[1]):
            if lines[i].lstrip().startswith("- "):
                starts.append(i)
    if not starts:
        return []
    starts.sort()
    total_lines = 0
    for k, s in enumerate(starts):
        nxt = starts[k + 1] if k + 1 < len(starts) else end
        span = [ln for ln in lines[s:nxt] if ln.strip()]
        total_lines += len(span)
    avg = total_lines / len(starts)
    if avg > 2:
        return [_issue("warning", "func.rule_density", func_path, root, None,
                       f"§ 4 + § 5 average {avg:.1f} lines/rule (budget: ≤2)")]
    return []


def _check_edge_behaviours(lines: list[str], b10: tuple[int, int] | None,
                           fr_codes_in_4: set[str], func_path: Path, root: Path) -> list[dict]:
    """§ 10 Edge Behaviours to Verify: every bold FR-### back-ref must exist in § 4."""
    if not b10:
        return []
    issues: list[dict] = []
    for i in range(b10[0], b10[1]):
        for m in _FUNC_EDGE_BEHAVIOUR_FR_RE.finditer(lines[i]):
            code = f"FR-{m.group(1)}"
            if code not in fr_codes_in_4:
                issues.append(_issue("critical", "func.edge_behaviour_dangling", func_path, root,
                                     i + 1,
                                     f"§ 10 back-references {code}, not present in § 4 Requirements"))
    return issues


def _check_code_surfacing(lines: list[str], b4: tuple[int, int] | None,
                          b5: tuple[int, int] | None, tech_text: str,
                          func_path: Path, root: Path,
                          own_fcode: str | None = None,
                          features_root: Path | None = None) -> tuple[list[dict], set[str]]:
    """Cross-check § 4/§ 5 one-liners against technical-spec.md's declared codes.

    func.code_unsurfaced (critical): a code declared in technical-spec.md has no
      matching one-liner in § 4/§ 5 — the "silent-pass" guard (Constraint 2): if the
      functional-spec side goes empty or malformed, this is what fires.
    func.code_orphan (critical): a code cited in § 4/§ 5 does not exist in
      technical-spec.md at all (phantom code).

    `features_root` is the directory containing this feature's siblings (i.e.
    `func_path.parent.parent`) — passed through to `_func_declared_codes` so a
    cross-feature reference tag can be verified against the named feature's own
    technical-spec.md rather than trusted blindly (finding 2 rework). `None`
    when the caller cannot resolve one; that fails closed, never open.

    Returns (issues, fr_codes_found_in_section_4) — the FR set is reused by the
    § 10 back-ref check (and § 2 Capabilities cross-check) so it isn't re-derived twice.
    """
    fr_in_4: set[str] = set()
    if b4:
        for i in range(b4[0], b4[1]):
            m = _FUNC_FR_BULLET_RE.match(lines[i])
            if m:
                fr_in_4.add(f"FR-{m.group(1)}")

    tagged_in_5: set[str] = set()
    if b5:
        for i in range(b5[0], b5[1]):
            m = _FUNC_RULE_TAG_RE.search(lines[i])
            if m:
                tagged_in_5.add(f"{m.group(1)}-{m.group(2)}")

    func_all = fr_in_4 | tagged_in_5
    tech_by_prefix = _func_declared_codes(tech_text, own_fcode, features_root)
    tech_all = set().union(*tech_by_prefix.values()) if tech_by_prefix else set()

    issues: list[dict] = []
    for code in sorted(tech_all - func_all):
        line = (b4[0] + 1) if code.startswith("FR-") and b4 else (b5[0] + 1 if b5 else None)
        issues.append(_issue("critical", "func.code_unsurfaced", func_path, root, line,
                             f"{code} is declared in technical-spec.md but has no one-liner "
                             f"in § 4/§ 5"))
    for code in sorted(func_all - tech_all):
        issues.append(_issue("critical", "func.code_orphan", func_path, root, None,
                             f"{code} appears in § 4/§ 5 but is not declared anywhere in "
                             f"technical-spec.md"))
    return issues, fr_in_4


def _func_code_sets(lines: list[str], b4: tuple[int, int] | None, b5: tuple[int, int] | None,
                    b6: tuple[int, int] | None, b7: tuple[int, int] | None) -> dict[str, set[str]]:
    """Every US###/BR-###|DEC-###|SM-###/FR-###/SCR### declared anywhere in §§ 4-7,
    keyed by family — the DECLARED half of the § 2 exhaustiveness rule (phase 05,
    research digest § A4: "US### and SCR### sets do not exist yet anywhere"; this is
    where they get built, reusing the four idioms that already exist in this file rather
    than re-deriving them: `_FUNC_FR_BULLET_RE` for § 4, `_FUNC_RULE_TAG_RE` for § 5
    trailing tags (mirrors `tagged_in_5` in `_check_code_surfacing` — BR/DEC/SM share one
    family), `_check_screens_section`'s own SCR-column shape for § 6, and
    `_FUNC_US_HEADING_RE` for § 7 headings.

    Background-feature exemption: a § 6 replaced by the
    "N/A — background feature; no user-facing screens." fallback (`_FUNC_BACKGROUND_RE`)
    yields an empty SCR set here, so `cap.code_unclaimed` with `family=SCR` can never
    fire for such a feature — there is nothing declared to claim."""
    sets: dict[str, set[str]] = {"US": set(), "BR": set(), "FR": set(), "SCR": set()}
    if b4:
        for i in range(b4[0], b4[1]):
            m = _FUNC_FR_BULLET_RE.match(lines[i])
            if m:
                sets["FR"].add(f"FR-{m.group(1)}")
    if b5:
        for i in range(b5[0], b5[1]):
            m = _FUNC_RULE_TAG_RE.search(lines[i])
            if m:
                sets["BR"].add(f"{m.group(1)}-{m.group(2)}")
    if b6:
        section_lines = lines[b6[0]:b6[1]]
        section_text = "\n".join(section_lines).strip()
        if not _FUNC_BACKGROUND_RE.match(section_text):
            table_rows = [ln for ln in section_lines if ln.strip().startswith("|")]
            if table_rows:
                header_cells = [c.strip().casefold() for c in table_rows[0].strip().strip("|").split("|")]
                scr_idx = next((i for i, h in enumerate(header_cells) if re.search(r"\bscr(\b|#|\d)", h)), None)
                if scr_idx is not None:
                    for row in table_rows[2:]:
                        cells = [c.strip() for c in row.strip().strip("|").split("|")]
                        if not cells or cells[0].startswith("{") or scr_idx >= len(cells):
                            continue
                        m = _FAMILY_CODE_RE["SCR"].search(cells[scr_idx])
                        if m:
                            sets["SCR"].add(m.group())
    if b7:
        for i in range(b7[0], b7[1]):
            m = _FUNC_US_HEADING_RE.match(lines[i])
            if m:
                code_m = _FAMILY_CODE_RE["US"].search(m.group(1))
                if code_m:
                    sets["US"].add(code_m.group())
    return sets


def _cap_claims(lines: list[str], b2: tuple[int, int] | None) -> dict[str, list[str]]:
    """code -> the list of § 2 CAP ids that claim it (in row order), across every
    resolvable family column — the CLAIMED half of the § 2 exhaustiveness rule. Built on
    `_cap_table_lib` (AD-6): this is not a second § 2 parser, it consumes the shared
    `data_rows`/`claim_columns` contract. A family whose column is absent from the
    header is simply skipped — that family cannot be checked here, matching the
    `req_idx is None: return issues` fail-soft precedent elsewhere in this file (a
    malformed header is already covered by `func.missing_h2`/schema checks)."""
    header_cells, rows = _cap_table_lib.data_rows(lines, b2)
    cols = _cap_table_lib.claim_columns(header_cells)
    claims: dict[str, list[str]] = {}
    for row in rows:
        cap_id = row[0] if row else ""
        for family, idx in cols.items():
            if idx >= len(row):
                continue
            # SCR is the one family with a composite form (`SCR###/REG###`). It keeps its
            # own tokenizer so a region claim stays distinct from a screen-shell claim —
            # see `_SCR_CLAIM_RE` / `_claim_parents` for the two-views split this creates.
            pattern = _SCR_CLAIM_RE if family == "SCR" else _FAMILY_CODE_RE[family]
            for m in pattern.finditer(row[idx]):
                if _is_possessive(row[idx], m.end()):
                    continue
                code = _normalize_scr_claim(m.group()) if family == "SCR" else m.group()
                claims.setdefault(code, []).append(cap_id)
    return claims


def _check_capabilities_section(lines: list[str], b2: tuple[int, int] | None,
                                b4: tuple[int, int] | None, b5: tuple[int, int] | None,
                                b6: tuple[int, int] | None, b7: tuple[int, int] | None,
                                func_path: Path, root: Path) -> list[dict]:
    """§ 2 Functional Capabilities — forward AND reverse directions (phase 05,
    capability-map plan). AD-6: the table is parsed exactly once, via `_cap_table_lib`;
    this function is its only caller inside this file.

    func.capabilities_empty (warning): § 2 has 0 data rows while § 4 Requirements
      already declares >= 1 real FR-### — the capability rollup has fallen behind the
      requirements it is supposed to summarize.
    func.capability_fr_dangling (critical): a § 2 "Requirements" cell cites an FR-###
      code that is not declared in § 4 — a phantom cross-reference.
    cap.code_unclaimed (critical): a US###/FR-###/BR-###|DEC-###|SM-###/SCR### declared
      anywhere in §§ 4-7 is claimed by zero § 2 rows. Message opens with
      `family=US|BR|FR|SCR` (SC-2: one rule id, not five — the family is grep-able text
      in the message because an extra dict key would be silently dropped by the only
      renderer, `buildFsValidatorPreamble`).
    cap.double_claimed (critical): a code is claimed by two or more § 2 rows — every
      code belongs to exactly one capability (a cardinality rule, kept separate from
      `cap.code_unclaimed` because no set-difference expresses "how many").
    cap.claims_unfilled (warning): § 2 has >=1 data row and EVERY row's claim cells are
      empty (`_cap_table_lib.claim_state(...) == "unfilled"`) — the structural,
      post-`cap-map`/pre-fill window (FM-4). While this fires, `cap.code_unclaimed` and
      `cap.double_claimed` are suppressed for the file; the mute is all-or-nothing by
      design, never a percentage threshold (a partially-filled table is real, actionable
      signal, not noise to swallow).

    [SA-2] The reverse checks (`declared`, `state`) are computed FIRST and
    UNCONDITIONALLY — nothing here may `return` before them. A § 2 with only a
    header/separator row (no data rows) still runs the reverse check: every declared
    code is genuinely unclaimed in that state, which is the maximal, not the minimal,
    finding count. The old code returned before ever reaching that arithmetic; see
    `TestMaximalCount` in the test file for the regression test."""
    if not b2:
        return []

    declared = _func_code_sets(lines, b4, b5, b6, b7)
    header_cells, rows = _cap_table_lib.data_rows(lines, b2)
    state = _cap_table_lib.claim_state(header_cells, rows)
    cols = _cap_table_lib.claim_columns(header_cells)

    issues: list[dict] = []

    if state == "unfilled":
        issues.append(_issue("warning", "cap.claims_unfilled", func_path, root, b2[0] + 1,
                             f"§ 2 Functional Capabilities has {len(rows)} row(s) but every "
                             "claim cell (User Stories/Requirements/Business Rules/Screens) "
                             "is empty — pending fill; run `--migrate --only cap-map` then "
                             "complete the claims"))
    else:
        claims = _cap_claims(lines, b2)
        # Completeness reads the parent-expanded view (a declared bare `SCR161` is
        # satisfied by a `SCR161/REG002` claim); cardinality below reads exact tokens.
        claimed_codes = _claim_parents(claims)
        for family in ("US", "BR", "FR", "SCR"):
            if family not in cols:
                continue
            for code in sorted(declared.get(family, set()) - claimed_codes):
                issues.append(_issue("critical", "cap.code_unclaimed", func_path, root,
                                     b2[0] + 1,
                                     f"family={family} {code} is declared in §§ 4-7 but "
                                     "claimed by no § 2 Functional Capabilities row — see "
                                     "references/code-formats.md § Capability-Level Intent "
                                     "(authority)"))
        for code in sorted(claims):
            caps = claims[code]
            if len(caps) >= 2:
                issues.append(_issue("critical", "cap.double_claimed", func_path, root,
                                     b2[0] + 1,
                                     f"{code} is claimed by {len(caps)} § 2 rows: "
                                     f"{', '.join(sorted(caps))} — every code belongs to "
                                     "exactly one capability"))

    fr_in_4 = declared.get("FR", set())
    if rows:
        req_idx = cols.get("FR")
        if req_idx is not None:
            for cells in rows:
                if req_idx >= len(cells):
                    continue
                for code in _FR_CODE_IN_CELL_RE.findall(cells[req_idx]):
                    if code not in fr_in_4:
                        issues.append(_issue("critical", "func.capability_fr_dangling",
                                             func_path, root, b2[0] + 1,
                                             f"§ 2 Capabilities row cites {code!r}, not "
                                             "declared in § 4 Requirements"))
    elif fr_in_4:
        issues.append(_issue("warning", "func.capabilities_empty", func_path, root,
                             b2[0] + 1,
                             "§ 2 Functional Capabilities has 0 rows but § 4 Requirements "
                             f"already declares {len(fr_in_4)} FR(s)"))

    return issues


# ---------------------------------------------------------------------------
# Phase 06 (capability-map plan) — cap.analysis_required / cap.review_advised.
#
# [SC-7] PROVISIONAL — the BL bands below were scaled ~1.6x off the US bands
# (3-4 warn / >=5 crit) against n=8 background features measured in the
# sharetribe corpus (F063=15, F058=8, F059=8, F061=6, F060=6, F062=5, F053=3,
# F057=1): a BL is a single job/listener, roughly FR-grained, whereas a US is a
# whole narrative, so equivalent breadth runs denser in BL count. Eight
# features is a handful, not a distribution — these numbers satisfy the two
# constraints they were chosen against (F063/F058/F059 must fire, F057 must
# not) and nothing more. They MUST be re-measured once a second real corpus
# with background features exists; do not silently re-tune without recording
# why here.
_CAP_ANALYSIS_BANDS: dict[str, dict[str, tuple[int, int]]] = {
    "ui": {"US": (3, 5)},
    "background": {"BL": (5, 8)},
    # [SC-7 mixed gap — CLOSED] evaluated below as BOTH rows above, taking the
    # STRICTER outcome (critical beats warning beats silent). The original plan
    # left `mixed` on the US row alone, so a `mixed` feature heavy on BL and
    # light on US escaped both bands — a real hole inside a claim of exhaustive
    # coverage. The counting machinery for both denominators already exists, so
    # closing it costs nothing new: one comparison over two band positions.
    "mixed": {"US": (3, 5), "BL": (5, 8)},
}
_CAP_SEVERITY_RANK = {"silent": 0, "warning": 1, "critical": 2}
# One extraction regex per family for the rationale's citation check — reusing
# `_FAMILY_CODE_RE["US"]` (AD-6-style: no second US-code regex in this file).
_CAP_FAMILY_RE: dict[str, re.Pattern[str]] = {"US": _FAMILY_CODE_RE["US"], "BL": _FUNC_BL_CODE_RE}


def _cap_band_state(count: int, warn_floor: int, crit_floor: int) -> str:
    if count >= crit_floor:
        return "critical"
    if count >= warn_floor:
        return "warning"
    return "silent"


def _cap_rationale_verdict(section2_text: str, families: list[str],
                           declared: set[str]) -> tuple[bool, list[str]]:
    """[SC-1] The three deterministic hatch conditions, each its OWN named boolean
    so the failure message can say exactly which one failed — collapsing these
    into one compound expression is the "simplify it back to a presence check"
    regression the phase-06 plan's SC-1 Key Insight warns against; do not do it.

    ok_1 — a same-line, non-empty body follows the label (SA-1's own regex makes
           an empty label unable to match at all, so `bool(body)` is sufficient).
    ok_2 — the body has >= 12 words (`body.split()` on that same-line text).
    ok_3 — the body cites >= 2 DISTINCT codes from `families`, and EVERY cited
           code exists in `declared`. Both halves are required: citing the same
           code twice is not two stories (the `set()` dedup handles this for
           free); citing a code the feature never declares is fabrication, not
           citation — `cited <= declared` is the subset test that makes the
           hatch unforgeable.

    Returns `(qualifies, reasons)`; `reasons` names every FAILED condition and is
    empty iff `qualifies` is True.
    """
    m = _FUNC_CAP_RATIONALE_RE.search(section2_text)
    body = m.group("body") if m else ""
    ok_1 = bool(body)
    word_count = len(body.split())
    ok_2 = ok_1 and word_count >= 12
    cited: set[str] = set()
    for fam in families:
        cited |= set(_CAP_FAMILY_RE[fam].findall(body))
    ok_3 = ok_1 and len(cited) >= 2 and cited <= declared

    reasons: list[str] = []
    if not ok_1:
        reasons.append("no same-line '**Single-capability rationale:** <text>' found in § 2")
    else:
        if not ok_2:
            reasons.append(f"rationale is {word_count} word(s), needs >= 12")
        unknown = cited - declared
        if len(cited) < 2:
            reasons.append(f"rationale cites {len(cited)} distinct code(s), needs >= 2")
        elif unknown:
            reasons.append(
                "rationale cites code(s) this feature never declares: "
                + ", ".join(sorted(unknown))
            )
    return (ok_1 and ok_2 and ok_3), reasons


def _check_capability_analysis(lines: list[str], b2: tuple[int, int] | None,
                               b7: tuple[int, int] | None, func_type: str, tech_text: str,
                               func_path: Path, root: Path) -> list[dict]:
    """§ 2 Functional Capabilities — count-based review triggers (phase 06,
    capability-map plan). D-7: the US/BL count NEVER forces a split — it forces a
    WRITTEN decision. Only `b7` is threaded through (not `b4`/`b5`/`b6`): the "US"
    family in `_func_code_sets` is populated exclusively from § 7 headings, and
    this check has no use for the FR/BR/SCR families that the other three bounds
    feed — passing them would be dead weight this function never reads.

    `cap.analysis_required` (critical): `#CAP == 1`, the claim state is not
      "unfilled", the feature is over its type's CRITICAL band, and the
      `**Single-capability rationale:**` line fails any of SC-1's three
      deterministic conditions (see `_cap_rationale_verdict`).
    `cap.review_advised` (warning): `#CAP == 1` and the count sits in the WARNING
      band. No rationale requirement — this is a nudge, not a gate.
    `#CAP >= 2` silences both, for every type — the count never forces a split
    (D-7, verbatim: "Không tạo CAP chỉ vì số lượng US vượt threshold").

    Band table (`_CAP_ANALYSIS_BANDS`): `ui` keys on distinct `US###` declared in
    § 7 (warn 3-4, crit >=5); `background` keys on distinct `BL###` cited in the
    twin technical-spec.md (warn 5-7, crit >=8) — [SC-7] that BL threshold is a
    ~1.6x scaling of the US bands measured against n=8 background features in one
    corpus, PROVISIONAL, and must be re-measured once a second real corpus with
    background features exists (see the constant's own comment for the full
    provenance). `mixed` evaluates BOTH rows and takes the stricter outcome
    (critical beats warning beats silent) — the citation family for the rationale
    follows the same union, so `mixed` accepts any 2 verified codes across both
    families (never just US), matching the band's own denominator.

    [SA-6] ACCEPTED LIMITATION: a BL count tallies DECLARED codes, so it is
    gameable by umbrella codes — one `BL050_EmailNotifications` "covering all 25
    Mail classes" counts as 1, not 25. This is not hypothetical:
    `templates/behavior-logic-template.md:84-95` documents it as an OCCURRING
    anti-pattern (`BL050_EmailNotifications` "Covers all 25 Mail classes",
    `BL080_AuditLogWorkers` "Umbrella for 12 audit log job variants"). This
    check's background variant inherits the BL reviewer's own Rule C1
    aggregation gate as its dependency; where that gate is bypassed, this check
    under-counts and stays silent. A BL-per-source-symbol check belongs to the
    BL validator, not here.

    [FM-4] Gated on `_cap_table_lib.claim_state(...) != "unfilled"` — reused
    verbatim from phase 05 so the validator and the `cap-map` migrate step can
    never disagree about what "unfilled" means. This mute is checked FIRST, and
    the `#CAP != 1` guard is the very next statement, on purpose: it makes "the
    count never forces a split" structurally true rather than a property of
    message wording.
    """
    header_cells, rows = _cap_table_lib.data_rows(lines, b2)
    if _cap_table_lib.claim_state(header_cells, rows) == "unfilled":
        return []
    if len(rows) != 1:
        return []

    us_declared = _func_code_sets(lines, None, None, None, b7)["US"]
    bl_declared = set(_FUNC_BL_CODE_RE.findall(tech_text))
    declared_by_family = {"US": us_declared, "BL": bl_declared}
    counts = {"US": len(us_declared), "BL": len(bl_declared)}

    # `_func_type` already defaults an absent/unparseable Type field to "ui" (its
    # own docstring: "never silently relaxes"); this `.get` fallback mirrors that
    # same philosophy for the rarer case of a PRESENT but non-standard Type value
    # (e.g. a typo) — fail to the stricter "ui" band rather than skip the check.
    bands = _CAP_ANALYSIS_BANDS.get(func_type, _CAP_ANALYSIS_BANDS["ui"])
    ranked = []
    for family, (warn_floor, crit_floor) in bands.items():
        count = counts[family]
        state = _cap_band_state(count, warn_floor, crit_floor)
        overage = count - (crit_floor if state == "critical" else warn_floor)
        ranked.append((_CAP_SEVERITY_RANK[state], overage, family, count, warn_floor, crit_floor, state))
    ranked.sort(key=lambda t: (t[0], t[1]), reverse=True)
    _, _, family, count, warn_floor, crit_floor, state = ranked[0]

    if state == "silent":
        return []

    section2_text = "\n".join(lines[b2[0]:b2[1]])
    declared_union: set[str] = set()
    for fam in bands:
        declared_union |= declared_by_family[fam]
    qualifies, reasons = _cap_rationale_verdict(section2_text, list(bands), declared_union)

    line = b2[0] + 1

    if state == "critical":
        if qualifies:
            return []
        return [_issue(
            "critical", "cap.analysis_required", func_path, root, line,
            f"type={func_type} {family} count {count} >= critical floor {crit_floor} with "
            f"#CAP == 1 and no qualifying rationale ({'; '.join(reasons)}) — declare a second "
            "capability or write a qualifying '**Single-capability rationale:**' per "
            "references/code-formats.md § Capability-Level Intent (authority)",
        )]

    return [_issue(
        "warning", "cap.review_advised", func_path, root, line,
        f"type={func_type} {family} count {count} is in the review band "
        f"({warn_floor}-{crit_floor - 1}) with #CAP == 1 — review the intent boundary per "
        "references/code-formats.md § Capability-Level Intent (authority)",
    )]


# ---------------------------------------------------------------------------
# Phase 08 (capability-map plan) — cap.promote_candidate, Tier 1 of the
# promote-eligibility advisory. Tiers 2/3 (a corpus-wide F###-reference
# enumerator + a directory-move migrate step) do not exist anywhere in this
# repo and are deliberately out of scope (Plan B) — this check writes NOTHING.
# ---------------------------------------------------------------------------
_CAP_PROMOTE_MEDIAN_US = 2  # sharetribe corpus's measured median whole-feature US count


def _check_promote_candidates(lines: list[str], b2: tuple[int, int] | None,
                              func_path: Path, root: Path) -> list[dict]:
    """`cap.promote_candidate` (warning): a § 2 CAP row that already carries more
    substance, by itself, than the median whole feature — ALL FOUR conditions:

    - `#CAP >= 2` for the feature (a lone CAP cannot be "promoted"; there is
      nothing to split it from — promoting it is just renaming the feature).
      `#CAP` is the total § 2 data-row count from `_cap_table_lib.data_rows`,
      the SAME denominator `_check_capability_analysis` uses for `#CAP == 1` —
      not "capabilities that happen to have >=1 claim" (a capability declared
      but not yet claimed, a "partial" fill state, still counts toward `#CAP`;
      it simply cannot itself qualify, since 0 claims can never clear the
      per-family floors below).
    - the row's own claimed US### count is `>= 3`.
    - the row's own claimed FR-### count is `>= 3`.
    - the row's own claimed SCR### count is `>= 1`.

    Every count comes from `_cap_claims` (phase 05) — the § 2 table's own claim
    cells, never a fresh §§ 4-7 parse (AD-6: one § 2 table parser, no second
    independent implementation of the same invariant). Because phase 05's
    exhaustiveness already guarantees every code belongs to exactly one CAP
    row, "this CAP's codes don't overlap another's" carries zero information —
    the signal here is magnitude, not overlap: the measured median feature in
    the sharetribe corpus carries `_CAP_PROMOTE_MEDIAN_US` US, so a single CAP
    row claiming >= 3 US already exceeds a whole median feature.

    [FM-4] Gated on `_cap_table_lib.claim_state(...) != "unfilled"`, reused
    verbatim from phase 05/06 (never re-derived) — a widened-but-empty § 2 has
    no claims to count, so this stays silent rather than reporting a hollow 0
    as if it were a real verdict about the modelling.

    The message states all four observed counts so a human reviewer sees the
    REASON, not a verdict, and explicitly says promotion is a manual,
    human-decided operation today — no `--migrate` step implements it (Tier 2/3
    is Plan B; naming a command that no code implements would be a documented
    lie). Writes NOTHING: no rename, no directory creation, no sentinel — this
    check only ever returns `_issue(...)` warnings."""
    header_cells, raw = _cap_table_lib.data_rows(lines, b2)
    if _cap_table_lib.claim_state(header_cells, raw) == "unfilled":
        return []
    if len(raw) < 2:
        return []

    claims = _cap_claims(lines, b2)
    per_cap: dict[str, set[str]] = {}
    for code, cap_ids in claims.items():
        for cap_id in cap_ids:
            per_cap.setdefault(cap_id, set()).add(code)
    names = {row[0]: row[1] for row in raw if len(row) > 1}

    issues: list[dict] = []
    for cap_id in sorted(per_cap):
        codes = per_cap[cap_id]
        n_us = sum(1 for c in codes if _FAMILY_CODE_RE["US"].fullmatch(c))
        n_fr = sum(1 for c in codes if _FAMILY_CODE_RE["FR"].fullmatch(c))
        # `_SCR_CLAIM_RE`, not `_FAMILY_CODE_RE["SCR"]`: `_cap_claims` now keys composite
        # refs by their full `SCR###/REG###` token, which the bare-parent pattern cannot
        # fullmatch. Counting with the bare pattern would silently undercount every
        # region-scoped capability here — magnitude is exactly what this check measures.
        n_scr = sum(1 for c in codes if _SCR_CLAIM_RE.fullmatch(c))
        if n_us >= 3 and n_fr >= 3 and n_scr >= 1:
            name = names.get(cap_id, "")
            issues.append(_issue(
                "warning", "cap.promote_candidate", func_path, root, b2[0] + 1,
                f"{cap_id} '{name}' claims {n_us} US / {n_fr} FR / {n_scr} SCR — exceeds "
                f"the median feature's {_CAP_PROMOTE_MEDIAN_US} US. Promotion to its own "
                "F### is a human decision today; no automated path exists. See "
                "references/code-formats.md § Capability-Level Intent.",
            ))
    return issues


def _check_risk_as_rule(lines: list[str], b5: tuple[int, int] | None,
                        b11: tuple[int, int] | None, func_path: Path,
                        root: Path) -> list[dict]:
    """func.risk_as_rule (warning): a § 5 Business Rules line reads like an observed
    DEFECT ('should not' / 'incorrectly' / 'bug') with no § 11 Risks & Known Issues
    counterpart recorded anywhere in the file. The rule never inspects WHICH BR row
    the risk belongs to — only whether § 11 has any recorded row at all — because
    matching a specific BR to a specific RISK row is a judgment call for the
    researcher/reviewer, not a deterministic pairing this script should invent."""
    if not b5:
        return []
    has_risk_row = False
    if b11:
        section_text = "\n".join(lines[b11[0]:b11[1]]).strip()
        if section_text and not _FUNC_RISKS_NONE_RE.match(section_text):
            table_rows = [ln for ln in lines[b11[0]:b11[1]] if ln.strip().startswith("|")]
            has_risk_row = len(table_rows) > 2  # header + separator + >=1 data row
    if has_risk_row:
        return []
    issues: list[dict] = []
    for i in range(b5[0], b5[1]):
        if _FUNC_RISK_LANGUAGE_RE.search(lines[i]):
            issues.append(_issue("warning", "func.risk_as_rule", func_path, root, i + 1,
                                 "§ 5 Business Rules row reads like an observed defect "
                                 "('should not' / 'incorrectly' / 'bug'); record it as-is in "
                                 "§ 11 Risks & Known Issues instead of folding it into a rule"))
    return issues


def _check_user_story_shape(lines: list[str], headings: list, b7: tuple[int, int] | None,
                            func_path: Path, root: Path) -> list[dict]:
    """func.user_story_shape (warning): every § 7 User Stories block must lead with
    **Actor:**, **Goal:**, and **Business value:** bold-labeled fields (each with a
    value on the same line) before its narrative — the Actor -> Goal -> Business value
    shape the audience-split feedback asked for. A fresh scaffold has no ### US###
    heading yet (§ 7 is a curly-brace placeholder), so this never fires on a blank
    scaffold — nothing to check."""
    if not b7:
        return []
    us_heads = [(idx, h) for idx, h in headings
               if b7[0] <= idx < b7[1] and _FUNC_US_HEADING_RE.match(h)]
    issues: list[dict] = []
    for k, (idx, raw) in enumerate(us_heads):
        end = us_heads[k + 1][0] if k + 1 < len(us_heads) else b7[1]
        block_text = "\n".join(lines[idx:end])
        missing = []
        if not _FUNC_US_ACTOR_RE.search(block_text):
            missing.append("**Actor:**")
        if not _FUNC_US_GOAL_RE.search(block_text):
            missing.append("**Goal:**")
        if not _FUNC_US_VALUE_RE.search(block_text):
            missing.append("**Business value:**")
        if missing:
            issues.append(_issue("warning", "func.user_story_shape", func_path, root, idx + 1,
                                 f"{raw} missing {', '.join(missing)} field(s) — the "
                                 f"Actor -> Goal -> Business value shape is required"))
    return issues


def _check_functional_spec(func_path: Path, tech_path: Path, root: Path,
                           is_draft: bool = False) -> list[dict]:
    """Validate functional-spec.md — the BA/QA half of the feature-spec pair.

    Unions the 3 retired checkers (_check_business_context / _check_screens /
    _check_edge_cases) into one, on the new file, per the Deterministic Validator
    Coverage table in references/verification-checklist-feature-spec.md. Re-homes all
    7 old rule_ids (2 subsumed into func.missing_h2) and adds new ones with no legacy
    predecessor. See that table for the full old->new map.

    P07 (human-readable SOT) renumbered the 10-section shape to 13 (net-new §§ 2, 11,
    12 — see REQUIRED_H2_FUNC). A file still in the OLD shape is detected once
    (`is_pre_sot`) and reported as a SINGLE `func.sections_pre_sot` warning instead of
    a wall of findings keyed on headings that do not exist yet — see the constant
    comment above `_FUNC_PRE_SOT_SENTINEL`.
    """
    if not func_path.is_file():
        sev = "warning" if is_draft else "critical"
        return [_issue(sev, "func.missing", func_path, root, 0, "functional-spec.md not found")]

    lines = func_path.read_text(encoding="utf-8", errors="replace").splitlines()
    headings, blocks = parse_headings_and_blocks(lines)
    scrubbed = strip_html_comments(lines)
    h2 = [(i, h) for i, h in headings if h.startswith("## ") and not h.startswith("### ")]
    issues: list[dict] = []

    h2_names = [h for _, h in h2]
    # [SA-3] Whole-document sentinel membership alone is fail-open: a v27-shaped file
    # carrying a STRAY "## 2. Open Decisions" heading anywhere (e.g. a leftover/misplaced
    # section) would otherwise mute every section-bound critical for the whole file, new
    # and old. A genuine pre-SOT file lacks "## 2. Functional Capabilities" by
    # definition — that absence IS what makes it pre-SOT — so presence of BOTH headings
    # must never resolve to "pre-SOT". This widens un-muting to pre-existing
    # section-bound criticals too, not just this phase's new checks — see
    # test_stray_functional_capabilities_heading_unmutes_pre_sot for the regression test
    # this exact co-condition guards; reverting it to a bare membership test is a
    # one-line diff that reopens the hole, so do not "simplify" this back.
    is_pre_sot = (_FUNC_PRE_SOT_SENTINEL in h2_names
                  and "## 2. Functional Capabilities" not in h2_names)

    if is_pre_sot:
        issues.append(_issue("warning", "func.sections_pre_sot", func_path, root, None,
                             "functional-spec.md is still in the pre-SOT 10-section shape "
                             "('## 2. Open Decisions' present); migrate to the 13-section "
                             "shape (target-shape-spec.md § 2). Section-shape checks are "
                             "muted for this file until migrated — dev-token/secret-shape "
                             "scans still apply."))
    else:
        # Required H2 order (13 sections, exact order) — generalized from the old
        # 3-section BC list (func.missing_h2). screens.missing/screens.missing_h2/
        # edge_cases.missing are subsumed here: those files no longer exist standalone,
        # and their PRESENCE is covered by this same required-section check (§ 6 / § 9
        # are two of the 13 required H2s).
        present = [h for h in h2_names if h in REQUIRED_H2_FUNC]
        expected = [h for h in REQUIRED_H2_FUNC if h in present]
        if present != expected or set(present) != set(REQUIRED_H2_FUNC):
            missing = [h for h in REQUIRED_H2_FUNC if h not in present]
            issues.append(_issue("critical", "func.missing_h2", func_path, root, None,
                                 f"required H2 missing/out-of-order; missing: {missing}"
                                 if missing else "required H2 out of order"))

    # Forbidden-token scan — dev tokens (func.dev_token) + secret shapes (func.secret_shape),
    # outside fenced code / HTML comments. FR-###/BR-###/SM-###/DEC-###/SCR###/US### codes
    # are allowed and expected (inverted from the old business-context.md rule). Runs
    # regardless of is_pre_sot — content-level leaks are not a section-shape concern.
    fenced = {i for s, e, _ in blocks for i in range(s, e + 1)}
    for i, raw in enumerate(lines):
        if i in fenced:
            continue
        clean = scrubbed[i]
        if not clean.strip():
            continue
        # dev tokens: inline code spans are exempt (see strip_inline_code).
        m = FUNC_DEV_TOKEN_RE.search(strip_inline_code(clean))
        if m:
            issues.append(_issue("critical", "func.dev_token", func_path, root, i + 1,
                                 f"dev token outside fence: {m.group()!r}"))
        # secrets: UNCHANGED — scans the full line, inline code spans included.
        # A secret quoted in backticks is still a leaked secret; do not extend
        # the dev-token exemption here (see the scope-guard comment above
        # strip_inline_code and T6 in the test suite). A placeholder-only VALUE
        # (ellipsis, <bracket>, code-symbol reference) does not fire — see
        # _neutralize_placeholder_assignments above; a real credential's value
        # never reduces to that shape, so it is left untouched and still fires.
        neutralized = _neutralize_placeholder_assignments(clean)
        secret_hit = scrub_generic_secret(neutralized) != neutralized
        _, cred_hit = scrub_credentials(neutralized)
        if secret_hit or cred_hit:
            issues.append(_issue("critical", "func.secret_shape", func_path, root, i + 1,
                                 "secret-shaped value outside fence"))

    if is_pre_sot:
        return issues

    b2 = _func_h2_bounds(h2, "## 2. Functional Capabilities", len(lines))
    b4 = _func_h2_bounds(h2, "## 4. Requirements", len(lines))
    b5 = _func_h2_bounds(h2, "## 5. Business Rules", len(lines))
    b6 = _func_h2_bounds(h2, "## 6. Screens", len(lines))
    b7 = _func_h2_bounds(h2, "## 7. User Stories", len(lines))
    b9 = _func_h2_bounds(h2, "## 9. Edge Cases", len(lines))
    b10 = _func_h2_bounds(h2, "## 10. Edge Behaviours to Verify", len(lines))
    b11 = _func_h2_bounds(h2, "## 11. Risks & Known Issues", len(lines))
    b3 = _func_h2_bounds(h2, "## 3. Open Decisions", len(lines))
    func_type = _func_type(lines)

    issues.extend(_check_open_decisions(lines, b3, func_path, root))
    issues.extend(_check_screens_section(lines, b6, func_type, func_path, root))
    issues.extend(_check_edge_cases_section(lines, b9, func_type, func_path, root))
    issues.extend(_check_rule_density(lines, b4, b5, func_path, root))
    issues.extend(_check_capabilities_section(lines, b2, b4, b5, b6, b7, func_path, root))
    # Phase 08 (capability-map plan) — Tier 1 promote-eligibility advisory. Lives
    # right after the § 2 checks above (same § 2 table, same claims), not down by
    # `_check_capability_analysis` — that check reads `tech_text` for its BL
    # denominator; this one never touches `tech_text` at all.
    issues.extend(_check_promote_candidates(lines, b2, func_path, root))
    issues.extend(_check_risk_as_rule(lines, b5, b11, func_path, root))
    issues.extend(_check_user_story_shape(lines, headings, b7, func_path, root))

    tech_text = tech_path.read_text(encoding="utf-8", errors="replace") if tech_path.is_file() else ""
    # [AD-4] Phase 06's check lives here, not inside phase 05's
    # `_check_capabilities_section` above — it needs `tech_text` (the BL
    # denominator for background/mixed features), which isn't read until this
    # line. A new function called after this read avoids hoisting that read
    # and keeps phase 05's function untouched even though both share this file.
    issues.extend(_check_capability_analysis(lines, b2, b7, func_type, tech_text, func_path, root))
    own_fcode = _extract_own_fcode(lines)
    # features_root is func_path's grandparent — func_path is always
    # `<features_root>/<this_feature_dir>/functional-spec.md` (see
    # _check_feature_dir below), so this needs no extra plumbing through
    # validate()/main(); when func_path itself doesn't resolve to that shape
    # (e.g. an isolated fixture with no real sibling features), the glob in
    # _other_feature_declares_code simply finds nothing and fails closed.
    features_root = func_path.resolve().parent.parent
    code_issues, fr_in_4 = _check_code_surfacing(
        lines, b4, b5, tech_text, func_path, root, own_fcode, features_root)
    issues.extend(code_issues)
    issues.extend(_check_edge_behaviours(lines, b10, fr_in_4, func_path, root))

    return issues


def _check_feature_dir(feature_dir: Path, root: Path) -> list[dict]:
    """Run the technical-spec.md + functional-spec.md validators for a feature directory.

    A takumi draft (technical-spec.md carrying BOTH status:draft AND
    authored_by:takumi) may legitimately defer functional-spec.md — the
    "draft exit 0" contract. We determine draft-ness ONCE from the canonical
    technical-spec.md and thread it into the functional-spec check so a missing
    functional-spec.md downgrades critical -> warning instead of failing the run. [MED-1]
    """
    tech_spec = feature_dir / "technical-spec.md"
    is_draft = (
        tech_spec.is_file()
        and read_spec_status(tech_spec) == "draft"
        and read_authored_by(tech_spec) == "takumi"
    )
    issues = []
    issues.extend(_check_technical_spec(tech_spec, root))
    issues.extend(_check_functional_spec(feature_dir / "functional-spec.md", tech_spec, root, is_draft))
    return issues


_FEATURE_FILE_NAMES = set(FEATURE_FILES)


def validate(plan_dir, root, single, docs_root=None):
    if single is not None:
        if single.is_dir():
            feature_dir = single
            issues = _check_feature_dir(feature_dir, root)
        elif single.name in _FEATURE_FILE_NAMES:
            # Standard 4-file layout: derive feature dir from parent
            feature_dir = single.parent
            issues = _check_feature_dir(feature_dir, root)
        else:
            # Legacy/standalone spec file: validate directly as technical-spec
            feature_dir = single.parent
            issues = _check_technical_spec(single, root)
        try:
            rel = str(feature_dir.relative_to(root))
        except ValueError:
            rel = str(feature_dir)
        per_spec = {feature_dir.name: {"spec_path": rel, "issues": issues}}
    elif docs_root is not None:
        # F1: --docs-root mode — iterate docs/features/*/technical-spec.md
        per_spec = {}
        for spec_path in iter_docs_technical_specs(docs_root):
            # iter_docs_technical_specs already skips .pending dirs
            feature_dir = spec_path.parent
            try:
                rel = str(feature_dir.relative_to(root))
            except ValueError:
                rel = str(feature_dir)
            per_spec[feature_dir.name] = {
                "spec_path": rel,
                "issues": _check_feature_dir(feature_dir, root),
            }
    else:
        per_spec = {}
        for fd in iter_feature_dirs(plan_dir):
            if (fd / ".pending").is_file():
                continue  # W6 still in progress — skip incomplete feature dirs
            try:
                rel = str(fd.relative_to(root))
            except ValueError:
                rel = str(fd)
            per_spec[fd.name] = {"spec_path": rel, "issues": _check_feature_dir(fd, root)}
    return {"validator": VALIDATOR,
            "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "plan_dir": str(plan_dir), "specs": per_spec}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="rebuild-spec Wave 6.5 feature-spec validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir"); g.add_argument("--spec"); g.add_argument("--docs-root")
    p.add_argument("--project-root", default=None); p.add_argument("--summary-out", default=None)
    args = p.parse_args(argv)
    root = resolve_project_root(args.project_root)
    docs_root_path: Path | None = None
    if args.docs_root:
        # F1: --docs-root <project_root> mode — scan docs/features/*/technical-spec.md
        docs_root_path = Path(args.docs_root).resolve()
        if not docs_root_path.is_dir():
            print(f"[ERROR] --docs-root is not a directory: {docs_root_path}", file=sys.stderr)
            return 2
        # Defect fix (p14-migration-report.md § Risks item 2): THIS script's
        # --docs-root means the project root containing docs/features/ — unlike
        # validate_reading_guide_db_impact.py / validate_feature_screen_link.py /
        # run_doc_migrations.py, where the identical flag name means the docs/
        # folder itself. Passing the docs/ folder here used to look for the
        # non-existent <given>/docs/features and silently return `{"specs": {}}`
        # at exit 0 — a clean pass over zero files examined. Detect the tell-tale
        # shape (a features/ dir sitting directly under the given path, with no
        # nested docs/features/) and refuse loudly rather than guess which
        # directory the caller actually meant.
        if (docs_root_path / "features").is_dir() and not (docs_root_path / "docs" / "features").is_dir():
            print(
                f"[ERROR] --docs-root {docs_root_path} looks like a docs/ folder itself "
                f"(it has a features/ subdirectory) but this script's --docs-root means "
                f"the PROJECT ROOT containing docs/features/ — pass the parent directory "
                f"instead (e.g. --docs-root {docs_root_path.parent}).",
                file=sys.stderr,
            )
            return 2
        plan_dir = docs_root_path; single = None
    elif args.plan_dir:
        plan_dir = Path(args.plan_dir).resolve(); single = None
        if not plan_dir.is_dir():
            print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr); return 2
    else:
        single = Path(args.spec).resolve()
        # Accept a feature dir or a .md file inside a feature dir
        if single.is_dir():
            # single = artifacts/features/{slug}/ → plan_dir = two levels up
            plan_dir = single.parent.parent
        elif single.is_file():
            # single = artifacts/features/{slug}/some-file.md → plan_dir = three levels up
            plan_dir = single.parent.parent.parent
        else:
            print(f"[ERROR] --spec is not a file: {single}", file=sys.stderr); return 2
    try:
        if args.docs_root:
            assert_under(docs_root_path, root)
        else:
            assert_under(plan_dir, root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr); return 2
    try:
        result = validate(plan_dir, root, single, docs_root=docs_root_path)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] validator crashed: {exc}", file=sys.stderr); return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    crit = sum(1 for s in result["specs"].values() for i in s["issues"] if i["severity"] == "critical")
    if args.summary_out:
        sp = Path(args.summary_out).resolve()
        try:
            assert_under(sp.parent, root)
            summary = load_summary(sp, plan_dir.name)
            merge_validator_result(summary, VALIDATOR, result)
            recalculate_totals(summary); summary["overall_status"] = derive_overall_status(summary)
            atomic_write(sp, summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr); return 2
    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
