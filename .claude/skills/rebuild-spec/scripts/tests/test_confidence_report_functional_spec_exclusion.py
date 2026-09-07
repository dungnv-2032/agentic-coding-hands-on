"""Regression guard: A1 confidence-report scope excludes functional-spec.md (v27.0.0).

`references/confidence-report-contract.md` documents that A1 (`derive_confidence_report.py`)
runs on `technical-spec.md` ONLY within a v27 feature dir -- `functional-spec.md` (BA/QA prose)
is explicitly OUT of the citation-coverage denominator (see contract section "v27.0.0 -- A1
scope"). `derive_confidence_report.py` itself has NO artifact enumeration: it takes exactly one
`--artifact` path per invocation (see its `main()`), so the decision of *which* file in a
feature dir gets a companion is made entirely by the calling orchestration PROSE. This makes the
exclusion PROSE-driven, not code-driven -- confirmed by reading `derive_confidence_report.py` (no
allow/deny list of artifact names anywhere in it). The regression guard therefore parses that
prose rather than asserting against a Python-level constant.

Phase-04 (plans/260818-0758-rebuild-spec-post-migration-completion) widened this guard: a second
real call site (`references/pipeline-migrate.md`, the A1 confidence-report refresh) was added
alongside the original `references/pipeline-feature-specs.md` FS.7 loop. A guard hardcoded to one
path would silently stop covering the second the moment it existed -- exactly the failure this
phase's own plan warns about. So discovery now SCANS every `references/*.md` file for a real A1
call site (one with an extractable `--artifact` target), rather than naming files by hand -- and
carries its own vacuity assertion: a scan that silently finds zero call sites protects nothing,
so an empty discovery result MUST fail the check, never pass it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from derive_confidence_report import derive  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[5]  # agent-kit/
REFERENCES_DIR = REPO_ROOT / "claude/skills/rebuild-spec/references"

# The real call sites this guard is known to protect today. Used only as the vacuity
# assertion's minimum expectation (Requirement 5 / Test Matrix "vacuity probe") -- the
# discovery mechanism itself never hardcodes these as the search target, only checks
# afterward that scanning the real tree actually found (at least) them.
_KNOWN_CALL_SITES = ("pipeline-feature-specs.md", "pipeline-migrate.md")

# Matches the `--artifact ${docs_root}/features/${fcode}/<file>.md` argument inside an A1
# confidence-report sidecar loop (e.g. pipeline-feature-specs.md's
# "// [v25.2.0] A1 confidence-report sidecar" block, or pipeline-migrate.md's
# "// [v27.2.0] A1 confidence-report refresh" block).
A1_ARTIFACT_ARG_RE = re.compile(
    r"--artifact\s+\$\{docs_root\}/features/\$\{fcode\}/([\w.-]+\.md)"
)


def extract_a1_feature_targets(pipeline_text: str) -> set[str]:
    """Return the set of feature-dir filenames an A1 loop passes to
    derive_confidence_report.py. Scoped to a small window after each line that mentions
    derive_confidence_report.py so an unrelated `--artifact` invocation elsewhere in the doc
    is never picked up.
    """
    targets: set[str] = set()
    lines = pipeline_text.splitlines()
    for i, line in enumerate(lines):
        if "derive_confidence_report.py" not in line:
            continue
        window = "\n".join(lines[i : i + 4])
        targets.update(A1_ARTIFACT_ARG_RE.findall(window))
    return targets


def discover_a1_call_sites(references_dir: Path) -> dict[str, set[str]]:
    """Scan every `*.md` directly under `references_dir` and return
    `{filename: extracted target basenames}` for files that carry a REAL A1 call site --
    i.e. `extract_a1_feature_targets` finds at least one `--artifact` target in it.

    Deliberately NOT "any file that mentions derive_confidence_report.py in passing prose" --
    many contract/researcher docs reference the script by name without invoking it (e.g.
    confidence-report-contract.md discusses it at length but is not itself a call site). Using
    mention-only discovery would make the vacuity assertion below trivially satisfiable by
    files that protect nothing, defeating its purpose.
    """
    call_sites: dict[str, set[str]] = {}
    if not references_dir.is_dir():
        return call_sites
    for path in sorted(references_dir.glob("*.md")):
        targets = extract_a1_feature_targets(path.read_text(encoding="utf-8"))
        if targets:
            call_sites[path.name] = targets
    return call_sites


def assert_a1_scope_excludes_functional_spec(pipeline_text: str) -> None:
    """The load-bearing single-file assertion: an A1 loop must target technical-spec.md
    ONLY. Reused by the negative probes (each feeds a single regressed file's text)."""
    targets = extract_a1_feature_targets(pipeline_text)
    assert targets == {"technical-spec.md"}, (
        "A1 confidence-report loop must target technical-spec.md only "
        f"(functional-spec.md is explicitly excluded); found {targets or '(none)'}"
    )


def assert_discovery_is_non_vacuous(
    call_sites: dict[str, set[str]],
    *,
    minimum: int = 2,
    required_files: tuple[str, ...] = _KNOWN_CALL_SITES,
) -> None:
    """The vacuity guard (Requirement 5 / Test Matrix "vacuity probe"): a scan that finds
    zero (or too few) call sites passes silently and protects nothing -- indistinguishable
    from a guard that was never wired up. MUST fail loudly instead."""
    assert len(call_sites) >= minimum, (
        f"A1 call-site discovery found {len(call_sites)} file(s), expected >= {minimum} -- "
        "a vacuous scan protects nothing"
    )
    missing = [f for f in required_files if f not in call_sites]
    assert not missing, f"A1 call-site discovery did not find expected file(s): {missing}"


class TestA1CallSiteDiscoveryAcrossAllReferenceFiles:
    """Discovery must actually scan the real tree, find both known call sites, and prove
    their combined target set is still exactly {technical-spec.md} -- the exact regression
    a second, unguarded call site (phase-04's own pipeline-migrate.md addition) would cause
    if the guard had stayed hardcoded to one path."""

    def test_discovery_is_non_vacuous_and_covers_known_call_sites(self):
        call_sites = discover_a1_call_sites(REFERENCES_DIR)
        assert_discovery_is_non_vacuous(call_sites)

    def test_union_of_all_discovered_call_sites_never_includes_functional_spec(self):
        """The guard's actual job: `functional-spec.md` must never appear in ANY
        discovered A1 call site, anywhere. This is NOT an assertion that
        `technical-spec.md` is the only legitimate target in the whole tree --
        `pipeline-test-cases.md` legitimately targets `test-cases.md` (a different,
        unrelated artifact family; its own pass, out of scope for this guard) and
        must not be misread as a regression here."""
        call_sites = discover_a1_call_sites(REFERENCES_DIR)
        union: set[str] = set().union(*call_sites.values()) if call_sites else set()
        assert "functional-spec.md" not in union, (
            "functional-spec.md must never be an A1 target in any reference file "
            f"(phase-00 CORRECTION 1); discovered targets: {union}"
        )

    def test_known_technical_spec_call_sites_target_technical_spec_only(self):
        """The narrower, precise claim for the two call sites this guard is specifically
        about: each targets technical-spec.md and NOTHING else."""
        call_sites = discover_a1_call_sites(REFERENCES_DIR)
        for filename in _KNOWN_CALL_SITES:
            assert call_sites.get(filename) == {"technical-spec.md"}, (
                f"{filename} must target technical-spec.md only; found "
                f"{call_sites.get(filename) or '(not discovered)'}"
            )


class TestVacuityProbeCannotPassOnAnEmptyScan:
    """Requirement 5's own test: pointing discovery at a directory with no matching call
    sites must make the guard FAIL, not silently pass. A guard that never fires on an
    empty result is the same failure class as a fixture synthesizing the producer's own
    signal -- it looks green forever and catches nothing."""

    def test_discovery_on_empty_directory_yields_no_call_sites(self, tmp_path):
        assert discover_a1_call_sites(tmp_path) == {}

    def test_empty_discovery_fails_the_non_vacuous_assertion(self, tmp_path):
        call_sites = discover_a1_call_sites(tmp_path)
        with pytest.raises(AssertionError):
            assert_discovery_is_non_vacuous(call_sites)


class TestA1ScopeParsedFromRealPipeline:
    @pytest.mark.parametrize("filename", _KNOWN_CALL_SITES)
    def test_real_pipeline_file_excludes_functional_spec(self, filename):
        text = (REFERENCES_DIR / filename).read_text(encoding="utf-8")
        assert_a1_scope_excludes_functional_spec(text)

    @pytest.mark.parametrize("filename", _KNOWN_CALL_SITES)
    def test_end_to_end_only_technical_spec_gets_companion(self, filename, tmp_path):
        """Replay the ACTUAL parsed invocation from `filename` against a real v27
        feature-dir fixture and confirm only technical-spec.md gets a companion."""
        text = (REFERENCES_DIR / filename).read_text(encoding="utf-8")
        targets = extract_a1_feature_targets(text)
        assert targets, f"expected at least one A1 invocation target in {filename}"

        feature_dir = tmp_path / "F001_Sample"
        feature_dir.mkdir()
        (feature_dir / "technical-spec.md").write_text(
            "## Overview\n\n- A rule. **Source:** `app/models/user.rb:1-2`\n",
            encoding="utf-8",
        )
        (feature_dir / "functional-spec.md").write_text(
            "## 1. Overview\n\nPlain-language prose with no citations or markers.\n",
            encoding="utf-8",
        )

        for fname in targets:
            derive(feature_dir / fname)

        assert (feature_dir / "confidence-report_technical-spec.md").is_file()
        assert not (feature_dir / "confidence-report_functional-spec.md").is_file()


class TestNegativeProbeExclusionCannotSilentlyLapse:
    """Fixtures where the exclusion is removed must FAIL the check, so the exclusion cannot
    silently lapse in a future edit to EITHER real pipeline file -- one negative probe per
    known call site, so widening the guard to a second file doesn't halve its protection."""

    def test_regressed_pipeline_feature_specs_with_functional_spec_readded_is_caught(self):
        regressed_text = (
            "for (const fcode of resolvedTargetFcodes) {\n"
            "  bash: .claude/skills/.venv/bin/python3 \\\n"
            "    claude/skills/rebuild-spec/scripts/derive_confidence_report.py \\\n"
            "    --artifact ${docs_root}/features/${fcode}/technical-spec.md --project-root .\n"
            "  bash: .claude/skills/.venv/bin/python3 \\\n"
            "    claude/skills/rebuild-spec/scripts/derive_confidence_report.py \\\n"
            "    --artifact ${docs_root}/features/${fcode}/functional-spec.md --project-root .\n"
            "}\n"
        )
        with pytest.raises(AssertionError):
            assert_a1_scope_excludes_functional_spec(regressed_text)

    def test_regressed_pipeline_migrate_with_functional_spec_readded_is_caught(self):
        regressed_text = (
            "// [v27.2.0] A1 confidence-report refresh\n"
            "for (const fcode of resolvedTargetFcodes) {\n"
            "  bash: .claude/skills/.venv/bin/python3 \\\n"
            "    claude/skills/rebuild-spec/scripts/derive_confidence_report.py \\\n"
            "    --artifact ${docs_root}/features/${fcode}/technical-spec.md --project-root .\n"
            "  bash: .claude/skills/.venv/bin/python3 \\\n"
            "    claude/skills/rebuild-spec/scripts/derive_confidence_report.py \\\n"
            "    --artifact ${docs_root}/features/${fcode}/functional-spec.md --project-root .\n"
            "}\n"
        )
        with pytest.raises(AssertionError):
            assert_a1_scope_excludes_functional_spec(regressed_text)

    def test_extractor_detects_functional_spec_in_regressed_fixture(self):
        regressed_text = (
            "bash: .claude/skills/.venv/bin/python3 \\\n"
            "  claude/skills/rebuild-spec/scripts/derive_confidence_report.py \\\n"
            "  --artifact ${docs_root}/features/${fcode}/functional-spec.md --project-root .\n"
        )
        targets = extract_a1_feature_targets(regressed_text)
        assert "functional-spec.md" in targets
