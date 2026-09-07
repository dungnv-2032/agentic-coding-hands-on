# layout-exempt: rebuild-spec mirror-skew/prune tests — docs/<lang> paths here are this phase's own managed targets
"""Tests for phase-06 (plans/260818-0758-rebuild-spec-post-migration-completion/
phase-06-mirror-skew-prune-translate.md): mirror skew detection
(`_mirror_skew_detect_lib.py`), the `mirror-skew` registry step
(`_mirror_skew_lib.py`), the narrow satellite prune
(`prune_mirror_v26_satellites.py`), and `mirror_refusal_reason`'s updated message.

Two facts from phase-00 drive every fixture here:

1. Translate never deletes -- a mirror can hold the three retired v26 satellite
   files forever once the primary has moved past them. The prune's allow-list is
   exactly those three filenames; everything else about a mirror is left alone.
2. On the real corpus, a mirror's registered translate cursor (`translated_from_
   sha`) already EQUALS the primary's `last_rebuild_sha` -- so staleness must be
   provable from SHAPE (still v26, still holding a satellite), never from the
   cursor alone. Fixtures below deliberately set matching cursors to prove this.

Mirrors are CHILDREN of `docs_root` (the directory holding `.rebuild-state.json`),
never reached via `docs_root.parent` -- verified against the real corpus copy
during implementation (`docs_root / "vi"` exists; `docs_root.parent / "vi"` does
not, for this at-root primary layout). Every fixture below places `vi`/`jp` under
`docs_root` accordingly.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _audience_split_cli_lib as cli_lib  # noqa: E402
import _mirror_skew_detect_lib as detect_lib  # noqa: E402
import _mirror_skew_lib as step  # noqa: E402
import prune_mirror_v26_satellites as prune_cli  # noqa: E402

V26_SATELLITES = ("business-context.md", "screens.md", "edge-cases.md")


# --------------------------------------------------------------------------- #
# Fixture helpers
# --------------------------------------------------------------------------- #
def _init_git_repo(d: Path) -> None:
    subprocess.run(["git", "init", str(d)], capture_output=True, check=True)


def _write_state(docs_root: Path, *, primary_cursor_sha: str = "sha-NEW",
                  translations: dict | None = None) -> None:
    import json
    docs_root.mkdir(parents=True, exist_ok=True)
    data = {
        "primary_lang": "en",
        "last_rebuild_sha": primary_cursor_sha,
        "translations": translations or {},
    }
    (docs_root / ".rebuild-state.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8",
    )


def _write_v26_dir(feature_dir: Path) -> None:
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "technical-spec.md").write_text("# tech\n", encoding="utf-8")
    for name in V26_SATELLITES:
        (feature_dir / name).write_text("x\n", encoding="utf-8")


def _write_v27_dir(feature_dir: Path) -> None:
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "functional-spec.md").write_text("# func\n", encoding="utf-8")
    (feature_dir / "technical-spec.md").write_text("# tech\n", encoding="utf-8")


def _write_hybrid_dir(feature_dir: Path) -> None:
    _write_v27_dir(feature_dir)
    for name in V26_SATELLITES:
        (feature_dir / name).write_text("x\n", encoding="utf-8")


def _standard_translations(sha: str = "sha-OLD") -> dict:
    return {
        "vi": {"translated_from_sha": sha, "last_translate_run_sha": sha,
               "passes_translated": ["feature-specs"]},
        "jp": {"translated_from_sha": sha, "last_translate_run_sha": sha,
               "passes_translated": ["feature-specs"]},
    }


# --------------------------------------------------------------------------- #
# Unit -- detect_skew
# --------------------------------------------------------------------------- #
def test_detect_skew_reports_per_lang_counts_vi_v26_jp_v27(tmp_path):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, primary_cursor_sha="sha-NEW",
                 translations=_standard_translations("sha-NEW"))
    _write_v26_dir(docs_root / "vi" / "features" / "F001_Auth")
    _write_v27_dir(docs_root / "jp" / "features" / "F001_Auth")

    skews = {s.lang: s for s in detect_lib.detect_skew(docs_root)}

    assert skews["vi"].dirs_v26 == 1
    assert skews["vi"].satellite_files_present == 3
    assert skews["vi"].stale is True
    assert skews["jp"].dirs_v27 == 1
    assert skews["jp"].satellite_files_present == 0
    assert skews["jp"].stale is False  # v27 shape + matching cursor -> in sync


def test_detect_skew_no_translations_returns_empty_list_no_raise(tmp_path):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations={})
    assert detect_lib.detect_skew(docs_root) == []


def test_detect_skew_missing_state_file_returns_empty_list_no_raise(tmp_path):
    docs_root = tmp_path / "docs"
    docs_root.mkdir(parents=True)
    assert detect_lib.detect_skew(docs_root) == []


def test_detect_skew_stale_true_even_when_cursor_matches_but_shape_is_v26(tmp_path):
    """The real-corpus condition CORRECTION 2/3 measured: translated_from_sha
    already equals the primary cursor, yet the mirror is still plainly v26 on
    disk -- cursor equality alone must never read as "in sync"."""
    docs_root = tmp_path / "docs"
    _write_state(docs_root, primary_cursor_sha="sha-SAME",
                 translations=_standard_translations("sha-SAME"))
    _write_v26_dir(docs_root / "vi" / "features" / "F001_Auth")

    skews = detect_lib.detect_skew(docs_root)
    vi = next(s for s in skews if s.lang == "vi")
    assert vi.translated_from_sha == vi.primary_cursor_sha
    assert vi.stale is True


def test_mirrors_are_children_of_docs_root_not_its_parent(tmp_path):
    """Locks in the corrected join: `docs_root / lang`, never `docs_root.parent /
    lang` -- the latter resolves outside the repo entirely on an at-root primary
    layout and silently reports zero dirs everywhere."""
    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations=_standard_translations())
    _write_v26_dir(docs_root / "vi" / "features" / "F001_Auth")
    assert not (docs_root.parent / "vi").exists()

    skews = {s.lang: s for s in detect_lib.detect_skew(docs_root)}
    assert skews["vi"].dirs_total == 1


# --------------------------------------------------------------------------- #
# Unit -- count_hybrid_primary_dirs / count_pending
# --------------------------------------------------------------------------- #
def test_count_hybrid_primary_dirs_counts_only_hybrid_shape(tmp_path):
    docs_root = tmp_path / "docs"
    docs_root.mkdir(parents=True)
    _write_hybrid_dir(docs_root / "features" / "F001_Hybrid")
    _write_v27_dir(docs_root / "features" / "F002_Clean")
    assert detect_lib.count_hybrid_primary_dirs(docs_root) == 1


def test_count_pending_is_zero_when_every_mirror_synced(tmp_path):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, primary_cursor_sha="sha-NEW",
                 translations=_standard_translations("sha-NEW"))
    _write_v27_dir(docs_root / "vi" / "features" / "F001_Auth")
    _write_v27_dir(docs_root / "jp" / "features" / "F001_Auth")
    assert step.count_pending(docs_root, tmp_path, None) == 0


def test_count_pending_counts_stale_langs(tmp_path):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations=_standard_translations())
    _write_v26_dir(docs_root / "vi" / "features" / "F001_Auth")
    _write_v26_dir(docs_root / "jp" / "features" / "F001_Auth")
    assert step.count_pending(docs_root, tmp_path, None) == 2


# --------------------------------------------------------------------------- #
# Integration -- handoff with a hybrid primary -> refuses, names the --reviewed
# command, step counts INERT (never writes)
# --------------------------------------------------------------------------- #
def test_run_refuses_handoff_while_primary_hybrid_and_names_reviewed_command(
    tmp_path, capsys,
):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations=_standard_translations())
    _write_hybrid_dir(docs_root / "features" / "F001_Auth")
    _write_v26_dir(docs_root / "vi" / "features" / "F001_Auth")
    _write_v26_dir(docs_root / "jp" / "features" / "F001_Auth")

    result = step.run(docs_root, tmp_path, None)
    out = capsys.readouterr().out

    assert result.category == "inert"
    assert result.needs_llm_fill is False
    assert "[ACTION REQUIRED]" in out
    assert "--reviewed" in out
    assert "migrate_feature_audience_split.py" in out
    assert "[HANDOFF]" not in out  # never hands off while hybrid


def test_run_hybrid_refusal_writes_nothing(tmp_path):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations=_standard_translations())
    _write_hybrid_dir(docs_root / "features" / "F001_Auth")
    _write_v26_dir(docs_root / "vi" / "features" / "F001_Auth")

    before = sorted(p.name for p in (docs_root / "vi" / "features" / "F001_Auth").iterdir())
    step.run(docs_root, tmp_path, None)
    after = sorted(p.name for p in (docs_root / "vi" / "features" / "F001_Auth").iterdir())
    assert before == after


# --------------------------------------------------------------------------- #
# Integration -- handoff with a clean primary -> translation_sync_gate.py
# invoked, its stdout echoed byte-for-byte, [HANDOFF] naming the stale langs
# --------------------------------------------------------------------------- #
def test_run_clean_primary_invokes_translation_sync_gate_and_hands_off(
    tmp_path, capsys, monkeypatch,
):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, primary_cursor_sha="sha-NEW",
                 translations=_standard_translations("sha-OLD"))
    _write_v27_dir(docs_root / "features" / "F001_Auth")
    _write_v26_dir(docs_root / "vi" / "features" / "F001_Auth")
    _write_v26_dir(docs_root / "jp" / "features" / "F001_Auth")

    captured_argv: list[list[str]] = []
    import translation_sync_gate as real_gate
    real_main = real_gate.main

    def _spy_main(argv):
        captured_argv.append(list(argv))
        return real_main(argv)

    monkeypatch.setattr(real_gate, "main", _spy_main)

    result = step.run(docs_root, tmp_path, None)
    out = capsys.readouterr().out

    assert captured_argv, "translation_sync_gate.py must be invoked"
    assert captured_argv[0][:2] == ["--mode", "plan"]
    assert '"pass": "feature-specs"' in out  # the gate's OWN JSON, echoed verbatim
    assert "[HANDOFF]" in out
    assert "vi" in out and "jp" in out
    assert result.needs_llm_fill is True
    assert result.category == "progress"


def test_run_clean_primary_all_synced_reports_already_no_handoff(tmp_path, capsys):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, primary_cursor_sha="sha-NEW",
                 translations=_standard_translations("sha-NEW"))
    _write_v27_dir(docs_root / "features" / "F001_Auth")
    _write_v27_dir(docs_root / "vi" / "features" / "F001_Auth")
    _write_v27_dir(docs_root / "jp" / "features" / "F001_Auth")

    result = step.run(docs_root, tmp_path, None)
    out = capsys.readouterr().out

    assert result.category == "already"
    assert result.needs_llm_fill is False
    assert "[HANDOFF]" not in out


def test_run_reports_failed_when_translation_sync_gate_exits_nonzero(
    tmp_path, capsys, monkeypatch,
):
    """The gate's exit code is never silently swallowed -- a real failure (e.g. a
    state path outside project_root) must surface as FAILED, not get folded into
    a false ALREADY/PROGRESS."""
    docs_root = tmp_path / "docs"
    _write_state(docs_root, primary_cursor_sha="sha-NEW",
                 translations=_standard_translations("sha-OLD"))
    _write_v27_dir(docs_root / "features" / "F001_Auth")
    _write_v26_dir(docs_root / "vi" / "features" / "F001_Auth")

    import translation_sync_gate as real_gate
    monkeypatch.setattr(real_gate, "main", lambda argv: 2)

    result = step.run(docs_root, tmp_path, None)
    assert result.category == "failed"
    assert "exited 2" in result.message


def test_run_no_secondary_languages_reports_already(tmp_path, capsys):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations={})
    _write_v27_dir(docs_root / "features" / "F001_Auth")

    result = step.run(docs_root, tmp_path, None)
    assert result.category == "already"
    assert "no secondary languages" in result.message


def test_run_features_filter_warns_and_runs_unscoped(tmp_path, capsys):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations={})
    step.run(docs_root, tmp_path, frozenset({"F001_Auth"}))
    err = capsys.readouterr().err
    assert "--features does not scope" in err


# --------------------------------------------------------------------------- #
# Unit -- prune allow-list never selects anything but the 3 retired filenames
# --------------------------------------------------------------------------- #
def test_prune_allow_list_never_selects_technical_or_functional_spec(tmp_path):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations=_standard_translations())
    fd = docs_root / "vi" / "features" / "F001_Auth"
    fd.mkdir(parents=True)
    (fd / "technical-spec.md").write_text("x", encoding="utf-8")
    (fd / "functional-spec.md").write_text("x", encoding="utf-8")
    (fd / "confidence-report_technical-spec.md").write_text("x", encoding="utf-8")
    for name in V26_SATELLITES:
        (fd / name).write_text("x", encoding="utf-8")

    paths = prune_cli.find_satellite_paths(docs_root, tmp_path, ["vi"])
    names = {p.name for p in paths}
    assert names == set(V26_SATELLITES)
    assert "technical-spec.md" not in names
    assert "functional-spec.md" not in names
    assert "confidence-report_technical-spec.md" not in names


def test_prune_never_touches_files_outside_features_dir(tmp_path):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations=_standard_translations())
    (docs_root / "vi").mkdir(parents=True)
    (docs_root / "vi" / "business-context.md").write_text("x", encoding="utf-8")  # NOT under features/

    paths = prune_cli.find_satellite_paths(docs_root, tmp_path, ["vi"])
    assert paths == []


def test_prune_path_escape_is_rejected_never_string_joined(tmp_path):
    """`--lang` never reaches path construction directly -- only a state-registered
    key does. A traversal-shaped `--lang` value is rejected by `normalize_lang`
    before it ever reaches a path join."""
    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations=_standard_translations())
    exit_code = prune_cli.main([
        "--docs-root", str(docs_root), "--project-root", str(tmp_path),
        "--lang", "../../etc/passwd",
    ])
    assert exit_code == 2


def test_prune_symlink_escaping_project_root_is_skipped(tmp_path):
    outside = tmp_path.parent / f"outside-{tmp_path.name}"
    outside.mkdir(exist_ok=True)
    (outside / "business-context.md").write_text("secret", encoding="utf-8")

    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations=_standard_translations())
    fd = docs_root / "vi" / "features" / "F001_Auth"
    fd.mkdir(parents=True)
    (fd / "screens.md").write_text("x", encoding="utf-8")
    try:
        (fd / "business-context.md").symlink_to(outside / "business-context.md")
    except OSError:
        pytest.skip("symlinks not supported in this environment")

    paths = prune_cli.find_satellite_paths(docs_root, tmp_path, ["vi"])
    names = {p.name for p in paths}
    assert "screens.md" in names
    assert "business-context.md" not in names  # symlink escape -- skipped, not followed


# --------------------------------------------------------------------------- #
# Integration -- prune CLI: primary-safety refusal, report-default, --delete,
# idempotency
# --------------------------------------------------------------------------- #
def _make_prune_fixture(tmp_path: Path, *, n: int = 3, primary_hybrid: bool) -> Path:
    docs_root = tmp_path / "docs"
    _init_git_repo(tmp_path)
    _write_state(docs_root, translations=_standard_translations())
    for i in range(1, n + 1):
        slug = f"F{i:03d}_Feature{i}"
        if primary_hybrid:
            _write_hybrid_dir(docs_root / "features" / slug)
        else:
            _write_v27_dir(docs_root / "features" / slug)
        for lang in ("vi", "jp"):
            _write_v26_dir(docs_root / lang / "features" / slug)
    return docs_root


def test_prune_dry_run_lists_and_writes_nothing(tmp_path):
    n = 3
    docs_root = _make_prune_fixture(tmp_path, n=n, primary_hybrid=False)
    before = sorted(str(p) for p in docs_root.rglob("*") if p.is_file())

    exit_code = prune_cli.main(
        ["--docs-root", str(docs_root), "--project-root", str(tmp_path)]
    )
    after = sorted(str(p) for p in docs_root.rglob("*") if p.is_file())

    assert exit_code == 0
    assert before == after


def test_prune_delete_refused_while_primary_holds_satellites(tmp_path, capsys):
    docs_root = _make_prune_fixture(tmp_path, n=2, primary_hybrid=True)
    before = sorted(str(p) for p in docs_root.rglob("*") if p.is_file())

    exit_code = prune_cli.main(
        ["--docs-root", str(docs_root), "--project-root", str(tmp_path), "--delete"]
    )
    after = sorted(str(p) for p in docs_root.rglob("*") if p.is_file())
    err = capsys.readouterr().err

    assert exit_code == 2
    assert "refusing to prune" in err
    assert before == after  # NOTHING deleted


def test_prune_delete_after_primary_clean_removes_exactly_the_satellites(tmp_path):
    n = 5
    docs_root = _make_prune_fixture(tmp_path, n=n, primary_hybrid=False)

    exit_code = prune_cli.main(
        ["--docs-root", str(docs_root), "--project-root", str(tmp_path), "--delete"]
    )
    assert exit_code == 0

    for lang in ("vi", "jp"):
        for i in range(1, n + 1):
            fd = docs_root / lang / "features" / f"F{i:03d}_Feature{i}"
            for name in V26_SATELLITES:
                assert not (fd / name).exists()
            assert (fd / "technical-spec.md").is_file()  # untouched

    # Primary tree provably untouched by the prune.
    for i in range(1, n + 1):
        fd = docs_root / "features" / f"F{i:03d}_Feature{i}"
        assert (fd / "functional-spec.md").is_file()
        assert (fd / "technical-spec.md").is_file()


def test_prune_three_consecutive_runs_are_idempotent(tmp_path):
    n = 3
    docs_root = _make_prune_fixture(tmp_path, n=n, primary_hybrid=False)
    argv = ["--docs-root", str(docs_root), "--project-root", str(tmp_path), "--delete"]

    first = prune_cli.main(argv)
    fp_after_first = sorted(str(p) for p in docs_root.rglob("*") if p.is_file())
    second = prune_cli.main(argv)
    fp_after_second = sorted(str(p) for p in docs_root.rglob("*") if p.is_file())
    third = prune_cli.main(argv)
    fp_after_third = sorted(str(p) for p in docs_root.rglob("*") if p.is_file())

    assert first == second == third == 0
    assert fp_after_first == fp_after_second == fp_after_third


def test_prune_lang_filter_scopes_to_one_language(tmp_path):
    n = 2
    docs_root = _make_prune_fixture(tmp_path, n=n, primary_hybrid=False)

    prune_cli.main([
        "--docs-root", str(docs_root), "--project-root", str(tmp_path),
        "--lang", "vi", "--delete",
    ])

    for i in range(1, n + 1):
        vi_fd = docs_root / "vi" / "features" / f"F{i:03d}_Feature{i}"
        jp_fd = docs_root / "jp" / "features" / f"F{i:03d}_Feature{i}"
        for name in V26_SATELLITES:
            assert not (vi_fd / name).exists()
            assert (jp_fd / name).is_file()  # jp untouched -- --lang scoped it out


def test_prune_unregistered_lang_is_rejected(tmp_path):
    docs_root = _make_prune_fixture(tmp_path, n=1, primary_hybrid=False)
    exit_code = prune_cli.main([
        "--docs-root", str(docs_root), "--project-root", str(tmp_path),
        "--lang", "fr", "--delete",
    ])
    assert exit_code == 2


# --------------------------------------------------------------------------- #
# Integration -- mirror_refusal_reason names the 3-command sequence
# --------------------------------------------------------------------------- #
def test_mirror_refusal_reason_names_all_three_commands(tmp_path):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations=_standard_translations())
    mirror_root = docs_root / "vi"
    mirror_root.mkdir(parents=True, exist_ok=True)

    reason = cli_lib.mirror_refusal_reason(mirror_root)

    assert reason is not None
    assert "migrate_feature_audience_split.py" in reason
    assert "--reviewed" in reason
    assert "prune_mirror_v26_satellites.py" in reason
    assert "--delete" in reason
    assert "/tkm:rebuild-spec --lang" in reason


def test_mirror_refusal_reason_still_none_for_the_primary_itself(tmp_path):
    docs_root = tmp_path / "docs"
    _write_state(docs_root, translations=_standard_translations())
    assert cli_lib.mirror_refusal_reason(docs_root) is None
