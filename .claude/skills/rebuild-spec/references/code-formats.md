# Code Formats & Valid Requirements

Shared schema for rebuild-spec artifacts. Loaded by researcher and reviewer subagents.

## Code Formats

| Type | Format | Example | Scope |
|------|--------|---------|-------|
| Feature | `F###_NameSlug` | F001_Auth | project |
| User Story | `US###_NameSlug` | US001_Login | project |
| Screen | `SCR###_NameSlug` | SCR001_LoginScreen | project |
| Region | `REG###_NameSlug` | REG001_Header | per-screen |
| Background Logic | `BL###_NameSlug` | BL001_ScheduledReport | project |
| Permission | `PERM###_NameSlug` | PERM001_ViewReports | project |
| Discriminator | `DISC-###` | DISC-001 | project |
| Decision Logic | `DEC-###` | DEC-001 | per-spec |
| Business Rule | `BR-###` | BR-001 | per-spec |
| State Machine | `SM-###` | SM-001 | per-spec |
| Algorithm | `ALG-###` | ALG-001 | per-spec |
| Integration | `INT-###` | INT-001 | per-spec |
| Data Model Entity | `MODEL###_EntityName` | MODEL001_User | project |
| Process Flow | `FLOW###_NameSlug` | FLOW001_EvaluationCycle | project |

**Scope legend:** `per-screen` — ID namespaced under parent SCR###; same REG### may reappear under different SCR### without collision.

**Contiguity invariant:** project-scoped global schemes (F/US/SCR/BL/PERM/MODEL/FLOW) are contiguous 001..N in final artifacts (enforced by renumber gate + `validate_id_contiguity.py`). Per-screen REG### contiguous within each SCR###. Per-spec BR/SM/ALG/INT/DEC/FR not globally renumbered.

**Composite cross-ref parsing:** references of the form `SCR###/REG###` or `SCR###, SCR###/REG###` (comma-separated mixed refs) MUST split on `,` first (to separate multiple refs), then split each token on `/`. Left token = SCR### (must exist in ScreenList main index); right token (if present) = REG### (per-screen scope, must exist in that screen's Regions subsection). Validate left and right tokens independently. Grep-style validators looking for bare `SCR\d{3}` patterns MUST also match `SCR\d{3}(/REG\d{3}_\w+)?` when processing feature-list, user-stories, permissions artifacts.

### Discriminator Fields (DISC-###)

DISC-### codes identify enum/discriminator fields in the data model. Assigned by the W1 DataModel researcher; referenced by FS.1 feature spec researchers and W7a / FS.5 reviewers.

**Format:** `DISC-###` (3-digit zero-padded). Unique within a single `data-model.md` document. Not per-spec — project-scoped.

**Qualifies as a discriminator (enum OR boolean single-field):**
- Enum column in DB schema (`ENUM(...)`, `CHECK (col IN (...))`, TypeScript `enum`, Python `Enum`, etc.)
- String/integer field with a fixed value set enforced at application level (model constants, `const STATUS = [...]`, etc.)
- Boolean field that drives single-field conditional rendering or behavior (`survey.published`, `question.required`) — 2-row table (true/false)
- Field that drives `switch`/`case` or `if/elsif` branching on its value in controllers or services — where different values produce meaningfully different behavior (render path, validation, persistence, side effects)

