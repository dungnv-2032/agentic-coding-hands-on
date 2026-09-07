# Migration: v26 -> v27 audience split

Reference for `claude/skills/rebuild-spec/scripts/migrate_feature_audience_split.py` --
the one-time upgrade path for an existing rebuild-spec repo from the v26 layout (4-file
feature dirs, `business-rules.md`, old-order screen-spec) to v27 (2-file feature dirs,
`business-rules.md` folded into `behavior-logic.md`, BA-first screen-spec order). See
`plans/260814-1106-rebuild-spec-audience-split/phase-06-migration-scripts.md` for the
full design record; this file is the operational reference for running it and for the
LLM compaction pass specifically.

## The three modes

| Mode | Unit | Source(s) | Target | LLM pass? |
|------|------|-----------|--------|-----------|
| A | one `docs/features/{F###}/` dir | `business-context.md` + `screens.md` + `edge-cases.md` + `technical-spec.md` | `functional-spec.md` + reshaped `technical-spec.md` | yes (optional) |
| B | once, project-level | `docs/system/business-rules.md` | `docs/generated/behavior-logic.md` (folded in) | yes (optional) |
| C | one `docs/screens/{SCR###}/spec.md` | itself (in place) | itself, reordered | **no** -- pure reordering |

Mode A composition (`_audience_split_compose_a_lib.py` + `_audience_split_parse_v26_lib.py`
+ `_audience_split_parse_old_blocks_lib.py` + `_audience_split_render_func_sections_lib.py`)
is a DETERMINISTIC content move, not an LLM rewrite: text is parsed out of the 4 v26
files and reassembled into the 10 fixed functional-spec.md sections + a reshaped
technical-spec.md (old block heading `### BR-001_Slug` -> `### {sentence} (BR-001)`;
BR's `**Rule:**` and DEC's `**user_visible_outcome:**` fields move to functional-spec.md
§4, everything else in a block passes through byte-for-byte). The BR/DEC/SM one-liner in
functional-spec.md §4 and the new technical-spec.md heading for that code are the SAME
derived sentence (`sentence_for_block`) -- one derivation, two call sites, so the two
files can never say something different about the same code.

**The byte-for-byte guarantee has three disclosed exceptions, not one.** An undocumented
exception to a stated byte-for-byte pass-through is how the next maintainer gets misled, so
all three are named here:

1. **The `**Rule:**` / `**user_visible_outcome:**` strip** (above) -- these two fields move to
   functional-spec.md §4 and do not remain in the technical-spec.md block.
2. **The CCL `None.` backfill.** A v26 `technical-spec.md` with an empty required CCL H3
   (`### Business Rules`, `### State Machines`, `### Algorithms`, `### External Integrations`)
   gets that section body filled with a literal `None.` rather than left blank -- measured on
   the real corpus: all four H3s are present at H3 level in 66/66 technical-specs, but bodies
   were empty in 36 (`Business Rules`), 22 (`State Machines`), 22 (`Algorithms`), and 28
   (`External Integrations`) files, tripping `FeatureSpec.ccl_blank`. This is a backfill of
   absent content, never a rewrite of present content -- a section with any existing body passes
   through untouched.
3. **The `authored_by: rebuild-spec` frontmatter stamp.** Composition prepends a 3-line
   frontmatter block (`---\nauthored_by: rebuild-spec\n---`) at byte 0 of both output files. This
   is new content the v26 originals never had (see § Provenance and the legacy-marker path,
   below, for why it matters going forward).

Mode B (`_audience_split_mode_b_lib.py`) parses `business-rules.md`'s `### {Rule Name}`
blocks (`**Applies when:**` / `**Says:**` / `**Source artifact:**`) and inserts them as
a new `## Business Rules (folded from business-rules.md)` H2 immediately before
`## Dev Appendix` (or the first `## BL###` fragment if there's no Dev Appendix wrapper
yet) -- ahead of the existing BL### fragments either way, never inside one. Every
pre-fold `BL###` fragment is untouched.

**Mode B's re-entry guard is the ARTIFACT, not the sentinel.** Before folding,
`migrate_business_rules` reads `behavior-logic.md` and looks for the `FOLD_H2_HEADING`
it would emit; if that heading is already present the fold is a `no-op` (ALREADY) and the
per-feature sentinel is simply re-written. That check runs BEFORE the sentinel check, so
correctness never depends on `docs/.migrate-v27/` surviving.

