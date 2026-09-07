"""Tests for validate_behavior_logic.py (Wave 6.875 gate)."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_behavior_logic import validate, main  # noqa: E402

TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "behavior-logic-template.md"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_BEHAVIOR_LOGIC = """\
## Behavior Logic Index

| BL Code | Name | Source File | Description |
|---------|------|-------------|-------------|
| BL001 | CreateUser | app/Services/UserService.php | Creates a new user |
| BL002 | UpdateOrder | app/Services/OrderService.php | Updates order status |
| BL003 | SendNotification | app/Jobs/NotifyJob.php | Dispatches notification |

## BL001_CreateUser

**Source File:** `app/Services/UserService.php`
**Source Symbol:** `UserService::create`

Validates input, hashes password, persists user record, dispatches welcome email.

## BL002_UpdateOrder

**Source File:** `app/Services/OrderService.php`
**Source Symbol:** `OrderService::updateStatus`

Validates transition, updates order.status, logs audit entry.

## BL003_SendNotification

**Source File:** `app/Jobs/NotifyJob.php`
**Source Symbol:** `NotifyJob::handle`

Resolves notification channel, formats payload, dispatches to queue.
"""

DUPLICATE_BL = """\
## Behavior Logic Index

| BL Code | Name |
|---------|------|
| BL001 | CreateUser |

## BL001_CreateUser

**Source File:** `app/Services/UserService.php`
**Source Symbol:** `UserService::create`

First definition.

## BL001_CreateUser

**Source File:** `app/Services/UserService.php`
**Source Symbol:** `UserService::create`

Duplicate definition.
"""

MISSING_SOURCE_FILE = """\
## Behavior Logic Index

| BL Code | Name |
|---------|------|
| BL001 | CreateUser |

## BL001_CreateUser

**Source Symbol:** `UserService::create`

Missing source file field.
"""

MISSING_SOURCE_SYMBOL = """\
## Behavior Logic Index

| BL Code | Name |
|---------|------|
| BL001 | CreateUser |

## BL001_CreateUser

**Source File:** `app/Services/UserService.php`

Missing source symbol field.
"""

MISSING_BOTH_SOURCE_FIELDS = """\
## Behavior Logic Index

| BL Code | Name |
|---------|------|
| BL001 | CreateUser |

## BL001_CreateUser

No source fields at all — just a description.
"""

MISSING_INDEX_SECTION = """\
## BL001_CreateUser

**Source File:** `app/Services/UserService.php`
**Source Symbol:** `UserService::create`

Missing index section.
"""

FILE_EXCHANGE_WITH_SCHEMA = """\
## Behavior Logic Index

| BL Code | Name |
|---------|------|
| BL001 | ImportOrdersCsv |

## BL001_ImportOrdersCsv

**Type**: custom-command
**Trigger**: `php artisan orders:import`
**File Schema**: | Column | Type | Required | Notes |
|--------|------|----------|-------|
| order_id | string | yes | Unique order identifier |
| sku | string | yes | Product SKU |
**Source File:** `app/Console/Commands/ImportOrdersCsv.php`
**Source Symbol:** `ImportOrdersCsv::handle`

Reads a CSV upload and imports each row as an order.
"""

FILE_EXCHANGE_WITHOUT_SCHEMA = """\
## Behavior Logic Index

| BL Code | Name |
|---------|------|
| BL001 | ImportOrdersCsv |

## BL001_ImportOrdersCsv

**Type**: custom-command
**Trigger**: `php artisan orders:import`
**Source File:** `app/Console/Commands/ImportOrdersCsv.php`
**Source Symbol:** `ImportOrdersCsv::handle`

Reads a CSV upload and imports each row as an order.
"""

NON_FILE_EXCHANGE_BL = """\
## Behavior Logic Index

| BL Code | Name |
|---------|------|
| BL001 | SendWelcomeEmail |

## BL001_SendWelcomeEmail

**Type**: notification
**Trigger**: `UserRegistered event`
**Source File:** `app/Listeners/SendWelcomeEmail.php`
**Source Symbol:** `SendWelcomeEmail::handle`

