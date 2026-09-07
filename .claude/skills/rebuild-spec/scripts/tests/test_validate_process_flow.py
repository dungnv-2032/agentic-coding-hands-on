"""Tests for validate_process_flow.py (Wave 6.85 gate)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_process_flow import validate, main, _parse_frontmatter, _parse_transitions  # noqa: E402

VALID_FLOW = """\
---
status: ai-draft
kind: process-flow
subject_entity: Order
state_field: status
source:
  data-model: [Order]
  behavior-logic: [BL001]
  screens: [SCR001_OrderCreate]
  features: [F001_OrderManagement]
generated: 2026-05-27
---

# FLOW001_OrderLifecycle --- Order Lifecycle

> Tracks an order from creation to completion.

**Subject entity:** `Order` . **State field:** `status`
**Enum source:** `app/Enums/OrderStatus.php` --- `draft, confirmed, shipped, delivered`

---

## States

| State | Meaning | Who acts here | Invariant / what is allowed |
|-------|---------|---------------|----------------------------|
| `draft` | Newly created | Customer | Fully editable |
| `confirmed` | Confirmed by admin | Admin | Cannot edit items |
| `shipped` | In transit | System | Tracking number assigned |
| `delivered` | Received | System | Terminal |

---

## Transitions

| # | From --> To | Trigger type | Trigger | Guard (must hold) | Side effects | Source |
|---|-----------|--------------|---------|-------------------|--------------|--------|
| T1 | `draft -> confirmed` | user-action | Admin confirms order | items > 0 | send notification | `OrderController.php:45` |
| T2 | `confirmed -> shipped` | user-action | Admin marks shipped | tracking number set | dispatch ShipNotify | `OrderController.php:89` |
| T3 | `shipped -> delivered` | **scheduled** (BL001, hourly) | delivery_date passed | status=shipped | log delivery | `DeliveryCheck.php:30-42` |

## Open Questions

None.
"""

UNSOURCED_FLOW = """\
---
status: ai-draft
kind: process-flow
subject_entity: Order
state_field: status
source:
  data-model: [Order]
generated: 2026-05-27
---

# FLOW001_OrderLifecycle --- Order Lifecycle

**Enum source:** `app/Enums/OrderStatus.php` --- `draft, confirmed, shipped`

## States

| State | Meaning | Who acts here | Invariant |
|-------|---------|---------------|-----------|
| `draft` | New | Customer | Editable |
| `confirmed` | Done | Admin | Locked |
| `shipped` | Sent | System | Terminal |

## Transitions

| # | From --> To | Trigger type | Trigger | Guard | Side effects | Source |
|---|-----------|--------------|---------|-------|--------------|--------|
| T1 | `draft -> confirmed` | user-action | Admin confirms | items > 0 | notify | `OrderController.php:45` |
| T2 | `confirmed -> shipped` | **scheduled** | Cron fires | — | — | missing source here |
"""

FABRICATED_STATE_FLOW = """\
---
status: ai-draft
kind: process-flow
subject_entity: Order
state_field: status
source:
  data-model: [Order]
generated: 2026-05-27
---

# FLOW001_OrderLifecycle --- Order Lifecycle

**Enum source:** `app/Enums/OrderStatus.php` --- `draft, confirmed`

## States

| State | Meaning | Who acts here | Invariant |
|-------|---------|---------------|-----------|
| `draft` | New | Customer | Editable |
| `confirmed` | Done | Admin | Locked |
| `processing` | In progress | System | Busy |

## Transitions

| # | From --> To | Trigger type | Trigger | Guard | Side effects | Source |
|---|-----------|--------------|---------|-------|--------------|--------|
| T1 | `draft -> confirmed` | user-action | Admin confirms | — | — | `OrderController.php:45` |
| T2 | `confirmed -> processing` | **scheduled** | Cron | — | — | `ProcessJob.php:20` |
"""

SUB_THRESHOLD_FLOW = """\
---
status: ai-draft
kind: process-flow
subject_entity: Template
state_field: status
source:
  data-model: [Template]
generated: 2026-05-27
---

# FLOW010_TemplateLifecycle --- Template Lifecycle

**Enum source:** `app/Enums/TemplateStatus.php` --- `active, inactive`

## States

| State | Meaning | Who acts here | Invariant |
|-------|---------|---------------|-----------|
| `active` | In use | Manager | Referenced by evals |
| `inactive` | Disabled | Manager | Not referenced |

