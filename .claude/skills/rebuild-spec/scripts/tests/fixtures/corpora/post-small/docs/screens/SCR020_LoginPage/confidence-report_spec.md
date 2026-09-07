---
source_artifact: docs/screens/SCR020_LoginPage/spec.md
claims_total: 3
claims_with_evidence: 2
confidence_derived: 0.6667
generated_by: derive_confidence_report.py
---

# Confidence Report -- docs/screens/SCR020_LoginPage/spec.md

> **Self-reported citation-coverage stat -- NOT a correctness verification.** This report is derived deterministically by parsing the artifact's own inline `**Source:** file:line` citations and `[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]` marker tags. It does NOT verify that citations are accurate or that claims are true. For blind truth verification, see `claude/skills/audit-doc-parity/`.

## Claims ↔ Evidence

Legend: `○` = cited (Source file:line present) · `△` = marker-tagged (uncertain, no citation).

| Claim | Section | Evidence (file:line) | Status ○/△ |
|---|---|---|---|
| (unlabeled claim) | Validation & Error Feedback | app/controllers/sessions_controller.rb:25 | ○ |
| , `app/views/sessions/_password_forgotten.haml:3` | Validation & Error Feedback | app/controllers/sessions_controller.rb:98 | ○ |
| Devise `authenticate_person!` on POST /sessions \| auth \| Without server-side enforcement, unauthent… | Security Surface | — | △ |

## Missing Info

Candidate sections to check for `△` (marker-tagged) claims -- best-effort only, not authoritative:

- Security Surface: Devise `authenticate_person!` on POST /sessions \| auth \| Without server-side enforcement, unauthent…

## Risk Flags

_(none)_
