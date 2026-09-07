"""Hand-edit probe for the v26 -> v27 audience-split migration (I3, C-SEC1, B1).

Fail-closed: any undeterminable signal resolves to HAND_EDITED, never CLEAN. Stdlib only.

Origin and integrity are different questions, checked at different granularities
(phase-00 CORRECTION 2 / phase-02):

- Integrity, per FILE (this module): does this file's content still match what was last
  committed, and has nothing overridden it (`doc_lock: user`, a foreign `authored_by:`)?
  Unchanged in spirit from the original design -- git-log is corroboration, never a
  bypass.
- Origin, per UNIT (`_audience_split_provenance_lib.py`): did a generator write at least
  one file in this unit? rebuild-spec's own generator has NEVER written `authored_by:`
  (only takumi's promote path does), so a v26 corpus it produced carries zero
  frontmatter anywhere. Measured across all 66 sharetribe feature dirs, `edge-cases.md`
  carries no generator marker on ANY of them, only `technical-spec.md` does
  (`**Generated**: DATE`, 66/66) -- a per-file origin rule would fail every such corpus
  by construction. So origin is decided once per unit: if ANY file carries a recognized
  marker, the unit's origin is established and its markerless siblings ride along; a
  unit where NO file carries one still fails closed to HAND_EDITED.

TRAP: `read_authored_by()` (`_slug_lib.py:57`) defaults to `"rebuild-spec"` when the
field is absent -- fail-OPEN for a delete decision. This module checks presence
(`_AUTHORED_BY_PRESENT_RE`) BEFORE ever calling `read_authored_by()`, so that default is
never silently consumed.

Origin is never relaxed on integrity: `doc_lock: user`, a foreign `authored_by:`, a
missing git trail, or a working-tree diff still force HAND_EDITED regardless of any
marker present -- a marker only answers "who generated this", never "is this unchanged".
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_provenance_lib import (  # noqa: E402
    _AUTHORED_BY_PRESENT_RE, CLEAN, CLEAN_LEGACY, NO_ORIGIN, origin_signal,
)
from _slug_lib import _read_frontmatter, read_authored_by  # noqa: E402

HAND_EDITED = "hand-edited"

_DOC_LOCK_USER_RE = re.compile(r"^doc_lock:\s*['\"]?user['\"]?\s*$", re.MULTILINE)

_GIT_TIMEOUT = 5


@dataclass(frozen=True)
class ProbeResult:
    verdict: str            # CLEAN | HAND_EDITED | CLEAN_LEGACY
    reason: str              # human-readable evidence, for --dry-run / logs
    doc_lock: bool = False    # True when `doc_lock: user` specifically forced HAND_EDITED (I4)
    provenance: str = ""      # which signal established origin: "authored_by" or a marker name


def _git_available() -> bool:
    return shutil.which("git") is not None


def _has_git_dir(project_root: Path) -> bool:
    try:
        r = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "--git-dir"],
            capture_output=True, text=True, timeout=_GIT_TIMEOUT, check=False,
        )
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _has_git_trail(path: Path, project_root: Path) -> bool:
    """True iff *path* has at least one commit (untracked/uncommitted -> False)."""
    try:
        r = subprocess.run(
            ["git", "-C", str(project_root), "log", "-1", "--format=%H", "--", str(path)],
            capture_output=True, text=True, timeout=_GIT_TIMEOUT, check=False,
        )
        return r.returncode == 0 and bool(r.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return False


def _has_uncommitted_changes(path: Path, project_root: Path) -> bool:
    """C2 fix: True iff the WORKING TREE content of *path* differs from HEAD (a
    hand-edit made after the last commit, never re-committed), OR the check itself is
    undeterminable (any git error) -- fail-closed like every other signal in this
    module."""
    try:
        r = subprocess.run(
            ["git", "-C", str(project_root), "diff", "--quiet", "HEAD", "--", str(path)],
            capture_output=True, text=True, timeout=_GIT_TIMEOUT, check=False,
        )
        if r.returncode not in (0, 1):
            return True  # undeterminable (e.g. git error) -> fail-closed
        return r.returncode == 1
    except (OSError, subprocess.SubprocessError):
        return True  # undeterminable -> fail-closed


def _integrity_result(path: Path, project_root: Path) -> ProbeResult | None:
    """Per-file integrity check, independent of origin (I3/I4, unchanged in spirit).
    Returns a HAND_EDITED ProbeResult on the first tripped signal, or None when every
    integrity check passes (origin is then decided separately by `origin_signal`)."""
    if not path.is_file():
        return ProbeResult(HAND_EDITED, f"{path} does not exist -- undeterminable")

    fm = _read_frontmatter(path)
    if _DOC_LOCK_USER_RE.search(fm):
        return ProbeResult(HAND_EDITED, "doc_lock: user", doc_lock=True)

    if _AUTHORED_BY_PRESENT_RE.search(fm):
        authored = read_authored_by(path)
        if authored != "rebuild-spec":
            return ProbeResult(HAND_EDITED, f"authored_by={authored!r} (not rebuild-spec)")

    # git-log is corroboration for both the authored_by and the marker path alike.
    if not _git_available():
        return ProbeResult(HAND_EDITED, "git binary unavailable -- undeterminable")
    if not _has_git_dir(project_root):
        return ProbeResult(HAND_EDITED, "no .git directory -- undeterminable")
    if not _has_git_trail(path, project_root):
        return ProbeResult(HAND_EDITED, "no git trail (untracked/no commits) -- undeterminable")
    if _has_uncommitted_changes(path, project_root):
        return ProbeResult(HAND_EDITED, "working tree differs from HEAD (hand-edited, uncommitted)")

    return None


def probe_file(path: Path, project_root: Path) -> ProbeResult:
    """Fail-closed hand-edit probe for a single file (I3). Integrity fails -> HAND_EDITED
    (first offending reason). Integrity passes: `authored_by: rebuild-spec` -> CLEAN; no
    `authored_by:` but a legacy marker found -> CLEAN_LEGACY; neither -> HAND_EDITED
    (fail-closed: nothing establishes who generated this file)."""
    integrity = _integrity_result(path, project_root)
    if integrity is not None:
        return integrity

    kind, provenance = origin_signal(path)
    if kind == CLEAN:
        return ProbeResult(CLEAN, "authored_by=rebuild-spec + clean git trail", provenance=provenance)
    if kind == CLEAN_LEGACY:
        return ProbeResult(
            CLEAN_LEGACY,
            f"authored_by absent, legacy generator marker found ({provenance})",
            provenance=provenance,
        )
    assert kind == NO_ORIGIN  # exhaustive: origin_signal has no fourth return value
    return ProbeResult(
        HAND_EDITED,
        "authored_by absent and no generator marker found (undeterminable, fail-closed)",
    )


def probe_feature(paths: list[Path], project_root: Path) -> ProbeResult:
    """Aggregate verdict across every file in one unit (feature dir, or any other
    multi-file grouping). Two passes (origin is per-unit, integrity stays per-file):

    1. Integrity pass over every file -- ANY failure makes the whole unit HAND_EDITED
       (I3/I4, first offending file's reason/doc_lock), since its content must never
       reach composition/the LLM pass.
    2. Origin pass -- every file markerless-and-authored_by-absent -> HAND_EDITED
       (fail-closed, no recognizable origin at all). At least one marker found ->
       CLEAN_LEGACY, markerless siblings ride along. Otherwise (authored_by present
       everywhere) -> CLEAN.
    """
    for p in paths:
        integrity = _integrity_result(p, project_root)
        if integrity is not None:
            return integrity

    legacy_evidence: str | None = None
    saw_authored_by = False
    for p in paths:
        kind, provenance = origin_signal(p)
        if kind == CLEAN_LEGACY:
            if legacy_evidence is None:
                legacy_evidence = f"{p.name} ({provenance})"
        elif kind == CLEAN:
            saw_authored_by = True

    if legacy_evidence is None and not saw_authored_by:
        return ProbeResult(
            HAND_EDITED,
            "no generator marker in unit (authored_by absent on every file, undeterminable, "
            "fail-closed)",
        )
    if legacy_evidence is not None:
        return ProbeResult(CLEAN_LEGACY, f"legacy generator marker found: {legacy_evidence}")
    return ProbeResult(CLEAN, "all files clean")
