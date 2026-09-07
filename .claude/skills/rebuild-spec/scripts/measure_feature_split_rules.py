#!/usr/bin/env python3
"""Score candidate over-scope rules against the committed human/LLM feature-split labels.

WHY THIS EXISTS. The first version of this work reported a rule at "100% precision" --
measured against `cap.promote_candidate`, another unvalidated threshold rule. Two rules
agreeing tells you nothing about whether either is right; the second had been DERIVED from
the first by dropping a term, so the agreement was tautological. This script scores against
the labels in `fixtures/corpora/feature-split-labels/labels.json`, which were produced by
three blind independent labelers plus user adjudication -- the only non-circular yardstick
this repo has. Re-run it whenever a rule is proposed; never quote a precision figure that
did not come out of here.

READ THE LIMITATIONS BEFORE QUOTING ANY NUMBER (they are printed with every run):
  * n = 18, and the sample was DELIBERATELY ENRICHED across suspicion bands. Its 56% SPLIT
    rate is the sample's, never the corpus's. Precision on a random sample would be lower.
  * Fleiss kappa = 0.481 (moderate). The labels are not a gold standard; three competent
    labelers disagreed on 7 of 18.
  * Rules were searched against these same 18 labels, so the winner is partly fitted to
    them. Treat any figure here as an upper bound until validated on held-out features.

Usage:
    measure_feature_split_rules.py [--fixture-dir DIR] [--json]
"""
from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path

_DEFAULT_FIXTURE = Path(__file__).resolve().parent / "tests" / "fixtures" / "corpora" / "feature-split-labels"


def _load(fixture_dir: Path) -> tuple[dict, dict]:
    labels = json.loads((fixture_dir / "labels.json").read_text())
    metrics = json.loads((fixture_dir / "feature-metrics.json").read_text())
    return labels, metrics


# Candidate rules. Each maps a feature's metric row -> bool.
#
# `cap` is the § 2 Functional Capabilities row count. It is the single strongest signal
# measured (CAP>=5 scores 78%/70%) BUT IT DOES NOT EXIST BEFORE FS.1 -- § 2 is authored by
# the feature-spec pass. Any rule marked pre_spec=False therefore cannot run at the W5/W5.6
# gate this work targets, no matter how well it scores. Keeping them in the table is
# deliberate: it stops a future reader from "improving" the screen into something that
# cannot run where the screen runs.
# Callables, never expression strings fed to `eval`. The strings-plus-eval shape reads
# identically but leaves an execution path one refactor away from live: the moment someone
# plumbs a proposed rule in from a CLI flag, a review comment, or the very fixture JSON this
# module already reads at runtime, a dev-only measurement script becomes an injection vector.
RULES: dict[str, tuple[Callable[[dict], bool], bool]] = {
    # name: (predicate over the metric row, usable pre-spec?)
    "US>=5 OR BL>=8": (lambda m: m["us"] >= 5 or m["bl"] >= 8, True),
    "US>=5 OR BL>=5": (lambda m: m["us"] >= 5 or m["bl"] >= 5, True),
    "US>=4 OR BL>=6": (lambda m: m["us"] >= 4 or m["bl"] >= 6, True),
    "US>=4 AND SCR>=5": (lambda m: m["us"] >= 4 and m["scr"] >= 5, True),
    "US>=5": (lambda m: m["us"] >= 5, True),
    "CAP>=4": (lambda m: m["cap"] >= 4, False),
    "CAP>=5": (lambda m: m["cap"] >= 5, False),
    "CAP>=6": (lambda m: m["cap"] >= 6, False),
    "CAP>=5 OR US>=5": (lambda m: m["cap"] >= 5 or m["us"] >= 5, False),
}

# The rule the superseded plan was going to ship, kept so its failure stays visible rather
# than becoming folklore. It is not expressible over the metric row (it needs per-CAP-row
# claim counts), so it is pinned as the literal feature set it selects on this corpus.
_SUPERSEDED_RULE_FIRES = {"F015", "F018", "F020", "F030", "F048"}


def score(fired: set[str], truth: set[str], universe: set[str]) -> dict:
    fired = fired & universe
    tp, fp, fn = len(fired & truth), len(fired - truth), len(truth - fired)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"fires": len(fired), "tp": tp, "fp": fp, "fn": fn,
            "precision": prec, "recall": rec, "f1": f1,
            "missed": sorted(truth - fired), "false_alarms": sorted(fired - truth)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fixture-dir", type=Path, default=_DEFAULT_FIXTURE)
    ap.add_argument("--json", action="store_true", help="emit machine-readable results")
    args = ap.parse_args()

    labels, metrics = _load(args.fixture_dir)
    prov = labels["provenance"]
    labelled = set(labels["features"])
    truth = set(labels["final_split"])

    results = {}
    for name, (pred, pre_spec) in RULES.items():
        fired = {f for f in labelled if pred(metrics[f])}
        corpus_fires = sum(1 for m in metrics.values() if pred(m))
        results[name] = {**score(fired, truth, labelled),
                         "pre_spec": pre_spec,
                         "corpus_fires": corpus_fires,
                         "corpus_pct": corpus_fires / len(metrics)}
    results["SUPERSEDED #CAP>=2 & row(US>=3,SCR>=1)"] = {
        **score(_SUPERSEDED_RULE_FIRES, truth, labelled),
        "pre_spec": False, "corpus_fires": None, "corpus_pct": None}

    if args.json:
        print(json.dumps({"provenance": prov, "truth": sorted(truth),
                          "results": results}, indent=2))
        return 0

    print(f"labels: n={prov['n']}  SPLIT={len(truth)}  unanimous={prov['unanimous']}"
          f"  fleiss_kappa={prov['fleiss_kappa']}")
    print(f"adjudicated by user: {', '.join(prov['adjudicated_by_user'])}"
          f"  (overturning majority: {prov['adjudications_overturning_majority'] or 'none'})")
    print()
    print(f"{'rule':<42}{'pre':>4}{'fires':>6}{'prec':>7}{'rec':>6}{'F1':>6}{'/66':>6}")
    for name, r in sorted(results.items(), key=lambda kv: -kv[1]["f1"]):
        pre = "yes" if r["pre_spec"] else "NO"
        c = f"{r['corpus_fires']}" if r["corpus_fires"] is not None else "-"
        print(f"{name:<42}{pre:>4}{r['fires']:>6}{r['precision']:>6.0%}"
              f"{r['recall']:>6.0%}{r['f1']:>6.2f}{c:>6}")
    print()
    print("'pre' = usable before FS.1. A rule marked NO cannot run at the W5/W5.6 gate,")
    print("however well it scores -- § 2 (and therefore CAP) does not exist until FS.1.")
    print()
    print("LIMITATIONS -- quote no figure without them:")
    print(f"  * n={prov['n']}, sample DELIBERATELY ENRICHED. {prov['enrichment_warning']}")
    print(f"  * fleiss_kappa={prov['fleiss_kappa']} (moderate) -- labels are not a gold standard.")
    print("  * rules were searched against these same labels -> figures are an upper bound.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
