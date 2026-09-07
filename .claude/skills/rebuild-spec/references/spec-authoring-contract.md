<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Spec-Authoring Contract (takumi greenfield — delta from sibling)

**Extends:** [`feature-spec-researcher-contract.md`](feature-spec-researcher-contract.md)
(section ownership matrix, per-file depth rules, forbidden tokens, DEC-###/DISC-###/SM rules)

This file documents ONLY the delta for takumi-authored greenfield specs.
Do NOT duplicate sections already defined in the sibling contract.

---

## Draft Frontmatter Schema

Appears at the top of `technical-spec.md` and screen `spec.md` (the other feature file,
`functional-spec.md`, inherits provenance from the folder; validators only scan `technical-spec.md`).

**Exact keys in order — single-line values only (stdlib `re` parseable, no nested YAML):**

NEW feature (plan-dir draft — `fcode:` OMITTED, allocated at promote):
```yaml
---
status: draft
authored_by: takumi
created: 2026-06-11
lang: en
---
```

EXISTING `implemented` feature being revised (`fcode:` present — reuse its code):
```yaml
---
status: draft
authored_by: takumi
fcode: F042
created: 2026-06-11
lang: en
---
```

Allowed values: `status` = `draft|implemented`; `authored_by` = `takumi|rebuild-spec`;
`fcode` = `^F\d{3}$` — **omit entirely for NEW-feature plan-dir drafts** (allocated at promote);
present only when revising an EXISTING `implemented` feature (reuse its code); `created` = `^\d{4}-\d{2}-\d{2}$`;
`lang` = `^[a-z]{2,3}(-[a-z0-9]{2,8})*$` — the prose language resolved by `spec-stage-procedure.md`
Pre-Step (omitting it is read as `en`). Validators do not reject the key (frontmatter is parsed by
targeted per-key regexes, no whitelist).

When takumi promotes a draft at implement-start, `status` flips to `implemented`, `fcode:` is added if
absent, `authored_by` is unchanged, and `lang:` is preserved. For a greenfield first-promote (no
`docs/.rebuild-state.json` yet), promote seeds `primary_lang` from this `lang:` value — see
[`spec-state-registration.md`](spec-state-registration.md) Step 1. On a NON-greenfield promote where
the draft's `lang:` ≠ the established `primary_lang`, the orchestrator MUST warn and ask the user
whether to proceed — it NEVER silently overwrites `primary_lang`.

---

## Authoring Mode Inputs (OVERRIDES sibling § Mandatory Context Inputs)

In greenfield/takumi mode the researcher reads:

1. Study reports from Stage 1 (researcher output from plan artifacts)
2. `clarifications.md` from the active plan directory — if present
3. MoMorph specs fetched via MCP — when a MoMorph screen URL is present

**The following 5 upstream artifacts are NOT required and MUST NOT block authoring:**
`scout-report.md`, `screen-flow.md`, `user-stories.md`, `permissions-matrix.md`, `behavior-logic.md`
These are produced by rebuild-spec extraction passes that have not yet run.

**Per-section authoring rules:**

The H2 set + order of BOTH feature files is FIXED by the canonical templates
(`templates/functional-spec-template.md`, `templates/technical-spec-template.md`) and enforced by
`validate_feature_spec.py` at promote. Read the section numbers from `scripts/_spec_constants.py`
(`REQUIRED_H2_FUNC`, `REQUIRED_H2_TECH_THREAD`, `REQUIRED_APPENDIX_H3`, `REQUIRED_VERIF_H3`) —
that module is the single source of truth; never copy a number out of prose (this file went stale
exactly that way once already). **v27.7.0 (action-thread reshape):** author `technical-spec.md`
to the TARGET action-thread shape below — `REQUIRED_H2_TECH`/`REQUIRED_SYSDESIGN_H3` (the OLD
layer-first names) still govern the exact-order validator until a later phase repoints it; that
is a deliberate mid-migration window on the reverse-engineering side, not a reason to author a
NEW greenfield draft to the old shape. Author from intent within the fixed skeleton — a greenfield
draft never adds, removes, or renumbers a section.

A standalone, unnumbered `## Functional Requirements` / `## Requirements` / `## Business Rules` /
`## Success Criteria` H2 in `technical-spec.md` is **deprecated** (validator-critical). FRs and
BRs are stated ONCE, as one-liners, in `functional-spec.md` §§ 4/5 — `technical-spec.md` never
restates them, it only references the code and points at the implementation: a claiming row in
`## 2. Action Index`, plus (for a BR) the rule's home per the three-bin split — inline in the
owning action's Rule rung (§ 3, Bin 1) or in `## 4. Shared Foundation § 4.4` (Bin 2/3). See parent
contract § Placement Rules and § "New Technical Sections — Authoring Rules (v27.7.0
action-thread)".

