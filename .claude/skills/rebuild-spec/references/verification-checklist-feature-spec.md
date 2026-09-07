# Verification Checklist: FeatureSpec (FS.5)
See verification-checklist-universal.md for Universal rules and Pending Marker Rule.

### FeatureSpec (per-feature, 2 files)

**Cross-refs:** the 9-artifact cross-ref subset (of the 11 core artifacts; excludes Architecture, SystemOverview, PermissionsMatrix).

#### Universal (both files)
- File must exist; non-empty; no `{PLACEHOLDER}` literals outside fenced code/HTML comments.
- F### prefix in folder name matches canonical-fcodes.json slug.
- F### code, feature name, priority match FeatureList entry exactly.

#### TechnicalSpec (technical-spec.md)

**v27.7.0 (action-thread reshape) — full-set replacement of §§ 2-4, not an incremental rename:**
the layer-first shape (`## 2. Functional → Technical Mapping` / `## 3. System Design` / `## 4.
Technical Behavior by Capability`) is RETIRED — `wire-format-contract.md` is normative. The new
spine is ACTION-first: `## 2. Action Index` is the action→rule binding the layer-first shape
lacked (measured on a 43-feature/430-action corpus: the old `**Applies to:**` free text resolved
to an action only 26% of the time; 84% of actions had no attributable rule — see
`docs/decisions/ADR-0006.md`), `## 3. Actions` is the body (one capability bucket per twin § 2
row, each holding per-action blocks with a fixed labelled rung set), and `## 4. Shared
Foundation` is what used to be § 3 System Design, demoted to an appendix — its § 4.4 Shared Rules
subsection absorbs the old § 4's per-capability BR/DEC placement via a three-bin rule (below).

**Status of this rewrite: template + this checklist DONE (this phase); validator wiring for the
new shape's rule_ids is landing across several phases of
`plans/260824-1128-rebuild-spec-action-thread-v27-7/plan.md` — `_check_action_thread` in
`validate_feature_spec.py` already implements 6 of them (see the rule_id table below). The
exact-order structural check (`FeatureSpec.required_sections`) still enforces the OLD
`REQUIRED_H2_TECH` list until a later phase in that plan repoints it — a file in the new shape
will currently fail that ONE check until the repoint lands; this is a deliberate mid-migration
window, not a defect in the new shape or this checklist.**

**Required sections (5 H2s, exact order, TARGET shape — `REQUIRED_H2_TECH_THREAD`):**
`## 1. Technical Overview` → `## 2. Action Index` → `## 3. Actions` → `## 4. Shared Foundation`
→ `## 5. Verification & Technical Notes`. Read `_spec_constants.REQUIRED_H2_TECH_THREAD` for the
authoritative list — do not copy the heading text out of this file.

**v26.0.0 — A3/B4, RETIRED from technical-spec.md in v27.8.0 (self-sufficiency release,
`claude/skills/rebuild-spec/docs/decisions/ADR-0007.md`):** `## Source Walkthrough` (A3) and `## DB Impact per Event` (B4)
used to be appended AFTER `## 5.` here, gated by a DEDICATED validator. Both left
technical-spec.md's target shape this release — the § 2 Action Index + per-action `Source`/
`State` rungs replaced them; `check_db_impact()` and its `db_impact.*` rule_ids were deleted
outright. A technical-spec.md draft MUST NOT carry either heading; if one is still present
(pre-migration corpus), `FeatureSpec.retired_section_present` (warning) flags it. **A3 stays
fully live on screen-spec.md** — see `verification-checklist-screen-spec.md`'s A6 rules for
that (unaffected) validator.

**§ 2 Action Index structure:** one row per action, header
`| # | Action (handler) | Method · Path | Codes | Writes | Detail |` exactly
(`wire-format-contract.md § "§ 2 Action Index"`). `A0` (cross-cutting) is MANDATORY even at zero
real actions. `Action (handler)` is keyed on `` `Class#method` `` (D2 — handler IS the action's
identity), never `METHOD PATH` alone except as a last-resort fallback
(`FeatureSpec.action_key_not_handler`, warning). Every FR/BR/DEC/SM/US code declared in § 3 or
§ 4 must be claimed by AT LEAST one row's `Codes` column (`action_unclaimed`, critical). A code
claimed by several rows is legitimate fan-out (one requirement, several handling actions), not a
violation — the `action_double_claimed` check that once flagged this was retired; see
`docs/decisions/ADR-0006.md`'s addendum.

