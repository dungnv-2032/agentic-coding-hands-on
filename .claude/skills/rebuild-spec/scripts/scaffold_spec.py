#!/usr/bin/env python3
"""Spec scaffolder — emits a correct-by-construction greenfield spec tree.

Also the classification chokepoint: reads plans/<plan_dir>/spec/.intent-enum.json
and refuses (exit 2) unless the artifact is present and consistent with --mode.

Exit codes:
  0 — success
  1 — validation error (bad slug/args/collision/over-length/fcode+feature-names)
  2 — chokepoint refusal (missing/inconsistent .intent-enum.json, under-decomp,
      RP1.5a not approved) OR fs error (exists w/o --force)
"""
from __future__ import annotations
import argparse
import datetime as _dt
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _slug_lib import assert_under  # noqa: E402
from _spec_constants import (  # noqa: E402
    FUNC_CAPABILITIES_SKELETON,
    FUNC_DEPS_SKELETON,
    FUNC_EDGE_CASES_SKELETON,
    FUNC_RISKS_SKELETON,
    REQUIRED_APPENDIX_H3,
    REQUIRED_H2_FUNC,
    REQUIRED_H2_TECH_THREAD,
    REQUIRED_VERIF_H3,
)

# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

_DRAFT_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_DRAFT_SLUG_MAX = 64
_FCODE_RE = re.compile(r"^F\d{3}$")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def kebab(name: str) -> str:
    """Convert an arbitrary name to kebab-case draft slug segment.

    NFKD-folds accented Latin so VI/diacritic names transliterate instead of
    silently dropping (café -> cafe, Nâng cấp -> nang-cap). Names with no ASCII
    representation at all (pure CJK, e.g. 日本語機能) fold to '' — the caller
    must detect the empty result and surface a targeted error. [MED-2]
    """
    folded = unicodedata.normalize("NFKD", name)
    folded = folded.encode("ascii", "ignore").decode("ascii")
    lowered = folded.lower()
    result = _NON_ALNUM_RE.sub("-", lowered)
    result = result.strip("-")
    # Collapse consecutive hyphens
    result = re.sub(r"-{2,}", "-", result)
    return result


def is_valid_draft_slug(s: str) -> bool:
    """Draft slug: kebab-case, max 64 chars. Different from promoted SLUG_RE."""
    if len(s) > _DRAFT_SLUG_MAX:
        return False
    return bool(_DRAFT_SLUG_RE.match(s))


# ---------------------------------------------------------------------------
# Atomic write
# ---------------------------------------------------------------------------

def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Frontmatter rendering
# ---------------------------------------------------------------------------

