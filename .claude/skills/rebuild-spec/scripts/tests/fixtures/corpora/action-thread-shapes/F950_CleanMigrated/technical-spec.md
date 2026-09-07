---
authored_by: rebuild-spec
---
<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
<!-- Contract: references/feature-spec-researcher-contract.md -->

# F950_CleanMigrated — Technical Spec
**Priority**: P2
**Type**: ui
**Generated**: 2026-08-21

**See also:** [`functional-spec.md`](./functional-spec.md) — plain-language overview, open
decisions, requirements/business rules stated in one-liners, screens, user stories, scenarios,
edge cases, and configuration for a BA/QA audience.

## 1. Technical Overview

`Admin2::DashboardController#index` — a single action on a subclass of `Admin2::AdminBaseController`,
which gates every admin2 request behind `ensure_is_admin` — builds an `Admin::DomainsPresenter`
over an `Admin::DomainsService` for the welcome card's address text, picks one of three static
partials based on the current billing plan's `whitelabel`/`landing_page` feature flags, and
renders a single static-content view with no further data load. Nothing on this screen persists
any state; every quick link routes to a screen owned by a different feature.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|------------------|---------------|-------|--------|--------|
| **A0** | *cross-cutting — belongs to no single action* | — | BR-001, BR-002, DEC-001, FR-001, FR-202, FR-203, FR-204, FR-401 | — | § 4.4 |
| **A1** | `Admin2::DashboardController#index` | `GET` `/admin` | BR-003, FR-101, FR-201, FR-601, US084 | — *(read-only)* | § 3.1 |

## 3. Actions

### 3.1 CAP-01 — View the admin console dashboard

#### A1 · Non-admin redirect target

`GET /admin` → `Admin2::DashboardController#index`
`BR-003` `FR-101` `FR-201` `FR-601` `US084`

**FE** · **FR-201** Welcome card shows the admin's name and the marketplace's live address — `Admin2::DashboardController#index` builds `@presenter`; rendered at `index.haml:8-11` (`@presenter.domain_address` implements BR-002) [`app/controllers/admin2/dashboard_controller.rb:3-9`]; **US084** View the marketplace admin dashboard — `Admin2::DashboardController#index` end to end, rendering `index.haml` [`app/controllers/admin2/dashboard_controller.rb:3-11`]
**BE** · **FR-101** Admin reaches the dashboard at the marketplace's `/admin` root address — `GET (/:locale)/admin` → `admin2/dashboard#index` (`scope module: "admin2", path: "/admin", as: "admin2"`) [`config/routes.rb:173-174`]; **FR-601** Non-admin never sees the dashboard — `EnsureAdmin#ensure_is_admin` runs as a `before_action` ahead of `#index` (Redirects to `search_path`/`login_path`) [`app/controllers/concerns/ensure_admin.rb:6-16`]; **BR-003** Non-admin redirect target — `EnsureAdmin#ensure_is_admin` [`app/controllers/concerns/ensure_admin.rb:6-16`]
**Rule** ·

**A visitor without admin rights is redirected before any dashboard content is rendered (BR-003)**

**Linked FR:** FR-601
**Source:** `app/controllers/concerns/ensure_admin.rb:6-16`
**Applies to:** every admin2 request, as a `before_action` on `Admin2::AdminBaseController` — runs
before `Admin2::DashboardController#index`.

```ruby
def ensure_is_admin
  return if @is_current_community_admin
  flash[:error] = t("layouts.notifications.only_kassi_administrators_can_access_this_area")
  logged_in? ? (redirect_to search_path and return) : (session[:return_to] = request.fullpath; redirect_to login_path and return)
end
```
**Result** · — **read-only**.
**Source:** `app/controllers/admin2/dashboard_controller.rb:3-11`

### 3.2 Edge Cases

