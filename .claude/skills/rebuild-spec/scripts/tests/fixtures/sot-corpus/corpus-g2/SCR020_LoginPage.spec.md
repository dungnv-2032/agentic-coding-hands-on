# SCR020_LoginPage — Screen Spec

**Screen**: SCR020: Login Page
**Type**: atomic
**Route**: GET /login
**Generated**: 2026-06-04

## Purpose

Marketplace members log in to their community account from this screen using email/username + password or via configured OAuth providers (Facebook, Google, LinkedIn); it is also the redirect target for private communities requiring authentication.

### Layout Sketch

The screen renders inside the main `application.haml` layout (sessions controller inherits ApplicationController and declares no custom layout). The layout includes the topbar (React `TopbarApp` or legacy `global_header` partial). Below the topbar, the content region contains a narrow centered `.login-form.centered-section-narrow` div with optional social login buttons, a credential form, a "forgot password" link, and a hidden `#password_forgotten` panel that slides in on demand. (app/views/sessions/new.haml:1)

```
┌──────────────────────────────────────────────┐
│  R1: Topbar (TopbarApp / global_header)      │
│       (fixed-top or static per feature flag) │
├──────────────────────────────────────────────┤
│  R2: .login-form.centered-section-narrow     │
│       h1 title (login / connect Facebook)    │
│  - - - - - - - - - - - - - - - - - - - - -  │
│  │  Social buttons (conditional)            ││
│  │  Facebook / Google / LinkedIn            ││
│  - - - - - - - - - - - - - - - - - - - - -  │
│       "or sign in with username" (cond.)     │
│       form: login + password + submit        │
│       links: Create account | Forgot pw      │
├──────────────────────────────────────────────┤
│  R3: #password_forgotten panel (hidden)      │
│       (slides down on link click)            │
└──────────────────────────────────────────────┘
```

## User Flow

### Happy Path

1. Visitor lands on GET /login (redirected from private community middleware or direct navigation).
2. If already logged in (`logged_in?`), immediately redirected to `search_path` — screen never shown.
3. If `params[:return_to]` present, value stored in `session[:return_to]` for post-login redirect.
4. Screen renders with h1 title and available login methods.
5. User enters login (username or email) and password in R2 form, clicks "Log in".
6. On successful auth: flash notice shown, user redirected to `session[:return_to]`, `session[:return_to_content]`, or `search_path`.

### Branches

| Decision point | Condition | Outcome on this screen | Source |
|----------------|-----------|------------------------|--------|
| Already logged in | `logged_in?` true on GET | Immediate redirect to `search_path` — screen not rendered | `app/controllers/sessions_controller.rb:16` |
| Facebook button | `facebook_connect_in_use?` true | Facebook OAuth button rendered above credential form | `app/views/sessions/new.haml:8` |
| Google button | `google_connect_in_use?` true | Google OAuth button rendered | `app/views/sessions/new.haml:10` |
| LinkedIn button | `linkedin_connect_in_use?` true | LinkedIn OAuth button rendered | `app/views/sessions/new.haml:18` |
| Any social provider active | at least one OAuth provider enabled | "or sign in with your username" separator rendered | `app/views/sessions/new.haml:24` |
| Facebook merge mode | `@facebook_merge` true | h1 shows "Connect your Facebook to Kassi" instead of normal title; "Create new account" link hidden | `app/views/sessions/new.haml:5`, `35` |
| Login failed | Devise authentication fails | `flash.now[:error]` set to login failed message; form re-rendered with prior login value pre-filled | `app/controllers/sessions_controller.rb:32` |
| Forgot password link clicked | User clicks "#password_forgotten_link" | R3 `#password_forgotten` panel slides down via jQuery; page scrolls to bottom; focus moves to email input | `app/assets/javascripts/kassi.js:275` |
| `params[:password_forgotten]` on load | URL param `password_forgotten=true` | `#password_forgotten` panel auto-expanded on page load | `app/assets/javascripts/kassi.js:270` |
| Terms not accepted | `terms_accepted?` false after auth | User signed out, redirected to `terms_path` | `app/controllers/sessions_controller.rb:48` |
| Community label `okl` | `@current_community.label == "okl"` | Login field label changes to "Member ID or Email" instead of "Username or Email" | `app/helpers/application_helper.rb:208` |

## Data Inventory

| Display Label | Source | Format | Empty Behavior | Cross-ref |
|---------------|--------|--------|----------------|-----------|
| (pre-filled login field value) | `session[:form_login]` store state | raw string | empty string (blank input) | N/A (binding: ``session[:form_login]``) |

## UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| error | Devise auth failure (POST /sessions) | `flash.now[:error]` banner with login failed message; form re-rendered | Retry credentials | `app/controllers/sessions_controller.rb:32` |
| password_forgotten expanded | Click "#password_forgotten_link" or `params[:password_forgotten]=true` | `#password_forgotten` panel slides down; page scrolls to bottom | Submit email for password reset | `app/assets/javascripts/kassi.js:275` |
| password_forgotten collapsed | Default / toggle back | `#password_forgotten` panel hidden | Click link to reveal | `app/assets/javascripts/kassi.js:275` |