This ordering exists because the sentinel-only version was a silent data-corruption bug.
`business-rules.md` is never deleted (the source always remains), so a run that could not
see its own prior sentinel re-folded and APPENDED a second copy: measured on a real
66-feature corpus, run 1 produced one folded section (2368 lines) and run 2 with
`docs/.migrate-v27/` removed produced two (2416 lines) -- while reporting `migrated`,
`failed=0`, `run sentinel: WRITTEN` and exit 0. It was cumulative: a third run appended a
third copy. Nothing failed, nothing warned, and the operator saw a clean success.

That is the same "state inferred from a sentinel rather than from the artifact" mistake as
the run-sentinel-over-zero-migrations blocker this migration was written to fix, and the
same one `SHAPE_V27_HYBRID` addresses for Mode A (see below). The general rule for any
future write path here: **derive already-done from the output you would have written, and
treat a sentinel purely as a skip-optimization.** Verified after the fix by running three
successive migrations, deleting `docs/.migrate-v27/` before each: the folded-section count
stays at 1 and `behavior-logic.md` stays byte-identical.

Mode C needs no equivalent guard, and this was checked rather than assumed: its reorder
structurally REMOVES the `## Screen Layout` wrapper, and `migrate_screen` keys off that
heading's absence, so an already-reordered `spec.md` takes the confirm branch on a re-run
regardless of sentinel state. Byte-identity across sentinel-loss re-runs was verified on
the real corpus.

Mode C (`_audience_split_mode_c_lib.py`) reorders an existing screen-spec.md into the
Phase 02 order. `## Screen Layout` is unwrapped (C-AD3): `### Layout Sketch` absorbs the
wrapper's intro prose and moves into the BA body (right after `## Purpose`);
`### Layout Regions` moves into the dev appendix. Both keep their heading TEXT verbatim.
`## Data Inventory`'s `Field` column is dropped; `Display Label` becomes the sole
identity column, with the old Field value surviving as a `(binding: ...)` annotation on
Cross-ref rather than being discarded. No LLM pass touches Mode C's output.

## Screen-name resolution: the L0-L3 ladder (Mode A)

