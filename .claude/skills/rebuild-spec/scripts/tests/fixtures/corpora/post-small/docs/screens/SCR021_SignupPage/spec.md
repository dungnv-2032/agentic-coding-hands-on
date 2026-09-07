# SCR021_SignupPage — Screen Spec

**Screen**: SCR021: SignupPage
**Type**: atomic
**Route**: GET /signup
**Generated**: 2026-06-04

## Purpose

New visitors register for a community marketplace account from this screen, reached either directly via the signup URL or by invitation link; it supports both email/password registration and OAuth sign-up via Facebook, Google, or LinkedIn.

### Layout Sketch

The screen renders a centered single-column form under the community's global application layout. A `title_header` content block injects an `<h1>` heading at the top. The main region is a `.signup-form.centered-section` div containing optional social login buttons, a horizontal divider when OAuth providers are enabled, and the email-based registration form with all field groups stacked vertically. Help text lightbox partials are appended below the form. No sidebar or fixed/sticky positioning is present. (`app/views/people/new.haml:7`)

```
┌──────────────────────────────────────────┐
│  R1: Page Header / Title (static)        │
│  [h1: Sign Up — injected content_for]    │
├──────────────────────────────────────────┤
│  R2: Signup Form (.signup-form           │
│      .centered-section) (static,         │
│      scrollable)                         │
│                                          │
│  [optional info/email restriction text]  │
│  - - - - - - - - - - - - - - - - - - -  │
│  [R2a: OAuth buttons — conditional]      │
│  - - - - - - - - - - - - - - - - - - -  │
│  [horizontal divider — conditional]      │
│  [R2b: Email registration form]          │
│    invitation_code (conditional)         │
│    email, given_name, family_name        │
│    password, password2                   │
│    custom_fields (conditional)           │
│    terms checkbox, admin_emails checkbox │
│    recaptcha (conditional)               │
│    Submit button                         │
├──────────────────────────────────────────┤
│  R3: Help text lightboxes (static)       │
│      #terms, #privacy,                   │
│      #help_invitation_code               │
└──────────────────────────────────────────┘
```

## User Flow

### Happy Path

1. User lands on `/signup`; if already logged in, is redirected to search path (`app/controllers/people_controller.rb:35`).
2. If one or more OAuth providers are enabled (Facebook/Google/LinkedIn), social login buttons appear at top of R2.
3. User fills in email, given name, family name, password, password confirmation; optionally invitation code (if community requires it).
4. jQuery Validate fires async email uniqueness check against `/people/check_email_availability_and_validity` on field blur.
5. If invitation code field visible, jQuery Validate fires async check against `/people/check_invitation_code` on blur.
6. User checks Terms & Privacy checkbox (unless `@skip_terms_checkbox`).
7. Optionally checks admin_emails_consent checkbox.
8. If reCAPTCHA configured, user completes reCAPTCHA widget.
9. User clicks "Create new account" button; form submits `POST /people`.
10. On success: flash notice set, redirect to `confirmation_pending_path`.

### Branches

| Decision point | Condition | Outcome on this screen | Source |
|----------------|-----------|------------------------|--------|
| Page load | `logged_in?` is true | Immediate redirect to search path — form never shown | `app/controllers/people_controller.rb:35` |
| Page load | `@community_customization.signup_info_content` present | Custom info text rendered above form | `app/views/people/new.haml:9` |
| Page load | `@current_community.allowed_emails` set and not regex | Email restriction instructions text shown | `app/views/people/new.haml:12` |
| Page load | `facebook_connect_in_use?` and no `?no_fb` param | Facebook OAuth button rendered | `app/views/people/new.haml:19` |
| Page load | `google_connect_in_use?` | Google OAuth button rendered | `app/views/people/new.haml:22` |
| Page load | `linkedin_connect_in_use?` | LinkedIn OAuth button rendered | `app/views/people/new.haml:30` |
| Page load | Any OAuth provider active | Horizontal divider + "Sign up with email" h3 shown | `app/views/people/new.haml:38` |
| Page load | `@current_community.join_with_invite_only?` | Invitation code field rendered | `app/views/people/new.haml:47` |
| Page load | `params[:code]` present but invite not required | Hidden invitation code field injected | `app/views/people/new.haml:52` |
| Page load | `@service.has_person_custom_fields?` | Additional custom field inputs rendered | `app/views/people/new.haml:75` |
| Page load | `@skip_terms_checkbox` false | Terms checkbox rendered | `app/views/people/new.haml:97` |
| Page load | `@current_community.recaptcha_configured?` | reCAPTCHA widget rendered | `app/views/people/new.haml:111` |
| Submit | reCAPTCHA fails server-side | Flash error, re-renders form | `app/controllers/people_controller.rb:53` |
| Submit | Honey pot field populated | Flash error, redirect to signup | `app/controllers/people_controller.rb:59` |
| Submit | Invalid invitation code server-side | Flash error, redirect to signup | `app/controllers/people_controller.rb:71` |
| Submit | Email not valid for community | Flash error, redirect to signup | `app/controllers/people_controller.rb:81` |
| Submit | Person creation fails (DB error) | Flash error redirect to signup | `app/controllers/people_controller.rb:89` |
| Submit | `APP_CONFIG.skip_email_confirmation` true | Redirect to search path directly (test env only) | `app/controllers/people_controller.rb:112` |
| Submit | Successful registration | Flash notice, redirect to `confirmation_pending_path` | `app/controllers/people_controller.rb:118` |

