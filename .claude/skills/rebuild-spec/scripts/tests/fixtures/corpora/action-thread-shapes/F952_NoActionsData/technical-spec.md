---
authored_by: rebuild-spec
---
<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
<!-- Contract: references/feature-spec-researcher-contract.md -->

# F952_NoActionsData — Technical Spec
**Priority**: P1
**Type**: background
**Generated**: 2026-08-21

**See also:** [`functional-spec.md`](./functional-spec.md) — plain-language overview, open
decisions, requirements/business rules stated in one-liners, screens, user stories, scenarios,
edge cases, and configuration for a BA/QA audience.

## 1. Technical Overview

Two Rack middleware, both inserted directly in `config/application.rb` ahead of the Rails
middleware they need to run before, implement this feature: `EnforceSsl` 301-redirects a
non-SSL request to its HTTPS equivalent when `APP_CONFIG.always_use_ssl` is true, and
`CustomCookieRenamer` rewrites the raw `Cookie` header so a legacy session-cookie name is
migrated to the current one before `ActionDispatch::Cookies` ever parses it. Neither middleware
is route-scoped — both run on every request, before routing. Rails' own built-in `force_ssl`
(`config/environments/production.rb:49`) is commented out, so `EnforceSsl` is the sole
HTTPS-enforcement mechanism in this codebase.

## 2. Action Index

N/A — no HTTP/RPC surface; background feature only. Both middleware apply uniformly to every
route in the application rather than owning a route of their own.

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|------------------|---------------|-------|--------|--------|
| **A0** | *cross-cutting — belongs to no single action* | — | BR-001, BR-002, BR-003, FR-001, FR-002, FR-401, FR-402, FR-403, FR-601, US167 | — | § 4.4 |

## 3. Actions

### 3.1 CAP-01 — Force HTTPS and migrate the legacy session-cookie name

### 3.2 Edge Cases

| Scenario | Behavior |
|----------|----------|
| Request already over HTTPS | `req.ssl?` is true; `EnforceSsl` passes through unchanged (`@app.call(env)`), no 301 |
| Request host carries an extra address label ahead of the marketplace's own address | HTTP 301 with `Location` stripped to `IDENT.domain` + path, per BR-002's regex |
| Request cookie header already carries the current session-cookie key | Guard regex on line 7 of `custom_cookie_renamer.rb` is true, so `sub!` is never called — header untouched |
| Request has no `HTTP_COOKIE` header at all | `env["HTTP_COOKIE"]` is falsy, guard short-circuits, `@app.call(env)` runs unchanged |

## 4. Shared Foundation

### 4.1 Components

| Component | Responsibility | File |
|-----------|------------------|------|
| EnforceSsl | Rack middleware; 301-redirects a non-SSL request to its HTTPS equivalent, stripping one address label ahead of the marketplace's own address | `lib/rack_middleware/enforce_ssl.rb` |
| CustomCookieRenamer | Rack middleware; rewrites the legacy session-cookie name in the raw `Cookie` header to the current key, only when the current key is absent | `lib/rack_middleware/custom_cookie_renamer.rb` |

### 4.2 Data Model

This feature reads and writes no database tables. Both middleware operate purely on the Rack
`env` hash (HTTP request line and headers) before any model, session-store, or controller code
runs — `EnforceSsl` returns a redirect response without touching persistence, and
`CustomCookieRenamer` mutates `env["HTTP_COOKIE"]` in place. The session-cookie *name* it
migrates is later read by `ActionDispatch::Cookies` / the cookie-backed session store, which
belongs to a different feature slice (see F002_AuthenticationAndSession), not to this one.

#### Key Entities

N/A — no database tables read or written by this feature.

#### Polymorphic Behavior

N/A — no discriminator fields in Key Entities.

### 4.3 State Management

None.

### 4.4 Shared Rules

#### Bin 2 — used by ≥2 named actions

#### Bin 3 — cross-cutting, belongs to no single action