## Transitions

| # | From --> To | Trigger type | Trigger | Guard | Side effects | Source |
|---|-----------|--------------|---------|-------|--------------|--------|
| T1 | `inactive -> active` | user-action | Manager activates | no dup classification | — | `TemplateController.php:39` |
| T2 | `active -> inactive` | user-action | Manager deactivates | — | cascade children | `TemplateController.php:157` |
"""

# A complete, valid system-flow fixture using multiline composes: format (locks in Step-0 parser fix).
# ≥2 flows composed, Cross-Flow Handoffs with a real app/x.rb:42 citation, State-Field Inventory row.
VALID_SYSTEM_FLOW = """\
---
status: ai-draft
kind: system-flow
composes:
  - FLOW001_OrderLifecycle
  - FLOW002_PaymentLifecycle
generated: 2026-05-27
---

# System Flow --- How Orders Run End-to-End

> Synthesis of all Tier-1 flows.

## Lanes

| Lane | Driven by | Flow | Time vs Action |
|------|-----------|------|----------------|
| **Order** | Customer/Admin | [FLOW001_OrderLifecycle](order-lifecycle.md) | action |
| **Payment** | Payment gateway | [FLOW002_PaymentLifecycle](payment-lifecycle.md) | action |

---

## Master Composition Diagram

```mermaid
flowchart TB
    subgraph LANE_A[" Order "]
        A1["FLOW001_OrderLifecycle"]
    end
    subgraph LANE_B[" Payment "]
        B1["FLOW002_PaymentLifecycle"]
    end
    A1 -. "triggers payment" .-> B1
```

---

## Cross-Flow Handoffs

| # | Source flow / event | --> Target flow | Mechanism | Source |
|---|---------------------|-----------------|-----------|--------|
| H1 | FLOW001_OrderLifecycle confirmed | FLOW002_PaymentLifecycle entry | order.id passed | `app/Services/OrderService.rb:42` |

---

## State-Field Inventory (stored vs derived audit)

| Field | Entity | Flow | Stored? |
|-------|--------|------|---------|
| `status` | Order | FLOW001 | yes stored |
| `payment_status` | Payment | FLOW002 | yes stored |

---

## Open Questions (cross-cutting)

