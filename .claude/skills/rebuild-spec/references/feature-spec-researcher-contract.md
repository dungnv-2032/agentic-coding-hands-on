<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Researcher Contract (rebuild-spec v27.x — audience split + human-readable SOT)

## Provenance Frontmatter (MANDATORY, byte 0)

Every file this contract produces (`technical-spec.md`, `functional-spec.md`) MUST open with the
following as the literal first three lines — before any `<!-- layout-exempt -->` /
`<!-- Contract: -->` HTML comment, and before the `# F###_Name` heading:

```yaml
---
authored_by: rebuild-spec
---
```

`_slug_lib._read_frontmatter()` requires the `---` fence at byte 0, so this block cannot be moved
below any comment (`templates/technical-spec-template.md` and `templates/functional-spec-template.md`
already carry it this way — start from the template, do not hand-author the header). This is what
lets the audience-split migration probe (`_audience_split_probe_lib.py`) recognize a
rebuild-spec-authored file by presence, instead of falling back to the fail-closed `HAND_EDITED`
default when the field is absent. Allowed `authored_by` values are `takumi|rebuild-spec` — see
[`spec-authoring-contract.md`](spec-authoring-contract.md) § Draft Frontmatter Schema for the full
vocabulary (defined there, not restated here); rebuild-spec's own output is always
`authored_by: rebuild-spec`, never `takumi`. Do NOT omit this block, and do NOT invent a third value.

## Session Context

Read `plans/<active-plan>/artifacts/_session-context.md` FIRST before any other artifact read.
Do NOT re-derive information already present there.

## Mandatory Context Inputs (read ALL before drafting any file)

Read these upstream artifacts from `plans/<active>/artifacts/` before writing anything:
- `scout-report.md` — codebase map
- `screen-flow.md` — screen navigation graph
- `user-stories.md` — US### inventory
- `permissions-matrix.md` — PERM### roles (raw matrix; PERM### codes live here, not in the curated `permissions.md`)
- `business-rules.md` — system-level plain-language rules (W3 output). MUST NOT contradict these in `functional-spec.md`
- `flows/*.md` — cross-feature process-flows (FL.1 output; directory may be empty on first FS.1 run). Check if this F### participates in any flow via the flow file's frontmatter `source:` list. If yes → cross-reference in `functional-spec.md` § 1 Overview (plain language, no codes).
- `feature-list.md` — F### inventory + canonical slugs

**PASS-2 LARGE SPEC:** If dispatcher provides a `PASS_1_DRAFT` path, read that file using Read tool with specific offset/limit per section. Append SM/ALG/INT sections to `technical-spec.md`. Do NOT inline its full content into memory.

## Output Files (2 mandatory)

Each F### produces 2 files under `plans/<active>/artifacts/features/{slug}/`. **Section numbers
and order below are NOT restated in full here** — `target-shape-spec.md` §§ 2–3 and
`templates/{functional,technical}-spec-template.md` are the single source of truth; if this
contract and a template ever disagree, the template wins and this file is the bug.

1. `technical-spec.md` — Dev/QA/SA audience. **v27.7.0 action-thread reshape
   (`wire-format-contract.md` is normative; this contract is the bug if the two ever disagree):**
   `## 1. Technical Overview` → `## 2. Action Index` (the action→rule binding — one row per
   action, keyed on the HANDLER, not `METHOD PATH`; see "New Technical Sections" below) →
   `## 3. Actions` (the body: one `### 3.N CAP-NN` bucket per capability, each holding
   `#### A<n>` blocks that use a fixed labelled rung set, ending in one feature-wide Edge cases
   table) → `## 4. Shared Foundation` (appendix: components/data model/state/shared rules/
   algorithms & integrations/config — what used to be § 3 System Design, demoted) →
   `## 5. Verification & Technical Notes`, followed by the two unnumbered literal H2s
   `## Source Walkthrough` (A3) and `## DB Impact per Event` (B4, unchanged by this reshape).
   Carries all FR/BR/SM/ALG/INT/DEC codes with full `**Source:**` citations, pseudocode, key
   entities, DB impact, source walkthrough.
2. `functional-spec.md` — BA/QA audience. Plain language, no `file:line`, no class names, no HTTP
   verbs, no pseudocode outside fences (the 4 status markers below ARE permitted — D6). 13
   sections: Overview → Functional Capabilities → Open Decisions → Requirements → Business Rules
   → Screens → User Stories (Actor → Goal → Business value) → Scenarios → Edge Cases → Edge
   Behaviours to Verify → Risks & Known Issues → Dependencies → Configuration. See Forbidden
   Tokens below.

Every code (FR/BR/SM/DEC/ALG/INT) is **stated once** in `functional-spec.md` and **implemented
once** in `technical-spec.md`. Never restate a plain-language rule sentence, a User Story
narrative, or its Given/When/Then/Acceptance-Criteria in `technical-spec.md` — reference the code
and describe the implementation instead. Never restate a Source citation or pseudocode block in
`functional-spec.md`.

### Confidence Companion (advisory sidecar)

`confidence-report_technical-spec.md` is NOT one of the 2 mandatory files above. It is emitted
automatically by `scripts/derive_confidence_report.py` (a deterministic script, not authored
by the researcher) after `technical-spec.md` is promoted — a citation-coverage sidecar, never
gated, never asserted. `functional-spec.md` carries no `**Source:**` citations, so it is out of
scope for this sidecar by construction. See `references/confidence-report-contract.md` for the
full derivation rules and the A1 correctness-verification boundary.

### Sidecar Files (guard against future confusion)

`docs/features/{slug}/test-cases.md` (v26.1.0 B6, opt-in `--test-cases` pass) is a 3rd file that
lives in the SAME per-feature directory as the 2 mandatory files above, but it is **SIDECAR** —
same principle as the A1 confidence-report companion, different reason (test-cases.md is a real
researcher-authored deliverable that simply arrives on a separate, later, optional pass, not a
machine-derived stat). It is NEVER added to the `FEATURE_FILES` tuple (`scripts/_slug_lib.py`),
never checked by `check_promotion_gate.py`, and never part of `scaffold_spec.py`'s scaffold. Do
NOT treat its absence as `MISSING` in any feature-spec review. See
`references/test-cases-researcher-contract.md` for the pass that produces it.

## Section Ownership Matrix

Regenerated for the v27.x retaxonomy — 13 functional H2s + 5 technical H2s (+ A3/B4). Read
`_spec_constants.REQUIRED_H2_FUNC` for the authoritative current functional heading text.
**Technical heading text (v27.7.0 action-thread reshape):** the target shape below matches
`_spec_constants.REQUIRED_H2_TECH_THREAD` / `REQUIRED_APPENDIX_H3` — `REQUIRED_H2_TECH` /
`REQUIRED_SYSDESIGN_H3` still name the OLD layer-first shape and stay byte-identical until a
later phase repoints the exact-order validator (deliberate — several phases still import them
mid-migration; do not read their continued presence as this reshape being reverted). The numbers
below are for cross-reference, not restatement.

