---
authored_by: rebuild-spec
---
<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths -->
<!-- Contract: references/feature-spec-researcher-contract.md -->

# F951_UnresolvedRules — Technical Spec
**Priority**: P2
**Type**: mixed
**Generated**: 2026-08-21

**See also:** [`functional-spec.md`](./functional-spec.md) — plain-language overview, open
decisions, requirements/business rules stated in one-liners, screens, user stories, scenarios,
edge cases, and configuration for a BA/QA audience.

## 1. Technical Overview

Two thin Admin2 controllers let a marketplace admin persist `Community#google_analytics_key`
(format-checked) or view a static Google Tag Manager guide. Independently, `AnalyticService`
(constants module + `API::API` facade + `API::Intercom` client) is called from ordinary
controllers/models on three named actions and relays them to Intercom via `Delayed::Job`-backed
async methods; the same event, carried through the Rails `flash`, is fanned out client-side
(`app/assets/javascripts/analytics.js`) to whichever of Google Analytics, Google Tag Manager,
Amplitude, Kissmetrics, and the Intercom widget are active on the page.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|------------------|---------------|-------|--------|--------|
| **A0** | *cross-cutting — belongs to no single action* | — | BR-001, BR-002, BR-003, BR-004, BR-005, BR-006, BR-007, DEC-001, FR-001, FR-101, FR-102, FR-201, FR-203, FR-401, FR-402, FR-403, FR-601, FR-602, US164 | — | § 4.4 |
| **A1** | `Admin2::Analytics::GoogleController#index` | `GET` `/admin/analytics/google-analytics` | US116 | — *(read-only)* | § 3.3 |
| **A2** | `Admin2::Analytics::GoogleController#update_google` | `PATCH` `/admin/analytics/google-analytics/update_google` | FR-202, US116 | `communities` | § 3.3 |
| **A3** | `Admin2::Analytics::GoogleManagerController#index` | `GET` `/admin/analytics/google-tag-manager` | FR-301, US117 | — *(read-only)* | § 3.3 |

## 3. Actions

### 3.1 CAP-01 — Configure Google Analytics tracking

### 3.2 CAP-02 — View Google Tag Manager setup guide

### 3.3 CAP-03 — Dispatch canonical analytics events

#### A1 · Configure Google Analytics tracking

`GET /admin/analytics/google-analytics` → `Admin2::Analytics::GoogleController#index`
`US116`

**BE** · **US116** Configure Google Analytics tracking — `Admin2::Analytics::GoogleController#update_google` (Client-side + server-side validation both present) [`app/controllers/admin2/analytics/google_controller.rb:6-19`]
**Result** · — **read-only**.
**Source:** `app/controllers/admin2/analytics/google_controller.rb:4`

---

#### A2 · Saving checks the key's format before it is stored

`PATCH /admin/analytics/google-analytics/update_google` → `Admin2::Analytics::GoogleController#update_google`
`FR-202` `US116`

**BE** · **FR-202** Saving checks the key's format before it is stored — Client: `google_analytics` jQuery-validate method; Server: `check_google_analytics_key` (Same `UA-`/`G-` rule duplicated client+server) [`app/assets/javascripts/kassi.js:42-47`, `app/controllers/admin2/analytics/google_controller.rb:16-19`]
**Result** · UPDATE `communities` `google_analytics_key` — Literal from `params[:community][:google_analytics_key]`, after the format guard
**Source:** `app/controllers/admin2/analytics/google_controller.rb:6-19` → `app/controllers/admin2/analytics/google_controller.rb:8,21-23`

---

#### A3 · Static GTM setup instructions, no form

`GET /admin/analytics/google-tag-manager` → `Admin2::Analytics::GoogleManagerController#index`
`FR-301` `US117`

**FE** · **FR-301** Static GTM setup instructions, no form — `google_manager/index.haml` (`GoogleManagerController#index` is an empty action) [`app/controllers/admin2/analytics/google_manager_controller.rb:4`, `app/views/admin2/analytics/google_manager/index.haml:1-15`]
**BE** · **US117** View the Google Tag Manager setup guide — `Admin2::Analytics::GoogleManagerController#index` (Static render, no data load) [`app/controllers/admin2/analytics/google_manager_controller.rb:4-6`]
**Result** · — **read-only**.
**Source:** `app/controllers/admin2/analytics/google_manager_controller.rb:4-6`