## Data Inventory

| Display Label | Source | Format | Empty Behavior | Cross-ref |
|---------------|--------|--------|----------------|-----------|
| (none — body copy) | API field / DB | raw HTML (`.html_safe`) | region hidden | N/A (binding: ``@community_customization.signup_info_content``) |
| community_name in restriction text | store state | raw string | hidden | N/A (binding: ``@current_community.name(I18n.locale)``) |
| allowed_emails in restriction text | store state | raw string | region hidden | N/A (binding: ``@current_community.allowed_emails``) |
| Invitation Code | route param | raw string | empty field | N/A (binding: ``params[:code]``) |
| `custom_field.name(I18n.locale)` | API field | raw string | N/A (iterated) | N/A (binding: `custom field labels`) |
| (reCAPTCHA widget) | store state | raw string | widget absent | N/A (binding: ``@current_community.recaptcha_site_key``) |

## UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| loading | Form already submitted (submit handler fires) | Submit button disabled, text changes to "Please wait" | none | `app/assets/javascripts/marketplace_common.js:51` |
| email async-checking | Blur on email field | jQuery Validate fires remote check | none (field blocked until resolved) | `app/assets/javascripts/kassi.js:392` |
| invitation_code async-checking | Blur on invitation_code field | jQuery Validate fires remote check | none | `app/assets/javascripts/kassi.js:396` |
| inline validation error | Invalid field value | Error label inserted after field | Correct field value | `app/assets/javascripts/kassi.js:378` |
| terms lightbox open | Click on "terms" link | `#terms` lightbox overlay rendered centered | Dismiss / accept | `app/assets/javascripts/kassi.js:368` |
| privacy lightbox open | Click on "privacy" link | `#privacy` lightbox overlay rendered centered | Dismiss | `app/assets/javascripts/kassi.js:371` |
| invitation code help open | Click on "What is this?" link | `#help_invitation_code` lightbox rendered centered | Dismiss | `app/assets/javascripts/kassi.js:364` |
| error (flash) | Server-side validation failure on POST | Flash error message shown (via layout) | Correct and resubmit | `app/controllers/people_controller.rb:53,71,89` |

## Validation & Error Feedback

### A) Client-side

| Field | Type | Required | Constraints | Async Check | Error Message |
|-------|------|----------|-------------|-------------|---------------|
| `person[given_name]` | text | conditional (`name_required` community setting) | maxlength: 30 | none | [UNVERIFIED] standard required message |
| `person[family_name]` | text | conditional (`name_required`) | maxlength: 30 | none | [UNVERIFIED] standard required message |
| `person[email]` | email | yes | email format, `email_remove_spaces` custom rule | `GET /people/check_email_availability_and_validity` | `email_in_use_message` (i18n, passed from controller) |
| `person[terms]` | checkbox | yes | must be checked | none | [UNVERIFIED] standard required message |
| `person[password]` | password | yes | minlength: 4 | none | [UNVERIFIED] standard required message |
| `person[password2]` | password | yes | minlength: 4, equalTo `#person_password1` | none | [UNVERIFIED] standard equalTo message |
| `invitation_code` | text | conditional (`invitation_required`) | none | `GET /people/check_invitation_code` | `invalid_invitation_code_message` (i18n, passed from controller) |

### B) Server-side

#### Create Person (POST /people)
- **Endpoint:** `POST /people`
- **Request:** `person[email], person[given_name], person[family_name], person[password], person[password2], person[terms], person[admin_emails_consent], person[consent], person[custom_field_values_attributes][], invitation_code, g-recaptcha-response`
- **Success:** `302` → redirect to `confirmation_pending_path`; flash notice "Account created, please confirm your email"
- **Errors:** reCAPTCHA failure → flash error; honey pot triggered → flash error + redirect; invalid invitation → flash error; email not allowed → flash error; DB error → `t("people.new.invalid_username_or_email")` flash error
- **Trigger:** "Create new account" button click / form submit
- **Source:** `app/controllers/people_controller.rb:49`