Sends a welcome email to the newly registered user.
"""

FILE_EXCHANGE_NA_MISUSE = """\
## Behavior Logic Index

| BL Code | Name |
|---------|------|
| BL001 | ImportOrdersCsv |

## BL001_ImportOrdersCsv

**Type**: custom-command
**Trigger**: `php artisan orders:import`
**File Schema**: N/A — not a file-exchange type
**Source File:** `app/Console/Commands/ImportOrdersCsv.php`
**Source Symbol:** `ImportOrdersCsv::handle`

Reads a CSV upload and imports each row as an order.
"""

IMPORTANT_SUBSTRING_GUARD_BL = """\
## Behavior Logic Index

| BL Code | Name |
|---------|------|
| BL001 | ApplyDiscount |

## BL001_ApplyDiscount

**Type**: custom-command
**Trigger**: `php artisan discounts:apply`
**Source File:** `app/Console/Commands/ApplyDiscount.php`
**Source Symbol:** `ApplyDiscount::handle`

This is important business logic for applying seasonal discounts.
"""

MERGED_WITH_DUPLICATE_HEADER = """\
## Behavior Logic Index

| BL Code | Name |
|---------|------|
| BL001 | CreateUser |

## BL001_CreateUser

**Source File:** `app/Services/UserService.php`
**Source Symbol:** `UserService::create`

First fragment.

## Behavior Logic Index

| BL Code | Name |
|---------|------|
| BL002 | UpdateOrder |

## BL002_UpdateOrder

**Source File:** `app/Services/OrderService.php`
**Source Symbol:** `OrderService::updateStatus`

Second fragment — duplicate header from merge.
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_plan(tmp_path: Path, content: str) -> Path:
    plan = tmp_path / "test-plan"
    artifacts = plan / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "behavior-logic.md").write_text(content, encoding="utf-8")
    return plan


def _write_inventory(tmp_path: Path, entries: list[str]) -> Path:
    inv = tmp_path / "bl-inventory.txt"
    inv.write_text("\n".join(entries), encoding="utf-8")
    return inv


# ---------------------------------------------------------------------------
# Tests — PASS
# ---------------------------------------------------------------------------

def test_valid_behavior_logic_passes(tmp_path):
    plan = _setup_plan(tmp_path, VALID_BEHAVIOR_LOGIC)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS", result["issues"]
    assert result["summary"]["critical"] == 0
    assert result["summary"]["warning"] == 0


def test_cardinality_match_no_warn(tmp_path):
    plan = _setup_plan(tmp_path, VALID_BEHAVIOR_LOGIC)
    inv = _write_inventory(tmp_path, ["BL001_CreateUser", "BL002_UpdateOrder", "BL003_SendNotification"])
    result = validate(plan, tmp_path, scout_bl_inventory=inv)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "BehaviorLogic.cardinality" not in rule_ids


# ---------------------------------------------------------------------------
# Tests — FAIL (critical)
# ---------------------------------------------------------------------------

def test_duplicate_bl_fails(tmp_path):
    plan = _setup_plan(tmp_path, DUPLICATE_BL)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "BehaviorLogic.no_dup_bl" in rule_ids


def test_missing_source_file_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_SOURCE_FILE)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "BehaviorLogic.source_present" in rule_ids


def test_missing_source_symbol_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_SOURCE_SYMBOL)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "BehaviorLogic.source_present" in rule_ids


def test_missing_both_source_fields_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_BOTH_SOURCE_FIELDS)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "BehaviorLogic.source_present" in rule_ids
    # Both fields missing → two source_present issues
    source_issues = [i for i in result["issues"]
                     if i["rule_id"] == "BehaviorLogic.source_present"]
    assert len(source_issues) == 2


def test_missing_index_section_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_INDEX_SECTION)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "BehaviorLogic.required_sections" in rule_ids


def test_merged_with_duplicate_header_fails(tmp_path):
    """Fragment merge producing two ## Behavior Logic Index sections must be caught."""
    plan = _setup_plan(tmp_path, MERGED_WITH_DUPLICATE_HEADER)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "BehaviorLogic.single_header" in rule_ids


