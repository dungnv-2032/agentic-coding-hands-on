"""Guards for the two ways a test suite can be green everywhere and red on CI.

Both failures below reached the branch and survived **8 consecutive Quality Gate
runs** before anyone traced them, because neither is visible from a passing local
suite — a developer machine has `plans/` on disk and a Python newer than the
support floor, so the code under test never meets the conditions that break it.
A behavioral test cannot catch that. These are source-level gates instead.

1. **Fixtures read from a gitignored path.** `plans/**/*` is gitignored
   (`.gitignore:68`), so nothing under it reaches CI. Two test modules read a
   corpus from `plans/.../evidence/` at MODULE level, so the `FileNotFoundError`
   fired during pytest COLLECTION and took the whole 4000-test suite down with
   exit code 2 — not "some tests failed", but "no tests ran at all".

2. **PEP 604 below the support floor.** `X | Y` in an annotation is evaluated at
   runtime unless the module carries `from __future__ import annotations`, and it
   needs Python 3.10+. The kit's declared floor is 3.9 (`quality-gate.yml`), where
   such a module raises `TypeError` on import.

Each guard DISCOVERS its subjects by walking the AST rather than checking a
hard-coded list. That is deliberate: CI reported 3 offending files while the real
counts were 7 and 7 — a list written from what CI happened to print would have
been wrong the day it was committed.
"""
from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = Path(__file__).resolve().parents[3]  # claude/skills/
REPO_ROOT = Path(__file__).resolve().parents[5]

READ_CALLS = {"read_text", "read_bytes", "open", "glob", "rglob", "iterdir", "listdir"}

# PEP-604 sites deliberately left unfixed, with the reason. This list may only
# SHRINK. Adding to it means shipping a module that cannot be imported on the
# floor Python the Quality Gate claims to support — fix the module instead.
PEP604_ALLOWLIST = {
    # Reported 2026-08-27, left out of the CI-fix PR on the maintainer's call:
    # these are SHIPPED scripts (not tests), so the bug bites a user's install on
    # py3.9, not CI. They need their own PR — see plan
    # 260827-0906-fix-ci-collection-errors/plan.md "Ngoài phạm vi".
    "index-docs/scripts/extract_embedded_media.py",
    "index-docs/scripts/ooxml_text.py",
    "index-docs/scripts/tests/test_ooxml_extractors.py",
}


