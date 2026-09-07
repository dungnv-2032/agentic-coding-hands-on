<!-- layout-exempt: rebuild-spec owns docs/features|screens|generated paths — all references here are output targets -->
# Pipeline: `--migrate` (version-upgrade backfill)
<!-- Updated: phase-09, plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8
     (a3-b4 retired; its LLM-fill mechanism re-homed under a3-screens, its only
     surviving application) -->

`--migrate` finishes what a rebuild-spec version upgrade leaves behind on an EXISTING
corpus — it never runs as part of a normal generation pass, and normal generation flags
(`--feature-specs`, `--flows`, etc.) are refused in combination with it (see
`run_doc_migrations.py::_validate_composition`). It is ONE ordered registry of steps
(plan.md Decision 1), not several flags:

```
run_doc_migrations.py --docs-root docs [--migrate] [--dry-run]
                       [--only STEP ...] [--features F001,F002] [--project-root PATH]
                       [--rollback STEP]
```

This document owns the `a3-screens` step's LLM half — the researcher fill fan-out, the
prompt contract, the wave gate, and the classification table. The step's deterministic
scaffold half (`_a3_screens_step_lib.py`) and the registry/driver mechanics (P01,
`_doc_migration_registry_lib.py`) are documented in their own modules; this file does
not repeat them. (The `a3-b4` step this section used to describe — the identical
mechanism applied to `features/*/technical-spec.md`'s A3/B4 pair — retired in phase 09,
`plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8`: A3/B4 left
technical-spec.md's target shape in phase 08, leaving `a3-b4` nothing left to
scaffold. `a3-screens` is this mechanism's one surviving application; the guard
modules it depends on were RESCOPED A3-only, never deleted, exactly because this
document still needed them — see `_a3_fill_guard_lib.py` / `_a3_citation_target_lib.py`
below.)

## SKILL.md summary details (relocated here, v27.9.0 line-budget trim)

The four blocks below are the original SKILL.md prose, kept here so the version-upgrade
narrative it carried (A3/B4 retirement rationale, step-order rollback/degradation notes,
the action-thread one-command UX summary, and the full `--migrate` flag reference) isn't
lost to the trim — SKILL.md now points here instead of repeating it in full.

### A3 Source Walkthrough — original shape and retirement (moved from SKILL.md)

**A3 Source Walkthrough (v26.0.0, BREAKING; B4 DB Impact per Event retired from
technical-spec.md in v27.8.0):** originally two NEW REQUIRED sections —
`## Source Walkthrough` (technical-spec.md AND screen-spec spec.md; ordered reading
list + call-hierarchy diagram + a pointer to the recast `## Source Code References` /
`## Source References` table, F15 DRY) and `## DB Impact per Event` (technical-spec.md
ONLY; top-level H2, one row per DB-writing event/endpoint). **B4, and A3 on the
technical-spec.md side, retired this release** (v27.8.0, self-sufficiency): the
action-thread reshape (`--only action-thread`) replaced both with the § 2 Action Index
+ per-action `Source` rung, and the `a3-b4` migrate step that used to scaffold+fill
them retired with nothing left to scaffold. **A3 stays fully live on the screen-spec
side** (`screens/*/spec.md`, via the `a3-screens` migrate step) — gated by the same
DEDICATED validator (`scripts/validate_reading_guide_db_impact.py`, wired at FS.2) with
its own WARN-first `*.pre_migration` degradation contract, never added to
`_spec_constants.REQUIRED_H2_TECH_THREAD` (that exact-order check has no degradation
window; Decision 2). Migration: `/tkm:rebuild-spec --migrate --only a3-screens`
scaffolds then hands off to a researcher fill. A3's list entries use `**File:**` so
they never inflate the A1 stat — see `references/confidence-report-contract.md`.

### Step-order table — rollback, degradation, and `_TECH_SPEC_STEPS` notes (moved from SKILL.md)

`cap-map` has a real `--rollback cap-map` (restores its own `.bak`, refusing — never
destroying — any feature whose §2 claim cells are already `filled`/`partial`). `action-thread`
is the second step after `cap-map` to have one (`--rollback action-thread`). No other step has
one yet. `action-thread`'s prerequisite is `cap-map`; `mirror-skew`'s prerequisite changes from
`cap-map` to `action-thread` (it now runs after both). `action-thread` writes
`technical-spec.md`, so it belongs in `run_doc_migrations.py`'s `_TECH_SPEC_STEPS` (the A1
confidence-report refresh set) alongside `audience-split`/`feature-sot` — `cap-map` is
deliberately NOT in that set, since it writes only `functional-spec.md` §2; keep that
distinction intact wherever this set is described. Degradation: WARN-first (D4) — while a file
still carries the old-shape sentinel (`## 3. System Design`), the new action-thread validator
checks report `warning`, not `critical`.

### `action-thread`'s one-command UX (moved from SKILL.md)

**`action-thread`'s one-command UX (v27.8.0):** run `--migrate --only action-thread` once — it
composes every pending feature AND, per this file's action-thread runbook, the orchestrator
fans out a bounded-wave researcher fill pass over whichever rule_id(s) a new
`pending-breakdown.json` sidecar names for each feature (never a grep-derived guess). Run the
IDENTICAL command again — it resumes, never re-fills an already-filled feature
(`_action_thread_fill_guard_lib.evaluate_fill`'s per-unit wave gate + the artifact-derived
`_is_pending` predicate), and reports done only once every feature's rule ownership is genuinely
resolved. Killing the command mid-run and re-running it never duplicates work.

### `--migrate` flag reference (full, moved from SKILL.md's flag-overrides table)

`--migrate [--dry-run] [--only STEP ...] [--features F001,F002] [--rollback STEP]` —
**[v27.2.0]** Version-upgrade backfill over an EXISTING corpus — NOT a normal generation
pass. Runs `scripts/run_doc_migrations.py`'s ordered 7-step registry (`audience-split` →
`a3-screens` → `screen-sot` → `feature-sot` → `cap-map` → `action-thread` → `mirror-skew`
— see the step table in SKILL.md; `--only` picks one, refusing it if its prerequisite
step still has pending units). (`a3-b4`, which used to sit between `audience-split` and
`a3-screens`, retired in v27.8.0 — A3/B4 left technical-spec.md's target shape, leaving
it nothing left to scaffold; `a3-screens`'s own prerequisite repointed straight to
`audience-split`.) Writes by default; `--dry-run` prints per-step pending counts and
writes nothing. Refused (exit 2) in combination with any generation flag or a secondary
`--lang`; `--full`/`--since` are accepted, warned about, and ignored. `--rollback STEP`
undoes a step's own write — only `cap-map`/`action-thread` have one implemented; any
other STEP name exits 2. **`--only action-thread` is ONE command that both composes and
fills (v27.8.0):** it reshapes every pending `technical-spec.md`, prints a `[HANDOFF]`
naming a structured pending breakdown (per rule_id), the orchestrator dispatches a
bounded-wave researcher fill pass per this file's action-thread runbook, then re-running
the IDENTICAL command confirms and resumes — killing it mid-run and re-running never
duplicates work (artifact-derived idempotency, never a marker file).

