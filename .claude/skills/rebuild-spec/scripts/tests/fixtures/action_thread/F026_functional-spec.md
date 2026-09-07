---
authored_by: rebuild-spec
---
<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
<!-- Contract: references/feature-spec-researcher-contract.md -->

# Functional Spec — F026_TransactionalEmailSettings

**Priority**: P2
**Type**: mixed
**Generated**: 2026-08-21

**See also:** [`technical-spec.md`](./technical-spec.md) — endpoints, Source citations, pseudocode,
key entities, and DB writes for a Dev/QA/SA audience.

## 1. Overview

**Problem:** A marketplace admin has no way to make transactional emails look and read like they
come from their own brand — the sender name/address is a shared default, and the message new
members receive on joining is generic boilerplate.
**Solution:** The admin panel lets an admin (1) register and verify their own outgoing sender
address so future transactional emails use it instead of the shared default, and (2) edit the
welcome-email content new members receive, with a way to send themselves a preview before
trusting it.
**Scope:** Setting/verifying a custom sender address; editing welcome-email content; sending a
test copy of the welcome email to the admin themself.
**Non-Scope:** Editing any other transactional email template (order/payment/dispute emails);
choosing per-recipient email preferences; the actual send-to-new-member event (that trigger lives
in the signup/confirmation flow, only consumed here).

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Marketplace Admin | Person with admin rights on the marketplace | Make outgoing transactional email look on-brand and trustworthy |

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Set and verify a custom outgoing sender address | Register a sender name/email, watch it move through verification, and resend the verification email if it lapses | US120 | FR-001, FR-002, FR-201, FR-202, FR-203, FR-204, FR-205, FR-401, FR-602 | BR-001, BR-002, BR-003, BR-004, BR-005, DEC-001, DEC-002, SM-001 | SCR038 |
| CAP-02 | Configure and test the welcome email | Edit the welcome-email content members receive on joining, and send a preview to self | US121 | FR-101, FR-301, FR-302, FR-303, FR-601 | BR-006, BR-007, BR-008 | SCR039 |

## 3. Open Decisions

| D### | Decision | Default proposal | Rationale | Blocks work |
|------|----------|-------------------|-----------|--------------|
| D001 | No rate limit exists on how often "resend verification email" can be triggered — should one be added to prevent an admin (or a scripted actor with admin credentials) from repeatedly triggering AWS SES verification sends? | Ship as-is, unlimited resends | No abuse has been reported against this endpoint and adding a limiter is new scope, not a defect fix | no |

## 4. Requirements

### Foundation (0xx)

- **FR-001** The marketplace's plan determines what this feature allows: one plan feature enables setting a custom sender address at all, and a separate plan feature controls whether Sharetribe-branding upgrade notices are shown.
- **FR-002** Whether the marketplace's environment has email-sending (SES) configured determines whether a newly added sender address must go through address verification or is trusted immediately.

### Navigation (1xx)

- **FR-101** Admin reaches these settings from the "Emails" section of the admin panel sidebar, with the sender address and welcome email as separate pages.

### Outgoing Sender Address (2xx)

- **FR-201** The sender-address page shows the currently configured sender name/email and its verification state when the page loads.
- **FR-202** Admin can submit a name and email to register (or replace) the marketplace's custom sender address.
- **FR-203** When verification is required, a newly registered address starts in a "waiting" state and is checked against Amazon's records until it resolves to verified or expired.
- **FR-204** Once an address is expired or otherwise unverified, admin can resend the verification email without re-entering the address.
- **FR-205** While an address is waiting on verification, the page polls for status updates automatically, without a full page reload.

### Welcome Email (3xx)

- **FR-301** Admin can edit the welcome-email content shown to new members, using an inline rich-text editor.
- **FR-302** Admin can send themself a preview copy of the welcome email without affecting the content actually saved.
- **FR-303** A new member automatically receives the customized welcome-email content the first time they complete signup/confirmation.

### Interaction (4xx)