**§ 3 Actions structure:** one `### 3.N CAP-NN {capability title}` bucket per row in the twin
`functional-spec.md § 2`, in CAP- order, each holding one `#### A<n> · {action title}` block per
action (the ` · ` separator is REQUIRED — `ACTION_HEADING_RE`). Every block uses the SAME
labelled rung set, fixed order, presence never required —
`` **Who** → **FE** → **Request** → **BE** → **Rule** → **Result** → **State** → **Source** ``
(`_spec_constants.RUNG_LABELS`, 8 rungs — `State` joined as the 8th, self-sufficiency v27.8). An
absent rung is omitted entirely, never rendered as `N/A`/`None.`
(`FeatureSpec.rung_empty_rendered`, critical); whichever rungs a block DOES carry must appear in
this relative order (`FeatureSpec.rung_order`, critical). The Source rung is the ONE rung with NO
` · ` separator — `` **Source:** `path:line-line` `` (colon inside the bold, plain space, no
middot); every other rung, including State, uses ` · `:
`` **State** · `SM-###`: `{from}` → `{to}` *(§ 4.3)* `` (unconfirmed:
`` **State** · [UNVERIFIED] `SM-###`: transition not confirmed from source *(§ 4.3)* ``). State is
authored by a researcher fill pass reading source ONLY — never derived from a mermaid edge label
(no such join exists; measured and dropped, see `docs/decisions/ADR-0006.md`'s addendum) —
`FeatureSpec.state_rung_missing` (warning) flags a writing action inside an SM-modelled feature
that carries none. `DEC-###` renders as a table row inline in the gating
action's Rule rung (fixed columns `DEC | subtype | Condition | What the user sees | Source`), not
a standalone heading. § 3 ends with one feature-wide `### 3.{N+1} Edge cases` table (Action column
leading), not a per-capability `#### Edge Cases` sub-block. Every code cited in a block's H4
context line must be glossed in plain language somewhere in that same block
(`FeatureSpec.action_ref_unglossed`, warning) — see
`references/feature-spec-researcher-contract.md` § "Self-sufficiency of the H4 context line" for
the full rule.

**§ 4 Shared Foundation structure:** 6 required H3 subsections in order — `### 4.1 Components`
(gains a `Used in` column), `### 4.2 Data Model` (entity table directly, no separate `#### Key
Entities` wrapper; nests `#### Polymorphic Behavior` when applicable), `### 4.3 State
Management`, `### 4.4 Shared Rules` (the three-bin rule, below — replaces the old per-capability
BR/DEC placement), `### 4.5 Algorithms & Integrations` (ALG and INT now share one H3, each still
its own H4 block), `### 4.6 Configuration` — `_spec_constants.REQUIRED_APPENDIX_H3` (replaces the
retired-in-place `REQUIRED_SYSDESIGN_H3`, which is deprecated-but-still-imported until a later
phase deletes it — see that constant's own comment). Empty subsection MUST contain `None.`. The
`**Client behavior:** see [...]` anchor block closes this section (after § 4.6) — relocated here
from its P08 home at the end of `## 3. System Design`, which is now `## 3. Actions`
(`FeatureSpec.missing_client_behavior_anchor` re-homes with it).

**§ 4.4 Shared Rules — the three-bin rule:** a rule's placement is decided by HOW MANY named
actions use it, counted, never judged. **Bin 1** (used by exactly one action) is NOT in § 4.4 at
all — it lives inline in that action's Rule rung in § 3, full statement + `**Source:**`. **Bin 2**
(used by ≥2 named actions) has its one full block in § 4.4 under `#### Bin 2`, tagged
`Used in: A2, A3` — the citation and pseudocode live there once; each using action's Rule rung
ALSO carries the plain-language gloss inline, never a bare code with only a pointer
(`FeatureSpec.action_ref_unglossed`, warning — see
`references/feature-spec-researcher-contract.md` § "Self-sufficiency of the H4 context line").
**Bin 3**
(genuinely cross-cutting, claimed by no single action) lives in § 4.4 under `#### Bin 3`, claimed
by the `A0` row in § 2, and MUST carry an explicit cross-cutting label
(`FeatureSpec.crosscutting_unlabelled`, warning — wired, see the rule_id table below).

**§ 5 Verification & Technical Notes structure (UNCHANGED by the action-thread reshape):** 5
required H3 subsections in order — `### 5.1 Technical Verification` (global SC-### + per-US
`#### {US###}` sub-blocks carrying `**Independent Test:**` and Given/When/Then), `### 5.2
Assumptions`, `### 5.3 Unresolved Questions`, `### 5.4 Source References` (Action column now
LEADING), `### 5.5 Artifact References` — `_spec_constants.REQUIRED_VERIF_H3`.

**The duplication fix, stated as an enforceable rule.** `## 2. Action Index` replaces the retired
`## 2. Functional → Technical Mapping` — BOTH the old CCL § Requirements table AND the old per-US
"Requirements fulfilled" + per-US narrative duplication. Every FR/BR/DEC/SM/US code in the twin
`functional-spec.md` MUST be claimed by at least one row here or by `A0`
(absence → `FeatureSpec.action_unclaimed`, critical; a code claimed by several rows is legitimate
fan-out, not an error). The row
states the action's handler/path/tables — it is a reference row, never a restated story. A
`**What happens:**` field surviving anywhere in `technical-spec.md` is the same duplication in a
different shape (`FeatureSpec.us_narrative_present`).

**Format checks:**
- F### code follows `F###_NameSlug`, matches FeatureList entry exactly (code + name + priority).
- US### / SCR### / REG### formats valid (reference code-formats.md).
- `## 2. Action Index` header row matches `wire-format-contract.md § "§ 2 Action Index"` exactly:
  `| # | Action (handler) | Method · Path | Codes | Writes | Detail |`. `A0` row present even at
  zero real actions.
- `SM`/`ALG`/`INT` codes use the plain-sentence-plus-parenthetical H3 heading form the template
  shows — `### {sentence} (SM-001)`, `### {sentence} (ALG-001)` — NOT the retired
  `### SM-001_NameSlug` form, and **not H4** either, even though the B-v design sample nests
  ALG/INT under their `### 4.5` subsection one level deeper — `_spec_block_lib.BLOCK_HEADING_RE`
  matches only the H3 shape today; per-spec unique; code appears with full `**Source:**` block
  exactly once. **`BR` and `DEC` do NOT use this heading form** (v27.7.0 action-thread reshape —
  see below).
- `BR-###` placement follows the three-bin rule: Bin 1 (used by exactly one action) is inline in
  that action's `**Rule**` rung, full statement + `**Source:**`, no heading. Bin 2 (used by ≥2
  named actions) has ONE full block in `## 4.4 Shared Rules` under `#### Bin 2`, tagged
  `Used in: A2, A3`; each using action ALSO carries the plain-language gloss inline, never a bare
  code with only a pointer (self-sufficiency clause,
  `references/feature-spec-researcher-contract.md`). Bin 3 (cross-cutting,
  claimed by no single action) lives in § 4.4 under `#### Bin 3`, claimed by the `A0` row, and
  carries an explicit cross-cutting label. A Bin 2/3 entry with no `Used in:`/cross-cutting label
  respectively fires `FeatureSpec.crosscutting_unlabelled` (warning — wired, see the rule_id table
  below).
- `DEC-###` renders as a table row inline in the gating action's Rule rung — fixed columns
  `DEC | subtype | Condition | What the user sees | Source` — never a standalone `#### {sentence}
  (DEC-001)` H4 (that was the pre-thread shape).
- Each SM/ALG/INT full block, and each BR/DEC wherever it lives, has `**Source:** path:start-end`
  citation (line range mandatory).
- Each SM/ALG/INT full block has ≥1 `**Linked FR:** FR-###` (or the action-thread equivalent
  `**Used in:** A<n>`) referencing the same spec.
- A BR/DEC entry carries NO plain-language `**Rule:**`/`**user_visible_outcome:**` field — that
  sentence lives in `functional-spec.md § 5` as the one-liner for the same code. An entry WITH
  one of those fields present is not itself an error (forward-compatible during migration), but
  a reviewer should note it for cleanup.
- SM full block MUST contain a Mermaid `stateDiagram-v2` fenced block.
- Pseudocode blocks ≤20 lines; no literal `{lang}` in fence; no secrets/credentials.
- A `sequenceDiagram` fence MUST NOT cite `file:line` anywhere inside it — rungs carry FACTS,
  diagrams carry ORDER/BRANCHING (`FeatureSpec.diagram_cites_file_line`, critical — wired, see the
  rule_id table below). Cap: ≤12 arrows, ≤2 `alt` blocks (`FeatureSpec.diagram_over_cap`, warning,
  never critical — arrow/`alt` counting is a heuristic) — over-cap means the action should
  split, not that the diagram needs to compress.
- Every FR-###/BR-###/DEC-###/SM-###/US### code declared in `functional-spec.md` is claimed by
  at least one `## 2. Action Index` row (or `A0`) — there is no longer a US-scoped vs.
  cross-cutting split to reconcile (`action_unclaimed`). A code claimed by several rows is
  expected fan-out, not a violation.
- Every FR-### is covered by ≥1 `SC-###` via the `(covers …)` back-ref in `### 5.1`. Uncovered
  FR = critical (verification missing).
- No H2 heading named `## Cross-Cutting Logic`, `## User Stories`, `## Key Entities`,
  `## Requirements`, `## Business Rules`, `## State Machines*`, `## Algorithms*`,
  `## External Integrations*`, `## Success Criteria`, `## How It Works`, `## 2. Functional →
  Technical Mapping`, `## 3. System Design`, or `## 4. Technical Behavior by Capability` — all
  retired.
- No standalone `### API & Endpoints` H3 — that surface is now the § 2 Action Index's
  `Method · Path` column.
- No `## Appendix` heading in submitted draft.
- No `## Screens`, `## Screen List`, `## Why It Matters`, `## Who Uses It`, `## What They Do`, or
  top-level `## Edge Cases` heading — those H2s live in `functional-spec.md` now (or, for Edge
  Cases, the feature-wide `### 3.{N+1} Edge cases` table at the end of `## 3. Actions`); a
  top-level occurrence in `technical-spec.md` is stale-migration residue, not a new draft error,
  but flag it.

**Cross-refs (9-artifact subset mandatory — of the 11 core artifacts; excludes Architecture, SystemOverview, PermissionsMatrix):**

| Field in spec | Must match |
|---------------|-----------|
| F### code, feature name, priority | FeatureList (exact match) |
| All SCR###/US###/ROUTE###/MODEL###/BL### listed in FeatureList for this F### | Present across the pair (`technical-spec.md` + `functional-spec.md`) |
| SCR### codes (in `functional-spec.md § 6`) | Exist in ScreenList |
| US### codes | Exist in UserStories |
| Screen flow references | Match ScreenFlow |
| Routes referenced | Exist in RouteList. **v25.0.0:** `ROUTE###` citations (bare, never `{ROUTE###}` — a braced cell fires `Universal.no_placeholder` and is also read as unfilled by `_route_link_lib`, see the § 5.5 note below) in `technical-spec.md`'s `### 5.5 Artifact References` Codes Used column resolve to `route-list.md`'s `Code` column, and (twin-consistency) the citing F### must be IN that route's `Owner F###` set (`validate_feature_api_link.py` enforces both). |
| Entities referenced | Exist in DataModel |
| BL### codes in Artifact References | Exist in BehaviorLogic |
| PERM### codes in Artifact References | Exist in Permissions |
| `**Source:** file:line` cited in BR/SM/ALG/INT blocks | File exists and cited range contains the described logic (reviewer reads to verify) |

Content grounded in actual source code (no fabricated details).

**Critical edge cases:**
- Technical spec missing / empty → critical
- F### not in FeatureList → critical
- Feature name or priority mismatch with FeatureList → critical
- Required H2 (§ 1–§ 5, `REQUIRED_H2_TECH_THREAD`) absent or out of order → critical
  (`FeatureSpec.required_sections`) — **NOTE:** the shipped validator still checks against the
  OLD `REQUIRED_H2_TECH` list until a later phase repoints it, so a correctly-shaped
  action-thread file will currently trip this ONE check; do not read that as the new shape being
  wrong. Every other check below is unaffected.
- `## 2. Action Index` absent, or present with zero data rows (the mandatory `A0` row must always
  be present, even for a feature that resolves zero actions) → critical
  (`FeatureSpec.action_index_missing`)
- A non-`A0` row's `Action (handler)` cell is the bare `` `METHOD PATH` `` fallback shape →
  warning (`FeatureSpec.action_key_not_handler` — D2: the handler IS the action's identity; the
  fallback is reserved for a genuinely unparseable handler)
- A US###/FR-###/BR-###/DEC-###/SM-### declared in § 3 Actions or § 4 Shared Foundation claimed
  by zero § 2 rows (nor `A0`) → critical (`FeatureSpec.action_unclaimed`, message opens with
  `family=`)
- A code claimed by ≥2 § 2 rows is NOT an error — legitimate fan-out (one requirement, several
  handling actions). `FeatureSpec.action_double_claimed` once flagged this and was retired; see
  `docs/decisions/ADR-0006.md`'s addendum.
- Rungs inside one `#### A<n>` block appear out of `RUNG_LABELS` order → critical
  (`FeatureSpec.rung_order`)
- A rendered rung's body is empty, `N/A`, or `None.` (an absent rung must be omitted, not
  stubbed) → critical (`FeatureSpec.rung_empty_rendered`)
- A writing action's (§ 2 `Writes` non-`—`) block renders no `**State**` rung, inside a feature
  that carries a real `### … (SM-###)` heading block → warning, degrades while fill-pending
  (`FeatureSpec.state_rung_missing`)