| Scenario | Behavior |
|----------|----------|
| Visitor lacks admin rights on the current community | HTTP redirect (no status-body dashboard content) to `search_path` (signed in) or `login_path` (signed out) — `ensure_admin.rb:9-14` |
| Community has neither Stripe nor PayPal provisioned | `stripe_allowed`/`paypal_allowed` both `false`; the entire online-payments `<li>` group produces no output (`index.haml:33-43`) |
| Plan has neither `whitelabel` nor `landing_page` | `block_select`'s `else` branch runs; `_block_a` renders (`dashboard_controller.rb:22-23`) |
| Plan has `whitelabel` but not `landing_page` | `block_select`'s first branch runs; `_block_b` renders (`dashboard_controller.rb:18-19`) |

## 4. Shared Foundation

### 4.1 Components

| Component | Responsibility | File |
|-----------|------------------|------|
| Admin2::DashboardController | Single `#index` action: builds the domains presenter and picks the plan-based upsell partial | `app/controllers/admin2/dashboard_controller.rb` |
| Admin2::AdminBaseController | Shared parent for every admin2 controller; gates every request behind `ensure_is_admin`, sets the `layouts/admin` layout | `app/controllers/admin2/admin_base_controller.rb` |
| Admin::DomainsPresenter | Wraps `Admin::DomainsService` to compute the welcome card's shown marketplace address | `app/presenters/admin/domains_presenter.rb` |
| Admin::DomainsService | Reads the current community/plan; exposes `white_label?`/`use_domain?`/etc. that the presenter delegates to | `app/services/admin/domains_service.rb` |

### 4.2 Data Model

#### Key Entities

N/A — no database tables independently read or written by this feature. The welcome card's shown
address is computed by `Admin::DomainsPresenter`/`Admin::DomainsService` (§ 3.1), which read
`Community.ident`/`domain`/`use_domain` — but that presenter/service pair, and the `communities`
columns behind it, are owned by `F019_MarketplaceGeneralSettings`'s custom-domain feature (see
`functional-spec.md § 12 Dependencies`), not by this dashboard. `Admin2::DashboardController#index`
issues no query of its own beyond instantiating that shared presenter/service pair over
already-loaded, request-scoped objects (`@current_community`, `@current_plan`).

#### Polymorphic Behavior

N/A — no discriminator fields in Key Entities.

### 4.3 State Management

None.

### 4.4 Shared Rules

#### Bin 2 — used by ≥2 named actions

#### Bin 3 — cross-cutting, belongs to no single action

**A0 · cross-cutting** — codes with no single-action owner:
- **BR-001** Payment-method quick links gated by provisioning — `if stripe_allowed`/`if paypal_allowed`/`if paypal_allowed || stripe_allowed` [`app/views/admin2/dashboard/index.haml:33-43`]
- **BR-002** Welcome-card address: custom domain vs. subdomain — `Admin::DomainsPresenter#domain_used?`/`#domain_address`/`#ident_address` [`app/presenters/admin/domains_presenter.rb:26-36`]
- **DEC-001** Upsell card variant choice (a/b/c) — `Admin2::DashboardController#block_select` [`app/controllers/admin2/dashboard_controller.rb:15-24`]
- **FR-001** Dashboard access requires admin rights on the current community — `before_action :ensure_is_admin` on `Admin2::AdminBaseController` (Mirrors PERM001; `@is_current_community_admin` is set once per request in `ApplicationController#fetch_community_admin_status`) [`app/controllers/admin2/admin_base_controller.rb:5`]
- **FR-202** Quick links to Manage Users/Listings/Transactions/Reviews/Conversations — Static `link_to` calls (No controller-side data; fixed named-route targets) [`app/views/admin2/dashboard/index.haml:13-29`]
- **FR-203** Plan-dependent upsell card — `@block = block_select`, then `render "block_#{@block}"` (See DEC-001) [`app/controllers/admin2/dashboard_controller.rb:10,15-24`; `app/views/admin2/dashboard/index.haml:70-71`]
- **FR-204** Guide/academy links and help card always show — Static `link_to` calls, no gating (Intercom trigger via `'show-intercom': true` + `initIntercom()` JS call) [`app/views/admin2/dashboard/index.haml:45-68,73-82`]
- **FR-401** Payment quick links show only when provisioned — `StripeHelper.stripe_provisioned?` / `PaypalHelper.paypal_provisioned?` gate the `if` blocks in the view (See BR-001) [`app/views/admin2/dashboard/index.haml:33-43`]

