"""Unit tests for secret_gate.py — the sixth gate (red-team F5). Clean text -> no warnings; a
literal assignment-shaped secret -> non-empty warnings; an unavailable lib degrades to a named
`unavailable` reason rather than crashing or silently passing.
"""
import secret_gate


def test_clean_text_returns_no_warnings():
    assert secret_gate.scan("Just some ordinary documentation prose.") == []


def test_literal_secret_value_returns_warnings():
    warnings = secret_gate.scan("Example config: token=abc123def456")
    assert warnings != []


def test_placeholder_value_is_not_flagged():
    assert secret_gate.scan("token=<redacted>") == []


def test_unavailable_lib_degrades_instead_of_crashing(monkeypatch):
    monkeypatch.setattr(secret_gate, "_load_assert_no_secrets", lambda: None)
    warnings = secret_gate.scan("token=abc123def456")
    assert len(warnings) == 1
    assert warnings[0].startswith("secret-scan unavailable")
