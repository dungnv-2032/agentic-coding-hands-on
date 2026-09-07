<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows|screens paths -- all references here are output targets or internal definitions -->
# Verification Checklist: ScreenSpec (SS.2)
See verification-checklist-universal.md for Universal rules and Pending Marker Rule.

### ScreenSpec

**Applies when:** `--screen-specs` standalone pass. ScreenSpec files at `docs/screens/SCR###_Name/spec.md`.

**Required sections (v27 SOT reshape — 10 numbered BA/PO/QA/Designer sections, then a real `## Technical Appendix` divider, then 6 appendix H2 siblings — target-shape-spec.md § 1 is normative):** `# {SCR###_Name} — Screen Spec` header → `## 1. Overview` → `## 2. Screen Layout` (`### Layout Sketch`, `### Layout Regions`) → `## 3. UI Elements` → `## 4. User Actions` (`### Available Actions`, `### Happy Path`, `### Branches`, `### Interaction Notes`) → `## 5. UI States` → `## 6. Validation & Feedback` → `## 7. Conditional UI` → `## 8. Navigation` (`### Entry Points`, `### Exits`) → `## 9. Accessibility` → `## 10. Responsive Behavior` — then the **Technical Appendix**: `## Technical Appendix` (a divider H2, not a wrapper — everything after it is an H2 sibling, never nested under it) → `## Implementation Mapping` → `## Component Variants` (optional; when omitted, `## Child Routes` — or, when that's also absent, `## Security Surface` — follows directly) → `## Child Routes` (H6 shell only) → `## Security Surface` → `## Source References` → `## Source Walkthrough` (v26.0.0, MUST stay a literal, unnumbered H2 — see the A6 rules below; `validate_reading_guide_db_impact.py::_section_body` matches it as an anchored literal H2 string. B4 `## DB Impact per Event` used to share this same constraint in technical-spec.md; retired from that file in v27.8.0 — this A3 heading is now the ONLY section this validator walks).

**v27 SOT reshape (BA/PO/QA/Designer audience split, screen tier — content-preservation-map.md § A is the authoritative move-by-move ledger):** the section list above replaces the v27.0.0 shape wholesale. Every rule below has been re-pointed at its new home; **none of the accumulated severities from prior gap-fix rounds were reset by this move — this is a re-homing, not a re-review.** Named collapses and retirements, by old section:

- `## Purpose` → `## 1. Overview` `**Purpose:**` field. Both the "absent" and "content is technical" checks carry over unchanged (still `warning`).
- `## Data Inventory` **retires** as a section name. Its rows now live in `## 3. UI Elements` (D2 merge — every rendered element, display or interactive, in one inventory). The old "`## Data Inventory` section absent" rule (`critical`, Gap-fix Round 3) is **retired**; its severity is inherited whole by the new `screen.ui_elements_missing` rule below — critical in, critical out. The old "`## Data Inventory` row missing Cross-ref" rule (`warning`, Round 3) re-points to "`## 3. UI Elements` row with `Source: API field` missing Cross-ref" — same predicate, new home, same severity.
- `## User Flow` **retires** as a section name; its two children move under `## 4. User Actions` as `### Happy Path` and `### Branches` (heading text unchanged — content-preservation-map.md S-10/S-11). All 4 Gap-fix Round 3 `## User Flow` rules ("section absent" `critical`; "0-steps + empty branches", "cross-screen-nav", "written as Mermaid" — all `warning`) re-point to `## 4. § Happy Path` / `§ Branches` with their original severities intact.
- `## Validation & Error Feedback` **retires** as a section name; the reader-facing rule + user-visible message text merge into `## 6. Validation & Feedback` (the name drops "Error" deliberately — it now covers acceptance feedback too, not only errors). The old § A) Client-side rules re-point to `## 6.` directly, unchanged severity. The old § B) Server-side rule "`## Validation & Error Feedback` missing §B block" (`critical`, Gap-fix Round 1) is **retired**; its intent — every submit-style action's implementation detail must be recorded somewhere — is carried forward by the new `screen.impl_mapping_missing_action` rule below, same `critical` severity.
- `## Interaction Patterns` **retires** as a section name; its content moves to `## 4. § Interaction Notes` (content-preservation-map.md S-14, a straight re-parent — the bullets themselves are unchanged, they were already written user-visible-first). The "implementation-first format" rule (`critical`, Gap-fix Round 1) re-points to `## 4. § Interaction Notes` unchanged — same predicate, same severity.
- `## Conditional Rendering` **retires** as a section name in favor of `## 7. Conditional UI` (content-preservation-map.md S-15). Both Gap-fix Round 2 rules ("`auth`-type row has no Notes", "hardcoded-literal untagged", both `warning`) re-point to `## 7.` unchanged.
- `## Accessibility` moves from the dev appendix into the reader body as `## 9. Accessibility` (content-preservation-map.md S-17) and gains a 5th required row (`Error announcement`, v27 SOT template). The "bare N/A instead of audit table" rule (`warning`, Gap-fix Round 1B) re-points to `## 9.` and now checks for **5** rows, not 4.
- `screen.layout_regions_missing` (v27.0.0 merge, `critical`) **changes lookup location**: under v27.0.0 it looked in the dev appendix; it now looks in the **reader body**, under `## 2. Screen Layout` — `### Layout Regions` moves back into the reader body in the SOT reshape (content-preservation-map.md S-04, the reverse of the v27.0.0 move that had sent it the other way). `screen.layout_sketch_missing` is unaffected in predicate — `### Layout Sketch` was already in the reader body and stays there, now nested under a real `## 2. Screen Layout` parent instead of floating as an orphan H3.
- `### Layout Regions` column `Responsive Behavior` **retires** (content-preservation-map.md S-05, DRY) — each non-empty cell becomes a `## 10. Responsive Behavior` row instead, `Region / Element` naming the Region ID. See `screen.responsive_unevidenced` below.