## Validation & Error Feedback

### A) Client-side

`N/A — no client-side form validation detected.`

<!-- No JS form validation library used; `required` HTML5 attribute not present on inputs. -->

### B) Server-side

#### Login

- **Endpoint:** `POST /sessions` (maps to `sessions#create` via Devise)
- **Request:** `person[login]`, `person[password]`
- **Success:** `302` → redirect to `session[:return_to]` / `session[:return_to_content]` / `search_path`; flash notice with person name link
- **Errors:** `200` re-renders `sessions#new` with `flash.now[:error]` = `t("layouts.notifications.login_failed")` | terms not accepted → `302` redirect to `terms_path`
- **Trigger:** "Log in" button click
- **Source:** `app/controllers/sessions_controller.rb:25`

#### Password reset request

- **Endpoint:** `POST /sessions/request_new_password` (route: `request_new_password_sessions_path`)
- **Request:** `email`
- **Success:** `302` → redirect with flash notice `t("layouts.notifications.password_recovery_sent")`
- **Errors:** flash error `t("layouts.notifications.email_not_found")` if email not found
- **Trigger:** "Request new password" button click inside `#password_forgotten` panel
- **Source:** `app/controllers/sessions_controller.rb:98`, `app/views/sessions/_password_forgotten.haml:3`

## Interaction Patterns

- **Clicking "I forgot my password" reveals the password reset panel below the login form** (jQuery `slideToggle` + scroll to bottom + focus to email input) — source: `app/assets/javascripts/kassi.js:275`
- **If `params[:password_forgotten]=true` on page load, password reset panel auto-expands** — source: `app/assets/javascripts/kassi.js:269`

## Conditional Rendering

| Condition | Type | Renders | Hidden | Notes |
|-----------|------|---------|--------|-------|
| `facebook_connect_in_use?` | feature-flag | `_facebook_connect_button` partial | — | Checks `@current_community.facebook_connect_id` + `facebook_connect_enabled?` + `!@facebook_merge` |
| `google_connect_in_use?` | feature-flag | Google OAuth `link_to` button | — | Checks `@current_community.google_connect_enabled?` + `google_connect_id` |
| `linkedin_connect_in_use?` | feature-flag | LinkedIn OAuth `link_to` button | — | Checks `@current_community.linkedin_connect_enabled?` + `linkedin_connect_id` |
| Any OAuth provider active | feature-flag | "or sign up with your username" separator `<p>` | — | Combined condition on all three providers |
| `@facebook_merge` | auth | — | "Create new account" link | Hides signup link when merging existing account with Facebook |
| `@facebook_merge` | auth | "Connect your Facebook to Kassi" h1 | "Login to …" h1 | Title swaps based on merge mode |
| `FeatureFlagHelper.feature_enabled?(:topbar_v1)` | feature-flag | `TopbarApp` React component | legacy `_global_header` partial | Controls which topbar renders in R1 |

---

*Developer appendix below — implementation detail (layout regions, component wiring, security guards, accessibility audit, source citations, code-reading order). BA/QA readers can stop here.*

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components | Responsive Behavior |
|-----------|------|----------|------------|----------------|---------------------|
| R1 | Topbar | fixed-top or static | no | `TopbarApp` (React) or `_global_header` partial | determined by `FeatureFlagHelper.feature_enabled?(:topbar_v1)` |
| R2 | Login Form Area | static | no | `_facebook_connect_button` partial, `_google_icon` partial, `_linkedin_icon` partial, credential `form_tag`, `_password_forgotten` partial trigger link | `.centered-section-narrow` — narrow centered column |
| R3 | #password_forgotten panel | static (hidden, slides in) | no | `_password_forgotten.haml` (email input + submit) | hidden by default; jQuery `slideToggle` on click |

## Security Surface

| Guard | Type | Consequence if bypassed |
|-------|------|------------------------|
| `redirect_to search_path if logged_in?` in `sessions#new` | auth | Already-authenticated user would see login form; functionally harmless but inconsistent UX |
| Devise `authenticate_person!` on POST /sessions | auth | Without server-side enforcement, unauthenticated session could be established; [UNVERIFIED] server enforcement — Devise rack middleware enforces this independently of controller |
| `terms_accepted?` check post-authentication | permission | User who has not accepted terms is signed out and redirected to `terms_path`; bypassing at UI level would not bypass server-side sign_out |

## Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | absent | No `aria-*` or `role=` in view; `<label for="login">` and `<label for="password">` present and linked to inputs via `id: :main_person_login` / `id: :main_person_password` |
| Keyboard navigation | partial | `autofocus: true` set on login input; standard tab order; no explicit `tabindex` |
| Focus management | partial | `autofocus` on login field; JS moves focus to password-reset email input when panel opens (`$('input.request_password').focus()`) — source: `app/assets/javascripts/kassi.js:273` |
| Screen reader compatibility | partial | `<label>` elements linked to inputs; social login buttons wrapped in `link_to` with span text — accessible text present but no `aria-label` on OAuth links |

