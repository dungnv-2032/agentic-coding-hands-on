---
source_artifact: docs/screens/SCR001_Homepage/spec.md
claims_total: 5
claims_with_evidence: 2
confidence_derived: 0.4
generated_by: derive_confidence_report.py
---

# Confidence Report -- docs/screens/SCR001_Homepage/spec.md

> **Self-reported citation-coverage stat -- NOT a correctness verification.** This report is derived deterministically by parsing the artifact's own inline `**Source:** file:line` citations and `[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]` marker tags. It does NOT verify that citations are accurate or that claims are true. For blind truth verification, see `claude/skills/audit-doc-parity/`.

## Claims ↔ Evidence

Legend: `○` = cited (Source file:line present) · `△` = marker-tagged (uncertain, no citation).

| Claim | Section | Evidence (file:line) | Status ○/△ |
|---|---|---|---|
| `listing.price` \| price on card \| API field \| currency format — needs runtime confirmation \| hidden… | Data Inventory | — | △ |
| –142` | Validation & Error Feedback | app/controllers/homepage_controller.rb:80 | ○ |
| –113` | Validation & Error Feedback | app/controllers/homepage_controller.rb:100 | ○ |
| `listing_shape_menu_enabled` (`all_shapes.size > 1`) \| hardcoded-id \| listing-shape dropdown in too… | Conditional Rendering | — | △ |
| `@show_categories` (`@categories.size > 1`) \| hardcoded-id \| category sidebar (R4) + category dropd… | Conditional Rendering | — | △ |

## Missing Info

Candidate sections to check for `△` (marker-tagged) claims -- best-effort only, not authoritative:

- Data Inventory: `listing.price` \| price on card \| API field \| currency format — needs runtime confirmation \| hidden…
- Conditional Rendering: `listing_shape_menu_enabled` (`all_shapes.size > 1`) \| hardcoded-id \| listing-shape dropdown in too…
- Conditional Rendering: `@show_categories` (`@categories.size > 1`) \| hardcoded-id \| category sidebar (R4) + category dropd…

## Risk Flags

- Low citation coverage (40%) -- most claims are marker-tagged, not cited.
