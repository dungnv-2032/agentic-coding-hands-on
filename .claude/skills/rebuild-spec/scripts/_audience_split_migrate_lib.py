"""Staging, locking, sentinels, atomic swap, rollback and deletion for the v26 -> v27
audience-split migration (I1, I2, I5). Stdlib only.

DELIBERATE deviation from the 5 existing `migrate-*.py` scripts (CONSTRAINT 1, ADR-0004
pending in Phase 08): those mutate live files in place with no staging, no backup and no
dry-run -- safety rests on idempotency alone. The v15 in-place MOVE design lost real
customer data that way. This module never writes a live file before its staged,
validated replacement exists on disk, and never deletes an original before the
per-feature sentinel is written.

Mirrors `migrate_docs_layout.py`'s sentinel-write pattern (temp file + `os.replace`, the
LAST write of a successful step) and, for the lock file specifically, its POSIX
behaviour of leaving the lock file on disk after release. That is DELIBERATE, not an
oversight -- unlinking it reintroduces the same race the precedent's comment warns
about (a second process's `open()` racing the unlink between `flock` release and
`unlink`, then locking a now-orphaned inode nobody else can see). A later maintainer
must not "clean this up" to align with the other five in-place scripts.

ONE deviation from `migrate_docs_layout.py`'s own lock, by contrast, is intentional here
and is OURS, not a copy of anyone else's quirk: our `Lock` is NON-BLOCKING
(`LOCK_EX | LOCK_NB`) and raises `LockHeldError` immediately instead of blocking forever
on `flock`. A blocking lock cannot be given a deterministic unit test (I5) without a
second OS process; a non-blocking abort can, and "abort" is one of the two behaviours
I5 explicitly allows ("blocks/aborts, does not touch staging").
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_shape_lib import FUNCTIONAL_SPEC, TECHNICAL_SPEC  # noqa: E402

try:
    import fcntl  # POSIX advisory locks
    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - Windows
    _HAS_FCNTL = False

STAGING_DIRNAME = ".migrate-v27"
RUN_SENTINEL_NAME = ".migration-complete"
FEATURE_SENTINEL_NAME = ".migrated"
LOCK_NAME = ".migrate-feature-audience-split.lock"
BACKUP_SUFFIX = ".pre-swap-backup"


class LockHeldError(RuntimeError):
    """Raised when the run-level lock is already held by another invocation (I5)."""


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
def staging_root(docs_root: Path) -> Path:
    return docs_root / STAGING_DIRNAME


def staging_features_root(docs_root: Path) -> Path:
    return staging_root(docs_root) / "features"


def staging_feature_dir(docs_root: Path, slug: str) -> Path:
    return staging_features_root(docs_root) / slug


def staging_unit_dir(docs_root: Path, category: str, slug: str) -> Path:
    """Same staging-root convention as `staging_feature_dir`, generalized to a named
    category -- Mode B's singleton `system/business-rules` unit and Mode C's per-screen
    `screens/{slug}` units reuse the identical sentinel/backup/lock machinery this
    module already provides for features, rather than duplicating it."""
    return staging_root(docs_root) / category / slug


def run_sentinel_path(docs_root: Path) -> Path:
    return staging_root(docs_root) / RUN_SENTINEL_NAME


def feature_sentinel_path(feat_staging_dir: Path) -> Path:
    return feat_staging_dir / FEATURE_SENTINEL_NAME


def backup_path_for(feat_staging_dir: Path) -> Path:
    return feat_staging_dir / (TECHNICAL_SPEC + BACKUP_SUFFIX)


def has_run_sentinel(docs_root: Path) -> bool:
    return run_sentinel_path(docs_root).is_file()


def has_feature_sentinel(feat_staging_dir: Path) -> bool:
    return feature_sentinel_path(feat_staging_dir).is_file()


# --------------------------------------------------------------------------- #
# Locking (I5) -- one lock for the whole run, probe through sentinel write.
# --------------------------------------------------------------------------- #
class Lock:
    """Exclusive, NON-BLOCKING lock. A held lock raises LockHeldError immediately (I5)
    rather than blocking -- see module docstring for why this deviates from the
    (blocking) precedent on purpose. The POSIX lock FILE is deliberately left on disk
    after release (module docstring); only the Windows O_EXCL fallback unlinks."""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self._fh = None
        self._fd = None

    def __enter__(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        if _HAS_FCNTL:
            self._fh = open(self.lock_path, "w")
            try:
                fcntl.flock(self._fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                self._fh.close()
                self._fh = None
                raise LockHeldError(f"lock held: {self.lock_path}") from exc
        else:  # pragma: no cover - Windows
            try:
                self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except FileExistsError as exc:
                raise LockHeldError(f"lock held: {self.lock_path}") from exc
        return self

    def __exit__(self, *exc):
        if self._fh is not None:
            fcntl.flock(self._fh, fcntl.LOCK_UN)
            self._fh.close()
        if self._fd is not None:  # pragma: no cover - Windows
            os.close(self._fd)
            try:
                os.unlink(self.lock_path)
            except OSError:
                pass
        return False


# --------------------------------------------------------------------------- #
# Atomic write / copy helpers -- temp sibling + os.replace, mirroring
# migrate_docs_layout.py's _write_sentinel pattern.
# --------------------------------------------------------------------------- #
def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".aas-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, str(path))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _atomic_copy(src: Path, dst: Path) -> None:
    """Byte-identical copy of *src* to *dst* via temp sibling + os.replace (I2)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(dst.parent), prefix=".aas-bak-", suffix=".tmp")
    os.close(fd)
    try:
        shutil.copy2(str(src), tmp)
        os.replace(tmp, str(dst))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_feature_sentinel(feat_staging_dir: Path) -> None:
    _atomic_write_text(feature_sentinel_path(feat_staging_dir), "migrated\n")


