"""Unit tests for audience_filter.py — table-driven, one row per keep/drop/conditional rule from
the phase-02 audience table. Operates on synthetic file dicts (no disk I/O needed: `apply()`
only reads `rel`/`title`), matching the described "table-driven classification" test shape.
"""
import audience_filter

# (rel, surfaces, expected bucket) — bucket in {"kept", "dropped", "unmatched"}.
# "unmatched" implies "dropped" too (fail-closed), but is also asserted in dropped_unmatched.
CASES = [
    ("docs/user-guide/install.md", [], "kept"),
    ("getting-started.md", [], "kept"),
    ("docs/user-guide/anything.md", [], "kept"),
    ("docs/contributing.md", [], "dropped"),
    ("docs/dev-setup.md", [], "dropped"),
    ("docs/system/architecture.md", [], "dropped"),
    ("docs/flows/checkout.md", [], "dropped"),
    ("docs/decisions/adr-001.md", [], "dropped"),
    ("docs/screens/SCR001_Foo/spec.md", [], "dropped"),  # F7
    ("deploy-guide.md", [], "dropped"),  # F13
    ("hosting-notes.md", [], "dropped"),  # F13
    ("docs/ci-pipeline.md", [], "dropped"),  # separator-anchored "ci" token
    ("docs/policies.md", [], "kept"),  # must NOT false-positive on "ci" substring
    ("docs/odd-thing.md", [], "unmatched"),  # F6a
    ("openapi.yaml", [], "dropped"),  # conditional, surfaces don't declare api/mcp
    ("openapi.yaml", ["api"], "kept"),  # conditional, surfaces declare api
    ("docs/api/guide.md", ["mcp"], "kept"),
    ("docs/generated/route-list.md", [], "dropped"),
    ("docs/generated/feature-list.md", [], "kept"),  # named inventory carved out of docs/generated/**
    ("docs/generated/screen-list.md", [], "kept"),  # ditto — the F7 over-correction fix
    ("docs/generated/entities.md", [], "dropped"),  # rest of docs/generated/** stays dev-derived
    ("docs/generated/route-list.md", ["api"], "kept"),
]


def _profile(surfaces):
    return {"fields": {"surfaces": surfaces}}


def test_table_driven_classification():
    for rel, surfaces, bucket in CASES:
        files = [{"rel": rel, "title": ""}]
        kept, dropped, dropped_unmatched = audience_filter.apply(files, "user", _profile(surfaces))
        if bucket == "kept":
            assert rel in [f["rel"] for f in kept], f"{rel} should be kept"
            assert rel not in dropped
        else:
            assert rel in dropped, f"{rel} should be dropped"
            assert rel not in [f["rel"] for f in kept]
            if bucket == "unmatched":
                assert rel in dropped_unmatched, f"{rel} should be in dropped_unmatched"


def test_dev_audience_is_a_true_pass_through():
    files = [{"rel": r, "title": ""} for r, _, _ in CASES]
    kept, dropped, dropped_unmatched = audience_filter.apply(files, "dev", _profile([]))
    assert kept == files
    assert dropped == []
    assert dropped_unmatched == []


def test_deploy_dropped_under_user_kept_under_dev():
    files = [{"rel": "deploy/runbook.md", "title": ""}]
    kept_user, dropped_user, _ = audience_filter.apply(files, "user", _profile([]))
    assert kept_user == []
    assert dropped_user == ["deploy/runbook.md"]

    kept_dev, dropped_dev, _ = audience_filter.apply(files, "dev", _profile([]))
    assert kept_dev == files
    assert dropped_dev == []