- A BR/DEC/SM/ALG/INT/DISC code cited in a `#### A<n>` block where EVERY occurrence in that block
  is bare (no occurrence's line carries ≥12 non-code alphanumeric characters of gloss) → warning,
  degrades while fill-pending (`FeatureSpec.action_ref_unglossed`)
- `### 4.1`–`### 4.6` (Shared Foundation) missing or out of order → critical
  (`FeatureSpec.sysdesign_subsections` — rule_id retained across the reshape, now checked
  against `REQUIRED_APPENDIX_H3` instead of the old `REQUIRED_SYSDESIGN_H3`, pending the same
  validator repoint noted above)
- `### 5.1`–`### 5.5` missing or out of order → critical (`FeatureSpec.verification_subsections`
  — UNCHANGED)
- `## 3.` has no `### 3.\d+ ` capability-bucket child → critical
  (`FeatureSpec.capability_buckets_missing` — rule_id retained, now checked against `## 3.`
  instead of `## 4.`)
- A `### 3.N` with no matching `CAP-N` in the twin's `## 2.`, or vice versa → warning
  (`FeatureSpec.capability_twin_skew`)
- A Bin 2/3 entry in § 4.4 with no `Used in:` list (Bin 2) or no explicit cross-cutting label
  (Bin 3) → warning (`FeatureSpec.crosscutting_unlabelled` — wired, see the rule_id table below)
- A `sequenceDiagram` fence citing `file:line` anywhere inside it → critical
  (`FeatureSpec.diagram_cites_file_line` — wired, see the rule_id table below)
- `**What happens:**` field present anywhere in `technical-spec.md` → warning
  (`FeatureSpec.us_narrative_present`)
- Legacy two-section format detected (`## Related Artifacts` + `## Spec Documents` both present)
  → **CRITICAL** immediately (no transition window — replace with `### 5.5 Artifact References`
  table)
- `### 5.5 Artifact References` present but missing required rows (System Overview, Feature
  List, Route List, Data Model, Screen List, Screen Flow, Behavior Logic, Permissions, User
  Stories) → critical
- `### 5.5 Artifact References` Codes Used column contains bare REG### without parent SCR###
  prefix → critical
- `### 5.5 Artifact References` Codes Used cell is wholly braced (e.g. `{ROUTE012}`) → critical
  (`Universal.no_placeholder`) — codes in this column are always written bare (`ROUTE012,
  ROUTE014`); braces here are doubly wrong, since a wholly-braced cell also reads as unfilled to
  `_route_link_lib`'s pattern, so `validate_feature_api_link.py` silently skips the row instead of
  checking it
- Top-level deprecated heading present (any retired H2 from the Format checks list above) →
  critical
- `#### Polymorphic Behavior` (under `### 4.2`) section absent entirely → critical
  (`FeatureSpec.polymorphic_behavior_present` — retained, re-homed under § 4.2; validator wiring
  for the new location is a known gap, see the rule_id table below)
- `#### Polymorphic Behavior` present but Data Model includes entity with DISC-### in
  entities.md AND section body is `N/A` → critical (false N/A)
- `#### Polymorphic Behavior` has DISC-### subsection but one or more known values from
  entities.md are missing → critical (incomplete coverage)
- `#### Polymorphic Behavior` DISC-### subsection present but not all Data Model entities'
  DISC-### are covered (subsection for DISC-001 present, DISC-002 from same entity missing) →
  critical
- `#### Polymorphic Behavior` behavior cell is blank (empty string, not `unverified`) → warning
- `#### Polymorphic Behavior` DISC-### subsection references a DISC-### not present in
  entities.md for any entity in the Data Model table → critical (phantom discriminator)

**Content depth checks (CRITICAL — these catch shallow/generic specs):**
- A capability bucket in `## 3.` with <3 BRs (counting Bin 1 inline + Bin 2/3 references) for
  UI features → warning (shallow extraction)
- SM/ALG/INT block, or a BR/DEC wherever it lives, missing `**Source:** file:line-range`
  citation → critical
- `**Source:**` cites a non-existent file or invalid/unverified range → critical
- `## 2.` row missing for an FR/BR/DEC/SM/US code declared in the twin → critical (completeness
  half of `FeatureSpec.action_unclaimed`)
- `#### {US###}` sub-block under `### 5.1` missing `**Independent Test:**` or Given/When/Then →
  critical
- Acceptance scenarios without Given/When/Then structure → warning (vague criteria)
- `## 2.`'s `Method · Path` column missing an endpoint that a § 3 action block's request rung
  cites → warning (successor to the retired `### 3.4 API & Endpoints` cross-check — the surface
  moved, the check does not)
- `### 3.{N+1} Edge cases` (feature-wide, at the end of `## 3. Actions`) missing → critical (the
  plain-language twin lives in `functional-spec.md § 9`)
- `### 3.{N+1} Edge cases` with <3 rows for UI features or <1 for background features → critical
  (shallow)
- Edge case rows missing HTTP status code or specific error message → warning
- `### 4.2 Data Model` entity table missing or has 0 entity rows → critical
- `### 4.2 Data Model` entity table without database table names (just model codes) → warning
- `### 4.2 Data Model` entity table with <3 entities for non-trivial features → warning (likely
  incomplete)
- `### 5.4 Source References` missing or has 0 entries → critical
- `### 5.4 Source References` with <3 entries → warning (likely incomplete)
- `### 5.4 Source References` entries without file path line ranges → warning
- `### 5.2 Assumptions` missing or has 0 entries → warning
- `### 5.2 Assumptions` with <2 entries for non-trivial features → warning
- `### 5.3 Unresolved Questions` missing → warning (expected for complex features)
- `### 5.5 Artifact References` missing or has 0 rows → critical
- `### 5.5 Artifact References` missing System Overview or Feature List rows → critical (both
  are always-required, always-reviewed)
- `### 5.5 Artifact References` Codes Used column empty for non-overview rows when feature uses
  that artifact → warning (should list specific codes)
- Same BR/SM/ALG/INT/DEC code with a full `**Source:**` block appearing in 2+ places → critical
  (duplicate full block; secondary occurrences must be reference-only — a Bin 2 rule's
  reference line in a using action's Rule rung is NOT a duplicate as long as it has no
  `**Source:**` of its own)
- `### 4.1`/`4.3`/`4.5`/`4.6` subsection blank (no `None.` under an empty section) → critical
- Any SCR###/US###/ROUTE###/MODEL###/BL### from FeatureList absent from the pair → critical
- BR/SM/ALG/INT referencing FR-### not in same spec → critical
- Cross-spec BR/SM/ALG/INT/DEC ref (e.g., "see BR-001 in F002") → critical
- SM full block missing Mermaid `stateDiagram-v2` → critical
- Secret/credential leaked in pseudocode → critical
- `## Appendix` heading present in submitted draft → critical
- Pseudocode block > 20 lines → warning
- Pseudocode fence contains literal `{lang}` placeholder → warning
- US without priority → warning
- Legacy `## Related Artifacts` section present (deprecated) → **CRITICAL** (no transition
  window — use `### 5.5 Artifact References` table)
- Legacy `## Spec Documents` section present (deprecated) → **CRITICAL** (no transition window —
  use `### 5.5 Artifact References` table)
- **A3 (`## Source Walkthrough`) and B4 (`## DB Impact per Event`) retired from
  technical-spec.md in v27.8.0 (self-sufficiency release, `claude/skills/rebuild-spec/docs/decisions/ADR-0007.md`).**
  Neither heading belongs in a technical-spec.md draft any more — the § 2 Action Index +
  per-action `Source` (and `State`) rungs replaced both. A3 stays fully live on
  `screens/*/spec.md` only — see `verification-checklist-screen-spec.md`'s A6 rules /
  `_a3_fill_guard_lib.py` for that check.
- `## Source Walkthrough` or `## DB Impact per Event` still present in a technical-spec.md
  draft → warning `FeatureSpec.retired_section_present` (fires regardless of shape — old
  9-section, 5-bucket, or action-thread alike; strip via
  `run_doc_migrations.py --migrate --only action-thread`).

**Degradation contract — `FeatureSpec.tech_sections_pre_sot` (WARN-first, v27.x retaxonomy):**

**Detection predicate:** the spec still matches the retired 9-section shape — `## Cross-Cutting
Logic` is present as an H2. Mirrors `func.sections_pre_sot`'s design on the functional side: the
sentinel is the OLD shape's own distinguishing heading, not the absence of a new one.

**Muting behavior:** when it fires, every other rule in this TechnicalSpec section that is
defined in terms of the new 5-bucket shape is suppressed for that file — one finding for the
file's shape, not thirty. It does NOT mute `FeatureSpec.retired_section_present` (checks an axis
independent of the retaxonomy — a leftover A3/B4 heading can sit on an old 9-section file just
as easily as a reshaped one) or the Universal/cross-ref checks.

**Severity:** `warning` — the degradation window, mirroring `reading_guide.pre_migration`
(v26.0.0) and `func.sections_pre_sot` (P07) at document-wide granularity. Promotion to `critical`
is a follow-up, not P09 itself — it lands once a migrate composer can actually move a real corpus
through the retaxonomy.

**Second, independent degradation window — the action-thread reshape (v27.7.0):**

**Detection predicate:** `## 2. Action Index` is present (the file has reached the action-thread
shape) AND the file ALSO still carries `## 3. System Design` — the layer-first (P08) shape's own
distinguishing heading, never present in a fully-reshaped file
(`_spec_constants._TECH_PRE_THREAD_SENTINEL`). A file with NO `## 2. Action Index` at all is not
in this window — it has not started the reshape, and every one of the 5 action-thread rule_ids
(`FeatureSpec.action_index_missing`/`action_unclaimed`/
`action_key_not_handler`/`rung_order`/`rung_empty_rendered`) is simply silent for it (gated on
`## 2. Action Index`'s presence), not degraded. (A 6th, `action_double_claimed`, shipped and was
later retired outright — see `docs/decisions/ADR-0006.md`'s addendum — so it is no longer part of
this set at all.)

**Muting behavior:** while the sentinel is present, all 6 action-thread rule_ids above degrade
from their base severity to `warning`, with `(_pre_thread)` appended to the message —
`action_key_not_handler` is already `warning`, so degradation is a severity no-op for it, but its
message still gains the suffix (the "this file is mid-migration" signal applies uniformly). This
does NOT mute `FeatureSpec.required_sections`, `sysdesign_subsections`/`verification_subsections`,
`FeatureSpec.retired_section_present`, or the Universal/cross-ref checks — this window
is scoped to the 6 action-thread codes only, a narrower mute than
`FeatureSpec.tech_sections_pre_sot`'s whole-section mute above.

**Severity:** `warning`, same rationale as the first window — a corpus mid-migration between the
layer-first and action-thread shapes must not go red all at once.

**Third, independent degradation window — `diagram_required_missing` fill-pending (follow-up to
v27.7.0, plans/260824-1128-rebuild-spec-action-thread-v27-7):**

**Problem it closes:** `compose_action_thread` is deterministic/mechanical only — it can bind
rule ownership by handler/path match, but it cannot author a `sequenceDiagram`; drawing one needs
judgment, so it is the researcher fill pass's job, the same pass that resolves any rule the
composer marked `[UNVERIFIED]`. Measured on the real 43-feature sharetribe corpus: every
freshly-migrated file with an over-threshold action still lacking a diagram fires
`FeatureSpec.diagram_required_missing` as a hard `critical` (117 findings across 28/43 features)
even though the researcher pass that would draw the diagram has not run yet — "migrate then
validate" is red by construction, not because of a real defect.