## Step order

`STEP_ORDER = (audience-split, a3-screens, screen-sot, feature-sot, cap-map,
action-thread, mirror-skew)` (`_doc_migration_registry_lib.py` — read the literal
tuple, this is prose, not the source of truth) — fixed, each step's prerequisite is
the one before it. `a3-screens`'s prerequisite is `audience-split` (phase 09 repointed
it here — it used to be `a3-b4`, until that step retired): `run_doc_migrations.py`
refuses to run `a3-screens` while any feature dir is still un-migrated (`[REFUSED]
step=a3-screens prerequisite=audience-split pending=N`). `screen-sot` and `feature-sot`
(phase-06/phase-10, `plans/260818-1332-rebuild-spec-human-readable-sot`) were
inserted between `a3-screens` and `mirror-skew`. `cap-map` (phase-07,
`plans/260819-1016-rebuild-spec-capability-map`) was inserted between `feature-sot`
and `mirror-skew`. `action-thread` (phase-06,
`plans/260824-1128-rebuild-spec-action-thread-v27-7`) was inserted between `cap-map`
and `mirror-skew` — `mirror-skew`'s prerequisite has moved four times across these
plans and now depends on `action-thread`, not `cap-map`, `feature-sot`, `a3-screens`,
or `screen-sot` directly. This is not incidental: `mirror-skew` must see the final
action-thread shape AND every rule bound to an action before pruning/translating a
mirror tree, or the translate handoff mirrors an incomplete bind that then re-skews
the moment a researcher resolves it (see "The `action-thread` step" below).


<!-- Step table moved from SKILL.md — meaning unchanged, only its home. -->
**`--migrate` step order (`STEP_ORDER`, `_doc_migration_registry_lib.py`) — each step's prerequisite is the one before it:**

<!-- layout-exempt: migrate step table — docs/ paths are rebuild-spec's own migration targets -->
| # | Step | Writes | A1 refresh on run? |
|---|------|--------|---------------------|
| 1 | `audience-split` | v26→v27 `features/*/{functional,technical}-spec.md` split | yes |
| 2 | `a3-screens` | `screens/*/spec.md` § A3 Source Walkthrough scaffold+fill (prerequisite `audience-split`, repointed v27.8.0 — see `references/pipeline-migrate.md` § Step order) | no (screen-spec-only) |
| 3 | `screen-sot` | `screens/*/spec.md` → 10-§ SOT + `## Technical Appendix` (`compose_screen_sot`) | no (screen-spec-only) |
| 4 | `feature-sot` | `functional-spec.md` (13 §) + `technical-spec.md` (5 buckets) SOT (`compose_functional_sot`/`compose_technical_sot`) | yes |
| 5 | `cap-map` | `functional-spec.md` §2 — widens the 5-column `Functional Capabilities` header to 7 (`User Stories` + `Business Rules`) on corpora migrated before that schema shipped; a table WIDENER only, never assigns codes to a row | no (functional-spec.md only) |
| 6 | `action-thread` | Reshapes `technical-spec.md` into the action-thread shape (§ 2 Action Index → § 3 Actions → § 4 Shared Foundation), then fills unresolved rule ownership via a bounded-wave researcher pass (v27.8.0). Pending predicate + detector list: `references/pipeline-migrate.md` § The `action-thread` step. | yes |
| 7 | `mirror-skew` | vi/jp mirror prune + translate handoff | n/a (writes no technical-spec.md) |

Step 1 `audience-split` **writes the v26→v27 split of `features/*/{functional,technical}-spec.md`** — the one cell of the table above that this file never stated literally before the move.

## The `a3-screens` step, in two halves

182 screens measured post-migration (phase-08). One substitution from the retired
`a3-b4` step's own shape: **A3 `## Source Walkthrough` alone — B4 never applies to a
screen spec.** `validate_reading_guide_db_impact.py`'s own module docstring is explicit
that B4 was `technical-spec.md` ONLY (and retired from there too, phase 08);
`check_db_impact` no longer exists at all, and `_a3_screens_step_lib.py` never
constructs or writes a B4 block for any file. If either changes, that is a defect in
this step or the validator, not an intentional widening — report it, do not paper over
it.

| Half | Owner | What it does | Can it fabricate? |
|------|-------|---------------|--------------------|
| Scaffold | `_a3_screens_step_lib.py` (deterministic) | Appends an honest `{...}` placeholder for A3 wherever it is missing. Never writes real content. | No — a script cannot invent a reading order it never observed. |
| Fill | This document (LLM researcher, per screen) | Reads the screen's actual source and replaces the placeholder with real, cited content. | Yes, in principle — which is exactly why the guard below exists. |

`_a3_screens_step_lib.run()` always returns `needs_llm_fill=True` on real progress,
which `_doc_migration_registry_lib._effective_category()` forces to `INERT` —
scaffolding alone can never read as a completed `--migrate` run. The fill half closes
that gap.

## Fill fan-out (mirrors FS.1 verbatim — no new env vars)

One researcher unit = ONE screen. Same bounded-wave shape as the feature-specs pass
(`pipeline-feature-specs.md` § Wave FS.1), reusing its env conventions exactly:

```js
const FS_BATCH_SIZE = Math.max(1, parseInt(process.env.REBUILD_FS_BATCH_SIZE ?? '5') || 5)
const MAX_PARALLEL  = Math.max(1, parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5)
const WAVE_WIDTH = Math.min(FS_BATCH_SIZE, MAX_PARALLEL)  // effective width, never > the global cap

// pendingScreens: the a3-screens step's still-scaffolded screen dirs (from
// count_pending's enumeration, i.e. screens/*/spec.md missing A3 real content).
let prevWaveIds = [], waveIds = []
for (const [idx, screen] of pendingScreens.entries()) {
  if (idx > 0 && idx % WAVE_WIDTH === 0) { prevWaveIds = waveIds; waveIds = [] }
  const taskId = TaskCreate({
    description: `a3-screens fill: ${screen}`,
    addBlockedBy: prevWaveIds,  // [] for the first wave
  })
  waveIds.push(taskId)
}
```

