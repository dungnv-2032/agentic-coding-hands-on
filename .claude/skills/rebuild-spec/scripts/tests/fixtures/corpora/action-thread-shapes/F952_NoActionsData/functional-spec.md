---
authored_by: rebuild-spec
---
<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
<!-- Contract: references/feature-spec-researcher-contract.md -->

# Functional Spec — F952_NoActionsData

**Priority**: P1
**Type**: background
**Generated**: 2026-08-21

**See also:** [`technical-spec.md`](./technical-spec.md) — endpoints, Source citations, pseudocode,
key entities, and DB writes for a Dev/QA/SA audience.

## 1. Overview

**Problem:** Every request to the platform must arrive over an encrypted connection when the
install requires it, and the name used for the session cookie has changed at least once across
the product's history. Without a deliberate safeguard, insecure traffic would go through in the
clear, and a cookie-name change on its own would sign every visitor out the moment it shipped.
**Solution:** Before anything else runs, the system optionally forces the connection onto HTTPS
when the install has turned that switch on, and quietly renames a legacy session cookie to the
current name if it finds one — so encrypted transport is never accidentally optional, and a
past cookie-key rename never signs anyone out.
**Scope:** Force HTTPS on every request when the install's HTTPS-enforcement switch is on, and
carry an existing session across a legacy session-cookie name to the current one, with no visible
screen or user action involved.
**Non-Scope:** Issuing or verifying TLS certificates themselves; enabling the browser-side
"remember this site was HTTPS" protection some sites turn on alongside forced HTTPS (see § 11
Risks & Known Issues); working out which marketplace a request belongs to (a separate concern —
see F016_MultiTenancyRequestResolution).

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Any visitor or request | Anyone or anything sending an HTTP request to the platform, signed in or not | Reach the platform over an encrypted connection and stay signed in even if the session-cookie name has changed |
| Platform operator | Whoever sets the install's deployment configuration | Turn HTTPS enforcement on or off and control the domain/cookie-name values this feature reads |

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Force HTTPS and migrate the legacy session-cookie name | Every request the visitor sends is silently checked and, if needed, redirected to HTTPS or has its session cookie renamed — the visitor never has to do or notice anything | US167 | FR-001, FR-002, FR-401, FR-402, FR-403, FR-601 | BR-001, BR-002, BR-003 | — |

## 3. Open Decisions

None — no unresolved domain confirmations.

## 4. Requirements

### Foundation (0xx)

- **FR-001** HTTPS enforcement is a single per-install on/off switch plus the install's domain.
- **FR-002** The legacy cookie migration uses an old and a current session-cookie name per install.

### Interaction (4xx)

- **FR-401** A non-secure request, with enforcement on, is redirected to the same page over HTTPS.
- **FR-402** The HTTPS redirect drops one extra address label so the wildcard certificate matches.
- **FR-403** The old session-cookie name is renamed to the current one, unless already present.

### Security (6xx)

- **FR-601** Both checks run before routing/cookie handling, so nothing downstream sees stale state.

## 5. Business Rules

- Non-SSL requests are permanently redirected to their HTTPS equivalent when enforcement is on. (BR-001)
- The redirect drops one address label so the site's certificate still matches. (BR-002)
- The old cookie name is renamed only when the current name is not already present. (BR-003)

## 6. Screens

N/A — background feature; no user-facing screens.

## 7. User Stories

### US167_EnforceTransportAndCookieSecurity — Enforce transport and cookie security

**Actor:** Any visitor or request
**Goal:** Reach the platform over an encrypted connection and keep an existing session working
even after the session-cookie name has changed.
**Business value:** Traffic is never accidentally sent in the clear, and a past cookie-name
change never signs a returning visitor out.

As the system, on every request, HTTPS is enforced when the install requires it and a legacy
session cookie is transparently renamed to its current name — a backward-compatible migration
shim, not a permanent rewrite.

**Acceptance Criteria:**
- [ ] A plain HTTP request is 301-redirected to the same page over HTTPS when HTTPS enforcement
  is on.
- [ ] A request whose cookie header only carries the old session-cookie name has that cookie
  renamed to the current name before the session is looked up.

## 8. Scenarios

### US167_EnforceTransportAndCookieSecurity — Happy Path

**Given** HTTPS enforcement is on and a visitor's request arrives over plain HTTP, **When** the
request reaches the platform, **Then** the visitor is redirected to the identical page over
HTTPS.

### US167_EnforceTransportAndCookieSecurity — Error: request already carries the current cookie name

**Given** a visitor's request already carries a cookie under the current session-cookie name,
**When** the request reaches the platform, **Then** no rename is performed and the old cookie
name (if also present) is left untouched.

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Visitor is already on HTTPS | Nothing changes; the request proceeds as normal | "None — silent handling" |
| Visitor's address carries an extra label in front of the marketplace's own address (e.g. an old bookmark or shared link) | The extra label is dropped and the visitor is sent to the shorter, correct HTTPS address | "None — the browser's address bar updates automatically" |
| Visitor's browser carries a cookie under only the old session-cookie name | The cookie is renamed to the current name before the session is looked up, so the visitor stays signed in | "None — silent handling" |
| Visitor's browser already carries a cookie under the current session-cookie name | The cookie header is left untouched; no rename is attempted even if the old name is also present | "None — silent handling" |

## 10. Edge Behaviours to Verify

- **FR-401** → A plain-HTTP request, with HTTPS enforcement on, results in a redirect to the
  exact same path over HTTPS.
- **FR-402** → A request whose address carries an extra label in front of the marketplace's own
  address redirects to the shorter address, not the original one.
- **FR-403** → A request whose cookie header carries only the old session-cookie name still
  resolves to the visitor's existing session after the request is processed.

## 11. Risks & Known Issues

| ID | Type | Description | Impact | Status |
|----|------|--------------|--------|--------|
| RISK-01 | known-issue | An internal code comment attached to this feature's HTTPS-enforcement code states that a stronger transport-security header is "not a possibility" for this install. In practice, a separate part of the application does set that exact header on secure responses once HTTPS enforcement is switched on. | Anyone reading only this feature's code would wrongly conclude the stronger header is never sent, when it actually is — from code this feature does not own. Risks confusing or duplicate future security work. | confirmed |

## 12. Dependencies

| Dependency | Type | Why this feature needs it | Evidence |
|------------|------|-----------------------------|----------|
| TLS termination at the network edge (load balancer / reverse proxy) | infrastructure | The redirect decision only works if the platform can correctly tell whether the original visitor connection was already HTTPS | BR-001 |
| Session cookie store (F002_AuthenticationAndSession) | feature | Renaming the cookie only helps because the session store looks the session up under the current cookie name this feature renames to | US167 |

## 13. Configuration

```text
always_use_ssl = false   # per-install switch; when true, every plain HTTP request is sent to HTTPS instead
domain = "lvh.me:3000"   # the marketplace's own base address; HTTPS redirects always land on this address (or a shorter one), never on an unrelated address
```
