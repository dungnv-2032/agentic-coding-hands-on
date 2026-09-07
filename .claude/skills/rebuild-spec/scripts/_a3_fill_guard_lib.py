#!/usr/bin/env python3
"""_a3_fill_guard_lib.py -- section-scope + citation-honesty guard for the A3
researcher FILL pass over `screens/*/spec.md` (the `a3-screens` step,
references/pipeline-migrate.md).

RENAMED + RESCOPED from `_a3_b4_fill_guard_lib.py` (phase-09,
plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8, correction X3): that
module served BOTH the now-retired `a3-b4` step (features/*/technical-spec.md, A3+B4)
and `a3-screens` (screens/*/spec.md, A3 only). `a3-b4` retired because A3/B4 left
technical-spec.md's target shape in phase 08 -- but `a3-screens` still needs every
piece of this guard, so the module survives, A3-only. Deleting it outright (as the
sealed design first assumed) would have been SILENT: nothing in this codebase imports
`evaluate_fill`/`check_a3_citation_label`/`check_citation_targets`/`strip_sections` --
their only caller is the LLM researcher following `references/pipeline-migrate.md`'s
runbook -- so removing them would have raised no ImportError and broken no test while
the `a3-screens` fill pass quietly lost its guard.

The fill pass may touch ONLY the `## Source Walkthrough` (A3) section BODY of one
screen's `spec.md` -- nothing else, in any file (phase-00: "the dangerous failure is
not a bad A3 -- it is an LLM that rewrites the rest of a spec while filling one
section"). This module proves that boundary mechanically, plus guards the one failure
mode nothing downstream catches: a citation that reads correctly but points nowhere
real -- no other check in the pipeline flags a plausible-but-wrong `file:line`.
Whether a real citation SUPPORTS its claim is out of scope -- that is
`audit-doc-parity`'s job.

Section-body extraction reuses `validate_reading_guide_db_impact._section_body` (fence-
aware) and `_BRACE_RE` BY IMPORT -- same predicate the scaffold and the validator use;
a hand-rolled second walk here would repeat the double-fold this codebase already
shipped and fixed twice (phase-00, "Reusable machinery"). Every function here is a pure
read; the caller (the researcher-fill runbook, `references/pipeline-migrate.md`) owns
the pre-wave snapshot and the revert-on-violation write. Stdlib only.

Citation-EXISTENCE checking (`check_citation_targets`) lives in the sibling
`_a3_citation_target_lib.py` -- split out to keep this module under the repo's
200-line guidance; imported here so `evaluate_fill` still exposes one call.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _a3_citation_target_lib import check_citation_targets  # noqa: E402,F401
from _md_scan_lib import iter_lines_with_fence, mask_fenced  # noqa: E402
from _md_scan_lib import strip_comments as _strip_comments  # noqa: E402
from _spec_constants import A3_HEADING  # noqa: E402
from validate_reading_guide_db_impact import _BRACE_RE, _section_body  # noqa: E402

# A3-only (phase 09 dropped B4_HEADING along with the retired `a3-b4` step -- a
# screen spec never had a B4 heading to strip in the first place, so this is a
# name/scope correction, not a behavior change for `a3-screens`).
FILL_HEADINGS: tuple[str, ...] = (A3_HEADING,)

_HEADING_BOUNDARY_RE = re.compile(r"^#{1,2}[ \t]")
_SOURCE_LABEL_RE = re.compile(r"\*\*Source:\*\*")


def strip_sections(text: str, headings: tuple[str, ...] = FILL_HEADINGS) -> str:
    """`text` with the BODY of each heading in `headings` removed -- the heading lines
    themselves, and every byte outside those bodies, are preserved verbatim and in
    order. Fence-aware: a fenced `## X`-shaped line inside a stripped section can never
    be mistaken for the section's closing boundary (same walk `_section_body` uses)."""
    heading_pats = [re.compile(r"^" + re.escape(h) + r"[ \t]*$") for h in headings]
    out: list[str] = []
    stripping = False
    for _, line, in_fence in iter_lines_with_fence(text):
        if stripping:
            if in_fence or not _HEADING_BOUNDARY_RE.match(line):
                continue
            stripping = False
        out.append(line)
        if not in_fence and any(p.match(line) for p in heading_pats):
            stripping = True
    return "\n".join(out)


def check_scope(pre: str, post: str) -> list[str]:
    """Byte-for-byte equality of `pre` vs `post` OUTSIDE the A3 section body. A
    non-empty return means: revert `post` to `pre` -- the fill touched something it was
    never allowed to touch."""
    if strip_sections(pre) != strip_sections(post):
        return [
            "content outside '## Source Walkthrough' changed between the pre-fill "
            "and post-fill snapshot"
        ]
    return []


def check_a3_citation_label(text: str) -> list[str]:
    """A3 must cite with `**File:**`, never `**Source:**` -- the latter would pull this
    navigational list into `derive_confidence_report.py`'s citation-coverage
    denominator (feature-spec-researcher-contract.md ~L389-391)."""
    body = _section_body(text, A3_HEADING)
    if not body:
        return []
    if _SOURCE_LABEL_RE.search(mask_fenced(body)):
        return [f"{A3_HEADING!r} body contains a `**Source:**` citation label -- use "
                "`**File:**` instead (keeps A3 out of the A1 citation-coverage stat)"]
    return []


def check_no_leftover_placeholder(text: str) -> list[str]:
    """A3 may not still carry an unfilled `{...}` placeholder while the fill is
    reported successful (an HONEST leftover placeholder is a valid terminal state
    too -- `unfilled`, WARN `*.unmapped` -- this just stops it being mistaken for a
    completed fill)."""
    violations: list[str] = []
    for heading in FILL_HEADINGS:
        body = _section_body(text, heading)
        if body and _BRACE_RE.search(_strip_comments(body)):
            violations.append(f"{heading!r} still carries an unfilled `{{...}}` "
                               "placeholder")
    return violations


@dataclass(frozen=True)
class GuardResult:
    """One fill unit's guard verdict. `scope`/`citation_label`/`citation_target`
    violations are unacceptable outright (`must_revert`); a leftover placeholder alone
    isn't a scope breach -- it just can't be classified `filled`."""

    scope: list[str] = field(default_factory=list)
    citation_label: list[str] = field(default_factory=list)
    citation_target: list[str] = field(default_factory=list)
    placeholder: list[str] = field(default_factory=list)

    @property
    def must_revert(self) -> bool:
        return bool(self.scope or self.citation_label or self.citation_target)

    @property
    def all_violations(self) -> list[str]:
        return self.scope + self.citation_label + self.citation_target + self.placeholder


def evaluate_fill(pre: str, post: str, project_root: Path) -> GuardResult:
    """Run every check the wave gate needs after one researcher unit completes."""
    return GuardResult(
        scope=check_scope(pre, post),
        citation_label=check_a3_citation_label(post),
        citation_target=check_citation_targets(post, project_root),
        placeholder=check_no_leftover_placeholder(post),
    )


def is_already_filled(text: str) -> bool:
    """True when A3 carries real content -- present, and does not still hold a
    `{...}` placeholder. The ONE idempotency predicate: reads the artifact itself
    (imported `_section_body`/`_BRACE_RE`), never a marker file, so an interrupted
    mid-wave run resumes correctly."""
    return not check_no_leftover_placeholder(text) and all(
        _section_body(text, h) is not None for h in FILL_HEADINGS
    )
