"""Characterization tests for `_audience_split_data_inventory_lib.reshape_data_inventory`.

Phase 02 (plans/260818-1332-rebuild-spec-human-readable-sot) exists because this
function had ZERO direct unit tests anywhere in the suite before this file: every
fixture that flows through Mode C (`_audience_split_mode_c_lib.compose_mode_c`) carries
an `N/A` Data Inventory body, which short-circuits the reshape at L25-26 before the
column-reshape branch (L27-55) ever runs. Phase 05 rewrites that branch (the Data
Inventory table gets absorbed into a new `## 3. UI Elements` inventory) -- these tests
are the failure signal that rewrite needs. They are CHARACTERIZATION tests: they pin
today's behavior, including two surprising things found while writing them (see the
two `# CHARACTERIZATION:`-tagged tests below) -- reported, not fixed, per Phase 02 scope.

Branch inventory of `reshape_data_inventory` (`_audience_split_data_inventory_lib.py`,
L19-56), enumerated top to bottom:

  B1 (L23-26)  `table_idx` (lines matching `^\\s*\\|`) has fewer than 2 entries -> the
               body is returned UNCHANGED (`N/A` prose, empty string, or any body with
               no parseable 2+-line table all take this path).
  B2 (L27-30)  A table exists, but its header lacks "field" OR lacks "display label"
               (casefold-compared) -> UNCHANGED. Two sub-cases share this branch and are
               tested separately since they arise from different real situations: (a) the
               body is ALREADY reshaped (has "display label", no "field" -- the Mode C
               idempotency case) and (b) the body is some other table entirely (neither
               header present -- a defensive no-op, not an expected input shape).
  B3 (L31-38)  Header parses: `field_i`/`label_i` located, `cross_i` located if present
               (`None` if the table has no Cross-ref column at all). New header =
               [Display Label, <every other original column except Field, in original
               order>].
  B4 (L39-43)  The separator row (`|---|---|...|`, matched by `_TABLE_SEP_RE`) is
               REGENERATED from the new header's widths, not copied from the input.
  B5 (L44-47)  A data row with fewer cells than `max(field_i, label_i) + 1` is malformed
               / a placeholder -- passed through UNCHANGED, byte-for-byte, as its own
               output line (not reshaped into the new column order).
  B6 (L48-54)  A well-formed data row: `Field` is dropped, `Display Label` promoted to
               column 0. If (and only if) ALL of these hold: a Cross-ref column exists
               (`cross_i is not None`), the Field value is truthy, the Field value
               differs from the Display Label value, and the Field value is not the
               literal placeholder `"-"` -- the ORIGINAL Field value survives as a
               `` (binding: `{field}`) `` suffix appended to the Cross-ref cell, so
               dropping the column never silently discards information. Any one of
               those four conditions failing means the Cross-ref cell passes through
               with no suffix.
  BUG-1        NOT fence-aware: unlike every other scanner in this skill (which routes
               through `_md_scan_lib.iter_lines_with_fence`), `reshape_data_inventory`
               regexes every physical line of `body` regardless of fence state. A pipe
               that happens to lead a line INSIDE a fenced code sample is treated as a
               real table row.
  BUG-2        Consequence of BUG-1's own line accounting: the function's output is
               built from `lines[:table_idx[0]]` (preamble) plus one emitted line per
               entry in `table_idx[1:]` -- anything in `body` AFTER the last line that
               matched the table-row regex is never re-emitted and is silently dropped,
               not just miscategorized.

Real-corpus provenance for the "populated multi-row table" case (the one no existing
fixture exercises): no fixture anywhere in this repo (grep confirmed by the Phase 02
research report) carries a PRE-reshape Data Inventory table with a `Field` column --
every real generated corpus available today is POST-migration. The two multi-row test
rows below are therefore reverse-derived: each is the unique v26-shaped `Field | Display
Label | Source | Format | Empty Behavior | Cross-ref` row that `reshape_data_inventory`
maps onto the REAL already-reshaped row taken verbatim from
`evidence/corpus-g2/SCR020_LoginPage.spec.md` and `.../SCR012_ErrorNotFound.spec.md`
(P00 real generated output). The derivation was verified by hand (the `(binding:
...)` suffix's double backticks pin the exact pre-image Field value) and then confirmed
by running the function -- the assertions below check the ACTUAL real-fixture text, not
a hand-typed guess at what reshape "should" produce.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _audience_split_data_inventory_lib import reshape_data_inventory  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[5]  # agent-kit/
_SOT_CORPUS = Path(__file__).resolve().parent / "fixtures" / "sot-corpus"
"""Real generated corpus, git-tracked. Lived under `plans/` (gitignored) until it took
the whole CI suite down at collection time — see fixtures/sot-corpus/README.md."""
EVIDENCE_DIR = (
    _SOT_CORPUS
)
CORPUS_G1 = EVIDENCE_DIR / "corpus-g1"
CORPUS_G2 = EVIDENCE_DIR / "corpus-g2"


def _h2_body(text: str, heading: str) -> str:
    """Minimal H2-body slicer for the fixtures used here -- stops at the next H1/H2."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i + 1
            break
    assert start is not None, f"{heading!r} not found"
    end = len(lines)
    for j in range(start, len(lines)):
        stripped = lines[j].strip()
        if stripped.startswith("# ") or stripped.startswith("## "):
            end = j
            break
    return "\n".join(lines[start:end]).strip("\n")


