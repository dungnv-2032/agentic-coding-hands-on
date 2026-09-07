# Screen Spec Researcher Contract (Wave 2.5 — rebuild-spec)

Consumed by W2.5 researcher subagents generating per-screen ScreenSpec artifacts.
Activated only when `--screen-specs` flag is set.

## Provenance Frontmatter (MANDATORY, byte 0)

Every `spec.md` this contract produces MUST open with the following as the literal first three
lines — before the `<!-- Contract: -->` HTML comment, and before the `# {SCR###_Name} — Screen
Spec` heading:

```yaml
---
authored_by: rebuild-spec
---
```

`_slug_lib._read_frontmatter()` requires the `---` fence at byte 0, so this block cannot be moved
below any comment (`templates/screen-spec-template.md` already carries it this way — start from
the template, do not hand-author the header). This is what lets the audience-split migration probe
(`_audience_split_probe_lib.py`) recognize a rebuild-spec-authored file by presence, instead of
falling back to the fail-closed `HAND_EDITED` default when the field is absent. Allowed
`authored_by` values are `takumi|rebuild-spec` — see
[`spec-authoring-contract.md`](spec-authoring-contract.md) § Draft Frontmatter Schema for the full
vocabulary (defined there, not restated here); rebuild-spec's own output is always
`authored_by: rebuild-spec`, never `takumi`. Do NOT omit this block, and do NOT invent a third value.

## Session Context

Read `plans/<active-plan>/artifacts/_session-context.md` FIRST. Then read the target SCR### section from `screen-list.md` and the relevant entity sections from `entities.md` (data model). Do NOT re-derive information already in the session context.

Note the project stack (frontend framework + backend language) from session-context.md. JS/TS (Vue/React) patterns are shown as primary examples throughout; inline `(stack: ...)` notes in each section provide alternatives for Python, Rails, PHP, and other stacks.

**v24.0.0 — Feature backlink (header, MANDATORY):** the screen-spec header MUST carry `**Feature**: F###_Name` (placed directly under `**Screen**`) — the feature that OWNS this screen, sourced from `screen-flow.md` § Feature Entry Points (`**Owned screens**`) or `feature-list.md`. It is the inverse of the `SCR###` column in that feature's `functional-spec.md`, and MUST resolve to a `feature-list.md` row (`validate_feature_screen_link.py` enforces it both ways).

## Human-readable SOT shape (§§1-10 + appendix)

The template (`templates/screen-spec-template.md`) emits 10 numbered BA/PO/QA/Designer sections
in this exact order, followed by a `## Technical Appendix` divider and 6 appendix H2 siblings:

| § | Heading | H3 children |
|---|---------|-------------|
| 1 | `## 1. Overview` | *(bold-label fields)* |
| 2 | `## 2. Screen Layout` | `### Layout Sketch`, `### Layout Regions` |
| 3 | `## 3. UI Elements` | *(one table)* |
| 4 | `## 4. User Actions` | `### Available Actions`, `### Happy Path`, `### Branches`, `### Interaction Notes` |
| 5 | `## 5. UI States` | *(one table)* |
| 6 | `## 6. Validation & Feedback` | *(one table)* |
| 7 | `## 7. Conditional UI` | *(one table)* |
| 8 | `## 8. Navigation` | `### Entry Points`, `### Exits` |
| 9 | `## 9. Accessibility` | *(one table)* |
| 10 | `## 10. Responsive Behavior` | *(one table)* |

Appendix (H2 siblings AFTER the `## Technical Appendix` divider, NOT nested under it): `##
Implementation Mapping` (A1, NEW) → `## Component Variants` (A2) → `## Child Routes` (A3,
H6-shell-only) → `## Security Surface` (A4) → `## Source References` (A5) → `## Source
Walkthrough` (A6).

**Contract vs. template boundary:** this contract prescribes *what to extract and where it
belongs*, referencing the section numbers above. It does not restate the template's exact
heading text or table syntax — that is the template's job. If this contract and the template
ever disagree on a heading string, the template
(and `plans/260818-1332-rebuild-spec-human-readable-sot/target-shape-spec.md` § 1, which is
normative for both) wins.

**Retired heading — do not write it.** `## Data Inventory` no longer exists as a heading. Its
content is absorbed into `## 3. UI Elements` (below). A researcher that emits `## Data
Inventory` has used a stale mental model — check yourself against the table above.

## Purpose Extraction Rule

Write 1 sentence in plain language: who uses this screen (role/persona), what they accomplish (goal), and when they encounter it (entry point or trigger).

**Voice:** User-narrative, not implementation-narrative.
- REJECT: "The Vue page renders a `FormContainer` with `useFormStore` composable..."
- ACCEPT: "Survey participants complete and submit assigned questionnaire forms from this screen."

**Source signals:** Page title, route name, primary CTA button label, primary form submit handler or main action event.
**N/A:** NOT allowed. If purpose is unclear from code, write `[UNVERIFIED] {best-effort description} — needs domain confirmation.`

## Scope Boundary (CRITICAL)

**ScreenSpec documents UI-LAYER behaviour only.**

