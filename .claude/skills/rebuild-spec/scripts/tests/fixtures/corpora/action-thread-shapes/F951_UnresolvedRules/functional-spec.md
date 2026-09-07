---
authored_by: rebuild-spec
---
<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths -->
<!-- Contract: references/feature-spec-researcher-contract.md -->

# Functional Spec — F951_UnresolvedRules

**Priority**: P2
**Type**: mixed
**Generated**: 2026-08-21

**See also:** [`technical-spec.md`](./technical-spec.md) — endpoints, Source citations, pseudocode,
key entities, and DB writes for a Dev/QA/SA audience.

## 1. Overview

**Problem:** A marketplace admin who already runs Google Analytics has nowhere to enter their
tracking ID, and no guidance on wiring in Google Tag Manager instead. Separately, the platform
itself needs a fixed, nameable vocabulary of member actions (log out, listing created, user
invited) that it can forward to its own support/analytics tool so Sharetribe staff can see how a
marketplace is actually used.
**Solution:** Two small admin screens let the admin save a Google Analytics tracking key (format
checked before it is stored) or read static Google Tag Manager setup instructions. Independently,
whenever one of the fixed tracked actions happens, the system relays it to the platform's
analytics backend and, in the same page load, fans the same event out to whichever of the
marketplace's other analytics scripts are active.
**Scope:** Saving/clearing a per-marketplace Google Analytics tracking key with format validation;
a static Google Tag Manager instructions screen; a single fixed vocabulary of tracked actions
that both the platform's own analytics backend and the browser's active trackers receive.
**Non-Scope:** Actually configuring Google Tag Manager itself (the screen only instructs — it has
no form and stores nothing). Whether Google Analytics/Tag Manager scripts are allowed to run on
the marketplace's pages at all, and the platform-wide Tag Manager container ID, are deploy-time
settings this feature does not expose to the admin — see § 12 Dependencies.

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Marketplace Admin | Signed-in admin of one marketplace, using the Admin Console | Turn on Google Analytics tracking for their marketplace, or learn how to wire in Google Tag Manager |
| System (background) | The platform itself, reacting to member actions | Forward a fixed set of tracked actions to the platform's analytics backend and to the page's active trackers |

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Configure Google Analytics tracking | Admin saves or clears a Google Analytics tracking key; once saved, the matching tracking script starts loading on the marketplace's pages automatically | US116 | FR-001, FR-101, FR-201, FR-202, FR-203, FR-401, FR-601 | BR-001, BR-002, DEC-001 | SCR034 |
| CAP-02 | View Google Tag Manager setup guide | Admin reads static step-by-step instructions for wiring Google Tag Manager into their marketplace | US117 | FR-102, FR-301, FR-602 | BR-003 | SCR035 |
| CAP-03 | Dispatch canonical analytics events | The system relays a fixed vocabulary of tracked member actions to the platform's analytics backend and to the marketplace's active trackers | US164 | FR-402, FR-403 | BR-004, BR-005, BR-006, BR-007 | N/A — background, no screen |

## 3. Open Decisions

None — no unresolved domain confirmations found while researching this feature.

## 4. Requirements

### Foundation (0xx)

- **FR-001** A marketplace's Google Analytics tracking key is a single value that is either blank or starts with `UA-` or `G-`.

### Navigation (1xx)

- **FR-101** The admin reaches the Google Analytics screen from the "Analytics" group in the Admin Console sidebar.
- **FR-102** The admin reaches the Google Tag Manager guide from the same "Analytics" sidebar group.

### Google Analytics screen (2xx)

- **FR-201** The screen shows one field for the tracking key, with placeholder text and inline help explaining what to paste there.
- **FR-202** Saving checks the key's format before it is stored and shows an inline error if it is invalid.
- **FR-203** The admin can clear the field entirely and save, which stops tracking for the marketplace.

### Google Tag Manager screen (3xx)

- **FR-301** The screen shows static, step-by-step setup instructions with a link to the full external guide; there is no form and nothing is saved.

### Interaction (4xx)

