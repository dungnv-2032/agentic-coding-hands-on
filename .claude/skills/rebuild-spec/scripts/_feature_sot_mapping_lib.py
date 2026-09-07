"""content-preservation-map.md § C: `## 2. Functional -> Technical Mapping` (T-02/
T-03/T-11/T-13/T-16) + `### 3.4 API & Endpoints` (T-16/T-26) row-building. Split out
of `_feature_sot_technical_lib.py` to hold the repo's 200-line guidance.

Mechanical [M] seed (content-preservation-map.md): FR rows from the old CCL
`### Requirements` table (T-03), DEC rows from Decision Logic blocks (T-11), one row
per US### carrying its priority rationale (T-13) and first cited endpoint (T-16) --
plus a completeness pass (still mechanical, just not curated) that adds one bare row
for any OTHER twin-declared FR/BR/DEC/SM/US code (most commonly BR-###/SM-### from
functional-spec.md § 5 Business Rules) so `FeatureSpec.mapping_table_missing`
(validate_feature_spec.py) never CRITICALs on a code the twin already states but
neither the Requirements table nor a Decision Logic block happens to cover. Deciding
whether a bare completeness row's content is actually RIGHT (as opposed to merely
present) stays [L] -- a researcher's job.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _action_thread_handler_lib import (  # noqa: E402
    is_job_class, parse_handler_cell, render_handler,
)
from _audience_split_md_sections_lib import split_sections  # noqa: E402
from _feature_sot_extract_lib import (  # noqa: E402
    ExtractedThreadPieces, ThreadEndpointRow, UsBlock,
)
from _screen_sot_table_lib import build_table, cell, col_index, split_around_first_table  # noqa: E402
from _spec_constants import REQUIRED_H2_FUNC  # noqa: E402

MAPPING_HEADER = ["Code", "Name", "Where it is implemented", "Technical notes", "Source"]
API_HEADER = ["Method", "Path", "Handler", "Linked Code", "Source"]
MAPPING_NA = "N/A — no FR/BR/US/AC codes found to map."
API_NA = "N/A — no HTTP/RPC surface; background feature only."

_FR_BULLET_RE = re.compile(r"^-\s+\*\*(FR-\d+)\*\*\s+(.*)$")
_CODE_TAIL_RE = re.compile(r"^-?\s*(.*?)\s*\((BR-\d+|DEC-\d+|SM-\d+)\)\s*$")
_US_HEADING_TITLE_RE = re.compile(r"^###\s+(US\S+)\s+—\s+(.*?)\s+\(Priority:")
_ENDPOINT_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/\S+)")
_DEC_CODE_TAG_RE = re.compile(r"\((DEC-\d+)\)\s*$")
_CODE_TAG_ANY_RE = re.compile(r"\((BR-\d+|SM-\d+|DEC-\d+)\)\s*$")
_SOURCE_LINE_RE = re.compile(r"^\*\*Source:\*\*\s*(.*)$", re.MULTILINE)
# Mirrors `validate_feature_spec._MAPPING_CODE_RE` exactly -- the completeness pass
# below must scan the SAME code universe the validator checks against, or drift
# reproduces the exact "seemed fine, CRITICALs on real corpora" gap this closes.
_TWIN_CODE_RE = re.compile(r"\b(?:FR|BR|DEC|SM)-\d{3}(?!\d)|\bUS\d{3}(?!\d)")


def _h2_named(suffix: str) -> str:
    """Resolve a `REQUIRED_H2_FUNC` heading by its title text, not a hardcoded `## N.`
    number -- numbers have already moved once this plan (target-shape-spec.md § 2)."""
    for heading in REQUIRED_H2_FUNC:
        if heading.endswith(suffix):
            return heading
    raise ValueError(f"REQUIRED_H2_FUNC has no section ending with {suffix!r}")


# Section-scoped homes for each code family (functional-spec-template.md): FR bullets
# live in § 4 Requirements; BR/DEC/SM trailing-tag lines live in § 5 Business Rules;
# US narrative headings live in § 7 User Stories.
_H2_REQUIREMENTS = _h2_named("Requirements")
_H2_BUSINESS_RULES = _h2_named("Business Rules")
_H2_USER_STORIES = _h2_named("User Stories")


def build_title_index(twin_functional_text: str) -> dict[str, str]:
    """Best-effort Code -> one-line-title lookup from the (already-composed) twin
    functional-spec.md -- target-shape-spec.md § 3's `Name` rule. A code the twin
    does not (yet) state falls back to whatever the technical side already knows.

    Section-scoped (fixes p14-migration-report.md § Risks item 1): `## 10. Edge
    Behaviours to Verify` shares its `- **FR-###** ...` bullet shape with `## 4.
    Requirements`, and an unscoped scan let the later § 10 match overwrite § 4's real
    title (last-wins). Each regex below only sees the section that owns that code
    family, first-wins within it, so a same-shaped bullet elsewhere can't leak in."""
    _, h2 = split_sections(twin_functional_text, level=2)
    index: dict[str, str] = {}

    for line in h2.get(_H2_REQUIREMENTS, "").splitlines():
        m = _FR_BULLET_RE.match(line.strip())
        if m and m.group(1) not in index:
            index[m.group(1)] = m.group(2).strip()

    for line in h2.get(_H2_BUSINESS_RULES, "").splitlines():
        m = _CODE_TAIL_RE.match(line.strip())
        if m and m.group(1).strip() and m.group(2) not in index:
            index[m.group(2)] = m.group(1).strip()

    for line in h2.get(_H2_USER_STORIES, "").splitlines():
        m = _US_HEADING_TITLE_RE.match(line.strip())
        if m and m.group(1) not in index:
            index[m.group(1)] = m.group(2).strip()

    return index


