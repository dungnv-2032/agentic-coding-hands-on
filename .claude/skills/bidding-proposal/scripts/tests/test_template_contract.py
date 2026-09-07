"""The template-contract gate, run as a test.

`lib/templates/svn.py` addresses the shipped .pptx by exact string and by shape
index. Editing the template silently disables a mapping instead of erroring, so
this is what turns that into a failing build.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

pytest.importorskip('pptx')


def test_template_contract_holds(scripts_dir, template_path):
    result = subprocess.run(
        [sys.executable, str(scripts_dir / 'verify-template-contract.py')],
        capture_output=True, text=True, cwd=str(scripts_dir),
    )
    assert result.returncode == 0, (
        'A svn.py mapping no longer resolves against the shipped template.\n'
        'Fix the mapping or the template — do NOT delete the entry to make this '
        'pass; dropping a TEMPLATE_NOTE_TEXTS line re-ships a Vietnamese '
        f'authoring note to the client.\n\n{result.stdout}\n{result.stderr}'
    )


def test_verifier_detects_a_broken_mapping(scripts_dir, template_path, tmp_path):
    """The gate must actually fail when a mapping goes stale.

    Guards against the check quietly degrading into a no-op — a green gate that
    cannot go red is worse than no gate.
    """
    script = (scripts_dir / 'verify-template-contract.py').read_text(encoding='utf-8')
    probe = tmp_path / 'probe.py'
    probe.write_text(
        script.replace(
            'check_slide_text_map(report, prs, \'SLIDE_TEXT_OVERRIDES\', SLIDE_TEXT_OVERRIDES)',
            "check_slide_text_map(report, prs, 'SLIDE_TEXT_OVERRIDES', "
            "{21: {'text that is not in the template': 'x'}})",
        ),
        encoding='utf-8',
    )
    # The probe lives in tmp_path, so its own `sys.path.insert(parent)` points
    # away from the skill — hand it the scripts dir explicitly.
    # …and its template resolution is relative to that same parent, so name the
    # shipped template explicitly.
    env = {**os.environ, 'PYTHONPATH': str(scripts_dir)}
    result = subprocess.run(
        [sys.executable, str(probe), '--template', str(template_path)],
        capture_output=True, text=True, cwd=str(scripts_dir), env=env)
    assert result.returncode == 1, f'{result.stdout}\n{result.stderr}'
    assert 'unmatched' in result.stdout