Every task of wave *i+1* is `addBlockedBy` ALL tasks of wave *i* — at most `WAVE_WIDTH`
researchers are ever runnable at once, and raising `REBUILD_FS_BATCH_SIZE` can never
widen a wave past `REBUILD_MAX_PARALLEL` (SKILL.md § GLOBAL PARALLEL CAP). 182 screens
at the default width of 5 is 37 waves.

## Prompt contract (the orchestrator MUST include this, verbatim, in every fill task)

Each researcher's prompt carries: the screen dir path, the project root, the A3
contract excerpt below, and this exact prohibition —

> Never invent a `file:line`. If you cannot locate the source, leave the `{…}`
> placeholder exactly as it is and say so in your report. An honest WARN is the correct
> outcome; a fabricated citation is not.

**A3 `## Source Walkthrough`** — an ordered reading list (data model → entry point →
view → business logic), one file per step, each cited `**File:** path:line-range` plus
a one-sentence "why start here"; a call-hierarchy diagram (ASCII or Mermaid); a pointer
to the screen's own `## Source References` table (the screen-side analogue of the
`## Source Code References` table a technical-spec.md carries). MANDATORY, no `N/A`
fallback — every screen has source to walk. A screen whose source cannot be located
keeps its `{...}` scaffold and stays WARN `reading_guide.unmapped` — that is the
correct terminal state, not a defeat to paper over.

### `**File:**`, never `**Source:**` — and why

A3 entries MUST cite with `**File:**`. `derive_confidence_report.py`'s `CITATION_RE`
matches only the literal `**Source:**` token, so using a different label deliberately
keeps this navigational reading list OUT of the A1 citation-coverage denominator
(`references/confidence-report-contract.md` § A3 navigational entries;
`references/feature-spec-researcher-contract.md` ~L389-391). Using `**Source:**` here
would silently inflate that statistic with entries that were never meant to be counted
as evidentiary citations. `_a3_fill_guard_lib.check_a3_citation_label` enforces this
mechanically — it fails on any `**Source:**` token inside the A3 body.

### Honest-degradation options (all acceptable, all reported)

| Outcome | Condition | Validator grade |
|---|---|---|
| `filled` | Real content, all citations resolvable | PASS |
| `unfilled` | `{...}` scaffold left intact (source genuinely unreachable) | WARN `*.unmapped` |
| `reverted` | Guard caught a scope breach or a fabricated citation | n/a — pre-wave content restored |

A run that fills nothing still exits honestly: `unfilled` maps to `INERT`, `reverted`
maps to `FAILED` (`_audience_split_tally_lib` categories, reused by import — see
`_doc_migration_registry_lib.StepResult`). Only `filled` is `PROGRESS`.

## The one authoring trap that reverts an honest fill (measured, wave 1, while this
mechanism was still the retired `a3-b4` step's)

**Never use curly braces inside the A3 body.** `_BRACE_RE` (`\{[^{}]*\}`, in
`validate_reading_guide_db_impact.py`) treats ANY braced span as an unmapped placeholder —
that convention predates this pipeline and grades `reading_guide.unmapped` for every spec in
the corpus, so it cannot be narrowed to the literal scaffold token without changing validator
semantics repo-wide. The practical effect: a legitimate enumeration like
`{facebook,google_oauth2,linkedin}` or a literal `{expires_at: 30.days}` reads as "still
scaffolded", and `_a3_fill_guard_lib` will refuse to classify the file `filled`.
Write sets in parentheses or prose instead: `(facebook, google_oauth2, linkedin)`.

Two brace shapes that bite in practice, both hit live by wave-1 units: a legitimate
enumeration (`(facebook, google_oauth2, linkedin)` written with braces), and — far more common
in a Rails or JS codebase — **string interpolation quoted from source**, e.g.
`render template: "email_design/#{params[:page]}"`. Quoting that verbatim into A3 fails the
check. Describe it instead: "splices `params[:page]` into the template path
`email_design/PAGE`". The cheap defence a screen-fill unit found for itself: grep your own
draft for `{` before writing it to disk, not after.

**Three further authoring traps retired along with `a3-b4` (phase 09).** They were all
`## DB Impact per Event` TABLE-shape faults (an unescaped `|` splitting a cell, a
cell-count drift against the 6-column header, a duplicated header row inserted by a
careless splice). B4 never existed on a screen spec, so none of the three ever applied
to this step — they retired along with the step whose table they described, not as a
loss of coverage here.

## The wave gate — `_a3_fill_guard_lib.py` / `_a3_citation_target_lib.py`

After each researcher unit completes, the orchestrator:

1. Has the PRE-fill snapshot of that screen's `spec.md` (taken before dispatching the
   unit).
2. Reads the POST-fill file.
3. Calls `evaluate_fill(pre, post, project_root) -> GuardResult`:
   - `scope` — `check_scope`: byte-for-byte equality of `pre` vs `post` OUTSIDE the A3
     section body (built on `strip_sections`, which reuses the validator's own
     fence-aware `_section_body` walk — one presence predicate across scaffold, fill,
     and validation, never a second hand-rolled one). `FILL_HEADINGS` is A3-only by
     construction (phase 09 dropped `B4_HEADING` from it along with the retired
     `a3-b4` step) — a screen spec never had a B4 heading to strip in the first place,
     so this is a name/scope correction, not a behavior change.
   - `citation_label` — `check_a3_citation_label`: no `**Source:**` inside A3.
   - `citation_target` — `check_citation_targets`
     (`_a3_citation_target_lib.py`): every `**File:**` citation in A3 must name a path
     that EXISTS under `project_root`, at a line (or range) inside that file's actual
     length. This is the one check nothing else in the pipeline performs — a citation
     that reads correctly but points nowhere real would otherwise pass silently.
     Whether a real citation SUPPORTS its claim is out of scope; that is
     `audit-doc-parity`'s job.
   - `placeholder` — `check_no_leftover_placeholder`: A3 may not still carry a
     `{...}` placeholder while being reported `filled`. An honest, untouched
     placeholder is fine (`unfilled`); this only catches a PARTIAL fill mis-reported
     as complete.
4. `result.must_revert` (true on any `scope`, `citation_label`, or `citation_target`
   violation) → restore the pre-wave snapshot verbatim and classify the unit
   `reverted`. A `placeholder` violation alone does NOT revert — it just blocks the
   `filled` classification (see the table above).
5. Otherwise run `validate_reading_guide_db_impact.py --docs-root … --summary-out …`
   and classify per the honest-degradation table.

## A1 confidence-report refresh (phase-04)

