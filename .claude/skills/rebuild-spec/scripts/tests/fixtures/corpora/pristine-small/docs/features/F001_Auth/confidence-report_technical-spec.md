---
source_artifact: docs/features/F001_Auth/technical-spec.md
claims_total: 26
claims_with_evidence: 26
confidence_derived: 1.0
generated_by: derive_confidence_report.py
---

# Confidence Report -- docs/features/F001_Auth/technical-spec.md

> **Self-reported citation-coverage stat -- NOT a correctness verification.** This report is derived deterministically by parsing the artifact's own inline `**Source:** file:line` citations and `[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]` marker tags. It does NOT verify that citations are accurate or that claims are true. For blind truth verification, see `claude/skills/audit-doc-parity/`.

## Claims ↔ Evidence

Legend: `○` = cited (Source file:line present) · `△` = marker-tagged (uncertain, no citation).

| Claim | Section | Evidence (file:line) | Status ○/△ |
|---|---|---|---|
| (unlabeled claim) | Polymorphic Behavior | app/models/community_membership.rb:26-32 | ○ |
| (unlabeled claim) | Polymorphic Behavior | app/controllers/application_controller.rb:317-351 | ○ |
| , `app/controllers/people_controller.rb:49-120`, `app/controllers/application_controller.rb:239-248` | Cross-Cutting Logic | app/controllers/sessions_controller.rb:15-72 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/sessions_controller.rb:48-55 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/people_controller.rb:65-79 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/people_controller.rb:59-63 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/people_controller.rb:395-413 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/application_controller.rb:317-329 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/sessions_controller.rb:59-73 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/people_controller.rb:111-120 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/confirmations_controller.rb:54-68 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/models/community_membership.rb:26-84 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/sessions_controller.rb:25-73 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/controllers/sessions_controller.rb:91-106 | ○ |
| , `app/controllers/community_memberships_controller.rb:72` | Cross-Cutting Logic | app/controllers/confirmations_controller.rb:47-48 | ○ |
| , `app/controllers/confirmations_controller.rb:97-98` | Cross-Cutting Logic | app/controllers/people_controller.rb:116 | ○ |
| , `app/controllers/community_memberships_controller.rb:71` | Cross-Cutting Logic | app/controllers/people_controller.rb:105 | ○ |
| (unlabeled claim) | User Stories | app/controllers/people_controller.rb:84-120 | ○ |
| (unlabeled claim) | User Stories | app/controllers/people_controller.rb:59-63 | ○ |
| (unlabeled claim) | User Stories | app/controllers/people_controller.rb:53-57 | ○ |
| (unlabeled claim) | User Stories | app/models/community_membership.rb:56-59 | ○ |
| (unlabeled claim) | User Stories | app/controllers/sessions_controller.rb:13-73 | ○ |
| (unlabeled claim) | User Stories | app/controllers/sessions_controller.rb:15-23 | ○ |
| (unlabeled claim) | User Stories | app/controllers/sessions_controller.rb:91-106 | ○ |
| (unlabeled claim) | User Stories | app/controllers/sessions_controller.rb:75-85 | ○ |
| (unlabeled claim) | User Stories | app/controllers/community_memberships_controller.rb:147-149 | ○ |

## Missing Info

Candidate sections to check for `△` (marker-tagged) claims -- best-effort only, not authoritative:

_(none -- no marker-tagged claims)_

## Risk Flags

_(none)_
