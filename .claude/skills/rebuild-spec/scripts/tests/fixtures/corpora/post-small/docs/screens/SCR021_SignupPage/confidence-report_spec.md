---
source_artifact: docs/screens/SCR021_SignupPage/spec.md
claims_total: 7
claims_with_evidence: 1
confidence_derived: 0.1429
generated_by: derive_confidence_report.py
---

# Confidence Report -- docs/screens/SCR021_SignupPage/spec.md

> **Self-reported citation-coverage stat -- NOT a correctness verification.** This report is derived deterministically by parsing the artifact's own inline `**Source:** file:line` citations and `[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]` marker tags. It does NOT verify that citations are accurate or that claims are true. For blind truth verification, see `claude/skills/audit-doc-parity/`.

## Claims ↔ Evidence

Legend: `○` = cited (Source file:line present) · `△` = marker-tagged (uncertain, no citation).

| Claim | Section | Evidence (file:line) | Status ○/△ |
|---|---|---|---|
| `person[given_name]` \| text \| conditional (`name_required` community setting) \| maxlength: 30 \| non… | Validation & Error Feedback | — | △ |
| `person[family_name]` \| text \| conditional (`name_required`) \| maxlength: 30 \| none \| standard requ… | Validation & Error Feedback | — | △ |
| `person[terms]` \| checkbox \| yes \| must be checked \| none \| standard required message \| | Validation & Error Feedback | — | △ |
| `person[password]` \| password \| yes \| minlength: 4 \| none \| standard required message \| | Validation & Error Feedback | — | △ |
| `person[password2]` \| password \| yes \| minlength: 4, equalTo `#person_password1` \| none \| standard… | Validation & Error Feedback | — | △ |
| (unlabeled claim) | Validation & Error Feedback | app/controllers/people_controller.rb:49 | ○ |
| `validate_recaptcha` server-side check \| auth \| Bot submissions rejected with flash error; server e… | Security Surface | — | △ |

## Missing Info

Candidate sections to check for `△` (marker-tagged) claims -- best-effort only, not authoritative:

- Validation & Error Feedback: `person[given_name]` \| text \| conditional (`name_required` community setting) \| maxlength: 30 \| non…
- Validation & Error Feedback: `person[family_name]` \| text \| conditional (`name_required`) \| maxlength: 30 \| none \| standard requ…
- Validation & Error Feedback: `person[terms]` \| checkbox \| yes \| must be checked \| none \| standard required message \|
- Validation & Error Feedback: `person[password]` \| password \| yes \| minlength: 4 \| none \| standard required message \|
- Validation & Error Feedback: `person[password2]` \| password \| yes \| minlength: 4, equalTo `#person_password1` \| none \| standard…
- Security Surface: `validate_recaptcha` server-side check \| auth \| Bot submissions rejected with flash error; server e…

## Risk Flags

- Low citation coverage (14%) -- most claims are marker-tagged, not cited.