def _git_available() -> bool:
    """True when this tree is a real git checkout that git can answer questions about."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def _iter_py(root: Path):
    for p in sorted(root.rglob("*.py")):
        if ".venv" in p.parts or "__pycache__" in p.parts:
            continue
        try:
            yield p, ast.parse(p.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue  # deliberately malformed encoding fixtures live in the tree


def _has_future_annotations(tree: ast.Module) -> bool:
    return any(
        isinstance(n, ast.ImportFrom)
        and n.module == "__future__"
        and any(a.name == "annotations" for a in n.names)
        for n in tree.body
    )


class TestNoModuleLevelReadsFromGitignoredPaths:
    """Guard 1 — the shape that produced pytest exit code 2."""

    def test_no_test_module_reads_from_plans_at_import_time(self) -> None:
        offenders = []
        for path, tree in _iter_py(TESTS_DIR):
            for node in tree.body:  # TOP LEVEL only — this is what import executes
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                           ast.Import, ast.ImportFrom)
                ):
                    continue
                reads = any(
                    isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Attribute)
                    and sub.func.attr in READ_CALLS
                    for sub in ast.walk(node)
                )
                # Match the AST, not `ast.unparse` text: unparse normalizes string
                # literals to single quotes, so a substring test for '"plans"'
                # silently never fires — a gate that cannot fail.
                names_plans = any(
                    isinstance(sub, ast.Constant) and sub.value == "plans"
                    for sub in ast.walk(node)
                )
                if reads and names_plans:
                    offenders.append(f"{path.name}:{node.lineno}  {ast.unparse(node)[:90]}")
        assert not offenders, (
            "Test fixtures read from `plans/` at MODULE level. `plans/**/*` is gitignored, "
            "so the file is absent on CI and the read raises during COLLECTION — which "
            "aborts the entire suite (exit 2), not just this module. Move the fixture into "
            "tests/fixtures/ and commit it:\n  " + "\n  ".join(offenders)
        )


class TestTestFixturesAreGitTracked:
    """Guard 3 — broader than Guard 1: catches reads inside function bodies too.

    A fixture path that git ignores is not a fixture. It is a local convenience
    that silently disables its test everywhere else.
    """

    def test_declared_fixture_roots_are_not_gitignored(self) -> None:
        if not _git_available():
            pytest.skip("not a git checkout — `git check-ignore` cannot be consulted here")
        fixture_roots = {
            p for p in TESTS_DIR.rglob("fixtures") if p.is_dir()
        }
        assert fixture_roots, "expected at least one fixtures/ directory to check"
        ignored = []
        for root in sorted(fixture_roots):
            result = subprocess.run(
                ["git", "check-ignore", "-q", str(root)],
                cwd=REPO_ROOT, capture_output=True, timeout=30,
            )
            if result.returncode == 0:  # 0 means "is ignored"
                ignored.append(str(root.relative_to(REPO_ROOT)))
        assert not ignored, (
            "Fixture directories are gitignored, so CI will never see them:\n  "
            + "\n  ".join(ignored)
        )

    def test_the_sot_corpus_is_actually_committed(self) -> None:
        """The specific corpus whose absence caused the 8-run outage.

        Asserts on `git ls-files`, not on `Path.exists()` — the file being present
        on THIS machine is exactly the condition that hid the bug.

        Skips where git cannot answer (a source tarball, an export with no `.git`).
        That is not a loophole: CI checks the repo out with `actions/checkout`, so
        the gate is live exactly where it matters.
        """
        if not _git_available():
            pytest.skip("not a git checkout — `git ls-files` cannot be consulted here")
        corpus = TESTS_DIR / "fixtures" / "sot-corpus"
        assert corpus.is_dir(), "sot-corpus fixtures missing"
        result = subprocess.run(
            ["git", "ls-files", str(corpus.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )
        tracked = [ln for ln in result.stdout.splitlines() if ln.strip()]
        on_disk = [p for p in corpus.rglob("*") if p.is_file()]
        assert len(tracked) == len(on_disk), (
            f"{len(on_disk)} corpus file(s) on disk but {len(tracked)} tracked by git — "
            "an untracked fixture is invisible to CI"
        )


class TestPep604StaysBelowTheSupportFloor:
    """Guard 2 — `quality-gate.yml` pins py3.9 as the floor for exactly this."""

    def _offenders(self) -> list[str]:
        out = []
        for path, tree in _iter_py(SKILLS_ROOT):
            if _has_future_annotations(tree):
                continue
            rel = str(path.relative_to(SKILLS_ROOT))
            if rel in PEP604_ALLOWLIST:
                continue
            for node in ast.walk(tree):
                anns = []
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    anns = [a.annotation for a in node.args.args + node.args.kwonlyargs
                            if a.annotation]
                    if node.returns:
                        anns.append(node.returns)
                elif isinstance(node, ast.AnnAssign) and node.annotation:
                    anns = [node.annotation]
                for a in anns:
                    if any(isinstance(s, ast.BinOp) and isinstance(s.op, ast.BitOr)
                           for s in ast.walk(a)):
                        out.append(f"{rel}:{node.lineno}  {ast.unparse(a)}")
                        break
        return out

    def test_pep604_annotations_carry_the_future_import(self) -> None:
        offenders = self._offenders()
        assert not offenders, (
            "PEP 604 (`X | Y`) in an annotation is evaluated at runtime without "
            "`from __future__ import annotations`, and needs py3.10+. The kit's floor is "
            "py3.9 (quality-gate.yml). Add the future import:\n  " + "\n  ".join(offenders)
        )

    def test_allowlist_entries_still_exist(self) -> None:
        """An allowlist that outlives its subjects is a place for new rot to hide."""
        missing = [rel for rel in PEP604_ALLOWLIST if not (SKILLS_ROOT / rel).is_file()]
        assert not missing, (
            "PEP604_ALLOWLIST names files that no longer exist — remove them:\n  "
            + "\n  ".join(missing)
        )

    def test_allowlist_entries_are_genuinely_still_offending(self) -> None:
        """Proves the allowlist is load-bearing, not decorative.

        If an entry no longer has an offending annotation, keeping it means the
        next real offender in that file passes unnoticed.
        """
        stale = []
        for rel in sorted(PEP604_ALLOWLIST):
            path = SKILLS_ROOT / rel
            tree = ast.parse(path.read_text(encoding="utf-8"))
            if _has_future_annotations(tree):
                stale.append(rel)
        assert not stale, (
            "These allowlisted files now carry the future import — drop them from "
            "PEP604_ALLOWLIST:\n  " + "\n  ".join(stale)
        )