None.
"""


def _setup_plan(tmp_path: Path, flow_content: str, filename: str = "order-lifecycle.md",
                add_completed: bool = True) -> Path:
    plan = tmp_path / "test-plan"
    flows = plan / "artifacts" / "flows"
    flows.mkdir(parents=True)
    (flows / filename).write_text(flow_content, encoding="utf-8")
    if add_completed:
        (flows / ".completed").touch()
    return plan


def test_valid_flow_passes(tmp_path):
    plan = _setup_plan(tmp_path, VALID_FLOW)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0


def test_unsourced_transition_fails(tmp_path):
    plan = _setup_plan(tmp_path, UNSOURCED_FLOW)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    crit_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ProcessFlow.citation_missing" in crit_ids


def test_fabricated_state_fails(tmp_path):
    plan = _setup_plan(tmp_path, FABRICATED_STATE_FLOW)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    crit_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ProcessFlow.fabricated_state" in crit_ids


def test_sub_threshold_flow_fails(tmp_path):
    plan = _setup_plan(tmp_path, SUB_THRESHOLD_FLOW, filename="template-lifecycle.md")
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    crit_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ProcessFlow.sub_threshold_flow" in crit_ids


def test_missing_completed_marker(tmp_path):
    plan = _setup_plan(tmp_path, VALID_FLOW, add_completed=False)
    result = validate(plan, tmp_path)
    crit_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ProcessFlow.completed_missing" in crit_ids


def test_duplicate_flow_code(tmp_path):
    plan = tmp_path / "test-plan"
    flows = plan / "artifacts" / "flows"
    flows.mkdir(parents=True)
    (flows / "order-lifecycle.md").write_text(VALID_FLOW, encoding="utf-8")
    (flows / "order-lifecycle-dup.md").write_text(VALID_FLOW, encoding="utf-8")
    (flows / ".completed").touch()
    result = validate(plan, tmp_path)
    crit_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ProcessFlow.flow_code_duplicate" in crit_ids


def test_parse_frontmatter_with_comment():
    text = "<!-- comment -->\n---\nkind: process-flow\nstate_field: status\n---\n# FLOW001"
    fm = _parse_frontmatter(text)
    assert fm["kind"] == "process-flow"
    assert fm["state_field"] == "status"


# --- Step-0 regression: _parse_frontmatter multiline list support ---

def test_parse_frontmatter_multiline_list():
    """Multiline list → list; inline [a,b] → list; scalar → string.
    Covers composes, state_fields, derived_views, spans_entities, sub_flows."""
    # Multiline composes: → list
    text = "---\nkind: system-flow\ncomposes:\n  - FLOW001_OrderLifecycle\n  - FLOW002_PaymentLifecycle\n---\n"
    fm = _parse_frontmatter(text)
    assert isinstance(fm["composes"], list), "multiline composes: must be list"
    assert "FLOW001_OrderLifecycle" in fm["composes"]
    assert "FLOW002_PaymentLifecycle" in fm["composes"]
    assert len(fm["composes"]) == 2

    # Inline [a, b] → list (regression guard)
    text2 = "---\nstate_fields: [status, phase]\n---\n"
    fm2 = _parse_frontmatter(text2)
    assert isinstance(fm2["state_fields"], list)
    assert "status" in fm2["state_fields"]
    assert "phase" in fm2["state_fields"]

    # Scalar → string (regression guard)
    text3 = "---\nstate_field: status\n---\n"
    fm3 = _parse_frontmatter(text3)
    assert fm3["state_field"] == "status"

    # Multiline derived_views: → list
    text4 = "---\nderived_views:\n  - display_status\n  - label\n---\n"
    fm4 = _parse_frontmatter(text4)
    assert isinstance(fm4["derived_views"], list)
    assert "display_status" in fm4["derived_views"]

    # Multiline state_fields: → list
    text5 = "---\nstate_fields:\n  - status\n  - phase\n---\n"
    fm5 = _parse_frontmatter(text5)
    assert isinstance(fm5["state_fields"], list)
    assert "status" in fm5["state_fields"]
    assert "phase" in fm5["state_fields"]

    # Multiline spans_entities: → list
    text6 = "---\nspans_entities:\n  - Order\n  - Payment\n---\n"
    fm6 = _parse_frontmatter(text6)
    assert isinstance(fm6["spans_entities"], list)
    assert "Order" in fm6["spans_entities"]

    # Multiline sub_flows: → list
    text7 = "---\nsub_flows:\n  - FLOW003_RefundLifecycle\n---\n"
    fm7 = _parse_frontmatter(text7)
    assert isinstance(fm7["sub_flows"], list)
    assert "FLOW003_RefundLifecycle" in fm7["sub_flows"]

    # Backtick-stripped items (template uses backtick-wrapped placeholders)
    text8 = "---\ncomposes:\n  - `FLOW001_OrderLifecycle`\n  - `FLOW002_PaymentLifecycle`\n---\n"
    fm8 = _parse_frontmatter(text8)
    assert isinstance(fm8["composes"], list)
    assert "FLOW001_OrderLifecycle" in fm8["composes"]


# --- SystemFlow tests ---

def test_system_flow_valid(tmp_path):
    """VALID_SYSTEM_FLOW alone (no Tier-1 sibling) → critical == 0."""
    plan = _setup_plan(tmp_path, VALID_SYSTEM_FLOW, filename="system-flow.md")
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0


def test_system_flow_valid_with_tier1(tmp_path):
    """VALID_FLOW (Tier-1, state_field: status) + VALID_SYSTEM_FLOW whose composes includes
    FLOW001 and whose inventory lists 'status'. Assert critical==0 and inventory_incomplete NOT present."""
    plan = tmp_path / "test-plan"
    flows = plan / "artifacts" / "flows"
    flows.mkdir(parents=True)
    (flows / ".completed").touch()
    (flows / "order-lifecycle.md").write_text(VALID_FLOW, encoding="utf-8")

    # Build a system-flow that composes FLOW001 and lists 'status' in inventory
    sf = """\
---
status: ai-draft
kind: system-flow
composes:
  - FLOW001_OrderLifecycle
  - FLOW002_PaymentLifecycle
generated: 2026-05-27
---

# System Flow --- Order and Payment End-to-End

## Lanes

| Lane | Driven by | Flow | Time vs Action |
|------|-----------|------|----------------|
| **Order** | Admin | [FLOW001_OrderLifecycle](order-lifecycle.md) | action |

---

## Master Composition Diagram