### 3.4 Edge Cases

| Scenario | Behavior |
|----------|----------|
| Key with wrong prefix submitted | HTTP 422: JSON `{message: "Please enter a Google Analytics tracking ID that starts with \"UA-\" or \"G-\""}` |
| `update!` raises for a reason other than the format guard | HTTP 422: JSON `{message: e.message}` — the raw exception message, see RISK-02 |
| Empty key submitted | HTTP 200: JSON `{message: "Google analytics settings were updated"}`; `google_analytics_key` becomes `NULL`/empty |

| Scenario | Behavior |
|----------|----------|
| Non-admin requests the GET route directly | HTTP redirect (302) to `search_path` or `login_path`, per PERM001 |

| Scenario | Behavior |
|----------|----------|
| Tracked action fires but `admin_intercom_app_id`/`admin_intercom_access_token` are blank | No Intercom API call is attempted (`enabled?` short-circuits); no error, no log entry confirmed |
| Tracked action fires for a person who is not a marketplace admin of the community | `enabled_for_person?` returns false; no Intercom call; client-side fan-out still runs |
| Intercom SDK call itself raises (e.g. network error) | [UNVERIFIED] runs inside `handle_asynchronously`; failure becomes a failed Delayed::Job, no confirmed alerting/retry |

## 4. Shared Foundation

### 4.1 Components

| Component | Responsibility | File |
|-----------|------------------|------|
| GoogleController | Renders the GA key form; validates and persists the key on save | `app/controllers/admin2/analytics/google_controller.rb` |
| GoogleManagerController | Renders the static GTM instructions | `app/controllers/admin2/analytics/google_manager_controller.rb` |
| AnalyticService | Constants module holding the 4 tracked event/info-key names | `app/services/analytic_service.rb` |
| AnalyticService::API::API | Facade forwarding `send_event`/`send_incremental_properties` to the Intercom client | `app/services/analytic_service/api/api.rb` |
| AnalyticService::API::Intercom | Intercom-specific client: gates on config+admin, buckets events, calls the Intercom SDK asynchronously | `app/services/analytic_service/api/intercom.rb` |
| AnalyticService::PersonAttributes | Builds the custom-attribute payload sent when a user record is created/updated in Intercom | `app/services/analytic_service/person_attributes.rb` |
| AnalyticService::IncrementalProperties | Base class for counters sent to Intercom as incremental property updates | `app/services/analytic_service/incremental_properties.rb` |
| Analytics (controller concern) | `record_event`/`mark_logged_out` — writes the flash-carried event log and calls the Intercom facade | `app/utils/analytics.rb` |
| ST.analytics (client JS) | Reads the flash-carried event/logout payload on page load and fans it out to GA, GTM, Amplitude, Kissmetrics, Intercom-widget handlers | `app/assets/javascripts/analytics.js` |

### 4.2 Data Model

#### Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| Community | `communities` | `google_analytics_key` | The single per-marketplace GA tracking key this feature reads and writes |
| Person | `people` | `id`, `uuid`, `email`, `current_sign_in_ip`, `current_sign_in_at` | Read-only source for the Intercom user profile sent by the async dispatch |

#### Polymorphic Behavior

`communities` carries 3 discriminator fields per `docs/generated/entities.md` (DISC-001 `default_browse_view`, DISC-002 `name_display_type`, DISC-003 `footer_theme`). None of the three is read anywhere in this feature's code paths (`google_controller.rb`, `google_manager_controller.rb`, `analytic_service*`, `_head_scripts.haml`, `_customer_analytics*.haml`) — confirmed by reading each file; none references these column names.

##### DISC-001 — Community.default_browse_view

| Value | Render | Validation | Persistence |
|-------|--------|------------|-------------|
| grid | N/A — not read by this feature | N/A | N/A |
| map | N/A — not read by this feature | N/A | N/A |
| list | N/A — not read by this feature | N/A | N/A |

**Source:** docs/generated/entities.md § communities > Discriminator Fields

##### DISC-002 — Community.name_display_type

| Value | Render | Validation | Persistence |
|-------|--------|------------|-------------|
| first_name_only | N/A — not read by this feature | N/A | N/A |
| first_name_with_initial | N/A — not read by this feature | N/A | N/A |
| full_name | N/A — not read by this feature | N/A | N/A |

