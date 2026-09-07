---
source_artifact: docs/features/F051_TransactionStateMachine/technical-spec.md
claims_total: 19
claims_with_evidence: 19
confidence_derived: 1.0
generated_by: derive_confidence_report.py
---

# Confidence Report -- docs/features/F051_TransactionStateMachine/technical-spec.md

> **Self-reported citation-coverage stat -- NOT a correctness verification.** This report is derived deterministically by parsing the artifact's own inline `**Source:** file:line` citations and `[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]` marker tags. It does NOT verify that citations are accurate or that claims are true. For blind truth verification, see `claude/skills/audit-doc-parity/`.

## Claims ↔ Evidence

Legend: `○` = cited (Source file:line present) · `△` = marker-tagged (uncertain, no citation).

| Claim | Section | Evidence (file:line) | Status ○/△ |
|---|---|---|---|
| (unlabeled claim) | Polymorphic Behavior | app/state_machines/transaction_process_state_machine.rb:1-197 | ○ |
| (unlabeled claim) | Polymorphic Behavior | app/state_machines/transaction_process_state_machine.rb:136-160 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:31-196 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:190-195 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:135-161 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:37-50 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:125-129 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:95-101 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:174-184 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:1-30 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:136-161 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:163-171 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:157 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:49 | ○ |
| (unlabeled claim) | Cross-Cutting Logic | app/state_machines/transaction_process_state_machine.rb:174-184 | ○ |
| (unlabeled claim) | User Stories | app/jobs/automatic_confirmation_job.rb:14-21 | ○ |
| (unlabeled claim) | User Stories | app/jobs/automatic_booking_confirmation_job.rb:14-23 | ○ |
| (unlabeled claim) | User Stories | app/jobs/automatic_confirmation_job.rb:18-20 | ○ |
| (unlabeled claim) | User Stories | app/jobs/confirm_reminder_job.rb:14 | ○ |

## Missing Info

Candidate sections to check for `△` (marker-tagged) claims -- best-effort only, not authoritative:

_(none -- no marker-tagged claims)_

## Risk Flags

_(none)_
