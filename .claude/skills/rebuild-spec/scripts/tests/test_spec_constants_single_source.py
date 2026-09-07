"""Guard: single-source constants introduced in Phase 00 (DRY prep) stay single-sourced.

Four guards, per phase-00-dry-prep-single-source.md step 5:
  (a) no file other than _slug_lib.py re-types the feature-file literal
      "business-context.md" inside a tuple/set/list literal (dict literals — e.g. the
      per-language file_purposes prose dicts, or _nav_lib._ARTIFACT_DESCRIPTIONS — are
      intentionally out of scope for this guard; they keep literal keys/values by design).
  (b) no file other than _spec_block_lib.py calls re.compile() on a BR/SM/ALG/INT
      block-heading pattern.
  (c) the 3 per-language file_purposes dicts contain (at least) the SATELLITE_FEATURE_FILES
      key set — a SUBSET check, never equality. technical-spec.md (not a satellite) and
      test-cases.md (an optional sidecar, not in FEATURE_FILES at all) are deliberately
      outside the guarded set (C-AD1).
  (d) no required-H2 list literal (REQUIRED_H2_TECH_THREAD / REQUIRED_H2_FUNC /
      _LEGACY_TECH_H2_5BUCKET) is re-typed as a matching tuple/list/set literal outside
      _spec_constants.py.
      (v27.0.0: REQUIRED_H2_BC/REQUIRED_H2_SCR retired — REQUIRED_H2_FUNC replaces both.)
      (rebuild-spec 27.7.0, phase 10: REQUIRED_H2_TECH retired as a public name — the
      current shape is REQUIRED_H2_TECH_THREAD, and _LEGACY_TECH_H2_5BUCKET is guarded
      too, since it still governs the migration pipeline's own internal parsing.)

Stdlib only (ast + re for source scanning). Scans scripts/*.py non-recursively only —
tests/ and fixtures/ are out of scope (Risk Assessment: guard brittleness).
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _slug_lib import SATELLITE_FEATURE_FILES  # noqa: E402
from _spec_constants import (  # noqa: E402
    REQUIRED_H2_FUNC, REQUIRED_H2_TECH_THREAD, _LEGACY_TECH_H2_5BUCKET,
)


def _script_files(exclude: str) -> list[Path]:
    """Every scripts/*.py file except `exclude` (non-recursive: skips tests/, fixtures/)."""
    return [p for p in sorted(SCRIPTS.glob("*.py")) if p.name != exclude]


def _literal_container_strings(tree: ast.AST) -> set[str]:
    """Every string constant that is an element of a Tuple/List/Set literal.

    Deliberately excludes ast.Dict — dict keys (e.g. file_purposes, _ARTIFACT_DESCRIPTIONS)
    are a different DRY target (guard c handles them via containment, not literal-freeze).
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            for elt in node.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    found.add(elt.value)
    return found


class TestFeatureFileLiteralSingleSource:
    """Guard (a) — FEATURE_FILES must not be re-typed as a tuple/list/set literal."""

    def test_business_context_md_only_in_slug_lib(self):
        offenders = []
        for path in _script_files("_slug_lib.py"):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError:
                continue
            if "business-context.md" in _literal_container_strings(tree):
                offenders.append(path.name)
        assert not offenders, (
            f"'business-context.md' re-typed inside a tuple/set/list literal in: {offenders}. "
            "Import _slug_lib.FEATURE_FILES / SATELLITE_FEATURE_FILES instead."
        )


_RE_COMPILE_STR_RE = re.compile(r"""re\.compile\(\s*r?(['"])(.*?)\1""")

# v27.0.0 (Phase 04): guard (b) widened after a silent-pass regression was found — two files
# (_flow_sm_lib.py, validate_test_cases.py) re-typed a heading-anchored BR/SM/DEC regex that
# matched only the RETIRED slug form; once the canonical heading moved to the v27.0.0 trailing-tag
# form, both regexes silently matched zero blocks (a pattern matching nothing reports nothing —
# the exact failure mode this guard exists to close), while the ORIGINAL guard below (substring
# match on the retired-form literals only) stayed green throughout, since neither offending pattern
# contained those exact substrings. The fix: also flag ANY heading-anchored pattern (starts with
# the markdown heading marker `^#`) that references a BR/SM/ALG/INT/DEC code family, regardless of
# which form (old or new) it re-types — single-sourcing must hold for the CONCEPT of a block
# heading, not just for one retired literal spelling of it.
#
# This intentionally does NOT flag inline code-token regexes that scan a citation/reference string
# rather than a heading line (no leading `^#`) — e.g. `CODE_FAMILY_RE`/`SM_REF_RE` (bare `SM-\d{3}`
# token detection in prose) or `_FUNC_RULE_TAG_RE`/`_TECH_CODE_RE`/`_ALG_BLOCK_TAG_RE` (trailing-tag
# detection on a functional-spec.md bullet line, not a technical-spec.md heading). Those are a
# legitimately different single-source concern, own by their respective files. DISC-### is also
# exempt — its format has always been a bare `DISC-###` (code-formats.md), with no retired
# anchored-slug form to guard against, and it is not part of _spec_block_lib's tracked family.
_CODE_FAMILY_TOKEN_RE = re.compile(r"BR|SM|ALG|INT|DEC")


class TestBlockHeadingRegexSingleSource:
    """Guard (b) — BR/SM/ALG/INT/DEC block-heading regexes must live only in _spec_block_lib.py."""

    def test_block_heading_patterns_only_in_spec_block_lib(self):
        offenders = []
        for path in _script_files("_spec_block_lib.py"):
            text = path.read_text(encoding="utf-8")
            for pattern in (m.group(2) for m in _RE_COMPILE_STR_RE.finditer(text)):
                is_legacy_slug_form = (
                    "(BR|SM|ALG|INT)-" in pattern
                    or "SM-\\d{3}_" in pattern
                    or "DEC-\\d{3}_" in pattern
                )
                is_heading_anchored_code_family = (
                    pattern.startswith("^#") and _CODE_FAMILY_TOKEN_RE.search(pattern)
                )
                if is_legacy_slug_form or is_heading_anchored_code_family:
                    offenders.append(path.name)
                    break
        assert not offenders, (
            "BR/SM/ALG/INT/DEC block-heading pattern re-compiled outside _spec_block_lib.py in: "
            f"{offenders}. Import the named constant from _spec_block_lib instead."
        )


class TestFilePurposesSubsetGuard:
    """Guard (c) — C-AD1: the 3 per-language file_purposes dicts must be a SUPERSET of
    (i.e. contain) SATELLITE_FEATURE_FILES — never an equality check. A guard written as
    equality fails on unmodified code (technical-spec.md/test-cases.md are also present
    as keys, deliberately outside the guarded set) and is rejected on that basis."""

    def test_file_purposes_key_sets_contain_satellite_files(self):
        from _nav_strings_en import STRINGS as STRINGS_EN  # noqa: E402
        from _nav_strings_ja import STRINGS as STRINGS_JA  # noqa: E402
        from _nav_strings_vi import STRINGS as STRINGS_VI  # noqa: E402

        for lang, strings in (("en", STRINGS_EN), ("ja", STRINGS_JA), ("vi", STRINGS_VI)):
            file_purposes = strings["feature_readme"]["file_purposes"]
            missing = set(SATELLITE_FEATURE_FILES) - file_purposes.keys()
            assert not missing, (
                f"_nav_strings_{lang}.py file_purposes is missing satellite key(s): {missing}"
            )


class TestRequiredH2ListSingleSource:
    """Guard (d) — REQUIRED_H2_TECH_THREAD / REQUIRED_H2_FUNC / _LEGACY_TECH_H2_5BUCKET
    must not be re-typed as a matching literal list/tuple/set of ## headings outside
    _spec_constants.py (red-team M-FM6: a vestigial copy must not be able to hide from
    this test)."""

    def test_required_h2_lists_not_duplicated(self):
        guarded_sets = {
            "REQUIRED_H2_TECH_THREAD": frozenset(REQUIRED_H2_TECH_THREAD),
            "REQUIRED_H2_FUNC": frozenset(REQUIRED_H2_FUNC),
            "_LEGACY_TECH_H2_5BUCKET": frozenset(_LEGACY_TECH_H2_5BUCKET),
        }
        offenders = []
        for path in _script_files("_spec_constants.py"):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Tuple, ast.List, ast.Set)):
                    continue
                values = [
                    elt.value for elt in node.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
                if not values or len(values) != len(node.elts):
                    continue  # not a pure string-literal container
                literal_set = frozenset(values)
                for name, guarded in guarded_sets.items():
                    if literal_set == guarded:
                        offenders.append(f"{path.name}: duplicates {name}")
        assert not offenders, (
            f"Required-H2 list literal re-typed outside _spec_constants.py: {offenders}"
        )