def _requirements_rows(requirements_body: str) -> list[list[str]]:
    _, header, rows, _ = split_around_first_table(requirements_body)
    if header is None:
        return []
    header_cf = [h.casefold() for h in header]
    col = col_index(header_cf, "code", "description", "endpoint/handler")
    return [
        [cell(r, col, "code"), cell(r, col, "description"), cell(r, col, "endpoint/handler")]
        for r in rows if "code" in col
    ]


def _block_index(blocks: list[tuple[str, str]]) -> dict[str, tuple[str, str]]:
    """Code -> (title, body) for any BR-###/SM-###/DEC-### block, keyed by the
    trailing `(CODE)` tag on its own heading -- the completeness pass's lookup for
    "does technical-spec.md already know anything about this twin-declared code?"."""
    index: dict[str, tuple[str, str]] = {}
    for heading, body in blocks:
        tag = _CODE_TAG_ANY_RE.search(heading)
        if tag:
            index[tag.group(1)] = (heading[:tag.start()].strip(" #"), body)
    return index


def build_mapping_rows(
    requirements_body: str,
    dec_blocks: list[tuple[str, str]],
    br_blocks: list[tuple[str, str]],
    sm_blocks: list[tuple[str, str]],
    us_blocks: list[UsBlock],
    title_index: dict[str, str],
    twin_functional_text: str,
) -> list[list[str]]:
    rows: list[list[str]] = []
    seen_codes: set[str] = set()
    m = _SOURCE_LINE_RE.search(requirements_body)
    shared_source = m.group(1).strip() if m else "—"
    for code, description, endpoint in _requirements_rows(requirements_body):
        name = title_index.get(code) or description or "—"
        rows.append([code, name, endpoint or "—", "—", shared_source])
        seen_codes.add(code)

    for heading, body in dec_blocks:
        tag = _DEC_CODE_TAG_RE.search(heading)
        if not tag:
            continue
        code = tag.group(1)
        title = heading[:tag.start()].strip(" #")
        src = _SOURCE_LINE_RE.search(body)
        source = src.group(1).strip() if src else "—"
        rows.append([code, title_index.get(code) or title, "guard / render branch", "—", source])
        seen_codes.add(code)

    for us in us_blocks:
        why = us.fields.get("Why this priority", "").strip()
        notes = f"Priority rationale: {why}" if why else "—"
        req_fulfilled = us.fields.get("Requirements fulfilled", "")
        src = _SOURCE_LINE_RE.search(req_fulfilled)
        source = src.group(1).strip() if src else "—"
        endpoint_m = _ENDPOINT_RE.search(req_fulfilled)
        where = f"`{endpoint_m.group(0)}`" if endpoint_m else "—"
        name = title_index.get(us.code) or us.title
        rows.append([us.code, name, where, notes, source])
        seen_codes.add(us.code)

    # Completeness pass -- every OTHER code the twin declares (most commonly
    # BR-###/SM-### from functional-spec.md § 5) still gets a row, sourced from a
    # matching BR/SM block when technical-spec.md has one.
    block_index = {**_block_index(br_blocks), **_block_index(sm_blocks)}
    for code in sorted(set(_TWIN_CODE_RE.findall(twin_functional_text)) - seen_codes):
        title, body = block_index.get(code, ("", ""))
        src = _SOURCE_LINE_RE.search(body) if body else None
        source = src.group(1).strip() if src else "—"
        rows.append([code, title_index.get(code) or title or "—",
                     "—" if not body else "see § 4 capability bucket", "—", source])
    return rows


