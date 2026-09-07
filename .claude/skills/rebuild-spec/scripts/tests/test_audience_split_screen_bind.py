"""Tests for phase-05 (B4c): the SCR### resolution ladder --
`_audience_split_screen_bind_lib.py`. See
plans/260817-1420-rebuild-spec-v27-migrate-legacy-docs/phase-05-screen-binding-degradation.md.

Ladder: L0 whole-row inline SCR### code -> L1 exact normalized-name match against
generated/screen-list.md's Screen Index -> L2 unicode/trailing-suffix-folded match ->
L3 unresolved. Ordered, first-hit-wins, NO fuzzy/edit-distance matching.

T-numbers below track the phase file's own test matrix (T1-T8, T15-T17) plus the
real-corpus-derived regression that settles an ambiguity the phase file's prose left
open (see test_l2_never_strips_the_index_side -- "Access Denied" vs
"Access Denied (invite-only)").
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _audience_split_screen_bind_lib as bind_lib  # noqa: E402
import _nav_table_parse_lib as nav_lib  # noqa: E402

_SCREEN_INDEX = """# Screen List

## Screen Index

| Code | Name | Auth | Controller#Action | Route |
|------|------|------|--------------------|-------|
| SCR020_LoginPage | Login Page | pub | sessions#new | GET /login |
| SCR001_Homepage | Homepage / Search | pub | homepage#index | GET / |
| SCR028_AccessDenied | Access Denied (invite-only) | pub | community_memberships#access_denied | GET /community_memberships/access_denied |
| SCR065_Availability | Availability Calendar | auth | listings#edit | GET /listings/:id/edit |
| SCR122_ConversationDetail | Conversation Detail | auth | conversations#show | GET /:id/messages/:id |
| SCR212_Admin2ConversationDetail | Conversation Detail | admin | admin2/conversations#show | GET /admin/conversations/:id |
| SCR200_ComposeDM | Compose Direct Message | auth | messages#new | GET /messages/new |
"""


def _index() -> dict[str, str]:
    return nav_lib.index_screen_list(_SCREEN_INDEX)


# --------------------------------------------------------------------------- #
# T1/T2 -- L0: whole-row inline SCR### code wins, regardless of cell position
# --------------------------------------------------------------------------- #

def test_t1_l0_bare_code_in_name_cell_with_empty_index():
    code, rung = bind_lib.resolve_row(["Homepage / Search (SCR001)", "sees", "does"], {})
    assert (code, rung) == ("SCR001", "L0")


def test_t2_l0_code_in_third_cell_not_cell_indexed():
    code, rung = bind_lib.resolve_row(["Some Name", "prose", "see SCR001 for detail"], {})
    assert (code, rung) == ("SCR001", "L0")


def test_l0_uses_the_fixed_boundary_not_a_trailing_b():
    """Same boundary class as validate_feature_spec.py's SCR anchor (recurred 4+
    times in this repo): a slug-suffixed code must still resolve."""
    code, rung = bind_lib.resolve_row(["Login (SCR020_LoginPage)", "x", "y"], {})
    assert (code, rung) == ("SCR020", "L0")


# --------------------------------------------------------------------------- #
# T3 -- L1: exact normalized-name hit
# --------------------------------------------------------------------------- #

def test_t3_l1_exact_name_match_returns_bare_code():
    index = _index()
    code, rung = bind_lib.resolve_row(["Login Page", "sees", "does"], index)
    assert (code, rung) == ("SCR020", "L1")


# --------------------------------------------------------------------------- #
# T4-T6 -- L2: unicode + trailing-suffix folded match
# --------------------------------------------------------------------------- #

def test_t4_l2_strips_trailing_generic_parenthetical():
    index = _index()
    code, rung = bind_lib.resolve_row(["Availability Calendar (region)", "s", "d"], index)
    assert (code, rung) == ("SCR065", "L2")


def test_t5_l2_folds_curly_apostrophe_inside_stripped_parenthetical():
    index = _index()
    row = ["Compose Direct Message (accessed from recipient’s profile)", "s", "d"]
    code, rung = bind_lib.resolve_row(row, index)
    assert (code, rung) == ("SCR200", "L2")


def test_t6_l2_folds_em_dash_qualifier_suffix():
    index = _index()
    row = ["Conversation Detail — Message Thread region", "s", "d"]
    code, rung = bind_lib.resolve_row(row, index)
    # First-match-wins on the duplicated "Conversation Detail" name (SCR122 before
    # SCR212 in Screen Index source order).
    assert (code, rung) == ("SCR122", "L2")


# --------------------------------------------------------------------------- #
# T7 -- the anti-fuzzy guard: a genuinely different name must NEVER resolve
# --------------------------------------------------------------------------- #

def test_t7_homepage_topbar_does_not_bind_to_homepage_search():
    index = _index()
    code, rung = bind_lib.resolve_row(["Homepage / Topbar", "s", "d"], index)
    assert code is None
    assert rung == "L3"


# --------------------------------------------------------------------------- #
# T8 -- L3: absent from the index entirely
# --------------------------------------------------------------------------- #

def test_t8_absent_name_is_l3():
    index = _index()
    code, rung = bind_lib.resolve_row(["Access Denied", "not invite-only", "d"], index)
    assert code is None
    assert rung == "L3"


def test_l2_never_strips_the_index_side():
    """Settles a real-corpus ambiguity the phase file's prose left open: the
    Screen Index's `Access Denied (invite-only)` is a DIFFERENT screen from the
    generic banned-member `Access Denied` screen named in v26 screens.md (same
    literal text, different `Controller#Action`). If L2 stripped a trailing
    parenthetical off the INDEX side too, these two would collide -- a wrong
    binding, strictly worse than the honest L3 gap the phase's own
    '### Unbound Screens' worked example calls for on this exact name. So the
    trailing-suffix strip in `_fold` must apply ONLY to the row name being
    resolved, never to the Screen Index's own names."""
    index = _index()
    code, rung = bind_lib.resolve_row(["Access Denied", "s", "d"], index)
    assert code is None
    assert rung == "L3"