Every `technical-spec.md` a migration step rewrites owes a fresh
`confidence-report_technical-spec.md` beside it. This is the sidecar's own contract
word — **always-regenerate**, deterministic, LLM-free, sub-second per artifact — never
a staleness *detector*: `references/confidence-report-contract.md` already states A1
is not run on `functional-spec.md` at all (out of the citation-coverage denominator,
not a companion that happens to read `claims_total: 0`), so this loop's target set is
exactly one filename. Exactly the same shape `pipeline-feature-specs.md`'s FS.7
post-promotion loop uses, so one extractor parses both:

```js
// [v27.2.0] A1 confidence-report refresh -- best-effort, advisory, exit 0 always;
// NEVER gates. Fires once per feature immediately after a technical-spec-writing
// step's own work on that feature completes, regardless of outcome -- regeneration
// doesn't care about classification, it only reads whatever content is on disk right
// now. Mirrors .nav-metadata.json / A1's own precedent in pipeline-feature-specs.md;
// see references/confidence-report-contract.md.
for (const fcode of resolvedTargetFcodes) {
  bash: .claude/skills/.venv/bin/python3 \
    claude/skills/rebuild-spec/scripts/derive_confidence_report.py \
    --artifact ${docs_root}/features/${fcode}/technical-spec.md --project-root .
}
```

**Two firing points, by design, not by accident, for any step that both reshapes
`technical-spec.md` deterministically AND dispatches its own LLM fill pass over it**
(`action-thread` is the live example; the retired `a3-b4` step was the original one).
`run_doc_migrations.py` also calls this same regeneration in-process
(`_confidence_report_refresh_lib.py`, imported — never a subprocess) right after its
own technical-spec-writing steps return, before such a step's LLM fill wave has even
started. That in-process call cannot see the fill half's real content — the fill
happens across separate researcher dispatches that loop drives, outside the single
Python invocation entirely — so a "run once, in the right order" design is not
achievable here. The fix is not tighter ordering, it is what the contract already
prescribes: regeneration is idempotent and cheap enough to run **every time anything
touches `technical-spec.md`** — once after the deterministic half (Python-driven,
in-process), and again after the fill half (LLM-driven, per feature) — never gated,
never detected, never assumed stale or fresh. A companion regenerated twice in one
`--migrate` run simply reflects whichever content was on disk at each call; the
second call's output is authoritative because it runs after the fill, not because the
first call was wrong.

**`_TECH_SPEC_STEPS` names which steps qualify:** `{"audience-split", "feature-sot",
"action-thread"}` (`run_doc_migrations.py`) — every step that can write
`features/*/technical-spec.md`. `a3-screens` and `screen-sot` are BOTH
screen-spec-only and deliberately excluded (see the extended note under the
`a3-screens` wave gate above); `feature-sot` (phase-10) and `action-thread`
(phase-06, `plans/260824-1128-rebuild-spec-action-thread-v27-7`) DO write
`technical-spec.md`, so they belong in this set — getting either backwards is silent,
the companions just go stale. `cap-map` (phase-07) is deliberately excluded too — it
writes ONLY `functional-spec.md` §2, never `technical-spec.md`; adding it here would
trigger a pointless refresh of a companion file it never touches. (`a3-b4` carried
this same membership until it retired in phase 09,
`plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8` — A3/B4 left
technical-spec.md's target shape in phase 08, leaving nothing there for it to
refresh a companion over.)

**Gated on `ran`, never on merely `requested` (phase-06 ADDENDUM — the fix, not just
the intent).** `registry.execute()` accepts an optional `ran` set and adds a step's name
to it only when that step's `run()` actually executed — never when the step was
refused because its own prerequisite still had pending units. `run_doc_migrations.py`
computes `_TECH_SPEC_STEPS & ran_steps` (not `_TECH_SPEC_STEPS & set(step_names)`) to
decide whether to fire the in-process refresh after `registry.execute()` returns. Before
this fix a step named on the command line but refused at runtime still triggered a
companion rewrite over content that had NOT changed — a wasted, cosmetically-confusing
regeneration, not a correctness bug in the sidecar itself, but exactly the kind of "ran"
vs "requested" conflation this fix closes for good. (The dry-run preview path is
unaffected — it still checks `_TECH_SPEC_STEPS & set(step_names)`, i.e. "requested",
because a dry run never executes anything to gate on.)

**Never a `functional-spec.md` invocation, in either firing point.** The regression
guard (`scripts/tests/test_confidence_report_functional_spec_exclusion.py`) parses
every `references/*.md` file that invokes `derive_confidence_report.py` — including
this one — and asserts the union of every discovered call site's targets is exactly
`{technical-spec.md}`.

## Idempotency — "already filled" is decided by reading the file

`is_already_filled(text)` (`_a3_fill_guard_lib.py`) is the ONE predicate: A3 is
present AND does not still hold a `{...}` placeholder. It is read from the artifact
itself on every invocation — never from a marker file the driver writes — so a run
interrupted mid-wave, or re-run after completion, always sees the true state and
never re-fills, re-scaffolds, or downgrades an already-filled screen back to a
placeholder.

## Handoff / classification lines

- A wave that advances at least one screen to `filled`: `[HANDOFF]`-style summary line
  naming counts per outcome (`filled=N unfilled=N reverted=N`).
- Zero `filled` this run (everything already filled, or everything genuinely
  unfillable): step category `ALREADY` or `INERT` per
  `_doc_migration_registry_lib`'s `StepResult` contract — never a silent success.
- Any `reverted` unit: step category includes `FAILED`; `Tally.exit_code()` returns 1.

**No A1 confidence-report loop fires for this step — and the same holds for
`screen-sot` below.** Screen specs get no A1 companion change —
`confidence-report_spec.md` is already covered by the existing screen-spec pass, and
the A1 sweep's scope (§ above) is feature technical-specs only.
`run_doc_migrations.py`'s `_TECH_SPEC_STEPS` set already reflects this: it is
`{"audience-split", "feature-sot", "action-thread"}` — `a3-screens` and `screen-sot`
are BOTH screen-spec-only and never in that set, in-process or in this document's
runbook. Do not add either one.

## The `screen-sot` step (phase-06) — a reshape, not a scaffold+fill pair

`screen-sot`'s prerequisite is `a3-screens`. Unlike every step above, its deterministic
half does not append a placeholder next to unchanged content — it **reshapes the whole
document** via `compose_screen_sot` (`_screen_sot_compose_lib.py`), the sole authority
on the 10-numbered-§ + `## Technical Appendix` (6 H2-sibling) target order
(target-shape-spec.md § 1). Two generations reach the same composer: a v26 spec runs
through Mode C (the `audience-split` step, G1→G2) then `a3-screens` scaffolds A3 onto
that G2 text, then `screen-sot` composes G2→G3; a corpus already Mode-C-reordered
enters directly at `screen-sot` once `a3-screens` is satisfied. Both paths call the
SAME function, so they cannot drift.

