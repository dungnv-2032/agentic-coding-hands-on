#!/usr/bin/env python3
"""_mirror_skew_detect_lib.py -- pure, read-only mirror skew detection (phase-06,
plans/260818-0758-rebuild-spec-post-migration-completion). Split out of
`_mirror_skew_lib.py` to keep that module (the registry step wiring) under the
repo's 200-line guidance -- a sibling extraction, not a new subsystem; every
public name here is re-exported by `_mirror_skew_lib` for a single import point.

Two facts measured in phase-00 (§ CORRECTION 3) shape this module entirely:

1. Translate never deletes (`_translation_sync_lib.discover_artifacts` enumerates
   the primary tree forward only) -- so a mirror's shape (v26 4-file vs v27
   2-file) can only be learned by inspecting the mirror directly, never inferred
   from the translate cursor (`translations[lang].translated_from_sha`) alone. On
   the real corpus that cursor already EQUALS the primary's `last_rebuild_sha`
   (translate ran successfully before the audience-split migration), so a
   cursor-only staleness check would report "in sync" for a mirror that is still
   plainly v26 on disk. `MirrorSkew.stale` is true on EITHER signal (shape
   mismatch OR cursor mismatch) -- never cursor alone.
2. Docs-root resolution NEVER calls `_lang_lib.resolve_docs_root` (it would target
   a nonexistent `docs/en/` on this corpus's at-root primary layout). Every mirror
   lives at `docs_root.parent / <raw lang key from state.translations>`, exactly
   as `_audience_split_cli_lib.mirror_refusal_reason` already resolves it.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_shape_lib import (  # noqa: E402
    SHAPE_V26, SHAPE_V27, SHAPE_V27_HYBRID, V26_SATELLITE_FILES, detect_shape,
)
from _translation_sync_lib import load_state, secondary_langs  # noqa: E402

__all__ = ["MirrorSkew", "detect_skew", "render_skew_lines", "count_hybrid_primary_dirs"]


@dataclass(frozen=True)
class MirrorSkew:
    """One secondary language's skew report against the primary. Every count is a
    fresh read of the mirror's `features/*/` dirs -- nothing here is cached or
    sentinel-derived."""

    lang: str
    dirs_total: int
    dirs_v26: int
    dirs_v27: int
    dirs_hybrid: int
    dirs_other: int
    satellite_files_present: int
    translated_from_sha: str | None
    primary_cursor_sha: str

    @property
    def stale(self) -> bool:
        """True iff this mirror still needs (re)translating. Shape wins over the
        cursor -- a mirror can carry a MATCHING translate cursor and still be
        plainly out of shape (the exact real-corpus condition CORRECTION 3
        measured: cursor equal, shape still v26).

        "In shape" means every dir is `SHAPE_V27` -- NOT merely "no v26 dirs left
        and no satellites left". Measured while proving the prune end-to-end on
        the real corpus: after pruning the three retired satellites from a mirror
        whose `functional-spec.md` was never translated, the dir holds only
        `technical-spec.md` -- `detect_shape` reads that as `SHAPE_UNKNOWN`
        (matches neither v26 nor v27), so `dirs_v26 == 0` and
        `satellite_files_present == 0` even though the mirror is nowhere near
        synced. Counting anything short of "every dir is v27" as stale closes
        that gap; it also subsumes the v26/satellite/hybrid signals, so they are
        redundant with this check but kept as their own fields for the `[INFO]`
        report's diagnostic detail."""
        if self.dirs_total > 0 and self.dirs_v27 != self.dirs_total:
            return True
        return self.translated_from_sha != self.primary_cursor_sha


def detect_skew(docs_root: Path) -> list[MirrorSkew]:
    """Read-only per-secondary-language skew report. Enumerates
    `state["translations"]` keys (never `resolve_docs_root`) and joins each raw
    key onto the CONTAINER directory that holds `.rebuild-state.json` -- which is
    `docs_root` itself, not `docs_root.parent`. Measured against the real corpus
    (phase-00): `docs/.rebuild-state.json` sits directly inside `docs_root`, and
    `docs/vi/`, `docs/jp/` are its CHILDREN (`docs_root / "vi"` exists;
    `docs_root.parent / "vi"` does not) -- the at-root primary layout CORRECTION 4
    describes has no separate container one level up. `mirror_refusal_reason`'s own
    `.parent` join is in a different reference frame: its argument is a CANDIDATE
    path that might itself already BE a mirror, so its `.parent` walks UP to find
    the shared container. Here `docs_root` is already the confirmed container (we
    just read its own state file), so mirrors are its direct children. Empty list,
    never a raise, when `.rebuild-state.json` is absent/malformed or carries no
    secondaries."""
    state = load_state(docs_root / ".rebuild-state.json")
    primary_cursor_sha = state.get("last_rebuild_sha") or ""
    translations = state.get("translations") or {}

    results: list[MirrorSkew] = []
    for lang in secondary_langs(state):
        mirror_root = docs_root / lang
        dirs_v26 = dirs_v27 = dirs_hybrid = dirs_other = 0
        satellites = 0
        features_root = mirror_root / "features"
        if features_root.is_dir():
            for fd in sorted(features_root.iterdir()):
                if not fd.is_dir():
                    continue
                shape = detect_shape(fd)
                if shape == SHAPE_V26:
                    dirs_v26 += 1
                elif shape == SHAPE_V27:
                    dirs_v27 += 1
                elif shape == SHAPE_V27_HYBRID:
                    dirs_hybrid += 1
                else:
                    dirs_other += 1
                satellites += sum(
                    1 for name in V26_SATELLITE_FILES if (fd / name).is_file()
                )
        entry = translations.get(lang) or {}
        results.append(MirrorSkew(
            lang=lang,
            dirs_total=dirs_v26 + dirs_v27 + dirs_hybrid + dirs_other,
            dirs_v26=dirs_v26, dirs_v27=dirs_v27,
            dirs_hybrid=dirs_hybrid, dirs_other=dirs_other,
            satellite_files_present=satellites,
            translated_from_sha=entry.get("translated_from_sha"),
            primary_cursor_sha=primary_cursor_sha,
        ))
    return results


def render_skew_lines(skews: list["MirrorSkew"]) -> list[str]:
    """One `[INFO]` line per registered secondary language -- the whole point is
    that vi/jp are named explicitly, never summarized away."""
    if not skews:
        return ["[INFO] mirror-skew: no secondary languages registered -- nothing to translate"]
    return [
        f"[INFO] mirror-skew lang={s.lang} dirs={s.dirs_total} v26={s.dirs_v26} "
        f"v27={s.dirs_v27} hybrid={s.dirs_hybrid} other={s.dirs_other} "
        f"satellites={s.satellite_files_present} "
        f"translated_from_sha={s.translated_from_sha!r} "
        f"primary_cursor_sha={s.primary_cursor_sha!r} stale={s.stale}"
        for s in skews
    ]


def count_hybrid_primary_dirs(docs_root: Path) -> int:
    """Primary `features/*/` dirs still `SHAPE_V27_HYBRID` -- the hard precondition
    (phase-00 CORRECTION 3) for the translate handoff. Read fresh every call,
    artifact-derived, never a sentinel."""
    root = docs_root / "features"
    if not root.is_dir():
        return 0
    return sum(
        1 for fd in sorted(root.iterdir())
        if fd.is_dir() and detect_shape(fd) == SHAPE_V27_HYBRID
    )