`functional-spec.md` (13 sections — `REQUIRED_H2_FUNC`):

| Section | Source | Rule |
|---|---|---|
| `## 1. Overview` | Study reports + decisions | Author from intent — Problem/Solution/Scope/Non-Scope fields + Actors table; no source code needed |
| `## 2. Functional Capabilities` | Study reports + decisions | Author `CAP-###` rows from intent; `Requirements` cites FR-### codes that MUST also appear in § 4 |
| `## 3. Open Decisions` | `clarifications.md` + `[NEEDS_DOMAIN_CONFIRMATION]` markers raised while authoring | Every unresolved marker is promoted to a row here — never left inline |
| `## 4. Requirements` | Study reports + decisions | Author FR-### one-liners from intent, banded 0xx/1xx/2xx-3xx/4xx/6xx per template — NO standalone `## Functional Requirements` heading |
| `## 5. Business Rules` | intent only | Author BR-###/DEC-###/SM-### one-liners from intent — skeletal, explicit `TBD (draft)` markers, NEVER fabricate detail |
| `## 6. Screens` → `### User Journey` | Study reports + MoMorph if present | Author from intent; heading is `## 6. Screens` (NOT "Screen Route Table") |
| `## 7. User Stories` | intent only | Allocate US### LOCALLY (sequential no-hyphen — US001, US002 …; no upstream user-stories.md). Each block leads with **Actor** (matches a § 1 Actors row) / **Goal** / **Business value** (D6 — target-shape-spec.md § 6) |
| `## 8. Scenarios` | intent only | Given/When/Then per US### — at least one happy-path, one error scenario |
| `## 9. Edge Cases` | intent only | Minimum 3 rows for UI features (`FUNC_EDGE_CASES_SKELETON` supplies the header + placeholder rows) |
| `## 10. Edge Behaviours to Verify` | intent only | One line per cited FR-### → the plain-language behaviour a tester should confirm |
| `## 11. Risks & Known Issues` | N/A — no shipped code to misbehave yet | Greenfield default: `N/A — none found.` A design-level `risk` row is allowed; a `known-issue` row is not (nothing has been observed yet) |
| `## 12. Dependencies` | Study reports + decisions | Author from intent; `TBD (draft)` for a dependency not yet confirmed |
| `## 13. Configuration` | intent only | Author user-facing config from intent, or `N/A — no user-facing configuration constants for this feature.` |

`technical-spec.md` (action-thread taxonomy, v27.7.0 — `REQUIRED_H2_TECH_THREAD` +
`REQUIRED_APPENDIX_H3` + `REQUIRED_VERIF_H3`):

