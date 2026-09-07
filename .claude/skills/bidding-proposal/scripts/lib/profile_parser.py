"""Profile markdown parser — converts project_content_{id}_{ts}.md into ProjectProfile.

Markdown structure:
  # Project Profile: {id}
  Generated: {ts}

  ## Section Heading
  ### Subsection Heading      (optional)
  free text / bullet list / numbered list / table / `Image: path`
  ...

Tolerant: unknown sections logged + skipped; missing sections leave defaults.
"""
from __future__ import annotations

import re
from typing import Optional

from lib.extra_slide_classifier import build_extra_slide_entry
from lib.markdown_primitives import (
    parse_image_ref as _parse_image_ref,
    parse_list as _parse_list,
    parse_prose as _parse_prose,
    parse_table as _parse_table,
    parse_tables as _parse_tables,
    parse_text as _parse_text,
    split_paragraphs as _split_paragraphs,
    split_subsections as _split_subsections,
    strip_inline_markup as _strip_inline_markup,
)
from lib.profile_schema import (
    AfterBlock,
    AgendaSection,
    AssumptionSection,
    BackgroundSection,
    BenefitSection,
    BusinessProcessSection,
    CoverSection,
    FeaturesSection,
    NFROverviewSection,
    NFRSection,
    ProjectProfile,
    ScheduleSection,
    ScreenFlowSection,
    TableSection,
    section_has_content,
    _SECTION_CONTENT_CHECKS,
)
from lib.section_aliases import heading_display, heading_variants, resolve_section_key

# Hiragana + katakana. Kana, not the CJK ideograph block, is what separates a
# Japanese document from a Chinese one and from an English one quoting a
# Japanese product name — 株式会社 alone appears in an English proposal's
# footer, kana does not.
_KANA = re.compile(r'[぀-ゟ゠-ヿ]')


def parse_profile(markdown: str) -> ProjectProfile:
    """Top-level: parse markdown text into a ProjectProfile.

    A `## heading` is resolved to a section key through `section_aliases`, which
    accepts both gen-md.py's English schema headings and the chapter titles a
    human-written proposal uses (`## 1. システムの概要 — System Overview`).

    A heading that names no section is not dropped. It is first tried as a
    CONTAINER: a proposal chapter whose own `###` subsections are the real
    sections (chapter 1 holds 背景・目的 and 機能一覧). If any subsection
    resolves, the chapter is consumed and its subsections become sections.
    Only a block that resolves neither way is classified into an extra-slide
    entry (`auto_extra_slides`), which gen-slide.py places via the generic
    layouts in `extra_slide_layouts.py`, anchored after the last known section.
    """
    mapping, markdown = split_front_matter(markdown)
    project_id, timestamp = _parse_header(markdown)
    profile = ProjectProfile.empty(project_id=project_id, timestamp=timestamp)

    profile.is_japanese_source = bool(_KANA.search(markdown))

    routes = {'mapping': 0, 'alias': 0, 'appendix': 0}
    last_known_key = None
    for heading, content in _split_sections(markdown):
        key, route = _resolve(heading, mapping)
        if key == CONTAINER_KEY:
            key = None
        if key and _apply_section(profile, key, content, heading):
            routes[route] += 1
            last_known_key = key
            continue
        consumed = _consume_container(profile, content, last_known_key, mapping, routes)
        if consumed is not _UNCONSUMED:
            last_known_key = consumed
            continue
        routes['appendix'] += 1
        _route_to_extra_slide(profile, heading, content, last_known_key)
    _report_coverage(routes)

    # AFTER the loop: an explicit `## Cover` section is written for this purpose
    # and must win, while the front matter is only being interpreted. Filling
    # first and letting the section overwrite lost whichever field the section
    # omitted — a `## Cover` carrying only a company erased the date.
    _fill_cover_from_preamble(profile, markdown)
    return profile


# Honorific that FOLLOWS the addressee's name, anchored at end of line.
#
# Anchored, not a substring test: `様` is a character inside 仕様 (specification),
# 多様 (diverse) and 様々 (various) — words an opening paragraph uses constantly.
# Matching it anywhere picked up the document's first sentence instead of its
# addressee, and stripping it with `str.replace` then deleted those characters
# from the middle of that sentence, putting the wreckage on the cover.
# 御中 comes first because it is unambiguous where 様 is not.
_HONORIFIC_SUFFIX = re.compile(r'\s*(御中|様)\s*$')