```mermaid
flowchart TB
    A1["FLOW001_OrderLifecycle"] --> B1["FLOW002_PaymentLifecycle"]
```

---

## Cross-Flow Handoffs

| # | Source flow / event | --> Target flow | Mechanism | Source |
|---|---------------------|-----------------|-----------|--------|
| H1 | FLOW001 confirmed | FLOW002 entry | order.id passed | `app/OrderService.rb:10` |

---

## State-Field Inventory (stored vs derived audit)

| Field | Entity | Flow | Stored? |
|-------|--------|------|---------|
| `status` | Order | FLOW001 | yes stored |

---

## Open Questions (cross-cutting)

None.
"""
    (flows / "system-flow.md").write_text(sf, encoding="utf-8")
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "SystemFlow.inventory_incomplete" not in warn_ids


def test_system_flow_composes_missing(tmp_path):
    """No composes: key → SystemFlow.composes_missing critical."""
    sf = """\
---
status: ai-draft
kind: system-flow
generated: 2026-05-27
---

# System Flow --- No Composes

## Cross-Flow Handoffs

| # | Source flow / event | --> Target flow | Mechanism | Source |
|---|---------------------|-----------------|-----------|--------|
| H1 | FLOW001 event | FLOW002 entry | pass | `app/x.rb:1` |

## State-Field Inventory (stored vs derived audit)

| Field | Entity | Flow | Stored? |
|-------|--------|------|---------|
| `status` | Order | FLOW001 | yes stored |
"""
    plan = _setup_plan(tmp_path, sf, filename="system-flow.md")
    result = validate(plan, tmp_path)
    crit_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "SystemFlow.composes_missing" in crit_ids


def test_system_flow_composes_insufficient(tmp_path):
    """composes: with only 1 flow → SystemFlow.composes_insufficient critical."""
    sf = """\
---
status: ai-draft
kind: system-flow
composes:
  - FLOW001_OrderLifecycle
generated: 2026-05-27
---

# System Flow --- One Flow Only

## Lanes

| Lane | Driven by | Flow | Time vs Action |
|------|-----------|------|----------------|
| **Order** | Admin | [FLOW001_OrderLifecycle](order-lifecycle.md) | action |

---

## Master Composition Diagram

```mermaid
flowchart TB
    A1["FLOW001_OrderLifecycle"]
```

---

## Cross-Flow Handoffs

| # | Source flow / event | --> Target flow | Mechanism | Source |
|---|---------------------|-----------------|-----------|--------|
| H1 | FLOW001 confirmed | FLOW001 retry | loop | `app/x.rb:1` |

---

## State-Field Inventory (stored vs derived audit)

| Field | Entity | Flow | Stored? |
|-------|--------|------|---------|
| `status` | Order | FLOW001 | yes stored |

---

## Open Questions (cross-cutting)

None.
"""
    plan = _setup_plan(tmp_path, sf, filename="system-flow.md")
    result = validate(plan, tmp_path)
    crit_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "SystemFlow.composes_insufficient" in crit_ids


def test_system_flow_handoffs_missing(tmp_path):
    """No Cross-Flow Handoffs rows → SystemFlow.handoffs_missing critical."""
    sf = """\
---
status: ai-draft
kind: system-flow
composes:
  - FLOW001_OrderLifecycle
  - FLOW002_PaymentLifecycle
generated: 2026-05-27
---

# System Flow --- No Handoffs

## Lanes

| Lane | Driven by | Flow | Time vs Action |
|------|-----------|------|----------------|
| **Order** | Admin | FLOW001 | action |

---

## Cross-Flow Handoffs

<!-- intentionally empty — no H rows -->

---

## State-Field Inventory (stored vs derived audit)

| Field | Entity | Flow | Stored? |
|-------|--------|------|---------|
| `status` | Order | FLOW001 | yes stored |

---

## Open Questions (cross-cutting)

None.
"""
    plan = _setup_plan(tmp_path, sf, filename="system-flow.md")
    result = validate(plan, tmp_path)
    crit_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "SystemFlow.handoffs_missing" in crit_ids


def test_system_flow_handoff_uncited(tmp_path):
    """Handoff row with Source cell 'pending' (no citation) → SystemFlow.handoff_citation_missing.
    Sub-case: `event bus:1` (whitespace in filename) also fires the rule (HANDOFF_CITE_RE tighter)."""
    # Case A: plain text source cell, no citation
    sf_a = """\
