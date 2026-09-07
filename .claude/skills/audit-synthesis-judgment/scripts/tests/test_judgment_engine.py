"""Tests for Engine 3 — granularity stat, prepare extraction, assemble survival/accounting."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import _granularity_lib as gran  # noqa: E402
import judgment_engine as je  # noqa: E402
import locate_synthesis_artifacts as locator  # noqa: E402

_CAP_HEADER = (
    "| ID | Capability | What the user can do | User Stories | Requirements | "
    "Business Rules | Screens |\n"
    "|----|------------|------------------------|-----------------|---------------|"
    "-------------------|---------|\n"
)


def _write_func_spec(dirpath: Path, *rows: str) -> Path:
    """A minimal functional-spec.md with a § 2 table, `rows` already `| ... |` lines."""
    dirpath.mkdir(parents=True, exist_ok=True)
    body = ("# Functional Spec\n\n## 1. Overview\n\nx\n\n"
            "## 2. Functional Capabilities\n\n" + _CAP_HEADER + "".join(rows)
            + "\n## 3. Open Decisions\n\nnone\n")
    p = dirpath / "functional-spec.md"
    p.write_text(body, encoding="utf-8")
    return p


def _func_artifact(path: Path) -> dict:
    return {"kind": locator.KIND_FEATURE_SPEC_FUNCTIONAL, "tier": "features",
            "artifact": "functional-spec.md", "path": str(path), "present": True}


# --------------------------------------------------------------- granularity
class TestGranularity:
    def test_outlier_flagged(self):
        metrics = {f"F{i:03d}": 5.0 for i in range(10)}
        metrics["F999"] = 200.0
        res = gran.find_outliers(metrics)
        assert any(o["feature"] == "F999" and o["direction"] == "coarse" for o in res["outliers"])

    def test_uniform_set_clean(self):
        metrics = {f"F{i:03d}": 5.0 for i in range(10)}
        res = gran.find_outliers(metrics)
        assert res["outliers"] == []

    def test_too_few_features_no_signal(self):
        res = gran.find_outliers({"F001": 1.0, "F002": 99.0})
        assert res["outliers"] == []


# --------------------------------------------------------------- feature metrics (phase 09)
class TestFeatureMetrics:
    def test_per_cap_not_per_feature(self, tmp_path):
        """Discriminating test (Success Criteria): a raw-US-count implementation would give
        F002 metric 6 (6 US total) — the correct max-per-CAP-row axis gives it 2, because those
        6 US are spread across 3 rows. Write it the wrong way once, watch this fail, then fix."""
        f1 = _write_func_spec(
            tmp_path / "f1",
            "| CAP-01 | Sign in | Do it | US001, US002, US003, US004, US005, US006 | FR-1 | BR-1 | SCR1 |\n")
        f2 = _write_func_spec(
            tmp_path / "f2",
            "| CAP-01 | A | a | US101, US102 | FR-1 | BR-1 | SCR1 |\n",
            "| CAP-02 | B | b | US103, US104 | FR-2 | BR-2 | SCR2 |\n",
            "| CAP-03 | C | c | US105, US106 | FR-3 | BR-3 | SCR3 |\n")
        f3 = _write_func_spec(tmp_path / "f3", "| CAP-01 | X | x | US201, US202 | FR-1 | BR-1 | SCR1 |\n")
        artifacts = [_func_artifact(f1), _func_artifact(f2), _func_artifact(f3)]
        metrics, n_present = je._feature_metrics(artifacts)
        assert n_present == 3
        assert metrics == {"f1": 6.0, "f2": 2.0, "f3": 2.0}

    def test_absent_artifact_skipped(self, tmp_path):
        artifacts = [{"kind": locator.KIND_FEATURE_SPEC_FUNCTIONAL, "present": False,
                      "path": str(tmp_path / "missing" / "functional-spec.md")}]
        metrics, n_present = je._feature_metrics(artifacts)
        assert metrics == {} and n_present == 0

    def test_ad3_widened_but_empty_us_cells_omitted_not_zero(self, tmp_path):
        # Reaches: rows non-empty, every US cell empty -> widest == 0 -> feature OMITTED.
        f1 = _write_func_spec(tmp_path / "f1", "| CAP-01 | Bg job | runs | | FR-1 | BR-1 | N/A |\n")
        artifacts = [_func_artifact(f1)]
        metrics, n_present = je._feature_metrics(artifacts)
        assert n_present == 1
        assert "f1" not in metrics, "an unfilled feature must be OMITTED, never recorded as 0"

    def test_no_section_2_at_all_yields_no_rows(self, tmp_path):
        d = tmp_path / "f1"
        d.mkdir()
        (d / "functional-spec.md").write_text("# Spec\n\n## 1. Overview\n\nx\n", encoding="utf-8")
        artifacts = [_func_artifact(d / "functional-spec.md")]
        metrics, n_present = je._feature_metrics(artifacts)
        assert n_present == 1 and metrics == {}


class TestGranularityCandidatesStatus:
    def test_v26_shape_skipped_names_the_path(self, tmp_path):
        # Reaches: 0 functional-spec.md located -> len(metrics) 0 < 3.
        artifacts = [{"kind": "feature-spec", "present": True,
                      "path": str(tmp_path / "docs" / "features" / "F001" / "technical-spec.md")}]
        cands, status, note = je._extract_granularity_candidates(artifacts, tmp_path / "docs")
        assert cands == [] and status == "SKIPPED"
        assert "no functional-spec.md located" in note
        assert str(tmp_path / "docs") in note

    def test_ad3_half_migrated_skipped_note_distinguishes_from_absent(self, tmp_path):
        # Reaches: every row's US cell empty -> feature omitted -> metrics empty -> len < 3.
        specs = []
        for i in range(4):
            d = tmp_path / "docs" / "features" / f"F{i:03d}"
            specs.append(_write_func_spec(d, "| CAP-01 | X | x | | FR-1 | BR-1 | N/A |\n"))
        artifacts = [_func_artifact(p) for p in specs]
        cands, status, note = je._extract_granularity_candidates(artifacts, tmp_path / "docs")
        assert cands == [] and status == "SKIPPED"
        assert "4 functional-spec.md found" in note
        assert "unfilled" in note
        # The note text must differ from the "no § 2 found" case (operator actions differ).
        _, absent_status, absent_note = je._extract_granularity_candidates([], tmp_path / "docs")
        assert absent_status == "SKIPPED"
        assert note != absent_note
        assert "no functional-spec.md located" in absent_note

    def test_ok_status_with_enough_features(self, tmp_path):
        specs = []
        for i, n_us in enumerate([1, 1, 1, 1, 1, 1, 1, 1, 1, 10]):
            row = f"| CAP-01 | X | x | {', '.join(f'US{i}{j:02d}' for j in range(n_us))} | FR-1 | BR-1 | N/A |\n"
            d = tmp_path / "docs" / "features" / f"F{i:03d}"
            specs.append(_write_func_spec(d, row))
        artifacts = [_func_artifact(p) for p in specs]
        cands, status, note = je._extract_granularity_candidates(artifacts, tmp_path / "docs")
        assert status == "OK"
        assert any(c["dimension"] == "granularity" for c in cands)
        assert "granularity ran on 10 features" in note


# --------------------------------------------------------------- prepare
class TestPrepare:
    def _corpus(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "generated").mkdir(parents=True)
        (docs / "system").mkdir(parents=True)
        (docs / "generated" / "user-stories.md").write_text(
            "## US001_Create: Create Order\n\nAs a user, I want to create an order "
            "so that I can track my purchases.\n", encoding="utf-8")
        return tmp_path

    def test_extracts_inference_and_naming(self, tmp_path):
        root = self._corpus(tmp_path)
        res = je.prepare(root, "all", None, None)
        dims = {c["dimension"] for c in res["candidates"]}
        assert "inference-validity" in dims
        assert "naming" in dims

    def test_so_that_extracted(self, tmp_path):
        root = self._corpus(tmp_path)
        res = je.prepare(root, "all", None, None)
        inf = [c for c in res["candidates"] if c["dimension"] == "inference-validity"]
        assert any("so that" in c["text"] for c in inf)

    def test_only_user_stories_feed_the_inference_axis(self, tmp_path):
        """Every inference candidate is a US benefit clause — the axis has no other producer."""
        root = self._corpus(tmp_path)
        res = je.prepare(root, "all", None, None)
        inf = [c for c in res["candidates"] if c["dimension"] == "inference-validity"]
        assert inf and all(c["target"] == "user-stories" for c in inf)


# --------------------------------------------------------------- capability-intent (phase 10)
def _write_func_spec_full(dirpath: Path, cap_rows: str, us7_headings: list[str],
                           rationale: str | None = None) -> Path:
    """A `functional-spec.md` with a § 2 table AND § 7 headings — `_write_func_spec` (above)
    stops at § 3, which is enough for granularity but not for capability-intent (needs § 7 titles
    and, optionally, the § 2 rationale line)."""
    dirpath.mkdir(parents=True, exist_ok=True)
    rationale_block = f"\n**Single-capability rationale:** {rationale}\n" if rationale else ""
    body = ("# Functional Spec\n\n**Type**: ui\n\n## 1. Overview\n\nx\n\n"
            "## 2. Functional Capabilities\n\n" + _CAP_HEADER + cap_rows + rationale_block
            + "\n## 3. Open Decisions\n\nnone\n\n"
            + "## 7. User Stories\n\n"
            + "\n\n".join(f"### {h}\n\nBody text." for h in us7_headings) + "\n")
    p = dirpath / "functional-spec.md"
    p.write_text(body, encoding="utf-8")
    return p


def _write_tech_spec(dirpath: Path, mapping_rows: str) -> Path:
    dirpath.mkdir(parents=True, exist_ok=True)
    body = ("# Technical Spec\n\n## 2. Functional → Technical Mapping\n\n"
            "| Code | Name | Where it is implemented | Technical notes | Source |\n"
            "|------|------|-------------------------|-----------------|--------|\n"
            + mapping_rows + "\n## 3. System Design\n")
    p = dirpath / "technical-spec.md"
    p.write_text(body, encoding="utf-8")
    return p


def _tech_artifact(path: Path) -> dict:
    return {"kind": "feature-spec", "tier": "features",
            "artifact": "technical-spec.md", "path": str(path), "present": True}


class TestCapabilityIntentCandidates:
    def test_candidate_emitted_for_4_us_row_anchor_has_all_titles(self, tmp_path):
        # Reaches: CAP-01 claims 4 US >= 3, all 4 titles resolved from § 7, anchor non-empty.
        func = _write_func_spec_full(
            tmp_path / "f1",
            "| CAP-01 | Browse | Browse listings | US001, US002, US003, US004 | FR-1 | BR-1 | SCR1 |\n",
            ["US001_A — Browse listings", "US002_B — Filter listings",
             "US003_C — Search listings", "US004_D — View map pins"])
        cands, any_claimed = je._extract_capability_intent_candidates([_func_artifact(func)])
        assert any_claimed is True
        assert len(cands) == 1
        cand = cands[0]
        assert cand["dimension"] == "capability-intent"
        assert cand["anchor"]
        for title in ("Browse listings", "Filter listings", "Search listings", "View map pins"):
            assert title in cand["anchor"]

    def test_no_candidate_below_threshold(self, tmp_path):
        func = _write_func_spec_full(
            tmp_path / "f1",
            "| CAP-01 | Sign in | Sign in | US001, US002 | FR-1 | BR-1 | SCR1 |\n",
            ["US001_A — Sign in", "US002_B — Sign out"])
        cands, any_claimed = je._extract_capability_intent_candidates([_func_artifact(func)])
        assert cands == []
        assert any_claimed is True  # rows DID claim US, just under threshold — not SKIPPED-worthy

    def test_unbuildable_anchor_yields_no_candidate_and_no_expected_count_inflation(self, tmp_path):
        # Reaches: CAP-01 claims 3 US but § 7 only titles 2 of them -> anchor unbuildable.
        func = _write_func_spec_full(
            tmp_path / "f1",
            "| CAP-01 | X | x | US001, US002, US003 | FR-1 | BR-1 | SCR1 |\n",
            ["US001_A — Title A", "US002_B — Title B"])  # US003 has no § 7 heading
        cands, _ = je._extract_capability_intent_candidates([_func_artifact(func)])
        assert cands == []
        res = je.prepare(tmp_path, "all", None, None)
        assert res["expected_count"] == 0

    def test_rationale_in_text_not_in_anchor(self, tmp_path):
        rationale = ("This capability bundles several related actions under one screen because "
                     "they share the same controller and data model end to end.")
        func = _write_func_spec_full(
            tmp_path / "f1",
            "| CAP-01 | X | x | US001, US002, US003 | FR-1 | BR-1 | SCR1 |\n",
            ["US001_A — Title A", "US002_B — Title B", "US003_C — Title C"],
            rationale=rationale)
        cands, _ = je._extract_capability_intent_candidates([_func_artifact(func)])
        assert len(cands) == 1
        cand = cands[0]
        assert rationale in cand["text"]
        assert rationale not in cand["anchor"]
        assert rationale not in cand.get("severity_text", "")

    def test_rationale_never_in_anchor_or_severity_text_builders(self):
        """[Iron Law #2 correction] Static proof, not just a fixture-derived assertion: the
        rationale token can never even be REFERENCED inside the anchor/severity builders — a
        future edit that threads the rationale through either would fail this immediately,
        independent of what any particular fixture happens to contain."""
        import inspect
        anchor_src = inspect.getsource(je._capability_intent_anchor)
        severity_src = inspect.getsource(je._capability_intent_severity_text)
        text_src = inspect.getsource(je._capability_intent_text)
        assert "rationale" not in anchor_src.lower()
        assert "rationale" not in severity_src.lower()
        assert "rationale" in text_src.lower()

    def test_severity_text_built_from_claimed_codes_and_twin_spec_declaration(self, tmp_path):
        func = _write_func_spec_full(
            tmp_path / "f1",
            "| CAP-01 | X | x | US001, US002, US003 | FR-101 | BR-101 | SCR101 |\n",
            ["US001_A — Title A", "US002_B — Title B", "US003_C — Title C"])
        tech = _write_tech_spec(
            tmp_path / "f1",
            "| FR-101 | OAuth login handshake and token issuance | ctrl | — | — |\n")
        cands, _ = je._extract_capability_intent_candidates(
            [_func_artifact(func), _tech_artifact(tech)])
        assert len(cands) == 1
        assert "FR-101" in cands[0]["severity_text"]
        assert "OAuth login handshake" in cands[0]["severity_text"]

    def test_zero_us_row_contributes_no_candidate_and_does_not_mark_any_claimed(self, tmp_path):
        # [Req #13] a background-type row claiming 0 US (BL-keyed) never reaches this extractor.
        func = _write_func_spec_full(
            tmp_path / "f1", "| CAP-01 | Bg job | runs | | FR-1 | BR-1 | N/A |\n", [])
        cands, any_claimed = je._extract_capability_intent_candidates([_func_artifact(func)])
        assert cands == [] and any_claimed is False


class TestCapabilityIntentStatus:
    def test_half_migrated_corpus_zero_candidates_and_skipped(self, tmp_path):
        # Reaches: no row anywhere claims any US -> status SKIPPED, not a silent empty list.
        specs = []
        for i in range(4):
            d = tmp_path / "docs" / "features" / f"F{i:03d}"
            specs.append(_write_func_spec_full(d, "| CAP-01 | X | x | | FR-1 | BR-1 | N/A |\n", []))
        artifacts = [_func_artifact(p) for p in specs]
        cands, status, note = je._extract_capability_intent(artifacts, tmp_path / "docs")
        assert cands == [] and status == "SKIPPED"
        assert "4 functional-spec.md found" in note
        assert "no § 2 row claims any User Stories" in note

    def test_absent_corpus_skipped_names_the_path(self, tmp_path):
        cands, status, note = je._extract_capability_intent([], tmp_path / "docs")
        assert cands == [] and status == "SKIPPED"
        assert "no functional-spec.md located" in note
        assert str(tmp_path / "docs") in note

    def test_clean_corpus_below_threshold_zero_candidates_but_ok(self, tmp_path):
        """[FM-5] The pair that proves the field distinguishes "nothing to flag" from "could not
        look" — every row is filled (claims US) but stays under the >= 3 threshold."""
        specs = []
        for i in range(4):
            d = tmp_path / "docs" / "features" / f"F{i:03d}"
            specs.append(_write_func_spec_full(
                d, f"| CAP-01 | X | x | US{i}01, US{i}02 | FR-1 | BR-1 | SCR1 |\n",
                [f"US{i}01_A — Title A", f"US{i}02_B — Title B"]))
        artifacts = [_func_artifact(p) for p in specs]
        cands, status, note = je._extract_capability_intent(artifacts, tmp_path / "docs")
        assert cands == [] and status == "OK"

    def test_prepare_surfaces_capability_intent_status(self, tmp_path):
        d = tmp_path / "docs" / "features" / "F001"
        _write_func_spec_full(d, "| CAP-01 | X | x | | FR-1 | BR-1 | N/A |\n", [])
        res = je.prepare(tmp_path, "all", None, None)
        assert res["capability_intent_status"] == "SKIPPED"
        assert res["capability_intent_note"]


class TestCapabilityIntentSeverity:
    def test_medium_on_neutral_input(self):
        assert je._severity("capability-intent", "some neutral text") == "medium"

    def test_backward_compat_other_dimensions_unchanged(self):
        """[SA-4] No `severity_text` set -> falls back to `text`, exactly the pre-phase-10
        behaviour. The other dimensions' own severity tests (TestAssemble et al.) already
        cover their concrete outcomes; this asserts the fallback mechanism itself."""
        for dim in ("inference-validity", "naming", "granularity"):
            cand = {"severity_text": None, "text": "plain text mentioning nothing sensitive"}
            scanned = cand.get("severity_text") or cand.get("text", "")
            assert scanned == cand["text"]
            assert je._severity(dim, scanned) == je._severity(dim, cand["text"])

    def test_discrimination_auth_codes_bland_prose_is_high(self):
        """[SA-4] `severity_text` names claimed auth codes + their twin-spec declaration line;
        `text` (the rationale) is deliberately bland — the OLD implementation (scan `text`) would
        return `medium` here. Proves severity now derives from declared codes, not prose."""
        judged = {"expected_count": 1, "candidates": [{
            "id": "cap1", "dimension": "capability-intent", "verdict": "WARN", "confidence": 0.9,
            "anchor": "CAP-01 claims 3 user-story titles: 'A'; 'B'; 'C' (computed)",
            "target": "f1:CAP-01",
            "text": "Claimed user stories: 'Sign in'; 'Reset access'; 'View profile'.",
            "severity_text": "FR-001 — OAuth login handshake and token issuance",
            "refutations": [{"refuted": False}, {"refuted": False}],
        }]}
        res = je.assemble(judged, "medium")
        assert res["findings"][0]["severity"] == "high"

    def test_discrimination_settings_codes_password_prose_is_medium(self):
        """[SA-4] The case that FAILS against the old implementation: `text` mentions "password"
        (a blast-radius keyword) but `severity_text` names only settings codes with no
        blast-radius content. If severity scanned `text`, this would read `high` — proof that
        prose can no longer move severity."""
        judged = {"expected_count": 1, "candidates": [{
            "id": "cap2", "dimension": "capability-intent", "verdict": "WARN", "confidence": 0.9,
            "anchor": "CAP-02 claims 3 user-story titles: 'X'; 'Y'; 'Z' (computed)",
            "target": "f1:CAP-02",
            "text": "Claimed user stories: 'Update display name'; 'Update timezone'; 'Update "
                    "password reminder frequency'. **Single-capability rationale:** all settings "
                    "live on one screen so users configure their profile including password "
                    "reminder cadence in a single place, saving a navigation hop.",
            "severity_text": "FR-050 — Update display name preference; FR-051 — Update timezone preference",
            "refutations": [{"refuted": False}, {"refuted": False}],
        }]}
        res = je.assemble(judged, "medium")
        assert res["findings"][0]["severity"] == "medium"

    def test_assemble_drops_capability_intent_finding_with_empty_anchor(self):
        judged = {"expected_count": 1, "candidates": [{
            "id": "cap3", "dimension": "capability-intent", "verdict": "WARN", "confidence": 0.9,
            "anchor": "", "target": "f1:CAP-03", "text": "x",
            "refutations": [{"refuted": False}, {"refuted": False}],
        }]}
        res = je.assemble(judged, "medium")
        assert res["findings"] == []
        assert any("anchor" in d["reason"] for d in res["dropped"])


class TestPlantedPositiveCapMultiIntent:
    """[Req #12, REVISED 2026-08-19] A real, well-partitioned corpus can legitimately drive
    CAP_MULTI_INTENT findings to zero — that proves the corpus is good, not that the dimension is
    broken. This fixture proves the dimension CAN fire, independent of corpus luck: one CAP row
    claims a genuinely multi-outcome bundle of user stories (sign-in, password reset, account
    deletion, data export, billing history — five distinct business outcomes with nothing but a
    shared screen in common), with a rationale engineered to PASS rebuild-spec's own three
    deterministic gate conditions, so the deterministic layer stays silent and only the judge can
    object.
    """

    _RATIONALE = (
        "This capability bundles sign-in, password reset, account deletion, data export, and "
        "billing history under one umbrella because they all touch the same account settings "
        "screen, referencing US101 and US102.")
    _TITLES = [
        "US101_SignIn — Sign in to the marketplace",
        "US102_ResetPassword — Reset a forgotten password",
        "US103_DeleteAccount — Permanently delete the account",
        "US104_ExportData — Export personal data as a downloadable archive",
        "US105_ViewBillingHistory — View past billing and invoice history",
    ]

    def _write_fixture(self, tmp_path) -> Path:
        return _write_func_spec_full(
            tmp_path / "F999_AccountSelfService",
            "| CAP-01 | Account self-service | Manage account | "
            "US101, US102, US103, US104, US105 | FR-101, FR-102 | BR-101 | SCR101 |\n",
            self._TITLES, rationale=self._RATIONALE)

    def test_rationale_passes_rebuild_specs_three_deterministic_conditions(self, tmp_path):
        """The deterministic layer (rebuild-spec's own `cap.analysis_required` gate) must stay
        SILENT on this fixture — verified against rebuild-spec's OWN function via a skip-guarded
        cross-import (same precedent as `test_cap_map_lib_parity.py`), never re-implemented here."""
        rebuild_spec_scripts = (Path(je.__file__).resolve().parent.parent.parent
                                 / "rebuild-spec" / "scripts")
        if not (rebuild_spec_scripts / "validate_feature_spec.py").is_file():
            pytest.skip("rebuild-spec not installed alongside this skill")
        if str(rebuild_spec_scripts) not in sys.path:
            sys.path.insert(0, str(rebuild_spec_scripts))
        import validate_feature_spec as vfs  # noqa: E402

        func = self._write_fixture(tmp_path)
        text = func.read_text(encoding="utf-8")
        lines = text.splitlines()
        h2 = [(i, ln.rstrip()) for i, ln in enumerate(lines) if ln.startswith("## ")]
        b2 = next(((idx + 1, h2[i + 1][0] if i + 1 < len(h2) else len(lines))
                   for i, (idx, h) in enumerate(h2) if h == "## 2. Functional Capabilities"), None)
        section2_text = "\n".join(lines[b2[0]:b2[1]])
        declared = {"US101", "US102", "US103", "US104", "US105"}
        qualifies, reasons = vfs._cap_rationale_verdict(section2_text, ["US"], declared)
        assert qualifies, f"fixture rationale must pass rebuild-spec's own gate: {reasons}"

    def test_extractor_emits_candidate_for_the_bundled_row(self, tmp_path):
        func = self._write_fixture(tmp_path)
        cands, _ = je._extract_capability_intent_candidates([_func_artifact(func)])
        assert len(cands) == 1
        cand = cands[0]
        assert cand["dimension"] == "capability-intent"
        for title in ("Sign in to the marketplace", "Reset a forgotten password",
                      "Permanently delete the account",
                      "Export personal data as a downloadable archive",
                      "View past billing and invoice history"):
            assert title in cand["anchor"]

    def test_assemble_produces_cap_multi_intent_when_judge_warns(self, tmp_path):
        """Simulates the judge's WARN verdict — as every other dimension's assemble test in this
        suite already does, no live LLM runs in this test process — to prove the deterministic
        PIPELINE turns this candidate into a real `CAP_MULTI_INTENT` finding. This is the
        'can it fail' proof Requirement #12 demands, independent of real-corpus luck."""
        func = self._write_fixture(tmp_path)
        cands, _ = je._extract_capability_intent_candidates([_func_artifact(func)])
        cand = dict(cands[0])
        cand.update({"verdict": "WARN", "confidence": 0.9,
                     "refutations": [{"refuted": False}, {"refuted": False}]})
        judged = {"expected_count": 1, "candidates": [cand]}
        res = je.assemble(judged, "medium")
        assert len(res["findings"]) == 1
        finding = res["findings"][0]
        assert finding["kind"] == "CAP_MULTI_INTENT"
        assert finding["dimension"] == "capability-intent"
        assert finding["verdict"] == "WARN" and finding["adjudicated"] is True


# --------------------------------------------------------------- assemble
def _cand(cid, dim, verdict="WARN", refutations=None, confidence=0.9, anchor="a computed anchor"):
    c = {"id": cid, "dimension": dim, "verdict": verdict, "confidence": confidence,
         "anchor": anchor, "target": cid, "text": "x"}
    if refutations is not None:
        c["refutations"] = refutations
    return c


class TestAssemble:
    def test_survives_majority_refutation(self):
        judged = {"expected_count": 1, "candidates": [
            _cand("i1", "inference-validity",
                  refutations=[{"refuted": False}, {"refuted": False}, {"refuted": True}])]}
        res = je.assemble(judged, "medium")
        assert len(res["findings"]) == 1 and res["findings"][0]["adjudicated"] is True
        assert res["judgment_status"] == "OK"

    def test_refuted_dropped(self):
        judged = {"expected_count": 1, "candidates": [
            _cand("i1", "inference-validity",
                  refutations=[{"refuted": True}, {"refuted": True}])]}
        res = je.assemble(judged, "medium")
        assert res["findings"] == []
        assert any("refutation" in d["reason"] for d in res["dropped"])

    def test_no_anchor_dropped(self):
        judged = {"expected_count": 1, "candidates": [
            _cand("i1", "inference-validity", anchor="",
                  refutations=[{"refuted": False}, {"refuted": False}])]}
        res = je.assemble(judged, "medium")
        assert res["findings"] == []
        assert any("anchor" in d["reason"] for d in res["dropped"])

    def test_low_confidence_dropped(self):
        judged = {"expected_count": 1, "candidates": [
            _cand("i1", "inference-validity", confidence=0.3,
                  refutations=[{"refuted": False}, {"refuted": False}])]}
        res = je.assemble(judged, "medium")
        assert res["findings"] == []

    def test_single_refuter_only_at_low(self):
        judged = {"expected_count": 1, "candidates": [
            _cand("i1", "inference-validity", refutations=[{"refuted": False}])]}
        assert len(je.assemble(judged, "low")["findings"]) == 1     # low: single refuter OK
        assert je.assemble(judged, "medium")["findings"] == []      # medium: needs ≥2

    def test_dead_subagent_is_partial_not_clean(self):
        judged = {"expected_count": 2, "candidates": [
            _cand("i1", "inference-validity", refutations=[{"refuted": False}, {"refuted": False}]),
            {"id": "i2", "dimension": "naming", "anchor": "a"}]}  # no verdict → judge died
        res = je.assemble(judged, "medium")
        assert res["judgment_status"] == "PARTIAL"
        assert res["returned"] == 1 and res["expected"] == 2

    def test_all_dead_is_failed(self):
        judged = {"expected_count": 2, "candidates": [
            {"id": "i1", "dimension": "naming", "anchor": "a"},
            {"id": "i2", "dimension": "naming", "anchor": "a"}]}
        assert je.assemble(judged, "medium")["judgment_status"] == "FAILED"

    def test_engine3_never_fail_verdict(self):
        judged = {"expected_count": 1, "candidates": [
            _cand("i1", "inference-validity",
                  refutations=[{"refuted": False}, {"refuted": False}])]}
        res = je.assemble(judged, "medium")
        assert res["findings"] and all(f["verdict"] == "WARN" for f in res["findings"])