def build_mapping_table(rows: list[list[str]]) -> str:
    return build_table(MAPPING_HEADER, rows) if rows else MAPPING_NA


def build_api_endpoints(requirements_body: str, us_blocks: list[UsBlock]) -> str:
    """T-16/T-26: every `{METHOD} {PATH}` token cited in the old CCL Requirements
    table or a per-US `Requirements fulfilled` bullet, listed once as the endpoint
    surface. No v27.0 predecessor table -- seeded mechanically, completeness is [L]."""
    rows: list[list[str]] = []
    seen: set[tuple[str, str]] = set()

    def _add(method: str, path: str, code: str, source: str) -> None:
        key = (method, path)
        if key in seen:
            return
        seen.add(key)
        rows.append([method, path, "—", code, source])

    for code, _description, endpoint in _requirements_rows(requirements_body):
        for method, path in _ENDPOINT_RE.findall(endpoint):
            _add(method, path, code, "—")
    for us in us_blocks:
        req_fulfilled = us.fields.get("Requirements fulfilled", "")
        src = _SOURCE_LINE_RE.search(req_fulfilled)
        for method, path in _ENDPOINT_RE.findall(req_fulfilled):
            _add(method, path, us.code, src.group(1).strip() if src else "—")
    return build_table(API_HEADER, rows) if rows else API_NA


# ---------------------------------------------------------------------------
# rebuild-spec 27.7.0 (action-thread reshape, phase 05) -- `## 2. Action Index`
# row-building: D2's action->rule binding. An action's identity is its HANDLER
# (`Class#method`), never `METHOD PATH` -- see wire-format-contract.md § 2.
# ---------------------------------------------------------------------------

ACTION_INDEX_HEADER = ["#", "Action (handler)", "Method · Path", "Codes", "Writes", "Detail"]
# NOTE: matches this file's own `_TWIN_CODE_RE` family (US has no hyphen, unlike
# every other code kind) -- a mapping-table row's own Code cell is matched WHOLE
# (`^...$`), so the `(?!\d)`-vs-`\b` boundary hazard this repo has hit 7 times
# (regex-code-boundary-hazard) does not apply here, but the US-vs-hyphenated shape
# split still does: dropping the `US\d+` half silently excluded every US### row
# from the completeness pass (found via this composer's own token-set diff test).
_CODE_RE = re.compile(r"^(?:FR|BR|DEC|SM|ALG|INT)-\d+$|^US\d+[A-Za-z0-9_]*$")
_APPLIES_TO_RE = re.compile(
    r"\*\*Applies to:\*\*\s*(.*?)(?=\n\s*\n|\n\*\*[A-Za-z][^:*]*:\*\*|\Z)", re.DOTALL,
)
_CLASSMETHOD_RE = re.compile(r"\b([A-Z][A-Za-z0-9_:]*)#([a-zA-Z_][A-Za-z0-9_?!]*)")
_BARE_METHOD_RE = re.compile(r"#([a-zA-Z_][A-Za-z0-9_?!]*)")
_METHOD_PATH_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\b\s+(\S+)")
_BG_TAG_RE = re.compile(r"\(background\)", re.IGNORECASE)
_CLASS_NAME_RE = re.compile(r"\b([A-Z][A-Za-z0-9_]*(?:::[A-Z][A-Za-z0-9_]*)*)\b")


@dataclass
class ActionRecord:
    id: str
    handler: str
    handler_norm: str
    handler_class_norm: str
    method_norm: str
    http_method: str = ""
    path: str = ""
    is_background: bool = False
    codes: set[str] = field(default_factory=set)
    write_tables: list[str] = field(default_factory=list)
    write_reason: str = ""
    inferred_note: str = ""
    cap_id: str | None = None
    detail_ref: str = ""
    source_citations: list[str] = field(default_factory=list)
    write_notes: list[str] = field(default_factory=list)  # DB-Impact prose, one per joined row
    # Phase 05: `parse_handler_cell`'s non-handler remainder (e.g. `(stock,
    # SCR123)`), for `render_handler` to re-attach -- default-valued/appended
    # last per the `sm_blocks`/`alg_blocks` precedent (keyword construction safe).
    annotation: str = ""


def _class_basename(cls: str) -> str:
    return cls.rsplit("::", 1)[-1]