SENTINEL_ABSENT = "absent"
SENTINEL_POISONED = "poisoned"
SENTINEL_VALID = "valid"

_SENTINEL_FORMAT_VERSION = "27"
_TALLY_NUMERIC_KEYS = ("units", "progress", "already", "inert", "failed", "clean", "clean_legacy")


def write_run_sentinel(docs_root: Path, tally: dict) -> None:
    """B2/B3 fix (phase-06): the run sentinel is now JSON carrying the tally the run
    produced (phase-00 decision 2), not a bare `"migrated\\n"` marker -- a later
    invocation can honor + print the recorded tally without re-deriving anything, and an
    unparseable/zero-progress sentinel self-heals as POISONED (`read_run_sentinel`)
    instead of locking the corpus out forever (the exact B2 defect this phase fixes).

    Callers must gate this on the tally's own `sentinel_worthy` (FAILED == 0 and
    INERT == 0) -- this function does not re-check that itself; the decision belongs at
    the call site where the tally is assembled, not buried in the writer."""
    payload = {
        "format_version": _SENTINEL_FORMAT_VERSION,
        "written_at": datetime.now(timezone.utc).isoformat(),
        **tally,
    }
    _atomic_write_text(run_sentinel_path(docs_root), json.dumps(payload, sort_keys=True, indent=2) + "\n")


