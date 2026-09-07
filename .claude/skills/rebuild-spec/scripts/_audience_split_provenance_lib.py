"""Legacy generator marker detection + per-file origin signal for the audience-split
hand-edit probe (phase-02 / B1). Split out of `_audience_split_probe_lib.py` to keep
that module under the repo's 200-line guidance -- see its docstring for the full
origin/integrity design.

This module answers ONLY "did a generator write this file" (origin). It never answers
"has anything changed since a generator wrote it" -- that is integrity, and stays in the
parent module. A marker match here is never sufficient on its own to call a file clean;
the parent module's integrity checks (`doc_lock: user`, foreign `authored_by:`, git
trail, working-tree diff) still gate every file regardless of origin.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _slug_lib import _read_frontmatter  # noqa: E402

CLEAN = "clean"
CLEAN_LEGACY = "clean-legacy"

# Internal-only signal: authored_by absent AND no recognized generator marker on this
# file. Never a caller-visible ProbeResult.verdict -- the parent module collapses a lone
# NO_ORIGIN file to HAND_EDITED, and only surfaces it at the unit level when EVERY file
# in the unit shares it.
NO_ORIGIN = "no-origin"

# Presence-only check -- deliberately independent of read_authored_by()'s resolved
# value (the parent module's TRAP note): `\S+` requires a non-empty value after the colon.
_AUTHORED_BY_PRESENT_RE = re.compile(r"^authored_by:\s*\S+", re.MULTILINE)

_MARKER_SCAN_LINES = 15

# Legacy generator markers (phase-02 marker census against the real sharetribe corpus).
# Matched against the first `_MARKER_SCAN_LINES` lines of a file -- position varies
# (line 4, 5 and 7 all occur on technical-spec.md), so never assume line 0.
_LEGACY_MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # technical-spec 66/66, screens/*/spec.md 182/182, business-rules.md 1/1. Strict
    # ISO date only -- do NOT accept the literal "migrated" v27's own output emits;
    # that path is covered by `authored_by:`, not this marker.
    ("generated-date", re.compile(r"^\*\*Generated\*\*:\s*\d{4}-\d{2}-\d{2}\s*$", re.MULTILINE)),
    # technical-spec 41/66. Corroborating only -- insufficient coverage alone.
    ("contract-header",
     re.compile(r"^<!--\s*Contract:\s*references/[\w./-]+-contract\.md\s*-->", re.MULTILINE)),
    # business-context 31/66, six wordings, 10 with an unterminated multi-line comment --
    # prefix-anchored deliberately so all six (and the unterminated form) still match.
    ("forbidden-tokens", re.compile(r"^<!--\s*FORBIDDEN TOKENS\b", re.MULTILINE)),
)


def _first_lines(path: Path, n: int = _MARKER_SCAN_LINES) -> str:
    try:
        lines = []
        with path.open(encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= n:
                    break
                lines.append(line)
        return "".join(lines)
    except (OSError, FileNotFoundError):
        return ""


def origin_of(path: Path) -> str | None:
    """Return the name of the first recognized legacy generator marker found in
    *path*'s first `_MARKER_SCAN_LINES` lines, or None if none match."""
    text = _first_lines(path)
    for name, pattern in _LEGACY_MARKERS:
        if pattern.search(text):
            return name
    return None


def origin_signal(path: Path) -> tuple[str, str]:
    """Caller must already have confirmed integrity passes for *path*. Returns
    `(CLEAN | CLEAN_LEGACY | NO_ORIGIN, provenance)`."""
    fm = _read_frontmatter(path)
    if _AUTHORED_BY_PRESENT_RE.search(fm):
        return CLEAN, "authored_by"
    marker = origin_of(path)
    if marker:
        return CLEAN_LEGACY, marker
    return NO_ORIGIN, ""
