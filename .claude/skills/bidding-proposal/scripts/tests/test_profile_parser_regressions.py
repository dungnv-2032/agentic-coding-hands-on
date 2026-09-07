"""Regressions for parser defects that only showed on non-reference documents.

Each test asserts the SPECIFIC wrong value the bug produced, so a fixture that
stops reproducing fails loudly instead of passing vacuously.
"""
from __future__ import annotations

import pytest

from lib.profile_parser import parse_cover_date, parse_profile


# --- B2: addressee detection -------------------------------------------------

def test_addressee_ignores_shiyou_in_prose(fixtures_dir):
    """`様` inside 仕様 / 多様 must not be read as an honorific.

    The bug matched `様` as a substring, took the document's FIRST sentence
    instead of its addressee line, then stripped the character with a global
    `str.replace` — putting `本書は要件仕および多な運用パターン…` on the cover.
    """
    profile = parse_profile((fixtures_dir / 'duplicate-sections-and-honorifics.md')
                            .read_text(encoding='utf-8'))
    assert profile.cover.company == '株式会社テストクライアント'
    assert '仕' not in profile.cover.company  # the mangled form's fingerprint


@pytest.mark.parametrize('line, expected', [
    ('### 株式会社スタイルポート 御中', '株式会社スタイルポート'),
    ('### Kính gửi Quý công ty Styleport', 'Styleport'),
    ('### 東京物流株式会社 御中', '東京物流株式会社'),
    ('本書は要件仕様および多様な運用パターンを整理したものです。', ''),
    ('システムの仕様について', ''),
])
def test_addressee_anchoring(line, expected):
    """Suffix honorifics (JP) and prefix honorifics (VI) both resolve; prose does not."""
    profile = parse_profile(f'# T\n\n{line}\n\n## Features\n\nx\n')
    assert profile.cover.company == expected


def test_explicit_cover_section_keeps_preamble_date():
    """A `## Cover` giving only Company must not erase the preamble's date.

    The fill ran BEFORE the section loop, so `_handle_cover` overwrote the whole
    CoverSection and the date went with it.
    """
    profile = parse_profile(
        '# T\n\n### 株式会社エス 御中\n\n2026.06.01\n\n'
        '## Cover\n\n### Company\n明示された会社\n'
    )
    assert profile.cover.company == '明示された会社'  # explicit section wins
    assert profile.cover.date == '2026.06.01'        # preamble fills the gap


@pytest.mark.parametrize('text, expected', [
    ('2026年3月15日', '2026.03.15'),
    ('2026 年 3 月 15 日', '2026.03.15'),
    ('2026.03.15', '2026.03.15'),
    ('2026/03/15', '2026.03.15'),
    ('2026-03-15', '2026.03.15'),
    ('March 15, 2026', ''),
])
def test_cover_date_notations(text, expected):
    assert parse_cover_date(text) == expected


# --- Cover: an English proposal's own front matter ---------------------------

_ENGLISH_PREAMBLE = (
    '# Heathring Wellness Ring App — Development Proposal\n\n'
    '**Prepared for**: Evering\n'
    '**Prepared by**: Sun Asterisk Inc. (Sun*)\n'
    '**Document version**: 1.1\n'
    '**Date**: 2026-04-19\n\n'
    '## Executive Summary\n\nx\n'
)


def test_english_proposal_fills_the_cover():
    """`Prepared for:` + an ISO date must reach slide 1.

    The bug: neither notation was read, so a proposal naming its client on line
    3 still shipped the template's `SVN Proposal Menu` / `2025.04.04`.
    """
    profile = parse_profile(_ENGLISH_PREAMBLE)
    assert profile.cover.company == 'Evering'
    assert profile.cover.date == '2026.04.19'


def test_prepared_by_never_reaches_the_cover():
    """The vendor's line sits next to the client's — it must not win.

    A `for`/`to` alternation loose enough to match `Prepared by` would put
    `Sun Asterisk Inc. (Sun*)` on the cover as the addressee.
    """
    profile = parse_profile(_ENGLISH_PREAMBLE)
    assert 'Sun Asterisk' not in profile.cover.company