**Does NOT qualify:**
- String/integer fields with unbounded/arbitrary values (free-text names, amounts, URLs)
- Fields used only for display labels with no behavioral branching
- Multi-field conditions (those are DEC-###, not DISC-###)

**Assignment:** DataModel researcher assigns DISC-### IDs sequentially in order of discovery across all entities (DISC-001, DISC-002, ...). IDs do not reset per entity.

**Scope legend:** `project` — DISC-### IDs are globally unique within a data-model.md document; not per-entity namespaced.

### Per-Spec Scope (BR / SM / ALG / INT / DEC)

`BR-###`, `SM-###`, `ALG-###`, `INT-###`, `DEC-###` IDs are LOCAL to a single feature spec. A `BR-001` in `F001_Auth/technical-spec.md` is unrelated to `BR-001` in `F002_Profile/technical-spec.md`. Similarly, `DEC-001` in `F001_Auth/technical-spec.md` is unrelated to `DEC-001` in `F014_SurveyTaking/technical-spec.md`. Cross-spec references (e.g., "see DEC-001 in F002") are INVALID and will be flagged critical by the reviewer.

**Placement note (v27.7.0, action-thread reshape — supersedes the pre-P08 `## Cross-Cutting
Logic`-based note this replaced):** `DEC-###` is a table row inline in the gating action's
`**Rule**` rung under `## 3. Actions` — never a standalone heading anywhere in the file. `BR-###`
follows the three-bin rule: a rule used by exactly ONE action lives inline in that action's Rule
rung (Bin 1); a rule used by ≥2 named actions has its one full block in `## 4. Shared Foundation
§ 4.4 Shared Rules` under `#### Bin 2` — the citation and pseudocode live there once — while each
using action's own Rule rung ALSO carries the plain-language gloss inline, never a bare code with
only a pointer (Bin 2; self-sufficiency clause, `feature-spec-researcher-contract.md`); a rule
belonging to no single action lives in § 4.4 under `#### Bin 3`, claimed by the `A0` row
(Bin 3). `SM-###`/`ALG-###`/`INT-###` full blocks live in `## 4. Shared Foundation` (§ 4.3 / § 4.5
respectively). Dedicated top-level sections for these prefixes are NOT used (reviewer flags
critical if present). Full rule + corpus justification:
`references/feature-spec-researcher-contract.md § New Technical Sections — Authoring Rules
(v27.7.0 action-thread)` (authoritative — this note is a summary, not a restatement). FR placement
rule (authoritative): see `references/feature-spec-researcher-contract.md § Placement Rules` —
summary: FR-### MUST appear under AT LEAST ONE § 2 Action Index row (or `A0`); appearing in zero
rows = CRITICAL (`action_unclaimed`). Appearing in two or more rows is legitimate fan-out (one
requirement, several handling actions), not an error — the exactly-one reading was retired; see
`docs/decisions/ADR-0006.md`'s addendum.
<!-- canonical-source: feature-spec-researcher-contract.md § Placement Rules -->

**Heading form:**
- `SM-###` / `ALG-###` / `INT-###` (v27.0.0, audience split, UNCHANGED by the action-thread
  reshape): all THREE stay H3 — `### {entity/algorithm/integration stated in one plain sentence}
  (SM-001)` / `### {...} (ALG-001)` / `### {...} (INT-001)` — a plain-language sentence with the
  code as a trailing tag, NOT the retired anchored-slug form (`### SM-001_NameSlug`). **Not H4**,
  even though the B-v design sample nests ALG/INT one level deeper under its `### 4.5` subsection
  heading — `scripts/_spec_block_lib.BLOCK_HEADING_RE` (the canonical, shared parser both the
  validator and the template must agree with) matches ONLY the H3 shape; nesting these as H4
  would silently stop the validator from finding them. Re-nesting to fix the heading-depth defect
  the sample's H4 choice was reaching for (ADR-0005 § 1.2) is a joint doc+validator change for a
  later phase. The canonical parsing patterns live in `scripts/_spec_block_lib.py` — import them,
  never re-type them (see `scripts/tests/test_spec_constants_single_source.py` guard (b)).
- `BR-###` (v27.7.0, action-thread reshape): **no heading at all.** Bin 1 is bold-lead-in prose
  inline in a Rule rung (`**BR-001 — sentence.** ...`); Bin 2/3 are bold-paragraph entries under
  an `#### Bin 2`/`#### Bin 3` H4 in § 4.4 — never its own `### {sentence} (BR-001)` H3. This is a
  genuine break from the pre-thread convention above; do not apply the SM/ALG/INT heading form to
  a Bin 2/3 rule.
- `DEC-###` (v27.7.0, action-thread reshape): **no heading at all.** A table row inline in the
  gating action's Rule rung (see below) — never the pre-thread `#### {sentence} (DEC-001)` H4.

#### DEC-### Required Fields (v27.7.0 — table row, not a block)

`DEC-###` renders as a row in a fixed-column table inline in the gating action's `**Rule**` rung
(`## 3. Actions`), not a standalone H4 block:

```
| DEC | subtype | Condition | What the user sees | Source |
|---|---|---|---|---|
| **DEC-001** | render | `{predicate}` | {what renders/hides} | `{file:line-line}` |
```

- `subtype` — `render` \| `interaction` \| `flow` (≥1, comma-separated if multiple)
- `Condition` — the predicate, stated directly in the cell (a fenced pseudocode block is only
  needed when the branching genuinely does not fit in one cell)
- `What the user sees` — the observable outcome
- `Source` — `file:line-range` (source-location-agnostic — saga/component/controller all valid)

`**Triggers in:**` (screen + event) and `**Involved entities:**` (entity.field driving the
branch) — required fields in the pre-thread H4-block shape — are now facts already carried by the
owning action's `**Who**`/`**FE**`/`**BE**` rungs above the table; they are not repeated per DEC
row.

The `**user_visible_outcome:**` field (1-sentence justification of business relevance) is NOT part
of this block (unchanged since v27.0.0) — it is stated once in `functional-spec.md` § 5 Business
Rules as the plain-language line for this DEC-###, not duplicated here.

## Background Logic Types

Canonical 10 types — language-neutral. Single source of truth for template, checklist, and agent prompts.

| Type | Description |
|------|-------------|
| custom-command | CLI commands |
| event-listener | Event-driven handlers |
| integration | Third-party integrations (external API clients) |
| mail | Email sending logic |
| middleware | Request/response processing chain (non-auth) |
| notification | In-app / push notification logic |
| observer | Model lifecycle hooks (created/updated/deleted) |
| queue-worker | Background job workers (async queue consumers) |
| scheduled-job | Cron-like scheduled tasks |
| webhook | Incoming/outgoing webhook handlers |

Auth/permission middleware → Permissions artifact only.

## Background Logic Item Fields

Required fields on every BL item (v2.9.0+). Enforced by Wave 7a reviewer (missing = critical).

| Field | Format | Example | Notes |
|-------|--------|---------|-------|
| `**Source File**` | Relative path from repo root | `app/Jobs/SendInvoice.php` | Must match scout BL inventory entry path |
| `**Source Symbol**` | Class, `Class::method`, or `module::function` | `SendInvoice` / `MailService::sendWelcome` | Mode A: class name; Mode B: class + method |

## Permission Types

| Type | Description |
|------|-------------|
| route-guard | Route-level authorization middleware |
| screen-permission | UI element visibility/enabled rules |
| action-permission | Button/action execution rules |
| data-permission | Field-level access control |
| role-based | Role-based access control rules |
| resource-ownership | Owner/resource relationship checks |
| field-permission | Column/field visibility rules |
| api-scope | OAuth/API scope permission |
| feature-flag | Runtime-evaluated flag from a feature flag service or config (requires `source:` field) |
| experiment | A/B test variant assignment gate (requires `source:` field) |
| env-gate | Hardcoded check against an environment variable; fixed at deploy time (requires `source:` field) |
| locale-gate | UI branch conditioned on the active locale or language setting (requires `source:` field) |

## Authorization System Types

| Type | Description | Indicators |
|------|-------------|------------|
| rbac | Role-Based Access Control | Roles (admin, user, manager), role assignments |
| abac | Attribute-Based Access Control | Policies, attributes (department, owner, status) |
| acl | Access Control List | Explicit user permissions, permission matrices |
| ownership | Resource Ownership | owner_id, created_by, can_edit rules |
| hybrid | Mixed (RBAC + Ownership) | Roles combined with ownership checks |
| other | Custom/Other | Custom permission logic |

## Valid Feature Requirements

A valid Feature MUST satisfy ALL 3 criteria:

| Criteria | Check | Invalid Example | Valid Example |
|----------|-------|----------------|--------------|
| Clear Flow | Input → Process → Output defined | "User management" | "User Login: credentials → validate → session" |
| Independently Testable | Can test in isolation | "All CRUD operations" | "Create User", "Delete User" |
| Agent Implementable | Single task chain | "Manage entire system" | "View User Profile" |

Invalid: "Admin Management" (too broad), "CRUD Operations" (not user-facing).

### Capability-Level Intent (authority)

**Authority — every other document that touches this rule links here by heading name; none restates it.** A Feature MAY span several capabilities; a new CAP exists only for a distinct primary business outcome / user intent — a semantic judgment about the outcome, never a wording check for the literal words "and"/"or". User-story count never by itself forces a CAP split, and stories with genuinely different business outcomes must not be merged just to hold one CAP. Enforced by `cap.analysis_required`, `cap.review_advised`, and E3's `CAP_MULTI_INTENT` — thresholds live with those rules, not here.

### Feature Clustering Rule (authority)

**Authority — every other document that touches this rule links here by heading name; none restates it.** Group User Stories into Features by PRIMARY BUSINESS INTENT — never by artifact volume, technical layer, or implementation mechanism. No count decides this: a Feature spanning many capabilities can be sound, and one spanning few can still be mixed.

- Each Feature has ONE primary business outcome that explains every US in it.
- A group of US serving a distinct business outcome, or an independent user intent, is a SEPARATE Feature.
- Never form a Feature whose members are held together only by HOW they are implemented ("all rake tasks", "all middleware", "all low-logic pages").
- Never form a Feature serving two different actors (buyer vs seller, admin vs member) unless both act on one shared outcome.
- Screens, APIs and models are evidence of independent flows — never a reason to group or split on their own.
- A Feature name that itself declares more than one outcome (`A & B`, `A and B`, comma-joined) is the author's own signal of a possible second outcome: examine it against the ONE-outcome bullet above and either state the single outcome that explains every US in it, or split. This is a prompt to LOOK, never a verdict — on a real 33-feature corpus 27 names carried a conjunction and only 2 were genuine defects, so treating the conjunction as the violation would be a count-based rule in syntactic disguise (Finding 1). Conversely a single-outcome name is no defence: the axis of grouping decides, not the wording. **(UNMEASURED — see Provenance.)**
- A single misfiled US is not a Feature: attach it to the Feature whose business outcome it actually serves. **(UNMEASURED — see Provenance.)**
- Every screen and background job must be explained by some Feature's stated intent. If none explains it, that is an undeclared outcome — give it its own Feature.

**Provenance.** The judgment form of these criteria measured 86% precision / 60% recall over three independent runs, against 30% recall for the prior rubric — n=18, sample DELIBERATELY ENRICHED across suspicion bands (its SPLIT rate is the sample's, never the corpus's), Fleiss kappa 0.481, and rules searched against those same labels, so every figure is an upper bound. Two bullets are marked UNMEASURED and were never themselves run: the misfiled-US bullet (the trial's recommendation for its one false positive) and the multi-outcome-name bullet (added later from a field report, where 27 of 33 names carried a conjunction and 2 were real defects — the ratio is why it directs attention instead of deciding). Both are the first candidates for removal if a future measurement implicates them. Full record, including three designs that died reaching this one: `docs/decisions/ADR-0005.md`.

## Valid User Story Requirements

A valid User Story MUST satisfy ALL 4 criteria:

| Criteria | Check | Invalid Example | Valid Example |
|----------|-------|----------------|--------------|
| Single Action | One user action | "Login and view dashboard" | "Login" |
| Independent | No dependency on other US | "Reset password after login" | "Request Password Reset" |
| Testable | Clear pass/fail outcome | "User is happy" | "User receives email" |
| Observable Result | UI/API/data/state change | "System works" | "User sees confirmation message" |

**US Types**: `ui` US require at least one `SCR###` or `SCR###/REG###` mapping. `system` US require at least one BL### mapping.

## Valid Screen Requirements

| Criteria | Check |
|----------|-------|
| Has Route | Screen must have a route in RouteList |
| Has US Mapping | Screen must have at least one US### mapped |

F### mapping is NOT in Screen/ScreenList. FeatureList is the ONLY document that maps features to other artifacts.

## Valid Code Logic Block Requirements (BR / SM / ALG / INT)

A valid BR / SM / ALG / INT block (inside a feature spec) MUST satisfy ALL 4 criteria:

| Criteria | Check | Invalid | Valid |
|----------|-------|---------|-------|
| Has Source | `**Source:** {path}:{start}-{end}` present | missing or just file with no line range | `**Source:** src/auth/login.controller.ts:42-61` |
| Has Description | For SM/ALG/INT: heading states the entity/logic in one plain, non-placeholder sentence — the trailing `(CODE-###)` tag form, not a slug. For BR: the bold lead-in sentence inline in its Rule rung or § 4.4 Bin entry (no heading at all — v27.7.0 action-thread reshape). Either way: `technical-spec.md`'s block itself carries no separate narrative field; the plain-language "why" restatement lives once in `functional-spec.md` § 5 Business Rules (v27.0.0) | `### {Rule stated in one plain sentence} (BR-001)` left unfilled, or the retired anchored form `### BR-001_OrderMinItems` | `**BR-001 — Orders must contain at least one item.**` (Bin 1/2/3 lead-in) |
| Has Body | Pseudocode ≤20 lines OR Mermaid `stateDiagram-v2` (SM only) | empty code fence or >20 lines of raw source | compact pseudocode capturing intent |
| Has Linked FR | `**Linked FR:** FR-###` with ≥1 FR defined in same spec | links to FR in another spec | `**Linked FR:** FR-002` present in same spec |

**Additional rules:**
- BR / SM / ALG / INT IDs unique within the spec.
- SM MUST include a Mermaid `stateDiagram-v2` block (prose alone is not enough).
- Pseudocode MUST NOT contain secrets, credentials, API keys observed in source — redact.
- `file:line-range` cited in `**Source:**` MUST exist and contain the referenced logic (reviewer verifies via Read).

## Valid Background Logic Requirements

| Criteria | Check |
|----------|-------|
| Has Type | Must use a valid type (see Background Logic Types table) |
| Has Trigger | Must have a trigger condition |
| Has US Mapping | Must have at least one system US### mapped |

## Validation Rule Patterns

Detection patterns for validation rules in source code:

| Pattern | Example | Framework |
|---------|---------|-----------|
| `@NotNull`, `@Required` | `@NotNull` | Java, Kotlin |
| `NOT NULL` | `name VARCHAR(255) NOT NULL` | SQL |
| `unique` constraint | `UNIQUE(email)` | SQL |
| `@Unique` | `@Unique` | Various |
| `min/max` | `min: 1, max: 100` | JS/TS validators |
| `@Min`, `@Max` | `@Min(0) @Max(120)` | Java |
| `length` | `length: { min: 2, max: 50 }` | JS/TS |
| `@Size` | `@Size(min=2, max=50)` | Java |
| `pattern` / `regex` | `pattern: /^[a-z]+$/i` | JS/TS |
| `@Pattern` | `@Pattern(regexp="^[A-Z]")` | Java |
| `email` validator | `type: 'email'` | JS/TS |
| `@Email` | `@Email` | Java |
| `required` | `required: true` | JSON Schema |
| `allowNull: false` | `allowNull: false` | Sequelize |
| `validate: { notNull }` | `validate: { notNull: true }` | Sequelize |