**A0 · cross-cutting** — codes with no single-action owner:
- **BR-001** Non-SSL request 301s to HTTPS — `EnforceSsl#call` (301, `Content-Type: text/html`) [`lib/rack_middleware/enforce_ssl.rb:6-25`]
- **BR-002** Redirect target strips extra address label — `EnforceSsl#call` (Regex `/^(.*)\.(([^\.]+)\.#{domain})$/` against `req.host`; `req.fullpath == "/" ? "" : req.fullpath`) [`lib/rack_middleware/enforce_ssl.rb:11-20`]
- **BR-003** Rename skipped when current cookie key already present — `CustomCookieRenamer#call` (Regex guard `!(env["HTTP_COOKIE"] =~ /\bcookie_session_key/)` before the `sub!`) [`lib/rack_middleware/custom_cookie_renamer.rb:7-8`]
- **FR-001** HTTPS-enforcement switch + domain config — `APP_CONFIG.always_use_ssl` / `APP_CONFIG.domain`, read by `EnforceSsl#call` (Config-only; no code branch beyond the read) [`config/config.defaults.yml:155,7`]
- **FR-002** Legacy/current session-cookie name config — `APP_CONFIG.session_key` / `APP_CONFIG.cookie_session_key`, read by `CustomCookieRenamer#call` (Config-only) [`config/config.defaults.yml:244-245`]
- **FR-401** HTTPS redirect on non-secure request — `EnforceSsl#call` (301 redirect, `Rack::Request#ssl?` gate) [`lib/rack_middleware/enforce_ssl.rb:6-25`]
- **FR-402** Address-label stripping on redirect — `EnforceSsl#call`, regex against `req.host` (See BR-002 pseudocode) [`lib/rack_middleware/enforce_ssl.rb:11-18`]
- **FR-403** Legacy cookie-name rename — `CustomCookieRenamer#call` (In-place `String#sub!` on `env["HTTP_COOKIE"]`) [`lib/rack_middleware/custom_cookie_renamer.rb:6-9`]
- **FR-601** Middleware ordering ahead of routing/cookies — `config.middleware.insert_before` ordering (`EnforceSsl` before `Rack::Sendfile`; `CustomCookieRenamer` before `ActionDispatch::Cookies`) [`config/application.rb:108,113`]
- **US167** Enforce transport and cookie security — `EnforceSsl` + `CustomCookieRenamer`, both wired in `config/application.rb` (End-to-end: every request passes through both middleware before reaching Rails routing) [`config/application.rb:108,113`]

**Non-SSL requests are permanently redirected to their HTTPS equivalent whenever HTTPS enforcement is switched on (BR-001)**

[UNVERIFIED] carried from **Applies to:** — needs a researcher pass (original: "every request (Rack middleware layer, before routing); mirrors PERM006 (ForceSslEnvGate) in `permissions-matrix.md`.")

**Linked FR:** FR-401
**Source:** `lib/rack_middleware/enforce_ssl.rb:6-25`
**Applies to:** every request (Rack middleware layer, before routing); mirrors PERM006
(ForceSslEnvGate) in `permissions-matrix.md`.

```ruby
req = Rack::Request.new(env)
if APP_CONFIG.always_use_ssl.to_s == "true" && !req.ssl?
  redirect_to("https://#{redirect_host}#{path}")  # 301, see BR-002 for redirect_host/path
else
  @app.call(env)
end
```

**The redirect target drops one address label sitting in front of the marketplace's own address; a root-page redirect carries no extra trailing path (BR-002)**

[UNVERIFIED] carried from **Applies to:** — needs a researcher pass (original: "`EnforceSsl#call`, only when BR-001's redirect fires.")

**Linked FR:** FR-402
**Source:** `lib/rack_middleware/enforce_ssl.rb:11-20`
**Applies to:** `EnforceSsl#call`, only when BR-001's redirect fires.