@pytest.mark.parametrize('line, expected', [
    ('**Prepared for**: Evering', 'Evering'),
    ('Client: Acme Corp', 'Acme Corp'),
    ('To: Acme Corp', 'Acme Corp'),
    ('**Prepared by**: Sun Asterisk Inc.', ''),
    ('Prepared for the closed beta, the app is scoped to verification.', ''),
    ('This document is for internal review.', ''),
])
def test_addressee_label_is_anchored_and_needs_a_colon(line, expected):
    """The label is a field name at line start, not a word in a sentence."""
    profile = parse_profile(f'# T\n\n{line}\n\n## Features\n\nx\n')
    assert profile.cover.company == expected


def test_unfilled_cover_warns(capsys):
    """Falling back to the placeholder must be audible, not silent."""
    parse_profile('# T\n\nNo addressee, no date here.\n\n## Features\n\nx\n')
    out = capsys.readouterr().out
    assert 'WARNING: cover company and date not found' in out
    assert '--cover-company --cover-date' in out


# --- B3: duplicate section collision ----------------------------------------

def test_duplicate_heading_keeps_first_and_routes_second(fixtures_dir):
    """`## 機能一覧` then `## 機能一覧表` — both resolve to `features`.

    The second used to overwrite the first outright, deleting a whole table.
    """
    profile = parse_profile((fixtures_dir / 'duplicate-sections-and-honorifics.md')
                            .read_text(encoding='utf-8'))
    assert [row['No'] for row in profile.features.table] == ['1', '2']
    assert '機能一覧表' in [entry['title'] for entry in profile.auto_extra_slides]


def test_identical_headings_both_survive():
    """A dict keyed by heading text dropped the first block before any section
    logic could see it."""
    profile = parse_profile(
        '# T\n\n## 機能一覧\n\n| No | 名 |\n|---|---|\n| 1 | A |\n\n'
        '## 機能一覧\n\n| No | 名 |\n|---|---|\n| 9 | B |\n'
    )
    assert [row['No'] for row in profile.features.table] == ['1']
    assert len(profile.auto_extra_slides) == 1


# --- Phase 06: front-matter section mapping ---------------------------------

def test_sections_mapping_reaches_bespoke_slides(fixtures_dir):
    """An ordinary JP proposal resolves nothing via the alias table; with a
    mapping every chapter must reach its section."""
    unmapped = parse_profile((fixtures_dir / 'generic-jp-ordinary-wording.md')
                             .read_text(encoding='utf-8'))
    mapped = parse_profile((fixtures_dir / 'generic-jp-with-sections-mapping.md')
                           .read_text(encoding='utf-8'))

    assert unmapped.section_order == ['agenda']
    for key in ('project_background', 'features', 'benefits', 'approach_comparison',
                'assumptions', 'infrastructure', 'schedule', 'cost'):
        assert key in mapped.section_order, key
    assert mapped.auto_extra_slides == []


def test_front_matter_is_stripped_before_cover_and_header(fixtures_dir):
    """Front matter must not leak into the preamble the cover reads."""
    profile = parse_profile((fixtures_dir / 'generic-jp-with-sections-mapping.md')
                            .read_text(encoding='utf-8'))
    assert profile.cover.company == '東京物流株式会社'
    assert 'sections' not in profile.cover.company


def test_invalid_section_key_is_rejected():
    """A typo'd key would otherwise look exactly like a mapping that worked."""
    with pytest.raises(ValueError) as excinfo:
        parse_profile('---\nsections:\n  "X": features_table\n---\n# T\n\n## Features\n\nx\n')
    assert 'features_table' in str(excinfo.value)
    assert 'Valid keys' in str(excinfo.value)


def test_document_without_front_matter_is_unchanged():
    """The mapping is an override; absent it, behavior is exactly as before."""
    profile = parse_profile('# T\n\n## Features\n\n説明\n')
    assert profile.section_order == ['features']
