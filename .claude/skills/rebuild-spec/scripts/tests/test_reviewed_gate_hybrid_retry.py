# layout-exempt: gate regression test — docs paths are managed fixture targets
"""Regression: the `--reviewed` sample-size gate must bite on a HYBRID-corpus retry.

Every pre-existing test for `resolve_reviewed_gate` built `SHAPE_V26` fixtures, so the
retry path was never exercised -- and it was broken: eligibility was computed as
`detect_shape(fd) == SHAPE_V26`, which is the empty set once a corpus has been migrated
once, making `required_sample_size(0) == 0` and the gate pass for ANY manifest size.

Live-proven on a real 66-feature corpus before the fix: after a 7-slug first pass, 59 dirs
still held satellites, `eligible` read 0, and a ONE-slug manifest was authorized to delete
-- while the tool's own `[ACTION REQUIRED]` block printed "review at least 6 of them". The
retry path is the documented remedy that block tells operators to run, so the only control
guarding an irreversible delete was dead exactly where it mattered.

Eligibility is therefore "still holds a retained v26 satellite", not "is still SHAPE_V26".
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _audience_split_cli_lib import resolve_reviewed_gate  # noqa: E402
from _audience_split_shape_lib import (  # noqa: E402
    FUNCTIONAL_SPEC, TECHNICAL_SPEC, V26_SATELLITE_FILES, SHAPE_V26, detect_shape,
)

FM = "---\nauthored_by: rebuild-spec\n---\n"


def _v26(d: Path) -> None:
    """A pristine 4-file v26 feature dir."""
    d.mkdir(parents=True, exist_ok=True)
    (d / TECHNICAL_SPEC).write_text(FM + "# F\n\n## Overview\n\nx\n", encoding="utf-8")
    for f in V26_SATELLITE_FILES:
        (d / f).write_text(FM + "# S\n\nx\n", encoding="utf-8")


def _hybrid(d: Path) -> None:
    """A migrated-but-satellites-retained dir: the state EVERY dir is in on a retry."""
    _v26(d)
    (d / FUNCTIONAL_SPEC).write_text(FM + "# F\n\n## 1. Overview\n\nx\n", encoding="utf-8")


def _cleared(d: Path) -> None:
    """A reviewed dir whose satellites were already deleted -- no longer eligible."""
    d.mkdir(parents=True, exist_ok=True)
    (d / TECHNICAL_SPEC).write_text(FM + "# F\n\n## Overview\n\nx\n", encoding="utf-8")
    (d / FUNCTIONAL_SPEC).write_text(FM + "# F\n\n## 1. Overview\n\nx\n", encoding="utf-8")


def _dirs(root: Path, n: int, make) -> list[Path]:
    out = []
    for i in range(1, n + 1):
        d = root / f"F{i:03d}_Feature{i}"
        make(d)
        out.append(d)
    return out


class TestHybridRetryGate:
    def test_hybrid_dirs_are_not_shape_v26(self, tmp_path):
        """The premise: on a retry, the OLD eligibility test sees nothing."""
        dirs = _dirs(tmp_path, 10, _hybrid)
        assert all(detect_shape(d) != SHAPE_V26 for d in dirs)

    def test_undersized_manifest_refused_on_hybrid_retry(self, tmp_path, capsys):
        """The bug: 1 of 10 retained must be REFUSED, not waved through."""
        dirs = _dirs(tmp_path, 10, _hybrid)
        got = resolve_reviewed_gate(dirs, {"F001_Feature1"})
        assert got is None, "a 1-of-10 manifest must be treated as absent"
        out = capsys.readouterr().out
        assert "1 of 10 eligible" in out
        assert "nothing to sample" not in out, (
            "the vacuous 'nothing to sample' path means eligibility read 0 again")

    def test_sufficient_manifest_honored_on_hybrid_retry(self, tmp_path):
        dirs = _dirs(tmp_path, 10, _hybrid)
        reviewed = {f"F{i:03d}_Feature{i}" for i in range(1, 4)}  # 3 of 10 == min 3
        assert resolve_reviewed_gate(dirs, reviewed) == reviewed

    def test_cleared_dirs_drop_out_of_eligibility(self, tmp_path):
        """Satellites gone == no longer eligible, so the bar falls as work proceeds."""
        retained = _dirs(tmp_path / "keep", 4, _hybrid)
        cleared = _dirs(tmp_path / "done", 20, _cleared)
        reviewed = {retained[0].name, retained[1].name, retained[2].name}
        # 3 of 4 eligible clears min-3; the 20 cleared dirs must not inflate the bar.
        assert resolve_reviewed_gate(retained + cleared, reviewed) == reviewed

    def test_first_pass_v26_behaviour_unchanged(self, tmp_path):
        """The original first-migration case must still behave exactly as before."""
        dirs = _dirs(tmp_path, 66, _v26)
        assert resolve_reviewed_gate(dirs, {"F001_Feature1"}) is None
        seven = {f"F{i:03d}_Feature{i}" for i in range(1, 8)}
        assert resolve_reviewed_gate(dirs, seven) == seven