**Payment-method quick links are gated by per-provider provisioning (BR-001)**

[UNVERIFIED] carried from **Applies to:** — needs a researcher pass (original: "`index.haml`'s render of `SCR001_AdminDashboard`'s online-payments quick-links group.")

**Linked FR:** FR-401
**Source:** `app/views/admin2/dashboard/index.haml:33-43`
**Applies to:** `index.haml`'s render of `SCR001_AdminDashboard`'s online-payments quick-links group.

```text
stripe_allowed = StripeHelper.stripe_provisioned?(current_community.id)
paypal_allowed = PaypalHelper.paypal_provisioned?(current_community.id)
if paypal_allowed || stripe_allowed
  show "Transaction size" link
end
if stripe_allowed
  show "Stripe" link
end
if paypal_allowed
  show "PayPal" link
end
```

**The welcome card's shown address is the custom domain when white-labeled and in use, otherwise the default subdomain (BR-002)**

[UNVERIFIED] carried from **Applies to:** — needs a researcher pass (original: "`Admin::DomainsPresenter#domain_address`, read once at `index.haml:11`.")

**Linked FR:** FR-201
**Source:** `app/presenters/admin/domains_presenter.rb:26-36`
**Applies to:** `Admin::DomainsPresenter#domain_address`, read once at `index.haml:11`.

```ruby
def domain_used?
  white_label? && use_domain?
end

def domain_address
  domain_used? ? "https://#{domain}" : ident_address
end
```

**The upsell card variant depends on the plan's white-label and landing-page features (DEC-001)**

[UNVERIFIED] no resolvable owner — needs a researcher pass

**subtype:** render
**Triggers in:** SCR001_AdminDashboard mount (`GET (/:locale)/admin`)
**Involved entities:** `Plan.features.whitelabel`, `Plan.features.landing_page` (read from
`@current_plan[:features]`)
**Source:** `app/controllers/admin2/dashboard_controller.rb:15-24`

```ruby
if whitelabel && !landing_page
  'b'
elsif whitelabel && landing_page
  'c'
else
  'a'
end
```

### 4.5 Algorithms & Integrations

None. `block_select`'s 3-way branch is a user-facing decision (DEC-001, § 4), not a computation —
it has no numeric or derived output beyond selecting one of three fixed partial names.

None. `StripeHelper.stripe_provisioned?`/`PaypalHelper.paypal_provisioned?` (BR-001) call an
in-process service object (`TransactionService::API::API`, aliased `TxApi`), not an outbound
network integration this feature owns — the underlying payment-gateway connection itself belongs
to `F005_PaymentAndTransactionConfiguration`.

### 4.6 Configuration

N/A — no technical configuration beyond framework defaults.

**Client behavior:** see
[`behavior-logic.md`](../../generated/behavior-logic.md) (client-side patterns — debounce, optimistic UI, polling, upload, realtime),
[`permissions.md`](../../system/permissions.md) (feature flags / experiments / env / locale gates),
[`screen-flow.md`](../../generated/screen-flow.md) (guards / deep-link state restoration / unsaved-changes protection).

## 5. Verification & Technical Notes

### 5.1 Technical Verification

- **SC-001** A GET to `(/:locale)/admin` by a visitor without admin rights on the current
  community responds with a redirect to `search_path` or `login_path`, never a 200 with dashboard
  markup. (covers FR-601, BR-003)
- **SC-002** A GET to `(/:locale)/admin` by an admin renders `index.haml` with `@block` set to
  exactly one of `"a"`/`"b"`/`"c"`, matching the current plan's `whitelabel`/`landing_page` flags.
  (covers FR-203, DEC-001)
- **SC-003** The rendered welcome card's address text is `https://#{domain}` when
  `white_label? && use_domain?` are both true, otherwise `https://#{ident}.sharetribe.com`.
  (covers FR-201, BR-002)

#### US084_ViewAdminDashboard

