---
source_artifact: docs/features/F005_MarketplaceCreation/technical-spec.md
claims_total: 29
claims_with_evidence: 29
confidence_derived: 1.0
generated_by: derive_confidence_report.py
---

# Confidence Report -- docs/features/F005_MarketplaceCreation/technical-spec.md

> **Self-reported citation-coverage stat -- NOT a correctness verification.** This report is derived deterministically by parsing the artifact's own inline `**Source:** file:line` citations and `[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]` marker tags. It does NOT verify that citations are accurate or that claims are true. For blind truth verification, see `claude/skills/audit-doc-parity/`.

## Claims ↔ Evidence

Legend: `○` = cited (Source file:line present) · `△` = marker-tagged (uncertain, no citation).

| Claim | Section | Evidence (file:line) | Status ○/△ |
|---|---|---|---|
| (unlabeled claim) | Polymorphic Behavior | app/services/user_service/api/users.rb:56-75 | ○ |
| (unlabeled claim) | Polymorphic Behavior | app/services/user_service/api/users.rb:42-47 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/int_api/marketplaces_controller.rb:1-97 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/communities_controller.rb:1-65 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/services/marketplace_service.rb:120-250 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/int_api/marketplaces_controller.rb:11 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/int_api/marketplaces_controller.rb:75-91 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/forms/form.rb:2-12 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/services/marketplace_service.rb:239-251 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/services/user_service/api/users.rb:71-73 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/services/user_service/api/users.rb:10 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/int_api/marketplaces_controller.rb:30-33 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/int_api/marketplaces_controller.rb:56-70 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/int_api/marketplaces_controller.rb:75-91 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/int_api/marketplaces_controller.rb:10-71 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/services/marketplace_service.rb:239-251 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/int_api/marketplaces_controller.rb:30-33 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/int_api/marketplaces_controller.rb:36-46 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/int_api/marketplaces_controller.rb:64-66 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/services/user_service/api/users.rb:43-47 | ○ |
| (unlabeled claim) | User Stories | app/controllers/int_api/marketplaces_controller.rb:11 | ○ |
| (unlabeled claim) | User Stories | app/controllers/int_api/marketplaces_controller.rb:75-91 | ○ |
| (unlabeled claim) | User Stories | app/forms/form.rb:2-12 | ○ |
| (unlabeled claim) | User Stories | app/services/marketplace_service.rb:120-144 | ○ |
| (unlabeled claim) | User Stories | app/services/user_service/api/users.rb:8-54 | ○ |
| (unlabeled claim) | User Stories | app/controllers/int_api/marketplaces_controller.rb:56-70 | ○ |
| (unlabeled claim) | User Stories | app/controllers/communities_controller.rb:39-42 | ○ |
| (unlabeled claim) | User Stories | app/controllers/int_api/marketplaces_controller.rb:29-33 | ○ |
| (unlabeled claim) | User Stories | app/controllers/int_api/marketplaces_controller.rb:36-46 | ○ |

## Missing Info

Candidate sections to check for `△` (marker-tagged) claims -- best-effort only, not authoritative:

_(none -- no marker-tagged claims)_

## Risk Flags

_(none)_
