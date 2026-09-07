"""`--cover-company` / `--cover-date` — the manual escape hatch for slide 1.

The supplied-document path may not edit the user's proposal, so when its
addressee or date is written in a notation `profile_parser` doesn't read, these
flags are the only way to keep the template placeholder off the cover.
"""
from __future__ import annotations

import importlib.util

import pytest

from lib.profile_schema import CoverSection, ProjectProfile


@pytest.fixture(scope='module')
def gen_slide(scripts_dir):
    """Import `gen-slide.py` by path — the hyphen makes it un-importable by name."""
    spec = importlib.util.spec_from_file_location('gen_slide', scripts_dir / 'gen-slide.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _profile(**cover) -> ProjectProfile:
    profile = ProjectProfile.empty(project_id='t', timestamp='0')
    profile.cover = CoverSection(**cover)
    return profile


def test_override_fills_an_empty_cover(gen_slide):
    profile = _profile()
    gen_slide.apply_cover_overrides(profile, 'Evering', '2026-04-19')
    assert profile.cover.company == 'Evering'
    assert profile.cover.date == '2026.04.19'  # normalized like a parsed date


def test_override_beats_the_document(gen_slide):
    """A value typed on the command line is a correction, so it must win."""
    profile = _profile(company='株式会社エス', date='2026.01.01')
    gen_slide.apply_cover_overrides(profile, 'Evering', '2026-04-19')
    assert profile.cover.company == 'Evering'
    assert profile.cover.date == '2026.04.19'


def test_one_flag_leaves_the_other_field_alone(gen_slide):
    """Overriding the company must not erase the date the document gave."""
    profile = _profile(company='wrong', date='2026.01.01')
    gen_slide.apply_cover_overrides(profile, 'Evering', '')
    assert profile.cover == CoverSection(company='Evering', date='2026.01.01')


def test_no_flags_changes_nothing(gen_slide):
    profile = _profile(company='株式会社エス', date='2026.01.01')
    gen_slide.apply_cover_overrides(profile, '', '')
    assert profile.cover == CoverSection(company='株式会社エス', date='2026.01.01')


def test_unreadable_date_is_written_verbatim(gen_slide):
    """The author typed it; the renderer is not the place to second-guess it."""
    profile = _profile()
    gen_slide.apply_cover_overrides(profile, '', 'April 2026')
    assert profile.cover.date == 'April 2026'