**Detection predicate:** `_action_thread_diagram_lib.is_fill_pending(text)` — the whole file
still carries the `[UNVERIFIED]` tag. SAME tag `_doc_migration_action_thread_step_lib.
_UNVERIFIED_MARKER` counts into the `action-thread` migrate step's own rollback sidecar (and that
`ThreadComposeResult.needs_llm_fill` is computed from) — not a new marker invented for this
window; the composer already leaves this signature on disk for exactly this reason. Corpus-
measured honest: 0 of the 28 features that fire `diagram_required_missing` today carry zero
`[UNVERIFIED]` markers. A feature with no DEC blocks and every BR `Applies to:` resolved may
legitimately carry none even before a researcher ever looks at it (C11) — such a file is, correctly,
treated as already past this window.

**Muting behavior:** scoped to `FeatureSpec.diagram_required_missing` ALONE — none of the other 4
rule_ids in this same check function (`rule_bin_misplaced`, `crosscutting_unlabelled`,
`diagram_cites_file_line`, `diagram_over_cap`), nor the 5 action-thread rule_ids above, are
affected by this predicate. This is a narrower mute than either window above: one finding, one
signal, no adjacent amnesty.

**Severity:** `warning`, with `(_pre_fill)` appended to the message (distinct from `(_pre_thread)`
above — the two windows are independent and can, in principle, both apply). Reverts to hard
`critical` the moment the file's `[UNVERIFIED]` count reaches 0 — this is a promotion path, not a
permanent relaxation: a missing diagram in a fully-bound file is a real defect and must still block.

#### FunctionalSpec (functional-spec.md)

**Required sections (exact order, 13 H2s):** `## 1. Overview` → `## 2. Functional Capabilities`
→ `## 3. Open Decisions` → `## 4. Requirements` → `## 5. Business Rules` → `## 6. Screens` →
`## 7. User Stories` → `## 8. Scenarios` → `## 9. Edge Cases` → `## 10. Edge Behaviours to
Verify` → `## 11. Risks & Known Issues` → `## 12. Dependencies` → `## 13. Configuration`. Read
`_spec_constants.REQUIRED_H2_FUNC` for the authoritative list — do not copy the heading text out
of this file.

This is the file that replaces the retired `business-context.md` / `screens.md` /
`edge-cases.md` trio (see Deterministic Validator Coverage below for the old→new `rule_id` map).
It is also where `FR-###`/`BR-###`/`SM-###`/`DEC-###` are now **expected** — the old
business-context.md forbidden-token rule is inverted here (see Forbidden Tokens below). Net-new
in the v27.x human-readable-SOT retaxonomy: § 2 Functional Capabilities, § 11 Risks & Known
Issues, § 12 Dependencies (renumber map: old 1→1, 2→3, 3→4, 4→5, 5→6, 6→7, 7→8, 8→9, 9→10,
10→13). **This half is already live (P07)** — the checks below execute today.

- **§ 1 Overview**: Problem, Solution, Scope, Non-Scope all present as distinct labeled fields;
  an Actors table with ≥1 row. Problem must reference a real user problem, not "system feature."
- **§ 2 Functional Capabilities**: `ID | Capability | What the user can do | User Stories |
  Requirements | Business Rules | Screens` table with ≥1 `CAP-###` row once § 4 declares any real
  FR-### (`func.capabilities_empty` warns otherwise); every `Requirements` cell cites an FR-###
  that exists in § 4 (`func.capability_fr_dangling`, critical, on a phantom cite). Every
  US###/FR-###/BR-###|DEC-###|SM-###/SCR### declared anywhere in §§ 4-7 must be claimed by
  **exactly one** § 2 row per the researcher contract's exhaustiveness rule (SCR carries a region
  caveat there — a composite `SCR###/REG###` is its own claim, distinct from the bare parent and
  from sibling regions) — enforced by `cap.code_unclaimed` (critical, a declared code claimed by
  zero rows; message opens with the grep-able `family=US|BR|FR|SCR` token) and `cap.double_claimed`
  (critical, a code claimed by two or more rows). `cap.claims_unfilled` (warning) fires instead of those two, whole-file, when
  § 2 has ≥1 data row and EVERY row's claim cells are empty — the structural window right after a
  `--migrate --only cap-map` widening and before a human fills the claims; partial fill is never
  muted, only the all-empty state is.
- **§ 2 count-based review triggers (phase 06, capability-map plan — D-7: the count NEVER forces a
  split, it forces a written decision):** once § 2's claim state is not "unfilled" and `#CAP == 1`,
  the feature's US/BL count is checked against its type's band —
  `ui` keys on distinct `US###` in § 7 (warn 3-4, crit ≥5); `background` keys on distinct `BL###`
  in the twin `technical-spec.md` (warn 5-7, crit ≥8 — **provisional**, scaled ~1.6× off the `ui`
  bands against n=8 background features in one corpus; re-measure once a second real corpus with
  background features exists); `mixed` evaluates BOTH rows and takes the STRICTER outcome (a
  `mixed` feature heavy on one axis and light on the other is not allowed to escape both bands).
  `#CAP ≥ 2` silences everything below, for every type — the count never forces a split.
  In the warning band: `cap.review_advised` (warning, no rationale requirement — a nudge, not a
  gate). At or over the critical band: `cap.analysis_required` (critical) fires UNLESS a
  `**Single-capability rationale:**` line satisfies all three deterministic conditions — (a) a
  same-line, non-empty body; (b) ≥12 words; (c) names ≥2 DISTINCT codes of the type's family
  (US for `ui`, BL for `background`, either for `mixed`), and every named code exists in this
  feature's own declared set. All three are checked in Python, never delegated to an LLM (Iron
  Law #1 reserves FAIL for Engine 1) — this is what makes the hatch un-rubber-stampable rather than
  a bare presence check. A qualifying rationale silences `cap.analysis_required` but still makes
  the feature an E3 `CAP_MULTI_INTENT` candidate in phase 10 (non-blocking, evidence only). Full
  rule: `references/code-formats.md` § "Capability-Level Intent (authority)" — cited by name here,
  not restated. **[SC-3] Consumer boundaries for `cap.review_advised`:** the warning reaches a
  human reviewer via `--summary-out` → `merge_validator_result` → `buildFsValidatorPreamble`
  (`references/pipeline-feature-specs.md`), which prints every issue severity-agnostic into the
  FS.5 review prompt — but (a) that path exists only in the AUTHORING pipeline and only when
  `--summary-out` is passed; a corpus-time run against `docs/features/` has no consumer at all; and
  (b) the preamble renders exactly `severity`/`rule_id`/`location`/`message` — anything not in the
  message is invisible to that reviewer.