**Pending predicate** — `"## 2. Screen Layout"` absent from `spec.md`. That literal
heading is the 2nd BA section `compose_screen_sot` writes; it is absent from BOTH a raw
G1 (v26, carries the unnumbered `## Screen Layout`) and a Mode-C G2 (no `## Screen
Layout` H2 at all — Layout Sketch/Regions live as bare H3s under `## Purpose`), so its
presence is a safe, universal, single predicate for both input shapes. Read from the
artifact, never a marker file.

**What it writes** — every pending `screens/*/spec.md`, atomically, reshaped in place.
A read/write failure on one screen is recorded and every other in-scope screen is still
composed (per-file isolation, matching the `a3-screens` precedent) — the step
reports FAILED overall only if at least one screen failed, naming every offending path.
Zero screens changed → `ALREADY`. Real progress → `PROGRESS` with `needs_llm_fill=True`.

**`needs_llm_fill` → INERT → exit 4, same fail-closed contract as every step above.**
The composer scaffolds its own honest placeholders for content it cannot derive
mechanically — e.g. `{plain role names...}` in `## 1. Overview`, `{TBD}` /
`{action name}` cells, and a `needs_llm_fill: do not invent a destination` sentinel in
`## 8. Navigation` — the same "do not complete by guessing" discipline the A3/B4
scaffold already established. `_effective_category()` forces any step reporting
`needs_llm_fill=True` to `INERT` regardless of its nominal category, so a `--migrate`
run that only reshapes structure, without a researcher pass over the scaffolded cells,
can never exit 0 as if the corpus were actually done — `Tally.exit_code()` returns 4
(nothing sealed), the same code the v27.1.0 sentinel-run precedent established.

**The researcher fill pass that follows** mirrors the `a3-screens` fan-out shape
verbatim (bounded waves, `REBUILD_FS_BATCH_SIZE` clamped by `REBUILD_MAX_PARALLEL`, one
unit = one screen): read the scaffolded cell/paragraph, read the actual source, replace
the placeholder with real, cited content — never invent a `file:line`, never "complete"
a scaffold by guessing (phase-05's Key Insight, restated here for the operators who
run this step). An unreachable screen keeps its scaffold and stays honestly incomplete,
not a defeat to paper over.

**No A1 confidence-report loop fires for this step** — `screen-sot` never touches
`features/*/technical-spec.md`; see the extended note under the `a3-screens` wave gate
above.

**Safety property worth knowing** (target-shape-spec.md § 1.3): Mode C's re-entry
predicate is `"## Screen Layout" not in old_text`. The new `## 2. Screen Layout` does
NOT contain the bare substring `## Screen Layout` (the `2. ` sits between `## ` and
`Screen`), so a SOT-shaped spec stays invisible to Mode C — the one thing preventing an
infinite re-migration loop between the two steps.

## The `feature-sot` step (phase-10) — the pair, composed and written together

`feature-sot`'s prerequisite is `screen-sot`. Like `screen-sot`, this is a reshape, not
a scaffold+fill pair: a thin driver over `_feature_sot_functional_lib.
compose_functional_sot` and `_feature_sot_technical_lib.compose_technical_sot` — the
sole authorities on the functional-spec (13 §) and technical-spec (5-bucket) target
orders (target-shape-spec.md §§ 2–3). It composes **functional FIRST, then technical**
— technical reads the freshly-composed functional text as its twin (the CAP-N list /
US### set technical-spec.md § 4 groups against comes from functional-spec.md § 2,
which only exists post-compose) — then writes BOTH files atomically, or neither.

**Pending predicate** — a feature dir is pending when its `functional-spec.md` lacks
`"## 2. Functional Capabilities"` OR its sibling `technical-spec.md` lacks
`"## 2. Functional → Technical Mapping"` — either composer's own idempotency sentinel.
Read from the artifacts, never a marker file.

**Write-both-or-neither** — both composed texts are staged to their own temp file in
the same directory FIRST; only after BOTH temp writes succeed are the two atomic
renames performed (`_atomic_write_pair`). A failure during either temp write (disk
full, permissions) leaves NEITHER real file touched — the Requirements language this
guards against is explicit: "a failure on technical-spec.md must not leave a
renumbered functional-spec.md behind."

**Per-feature-dir isolation** — a read/write failure, or a `functional-spec.md` with no
sibling `technical-spec.md` at all (the pairing invariant `audience-split` guarantees;
its absence is the anomaly this step reports FAILED for, not a shape it silently
skips), is recorded and every other in-scope feature dir is still composed before the
step reports FAILED overall.

**`needs_llm_fill` → INERT → exit 4** — identical contract to every step above: both
composers scaffold their own `[L]`-owed content (e.g. capability rows redistributed
across a real multi-capability twin, `## 3. System Design`'s cross-reference anchor,
CAP-completeness) that a researcher must still fill; real progress alone can never
exit 0.

**The researcher fill pass that follows** is the mirror of `screen-sot`'s: bounded
waves, one unit = one feature dir, read the scaffolded cell, read the actual source,
replace with real cited content — never invent a `file:line`.

**A1 confidence-report refresh DOES fire for this step** — the opposite of
`screen-sot`'s rule, because `feature-sot` writes `technical-spec.md`.
`_TECH_SPEC_STEPS = {"audience-split", "feature-sot", "action-thread"}`
already names it (see the A1 refresh section above); getting this backwards is
silent — the companions just go stale.

## The `cap-map` step (phase-07, plans/260819-1016-rebuild-spec-capability-map) — a table widener, not a fill pass

`cap-map`'s prerequisite is `feature-sot`; `mirror-skew`'s prerequisite is `cap-map`,
not `feature-sot` directly. It exists because real v27 corpora were fully migrated
under the OLDER, 5-column `## 2. Functional Capabilities` header (`| ID | Capability |
What the user can do | Requirements | Screens |`) before `feature-sot`'s skeleton was
widened to 7 columns (`User Stories` + `Business Rules` inserted). `cap-map` retrofits
those corpora: it widens the header + separator and appends empty cells to every
existing data row for the two new families. **It writes NO new rows and assigns NO
codes to a row** — partitioning US/BR codes across CAP rows is modelling judgment; a
heuristic would produce a partition that passes `cap.code_unclaimed` while being
semantically wrong. That assignment is phase-07b's job, with a human in the loop.