| Source content | File owner | Notes |
|---|---|---|
| Overview (Problem/Solution/Scope/Non-Scope, Actors table) | `functional-spec.md` § 1 | Plain language; no codes |
| Technical Overview (2–3 sentence dev narrative) | `technical-spec.md` § 1 | |
| Functional Capabilities (`CAP-###` rollup — ID/Capability/What-the-user-can-do/User Stories/Requirements/Business Rules/Screens) | `functional-spec.md` § 2 | The anchor `technical-spec.md § 3`'s `### 3.N` buckets group against; every US###/FR-###/BR-###/SCR### declared in §§ 4-7 must be claimed by exactly one row — see § 2's own authoring rule below |
| Action Index (action→rule binding: handler, Method·Path, Codes claimed, tables written) | `technical-spec.md` § 2 | One row per action, keyed on the HANDLER (D2) — see "New Technical Sections" below. Replaces the retired `## 2. Functional → Technical Mapping` (a CODE-keyed table; this is ACTION-keyed) |
| Open Decisions (`[NEEDS_DOMAIN_CONFIRMATION]` promoted) | `functional-spec.md` § 3 | See Domain-Confirmation Promotion below |
| Requirements (plain sentence per FR) | `functional-spec.md` § 4 | One sentence per FR-###, code bold-inline; banded 0xx/1xx/2xx-3xx/4xx/6xx |
| Shared Foundation (components/data model/state/shared rules/algorithms & integrations/config) | `technical-spec.md` § 4 (`### 4.1`–`### 4.6`) | Capability-agnostic structure — demoted from spine (old § 3) to appendix; § 4.4 replaces the old per-capability BR/DEC placement with the three-bin rule (below) |
| Business Rules / Decision outcomes / State-machine purpose (one line each) | `functional-spec.md` § 5 | BR-###/DEC-###/SM-### code as trailing tag; a recorded DEFECT never goes here — see § 11 |
| Business Rules — Bin 1 (used by exactly one action) | `technical-spec.md` § 3, inline in that action's **Rule** rung | Full statement + `**Source:**`, no separate heading — the rung already owns this fact |
| Business Rules — Bin 2 (used by ≥2 named actions) | `technical-spec.md` § 4.4, bold paragraph under `#### Bin 2` | Full block (Source + pseudocode) lives HERE once; each using action's Rule rung ALSO carries the plain-language gloss inline — never a bare code with only a `Used in:` pointer (see "Self-sufficiency of the H4 context line" below) |
| Business Rules — Bin 3 (cross-cutting, no action list) | `technical-spec.md` § 4.4, bold paragraph under `#### Bin 3` | Claimed by the `A0` row in § 2; MUST carry an explicit cross-cutting label |
| Decision Logic (DEC-###) | `technical-spec.md` § 3, table row inline in the gating action's **Rule** rung | Fixed columns `DEC \| subtype \| Condition \| What the user sees \| Source` — NOT a separate H4 block (that was the pre-thread shape) |
| Polymorphic Behavior | `technical-spec.md` § 4.2 Data Model → `#### Polymorphic Behavior` | DISC-### tables |
| Screens (screen list + user journey) | `functional-spec.md` § 6 | SCR### column bridges to screen-list.md |
| User Stories (Actor → Goal → Business value narrative + observable AC) | `functional-spec.md` § 7 | Per-feature elaboration — see disambiguation note below |
| Action Index row for the same US### | `technical-spec.md` § 2 | Reference row only — the action(s) that implement this story, NEVER the narrative or its AC |
| Scenarios (Given/When/Then) | `functional-spec.md` § 8 | Happy path + ≥1 error scenario per US### |
| Edge Cases (plain-language table) | `functional-spec.md` § 9 | Min 3 UI / 1 background |
| Edge Cases (technical trace — status/error code) | `technical-spec.md` § 3, final `### 3.{N+1} Edge cases` table (feature-wide, Action column leading) | Same scenarios as § 9, 1:1, technical detail only — no longer per-capability (the Action column IS the anchor now) |
| Edge Behaviours to Verify | `functional-spec.md` § 10 | Plain-language equivalent of `technical-spec.md § 5.1`'s SC-###; back-refs FR-### |
| Risks & Known Issues (abnormal current behavior, never self-fixed) | `functional-spec.md` § 11 | See the three-way split below |
| Dependencies (feature / external-service / data / infrastructure / config) | `functional-spec.md` § 12 | Plain-language counterpart to `technical-spec.md § 4`'s integrations |
| Configuration (business-visible constants) | `functional-spec.md` § 13 | One fenced block; no secrets |
| Configuration (technical: env vars, flags, timeouts) | `technical-spec.md` § 4.6 | Different boundary from § 13 — a developer, not a stakeholder, changes these |
| Components | `technical-spec.md` § 4.1 | Carries a `Used in` column (action IDs) — new in the action-thread reshape |
| Key Entities | `technical-spec.md` § 4.2 Data Model | Table refs |
| API & Endpoints | *(retired as a standalone subsection)* | Folded into `technical-spec.md` § 2 Action Index's `Method · Path` column — no separate `### API & Endpoints` H3 in the new shape |
| Technical Verification (global SC-### + per-US Independent Test/Acceptance Scenarios) | `technical-spec.md` § 5.1 | Unchanged by this reshape |
| Assumptions | `technical-spec.md` § 5.2 | Tech assumptions |
| Unresolved Questions | `technical-spec.md` § 5.3 (implementation-detail unknowns) + `functional-spec.md` § 3 (domain/business unknowns) | Split by class — see Domain-Confirmation Promotion |
| Source References | `technical-spec.md` § 5.4 | Path:line, Action column LEADING (no consumer parses by position); NEVER copy to `functional-spec.md` |
| Artifact References | `technical-spec.md` § 5.5 | Code lists, updated paths to the layered structure |
| Source Walkthrough (A3, v26.0.0, UNCHANGED by the action-thread reshape) | `technical-spec.md`, unnumbered H2 after § 5 | Reading order; recasts `### 5.4 Source References` (adds Order column) — do NOT author a second file-list table. No separate Call Hierarchy diagram — each action's own **Source** rung in § 3 already owns its call chain |
| DB Impact per Event (B4, v26.0.0, UNCHANGED shape, Action column now LEADING) | `technical-spec.md`, unnumbered H2 after Source Walkthrough | One row per DB-writing action/event; NEVER copied to `functional-spec.md` § 6 (screens stay UI-scoped) |

### Disambiguation — "User Stories" names three things

Do not confuse these three artifacts sharing the name "User Stories":

1. `docs/generated/user-stories.md` — the project-wide US### inventory. WHAT stories exist.
2. `functional-spec.md` § 7 — the per-feature Actor → Goal → Business value narrative +
   observable acceptance-criteria checkboxes for THIS feature's US### codes, for a BA/QA reader.
   HOW the story plays out here.
3. `technical-spec.md` § 2 Action Index — the dev-facing reference row (Action/handler, Method ·
   Path, tables written) behind the SAME US### code, via that code's presence in the row's
   `Codes` column. **Not a narrative — a reference row only.** Per-US `**Independent Test:**` and
   technical Given/When/Then live in `technical-spec.md` § 5.1 instead, and MAY carry
   status/response detail the BA-facing § 8 Scenarios does not — that is not a restatement, it is
   additional dev-facing detail.

State this in both output files (see per-file rules below) so a reader never has to reconstruct
the distinction themselves.

## New Functional Sections — Authoring Rules (v27.x)

### § 2 Functional Capabilities

Derive `CAP-###` rows from `## 4. Requirements` groupings: cluster the FR-### band(s) that serve
one coherent user-facing capability (usually one screen's worth of a related action, or one
cross-screen interaction band) into a single `CAP-###` row. `Requirements` cites the
comma-separated FR-### codes that make up the capability; every code cited MUST also appear in
§ 4 (`func.capability_fr_dangling` is CRITICAL on a phantom cite). `Screens` cites the `SCR###`
codes from § 6 that surface this capability. This section is not optional bookkeeping — it is
the source of truth `technical-spec.md § 3`'s `### 3.N` buckets group against; an empty § 2 while
§ 4 already lists real FRs (`func.capabilities_empty`, warning) forces `technical-spec.md` to
fall back to one undifferentiated `### 3.1 {Feature name}` bucket instead of a real capability
split.

`User Stories` cites the comma-separated `US###` codes from § 7 that this capability fulfills.
`Business Rules` cites the comma-separated `BR-###`/`DEC-###`/`SM-###` tags from § 5 that govern
this capability.

**Exhaustiveness rule (stated here once — every other document cites this paragraph by pointer,
never restates it):** assign every `US###` declared in § 7, every `FR-###` declared in § 4, every
`BR-###`/`DEC-###`/`SM-###` tag declared in § 5, and every `SCR###` declared in § 6 to **exactly
one** § 2 row. A code claimed by zero rows is `cap.code_unclaimed` (critical, message opens with
`family=US|BR|FR|SCR`); a code claimed by two or more rows is `cap.double_claimed` (critical).
Every cell must name at least one real code, never leave a `{...}` placeholder or a bare `—`
unfilled — **except** the one whole-file, all-or-nothing case where § 2 has rows but EVERY row's
claim cells are empty (the structural window right after `--migrate --only cap-map` widens the
table, before anyone has filled it in): that state is `cap.claims_unfilled` (warning) instead,
and it suppresses `cap.code_unclaimed`/`cap.double_claimed` for the whole file until at least one
row is filled. A single empty cell on an otherwise-populated table is never muted this way — it
is a live `cap.code_unclaimed`.

**Region caveat (SCR only):** "exactly one" is scoped to the composite token, not the bare screen.
`SCR161/REG002` and `SCR161/REG005` are DISTINCT claims — two capabilities each owning a different
region of the same screen is not a double-claim (`cap.double_claimed` reads exact tokens). A bare
`SCR161` declared in § 6 is satisfied by any claim on that screen, composite or bare
(`cap.code_unclaimed` reads the parent-expanded view). See `code-formats.md` § Composite cross-ref
parsing for the token grammar.

**Intent rule (what makes a row its own `CAP-###` vs. a variation of an existing one):** a
semantic judgment, not a wording check — see `references/code-formats.md` § "Capability-Level
Intent (authority)" for the full rule; it is not restated here.

**When a rationale is required (phase 06, capability-map plan; D-7: the count never forces a
split, only a written decision):** once § 2 has real claims and `#CAP == 1`, this feature's own
US###/BL### count is checked against its Type's band — `ui` on distinct `US###` in § 7 (warn 3-4,
critical ≥5), `background` on distinct `BL###` in the twin `technical-spec.md` (warn 5-7, critical
≥8), `mixed` on the stricter of both. `#CAP ≥ 2` silences this entirely — declaring a second
capability is always an option, never a requirement forced by the count. In the warning band,
nothing further is required (`cap.review_advised`, a nudge). At or over the critical band, this
single CAP-### row needs a `**Single-capability rationale:**` line — same line as the label,
non-empty — satisfying all THREE conditions, or `cap.analysis_required` (critical) fires:

1. non-empty text on the same line as the label;
2. ≥ 12 words;
3. names ≥ 2 DISTINCT `US###`/`BL###` codes THIS feature actually declares elsewhere in this
   file — citing the same code twice, or a code this feature never declares, both fail this
   condition (a fabricated code is not merely ignored, it fails the check).

All three are checked deterministically, never by an LLM judgment call — write the rationale as a
real sentence naming the stories/jobs actually grouped, not a stock phrase; a short or generic
line will not pass condition 2 or 3 even if it is technically present.

### § 11 Risks & Known Issues

One `RISK-###` row per abnormal CURRENT behavior found in code (`Type: known-issue`) or per
foreseeable future exposure (`Type: risk`). Record the behavior AS OBSERVED — never editorialize
a fix, never soften it into a Business Rule line. `Status` uses the marker vocabulary below.
`N/A — none found.` is valid only after actually scanning for defects, not as a default. A § 5
Business Rules line that reads like an observed defect ("should not", "incorrectly", "bug") with
no corresponding § 11 row is exactly what `func.risk_as_rule` (warning) exists to catch.

### § 12 Dependencies

One row per thing this feature needs from elsewhere to function: another feature (`F###`), an
external service, a shared dataset, infrastructure, or a config value. This is the
plain-language counterpart to whatever `technical-spec.md § 3`'s Integrations subsection (§ 3.6)
cites — a BA/QA reader should be able to see "what else has to be true" without following that
link. `N/A — none found.` when the feature has zero cross-feature or external dependencies.

## New Technical Sections — Authoring Rules (v27.7.0 action-thread)

**Normative source:** `plans/260824-1128-rebuild-spec-action-thread-v27-7/wire-format-contract.md`
— read it in full before drafting `technical-spec.md`. Where this section and that file disagree,
the wire-format contract wins; treat this section as a summary with the authoring judgment calls
added, not a restatement of its tables.

### Why action-first: the corpus finding, not a taste

The prior layer-first shape had **no action→rule binding**. Measured on a 43-feature/430-action
corpus: the old `**Applies to:**` free-text field resolved to a specific action only **26%** of
the time (93/359); **84% of actions had no rule attributable to them at all**. `## 2. Action
Index` is the fix — a table where every FR/BR/DEC/SM/US code MUST be claimed by **at least one**
row (or by `A0`), checked mechanically (`action_unclaimed`), not left to a free-text field a human
might or might not fill in usefully. This is a completeness requirement, not an exclusivity one:
one requirement fanning out to several handling actions (e.g. a request/poll/generate triple) is
the normal shape, not a violation — see `docs/decisions/ADR-0006.md`'s addendum for the corpus
measurement behind that correction and the retired `action_double_claimed` check.

### D2 — the handler IS the action's identity

Key the `Action (handler)` column on `` `Class#method` ``, never on `METHOD PATH` alone: the same
path can back two different actions (e.g. two member routes sharing `/:id`), and a background
action (queue/job/cron) has no HTTP path at all. Fall back to the bare `` `METHOD PATH` `` shape
**only** when the handler is genuinely unparseable — that fallback fires
`action_key_not_handler` (warning), a signal for a re-read, not a shortcut to reach for.

### The rung set, and the FACTS-vs-ORDER split

Fixed order, `_spec_constants.RUNG_LABELS` (8 rungs, self-sufficiency v27.8 — `State` joins as the
8th, between Result and Source):

> **Who** → **FE** → **Request** → **BE** → **Rule** → **Result** → **State** → **Source**

`**State** · \`SM-###\`: \`{from_state}\` → \`{to_state}\` *(§ 4.3)*` — same ` · ` separator as
every rung except Source. `[UNVERIFIED]` variant: `**State** · [UNVERIFIED] \`SM-###\`: transition
not confirmed from source *(§ 4.3)*`. State is authored ONLY by a researcher fill pass reading the
real source — there is no automatic derivation from mermaid edge labels (that join was measured
and dropped: it resolved only 2 of 16 real `stateDiagram-v2` blocks on the corpus). Where the
transition cannot be resolved, the rung is **omitted entirely**, same as any other rung — never
rendered as `N/A` or `None.` (`rung_empty_rendered`); `FeatureSpec.state_rung_missing` (warning)
flags a writing action inside an SM-modelled feature that renders no `**State**` rung at all, as a
signal for the fill pass, never as a demand to guess one.

An absent rung is **omitted entirely** — never `N/A`, never `None.` (`rung_empty_rendered`).
Presence of any given rung is never required; the RELATIVE ORDER of whichever rungs a block does
carry is the contract (`rung_order`).

**A rung carries FACTS; a diagram carries ORDER and BRANCHING.** This is not a stylistic
preference — it is how the two are kept from becoming two records of one truth that can drift
apart. A rung states the endpoint, the handler, the table, the `file:line`. A `sequenceDiagram`
states the sequence of calls and which branch does what. Concretely: **never put `file:line`
inside a mermaid fence** (`diagram_cites_file_line`) — a diagram that also cites `file:line` is
narrating the same fact twice, and the two copies will eventually disagree. A rung must not
narrate sequence either — "first X happens, then Y" belongs in the diagram once the action
crosses the diagram threshold; below threshold, plain rung prose already tells the story linearly
because there is only one path through it.

**The Source rung's citation form — get this wrong and A1 citation coverage silently drops
project-wide.** Every other rung uses ` · ` (middot) after its bold label. The Source rung does
**not** — it is the ONE rung with no middot separator, because `derive_confidence_report.py:29`'s
`CITATION_RE` needs the colon **inside** the bold markup, then plain whitespace, then the first
backticked `path:line`:

```
**Source:** `index.haml:1-29` → `manage_listings_controller.rb:5` → `list_presenter.rb:1-142`
```

Measured against the real regex: `**Code** · \`file:line\`` (a plausible-looking label choice) —
**0 matches**. `**Source** · \`file:line\`` (middot kept, label fixed) — **0 matches**.
`**Source:** · \`file:line\`` (colon added, middot ALSO kept) — **0 matches**. Only
`**Source:** \`file:line\`` (colon inside the bold, single space, no middot) matches. The middot
is fatal: the regex's `\s+` stops at it, and its character class cannot cross the following
backtick to reach the colon inside `path:line`. **Do not "fix" this rung to look consistent with
the other six — that consistency is exactly what breaks it**, and it breaks silently: nothing
errors, the citation is simply never counted, corpus-wide, with no signal that anything went
wrong. This is the same silent-failure family this repo keeps hitting; it is called out here so
an author who reaches for consistency does not reintroduce it.

### The three-bin rule for shared rules (§ 4.4)

A rule's placement is decided by **how many named actions use it**, counted, never by judgment:

- **Bin 1 — used by exactly ONE action.** Lives INLINE in that action's `**Rule**` rung, full
  statement + `**Source:**` + optional pseudocode. Not duplicated anywhere else.
- **Bin 2 — used by ≥2 named actions.** Full block (statement + `**Source:**` + pseudocode) lives
  ONCE in § 4.4 under `#### Bin 2`, tagged `Used in: A2, A3, ...` — the citation and pseudocode
  live here and only here, never a second copy. Each using action's Rule rung ALSO carries the
  plain-language gloss inline (the one-sentence statement + mechanism) — see "Self-sufficiency of
  the H4 context line" below for why a bare code with no inline gloss is a defect even when § 4.4
  fully defines it.
- **Bin 3 — genuinely cross-cutting, claimed by no single action's list.** Lives in § 4.4 under
  `#### Bin 3`, claimed by the `A0` row in § 2, and MUST carry an explicit cross-cutting label
  (`crosscutting_unlabelled` fires on a Bin-3 entry with no such label) — a rule that applies to
  "every route" or "the whole controller" is not the same statement as a rule that applies to one
  named action, and the label is what tells a reader which kind they are looking at.

**Why Bin 3 exists as a THIRD bin, not folded into Bin 2:** on the corpus this reshape was
measured against, a meaningful share of rules belong to no single action at all (an
`ensure_is_admin`-style gate on an entire controller, not any one screen). Without a dedicated
bin, that class of rule gets stuffed into whichever action happens to need a home for it, which
corrupts the exact binding § 2 exists to create — a rule now reads as belonging to one action when
it actually gates all of them.

**Never guess a rule's owner.** When the composer (or a researcher migrating an older spec)
cannot resolve which bin a carried-forward rule belongs in, it keeps its original text and is
marked `[UNVERIFIED] carried from **Applies to:** — needs a researcher pass`. Do not force it into
a bin on a guess; a wrong bin assignment is worse than an explicit unresolved marker, because the
wrong assignment reads as confirmed.

### Self-sufficiency of the H4 context line (`action_ref_unglossed`)

The three-bin rule above governs WHERE a code's full definition lives. It does not, by itself,
say anything about whether the block that CITES the code is readable on its own — and that gap is
where the corpus's real defects sat (phase 00 measurement, self-sufficiency v27.8): a code bare in
the `#### A<n>` heading line with no gloss anywhere else in the block. This clause is additive to
the bin rule, not a replacement for it:

> Every code in the H4 context line MUST be glossed — a plain-language clause, anywhere in the
> same action block — before the file is considered fill-complete. A code that appears ONLY in
> the context line, with no gloss anywhere else in the block, is the self-sufficiency defect this
> rule exists to prevent. The Bin-2/3 "short reference line" (`Used in:` / cross-cutting tag)
> does **not** satisfy it: that pointer points OUT of the block; the gloss stays IN it.
> Enforced by `FeatureSpec.action_ref_unglossed` (warning).

Concretely for BR: a Bin 2/3 rule's full statement + `**Source:**` + pseudocode lives once in
§ 4.4 (unchanged by this clause) — but every action's own Rule rung that cites it ALSO carries the
plain-language gloss inline (the one-sentence statement + mechanism, the same content the A2
worked example above shows), never a bare `BR-001` with only a `Used in:`/cross-cutting pointer.
The same applies to a DEC table cell, an SM/ALG/INT `**Used in:**` back-reference, and a DISC
cross-reference — six families total (BR/DEC/SM/ALG/INT/DISC; FR/US are out of scope for this
check, matching the measurement's own scope). Six other files in this doc surface teach pieces of
this shape; this paragraph is the ONE canonical statement — they point here, they do not restate
it.

**The § 3 side points with `*(§ 4.4)*` — never with a `Used in:` list.** A `Used in:` marker naming
≥2 actions IS the Bin-2 marker, and `FeatureSpec.rule_bin_misplaced` (warning) fires wherever one
sits inside § 3. The action list belongs once, in § 4.4, beside the full statement it labels;
duplicating it into § 3 says nothing § 2's `Codes` column and § 4.4's own list do not already say.
So the § 3 Rule rung carries **gloss + `*(§ 4.4)*`**, the same plain section pointer every other
cross-section reference in the file uses (`*(§ 4.3)*`, `*(§ 4.5)*`). v27.14.3 removed the one
counter-example — the template's own worked example had invented a `Used in: … → § 4.4` hybrid that
fired this warning on every file copied from it.

### Decision Logic (DEC-###) — a table row, not a block

Under the action-thread reshape, `DEC-###` renders as a row in a table INLINE in the gating
action's `**Rule**` rung — it is no longer a standalone `#### {sentence} (DEC-001)` H4 block with
its own `**subtype:**`/`**Triggers in:**`/`**Involved entities:**` field set. Fixed columns:

```
| DEC | subtype | Condition | What the user sees | Source |
|---|---|---|---|---|
| **DEC-001** | render | `admin_mode` AND `state == 'approval_pending'` | shows Approve + Reject | `_actions.haml:4-16` |
```

`subtype` keeps the same vocabulary as before (`render`/`interaction`/`flow`, ≥1, comma-separated
if multiple — see § Decision Logic Extraction below for the full subtype signatures, unchanged by
this reshape). `Condition` replaces the old separate pseudocode fence — state the predicate
directly in the cell; reach for a fenced block only when the branching genuinely will not fit in
one cell (rare — most DEC rows are single-predicate or two-predicate). `Source` is the same
`file:line` discipline as every other citation. The 1-sentence business-outcome justification
still lives in `functional-spec.md` § 5 as this DEC-###'s one-liner — unchanged by this reshape.

### The diagram contract

An action's block gains a `sequenceDiagram` when it satisfies **≥1** of:

- **writes ≥2 tables** (from the § 2 `Writes` column), or
- **is a background/async-step action** (queue/job/cron, or a multi-handler thread like
  request → background job → poll endpoint).

A third criterion — **≥2 BR/DEC on the action** — is **deliberately deferred**, not rejected: it
measured a 4.4% base rate on the corpus this reshape was built against, too thin to justify adding
it before the action→rule binding itself has run on a real corpus. Do not add it back from
intuition; re-derive it from measurement once § 2 has been exercised at scale (see
`docs/decisions/ADR-0006.md`).

**Cap: ≤12 arrows, ≤2 `alt` blocks.** Going over the cap is a signal the ACTION is too big, not
that the diagram needs to be denser — split the action (or, for a multi-handler capability thread
like an export-and-poll flow, place ONE diagram at the capability level covering all the
handlers involved, rather than one bloated diagram per handler).

**Never cite `file:line` inside a mermaid fence** (`diagram_cites_file_line`) — see the
FACTS-vs-ORDER split above. A diagram participant/note may name a class, method, or table; it may
not carry a line-range citation, because that citation already lives in a rung and a second copy
is a second thing that can go stale.

**When NOT to add a diagram even above threshold:** an action whose real content is a branching
TABLE (e.g. 3 render conditions gating what a user sees) reads WORSE as a sequence diagram than as
the table itself — a diagram forces a table's parallel conditions into a false sequence. Use
judgment; state briefly in an HTML comment why a diagram was skipped if the action is otherwise
above threshold, so a reviewer does not read the omission as an oversight.

**Ordering note — do not clear `[UNVERIFIED]` markers without also drawing what is now due.**
`FeatureSpec.diagram_required_missing` degrades to `warning` while the file still carries the
`[UNVERIFIED]` tag (`_action_thread_diagram_lib.is_fill_pending` — see
`references/verification-checklist-feature-spec.md`'s third degradation window). That window
exists for the freshly-composed, not-yet-touched file, not as slack for a partial pass: resolving
every `[UNVERIFIED]` marker without drawing every diagram an over-threshold action now requires
turns the SAME finding back into a hard `critical` the moment the marker count reaches 0. Treat
rule-ownership resolution and diagram authoring as one pass, not two — clearing the last marker
should be the last thing done for a feature, after every required diagram is already in place.

## Status Marker Vocabulary (D6)

Canonical home: `references/confidence-report-contract.md` § "v27 amendment — the 4th state" —
read the definitions there, do not re-derive them here. Four markers total: `[UNVERIFIED]`,
`[INFERRED]`, `[NEEDS_DOMAIN_CONFIRMATION]` (unchanged), plus `[EXPECTED]` (new — desired/agreed
behavior that is not implemented, or not confirmable in code; an accessibility recommendation is
the canonical example). All four are now PERMITTED in `functional-spec.md` — previously excluded
by design. That is the ONLY relaxation to the Forbidden Tokens rule below.

`[EXPECTED]` MUST NEVER trigger the Domain-Confirmation Promotion below — only
`[NEEDS_DOMAIN_CONFIRMATION]` promotes to an Open Decisions row. An agreed/desired behavior is
already a recorded decision, not an open question a stakeholder still has to answer.

**The hard rule (quote verbatim if a reviewer asks why an observed bug reads as plain prose
instead of being fixed in the spec):**

> Never promote an observed current behavior into a SHOULD. If code does X and X looks wrong,
> write X, mark it, and open a § 11 Risks & Known Issues row. Do not invent, do not fix, do not
> delete as "merely technical".

## Three-Way Decision Procedure (Open Decisions / Unresolved Questions / Risks & Known Issues)

Every unresolved item found while researching belongs in exactly ONE of three buckets. Use this
test, in order:

1. **Needs a stakeholder / business / product / security answer** → `functional-spec.md` § 3
   Open Decisions. Every `[NEEDS_DOMAIN_CONFIRMATION]` marker discovered while researching this
   feature MUST be promoted into a row here — never left as an inline marker in either output
   file. Each row requires:
   - **Decision** — the open question, one sentence.
   - **Default proposal** — what ships if nobody answers before promotion.
   - **Rationale** — why that default, one sentence.
   - **Blocks work** — `yes` if the feature cannot ship correctly without an answer, `no` if it
     can ship with the default and be revisited.
2. **Needs more code reading, no business ambiguity** → `technical-spec.md` § 5.3 Unresolved
   Questions. An implementation-detail unknown ("could not confirm whether this queue retries on
   failure") stays here, never an Open Decisions row.
3. **Is abnormal CURRENT behavior, observed and recorded as-is** → `functional-spec.md` § 11
   Risks & Known Issues. Never invented, never fixed, never deleted as "merely technical" — see
   the hard rule above.

The test for (1) vs (2): does answering this need a stakeholder/domain decision, or just more
code reading? The test for (3): is this something the code actually does today that looks wrong,
as opposed to something nobody has verified yet (that is (2)) or a business question nobody has
answered yet (that is (1))?

## Forbidden Tokens (functional-spec.md only)

See the HTML-commented block at the top of `templates/functional-spec-template.md`. The forbidden
class is **dev tokens** (class names, `file:line` citations, HTTP verbs, pseudocode outside
fences) **plus secret shapes** (H-SEC4) — content that was safe only because it sat in a fenced
`technical-spec.md` block (DSN strings, `API_KEY=` values in a `Source` excerpt) has a legitimate
reason to sit beside BA prose in the widest-audience file in the repo, so both scrubbers gate it:
`scrub_generic_secret` and `scrub_credentials`. This is the **inversion** of the old
business-context.md rule, which forbade FR/BR/SM codes — those codes now canonically live in
`functional-spec.md` and are expected, not forbidden. The 4 status markers (§ above) are the one
addition to what is now permitted here.

Self-check the forbidden-token regex against drafted prose BEFORE writing. Any match outside a
fenced code block or HTML comment = CRITICAL; rewrite in plain language and move the technical
detail to `technical-spec.md`.

**Known limitation, recorded honestly (do not paper over it):** `FUNC_DEV_TOKEN_RE` only catches
HTTP verbs and a `path.ext:123` file:line shape. It does **not** catch bare class, job, or mailer
names — `SessionsController`, `Devise`, `PasswordResetJob` all read past the regex untouched. A
bigger regex is not the fix (it would false-positive on ordinary CamelCase business nouns like
`OrderSummary` or `ShopManager`); this stays a reviewer judgment call —
`func.dev_identifier_leak` below.

**`func.dev_identifier_leak` (reviewer rule, not automated):** flag a bare internal
class/service/job/mailer name in `functional-spec.md` prose outside a fence, even though
`FUNC_DEV_TOKEN_RE` will not catch it mechanically. Worked examples:
- ❌ "`SessionsController` validates the session before rendering the dashboard." — internal
  class name leaking into BA prose.
- ❌ "A `PasswordResetJob` runs in the background to send the reset email." — job class name.
- ❌ "`Devise` handles the authentication flow." — third-party library name, still an internal
  implementation detail to a BA reader.
- ✅ "The system checks the session is still valid before showing the dashboard." — same fact,
  no internal name.
- ✅ "A background job sends the password-reset email." — the mechanism (background job) is
  user-relevant; the class name is not.
This is a security-relevant guard, not merely a style rule: it is the one thing standing between
internal class/host names and a BA-facing document that may be exported to clients.

Cross-references to `flows/` ARE ALLOWED: "This feature is part of [Name] — see `flows/{slug}.md`".

## Source Citations

`**Source:** path:line-start-end` MUST appear ONLY in `technical-spec.md`.
Citation validator (FS.2) only scans `technical-spec.md`; a source citation in `functional-spec.md`
= CRITICAL contract violation.

## Mandatory Source-Code Reading

- MUST read actual source code files (controllers, models, jobs, services, Vue/React pages) for every feature — NOT just summarize from upstream artifacts.
- Use Grep/Read tools to find real controllers, models, jobs, routes for this F###.
- Extract specifically: file paths with line ranges, method names, table/column names, HTTP status codes for error cases, job class names, event names.
- If a file cannot be read, note it under `technical-spec.md § 5.3 Unresolved Questions`.

## Discriminator Coverage (CRITICAL)

After identifying Key Entities, MUST check `entities.md` for discriminator fields:

1. For each entity in `technical-spec.md § 4.2 Data Model`'s entity table, read its `**Discriminator Fields**` block in `entities.md`.
2. If ANY entity has DISC-### entries → MUST write `#### Polymorphic Behavior` under `### 4.2 Data Model` in `technical-spec.md`, with one subsection per DISC-### (v27.7.0: `### 4.2 Data Model` replaces the pre-thread `### 3.2 Data Model` — no separate `#### Key Entities` wrapper heading; the entity table sits directly under `### 4.2`, same as the B-v sample).
3. Cover ALL values listed in `entities.md`. Missing a known value = CRITICAL reviewer rejection.
4. Include ≥1 edge case per variant in `functional-spec.md` § 9 Edge Cases.
5. Each behavior cell MUST be grounded in source code. Write `unverified` if not confirmable — do not leave blank or fabricate.

**N/A fallback** — only valid when Key Entities have zero DISC-### in `entities.md`:
`N/A — no discriminator fields in Key Entities.`

**`#### Polymorphic Behavior` is ALWAYS present under `### 4.2 Data Model` in `technical-spec.md`.** Omitting it = CRITICAL.

#### SM `kind` Classification

For every extracted SM-###, set `**kind:**` as the first metadata line after the heading (in `technical-spec.md § 3.3 State Management`):
- **`entity`** — state field is persisted (DB column, ORM attribute, model field, type in `entities.md`).
- **`ui`** — state is component-local (useState, ref, computed, signal — NOT persisted beyond render cycle).
- If same concept has both, document as 2 separate SM-### blocks.
- **Threshold:** only classify `kind: ui` for state machines with ≥3 states OR ≥2 transitions.

## Decision Logic Extraction (DEC-###)

DEC-### captures decisions with **user-visible business outcome** — regardless of which file the
code lives in. Component files, saga files, controller files, route guards — all valid Sources if
the decision changes what the user sees, does, or where they go.

### Scope

Scope is **outcome-based, source-location-agnostic**. Ask: "Does this decision change what the
user sees, does, or where they go?" If yes → DEC candidate. If no → skip.

### Subtype Signatures

**render — multi-predicate render branches:**
- JSX/template trees with conditional rendering involving ≥2 predicates OR non-single-field predicates
- Signature: `{(condA && condB) ? <A/> : <B/>}`, `v-if="condA && condB"`, computed render props using ≥2 entity fields, switch statement rendering different components
- SKIP single-field conditions — those go to DISC (enum or boolean)
- SKIP cosmetic toggles (class names, padding, color only)

**interaction — event handlers with visible business meaning:**
- Event handlers (`onClick`, `onChange`, `onSelect`, `onKeyDown`) where body reveals/hides substantive UI, focuses a new input, or shows/hides meaningful sections
- SKIP form-field two-way binding (input value mirrors state only)
- SKIP loading spinner reveals (`isLoading ? <Spinner/> : ...`)
- SKIP error toast displays (those are error-handling, separate section)

**flow — multi-step / navigation / step routing:**
- Functions/handlers advancing user position in a flow: `setStep(...)`, `next()`, `history.push(...)`, `router.push(...)`, `redirect(...)`, conditional rendering of next/previous wizard page
- In-feature scope: stays within feature (multi-step wizard advance, sub-screen routing, post-action navigation)
- SKIP cross-feature navigation — that is screen-flow.md territory
- SKIP error redirects to global error pages — that is error-handling territory

### Anti-examples (skip these — they are plumbing)

```pseudo
❌ if isLoading → show spinner          (loading toggle — not decision)
❌ if api.success → dispatch SUCCESS    (dispatch wrapper — not decision)
❌ if !error → show data                (presence check — not branching)
❌ if token expired → refresh token     (fetch mechanic — not user-facing)
❌ if response.status === 200 → ...     (HTTP plumbing)
❌ if user.locale === 'en' → load 'en'  (i18n routing — not business)
❌ debounce(handler, 300)               (timing wrapper)
❌ if cache hit → return cached         (cache mechanic)
```

If uncertain, ask: **"Does this affect what the user SEES, DOES, or WHERE they go?"** If no → skip.

### DISC vs DEC boundary

- Single-field condition with **enum type** (≥2 named values with distinct behavioral outcomes) → **DISC**
- Boolean flag (`is_published: boolean`, `is_active: boolean`) → **Business Rule** or FR note, NOT DISC
- ≥2 predicates OR interaction-driven OR flow-step routing → **DEC**

Examples:
- `if question.type === 'multiple choice' → render MultipleChoice` → DISC (single enum field)
- `if survey.published === true → show banner` → Business Rule (single boolean, no DISC code needed)
- `order.status` enum with values `pending / shipped / cancelled` each affecting UI → DISC (enum ≥2 values)
- `user.is_admin === true → show admin panel` → DEC-interaction or Business Rule depending on complexity; NOT DISC
- `if user.role === 'admin' AND survey.published_at !== null → show MetricsPanel` → DEC (multi-predicate render)
- `on option select: if option.is_other_option → reveal CommentInput` → DEC (interaction reveal)
- `on submit success: if survey.type === 'mbti' → push('/result')` → this is single-field but it's a navigation flow decision — DEC-flow (navigation post-action with meaningful routing)

`N/A — no discriminator fields in Key Entities.` is valid when Key Entities have zero DISC-### entries in `entities.md`. Boolean fields are NOT DISC-### — their absence from Polymorphic Behavior is correct.

### Multi-subtype guidance

If a decision spans ≥2 dimensions (e.g. a Submit button that both validates form AND advances wizard), declare `subtype: render, flow`. The pseudocode block captures both dimensions together.

### Required output fields per DEC (technical-spec.md § 3, table row inline in the gating action's Rule rung)

**v27.7.0 (action-thread reshape):** DEC-### is a TABLE ROW, not a standalone H4 block — see
"New Technical Sections — Authoring Rules" above for the full rationale. Fixed columns:

```
| DEC | subtype | Condition | What the user sees | Source |
```

- `DEC` — the code, bold (`**DEC-001**`)
- `subtype` — ≥1, comma-separated: `render`, `interaction`, `flow`
- `Condition` — the predicate, stated directly in the cell (state it in prose/code-span form; a
  fenced pseudocode block is only needed when the branching genuinely will not fit in one cell)
- `What the user sees` — the observable outcome of each branch
- `Source` — `` `file/path.js:start-end` `` (read the actual line range; source location NOT
  validated — saga/component/controller all valid)

`**Triggers in:**` (screen + event) and `**Involved entities:**` (entity.field driving the
branch) are folded into the action block's own `**Who**`/`**FE**`/`**BE**` rungs above the table
— they are facts about the ACTION, not a separate field set repeated per DEC row.

The 1-sentence business-outcome justification (`**user_visible_outcome:**` in the pre-thread
shape) lives in `functional-spec.md` § 5 Business Rules as this DEC-###'s one-line entry — write
it there, not here.

### N/A fallback rule

`N/A — no user-facing decision logic beyond DISC-### Polymorphic Behavior.` is ONLY valid if the
feature has **zero** non-plumbing user-facing branches AND no multi-predicate / interaction / flow
decisions. Researcher MUST scan all source files implicated by the feature before writing N/A. If
component files contain JSX ternaries with ≥2 predicates, N/A is invalid.

### Client-Side Logic Extraction (→ behavior-logic.md § Client-Side Logic)

Scan for these 5 patterns in client/frontend source files. For each found, add an entry to the `## Client-Side Logic` section of `behavior-logic.md`:

**Debounce / Throttle**
Signature: `setTimeout`/`clearTimeout` wrapping a handler, `debounce(fn, ms)`, `throttle(fn, ms)`, `useDebounce`, `useDebouncedCallback`
Capture: trigger location (file:line), delay value, what action is debounced.

**Optimistic UI**
Signature: state mutation applied before `await`, with a catch/rollback block; `useOptimistic`, `optimisticUpdate`
Capture: trigger (user action), optimistic state change, rollback target, API endpoint.

**Polling**
Signature: `setInterval` calling an API, recursive `setTimeout` + API call, `refetchInterval`, `usePolling`
Capture: interval duration, condition to stop polling, API called.

**Upload Progress**
Signature: `XHR.upload.onprogress`, `axios onUploadProgress`, `fetch` with streaming body, `useUpload`, `onProgress`
Capture: trigger action, progress state field name, error path.

**Realtime**
Signature: `new WebSocket(...)`, `new EventSource(...)`, `useWebSocket`, ActionCable subscribe, Pusher subscribe, SSE listener
Capture: channel/URL pattern, trigger (mount/user action), reconnect strategy, teardown (unmount handler).

If a pattern is absent in the entire codebase, write `N/A — no {pattern} patterns detected.` in the corresponding subsection.

### Client-Side Gate Extraction (→ permissions.md)

Scan for runtime gates that affect UI rendering. Use these function-name signatures — do NOT hard-code library names:

**feature-flag:** `useFlag|useFeature|isEnabled|featureFlag\(|checkFlag` — capture first string argument (flag name), file:line, effect (what branch differs).

**experiment:** `useExperiment|getVariant|abTest\(|experiment\.variant|useAbTest` — capture experiment name, variant identifiers found in code.

**env-gate:** comparison against `process\.env\.|import\.meta\.env\.|ENV\[|os\.environ\[` followed by `===`/`==`/`in (...)` — capture env var name, compared value, effect.

**locale-gate:** comparison against `i18n\.locale|currentLocale|getLocale\(\)|locale\s*===|lang\s*===` — capture locale value, effect.

Name-only rule: capture the flag/experiment name found in source. Do NOT look up the flag's configuration in LaunchDarkly, Statsig, or any external service.
If none found: write `N/A — no {type} gates detected.` for each absent type.

### Screen-Flow Client-Side Extraction (→ screen-flow.md)

**Guard Logic**
Signature: function/method definitions tied to route entry: `beforeEnter|canActivate|middleware|loader|before_action|authenticate|authorize` — check if registered in router config or route annotation.
For each guard: record GUARD-### id, trigger hook name, source file:line, pseudocode logic (if/redirect chains), failure path.
N/A rule: only write `N/A — no route guards detected.` after confirming no route-level interception exists (check router config files, not just component code).

**Deep-Link State Restoration**
Signature: URL param reads at component mount → state sync: `useSearchParams|useQuery|router\.query|URLSearchParams|params\[|$route\.query`
For each screen: record URL pattern, table of param → UI state, default-if-missing, failure mode.
N/A rule: write `N/A — no URL-driven state restoration detected.` only if no URL params are read into component state.

**Unsaved-Changes Protection**
Signature: `beforeunload|onbeforeunload|usePrompt|useBeforeUnload|leaveGuard|isDirty|formState\.isDirty|data-turbo-confirm`
For each form/screen: record trigger, source, dirty detection method, exact prompt text.
N/A rule: write `N/A — no unsaved-changes guards detected.` only after checking all forms with user input.

### Client Behavior Anchor (→ technical-spec.md § 4 Shared Foundation, end)

Every feature spec MUST include the client behavior anchor block at the end of `## 4. Shared
Foundation` (after `### 4.6 Configuration`), even if all 3 linked artifacts have mostly N/A
content. **v27.7.0 (action-thread reshape):** relocated here from its P08 placement at the end of
`## 3. System Design` — § 3 is now `## 3. Actions`, and § 4 Shared Foundation is what used to be
§ 3 System Design, demoted to an appendix; the anchor moved with it. Before P08 it lived inside
the retired `## Cross-Cutting Logic`. The anchor links are relative from
`docs/features/{slug}/technical-spec.md`:

```markdown
**Client behavior:** see
[`behavior-logic.md`](../../generated/behavior-logic.md) (client-side patterns — debounce, optimistic UI, polling, upload, realtime),
[`permissions.md`](../../system/permissions.md) (feature flags / experiments / env / locale gates),
[`screen-flow.md`](../../generated/screen-flow.md) (guards / deep-link state restoration / unsaved-changes protection).
```

This anchor is always present. The linked files may have N/A sections — that is fine and correct.

## Scope & Codes

- All FR/BR/SM/ALG/INT/DEC codes are LOCAL to this feature. Cross-spec refs (e.g., "see BR-001 in F002") = INVALID.
- Every BR/SM/ALG/INT block, wherever it lives (inline in a Rule rung, or in § 4.4/§ 4.5), MUST
  cite `**Source:** path/to/file.ext:start-end`. NEVER fabricate paths or line ranges. Confirm
  each by reading the range.
- **v27.7.0 (action-thread reshape) heading form:** `SM-###`/`ALG-###`/`INT-###` blocks in § 4.3
  and § 4.5 keep the OLD plain-sentence H3 heading form the template shows for ALL THREE —
  `### {entity stated in one plain sentence} (SM-001)`, `### {algorithm/integration stated in one
  plain sentence} (ALG-001)` — NOT `### SM-001_NameSlug`, and **not H4** either, even though the
  B-v design sample nests ALG/INT one level deeper under its `### 4.5` subsection heading;
  `_spec_block_lib.BLOCK_HEADING_RE` (the canonical, shared parser) matches only the H3 shape
  today, so nesting these as H4 would silently stop the validator from finding them — re-nesting
  to fix that heading-depth defect (ADR-0005 § 1.2) is a joint doc+validator change for a later
  phase, not a documentation-only deviation to make alone. `BR-###` does NOT use this heading form
  anymore: Bin 1 is inline prose in a Rule rung (no heading at all), Bin 2/3 are bold-paragraph
  entries under an `#### Bin 2`/`#### Bin 3` H4 in § 4.4 (`**BR-001 — sentence.**`, not its own
  H3). `DEC-###` is a table row inline in a Rule rung (see above) — never a heading either. This
  is a genuine shape break from the pre-thread `### {sentence} (BR-001)` convention
  `code-formats.md` documents for older/non-thread specs; see that file's own note for the split.
- Pseudocode ≤20 lines per block. Use a concrete language hint (ts/py/php/go) or `text`. NEVER leave `{lang}` literally.
- Pseudocode MUST NOT embed secrets or credentials.

## Placement Rules

- Every `FR-###`/`BR-###`/`DEC-###`/`SM-###`/`US###` code stated in `functional-spec.md` gets
  AT LEAST ONE claiming row in `technical-spec.md § 2 Action Index` — via that code's presence in
  a row's `Codes` column (`A0`'s Codes column for a genuinely cross-cutting code). There is no
  longer a split between "under a US" and "Cross-Cutting" tables; the action-thread reshape folds
  both into this one binding (`action_unclaimed`). A code claimed by zero rows is a contract
  violation. A code claimed by two or more rows is NOT a violation — one requirement legitimately
  fanning out to several handling actions is the normal shape (measured on the 43-feature corpus:
  127 such fan-outs across 31 features, 85% a claim-width of exactly 2). An earlier version of
  this contract required exactly-one and that requirement was wrong; see
  `docs/decisions/ADR-0006.md`'s addendum.
- `BR-###` full blocks: **Bin 1** (used by exactly one action) lives INLINE in that action's
  `**Rule**` rung in § 3 — no separate heading, no separate section. **Bin 2** (used by ≥2 named
  actions) lives ONCE in `## 4. Shared Foundation § 4.4 Shared Rules` under `#### Bin 2`, tagged
  `Used in: A2, A3` — the citation and pseudocode live here and only here. Each using action's
  Rule rung ALSO carries the plain-language gloss inline, never a bare code with only a pointer
  (see "Self-sufficiency of the H4 context line" above). **Bin 3** (cross-cutting, no single
  action) lives in § 4.4 under `#### Bin 3`, claimed by the `A0` row, and MUST carry an explicit
  cross-cutting label. See "New Technical Sections — Authoring Rules" above for the full
  three-bin rule and its corpus basis.
- `DEC-###` is a table row inline in the gating action's `**Rule**` rung in § 3 — never a
  standalone heading anywhere in the file (see "Decision Logic (DEC-###) — a table row, not a
  block" above).
- `SM-###`/`ALG-###`/`INT-###` full blocks ALWAYS live in `## 4. Shared Foundation`
  (`### 4.3`/`### 4.5`/`### 4.5` respectively — ALG and INT now share one H3, "Algorithms &
  Integrations"), regardless of which capability or action they support — they describe
  structure, not per-action behavior. Tag the block `**Used in:** A2` (or `A5 → A9` for a
  multi-handler thread) so a reader can trace back to the action(s) that reference it — this
  replaces the pre-thread `**Linked US:**` field, which named a US### rather than the actions
  that actually consume the block. That `**Used in:**` tag names the § 4-side back-reference only
  — it does not by itself satisfy "Self-sufficiency of the H4 context line" above: the *action's*
  own rung citing this SM/ALG/INT code still needs its own plain-language gloss, not just the
  bare code.
- `SC-###` (global pass/fail conditions) live in `technical-spec.md § 5.1 Technical
  Verification`. Per-US `**Independent Test:**` and Given/When/Then acceptance scenarios also
  live in § 5.1, under a `#### {US###}` sub-block. No standalone `## Success Criteria` heading.
  The plain-language equivalent of each SC-### goes in `functional-spec.md § 10 Edge Behaviours
  to Verify`, back-referencing the FR-### it covers. This is UNCHANGED by the action-thread
  reshape.

## Depth Requirements (CRITICAL — incomplete sections = reviewer rejection)

- `functional-spec.md` § 1 Overview: Problem/Solution/Scope/Non-Scope all present; Actors table
  has ≥1 row. Problem must reference the real user problem, not "system feature."
- `functional-spec.md` § 2 Functional Capabilities: ≥1 `CAP-###` row once § 4 declares any real
  FR-###; every `Requirements` cell cites a real FR-### from § 4 (`func.capability_fr_dangling`
  is CRITICAL on a phantom cite); every US###/FR-###/BR-###/SCR### in §§ 4-7 claimed by exactly
  one row (the exhaustiveness rule above — enforced by `cap.code_unclaimed`/`cap.double_claimed`,
  muted whole-file only while `cap.claims_unfilled` fires).
- `functional-spec.md` § 4 Requirements: every FR-### declared in `technical-spec.md § 2` gets
  exactly one line here, in its band (0xx/1xx/2xx-3xx/4xx/6xx), ≤2 lines.
- `functional-spec.md` § 5 Business Rules: every BR-###/DEC-###/SM-### declared in
  `technical-spec.md` gets exactly one line here, ≤2 lines, code as a trailing tag. Aim ≥3 BR
  lines per UI feature; ≥1 per background feature. An observed DEFECT is NEVER written here as
  if it were an intended rule — route it to § 11 Risks & Known Issues instead
  (`func.risk_as_rule`).
- `technical-spec.md § 2 Action Index`: every FR/BR/DEC/SM/US code from the twin gets at least one
  claiming row (or `A0`); `A0` is mandatory even at zero real actions. A code claimed by several
  rows is expected fan-out, not an error. See "New Technical Sections — Authoring Rules" above.
- `technical-spec.md § 3 Actions`: one `### 3.N CAP-NN` bucket per `functional-spec.md § 2` row,
  in CAP- order, each holding one `#### A<n>` block per action using the fixed rung set; ends in
  one feature-wide `### 3.{N+1} Edge cases` table. Structure (endpoint, table, file:line) lives in
  the rungs; guards/validations/constraints belong in the Rule rung or § 4.4, never restated
  elsewhere.
- `technical-spec.md § 4 Shared Foundation`: Components/Data Model/State Management/Shared
  Rules/Algorithms & Integrations/Configuration — structure only, appendix to § 3. § 4.4 Shared
  Rules holds Bin 2/Bin 3 BR full blocks; Bin 1 lives inline in § 3 instead (see the three-bin
  rule above).
- `functional-spec.md § 7 User Stories`: each block leads with **Actor** / **Goal** / **Business
  value** (matching a § 1 Actors row), then observable `**Acceptance Criteria:**` checkboxes.
  `technical-spec.md § 2` carries the SAME US### as a reference row ONLY — never a narrative,
  never a restated AC. Per-US `**Independent Test:**` and technical Given/When/Then live in
  `technical-spec.md § 5.1`, not § 2.
- `functional-spec.md § 9 Edge Cases`: MUST contain ≥3 rows for UI features; ≥1 for background
  features.
- `technical-spec.md § 4.2 Data Model`: table MUST list ALL database tables this feature
  reads/writes; ≥3 entities for non-trivial features.
- `technical-spec.md § 5.4 Source References`: MUST list primary controller(s), model(s), job(s),
  service(s), page/component file(s) with paths and line ranges, Action column leading. ≥3
  entries required. **v27.12.0:** an `#### Data Flow` subsection immediately after this table is
  BEST-EFFORT — zero dedicated enforcement (`validate_reading_guide_db_impact.py` deliberately
  does not walk `features/*/technical-spec.md` any more; only `screens/*/spec.md` is). It traces
  what DATA moves and how it is transformed along ONE action's own Request → BE → Rule → Result
  rungs (§ 3) — NOT a feature-wide diagram, and NOT a restatement of "who calls whom" (each
  action's own `sequenceDiagram` in § 3 already owns that, at the diagram threshold).
- `technical-spec.md § 5.2 Assumptions`: ≥2 entries for any non-trivial feature.
- `technical-spec.md § 5.3 Unresolved Questions`: list anything not verifiable from source
  (implementation-detail unknowns only). ≥1 entry expected for complex features. Domain/business
  unknowns go to `functional-spec.md § 3 Open Decisions` instead — see the Three-Way Decision
  Procedure above.
- `technical-spec.md` § Source Walkthrough (A3, unnumbered, after § 5, UNCHANGED by the
  action-thread reshape): ordered reading list (data model → entry point → view → business
  logic), 1 file per step, each cited `**File:** path:line-range` (NOT `**Source:**` — see
  below) + a 1-sentence "why start here"; a pointer to the recast `### 5.4 Source References`
  table. No separate call-hierarchy diagram is required — each action's own **Source** rung in
  § 3 already owns its call chain more precisely than one feature-wide diagram could. MANDATORY —
  no N/A fallback (every feature has source to walk through).
- `technical-spec.md` § DB Impact per Event (B4, unnumbered, after Source Walkthrough, UNCHANGED
  shape by the action-thread reshape): one row per action/event/job that WRITES to the database
  (`Action | Event/Endpoint | Table | Columns | Operation | Value Derivation | Source`, Action
  column leading). Read-only queries are out of scope. `N/A — read-only feature, no DB writes.` is
  the ONLY valid fallback, and only after confirming zero writes.
- `functional-spec.md § 11 Risks & Known Issues`: `N/A — none found.` allowed; a real row MUST
  NOT be rewritten into a BR line and MUST NOT be silently "fixed."
- `functional-spec.md § 12 Dependencies`: `N/A — none found.` allowed; a real dependency cites an
  F###/SCR###/FR-###/BR-### code or a plain pointer as Evidence.

## Per-File Rules

### technical-spec.md

- **v27.7.0 (action-thread reshape, TARGET shape — `REQUIRED_H2_TECH_THREAD`):** `## 1. Technical
  Overview` → `## 2. Action Index` → `## 3. Actions` → `## 4. Shared Foundation` → `## 5.
  Verification & Technical Notes`, plus the two unnumbered literal H2s `## Source Walkthrough`
  (A3) and `## DB Impact per Event` (B4) after § 5 — see `wire-format-contract.md` (normative)
  for the exact byte-for-byte shapes; this contract does not restate them. `REQUIRED_H2_TECH`
  (the OLD 5-heading list: `## 2. Functional → Technical Mapping` / `## 3. System Design` /
  `## 4. Technical Behavior by Capability`) still governs the exact-order validator until a later
  phase repoints it — this is a deliberate mid-migration window, not a contradiction; author to
  the TARGET shape below regardless.
- `### 4.1`–`### 4.6` (Shared Foundation) H3 children MUST be present in order —
  `_spec_constants.REQUIRED_APPENDIX_H3` (replaces the retired-in-place `REQUIRED_SYSDESIGN_H3`,
  which named the old `### 3.1`–`### 3.7`). `### 5.1`–`### 5.5` (Verification & Technical Notes)
  are UNCHANGED — `_spec_constants.REQUIRED_VERIF_H3`.
- `## 3.` H3 capability buckets are DYNAMIC: one `### 3.N {Capability}` per `CAP-N` row in the
  twin `functional-spec.md § 2`, in `CAP-` order, PLUS one final `### 3.{N+1} Edge cases` bucket
  (feature-wide, Action column leading — not per-capability). When § 2 is absent/empty, emit
  exactly one bucket `### 3.1 {Feature name}` and flag it for a follow-up researcher pass once
  § 2 exists.
- Source citations (`**Source:** path:line-start-end`) live here and ONLY here — inline in a
  Rule/Source rung, or in a § 4.4/§ 4.5 full block; never in `functional-spec.md`.
- SM Mermaid state diagrams, DISC tables belong in § 4 (§ 4.3, § 4.2 respectively). DEC tables
  and inline BR statements live in § 3, inside the action's Rule rung — NOT in § 4 (see the
  three-bin rule and the DEC-as-table-row rule above; this is the biggest placement change from
  the pre-thread shape, where both lived under `## 4.`'s capability buckets).
- **The duplication fix — still the highest-value rule in this contract, now expressed through
  § 2 Action Index instead of the retired `## 2. Functional → Technical Mapping`.** Every
  FR/BR/DEC/SM/US code is claimed by AT LEAST ONE § 2 row (or `A0`) — claimed by two or more is
  legitimate fan-out (one requirement, several handling actions), not an error; the exactly-one
  reading was retired along with `action_double_claimed` (see `docs/decisions/ADR-0006.md`'s
  addendum). The row states the action's
  handler/path/tables, never a restated story. Do NOT write a `**What happens:**` field, a
  narrative paragraph, or a re-derived Given/When/Then block anywhere in `technical-spec.md`. The
  only per-US narrative content `technical-spec.md` carries is `§ 5.1`'s `**Independent Test:**`
  and its OWN Given/When/Then acceptance scenarios — those may additionally carry status/response
  detail the BA-facing § 8 Scenarios does not, which is why they are not themselves a forbidden
  restatement (content-preservation-map T-14/T-15).
- **T-12 guard, for context (migrate-composer concern, not an authoring choice — stated here so
  a researcher never reintroduces the retired field by hand):** when an OLDER spec is migrated,
  its retired per-US narrative field is removed ONLY when the twin `functional-spec.md § 7 User
  Stories` carries that exact `US###` code; otherwise the migrate composer carries it forward
  under the matching § 3 action's Rule rung, prefixed `[UNVERIFIED] carried from technical-spec
  §User Stories — `. A researcher drafting a NEW feature spec never writes this field at all —
  the twin's § 7 always exists for a feature under active research.
- `## Client Behavior Anchor` — the `**Client behavior:** see [...]` cross-reference block — MUST
  appear at the end of `## 4. Shared Foundation` (after `### 4.6 Configuration`), even if all
  linked artifacts are mostly N/A. Pre-P08 this lived inside the retired `## Cross-Cutting
  Logic`; P08 moved it to the end of `## 3. System Design`; the action-thread reshape moves it
  again to the end of `## 4. Shared Foundation` (§ 3 no longer being a structure section).
- `## 5.5 Artifact References` is a single merged 4-column table: `Artifact | File | Codes Used |
  Reviewed`. Always include System Overview and Feature List. LEGACY two-section format (`##
  Related Artifacts` + `## Spec Documents`) = CRITICAL.
- Artifact References point to layered paths: `docs/features/{slug}/technical-spec.md`,
  `docs/system/overview.md`, `docs/generated/route-list.md`. The Screens row points at
  `functional-spec.md § 6` (renumbered from the old § 5).
- **v25.0.0 (unchanged by the retaxonomy):** the `API Map` row's Codes Used column carries bare
  `ROUTE###` codes (e.g. `ROUTE012, ROUTE014` — never braced: a wholly-braced cell fires
  `Universal.no_placeholder` AND reads as unfilled to `_route_link_lib`, silently skipping the
  row's twin-consistency check) — despite the row label, these codes are NOT checked against
  `api-map.md` (which has no code scheme); they are the bridge to `route-list.md`'s `Code` column,
  the inverse of that table's `Owner F###` cell. Every cited `ROUTE###` MUST resolve to a
  `route-list.md` row, and the citing F### must appear in that route's `Owner F###` set
  (`validate_feature_api_link.py` enforces both directions + twin-consistency).
  `api-map.md`/`api-contracts.md` remain separate, unbound views.
- **`## Source Walkthrough` (A3) and `## DB Impact per Event` (B4) do NOT belong in
  technical-spec.md — RETIRED in v27.8.0 (self-sufficiency release, `claude/skills/rebuild-spec/docs/decisions/ADR-0007.md`).**
  A researcher drafting a NEW technical-spec.md never writes either heading. What replaced them:
  every action's own `**Source:**` rung already carries its call-chain citations (the job A3 used
  to do per-file), and its `**State:**` rung — the 8th rung, SM-anchored — carries the DB-write
  statement A3's own Result rung already made B4 redundant for (measured: 0 of 334 B4 citation
  line-segments failed to already appear in the owning action's own `**Source:**` rung). If an
  older draft still carries either heading, `FeatureSpec.retired_section_present` (warning) flags
  it for a mechanical strip via `--migrate --only action-thread` — do not hand-author a fix.
  **A3 stays fully live on screen-spec.md** (unaffected by this retirement) — see
  `references/verification-checklist-screen-spec.md`'s A6 rules for that authoring contract.
- **v27.x (retaxonomy):** the retired `## Cross-Cutting Logic`, its 7 H3 children, and the old
  `## User Stories` narrative fields no longer exist anywhere in this file. Do NOT author any of
  them. If a reviewer asks why a field looks thin compared to the pre-P08 shape, state the "two
  files, one code" split plus the retaxonomy explicitly — content moved, it was not dropped (see
  `content-preservation-map.md`).

### functional-spec.md

- All 13 H2 sections in the exact order from `templates/functional-spec-template.md` /
  `_spec_constants.REQUIRED_H2_FUNC` MUST be present: Overview → Functional Capabilities → Open
  Decisions → Requirements → Business Rules → Screens → User Stories → Scenarios → Edge Cases →
  Edge Behaviours to Verify → Risks & Known Issues → Dependencies → Configuration.
- Run the forbidden-token self-check (dev tokens + secret shapes) before writing. FR/BR/SM/DEC/
  SCR/US codes are allowed and expected. The four status markers `[UNVERIFIED]`, `[INFERRED]`,
  `[NEEDS_DOMAIN_CONFIRMATION]`, `[EXPECTED]` are PERMITTED here (D6) — see Status Marker
  Vocabulary above.
- Rule density: § 4 and § 5 are ≤2 lines per rule, measured in lines. A rule needing more detail
  gets a pointer to `technical-spec.md`, not a longer line here.
- § 2 Functional Capabilities: `CAP-###` rows are the anchor `technical-spec.md § 4` groups
  against — every `Requirements` cell cites a real FR-### from § 4 below.
- § 6 Screens: 4-column table (`Screen Name | SCR### | What User Sees | What User Can Do`, per
  `templates/functional-spec-template.md`) MANDATORY for UI/mixed features. The `SCR###` column
  carries the canonical `SCR###_NameSlug` from `screen-list.md` — it is the bridge to
  `docs/screens/SCR###_Name/spec.md` and the inverse of that spec's `**Feature**` backlink. Every
  code MUST resolve to a `screen-list.md` row (`validate_feature_screen_link.py` enforces this).
  Routes live in `route-list.md`, not this table.
- Write `N/A — background feature; no user-facing screens.` for background-only features in § 6.
- § 6 User Journey numbered steps MUST reference screen names, NOT routes or endpoints.
- § 7 User Stories: every block opens with **Actor** / **Goal** / **Business value** (Actor
  matches a § 1 Actors row) before its optional narrative — `func.user_story_shape` (warning)
  fires when a block skips one of the three. Then observable `**Acceptance Criteria:**`
  checkboxes — NO Endpoint, Data Required, or Dependencies fields (those live in
  `technical-spec.md § 2`).
- § 8 Scenarios: Given/When/Then, at least one happy-path and one error scenario per US### in
  § 7.
- § 9 Edge Cases: single table `Scenario | What Happens | User-Facing Message`. ≥3 rows for UI
  features; ≥1 for background-only features. "User-Facing Message" MUST be plain language. Raw
  HTTP status codes in this column = REJECTED. Include edge cases lifted from DISC-### variants
  and DEC-### branches.
- § 10 Edge Behaviours to Verify: one line per behaviour, FR-### bold, back-referencing a code
  from § 4.
- § 11 Risks & Known Issues: `ID | Type | Description | Impact | Status` table, or `N/A — none
  found.`. `Type` ∈ `known-issue` (observed abnormal current behavior) | `risk` (future
  exposure). A row here is NEVER rewritten into a § 5 Business Rule line
  (`func.risk_as_rule` warns on the inverse — a § 5 line that reads like a recorded defect with
  no § 11 counterpart).
- § 12 Dependencies: `Dependency | Type | Why this feature needs it | Evidence` table, or `N/A —
  none found.`. `Type` ∈ `feature` (another F###) | `external-service` | `data` |
  `infrastructure` | `config`.
- § 13 Configuration: one fenced block, name = value + trailing comment; no secrets, no
  environment-specific values. This is BUSINESS-VISIBLE configuration a BA/PO would recognize —
  technical configuration (env vars, timeouts, retry counts) belongs in `technical-spec.md §
  3.7` instead.
- MUST NOT contain `**Source:**` citations, pseudocode outside fences, `file:line` references,
  class names, or HTTP verbs — the four status markers above are the one exception.

## Folder Lifecycle (2-file atomicity)

Wave 5 creates `{slug}/.pending`. On successful researcher run:

1. Write both files.
2. Verify both are non-empty:
   `[ -s technical-spec.md ] && [ -s functional-spec.md ]`
3. If both pass → `rm .pending`. If EITHER fails → leave `.pending` intact. FS.5 will mark MISSING.
4. A partial write (only 1 file written) MUST leave `.pending` — do NOT remove on partial success.

## Task Closure

On successful 2-file write + `rm .pending`: call `TaskUpdate(status=completed)` on this task id BEFORE returning.

## See Also

- `process-flow-researcher-contract.md` (Wave 6.8 process-flow synthesis)
- `references/canonical-fcode-schema.md` § Folder Lifecycle
- `references/verification-checklist-universal.md` § Pending Marker Rule
- `references/confidence-report-contract.md` § "v27 amendment — the 4th state" (status marker vocabulary, canonical)
- `plans/260818-1332-rebuild-spec-human-readable-sot/target-shape-spec.md` (normative section shapes for both output files)
- `plans/260818-1332-rebuild-spec-human-readable-sot/content-preservation-map.md` (the move-by-move ledger this contract implements)