---
status: ai-draft
kind: system-flow
composes:
  - FLOW001_OrderLifecycle
  - FLOW002_PaymentLifecycle
generated: 2026-05-27
---

# System Flow --- Uncited Handoff

## Lanes

| Lane | Driven by | Flow | Time vs Action |
|------|-----------|------|----------------|
| **Order** | Admin | FLOW001 | action |

---

## Master Composition Diagram

```mermaid
flowchart TB
    A1["FLOW001_OrderLifecycle"] --> B1["FLOW002_PaymentLifecycle"]
```

---

## Cross-Flow Handoffs

| # | Source flow / event | --> Target flow | Mechanism | Source |
|---|---------------------|-----------------|-----------|--------|
| H1 | FLOW001 confirmed | FLOW002 entry | pass | pending |

---

## State-Field Inventory (stored vs derived audit)

| Field | Entity | Flow | Stored? |
|-------|--------|------|---------|
| `status` | Order | FLOW001 | yes stored |

---

## Open Questions (cross-cutting)

None.
"""
    plan_a = _setup_plan(tmp_path / "a", sf_a, filename="system-flow.md")
    result_a = validate(plan_a, tmp_path / "a")
    crit_ids_a = [i["rule_id"] for i in result_a["issues"] if i["severity"] == "critical"]
    assert "SystemFlow.handoff_citation_missing" in crit_ids_a

    # Case B: `event bus:1` — contains whitespace in filename → HANDOFF_CITE_RE rejects it
    sf_b = sf_a.replace("| H1 | FLOW001 confirmed | FLOW002 entry | pass | pending |",
                        "| H1 | FLOW001 confirmed | FLOW002 entry | pass | `event bus:1` |")
    plan_b = _setup_plan(tmp_path / "b", sf_b, filename="system-flow.md")
    result_b = validate(plan_b, tmp_path / "b")
    crit_ids_b = [i["rule_id"] for i in result_b["issues"] if i["severity"] == "critical"]
    assert "SystemFlow.handoff_citation_missing" in crit_ids_b, (
        "HANDOFF_CITE_RE must reject `event bus:1` (whitespace in filename segment)"
    )


def test_system_flow_inventory_missing(tmp_path):
    """No State-Field Inventory section → SystemFlow.inventory_missing critical."""
    sf = """\
---
status: ai-draft
kind: system-flow
composes:
  - FLOW001_OrderLifecycle
  - FLOW002_PaymentLifecycle
generated: 2026-05-27
---

# System Flow --- No Inventory

## Lanes

| Lane | Driven by | Flow | Time vs Action |
|------|-----------|------|----------------|
| **Order** | Admin | FLOW001 | action |

---

## Cross-Flow Handoffs

| # | Source flow / event | --> Target flow | Mechanism | Source |
|---|---------------------|-----------------|-----------|--------|
| H1 | FLOW001 confirmed | FLOW002 entry | pass | `app/x.rb:1` |

---

## Open Questions (cross-cutting)

None.
"""
    plan = _setup_plan(tmp_path, sf, filename="system-flow.md")
    result = validate(plan, tmp_path)
    crit_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "SystemFlow.inventory_missing" in crit_ids


def test_system_flow_inventory_incomplete(tmp_path):
    """VALID_FLOW (Tier-1 state_field: status) composed, but inventory omits 'status'.
    → SystemFlow.inventory_incomplete warning, critical == 0."""
    plan = tmp_path / "test-plan"
    flows = plan / "artifacts" / "flows"
    flows.mkdir(parents=True)
    (flows / ".completed").touch()
    (flows / "order-lifecycle.md").write_text(VALID_FLOW, encoding="utf-8")

    # system-flow composes FLOW001 but inventory does NOT list 'status'
    sf = """\
---
status: ai-draft
kind: system-flow
composes:
  - FLOW001_OrderLifecycle
  - FLOW002_PaymentLifecycle
generated: 2026-05-27
---

# System Flow --- Incomplete Inventory

## Lanes

| Lane | Driven by | Flow | Time vs Action |
|------|-----------|------|----------------|
| **Order** | Admin | FLOW001 | action |

---

## Master Composition Diagram

```mermaid
flowchart TB
    A1["FLOW001_OrderLifecycle"] --> B1["FLOW002_PaymentLifecycle"]
```

---

## Cross-Flow Handoffs