```ruby
# something.IDENT.domain -> IDENT.domain (dodges wildcard-cert mismatch)
matches = /^(.*)\.(([^\.]+)\.#{domain})$/.match(req.host)
redirect_host = matches ? matches[2] : req.host
path = req.fullpath == "/" ? "" : req.fullpath
```

**The old session-cookie name is renamed to the current one only when the current name is not already present (BR-003)**

[UNVERIFIED] carried from **Applies to:** — needs a researcher pass (original: "`CustomCookieRenamer#call`, every request with an `HTTP_COOKIE` header.")

**Linked FR:** FR-403
**Source:** `lib/rack_middleware/custom_cookie_renamer.rb:6-9`
**Applies to:** `CustomCookieRenamer#call`, every request with an `HTTP_COOKIE` header.

```ruby
if env["HTTP_COOKIE"] && !(env["HTTP_COOKIE"] =~ /\b#{cookie_session_key}/)
  env["HTTP_COOKIE"].sub!(/\b#{session_key}=/, "#{cookie_session_key}=")
end
```

**Decision Logic**

`N/A — no user-facing decision logic beyond DISC-### Polymorphic Behavior.` Both middleware
apply one deterministic rule per request (BR-001/BR-003); neither branches on multiple
predicates in a way that changes what the visitor sees or does beyond the single redirect/rename
outcome already captured as a Business Rule.

### 4.5 Algorithms & Integrations

None. The subdomain-stripping logic in `EnforceSsl` (BR-002) is a single regex substitution and
does not rise to the complexity threshold for a dedicated `ALG-###` entry.

None.

### 4.6 Configuration

```text
APP_CONFIG.always_use_ssl = false                 # env-driven; EnforceSsl redirects to HTTPS when this compares equal to the string "true"
APP_CONFIG.domain = "lvh.me:3000"                  # top-level domain; EnforceSsl strips one label ahead of "IDENT.domain" before redirecting
APP_CONFIG.session_key = "_sharetribe_session"     # legacy cookie name CustomCookieRenamer looks for
APP_CONFIG.cookie_session_key = "_st_session"      # current cookie name; CustomCookieRenamer's rename target
```

**Client behavior:** see
[`behavior-logic.md`](../../generated/behavior-logic.md) (client-side patterns — debounce, optimistic UI, polling, upload, realtime),
[`permissions.md`](../../system/permissions.md) (feature flags / experiments / env / locale gates),
[`screen-flow.md`](../../generated/screen-flow.md) (guards / deep-link state restoration / unsaved-changes protection).

## 5. Verification & Technical Notes

### 5.1 Technical Verification

- **SC-001** A plain-HTTP request, with `always_use_ssl` true, receives an HTTP 301 whose
  `Location` header is the same path over `https://`, with any extra address label ahead of the
  marketplace's own address stripped. (covers FR-401, FR-402, BR-001, BR-002)
- **SC-002** A request whose `Cookie` header carries only the legacy session-cookie name arrives
  at `ActionDispatch::Cookies` with that name already rewritten to the current key. (covers
  FR-403, BR-003)
- **SC-003** A request whose `Cookie` header already carries the current session-cookie name is
  passed through with its `Cookie` header byte-for-byte unchanged. (covers FR-403, BR-003)

#### US167_EnforceTransportAndCookieSecurity

**Independent Test:** Send a plain-HTTP request with `always_use_ssl` true and confirm the 301
response; separately, send a request whose cookie header carries only the legacy session-cookie
name and confirm the request still resolves to the visitor's existing session.

**Acceptance Scenarios:**

1. **Given** `always_use_ssl` is true and the request is not SSL, **When** `EnforceSsl#call`
   runs, **Then** the response is HTTP 301 with `Location` set to the HTTPS equivalent of the
   same path.
2. **Given** a request's `Cookie` header carries only `_sharetribe_session=...`, **When**
   `CustomCookieRenamer#call` runs, **Then** the header is rewritten to `_st_session=...` before
   `ActionDispatch::Cookies` parses it.