| Belongs in ScreenSpec | Belongs in Feature Spec |
|----------------------|------------------------|
| UI states (loading/empty/error/success) | Server-side validation rules (BR/SM/ALG) |
| Client-side form validation (field constraints, async checks) | Business workflow (BR/SM/ALG) |
| Interaction patterns (optimistic update, infinite scroll) | Background logic (BL###) |
| ARIA roles, keyboard navigation, focus management | Decision logic (DEC-###) |
| Client-side conditional rendering (role gates, feature flags, breakpoints) | FR/BR/SM/ALG/INT/SC codes |
| Screen-specific UI state machines | Cross-feature navigation (→ screen-flow.md) |
| Server-side validation feedback visible to the user (error messages, toasts, banners) | Server-side validation logic itself |

**Never write FR/BR/SM/ALG/INT/SC codes in ScreenSpec.** Cross-reference `entities.md` for server-side field constraints (do not re-state them — reference the source).

## Mandatory Source-Code Reading

- You MUST read the actual source code files (controllers, models, jobs, services,
  Vue/React pages) for every screen — NOT just summarize from upstream artifacts.
- Use Grep/Read tools to find the real page/view files, form schemas, state managers for this SCR###.
- Extract specific: file paths with line ranges, component names, prop names, API call sites.
- If you cannot read a file, note it under `## Unresolved Questions`.

**Import Discovery Rule:** After reading the page/view file, collect all non-vendor component imports (JS/TS: `./` or `@/`; Python templates: `{% include %}`/`{% extends %}`; Ruby: `render partial:`/`require_relative`; PHP/Blade: `@include`/`@component`/`@extends`; generic: include/import/require patterns). For each imported component file:
1. Grep for async/form signals — JS/TS: `useQuery|useMutation|axios|\$fetch|api\.|useForm`; htmx: `hx-get|hx-post`; generic: `\.get(\|\.post(\|fetch(\|validate\|rules` *(omit Vue-only `emit\(` and `v-model` — too broad)*
2. If matched AND file > 20 lines → read lines containing the matched pattern ±30 lines of context
3. Document behavior-relevant findings under the appropriate section (UI States, Validation, Interaction Notes)
4. If file cannot be read: add to `## Unresolved Questions` as `(not read — referenced by import)`

**Depth:** 1 level only (page imports → components; do NOT follow component-to-component imports).

**Exception — file-exchange server actions:** when a submit-style action endpoint is file-producing/consuming (path/handler contains `export|import|download|upload`, or Content-Type is multipart/file), follow the backend handler (controller → job/service, bounded to that chain) far enough to identify the file schema. Cross-reference the feature's `BL-### File Schema` rather than re-deriving the column list (DRY). If the file-generation code cannot be reached within the controller→service chain, escalate under `## Unresolved Questions` — never silently omit.

## `E##` Element ID Allocation

- Assigned **top-to-bottom in reading order of the rendered screen** — the order a sighted user
  encounters elements, not source-file declaration order.
- Zero-padded to 2 (`E01`, `E02`, … `E10`, `E11`, …), unique within the screen.
- **Stable across regenerations:** if an element still exists on re-generation, it keeps its
  `E##`. Do not renumber the whole table because a middle element was removed — leave a gap.

## Referential Rules (§3 ↔ §4 ↔ §6 ↔ §7)

These four sections all key off the same `E##` inventory. A researcher MUST NOT leave a
dangling reference in either direction:

- Every `E##` cited in `## 4. § Available Actions`, `## 6. Validation & Feedback`, or
  `## 7. Conditional UI` MUST exist as a row in `## 3. UI Elements`.
- Every `## 3.` row with `Visibility: Conditional` MUST have a matching `## 7. Conditional UI`
  row explaining when it is visible/hidden.
- Every `## 3.` row with a non-`—` `Action` MUST have a matching `## 4. § Available Actions` row.

Before closing the spec, walk the `E##` column of § 3 against §§ 4/6/7 and fix any orphan on
either side — this is a self-check, not optional QA.

## Extraction Signatures

### §1 Overview

Populate the 4 bold-label fields:
- **Purpose:** see "Purpose Extraction Rule" above.
- **Actors:** plain role names actually observed gating access or acting on this screen (e.g.
  "Applicant, Reviewer") — comma separated, no auth-class/enum names (`ROLE_ADMIN` is wrong;
  "Admin" is right).
- **Entry Conditions:** what must be true for a user to reach this screen — partly derivable
  from `## 8. § Entry Points` once that section is filled; state it in plain language here
  regardless (e.g. "User is authenticated and has at least one active submission").
- **Exit Conditions:** the terminal states — what "done with this screen" means (e.g. "Form
  submitted successfully and user is redirected", "User cancels and returns to the list").

**N/A:** NOT allowed for any of the 4 fields. Use `[UNVERIFIED] {best-effort} — needs domain
confirmation` when a field cannot be confirmed from source.

### §2 Screen Layout

**`### Layout Sketch` (prose + ASCII, required):** Read page/view file root template/JSX. Name major regions (header, sidebar, main content, modals/drawers). Note fixed/sticky/scrollable positioning; responsive breakpoint signals (CSS class names, `useBreakpoint`, media queries). Cite layout root file:line in trailing parenthetical.

After the prose paragraph, draw top-level regions as ASCII boxes:
- Label each box: `R{N}: {Name} ({position})` — e.g., `R1: Top Nav (fixed-top)`
- Region IDs (R1, R2, …) MUST match the `### Layout Regions` table immediately below
- Use dashed lines (`- - -`) for conditionally visible regions (e.g., sidebar that collapses on mobile)
- Use nested boxes for floating/overlapping regions (modals, drawers, toast stack)
- Width/height proportions approximate — pixel-perfect not required
- Minimum 2 boxes (one per region in the Layout Regions table)
- Read root container CSS class names to infer the flex/grid axis (row vs. column splits)

Stack notes: Tailwind `flex flex-row`/`flex flex-col`/`fixed inset-0`; CSS Grid
`grid-template-areas` maps directly to region layout; SSR/templates — read outer `<div>` /
`<section>` class names + partial structure.

**N/A:** NOT allowed. Layout is always documentable. If page imports a layout wrapper not readable, write `[UNVERIFIED]` + escalate as Unresolved Question.

**`### Layout Regions` (table, required, ≥2 rows):** one row per top-level region.
- **Region ID:** sequential R1, R2, R3, … (stable within this spec only), matching the sketch.
- **Name:** human label (Top Nav, Sidebar, Main Content, Footer Toolbar, Modal Stack)
- **Position:** `fixed-top` | `sticky` | `static` | `absolute` (read from CSS/utility classes — Tailwind `fixed top-0`, Bootstrap `sticky-top`, plain CSS `position: fixed`)
- **Scrollable:** `yes` | `no` (read from `overflow-y-auto`, `overflow-scroll`, or container with explicit height + overflow)
- **Key Components:** comma-separated component names imported and rendered in this region (use the Import Discovery Rule output — already collected)

**No `Responsive Behavior` column here (DRY, see target-shape §1.4).** Any breakpoint-dependent
behavior for a region becomes a `## 10. Responsive Behavior` row instead, with `Region /
Element` naming the Region ID.

Stack notes: SSR/template (Django/Rails/Blade) — `Key Components` may be partial names
(`_sidebar.html.erb`, `@include('partials.nav')`, `{% include "header.html" %}`) or CSS class
selectors when partials are not used; htmx-driven — regions with `hx-target` are independent
scroll/swap units, flag their breakpoint behavior (if any) in `## 10.`.

**N/A:** NOT allowed. If a layout wrapper is not readable, write `[UNVERIFIED]` row + escalate as Unresolved Question.

### §3 UI Elements

**Scope:** every rendered element — read-only display fields AND editable form inputs AND
buttons/links — in ONE inventory (D2 merge; absorbs the retired `## Data Inventory` and the
field-identity half of the retired `## Validation & Error Feedback § A`).

**Source signals — display bindings:**
- JS/TS (Vue): `{{ field }}`, `v-text="field"`, `:value="field"`, `v-model="field"` (templates)
- JS/TS (React/JSX): `{field}`, `value={field}`, `{user.name}`, `{data?.email}`
- Python (Django/Jinja): `{{ field }}`, `{{ object.field }}`, `{{ user.name }}`
- Rails ERB: `<%= field %>`, `<%= @user.name %>`
- PHP/Blade: `{{ $field }}`, `{!! $field !!}`, `{{ $user->name }}`
- htmx: `hx-vals` payload (sent fields) + response template's bindings (displayed fields)

**Source signals — computed:** `computed(() => ...)`, `useMemo(...)`, getter functions,
template-level string interpolation.

**Source signals — editable inputs:** `<input>`, `<textarea>`, `<select>`, HTML5
`required`/`pattern`/`min`/`max`, form libraries (`useForm`, `Formik`, `react-hook-form`,
`vee-validate`, `VueUseForm`, Zod/Yup/Joi schemas).

**Source signals — buttons/links:** primary CTA elements, submit buttons, nav links, icon
buttons with a click handler.

**Per-row extraction:**
- **ID:** next `E##` in reading order (see "`E##` Element ID Allocation" above).
- **Element:** the visible label text the user sees (read adjacent `<label>` tag, table `<th>` header, button text, or aria-label) — never the source-code variable/binding name.
- **Type:** one of the vocabulary listed in the template's `## 3.` comment (`text input`, `password input`, `textarea`, `select`, `checkbox`, `radio`, `file input`, `date input`, `button`, `link`, `message`, `display field`, `image`, `list`, `table`, `region label`).
- **Required:** `yes` | `no` for inputs; `—` for non-input elements.
- **Default:** initial value/state (`Empty`, `Enabled`, `Disabled`, `Hidden`, `Visible`, or a literal).
- **Visibility:** `Always` | `Conditional` — every `Conditional` row needs a matching `## 7.` row (see Referential Rules).
- **Action:** one-phrase user-visible effect for buttons/links (e.g. "Submits login form"), or `—`. Any real Action needs a matching `## 4. § Available Actions` row.
- **Source** (displayed-value provenance only — inputs the user types into are `—` here): `API field` | `route param` | `store state` | `computed` | `static` | `—`.
- **Format:** date format / currency / truncation / raw / `—`.
- **Empty Behavior:** `dash` | placeholder text | `hidden` | `—`.
- **Cross-ref:** `MODEL###.field` when the field maps to a documented entity attribute; append `` (binding: `{name}`) `` when the binding name is worth keeping; `N/A` for transient UI-only state.

**Cap:** 25 primary rows. For dense screens (data tables with many columns), group repetitive patterns as one row with `{field_1..N}` notation + a trailing note.

**Do NOT include:** DB constraints (NOT NULL, FK, unique — that's `data-model.md` territory), server-side validation rules (that's Feature Spec), API-response fields never rendered to the user, layout/styling attributes (`className`, `style`).

**N/A:** `N/A — screen displays no dynamic data and has no interactive elements (static marketing/error page)` — valid only after scanning source confirms zero bindings/interpolations and zero interactive controls.

**[UNVERIFIED]:** Use for a format inferred from a binding name without a confirmed formatter call. Example: `[UNVERIFIED] currency format — needs runtime confirmation`.

### §4 User Actions

**`### Available Actions` (table):** one row per `## 3.` element whose `Action` column is
non-`—`. `Element` is the `E##` reference (never re-list the field name). `Result on this
screen` is within-screen only — anything that leaves the screen belongs in `## 8. Navigation`
instead.

**N/A:** `N/A — no elements carry a discrete user-triggered action.` — valid only when every
`## 3.` row has `Action: —`.

**`### Happy Path` (numbered prose) and `### Branches` (table) — scope and signals unchanged
from the pre-SOT shape:**

**Scope:** Within-screen interactions only. Cross-screen navigation (router transitions to other SCR###) is documented in `## 8. Navigation` — NOT here.

**Source signals — happy path:**
- Primary CTA handler (button onClick / form onSubmit / link click) and what UI state it produces on this screen
- Step controllers: `currentStep`, `wizardStep`, `step` state variable; conditional render gated on step value (stays on same screen)
- Inline state transitions: `setIsEditing(true)` → form replaces read-only view; `showConfirm` → confirmation panel appears
- Async submission feedback: spinner → success toast → form reset (all observable on this screen)

**Source signals — branches:**
- Validation early-exit before submit (returns without API call)
- Conditional render based on form state: error inline vs. success panel
- Permission gates that swap visible region (e.g., admin sees extra panel)
- Empty/error/loading state branches (cross-ref `## 5. UI States` — but mention the user-visible branch here)

**Exclude:**
- `router.push(...)` / `navigate(...)` / `Inertia.visit(...)` to a different route → belongs in `## 8. Navigation`
- Cross-screen redirects on success → mention as a terminal step (e.g., "submit → redirect to {SCR###}"), do NOT detail the next screen — the § Exits *table* in `## 8.` is the only place that may name the destination

**[WARN_ADVISORY]:** If `screen-flow.md` is already loaded in context, spot-check that Happy Path terminal steps align with navigation events in `## 8. Navigation`. This is advisory only — do NOT load screen-flow.md solely for this check.

**Format:** Happy Path = numbered prose steps, one observable action/response per step. Branches = table with Decision point | Condition | Outcome on this screen | Source.

**Stack-specific signals:** JS/TS (Vue/React) — `useState`, `ref()`, `reactive()`,
`currentStep`, event handlers on root template; Python templates (Django/Jinja) — form POST →
re-render with errors, `{% if form.errors %}` branches; Rails/PHP — form `action` POST →
controller re-renders same view with `@errors`/`$errors`; htmx — `hx-post` returning partial →
swap target, `hx-trigger` chains.

**N/A (Branches only):** `N/A — single-action screen, no branches` — valid only when the screen has exactly 1 CTA AND no `currentStep`/`isEditing`/conditional render based on form state.

**[UNVERIFIED]:** Use when a branch outcome is inferred (e.g., toast text not readable from source).

**`### Interaction Notes` (bullets, MOVE from the retired `## Interaction Patterns`):** extract
non-trivial patterns — optimistic update, infinite scroll, drag-drop, debounced search, keyboard
shortcut.

**Format MUST be behavior-first:** `**{User behavior — observable outcome}** — source: {file:line}`

Implementation details (handler name, store action) may appear in trailing parenthetical — NEVER first.

- REJECT: "Root `div` has `@click='resetTarget'` which calls `store.dispatch(...)`..."
- ACCEPT: "Clicking outside any group deselects it — source: questions.vue:2"

Researcher MUST reformulate any handler-first extraction before writing.

**N/A:** `N/A — no non-trivial interaction patterns detected (only standard form input bindings).`

### §5 UI States

Scan page/view file and immediate dependencies for async signals:

- Loading: `isLoading`, `loading`, skeleton components, `Suspense`, spinner
- Empty: `isEmpty`, `data.length === 0`, empty-state components, zero-results branches
- Error: `isError`, `error !== null`, error boundary, catch blocks in data hooks
- Success: toast calls, `showSuccess`, confirmation components, mutation success handlers
- Custom: any named state not covered above (`isDraft`, `isPending`, etc.)

**Depth rule:** Scan for async calls by frontend paradigm — SPA (Vue/React/Angular): `axios|fetch|useQuery|useMutation|asyncData|\$fetch|API\.|api\.`; htmx-driven: `hx-get|hx-post|hx-patch|hx-delete|hx-trigger`; Turbo (Rails): `data-turbo-stream`; generic: `\.get(\|\.post(\|\.put(\|\.delete(` — produce ≥1 error row per distinct async endpoint + ≥1 empty row per data-displaying region. For each state: record trigger, visual component, user actions, source file:line.

**N/A:** `N/A — no async ops` — valid only when grep returns zero async matches AND screen renders no list/data block.

### §6 Validation & Feedback

**Scope:** the reader-facing rule + the user-visible message text, merged from the retired
`## Validation & Error Feedback § A/§B`. Endpoint, HTTP status, async-check URL, and
request/response shape are implementation detail — they go to `## Implementation Mapping`
(appendix), never here.

**Client-side rules:** scan for client-side validation (runs in browser — backend validation
rules belong in Feature Spec) — JS/TS: `useForm`, `Formik`, `react-hook-form`, `vee-validate`,
`VueUseForm`, Zod/Yup/Joi; all stacks: HTML5 `required`/`pattern`/`min`/`max`; generic:
`validate|rules|constraints`. For each field, emit one `## 6.` row: `Element` = the field's
`E##`, `Rule` = plain language (`Required`, `Must be a valid email`, `Must match Password` — not
a regex), `Feedback` = the exact user-visible message text, `Trigger` = `blur`/`change`/`submit`.

**Server-side, user-visible portion:** signature — action handler containing `await
{api}.{method}(...)` combined with `.catch`/try-catch/`.then(err => ...)` that surfaces a
user-visible error (toast, banner, inline message). For each such action: locate the message
text and emit a `## 6.` row with `Element` = the submitting `E##`, `Trigger` = `server
response`. Deciding which error text a user actually sees (vs. an internal-only error code) is
a judgment call — do it here, not mechanically.

**Server-side escalation (before `[UNVERIFIED]`):** if an error message is server-driven, first
locate and read the endpoint's backend validator class (FormRequest / request-validator /
serializer / DTO). If read → extract the real message (no `[UNVERIFIED]`). Only if the class
cannot be found or read may you write `[UNVERIFIED]`, and you MUST add a matching `##
Unresolved Questions` entry naming the endpoint + the validator path you could not reach.
(stack: Laravel `app/Http/Requests/*Request.php`; Rails strong params / `validates` in model;
DRF serializer `*Serializer`; NestJS DTO `class-validator` decorators; Zod/Yup schema on the
route handler — non-exhaustive.)

*Cross-ref: the `verification-checklist-screen-spec.md` rule "Validation rules documented that
are server-side only" covers documentation presence for server-side-only validation rules — a
related but distinct concern from the escalation-attempt requirement above.*

**Implementation detail that does NOT belong here** (route to `## Implementation Mapping`
instead): endpoint method+path, request field list, HTTP success/error codes, async-check URL.
For file-producing/consuming endpoints (see Import Discovery Rule exception above), record
`Kind: endpoint` + `Implementation: File schema — see BL-### File Schema (behavior-logic.md)`
instead of restating columns.

**N/A:** `N/A — no validation rules or submit-side error feedback detected.`

### §7 Conditional UI

Scan for runtime gates by type:

- **auth:** `hasRole`, `currentUser.role`, `can(`, `ability.can`, `isAdmin`, permission-based visibility
- **feature-flag:** `useFlag`, `useFeature`, `isEnabled`, `featureFlag(`, `checkFlag`
- **configuration:** a non-boolean config/settings value gates rendering (tenant setting, plan tier, env-driven toggle read from a config service rather than a boolean feature-flag API)
- **responsive:** CSS-in-JS breakpoint checks, `useMediaQuery`, `useBreakpoint`, Tailwind responsive classes controlling visibility
- **legacy:** condition that compares against a string constant name (e.g., `status === 'LEGACY_MODE'`) with no feature-flag API
- **hardcoded-id:** condition that compares a route param, entity ID, or field value against a numeric/string literal (e.g., `Number($route.params.form) === 458`)

**`Condition` column rule:** state it as **user-visible behavior first** ("Facebook login is
offered when the community has Facebook login enabled"), never as the raw expression
(`FeatureFlagHelper.feature_enabled?(...)`). The implementing expression goes to `##
Implementation Mapping` instead — do not drop it, relocate it.

**`Element(s)` column:** `E##` reference(s) into `## 3. UI Elements` — see Referential Rules.

**Notes column rules:**
- `auth` type → Notes MUST state: "Consequence if bypassed: {redirect / 403 / data exposure}". If consequence cannot be determined from source, write `[UNVERIFIED] consequence — needs security review`.
- `hardcoded-id` or `legacy` type → Notes MUST contain: `[NEEDS_DOMAIN_CONFIRMATION] — {description of what this gate does}; unknown whether legacy bug, feature flag, or intentional design`
- `feature-flag` / `configuration` / `responsive` → Notes optional

**N/A:** `N/A — no conditional UI detected.`

### §8 Navigation

**D3 — the DRY statement that MUST appear verbatim in the template and the contract:**

> `## 8. Navigation` is the **per-screen projection** of `screen-flow.md § Screen Access Paths`.
> It is not a second source of truth. Every row here MUST be derivable from a path in
> `screen-flow.md`; every path in `screen-flow.md` touching this SCR### MUST appear here.
> Two-way consistency is a reviewer rule (`screen.nav_flow_skew`), not a Python check.
> `## 4. User Actions § Happy Path` narrative keeps its v27 scope rule unchanged: **prose still
> must not narrate cross-screen navigation**; only the § Exits *table* may name destinations.

**Do NOT invent destinations.** Fill `### Entry Points` and `### Exits` as a projection read
FROM `screen-flow.md § Screen Access Paths` for this SCR### — never guess a destination from
the button label alone (feedback: "Không tự suy diễn destination"). If `screen-flow.md` has no
path touching this screen yet, leave the row scaffolded and escalate under `## Unresolved
Questions` rather than fabricating one.

**`### Entry Points`:** `From` (originating SCR###_Name or `external`), `Trigger there` (the
gesture/event on the origin screen that leads here), `Condition` (or `—`), `Source` (file:line
of the route/link definition, or the `screen-flow.md` path entry).

**`### Exits`:** `Action` (name matching an `## 4. § Available Actions` row where applicable),
`Element` (`E##`), `Condition` (or `—`), `Destination` (`SCR###_Name`, an external URL, or
`(stays on screen)`), `Result` (redirect / new tab / modal / toast then redirect), `Source`.

**N/A:** `N/A — this screen has no other entry points beyond the ones enumerated in
screen-flow.md.` (Entry Points) / `N/A — this screen has no exits (terminal screen).` (Exits).

### §9 Accessibility

Always produce the 5-row table (Aspect | Status | Notes) — no section-level N/A.

Per-row scan signatures:
- **ARIA roles/labels:** `aria-\w+|role=` across component files
- **Keyboard navigation:** explicit `keydown|keyup|keypress|tabindex` handlers
- **Focus management:** `\.focus\(\)|focus-trap|useFocus|autofocus`
- **Screen reader compatibility:** `<label>` linkage, semantic landmarks (`role="main"`, `role="dialog"`)
- **Error announcement:** `aria-live`, `role="alert"` on validation/error message containers

**`[EXPECTED]` usage here (v27 amendment, see `references/confidence-report-contract.md`):** a
row describing something the code does NOT currently do — e.g. recommending an `aria-live`
region be added — is written with `Status: [EXPECTED]`, never as if it were already
implemented. `[EXPECTED]` is for recommendations/desired behavior; it is never a substitute for
observing and reporting what the code actually does today.

When all 5 status cells are absent/unmanaged/unknown, append:
`[NO_A11Y_DETECTED] — accessibility audit needed before production release.`

### §10 Responsive Behavior

**Source:** primarily the `Responsive Behavior` cells that used to live in `### Layout Regions`
— each non-empty cell becomes one `## 10.` row here instead (`Region / Element` = the Region ID,
`Behavior` = what the cell described). Also capture any breakpoint-gated `## 7. Conditional UI`
row whose visibility is `responsive`-typed (cross-reference, don't duplicate the full condition
text — name the `E##`/Region and summarize the breakpoint behavior).

**`Breakpoint`:** `desktop` | `tablet` | `mobile` | a literal media query.

**N/A:** `N/A — no responsive behavior found in source.` — valid only after confirming zero
breakpoint-dependent regions/elements.

## Appendix A1 — Implementation Mapping

**NEW section.** Receives everything demoted out of §§1-10: submit-action endpoint/request/
response detail (from the retired `## Validation & Error Feedback § B`), conditional-UI
implementing expressions (from `## 7.`'s raw condition), JS wiring, session state, and any other
controller/class-name-level detail a BA/QA/Designer reader does not need.

Per submit-style action, one block's worth of implementation detail becomes consecutive rows:
- **Refers to:** the `E##` / `## N.` section / region `R#` this implementation detail is
  attached to.
- **Kind:** `endpoint` | `handler` | `helper` | `feature-flag` | `session` | `js` | `guard` |
  `component`.
- **Implementation:** `{METHOD /path}`, a function/class name, or the raw expression.
- **Source:** `file:line`.

Record, at minimum, for each submit-style action: `Endpoint` (METHOD + path), `Request` (field
names sent — skip auth headers; if assembled beyond Import Discovery depth, write
`[UNVERIFIED] — payload assembled outside 1-level read depth; see Unresolved Questions`),
`Success` (HTTP code + outcome), and any error code → internal message that is NOT the
user-visible text already captured in `## 6.`.

**N/A:** `N/A — no implementation-level detail beyond what is already cited inline above.`

## Appendix A2 — Component Variants (optional)

**Trigger:** component imported on this screen also appears in ≥2 other screens in ScreenList AND renders ≥2 visual variants based on a discriminating field.

Scan: component file's render switch (`v-if`, switch statement, ternary chain) keyed off a prop value.

Output: screen-specific props/slots only. Reference DISC-### in data-model.md OR feature-spec § Polymorphic Behavior for variant business rules. DO NOT re-document the component's universal behavior.

**Omit section entirely when criteria not met** — this is the only optional section.

## Appendix A3 — Child Routes (H6 shells only)

Trigger: screen tagged `[H6]` in screen-list.md. See "H6 Shell Screen Protocol" below for the
full protocol; this appendix section holds the resulting table.

## Appendix A4 — Security Surface

**Trigger:** Populate when `## 7. Conditional UI` has ≥1 `auth`-type row OR a route guard / navigation guard is found in the router config for this screen's route.

**Scan for:**
- Route-level guards (find router/routes config, check this screen's route entry): JS/TS: `src/router/index.{js,ts}` — grep `beforeEnter|meta\.requiresAuth|meta\.roles|router\.beforeEach`; Python: grep `@login_required|LoginRequiredMixin` in views/urls; Rails: grep `before_action :authenticate` in controllers; PHP: grep `->middleware('auth')` in route files; generic: grep `auth|guard|middleware` on route entries
- Component-level guards (auth conditional gating component render): JS/TS: `v-if="isAuthenticated"`, `can('action','resource')`; Python: `{% if user.is_authenticated %}`; Rails: `if current_user.admin?`; PHP: `@auth`/`@can` Blade directives; generic: conditional block keyed on auth/permission check
- Data-access guards: API calls that return 403 when unauthorized (document the permission boundary)

**For each guard, record:**
- Guard expression or middleware name
- Type: `auth` (login required) | `permission` (role/ability check) | `role` (specific role required)
- Consequence if bypassed: what a non-authorized user would see or access. If not determinable from static analysis, write `[UNVERIFIED] server enforcement — static analysis cannot confirm API middleware`.

**N/A:** `N/A — no auth guards or permission checks detected on this screen.`
Valid only when: `## 7. Conditional UI` has zero `auth`-type rows AND router config has no guard for this route.

## Appendix A5 — Source References

- Minimum 1 entry: the page/view file
- List every file actually read while extracting (not aspirational paths)
- If a file should exist but could not be found, log under Unresolved Questions — never fabricate

## Appendix A6 — Source Walkthrough (A3, v26.0.0)

**HARD CONSTRAINT — do not demote or renumber.** `## Source Walkthrough` MUST stay a literal,
unnumbered H2 in the emitted file — `_spec_constants.A3_HEADING` is matched as an anchored
literal H2 by `validate_reading_guide_db_impact.py::_section_body`. A researcher (or a future
editor) nesting it as `### Source Walkthrough` under `## Technical Appendix` makes the section
read as ABSENT and fires `reading_guide.pre_migration` on the spec. The template's own HTML
comment carries this same warning beside the heading — do not remove it.

**Scope:** UI-layer only, mirroring Appendix A5 — this screen's own files, not the owning
feature's server-side files (those belong in the feature's `technical-spec.md` § Source
Walkthrough).

Ordered reading list covering the files in Appendix A5 Source References (data model cross-ref →
entry point → view → interaction logic), 1 file per step, with a 1-sentence "why start here."
Cite each entry with `**File:**` (NOT `**Source:**` — keeps this navigational list out of the
A1 confidence-report citation-coverage stat; see `references/confidence-report-contract.md` §
A3 navigational entries). Followed by a `### Call Hierarchy` diagram (ASCII or Mermaid: page/view
→ component → store/hook) and a pointer line: "see `## Source References` above" — do NOT
author a second, independent file list (F15 DRY; Appendix A5's list is numbered/ordered already).
**v26.2.0:** a `### Data Flow` subsection (user interaction/props → component state update →
store/hook → re-render) is BEST-EFFORT — same discretion as `### Call Hierarchy`, no dedicated
enforcement beyond the whole-section check.

**MANDATORY — no N/A fallback.** Every screen has source to walk through (at minimum the
page/view file from Appendix A5).

**Gated by:** `scripts/validate_reading_guide_db_impact.py` (dedicated validator, WARN-first
`*.pre_migration` degradation contract — screen-spec has no other Python structural validator
today).

## N/A Fallback Master Rule

Researcher MUST scan source file + immediate imports before writing any N/A. N/A is valid only after confirming absence — not as a default. At least one section MUST be populated (all-N/A = reviewer warning).

Rows below follow the SOT §1-10 + appendix order. `## Data Inventory` and `Screen Layout` (as a
wrapping H2) no longer exist as section names — see the shape table above.

| Section | Exact N/A string |
|---------|-----------------|
| §1 Overview | N/A — not allowed for any field; write `[UNVERIFIED]` if unclear |
| §2 Layout Sketch | N/A — not allowed; escalate as Unresolved Question |
| §2 Layout Regions | N/A — not allowed; minimum 2 rows required |
| §3 UI Elements | `N/A — screen displays no dynamic data and has no interactive elements (static marketing/error page)` |
| §4 Available Actions | `N/A — no elements carry a discrete user-triggered action.` |
| §4 Branches | `N/A — single-action screen, no branches` |
| §4 Interaction Notes | `N/A — no non-trivial interaction patterns detected (only standard form input bindings).` |
| §5 UI States | `N/A — no async ops` |
| §6 Validation & Feedback | `N/A — no validation rules or submit-side error feedback detected.` |
| §7 Conditional UI | `N/A — no conditional UI detected.` |
| §8 Entry Points | `N/A — this screen has no other entry points beyond the ones enumerated in screen-flow.md.` |
| §8 Exits | `N/A — this screen has no exits (terminal screen).` |
| §9 Accessibility | No section-level N/A; always write the 5-row table |
| §10 Responsive Behavior | `N/A — no responsive behavior found in source.` |
| Appendix A1 Implementation Mapping | `N/A — no implementation-level detail beyond what is already cited inline above.` |
| Appendix A2 Component Variants | Omit section entirely |
| Appendix A3 Child Routes | N/A — section omitted unless screen is tagged `[H6]` |
| Appendix A4 Security Surface | `N/A — no auth guards or permission checks detected on this screen.` |
| Appendix A6 Source Walkthrough | N/A — not allowed; every screen has source to walk through |

## Never-Invent Rule (client's core demand — quote verbatim)

> Never promote an observed current behavior into a SHOULD. If code does X and X looks wrong,
> write X, mark it, and open an Unresolved Question. Do not invent, do not fix, do not delete as
> "merely technical".

This governs every section above. If code does something that looks like a bug, the spec still
records the observed behavior (cited or marker-tagged as appropriate) and opens an `##
Unresolved Questions` entry — it never silently "corrects" the observation into what the
researcher thinks the code *should* do, and it never omits the observation as not worth
documenting.

## `[UNVERIFIED]` Marker Protocol

Use `[UNVERIFIED]` when a value is observable only at runtime and cannot be confirmed from source alone.

**Format:** `[UNVERIFIED] {best-effort description} — needs runtime confirmation`

**Example:** `[UNVERIFIED] "Email already registered" toast — needs runtime confirmation`

- Distinct from **N/A** — N/A means "scanned, confirmed absent"; [UNVERIFIED] means "likely present, not confirmable from static analysis"
- Distinct from **fabrication** — fabrication is banned; [UNVERIFIED] is a tracked best-effort with explicit caveat
- Use for: exact server error message text, toast duration, animation timing, backend-driven content
- For server-side error messages, `[UNVERIFIED]` is valid ONLY after attempting to read the backend FormRequest/validator class (see §6 escalation). Unattempted → reviewer warning.

**Canonical trailing phrase variants:**
- `— needs runtime confirmation` — use when value is observable at runtime (toast text, animation timing)
- `— needs domain confirmation` — use when value requires domain expert input (purpose, business intent)

## `[NEEDS_DOMAIN_CONFIRMATION]` Marker Protocol

Use `[NEEDS_DOMAIN_CONFIRMATION]` when a condition's intent cannot be determined from static analysis alone and requires domain expert input.

**When to use:** `## 7. Conditional UI` rows where `Type` is `hardcoded-id` or `legacy`.

**Canonical format:** `[NEEDS_DOMAIN_CONFIRMATION] — {what this gate does}; unknown whether legacy bug, feature flag, or intentional design`

**Example:** `[NEEDS_DOMAIN_CONFIRMATION] — hides form for form ID 458; unknown whether legacy bug, feature flag, or intentional design`

- Distinct from `[UNVERIFIED]` — [UNVERIFIED] means "likely present but unconfirmable from source"; [NEEDS_DOMAIN_CONFIRMATION] means "present and confirmed, but purpose is unknown"
- Always include a description of what the gate does — never write bare `[NEEDS_DOMAIN_CONFIRMATION]`

## `[EXPECTED]` Marker Protocol (v27 amendment, D6)

`[EXPECTED]` is the 4th status marker (see `references/confidence-report-contract.md` § "v27
amendment — the 4th state" — canonical home for this marker's derivation rules and its `△`
mapping in the A1 confidence report). It is defined and used here per that contract:

- **Use it for:** desired/agreed behavior that a stakeholder has signed off on as the target but
  that the code does not currently implement or confirm — e.g. an accessibility improvement not
  yet built (`## 9.`), a responsive breakpoint the design calls for but the code doesn't gate on
  yet (`## 10.`).
- **Never use it for:** current behavior. `[EXPECTED]` describes what SHOULD exist, never what
  DOES exist. If you are describing what the code does today — even if it looks wrong — that is
  a plain statement (cited) or `[UNVERIFIED]`, never `[EXPECTED]`.
- **The boundary test:** if you catch yourself writing `[UNVERIFIED]` for something you are
  actually recommending rather than something you failed to pin down, it is `[EXPECTED]`
  instead.
- **`[EXPECTED]` never promotes to an Open Decision** — it is a recorded, agreed decision, not
  an open question. Only `[NEEDS_DOMAIN_CONFIRMATION]` promotes.

## SHARED_COMPONENT Extraction Rule

A component is SHARED when it appears in ≥2 screens in ScreenList.

For shared components on this screen, document ONLY:
- Props this screen passes to the component
- Slot content this screen injects
- Events this screen handles from the component

DO NOT re-document the component's universal behavior. Defer to:
- DataModel DISC-### entry (for discriminator-driven variants)
- Feature spec § Polymorphic Behavior (for cross-feature variant logic)

## H6 Shell Screen Protocol

**Trigger:** Screen tagged `[H6]` in screen-list.md, OR screen file's primary template contains a router outlet (`<nuxt-child>`, `<router-view>`, `<Outlet>`, `<router-outlet>`) with ≥2 child routes in route config.

**Problem this solves:** H6 shell files have minimal logic (persistent nav + outlet). Standard extraction produces: Layout Sketch = nav component only, all other sections = N/A. The spec must communicate orchestration purpose and child route structure.

**SOT order note:** `### Layout Sketch`/`### Layout Regions` live in `## 2.` (reader body);
`## Child Routes` lives in the appendix (Appendix A3, after `## Component Variants`, before
`## Security Surface`).

### 1. Overview (§1)
Write Purpose as navigation orchestration — not feature description:
> "{Persona} navigates between {child screen names} via the {nav component name}. The {nav} persists across all child routes while content in the main region updates per active route."

### 2. Layout Sketch (§2)
- **R1 (persistent UI):** Name the component, describe behavior (static/data-driven), note scroll axis (horizontal/vertical), note if data-driven (then add loading row to `## 5. UI States`). Cite file:line.
- **R2 (outlet):** Write exactly: "R2: child outlet — delegates rendering to [{SCR###a} / {SCR###b}] per active route. No direct content rendered here."

### 3. UI States (§5)
- Shell-level only. DO NOT document child screen states here.
- If persistent nav loads data asynchronously → add loading/error row for it.
- If persistent nav is fully static → `N/A — no async ops` is valid (no scan of child files required).

### 4. Interaction Notes (§4)
Navigation actions qualify as non-trivial interaction patterns:
- `**Clicking a {circle/tab/step} in the {nav name} navigates to {SCR###} at {URL}** — source: {file:line}`
- Include keyboard navigation if the nav supports it.

### 5. Validation & Feedback (§6)
`N/A` is expected — shell screens have no forms. Do not scan child files to fill this.

### 6. Layout Regions (§2)
Mirror R1/R2 as table rows (see the standard `### Layout Regions` extraction signature, §2 above).

### 7. Child Routes (MANDATORY for H6 shells, Appendix A3)
Add `## Child Routes` section in the spec (appendix — after `## Component Variants`, before `## Security Surface`). Read route config to enumerate:

| Route | SCR | URL | Notes |
|-------|-----|-----|-------|
| {label visible in nav} | SCR###a | /path/a | {one-line child purpose} |

**Route config locations by stack:**
- Nuxt 2: infer from `pages/` directory structure (subdirectory = child route)
- Vue Router: `src/router/index.{js,ts}` or `routes.ts` — `children:` array under parent route
- React Router v6: `react-router-dom` route config — `<Outlet>` parent children
- Angular: `RouterModule.forChild` children array

### 8. Source References (Appendix A5)
Always include:
- Shell layout file
- Route config file (where child routes are defined)

### Shell vs Child Boundary (CRITICAL)
Shell spec documents: persistent UI + navigation patterns + child route enumeration.
Shell spec does NOT include: forms, data tables, modals, or async calls specific to child screens.
Reviewer flags child-screen content in shell spec as scope violation.

## H6 Child Screen Context

**Trigger:** Screen is a child route inside an H6 shell (parent shell SCR### tagged `[H6]` in screen-list.md AND this screen's route is in parent's Child Routes table).

**Protocol:**

1. **Layout Sketch (§2)** — Open with one sentence: "Renders inside [parent SCR###_Name] shell at the child outlet (R2). The shell's persistent [nav component] is always visible." Then document this screen's own content (form fields, data table, etc.) — DO NOT re-describe the parent's persistent nav.

2. **Source References (Appendix A5)** — Add the parent shell file as a context reference (not as the primary source): `Parent shell context: {parent-layout-file}:{line}`.

3. **Navigation entry/exit (§8)** — Document only the screen's own navigation triggers (submit, next-step button). Timeline-click navigation belongs in the parent shell spec, not here.

4. **Scope** — Child screen spec documents the screen's own forms/data/interactions in full. The shell's persistent nav is referenced, not re-documented.

**Reviewer rule:** Child spec MUST NOT contain a full description of the shell's Timeline/sidebar/header — only a one-line context reference. Full re-documentation → warning.

## Output Path

Draft: `plans/<active-plan>/artifacts/screens/{SCR###_Name}/spec.md`

<!-- layout-exempt: rebuild-spec promote target for ScreenSpec — definitional output path, mode-resolved at runtime -->
Final (promoted by Wave SS.3): `docs/screens/{SCR###_Name}/spec.md`

### Confidence Companion (advisory sidecar)

`confidence-report_spec.md` is NOT part of the researcher's output above. It is emitted
automatically by `scripts/derive_confidence_report.py` (a deterministic script, not authored
by the researcher) after `spec.md` is promoted — a citation-coverage sidecar, never gated,
never asserted. See `references/confidence-report-contract.md` for the full derivation rules
and the A1 correctness-verification boundary.

## Task Closure

Call `TaskUpdate(status=completed)` on this task BEFORE returning.