# --------------------------------------------------------------------------- #
# B3/B4/B6 -- the column-reshape branch, on inputs reverse-derived from real
# corpus output (see module docstring for the derivation method).
# --------------------------------------------------------------------------- #
def test_reshape_populated_multirow_table_matches_real_corpus_output():
    # Reaches B3 (header parse), B4 (separator regeneration), B6 (binding-annotation
    # append) across two independently-sourced rows in a single table -- the branch
    # combination no existing fixture (all N/A bodies) has ever exercised.
    v26_header = "| Field | Display Label | Source | Format | Empty Behavior | Cross-ref |"
    v26_sep = "|---|---|---|---|---|---|"
    # Pre-image of the real SCR020_LoginPage.spec.md row (binding value `session[:form_login]`,
    # itself backtick-quoted -- the double backticks in the real output's Cross-ref cell
    # are the tell: `` (binding: ``session[:form_login]``) ``).
    row_020 = (
        "| `session[:form_login]` | (pre-filled login field value) "
        "| `session[:form_login]` store state | raw string "
        "| empty string (blank input) | N/A |"
    )
    # Pre-image of the real SCR012_ErrorNotFound.spec.md row (binding value `title(404)`).
    row_012 = (
        '| `title(404)` | `<title>` in `<head>` '
        '| computed — `@current_community.name(locale) + " - page not found"` '
        '| string concat | Falls back to `"page not found"` if community not resolved '
        "| N/A |"
    )
    v26_body = "\n".join([v26_header, v26_sep, row_020, row_012])

    golden_020 = _h2_body(
        (CORPUS_G2 / "SCR020_LoginPage.spec.md").read_text(encoding="utf-8"),
        "## Data Inventory",
    )
    golden_012 = _h2_body(
        (CORPUS_G2 / "SCR012_ErrorNotFound.spec.md").read_text(encoding="utf-8"),
        "## Data Inventory",
    )
    expected = "\n".join(
        golden_020.splitlines()[:2]  # shared header + regenerated separator
        + [golden_020.splitlines()[2], golden_012.splitlines()[2]]
    )

    assert reshape_data_inventory(v26_body) == expected


def test_reshape_single_row_reproduces_real_scr020_fixture_byte_for_byte():
    # Isolates the SCR020 row from the combined test above, so a future failure there
    # points at exactly one row's transform rather than the pair.
    v26_body = (
        "| Field | Display Label | Source | Format | Empty Behavior | Cross-ref |\n"
        "|---|---|---|---|---|---|\n"
        "| `session[:form_login]` | (pre-filled login field value) "
        "| `session[:form_login]` store state | raw string "
        "| empty string (blank input) | N/A |"
    )
    golden = _h2_body(
        (CORPUS_G2 / "SCR020_LoginPage.spec.md").read_text(encoding="utf-8"),
        "## Data Inventory",
    )
    assert reshape_data_inventory(v26_body) == golden


# --------------------------------------------------------------------------- #
# B2(a) -- already-reshaped body (idempotency), on the REAL post-migration fixtures.
# --------------------------------------------------------------------------- #
def test_reshape_is_idempotent_on_real_already_reshaped_scr020_body():
    # Reaches B2: header has "display label", lacks "field" -> UNCHANGED.
    body = _h2_body(
        (CORPUS_G2 / "SCR020_LoginPage.spec.md").read_text(encoding="utf-8"),
        "## Data Inventory",
    )
    assert reshape_data_inventory(body) == body


def test_reshape_is_idempotent_on_real_already_reshaped_scr012_body():
    # Same branch (B2), second independent real fixture.
    body = _h2_body(
        (CORPUS_G2 / "SCR012_ErrorNotFound.spec.md").read_text(encoding="utf-8"),
        "## Data Inventory",
    )
    assert reshape_data_inventory(body) == body