def _extract_class_name(text: str) -> str:
    """First CamelCase-shaped identifier in *text*, backtick-stripped. Best-effort:
    returns `""` when none found (e.g. a notification Target naming a mailer method,
    not a plain class)."""
    m = _CLASS_NAME_RE.search(text.replace("`", ""))
    return m.group(1) if m else ""


def _split_codes(text: str) -> list[str]:
    return [c.strip() for c in re.split(r"[,/]", text) if _CODE_RE.match(c.strip())]


def _normalize_path(p: str) -> str:
    p = p.strip("` ")
    p = re.sub(r"^\(/:locale\)", "", p)
    p = re.sub(r"^\.\.\.", "", p)
    return p.rstrip("/")


def _path_matches(action_path: str, short_path: str) -> bool:
    return bool(short_path) and bool(action_path) and action_path.endswith(short_path)


def extract_applies_to(body: str) -> str:
    m = _APPLIES_TO_RE.search(body)
    return " ".join(m.group(1).split()) if m else ""


def resolve_rule_owners(applies_to_text: str, actions: list[ActionRecord]) -> list[str]:
    """3-way resolution (merge blocker #2, wire-format-contract.md § 4.4): handler
    match, then path match, else unresolved (`[]`) -- NEVER a guess. Handler match
    includes a narrow class-only fallback (unique candidate only, e.g. a background
    job named by a DIFFERENT method than its Action Index entry, `ExportListingsJob#
    generate_csv_content` vs `#perform`) -- deliberately broader than a literal
    reading of "handler match", reported as a documented decision, not silently."""
    if not applies_to_text.strip():
        return []
    text = applies_to_text.replace("`", "")
    owners: dict[str, None] = {}
    for cls, meth in _CLASSMETHOD_RE.findall(text):
        norm = f"{_class_basename(cls).lower()}#{meth.lower()}"
        exact = [a for a in actions if a.handler_norm == norm]
        if len(exact) == 1:
            owners[exact[0].id] = None
            continue
        by_cls = [a for a in actions if a.handler_class_norm == _class_basename(cls).lower()]
        if len(by_cls) == 1:
            owners[by_cls[0].id] = None
    for meth in _BARE_METHOD_RE.findall(text):
        by_meth = [a for a in actions if a.method_norm == meth.lower()]
        if len(by_meth) == 1:
            owners[by_meth[0].id] = None
    if owners:
        return sorted(owners, key=lambda i: int(i[1:]))
    for a in actions:
        if a.http_method and a.http_method in text.upper() and _path_matches(a.path, text):
            owners[a.id] = None
    return sorted(owners, key=lambda i: int(i[1:]))