**Source:** docs/generated/entities.md § communities > Discriminator Fields

##### DISC-003 — Community.footer_theme

| Value | Render | Validation | Persistence |
|-------|--------|------------|-------------|
| dark | N/A — not read by this feature | N/A | N/A |
| light | N/A — not read by this feature | N/A | N/A |
| marketplace_color | N/A — not read by this feature | N/A | N/A |
| logo | N/A — not read by this feature | N/A | N/A |

**Source:** docs/generated/entities.md § communities > Discriminator Fields

### 4.3 State Management

None.

### 4.4 Shared Rules

#### Bin 2 — used by ≥2 named actions

#### Bin 3 — cross-cutting, belongs to no single action

**A0 · cross-cutting** — codes with no single-action owner:
- **BR-001** Saved key must be blank or start with `UA-`/`G-` — `check_google_analytics_key` raises on mismatch (Caught by the broad `rescue StandardError` below it — see RISK-02) [`app/controllers/admin2/analytics/google_controller.rb:16-19`]
- **BR-002** Empty key is allowed and turns tracking off — Same guard, `code.present?` short-circuits [`app/controllers/admin2/analytics/google_controller.rb:18`]
- **BR-003** GTM screen stores nothing — `GoogleManagerController#index` has no update action, no params permitted [`app/controllers/admin2/analytics/google_manager_controller.rb:1-7`]
- **BR-004** Backend relay gated on integration configured + admin actor — `Intercom.enabled_for_person?` (AND of `enabled?` (API id + token present) and `person.is_marketplace_admin?(community)`) [`app/services/analytic_service/api/intercom.rb:85-87`]
- **BR-005** Only 3 named actions recognized; logout is a light event, listing/invite trigger a full profile update — `TRACK_EVENTS`/`TRACK_STATUS_CHANGE_EVENTS` constants + `track_event?`/`status_change_event?` (Different downstream Intercom API call per bucket) [`app/services/analytic_service/api/intercom.rb:4-11,89-99`]
- **BR-006** Vocabulary centralized in one constants module — `AnalyticService` module (4 constants total, one unused by the dispatcher (`INFO_MARKETPLACE_IDENT`, consumed by `PersonAttributes` instead)) [`app/services/analytic_service.rb:1-7`]
- **BR-007** Tracked action always reaches the page's other active trackers regardless of backend outcome — `_bottom_scripts.haml` renders `ST.analytics.init` unconditionally from the same flash payload (Client fan-out does not check whether the Intercom relay succeeded) [`app/views/analytics/_bottom_scripts.haml:1-8`]
- **DEC-001** Which GA tag variant loads depends on the saved key's prefix — `_head_scripts.haml` branch [`app/views/analytics/_head_scripts.haml:1-15`]
- **FR-001** A marketplace's Google Analytics tracking key is a single value that is either blank or starts with `UA-` or `G-` — `communities.google_analytics_key` column, checked in `GoogleController#check_google_analytics_key` (No DB-level CHECK constraint — app-level only) [`db/structure.sql:283`, `app/controllers/admin2/analytics/google_controller.rb:16-19`]
- **FR-101** Admin reaches the Google Analytics screen from the sidebar Analytics group — `Admin2Helper#expand_rules[:analytics]` + `_sidebar.haml` link (`admin2_analytics_google_index_path`) [`app/helpers/admin2_helper.rb:23`, `app/views/admin2/_sidebar.haml:227-228`]
- **FR-102** Admin reaches the Google Tag Manager guide from the same sidebar group — Same sidebar partial, second link (`admin2_analytics_google_manager_index_path`) [`app/views/admin2/_sidebar.haml:229-230`]
- **FR-201** Screen shows one field for the tracking key with placeholder + inline help — `google/index.haml` form (maxlength 15 on the input) [`app/views/admin2/analytics/google/index.haml:16-20`]
- **FR-203** Admin can clear the field and save to stop tracking — `code.present?` guard skips the format check on blank (Empty string passes both validators) [`app/controllers/admin2/analytics/google_controller.rb:18`]
- **FR-401** Saved key auto-activates the matching tracking script on public pages — `_head_scripts.haml` reads `community.google_analytics_key_ua`/`_g` (See DEC-001) [`app/views/analytics/_head_scripts.haml:10-15`, `app/models/community.rb:383-392`]
- **FR-402** System relays 3 named actions to the analytics backend — `record_event`/`mark_logged_out` → `AnalyticService::API::API.send_event` (See INT-001, BR-004, BR-005) [`app/utils/analytics.rb:22-46`]
- **FR-403** Every tracked action also reaches the page's other active trackers — `flash[:_analytics_events]` → `ST.analytics.init` → per-vendor handlers (See INT-002) [`app/utils/analytics.rb:22-35`, `app/assets/javascripts/analytics.js:4-17`]
- **FR-601** Google Analytics screen requires a signed-in marketplace admin — `Admin2::AdminBaseController` before_action (Shared PERM001 gate, not owned by this feature) [`app/controllers/admin2/admin_base_controller.rb:5`]
- **FR-602** Google Tag Manager guide requires a signed-in marketplace admin — Same `Admin2::AdminBaseController` before_action (Shared PERM001 gate, not owned by this feature) [`app/controllers/admin2/admin_base_controller.rb:5`]
- **US164** Dispatch analytics events — `AnalyticService::API::API` facade → `API::Intercom` (Async via `handle_asynchronously` (Delayed::Job)) [`app/services/analytic_service/api/api.rb:1-18`, `app/services/analytic_service/api/intercom.rb:26,47,59`]