`validate_feature_spec.py`'s `func.screens_scr_unresolved` check itself has a regex fix
folded in: the old anchor `\bSCR\d{3}\b` never matched `SCR001_Login` because `_` is a
word character with no boundary after the digits (the same shape recurs elsewhere in this
repo, e.g. `screen.layout_sketch_missing`'s sibling note in the Phase 02 checklist) --
fixed to a negative lookahead so a bare or slug-suffixed code both resolve. That fix alone
does not bind a screen NAME to a code, though: a v26 feature's `screens.md` § Screen List
names a screen in prose (`Screen Name | What User Sees | What User Can Do`), and the code
that name maps to lives only in `docs/generated/screen-list.md` § Screen Index
(`Code | Name | Auth | Controller#Action | Route`) -- a separate file, joined only by
matching the name text. Getting that join right, and being honest about the rows it can't
join, is the harder problem this ladder solves.

Measured over the real 195 feature-side screen rows against the 182-row Screen Index:

| Level | What it resolves | Count | How |
|-------|-------------------|-------|-----|
| **L0** | code already inline in the `screens.md` name | **44** | the name itself carries `(SCR062)` or `(SCR062/REG002)` -- extract directly, no lookup needed |
| **L1** | exact name match | **92** | `norm_name()` (strip / collapse whitespace / casefold) matches a Screen Index `Name` byte-for-byte after normalization |
| **L2** | unicode / parenthetical fold | **34** | folds `’` (U+2019) / `—` (U+2014) variants and strips a trailing parenthetical or region suffix before re-matching |
| **L3** | unresolved | **25** | no code inline, no name match at any fold level -- an honest gap, not a guess |

**There is no L4 -- no fuzzy or edit-distance matching, by deliberate non-goal.** A wrong
SCR binding silently mis-links a feature to the wrong screen and is worse than an honest
gap that a human can close in minutes; L0-L2 exhaust every match the source data actually
supports, and L3 says so plainly instead of guessing.

**Screen Index name duplication.** 6 distinct names are shared across more than one
Screen Index row (176 distinct names over 182 rows) -- when a matched name is one of
these, the binding is flagged ambiguous rather than silently taking the first hit. 7
row-level bindings were flagged this way on the real corpus.

### The `### Unbound Screens` degradation contract

The 25 L3 rows are not dropped. They span **12 features** (a feature can have more than
one unbound row), and every one of the 12 is recorded in the composed
`functional-spec.md` in two places, both required:

1. A `### Unbound Screens` sub-block under `## 5 Screens`, listing the unresolved name(s)
   verbatim as they appeared in the v26 `screens.md`.
2. One row per unresolved screen under `## 2 Open Decisions`, continuing the SAME `D###`
   numbering series the feature's other open decisions already use -- not a separate
   counter, so a reader scanning § 2 sees every open item in one list regardless of
   source.

A feature with zero L3 rows has no `### Unbound Screens` sub-block at all; the contract
only fires where the source data actually left a gap.

## Gate 8 -- the SHAPE_V27 branch does not skip an LLM-compaction opportunity

A feature dir already in 2-file (v27) shape is confirmed via the validator and sealed
with its sentinel WITHOUT ever calling `compose_fn` or running the LLM pass, regardless
of how it reached that shape. This is deliberate, not a gap:

- Requirement 1 scopes Mode A's composition to content DRAWN FROM the 4 v26 files
  (business-context/screens/edge-cases -> functional-spec.md §1/2/5/8). A dir with no
  v26 satellites has nothing left for Mode A to compose FROM.
- Requirement 5 scopes the LLM pass to staging Mode A/B just produced, re-validated
  under I4/I5. There is no such staging for an already-v27 dir -- inventing one to run
  compaction against arbitrary pre-existing content would be a DIFFERENT, unscoped
  feature (general-purpose doc-shrinking), not this migration's job.

Confirm-and-seal is the correct, complete behavior for that branch. A genuinely
over-long already-v27 file is the reviewer's / Wave 6.5's concern, not this migration's.

## SHAPE_V27_HYBRID -- the resumable common case (adversarial-review HIGH fix)

**The default run's own documented output (§ "What a reader should expect from the
default run", below) is a shape `detect_shape()` originally could not recognize.** A
feature dir left with `functional-spec.md` + `technical-spec.md` + all three retained
v26 satellites (`business-context.md`, `screens.md`, `edge-cases.md`) -- five files --
used to classify as `SHAPE_UNKNOWN` and REFUSE on any re-run that could not consult the
per-feature sentinel under `docs/.migrate-v27/`. Sentinel survival was therefore
load-bearing for the common case, not just an optimization -- and `docs/.migrate-v27/`
is a dot-directory sitting directly under `docs/`, exactly where a consumer team is
likely to gitignore it or clear it as scratch. Measured on the real 66-feature corpus
with `docs/.migrate-v27/` deleted: `progress=0 already=7 inert=0 failed=59` -- the 59
hybrid dirs refused, safely (exit 1, no data loss, no false seal) but with no automatic
recovery route short of hand-restructuring back to pure v26 and discarding the already-
composed `functional-spec.md` content.

**The fix:** `_audience_split_shape_lib.detect_shape()` recognizes this exact
combination -- `functional-spec.md` AND `technical-spec.md` AND ALL THREE v26
satellites present together -- as `SHAPE_V27_HYBRID`, a shape distinct from both
`SHAPE_V27` (zero satellites) and `SHAPE_V26` (no functional-spec.md). It is
deliberately narrower than "at least one satellite present": a dir with only ONE or TWO
satellites left over matches neither the documented hybrid state nor any other
recognized shape and stays `SHAPE_UNKNOWN` -- widening the hybrid predicate to swallow
that case would blur the line between "the documented common case" and "a genuinely
corrupted or hand-restructured tree", which is exactly the REFUSE path's job to catch.

`migrate_feature`'s `SHAPE_V27_HYBRID` branch (Gate 8b) is handled the same way as the
existing `SHAPE_V27` branch (Gate 8): it validates the LIVE `functional-spec.md` +
`technical-spec.md` pair and, if validation passes, (re-)writes the per-feature sentinel
and reports the ALREADY-category `confirmed-v27` action -- **it never calls `compose_fn`
again.** Re-composing a hybrid dir would re-derive `functional-spec.md` content from the
satellites sitting next to it and could silently overwrite reviewed edits made to the
composed output since the original run; validate-and-seal is the only safe move, mirroring
the same reasoning as Gate 8. If validation fails, the branch refuses with
`refused-invalid-v27` (FAILED) rather than guessing. The one way this branch differs from
`SHAPE_V27`: a hybrid dir DOES have satellites on disk, so it still honors `--reviewed`
for cleanup -- a reviewed slug reaching this branch gets its satellites deleted (action
`migrated`, PROGRESS) exactly as a fresh Mode A run would.

**Practical effect:** the per-feature sentinel is now a skip-optimization (skip the
validate-and-seal work when it is known to have already run), not a correctness
dependency (recognizing and safely resuming the hybrid state no longer requires it). Re-
running the migration after `docs/.migrate-v27/` is lost now resolves every hybrid unit
to `already` with zero `failed`, and the `functional-spec.md`/`technical-spec.md` content
is provably untouched (byte-identical before/after) because composition never runs again.
**That said, `docs/.migrate-v27/` is still best preserved** -- losing it forces every
hybrid unit to re-run its validator pass on the next invocation (cheap, but not free), and
a PARTIAL (sentinel-absent, pre-swap-backup-present) Mode A run still depends on the
staging dir for `--rollback` to have anything to restore from.

## Provenance and the legacy-marker path

The hand-edit probe (`_audience_split_probe_lib.probe_file` / `probe_feature`, all three
modes) must decide whether a v26 directory is safe to migrate automatically or whether a
human hand-edited it and should be left alone. Its ORIGINAL signal, `authored_by:`
frontmatter, is written only by takumi's promote path -- rebuild-spec's own generator
never emitted it, in any version before this one. On a corpus rebuild-spec generated
itself (zero frontmatter anywhere, by construction) that made every unit `HAND_EDITED`
by construction -- see ADR-0004's amendment for the full incident. The fix splits
provenance into two signals at different granularity:

- **Origin, per UNIT.** At least one file in the unit carries a recognized signal --
  `authored_by:` frontmatter (unchanged), OR a generator marker: `<!-- Contract: … -->`
  at line 1, or a `**Generated**: DATE` line. Measured coverage on the real corpus (66
  feature dirs / 264 files): `**Generated**: DATE` in `technical-spec.md` 66/66 (full
  coverage -- load-bearing); `<!-- Contract: … -->` in `technical-spec.md` 41/66;
  neither marker appears in `business-context.md`, `screens.md`, or `edge-cases.md` on
  any file, ever. No file in the unit carries any of the three signals -> `HAND_EDITED`.
- **Integrity, per FILE, unchanged.** `doc_lock: user`, a foreign `authored_by:`, a
  missing git trail, or a working-tree diff against HEAD still resolves that file --
  and therefore the whole unit -- to `HAND_EDITED`. Origin says "a generator wrote this
  directory"; the git trail says "no byte has moved since". Both are required; a
  marker-backed origin never substitutes for a clean git trail.
- **`CLEAN_LEGACY` verdict.** A unit that resolves clean via a generator marker (rather
  than via `authored_by:`) gets its own verdict, `CLEAN_LEGACY`, so the run tally can
  report marker-backed vs. `authored_by:`-backed counts separately. `CLEAN_LEGACY` does
  **not** restrict deletion by itself -- `--reviewed` remains the single human gate
  before any v26 original is deleted, exactly as it is for an `authored_by:`-backed
  unit. Do not read `CLEAN_LEGACY` as a weaker guarantee; it is the same guarantee,
  reached by a different accepted signal.
- **Going forward.** Every template and researcher contract this skill ships now emits
  `authored_by: rebuild-spec` at generation time (the same signal takumi's promote path
  already writes), so a corpus generated under v27.1.0+ carries `authored_by:` from the
  start and the legacy-marker path exists purely as a bridge for corpora generated
  before this fix -- it is not a permanent second path to maintain.

## Exit codes and the run sentinel

| Exit | Meaning |
|------|---------|
| `0` | Success, or a genuine no-op (every unit already `ALREADY` / clean) |
| `1` | At least one unit `FAILED` |
| `2` | Argument or I/O error, an `assert_under` path-containment violation, or a mirror-tree refusal (see below) |
| `3` | The run lock is held by another invocation |
| `4` | **New.** `FAILED == 0` but `INERT > 0` -- nothing was sealed, the sentinel is NOT written, and the corpus remains migratable on the next run |

Every migrated unit resolves to exactly one outcome category, via `categorize()`:

| Category | Meaning | Example actions |
|----------|---------|------------------|
| `PROGRESS` | this run moved the unit forward | `migrated`, `migrated-originals-retained` |
| `ALREADY` | already in target shape, nothing to do | `confirmed-v27`, `no-op` |
| `INERT` | blocked -- not an error, but not progress either | `skipped-hand-edited`, `rejected-bad-slug`, `skipped-no-target` |
| `FAILED` | validation or composition failed | `failed-validation`, `refused-invalid-v27` |

The run prints one `[SUMMARY]` line and, on success, writes a JSON sentinel:

```
[SUMMARY] units=249 progress=249 already=0 inert=0 failed=0 | provenance: authored_by=0 marker=66 | run sentinel: WRITTEN
```

```json
{"format_version": "27", "units": 249, "progress": 249, "already": 0, "inert": 0,
 "failed": 0, "clean": 0, "clean_legacy": 66, "written_at": "2026-08-17T10:42:31.240209+00:00"}
```

**The sentinel is written only when `failed == 0 AND inert == 0`.** A run with any
`INERT` unit exits 4 and writes nothing -- this is the fix for the original silent-pass
bug (B3): the pre-fix script wrote a "success" sentinel after migrating zero units,
locking a corpus out permanently on the very first run. `inert > 0` now means the corpus
stays migratable: fix whatever is blocking the inert units (usually a hand-edit false
positive worth investigating) and re-run.

**Poisoned-sentinel self-heal.** A sentinel that fails to parse as the expected JSON
shape, or one whose `progress` field is `0`, is treated as POISONED: the run logs a WARN,
ignores it, and re-runs from scratch rather than treating an unreadable or zero-progress
file as "already done". This covers both a corrupted write and the legacy plain-text
`"migrated\n"` sentinel format some historical local branches wrote before the JSON
format existed -- v27 itself never shipped, so there is no real compatibility burden here,
just defensive handling of a state file that cannot be trusted. Manual recovery, if ever
needed, is `rm docs/.migrate-v27/.migration-complete` and re-run.

## Running it across repositories

`--project-root` defaults from `--docs-root`'s git toplevel rather than the invoking
process's CWD -- so running the migration against a `--docs-root` in a different repo
than the one the script is being invoked from resolves the project root correctly
instead of silently anchoring to the wrong repo (the old CWD-based default's failure
mode was a bare exit 2 with no repo context in the message).

## Language mirror trees

`docs/vi/` and `docs/jp/` (or any non-primary-language mirror) are **not migrated** by
this script, and pointing `--docs-root` at one is refused with exit 2 and a message
naming the translate pipeline as the correct next step -- not a silent partial run. The
discriminator is `docs/.rebuild-state.json`: it exists only under the primary tree, never
under a mirror, and the refusal guard checks for its absence. Reason: `docs/vi/` and
`docs/jp/` are derived artifacts. v27's own translate pipeline
(`references/pipeline-translate.md`, `references/translation-contract.md`) materializes
them FROM the primary tree; migrating a mirror independently would produce a tree whose
structure came from a different code path than the primary tree's, and the two could
silently diverge. The correct post-migration action is: migrate the primary tree, then
re-run translate to regenerate the mirrors from the now-migrated primary.

## The LLM prose-compaction pass (Modes A/B only)

The compaction pass itself is NOT run by any script here -- it is a separate,
human-reviewed authoring step the calling agent performs against STAGED content (never
live files), gated by `_audience_split_llm_invariant_lib.check_invariants(pre, post)`
before the result is ever accepted.

**The pass runs AFTER the validation gate, and may only shorten -- it can never be the
fix for a validation critical.** This was a live misconception during this migration's
own diagnosis (a critical was briefly assumed fixable by "let the compaction pass clean
it up") and is written down here so it does not recur: composition must already be
validator-clean before compaction ever sees the content, because compaction's own
invariant check (`check_invariants`, below) forbids adding anything a critical fix would
require -- it can drop a hedge word, never add a missing section, backfill, or code.

**Inputs:** the staged `functional-spec.md` (Mode A) or the folded
`behavior-logic.md` (Mode B) -- staging content ONLY, never a live file, and never
content I4 already ruled hand-edited or `doc_lock: user` (that content is carried
verbatim or the feature is skipped; it is never passed to an LLM at all).

**Forbidden operations** -- compaction may only SHORTEN. It may never:
- drop an H2 section
- drop or rename an FR/BR/SM/DEC/SCR code
- decrease the Edge Cases table's row count
- drop or alter a numeral, threshold, enum value, date, or endpoint count present in
  the source (H-FM4) -- this is the invariant that actually matters. Structure alone
  (identical headings, identical codes) lets a rule keep its code and its heading while
  quietly losing two of its three conditions; only a token-level diff catches that.

**Invariants checked (`check_invariants`)**:
1. Identical H2 heading set.
2. Identical FR/BR/SM/DEC/SCR code set.
3. Edge Cases table row count not decreased.
4. Every numeral (bare, `$`-money, `%`-percentage), ISO/slash date, and short
   backtick-wrapped enum/status/config token present pre-compaction is present,
   verbatim, post-compaction.

A violation of ANY of the four is a hard reject -- the caller must not swap the
compacted version into staging or live. `InvariantResult.ok` is `False` and
`.violations` names exactly what changed.

**Review gate (Requirement 5, mechanical, not advisory):** delete of v26 originals
requires a `--reviewed MANIFEST` acknowledging a SAMPLE of the migrated features --
default >=10% of this run's v26-eligible features, minimum 3
(`_audience_split_review_gate_lib.required_sample_size`). A manifest listing FEWER
slugs than the threshold is treated as ABSENT for the entire run -- delete is skipped
for every feature (not just the ones missing from the list), with a WARN, because a
too-small sample is not a real review pass regardless of which slugs it happens to name.

**What a reader should expect from the default run, stated plainly:** running the
migration with NO `--reviewed` flag at all is the common case, and its default outcome
is `migrated-originals-retained`, not the true v27 2-file shape -- `functional-spec.md`
and the reshaped `technical-spec.md` are written, but `business-context.md`,
`screens.md`, and `edge-cases.md` REMAIN on disk alongside them, with a WARN. This is by
design (a delete with no review pass is a delete nobody looked at), but it is easy to
misread as "the migration didn't finish" -- it finished; the v26 satellites are simply
still there until a `--reviewed` manifest clears the threshold. On the real 66-feature
corpus, a manifest naming 7 features (>=10% of 66, i.e. `(>= 7 required)`) let exactly
those 7 reach the true 2-file shape with their satellites deleted; the other 59 retained
all 5 files (the 2 new v27 files plus the 3 original v26 satellites) until reviewed and
re-run with an expanded manifest.

## Rollback

`--rollback` reverses a PARTIAL (sentinel-absent) Mode A run per feature, restoring
`technical-spec.md` from the retained pre-swap backup. A COMPLETED migration (sentinel
written) is reversed through the customer's own VCS, not this tool -- same posture as
`migrate_docs_layout.py`. Mode B/C do not yet have a dedicated `--rollback` path in this
pass; a partial Mode B/C run leaves its pre-swap backup in
`docs/.migrate-v27/{system/business-rules,screens/{slug}}/` for manual recovery.

## Post-migration sequence (v27.2.0)

A default run (no `--reviewed`) is a complete, correct migration that deliberately leaves
the three v26 satellites on disk pending human review (§ "What a reader should expect from
the default run", above) -- it is not a half-finished state, but it does have a fixed next
step, and that step has a fixed order:

```
1. migrate_feature_audience_split.py --reviewed <manifest>   # clears reviewed satellites
2. prune_mirror_v26_satellites.py --delete                   # drops the 3 retired
                                                               # filenames from vi/jp mirrors
3. /tkm:rebuild-spec --lang <code>                            # translates the now-clean primary
```

The order is fixed, not a preference: translate never deletes
(`_translation_sync_lib.discover_artifacts` enumerates the primary tree forward only), so
translating before step 1 mirrors the still-retained v26 satellites into every secondary
language, and pruning before step 1 would remove nothing (the primary satellites are still
there for the prune script's own refusal guard to catch, correctly, at exit 2 -- see
`prune_mirror_v26_satellites.py`'s docstring). `/tkm:rebuild-spec --migrate` runs the first
two steps for you, in this order, and REFUSES to hand off to the third (`mirror-skew`'s
translate handoff) while any feature dir is still `SHAPE_V27_HYBRID`, naming the exact
`--reviewed` command from the `[ACTION REQUIRED]` block rather than translating a corpus it
knows is not ready. See `references/pipeline-migrate.md` for the step registry this
sequence is wired into.

**The mirror `--docs-root` refusal guard's policy did not change, only its wording.**
`_audience_split_cli_lib.mirror_refusal_reason()` already refused a `docs/vi/` or `docs/jp/`
`--docs-root` before this release, with the correct policy ("migrate the primary first, then
re-run translate") -- v27.2.0 rewrites the message to name the concrete 3-command sequence
above instead of describing it in prose. A reader comparing before/after should not read this
as a behavior change: the refusal still fires on exactly the same discriminator (absence of a
mirror's own `.rebuild-state.json`), still returns exit 2, and still refuses unconditionally.
