"""Shared spec structure constants. Stdlib only — zero imports.

Single source of truth for required H2 sections and skeleton content.
Referenced by validate_feature_spec.py and scaffold_spec.py.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Required H2 sections — ORDER IS LOAD-BEARING (validator checks exact order)
# ---------------------------------------------------------------------------


# P08 (human-readable SOT) — technical-spec.md's 9-section shape is RETIRED and replaced
# by the feedback's 5-bucket retaxonomy. This is a full-set replacement, not an incremental
# rename: all 9 old strings disappear (several become sub-sections instead of H2s), and
# `REQUIRED_CCL_H3` below is retired outright (see the two H3 constants that replace it).
# Order is load-bearing (validator checks exact order). `## 2.`'s headline job: fold the old
# CCL Requirements table + the old per-US narrative-duplication into ONE mapping table
# against functional-spec.md's FR/BR/US/AC codes. `## 4.`'s H3 children are DYNAMIC — one
# `### 4.N {Capability}` per CAP-N row in the twin functional-spec.md § 2 Functional
# Capabilities, in CAP- order; when § 2 is absent/empty exactly one bucket `### 4.1 {Feature
# name}` is emitted (validator/scaffold concern, P09). See
# plans/260818-1332-rebuild-spec-human-readable-sot/target-shape-spec.md § 3 (normative).
# RETIRED as a public name (rebuild-spec 27.7.0, phase 10, action-thread reshape).
# This used to be `REQUIRED_H2_TECH` — "the" required technical-spec.md H2 shape.
# Now that `REQUIRED_H2_TECH_THREAD` (below) is the current, final shape, this list
# means something narrower: the `feature-sot` migrate step's own OUTPUT shape
# (`_feature_sot_technical_lib.compose_technical_sot`, v26 -> v27), which the
# `action-thread` migrate step then reads as ITS input
# (`_feature_sot_extract_lib.extract_v27_thread_pieces`). Both of those are permanent,
# not transitional — a repo may run the two migrate steps on separate occasions, so
# this 5-bucket shape is a real, inspectable intermediate state, not dead code. Renamed
# to a private, migration-pipeline-only name so nothing outside those two modules (plus
# `_feature_sot_structure_lib.py`'s own private mirror of `REQUIRED_SYSDESIGN_H3`) treats
# it as "the" required shape any more; `validate_feature_spec.py`'s `required_sections`
# now accepts EITHER this shape or `REQUIRED_H2_TECH_THREAD` (see that module for why).
# Value is byte-identical to the pre-phase-10 `REQUIRED_H2_TECH` — only the name and its
# public/private status changed.
_LEGACY_TECH_H2_5BUCKET = [
    "## 1. Technical Overview",
    "## 2. Functional → Technical Mapping",
    "## 3. System Design",
    "## 4. Technical Behavior by Capability",
    "## 5. Verification & Technical Notes",
]

# v27.0.0 (audience split): business-context.md/screens.md/edge-cases.md are retired —
# replaced by the single functional-spec.md (BA/QA audience).
# v27.x (P07 human-readable-SOT): renumbered 10 -> 13 sections. Net-new: "## 2. Functional
# Capabilities" (the anchor technical-spec.md § 4 groups against), "## 11. Risks & Known
# Issues" (the third bucket — an observed defect is recorded here, never folded into a
# Business Rule and never "fixed"), "## 12. Dependencies". `Scope`/`Non-Scope`/`Actors` stay
# FIELDS inside § 1 Overview (see target-shape-spec.md § 4 Deviations) rather than becoming
# H2s — promoting them would be renumber churn with no reader gain. Renumber map (old -> new):
# 1->1, 2->3, 3->4, 4->5, 5->6, 6->7, 7->8, 8->9, 9->10, 10->13. Order is load-bearing
# (validator checks exact order), matching templates/functional-spec-template.md. See
# plans/260818-1332-rebuild-spec-human-readable-sot/target-shape-spec.md § 2 (normative).
REQUIRED_H2_FUNC = [
    "## 1. Overview",
    "## 2. Functional Capabilities",
    "## 3. Open Decisions",
    "## 4. Requirements",
    "## 5. Business Rules",
    "## 6. Screens",
    "## 7. User Stories",
    "## 8. Scenarios",
    "## 9. Edge Cases",
    "## 10. Edge Behaviours to Verify",
    "## 11. Risks & Known Issues",
    "## 12. Dependencies",
    "## 13. Configuration",
]

# ---------------------------------------------------------------------------
# P08 (human-readable SOT) — `REQUIRED_CCL_H3` is RETIRED. `## Cross-Cutting Logic`
# no longer exists as an H2; its old H3 children are redistributed across the new
# `## 3. System Design` (structure: components/data model/state/API/algorithms/
# integrations/config — capability-agnostic) and `## 4. Technical Behavior by
# Capability` (behavior: BR-###/DEC-### blocks, grouped per capability). These two
# constants are the direct replacement — order is load-bearing on each, independently,
# within its own H2's body. P09 rewrites every importer of the retired constant
# (validate_feature_spec.py, scaffold_spec.py, _audience_split_ccl_normalize_lib.py) —
# see plans/260818-1332-rebuild-spec-human-readable-sot/reports/p08-handoff-to-p09.md.
# ---------------------------------------------------------------------------

# RETIRED as a public name (rebuild-spec 27.7.0, phase 10). Was `REQUIRED_SYSDESIGN_H3`,
# imported by 4 modules; phase 04 repointed `scaffold_spec.py` to `REQUIRED_APPENDIX_H3`
# (§ 4 Shared Foundation's replacement subsections) and `validate_feature_spec.py` no
# longer needs it at all (its only consumer, `FeatureSpec.sysdesign_subsections`, is
# retired outright — no new-shape successor, see validate_feature_spec.py's own note).
# The remaining two importers (`_feature_sot_extract_lib.py`, `_feature_sot_structure_lib.py`)
# still need these exact 7 literal strings forever: they are the `feature-sot` migrate
# step's own § 3 System Design subsection headings — produced by
# `_feature_sot_structure_lib.build_system_design` and re-parsed by
# `_feature_sot_extract_lib.extract_v27_thread_pieces` as the `action-thread` step's own
# input. Renamed private or the same reason as `_LEGACY_TECH_H2_5BUCKET` above. Value is
# byte-identical to the pre-phase-10 `REQUIRED_SYSDESIGN_H3`.
_LEGACY_SYSDESIGN_H3 = [
    "### 3.1 Components",
    "### 3.2 Data Model",
    "### 3.3 State Management",
    "### 3.4 API & Endpoints",
    "### 3.5 Algorithms & Processing Logic",
    "### 3.6 Integrations",
    "### 3.7 Configuration",
]

REQUIRED_VERIF_H3 = [
    "### 5.1 Technical Verification",
    "### 5.2 Assumptions",
    "### 5.3 Unresolved Questions",
    "### 5.4 Source References",
    "### 5.5 Artifact References",
]

# ---------------------------------------------------------------------------
# A3/B4 (v26.0.0) — NEW REQUIRED sections gated by a DEDICATED validator
# (validate_reading_guide_db_impact.py), never added to REQUIRED_H2_TECH_THREAD above
# (Decision 2 — the exact-order check has no degradation window; see
# references/confidence-report-contract.md § A3 navigational-entries amendment
# and plans/260707-0803-acsim-learnings-rebuild-spec/phase-03-*.md).
# Single source of truth for the heading text: validate_reading_guide_db_impact.py,
# _a3_fill_guard_lib.py, _a3_citation_target_lib.py, and _a3_screens_step_lib.py all
# import these instead of re-declaring the literal strings. (`migrate-reading-guide-
# db-impact.py`, named here until phase-09, plans/260824-1846-rebuild-spec-action-
# self-sufficiency-v27-8, was deleted along with the `a3-b4` step it served.)
# ---------------------------------------------------------------------------

A3_HEADING = "## Source Walkthrough"
B4_HEADING = "## DB Impact per Event"

# ---------------------------------------------------------------------------
# v27.0.0: functional-spec.md § 8 Edge Cases skeleton — 3 placeholder rows so a
# fresh scaffold clears func.edge_cases_few_rows' UI-feature threshold (≥3) without
# a manual edit. Shape matches templates/functional-spec-template.md § 8
# (Scenario | What Happens | User-Facing Message).
# ---------------------------------------------------------------------------

FUNC_EDGE_CASES_SKELETON = """\
| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| {boundary condition / invalid input} | {specific system behavior} | "{plain-language message}" |
| {concurrent operation / race condition} | {specific system behavior} | "{plain-language message}" |
| {missing prerequisite / empty state} | {fallback behavior} | "{plain-language message}" |
"""

# ---------------------------------------------------------------------------
# P07 (human-readable SOT): functional-spec.md § 2/§ 11/§ 12 scaffolds.
# Header row only (content-preservation-map.md F-04/F-05/F-06) — deriving the actual
# capability/risk/dependency rows is a researcher judgment call ([L]), not something a
# deterministic scaffold should guess at. § 11/§ 12 additionally carry the literal
# "N/A — none found" fallback (matches the § 5 background / § 3 open-decisions
# precedent) so a fresh scaffold reads as "checked, nothing to report" rather than
# blank. This keeps func.capabilities_empty from firing on a fresh scaffold (0 rows
# in § 2 is only a warning when § 4 Requirements already declares >=1 real FR-###,
# which a fresh scaffold never does — see scaffold_spec.py::_render_functional_spec).
# ---------------------------------------------------------------------------

FUNC_CAPABILITIES_SKELETON = """\
| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
"""

FUNC_RISKS_SKELETON = """\
| ID | Type | Description | Impact | Status |
|----|------|--------------|--------|--------|