- **FR-401** Once a valid key is saved, the marketplace's public pages automatically load the matching tracking script on their next load — no further admin action is needed.
- **FR-402** The system recognizes exactly one fixed vocabulary of tracked actions (log out, listing created, user invited) and relays them to the platform's analytics backend.
- **FR-403** Every tracked action is also handed, in the same page load, to whichever of the marketplace's other analytics scripts are currently active, independently of whether the platform's own analytics backend is reachable.

### Security (6xx)

- **FR-601** The Google Analytics screen is visible only to a signed-in admin of the marketplace being configured.
- **FR-602** The Google Tag Manager guide is visible only to a signed-in admin of the marketplace being configured.

## 5. Business Rules

- A saved Google Analytics tracking key must be blank or start with `UA-` or `G-`; both the on-page check and the save itself reject anything else (BR-001)
- An admin may save an empty key to turn tracking off again; only a non-blank key is format-checked (BR-002)
- The Google Tag Manager screen never stores anything — it is instructions only (BR-003)
- The platform only relays a tracked action to its analytics backend when that backend is configured for this Sharetribe instance and the acting person is an admin of the marketplace (BR-004)
- Only three tracked actions — log out, listing created, user invited — are recognized by name; anything else recorded through the same mechanism never reaches the platform's analytics backend (BR-005)
- The tracked-action vocabulary is centralized in one constants list so every caller uses the same fixed names (BR-006)
- Every tracked action reaches the page's other active trackers (the marketplace's own Google Analytics/Tag Manager scripts, plus the platform's own secondary trackers) the same way, whether or not the platform's analytics backend accepted it (BR-007)
- Whether the matching Google Analytics tag (legacy or the newer kind) loads on a page depends only on which prefix the saved key has — never both at once (DEC-001)

## 6. Screens

| Screen Name | SCR### | What User Sees | What User Can Do |
|-------------|--------|-----------------|-------------------|
| GoogleAnalytics | SCR034_GoogleAnalytics | A single form with one text field for the Google Analytics tracking key, placeholder text, and inline help | Enter, edit, or clear the tracking key and save |
| GoogleTagManager | SCR035_GoogleTagManager | Static step-by-step instructions for wiring Google Tag Manager into the marketplace, with a link to the full guide | Read the instructions; follow the external link |

### User Journey

1. Admin opens the Admin Console, expands "Analytics" in the sidebar, and lands on GoogleAnalytics.
2. Admin types a tracking key and saves — the field is checked for the `UA-`/`G-` prefix; on success the save button briefly shows a checkmark, on failure an inline message appears next to the field.
3. Admin instead opens GoogleTagManager to read setup instructions and follows the external link to Google's own guide; nothing on this screen is saved.

## 7. User Stories

### US116_ConfigureGoogleAnalytics — Configure Google Analytics tracking

**Actor:** Marketplace Admin
**Goal:** Set a Google Analytics tracking key for the marketplace.
**Business value:** Lets the admin measure marketplace traffic with their own Google Analytics account.

**Acceptance Criteria:**
- [ ] Saving a key that does not start with `UA-` or `G-` is rejected with a clear inline error and nothing is persisted.
- [ ] Saving a valid key (or an empty value) persists it and the marketplace's public pages pick up the change.

### US117_ViewGoogleTagManagerGuide — View the Google Tag Manager setup guide

**Actor:** Marketplace Admin
**Goal:** Read instructions for wiring Google Tag Manager into the marketplace.
**Business value:** Lets the admin adopt the more capable tag-management workflow without needing developer help.

**Acceptance Criteria:**
- [ ] The screen renders the setup instructions and a link to the full guide; no data loads and there is no form to submit.

### US164_DispatchAnalyticsEvents — Dispatch analytics events

**Actor:** System (background)
**Goal:** Relay a fixed set of tracked member actions to the platform's analytics backend and to the marketplace's active trackers.
**Business value:** Makes real member behavior (signups, listings, churn signals) observable to the platform without any admin setup.

**Acceptance Criteria:**
- [ ] Logging out, creating a listing, and inviting a user each produce exactly one tracked action carrying the fixed event name for that action.
- [ ] Each tracked action reaches the platform's analytics backend only when that backend is configured and the actor is a marketplace admin; it always reaches the page's other active trackers regardless.

## 8. Scenarios

### US116_ConfigureGoogleAnalytics — Happy Path