def _render_frontmatter(*, status: str, authored_by: str, created: str,
                         lang: str, fcode: str | None) -> str:
    lines = [
        "---",
        f"status: {status}",
        f"authored_by: {authored_by}",
        f"created: {created}",
        f"lang: {lang}",
    ]
    if fcode:
        lines.append(f"fcode: {fcode}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _render_feature_list_frontmatter(*, status: str, authored_by: str,
                                      created: str) -> str:
    lines = [
        "---",
        f"status: {status}",
        f"authored_by: {authored_by}",
        f"created: {created}",
        "---",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Spec content renderers
# ---------------------------------------------------------------------------

def _render_technical_spec(slug: str, frontmatter: str, fcode: str | None) -> str:
    """Render a draft technical-spec.md skeleton (v27.7.0 — action-thread reshape).

    The validator requires a `# F###_Slug` heading even for drafts (structural
    rule, not relaxed for draft status). When fcode is known, use it; otherwise
    use the placeholder `F000_Placeholder` which is valid per FCODE_HEADING_RE.
    Placeholder-heavy by design (lowercase-prose curly braces, `None.`/`N/A`
    fallbacks — no ALL-CAPS `{TOKEN}` shape, so Universal.no_placeholder never
    fires) so a fresh draft passes validate_feature_spec.py's
    _check_technical_spec with no manual edits.

    § 2 Action Index ALWAYS carries the reserved `A0` cross-cutting row (D2/C2):
    measured on the real corpus, a feature with zero endpoints and zero DB-Impact
    rows (F016/F017/F029) still needs a non-empty index, or
    FeatureSpec.action_index_missing (critical) fires on a legitimate
    infrastructure-only feature. A matching `A1` row/block is scaffolded too so
    the index and the body it points at start in agreement.

    § 3's one `#### A1 · {action title}` skeleton renders NO live rung lines at
    all — the fixed rung order (wire-format-contract.md § 3: Who -> FE ->
    Request -> BE -> Rule -> Result -> Source) is shown only in an HTML comment.
    A rung stub with an empty/`N/A`/`None.` body would trip
    FeatureSpec.rung_empty_rendered (critical) the moment an author saves the
    file unedited; omitting every rung line entirely is the only scaffold shape
    that cannot trip it.
    """
    fcode_part = fcode if fcode else "F000"
    # Derive a CamelCase heading label from the draft slug
    label = "".join(w.capitalize() for w in slug.replace("-", "_").split("_")) or "Placeholder"
    heading = f"# {fcode_part}_{label}"
    sections = [frontmatter, heading, ""]
    for h2 in REQUIRED_H2_TECH_THREAD:
        sections.append(h2)
        if h2 == "## 1. Technical Overview":
            sections.append("")
            sections.append("{2-3 sentence narrative — populated once technical-spec.md's "
                             "source has been read.}")
        elif h2 == "## 2. Action Index":
            sections.append("")
            sections.append("| # | Action (handler) | Method · Path | Codes | Writes | Detail |")
            sections.append("|---|---|---|---|---|---|")
            sections.append(
                "| **A0** | *cross-cutting — belongs to no single action* | — | "
                "{no codes yet} | — | § 4.4 |"
            )
            sections.append(
                "| **A1** | `{Controller#method}` | `{METHOD /path}` | {no codes yet} | "
                "— *(read-only)* | § 3.1 |"
            )
        elif h2 == "## 3. Actions":
            sections.append("")
            # Bucket heading MUST carry a `CAP-NN` token: `capability_buckets_missing`
            # (re-homed to `## 3. Actions` in phase 03c) reads the wire-format
            # contract's `### 3.N CAP-NN — title` shape. A bare `### 3.1 {label}`
            # has no capability bucket by that definition and fires a critical on a
            # brand-new scaffold — a scaffold born failing trains authors to ignore
            # criticals.
            sections.append(f"### 3.1 CAP-01 — {label}")
            sections.append("")
            sections.append("#### A1 · {action title}")
            sections.append("`{METHOD /path}` → `{Controller#method}`")
            sections.append("`{FR-###}` · `{SCR###_Name}`")
            sections.append("")
            sections.append(
                "<!-- Rung order per wire-format-contract.md § 3 — include only the rungs "
                "that apply, in this order: Who, FE, Request, BE, Rule, Result, Source. An "
                "absent rung is OMITTED entirely, never rendered as N/A or None. (that shape "
                "trips rung_empty_rendered, a critical). Only the RELATIVE ORDER of whichever "
                "rungs you do include is checked (rung_order); presence of every rung is "
                "never required. Every rung except Source is rendered as a bold label, a "
                "middot, then the body; Source is the one exception — colon inside the bold, "
                "a single space, then a backticked path:line citation, no middot — see the "
                "contract for the exact form. -->"
            )
        elif h2 == "## 4. Shared Foundation":
            for h3 in REQUIRED_APPENDIX_H3:
                sections.append("")
                sections.append(h3)
                sections.append("")
                if h3 == "### 4.2 Data Model":
                    sections.append("#### Key Entities")
                    sections.append("")
                    sections.append("| Entity | Table | Key Columns | Purpose |")
                    sections.append("|--------|-------|-------------|---------|")
                    sections.append("")
                    sections.append("#### Polymorphic Behavior")
                    sections.append("")
                    sections.append("N/A — no discriminator fields in Key Entities.")
                else:
                    sections.append("None.")
            sections.append("")
            sections.append(
                "**Client behavior:** see behavior-logic.md, permissions.md, architecture.md"
            )
        elif h2 == "## 5. Verification & Technical Notes":
            for h3 in REQUIRED_VERIF_H3:
                sections.append("")
                sections.append(h3)
                sections.append("")
                sections.append("None.")
                if h3 == "### 5.4 Source References":
                    # v27.12.0 (A3 Data Flow companion, BEST-EFFORT — no dedicated
                    # enforcement, same discretion as screen-spec's Call Hierarchy,
                    # which this script does not scaffold at all). Placeholder-heavy
                    # body (curly braces) so a fresh draft never invents a reading
                    # order it did not observe; this is an H4 nested under 5.4, not a
                    # new top-level H2/H3 — the 5-H2 / REQUIRED_VERIF_H3 sequences
                    # test_scaffold_matches_template.py checks are unaffected.
                    sections.append("")
                    sections.append("#### Data Flow")
                    sections.append("")
                    sections.append("```text")
                    sections.append(
                        "{request/event payload -> handler transforms -> DB read/write -> "
                        "response shape}"
                    )
                    sections.append("```")
        sections.append("")

    # A3 (`## Source Walkthrough`) / B4 (`## DB Impact per Event`) RETIRED from a
    # fresh technical-spec.md scaffold (phase 08, self-sufficiency v27.8): both
    # duplicated content § 3's per-action rungs already carry (see the template's
    # own retirement note). This scaffolder now renders exactly
    # REQUIRED_H2_TECH_THREAD's 5 sections, nothing after — matching
    # `templates/technical-spec-template.md`'s own current shape
    # (`test_scaffold_matches_template.py`'s whole reason for existing: catch
    # scaffold/template drift, never paper over it).
    return "\n".join(sections)


def _render_functional_spec(frontmatter: str) -> str:
    """Render a draft functional-spec.md skeleton (v27.x — human-readable SOT, 13 sections).

    Replaces the retired _render_business_context / _render_screens /
    _render_edge_cases (business-context.md / screens.md / edge-cases.md are gone).
    Placeholder-heavy by design (curly braces, N/A fallbacks) so a fresh draft
    passes validate_feature_spec.py's _check_functional_spec with no manual edits:
    no dev-token/secret shapes, no invented FR/BR/DEC/SM codes (technical-spec.md's
    draft CCL is "None." — nothing to surface, nothing to orphan), § 3/§ 6/§ 13 use
    the literal N/A/None fallbacks, § 9 carries 3 placeholder rows to clear the
    UI-feature row-count threshold, and § 2/§ 11/§ 12 (net-new — Functional
    Capabilities / Risks & Known Issues / Dependencies) emit a header-row-only table
    per content-preservation-map.md F-04/F-05/F-06 — deriving actual rows is a
    researcher judgment call, not something this deterministic scaffold should guess.
    § 2 having 0 rows never trips func.capabilities_empty here because § 4 Requirements
    carries no real FR-### bullet yet (just the curly-brace placeholder below).
    """
    sections = [
        frontmatter,
        "**Priority**: {P0|P1|P2|P3}",
        "**Type**: {ui|background|mixed}",
        "",
    ]
    for h2 in REQUIRED_H2_FUNC:
        sections.append(h2)
        sections.append("")
        if h2 == "## 2. Functional Capabilities":
            sections.append(FUNC_CAPABILITIES_SKELETON.rstrip("\n"))
        elif h2 == "## 3. Open Decisions":
            sections.append("None — no unresolved domain confirmations.")
        elif h2 == "## 4. Requirements":
            sections.append(
                "{No FR-### declared yet — populate once technical-spec.md defines "
                "requirements.}"
            )
        elif h2 == "## 5. Business Rules":
            sections.append("{No BR-###/DEC-###/SM-### declared yet.}")
        elif h2 == "## 6. Screens":
            sections.append("N/A — background feature; no user-facing screens.")
        elif h2 == "## 7. User Stories":
            sections.append("{Populated once technical-spec.md declares US### stories.}")
        elif h2 == "## 8. Scenarios":
            sections.append("{Given/When/Then scenarios per US###.}")
        elif h2 == "## 9. Edge Cases":
            sections.append(FUNC_EDGE_CASES_SKELETON.rstrip("\n"))
        elif h2 == "## 10. Edge Behaviours to Verify":
            sections.append("{Populate after § 4 Requirements are defined.}")
        elif h2 == "## 11. Risks & Known Issues":
            sections.append(FUNC_RISKS_SKELETON.rstrip("\n"))
        elif h2 == "## 12. Dependencies":
            sections.append(FUNC_DEPS_SKELETON.rstrip("\n"))
        elif h2 == "## 13. Configuration":
            sections.append("N/A — no user-facing configuration constants for this feature.")
        sections.append("")
    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Chokepoint: .intent-enum.json validation
# ---------------------------------------------------------------------------

def _load_intent_enum(plan_dir: Path) -> dict:
    """Load and parse .intent-enum.json. Raises SystemExit(2) on any failure."""
    path = plan_dir / "spec" / ".intent-enum.json"
    if not path.exists():
        print(f"[CHOKEPOINT] missing: {path}", file=sys.stderr)
        print("exit 2: .intent-enum.json not found — run intent-enum step first", file=sys.stderr)
        sys.exit(2)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[CHOKEPOINT] garbled .intent-enum.json: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict):
        print("[CHOKEPOINT] .intent-enum.json must be a JSON object", file=sys.stderr)
        sys.exit(2)
    if "mode" not in data or "intents" not in data:
        print("[CHOKEPOINT] .intent-enum.json missing required keys: mode, intents", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data["intents"], list):
        print("[CHOKEPOINT] .intent-enum.json intents must be a list", file=sys.stderr)
        sys.exit(2)
    return data


