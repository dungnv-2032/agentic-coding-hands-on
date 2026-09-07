#!/usr/bin/env python3
"""The sixth gate — a secret scan over the FINAL `llms-full.txt` text before promotion.

v1 inlined document content only under an explicit `--full`; v2 flips inlining to default-on
and presents the result as a file meant to be downloaded and shared. The compensating control
has to arrive with the change that removes the opt-in (red-team F5). The privacy-block hook is
not that control — it inspects the agent's tool calls and cannot see what this Python subprocess
reads.

Reuse mechanism is a path import, not a relocation: `assert_no_secrets` stays in
`rebuild-spec/scripts/_credential_scrub_lib.py` (four live rebuild-spec importers + reference/
CHANGELOG mentions make relocating it its own plan — recorded as a follow-up, not built here).

Two candidate locations are tried, sibling first. A project-scoped or partial install that carries
THIS skill alone has no sibling `rebuild-spec`, and fail-closed would then withhold the primary
deliverable on every run — a dependency-layout accident, not a real secret. The user-scope kit root
is the fallback, so a normal `tkm init -g` install satisfies the gate from either scope.

Fail-closed, proportionately: a non-empty `warnings[]` — or a lib missing from BOTH candidates —
withholds `llms-full.txt` ONLY. `llms.txt` still promotes, because the index inlines nothing and
carries none of the risk this gate protects against.
"""
import importlib.util
import os
from pathlib import Path

_LIB_REL = ("rebuild-spec", "scripts", "_credential_scrub_lib.py")


def _candidates():
    """Sibling skill dir first (a full kit install, project- or user-scoped), then the user-scope
    kit root (`~/.claude/skills/`) for an install that carries this skill without its sibling."""
    yield Path(__file__).resolve().parents[2].joinpath(*_LIB_REL)
    home = os.environ.get("HOME") or str(Path.home())
    yield Path(home).joinpath(".claude", "skills", *_LIB_REL)


def _load_assert_no_secrets():
    """Path import of the first candidate that exists; returns None when none is found or the
    import fails — never raises, so an absent dependency degrades instead of crashing."""
    lib_path = next((p for p in _candidates() if p.is_file()), None)
    if lib_path is None:
        return None
    try:
        spec = importlib.util.spec_from_file_location("_rebuild_spec_credential_scrub_lib", lib_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception:
        # Defensive: any import-time failure (syntax error, missing stdlib symbol after an
        # incompatible edit upstream, etc.) degrades to "unavailable" rather than crashing the
        # whole run — the full artifact is withheld either way, just with a clearer reason when
        # the file is simply absent.
        return None
    return getattr(module, "assert_no_secrets", None)


def scan(text: str) -> list:
    """Returns warnings[]. Empty == clean. Fail-closed on an unavailable lib."""
    fn = _load_assert_no_secrets()
    if fn is None:
        return ["secret-scan unavailable: rebuild-spec/_credential_scrub_lib.py not found "
                "next to this skill or under ~/.claude/skills/"]
    return fn(text)