### 5.2 Assumptions

- `Rack::Request#ssl?` is trusted to correctly reflect whether the original client connection
  was HTTPS; `enforce_ssl.rb` never itself inspects `X-Forwarded-Proto`, so this assumes the
  deployment's TLS-terminating proxy sets whatever Rack/Rails config makes `req.ssl?` accurate
  (`lib/rack_middleware/enforce_ssl.rb:7-8`; Rails' own `config.force_ssl` is commented out at
  `config/environments/production.rb:49`, so no independent Rails-level SSL check backs this up).
- `APP_CONFIG.session_key`/`cookie_session_key` are assumed to be stable, install-wide constants
  set once at deploy time — no per-marketplace override for either was found in `community.rb`,
  unlike `hsts_max_age` which the model does expose per-community.
- The `always_use_ssl` config flag is also read by a separate, out-of-this-feature's-ownership
  mechanism (`app/controllers/concerns/hsts.rb:4-18`, included by `ApplicationController` and
  `LandingPageController`) that sets a `Strict-Transport-Security` header on secure responses —
  this directly contradicts the code comment at `config/application.rb:105-107` claiming HSTS
  "is not a possibility." Recorded here with its citation as the technical detail behind
  `functional-spec.md § 11` RISK-01; not treated as this feature's own code since it lives
  outside `EnforceSsl`/`CustomCookieRenamer` and outside this feature's declared BL/PERM set
  (`BL052`, `BL053`, `PERM006`).

### 5.3 Unresolved Questions

1. **Legacy-cookie sunset timing**: how long `CustomCookieRenamer` needs to stay in the
   middleware stack — i.e. whether any current production session still carries the old
   `_sharetribe_session` name — could not be confirmed from source; no dated flag or removal
   ticket reference was found near the insertion point (`config/application.rb:110-113`).
2. **No test coverage found**: no spec file under `spec/` or `test/` references `EnforceSsl` or
   `CustomCookieRenamer` by name; whether either middleware is covered by a broader
   request/integration spec that does not name the class directly was not confirmed.

### 5.4 Source References

| Action | Order | Symbol | Path | Purpose |
|--------|-------|--------|------|---------|
| — | 1 | Middleware registration | `config/application.rb:105-113` | Wires both middleware into the Rack stack, in order, ahead of the Rails components they must precede |
| — | 2 | EnforceSsl | `lib/rack_middleware/enforce_ssl.rb:1-32` | HTTPS-enforcement redirect + wildcard-cert-safe host rewrite |
| — | 3 | CustomCookieRenamer | `lib/rack_middleware/custom_cookie_renamer.rb:1-14` | Legacy session-cookie name migration |
| — | 4 | Config defaults | `config/config.defaults.yml:7,155,244-245` | Default values for `domain`, `always_use_ssl`, `session_key`, `cookie_session_key` |

### 5.5 Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [overview.md](../../system/overview.md) | — | [x] |
| Architecture | [architecture.md](../../system/architecture.md) | — | [x] |
| Feature List | [feature-list.md](../../generated/feature-list.md) | F952 | [x] |
| API Map | [api-map.md](../../generated/api-map.md) | — (none owned by F952; applies to every route) | [ ] |
| Entities | [entities.md](../../generated/entities.md) | — (none owned by F952) | [ ] |
| Screens | [functional-spec.md § 6](./functional-spec.md#6-screens) | — (background feature; no screens) | [ ] |
| Behavior Logic | [behavior-logic.md](../../generated/behavior-logic.md) | BL052, BL053 | [ ] |
| Permissions Matrix | [permissions-matrix.md](../../generated/permissions-matrix.md) | PERM006 | [ ] |
| User Stories | [user-stories.md](../../generated/user-stories.md) | US167 | [ ] |

**Rule:** Every code listed in Codes Used MUST exist in its source artifact. Orphan refs =
reviewer critical.
