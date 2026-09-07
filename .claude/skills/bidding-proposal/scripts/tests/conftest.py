"""Shared pytest fixtures for the bidding-proposal suite.

Puts `scripts/` on `sys.path` the same way `gen-slide.py` does, so tests import
`lib.*` exactly as the entry points do rather than through a package install.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture(scope='session')
def scripts_dir() -> Path:
    return SCRIPTS_DIR


@pytest.fixture(scope='session')
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / 'fixtures'


@pytest.fixture(scope='session')
def template_path(scripts_dir: Path) -> Path:
    """The SVN template that ships with the skill."""
    return scripts_dir.parent / 'templates' / 'SVN Proposal Menu.pptx'


def read_fixture(fixtures_dir: Path, name: str) -> str:
    return (fixtures_dir / name).read_text(encoding='utf-8')