- **§ 2 promote-eligibility advisory, Tier 1 only (phase 08, capability-map plan):** once § 2's
  claim state is not "unfilled" and `#CAP >= 2`, each row's own claimed counts are checked against
  fixed floors — `cap.promote_candidate` (warning) fires when a single row claims `>= 3` US **AND**
  `>= 3` FR **AND** `>= 1` SCR. Every count comes from the § 2 table's own claim cells
  (`_cap_claims`, phase 05) — never a fresh §§ 4-7 parse. Because phase 05's exhaustiveness already
  guarantees every code belongs to exactly one CAP row, an overlap check would carry zero
  information; the signal is magnitude — the measured sharetribe-corpus median WHOLE feature
  carries 2 US, so a single CAP row claiming >= 3 US already exceeds it. `#CAP >= 2` is required
  because a lone CAP cannot be "promoted" — promoting it is just renaming the feature. **Tier 1
  only:** this is an advisory that writes NOTHING — no rename, no directory creation, no sentinel.
  Tiers 2/3 (a corpus-wide F###-reference enumerator and a directory-move migrate step) do not
  exist anywhere in this repo; the message says promotion is a manual, human-decided operation
  today and names no `--migrate` flag, because none implements it (Plan B). **[SC-3] Consumer
  boundaries for `cap.promote_candidate` — identical shape to `cap.review_advised` above, verified
  there by assertion, inherited here rather than re-verified:** (a) the warning reaches a human
  only via `--summary-out` → `merge_validator_result` → `buildFsValidatorPreamble`, in the
  AUTHORING pipeline only — a corpus-time run against `docs/features/` has no consumer at all; (b)
  the preamble renders exactly `severity`/`rule_id`/`location`/`message` — the four observed counts
  live in `message`, or they are invisible to that reviewer.
- **§ 3 Open Decisions**: table with columns `D### | Decision | Default proposal | Rationale |
  Blocks work`, OR the literal fallback `None — no unresolved domain confirmations.`. Every
  `[NEEDS_DOMAIN_CONFIRMATION]` marker found anywhere in the researched material for this feature
  MUST correspond to exactly one row here.
- **§ 4 Requirements**: every `FR-###` declared in `technical-spec.md § 2` has exactly one line
  here (`- **FR-###** {one sentence}`), grouped under a band matching its number (0xx foundation /
  1xx navigation / 2xx-3xx per-screen / 4xx interaction / 6xx security). No endpoint, no handler
  name, no pseudocode.
- **§ 5 Business Rules**: every `BR-###`/`DEC-###`/`SM-###` declared in `technical-spec.md` has
  exactly one line here, code as a trailing tag (e.g. `... (BR-001)`). A line that reads like an
  observed defect ("should not"/"incorrectly"/"bug") with no § 11 counterpart is flagged by
  `func.risk_as_rule` (warning) — record the defect in § 11 instead of folding it into a rule.
- **§ 6 Screens**: 4-column table (`Screen Name | SCR### | What User Sees | What User Can Do`)
  for UI/mixed features; `N/A — background feature; no user-facing screens.` for background-only.
  Each `SCR###` resolves to a `screen-list.md` row (`validate_feature_screen_link.py`). `###
  User Journey` H3 follows, numbered steps referencing screen names, NOT routes/endpoints.
- **§ 7 User Stories**: each block opens with **Actor** / **Goal** / **Business value**
  bold-labeled fields (Actor matching a § 1 Actors row) before its optional narrative
  (`func.user_story_shape`, warning, when a block skips one of the three) — the Actor → Goal →
  Business value shape the client's guidelines ask for. Then `**Acceptance Criteria:**`
  checkboxes for the SAME `US###` codes referenced (never restated) in `technical-spec.md § 2`.
  NO Endpoint / Data Required / Dependencies fields — those belong to `technical-spec.md`.
- **§ 8 Scenarios**: Given/When/Then; at least one happy-path and one error scenario per `US###`
  in § 7.
- **§ 9 Edge Cases**: table `Scenario | What Happens | User-Facing Message`; ≥3 rows for UI
  features, ≥1 for background. "User-Facing Message" must be plain language; a bare HTTP status
  code alone is REJECTED.
- **§ 10 Edge Behaviours to Verify**: one line per behaviour, `**FR-###**` bold,
  back-referencing a code declared in § 4.
- **§ 11 Risks & Known Issues**: `ID | Type | Description | Impact | Status` table, or the
  literal fallback `N/A — none found.`. `Type` ∈ `known-issue` (observed abnormal current
  behavior) | `risk` (future exposure). A row here MUST NOT be rewritten into a § 5 line and MUST
  NOT be "fixed" by the spec — quote the hard rule (target-shape-spec.md § 5) to a reviewer who
  asks why: "Never promote an observed current behavior into a SHOULD. If code does X and X looks
  wrong, write X, mark it, and open a § 11 Risks & Known Issues row. Do not invent, do not fix, do
  not delete as 'merely technical'."
- **§ 12 Dependencies**: `Dependency | Type | Why this feature needs it | Evidence` table, or
  `N/A — none found.`. `Type` ∈ `feature` (another F###) | `external-service` | `data` |
  `infrastructure` | `config`.
- **§ 13 Configuration**: one fenced block of `NAME = value  # comment` lines, or `N/A — no
  user-facing configuration constants for this feature.`.

**Forbidden Tokens (dev-token + secret-shape scan, inverted from business-context.md):**
- Class names, `` `file:line` `` citations, HTTP verbs (`GET`/`POST`/`PUT`/`DELETE`/`PATCH`),
  pseudocode, outside a fenced code block or HTML comment → critical (auto-validated,
  `func.dev_token`). **Known limitation, on record, not silently trusted:** the pattern
  (`FUNC_DEV_TOKEN_RE`) only catches HTTP verbs and `path.ext:123` shapes — bare class/job/mailer
  names (`SessionsController`, `PasswordResetJob`) read past it. A reviewer catches those via
  `func.dev_identifier_leak` (see the researcher contract's worked examples) — this is a
  reviewer-only judgment call, not automatable without unbounded false positives on ordinary
  business nouns.
- Secret-shaped values (API keys, DSNs, tokens, connection strings) outside a fence → critical
  (auto-validated via `scrub_generic_secret` + `scrub_credentials`, H-SEC4, `func.secret_shape`).
- `FR-###`/`BR-###`/`SM-###`/`DEC-###`/`SCR###`/`US###` codes are ALLOWED — do NOT flag them.
- `[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]`/`[EXPECTED]` status markers (D6) are
  ALLOWED — do NOT flag them. This is the only relaxation to the forbidden-token rule.

**Rule density (mechanically checked, success metric #1):**
- Avg lines per rule across § 4 + § 5 entries > 2 → warning `func.rule_density` (a single
  overlong entry is not itself critical — the metric is an average, per the plan's Validation
  Decision V1; long-single-line evasion is an accepted risk on record).

**Plain-language rubric (reviewer manual check, carried from the retired BusinessContext
rubric):**
- **Persona clarity**: each persona in § 1 Actors named with role + concrete action; not "the
  user" only.
- **Requirement/rule specificity**: § 4/§ 5 lines use business verbs and observable outcomes,
  not technical verbs ("dispatches", "hydrates").
- **Jargon score**: zero forbidden tokens (auto-validated); plus subjective check for terms like
  "endpoint", "schema", "controller" leaking into prose (`func.dev_identifier_leak`'s territory).
- Rubric scoring: 0–3 per criterion; threshold ≥2 = pass.

**Critical edge cases:**
- Functional spec missing / empty → critical
- Required H2 absent or out of order (any of the 13) → critical, UNLESS `func.sections_pre_sot`
  has already fired for this file (see Degradation Contract below), in which case this check —
  and every other section-bound check in this subsection — is muted for that file.
- Forbidden token (dev-token or secret-shape) detected outside a fence → critical
  (auto-validated); a status marker is NOT a forbidden token (D6)
- § 3 Open Decisions row missing `Default proposal` or `Blocks work` → critical
  (`func.open_decisions_shape`)
- A `[NEEDS_DOMAIN_CONFIRMATION]` marker left inline anywhere in either file (not promoted to a
  § 3 row) → critical (`func.open_decisions_shape`); `[EXPECTED]` never triggers this — it does
  not promote (confidence-report-contract.md § "v27 amendment — the 4th state")
- § 2 Functional Capabilities has 0 rows while § 4 already declares ≥1 real FR → warning
  (`func.capabilities_empty`)
- § 2 row cites an FR-### not declared in § 4 → critical (`func.capability_fr_dangling`)
- § 4/§ 5 missing a one-line entry for an FR-###/BR-###/DEC-###/SM-### declared in
  `technical-spec.md` → critical (`func.code_unsurfaced` — code stated in the dev file but never
  surfaced to BA/QA)
- § 4/§ 5 entry for a code NOT declared anywhere in `technical-spec.md` → critical
  (`func.code_orphan` — phantom code)
- § 5 line reads like an observed defect with no § 11 counterpart → warning (`func.risk_as_rule`)
- § 6 Screens missing for a UI/mixed feature → critical
- § 6 SCR### column present but a code does not resolve to `screen-list.md` → critical
  (`func.screens_scr_unresolved`); column entirely absent on an un-migrated doc → warning
  (`link.pre_migration`, non-blocking)
- § 6 User Journey references routes/endpoints instead of screen names → warning
- § 7 User Story block missing one of **Actor**/**Goal**/**Business value** → warning
  (`func.user_story_shape`)
- § 7 User Story missing `**Acceptance Criteria:**` checkboxes → critical
- § 7 carries an Endpoint / Data Required / Dependencies field → warning (dev detail leaking
  into the BA file; belongs in `technical-spec.md`)
- § 8 Scenario missing Given/When/Then structure → warning (vague criteria)
- § 8 has zero error scenarios for a US### that has ≥1 error edge case in § 9 → warning
- § 9 table missing or has 0 rows → critical
- § 9 with <3 rows for UI features → critical
- § 9 "User-Facing Message" contains a raw HTTP code without explanation → warning
- § 10 entry not back-referencing an FR-### present in § 4 → critical
  (`func.edge_behaviour_dangling` — dangling verification ref)
- § 11 row rewritten as if it were a § 5 Business Rule, or edited to read as "fixed" → warning
  (reviewer judgment — enforces the never-self-fix rule)
- § 12 row missing an Evidence code/pointer → warning (reviewer judgment)
- "Why It Matters"-equivalent (§ 1 Problem) reads as fabricated rationale → warning
- If feature participates in a cross-feature flow → plain-language cross-ref to `flows/{slug}.md`
  present in § 1; absent → warning

**Degradation contract — `func.sections_pre_sot` (WARN-first, v27.x retaxonomy — LIVE, shipped
in P07):**

**Detection predicate:** the spec still matches the retired 10-section shape — `## 2. Open
Decisions` is present as an H2 (that exact string never appears in the new 13-section shape;
Open Decisions moved to `## 3.`).

**Muting behavior:** when it fires, `func.missing_h2` and every section-bound check in this
FunctionalSpec section (old shape AND new shape alike) are skipped for that file — one finding
for the file's shape, not a wall of findings keyed on headings that do not exist yet.
Content-level scans unrelated to section shape (`func.dev_token`, `func.secret_shape`) are NOT
part of this muting — they still run.

**Severity:** `warning` — the degradation window. Promotion to `critical` is a follow-up, not
this phase (mirrors the existing `reading_guide.pre_migration` precedent, v26.0.0).

### FlowsDraft (per inferred flow, `flows/{slug}.md`)

**Cross-refs:** UserStories, ScreenFlow

- Frontmatter present: `status: ai-draft | human-curated`; `source: [US###, SCR###, ...]`; `generated: ISO-8601`.
- Slug kebab-case ≤40 chars; no collision with existing flow file (unless suffixed -2/-3 with `[WARN]`).
- Spans ≥2 features (cross-feature requirement); single-feature flows belong in the feature's `functional-spec.md § 6`.
- Plain-language: same forbidden-tokens regex as FunctionalSpec. Any match = critical.
- "Open Questions" section present (may be `None.`).
- `## Diagram` section present after `## Steps`; contains a fenced ` ```mermaid ` block with at least 3 lines (non-empty diagram).
- Mermaid block opens with `flowchart TD` directive.
- Simplified flows (>10 steps or >3 diamonds): mermaid block contains `%% simplified: complex flow` comment on first line inside the block.
- `flows/.completed` marker present after FL.1 completes (former W6.8) (zero-byte if flows emitted; contains `no_flows_inferred` if zero-output).

> **Note:** process-flow files are reviewed by the flows pass FL.3 reviewer (see `pipeline-flows-glossary.md`); the FL.2 liveness validator (former W6.85) enforces deterministic citation/format checks before FL.3.

**Critical edge cases:**
- Frontmatter missing or malformed → critical
- `source:` entries empty → critical
- Transition row without `file:line` citation → critical (contract violation)
- Forbidden token in prose → critical
- `.completed` marker absent after FL.1 task completes (former W6.8) → warning (task may have failed silently)
- Derived view modeled as stored state → critical (fabricated state)

### Large Feature Handling

- If feature dir total > 500 lines across the 2 files, orchestrator reduces FS.5 batch size to 2-3 features.
- W7a reviewer processes core artifacts >600 lines section-by-section. Reviewer agent MUST NOT skip sections — receives section range in TaskCreate description.
- **v27.7.0 (action-thread reshape) — the line-count trigger for `technical-spec.md` is RETIRED,
  replaced by a count-gated capability-chunk decision.** `scripts/decide_action_chunking.py`
  (called by the orchestrator, per `references/pipeline-feature-specs.md § Wave FS.1`) chunks
  generation by CAPABILITY when the feature's `## 2. Action Index` row count is
  `>= REBUILD_ACTION_CHUNK_THRESHOLD` (default 15, env-overridable) AND the twin functional-spec
  has `>= 2` capabilities — never on a line count. Output still merges to ONE
  `technical-spec.md` (D6, LOCKED) via the same fragment/merge mechanism as
  `plans/260602-2230-rebuild-spec-chunked-artifact-generation/`. See that reference file for the
  full fragment path and merge-step shape. **Out of scope, deliberately:** `estimate_artifact_loc.py`
  / `docs.maxLoc` is a DIFFERENT mechanism (core-artifact/api-contracts sharding, LOC-based) —
  feature specs never went through it and this reshape does not touch it.


## Deterministic Validator Coverage

These `rule_id`s are pre-checked by `scripts/validate_*.py` BEFORE the FS.5 reviewer runs. When `fs-validation-summary.json` reports a rule as `PASS`, the reviewer marks that rule `[deterministic-pass]` and focuses on semantic depth instead. When a rule is `FAIL`, the orchestrator dispatches an `implementer` fix cycle before FS.5 runs (see `pipeline-feature-specs.md § Wave FS.2`).

### v27.0.0 — old → new `rule_id` migration (`_check_business_context`/`_check_screens`/`_check_edge_cases` retirement)

The 3 dead checkers being retired (`_check_business_context` / `_check_screens` / `_check_edge_cases`
in `scripts/validate_feature_spec.py`) emit **7** `rule_id`s total, re-verified by direct code
read against the current file (`_issue(...)` call sites): `bc.missing`, `bc.missing_h2`,
`bc.forbidden_token` (3, from `_check_business_context`); `screens.missing`, `screens.missing_h2`
(2, from `_check_screens`); `edge_cases.missing`, `edge_cases.few_rows` (2, from
`_check_edge_cases`). All 7 are re-homed below under `_check_functional_spec` — zero silently
dropped. Two rows split 1-to-many (the inverted forbidden-token scan grew a second family), and
two rows are subsumed into the generic required-H2 check because their file no longer exists
standalone — both documented with a reason, per the "old set ⊆ new set ∪ documented-dropped set"
success criterion.

| old rule_id | old severity | new rule_id | new severity | disposition |
|-------------|---------------|-------------|----------------|-------------|
| `bc.missing` | critical | `func.missing` | critical | direct rename — `functional-spec.md` is now the one BA/QA file |
| `bc.missing_h2` | critical | `func.missing_h2` | critical | generalized from the 3-section BC list to the (now 13-section) `REQUIRED_H2_FUNC` list |
| `bc.forbidden_token` | critical | `func.dev_token` | critical | split 1/2 — class names / `file:line` / HTTP verbs / pseudocode outside fences |
| `bc.forbidden_token` | critical | `func.secret_shape` | critical | split 2/2 — secret-shaped values outside fences (H-SEC4; new family, not present in the old check) |
| `screens.missing` | critical | *(subsumed)* | — | dropped — `screens.md` no longer exists as a standalone file; its presence is covered by `func.missing_h2` (§ 6 is one of the 13 required H2s) |
| `screens.missing_h2` | critical | `func.screens_scr_unresolved` | critical | narrowed — was "does `## Screen List`/`## User Journey` exist," now "does § 6's SCR### column resolve to `screen-list.md`" (carries the `validate_feature_screen_link.py` contract forward) |
| `edge_cases.missing` | critical | *(subsumed)* | — | dropped — `edge-cases.md` no longer exists as a standalone file; its presence is covered by `func.missing_h2` (§ 9 is one of the 13 required H2s) |
| `edge_cases.few_rows` | warning | `func.edge_cases_few_rows` | warning | direct rename — same ≥3 UI / ≥1 background threshold, now checked within § 9 |

### v27.x — human-readable SOT retaxonomy (P07 functional half — LIVE; P08/P09 technical half — pending)

**Functional half (already shipped, P07).** New `rule_id`s with no legacy predecessor, needed to
enforce the 13-section shape plus the three-way Open Decisions / Unresolved Questions / Risks &
Known Issues split (pass B implements these under `_check_functional_spec`):

| new rule_id | severity | checks |
|-------------|----------|--------|
| `func.sections_pre_sot` | warning | file still matches the old 10-section shape (`## 2. Open Decisions` present) — degradation window, mutes every other section-bound check for that file |
| `func.rule_density` | warning | avg lines per rule across § 4 + § 5 > 2 |
| `func.open_decisions_shape` | critical | § 3 table missing `Default proposal` or `Blocks work` column, or a `[NEEDS_DOMAIN_CONFIRMATION]` marker left unpromoted |
| `func.code_orphan` | critical | § 4/§ 5 entry cites a code not declared in `technical-spec.md` (phantom code) |
| `func.code_unsurfaced` | critical | an FR-###/BR-###/DEC-###/SM-### declared in `technical-spec.md` has no matching one-liner in § 4/§ 5 |
| `func.edge_behaviour_dangling` | critical | § 10 entry back-references an FR-### not present in § 4 |
| `func.capabilities_empty` | warning | § 2 Functional Capabilities has 0 rows while § 4 Requirements already declares ≥1 real FR-### |
| `func.capability_fr_dangling` | critical | a § 2 "Requirements" cell cites an FR-### not declared in § 4 |
| `func.risk_as_rule` | warning | a § 5 Business Rules line reads like an observed defect ("should not"/"incorrectly"/"bug") with no § 11 counterpart recorded |
| `func.user_story_shape` | warning | a § 7 User Story block is missing one of **Actor:**/**Goal:**/**Business value:** |
| `cap.code_unclaimed` | critical | A US###/FR-###/BR-###\|DEC-###\|SM-###/SCR### declared in §§ 4-7 is claimed by zero § 2 rows. Message opens with `family=US\|BR\|FR\|SCR` — filter on that token to select one family |
| `cap.double_claimed` | critical | A code is claimed by two or more § 2 rows (should be exactly one; a composite `SCR###/REG###` is its own token, so two rows owning different regions of one screen is not a collision — see researcher contract's region caveat); message names every claiming CAP id, sorted |
| `cap.claims_unfilled` | warning | § 2 has ≥1 data row but EVERY row's User Stories/Requirements/Business Rules/Screens cells are empty (all-or-nothing — a partially-filled table keeps `cap.code_unclaimed` live instead). Mutes `cap.code_unclaimed`/`cap.double_claimed` for the file while it fires |
| `cap.analysis_required` | critical | (phase 06) `#CAP == 1`, claim state not "unfilled", US/BL count at or over the type's CRITICAL band, and no `**Single-capability rationale:**` line satisfying all 3 deterministic conditions (same-line non-empty body, ≥12 words, ≥2 distinct declared codes cited) — D-7: the count never forces a split, only a written decision |
| `cap.review_advised` | warning | (phase 06) `#CAP == 1` and the US/BL count sits in the type's WARNING band. No rationale requirement; non-blocking. [SC-3] reaches a reviewer only via `--summary-out` (authoring pipeline only) — see § 2 prose above for both consumer boundaries |
| `cap.promote_candidate` | warning | (phase 08, Tier 1 only) `#CAP >= 2` and a single row claims `>= 3` US **AND** `>= 3` FR **AND** `>= 1` SCR — message names the CAP id, its Capability name, and all four observed counts. Advisory only: writes nothing, names no automated promotion command (none exists — Plan B). [SC-3] consumer is identical to `cap.review_advised`'s — reaches a reviewer only via `--summary-out` (authoring pipeline only), message-only rendering — see § 2 prose above for both boundaries, verified there, inherited here |

**Technical half — P08 layer-first shape (LANDED, then RETIRED as the target — see below).**
The rule_ids below were the P08 (layer-first, "5-bucket") target and are what
`FeatureSpec.required_sections`/`sysdesign_subsections`/`verification_subsections` still check
against in the shipped validator today, pending the exact-order repoint noted throughout this
file:

| rule_id | severity | checks | disposition |
|-------------|----------|--------|-------------|
| `FeatureSpec.tech_sections_pre_sot` | warning | file still matches the pre-P08 9-section shape (`## Cross-Cutting Logic` present) — degradation window, mutes the other tech rules | retained |
| `FeatureSpec.sysdesign_subsections` | critical | (P08 shape) `### 3.1`–`### 3.7` missing or out of order | replaces `FeatureSpec.ccl_subsections`; re-targeted to `### 4.1`–`### 4.6` under the action-thread shape, below |
| `FeatureSpec.verification_subsections` | critical | `### 5.1`–`### 5.5` missing or out of order | UNCHANGED by the action-thread reshape |
| `FeatureSpec.capability_buckets_missing` | critical | (P08 shape) `## 4.` has no `### 4.\d+ ` child | re-targeted to `## 3.` under the action-thread shape, below |
| `FeatureSpec.capability_twin_skew` | warning | a capability-bucket H3 with no matching `CAP-N` in the twin's `## 2.`, or vice versa | UNCHANGED in predicate, re-targeted from `### 4.N` to `### 3.N` |
| `FeatureSpec.mapping_table_missing` | critical | (P08 shape) `## 2.` absent, empty, or with no FR/BR/US code in any `Code` cell | superseded by `FeatureSpec.action_index_missing`/`action_unclaimed` under the action-thread shape, below |
| `FeatureSpec.mapping_restates_story` | warning | (P08 shape) a `## 2.` `Name` cell longer than ~120 chars or containing `Given`/`When`/`Then` | superseded — the action-thread § 2 Action Index has no `Name` cell to restate a story in; the duplication guard is now structural (the row states handler/path/tables, nothing else fits) |
| `FeatureSpec.us_narrative_present` | warning | a `**What happens:**` field survives anywhere | UNCHANGED by the action-thread reshape |
| `FeatureSpec.polymorphic_behavior_present` | critical (unchanged) | **shipped code still checks `### 3.2 Data Model`** (gated on `## 3. System Design`, P08 shape); TARGET is `### 4.2 Data Model` under the action-thread shape — re-wiring is a known validator gap, not yet done | retained, re-homing to § 4.2 is future work |
| `FeatureSpec.decision_logic_section_present` | critical (unchanged) | (P08 shape) looked under `## 4.` | **retired under the action-thread shape** — DEC is now a table row inline in a Rule rung, so "a Decision Logic section exists under the capability bucket" is no longer a meaningful check; no direct successor rule_id exists yet |

**Technical half — action-thread shape (v27.7.0, PARTIALLY LANDED; self-sufficiency v27.8 adds 2
more).** `_check_action_thread` in `validate_feature_spec.py` implements the 7 LIVE rule_ids
below, gated on `## 2. Action Index` being present (silent otherwise — see the action-thread
degradation window above). **Corrected (self-sufficiency v27.8):** an earlier revision of this
checklist claimed the three-bin `crosscutting_unlabelled` check and the diagram contract's
`diagram_cites_file_line`/`diagram_over_cap` checks were an unwired "known validator gap" — that
was stale even before this phase; all three have been wired for some time, in a sibling function
(`_check_rule_bins_and_diagrams`, table below), together with `rule_bin_misplaced` and
`diagram_required_missing`. The genuinely still-open gap is narrower: the § 4.2 Polymorphic
Behavior re-wiring (line above) only:

| new rule_id | severity | checks |
|-------------|----------|--------|
| `FeatureSpec.action_index_missing` | critical | `## 2. Action Index` absent, or present with zero data rows (the mandatory `A0` row must always be present) |
| `FeatureSpec.action_key_not_handler` | warning | a non-`A0` row's `Action (handler)` cell is the bare `` `METHOD PATH` `` fallback shape (D2 — the handler IS the action's identity) |
| `FeatureSpec.action_unclaimed` | critical | a US###/FR-###/BR-###/DEC-###/SM-### declared in § 3 Actions or § 4 Shared Foundation claimed by zero § 2 rows (nor `A0`); message opens with `family=` |
| `FeatureSpec.rung_order` | critical | rungs inside one `#### A<n>` block appear out of `RUNG_LABELS` order (presence of every rung is never required — only the relative order of whichever rungs a block does carry) |
| `FeatureSpec.rung_empty_rendered` | critical | a rendered rung's body is empty, `N/A`, or `None.` — an absent rung must be omitted, never stubbed |
| `FeatureSpec.state_rung_missing` | warning, degrades identically to `diagram_required_missing` (`is_pre_thread` OR `is_fill_pending`) | (self-sufficiency v27.8, D8 re-anchor) BOTH hold: the feature carries a real `### … (SM-###)` heading block ANYWHERE in the document, AND this action's § 2 `Writes` cell is non-`—` — but the block renders no `**State**` rung. Document-level anchor, never per-action Codes-cell (that anchor fired on 1 action corpus-wide, HALT) |
| `FeatureSpec.action_ref_unglossed` | warning, same degradation window | (self-sufficiency v27.8) a BR/DEC/SM/ALG/INT/DISC code appears in a `#### A<n>` block and EVERY occurrence in that block is bare (see "Self-sufficiency of the H4 context line," `feature-spec-researcher-contract.md`) — implemented in a sibling function, `_check_action_ref_unglossed`, gated identically |
| ~~`FeatureSpec.action_double_claimed`~~ | — | **RETIRED** (shipped in phase 02, removed after phase 11): modelled Action Index codes as a partition ("claimed by exactly one row"), copied from `cap.double_claimed` where § 2 Functional Capabilities genuinely partitions. Actions do not — one requirement fanning out to several handling actions is normal (measured: 127 firings/31 features, 85% width=2, including on the plan's own B-v sample). Removed outright rather than demoted to a threshold warning: the measured distribution has no cutoff separating "implausible" from "a few more handlers." See `docs/decisions/ADR-0006.md`'s addendum. |

**Technical half — three-bin + diagram contract (v27.7.0, phase 03, LIVE).**
`_check_rule_bins_and_diagrams` in `validate_feature_spec.py` — a sibling function, gated
identically to `_check_action_thread` — implements these 5:

| rule_id | severity | checks |
|---------|----------|--------|
| `FeatureSpec.rule_bin_misplaced` | warning | a `Used in:` marker naming ≥2 actions sits inline in § 3 (belongs in § 4.4 Bin 2), or one naming exactly 1 action sits in § 4.4 (belongs inline in that action's § 3 block, Bin 1) |
| `FeatureSpec.crosscutting_unlabelled` | warning | inside § 4.4, an FR/BR/DEC/SM rule paragraph with no `Used in:` list, whose enclosing bin heading (or absence of one) does not say "cross-cutting" |
| `FeatureSpec.diagram_required_missing` | critical, degrades to warning while fill-pending (`is_pre_thread` OR `is_fill_pending`) | an over-threshold action's capability bucket carries no mermaid fence |
| `FeatureSpec.diagram_cites_file_line` | critical | a `path:line`-shaped token inside any mermaid fence — rungs carry facts, diagrams carry order/branching only |
| `FeatureSpec.diagram_over_cap` | warning, never critical (heuristic count) | a single mermaid fence with >12 arrow lines or >2 `alt` lines |

`FeatureSpec.ccl_blank` (the old "empty CCL subsection must contain `None.`" check) is subsumed
into `sysdesign_subsections`/`verification_subsections` above — the same predicate, applied to
the new H3 lists, has no reason to stay a separate rule_id once the H3 lists themselves changed.
`FeatureSpec.screen_flow_crossref`, `FeatureSpec.bw_steps`, `FeatureSpec.deprecated_headings`,
`FeatureSpec.no_appendix`, `FeatureSpec.edge_cases`, `FeatureSpec.br_linked_fr_present` were **out
of P09's stated scope** — unaffected by the P08 retaxonomy in predicate, only in section
location, and expected to keep working once P09's re-homing landed (the FR-linking and
deprecated-heading checks are string/regex checks that do not care which H2 they run under).

**Known gap, called out honestly rather than left to be discovered by a silent pass (v27.7.0
action-thread reshape):** `FeatureSpec.dec_blocks_well_formed` and `FeatureSpec.dec_lazy_na` were
also carried forward as "unaffected by retaxonomy" through P08, because P08 kept DEC as an H4
block (`DEC_BLOCK_RE`-shaped) and only moved WHERE that block lived. The action-thread reshape
changes the SHAPE, not just the location — `DEC-###` is now a table row inline in a Rule rung,
which `DEC_BLOCK_RE` will not match at all. Left unfixed, these two checks would find **zero** DEC
blocks on a correctly-shaped action-thread file and report a silent pass, which is exactly the
"a gate that cannot fail" defect this repo has hit before. **Not fixed here** (out of this
documentation phase's scope — it requires a `.py` change to `_check_dec_blocks`/`_spec_block_lib.py`)
— recorded as a named follow-up so it is fixed deliberately, not discovered by a false-green
review.

| rule_id | validator script | severity |
|---------|------------------|----------|
| existence.folder_missing | validate_feature_existence.py | critical |
| existence.folder_incomplete | validate_feature_existence.py | critical |
| existence.slug_format | validate_feature_existence.py | critical/warning |
| existence.orphan_folder | validate_feature_existence.py | warning |
| existence.canonical_missing | validate_feature_existence.py | warning |
| FeatureSpec.required_sections | validate_feature_spec.py | critical |
| FeatureSpec.ccl_subsections | validate_feature_spec.py (superseded by `sysdesign_subsections`/`verification_subsections`, pending P09) | critical |
| FeatureSpec.ccl_blank | validate_feature_spec.py (subsumed into the two above, pending P09) | critical |
| FeatureSpec.screen_flow_crossref | validate_feature_spec.py | critical |
| FeatureSpec.bw_steps | validate_feature_spec.py | critical |
| FeatureSpec.deprecated_headings | validate_feature_spec.py | critical |
| FeatureSpec.no_appendix | validate_feature_spec.py | critical |
| FeatureSpec.edge_cases | validate_feature_spec.py | critical |
| FeatureSpec.f_code_format | validate_feature_spec.py | critical |
| FeatureSpec.sm_mermaid | validate_feature_spec.py | critical |
| FeatureSpec.pseudocode_length | validate_feature_spec.py | warning |
| FeatureSpec.pseudocode_fence | validate_feature_spec.py | warning |
| Universal.no_placeholder | validate_feature_spec.py | critical |
| citation.file_missing | validate_source_citations.py | critical |
| FeatureSpec.linked_fr_missing | validate_feature_spec.py | critical |
| FeatureSpec.disc_boolean | validate_feature_spec.py | warning |
| citation.range_invalid | validate_source_citations.py | critical |
| citation.range_inverted | validate_source_citations.py | critical |
| citation.path_traversal | validate_source_citations.py | critical |
| citation.unreadable | validate_source_citations.py | warning |
| FeatureSpec.br_linked_fr_present | structural_fixer.py | critical |
| FeatureSpec.polymorphic_behavior_present | validate_feature_spec.py (re-homed under § 3.2, pending P09) | critical |
| FeatureSpec.decision_logic_section_present | validate_feature_spec.py (re-homed under § 4, pending P09) | critical |
| FeatureSpec.dec_blocks_well_formed | validate_feature_spec.py | critical/warning |
| FeatureSpec.dec_lazy_na | validate_feature_spec.py | warning |
| FeatureSpec.missing_client_behavior_anchor | validate_feature_spec.py (re-homed to end of § 3, pending P09) | critical |
| func.missing | validate_feature_spec.py | critical |
| func.missing_h2 | validate_feature_spec.py | critical |
| func.sections_pre_sot | validate_feature_spec.py | warning |
| func.dev_token | validate_feature_spec.py | critical |
| func.secret_shape | validate_feature_spec.py | critical |
| func.screens_scr_unresolved | validate_feature_spec.py | critical |
| func.edge_cases_few_rows | validate_feature_spec.py | warning |
| func.rule_density | validate_feature_spec.py | warning |
| func.open_decisions_shape | validate_feature_spec.py | critical |
| func.code_orphan | validate_feature_spec.py | critical |
| func.code_unsurfaced | validate_feature_spec.py | critical |
| func.edge_behaviour_dangling | validate_feature_spec.py | critical |
| func.capabilities_empty | validate_feature_spec.py | warning |
| func.capability_fr_dangling | validate_feature_spec.py | critical |
| func.risk_as_rule | validate_feature_spec.py | warning |
| func.user_story_shape | validate_feature_spec.py | warning |
| cap.code_unclaimed | validate_feature_spec.py | critical |
| cap.double_claimed | validate_feature_spec.py | critical |
| cap.claims_unfilled | validate_feature_spec.py | warning |
| cap.analysis_required | validate_feature_spec.py | critical |
| cap.review_advised | validate_feature_spec.py | warning |
| cap.promote_candidate | validate_feature_spec.py | warning |
| FeatureSpec.tech_sections_pre_sot | validate_feature_spec.py | warning |
| FeatureSpec.sysdesign_subsections | validate_feature_spec.py | critical |
| FeatureSpec.verification_subsections | validate_feature_spec.py | critical |
| FeatureSpec.capability_buckets_missing | validate_feature_spec.py | critical |
| FeatureSpec.capability_twin_skew | validate_feature_spec.py | warning |
| FeatureSpec.mapping_table_missing | validate_feature_spec.py (P08 shape; superseded by the row below under the action-thread shape) | critical |
| FeatureSpec.mapping_restates_story | validate_feature_spec.py (P08 shape; superseded, see the technical-half table above) | warning |
| FeatureSpec.us_narrative_present | validate_feature_spec.py | warning |
| FeatureSpec.action_index_missing | validate_feature_spec.py (`_check_action_thread`) | critical |
| FeatureSpec.action_key_not_handler | validate_feature_spec.py (`_check_action_thread`) | warning |
| FeatureSpec.action_unclaimed | validate_feature_spec.py (`_check_action_thread`) | critical |
| FeatureSpec.action_double_claimed | RETIRED — see ADR-0006 addendum; no longer wired anywhere | — |
| FeatureSpec.rung_order | validate_feature_spec.py (`_check_action_thread`) | critical |
| FeatureSpec.rung_empty_rendered | validate_feature_spec.py (`_check_action_thread`) | critical |
| FeatureSpec.state_rung_missing | validate_feature_spec.py (`_check_action_thread`) | warning, degrades |
| FeatureSpec.action_ref_unglossed | validate_feature_spec.py (`_check_action_ref_unglossed`) | warning, degrades |
| FeatureSpec.rule_bin_misplaced | validate_feature_spec.py (`_check_rule_bins_and_diagrams`) | warning |
| FeatureSpec.crosscutting_unlabelled | validate_feature_spec.py (`_check_rule_bins_and_diagrams`) | warning |
| FeatureSpec.diagram_required_missing | validate_feature_spec.py (`_check_rule_bins_and_diagrams`) | critical, degrades |
| FeatureSpec.diagram_cites_file_line | validate_feature_spec.py (`_check_rule_bins_and_diagrams`) | critical |
| FeatureSpec.diagram_over_cap | validate_feature_spec.py (`_check_rule_bins_and_diagrams`) | warning |
| BehaviorLogic.file_schema_missing | validate_behavior_logic.py | warning |
| BehaviorLogic.code_format | validate_behavior_logic.py | warning |
| FeatureSpec.alg_file_schema_missing | validate_feature_spec.py | warning |
| link.route_unresolved | validate_feature_api_link.py | critical |
| link.feature_unresolved | validate_feature_api_link.py | critical |
| link.owner_mismatch | validate_feature_api_link.py | critical |
| link.pre_migration | validate_feature_api_link.py | warning |
| link.unmapped | validate_feature_api_link.py | warning |
| link.inventory_absent | validate_feature_api_link.py | warning |
| gate.files_incomplete | check_promotion_gate.py | critical |
| gate.pending_marker | check_promotion_gate.py | critical |
| gate.validation_summary | check_promotion_gate.py | warning |
| reading_guide.pre_migration | validate_reading_guide_db_impact.py (screens/\*/spec.md only as of v27.8.0) | warning |
| reading_guide.malformed | validate_reading_guide_db_impact.py (screens/\*/spec.md only as of v27.8.0) | critical |
| reading_guide.unmapped | validate_reading_guide_db_impact.py (screens/\*/spec.md only as of v27.8.0) | warning |
| db_impact.pre_migration | RETIRED v27.8.0 — B4 left technical-spec.md; see ADR-0007 | — |
| db_impact.malformed | RETIRED v27.8.0 — B4 left technical-spec.md; see ADR-0007 | — |
| db_impact.unmapped | RETIRED v27.8.0 — B4 left technical-spec.md; see ADR-0007 | — |
| db_impact.uncited | RETIRED v27.8.0 — B4 left technical-spec.md; see ADR-0007 | — |
| FeatureSpec.retired_section_present | validate_feature_spec.py | warning |

> **Note (current shipped behavior, P08 shape — see the known-gap row above for the action-thread
> TARGET):** `FeatureSpec.polymorphic_behavior_present` only checks section presence (not N/A
> validity or value coverage — those require semantic reading). The validator checks: `####
> Polymorphic Behavior` heading exists under `### 3.2 Data Model`, gated on `## 3. System Design`
> being present — so it is silent (not failing, simply not evaluated) on an action-thread file
> that has already dropped that heading. Re-wiring this check to `### 4.2 Data Model` under
> `## 4. Shared Foundation` is a named follow-up, not done in this documentation phase.

> **Note (current shipped behavior — see the "Known gap" callout above for why this is now
> stale against the action-thread shape):** `FeatureSpec.decision_logic_section_present` checks a
> Decision Logic block presence under `## 4.` (covered by `FeatureSpec.capability_buckets_missing`
> at the bucket level). `FeatureSpec.dec_blocks_well_formed` checks structural fields per DEC
> block — **v27.0.0: 4 fields** (`subtype`, `Triggers in`, `Involved entities`, `Source`;
> `user_visible_outcome` dropped per D-f, forward-compatible if still present), pseudocode ≤8
> lines. `FeatureSpec.dec_lazy_na` uses grep to flag JSX-ternary patterns when section says N/A —
> raises warning for reviewer attention (not auto-fail). Source-file location is NOT validated per
> scope-agnostic rule. Both `dec_blocks_well_formed`/`dec_lazy_na` are DEC-H4-block-shaped checks
> and will find nothing to check on a table-row-shaped DEC under the action-thread reshape — see
> the "Known gap" callout above; not fixed here. `FeatureSpec.missing_client_behavior_anchor`
> currently checks for the `**Client behavior:** see` anchor at the end of `## 3. System Design`
> (P08 shape); TARGET under the action-thread shape is the end of `## 4. Shared Foundation` — same
> re-wiring gap as the two checks above.

Rules NOT in this table remain reviewer-only (e.g., FR/SC coverage cross-refs, BR depth
heuristics, cardinality cross-check, composite detection, `func.dev_identifier_leak` — these
need semantic judgement no deterministic script can safely automate).


## Failure Trap Assertions

- **Trap 1 (proliferation):** every REG has ≥1 independence signal, drawn from: distinct API endpoint (read or write), independent loading state, independent scroll container, independent auth / permission gate, distinct business workflow, distinct mutation surface / API cluster (distinct write endpoints or POST/PUT/DELETE namespace — even if the initial GET payload is shared), distinct validation / action path. Missing signal → critical. Visual separation alone is NOT sufficient.
- **Trap 2 (tab/stepper misclassification):** mutually-exclusive tab content declared as REG (not SCR variants) → critical. Wizard/stepper content: Case A emitted without cited distinct-validation + distinct-endpoint evidence → warning (prompt researcher to re-evaluate as Case B). 2-step wizard emitted as Case A → critical.
- **Trap 3 (shared data):** collapse two REG candidates into one Feature ONLY when they share ALL of: read surface (same GET endpoint/store) AND write surface (same mutations) AND business workflow. Shared initial payload alone does NOT disqualify a split — if regions diverge on write endpoints, validation rules, action paths, or business workflow, they remain separate. Researcher self-check advisory (NOT reviewer-enforceable critical — reviewer cannot inspect codebase at review time).
- **Trap 4 (LOC-based over-split):** LOC is NOT a composite signal. H3 uses named wrapper components only. Advisory note: flag any ScreenList entry where the researcher's justification cites line count rather than named wrappers or import count.
- **Trap 5 (spec orphan):** every REG### in ScreenList must have an owner annotation (can be `TBD`) → critical if owner annotation missing entirely.
- **Trap 6 (inferred-signal abuse):** `[SIGNAL_INFERRED]` tag without all 3 justification parts (Intent matched, No-row reason, Observed pattern) → critical. Tag citing H1 (which has no signal table) → critical; H2–H6 only. Tag used to bypass a per-stack row that DOES match the screen's stack/library naming → critical (researcher must use explicit row first). Tag count exceeding `max(5, ceil(0.10 × SCR_count))` across the entire ScreenList document → warning (suggests per-stack tables need updating or stack/library not covered).