**A saved tracking key must be blank or start with UA- or G- (BR-001)**

[UNVERIFIED] carried from **Applies to:** — needs a researcher pass (original: "`PATCH (/:locale)/admin/analytics/google-analytics/update_google`")

**Linked FR:** FR-202
**Linked US:** US116
**Source:** `app/controllers/admin2/analytics/google_controller.rb:16-19`
**Applies to:** `PATCH (/:locale)/admin/analytics/google-analytics/update_google`

**Pseudocode:**
```text
code = params[:community][:google_analytics_key]
if code.present? and not code.start_with?('UA-') and not code.start_with?('G-'):
  raise error_text  # rescued as 422 by the caller
```

**An empty key is allowed and turns tracking off (BR-002)**

[UNVERIFIED] carried from **Applies to:** — needs a researcher pass (original: "same PATCH endpoint as BR-001")

**Linked FR:** FR-203
**Linked US:** US116
**Source:** `app/controllers/admin2/analytics/google_controller.rb:18`
**Applies to:** same PATCH endpoint as BR-001

**Pseudocode:**
```text
if code.present?:
  check_prefix(code)
# blank code skips the check entirely and is persisted as-is
```

**Which Google Analytics tag variant loads is decided by the saved key's prefix (DEC-001)**

[UNVERIFIED] no resolvable owner — needs a researcher pass

