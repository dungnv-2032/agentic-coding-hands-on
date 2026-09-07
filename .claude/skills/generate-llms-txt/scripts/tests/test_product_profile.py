"""Unit tests for product_profile.py: the docs/product-profile.md reader/writer.

Covers the missing/incomplete/ok status ladder, the `<TODO ...>` placeholder-as-absent rule
(FR-7), list-splitting of `urls`/`surfaces`, `--init`'s overwrite guard, the symlink-escape
containment fix (red-team F1), and the per-lang advisory (red-team F15).
"""
import json
import os

import product_profile
import pytest

REQUIRED = product_profile.REQUIRED

FULL_PROFILE = """\
**Product name**: Foo
**URL**: https://foo.test/
**Department**: Platform
**Owner**: Platform Lead
**Support contact**: platform-support@example.test
**Summary**: A fixture product.
**Surfaces**: web
"""


def _write_profile(tmp_path, content):
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "product-profile.md").write_text(content, encoding="utf-8")
    return tmp_path


def test_missing_file_returns_missing_status_and_all_required_fields(tmp_path):
    profile = product_profile.load(tmp_path, "")
    assert profile.status == "missing"
    assert profile.fields == {}
    assert profile.missing_fields == list(REQUIRED)


def test_partial_profile_returns_incomplete_with_exact_missing_fields(tmp_path):
    partial = (
        "**Product name**: Foo\n"
        "**URL**: https://foo.test/\n"
        "**Support contact**: platform-support@example.test\n"
        "**Summary**: A fixture product.\n"
        "**Surfaces**: web\n"
    )
    source = _write_profile(tmp_path, partial)
    profile = product_profile.load(source, "")
    assert profile.status == "incomplete"
    assert profile.missing_fields == ["department", "owner"]


def test_todo_placeholder_parses_as_absent(tmp_path):
    content = FULL_PROFILE.replace(
        "**Department**: Platform", "**Department**: <TODO owning department or team>"
    )
    source = _write_profile(tmp_path, content)
    profile = product_profile.load(source, "")
    assert profile.status == "incomplete"
    assert profile.missing_fields == ["department"]
    assert "department" not in profile.fields


def test_surfaces_and_urls_split_to_lists(tmp_path):
    content = FULL_PROFILE.replace(
        "**URL**: https://foo.test/", "**URL**: https://foo.test/, https://foo.test/docs"
    ).replace("**Surfaces**: web", "**Surfaces**: web, api, cli")
    source = _write_profile(tmp_path, content)
    profile = product_profile.load(source, "")
    assert profile.status == "ok"
    assert profile.fields["urls"] == ["https://foo.test/", "https://foo.test/docs"]
    assert profile.fields["surfaces"] == ["web", "api", "cli"]


def test_init_refuses_overwrite_without_force(tmp_path):
    path = tmp_path / "docs" / "product-profile.md"
    product_profile.write(path, {"name": "Foo"})
    assert path.is_file()
    with pytest.raises(FileExistsError):
        product_profile.write(path, {"name": "Bar"})
    # force=True is allowed to overwrite.
    product_profile.write(path, {"name": "Bar"}, force=True)
    assert "Bar" in path.read_text(encoding="utf-8")


def test_symlink_escape_reads_as_missing(tmp_path):
    """A product-profile.md symlinked to a path outside the repo must read as `missing`, never
    as the outside content (red-team F1)."""
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_file = outside / "real-profile.md"
    outside_file.write_text(FULL_PROFILE, encoding="utf-8")

    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    symlink_path = repo / "docs" / "product-profile.md"
    os.symlink(outside_file, symlink_path)

    profile = product_profile.load(repo, "")
    assert profile.status == "missing"
    assert profile.fields == {}


def test_per_lang_advisory_fires_without_lang_flag(tmp_path):
    state = {"primary_lang": "en", "translations": {"en": {}, "vi": {}}}
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / ".rebuild-state.json").write_text(json.dumps(state), encoding="utf-8")

    advisory = product_profile.per_lang_advisory(tmp_path, "")
    assert advisory is not None
    assert "--lang" in advisory

    # Passing --lang short-circuits before the state file is even read.
    assert product_profile.per_lang_advisory(tmp_path, "en") is None


def test_per_lang_advisory_returns_none_for_malformed_state(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / ".rebuild-state.json").write_text("{not valid json", encoding="utf-8")
    assert product_profile.per_lang_advisory(tmp_path, "") is None

    # Also None when the file is absent entirely.
    assert product_profile.per_lang_advisory(tmp_path / "nope", "") is None