# --------------------------------------------------------------------------- #
# T15 -- build_index: missing/unparseable generated/screen-list.md never raises
# --------------------------------------------------------------------------- #

def test_t15_build_index_missing_file_returns_empty_dict(tmp_path):
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    assert bind_lib.build_index(docs_root) == {}


def test_t15_build_index_missing_generated_dir_entirely(tmp_path):
    assert bind_lib.build_index(tmp_path / "docs") == {}


def test_build_index_reads_real_screen_index(tmp_path):
    docs_root = tmp_path / "docs"
    (docs_root / "generated").mkdir(parents=True)
    (docs_root / "generated" / "screen-list.md").write_text(_SCREEN_INDEX, encoding="utf-8")
    index = bind_lib.build_index(docs_root)
    assert index[nav_lib.norm_name("Login Page")] == "SCR020_LoginPage"


# --------------------------------------------------------------------------- #
# T16 -- screen-list.md whose first pipe table is NOT the Screen Index
# --------------------------------------------------------------------------- #

def test_t16_first_table_is_not_screen_index_correct_table_used(tmp_path):
    text = (
        "# Screen List\n\n"
        "## Components\n\n"
        "| Component | Type | Purpose |\n|---|---|---|\n| Header | ui | nav |\n\n"
        "## Screen Index\n\n"
        "| Code | Name | Auth | Controller#Action | Route |\n"
        "|------|------|------|--------------------|-------|\n"
        "| SCR020_LoginPage | Login Page | pub | sessions#new | GET /login |\n"
    )
    docs_root = tmp_path / "docs"
    (docs_root / "generated").mkdir(parents=True)
    (docs_root / "generated" / "screen-list.md").write_text(text, encoding="utf-8")
    index = bind_lib.build_index(docs_root)
    code, rung = bind_lib.resolve_row(["Login Page", "s", "d"], index)
    assert (code, rung) == ("SCR020", "L1")


# --------------------------------------------------------------------------- #
# T17 -- duplicated Screen Index names are reported ambiguous, not disambiguated
# --------------------------------------------------------------------------- #

def test_t17_duplicate_names_reports_conversation_detail(tmp_path):
    docs_root = tmp_path / "docs"
    (docs_root / "generated").mkdir(parents=True)
    (docs_root / "generated" / "screen-list.md").write_text(_SCREEN_INDEX, encoding="utf-8")
    dupes = bind_lib.duplicate_index_names(docs_root)
    assert "conversation detail" in dupes
    assert "login page" not in dupes


def test_duplicate_names_missing_file_returns_empty_set(tmp_path):
    assert bind_lib.duplicate_index_names(tmp_path / "docs") == set()


# --------------------------------------------------------------------------- #
# Regex boundary regression -- the recurring \\b-vs-(?!\\d) class of bug
# --------------------------------------------------------------------------- #

def test_l0_regex_uses_fixed_anchor_not_trailing_b():
    src = (_SCRIPTS_DIR / "_audience_split_screen_bind_lib.py").read_text(encoding="utf-8")
    assert r"SCR\d{3}\b" not in src, "trailing \\b anchor reintroduced"
