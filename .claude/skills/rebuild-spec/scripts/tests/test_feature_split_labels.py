#!/usr/bin/env python3
"""Integrity of the committed feature-split label fixture + the rule scorer over it.

NO `skipif` ON A FIXTURE PATH IN THIS FILE, DELIBERATELY. This repo has already shipped the
opposite: `test_run_doc_migrations_cli.py` once pinned a hardcoded `/tmp/<session-uuid>`
scratch path behind a file-level `pytest.mark.skipif`, so when the directory vanished the
23 load-bearing tests turned into 23 silent skips and the suite still reported green. The
fixture these tests read is committed to git; if it is missing that is a defect, and these
tests must go RED, never yellow.

The labels here are NOT a gold standard and the tests must not imply otherwise -- see
`labels.json` -> `provenance` (n=18, Fleiss kappa 0.481, deliberately enriched sample).
What is pinned below is that the fixture says what it said on 2026-08-20, so a later change
to a rule cannot silently move the yardstick it is judged by.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent
_FIXTURE = _SCRIPTS / "tests" / "fixtures" / "corpora" / "feature-split-labels"
_MEASURE = _SCRIPTS / "measure_feature_split_rules.py"

# Frozen 2026-08-20: 3 blind labelers, majority vote, 5 calls adjudicated by the user
# (none of which overturned the majority).
_EXPECTED_SPLIT = {"F001", "F006", "F020", "F030", "F034",
                   "F041", "F046", "F048", "F058", "F063"}
_EXPECTED_N = 18
_EXPECTED_UNANIMOUS = 11


@pytest.fixture(scope="module")
def labels() -> dict:
    path = _FIXTURE / "labels.json"
    assert path.is_file(), (
        f"label fixture missing: {path}. This is a FAILURE, not a skip -- the fixture is "
        "committed to git precisely so it cannot vanish."
    )
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def metrics() -> dict:
    path = _FIXTURE / "feature-metrics.json"
    assert path.is_file(), f"metrics fixture missing: {path}"
    return json.loads(path.read_text())


def test_final_split_set_is_frozen(labels: dict) -> None:
    assert set(labels["final_split"]) == _EXPECTED_SPLIT


def test_label_shape_and_counts(labels: dict) -> None:
    feats = labels["features"]
    assert len(feats) == _EXPECTED_N
    unanimous = sum(1 for r in feats.values() if r["unanimous"])
    assert unanimous == _EXPECTED_UNANIMOUS
    for fcode, row in feats.items():
        assert set(row["votes"]) == {"A", "B", "C"}, fcode
        assert set(row["votes"].values()) <= {"KEEP", "SPLIT"}, fcode
        # `final` is the adjudicated call when one exists, else the majority.
        assert row["final"] == (row["adjudicated"] or row["majority"]), fcode


def test_majority_matches_votes(labels: dict) -> None:
    """The recorded majority is recomputed here rather than trusted."""
    for fcode, row in labels["features"].items():
        splits = list(row["votes"].values()).count("SPLIT")
        assert row["majority"] == ("SPLIT" if splits >= 2 else "KEEP"), fcode


def test_provenance_records_its_own_limitations(labels: dict) -> None:
    """A label set that hides its uncertainty gets quoted as fact. Pin the disclosures."""
    prov = labels["provenance"]
    assert prov["fleiss_kappa"] == pytest.approx(0.481)
    assert prov["sample_is_enriched"] is True
    assert prov["enrichment_warning"]
    assert prov["adjudications_overturning_majority"] == []
    assert "cap.promote_candidate" in prov["blind_to"]


def test_packets_carry_no_client_name() -> None:
    """The corpora README's Security scrub rule, enforced rather than asserted in prose."""
    packets = (_FIXTURE / "packets.md").read_text()
    assert not re.search(r"sharetribe", packets, re.I)


def test_packets_have_no_credential_or_email_shapes() -> None:
    packets = (_FIXTURE / "packets.md").read_text()
    assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", packets)
    assert not re.search(r"BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}", packets)


def test_every_labelled_feature_has_metrics(labels: dict, metrics: dict) -> None:
    missing = set(labels["features"]) - set(metrics)
    assert not missing, f"labelled features with no metric row: {sorted(missing)}"


def test_superseded_rule_is_recorded_as_failing() -> None:
    """The rule the earlier plan would have shipped scored 60%/30%.

    Pinned so the failure stays a measurement in the repo rather than folklore in a report.
    """
    out = subprocess.run([sys.executable, str(_MEASURE), "--json"],
                         capture_output=True, text=True, check=True)
    results = json.loads(out.stdout)["results"]
    superseded = results["SUPERSEDED #CAP>=2 & row(US>=3,SCR>=1)"]
    assert superseded["precision"] == pytest.approx(0.60)
    assert superseded["recall"] == pytest.approx(0.30)


def test_chosen_screen_has_full_recall_and_is_pre_spec() -> None:
    """`US>=5 OR BL>=8` is the screen phase 01 ships: recall is what a screen owes.

    Precision is the judge's job, so it is NOT asserted here -- only recorded by the scorer.
    """
    out = subprocess.run([sys.executable, str(_MEASURE), "--json"],
                         capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)
    screen = data["results"]["US>=5 OR BL>=8"]
    assert screen["pre_spec"] is True
    assert screen["recall"] == pytest.approx(1.0)
    assert screen["missed"] == []
    assert screen["corpus_fires"] == 17


def test_cap_rules_are_marked_unusable_pre_spec() -> None:
    """CAP scores well but § 2 does not exist before FS.1.

    If someone later flips one of these to pre_spec=True, this test fails and they have to
    justify how CAP became available at W5.
    """
    out = subprocess.run([sys.executable, str(_MEASURE), "--json"],
                         capture_output=True, text=True, check=True)
    results = json.loads(out.stdout)["results"]
    for name, row in results.items():
        if name.startswith("CAP>="):
            assert row["pre_spec"] is False, name