class _ActionBuilder:
    """Assigns contiguous `A<n>` ids in build order: § 3.4 endpoint rows first
    (D2 -- HTTP actions), then background jobs synthesized from § 3.6 Integration
    blocks (`**Type:** queue-job`/`background-job` naming a `**Target:**` class not
    already a known handler), then any `## DB Impact per Event` row that still
    doesn't join anywhere."""

    def __init__(self) -> None:
        self.actions: list[ActionRecord] = []
        self.by_handler: dict[str, ActionRecord] = {}
        self._next = 1

    def _new(
        self, handler: str, is_background: bool, http_method: str = "", path: str = "",
        norm_key: str | None = None,
    ) -> ActionRecord:
        """`norm_key=None` (the default, used by every real handler) derives
        handler_norm/handler_class_norm/method_norm from `handler.partition("#")`
        -- correct for a genuine `Class#method` string. `ensure_raw` passes an
        explicit `norm_key` instead: raw fallback text is opaque prose, not a real
        handler, and MUST NOT populate handler_class_norm/method_norm with
        anything `resolve_rule_owners`'s by-class/by-method fallback could treat
        as a candidate (see `ensure_raw`'s own docstring for the corpus regression
        this guards)."""
        if norm_key is not None:
            handler_norm, handler_class_norm, method_norm = norm_key, "", ""
        else:
            cls, _, meth = handler.partition("#")
            handler_norm = f"{_class_basename(cls).lower()}#{meth.lower()}"
            handler_class_norm, method_norm = _class_basename(cls).lower(), meth.lower()
        rec = ActionRecord(
            id=f"A{self._next}", handler=handler, handler_norm=handler_norm,
            handler_class_norm=handler_class_norm, method_norm=method_norm,
            http_method=http_method, path=path, is_background=is_background,
        )
        self._next += 1
        self.actions.append(rec)
        self.by_handler[rec.handler_norm] = rec
        return rec

    def from_endpoint(self, ep: ThreadEndpointRow) -> ActionRecord:
        # Phase 05: `parse_handler_cell` replaces the old `.strip("` ")` call,
        # which could not remove an INTERIOR backtick (an annotation trailing
        # the handler). `handler` is now always the clean first backticked span;
        # the annotation rides on `rec.annotation` for `render_handler` to
        # re-attach at both render sites.
        handler, annotation = parse_handler_cell(ep.handler)
        rec = self._new(handler, is_background=False, http_method=ep.method.strip("` "),
                         path=_normalize_path(ep.path))
        rec.annotation = annotation
        rec.codes |= set(_split_codes(ep.linked_codes))
        if ep.source.strip():
            rec.source_citations.append(ep.source.strip())
        if "[INFERRED]" in ep.source:
            rec.inferred_note = "[INFERRED]"
        return rec

    def ensure_background(self, cls: str) -> ActionRecord | None:
        if not cls:
            return None
        norm = f"{cls.lower()}#perform"
        return self.by_handler.get(norm) or self._new(f"{cls}#perform", is_background=True)

    def ensure_raw(self, raw_text: str) -> ActionRecord:
        """Fallback for a DB-Impact event that names neither a known handler nor a
        real job/service/mailer class (`is_job_class`) -- e.g. free prose like
        "Commission retry", or an HTTP-verb/English-word token the naive class-name
        regex mis-extracted (phase 04, defect 2). Keys on the raw text itself
        (`action_key_not_handler`, wire-format-contract.md § 2) via an explicit
        `raw:`-prefixed `norm_key`, for two independent reasons:

        1. Dedup: a plain `text.lower()` key would never hit the `by_handler` dict
           `_new` actually populates for every OTHER caller (real handlers store
           under `f"{cls}#{meth}"`), so two DB-Impact rows naming the identical
           raw event (real corpus shape: F002's "Scheduled cleanup" appears twice,
           against two different tables) would silently fork into two actions
           instead of merging their write_tables into one.
        2. Isolation from `resolve_rule_owners`: raw event prose routinely CONTAINS
           its own `#` (e.g. `` PATCH/PUT listings#update ``, copied verbatim from
           the DB-Impact cell) -- letting `_new`'s generic `handler.partition("#")`
           run on it would derive a handler_class_norm/method_norm from that
           substring (e.g. method_norm `"update"`), which can collide with a REAL
           action's method_norm and turn a previously-unique `resolve_rule_owners`
           bare-method match ambiguous (measured regression: F003's BR-007 lost
           its correct A6 binding this way before this norm_key fix). A raw
           fallback action is not a known handler, so it must never be a
           candidate for that resolver at all -- `norm_key=...` makes `_new` set
           handler_class_norm/method_norm to `""`, which cannot equal any
           non-empty class/method token `resolve_rule_owners` ever looks up.

        `is_background=False`: a raw event keyed on unparsed prose is not KNOWN to
        be background work -- only `(background)`-tagged events, an INT
        `queue-job` block, or a suffix-matching class earn that label (see
        `build_action_records`)."""
        text = raw_text.strip()
        key = f"raw:{text.lower()}"
        return self.by_handler.get(key) or self._new(text, is_background=False, norm_key=key)


def _parse_db_impact_rows(db_impact_body: str) -> list[tuple[str, str, str, str]]:
    """`(event, table, source, prose)` per data row -- `prose` renders one **Result**
    rung bullet, built from whatever columns the table actually has (corpus tables
    vary: some carry Columns/Operation/Value Derivation, some don't)."""
    _, header, rows, _ = split_around_first_table(db_impact_body)
    if not header:
        return []
    header_cf = [h.casefold() for h in header]
    col = col_index(header_cf, "event/endpoint", "table", "source", "columns", "operation",
                     "value derivation")
    out = []
    for r in rows:
        table_raw = cell(r, col, "table", "")
        table = table_raw.strip("` ")
        op = cell(r, col, "operation", "")
        cols = cell(r, col, "columns", "")
        deriv = cell(r, col, "value derivation", "")
        parts = [p for p in (op, f"`{table}`" if table else "", cols) if p and p != "—"]
        prose = " ".join(parts)
        if deriv and deriv != "—":
            prose = f"{prose} — {deriv}" if prose else deriv
        out.append((cell(r, col, "event/endpoint", ""), table, cell(r, col, "source", ""), prose))
    return out