# --------------------------------------------------------------------------- #
# B1 -- no parseable table (N/A short-circuit, empty body).
# --------------------------------------------------------------------------- #
def test_reshape_na_body_from_real_g1_fixture_is_unchanged():
    # Reaches B1: zero lines match the leading-pipe regex. Exact text lifted from the
    # real v26 fixture (corpus-g1/SCR001_Login.spec.md's own Data Inventory body) --
    # this is the shape EVERY fixture in the suite used before Phase 02, per the
    # blast-radius report's zero-coverage finding.
    body = "N/A — screen displays no dynamic data (static marketing/error page)"
    assert body == _h2_body(
        (CORPUS_G1 / "SCR001_Login.spec.md").read_text(encoding="utf-8"),
        "## Data Inventory",
    )
    assert reshape_data_inventory(body) == body


def test_reshape_empty_body_is_unchanged():
    # Reaches B1 via the degenerate case: `table_idx` is `[]`, `len([]) < 2`.
    assert reshape_data_inventory("") == ""


# --------------------------------------------------------------------------- #
# B2(b) -- a real table present, but not Data-Inventory-shaped at all (defensive
# no-op, distinct real-world trigger from the idempotency case above).
# --------------------------------------------------------------------------- #
def test_reshape_leaves_unrelated_real_table_untouched():
    # Reaches B2 via the OTHER route: header has neither "field" nor "display label".
    # Body is the real Layout Regions table lifted verbatim from corpus-g1's
    # SCR001_Login.spec.md -- proof that if a non-Data-Inventory table ever lands in
    # this function's input (e.g. a mis-scoped caller), it is passed through rather
    # than mangled.
    body = (
        "| Region ID | Name | Position | Scrollable | Key Components | Responsive Behavior |\n"
        "|-----------|------|----------|------------|----------------|---------------------|\n"
        "| R1 | Header | fixed-top | no | Header | always |"
    )
    fixture_text = (CORPUS_G1 / "SCR001_Login.spec.md").read_text(encoding="utf-8")
    assert body in fixture_text  # provenance check: this table really is in the fixture
    assert reshape_data_inventory(body) == body


# --------------------------------------------------------------------------- #
# B5 -- malformed / placeholder data row (too few cells to reshape).
# --------------------------------------------------------------------------- #
def test_reshape_passes_through_malformed_short_row_unchanged():
    # Reaches B5: `len(cells) <= max(field_i, label_i)` (1 cell <= 1). Synthetic --
    # this shape (a stray single-cell placeholder row under a full 6-column header) is
    # a defensive case the real corpus has not been observed to produce; the code path
    # exists in the source, so it is characterized here rather than left silently
    # unverified.
    v26_body = (
        "| Field | Display Label | Source | Format | Empty Behavior | Cross-ref |\n"
        "|---|---|---|---|---|---|\n"
        "| N/A |"
    )
    out = reshape_data_inventory(v26_body)
    assert out.splitlines()[-1] == "| N/A |"  # malformed row emitted byte-for-byte


# --------------------------------------------------------------------------- #
# B6's four guard conditions, isolated -- each is synthetic (single-purpose branch
# probes for the `if cross_i is not None and field_val and field_val != label_val
# and field_val != "-":` condition), not a real-corpus shape.
# --------------------------------------------------------------------------- #
def test_reshape_no_binding_annotation_when_no_crossref_column():
    # cross_i is None -- the table has no Cross-ref column to append onto at all.
    v26_body = "| Field | Display Label | Source |\n|---|---|---|\n| `x` | Label X | src |"
    out = reshape_data_inventory(v26_body)
    assert out == "| Display Label | Source |\n|---------------|--------|\n| Label X | src |"
    assert "binding" not in out


def test_reshape_no_binding_annotation_when_field_equals_label():
    # field_val == label_val -- nothing was actually dropped, so no annotation is added.
    v26_body = (
        "| Field | Display Label | Source | Format | Empty Behavior | Cross-ref |\n"
        "|---|---|---|---|---|---|\n"
        "| Same | Same | src | fmt | eb | N/A |"
    )
    out = reshape_data_inventory(v26_body)
    assert out.splitlines()[-1] == "| Same | src | fmt | eb | N/A |"
    assert "binding" not in out


def test_reshape_no_binding_annotation_when_field_is_dash_placeholder():
    # field_val == "-" -- the literal placeholder is never worth preserving.
    v26_body = (
        "| Field | Display Label | Source | Format | Empty Behavior | Cross-ref |\n"
        "|---|---|---|---|---|---|\n"
        "| - | Label | src | fmt | eb | N/A |"
    )
    out = reshape_data_inventory(v26_body)
    assert out.splitlines()[-1] == "| Label | src | fmt | eb | N/A |"
    assert "binding" not in out


def test_reshape_no_binding_annotation_when_field_is_blank():
    # field_val is falsy (empty after strip) -- nothing to preserve.
    v26_body = (
        "| Field | Display Label | Source | Format | Empty Behavior | Cross-ref |\n"
        "|---|---|---|---|---|---|\n"
        "|  | Label | src | fmt | eb | N/A |"
    )
    out = reshape_data_inventory(v26_body)
    assert out.splitlines()[-1] == "| Label | src | fmt | eb | N/A |"
    assert "binding" not in out