def read_run_sentinel(docs_root: Path) -> tuple[str, dict]:
    """Returns `(state, data)`, `state` one of `SENTINEL_ABSENT` / `SENTINEL_POISONED` /
    `SENTINEL_VALID` (phase-00 decision 2). POISONED covers both the legacy plain-text
    sentinel (`"migrated\\n"`, unparseable as JSON) and a JSON sentinel recording
    `progress + already == 0` -- either way the caller re-runs with a WARN instead of
    honoring it; v27 has never shipped, so no real operator sentinel is lost by this,
    and no new flag is needed to escape it."""
    path = run_sentinel_path(docs_root)
    if not path.is_file():
        return SENTINEL_ABSENT, {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return SENTINEL_POISONED, {}
    if not isinstance(data, dict):
        return SENTINEL_POISONED, {}
    if not all(isinstance(data.get(k, 0), int) for k in _TALLY_NUMERIC_KEYS):
        return SENTINEL_POISONED, data
    if data.get("progress", 0) + data.get("already", 0) <= 0:
        return SENTINEL_POISONED, data
    return SENTINEL_VALID, data


# --------------------------------------------------------------------------- #
# Staging (I2) -- composed content + the pre-swap backup, never a live write.
# --------------------------------------------------------------------------- #
def stage_feature(feature_dir: Path, feat_staging_dir: Path, composed: dict[str, str]) -> None:
    """Write *composed* content to staging (never to the live feature dir) plus a
    byte-identical pre-swap backup of the CURRENT live technical-spec.md (I2), taken
    BEFORE any swap -- so --rollback always has something to restore from."""
    feat_staging_dir.mkdir(parents=True, exist_ok=True)
    live_tech = feature_dir / TECHNICAL_SPEC
    if live_tech.is_file():
        _atomic_copy(live_tech, backup_path_for(feat_staging_dir))
    _atomic_write_text(feat_staging_dir / FUNCTIONAL_SPEC, composed[FUNCTIONAL_SPEC])
    _atomic_write_text(feat_staging_dir / TECHNICAL_SPEC, composed[TECHNICAL_SPEC])


def validate_feature_dir(feature_dir: Path, project_root: Path) -> tuple[bool, list[dict]]:
    """Run validate_feature_spec.py's checks against *feature_dir* (staging OR live) --
    non-PASS is a hard stop; the caller must not swap or delete anything on failure."""
    import validate_feature_spec as _vfs  # local import: scripts/ dir already on sys.path

    result = _vfs.validate(plan_dir=feature_dir.parent, root=project_root, single=feature_dir)
    issues: list[dict] = []
    for entry in result["specs"].values():
        issues.extend(entry["issues"])
    critical = [i for i in issues if i.get("severity") == "critical"]
    return (not critical), issues


# --------------------------------------------------------------------------- #
# Atomic swap (I2) -- temp name in the REAL feature dir + os.replace.
# --------------------------------------------------------------------------- #
def _swap_one(staged_path: Path, live_path: Path) -> None:
    content = staged_path.read_text(encoding="utf-8")
    fd, tmp = tempfile.mkstemp(dir=str(live_path.parent), prefix=".aas-swap-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, str(live_path))  # atomic on POSIX
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def swap_functional_spec(feature_dir: Path, feat_staging_dir: Path) -> None:
    """Idempotent -- safe to redo on resume (I1): re-writing the same staged content
    into the live file is harmless."""
    _swap_one(feat_staging_dir / FUNCTIONAL_SPEC, feature_dir / FUNCTIONAL_SPEC)


def swap_technical_spec(feature_dir: Path, feat_staging_dir: Path) -> None:
    _swap_one(feat_staging_dir / TECHNICAL_SPEC, feature_dir / TECHNICAL_SPEC)


# --------------------------------------------------------------------------- #
# Rollback (I2) -- undo a PARTIAL (sentinel-absent) per-feature migration.
# --------------------------------------------------------------------------- #
def rollback_feature(feature_dir: Path, feat_staging_dir: Path) -> list[str]:
    """Restore technical-spec.md from the retained pre-swap backup and remove any
    functional-spec.md this migration injected (v26 dirs never had one). Refuses if
    the sentinel is present -- that migration is COMPLETE, not partial, and a completed
    migration is reversed through the customer's own VCS, not this tool."""
    if has_feature_sentinel(feat_staging_dir):
        raise RuntimeError(
            f"sentinel present ({feature_sentinel_path(feat_staging_dir)}) -- migration "
            f"COMPLETE, not partial. Refusing to roll back a finished migration."
        )
    restored: list[str] = []
    backup = backup_path_for(feat_staging_dir)
    if backup.is_file():
        _swap_one(backup, feature_dir / TECHNICAL_SPEC)
        restored.append(TECHNICAL_SPEC)
    injected_func = feature_dir / FUNCTIONAL_SPEC
    if injected_func.is_file() and backup.is_file():
        injected_func.unlink()
        restored.append(f"{FUNCTIONAL_SPEC} (removed)")
    return restored


# --------------------------------------------------------------------------- #
# Delete originals -- gated by the caller on sentinel-written AND verdict clean AND
# a --reviewed acknowledgement (step 4). Never follows a symlink (M-SEC3).
# --------------------------------------------------------------------------- #
def delete_originals(feature_dir: Path, filenames: tuple[str, ...]) -> list[str]:
    deleted: list[str] = []
    for name in filenames:
        p = feature_dir / name
        if p.is_symlink():
            continue  # never follow/delete through a symlink (M-SEC3)
        if p.is_file():
            p.unlink()
            deleted.append(name)
    return deleted


@dataclass
class MigrationOutcome:
    slug: str
    action: str
    exit_ok: bool
    message: str
    # "" | "clean" | "clean-legacy" (phase-06 CLEAN_LEGACY wiring) -- set by Mode A
    # (`migrate_feature`) from the probe verdict established BEFORE compose/swap, so the
    # run tally can report `authored_by=N marker=N` alongside progress/already/inert/
    # failed. Empty when the outcome never reached a probe (e.g. already-v27, rejected
    # slug, resumed-from-crash) -- optional and purely informational, never gates
    # anything.
    provenance: str = ""