**What "done" honestly means here.** `cap-map` is a TABLE WIDENER. Its `run()` always
returns `needs_llm_fill=True` on real progress, which the registry's fail-closed
override forces to INERT — `--migrate` can never exit 0 on this step's work alone. Its
value is that it makes the pipeline REFUSE to move on until phase-07b's fill exists,
not that it delivers a finished §2 by itself.

**`count_pending` is `shape_pending + fill_pending`** — the fix for a skew the
placement fix alone does not stop. If `count_pending` reported 0 the moment both
column HEADERS exist, `mirror-skew` would proceed the moment `cap-map` widens a table,
translating every claim cell while it is still blank — then phase-07b's later fill
re-skews every mirror it just produced. So:
- `shape_pending` — the §2 header lacks either new column (what `run()` fixes).
- `fill_pending` — the header is already 7-column, but `_cap_table_lib.claim_state(...)
  != "filled"` (what phase-07b fixes) — imported, not re-derived, from the SAME
  predicate `cap.claims_unfilled` uses, so the validator and this migration step can
  never disagree about what "filled" means.
A feature dir with no `## 2. Functional Capabilities` heading at all contributes to
NEITHER count — that shape belongs to `feature-sot`, and double-counting it here would
make `mirror-skew`'s own prerequisite refusal message incoherent.

| state | `run()` writes | category | `needs_llm_fill` |
|---|---|---|---|
| any `shape_pending` | widens those files | PROGRESS | True |
| only `fill_pending` | nothing | ALREADY | True |
| neither | nothing | ALREADY | False |

Because `fill_pending` only clears once a human/LLM (phase-07b) actually populates
claim cells, a corpus can sit at `[HANDOFF] step=cap-map ... N still await the
phase-07b claim-cell fill` indefinitely, with `mirror-skew` REFUSED every run. This is
intended, not a regression: `--dry-run` always reports the exact outstanding count, and
the handoff line names the fix, so an operator sees "N pending, here's why" rather than
a false green.

**Idempotency is artifact-derived, same non-negotiable rule as every other step.**
`count_pending` reads the §2 header shape and claim state — never a marker file. The
`.bak` this step writes before its first per-feature write (see rollback below) is
ROLLBACK STATE ONLY; `count_pending` never reads it. Losing `docs/.migrate-v27/` once
caused a real re-run to RE-FOLD content (2368→2416 lines) while still reporting
success — a sentinel- or backup-based "already done?" check repeats that exact bug.

**`cap-map` is absent from `_TECH_SPEC_STEPS`** (see above) — it writes ONLY
`functional-spec.md` §2, never `technical-spec.md`.

## The `action-thread` step (phase-06, plans/260824-1128-rebuild-spec-action-thread-v27-7) — a reshape, not a scaffold+fill pair

`action-thread`'s prerequisite is `cap-map`; `mirror-skew`'s prerequisite is
`action-thread`, not `cap-map` directly. Like `screen-sot`/`feature-sot`, this is a
reshape: a thin driver over `_feature_sot_technical_lib.compose_action_thread` — the
sole authority on the v27 (5-bucket) → v27.7 (action-thread) technical-spec.md
reshape (wire-format-contract.md, normative). `compose_action_thread` is NET-NEW,
never a rename of the still-live `compose_technical_sot` the `feature-sot` step
depends on — they serve different input shapes (v26→v27 vs. v27→v27.7) and both stay
green.