# --------------------------------------------------------------------------- #
# BUG-1 / BUG-2 -- FIXED (Phase 05 ADDENDUM). Originally characterized as pinned
# (buggy) behavior; Phase 05 absorbs this function's data-loss/fence-blindness into
# `## 3. UI Elements` and is REQUIRED to fix both defects first. These assertions are
# the INVERSION of the old characterization -- the old behavior (fenced lookalikes
# mistaken for the real table; trailing/interleaved non-table content silently
# dropped) was a BUG, not a contract worth preserving. See ADDENDUM in
# plans/260818-1332-rebuild-spec-human-readable-sot/phase-05-screen-sot-compose-lib.md.
# --------------------------------------------------------------------------- #
def test_reshape_is_fence_aware_and_leaves_fenced_table_lookalike_untouched():
    # Reaches the fixed B1 branch: the fence-aware scan finds ZERO real (non-fenced)
    # table rows (both pipe-lines live inside the ``` fence), so table_idx has < 2
    # entries and the ENTIRE body -- including the fenced lookalike and the trailing
    # prose -- is returned byte-for-byte unchanged. This is the fix for BUG-1: a fenced
    # code sample is never again mistaken for the real Data Inventory table.
    body = (
        "Some description.\n\n"
        "```\n"
        "| Field | Display Label |\n"
        "|-|-|\n"
        "| foo | bar |\n"
        "```\n\n"
        "More text after."
    )
    out = reshape_data_inventory(body)
    assert out == body
    assert "foo" in out
    assert "More text after." in out


def test_reshape_reshapes_real_table_while_leaving_a_separate_fenced_lookalike_alone():
    # Reaches the fixed B3/B6 branch (a REAL non-fenced table is present) together with
    # the fence-aware guard: a fenced lookalike elsewhere in the same body must not be
    # touched, and must not be mistaken for extra rows of the real table either.
    body = (
        "| Field | Display Label | Cross-ref |\n"
        "|---|---|---|\n"
        "| Label X | Label X | N/A |\n\n"
        "```\n"
        "| Field | Display Label |\n"
        "|-|-|\n"
        "| foo | bar |\n"
        "```\n"
    )
    out = reshape_data_inventory(body)
    assert out.splitlines()[0] == "| Display Label | Cross-ref |"
    assert "| Label X | N/A |" in out
    assert "| foo | bar |" in out  # fenced lookalike preserved verbatim, untouched
    assert "binding" not in out.split("```")[0]  # Field == Display Label, no annotation


def test_reshape_preserves_trailing_content_after_last_table_row():
    # Reaches the fixed B6 -> post-loop path: the fix for BUG-2. Reproduces the exact
    # data-loss shape the ADDENDUM cites (HTML comments + a researcher note trailing
    # the last data row) and asserts none of it is dropped.
    v26_body = (
        "| Field | Display Label | Source | Format | Empty Behavior | Cross-ref |\n"
        "|---|---|---|---|---|---|\n"
        "| Label X | Label X | src | fmt | eb | N/A |\n"
        "\n"
        "<!-- Cap: max 20 primary fields. Grouped as {field_1..N} for dense screens. -->\n"
        "<!-- Computed fields: Source: computed + derivation in trailing parenthetical. -->\n"
        "\n"
        "**Note:** the totals row is hidden for guest checkout — see SCR044."
    )
    out = reshape_data_inventory(v26_body)
    assert "<!-- Cap: max 20 primary fields. Grouped as {field_1..N} for dense screens. -->" in out
    assert "<!-- Computed fields: Source: computed + derivation in trailing parenthetical. -->" in out
    assert "**Note:** the totals row is hidden for guest checkout — see SCR044." in out
    # And the real reshape still happened -- this isn't just a no-op fallback.
    assert "| Label X | src | fmt | eb | N/A |" in out
    assert out.splitlines()[0] == "| Display Label | Source | Format | Empty Behavior | Cross-ref |"


def test_reshape_preserves_interleaved_content_between_table_rows():
    # Reaches the fixed B6 -> mid-loop path: a comment line SANDWICHED between two
    # data rows (not just before/after the whole table) must survive too -- the fix
    # generalizes past "only trailing content was lost."
    v26_body = (
        "| Field | Display Label | Cross-ref |\n"
        "|---|---|---|\n"
        "| Label A | Label A | N/A |\n"
        "<!-- interleaved note between rows -->\n"
        "| Label B | Label B | N/A |"
    )
    out = reshape_data_inventory(v26_body)
    assert "<!-- interleaved note between rows -->" in out
    assert "| Label A | N/A |" in out
    assert "| Label B | N/A |" in out