# Honorific that PRECEDES the name, as Vietnamese writes it. Longest form first
# so `Kính gửi Quý công ty X` does not strip down to `Quý công ty X`.
_HONORIFIC_PREFIX = re.compile(r'^\s*Kính gửi(?:\s+Quý công ty)?\s+', re.IGNORECASE)

# An English proposal has no honorific at all — it labels its addressee instead
# (`**Prepared for**: Evering`). The label is what carries the meaning, so it is
# matched as a field name, anchored at line start and requiring the colon: an
# unanchored `for` or `to` appears in every other sentence of a preamble.
#
# `Prepared for` must not be shortened to `for` in the alternation, or the
# neighbouring `**Prepared by**: Sun Asterisk Inc.` line would match too and put
# the VENDOR's name on the client's cover. Longest label first, for the same
# reason the Vietnamese prefix lists its long form first.
_ADDRESSEE_LABEL = re.compile(
    r'^\s*(?:Prepared for|Addressed to|Addressee|Client|To|For)\s*[:：]\s*',
    re.IGNORECASE,
)

# `2026.03.15` / `2026/03/15` / the ISO `2026-03-15`, and the JP business form
# `2026年3月15日`. ISO is what an English proposal writes and what every
# document generator emits by default; without it such a document silently kept
# the template's own placeholder date.
_DATE_PATTERNS = (
    re.compile(r'\b(\d{4})[./-](\d{1,2})[./-](\d{1,2})\b'),
    re.compile(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日'),
)
# Any four-digit year, used only to notice a date notation none of the patterns
# above understands — so an unsupported format is visible rather than silently
# falling back to the template's own placeholder date.
_YEAR_HINT = re.compile(r'\b(19|20)\d{2}\b')


def _fill_cover_from_preamble(profile: ProjectProfile, markdown: str) -> None:
    """Read the cover's client name and date off the document's own front matter.

    A proposal opens with its title, the addressee, and the date — above the
    first `##`, which is territory `_split_sections` discards. Without this, a
    document that plainly names its client on line 3 still shipped a cover
    reading `SVN Proposal Menu` / `○○株式会社　御中`, the template's placeholder.

    Runs AFTER the section loop and fills only what a `## Cover` section left
    empty: an explicit section was written for this purpose, while the front
    matter is only being interpreted.
    """
    preamble = re.split(r'^##\s', markdown, maxsplit=1, flags=re.MULTILINE)[0]
    company = profile.cover.company
    date = profile.cover.date
    if preamble.strip():
        company = company or _parse_addressee(preamble)
        date = date or parse_cover_date(preamble)
    if company or date:
        profile.cover = CoverSection(company=company, date=date)
        print(f'[profile-parser] Cover read from the document front matter: '
              f'company={company!r} date={date!r}')
    _warn_unfilled_cover(company, date)


def _warn_unfilled_cover(company: str, date: str) -> None:
    """Say plainly which cover field will ship the template's placeholder.

    Falling back is deliberate — a guessed client name is worse than a known
    placeholder — but the fallback used to be announced only by the ABSENCE of
    a line, which reads identically to a document that had no cover data to
    give. A deck went out headed `SVN Proposal Menu` / `○○株式会社　御中`
    because that silence was indistinguishable from success.
    """
    unfilled = [name for name, value in (('company', company), ('date', date)) if not value]
    if not unfilled:
        return
    print(f'[profile-parser] WARNING: cover {" and ".join(unfilled)} not found in the '
          f'document front matter — slide 1 will ship the TEMPLATE PLACEHOLDER '
          f'("SVN Proposal Menu" / "2025.04.04"). Pass '
          f'{" ".join("--cover-" + name for name in unfilled)} to gen-slide.py to set '
          f'it, or see references/cover-and-agenda.md for the addressee/date '
          f'notations the parser reads.')


def _parse_addressee(preamble: str) -> str:
    """Client name from the addressee line, honorific or label stripped as an affix.

    Three notations, one per language the source proposals are written in: the
    Japanese suffix honorific, the Vietnamese prefix honorific, and the English
    field label. Each is anchored to a line edge, so none of them can match the
    middle of a sentence.

    Returns '' when no line carries one. That is a real answer, not a failure:
    the cover then keeps the template's own wording, which is what
    `references/cover-and-agenda.md` documents as the fallback. A guessed name
    is worse than a known placeholder.
    """
    for line in preamble.splitlines():
        text = _strip_inline_markup(line.strip().lstrip('#').strip())
        if not text:
            continue
        for affix in (_HONORIFIC_SUFFIX, _HONORIFIC_PREFIX, _ADDRESSEE_LABEL):
            stripped = affix.sub('', text)
            if stripped != text:
                break
        else:
            continue
        stripped = stripped.strip(' 　:：')
        if stripped:
            return stripped
    return ''


def parse_cover_date(preamble: str) -> str:
    """The latest date in the front matter, normalized to `YYYY.MM.DD`.

    A revised proposal states both its original and its revision date; the cover
    carries the revision, so the latest one wins.

    Public because `gen-slide.py` runs a `--cover-date` value through it too, so
    a date typed on the command line reaches the cover in the same notation as
    one read out of the document.
    """
    matches = [m for pattern in _DATE_PATTERNS for m in pattern.findall(preamble)]
    if not matches:
        if _YEAR_HINT.search(preamble):
            print('[profile-parser] NOTE: the front matter names a year but no '
                  'date notation this parser reads (YYYY.MM.DD, YYYY/MM/DD, '
                  'YYYY-MM-DD, YYYY年M月D日) — the cover keeps the template\'s '
                  'own date')
        return ''
    year, month, day = max(matches, key=lambda m: (int(m[0]), int(m[1]), int(m[2])))
    return f'{year}.{int(month):02d}.{int(day):02d}'


def _apply_section(profile: ProjectProfile, key: str, content: str,
                   heading: str = '') -> bool:
    """Run the handler for *key* over *content*. True when it was applied.

    False when no handler exists OR the section is already filled. A second
    chapter resolving to a key that already holds content does NOT overwrite
    it: the first occupant wins and the caller routes this block to an appendix
    slide, so both reach the deck. Overwriting silently deleted the first
    chapter — `## 機能一覧` and `## 機能一覧表` both resolve to `features`, and
    the second one replaced the first one's whole table.
    """
    handler = globals().get(f'_handle_{key}')
    if not handler:
        return False
    if section_has_content(profile, key):
        print(f'[profile-parser] WARNING: a second block also resolves to '
              f'"{key}", which is already filled — keeping the first and '
              f'routing this one to an appendix slide instead of overwriting')
        return False
    handler(profile, content)
    if key not in profile.section_order:
        profile.section_order.append(key)
    # Recorded from the FIRST block that filled the section, matching the
    # first-occupant-wins rule above: the slide is titled after the chapter
    # whose content it actually carries.
    display = heading_display(heading)
    if display and key not in profile.section_headings:
        profile.section_headings[key] = display
    return True


# Sentinel: `_consume_container` returning this means the block held nothing it
# recognized, so the caller should fall through to the extra-slide route. A
# plain None can't say that — None is also a valid "no section seen yet" anchor.
_UNCONSUMED = object()


def _resolve(heading: str, mapping: dict[str, str]) -> tuple[Optional[str], str]:
    """Resolve *heading* to a section key, and say which route found it.

    The agent's mapping wins over the alias table: it was written by something
    that read THIS document, while the table only knows the wordings someone
    met before. Exact spelling first, then the same normalization the alias
    table uses, so a mapping key survives the numbering and gloss a heading
    carries.
    """
    if heading in mapping:
        return mapping[heading], 'mapping'
    for variant in heading_variants(heading):
        if variant in mapping:
            return mapping[variant], 'mapping'
    return resolve_section_key(heading), 'alias'


def _report_coverage(routes: dict[str, int]) -> None:
    """Say how many chapters found a template slide, and by which route.

    A document whose chapters mostly fall through to appendix slides still
    renders — it just renders as a generic deck wearing the SVN chrome, which
    is easy to miss when every individual WARNING looks routine. The ratio is
    the signal the per-heading warnings cannot give.
    """
    total = sum(routes.values())
    if not total:
        return
    placed = routes['mapping'] + routes['alias']
    print(f'[profile-parser] Sections resolved: {placed}/{total} chapters '
          f'({routes["mapping"]} mapping, {routes["alias"]} alias, '
          f'{routes["appendix"]} appendix)')
    if placed * 2 < total:
        print('[profile-parser] WARNING: fewer than half the chapters reached a '
              'template slide — the deck will be mostly appendix slides. Supply '
              'a front-matter `sections:` mapping (see '
              'references/supplied-document.md).')


def _consume_container(profile: ProjectProfile, content: str,
                       last_known_key: Optional[str],
                       mapping: Optional[dict] = None,
                       routes: Optional[dict] = None):
    """Try *content* as a chapter whose `###` subsections are the real sections.

    Returns the last section key applied, or `_UNCONSUMED` when no subsection
    resolved — in which case the caller routes the whole chapter to an extra
    slide, exactly as before.

    A subsection that resolves to nothing is routed to its own extra slide
    rather than discarded, so `### 1.3 UIデザイン・画面遷移` still reaches the
    deck instead of vanishing inside a chapter that was otherwise understood.
    """
    mapping = mapping or {}
    subs = _split_subsections(content)
    if not subs:
        return _UNCONSUMED
    resolved = []
    for sub in subs:
        key, route = _resolve(sub, mapping)
        # A subsection is never itself a container — nesting stops here.
        resolved.append((sub, None if key == CONTAINER_KEY else key, route))
    if not any(key for _, key, _ in resolved):
        return _UNCONSUMED

    for sub_heading, key, route in resolved:
        sub_content = subs[sub_heading]
        if key and _apply_section(profile, key, sub_content, sub_heading):
            if routes is not None:
                routes[route] += 1
            last_known_key = key
            continue
        if routes is not None:
            routes['appendix'] += 1
        _route_to_extra_slide(profile, sub_heading, sub_content, last_known_key)
    return last_known_key


def _route_to_extra_slide(profile: ProjectProfile, heading: str, content: str,
                          anchor: Optional[str]) -> Optional[str]:
    """Record one unrecognized block as an extra slide. Returns *anchor* unchanged."""
    entry = _route_unmatched_section(heading, content, anchor)
    profile.auto_extra_slides.append(entry)
    print(f'[profile-parser] WARNING: unrecognized section "{heading}" — '
          f'auto-routed to \'{entry["layout"]}\' extra-slide layout '
          f'(anchor: {anchor or "end of deck"}); review the '
          f'rendered slide before handing the deck over')
    return anchor


def _route_unmatched_section(heading: str, content: str, anchor_section: Optional[str]) -> dict:
    """Classify one unrecognized `## heading` block into an extra-slide entry.

    Parsing (table/list/subsection detection) stays here, reusing the same
    primitives the known-section handlers use; `build_extra_slide_entry` only
    picks a layout and shapes the already-parsed pieces.

    Tables are looked for whether or not the block has `###` subsections. They
    used to be skipped entirely when it did, which is exactly the case that
    matters: a chapter like `## 4. Sun* のスコープ` carries its whole
    responsibility matrix inside `### 4.1 Responsibility Split`, and skipping it
    flattened an 11-row table into one unreadable bullet. The largest table in
    the block wins — that is the one the chapter is about.
    """
    subs = _split_subsections(content)
    tables = _parse_tables(content)
    table_rows = max(tables, key=len) if tables else []
    if len(tables) > 1:
        print(f'[profile-parser] NOTE: "{heading}" holds {len(tables)} tables — '
              f'rendering the largest ({len(table_rows)} rows); the rest stay in '
              f'the markdown only')
    list_items = _parse_list(content) if not subs and not table_rows else []
    entry = build_extra_slide_entry(
        # The heading becomes the slide's visible title, so it gets the same
        # markup cleanup as body text — a raw `4\. Sun\* のスコープ` otherwise
        # ships its backslashes to the deck.
        _strip_inline_markup(heading), subsections=subs, table_rows=table_rows,
        list_items=list_items, raw_text=content,
    )
    entry['anchor_section'] = anchor_section
    return entry


# ---------------------------------------------------------------------------
# Header + section splitting
# ---------------------------------------------------------------------------

# Leading `---` … `---` block carrying the agent's heading → section mapping.
_FRONT_MATTER = re.compile(r'\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)', re.DOTALL)
# One `"heading": key` line inside it. Flat by design — see `_parse_front_matter`.
_MAPPING_LINE = re.compile(r'^\s{2,}(.+?)\s*:\s*(\S+)\s*$')

# The value that says "this chapter is a wrapper; its `###` subsections are the
# real sections" — the shape `_consume_container` already handles.
CONTAINER_KEY = 'container'


def split_front_matter(md: str) -> tuple[dict[str, str], str]:
    """Split a leading `---` block off *md*. Returns (section mapping, body).

    A supplied proposal names its chapters however its author chose, and no
    fixed alias table can cover every wording in every language. The agent that
    reads the document at Step 0.0 writes what it found into front matter:

        ---
        sections:
          "1. 本システムの全体像": container
          "1.1 現行業務の課題と狙い": project_background
        ---

    This is the ONLY thing that may be added to a supplied document — the
    chapters, their order, their heading levels and their wording stay exactly
    as written. The mapping is metadata ABOUT the document, never a rewrite OF
    it.

    The body is returned with the block removed, so `_parse_header` and
    `_fill_cover_from_preamble` — both of which read the text above the first
    `##` — never see it.
    """
    match = _FRONT_MATTER.match(md)
    if not match:
        return {}, md
    return _parse_front_matter(match.group(1)), md[match.end():]


def _parse_front_matter(block: str) -> dict[str, str]:
    """Read the `sections:` map out of a front-matter block.

    Deliberately a flat two-level reader rather than a YAML dependency: the
    shape is fixed and narrow, `scripts/requirements.txt` carries no yaml, and
    a real YAML loader would accept far more than this file should ever hold
    from a user-supplied document.
    """
    mapping: dict[str, str] = {}
    in_sections = False
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if re.match(r'^\S', line):
            in_sections = line.strip().rstrip(':').strip() == 'sections'
            continue
        if not in_sections:
            continue
        entry = _MAPPING_LINE.match(line)
        if entry:
            heading = entry.group(1).strip().strip('"\'')
            mapping[heading] = entry.group(2).strip().strip('"\'')
    return _validated_mapping(mapping)


def _validated_mapping(mapping: dict[str, str]) -> dict[str, str]:
    """Reject any value that is not a real section key.

    The value reaches `globals().get(f'_handle_{key}')`, so an unchecked one is
    an arbitrary-attribute lookup driven by a user-supplied document. It is
    also simply a typo the author wants to hear about: a silently ignored
    mapping line looks identical to a mapping that worked.
    """
    valid = set(_SECTION_CONTENT_CHECKS) | {CONTAINER_KEY}
    bad = {h: k for h, k in mapping.items() if k not in valid}
    if bad:
        raise ValueError(
            'Invalid section key(s) in the front-matter `sections:` mapping: '
            + ', '.join(f'{h!r} -> {k!r}' for h, k in sorted(bad.items()))
            + '\nValid keys: ' + ', '.join(sorted(valid))
        )
    return mapping


def _parse_header(md: str) -> tuple[str, str]:
    """Extract project_id from `# Project Profile: X` and timestamp from `Generated: X`."""
    pid_match = re.search(r'^#\s*Project Profile:\s*(\S+)', md, re.MULTILINE)
    ts_match = re.search(r'^Generated:\s*(\S+)', md, re.MULTILINE)
    return (pid_match.group(1) if pid_match else '',
            ts_match.group(1) if ts_match else '')


def _split_sections(md: str) -> list[tuple[str, str]]:
    """Split markdown by `^## ` headings, in document order.

    A list of pairs rather than a dict: a proposal may repeat a heading (two
    `## 機能一覧` chapters), and a dict drops the first one before any section
    logic can see it — content the user wrote, gone with no warning. Order
    matters too: the prune pass emits slides in the order the markdown
    introduces its sections.
    """
    parts: list[tuple[str, str]] = []
    current_heading = None
    current_lines: list[str] = []
    for line in md.splitlines():
        m = re.match(r'^##\s+(.+?)\s*$', line)
        if m and not line.startswith('###'):
            if current_heading is not None:
                parts.append((current_heading, '\n'.join(current_lines).strip()))
            current_heading = m.group(1).strip()
            current_lines = []
        else:
            if current_heading is not None:
                current_lines.append(line)
    if current_heading is not None:
        parts.append((current_heading, '\n'.join(current_lines).strip()))
    return parts


# ---------------------------------------------------------------------------
# Section handlers — one per top-level section
# ---------------------------------------------------------------------------

def _handle_cover(profile: ProjectProfile, content: str):
    subs = _split_subsections(content)
    profile.cover = CoverSection(
        # `Title` is the pre-rename spelling, still accepted so older profile
        # markdown keeps filling the cover instead of silently falling back to
        # the template's 'SVN Proposal Menu' placeholder.
        company=_parse_text(subs.get('Company') or subs.get('Title', '')),
        date=_parse_text(subs.get('Date', '')),
    )


def _handle_agenda(profile: ProjectProfile, content: str):
    subs = _split_subsections(content)
    if subs:
        chapters = _parse_list(subs.get('Chapters', ''))
        cost_breakdown = _parse_list(subs.get('Cost Breakdown', ''))
    else:
        # A bare `## Agenda` followed by the source document's numbered list —
        # the shape a hand-written profile most naturally takes. Everything is
        # a chapter; the 費用 sub-items then stay at the template's wording.
        chapters, cost_breakdown = _parse_list(content), []
    profile.agenda = AgendaSection(chapters=chapters, cost_breakdown=cost_breakdown)


# Every handler below reads the schema's own `###` subsection names first and
# falls back to the bare block. The fallback is what lets a chapter lifted
# straight out of a proposal fill its slide: `### 1.2 機能一覧` carries its
# intro prose and its table together, with no `### Description` to look under.
# The fallback never overrides a named subsection — it only fills what one
# would have filled and didn't.

def _handle_project_background(profile: ProjectProfile, content: str):
    subs = _split_subsections(content)
    current_issues = _parse_text(subs.get('Current Issues', ''))
    objectives = _parse_text(subs.get('Objectives', ''))
    if not (current_issues or objectives):
        # A bare 背景・目的 block states the situation first and the goal after,
        # in that order — the same order the template's two boxes sit in. One
        # paragraph only fills the first box rather than being split in half.
        paragraphs = _split_paragraphs(_parse_prose(content))
        current_issues = paragraphs[0] if paragraphs else ''
        objectives = '\n\n'.join(paragraphs[1:])
    profile.project_background = BackgroundSection(
        current_issues=current_issues, objectives=objectives,
    )


def _handle_features(profile: ProjectProfile, content: str):
    subs = _split_subsections(content)
    profile.features = FeaturesSection(
        description=_parse_text(subs.get('Description', '')) or _parse_prose(content),
        table=_parse_table(subs.get('Feature Table', '')) or _parse_table(content),
    )


def _handle_nfr_overview(profile: ProjectProfile, content: str):
    subs = _split_subsections(content)
    profile.nfr_overview = NFROverviewSection(
        description=_parse_text(subs.get('Description', '')) or _parse_prose(content),
        table=_parse_table(subs.get('Requirements Table', '')) or _parse_table(content),
    )


def _handle_screen_flow(profile: ProjectProfile, content: str):
    profile.screen_flow = ScreenFlowSection(image_path=_parse_image_ref(content))


def _handle_business_process(profile: ProjectProfile, content: str):
    subs = _split_subsections(content)
    after_blocks = []
    after_content = subs.get('After (Post-Introduction)') or subs.get('After', '')
    # Each `#### title` followed by body
    for m in re.finditer(r'^####\s+(.+?)\s*$\n(.*?)(?=^####\s|\Z)', after_content, re.MULTILINE | re.DOTALL):
        after_blocks.append(AfterBlock(title=_parse_text(m.group(1)), body=_parse_text(m.group(2))))
    profile.business_process = BusinessProcessSection(
        categories=_parse_list(subs.get('Categories', '')),
        before_steps=_parse_list(subs.get('Before (Current Process)') or subs.get('Before', '')),
        after_blocks=after_blocks,
    )


def _handle_benefits(profile: ProjectProfile, content: str):
    benefits = []
    for m in re.finditer(r'^###\s+(.+?)\s*$\n(.*?)(?=^###\s|\Z)', content, re.MULTILINE | re.DOTALL):
        benefits.append(BenefitSection(title=_parse_text(m.group(1)), content=_parse_text(m.group(2))))
    if not benefits:
        # A proposal states its benefits as a two-column `観点 | メリット` table
        # rather than as headed blocks. Same pairs, different shape.
        benefits = [
            BenefitSection(title=title.strip(), content=body.strip())
            for title, body in (
                tuple(row.values())[:2] for row in _parse_table(content)
                if len(row) >= 2
            )
        ]
    profile.benefits = benefits


def _handle_approach_comparison(profile: ProjectProfile, content: str):
    profile.approach_comparison = _parse_table(content)


def _handle_assumptions(profile: ProjectProfile, content: str):
    assumptions = []
    for m in re.finditer(r'^###\s+(.+?)\s*$\n(.*?)(?=^###\s|\Z)', content, re.MULTILINE | re.DOTALL):
        assumptions.append(AssumptionSection(label=_parse_text(m.group(1)), content=_parse_text(m.group(2))))
    profile.assumptions = assumptions


def _handle_infrastructure(profile: ProjectProfile, content: str):
    profile.infrastructure = _parse_table(content)


def _handle_software_stack(profile: ProjectProfile, content: str):
    profile.software_stack = _parse_table(content)


def _handle_nfr_sections(profile: ProjectProfile, content: str):
    sections = []
    for m in re.finditer(r'^###\s+(.+?)\s*$\n(.*?)(?=^###\s|\Z)', content, re.MULTILINE | re.DOTALL):
        sections.append(NFRSection(title=_parse_text(m.group(1)), body=_parse_text(m.group(2))))
    profile.nfr_sections = sections


def _handle_nfr_detailed(profile: ProjectProfile, content: str):
    profile.nfr_detailed = _parse_table(content)


def _handle_deliverables(profile: ProjectProfile, content: str):
    profile.deliverables = _table_section(content)


def _handle_cost(profile: ProjectProfile, content: str):
    profile.cost = _table_section(content)


def _table_section(content: str) -> TableSection:
    """Shape a chapter into its main table plus the wording around it.

    `parse_tables` rather than `parse_table`: these chapters carry more than one
    table (費用 holds a cost breakdown and an infra note), and concatenating them
    would apply the first one's header to the second one's rows. The largest is
    the one the chapter is about.

    Title and description come from wherever that table actually lives — under a
    `###` subsection (費用's table sits under 9.1 開発費用) it is that
    subsection's heading and prose; loose in the chapter, the title is left
    empty so the template's own heading stands.
    """
    # The chapter's opening prose, before its first `###`. That is the sentence
    # introducing the table; anything after it is the footnotes and caveats the
    # subsection appends, which do not belong in a slide's lead-in.
    lead_in = _parse_prose(re.split(r'^###\s', content, maxsplit=1,
                                    flags=re.MULTILINE)[0])
    subs = _split_subsections(content)
    for heading, body in subs.items():
        tables = _parse_tables(body)
        if tables:
            return TableSection(title=_strip_leading_number(heading),
                                description=lead_in, rows=max(tables, key=len))
    tables = _parse_tables(content)
    return TableSection(description=lead_in,
                        rows=max(tables, key=len) if tables else [])


def _strip_leading_number(heading: str) -> str:
    """`9.1 開発費用（概算工数）` -> `開発費用（概算工数）`.

    Section numbering belongs to the document's outline, not to a slide that
    carries its own chapter divider.
    """
    return _strip_inline_markup(re.sub(r'^\d+(?:\.\d+)*\s*[.．、）)]?\s+', '',
                                       heading.strip()))


def _handle_schedule(profile: ProjectProfile, content: str):
    subs = _split_subsections(content)
    tables = _parse_tables(content)
    profile.schedule = ScheduleSection(
        description=_parse_text(subs.get('Description', '')) or _parse_prose(content),
        image_path=(_parse_image_ref(subs.get('Chart', ''))
                    or _parse_image_ref(content)),
        table=max(tables, key=len) if tables else [],
    )