def _enforce_chokepoint(plan_dir: Path, mode: str) -> None:
    """Enforce classification gate. Exits 2 on refusal."""
    data = _load_intent_enum(plan_dir)
    artifact_mode = data.get("mode", "")
    intents = data["intents"]
    justification = data.get("justification", "")
    n = len(intents)

    if artifact_mode != mode:
        print(
            f"[CHOKEPOINT] mode mismatch: --mode={mode} but .intent-enum.json mode={artifact_mode!r}",
            file=sys.stderr,
        )
        sys.exit(2)

    if mode == "single":
        if n > 1 and not justification:
            print(
                f"under-decomposition: {n} intents enumerated, mode=single, no justification",
                file=sys.stderr,
            )
            sys.exit(2)

    elif mode == "system":
        sentinel = plan_dir / ".rp-1.5a-pending"
        if sentinel.exists():
            print(
                "[CHOKEPOINT] RP1.5a not approved: sentinel plans/<plan_dir>/.rp-1.5a-pending is present",
                file=sys.stderr,
            )
            sys.exit(2)
        if n < 2:
            print(
                f"[CHOKEPOINT] system mode requires ≥2 intents; only {n} enumerated",
                file=sys.stderr,
            )
            sys.exit(2)


# ---------------------------------------------------------------------------
# Fcode clobber check (RT-10)
# ---------------------------------------------------------------------------