- **FR-401** Once a sender address is verified, it becomes the "from" address used for the marketplace's outgoing transactional email in place of the shared default, until a newer address is verified.

### Security (6xx)

- **FR-601** Every page and action in this feature requires the visitor to be signed in as a marketplace admin.
- **FR-602** A submitted sender address is rejected if it uses the marketplace's own platform domain, or (when address verification is active) a small set of disallowed consumer webmail domains.

## 5. Business Rules

- Setting a custom sender address is only allowed when the marketplace's plan includes that feature; other plans see an upgrade notice instead of the form. (BR-001)
- A submitted sender address must be a valid email shape, must not be on the platform's own domain, and — only while verification is active — must not be on a short list of disallowed consumer webmail domains. (BR-002)
- If the marketplace's environment has no email-verification service configured, a newly registered sender address is marked verified immediately instead of waiting on external confirmation. (BR-003)
- Resubmitting the exact same email address that is already on file only updates the display name — it does not start a new verification cycle. (BR-004)
- The marketplace's most recently verified sender address is used for outgoing transactional email; until one exists, a shared default address is used instead. (BR-005)
- Whether the sender-address form is usable, and whether an upgrade notice appears, is decided jointly by the marketplace's plan features rather than a single flag. (DEC-001)
- Whether the page shows a "waiting on verification" spinner or the normal save form is decided jointly by whether an address exists at all and what state it is in. (DEC-002)
- A sender address moves through a fixed set of verification states (waiting → verified, or waiting → expired → waiting again on resend) rather than being simply on/off. (SM-001)
- Welcome-email content is saved the moment the admin edits it in the inline editor — the page's own "save" action is not what persists the content. (BR-006)
- Sending a test welcome email always delivers to the admin's own confirmed address and never changes what is actually saved for new members. (BR-007)
- A brand-new member automatically receives the current welcome-email content the first time they confirm/join, unless they are themself a marketplace admin. (BR-008)

## 6. Screens

| Screen Name | SCR### | What User Sees | What User Can Do |
|-------------|--------|-----------------|-------------------|
| OutgoingEmailAddress | SCR038_OutgoingEmailAddress | Sender name/email fields, a verification-state indicator (waiting/verified/expired/unverified), and — on plans without this feature — an upgrade notice instead of an editable form | Enter/replace a sender name and email; resend a lapsed verification email; watch verification status update live |
| WelcomeEmail | SCR039_WelcomeEmail | An inline rich-text box pre-filled with the marketplace's current welcome-email content (or a default message if none was ever set), and a link to open the same content in a full editor | Edit the welcome-email content directly in the box; send a preview of it to their own inbox |

### User Journey

1. Admin opens OutgoingEmailAddress and sees whether a sender address is already set and its verification state.
2. Admin enters a name and email and submits — if the plan allows it and the address is acceptable, the state becomes "waiting" and the page starts polling.
3. Once Amazon confirms the address (or it lapses), the page updates on its own; if it lapsed, admin can resend the verification email from the same page.
4. Separately, admin opens WelcomeEmail, edits the message members will see, and optionally clicks "send a test email to yourself" to preview it before trusting it.

## 7. User Stories

### US120_SetOutgoingEmailAddress — Set a custom outgoing email address

**Actor:** Marketplace Admin
**Goal:** Set and verify a custom outgoing sender address
**Business value:** Transactional emails come from the admin's own domain instead of the shared default, which makes the marketplace look more legitimate and trustworthy to its members.

**Acceptance Criteria:**
- [ ] Setting the address on a plan that doesn't include this feature is blocked, with an upgrade notice shown instead of the form.
- [ ] Verification status updates on the page without the admin needing to reload it.
- [ ] Admin can resend the verification email on its own, without re-entering the address, once the status is expired or unverified.

### US121_ConfigureWelcomeEmail — Configure the member welcome email

**Actor:** Marketplace Admin
**Goal:** Customize the welcome-email content and preview it before trusting it
**Business value:** New members get an on-brand first message instead of generic boilerplate, which shapes their first impression of the marketplace.

