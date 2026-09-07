"""Pytest fixtures shared across the generate-llms-txt v2 test suite: script paths, fixture-repo
paths, and a `run_script()` helper that shells out to `build-llms-skeleton.py` the same way a real
caller would (subprocess, not an in-process import) so the CLI wiring itself is under test.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
BUILD_SCRIPT = SCRIPTS_DIR / "build-llms-skeleton.py"

RICH_REPO = FIXTURES_DIR / "rich-repo"
THIN_REPO = FIXTURES_DIR / "thin-repo"
DEV_TOOL_REPO = FIXTURES_DIR / "dev-tool-repo"
UNFILLED_API_REPO = FIXTURES_DIR / "unfilled-api-repo"
SECRET_REPO = FIXTURES_DIR / "secret-repo"
OVERSIZED_REPO = FIXTURES_DIR / "oversized-repo"

# Ensure the scripts directory is on sys.path so unit test modules can import the skill's own
# modules directly (product_profile, audience_filter, content_contract, budget, render,
# secret_gate, md_parse, discovery) the same way build-llms-skeleton.py does.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def stage_fixture(tmp_path: Path, fixture_dir: Path) -> Path:
    """Copy a fixture repo into `tmp_path` and return the copy's path.

    `discovery.collect_markdown()` excludes any file whose path has a component matching
    `EXCLUDE_DIRS` (which includes "tests" and "fixtures") — matched against the file's
    ABSOLUTE path, not the path relative to the scanned `--source` root. Our fixtures live
    under `scripts/tests/fixtures/...`, so invoking the CLI with `--source` pointed directly
    at a fixture there would have "tests" and "fixtures" as ANCESTOR components of every
    discovered file's absolute path, and discovery would silently find nothing — not because
    the fixture is wrong, but because of where the checked-out repo happens to sit. Staging a
    copy under `tmp_path` (which carries no such component) sidesteps that incidental
    interaction without touching production code or weakening any assertion; see the dogfood
    report for the finding recorded against discovery.py itself."""
    dest = tmp_path / fixture_dir.name
    shutil.copytree(fixture_dir, dest)
    return dest


def run_script(args, cwd=None):
    """Run build-llms-skeleton.py as a subprocess of THIS interpreter (so a py3.9 test run
    exercises the script under py3.9 too). Returns (returncode, manifest_or_None, stdout, stderr).
    `manifest` is parsed from stdout only when the run asked for `--manifest -` (the default) and
    stdout is valid JSON; callers that redirect the manifest elsewhere get None and read stdout
    themselves."""
    cmd = [sys.executable, str(BUILD_SCRIPT), *args]
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    manifest = None
    if proc.stdout.strip():
        try:
            manifest = json.loads(proc.stdout)
        except json.JSONDecodeError:
            manifest = None
    return proc.returncode, manifest, proc.stdout, proc.stderr


def run_for_manifest(source: Path, output: Path, *extra_args):
    """Convenience: run against `source`, staging into `output`, and return the manifest dict.
    Asserts the run succeeded (exit 0) and produced parseable JSON — callers that need to assert
    a non-zero exit or unparsed stdout should call `run_script` directly instead."""
    code, manifest, out, err = run_script(
        ["--source", str(source), "--output", str(output), "--manifest", "-", *extra_args]
    )
    assert code == 0, f"run failed (exit {code}): {err}"
    assert manifest is not None, f"manifest did not parse from stdout: {out!r}"
    return manifest
