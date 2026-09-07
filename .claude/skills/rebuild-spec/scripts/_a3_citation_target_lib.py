#!/usr/bin/env python3
"""_a3_citation_target_lib.py -- citation-EXISTENCE check for the A3 fill guard
(the `a3-screens` step, references/pipeline-migrate.md).

RENAMED + RESCOPED from `_a3_b4_citation_target_lib.py` (phase-09,
plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8, correction X3): that
module checked BOTH A3 `**File:**` citations and B4 Source-cell citations, serving the
now-retired `a3-b4` step (features/*/technical-spec.md) as well as `a3-screens`
(screens/*/spec.md, A3 only). B4 never applied to a screen spec in the first place --
the B4 arm here served ONLY `a3-b4`. Sibling of `_a3_fill_guard_lib.py`, split out to
keep that module under the repo's 200-line guidance.

Answers exactly one question: does every `**File:**` citation in A3 name a path that
EXISTS under `project_root`, at a line (or line range) inside that file's actual
length? A citation that reads correctly but points nowhere real is a fabrication --
nothing else in the pipeline checks whether a `file:line` citation is real. Whether a
real citation SUPPORTS its claim is out of scope -- that is `audit-doc-parity`'s job.

Stdlib only. Pure reads -- writes nothing.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _md_scan_lib import mask_fenced  # noqa: E402
from _slug_lib import assert_under  # noqa: E402
from _spec_constants import A3_HEADING  # noqa: E402
from validate_reading_guide_db_impact import _section_body  # noqa: E402

_A3_FILE_CITE_RE = re.compile(r"\*\*File:\*\*\s*`?([^\s`|]+):(\d+)(?:-(\d+))?`?")


def _check_one_citation(project_root: Path, path_str: str, start_s: str,
                         end_s: str | None, label: str) -> list[str]:
    target = (project_root / path_str).resolve()
    try:
        assert_under(target, project_root)
    except ValueError:
        return [f"{label} {path_str!r} escapes project_root"]
    if not target.is_file():
        return [f"{label} points at a nonexistent file: {path_str}"]
    try:
        total_lines = sum(1 for _ in target.open(encoding="utf-8", errors="replace"))
    except OSError:
        return [f"{label} file unreadable: {path_str}"]
    start, end = int(start_s), int(end_s) if end_s else int(start_s)
    if start < 1 or end > total_lines or start > end:
        rng = f"{start_s}-{end_s}" if end_s else start_s
        return [f"{label} {path_str}:{rng} is out of range "
                f"(file has {total_lines} line(s))"]
    return []


def check_citation_targets(text: str, project_root: Path) -> list[str]:
    """Every `**File:**` citation in A3 must name a path that EXISTS under
    `project_root` with a line (or range) inside that file's actual length. A
    citation to a nonexistent file or an out-of-range line is a fabrication."""
    violations: list[str] = []
    a3_body = _section_body(text, A3_HEADING) or ""
    for path_str, start_s, end_s in _A3_FILE_CITE_RE.findall(mask_fenced(a3_body)):
        violations += _check_one_citation(project_root, path_str, start_s, end_s,
                                           f"{A3_HEADING!r} **File:** citation")
    return violations
