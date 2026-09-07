"""Every `--scope` choice list is hand-duplicated across the CLIs that declare one.

Each script declaring `--scope` carries its own `choices=[...]` literal. Nothing links them, so a
value added to one and missed on another means one CLI accepts what the next rejects — a run that
dies halfway through the pipeline on a flag the orchestrator was told is valid.

This module reads the literal out of each source file with `ast` (never by running the parser, so
a drifted list is caught even in a branch no test happens to exercise) and asserts every one is
byte-identical to the canonical set.

The CLI list is DISCOVERED, not hard-coded. An earlier hand-maintained list named four scripts
and silently omitted `assemble_judgment_report.py`, which declared `--scope` with no `choices=`
at all and so went on accepting a retired scope value after every other CLI had stopped. A list
that must be remembered is a list that will be forgotten; discovery makes a newly-added CLI a
test failure rather than a hole.
"""
import ast
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

CANONICAL_SCOPES = ["feature-list", "user-stories", "system", "all"]

def _declares_scope(script: Path) -> bool:
    """True if this script has an `add_argument("--scope", ...)` call at all."""
    tree = ast.parse(script.read_text(encoding="utf-8"))
    return any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute) and n.func.attr == "add_argument"
        and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == "--scope"
        for n in ast.walk(tree)
    )


SCOPE_CLIS = sorted(p.name for p in SCRIPTS.glob("*.py") if _declares_scope(p))


def _scope_choices(script: Path) -> list[str]:
    """The `choices=[...]` literal on the `--scope` add_argument call, read statically."""
    tree = ast.parse(script.read_text(encoding="utf-8"))
    found: list[list[str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"):
            continue
        if not (node.args and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == "--scope"):
            continue
        for kw in node.keywords:
            if kw.arg == "choices":
                found.append(ast.literal_eval(kw.value))
    assert len(found) == 1, f"{script.name}: expected exactly one --scope choices list, got {found}"
    return found[0]


@pytest.mark.parametrize("name", SCOPE_CLIS)
def test_scope_choices_match_canonical(name):
    assert _scope_choices(SCRIPTS / name) == CANONICAL_SCOPES


def test_every_list_is_identical():
    assert SCOPE_CLIS, "discovery found no --scope CLI at all; the glob or parser is broken"
    lists = {name: _scope_choices(SCRIPTS / name) for name in SCOPE_CLIS}
    assert len(set(map(tuple, lists.values()))) == 1, f"scope choices drifted: {lists}"


def test_discovery_covers_every_scope_cli():
    """The guard against the hole this suite was written to close.

    `assemble_judgment_report.py` declared `--scope` with no `choices=` and was absent from the
    old hand-maintained list, so it kept accepting a retired scope after every sibling rejected
    it. Discovery must therefore reach it — and any future CLI like it."""
    assert "assemble_judgment_report.py" in SCOPE_CLIS
    assert len(SCOPE_CLIS) >= 5, SCOPE_CLIS


def test_a_retired_scope_is_an_argparse_error_not_a_silent_empty_run():
    """The choices literal is really wired to the parser.

    Together with `test_scope_choices_match_canonical` (which asserts the literal is EXACTLY the
    canonical four, so any retired value is absent) this closes the whole surface: a scope value
    that is no longer supported exits 2 with a usage error, rather than running the pipeline over
    an empty artifact set and reporting a clean result.
    """
    import locate_synthesis_artifacts as loc

    with pytest.raises(SystemExit) as exc:
        loc.main(["--scope", "a-retired-scope-value"])
    assert exc.value.code == 2
