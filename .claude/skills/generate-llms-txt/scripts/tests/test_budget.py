"""Unit tests for budget.py: the token-budget trim ladder. `enforce()` owns rendering — it is
exercised here with the real `render.full` (imported), matching how build-llms-skeleton.py wires
it, so the fence-aware truncation and the F9 render-per-trim-step contract are both tested
against real behavior rather than a stand-in.
"""
import budget
import render


def _entry(tmp_path, name, body):
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return {"rel": name, "title": name, "abs": str(path), "desc": ""}


def _profile(summary):
    return {"fields": {"summary": summary}}


def _sections(tmp_path):
    return [
        {"id": "intro", "title": "General Introduction", "status": "filled",
         "entries": [], "sources": []},
        {"id": "install", "title": "Installation", "status": "filled",
         "entries": [_entry(tmp_path, "install.md", "Install text. " * 20)],
         "sources": ["install.md"]},
        {"id": "usage", "title": "Usage Guide", "status": "filled",
         "entries": [_entry(tmp_path, "usage.md", "Usage text. " * 20)],
         "sources": ["usage.md"]},
        {"id": "screens", "title": "Screens", "status": "filled",
         "entries": [_entry(tmp_path, "screens.md", "Screens text. " * 20)],
         "sources": ["screens.md"]},
        {"id": "features", "title": "Features", "status": "filled",
         "entries": [_entry(tmp_path, "features.md", "Features text. " * 20)],
         "sources": ["features.md"]},
        {"id": "api", "title": "API & MCP Guide", "status": "filled",
         "entries": [_entry(tmp_path, "api.md", "API text. " * 20)],
         "sources": ["api.md"]},
        {"id": "optional", "title": "Optional", "status": "filled",
         "entries": [_entry(tmp_path, "optional.md", "Optional text. " * 20)],
         "sources": ["optional.md"]},
    ]


def test_ladder_drops_optional_before_collapsing_api(tmp_path):
    sections = _sections(tmp_path)
    render_fn = lambda secs: render.full("Bulky", secs, _profile("Summary."), "")
    _, report = budget.enforce(sections, 10, render_fn)
    assert report["trims"], "a tiny cap must force at least one trim step"
    assert report["trims"][0]["step"] == "optional-dropped"


def test_intro_and_install_are_never_trimmed(tmp_path):
    sections = _sections(tmp_path)
    render_fn = lambda secs: render.full("Bulky", secs, _profile("Summary."), "")
    text, report = budget.enforce(sections, 1, render_fn)
    # Even after the whole ladder runs (cap=1 forces every step), install's body is untouched.
    assert text.count("Install text.") == 20


def test_over_cap_true_still_returns_text(tmp_path):
    sections = _sections(tmp_path)
    render_fn = lambda secs: render.full("Bulky", secs, _profile("Summary."), "")
    text, report = budget.enforce(sections, 1, render_fn)
    assert report["over_cap"] is True
    assert text  # the file is still written, over-cap is reported, not raised


def test_est_method_present_and_no_trims_under_cap(tmp_path):
    sections = [{"id": "install", "title": "Installation", "status": "filled",
                 "entries": [_entry(tmp_path, "install.md", "short")], "sources": ["install.md"]}]
    render_fn = lambda secs: render.full("Name", secs, _profile("s"), "")
    _, report = budget.enforce(sections, 50000, render_fn)
    assert report["est_method"] == "chars/4 (estimate)"
    assert report["over_cap"] is False
    assert report["trims"] == []


def test_render_fn_called_once_per_trim_step(tmp_path):
    sections = _sections(tmp_path)
    calls = []

    def counting_render(secs):
        calls.append(1)
        return render.full("Bulky", secs, _profile("Summary."), "")

    _, report = budget.enforce(sections, 5, counting_render)
    assert len(calls) == 1 + len(report["trims"])


def test_truncation_point_inside_fence_advances_past_fence():
    body = (
        "Intro paragraph text.\n"
        "\n"
        "```\n"
        "## looks like a heading but is inside a fence\n"
        "more code\n"
        "```\n"
        "\n"
        "## Real Heading\n"
        "Content after heading that should be cut off.\n"
    )
    out = budget._truncate_at_first_heading(body)
    assert "## Real Heading" not in out
    assert "Content after heading" not in out
    assert "looks like a heading" in out
    assert out.count("```") == 2