N/A — none found.
"""

FUNC_DEPS_SKELETON = """\
| Dependency | Type | Why this feature needs it | Evidence |
|------------|------|-----------------------------|----------|

N/A — none found.
"""

# ---------------------------------------------------------------------------
# rebuild-spec 27.7.0 (action-thread reshape) — technical-spec.md moves from a
# layer-first § 3 System Design spine to an action-first spine: § 2 Action Index is the
# action→rule binding v27 lacked (measured on a 43-feature/430-action corpus: `**Applies
# to:**` free text resolves to an action only 26% of the time), § 3 Actions is the new
# spine (per capability → per action, a uniform rung set), § 4 Shared Foundation is what
# used to be § 3's body, demoted to an appendix. See
# plans/260824-1128-rebuild-spec-action-thread-v27-7/plan.md (normative) and
# phase-01-shape-constants.md.
#
# This is now THE required shape (phase 10 repointed `validate_feature_spec.py`'s
# `required_sections` at it, and retired the old public name outright — see
# `_LEGACY_TECH_H2_5BUCKET` above). Kept its own name (not renamed back to a bare
# `REQUIRED_H2_TECH`) since the "_THREAD" suffix still documents which reshape produced
# it, and every existing importer (scaffold_spec.py, compose_action_thread) already
# uses this exact name.
# ---------------------------------------------------------------------------

REQUIRED_H2_TECH_THREAD = [
    "## 1. Technical Overview",
    "## 2. Action Index",
    "## 3. Actions",
    "## 4. Shared Foundation",
    "## 5. Verification & Technical Notes",
]

# Replaces the retired `_LEGACY_SYSDESIGN_H3` as § 4 Shared Foundation's H3 children
# (§ 4 is now an appendix, not the spine) — same "Shared Rules" bucket absorbs what used
# to be spread across the old § 4 Technical Behavior by Capability's per-capability
# BR/DEC blocks.
REQUIRED_APPENDIX_H3 = [
    "### 4.1 Components",
    "### 4.2 Data Model",
    "### 4.3 State Management",
    "### 4.4 Shared Rules",
    "### 4.5 Algorithms & Integrations",
    "### 4.6 Configuration",
]

# § 3 Actions' fixed rung set, in contract order. An absent rung (e.g. a backend-only
# action with no FE) is simply not rendered — no "N/A" placeholder, no "None." line — so
# ORDER is the contract a validator checks (rungs that ARE present must appear in this
# relative order); PRESENCE of every rung is explicitly not required. Tuple, not list:
# this is a fixed enum-like set, never appended to at runtime the way the H2/H3 heading
# lists occasionally grow a new entry.
# The first rung is "Who" (the actor), NOT "Ai". The B-v design sample was written in
# Vietnamese, where "Ai" IS the word for "who", and the label leaked verbatim into the
# plan's rung set. The authoring template is English (phase 09), where a rung labelled
# "Ai" reads as "AI" — a different concept entirely. Renamed before any consumer baked
# it in; these literals are what the validator matches, so a later rename would mean
# migrating every generated technical-spec.md.
# TWO-PLACE CONTRACT (phase 01, self-sufficiency v27.8): this tuple is NOT the only
# place the rung set is spelled out. `_action_thread_lib._RUNG_LINE_RE` deliberately
# repeats the labels literally rather than importing this tuple (a rung-line parsing
# regex is not a family-code regex — see that module's comment for why literal
# repetition is the safer choice there). Adding, removing, or renaming a rung HERE
# without also editing `_RUNG_LINE_RE` leaves the parser blind to it, which makes
# `FeatureSpec.rung_order`/`rung_empty_rendered` (both of which iterate this tuple
# generically) gates that CANNOT FAIL on the new label — this repo's #1 recurring
# defect class. Keep the two lists in lockstep by inspection.
# "State" sits before "Source" (added phase 01): the § 4.3 state-transition rung a
# state-machine-coded, writing action carries. `Source` remains the tuple's LAST
# entry — confidence-report-contract.md § "the rung set" depends on that positional
# fact for its own A1 citation-source description.
RUNG_LABELS = ("Who", "FE", "Request", "BE", "Rule", "Result", "State", "Source")

# § 3's H4 spine: `#### A12 · Approve Listing`. Group 1 captures the bare action ID
# (`A12`); the ` · ` separator is required so a plain `#### A12 Approve Listing` (missing
# the separator) does not silently parse as a valid action heading. Applied line-by-line
# by consumers (no re.MULTILINE needed), matching the existing convention for this file's
# other per-line heading patterns (e.g. `_CAP_BUCKET_H3_RE` in validate_feature_spec.py).
# Stored as a plain pattern string, not a compiled `re.Pattern` — this module stays
# declaration-only, zero imports (no `import re` here); consumers compile it themselves.
ACTION_HEADING_RE = r"^#### (A\d+) · "

# Bare action-ID token inside prose or a table cell (an Action Index cross-reference, or
# an anchor slug that carries the ID as its prefix, e.g. `A1_Slug`). Uses this repo's
# `(?!\d)` boundary convention — NEVER a trailing `\b`. The repo has hit this exact hazard
# 7 times across 3 variants: `_` is a word character, so `\bA\d+\b` silently fails to
# match inside `A1_Slug` (no boundary exists between the digit and the underscore), which
# would make a genuinely-referenced action ID invisible to anything scanning for it.
# `(?!\d)` sidesteps that: it only refuses to extend the match when the NEXT character is
# a digit (so `A10` is not misread as `A1` followed by a stray `0`), and is silent about
# what follows otherwise — a letter, an underscore, end of string all end the match
# cleanly. See test_spec_constants_sot.py::TestActionIdReBoundaryHazard for the
# fail-direction trace (a miss here silently under-counts binding coverage) and one test
# per variant (`A1`, `A10`, `A1_Slug`).
ACTION_ID_RE = r"\bA\d+(?!\d)"

# Degradation sentinel (D4), same design as `_TECH_PRE_SOT_SENTINEL` in
# validate_feature_spec.py — not a third pattern. The OLD (layer-first) shape's own
# distinguishing heading, never present in the new action-thread shape: the new § 3 is
# `## 3. Actions`, so a file that still carries a literal `## 3. System Design` H2 is
# unambiguously still old-shaped. While a file carries this sentinel, later phases'
# action-thread checks degrade to `warning` with a `_pre_thread` message suffix instead of
# `critical` — a 43-feature corpus must not go red all at once (mirrors `_FUNC_PRE_SOT_
# SENTINEL`'s and `_TECH_PRE_SOT_SENTINEL`'s WARN-first window exactly).
_TECH_PRE_THREAD_SENTINEL = "## 3. System Design"
