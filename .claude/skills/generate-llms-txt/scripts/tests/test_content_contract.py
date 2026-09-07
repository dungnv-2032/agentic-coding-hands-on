"""Unit tests for content_contract.py — the 7-section end-user contract builder.

Covers: EMIT_ORDER is always returned in full; a doc is claimed by at most one section;
the F2 screens-vs-usage match-order fix; F7 (docs/screens/** never enters the screens
section); F6b (kept-but-unclaimed folds into Optional and is reported); F6c (the
three-valued `_api_state`, including detecting a filter-dropped OpenAPI spec); and the
`--audience dev` legacy passthrough.
"""
import content_contract as cc

EMPTY_PROFILE = {"status": "missing", "path": "/abs/docs/product-profile.md", "fields": {}}
OK_PROFILE = {"status": "ok", "path": "/abs/docs/product-profile.md",
              "fields": {"surfaces": ["web"], "summary": "A thing."}}


def _by_id(sections):
    return {s["id"]: s for s in sections}


def test_all_seven_sections_always_returned_in_emit_order():
    sections, unclaimed = cc.build([], EMPTY_PROFILE, "user")
    assert [s["id"] for s in sections] == list(cc.EMIT_ORDER)
    assert unclaimed == []


def test_doc_claimed_by_exactly_one_section():
    files = [
        {"rel": "docs/user-guide/install.md", "title": "Install"},
        {"rel": "docs/user-guide/screens.md", "title": "Screens"},
        {"rel": "docs/user-guide/usage.md", "title": "Usage"},
    ]
    sections, _ = cc.build(files, OK_PROFILE, "user")
    # "intro" is profile-driven (its own source is the profile path, not a kept file) —
    # excluded here since this test is about the FILE-matching sections only.
    seen = [rel for s in sections if s["id"] != "intro" for rel in s["sources"]]
    assert sorted(seen) == sorted(f["rel"] for f in files)
    assert len(seen) == len(set(seen))


def test_screens_md_lands_in_screens_not_usage():
    """F2: the usage catch-all (docs/user-guide/*) must not claim screens.md before the
    screens section gets a look."""
    files = [{"rel": "docs/user-guide/screens.md", "title": "Screens"}]
    sections, _ = cc.build(files, OK_PROFILE, "user")
    by_id = _by_id(sections)
    assert by_id["screens"]["status"] == "filled"
    assert by_id["screens"]["sources"] == ["docs/user-guide/screens.md"]
    assert by_id["usage"]["sources"] == []
    assert by_id["usage"]["status"] == "gap"


def test_docs_screens_dev_spec_never_enters_screens_section():
    """F7: docs/screens/** (rebuild-spec's dev-coded, promoted screen specs) is excluded from
    SCREENS_GLOBS. Even if it somehow reached content_contract.build() (the audience filter
    already drops it — tested separately), it must not be claimed by the screens section; it
    falls through to unclaimed/Optional instead."""
    files = [{"rel": "docs/screens/SCR001_Foo/spec.md", "title": "SCR001"}]
    sections, unclaimed = cc.build(files, OK_PROFILE, "user")
    by_id = _by_id(sections)
    assert by_id["screens"]["sources"] == []
    assert by_id["screens"]["status"] == "gap"
    assert [f["rel"] for f in unclaimed] == ["docs/screens/SCR001_Foo/spec.md"]
    assert by_id["optional"]["sources"] == ["docs/screens/SCR001_Foo/spec.md"]


def test_gap_carries_non_null_advisory():
    sections, _ = cc.build([], EMPTY_PROFILE, "user")
    for s in sections:
        if s["status"] == "gap":
            assert s["advisory"], f"{s['id']} gap must carry a non-null advisory"
        else:
            assert s["advisory"] is None


def test_kept_but_unclaimed_folds_into_optional_and_is_reported():
    """F6b: a file kept by the audience filter but matching no CONTRACT section must not
    vanish — it is folded into Optional and named in the returned `unclaimed` list."""
    files = [{"rel": "docs/generated/api-map.md", "title": "API Map"}]
    sections, unclaimed = cc.build(files, OK_PROFILE, "user")
    assert [f["rel"] for f in unclaimed] == ["docs/generated/api-map.md"]
    by_id = _by_id(sections)
    assert "docs/generated/api-map.md" in by_id["optional"]["sources"]
    assert by_id["optional"]["status"] == "filled"