**Acceptance Criteria:**
- [ ] Admin edits the welcome-email content using the inline rich-text editor and it is saved without a separate "save" step.
- [ ] Sending a test copy to self delivers promptly and does not alter the content that real new members will receive.

## 8. Scenarios

### US120_SetOutgoingEmailAddress — Happy Path

**Given** the marketplace's plan includes custom sender addresses and no address is set yet, **When** admin submits a valid name and email, **Then** the address is saved, verification status shows "waiting," and the page begins polling until it resolves to verified.

### US120_SetOutgoingEmailAddress — Error: plan does not include this feature

**Given** the marketplace's plan does not include custom sender addresses, **When** admin submits the form anyway, **Then** the request is blocked and an upgrade notice is shown instead of a saved address.

### US121_ConfigureWelcomeEmail — Happy Path

**Given** admin has open the welcome-email page, **When** admin edits the content in the inline editor, **Then** the change is saved automatically and reflected the next time the page (or a test send) is viewed.

### US121_ConfigureWelcomeEmail — Error: save fails

**Given** admin clicks "send a test email to yourself", **When** the send raises an error, **Then** the page shows a plain-language failure message instead of the usual confirmation.

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Admin submits an email on a disallowed domain (own platform domain, or a disallowed webmail provider while verification is active) | The request is rejected before anything is saved | "Please enter a valid email address" or a domain-specific message naming the unsupported provider |
| Admin clicks "resend verification" while a scheduled background check is also updating the same address | Whichever update lands last wins; the next status poll simply reflects the latest state — no error surfaces | "None — silent handling" |
| No sender address has ever been configured for the marketplace | Outgoing transactional email uses the shared default address; the page shows empty/disabled fields and does not poll | "None — silent handling" |
| Admin attempts to set an address while the plan does not include this feature (even by bypassing the disabled form) | The server blocks the request independently of the disabled UI and sends the admin back to the same page | "Not included in your current plan" |
| A brand-new member who is themself a marketplace admin joins | No welcome email is sent to them at all | "None — silent handling" |

## 10. Edge Behaviours to Verify

- **FR-202** → Confirm an invalid or disallowed email is rejected with a clear message and nothing is saved.
- **FR-205** → Confirm the verification-status indicator updates on its own while an address is waiting, without a page reload.
- **FR-303** → Confirm a newly confirmed member (who is not an admin) actually receives the current welcome-email content.

## 11. Risks & Known Issues

| ID | Type | Description | Impact | Status |
|----|------|--------------|--------|--------|
| RISK-01 | known-issue | On the welcome-email settings page, the already-saved content renders escaped (as literal markup text rather than rendered rich text) specifically when the viewer is a platform-wide (global) Sharetribe administrator. This page's own access gate only requires admin rights on the current marketplace, which a visitor can hold either as a platform-wide administrator or as an admin scoped to just that one marketplace — but the rendering choice checks the narrower, platform-wide flag alone, not the broader condition the access gate itself enforces. An admin whose rights are scoped to a single marketplace does not hit this: they see the same saved content rendered normally. | A platform-wide administrator re-opening the welcome-email page after it already has saved content sees raw HTML source inside the rich-text box instead of the rendered message; a marketplace-scoped admin viewing the same page is unaffected. | confirmed |

## 12. Dependencies

| Dependency | Type | Why this feature needs it | Evidence |
|------------|------|-----------------------------|----------|
| Marketplace plan / billing entitlements (provisioned by F030_ExternalPlatformWebhooks) | feature | Two separate plan features gate whether the sender-address form is usable and whether branding-upgrade notices show | FR-001, DEC-001 |
| Amazon SES (email sending + address verification) | external-service | Verifying a submitted sender address, and detecting bounces/complaints against it, both depend on AWS SES | FR-203, BR-002 |

## 13. Configuration

```text
WELCOME_EMAIL_CONTENT_MAX_CHARS = 65535   # welcome-email content is capped at this many characters
```
