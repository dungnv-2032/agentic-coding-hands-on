"""Shape detection for the v26 -> v27 audience-split migration (I6, M-AD6).

Stdlib only. See plans/260814-1106-rebuild-spec-audience-split/phase-06-migration-scripts.md.

Recognized shapes:
  - v26 4-file  -- technical-spec.md + business-context.md + screens.md + edge-cases.md
                   (functional-spec.md absent). Migrated by migrate_feature_audience_split.py.
  - v27 2-file  -- functional-spec.md + technical-spec.md, no v26 satellites. Already in
                   target shape; a no-op *only* once the per-feature sentinel confirms it
                   (see _audience_split_migrate_lib.py -- I1: a populated-but-unsentineled
                   dir is always partial, never skipped on file presence alone).
  - v27 hybrid  -- functional-spec.md + technical-spec.md + ALL THREE retired v26
                   satellites, still present together. This is the DOCUMENTED common case
                   of a default (no --reviewed) migration run (see
                   references/migration-audience-split.md, "What a reader should expect
                   from the default run") -- deletion of the satellites is gated on human
                   review and can be a long window. It is also what a corpus in that state
                   looks like if the per-feature sentinel is ever lost (e.g. an operator
                   deletes/gitignores docs/.migrate-v27/, a dot-directory sitting right
                   under docs/). Recognizing this shape makes the sentinel a
                   skip-optimization, not a correctness dependency: `migrate_feature`
                   validates the existing 2-file pair and, if it passes, re-writes the
                   sentinel WITHOUT ever calling `compose_fn` again -- re-composing would
                   re-derive functional-spec.md content from the satellites and could
                   silently overwrite reviewed edits. See migrate_feature_audience_split.py
                   for the routing.

Anything else -- a v25-era single spec.md, a partially hand-restructured tree (e.g. only
ONE of the three v26 satellites left alongside a v27 pair -- a genuinely ambiguous mix,
not the documented hybrid state), or an unrecognized mix of files -- is REFUSED
(UnrecognizedShapeError), never mangled. detect_shape()
only ever inspects file NAMES; it never opens file content (that is the hand-edit probe's job,
_audience_split_probe_lib.py) and it never derives a path component from anything it reads --
callers must independently validate any directory name against `_slug_lib.SLUG_RE` before this
module (or anything downstream) composes a path from it (M-SEC3).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _slug_lib import RETIRED_V26_SATELLITE_FILES  # noqa: E402

SHAPE_V27 = "v27_2file"
SHAPE_V26 = "v26_4file"
SHAPE_V27_HYBRID = "v27_hybrid"
SHAPE_V25 = "v25_single_spec"
SHAPE_UNKNOWN = "unknown"

FUNCTIONAL_SPEC = "functional-spec.md"
TECHNICAL_SPEC = "technical-spec.md"

# The three v26 satellite files functional-spec.md absorbs and retires (Phase 01).
# Single-sourced in _slug_lib.py (test_spec_constants_single_source.py guard (a));
# re-exported here under the name this module's callers already use.
V26_SATELLITE_FILES = RETIRED_V26_SATELLITE_FILES

V25_SPEC_FILE = "spec.md"

_SHAPE_DESCRIPTIONS = {
    SHAPE_V27: "v27 2-file layout (functional-spec.md + technical-spec.md)",
    SHAPE_V26: ("v26 4-file layout (technical-spec.md + "
                + ", ".join(V26_SATELLITE_FILES) + ")"),
    SHAPE_V27_HYBRID: ("v27 hybrid (functional-spec.md + technical-spec.md, satellites "
                       "retained: " + ", ".join(V26_SATELLITE_FILES) + ")"),
    SHAPE_V25: "v25-era single spec.md layout",
    SHAPE_UNKNOWN: "unrecognized or partially-restructured layout",
}


def describe_shape(shape: str) -> str:
    return _SHAPE_DESCRIPTIONS.get(shape, shape)


class UnrecognizedShapeError(Exception):
    """Raised when a feature dir is neither v26 4-file nor v27 2-file (I6/M-AD6).

    Names the detected shape and the required intermediate step -- the migration
    refuses to guess rather than best-effort-parsing an unknown tree.
    """

    def __init__(self, feature_dir: Path, shape: str, files: list[str]):
        self.feature_dir = feature_dir
        self.shape = shape
        self.files = files
        super().__init__(
            f"REFUSE {feature_dir}: detected {describe_shape(shape)} -- files present: "
            f"{sorted(files)}. Required intermediate step: hand-restructure this feature "
            f"dir into the recognized v26 4-file layout ({TECHNICAL_SPEC} + "
            f"{', '.join(V26_SATELLITE_FILES)}) before re-running this migration; "
            f"refusing to best-effort-parse an unrecognized tree."
        )


def detect_shape(feature_dir: Path) -> str:
    """Classify *feature_dir* by file NAMES only -- never raises, never reads content.

    The caller decides whether SHAPE_UNKNOWN / SHAPE_V25 is a hard refusal (I6).
    """
    if not feature_dir.is_dir():
        return SHAPE_UNKNOWN
    files = {p.name for p in feature_dir.iterdir() if p.is_file()}
    has_func = FUNCTIONAL_SPEC in files
    has_tech = TECHNICAL_SPEC in files
    has_all_satellites = all(f in files for f in V26_SATELLITE_FILES)
    has_any_satellite = any(f in files for f in V26_SATELLITE_FILES)
    has_spec_md = V25_SPEC_FILE in files

    if has_func and has_tech and not has_any_satellite and not has_spec_md:
        return SHAPE_V27
    if has_tech and has_all_satellites and not has_func and not has_spec_md:
        return SHAPE_V26
    # The documented common case of a default (no --reviewed) run: composition already
    # happened (both v27 files present) but deletion of the v26 satellites is gated on
    # human review and hasn't cleared yet -- ALL THREE satellites together, never a
    # partial subset. Deliberately narrower than "at least one satellite": a partial
    # 1-or-2-satellite leftover is a genuinely ambiguous hand-restructure mix (matches
    # neither the documented hybrid state nor any other recognized shape) and must stay
    # SHAPE_UNKNOWN rather than being guessed into hybrid -- widening this predicate
    # would swallow real corruption the refusal path exists to catch.
    if has_func and has_tech and has_all_satellites and not has_spec_md:
        return SHAPE_V27_HYBRID
    if has_spec_md and not has_func and not has_tech and not has_any_satellite:
        return SHAPE_V25
    return SHAPE_UNKNOWN