**Independent Test:** Visit `/admin` as a community-scoped admin whose plan has `whitelabel: true`
and `landing_page: false`, and whose community has PayPal provisioned but not Stripe. Confirm the
rendered page shows the `_block_b` upsell card, only the transaction-size and PayPal links in the
payments group, and a welcome-card address consistent with BR-002 for this community's
white-label/domain-use state.

**Acceptance Scenarios:**

1. **Given** an admin whose plan has `whitelabel: true` and `landing_page: false`, **When** they
   GET `/admin`, **Then** `@block` is `"b"` and `_block_b` is rendered.
2. **Given** a signed-out visitor, **When** they GET `/admin`, **Then** the response redirects to
   `login_path` with `session[:return_to]` set to the request's full path.

### 5.2 Assumptions

- `@current_plan` is assumed always present and shaped as a hash with a `[:features]` key by the
  time `Admin2::DashboardController#block_select` runs — that method has no nil-guard
  (`dashboard_controller.rb:16-17`), so a `nil` `@current_plan` would raise `NoMethodError` rather
  than falling back to variant `"a"`, unlike `Admin::DomainsService#white_label?`'s own
  `plan.try(:[], :features).try(:[], :whitelabel)`, which does guard against a nil plan
  (`app/services/admin/domains_service.rb:20-22`).
- `stripe_allowed`/`paypal_allowed` (`index.haml:33-34`) are assumed cheap enough to compute on
  every dashboard render — each is a call through `TransactionService::API::API.settings.get`; no
  caching of the provisioned-state result was found in this view or its helpers.

### 5.3 Unresolved Questions

1. **`@current_plan` nil-safety**: whether `request.env[:current_plan]` can ever be `nil` for an
   authenticated admin request in production was not confirmed from source in this feature's
   slice — see Assumption 1 above.
2. **`TxApi.settings.get` cost**: whether `StripeHelper.stripe_provisioned?`/
   `PaypalHelper.paypal_provisioned?` hit a remote call or a cached/local settings store on every
   dashboard load could not be confirmed without reading `TransactionService::API::API` itself,
   which sits outside this feature's declared slice.

### 5.4 Source References

| Action | Order | Symbol | Path | Purpose |
|--------|-------|--------|------|---------|
| — | 1 | Admin2::AdminBaseController | `app/controllers/admin2/admin_base_controller.rb:1-35` | Shared admin2 gate (`ensure_is_admin`) and layout, run before every admin2 action including this one |
| A1 | 2 | Admin2::DashboardController | `app/controllers/admin2/dashboard_controller.rb:1-26` | Entry point; builds the presenter and picks the upsell card variant |
| — | 3 | index.haml | `app/views/admin2/dashboard/index.haml:1-86` | The single view this feature renders — every quick link, both conditional gates (BR-001, DEC-001) |
| — | 4 | Admin::DomainsPresenter / Admin::DomainsService | `app/presenters/admin/domains_presenter.rb:1-57`; `app/services/admin/domains_service.rb:1-92` | Business logic behind the welcome card's address text (BR-002) |

### 5.5 Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [overview.md](../../system/overview.md) | — | [x] |
| Architecture | [architecture.md](../../system/architecture.md) | — | [x] |
| Feature List | [feature-list.md](../../generated/feature-list.md) | F950 | [x] |
| API Map | [api-map.md](../../generated/api-map.md) | ROUTE088 | [ ] |
| Entities | [entities.md](../../generated/entities.md) | — (none owned by F950) | [ ] |
| Screens | [functional-spec.md § 6](./functional-spec.md#6-screens) | SCR001 | [ ] |
| Behavior Logic | [behavior-logic.md](../../generated/behavior-logic.md) | — (none owned by F950) | [ ] |
| Permissions Matrix | [permissions-matrix.md](../../generated/permissions-matrix.md) | PERM001 | [ ] |
| User Stories | [user-stories.md](../../generated/user-stories.md) | US084 | [ ] |

**Rule:** Every code listed in Codes Used MUST exist in its source artifact. Orphan refs =
reviewer critical.