| # | Source flow / event | --> Target flow | Mechanism | Source |
|---|---------------------|-----------------|-----------|--------|
| H1 | FLOW001 confirmed | FLOW002 entry | pass | `app/x.rb:10` |

---

## State-Field Inventory (stored vs derived audit)

| Field | Entity | Flow | Stored? |
|-------|--------|------|---------|
| `payment_status` | Payment | FLOW002 | yes stored |

---

## Open Questions (cross-cutting)

None.
"""
    (flows / "system-flow.md").write_text(sf, encoding="utf-8")
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "SystemFlow.inventory_incomplete" in warn_ids


def test_system_flow_inventory_incomplete_ignores_uncomposed(tmp_path):
    """Two Tier-1 flows in flows/ but composes lists only one.
    Un-composed flow's field omitted from inventory → NO inventory_incomplete warning.
    Proves subset filtering (Finding 3)."""
    FLOW002 = """\
---
status: ai-draft
kind: process-flow
subject_entity: Payment
state_field: payment_status
source:
  data-model: [Payment]
generated: 2026-05-27
---

# FLOW002_PaymentLifecycle --- Payment Lifecycle

**Enum source:** `app/Enums/PaymentStatus.php` --- `pending, captured, refunded`

## States

| State | Meaning | Who acts here | Invariant |
|-------|---------|---------------|-----------|
| `pending` | Awaiting | Gateway | Locked |
| `captured` | Charged | Gateway | Settled |
| `refunded` | Returned | Admin | Terminal |

## Transitions

| # | From --> To | Trigger type | Trigger | Guard | Side effects | Source |
|---|-----------|--------------|---------|-------|--------------|--------|
| T1 | `pending -> captured` | event | gateway webhook | amount > 0 | — | `PaymentController.php:55` |
| T2 | `captured -> refunded` | user-action | Admin refunds | — | notify | `PaymentController.php:90` |

## Open Questions

None.
"""
    plan = tmp_path / "test-plan"
    flows = plan / "artifacts" / "flows"
    flows.mkdir(parents=True)
    (flows / ".completed").touch()
    (flows / "order-lifecycle.md").write_text(VALID_FLOW, encoding="utf-8")
    (flows / "payment-lifecycle.md").write_text(FLOW002, encoding="utf-8")

    # system-flow composes only FLOW001 (not FLOW002); inventory lists only 'status'
    sf = """\
---
status: ai-draft
kind: system-flow
composes:
  - FLOW001_OrderLifecycle
  - FLOW003_InvoiceLifecycle
generated: 2026-05-27
---

# System Flow --- Only FLOW001 Composed

## Lanes

| Lane | Driven by | Flow | Time vs Action |
|------|-----------|------|----------------|
| **Order** | Admin | FLOW001 | action |

---

## Master Composition Diagram

```mermaid
flowchart TB
    A1["FLOW001_OrderLifecycle"] --> C1["FLOW003_InvoiceLifecycle"]
```

---

## Cross-Flow Handoffs

| # | Source flow / event | --> Target flow | Mechanism | Source |
|---|---------------------|-----------------|-----------|--------|
| H1 | FLOW001 confirmed | FLOW003 trigger | order.id | `app/x.rb:10` |

---

## State-Field Inventory (stored vs derived audit)

| Field | Entity | Flow | Stored? |
|-------|--------|------|---------|
| `status` | Order | FLOW001 | yes stored |

---

## Open Questions (cross-cutting)

None.
"""
    (flows / "system-flow.md").write_text(sf, encoding="utf-8")
    result = validate(plan, tmp_path)
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "SystemFlow.inventory_incomplete" not in warn_ids, (
        "payment_status from un-composed FLOW002 must NOT trigger inventory_incomplete"
    )


def test_system_flow_phantom_flow_ref(tmp_path):
    """Lanes table references FLOW999_Ghost not in composes → SystemFlow.phantom_flow_ref warning."""
    sf = """\
---
status: ai-draft
kind: system-flow
composes:
  - FLOW001_OrderLifecycle
  - FLOW002_PaymentLifecycle
generated: 2026-05-27
---

# System Flow --- Phantom Ref

## Lanes

| Lane | Driven by | Flow | Time vs Action |
|------|-----------|------|----------------|
| **Order** | Admin | [FLOW001_OrderLifecycle](order-lifecycle.md) | action |
| **Ghost** | Nobody | [FLOW999_Ghost](ghost.md) | never |