**subtype:** render
**Triggers in:** every public page render (`analytics/_bottom_scripts` partial, not a single admin SCR###)
**Involved entities:** `Community.google_analytics_key` (via the derived `google_analytics_key_ua`/`google_analytics_key_g` methods)
**Source:** `app/views/analytics/_head_scripts.haml:10-15`, `app/models/community.rb:383-392`

```pseudo
if community.google_analytics_key starts_with 'UA-' -> render legacy universal-analytics tag (customer_analytics.haml)
else if community.google_analytics_key starts_with 'G-' -> render gtag.js tag (customer_analytics_ga.haml)
else -> render neither
```

---

**The GTM screen stores nothing (BR-003)**

[UNVERIFIED] carried from **Applies to:** — needs a researcher pass (original: "`GET (/:locale)/admin/analytics/google-tag-manager`")

**Linked FR:** FR-301
**Linked US:** US117
**Source:** `app/controllers/admin2/analytics/google_manager_controller.rb:1-7`
**Applies to:** `GET (/:locale)/admin/analytics/google-tag-manager`

**Pseudocode:**
```text
def index; end   # no instance vars set, no params read, no model touched
```

**Backend relay is gated on integration configured and actor being an admin (BR-004)**

[UNVERIFIED] carried from **Applies to:** — needs a researcher pass (original: "`AnalyticService::API::API.send_event` / `.send_incremental_properties`")

**Linked FR:** FR-402
**Linked US:** US164
**Source:** `app/services/analytic_service/api/intercom.rb:80-91`
**Applies to:** `AnalyticService::API::API.send_event` / `.send_incremental_properties`

**Pseudocode:**
```text
def enabled_for_person(person, community):
  return enabled?() and person and community and person.is_marketplace_admin?(community)
def enabled?():
  return admin_intercom_app_id.present? and admin_intercom_access_token.present?
```

**Only 3 named actions are recognized, bucketed into 2 different Intercom calls (BR-005)**

[UNVERIFIED] carried from **Applies to:** — needs a researcher pass (original: "`AnalyticService::API::Intercom.send_event`")

**Linked FR:** FR-402
**Linked US:** US164
**Source:** `app/services/analytic_service/api/intercom.rb:4-11,89-99`
**Applies to:** `AnalyticService::API::Intercom.send_event`

**Pseudocode:**
```text
TRACK_EVENTS = [EVENT_LOGOUT]
TRACK_STATUS_CHANGE_EVENTS = [EVENT_LISTING_CREATED, EVENT_USER_INVITED]
if event_name in TRACK_EVENTS: enqueue event(person.id, event_data)
if event_name in TRACK_STATUS_CHANGE_EVENTS: enqueue create_or_update_user(person.id, community.id)
# any other event_name matches neither bucket and produces no Intercom call
```

**The tracked-action vocabulary lives in one constants module (BR-006)**

[UNVERIFIED] carried from **Applies to:** — needs a researcher pass (original: "every caller of `AnalyticService::EVENT_*`/`AnalyticService::INFO_MARKETPLACE_IDENT`")

**Linked FR:** FR-402
**Linked US:** US164
**Source:** `app/services/analytic_service.rb:1-7`
**Applies to:** every caller of `AnalyticService::EVENT_*`/`AnalyticService::INFO_MARKETPLACE_IDENT`

**Pseudocode:**
```text
module AnalyticService
  EVENT_LOGOUT = 'logout'
  EVENT_LISTING_CREATED = 'listing_created'
  EVENT_USER_INVITED = 'user_invited'
  INFO_MARKETPLACE_IDENT = :info_marketplace_ident
end
```

**Client-side fan-out is independent of the backend relay's outcome (BR-007)**

[UNVERIFIED] carried from **Applies to:** — needs a researcher pass (original: "every page render that includes `_bottom_scripts.haml`")

**Linked FR:** FR-403
**Linked US:** US164
**Source:** `app/views/analytics/_bottom_scripts.haml:1-8`, `app/assets/javascripts/analytics.js:4-17`
**Applies to:** every page render that includes `_bottom_scripts.haml`

**Pseudocode:**
```text
ST.analytics.init({analyticsData, events: flash[:_analytics_events], logout: flash[:_analytics_logout]})
# runs unconditionally on render; never checks whether send_event succeeded
```

**Decision Logic**

**Subtypes:** render

**Out of scope:** N/A for this capability.

---

**Decision Logic**

N/A — no user-facing decision logic beyond DISC-### Polymorphic Behavior.

**Decision Logic**

N/A — no user-facing decision logic beyond DISC-### Polymorphic Behavior.

### 4.5 Algorithms & Integrations

None.

### The system relays tracked actions to the platform's Intercom instance (INT-001)
**Linked FR:** FR-402
**Linked US:** US164
**Source:** `app/utils/analytics.rb:22-46`, `app/services/analytic_service/api/api.rb:1-18`, `app/services/analytic_service/api/intercom.rb:79-120`
**Type:** api-call
**Target:** Intercom REST API (via the `intercom` gem's `Intercom::Client`)
**Trigger:** `record_event`/`mark_logged_out` called from controllers on a tracked user action
**Payload:** event name (one of `EVENT_LOGOUT`/`EVENT_LISTING_CREATED`/`EVENT_USER_INVITED`) + acting person's uuid/email; for status-change events, a full Intercom user upsert with `PersonAttributes#attributes` merged in as custom attributes
**Failure handling:** [UNVERIFIED] no explicit retry/rescue found around the Intercom SDK calls in `intercom.rb`; the calls run inside `handle_asynchronously` (Delayed::Job) so a raised error becomes a failed job, not a user-visible error — no dead-letter/alerting path confirmed in this pass

**Pseudocode:**
```text
def send_event(person, community, event_data):
  if not enabled_for_person(person, community): return
  if event_data.event_name in TRACK_EVENTS:
    enqueue_async: Intercom.event(person.id, event_data)
  if event_data.event_name in TRACK_STATUS_CHANGE_EVENTS:
    enqueue_async: Intercom.create_or_update_user(person.id, community.id)
```

### The browser fans every tracked action out to whichever trackers are active on the page (INT-002)
**Linked FR:** FR-403
**Linked US:** US164
**Source:** `app/utils/analytics.rb:22-35`, `app/views/analytics/_bottom_scripts.haml:1-8`, `app/assets/javascripts/analytics.js:1-149`
**Type:** event-publish
**Target:** Google Analytics (`ST.customerReportEvent`/legacy `_gaq`), Google Tag Manager (`window.dataLayer`), Amplitude, Kissmetrics, the Intercom widget — whichever init function ran for the current page
**Trigger:** page load; `record_event`/`mark_logged_out` write to `flash[:_analytics_events]`/`flash[:_analytics_logout]`, which `_bottom_scripts.haml` serializes into `ST.analytics.init(...)` on the next render
**Payload:** `{event, props}` per queued item, republished as the jQuery custom event `st-analytics:event`; `logout` republishes as `st-analytics:logout`
**Failure handling:** N/A — pure client-side event bus (`$(document).trigger(...)`); a vendor script that failed to load simply never attaches its handler, no error surfaces

**Pseudocode:**
```text
on page ready:
  trigger('st-analytics:setup', analyticsData)
  for event in flash.events: trigger('st-analytics:event', event)
  if flash.logout: trigger('st-analytics:logout')
# each active vendor's init*() subscribes to these 3 events independently
```

### 4.6 Configuration

```text
admin_intercom_app_id = ""              # Intercom workspace app id; blank disables the integration
admin_intercom_access_token = ""        # Intercom API token; blank disables the integration
use_google_analytics = false            # deploy-time flag gating the legacy site-wide GA script partial
use_google_tag_manager = false          # deploy-time flag gating the site-wide GTM script partial
google_tag_manager_key = nil            # platform-wide GTM container id (separate from the per-marketplace key this feature stores)
```

**Client behavior:** see
[`behavior-logic.md`](../../generated/behavior-logic.md) (client-side patterns — debounce, optimistic UI, polling, upload, realtime),
[`permissions.md`](../../system/permissions.md) (feature flags / experiments / env / locale gates),
[`screen-flow.md`](../../generated/screen-flow.md) (guards / deep-link state restoration / unsaved-changes protection).

## 5. Verification & Technical Notes

### 5.1 Technical Verification

- **SC-001** Saving a key without `UA-`/`G-` prefix never changes `communities.google_analytics_key` (covers FR-202, BR-001)
- **SC-002** Saving a blank key succeeds and `communities.google_analytics_key` reads back blank (covers FR-203, BR-002)
- **SC-003** Only `logout`/`listing_created`/`user_invited` ever reach `AnalyticService::API::Intercom` (covers FR-402, BR-005)

#### US116_ConfigureGoogleAnalytics

**Independent Test:** PATCH the update endpoint with a key lacking the `UA-`/`G-` prefix and assert a 422 response with the exact error-text message, then assert the community's key is unchanged.

**Acceptance Scenarios:**

1. **Given** a community with no `google_analytics_key`, **When** `update_google` is called with `google_analytics_key: "G-1A2B3C4D5E"`, **Then** the update succeeds and a 200 with the update-confirmation message is returned.
2. **Given** a community with `google_analytics_key: "G-OLD"`, **When** `update_google` is called with `google_analytics_key: "not-valid"`, **Then** a 422 is returned and the community's key remains `"G-OLD"`.

#### US117_ViewGoogleTagManagerGuide

**Independent Test:** GET the GTM index route as an admin and assert the response renders with no database query beyond the standard admin-context load.

**Acceptance Scenarios:**

1. **Given** an admin is signed in, **When** they GET the GTM guide route, **Then** the static instructions render with a 200 and no form is present.

#### US164_DispatchAnalyticsEvents

**Independent Test:** Stub `AnalyticService::API::Intercom.enabled?` to true, call `record_event` for `AnalyticService::EVENT_LISTING_CREATED`, and assert `create_or_update_user` is enqueued for the acting person.

**Acceptance Scenarios:**

1. **Given** Intercom is configured and the actor is a marketplace admin, **When** a listing is created, **Then** `create_or_update_user` is enqueued with that person's id and the community's id.
2. **Given** Intercom is NOT configured, **When** a member logs out, **Then** `enabled_for_person?` returns false and no Intercom call is enqueued.

### 5.2 Assumptions

- The `intercom` gem's `Intercom::Client` is assumed configured correctly whenever `admin_intercom_app_id`/`admin_intercom_access_token` are both present — no additional health check was found.
- `google_analytics_key` uniqueness across marketplaces is not enforced anywhere; two marketplaces could share the same tracking key without the app objecting.
- The maxlength `15` on the client-side input field is a UI-only constraint; the server does not re-check length, only the prefix.

### 5.3 Unresolved Questions

1. **Intercom failure handling**: Could not confirm from source whether a raised error inside the `handle_asynchronously`-wrapped Intercom SDK calls (`event`, `create_or_update_user`, `update_user_incremental_properties`) is retried, logged, or surfaced anywhere — no rescue block or error-tracking hook was found in `intercom.rb`.
2. **PersonAttributes dead code**: Could not confirm whether the unused private methods in `PersonAttributes` (`payment_providers`, `listing_shapes_online_payment`, `configured_paypal_account`, etc.) are leftovers from a richer profile that was intentionally scaled back, or a regression where `attributes` stopped calling them — see RISK-01.
3. **Amplitude/Kissmetrics ownership**: `analytics.js`'s `initAmplitude`/`initKissmetrics` handlers subscribe to the same `st-analytics:*` events this feature's dispatch produces, but neither integration appears in any upstream artifact (`feature-list.md`, `behavior-logic.md`) under any F###. Flagging for the orchestrator rather than claiming ownership here.

### 5.4 Source References

| Action | Order | Symbol | Path | Purpose |
|--------|-------|--------|------|---------|
| — | 1 | Community | `app/models/community.rb:59,383-392` | `google_analytics_key` column + derived `_ua`/`_g` accessors |
| A1, A2 | 2 | GoogleController | `app/controllers/admin2/analytics/google_controller.rb:1-25` | Render + validate/save the tracking key |
| A3 | 3 | GoogleManagerController | `app/controllers/admin2/analytics/google_manager_controller.rb:1-7` | Render the static GTM guide |
| — | 4 | AnalyticService | `app/services/analytic_service.rb:1-7` | Event-name/info-key constants |
| — | 5 | AnalyticService::API::API | `app/services/analytic_service/api/api.rb:1-18` | Facade to the Intercom client |
| — | 6 | AnalyticService::API::Intercom | `app/services/analytic_service/api/intercom.rb:1-123` | Gating, bucketing, async Intercom calls |
| — | 7 | AnalyticService::PersonAttributes | `app/services/analytic_service/person_attributes.rb:1-84` | Intercom custom-attribute payload (mostly dead code, see RISK-01) |
| — | 8 | Analytics (concern) | `app/utils/analytics.rb:1-47` | `record_event`/`mark_logged_out` flash + Intercom dispatch |
| — | 9 | analytics.js | `app/assets/javascripts/analytics.js:1-149` | Client-side fan-out to GA/GTM/Amplitude/Kissmetrics/Intercom widget |
| — | 10 | _head_scripts.haml | `app/views/analytics/_head_scripts.haml:1-16` | Chooses which GA tag variant to render |

### 5.5 Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [overview.md](../../system/overview.md) | — | [x] |
| Architecture | [architecture.md](../../system/architecture.md) | — | [x] |
| Feature List | [feature-list.md](../../generated/feature-list.md) | F951 | [x] |
| API Map | [api-map.md](../../generated/api-map.md) | ROUTE303, ROUTE304, ROUTE305 | [ ] |
| Entities | [entities.md](../../generated/entities.md) | communities | [ ] |
| Screens | [functional-spec.md § 6](./functional-spec.md#6-screens) | SCR034, SCR035 | [ ] |
| Behavior Logic | [behavior-logic.md](../../generated/behavior-logic.md) | BL078, BL079 | [ ] |
| Permissions Matrix | [permissions-matrix.md](../../generated/permissions-matrix.md) | — (none owned by F951; PERM001 gate is shared, owned elsewhere) | [ ] |
| User Stories | [user-stories.md](../../generated/user-stories.md) | US116, US117, US164 | [ ] |
