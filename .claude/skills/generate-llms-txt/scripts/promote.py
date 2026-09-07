#!/usr/bin/env python3
"""Publish enriched staging files to their final artifacts — the `--promote` step.

Split out of `build-llms-skeleton.py` so that file stays under the 200-line ceiling; the CLI
surface is unchanged. Staging names live here because promote owns their lifecycle.
"""
import os
import sys
from pathlib import Path

import secret_gate

STAGE_SKELETON = ".llms.txt.work"
STAGE_FULL = ".llms-full.txt.work"


def promote(out: Path, want_full: bool) -> None:
    """Atomic publish, both-or-refuse on missing staging. Re-scans the staged full text HERE
    (not the discovery-time scan already in the manifest) because the SKILL.md LLM step may have
    edited the staged file since discovery ran — the gate must see the text that is actually
    about to ship. A non-clean scan (or an unavailable lib) withholds `llms-full.txt` only; the
    index still promotes, since it inlines nothing (FR-10, red-team F5)."""
    pairs = [(out / STAGE_SKELETON, out / "llms.txt")]
    full_stage = out / STAGE_FULL
    scan_warnings = None
    if want_full:
        if full_stage.is_file():
            scan_warnings = secret_gate.scan(full_stage.read_text(encoding="utf-8"))
        pairs.append((full_stage, out / "llms-full.txt"))
    missing = [str(s) for s, _ in pairs if not s.is_file()]
    if missing:
        print(f"Error: staging file(s) missing, refusing to promote: {missing}", file=sys.stderr)
        sys.exit(1)
    if scan_warnings:
        pairs = pairs[:1]
        print("secret scan not clean — withholding llms-full.txt: " + "; ".join(scan_warnings),
              file=sys.stderr)
    for stage, final in pairs:  # each os.replace is atomic
        os.replace(stage, final)
    print("promoted: " + ", ".join(str(f) for _, f in pairs))