## Interaction Patterns

- **Clicking the "What is this?" link next to Invitation Code reveals a lightbox overlay centered on screen** — source: `app/assets/javascripts/kassi.js:364`
- **Clicking the "terms" link in the checkbox label opens the terms text in a lightbox overlay** — source: `app/assets/javascripts/kassi.js:368`
- **Clicking the "privacy" link in the checkbox label opens the privacy text in a lightbox overlay** — source: `app/assets/javascripts/kassi.js:371`
- **Email field blur triggers async remote validation against `/people/check_email_availability_and_validity`; validation is suppressed on keyup to reduce API calls** — source: `app/assets/javascripts/kassi.js:392,401`
- **Submit button is disabled and text replaced with "Please wait" upon form submission to prevent double-submit** — source: `app/assets/javascripts/marketplace_common.js:51`

## Conditional Rendering

| Condition | Type | Renders | Hidden | Notes |
|-----------|------|---------|--------|-------|
| `@community_customization.signup_info_content` present | auth | custom info paragraph | email restriction text | Consequence if bypassed: cosmetic only — no security boundary |
| `@current_community.allowed_emails` set and not regex | feature-flag | email restriction instructions | custom info | Cosmetic; server enforces email restriction on submit |
| `facebook_connect_in_use? && !params[:no_fb]` | feature-flag | Facebook OAuth button | nothing | Provider disabled at community level |
| `google_connect_in_use?` | feature-flag | Google OAuth button | nothing | Provider disabled at community level |
| `linkedin_connect_in_use?` | feature-flag | LinkedIn OAuth button | nothing | Provider disabled at community level |
| any OAuth provider active | feature-flag | horizontal divider + "Sign up with email" h3 | nothing | Layout separator |
| `@current_community.join_with_invite_only?` | feature-flag | invitation_code text field + help link | hidden invitation field | Server re-validates invitation code |
| `params[:code]` present but invite not required | legacy | hidden invitation code field | visible field | Pre-fills code from URL |
| `@service.has_person_custom_fields?` | feature-flag | community-specific custom field inputs | nothing | Fields vary per community |
| `!@skip_terms_checkbox` | feature-flag | terms & privacy checkbox | nothing | Server validates `person[terms]` |
| `@current_community.recaptcha_configured?` | feature-flag | reCAPTCHA widget | nothing | Server validates reCAPTCHA response |

---

*Developer appendix below — implementation detail (layout regions, component wiring, security guards, accessibility audit, source citations, code-reading order). BA/QA readers can stop here.*

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components | Responsive Behavior |
|-----------|------|----------|------------|----------------|---------------------|
| R1 | Page Title Header | static | no | `content_for :title_header` h1 | always visible |
| R2 | Signup Form | static | yes | `form_for @service.person`, OAuth buttons (Facebook, Google, LinkedIn), recaptcha, custom_field partials | `.centered-section` — centered, fluid width |
| R3 | Help Text Lightboxes | static (off-screen until triggered) | no | `_help_texts` partial — terms, privacy, help_invitation_code | hidden until JS lightbox trigger |

## Security Surface

| Guard | Type | Consequence if bypassed |
|-------|------|------------------------|
| `redirect_to search_path if logged_in?` (controller) | auth | Already-authenticated users see form but POST handled by server — no security exposure beyond UX confusion |
| Honey pot field `person[input_again]` (hidden CSS) | auth | Bots that fill all fields get rejected server-side with flash error |
| `validate_recaptcha` server-side check | auth | Bot submissions rejected with flash error; [UNVERIFIED] server enforcement — static analysis cannot confirm reCAPTCHA middleware bypass consequence |
| `Invitation.code_usable?` check | permission | Invalid invitation code rejected server-side; form never completes registration |

## Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | absent | No explicit `aria-*` attributes detected in view or JS |
| Keyboard navigation | partial | `tabindex="-1"` on help/terms/privacy links to exclude from tab order; autofocus not set on first field |
| Focus management | partial | Lightboxes opened but no focus trap found in kassi.js lightbox calls |
| Screen reader compatibility | unknown | `<label>` tags present and linked via `for` / `form.label` helpers; no `role` landmarks detected |

[NO_A11Y_DETECTED] — accessibility audit needed before production release.

## Source References

- Page/View: `app/views/people/new.haml:1`
- Controller: `app/controllers/people_controller.rb:33`
- Client-side validation: `app/assets/javascripts/kassi.js:363`
- Form initialization helper: `app/assets/javascripts/marketplace_common.js:51`
- Service: `app/services/persons/omniauth_service.rb:1` (OAuth provider helpers referenced)
- Routes: `config/routes.rb:816`