def _warn_fcode_clobber(project_root: Path, fcode: str) -> None:
    """Warn if fcode already referenced in .spec-promote-pending.json."""
    pending = project_root / "docs" / ".spec-promote-pending.json"
    if not pending.exists():
        return
    try:
        data = json.loads(pending.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if isinstance(data, dict):
        entries = data.get("pending", [])
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and entry.get("fcode") == fcode:
                    print(
                        f"[WARN] fcode {fcode} already referenced in docs/.spec-promote-pending.json "
                        "(documented limitation: no lock — proceeding)",
                        file=sys.stderr,
                    )
                    return


# ---------------------------------------------------------------------------
# Scaffold: single feature
# ---------------------------------------------------------------------------

def _scaffold_feature(
    spec_root: Path,
    slug: str,
    frontmatter: str,
    *,
    force: bool,
) -> list[Path]:
    """Scaffold 4 files + marker for one feature. Returns list of created paths."""
    feature_dir = spec_root / slug
    marker = feature_dir / ".scaffold-complete"

    # RT-4: skip-if-exists keyed on MARKER, not directory
    if marker.exists() and not force:
        return []

    # Path-traversal guard BEFORE any filesystem write (defense-in-depth even
    # if _scaffold_feature is called without the outer main() guard)
    assert_under(feature_dir, spec_root)

    feature_dir.mkdir(parents=True, exist_ok=True)

    # Extract fcode from frontmatter if present (parse the `fcode:` line)
    _fcode_fm = None
    for _line in frontmatter.splitlines():
        if _line.startswith("fcode:"):
            _fcode_fm = _line.split(":", 1)[1].strip()
            break

    files = {
        "technical-spec.md": _render_technical_spec(slug, frontmatter, _fcode_fm),
        "functional-spec.md": _render_functional_spec(frontmatter),
    }

    created: list[Path] = []
    for fname, content in files.items():
        fpath = feature_dir / fname
        assert_under(fpath, spec_root)
        # RT-4: re-scaffold only absent files when marker is missing
        if not fpath.exists() or force:
            _atomic_write_text(fpath, content)
            created.append(fpath)

    # Write marker LAST (after all 4 files land)
    _atomic_write_text(marker, "")
    created.append(marker)
    return created


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# RT-14: SYSTEM folder-count machine check
# ---------------------------------------------------------------------------

_FCODE_ROW_RE = re.compile(r"^\|\s*F\d{3}")


def check_folder_count(plan_dir: Path) -> int:
    """Compare feature folder count vs feature-list.md row count.

    Prints a one-line result to stdout.
    Returns 0 on match, 1 on mismatch, 2 on missing inputs.
    """
    spec_root = plan_dir / "spec"
    feature_list = spec_root / "feature-list.md"
    if not feature_list.exists():
        print(
            f"[ERROR] feature-list.md not found: {feature_list}",
            file=sys.stderr,
        )
        return 2

    # Count ONLY scaffolded feature dirs — those carrying the `.scaffold-complete`
    # marker the scaffolder writes last. Stray dirs (research/, flows/,
    # .review-archive/, …) must NOT inflate the count, or RT-14 reports a false
    # MISMATCH and blocks an otherwise-correct SYSTEM scaffold. [H1]
    folder_count = sum(
        1 for p in spec_root.iterdir()
        if p.is_dir() and (p / ".scaffold-complete").is_file()
    )

    try:
        rows = [
            line
            for line in feature_list.read_text(encoding="utf-8").splitlines()
            if _FCODE_ROW_RE.match(line)
        ]
    except OSError as exc:
        print(f"[ERROR] cannot read feature-list.md: {exc}", file=sys.stderr)
        return 2

    row_count = len(rows)
    if folder_count == row_count:
        print(f"OK folder-count={folder_count} matches feature-list rows={row_count}")
        return 0
    else:
        print(
            f"MISMATCH folders={folder_count} feature-list rows={row_count}",
            file=sys.stderr,
        )
        return 1


def main(argv: list[str]) -> int:  # noqa: C901
    p = argparse.ArgumentParser(description="Scaffold a greenfield spec tree")
    p.add_argument("--plan-dir", required=True)
    p.add_argument("--mode", required=True, choices=["single", "system"])
    p.add_argument("--lang", required=True)
    p.add_argument("--slug", default=None)
    p.add_argument("--feature-names", default=None)
    p.add_argument("--fcode", default=None)
    p.add_argument("--date", default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument(
        "--check-folder-count",
        action="store_true",
        help="[RT-14] Compare feature folder count vs feature-list.md rows. "
             "No files created. Exit 0 = match, 1 = mismatch, 2 = error.",
    )
    args = p.parse_args(argv)

    # RT-14: check-only mode — resolve plan-dir then delegate, skip all scaffold logic.
    if args.check_folder_count:
        if ".." in Path(args.plan_dir).parts:
            print("[ERROR] --plan-dir must not contain '..'", file=sys.stderr)
            return 1
        return check_folder_count(Path(args.plan_dir).resolve())

    # RT-3: path-traversal guard on --plan-dir
    if ".." in Path(args.plan_dir).parts:
        print("[ERROR] --plan-dir must not contain '..'", file=sys.stderr)
        return 1

    plan_dir = Path(args.plan_dir).resolve()
    spec_root = plan_dir / "spec"

    # RT-3: path-traversal guard on --slug
    if args.slug and ".." in args.slug:
        print("[ERROR] --slug must not contain '..'", file=sys.stderr)
        return 1

    # RT-1/RT-2: Chokepoint — FIRST substantive action after '..' rejection
    _enforce_chokepoint(plan_dir, args.mode)

    # Mode/arg coherence
    if args.mode == "single" and not args.slug:
        print("[ERROR] --mode single requires --slug", file=sys.stderr)
        return 1
    if args.mode == "system" and not args.feature_names:
        print("[ERROR] --mode system requires --feature-names", file=sys.stderr)
        return 1
    if args.fcode and args.feature_names:
        print("[ERROR] --fcode and --feature-names are mutually exclusive", file=sys.stderr)
        return 1
    if args.fcode:
        if args.mode != "single":
            print("[ERROR] --fcode requires --mode single", file=sys.stderr)
            return 1
        if not _FCODE_RE.match(args.fcode):
            print(f"[ERROR] --fcode must match ^F\\d{{3}}$, got: {args.fcode!r}", file=sys.stderr)
            return 1

    # Validate/derive date
    created_date = args.date or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")

    if args.mode == "single":
        slug = args.slug
        if len(slug) > _DRAFT_SLUG_MAX:
            print(
                f"[ERROR] --slug exceeds {_DRAFT_SLUG_MAX} characters: {slug!r}",
                file=sys.stderr,
            )
            return 1
        if not is_valid_draft_slug(slug):
            print(
                f"[ERROR] --slug is not valid kebab-case: {slug!r}",
                file=sys.stderr,
            )
            return 1

        # RT-10: fcode clobber check
        if args.fcode:
            _warn_fcode_clobber(plan_dir.parent.parent, args.fcode)

        frontmatter = _render_frontmatter(
            status="draft",
            authored_by="takumi",
            created=created_date,
            lang=args.lang,
            fcode=args.fcode,
        )

        if args.dry_run:
            feature_dir = spec_root / slug
            tree = [
                str(feature_dir / "technical-spec.md"),
                str(feature_dir / "functional-spec.md"),
                str(feature_dir / ".scaffold-complete"),
            ]
            print(json.dumps(tree))
            return 0

        # RT-3: assert spec_root boundary
        try:
            assert_under(spec_root / slug, spec_root)
        except ValueError as exc:
            print(f"[ERROR] path traversal detected: {exc}", file=sys.stderr)
            return 2

        created = _scaffold_feature(spec_root, slug, frontmatter, force=args.force)
        all_paths = [str(p) for p in created]
        print(json.dumps(all_paths))
        return 0

    else:  # system
        names = [n.strip() for n in args.feature_names.split(",") if n.strip()]
        if not names:
            print(
                "[ERROR] --feature-names contained no non-empty names",
                file=sys.stderr,
            )
            return 1

        # RT-9: derive slugs first, dedup check before any write
        slugs: list[str] = []
        slug_to_names: dict[str, list[str]] = {}
        for name in names:
            derived = kebab(name)
            if not derived:
                # Name has no ASCII representation (e.g. pure CJK) — slugs are
                # ASCII-only. Don't blame the user for kebab-case; tell them how
                # to proceed. [MED-2]
                print(
                    f"[ERROR] feature name {name!r} has no ASCII representation; "
                    f"slugs are ASCII-only — pass an explicit ASCII --slug "
                    f"(single mode) or rename the feature with Latin characters.",
                    file=sys.stderr,
                )
                return 1
            if len(derived) > _DRAFT_SLUG_MAX:
                print(
                    f"[ERROR] derived slug exceeds {_DRAFT_SLUG_MAX} characters for name {name!r}: {derived!r}",
                    file=sys.stderr,
                )
                return 1
            if not is_valid_draft_slug(derived):
                print(
                    f"[ERROR] derived slug is not valid kebab-case for name {name!r}: {derived!r}",
                    file=sys.stderr,
                )
                return 1
            slugs.append(derived)
            slug_to_names.setdefault(derived, []).append(name)

        collisions = {slug: names_list for slug, names_list in slug_to_names.items()
                      if len(names_list) > 1}
        if collisions:
            collision_detail = "; ".join(
                f"{slug!r} <- {names_list}" for slug, names_list in collisions.items()
            )
            print(f"[ERROR] slug collisions: {collision_detail}", file=sys.stderr)
            return 1

        if args.dry_run:
            tree: list[str] = [str(spec_root / "feature-list.md")]
            for slug in slugs:
                feature_dir = spec_root / slug
                tree += [
                    str(feature_dir / "technical-spec.md"),
                    str(feature_dir / "functional-spec.md"),
                    str(feature_dir / ".scaffold-complete"),
                ]
            print(json.dumps(tree))
            return 0

        # Write feature-list.md stub (no lang, no fcode) — ONLY when absent (or --force).
        # The decomposition researcher writes a richer feature-list.md in Step 0a (BEFORE the
        # scaffolder runs in the RP1.5a APPROVED branch); clobbering it here would destroy the
        # confirmed feature breakdown and trip a false RT-14 folder-count MISMATCH (rows=0).
        fl_path = spec_root / "feature-list.md"
        assert_under(fl_path, spec_root)
        spec_root.mkdir(parents=True, exist_ok=True)

        all_paths: list[str] = []
        if not fl_path.exists() or args.force:
            fl_fm = _render_feature_list_frontmatter(
                status="draft",
                authored_by="takumi",
                created=created_date,
            )
            _atomic_write_text(fl_path, fl_fm)
            all_paths.append(str(fl_path))

        for slug in slugs:
            frontmatter = _render_frontmatter(
                status="draft",
                authored_by="takumi",
                created=created_date,
                lang=args.lang,
                fcode=None,
            )
            try:
                assert_under(spec_root / slug, spec_root)
            except ValueError as exc:
                print(f"[ERROR] path traversal detected: {exc}", file=sys.stderr)
                return 2
            created = _scaffold_feature(spec_root, slug, frontmatter, force=args.force)
            all_paths.extend(str(p) for p in created)

        print(json.dumps(all_paths))
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