## Source References

- Page/View: `app/views/sessions/new.haml:1`
- Password forgotten partial: `app/views/sessions/_password_forgotten.haml:1`
- Controller: `app/controllers/sessions_controller.rb:1`
- Form validation (server): `app/forms/form.rb` (N/A — login uses Devise directly, no Form object)
- Social auth helpers: `app/helpers/social_network_helper.rb:1`
- Username label helper: `app/helpers/application_helper.rb:208`
- Login JS init: `app/assets/javascripts/kassi.js:269`
- Layout: `app/views/layouts/application.haml:1`
- Route: `config/routes.rb:143`
- Social partials (referenced, not read): `app/views/layouts/_facebook_connect_button.haml`, `app/views/layouts/_google_icon.haml`, `app/views/layouts/_linkedin_icon.haml`

## Source Walkthrough

1. **File:** `config/routes.rb:143` -- entry route; `GET /login` maps to `sessions#new`, inside the locale-scoped routes block that begins at `config/routes.rb:113`.
2. **File:** `app/controllers/sessions_controller.rb:15-23` -- `def new`; the FIRST thing it does is redirect already-authenticated visitors to `search_path` (line 16, screen never renders for them -- the spec's first Branches row above), then stashes `params[:return_to]` into the session for post-login redirect (lines 18-20).
3. **File:** `app/views/layouts/application.haml:21-32` -- the shared marketplace layout's topbar branch, NOT `blank_layout` (unlike every other screen in this batch); `FeatureFlagHelper.feature_enabled?(:topbar_v1)` (line 21) picks between the React `TopbarApp` component (line 30) and the legacy `_global_header` partial (line 32) -- read this before the view since R1 in the Layout Sketch above depends on it.
4. **File:** `app/views/sessions/new.haml:1-41` -- the form itself; lines 8-23 gate the three OAuth buttons behind `SocialNetworkHelper` predicates (step 5 below), line 25 the "or sign up with your username" separator, lines 26-38 the credential form and links, line 41 renders the password-reset partial (step 6).
5. **File:** `app/helpers/social_network_helper.rb:2-13` -- `facebook_connect_in_use?` / `google_connect_in_use?` / `linkedin_connect_in_use?`; each reads a `@current_community` flag plus provider ID, and the Facebook variant additionally excludes `@facebook_merge` mode -- source of every OAuth-button row in the spec's Conditional Rendering table above.
6. **File:** `app/views/sessions/_password_forgotten.haml:1-7` -- the hidden `#password_forgotten` panel's markup (R3 in Layout Regions above); a plain form posting to `request_new_password_sessions_path`.
7. **File:** `app/assets/javascripts/kassi.js:269-282` -- `initialize_login_form`; wires the `#password_forgotten_link` click handler (slideToggle plus scroll plus focus, lines 274-278) and auto-expands the panel on load when `params[:password_forgotten]` is true (lines 270-273) -- invoked from `new.haml:2`'s `content_for :javascript` block.
8. **File:** `app/helpers/application_helper.rb:208-210` -- `username_or_email_label`; swaps the login field's label to "Member ID or Email" for the `okl` community label, matching the spec's Branches table row on that condition.
9. **File:** `app/controllers/sessions_controller.rb:25-73` -- `def create`; the `POST /sessions` handler behind Devise's `authenticate_person!` recall (line 37) -- sets `flash.now[:error]` optimistically (line 32), clears it on success (line 40), checks `terms_accepted?` (line 48, redirecting to `terms_path` and signing the user back out if not accepted), then redirects to `session[:return_to]`, `session[:return_to_content]`, or `search_path` in that priority order (lines 64-72).
10. **File:** `app/controllers/sessions_controller.rb:91-106` -- `def request_new_password`; looks up the person by email (scoped to the current community or an admin, lines 92-96), queues a `PersonMailer` reset email on a hit (line 99), and always redirects back to `login_path` with a success or "email not found" flash (lines 100-105).

```
GET /login
  -> routes.rb:143
     -> SessionsController#new (:15) -- redirect to search_path if already logged in
        -> application.haml layout (:21 topbar branch)
           -> sessions/new.haml view (:1-41)
              -> social_network_helper predicates (:2-13) -- OAuth buttons
              -> _password_forgotten.haml partial (rendered at :41) -- R3 hidden panel
              -> kassi.js initialize_login_form (:269) -- client-side slide/focus

POST /sessions                       -> SessionsController#create (:25)  -- Devise auth, terms check, redirect
POST /sessions/request_new_password  -> #request_new_password (:91)      -- email lookup + mailer
```

See this screen's own `## Source References` table above for the citation set this walkthrough draws from.
