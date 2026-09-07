---
authored_by: rebuild-spec
---
<!-- Contract: references/screen-spec-researcher-contract.md -->
<!-- Human-readable SOT reshape: 10 numbered BA/PO/QA/Designer sections (§1-§10), then a
     `## Technical Appendix` divider, then 6 appendix H2 siblings (A1-A6). PO/BA/QA/Designer
     readers can stop at § 10; everything past the divider is implementation detail.
     Section list, table columns, and heading text are normative in
     plans/260818-1332-rebuild-spec-human-readable-sot/target-shape-spec.md § 1 — copy from
     there, do not paraphrase. -->

# {SCR###_Name} — Screen Spec

**Screen**: {SCR###_CODE}: {NAME}
**Feature**: {F###_NAME}
**Type**: {atomic|composite}
**Route**: {URL}
**Generated**: {DATE}

<!-- **Feature** is the F###_NameSlug (from feature-list.md) that OWNS this screen — the
     inverse of the SCR### column in that feature's functional-spec.md § 5 Screens. MUST resolve to a row in
     feature-list.md (validate_feature_screen_link.py enforces this). -->

## 1. Overview

**Purpose:** {1 sentence — who uses this screen, what they accomplish, and when they meet it. Plain language — no component names, no technical internals.}
**Actors:** {plain role names, comma separated — no auth-class names}
**Entry Conditions:** {what must be true for a user to reach this screen}
**Exit Conditions:** {the terminal states — what "done with this screen" means}

<!-- N/A is NOT allowed for Purpose. If unclear from code, write [UNVERIFIED] + best-effort description. -->

## 2. Screen Layout

### Layout Sketch

{2–4 sentences naming major regions (header, sidebar, main content area, modals/drawers). Note fixed/sticky positioning and responsive breakpoints if present. Cite layout root file:line in trailing parenthetical.}

<!-- N/A is NOT allowed here. If layout is truly unreadable, escalate as Unresolved Question instead. -->

```
┌─────────────────────────────────────────┐
│  R1: {Name} ({fixed-top|sticky|static}) │
├──────────────┬──────────────────────────┤
│ R2: {Name}   │ R3: {Name} (scrollable)  │
│ ({position}) │                          │
└──────────────┴──────────────────────────┘
```

<!-- Required: ASCII box diagram of top-level regions. Label each box with Region ID (R1, R2, …) matching the Layout Regions table immediately below. Use dashed lines (- - -) for conditionally visible regions. Nested boxes for modals/drawers that float above main layout. Proportions approximate — not pixel-perfect. -->

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components |
|-----------|------|----------|------------|----------------|
| R1 | {e.g., Top Nav} | {fixed-top \| sticky \| static} | {yes \| no} | {component names from imports} |
| R2 | {e.g., Main Content} | {static} | {yes \| no} | {component names} |

<!-- Required: ≥2 rows (at minimum: top container + content area). Even fullscreen/modal screens have an outer wrapper + content region. -->
<!-- For SSR/template-rendered screens, Key Components may be CSS class names or template partial names. -->
<!-- Source citation: layout root file:line already cited in `### Layout Sketch` above; per-region citations optional unless region maps to a non-obvious file. -->
<!-- Responsive Behavior is NOT a column here (DRY) — a region's breakpoint-dependent behavior is a `## 10. Responsive Behavior` row instead, with `Region / Element` naming this Region ID. -->

## 3. UI Elements

<!-- Single element inventory — absorbs the retired `## Data Inventory`. Every rendered element
     (read-only display, editable input, button, link) gets one row. Type vocabulary: text input,
     password input, textarea, select, checkbox, radio, file input, date input, button, link,
     message, display field, image, list, table, region label. -->

| ID | Element | Type | Required | Default | Visibility | Action | Source | Format | Empty Behavior | Cross-ref |
|----|---------|------|----------|---------|------------|--------|--------|--------|-----------------|-----------|
| E01 | Email | text input | yes | Empty | Always | — | — | raw | dash | binding: `form.email` |
| E02 | Password | password input | yes | Empty | Always | — | — | raw | dash | binding: `form.password` |
| E03 | Sign In | button | — | Enabled | Always | Submits login form (requires E01, E02) | — | — | — | N/A |

<!-- `ID`: E01, E02, … zero-padded to 2, unique within the screen, stable across regenerations. -->
<!-- `Element`: the visible label the user reads — NEVER the variable/binding name. -->
<!-- `Required`: yes | no | — (non-input element). -->
<!-- `Visibility`: Always | Conditional — every `Conditional` row MUST have a matching `## 7. Conditional UI` row. -->
<!-- `Action`: one-phrase user-visible effect, or —. Any real Action MUST have a matching `## 4. § Available Actions` row. -->
<!-- `Source` (provenance of a *displayed* value): API field | route param | store state | computed | static | —. -->
<!-- `Format`: date format / currency / truncation / raw / —. -->
<!-- `Empty Behavior`: dash | placeholder text | hidden | —. -->
<!-- `Cross-ref`: MODEL###.field, or `binding: {name}` when the binding name is worth keeping, or N/A. -->
<!-- Cap: 25 primary rows. Repetitive groups collapse to one row + a note (e.g. `{field_1..N}`). -->

{`N/A — screen displays no dynamic data and has no interactive elements (static marketing/error page)`} *(use only after confirming source has no bindings/interpolations and no interactive controls)*

## 4. User Actions

> **Scope:** within-screen interactions only. Cross-screen navigation belongs in `## 8. Navigation` (which projects `screen-flow.md § Screen Access Paths` — see the D3 note below). Reference region names from `### Layout Regions` (§2, above) when describing where actions occur.

### Available Actions

| Action | Element | Trigger | Condition | Result on this screen | Source |
|--------|---------|---------|-----------|------------------------|--------|
| {action name} | E{##} | {gesture} | {condition, or —} | {within-screen outcome only} | `{file}:{line}` |

<!-- `Element` is an E## reference (D2 — no re-listing of field names). `Result on this screen` is
     within-screen only; anything that leaves the screen belongs in `## 8. Navigation`. -->

{`N/A — no elements carry a discrete user-triggered action.`}

### Happy Path

1. {Numbered step — user action observable on this screen, referencing region if relevant (e.g., "User clicks Submit in R2 Main Content")}
2. {Next step — system response visible on this screen}
3. {... continue until terminal state or hand-off to another screen}

### Branches

| Decision point | Condition | Outcome on this screen | Source |
|----------------|-----------|------------------------|--------|
| {step number/label} | {condition checked} | {visible outcome — alt UI state, inline error, secondary CTA} | `{file}:{line}` |

{`N/A — single-action screen, no branches`} *(use when screen has 1 primary CTA and no conditional sub-flows)*

<!-- Format note: numbered prose for happy path; table for branches. No Mermaid — per-feature flows live in screen-flow.md. -->
<!-- [WARN_ADVISORY]: if screen-flow.md is already in context, spot-check that terminal steps here align with navigation events there. Not a required cross-ref load. -->

### Interaction Notes

<!-- Format: "**{User behavior — observable outcome}** — source: {file:line}" -->
<!-- BAD: "Root div has @click='resetTarget' which calls store.dispatch..." -->
<!-- GOOD: "Clicking outside any group deselects it — source: questions.vue:2" -->

- **{User behavior — observable outcome}** — source: `{file}:{line}`

{`N/A — no non-trivial interaction patterns detected (only standard form input bindings).`}

## 5. UI States

> **Required rows:** loading + ≥1 error (per async call) + ≥1 empty (per data-displaying region) + saving/submitting + success/redirect. Write `N/A — no async ops` only if screen has zero API calls.

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| loading | API in-flight | skeleton/spinner | none | `{file}:{line}` |
| empty | 0 results | empty-state illustration + CTA | {CTA label} | `{file}:{line}` |
| error | API error / network | error message + retry | retry | `{file}:{line}` |
| saving | mutation in-flight | button spinner / disabled form | none | `{file}:{line}` |
| success | mutation complete | toast / inline confirmation | dismiss | `{file}:{line}` |
| {custom} | {trigger} | {behavior} | {action} | `{file}:{line}` |

## 6. Validation & Feedback

<!-- Merges the retired Validation & Error Feedback §A/§B for the reader-facing rule + message
     text. Endpoint, HTTP status, async-check URL, and request/response shape live in
     `## Implementation Mapping` (appendix), not here. -->

| Element | Rule | Feedback | Trigger |
|---------|------|----------|---------|
| E{##} | {plain-language rule, e.g. "Required", "Must be a valid email", "Must match Password"} | {user-visible message text} | {blur \| change \| submit \| server response} |

<!-- `Element` is an E## reference (D2). `Rule` is plain language, never a regex/expression.
     `Feedback` is the exact user-visible message text. `Trigger` is one of blur/change/submit/server response. -->

{`N/A — no validation rules or submit-side error feedback detected.`}

## 7. Conditional UI

| Condition | Type | Element(s) | Visible when | Hidden when | Notes |
|-----------|------|------------|--------------|-------------|-------|
| {user-visible condition, stated as behavior — never as an expression} | {auth\|feature-flag\|configuration\|responsive\|legacy\|hardcoded-id} | E{##}[, E{##}] | {condition} | {condition} | {consequence of bypass for auth; [NEEDS_DOMAIN_CONFIRMATION] for hardcoded-id/legacy} |

<!-- `Condition` is stated user-visible-first, e.g. "Facebook login is offered when the community
     has Facebook login enabled" — never "FeatureFlagHelper.feature_enabled?(...)". The
     implementing expression goes to `## Implementation Mapping` instead. `Element(s)` are E## refs. -->

{`N/A — no conditional UI detected.`}

## 8. Navigation

> **D3 — the DRY statement that MUST appear verbatim in the template and the contract:**
>
> `## 8. Navigation` is the **per-screen projection** of `screen-flow.md § Screen Access Paths`.
> It is not a second source of truth. Every row here MUST be derivable from a path in
> `screen-flow.md`; every path in `screen-flow.md` touching this SCR### MUST appear here.
> Two-way consistency is a reviewer rule (`screen.nav_flow_skew`), not a Python check.
> `## 4. User Actions § Happy Path` narrative keeps its v27 scope rule unchanged: **prose still
> must not narrate cross-screen navigation**; only the § Exits *table* may name destinations.

### Entry Points

| From | Trigger there | Condition | Source |
|------|----------------|-----------|--------|
| {SCR###_Name \| external} | {gesture/event on the origin screen} | {condition, or —} | `{file}:{line}` |

{`N/A — this screen has no other entry points beyond the ones enumerated in screen-flow.md.`}

### Exits

| Action | Element | Condition | Destination | Result | Source |
|--------|---------|-----------|-------------|--------|--------|
| {action name} | E{##} | {condition, or —} | {SCR###_Name \| external URL \| (stays on screen)} | {redirect \| new tab \| modal \| toast then redirect} | `{file}:{line}` |

{`N/A — this screen has no exits (terminal screen).`}

## 9. Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | {present\|absent\|partial} | {aria-label, role=, aria-labelledby usage} |
| Keyboard navigation | {supported\|not implemented\|unknown} | {tab order, shortcut keys} |
| Focus management | {managed\|unmanaged} | {modal/drawer focus trap, autofocus} |
| Screen reader compatibility | {unknown\|tested} | {label linkage, semantic landmarks} |
| Error announcement | {supported\|not implemented\|unknown} | {aria-live region, role="alert" usage for validation/error messages} |

<!-- All 5 Aspect rows are required — this table has no section-level N/A. A row describing
     something NOT in the code is `[EXPECTED]` in Status, never written as current behavior. -->

{When all status cells are absent/unmanaged/unknown: `[NO_A11Y_DETECTED] — accessibility audit needed before production release.`}

## 10. Responsive Behavior

| Breakpoint | Region / Element | Behavior | Source |
|------------|-------------------|----------|--------|
| {desktop\|tablet\|mobile\|literal media query} | {R## or E##} | {visibility/layout change at this breakpoint} | `{file}:{line}` |

<!-- Only evidence-backed rows. This is where a region's breakpoint-dependent behavior lands —
     the `## 2. § Layout Regions` table no longer carries a Responsive Behavior column (DRY). -->

{`N/A — no responsive behavior found in source.`}

## Technical Appendix

> Implementation detail below — controller/class names, framework specifics, helper methods,
> JavaScript wiring, API implementation, session state, security implementation, source
> citations and code-reading order. PO/BA/QA/Designer readers can stop at § 10.

## Implementation Mapping

<!-- NEW appendix section. Absorbs everything demoted out of §§1-10: submit-action
     endpoint/request/response detail, conditional-UI implementing expressions, JS wiring, etc. -->

| Refers to | Kind | Implementation | Source |
|-----------|------|-----------------|--------|
| E{##} \| § {N}. \| R{#} | {endpoint\|handler\|helper\|feature-flag\|session\|js\|guard\|component} | {METHOD /path, function/class name, or expression} | `{file}:{line}` |

<!-- `Refers to` is an E## / `## N.` section / region R# back into the reader body. One block
     per submit-style action's endpoint detail (method, request fields, success/error codes)
     may be recorded here as consecutive rows rather than free prose. -->

{`N/A — no implementation-level detail beyond what is already cited inline above.`}

## Component Variants

<!-- Omit this section if no shared polymorphic component renders on this screen. -->

| Component | Discriminating field | Variants on this screen | Screen-specific props/slots | Cross-ref |
|-----------|---------------------|------------------------|----------------------------|-----------|
| {ComponentName} | {prop/field} | {variant-a, variant-b} | {props this screen passes} | DISC-### |

<!-- Cross-ref: prefer DISC-### from data-model.md when available. DO NOT restate variant business rules — reference only. -->

<!-- ## Child Routes: EMIT ONLY FOR H6 SHELL SCREENS
     Trigger: screen tagged [H6] in screen-list.md
     Source: read route config to enumerate child routes -->

## Child Routes

| Route | SCR | URL | Notes |
|-------|-----|-----|-------|
| {label in nav} | SCR###a | {/path/a} | {one-line child purpose} |
| {label in nav} | SCR###b | {/path/b} | {one-line child purpose} |

<!-- Route config source: {file}:{line} -->

## Security Surface

| Guard | Type | Consequence if bypassed |
|-------|------|------------------------|
| {expression / route guard / middleware name} | {auth\|permission\|role} | {redirect / 403 from API / data exposure} |

{`N/A — no auth guards or permission checks detected on this screen.`}

<!-- When not triggered (no auth-type CR rows, no route guards found): use the N/A string above. When triggered: replace the placeholder row with real guard entries. -->
<!-- For each guard, note server enforcement: "[UNVERIFIED] server enforcement — static analysis cannot confirm API middleware" when unknown. -->

## Source References

<!-- v26.0.0 (A3, F15 DRY): numbered = the reading-order recast (1 = read first). This list IS the `## Source Walkthrough` section's related-files table below — do NOT author a second, independent file list. -->

1. Page/View: `{file}:{line}`
2. Form schema / validation: `{file}:{line}`
3. State management: `{file}:{line}`

{List every file read to produce this spec, in recommended reading order. Minimum 1 entry (the
page/view file). DO NOT fabricate paths.}

<!-- HARD CONSTRAINT: `## Source Walkthrough` below MUST stay a literal, unnumbered H2 —
     `validate_reading_guide_db_impact.py::_section_body` matches `_spec_constants.A3_HEADING`
     ("## Source Walkthrough") as an anchored literal H2. Demoting it to `###` under
     `## Technical Appendix` makes it read as ABSENT and fires `reading_guide.pre_migration` on
     every screen spec. Do NOT nest it, do NOT number it, do NOT rename it. (`## DB Impact per
     Event` used to carry this same constraint in technical-spec.md; both it and A3's
     technical-spec.md side retired in v27.8.0 — this screen-spec heading is the only survivor.) -->

## Source Walkthrough

<!-- v26.0.0 (A3, renamed from "Code Reading Guide" per F15). NEW REQUIRED section, gated by
scripts/validate_reading_guide_db_impact.py (dedicated validator, WARN-first `*.pre_migration`
degradation contract — screen-spec has no other Python structural validator today). -->

{Ordered reading list (data model → entry point → view → logic) covering the files above, 1 file
per step, with a 1-sentence "why start here." Cite each file with the `**File:**` label (NOT
`**Source:**` — keeps this navigational list out of the A1 confidence-report citation-coverage
stat; see `references/confidence-report-contract.md` § A3 navigational entries). Cross-reference
`entities.md` MODEL### for the data layer — this screen has no server-side data layer of its own.}

1. **File:** `{path/to/page-view-file.ext:start-end}` — {why start here: the page/view component itself}
2. **File:** `{path/to/component-file.ext:start-end}` — {next: a key imported component}

### Call Hierarchy

{ASCII or Mermaid diagram of the render/interaction chain — page/view → component(s) → store/hook.}

```text
{Page/View} -> {Component} -> {Store/Hook}
```

**Related files:** see `## Source References` above (already numbered in reading order — F15
DRY, one list not two).

### Data Flow

<!-- v26.2.0 (A3 companion). BEST-EFFORT, same discretion as Call Hierarchy — no dedicated
enforcement beyond the whole-section check `validate_reading_guide_db_impact.py` already runs.
Call Hierarchy = who calls whom; Data Flow = what data moves and how it's transformed. Every
arrow implying a call MUST be source-cited (reuse the matching `## Source References` entry) or
marked "derived from Call Hierarchy above" when it just restates an already-cited hop — never
fabricate a hop. -->

{ASCII or Mermaid diagram of the render/interaction data flow — user interaction/props →
component state update → store/hook → re-render. Prefer ASCII for a short chain; use a Mermaid
`flowchart` or `sequenceDiagram` block for ≥5 hops.}

```text
{User interaction/props} -> {Component state update} -> {Store/Hook} -> {Re-render}
```