| Section | Source | Rule |
|---|---|---|
| `## 1. Technical Overview` | Study reports + decisions | Author from intent — no source code needed |
| `## 2. Action Index` | twin `functional-spec.md` §§ 2/4/5/7 + § 3 below | One row per PLANNED action (a `Class#method` handler is unlikely to exist yet — use the intended handler name as a provisional identity, e.g. `` `RefundRequestController#create` (planned)``, never `TBD (draft)` alone for this cell since the row's whole point is the identity); `Codes` claims every FR/BR/DEC/SM/US the action will serve; `Writes`/`Detail` → `TBD (draft)` where no table/diagram decision has been made yet. `A0` is mandatory even in a draft. |
| `## 3. Actions` → dynamic `### 3.N CAP-NN` buckets, each with `#### A<n>` blocks | twin `functional-spec.md` § 2, in CAP- order | One bucket per CAP-N row in the twin (never invented here); one block per § 2 Action Index row. Rungs are skeletal — author `**Who**`/`**FE**`/`**Request**`/`**BE**` from intent, `**Rule**`/`**Result**` as `TBD (draft)` where the behavior is not yet decided, `**Source:**` → `TBD (draft)` (no code exists yet). **State** is omitted entirely in a draft rather than guessed — no source exists yet to confirm a transition from. Ends with a skeletal `### 3.{N+1} Edge cases` table. Every code in an H4 context line still needs its gloss even in a draft — see the sibling contract's § "Self-sufficiency of the H4 context line" (canonical; not restated here). |
| `## 4. Shared Foundation` → `### 4.1`–`### 4.6` | intent only | Skeletal with explicit `TBD (draft)` markers, in `REQUIRED_APPENDIX_H3` order — NEVER fabricate a component/table/endpoint that doesn't exist yet. § 4.4 Shared Rules: only author a Bin 2/3 entry when the design intent is genuinely "used by ≥2 planned actions" or "cross-cutting" — when unsure, default to inline (Bin 1) in § 3, since promoting a rule to § 4.4 on a guess is itself a fabrication about scope. |
| `## 5. Verification & Technical Notes` → `### 5.1`–`### 5.5` | intent only | Author in `REQUIRED_VERIF_H3` order; `### 5.4 Source References` heading MUST be present with an empty or prose-only body (code not written yet); `### 5.5 Artifact References` — the `Feature List` row carries the provisional `F###`, every other row's `Codes Used` is `TBD (draft)` |

NEVER invent `**Source:** path:N-M` citations for code that does not yet exist.
A cited non-existent path is a **warning** while the spec is `status: draft` (authored_by: takumi),
but `citation.file_missing` becomes **critical** once the spec is promoted to `status: implemented` —
a fabricated draft citation will block validation at implement-start. Do not add it.

---

## Greenfield Output Paths

| Output | Path |
|---|---|
| Feature-list (SYSTEM only) | `plans/<plan_dir>/spec/feature-list.md` (plan-local draft — NOT docs/) |
| Feature 2-file set | `plans/<plan_dir>/spec/<slug>/` (plan-local draft — NOT docs/) |
| Screen spec | `plans/<plan_dir>/spec/<slug>/screens/SCR-<name>/spec.md` (plan-local) |
| System doc (architecture/permissions — opt-in, see § Forward-Authored System Docs) | `plans/<plan_dir>/spec/system/<name>.md` (plan-local draft — NOT docs/) |

**`### 5.4 Source References` rule** (renamed/renumbered from the retired `## Source Code
References` — see the § Authoring Mode Inputs table above): heading is ALWAYS present in
`technical-spec.md`; body is empty or contains prose-only notes (e.g. "No source code written yet
— see `## 7. User Stories` in functional-spec.md for planned behavior"). The `**Source:** path:N-M`
pattern MUST NOT appear in any draft spec — the validator only *warns* (not blocks) on source
checks for drafts, but any such citation flips to a critical failure after promote
(`status: implemented`).

---

## Forward-Authored System Docs (architecture + permissions)

SYSTEM-level design IS proper SDD: architecture and the permission model are decided BEFORE code.
So when a feature TOUCHES architecture or auth, Stage 1.5 ALSO forward-drafts the relevant system
narrative — drafted in the plan dir, promoted at implement-start (single-file § Promote — SYSTEM-DOC),
then RECONCILED to as-built by the post-forge Core pass.

- **Forward-authorable set = `docs/system/architecture.md`, `docs/system/permissions.md` ONLY.**
  (`entities` is NOT in scope — per-feature `technical-spec.md § 3.2 Data Model > #### Key Entities`
  already carries data-model intent.)
- **Trigger (reuse, do not reinvent):** the Trigger Mapping in
  `claude/skills/takumi/references/subagent-patterns.md` → `## Documentation` —
  new service/layer/integration/data-store → `architecture.md`; Auth/RBAC/policy/guard/middleware/roles
  → `permissions.md`. A feature touching neither produces NO system draft (opt-in, no noise).
- **Draft frontmatter** (single-file; mirrors the feature draft MINUS `fcode:` — system docs are not features):
  ```yaml
  ---
  status: draft
  authored_by: takumi
  created: <YYYY-MM-DD>
  lang: <spec_lang>
  ---
  ```
- **HARD RULES (non-negotiable):**
  1. Write ONLY the `docs/system/*` narrative homes — **NEVER `docs/generated/*`** (route-list, entities,
     permissions-matrix). Those are code-derived inventories (DRY; the Core pass owns them).
  2. **NEVER fabricate codes** — `PERM###/SCR###/US###/ROUTE###/MODEL###/BL###` MUST be `TBD (draft)`,
     never a guessed/real code (these are machine-allocated, not provisional like feature-list `F###`);
     real codes are assigned at reconcile.
  3. Design **RATIONALE** ("why this architecture / permission model") goes in `docs/decisions/ADR-*.md`
     (human-owned, never regenerated) — NOT the draft. The Core reconcile may overwrite the narrative.

---

## Greenfield Feature-List (SYSTEM decomposition)

When a task is a SYSTEM (more than one user-facing intent), the spec stage first decomposes it into a
`feature-list.md` draft, then fans out one 2-file set per feature. This section is the delta for that
draft; the SINGLE-feature path never produces a feature-list. Orchestration lives in
`spec-stage-procedure.md` Steps 0–0b; this file owns the **format + content rules**.

**Format — reuse the rebuild-spec template verbatim:** `templates/feature-list-template.md`
(the `Code | Name | Type | Language | Workspace | Priority` Feature Hierarchy table + a "Feature
Details" block per `F###`). Do NOT invent a bespoke layout.

**Greenfield deltas (because no code/upstream artifacts exist yet):**

| Template element | Greenfield rule |
|---|---|
| `F###` codes | **PROVISIONAL** `F001..FNNN`, sequential. Real allocation/renumber happens at promote (existing `id_contiguity` machinery). The draft folders are named by slug (no `F###` prefix). |
| Related Screens / User Stories / APIs / Data Models / Background Logic / Permissions | Fill from intent where derivable; otherwise `TBD (draft)`. **NEVER fabricate** `SCR###/US###/ROUTE###/MODEL###/BL###/PERM###` codes for artifacts that do not exist. |
| "Cross-Reference Validation" checklist | Drop the rows that validate against `user-stories.md` / `screen-list.md` / `route-list.md` etc. (those artifacts are not produced in greenfield). Keep only `F### codes are unique`. |
| Workspace / Language columns | Best-effort from the intended stack; `TBD (draft)` if unknown. |

**Quality gate (greenfield subset of W5.6 — `verification-checklist-quality-gates.md` § FeatureList).**
The decomposition is gated before the user confirms it. Reviewer keeps the intent-based checks and
relaxes the cross-artifact ones:
- **Kept:** Check 4 F-code uniqueness (needs only the feature-list itself), Check 6 Clear Flow /
  input→process→output (warning), Check 7 Vague-naming (warning), Check 8 Scope-overlap >50%
  (warning), Check 9 Grouping-coherence (critical).
- **Not a gate:** Check 5 is a pointer slot, not an evaluated check — capability-intent judgment lives
  in `code-formats.md § Capability-Level Intent (authority)`.
- **Skipped (not failed):** Checks 1–3 only (US###/SCR### coverage + orphan) — nothing to
  cross-reference yet. Check 4 is NOT skipped despite being in Group A.

Output: `plans/<plan_dir>/spec/feature-list-review.md` with frontmatter `passed: bool, issues: int, warnings: int`.

**Feature-list frontmatter** (single-line, stdlib-`re` parseable, mirrors the per-spec schema):

```yaml
---
status: draft
authored_by: takumi
created: <YYYY-MM-DD>
---
```

No `fcode:` key on the feature-list itself (it indexes many provisional codes). The decomposition
researcher writes ONLY `feature-list.md`; it does NOT touch state files (registration is the
orchestrator's job at promote).

---

## Screen-Spec Authoring

Draft file: `plans/<plan_dir>/spec/<slug>/screens/SCR-<name>/spec.md` (plan-local, no `SCR###`).
Promoted to `docs/screens/SCR###_Name/spec.md` at implement-start (promote allocates the `SCR###`).

Draft frontmatter uses `fcode` of the owning feature (present only for EXISTING-feature updates; omit
for a NEW feature until promote):

```yaml
---
status: draft
authored_by: takumi
fcode: F042
created: 2026-06-11
---
```

**Scope: UI-layer ONLY.** Screen specs MUST NOT contain codes from these namespaces:
`FR-###`, `BR-###`, `SM-###`, `ALG-###`, `INT-###`, `SC-###`. Those codes belong in `technical-spec.md`.
A greenfield author is the person MOST likely to invent a navigation destination that doesn't
exist yet — `## 8. Navigation` is the per-screen PROJECTION of `screen-flow.md § Screen Access
Paths` (the D3 DRY rule, target-shape-spec.md § 1), never a second source of truth, even in a
draft. A destination not yet reflected in `screen-flow.md` is `TBD (draft)`, not a guess.

**Format: follow `templates/screen-spec-template.md` headings — greenfield-lite subset.** The canonical
screen-spec template (reshaped P03/P04) is built for reverse-engineering existing code: 10 numbered
BA/PO/QA/Designer sections (§§ 1–10), then a `## Technical Appendix` divider, then 6 H2 appendix
sections (A1–A6: `## Implementation Mapping`, `## Component Variants`, `## Child Routes`,
`## Security Surface`, `## Source References`, `## Source Walkthrough` — target-shape-spec.md § 1).
In greenfield no code exists yet, so author the subset derivable from design intent and OMIT the
entire appendix (rather than inventing a bespoke shape) — a greenfield draft has no implementation
to appendix. Use the template's **canonical headings verbatim** so promote reconciles cleanly:

| Template section | Greenfield draft |
|---|---|
| `# {SCR###_Name} — Screen Spec` + `**Screen** / **Feature** / **Type** / **Route** / **Generated**` | Author. Draft uses the draft name (`SCR-<name>`, no `SCR###`); `**Type**` = atomic\|composite. |
| `## 1. Overview` | Author from intent — Purpose/Actors/Entry Conditions/Exit Conditions fields, plain language. |
| `## 2. Screen Layout` | `### Layout Sketch` REQUIRED — author from intended layout (region names + ASCII sketch). `### Layout Regions` optional; when present, `Key Components` → `TBD (draft)` (no code exists yet). |
| `## 3. UI Elements` | REQUIRED — the primary greenfield artifact. Author the full element inventory from intent; `Source`/`Cross-ref` → `TBD (draft)` where no binding exists yet. |
| `## 4. User Actions` | `### Available Actions` + `### Happy Path` REQUIRED; `### Branches` optional. Author from intent. `Source` column → `TBD (draft)`. |
| `## 5. UI States` | REQUIRED — author loading/empty/error/saving/success rows from intent. `Source` column → `TBD (draft)`. |
| `## 6. Validation & Feedback` | REQUIRED — author the rule + user-visible message text from intent. Endpoint/HTTP/async-check detail does NOT appear anywhere in a greenfield draft — that is `## Implementation Mapping`'s job, and the whole appendix is omitted (see below). |
| `## 7. Conditional UI` | Optional — author only conditions already decided; otherwise `N/A — no conditional UI detected.` |
| `## 8. Navigation` | REQUIRED — `### Entry Points` / `### Exits`, intent-derived. `Source` column → `TBD (draft)`. See the D3 DRY rule above: every row must be derivable from (or become) a `screen-flow.md` path. |
| `## 9. Accessibility` | Optional. Greenfield entries are `[EXPECTED]` BY DEFINITION — see below — never written as current behavior, since there is no current behavior yet. |
| `## 10. Responsive Behavior` | Optional — author only breakpoints already decided; otherwise `N/A — no responsive behavior found in source.` |
| `## Technical Appendix` + its 6 H2 siblings (`## Implementation Mapping`, `## Component Variants`, `## Child Routes`, `## Security Surface`, `## Source References`, `## Source Walkthrough`) | **OMIT entirely in greenfield** (no exceptions) — a greenfield draft has no implementation to appendix. Promote/post-forge reconcile adds the whole appendix from the as-built code. |

`[EXPECTED]` is THE greenfield marker (see `references/confidence-report-contract.md` for the
canonical taxonomy — do not restate or fork it here): every assertion a greenfield draft makes is
DESIRED behavior, never observed, because nothing has been built yet. `## 9. Accessibility` is
the clearest instance — a greenfield accessibility posture is always a plan, so its `Status`
cells read `[EXPECTED]`, never `present`/`supported`/`unknown`.

Do NOT emit ad-hoc headings (`## Layout & Component Tree`, `## Form Fields`, `## User-Visible Copy`,
`## Constraints`) — those diverge from the canonical template. **Collision check (P12):** none of
these four retired literals matches any of the 10 canonical section names above — confirmed safe,
recorded here so a future editor does not have to re-derive it. Fold their content into the
canonical headings instead (component tree → `## 2. Screen Layout`; form fields →
`## 6. Validation & Feedback`; copy → inline in the relevant `## 4. User Actions` / `## 5. UI
States` rows).

---

## Minimal-Spec Rule

| Discipline | Output |
|---|---|
| NEW feature (SINGLE) | Full 2-file set in `plans/<plan_dir>/spec/<slug>/`: `technical-spec.md`, `functional-spec.md` |
| NEW SYSTEM (multi-feature) | `feature-list.md` + one full 2-file set per confirmed feature, all under `plans/<plan_dir>/spec/`. See § Greenfield Feature-List. |
| `--fast` discipline | `technical-spec.md` delta only, in the plan dir (single-feature; never decomposes). Advisory note at delivery: unwritten files remain `status: draft` with empty bodies. |
| EXISTING feature (`status: implemented`) | Author the revised draft into the plan dir tied to the existing `F###` (the shipped `docs/` spec is untouched until promote overwrites it). |

---

## Gap-Analysis Return Block

After authoring, the researcher MUST return a `## Gaps for Clarification` block.
The orchestrator (Phase 3) parses the typed fields into `AskUserQuestion` — free-form prose
is NEVER lifted verbatim as a default.

**Strict schema — numbered list, each item with exactly these fields:**

```
## Gaps for Clarification

1. question: Can unauthenticated users access this feature?
   options: [Yes public, No auth required, Role-gated, TBD]
   recommended: No auth required
   category: auth

2. question: Which external service handles payment processing?
   options: [Stripe, PayPal, Internal, TBD]
   recommended: TBD
   category: external-integration
```

**`category` values:** `auth | permissions | scope | external-integration | data-model | ui | copy | other`

Rules:
- `options` must contain 2–4 entries.
- `recommended` must be one of the `options` values exactly.
- No prose paragraphs under gap items — fields only.
- If no gaps exist, write `## Gaps for Clarification\n\n_None._`

---

## State-Registration Handoff

Registration of new F### and SCR### codes into rebuild-spec state files (`docs/.rebuild-state.json`,
`docs/_source-to-fcode.json`, `docs/generated/feature-list.md`, `docs/generated/screen-list.md`,
`_canonical-fcodes.json`) is the **orchestrator's responsibility** — not the researcher's, and it runs
at **PROMOTE time** (implement-start), not at author time.

The researcher writes spec files only, to the plan dir. It MUST NOT touch state files.

See [`spec-state-registration.md`](spec-state-registration.md) for the registration recipe.

---

## Security

Draft specs MUST NOT embed secrets, credentials, or API keys in pseudocode or prose
(inherited from sibling contract).