def _resolve_db_event(event: str, actions: list[ActionRecord]) -> ActionRecord | None:
    has_bg = bool(_BG_TAG_RE.search(event))
    remainder = _BG_TAG_RE.sub(" ", event).replace("`", "")
    m = _CLASSMETHOD_RE.search(remainder)
    if m:
        norm = f"{_class_basename(m.group(1)).lower()}#{m.group(2).lower()}"
        match = next((a for a in actions if a.handler_norm == norm), None)
        if match:
            return match
    if has_bg:
        bg = [a for a in actions if a.is_background]
        if len(bg) == 1:
            return bg[0]
    pm = _METHOD_PATH_RE.search(remainder)
    if pm:
        method, short = pm.group(1), _normalize_path(pm.group(2))
        matches = [a for a in actions if a.http_method == method and _path_matches(a.path, short)]
        if len(matches) == 1:
            return matches[0]
    return None


def build_action_records(pieces: ExtractedThreadPieces) -> list[ActionRecord]:
    b = _ActionBuilder()
    for ep in pieces.endpoints:
        b.from_endpoint(ep)
    for blk in pieces.int_blocks:
        if blk.kind.strip().lower() in ("queue-job", "background-job", "job"):
            b.ensure_background(_extract_class_name(blk.target))
    for event, table, source, prose in _parse_db_impact_rows(pieces.db_impact_body):
        target = _resolve_db_event(event, b.actions)
        if target is None:
            cls = _extract_class_name(_BG_TAG_RE.sub(" ", event))
            # phase 04 (defect 2): `cls` alone used to be enough -- any capitalised
            # word in the prose (an HTTP verb, "Any", "Scheduled", ...) became a
            # fabricated `<Word>#perform` background action. `is_job_class` is the
            # measured gate (100% precision/recall on the real corpus, see
            # `_action_thread_handler_lib.py`); ONLY here on the fallback path --
            # the INT-block `**Type:** queue-job` call to `ensure_background`
            # above stays unguarded, it already has an explicit source
            # declaration (`SendWelcomeEmail` has no Job/Worker/Service/Mailer
            # suffix and would fail this gate).
            target = b.ensure_background(cls) if cls and is_job_class(cls) else b.ensure_raw(event)
        table = table.strip("` ")
        if table and table not in target.write_tables:
            target.write_tables.append(table)
        if prose:
            target.write_notes.append(prose)
        if source.strip() and source.strip() not in target.source_citations:
            target.source_citations.append(source.strip())
    for a in b.actions:
        if a.write_tables:
            continue
        if a.inferred_note:
            a.write_reason = "unreachable"
        elif a.http_method.upper() == "GET":
            a.write_reason = "read-only"
        else:
            a.write_reason = "no DB write observed"
    return b.actions