**Pending predicate** — `"## 3. System Design"` present in `technical-spec.md` (the
old layer-first shape's own distinguishing H2, `_spec_constants._TECH_PRE_THREAD_
SENTINEL`) means the file has not been reshaped yet. A file already reshaped but
still carrying an `[UNVERIFIED]` marker (a rule the composer could not bind to an
action — wire-format-contract.md § 4.4) ALSO counts as pending, mirroring `cap-map`'s
own `shape_pending + fill_pending` split: `mirror-skew` must not proceed past a
corpus with unresolved rule ownership, or the vi/jp translate handoff mirrors an
incomplete bind and re-skews the moment a researcher resolves it by hand.

**What it writes** — every pending `features/*/technical-spec.md`, atomically,
reading the sibling `functional-spec.md` as the composer's twin input. A read/write
failure, or a `technical-spec.md` with no sibling `functional-spec.md` at all, is
recorded and every other in-scope feature dir is still composed before the step
reports FAILED overall (per-feature isolation, matching `cap-map`'s own precedent).
Zero features changed → `ALREADY`. Real progress → `PROGRESS` with
`needs_llm_fill=True` whenever any feature still carries an unresolved rule.

**`needs_llm_fill` → INERT → exit 4, same fail-closed contract as every step above.**
A rule the composer cannot bind to exactly one action by handler- or path-match is
marked `[UNVERIFIED]` and left in § 4.4 bin 3 — never guessed. `--migrate` cannot
exit 0 while any feature's rule ownership is unresolved, by design.

**A1 confidence-report refresh DOES fire for this step** — it writes
`technical-spec.md`. `_TECH_SPEC_STEPS` already names it (see the A1 refresh section
above); omitting it here is this step's own named top risk — silent, no error, no
warning, the companions just go stale.

**Rollback — the naive `cap-map`-style predicate is WRONG here.** Copying `cap-map`'s
own stance ("refuse if the target's claims are filled") would refuse EVERY successful
migration, because `compose_action_thread` itself is what fills those claims (or
marks them `[UNVERIFIED]`) — rollback could then never run at all. The correct
predicate instead compares an `[UNVERIFIED]`-marker COUNT across time: `run()`
records the count present in the text it just wrote to a JSON sidecar
(`<docs_root>/.migrate-v27/action-thread/<feature>/unverified-count.json`) next to
the `.bak`; `--rollback action-thread` refuses ONLY when the LIVE file's current
count is LOWER than the recorded one — that drop is the signature of a researcher
having resolved rules by hand since migrate ran, and restoring the `.bak` would throw
that work away. A count that stayed the same or rose is safe to restore.

### Fill fan-out (action-thread, mirrors a3-b4 verbatim — no new env vars)

One researcher unit = ONE feature dir — the same precedent this document fixes above
("Fill fan-out": *"One researcher unit = ONE feature"*), never one unit per action.
Same bounded-wave shape, same env conventions, reused, not re-derived:

```js
const FS_BATCH_SIZE = Math.max(1, parseInt(process.env.REBUILD_FS_BATCH_SIZE ?? '5') || 5)
const MAX_PARALLEL  = Math.max(1, parseInt(process.env.REBUILD_MAX_PARALLEL ?? '5') || 5)
const WAVE_WIDTH = Math.min(FS_BATCH_SIZE, MAX_PARALLEL)  // effective width, never > the global cap

// pendingFeatures: `_doc_migration_action_thread_step_lib.count_pending`'s own
// enumeration -- every feature dir `_is_pending` still flags, whatever the reason:
// an [UNVERIFIED] marker, a firing REOPEN_RULE_IDS detector (C1), or F2's regate
// check (a prior write never got its wave gate).
let prevWaveIds = [], waveIds = []
for (const [idx, feature] of pendingFeatures.entries()) {
  if (idx > 0 && idx % WAVE_WIDTH === 0) { prevWaveIds = waveIds; waveIds = [] }
  const taskId = TaskCreate({
    description: `action-thread fill: ${feature}`,
    addBlockedBy: prevWaveIds,  // [] for the first wave
  })
  waveIds.push(taskId)
}
```

**No new env vars (D13).** Raising `REBUILD_FS_BATCH_SIZE` can never widen a wave
past `REBUILD_MAX_PARALLEL`, identical to every fan-out in this document. **Named
risk, inherited, not introduced here:** no `scripts/*.py` in this tree reads either
variable (`decide_action_chunking.py:15-21`, checked 2026-08-24) — the wave-width
clamp above is orchestrator PROSE the orchestrator executes, with no code enforcing
it. The per-unit wave gate below is the safety net that DOES run in code regardless
of how wide a wave actually turns out to be.

### Prompt contract (the orchestrator MUST include this, verbatim, in every action-thread fill task)

Each researcher's prompt carries: the feature dir path, the project root, the § 2 /
§ 3 / § 4.4 excerpt of wire-format-contract.md (the Action Index binding + rung
structure + three-bin rule this fill pass completes), the rung set **including
`State`** —

```
Who → FE → Request → BE → Rule → Result → State → Source
```

— phase 06's self-sufficiency clause, quoted verbatim (never paraphrased --
`references/feature-spec-researcher-contract.md`, "Self-sufficiency of the H4
context line"):

> Every code in the H4 context line MUST be glossed — a plain-language clause, anywhere in the
> same action block — before the file is considered fill-complete. A code that appears ONLY in
> the context line, with no gloss anywhere else in the block, is the self-sufficiency defect this
> rule exists to prevent. The Bin-2/3 "short reference line" (`Used in:` / cross-cutting tag)
> does **not** satisfy it: that pointer points OUT of the block; the gloss stays IN it.
> Enforced by `FeatureSpec.action_ref_unglossed` (warning).

and BOTH prohibitions:

> Never invent a `file:line`. If you cannot locate the source, leave the rule's ownership at
> `[UNVERIFIED]` exactly as it is and say so in your report. An honest WARN is the correct
> outcome; a fabricated citation is not.

> Never guess a rule owner or a FROM state. An `**Applies to:**`/handler match that does not
> resolve, or a state transition whose prior state cannot be read from the source, resolves to
> `[UNVERIFIED]` — never a guessed action ID, never an invented FROM state (D3: never prose-sniff
> a transition from a method name or body text). Where a **State** rung cannot be resolved, emit
> NOTHING — never `N/A`, never `None.` (`FeatureSpec.rung_empty_rendered` is critical on exactly
> that stub shape).

The prompt also carries the feature's own pending breakdown — this step's
`pending-breakdown.json` sidecar (or the `[HANDOFF]` line's summary, same content):
which rule_id(s) fired (`state_rung_missing`, `action_ref_unglossed`,
`diagram_required_missing`, `rule_bin_misplaced`, `crosscutting_unlabelled`) and
which `#### A<n>` blocks (`dispatched_action_ids`) the unit may touch — see "The
wave gate" below. A sixth registered rule_id, `retired_section_present`, is
deliberately absent from this list — it needs NO researcher action (the composer
strips the retired section mechanically, see "The A3/B4 retirement strip" below),
so it is never dispatched into a fill prompt the way the five above are.

### The wave gate — `_action_thread_fill_guard_lib.py`

After each researcher unit completes, the orchestrator:

1. Has the PRE-fill snapshot of that feature's `technical-spec.md` (taken before
   dispatching the unit) AND the `allowed_actions` set for that SAME unit —
   `pending-breakdown.json`'s `dispatched_action_ids` field, read at the SAME
   pre-dispatch moment, never recomputed after the fill (a post-fill recompute
   would shrink to whatever the fill already resolved and disarm the very bound
   it exists to enforce).
2. Reads the POST-fill file.
3. Calls `evaluate_fill(pre, post, project_root, allowed_actions) -> GuardResult`
   — **passing `allowed_actions` is MANDATORY, not optional (D13).** `None` (the
   default) disarms the "did not touch an action nobody asked about" protection
   entirely — a declared-but-never-armed guard is this repo's own dead-gate
   family, and phase 04 built this exact bound to catch it:
   - `scope` — `check_scope`: byte-for-byte equality outside every rung
     occurrence, every mermaid fence inside § 3, and every § 4.4 paragraph (the
     declared editable surface), PLUS every `#### A<n>` block whose rung content
     changed must be a member of `allowed_actions` — a block changing outside
     the dispatched set reverts, including a one-for-one swap (dispatched to A2,
     quietly edits only A1) that a bare count bound would have let through.
   - `owner_plausibility` — `check_owner_plausibility`: every action ID a fill
     unit writes into a `Used in:` list must name a row that exists in this
     feature's own § 2 Action Index.
4. `result.must_revert` (true on either violation) → restore the pre-wave
   snapshot verbatim and classify the unit `reverted`.
5. Otherwise run `validate_feature_spec.py --docs-root … --project-root … --summary-out …`
   and classify the unit `filled` / `unfilled` per the Handoff section below.

**Adding an absent rung is ALLOWED inside a dispatched block — and that was a
real defect, found and FIXED before release.** As first built, `check_scope`'s
`_skeleton` folded each rung occurrence to one sentinel **per label**, which put
the SET of a block's rung labels into the immutable skeleton. A fill unit adding
a **State** rung genuinely absent from `pre` — the entire point of resolving
`state_rung_missing`, this release's headline work — therefore made
`skeleton(pre) != skeleton(post)` on that ground ALONE, and `check_scope`
reverted the unit **regardless of `allowed_actions`**, even with the block
correctly dispatched. The workflow could never have passed its own gate.

`_skeleton` now **drops** the rung region instead of sentinelling it, because
rungs are the declared editable surface. **No protection was lost:** rung-level
change is the other arm's job — `_changed_action_blocks` diffs
`{block: {label: body}}` and `allowed_actions` reverts any block outside the
dispatched set, so a State rung added to a block nobody dispatched is still
reverted. Both directions are pinned by live tests (no longer `xfail`):
`test_action_thread_pending_breakdown.py::
TestDispatchedActionIdsInteropWithTheWaveGate::
test_a_dispatched_action_may_have_its_rungs_changed` (allowed) and
`::test_an_undispatched_action_may_not_have_its_rungs_changed` (reverted).
Keep both green — if the first ever reverts again, resolving `state_rung_missing`
becomes impossible at this step and the capability dies silently.

**F2 — the fill-wave crash window (disclosed; closed in its stronger form where
cheap — see Idempotency).** The gate above runs strictly AFTER the fill unit's
write has already landed on disk — the write and its gate are NOT atomic. Killing
the orchestrator in that gap leaves an ungated write on disk that content alone
cannot tell apart from a genuinely gated one.

### Idempotency

`_is_pending` (`_doc_migration_action_thread_step_lib.py`) is read from the
artifact, never a marker file: the `[UNVERIFIED]` tag, any `REOPEN_RULE_IDS`
detector firing (C1), OR — F2's addition — a feature whose `.migrate-v27` staging
dir exists (`run()` wrote to it at least once) while its `pending-breakdown.json`
sidecar's `gated` field is not yet `true`.

`gated` is written EXCLUSIVELY by the orchestrator, immediately after step 5 of
the wave gate above passes for that feature (any outcome — `filled` / `unfilled` /
`reverted` — sets it `true`; the field records "a gate ran", not "a gate
approved"). `run()` never sets it `true` itself: a fresh compose/reopen write
resets it `false` (new content needs a fresh gate cycle); a call that writes
nothing this invocation preserves whatever value is already there, so a routine
"already surfaced this finding" re-run can never clobber a `gated: true` the
orchestrator already recorded. A feature `run()` has never touched (no staging
dir at all) is exempt — nothing was ever dispatched for a gate to have missed.

This does NOT retroactively re-verify a crashed write's content — no artifact
preserves the transient pre-fill snapshot the scope check would need for that, and
inventing a new marker file to persist it was explicitly rejected (the idempotency
rule stays artifact-derived, never a marker file of its own). It converts the
crash window from a SILENT gap into a PERSISTENTLY SURFACED one: the feature stays
in the next fan-out until an orchestrator run actually gates it, rather than
vanishing into "already done" with nobody having checked it.

### The A3/B4 retirement strip (phase 08, self-sufficiency v27.8) — deletion, not a fill

`## Source Walkthrough` (A3) and `## DB Impact per Event` (B4) retired from
`technical-spec.md` this release; `FeatureSpec.retired_section_present` (warning)
fires on either heading's presence and is registered into `REOPEN_RULE_IDS` — the
deletion-direction twin of the five fill-pass detectors above, going through the
exact same `needs_reopen` mechanism (C1/D7), never a second one. Its remediation
is NOT a researcher fill pass: `compose_action_thread` itself strips both
sections on the next `--migrate --only action-thread` run, whether the file is
still pre-thread-shaped (the sections are simply never re-emitted) or already
action-thread-shaped (the reopen path recomposes it in place, through the SAME
write-before-destroy `.bak`/sidecar sequence every other reopen uses — no second
backup path). One-shot: a file already stripped carries neither heading, so
`retired_section_present` stops firing and the file reports `ALREADY` on the very
next run, byte-identical to the stripped output. `screens/*/spec.md` is untouched
— A3 stays fully live there via `check_source_walkthrough`; only the
technical-spec.md side retires.

### Handoff

- A run with real progress or unresolved rule ownership remaining prints, folded
  into the same `[HANDOFF]` line every step above uses (the exit-4 contract is
  unchanged — this only extends the text riding along with it):
  `[HANDOFF] step=action-thread needs_llm_fill=true -- composed N feature dir(s)
  … -- pending breakdown totals: unverified=N state_rung_missing=N
  action_ref_unglossed=N diagram_required_missing=N rule_bin_misplaced=N
  crosscutting_unlabelled=N retired_section_present=N -- feature=<name> …;
  feature=<name> …` (`_action_thread_pending_breakdown_lib.summarize_breakdowns`;
  a zero-valued rule_id is omitted from the real line, per that function's own
  `if v` filter — every key shown here as `=N` may simply be absent when it is 0).
- Per-unit classification vocabulary, reused verbatim from `a3-b4`:
  `filled` / `unfilled` / `reverted`.
- Zero `filled` this run (everything already filled, or genuinely unfillable this
  pass): step category `ALREADY` or `INERT` — never a silent success.
- Any `reverted` unit: step category includes `FAILED`; `Tally.exit_code()`
  returns 1.

## `--rollback STEP` (phase-07, joined by `action-thread` in phase-06) — undo, not crash-safety

`run_doc_migrations.py --rollback STEP` is a separate mode from `--migrate`, dispatched
before any `--dry-run`/`--only` composition is even read. **`cap-map` and
`action-thread` are the two steps with a rollback implemented** — any other `STEP`
name exits 2, naming both supported values (YAGNI: no generic rollback registry
beyond steps that actually ship one).

**Atomic write is crash-safety, not undo — two different guarantees.** Both steps'
staged-temp-then-`os.replace` writes guarantee a concurrent reader never observes a
half-rewritten file; they guarantee nothing about recovering the pre-migration
content afterward. Recovery is what the `.bak` is for: before its first write to a
feature, `cap-map` copies the original `functional-spec.md` to
`<docs_root>/.migrate-v27/cap-map/<feature>/functional-spec.md.bak`, and
`action-thread` copies the original `technical-spec.md` to
`<docs_root>/.migrate-v27/action-thread/<feature>/technical-spec.md.bak`
(write-before-destroy, both cases). `--rollback cap-map` / `--rollback action-thread`
restores each backup and removes it.

**Refusal — two different predicates for two different reasons.** `cap-map`
refuses a feature whose live `claim_state` is `"filled"` or `"partial"` — a human has
done modelling work in those §2 claim cells, and restoring the narrow table would
destroy it. `action-thread` refuses a feature whose live `[UNVERIFIED]`-marker count
has dropped below its sidecar's recorded value — see "The `action-thread` step"
above for why the `cap-map`-style predicate does not transfer here. In both cases the
refusal is printed, the loop continues past it, and the overall exit code is
non-zero whenever anything was refused. Reversing a *finished* migration is the
customer's own VCS's job, not this tool's.

Exit codes: 0 on a clean restore (or "nothing to roll back"); non-zero whenever
anything was refused or a real I/O error occurred; 2 for an unsupported `STEP` name.