Where this list does not name a rule, its section name and severity are unchanged from the prior round tables (e.g. the SCR### header check, the business-logic scope check, the `## Source References` rules, `## Component Variants`, `## Security Surface`, and the A6 Source Walkthrough rules).

**Severity policy** (grouped by the release round each rule was added in — position in the table below now follows document order (v27 SOT reshape), not release-round order, so rounds are named here rather than pointed at by row range):

- **Initial release** — `warning`, promotes to `critical` at stable: SCR### header code check, all-sections-N/A check, business-logic/FR-BR-SM-ALG-INT-SC scope check, `## Source References` missing/empty, required-section-absent, lazy-N/A, server-side-only-validation-documented (re-homed to `## 6.`), twin create/edit divergence (W7i, updated for the merged `## 6.`).
- **Gap-fix Round 1** — `critical` immediately: `## UI States` missing error row, `## UI States` missing empty row (both now `## 5. UI States`), legacy `## Form Validation Rules` heading, `## Interaction Patterns` implementation-first (re-homed to `## 4. § Interaction Notes`). `## Validation & Error Feedback` missing §B block is **retired** — see the v27 SOT reshape paragraph above (`screen.impl_mapping_missing_action` carries its severity forward). (The Round 1 Screen-Layout rules are superseded by the v27.0.0 merge below, and their lookup location moves again under the v27 SOT reshape.)
- **Gap-fix Round 1B** — `warning` during initial release: `## Accessibility` bare N/A (re-homed to `## 9.`, now a 5-row check), `## Component Variants` appears unnecessarily, `## Component Variants` restates DEC/DISC, `[UNVERIFIED]` without description.
- **Gap-fix Round 2** — `warning` immediately, promotes to `critical` at stable: `## Purpose` absent, `## Purpose` technical (both re-homed to `## 1. Overview`), Conditional Rendering auth-row no Notes, Conditional Rendering hardcoded-literal untagged (both re-homed to `## 7. Conditional UI`), `## Security Surface` absent with auth-row (auth-row now read from `## 7.`), Source References `(not read)` entry with no Unresolved Question.
- **Gap-fix Round 3** (audience expansion: Designer/PM + FE dev + QA) — `## User Flow` absent and `## Data Inventory` absent were `critical` immediately; the former re-points to `## 4. User Actions` (still critical), the latter is **retired**, its severity inherited by `screen.ui_elements_missing`. `## User Flow` 0-steps+empty-branches, cross-screen-nav, as-Mermaid, and `## Data Inventory` row missing Cross-ref were `warning` immediately promoting to `critical` at stable — all re-home with severity intact (`## 4. § Happy Path`/`§ Branches` and `## 3. UI Elements` respectively). (The Round 3 Screen-Layout rules are superseded by the v27.0.0 merge below, except `### Layout Regions` < 2 rows, which is unaffected in severity and moves again under the v27 SOT reshape.)
- **v27.0.0 layout re-homing** (BA/QA audience split — screen tier reorder; a **merge**, not a deletion): old rules "`Screen Layout` section absent" (`critical`, Round 1) and "`### Layout Sketch` ASCII box diagram absent under `Screen Layout`" (`warning`, Round 3) collapsed into **`screen.layout_sketch_missing`** — critical, inheriting the Round 1 rule's severity. Old rules "`Screen Layout` is bare N/A" (`critical`, Round 1) and "`### Layout Regions` sub-table absent under `Screen Layout`" (`warning`, Round 3) collapsed into **`screen.layout_regions_missing`** — critical. "`### Layout Regions` has fewer than 2 rows" was **not** part of this merge — same rule, same `warning` severity, only its section moved.
- **v27 SOT reshape** (BA/PO/QA/Designer audience split, target-shape-spec.md § 1) — see the collapse/retirement paragraph above for the full list. New rule_ids introduced in this round, none inheriting a prior severity because the surface itself is new: `screen.ui_elements_missing` (critical — but see above, it DOES inherit `## Data Inventory` absent's severity), `screen.element_id_dangling` (critical), `screen.element_id_unreferenced_conditional` (warning), `screen.impl_mapping_missing_action` (critical — inherits the retired §B-block rule's severity), `screen.nav_flow_skew` (warning, `[WARN_ADVISORY]`), `screen.nav_invented_destination` (critical), `screen.responsive_unevidenced` (warning), `screen.expected_without_basis` (warning), `screen.appendix_leak` (warning).

**Degradation contract — `screen.sot_pre_sot` (WARN-first, v27 SOT reshape):**

**Detection predicate:** the spec still matches the v27.0.0 shape — `### Layout Sketch` is present in the file with no `## 2. Screen Layout` parent heading above it (equivalently: the literal substring `## Screen Layout` is present somewhere in the document — the new `## 2. Screen Layout` heading does NOT contain that substring, because `2. ` sits between `## ` and `Screen`; this is the same substring-safety property `_audience_split_mode_c_lib.py`'s re-entry guard relies on, documented in target-shape-spec.md § 1.3). A spec with neither `### Layout Sketch` nor `## Screen Layout` present at all is not a v27.0.0-shaped document either (it fails the required-sections chain outright, which is a separate, still-active check).

**Muting behavior:** when `screen.sot_pre_sot` fires, the reviewer suppresses every other rule in the main severity table above, the "New rule specifications" block below, and the H6 Shell rules block — every rule that is defined in terms of the numbered §1–10 + appendix shape. A pre-migration spec must produce exactly one finding for its shape, not thirty. It does **not** mute the A6 Source Walkthrough (`reading_guide.*`) rules, the W7c–W7i cross-artifact rules, or the Composite Detection / Failure Trap rules below — those check axes that are independent of section ordering (Source Walkthrough content, other artifacts' sections, ScreenList composite detection) and are unaffected by whether this file has been reordered yet.

**Severity:** `warning` — the degradation window. This mirrors the existing `reading_guide.pre_migration` precedent (v26.0.0) but at document-wide granularity rather than one section's, because the entire section list changed here, not one section. **Promotion of `screen.sot_pre_sot` to `critical` is a follow-up, not this phase** — run `migrate_feature_audience_split.py` Mode C (`references/migration-audience-split.md`) to clear it.

| Rule | Severity |
|------|----------|
| SCR### code in header does not exist in ScreenList | warning |
| All sections are N/A (no content populated at all) | warning (flag for re-examination) |
| Business logic or FR/BR/SM/ALG/INT/SC codes present | warning (scope violation — promoted to critical after stable release) |
| `screen.sot_pre_sot` — the spec still matches the v27.0.0 shape (see Degradation contract above); mutes every other row in this table | warning |
| `## 1. Overview` `**Purpose:**` absent | warning |
| `## 1. Overview` `**Purpose:**` content is technical (references component names, store names, or code internals) | warning |
| `screen.layout_sketch_missing` — `### Layout Sketch` is absent from, or bare `N/A` in, `## 2. Screen Layout` (v27.0.0 merge; unaffected by the v27 SOT reshape beyond its new parent heading) | critical |
| `screen.layout_regions_missing` — `### Layout Regions` is absent from, or bare `N/A` in, `## 2. Screen Layout` (v27.0.0 merge; v27 SOT reshape moves the lookup from the dev appendix into the reader body) | critical |
| `### Layout Regions` has fewer than 2 rows | warning |
| `screen.ui_elements_missing` — `## 3. UI Elements` is absent, or present with 0 rows, while the screen renders anything (display or interactive) — retires "`## Data Inventory` section absent", same severity | critical |
| `## 3. UI Elements` row missing `Cross-ref` when `Source` is `API field` and the field name matches an entity attribute in data-model.md (copy-instead-of-reference smell; re-homed from `## Data Inventory` row missing Cross-ref) | warning |
| `## 3. UI Elements` `ID` column has a duplicate, non-sequential, or non-zero-padded `E##` value | warning |
| `## 3. UI Elements` row's `Action` column is non-`—` but has no matching `## 4. § Available Actions` row | warning |
| `screen.element_id_dangling` — an `E##` cited in `## 4. § Available Actions`, `## 6. Validation & Feedback`, or `## 7. Conditional UI` has no matching `## 3.` row (mirrors `screen-spec-researcher-contract.md` § Referential Rules) | critical |
| `screen.element_id_unreferenced_conditional` — a `## 3.` row with `Visibility: Conditional` has no matching `## 7. Conditional UI` row | warning |
| `## 4. User Actions` section absent (re-homed from "`## User Flow` section absent") | critical |
| `### Happy Path` has 0 numbered steps AND `### Branches` table absent/empty (no content at all) (re-homed from `## User Flow`) | warning |
| `### Happy Path` documents cross-screen navigation (router.push to other SCR###) instead of within-screen interactions (re-homed from `## User Flow`) | warning |
| `### Happy Path` written as Mermaid diagram instead of numbered prose + `### Branches` table (re-homed from `## User Flow`) | warning |
| `### Interaction Notes` entry uses implementation-first format (re-homed from `## Interaction Patterns`, unchanged predicate) | critical |
| `## 5. UI States` lacks ≥1 error row when screen has async calls | critical |
| `## 5. UI States` lacks ≥1 empty row when screen renders data lists/blocks | critical |
| Legacy section name `## Form Validation Rules` present | critical |
| `screen.impl_mapping_missing_action` — a submit-style action (a `## 4. § Available Actions` row, or a `## 3.` element with a real `Action`) has no matching `## Implementation Mapping` row — retires "`## Validation & Error Feedback` missing §B block", same severity | critical |
| Validation rules documented that are server-side only (no client-side enforcement found in code) (re-homed to `## 6. Validation & Feedback`) | warning |
| Twin create/edit screens (same `**Feature**` backlink, create/edit name pair) diverge on `## 6. Validation & Feedback` validated field coverage with no stated reason (see W7i, updated for the merged section) | warning |
| `## 7. Conditional UI` `auth`-type row has no Notes entry stating consequence of bypass (re-homed from Conditional Rendering) | warning |
| `## 7. Conditional UI` row with hardcoded numeric/string literal lacks `[NEEDS_DOMAIN_CONFIRMATION]` in Notes (re-homed from Conditional Rendering) | warning |
| `## 7. Conditional UI` row's `Condition` column is written as a raw expression (e.g. `FeatureFlagHelper.feature_enabled?(...)`) instead of user-visible behavior first (target-shape-spec.md § 1.4) | warning |
| `screen.nav_flow_skew` — a `## 8. § Exits` destination absent from `screen-flow.md § Screen Access Paths`, or a path in `screen-flow.md` touching this SCR### absent from `## 8. § Exits` — `[WARN_ADVISORY]`, spot-check only when `screen-flow.md` is already loaded in context | warning |
| `screen.nav_invented_destination` — a `## 8. § Exits` row names a `Destination` with no `Source` citation | critical |
| `## 9. Accessibility` uses bare `N/A` instead of the 5-row audit table (re-homed from the dev appendix; now checks 5 rows, not 4) | warning |
| `screen.responsive_unevidenced` — a `## 10. Responsive Behavior` row has no `Source` citation and is not the section's own `N/A` line | warning |
| `[UNVERIFIED]` marker used without best-effort description | warning |
| `screen.expected_without_basis` — see "New rule specifications" below | warning |
| `screen.appendix_leak` — see "New rule specifications" below | warning |
| `## Component Variants` (Appendix A2) appears for screen with no shared polymorphic components | warning |
| `## Component Variants` (Appendix A2) restates DEC/DISC business rules instead of cross-referencing | warning |
| `## Security Surface` (Appendix A4) absent when `## 7. Conditional UI` has ≥1 `auth`-type row OR router config guard confirmed for this screen's route | warning |
| `## Source References` (Appendix A5) missing or empty | warning |
| `(not read — referenced by import)` entry in `## Source References` (Appendix A5) with no corresponding Unresolved Question | warning |
| Required section absent | warning |
| N/A written without source file scan evidence (lazy N/A) | warning |

**H6 Shell rules (`warning` immediately — `## Child Routes` is Appendix A3, an H2 sibling after `## Component Variants` (A2) and before `## Security Surface` (A4)):**

| Rule | Severity |
|------|----------|
| `## Child Routes` section absent on H6 shell screen (screen tagged `[H6]` in screen-list.md or outlet pattern detected) | warning |
| `## Child Routes` table has 0 data rows on H6 shell screen | warning |
| `## 5. UI States` on H6 shell screen documents child-screen states (forms, data tables, or API calls belonging to child SCR) instead of shell-level only | warning |

**A6 Source Walkthrough rules (v26.0.0 — `reading_guide.*` rule_ids from `validate_reading_guide_db_impact.py`; the last H2 sibling in the Technical Appendix — unaffected by the v27 SOT reshape, see the Degradation contract above for why this axis is not muted by `screen.sot_pre_sot`):**

| Rule | Severity |
|------|----------|
| `## Source Walkthrough` entirely absent | warning (`reading_guide.pre_migration` — un-migrated doc, non-blocking) |
| `## Source Walkthrough` present but body empty | critical (`reading_guide.malformed`) |
| `## Source Walkthrough` present but only the unfilled `{...}` template placeholder | warning (`reading_guide.unmapped`) |

#### New rule specifications (v27 SOT reshape)

The rules below are new or materially reworked by the SOT reshape and need more than a
one-line predicate to apply consistently — same Check/Pass/Fail-evidence/N/A shape as the W7
series below, so a reviewer can apply them without guessing.

##### `screen.ui_elements_missing`

**Check:** `## 3. UI Elements` is present with ≥1 row, OR the section's own N/A string is used and justified.
**Pass:** ≥1 row present when the screen renders any display or interactive element; OR `N/A — screen displays no dynamic data and has no interactive elements (static marketing/error page)` with source-scan confirmation (zero bindings/interpolations, zero interactive controls).
**Fail evidence:** section absent entirely, present with 0 rows and no N/A string, or N/A string used while the page/view file contains a binding, interpolation, or interactive control.
**N/A:** never — the section itself is mandatory; a screen with nothing to inventory still states the N/A string above.

##### `screen.element_id_dangling`

**Check:** every `E##` cited in `## 4. § Available Actions`, `## 6. Validation & Feedback`, or `## 7. Conditional UI` resolves to a row in `## 3. UI Elements`.
**Pass:** all cited `E##` values exist in `## 3.`.
**Fail evidence:** an `E##` cited in any of the three sections above with no matching `## 3.` row.
**N/A:** the citing section itself is N/A (nothing to check).

##### `screen.element_id_unreferenced_conditional`

**Check:** every `## 3.` row with `Visibility: Conditional` has a matching `## 7. Conditional UI` row naming its `E##`.
**Pass:** each `Conditional` row's `E##` appears in a `## 7.` row's `Element(s)` column.
**Fail evidence:** a `## 3.` row with `Visibility: Conditional` and no `## 7.` row covering it.
**N/A:** `## 3.` has zero `Conditional` rows.

##### `screen.impl_mapping_missing_action`

**Check:** every submit-style action — a `## 4. § Available Actions` row, or a `## 3.` element whose `Action` column is non-`—` and describes a real (not purely local) effect — has a corresponding `## Implementation Mapping` row recording its endpoint/handler.
**Pass:** each such action's `E##` or action name appears in `Refers to` in `## Implementation Mapping`.
**Fail evidence:** a submit-style action with no matching `## Implementation Mapping` row at all (this is the retired `## Validation & Error Feedback` §B check, carried forward — a submit action must have ITS implementation detail recorded somewhere, not necessarily under the old heading).
**N/A:** `## Implementation Mapping`'s own N/A string is valid only when `## 4.` has zero submit-style actions and no `## 3.` row carries a real `Action`.

##### `screen.nav_flow_skew`

**Check:** two-way consistency between `## 8. § Exits` and `screen-flow.md § Screen Access Paths` for this SCR### (D3, target-shape-spec.md § 1.4 — `## 8. Navigation` is a *projection*, not a second source of truth).
**Pass:** every `## 8. § Exits` `Destination` is derivable from a path in `screen-flow.md`; every `screen-flow.md` path touching this SCR### appears as a `## 8. § Exits` row.
**Fail evidence:** a `## 8.` row with no corresponding `screen-flow.md` path, or a `screen-flow.md` path for this SCR### with no `## 8.` row.
**Advisory scope (`[WARN_ADVISORY]`):** only spot-check when `screen-flow.md` is already loaded in the reviewer's context for this pass — do NOT load it solely to run this check, mirroring the existing `## 4. § Happy Path` terminal-step advisory.
**N/A:** `## 8. § Exits` uses its own N/A string (terminal screen) AND `screen-flow.md` has no path touching this SCR### either.

##### `screen.nav_invented_destination`

**Check:** every `## 8. § Exits` row has a `Source` citation.
**Pass:** `Source` is a `file:line` or a named `screen-flow.md` path entry.
**Fail evidence:** a `## 8. § Exits` row with `Destination` filled in but `Source` blank, `—`, or absent — a destination must never be guessed from a button label alone (feedback: "Không tự suy diễn destination"). This is `critical`, not `warning`, because an invented destination is a fabricated fact, not a documentation gap.
**N/A:** `## 8. § Exits` uses its own N/A string.

##### `screen.responsive_unevidenced`

**Check:** every `## 10. Responsive Behavior` row has a `Source` citation.
**Pass:** `Source` is a `file:line`.
**Fail evidence:** a `## 10.` row with `Source` blank or `—`, and the row is not the section's own N/A line.
**N/A:** `N/A — no responsive behavior found in source.` after confirming zero breakpoint-dependent regions/elements (including a scan of `## 2. § Layout Regions`, which no longer carries its own `Responsive Behavior` column — content-preservation-map.md S-05).

##### `screen.expected_without_basis`

This is the reviewer-checkable form of the client's core demand: **an observed current
behavior must never be written as a SHOULD/desired statement** (see the researcher contract's
"Never-Invent Rule" and `references/confidence-report-contract.md` § the `[EXPECTED]`
marker). It checks both directions of that boundary with one rule_id:

**Check (direction 1 — `[EXPECTED]` misuse):** every `[EXPECTED]` marker (most commonly in `## 9. Accessibility` or `## 10. Responsive Behavior`) carries a stated agreement/decision origin — a cited decision, a stakeholder sign-off note, or an explicit "recommended because…" rationale, not a bare tag.
**Fail evidence (direction 1):** `[EXPECTED]` present with no such origin stated in the same cell/row.
**Check (direction 2 — current behavior mis-marked as desired):** a row or sentence describing what the code does today is written as a recommendation or SHOULD-statement instead of a plain (cited, or `[UNVERIFIED]`) factual statement.
**Fail evidence (direction 2):** e.g. an accessibility row phrased as "should add an `aria-live` region" with no `[EXPECTED]` tag and no citation — the reviewer cannot tell whether this is current behavior or a recommendation, which is exactly the ambiguity the marker exists to remove. Reviewer flags this as `screen.expected_without_basis` regardless of which direction the ambiguity runs.
**N/A:** the spec contains no `[EXPECTED]` markers and no should/recommend-phrased sentences describing screen behavior.

##### `screen.appendix_leak`

Also a mild data-exposure guard (see Security Considerations) — internal class and host names
leaking into a BA/PO/QA/Designer-facing document that may be exported to clients.

**Check:** §§1–10 (everything before `## Technical Appendix`) contain no identifier-shaped
implementation token.
**Scope (deliberately narrow — do not flag prose):** an identifier-shaped token is one of:
a CamelCase word ending in a known implementation suffix (`Controller`, `Service`, `Helper`,
`Component`, `Store`, `Handler`, `Middleware`, `Guard`), a `::`-qualified name, a `#method`-style
method reference, or a `snake_case`/`camelCase` token that also appears verbatim as a `Kind:
component|handler|helper|guard` `Implementation` value in `## Implementation Mapping`.
**Pass:** no such token appears in §§1–10; all such detail lives in `## Implementation Mapping`
or another appendix section.
**Fail evidence:** an identifier-shaped token (as scoped above) found inside §§1–10, e.g.
`FeatureFlagHelper.feature_enabled?` written directly in a `## 7.` `Condition` cell instead of
being restated as user-visible behavior with the expression moved to `## Implementation
Mapping`.
**Do not flag:** plain English words even when they resemble technical vocabulary ("endpoint",
"session", "token" used in prose) — the scope test is the identifier SHAPE (suffix/qualifier/
method-reference), not the vocabulary.
**N/A:** never — this is a continuous scan, not a section with a fallback string.

##### `screen.sot_pre_sot`

See the Degradation contract block above the main table — detection predicate, muting scope,
and promotion note are stated there in full and not repeated here.

**Cross-refs:**
- `## Child Routes` (Appendix A3) SCR### codes must exist in ScreenList index; URL patterns must match route config
- SCR### in header MUST exist in ScreenList main index
- Source citations MUST reference real files (reviewer spot-checks 1–2 per spec)
- DataModel `## Discriminator Fields` for `## Component Variants` (Appendix A2) cross-refs; FeatureSpec § Polymorphic Behavior when present.
- `## Security Surface` (Appendix A4) guard types cross-reference `## 7. Conditional UI` `auth`-type rows — must be consistent.
- `## 1. Overview` `**Purpose:**` must not contradict screen's SCR### entry in ScreenList (same user persona / goal).
- `## 3. UI Elements` `Cross-ref` entries pointing to MODEL### must exist in data-model.md; bare entity attribute name without MODEL### prefix is acceptable only when entity is not yet documented (reviewer notes [validator-absent] in report)
- `## 4. § Happy Path` terminal step cross-ref to screen-flow.md is **advisory only** (`[WARN_ADVISORY]`): if screen-flow.md is already in context, spot-check alignment; do NOT load screen-flow.md solely for this check — distinct from `screen.nav_flow_skew` above, which checks the `## 8. § Exits` *table*, not the Happy Path prose
- `### Layout Regions` (`## 2.`, reader body) Key Components column entries must appear in `## Source References` (Appendix A5) file list OR be CSS class names / template partials documented elsewhere
- `[UNVERIFIED]` in `## 4. § Branches` / `## 3. UI Elements` `Format` / `## 10. Responsive Behavior` columns is acceptable when accompanied by best-effort description ("[UNVERIFIED] currency format — needs runtime confirmation"); bare `[UNVERIFIED]` → warning
- The `**Feature**` backlink (header, v24.0.0) is the grouping key for twin create/edit detection (W7i) — reviewer groups sibling screen specs sharing the same `**Feature**` value before applying the create/edit name-pair heuristic
- `## 8. § Exits` `Destination` values must be derivable from a path in `screen-flow.md § Screen Access Paths` for this SCR### (D3, target-shape-spec.md § 1.4) — see `screen.nav_flow_skew` / `screen.nav_invented_destination` above
- The §3 ↔ §4 ↔ §6 ↔ §7 `E##` referential-integrity rules above (`screen.element_id_dangling`, `screen.element_id_unreferenced_conditional`, and the two plain `## 3.` rows for Action/uniqueness) mirror `screen-spec-researcher-contract.md` § "Referential Rules (§3 ↔ §4 ↔ §6 ↔ §7)" — same predicate, reviewer-side enforcement of what the researcher is already required to self-check before closing the spec

**N/A handling for the SOT-reshaped sections (v27 SOT reshape; was "gap-fix Round 3 / v27.0.0 sections"):**

| Section | Valid N/A string | Reviewer action when N/A used |
|---------|------------------|-------------------------------|
| `## 4. § Branches` (was User Flow) | `N/A — single-action screen, no branches` | Verify screen has exactly 1 CTA and no `currentStep`/conditional render in Source References files. If multiple CTAs or branches found → flag warning. |
| `## 2. § Layout Sketch` | None — always required | Always flag if absent. Even a single-box sketch is acceptable for trivial screens. |
| `## 2. § Layout Regions` | None — always required | Always flag if absent. |
| `## 3. UI Elements` (was Data Inventory) | `N/A — screen displays no dynamic data and has no interactive elements (static marketing/error page)` | Verify Source References files contain zero bindings/interpolations AND zero interactive controls. If either is found → flag warning (`screen.ui_elements_missing` if the whole section is absent; this row otherwise). |

Lazy N/A (writing N/A without scanning source) → warning, regardless of section.

#### W7c — SM `kind` field present and valid
**Check:** Every SM-### block has `**kind:**` as the first metadata line.
**Pass:** `kind` value is `entity` or `ui` for all SM blocks.
**Fail evidence:** SM-### block missing `**kind:**` line, OR `kind` value is anything other than `entity`/`ui`.
**N/A:** Feature has no state machines (SM section is empty or absent).

#### W7d — behavior-logic.md Client-Side Logic section populated
**Check:** `behavior-logic.md` contains a `## Client-Side Logic` section.
**Pass:** At least one subsection has content (not all N/A) — OR — all subsections are N/A with confirmation note that codebase has no client-side code.
**Fail evidence:** `## Client-Side Logic` section absent; OR subsection shows N/A but code evidence of the pattern exists (reviewer must cite file:line).
**N/A:** Feature is backend/server-only with no client-side code (reviewer must state this explicitly).

#### W7e — permissions.md captures client-side gates
**Check:** `permissions.md` includes entries for any feature-flag / experiment / env-gate / locale-gate found in code for this feature.
**Pass:** All gates found in code appear in permissions.md — OR — `N/A — no {type} gates detected.` with confirmation.
**Fail evidence:** Gate function call found in code (cite file:line) but not listed in permissions.md.
**N/A:** Reviewer confirms no gate patterns present in feature's code surface.

#### W7f — screen-flow.md has Guard Logic / Deep-Link / Unsaved-Changes sections
**Check:** `screen-flow.md` contains the 3 new sections.
**Pass:** Each section either has entries OR an explicit N/A statement confirmed by code review.
**Fail evidence:** Section absent entirely; OR N/A written without reviewer confirming code absence (lazy N/A).
**N/A:** Not applicable for this feature (e.g., feature has no screens).

#### W7g — Client behavior anchor present in every feature-spec
**Check:** `## Cross-Cutting Logic` in `spec.md` contains the `**Client behavior:**` anchor block.
**Pass:** Anchor block present with all 3 relative links.
**Fail evidence:** Anchor absent, or only 1–2 of the 3 links present.
**N/A:** Never — this anchor is mandatory regardless of N/A content in the linked files.

#### W7h — DEC-### Coverage (Semantic)

**Applies to:** each feature spec (run after `validate_feature_spec.py` passes structural check).

**Pass criteria:**
- `## Cross-Cutting Logic > ### Decision Logic` section present (structural — pre-checked by validator)
- For each DEC-###:
  - `subtype:` declaration matches outcome (e.g. `flow` subtype requires navigation/step in `user_visible_outcome`)
  - `user_visible_outcome` is genuine business outcome (not "spinner shows" / "loading toggle" / dispatch wrapper)
  - Pseudocode matches Source at cited lines (reviewer cross-checks by reading source)
  - No anti-example patterns captured (loading toggle, generic dispatch, debounce/throttle, i18n routing, cache mechanic)
- For N/A: validator already confirmed no JSX-ternary hits in involved files; reviewer scans for non-JSX branches if applicable

**Fail evidence:**
- subtype `flow` declared but pseudocode contains no navigation → mismatch
- `user_visible_outcome` is "spinner appears" → plumbing leakage, fail
- Pseudocode references variables not in cited Source range → hallucination
- Anti-example pattern detected (e.g. `if isLoading → show <Spinner/>`) → fail

**Subtype routing for evidence-check:**
- `render` → reviewer reads component render tree at Source
- `interaction` → reviewer reads event handler body at Source
- `flow` → reviewer reads navigation/step-advance code at Source (can be saga, controller, route, anywhere — Source location agnostic)

**Fail evidence:**
- DEC pseudocode with single predicate (no AND/OR/multi-condition) and subtype `render` → warning: "consider expressing as DISC or Business Rule"

**Cross-link:** When validator catches single-field condition in a DEC, reviewer suggests moving to DISC. See W7a (DISC boolean — data-model.md).

#### W7i — Twin create/edit client-side validation consistency

**Applies when:** two screen specs share the same `**Feature**` backlink (v24 header field) AND their names form a create/edit pair (`create|new|add` ↔ `edit|update` on the same entity noun).

**Check:** their `## 6. Validation & Feedback` field coverage is consistent — compare the *underlying field names* each spec's validated `E##` rows resolve to via that spec's own `## 3. UI Elements` `Element` column (edit may legitimately omit immutable/system fields — that's a signal, not automatically a fail).

**Pass:** field-name sets match, OR the divergence has a stated reason in either spec (e.g. "edit hides `password`").

**Fail evidence:** symmetric difference in validated field names, resolved through each spec's own `E##` → `Element` mapping, with no stated reason → **warning** (not critical).

**N/A:** the feature has no create/edit twin pair.

Reviewer-only (no Python validator exists for this rule — cross-screen semantic field-set comparison is outside `validate_feature_screen_link.py`'s scope, which only checks the `**Feature**` link resolves).


## Composite Detection Rules

Rules fire unconditionally on every pipeline invocation. No opt-in flag.

- [ ] **H4 short-circuit respected (tabs only):** mutually-exclusive tab content (per-stack tab signals in `composite-screen-detection.md § H4`) → SCR variants (SCR###a/b), not REG. Hard rule; overrides all other heuristics for tab-style screens. Reviewer selects signals from the row matching the task's `Detected stack:` value.
- [ ] **H5 wizard/stepper classification:** screens with wizard/stepper signals (per-stack signals in `composite-screen-detection.md § H5`) MUST cite classification evidence in spec. Case A (SCR variants) requires explicit citation of distinct validation rules AND distinct API endpoints AND distinct user action per step. Case A without cited evidence → warning (researcher should re-evaluate as Case B). 2-step wizards defaulting to Case A → critical (must be Case B). ≥3-step wizards default to Case B (composite SCR + step REGs).
- [ ] **H3 region count excludes H4/H5 signals:** tab signals (H4) and wizard/stepper signals (H5) — per per-stack tables in `composite-screen-detection.md § H4` and `§ H5` — MUST NOT count toward H3 (any stack).
- [ ] **H2 module count uses per-stack include/exclude tables:** only domain/feature module imports count toward H2; UI-library and framework-primitive imports are excluded. Reviewer applies the include/exclude row matching the task's `Detected stack:` value — see per-stack tables in `composite-screen-detection.md § H2`.
- [ ] **2-of-3 signal gate applied:** composites cite which 2 signals passed (H1∧H2, H1∧H3, or H2∧H3). Screens not meeting gate → emit bare SCR###.
- [ ] **Raw-div fallback noted when H3=0:** if H3 yields 0, gate uses H1+H2 only. If both H1 and H2 also fail → emit atomic + warning. Known Detection Limitation documented in spec output.
- [ ] **FeatureList composite-ref tokenizer (C3):** FeatureList Related Screens tokenizer splits on `,` then on `/`. Left token = SCR### (must exist in ScreenList main index). Right token (if present) = REG### (must exist in that screen's Regions subsection). Both tokens validated independently. Missing REG### under valid SCR### → critical.
- [ ] **Malformed composite ref (M3):** malformed composite refs (`SCR001REG001` missing `/`, `SCR001/` missing REG, `SCR/REG001` missing digits, `SCR001/REG` missing digits) → critical. Regex: `^SCR\d{3}_\w+(/REG\d{3}_\w+)?$` must match.
- [ ] **W1 no-REG rule (M5):** W1 artifacts (SystemOverview, RouteList, DataModel) MUST NOT contain REG### codes. REG### first appears in W2 ScreenList. Orphan REG### in W1 artifact → critical.
- [ ] **Partial-screen ownership (CE3):** each SCR### must have ≥1 F### owning the screen shell (bare SCR### ref in FeatureList Related Screens); each REG### must have ≥1 F### owning it (SCR###/REG### ref). An F### with only SCR###/REG### refs does NOT own the parent SCR.
- [ ] **SIGNAL_INFERRED cap and justification:** `[SIGNAL_INFERRED]` tag in ScreenList Notes signals researcher used `composite-screen-detection.md § Signal Inference Fallback`. Tag MUST cite an H-rule in H2–H6 (H1 has no signal table — inference invalid for H1). Each occurrence MUST carry a 3-part justification (Intent matched / No-row reason / Observed pattern). Missing any part → critical. Count `[SIGNAL_INFERRED]` occurrences across the entire ScreenList document; threshold = `max(5, ceil(0.10 × SCR_count))` — exceeding triggers warning (over-reliance on inference; per-stack tables likely outdated or stack uncovered).


## Failure Trap Assertions

- **Trap 1 (proliferation):** every REG has ≥1 independence signal, drawn from: distinct API endpoint (read or write), independent loading state, independent scroll container, independent auth / permission gate, distinct business workflow, distinct mutation surface / API cluster (distinct write endpoints or POST/PUT/DELETE namespace — even if the initial GET payload is shared), distinct validation / action path. Missing signal → critical. Visual separation alone is NOT sufficient.
- **Trap 2 (tab/stepper misclassification):** mutually-exclusive tab content declared as REG (not SCR variants) → critical. Wizard/stepper content: Case A emitted without cited distinct-validation + distinct-endpoint evidence → warning (prompt researcher to re-evaluate as Case B). 2-step wizard emitted as Case A → critical.
- **Trap 3 (shared data):** collapse two REG candidates into one Feature ONLY when they share ALL of: read surface (same GET endpoint/store) AND write surface (same mutations) AND business workflow. Shared initial payload alone does NOT disqualify a split — if regions diverge on write endpoints, validation rules, action paths, or business workflow, they remain separate. Researcher self-check advisory (NOT reviewer-enforceable critical — reviewer cannot inspect codebase at review time).
- **Trap 4 (LOC-based over-split):** LOC is NOT a composite signal. H3 uses named wrapper components only. Advisory note: flag any ScreenList entry where the researcher's justification cites line count rather than named wrappers or import count.
- **Trap 5 (spec orphan):** every REG### in ScreenList must have an owner annotation (can be `TBD`) → critical if owner annotation missing entirely.
- **Trap 6 (inferred-signal abuse):** `[SIGNAL_INFERRED]` tag without all 3 justification parts (Intent matched, No-row reason, Observed pattern) → critical. Tag citing H1 (which has no signal table) → critical; H2–H6 only. Tag used to bypass a per-stack row that DOES match the screen's stack/library naming → critical (researcher must use explicit row first). Tag count exceeding `max(5, ceil(0.10 × SCR_count))` across the entire ScreenList document → warning (suggests per-stack tables need updating or stack/library not covered).
