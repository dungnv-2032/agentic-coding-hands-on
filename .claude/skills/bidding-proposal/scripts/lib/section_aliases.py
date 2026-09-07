"""Heading vocabulary — resolves one markdown heading to a profile section key.

`gen-md.py` writes profile markdown with fixed English headings (`## Features`),
but a proposal a human wrote names its chapters the way the document does:
`## 1\\. システムの概要 — System Overview`, `### 1.2 機能一覧`. Both must land on
the same section key, or the proposal's chapters fall out of the schema and get
rendered as loose appendix slides instead of filling their template slides.

Resolution is deliberately narrow. A heading is normalized (markdown escapes
removed, chapter numbering stripped, the `JP — English` gloss split) into a few
candidate spellings, and each is looked up in a fixed table. Nothing is guessed:
a heading that matches no entry resolves to None and the caller keeps its
existing fallback. Adding a new document wording means adding a line here.

Kept dependency-free so `profile_parser.py` and any future consumer can import
it without a cycle.
"""
from __future__ import annotations

import re

# `Sun\*` → `Sun*`, `1\.` → `1.` — markdown escapes as Google Docs exports them.
_MD_ESCAPE = re.compile(r'\\(.)')

# Chapter numbering a proposal puts in front of the real title: `1. `, `1.2 `,
# `5.1 `, `9.1 `, and the JP full-width variants.
_LEADING_NUMBER = re.compile(r'^\d+(?:\.\d+)*\s*[.．、）)]?\s+')

# `<JP title> — <English gloss>`; en dash and hyphen are accepted because which
# one a document uses is arbitrary.
_GLOSS_DASH = re.compile(r'\s+[—–-]\s+')

# Trailing parenthetical qualifier: `非機能要件（ROOV SLO 準拠）` → `非機能要件`.
_PAREN_SUFFIX = re.compile(r'[（(][^（()）]*[）)]\s*$')

# Canonical headings as gen-md.py writes them. Keys are lookup-normalized
# (casefolded, whitespace collapsed) — see `_lookup_key`.
_CANONICAL: dict[str, str] = {
    'cover': 'cover',
    'agenda': 'agenda',
    'project background': 'project_background',
    'features': 'features',
    'non-functional requirements (overview)': 'nfr_overview',
    'nfr overview': 'nfr_overview',
    'screen flow': 'screen_flow',
    'business process': 'business_process',
    'benefits': 'benefits',
    'approach comparison': 'approach_comparison',
    'assumptions': 'assumptions',
    'infrastructure': 'infrastructure',
    'software stack': 'software_stack',
    'nfr sections': 'nfr_sections',
    'nfr detailed': 'nfr_detailed',
    'schedule': 'schedule',
}

# Japanese chapter and subsection titles as the source proposals write them,
# plus the English glosses their AGENDA block pairs with each chapter.
#
# Note what is deliberately ABSENT: `システムの概要` / `system overview`. That
# chapter is a container — its own `###` subsections (背景・目的, 機能一覧) are
# the real sections, and the caller promotes them. Mapping the container itself
# would swallow all of them into one section.
_DOCUMENT_ALIASES: dict[str, str] = {
    # 1.x — inside the システムの概要 container
    'プロジェクト背景・目的': 'project_background',
    'プロジェクト背景': 'project_background',
    '背景・目的': 'project_background',
    '機能一覧': 'features',
    '機能一覧表': 'features',
    '画面遷移図': 'screen_flow',
    '業務フロー': 'business_process',
    '業務フロー図': 'business_process',
    # 2 — メリット
    'システム導入のメリット': 'benefits',
    'システムの導入のメリット': 'benefits',  # the template's own wording
    'advantages': 'benefits',
    'advantage of system introduction': 'benefits',
    # 3 — 提案の要諦
    '提案の要諦': 'approach_comparison',
    'the essence of the proposal': 'approach_comparison',
    # 5 — 前提条件
    'お見積りの前提条件': 'assumptions',
    '見積りの前提条件': 'assumptions',
    '前提条件': 'assumptions',
    'estimated assumptions': 'assumptions',
    # 6 — システム構成
    'システム構成図の提案': 'infrastructure',
    'システム構成図': 'infrastructure',
    'システム構成': 'infrastructure',
    'system architecture': 'infrastructure',
    'ソフトウェア構成': 'software_stack',
    '技術スタック': 'software_stack',
    # 8 — スケジュール
    '実施スケジュール': 'schedule',
    'スケジュール': 'schedule',
    'implementation schedule': 'schedule',
    # 7 — 想定成果物. The template's own divider spells it 想定作成物; both mean
    # the same chapter, so both resolve here.
    '想定成果物': 'deliverables',
    '想定作成物': 'deliverables',
    'expected deliverables': 'deliverables',
    'the expected output': 'deliverables',
    # 9 — 費用
    '費用': 'cost',
    'お見積もりサマリ': 'cost',
    'cost': 'cost',
    # non-functional, when a document gives them their own chapter
    '非機能要件': 'nfr_overview',
    '非機能要件一覧': 'nfr_overview',
    '非機能要件詳細': 'nfr_detailed',
}

_ALIASES: dict[str, str] = {**_CANONICAL, **_DOCUMENT_ALIASES}


def _lookup_key(text: str) -> str:
    """Casefold and collapse whitespace, including the JP full-width space."""
    return re.sub(r'\s+', ' ', text.replace('　', ' ')).strip().casefold()


def heading_variants(heading: str) -> list[str]:
    """Spellings of *heading* worth looking up, most specific first.

    `1\\. システムの概要 — System Overview` yields the whole normalized title,
    then the Japanese side, then the English gloss — so a document that writes
    only one of the two still resolves.

    Public because matching a heading against something other than the alias
    table needs the same normalization — the renderer pairs an appendix slide
    with its AGENDA line this way.
    """
    base = _MD_ESCAPE.sub(r'\1', heading).strip()
    base = _LEADING_NUMBER.sub('', base).strip()
    found = [base]
    parts = _GLOSS_DASH.split(base, maxsplit=1)
    if len(parts) > 1:
        found.extend(part.strip() for part in parts)
    # A parenthetical qualifier is a document's aside, never part of the name.
    for text in list(found):
        trimmed = _PAREN_SUFFIX.sub('', text).strip()
        if trimmed and trimmed != text:
            found.append(trimmed)
    return [text for text in found if text]


def heading_display(heading: str) -> str:
    """*heading* as it should READ on a slide: escapes and numbering gone.

    The most specific variant, which is the whole title minus the chapter
    number a document numbers its sections with — `### 1.1. Project Background`
    is titled `Project Background` on the slide, the way the template's own
    chrome is worded. The gloss is deliberately kept: a document writing
    `機能一覧 — Feature List` chose to show both halves.
    """
    variants = heading_variants(heading)
    return variants[0] if variants else ''


def resolve_section_key(heading: str) -> str | None:
    """Return the profile section key *heading* names, or None if it names none.

    None is not a failure — it is the signal that the caller should apply its
    own fallback (promote the block's subsections, or route it to an
    extra slide). Nothing here ever guesses a key from a partial match.
    """
    for candidate in heading_variants(heading):
        key = _ALIASES.get(_lookup_key(candidate))
        if key:
            return key
    return None