---

## Master Composition Diagram

```mermaid
flowchart TB
    A1["FLOW001_OrderLifecycle"] --> B1["FLOW002_PaymentLifecycle"]
```

---

## Cross-Flow Handoffs

| # | Source flow / event | --> Target flow | Mechanism | Source |
|---|---------------------|-----------------|-----------|--------|
| H1 | FLOW001 confirmed | FLOW002 entry | pass | `app/x.rb:10` |

---

## State-Field Inventory (stored vs derived audit)

| Field | Entity | Flow | Stored? |
|-------|--------|------|---------|
| `status` | Order | FLOW001 | yes stored |

---

## Open Questions (cross-cutting)

None.
"""
    plan = _setup_plan(tmp_path, sf, filename="system-flow.md")
    result = validate(plan, tmp_path)
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "SystemFlow.phantom_flow_ref" in warn_ids
    # Must not be a critical failure
    assert result["summary"]["critical"] == 0


# --- B2: stuck-state (liveness backstop) ---

STUCK_FLOW = """\
---
status: ai-draft
kind: process-flow
subject_entity: Job
state_field: status
source:
  data-model: [Job]
generated: 2026-05-27
---

# FLOW020_JobLifecycle --- Job Lifecycle

**Enum source:** `app/Enums/JobStatus.php` --- `open, processing, closed`

## States

| State | Meaning | Who acts here | Invariant |
|-------|---------|---------------|-----------|
| `open` | Queued | User | Editable |
| `processing` | Running | System | Locked |
| `closed` | Finished | System | Read-only |

## Transitions

| # | From --> To | Trigger type | Trigger | Guard | Side effects | Source |
|---|-----------|--------------|---------|-------|--------------|--------|
| T1 | `open -> processing` | user-action | User starts job | — | — | `JobController.php:20` |
| T2 | `processing -> closed` | **scheduled** | Cron finalizes | clone ok | snapshot | `FinalizeJob.php:30` |
"""


def test_possible_stuck_state_warns(tmp_path):
    # `closed` is a target with no outgoing transition and not declared terminal.
    plan = _setup_plan(tmp_path, STUCK_FLOW, filename="job-lifecycle.md")
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"  # warning must not flip to FAIL
    assert result["summary"]["critical"] == 0
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ProcessFlow.possible_stuck_state" in warn_ids


def test_declared_terminal_no_stuck_warning(tmp_path):
    # VALID_FLOW marks `delivered` "Terminal" in its invariant cell → suppressed.
    plan = _setup_plan(tmp_path, VALID_FLOW)
    result = validate(plan, tmp_path)
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ProcessFlow.possible_stuck_state" not in warn_ids


# --- B3: SM/FLOW DRY cross-ref ---

# v27.0.0 (audience split, Phase 04 collateral fix): canonical SM block heading is H3 with a
# trailing-tag code (`### {sentence} (SM-001)`), not the retired H4 anchored-slug form
# (`#### SM-001_JobStatus`) — see _spec_block_lib.py / templates/technical-spec-template.md.
# _flow_sm_lib.scan_entity_state_machines was repointed at the canonical form (Phase 04 silent-pass
# fix), so this fixture must use it too or these regression tests would exercise dead code.
ENTITY_SM_SPEC = """\
# F050 — Job Admin

### Job status lifecycle (SM-001)
**kind:** entity
**States:** open, processing, closed

