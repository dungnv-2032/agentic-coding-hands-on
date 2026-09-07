"""Mode A -- SCR### resolution ladder for functional-spec.md § 5 Screens (phase-05,
B4c). v26 `screens.md` carries screen NAMES with no code column (pre-dates the v24
feature<->screen binding). This module joins each row against
`generated/screen-list.md`'s Screen Index by an ORDERED ladder -- L0 whole-row inline
code, L1 exact normalized-name match, L2 unicode/trailing-suffix-folded match, L3
unresolved -- first hit wins.

NO fuzzy/edit-distance matching, on purpose (phase-05's "no L4" decision): a wrong
SCR binding silently attaches a feature to the wrong screen, which is strictly worse
than an honest L3 gap.

L2 folds the trailing-suffix strip ONLY on the row name being resolved, never on the
Screen Index's own names -- settled against the real corpus, not assumed: v26
screens.md names a generic banned-member "Access Denied" screen, and the real Screen
Index separately carries `SCR028_AccessDenied | Access Denied (invite-only)` -- a
DIFFERENT screen (different `Controller#Action`) that merely shares the literal
prefix. Stripping the Index side's parenthetical would collide the two. Both sides
still get the same basic unicode/whitespace/case canonicalization -- only the
trailing-suffix strip is one-directional. See `test_l2_never_strips_the_index_side`
in tests/test_audience_split_screen_bind.py for the regression this guards.

Stdlib only.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _nav_table_parse_lib import _first_table_after, _split_row, index_screen_list, norm_name  # noqa: E402

# Leading \b only -- a trailing \b never matches "SCR001_Login" ("_" is a word char
# with no boundary after the digits). Same recurring boundary-anchor class as
# validate_feature_spec.py's SCR cell check; do not retype this from memory.
_SCR_ANYWHERE_RE = re.compile(r"\bSCR\d{3}(?!\d)")

# Trailing " - qualifier" / " — qualifier" / " – qualifier" (ASCII hyphen, em dash,
# en dash all accepted directly -- no need to pre-fold unicode first).
_TRAILING_QUALIFIER_RE = re.compile(r"\s+[-–—]\s+\S.*$")
# Trailing "(...)" with no nested parens, e.g. " (region)", " (Legacy)".
_TRAILING_PAREN_RE = re.compile(r"\s*\([^()]*\)\s*$")


def build_index(docs_root: Path) -> dict[str, str]:
    """Best-effort {normalized name: SCR###_Slug} from
    generated/screen-list.md's Screen Index. Missing/unparseable file -> {}
    (never raises) -- every row then falls to L0-or-L3, matching phase-05's
    "compose_mode_a derives docs_root itself, best-effort" seam constraint."""
    screen_list = docs_root / "generated" / "screen-list.md"
    try:
        text = screen_list.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    return index_screen_list(text)


def _basic_fold(name: str) -> str:
    """Canonicalization applied to BOTH sides for L2 comparison: NFC-normalize,
    fold curly apostrophe / en-dash / em-dash to ASCII, collapse whitespace,
    casefold. No trailing-suffix stripping here (see module docstring)."""
    folded = unicodedata.normalize("NFC", name or "")
    folded = folded.replace("’", "'")
    folded = re.sub(r"[–—]", "-", folded)
    return norm_name(folded)


def _strip_trailing_suffix(name: str) -> str:
    """L2's extra step, applied ONLY to the row name being resolved: remove at
    most one trailing ` - qualifier` (any dash form) and/or one trailing
    ` (parenthetical)`. Only ever strips TRAILING text -- never touches interior
    words -- so it cannot manufacture a match between two genuinely different
    names (the T7 anti-fuzzy guarantee)."""
    stripped = _TRAILING_QUALIFIER_RE.sub("", name or "")
    stripped = _TRAILING_PAREN_RE.sub("", stripped)
    return stripped


def _bare(code: str) -> str:
    """Emit the BARE SCR### (no `_NameSlug` suffix), matching the documented Mode A
    workaround (references/migration-audience-split.md § "Known validator
    workaround"): the descriptive slug already lives in the Screen Name column, and
    `validate_feature_screen_link.py` resolves cross-file by bare prefix anyway, so
    nothing is lost by dropping it here. Applied uniformly to every rung's output,
    not just L0 -- `index_screen_list` returns the full `SCR###_Slug` for L1/L2."""
    m = _SCR_ANYWHERE_RE.search(code)
    return m.group(0) if m else code


def resolve_row(cells: list[str], index: dict[str, str]) -> tuple[str | None, str]:
    """Resolve one Screen List row's SCR### binding. Returns (bare code or None,
    rung fired) where rung in {"L0", "L1", "L2", "L3"}. Ordered, first-hit-wins,
    no fuzzy matching."""
    m = _SCR_ANYWHERE_RE.search(" | ".join(cells))
    if m:
        return m.group(0), "L0"
    name = cells[0] if cells else ""
    key = norm_name(name)
    if key in index:
        return _bare(index[key]), "L1"
    folded_name = _basic_fold(_strip_trailing_suffix(name))
    if folded_name:
        for idx_key, code in index.items():
            if _basic_fold(idx_key) == folded_name:
                return _bare(code), "L2"
    return None, "L3"


def duplicate_index_names(docs_root: Path) -> set[str]:
    """Normalized names appearing MORE THAN ONCE in the raw Screen Index table
    (before `index_screen_list`'s first-match-wins collapse) -- used only to flag
    a resolved binding 'ambiguous' for the evidence tally (phase-05 measured 6
    duplicated names over 182 rows). Never used to change resolution: accept
    first-match-wins, no disambiguation logic. Missing/unparseable file -> set()."""
    screen_list = docs_root / "generated" / "screen-list.md"
    try:
        text = screen_list.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    table = _first_table_after(text, r"#+\s*Screen Index\b")
    if len(table) < 2:
        return set()
    header = [h.casefold() for h in _split_row(table[0])]
    name_idx = next((i for i, h in enumerate(header) if "name" in h), 1)
    seen: dict[str, int] = {}
    for raw in table[2:]:
        cells = _split_row(raw)
        if name_idx >= len(cells):
            continue
        name = cells[name_idx].strip()
        if not name or name.startswith("{"):
            continue
        key = norm_name(name)
        seen[key] = seen.get(key, 0) + 1
    return {k for k, n in seen.items() if n > 1}