# ---------------------------------------------------------------------------
# Tests — WARN
# ---------------------------------------------------------------------------

def test_missing_file_warns(tmp_path):
    plan = tmp_path / "test-plan"
    (plan / "artifacts").mkdir(parents=True)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "BehaviorLogic.completed_missing" in rule_ids


def test_cardinality_mismatch_warns(tmp_path):
    plan = _setup_plan(tmp_path, VALID_BEHAVIOR_LOGIC)
    # Inventory has 5 entries but doc has 3 BL sections
    inv = _write_inventory(tmp_path, [
        "BL001_CreateUser", "BL002_UpdateOrder", "BL003_SendNotification",
        "BL004_Extra", "BL005_AlsoExtra",
    ])
    result = validate(plan, tmp_path, scout_bl_inventory=inv)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "BehaviorLogic.cardinality" in rule_ids


def test_cardinality_inventory_fewer_warns(tmp_path):
    plan = _setup_plan(tmp_path, VALID_BEHAVIOR_LOGIC)
    # Inventory has only 1 entry but doc has 3 BL sections
    inv = _write_inventory(tmp_path, ["BL001_CreateUser"])
    result = validate(plan, tmp_path, scout_bl_inventory=inv)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "BehaviorLogic.cardinality" in rule_ids


# ---------------------------------------------------------------------------
# Tests — file_schema_missing (BehaviorLogic.file_schema_missing, warning)
# ---------------------------------------------------------------------------

def test_bl_file_schema_missing_warns(tmp_path):
    plan = _setup_plan(tmp_path, FILE_EXCHANGE_WITHOUT_SCHEMA)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "BehaviorLogic.file_schema_missing" in rule_ids


def test_bl_file_schema_present_passes(tmp_path):
    plan = _setup_plan(tmp_path, FILE_EXCHANGE_WITH_SCHEMA)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "BehaviorLogic.file_schema_missing" not in rule_ids


def test_bl_non_file_exchange_no_warn(tmp_path):
    plan = _setup_plan(tmp_path, NON_FILE_EXCHANGE_BL)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "BehaviorLogic.file_schema_missing" not in rule_ids


def test_bl_na_misuse_warns(tmp_path):
    """Vocab-matching block that declares the N/A string anyway is a contradiction — warn."""
    plan = _setup_plan(tmp_path, FILE_EXCHANGE_NA_MISUSE)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "BehaviorLogic.file_schema_missing" in rule_ids


def test_bl_important_substring_no_false_positive(tmp_path):
    """'important' must not be mistaken for the 'import' vocab word."""
    plan = _setup_plan(tmp_path, IMPORTANT_SUBSTRING_GUARD_BL)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "BehaviorLogic.file_schema_missing" not in rule_ids


# ---------------------------------------------------------------------------
# Tests — CLI / main()
# ---------------------------------------------------------------------------

def test_main_plan_dir_pass(tmp_path, capsys):
    plan = _setup_plan(tmp_path, VALID_BEHAVIOR_LOGIC)
    rc = main(["--plan-dir", str(plan), "--project-root", str(tmp_path)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "PASS"


def test_main_single_file_fail(tmp_path, capsys):
    plan = _setup_plan(tmp_path, DUPLICATE_BL)
    bl_file = plan / "artifacts" / "behavior-logic.md"
    rc = main(["--behavior-logic-file", str(bl_file), "--project-root", str(tmp_path)])
    assert rc == 1


def test_main_with_scout_inventory(tmp_path, capsys):
    plan = _setup_plan(tmp_path, VALID_BEHAVIOR_LOGIC)
    inv = _write_inventory(tmp_path, ["BL001_CreateUser", "BL002_UpdateOrder", "BL003_SendNotification"])
    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--scout-bl-inventory", str(inv),
    ])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "PASS"


def test_main_summary_out(tmp_path):
    plan = _setup_plan(tmp_path, VALID_BEHAVIOR_LOGIC)
    summary_path = tmp_path / "validation-summary.json"
    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--summary-out", str(summary_path),
    ])
    assert rc == 0
    assert summary_path.is_file()
    summary = json.loads(summary_path.read_text())
    assert "behavior_logic" in summary["validators"]
    assert summary["validators"]["behavior_logic"]["status"] == "PASS"


