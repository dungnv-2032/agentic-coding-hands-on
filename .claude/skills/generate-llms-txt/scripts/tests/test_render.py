"""Unit tests for render.py: self-containment link rewriting, v1-unchanged heading
demotion/frontmatter strip, and the F8 guarantee that `skeleton()` (the llms.txt index)
never renders profile prose or a raw product URL.
"""
import render


def test_rewrite_links_bare_text_for_inlined_target():
    body = "See [the guide](docs/user-guide/usage.md) for details."
    out = render.rewrite_links(body, {"docs/user-guide/usage.md"})
    assert out == "See the guide for details."


def test_rewrite_links_citation_for_non_inlined_target():
    body = "See [the guide](docs/user-guide/usage.md) for details."
    out = render.rewrite_links(body, set())
    assert out == "See the guide (source: docs/user-guide/usage.md) for details."


def test_rewrite_links_image_becomes_bracketed_alt():
    body = "![Diagram](img/diagram.png)"
    out = render.rewrite_links(body, set())
    assert out == "[image: Diagram]"


def test_rewrite_links_http_link_untouched():
    body = "[External](https://example.test/docs)"
    out = render.rewrite_links(body, set())
    assert out == "[External](https://example.test/docs)"


def test_rewrite_links_anchor_stripped():
    body = "[Jump to section](#section-two)"
    out = render.rewrite_links(body, set())
    assert out == "Jump to section"


def test_inline_body_strips_frontmatter_drops_h1_demotes_headings():
    content = (
        "---\n"
        "kind: doc\n"
        "---\n"
        "# Install Guide\n\n"
        "## Web\n\n"
        "Some text.\n"
    )
    out = render.inline_body(content)
    assert "kind: doc" not in out
    assert "# Install Guide" not in out
    assert "#### Web" in out
    assert "Some text." in out


def test_skeleton_renders_no_profile_prose_or_product_url():
    """F8: skeleton() takes only a plain-text `summary`, never the profile dict — structurally
    it has no channel for a product URL/department/owner to leak into the index."""
    sections = [
        {"id": "intro", "title": "General Introduction", "status": "filled",
         "entries": [], "sources": [], "advisory": None},
        {"id": "install", "title": "Installation", "status": "filled",
         "entries": [{"rel": "docs/user-guide/install.md", "title": "Install",
                       "desc": "How to install."}],
         "sources": ["docs/user-guide/install.md"], "advisory": None},
    ]
    text = render.skeleton("Acme Portal", sections, "", summary="A self-service portal.")
    assert "http://" not in text and "https://" not in text
    assert "# Acme Portal" in text
    assert "> A self-service portal." in text
    assert "## Installation" in text
    assert "## General Introduction" not in text  # intro is the H1 + blockquote, no own heading


def test_self_containment_counts_zero_after_rewrite(tmp_path):
    doc = tmp_path / "usage.md"
    doc.write_text("See [other](docs/other.md) and ![img](x.png).", encoding="utf-8")
    sections = [{"id": "usage", "title": "Usage Guide", "status": "filled",
                 "entries": [{"rel": "usage.md", "title": "Usage", "abs": str(doc)}],
                 "sources": ["usage.md"]}]
    full_text = render.full("Name", sections, {"fields": {}}, "")
    counts = render.self_containment_counts(sections, full_text)
    assert counts["remaining"] == 0