def assign_codes(
    pieces: ExtractedThreadPieces, actions: list[ActionRecord],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """`({code: owner_id}, {rule_code: full_owners_list})` for every FR/BR/DEC/SM/
    ALG/INT/US code declared anywhere in *pieces* -- `owner_id` is `"A0"` when
    unresolved/cross-cutting. A BR/DEC rule resolved to >=2 actions (bin 2) credits
    its code to the lowest-numbered owner only in the first dict (the wire
    contract's "exactly one row's Codes" completeness invariant); the second dict
    keeps the FULL owner list so `build_bin2_writeup` can render "Used in: A2, A7"
    (SM/ALG/INT never populate the second dict -- they have no capability-bucket
    home to render a bin-2/bin-3 write-up under; see the fallback loop below)."""
    owner: dict[str, str] = {}
    rule_owners: dict[str, list[str]] = {}
    for a in actions:
        for code in a.codes:
            # first-declared action wins when the source data itself double-claims
            # a code across two `### 3.4` rows (observed: FR-204 named in both the
            # `#update` and `#approve` rows' `Linked Code` cells).
            owner.setdefault(code, a.id)
    for bucket in pieces.capability_buckets:
        for rule in (*bucket.br_blocks, *bucket.dec_blocks):
            owners = resolve_rule_owners(extract_applies_to(rule.body), actions)
            rule_owners[rule.code] = owners
            owner[rule.code] = owners[0] if owners else "A0"
    for row in pieces.mapping_rows:
        # positional -- `pieces.mapping_rows` always comes from the old "## 2."
        # table, whose fixed column order is `MAPPING_HEADER` (this module's own
        # constant): Code, Name, Where it is implemented, Technical notes, Source.
        code = (row[0] if row else "").strip()
        if not code or code in owner or not _CODE_RE.match(code):
            continue
        where = row[2] if len(row) > 2 else ""
        notes = row[3] if len(row) > 3 else ""
        owners = resolve_rule_owners(f"{where} {notes}", actions)
        owner[code] = owners[0] if owners else "A0"
    # Fallback for codes that live OUTSIDE both the capability-bucket BR/DEC blocks
    # above and the § 2 mapping-table completeness rows: SM-###/ALG-### blocks in
    # § 3 System Design's non-capability subsections (3.3 State Management, 3.5
    # Algorithms), plus INT-### integration blocks (3.6) -- none of these carry a
    # `### 4.N` capability parent, and unlike BR/DEC they are never guaranteed a
    # § 2 completeness row either. Real-corpus defect this closes: F026_Transactional
    # EmailSettings's SM-001 had NEITHER a capability-bucket home NOR a § 2 mapping
    # row, so it was invisible to every prior pass and fired
    # `FeatureSpec.action_unclaimed`. Resolution is the SAME deterministic
    # `Applies to:`-only mechanism as every other code family here (never guessed);
    # measured on the full 43-feature corpus, 0 of the 62 SM/ALG/INT blocks carry an
    # `Applies to:` field, so this always lands on A0 today -- but it does so
    # EXPLICITLY, which is what makes the code claimed rather than merely absent.
    # Runs LAST and only fills a genuine gap (`code in owner: continue`), so a
    # feature whose § 2 mapping table already resolved this same code to a real
    # handler (e.g. F011's SM-001/SM-002, both resolved via their own mapping row's
    # "Where it is implemented" text) is never overridden.
    for block in (*pieces.sm_blocks, *pieces.alg_blocks, *pieces.int_blocks):
        if not block.code or block.code in owner:
            continue
        owners = resolve_rule_owners(extract_applies_to(block.body), actions)
        owner[block.code] = owners[0] if owners else "A0"
    for a in actions:
        a.codes |= {c for c, o in owner.items() if o == a.id}
    return owner, rule_owners


def build_bin2_writeup(pieces: ExtractedThreadPieces, rule_owners: dict[str, list[str]]) -> str:
    """§ 4.4 Bin 2: every BR/DEC block resolved to >=2 actions, verbatim body plus
    the `Used in: A2, A7` line the wire contract requires."""
    lines = ["#### Bin 2 — used by ≥2 named actions", ""]
    for bucket in pieces.capability_buckets:
        for rule in (*bucket.br_blocks, *bucket.dec_blocks):
            owners = rule_owners.get(rule.code, [])
            if len(owners) < 2:
                continue
            lines.append(f"**{rule.heading.lstrip('#').strip()}**")
            lines.append(f"Used in: {', '.join(f'**{o}**' for o in owners)}")
            lines.append("")
            lines.append(rule.body.strip())
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_action_index_table(
    actions: list[ActionRecord], a0_codes: list[str], endpoints_note: str = "",
) -> str:
    rows: list[list[str]] = [[
        "**A0**", "*cross-cutting — belongs to no single action*", "—",
        ", ".join(sorted(a0_codes)) or "—", "—", "§ 4.4",
    ]]
    for a in actions:
        # Phase 05: `render_handler` -- shared with `_context_lines` -- so the
        # § 2 cell and the § 3 context line never disagree on the rendering.
        name = render_handler(a.handler, a.annotation)
        name += " *(background, no FE)*" if a.is_background else ""
        if a.path:
            mp = f"`{a.http_method}` `{a.path}`"
        elif a.is_background:
            mp = "queue · `Delayed::Job`"
        else:
            mp = "—"
        writes = ", ".join(f"`{t}`" for t in a.write_tables) or f"— *({a.write_reason})*"
        detail = a.detail_ref or "§ 4.4"
        rows.append([f"**{a.id}**", name, mp, ", ".join(sorted(a.codes)) or "—", writes, detail])
    table = build_table(ACTION_INDEX_HEADER, rows)
    # `endpoints_note` is the old "### 3.4" section's own prose (e.g. "N/A -- no
    # HTTP/RPC surface; background feature only") on a feature with zero endpoint
    # ROWS -- absorbing the table into § 2 must not silently drop that explanation.
    return f"{endpoints_note}\n\n{table}" if endpoints_note else table


_FRONTEND_FILE_RE = re.compile(r"\.(haml|erb|js|jsx|tsx|coffee|vue)\b")


def build_be_fe_notes(
    pieces: ExtractedThreadPieces, owner: dict[str, str],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Content-preservation for the OLD `## 2. Functional -> Technical Mapping`
    table (retired by the new `## 2. Action Index`, plan.md's own problem
    statement): every row's Name/Where/Notes prose is folded into its resolved
    owner's **FE** or **BE** rung bullet list, keyed by *owner* (bin classification
    already decided). A code owned by `"A0"` is handled by the A0 write-up instead
    (`build_a0_writeup`), not here."""
    fe: dict[str, list[str]] = {}
    be: dict[str, list[str]] = {}
    for row in pieces.mapping_rows:
        code = (row[0] if row else "").strip()
        owner_id = owner.get(code)
        if not owner_id or owner_id == "A0":
            continue
        bullet = _mapping_row_bullet(row)
        where = row[2] if len(row) > 2 else ""
        notes = row[3] if len(row) > 3 else ""
        target = fe if _FRONTEND_FILE_RE.search(f"{where} {notes}") else be
        target.setdefault(owner_id, []).append(bullet)
    return fe, be


def _mapping_row_bullet(row: list[str]) -> str:
    """One bullet carrying an OLD `## 2.` row's full content -- Name, Where,
    Technical notes AND its own Source citation column, which a plain "Name —
    Where (Notes)" rendering was silently dropping (content-preservation gap found
    via the composer's own token-set diff test)."""
    code = row[0] if row else ""
    name = row[1] if len(row) > 1 else ""
    where = row[2] if len(row) > 2 else ""
    notes = row[3] if len(row) > 3 else ""
    source = row[4] if len(row) > 4 else ""
    bullet = f"**{code}** {name} — {where}" + (f" ({notes})" if notes and notes != "—" else "")
    if source and source != "—":
        bullet += f" [{source}]"
    return bullet


def build_a0_writeup(pieces: ExtractedThreadPieces, owner: dict[str, str]) -> str:
    """§ 4.4 Bin 3's `A0` entry: every code the completeness pass could not bind to
    a specific action, each carrying its full old-`## 2.` row content so nothing is
    lost, plus every genuinely-unresolved BR/DEC block's own body (merge blocker #2
    -- `[UNVERIFIED] carried from **Applies to:** — needs a researcher pass`,
    original text preserved verbatim)."""
    parts = ["#### Bin 3 — cross-cutting, belongs to no single action", "",
              "**A0 · cross-cutting** — codes with no single-action owner:"]
    by_code = {(row[0] if row else "").strip(): row for row in pieces.mapping_rows}
    for code in sorted(c for c, o in owner.items() if o == "A0"):
        row = by_code.get(code)
        if row and len(row) > 2:
            parts.append(f"- {_mapping_row_bullet(row)}")
        else:
            parts.append(f"- **{code}**")
    for bucket in pieces.capability_buckets:
        for rule in (*bucket.br_blocks, *bucket.dec_blocks):
            if owner.get(rule.code) != "A0":
                continue
            applies_to = extract_applies_to(rule.body)
            marker = (f"[UNVERIFIED] carried from **Applies to:** — needs a researcher pass "
                      f"(original: \"{applies_to}\")") if applies_to else \
                "[UNVERIFIED] no resolvable owner — needs a researcher pass"
            parts.append(f"\n**{rule.heading.lstrip('#').strip()}**\n\n{marker}\n\n{rule.body.strip()}")
    return "\n".join(parts)


# join_db_impact_rows / add_leading_action_column RETIRED (phase 08,
# self-sufficiency v27.8): both existed solely to render `## DB Impact per Event`'s
# OUTPUT table with a leading Action column in `compose_action_thread` -- B4 no
# longer leaves that composer as an output section (see
# `_feature_sot_technical_lib.py`'s own note). `_parse_db_impact_rows`/
# `_resolve_db_event`/`_extract_class_name`/`_BG_TAG_RE` all stay: they remain
# load-bearing INPUT parsing for `build_action_records`'s background-action
# synthesis below, which reads the OLD file's B4 body regardless of whether B4
# is rendered again.


def add_source_refs_action_column(body: str, actions: list[ActionRecord]) -> str:
    """Same leading `Action` column for `### 5.4 Source References`, whose rows are
    shared SYMBOLS (a model, a controller, a service) rather than events -- so the
    join key is different: which known handler CLASS name appears anywhere in the
    row's own text. Best-effort substring match, several actions may qualify per
    row (a controller backs every one of its own routes)."""
    prefix, header, rows, suffix = split_around_first_table(body)
    if not header:
        return body
    new_rows = []
    for r in rows:
        text = " ".join(r).lower()
        hits = sorted({a.id for a in actions if a.handler_class_norm and a.handler_class_norm in text},
                      key=lambda i: int(i[1:]))
        new_rows.append([", ".join(hits) or "—", *r])
    table_text = build_table(["Action", *header], new_rows)
    return "\n\n".join(p for p in (prefix, table_text, suffix) if p)