def test_main_invalid_plan_dir(tmp_path, capsys):
    rc = main(["--plan-dir", str(tmp_path / "nonexistent"), "--project-root", str(tmp_path)])
    assert rc == 2


# ---------------------------------------------------------------------------
# Tests — Phase 03 (rebuild-spec 27.0.0): behavior-logic-template.md rewrite
# [Hard gate 2] the BA-first + Dev Appendix rewrite must still satisfy every
# deterministic rule this validator enforces: BL### code forms, single index
# header, and Source File/Source Symbol presence on every BL### block.
# ---------------------------------------------------------------------------

def _render_template_skeleton() -> str:
    """Instantiate the template's placeholders with concrete example values.

    The raw template ships `{BL001_CODE}`-style placeholders, which never match
    BL_H2_RE — validating the raw file would trivially "pass" by finding zero BL
    sections. Substituting real values proves the *rewritten structure* (BA index
    banded by type + Dev Appendix with Source File/Symbol) still satisfies every
    rule the deterministic validator enforces.
    """
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    substitutions = {
        "{PROJECT_NAME}": "TestProject",
        "{DATE}": "2026-08-14",
        "{SCOPE}": "full",
        "{TYPE_A}": "mail",
        "{TYPE_B}": "queue-worker",
        "{BL001_CODE}": "BL001",
        "{BL001_NAME}": "SendWelcomeMail",
        "{BL002_CODE}": "BL002",
        "{BL002_NAME}": "ProcessQueueJob",
        "{BL003_CODE}": "BL003",
        "{BL003_NAME}": "SyncInventory",
        "{TYPE}": "mail",
        "{TRIGGER}": "UserRegistered event",
        "{DESCRIPTION}": "Test description.",
        "{MODULE_1}": "TestModule1",
        "{MODULE_2}": "TestModule2",
        "{ROUTE_METHOD}": "GET",
        "{ROUTE_PATH}": "/test",
        "{MODEL_ENTITY}": "TestModel",
        "{POPULATED_BY_FRAGMENTS}": "",
    }
    for placeholder, value in substitutions.items():
        text = text.replace(placeholder, value)
    return text


def test_template_skeleton_passes_validator(tmp_path):
    """[Hard gate 2] The rewritten template's own (placeholder-filled) skeleton PASSES —
    exactly one Index section, unique BL### codes, Source File + Source Symbol present."""
    plan = _setup_plan(tmp_path, _render_template_skeleton())
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0, result["issues"]
    rule_ids = {i["rule_id"] for i in result["issues"]}
    assert "BehaviorLogic.required_sections" not in rule_ids
    assert "BehaviorLogic.single_header" not in rule_ids
    assert "BehaviorLogic.no_dup_bl" not in rule_ids
    assert "BehaviorLogic.source_present" not in rule_ids