def test_api_state_stated_absent_is_silent_omit():
    profile = {"status": "ok", "path": "p", "fields": {"surfaces": ["web"]}}
    sections, _ = cc.build([], profile, "user")
    api = _by_id(sections)["api"]
    assert api["status"] == "omitted"
    assert api["advisory"] is None


def test_api_state_unfilled_surfaces_with_kept_spec_is_gap_with_advisory():
    profile = {"status": "incomplete", "path": "p", "fields": {"surfaces": []}}
    files = [{"rel": "openapi.yaml", "title": "API Reference"}]
    sections, unclaimed = cc.build(files, profile, "user")
    api = _by_id(sections)["api"]
    assert api["status"] == "filled"  # the spec itself is kept and claimed
    assert unclaimed == []


def test_api_state_unfilled_surfaces_with_filter_dropped_spec_is_gap():
    """F6c: the audience filter may have already dropped the OpenAPI spec (because surfaces
    were unfilled); `_api_state` must still see it via the `dropped` list and report a gap
    with the fill-the-profile advisory, not silence."""
    profile = {"status": "incomplete", "path": "p", "fields": {"surfaces": []}}
    sections, _ = cc.build([], profile, "user", dropped=["openapi.yaml"])
    api = _by_id(sections)["api"]
    assert api["status"] == "gap"
    assert "surfaces" in api["advisory"].lower() or "Surfaces" in api["advisory"]


def test_dev_audience_returns_legacy_grouping():
    files = [
        {"rel": "docs/api/guide.md", "title": "API", "section": "API"},
        {"rel": "README.md", "title": "Readme", "section": "Overview"},
    ]
    sections, unclaimed = cc.build(files, OK_PROFILE, "dev")
    assert unclaimed == []
    # Legacy grouping orders by discovery.SECTION_ORDER, not by input/file order — "Overview"
    # precedes "API" there regardless of the files list's own order.
    assert [s["id"] for s in sections] == ["Overview", "API"]
    assert all(s["status"] == "filled" for s in sections)


def test_generated_screen_list_fills_screens_section():
    """The F7 over-correction fix: `docs/screens/**` (dev-coded per-screen specs) stays out, but
    `docs/generated/screen-list.md` — the generated screen INVENTORY — is a valid screens source.
    Without this, running /tkm:rebuild-spec could never close a screens gap."""
    files = [{"rel": "docs/generated/screen-list.md", "title": "Screen List"}]
    sections, unclaimed = cc.build(files, OK_PROFILE, "user")
    by_id = _by_id(sections)
    assert by_id["screens"]["status"] == "filled"
    assert by_id["screens"]["sources"] == ["docs/generated/screen-list.md"]
    assert unclaimed == []


def test_screens_advisory_names_both_fixers():
    """A gap must point at the tool that can actually close it — rebuild-spec for the generated
    inventory, or a hand-written end-user tour."""
    sections, _ = cc.build([], EMPTY_PROFILE, "user")
    advisory = _by_id(sections)["screens"]["advisory"]
    assert "rebuild-spec" in advisory and "docs/user-guide/screens.md" in advisory


def test_readiness_counts_required_gaps_and_flags_thin():
    sections, _ = cc.build([], EMPTY_PROFILE, "user")
    r = cc.readiness(sections)
    assert r["required_total"] == 6  # intro, install, usage, screens, features, api(surface)
    assert r["gaps"] == ["intro", "install", "usage", "screens", "features"]
    assert r["filled"] == r["required_total"] - len(r["gaps"])
    assert r["thin"] is True


def test_readiness_single_gap_is_not_thin():
    """THIN_THRESHOLD is 2: one missing section is a normal advisory, not a preflight stop."""
    files = [
        {"rel": "docs/user-guide/install.md", "title": "Install"},
        {"rel": "docs/user-guide/usage.md", "title": "Usage"},
        {"rel": "docs/generated/screen-list.md", "title": "Screens"},
        {"rel": "docs/features/thing.md", "title": "Thing"},
    ]
    r = cc.readiness(cc.build(files, OK_PROFILE, "user")[0])
    assert r["gaps"] == []
    assert r["thin"] is False


def test_readiness_dev_audience_is_never_thin():
    """`--audience dev` bypasses the contract entirely, so nothing is required there."""
    files = [{"rel": "README.md", "title": "Readme", "section": "Overview"}]
    r = cc.readiness(cc.build(files, OK_PROFILE, "dev")[0])
    assert r == {"required_total": 0, "filled": 0, "gaps": [], "thin": False}