**Given** the admin is on the GoogleAnalytics screen, **When** the admin enters `G-1A2B3C4D5E` and saves, **Then** the key is persisted and the save button shows a brief confirmation.

### US116_ConfigureGoogleAnalytics — Error: invalid prefix

**Given** the admin is on the GoogleAnalytics screen, **When** the admin enters `XYZ-12345` and saves, **Then** the field shows "Please enter a Google Analytics tracking ID that starts with \"UA-\" or \"G-\"" and nothing is saved.

### US117_ViewGoogleTagManagerGuide — Happy Path

**Given** the admin opens the GoogleTagManager screen, **When** the page loads, **Then** the setup instructions and the external guide link render with no data request and no form.

### US164_DispatchAnalyticsEvents — Happy Path

**Given** a marketplace has the platform's analytics backend configured, **When** a member creates a listing, **Then** the fixed `listing_created` action is relayed to that backend for the acting admin's marketplace.

### US164_DispatchAnalyticsEvents — Error: backend unreachable

**Given** the platform's analytics backend is configured but temporarily unreachable, **When** a tracked action fires, **Then** [UNVERIFIED] no retry or user-visible failure path was found for this outbound call in this pass — see technical-spec.md § 5.3.

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Admin saves a key with the wrong prefix (e.g. `XYZ-123`) | Save is rejected before anything is persisted; the previous key (if any) is unchanged | "Please enter a Google Analytics tracking ID that starts with \"UA-\" or \"G-\"" |
| Admin saves an empty key | Empty value passes the format check and is persisted, turning tracking off | None — the save button shows the normal success confirmation |
| A save fails for a reason other than the format check (e.g. an unexpected save error) | The same generic error path renders whatever message the failure produced, unfiltered | "{whatever the underlying error's message was}" — see RISK-02 |
| Admin without marketplace-admin rights requests either analytics screen directly | Request is blocked before rendering | Redirected away from the page (to search, or to log in) |
| A tracked action fires for a marketplace where the analytics backend is not configured (e.g. sandbox/dev) | The action is dropped for that backend only; the page's other active trackers still receive it | None — silent for the backend, unchanged for the browser-side trackers |

## 10. Edge Behaviours to Verify

- **FR-202** → Saving a badly-formatted key never reaches the database — verify no row is written.
- **FR-203** → Saving a blank key succeeds and reads back as blank afterward.
- **FR-402** → Only log out / listing created / user invited ever produce a tracked action toward the analytics backend; verify no other action does.
- **FR-601** → A non-admin (or logged-out) request to the Google Analytics screen never renders the screen content.
- **FR-602** → A non-admin (or logged-out) request to the Google Tag Manager guide never renders the screen content.

## 11. Risks & Known Issues

| ID | Type | Description | Impact | Status |
|----|------|--------------|--------|--------|
| RISK-01 | known-issue | The person-attributes helper used to enrich the platform's analytics profile has several private methods (payment-provider detection, listing-shape payment type, configured fees) that are never called by its own public entry point — only one attribute (`info_marketplace_ident`) is actually sent | Dead code; any richer profile data this class appears designed to send is not actually reaching the analytics backend | confirmed |
| RISK-02 | known-issue | The Google Analytics save action catches every standard error the same way and returns the raw exception message as the on-screen error text, not just the intended format-validation message | An unexpected internal error message could be shown verbatim to the admin instead of a clean error | confirmed |

## 12. Dependencies

| Dependency | Type | Why this feature needs it | Evidence |
|------------|------|-----------------------------|----------|
| Platform analytics backend (Intercom) | external-service | Tracked actions are only relayed when this backend is configured for the Sharetribe instance | BR-004 |
| Platform-wide analytics toggles and Tag Manager container ID | config | Whether the legacy/global Google Analytics and Tag Manager scripts render at all is a deploy-time setting outside this feature's screens | FR-401 |
| Admin Console access control | feature | Both screens rely on the shared marketplace-admin gate that every Admin Console screen uses | FR-601, FR-602 |

## 13. Configuration

```text
GOOGLE_ANALYTICS_KEY_PREFIX_UA = "UA-"   # legacy Universal Analytics key prefix, accepted on save
GOOGLE_ANALYTICS_KEY_PREFIX_G  = "G-"    # current Google Analytics 4 key prefix, accepted on save
```