def test_cli_negated_probe_missing_source_symbol_fails(tmp_path):
    """[Hard gate 2] Real non-zero exit — negated-command probe (subprocess, not just a
    pytest assertion on an in-process return value). A BL### block missing Source Symbol
    must fail the CLI outright."""
    plan = _setup_plan(tmp_path, MISSING_SOURCE_SYMBOL)
    bl_file = plan / "artifacts" / "behavior-logic.md"
    script = Path(__file__).resolve().parent.parent / "validate_behavior_logic.py"
    result = subprocess.run(
        [sys.executable, str(script), "--behavior-logic-file", str(bl_file),
         "--project-root", str(tmp_path)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0, (
        f"expected non-zero exit for missing Source Symbol, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# code_format — the mandated `BL###_NameSlug` heading contract is enforced
# ---------------------------------------------------------------------------

COLON_FORMAT_BL = """\
## BL001: CreateUser

**Source File:** `app/Services/UserService.php`
**Source Symbol:** `UserService::create`
**Type**: observer

### Description

Creates a user.
"""


def _rule_ids(result, rule_id):
    return [i for i in result["issues"] if i["rule_id"] == rule_id]


def test_colon_heading_flagged_as_code_format_violation(tmp_path):
    """`## BL001: Name` violates code-formats.md `BL###_NameSlug` and must be reported.

    Regression: BL_H2_RE accepts both shapes, so 72/103 non-conforming headings in a
    real corpus passed silently while any consumer keying on `BL###_` skipped them.
    """
    plan = _setup_plan(tmp_path, COLON_FORMAT_BL)
    result = validate(plan, tmp_path)
    found = _rule_ids(result, "BehaviorLogic.code_format")
    assert len(found) == 1
    assert found[0]["severity"] == "warning"
    assert "BL###_NameSlug" in found[0]["message"]


def test_underscore_heading_is_not_flagged(tmp_path):
    """The compliant form must NOT be flagged — `_` is a word char, so a trailing
    `\\b` in the check would have exempted the wrong half of the population."""
    plan = _setup_plan(tmp_path, VALID_BEHAVIOR_LOGIC)
    result = validate(plan, tmp_path)
    assert _rule_ids(result, "BehaviorLogic.code_format") == []


def test_code_format_violation_does_not_suppress_other_checks(tmp_path):
    """A malformed heading is still PARSED, so its section keeps its other checks."""
    plan = _setup_plan(tmp_path, "## BL001: NoSourceFields\n\n### Description\n\nx\n")
    result = validate(plan, tmp_path)
    assert _rule_ids(result, "BehaviorLogic.code_format")
    assert _rule_ids(result, "BehaviorLogic.source_present")


# ---------------------------------------------------------------------------
# cardinality — counter must not count prose or empty-category sentinels
# ---------------------------------------------------------------------------

def test_cardinality_skips_sentinels_and_comment_prose(tmp_path):
    """Regression: the counter took "any non-#/non-// line", so HTML-comment header
    lines and `(none found)` sentinels inflated the total and produced a false
    mismatch on a correct document."""
    plan = _setup_plan(tmp_path, VALID_BEHAVIOR_LOGIC)   # 3 BL sections
    inv = tmp_path / "inv.md"
    inv.write_text(
        "<!-- Rebuilt deterministically by the orchestrator from bl-source-patterns.md\n"
        "     Format contract: `- <category>: <path>` — one entry per BL item. -->\n"
        "\n"
        "### queue-worker\n"
        "\n"
        "- queue-worker: app/Services/UserService.php\n"
        "- queue-worker: app/Services/OrderService.php\n"
        "- queue-worker: app/Jobs/NotifyJob.php\n"
        "\n"
        "### observer\n"
        "\n"
        "- observer: _(none found)_\n",
        encoding="utf-8",
    )
    result = validate(plan, tmp_path, scout_bl_inventory=inv)
    assert _rule_ids(result, "BehaviorLogic.cardinality") == []


def test_cardinality_still_detects_a_real_mismatch(tmp_path):
    """The gate must still be able to FIRE — a counter that never mismatches is
    not a gate."""
    plan = _setup_plan(tmp_path, VALID_BEHAVIOR_LOGIC)   # 3 BL sections
    inv = tmp_path / "inv.md"
    inv.write_text(
        "- queue-worker: a.rb\n"
        "- queue-worker: b.rb\n"
        "- queue-worker: c.rb\n"
        "- queue-worker: d.rb\n",   # 4 entries vs 3 sections
        encoding="utf-8",
    )
    result = validate(plan, tmp_path, scout_bl_inventory=inv)
    found = _rule_ids(result, "BehaviorLogic.cardinality")
    assert len(found) == 1
    assert "4" in found[0]["message"] and "3" in found[0]["message"]


def test_cardinality_plain_line_inventory_still_supported(tmp_path):
    """The plain one-entry-per-line shape must keep working alongside the contract shape."""
    plan = _setup_plan(tmp_path, VALID_BEHAVIOR_LOGIC)
    inv = _write_inventory(tmp_path, ["BL001_CreateUser", "BL002_UpdateOrder", "BL003_SendNotification"])
    result = validate(plan, tmp_path, scout_bl_inventory=inv)
    assert _rule_ids(result, "BehaviorLogic.cardinality") == []
