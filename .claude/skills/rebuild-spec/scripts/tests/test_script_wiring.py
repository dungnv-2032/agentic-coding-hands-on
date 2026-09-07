"""Wiring guard — every entrypoint script must have a real caller.

WHY THIS EXISTS (2026-08-25, rebuild-spec 27.11.0-27.14.0)

Two scripts shipped in that wave fully built, fully unit-tested, and invoked by
NOTHING:

  * `build_traceability_matrix.py` — the flagship deliverable of its phase. The
    artifact it produces would never have existed after a real run.
  * `validate_deployment_view.py` — the release's only hard gate. A credential in
    a docker-compose could have reached a client bundle with no check firing.

A 4122-test green suite could not see either, because every unit test imports the
module and calls its functions directly. That proves the script WORKS. It says
nothing about whether anything ever RUNS it. Both were caught by human review, not
by the suite — which is precisely the gap this test closes.

WHAT COUNTS AS A CALLER

The pipeline is driven by an LLM orchestrator reading `references/*.md`. The only
form that reliably gets executed is a copy-pasteable full invocation path:

    claude/skills/rebuild-spec/scripts/<name>.py

Weaker mentions do NOT count, and the distinction is not academic — it is exactly
how both defects above hid:

  * a `verification-checklist-*.md` entry is an LLM READ, not a check. That was
    `validate_deployment_view.py`'s only reference, and it looked wired.
  * an `artifact-sharding.md` table cell names the validator that OWNS an artifact.
    It is a registry, not an invocation.
  * a `// Gate: bash <name>.py ...` comment is a comment. Two such comments existed
    against 150 real `bash:` invocations, and the command inside them was not even
    runnable (no venv interpreter, no full path). Both were promoted to real
    invocations on 2026-08-25.

So this test greps for the invocation path and nothing softer. Keeping the bar
there is the whole point: a softer pattern would have passed for both defects.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = SKILL_ROOT / "scripts"
REFERENCES = SKILL_ROOT / "references"
SKILL_MD = SKILL_ROOT / "SKILL.md"

# Entrypoint prefixes. `_`-prefixed modules are libraries imported by other scripts
# and are deliberately out of scope — their caller is an `import`, not a `bash:` line.
ENTRYPOINT_RE = re.compile(r"^(validate|build|check|migrate)_.*\.py$")

# Scripts with no invocation path today, each with the reason and what closing it
# requires. This allowlist is the honest part of the test: it is NOT permission to
# leave things unwired, it is a named backlog. Adding an entry is a deliberate act
# that shows up in review; forgetting to wire a NEW script is not — that fails.
#
# Full analysis: plans/reports/finding-260825-2110-entrypoint-scripts-without-callers.md
KNOWN_UNWIRED: dict[str, str] = {
    "check_layout_paths.py": (
        "Repo-hygiene guard, not a pipeline step: fails on a hardcoded docs/ path that "
        "lacks a layout-exempt annotation. Has tests. Genuinely runs NOWHERE — not in "
        ".github/workflows/, not .githooks/, not package.json, not Makefile. Needs a "
        "CI-vs-githook decision, which is a repo-level call outside rebuild-spec."
    ),
    "validate_api_map.py": (
        "Real validator with tests. Its only pipeline mention is a comment claiming it is "
        "'wired into W2.9 review' — there is no invocation. Needs a wave placement and a "
        "WARN/FAIL posture decision."
    ),
}

# Invoked from Python rather than from a pipeline `bash:` line. Their caller is real,
# it just is not a markdown invocation, so the grep below cannot see it.
PYTHON_INVOKED: dict[str, str] = {
    "check_promotion_gate.py": "called from check_translation_gate.py / derive_confidence_report.py",
}

# CORRECTED 2026-08-25: `validate_behavior_logic.py` was briefly excused here as Python-invoked.
# That excuse was WRONG and worth remembering — the "callers" only did
# `from validate_behavior_logic import BL_H2_RE` and a bare module import. Importing a regex
# constant out of a validator is not running the validator. It is now properly wired at both W2b
# behavior-logic gates. When classifying something as PYTHON_INVOKED, confirm the caller actually
# INVOKES it (calls validate()/main()), rather than merely importing a symbol from it.


def _entrypoints() -> list[str]:
    return sorted(p.name for p in SCRIPTS.glob("*.py") if ENTRYPOINT_RE.match(p.name))


def _invocation_corpus() -> str:
    """Every place an orchestrator could read a command from."""
    chunks = [SKILL_MD.read_text(encoding="utf-8", errors="replace")]
    chunks += [p.read_text(encoding="utf-8", errors="replace") for p in sorted(REFERENCES.rglob("*.md"))]
    return "\n".join(chunks)


@pytest.fixture(scope="module")
def corpus() -> str:
    return _invocation_corpus()


def _has_invocation(script: str, corpus: str) -> bool:
    return f"rebuild-spec/scripts/{script}" in corpus


class TestEveryEntrypointHasACaller:
    def test_at_least_one_entrypoint_discovered(self) -> None:
        """Guard the guard: a broken glob would make every assertion below vacuous."""
        assert len(_entrypoints()) >= 25, _entrypoints()

    @pytest.mark.parametrize("script", _entrypoints())
    def test_script_is_invoked_or_explicitly_excused(self, script: str, corpus: str) -> None:
        if script in KNOWN_UNWIRED or script in PYTHON_INVOKED:
            pytest.skip(f"excused: {(KNOWN_UNWIRED | PYTHON_INVOKED)[script][:60]}...")
        assert _has_invocation(script, corpus), (
            f"{script} has no `claude/skills/rebuild-spec/scripts/{script}` invocation in "
            f"SKILL.md or references/**.md.\n\n"
            f"A script nothing invokes is dead weight at best and a phantom gate at worst — "
            f"this exact defect shipped twice in the 27.11-27.14 wave past a fully green suite.\n\n"
            f"Fix it, do not silence it:\n"
            f"  1. add a `bash:` invocation at the pipeline wave where it belongs, using the "
            f"full path and the venv interpreter (copy the shape from W1.1's route-list gate "
            f"in references/pipeline-w0-w5.md); or\n"
            f"  2. if it is genuinely not a pipeline step, add it to KNOWN_UNWIRED with a "
            f"reason and what closing it requires; or\n"
            f"  3. if it is dead, delete it AND add the path to claude/metadata.json's "
            f"`deletions` array, per CLAUDE.md."
        )


class TestAllowlistStaysHonest:
    """An allowlist rots into a rug. These keep it swept."""

    @pytest.mark.parametrize("script", sorted(KNOWN_UNWIRED))
    def test_allowlisted_script_still_exists(self, script: str) -> None:
        """A deleted script must leave the allowlist, or the list becomes fiction."""
        assert (SCRIPTS / script).is_file(), (
            f"{script} is in KNOWN_UNWIRED but no longer exists — remove the entry."
        )

    @pytest.mark.parametrize("script", sorted(KNOWN_UNWIRED))
    def test_allowlisted_script_is_still_unwired(self, script: str, corpus: str) -> None:
        """The happy failure: someone wired it. Remove it from the list and enforce it."""
        assert not _has_invocation(script, corpus), (
            f"{script} now HAS an invocation — remove it from KNOWN_UNWIRED so the wiring is "
            f"enforced from here on."
        )

    @pytest.mark.parametrize("script", sorted(PYTHON_INVOKED))
    def test_python_invoked_caller_still_exists(self, script: str) -> None:
        """Its excuse is a Python caller; if that vanished, the excuse did too."""
        stem = script[:-3]
        callers = [
            p for p in SCRIPTS.glob("*.py")
            if p.name != script and stem in p.read_text(encoding="utf-8", errors="replace")
        ]
        assert callers, (
            f"{script} is excused as Python-invoked but no other script references it — "
            f"re-classify it (wire it, allowlist it, or delete it)."
        )

    @pytest.mark.parametrize("script", sorted(KNOWN_UNWIRED))
    def test_every_excuse_names_what_closing_it_requires(self, script: str) -> None:
        """A reason that does not say what to do next is a shrug, not a reason."""
        reason = KNOWN_UNWIRED[script]
        assert len(reason) > 80, f"{script}: reason too thin to act on"
        assert "Needs" in reason or "decision" in reason or "call" in reason, (
            f"{script}: reason must name the decision required to close it"
        )


class TestChecklistClaimsAreTrue:
    """A `(pre-W7a)` label is a PROMISE to the W7a reviewer, and a dangerous one.

    The verification checklists mark some rule_ids `[deterministic-pass]`, meaning "a deterministic
    step already checked this — skip it and spend your attention on semantic depth". When the named
    validator is not actually invoked anywhere, that label is worse than an unwired script: the
    script does not run AND the human review meant to compensate is switched off. Nothing is
    checking those rule_ids at all, and the checklist says that is fine.

    Found on 2026-08-25 in exactly that state:
      * `validate_screen_flow.py`   — labelled "(pre-W7a)", invoked nowhere.
      * `validate_behavior_logic.py`— labelled "(pre-W7a)", invoked nowhere. Its only Python
        "callers" imported a regex constant out of it, which is not running a validator.
    Both are now wired at real gates. This test keeps the promise honest from here on.
    """

    CLAIM_RE = re.compile(r"Deterministic checks[^:]*?`(validate_[a-z0-9_]+)\.py`")

    def _claims(self) -> dict[str, list[str]]:
        """Map validator -> checklist files that promise it already ran."""
        out: dict[str, list[str]] = {}
        for f in sorted(REFERENCES.glob("verification-checklist-*.md")):
            for m in self.CLAIM_RE.finditer(f.read_text(encoding="utf-8", errors="replace")):
                out.setdefault(f"{m.group(1)}.py", []).append(f.name)
        return out

    def test_claims_were_actually_found(self) -> None:
        """Guard the guard: a regex that matches nothing would make this class vacuous, which is
        the same class of bug it exists to catch."""
        claims = self._claims()
        assert len(claims) >= 7, f"expected the checklists to promise >=7 validators, got {claims}"

    def test_every_promised_validator_is_really_invoked(self, corpus: str) -> None:
        unbacked = {
            script: files for script, files in self._claims().items()
            if not _has_invocation(script, corpus)
        }
        assert not unbacked, (
            "A verification checklist promises these validators already ran, but nothing invokes "
            f"them: {unbacked}\n\n"
            "That label tells the W7a reviewer to mark those rule_ids [deterministic-pass] and skip "
            "them, so the rules end up checked by NOBODY. Either wire the validator at the wave the "
            "label names, or delete the label so the reviewer checks those rules semantically. Do "
            "not leave the promise standing."
        )

    def test_promised_validators_are_not_merely_allowlisted(self) -> None:
        """A checklist promise and a KNOWN_UNWIRED excuse are contradictory: one says the check
        already ran, the other says nothing runs it. Reconcile, do not hold both."""
        both = sorted(set(self._claims()) & (set(KNOWN_UNWIRED) | set(PYTHON_INVOKED)))
        assert not both, (
            f"{both} are promised as deterministic pre-checks by a verification checklist AND "
            f"excused as unwired/Python-invoked. Pick one: wire it and drop the excuse, or drop the "
            f"checklist label."
        )


class TestDetectorPrecision:
    """The detector must not be gameable, and must not be so loose it proves nothing.

    Both defects in the 27.11-27.14 wave were mentioned in markdown — just not as
    invocations. If a checklist or table mention satisfied this test, it would have
    passed for both, which is the failure mode being guarded against.
    """

    @pytest.mark.parametrize("script", [
        "validate_route_list.py",       # bash: in pipeline-w0-w5.md, exit-1 HALT
        "validate_deployment_view.py",  # bash: at W9.5a (fixed in this wave)
        "build_traceability_matrix.py", # bash: at W9.5b (fixed in this wave)
        "build_navigation.py",          # bash: at W9.6 and elsewhere
    ])
    def test_known_wired_controls_are_detected(self, script: str, corpus: str) -> None:
        """Positive controls: if these ever fail, the detector broke, not the wiring."""
        assert _has_invocation(script, corpus), f"detector regression: {script} IS wired"

    def test_a_weak_mention_alone_does_not_count(self, corpus: str) -> None:
        """Negative control, pinned to a real file. `validate_api_map.py` is named in an
        artifact-sharding table cell, and `pipeline-w0-w5.md` even carries a comment claiming it is
        "wired into W2.9 review" — yet no invocation exists. If this ever passes, the detector went
        soft and would no longer catch the defect class it was built for.

        Repointed 2026-08-25: this control used to be pinned to `validate_screen_flow.py`, which has
        since been genuinely wired. A negative control must track a still-unwired script or it
        quietly stops testing anything."""
        assert "validate_api_map.py" in corpus, "fixture drift: expected the weak mention to exist"
        assert not _has_invocation("validate_api_map.py", corpus), (
            "validate_api_map.py now resolves as invoked — either it was genuinely wired (remove it "
            "from KNOWN_UNWIRED and repoint this control at another still-unwired script) or the "
            "detector started accepting mere mentions, which would have passed for both wave defects."
        )