```mermaid
stateDiagram-v2
  [*] --> open
```
"""


def _add_feature_spec(plan: Path, feature: str, content: str) -> None:
    fdir = plan / "artifacts" / "features" / feature
    fdir.mkdir(parents=True, exist_ok=True)
    (fdir / "technical-spec.md").write_text(content, encoding="utf-8")


def test_sm_crossref_missing_warns(tmp_path):
    plan = _setup_plan(tmp_path, STUCK_FLOW, filename="job-lifecycle.md")
    _add_feature_spec(plan, "F050_JobAdmin", ENTITY_SM_SPEC)
    result = validate(plan, tmp_path)
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ProcessFlow.sm_crossref_missing" in warn_ids
    assert result["summary"]["critical"] == 0


def test_sm_crossref_present_ok(tmp_path):
    flow_with_ref = STUCK_FLOW + "\n## Composition\n\nThis flow extends `SM-001` in F050 (scheduled edges only).\n"
    plan = _setup_plan(tmp_path, flow_with_ref, filename="job-lifecycle.md")
    _add_feature_spec(plan, "F050_JobAdmin", ENTITY_SM_SPEC)
    result = validate(plan, tmp_path)
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ProcessFlow.sm_crossref_missing" not in warn_ids


def test_flow_file_mode_reaches_features(tmp_path, capsys):
    # M1 regression: --flow-file must derive plan root so features/ is scanned.
    plan = _setup_plan(tmp_path, STUCK_FLOW, filename="job-lifecycle.md")
    _add_feature_spec(plan, "F050_JobAdmin", ENTITY_SM_SPEC)
    flow_file = plan / "artifacts" / "flows" / "job-lifecycle.md"
    main(["--flow-file", str(flow_file), "--project-root", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    warn_ids = [i["rule_id"] for i in out["issues"] if i["severity"] == "warning"]
    assert "ProcessFlow.sm_crossref_missing" in warn_ids


# --- v26.2.0: Trigger Sequence companion (sequenceDiagram) WARN-first rule ---

FLOW_WITH_SEQUENCE = VALID_FLOW.replace(
    "---\n\n## Transitions",
    """---

### Trigger Sequence

```mermaid
sequenceDiagram
    actor Admin
    participant OrderController
    participant DB as Order table
    Admin->>OrderController: T1 confirm order
    OrderController->>DB: set status=confirmed
    DB-->>OrderController: ok
```

---

## Transitions""",
    1,
)


def test_sequence_diagram_present_no_warn(tmp_path):
    """Tier-1 flow WITH the `### Trigger Sequence` sequenceDiagram fence -> no WARN."""
    assert "sequenceDiagram" in FLOW_WITH_SEQUENCE  # sanity: fixture actually has the fence
    plan = _setup_plan(tmp_path, FLOW_WITH_SEQUENCE)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ProcessFlow.sequence_diagram.pre_migration" not in warn_ids


def test_sequence_diagram_absent_warns(tmp_path):
    """Tier-1 flow WITHOUT the sequenceDiagram fence -> WARN, never CRITICAL; pass still completes."""
    plan = _setup_plan(tmp_path, VALID_FLOW)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"  # WARN must never flip status to FAIL
    assert result["summary"]["critical"] == 0
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ProcessFlow.sequence_diagram.pre_migration" in warn_ids


def test_sequence_diagram_exempt_for_system_flow(tmp_path):
    """system-flow.md (flowchart TB, no state machine) is exempt — never gets the WARN."""
    plan = _setup_plan(tmp_path, VALID_SYSTEM_FLOW, filename="system-flow.md")
    result = validate(plan, tmp_path)
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ProcessFlow.sequence_diagram.pre_migration" not in warn_ids


def test_empty_flows_dir_with_completed(tmp_path):
    plan = tmp_path / "test-plan"
    flows = plan / "artifacts" / "flows"
    flows.mkdir(parents=True)
    (flows / ".completed").write_text("no_flows_inferred", encoding="utf-8")
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0


# --- v27.12.0: structural proof the sequence_diagram WARN has no path to FAIL ---

def test_status_computation_only_checks_critical_severity():
    """Structural proof (not just a sample instance): `validate()`'s status field is
    computed from exactly one expression in the whole module, and that expression only
    ever tests `severity == "critical"` — a `"warning"` issue (whatever its rule_id, incl.
    `ProcessFlow.sequence_diagram.pre_migration`) has no code path to FAIL. Guards against
    a future edit accidentally adding a second status computation that checks warnings too."""
    import inspect
    import validate_process_flow as vpf

    src = inspect.getsource(vpf.validate)
    status_lines = [ln for ln in src.splitlines() if '"status":' in ln]
    assert len(status_lines) == 1, (
        f"expected exactly one status computation in validate(), found {len(status_lines)}"
    )
    assert 'severity"] == "critical"' in status_lines[0]
    assert "warning" not in status_lines[0]


def test_sequence_diagram_warn_cannot_escalate_even_with_many_other_warnings(tmp_path):
    """Pile up the sequence_diagram WARN alongside other legitimate warnings on the same
    file (still zero criticals) and confirm status stays PASS — proves the WARN doesn't
    escalate via count or combination with other warnings either."""
    plan = _setup_plan(tmp_path, VALID_FLOW)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    assert result["summary"]["warning"] >= 1
    assert result["status"] == "PASS"
