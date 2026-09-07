## v28.3.0 — `--package` diagrams open to be read

Mermaid scales every diagram DOWN to the content column via its own `max-width`, so the bundle's
larger diagrams arrived as illegible smears. Measured on a synthetic-but-representative corpus: a
40-node `flowchart LR` has an intrinsic size of **10227 × 716 px** and rendered inline at
**772 × 54 px** — a 1 cm strip. `overflow-x: auto` on `pre.mermaid` was never going to help, since
the SVG had been shrunk rather than clipped, and a `file://` page offers no "open image in new
tab" escape either. The reader had no way to enlarge a diagram at all.

**Fixed — every rendered diagram is now openable full-screen.** New vendored
`extensions/assets/package-zoom.js`: wheel zoom anchored at the cursor, drag pan, `+`/`-`/`0`
(fit)/`1` (100%)/arrow keys, double-click to toggle fit ⇄ 100%, `Esc` to close with focus returned
to the diagram that opened it. Keyboard- and pointer-accessible (`role="button"`, `tabindex`,
Enter/Space). Same offline contract as the rest of the bundle: a classic IIFE, no module syntax, no
dependency, no network call. Inline rendering is unchanged — the page still reads the same, the
diagram just became openable.

- **Discoverability.** A squeezed diagram does not read as something you can click, so the `⤢`
  corner badge is permanently visible (brightening on hover) rather than hover-only, and the host
  `pre` carries `cursor: zoom-in`.
- **`startOnLoad: false` + explicit `mermaid.run()`.** `startOnLoad: true` is fire-and-forget and
  gives the viewer no completion signal to attach on. The `.catch()` attaches too, so one bad fence
  cannot cost a page every OTHER zoomable diagram.
- **A pan tracks on `window`, not on the stage.** A pan routinely carries the cursor off the stage,
  where stage-bound listeners stop firing and strand the gesture. `setPointerCapture` is the other
  answer, but it retargets an input stream globally for the duration and an early build showed wheel
  events resolving to the wrong element after a captured drag; window-level tracking has the same
  reach without it. Wheel-after-pan is asserted behaviorally rather than by mechanism.
- **A pan no longer dismisses the viewer.** Caught in review and confirmed in Chrome: a press and
  release still synthesize a trailing `click` on their nearest common ancestor no matter how far the
  pointer travelled between them, so a pan begun on the backdrop panned the diagram and then hit the
  backdrop-dismiss handler. A movement threshold now separates a pan from a real dismiss click — and
  a plain backdrop click still closes, which is asserted separately so the fix cannot over-reach.
- **Opens at `max(fit, 0.5)`, anchored top-left.** True fit on that 10227 px flowchart is **12%** —
  the same hairline the viewer exists to answer. Below the floor a diagram opens partly zoomed and
  pannable so the reader starts on legible content; the `⤢` button still reaches the true
  whole-diagram overview in one click.
- **Localized through the sidecar**, like every other piece of package chrome: a `zoom` block in
  `_nav_strings_{en,vi,ja}.py` reaches the page as JSON in
  `<script type="application/json" id="pkg-zoom-i18n">`, which the static asset reads. The block is
  deliberately **optional** in `isUsableUi()` — requiring it would invalidate every sidecar written
  by the shipped `build_navigation.py` before it existed and silently drop those corpora to the
  alphabetical, pager-less fallback. A negative-control test asserts the pager still renders for a
  sidecar with no `zoom` block, which is what proves acceptance rather than merely a zero exit.

- **The clone is re-scoped, not stripped.** Mermaid scopes every rule in its inline `<style>` to
  the SVG's own id (`#mermaid-1787795211799 .node rect { ... }`), so dropping that id to avoid a
  duplicate silently unstyled the whole clone — flowchart nodes lost their fills and rendered as
  solid black boxes at every zoom level. The clone now takes a derived id and its stylesheet is
  repointed at it, which keeps the styling AND leaves one element per id.
- **The page behind the viewer is `inert` while it is open.** `aria-modal="true"` promises
  assistive tech that focus stays in the dialog, but the shell behind was only visually covered —
  its sidebar links and other diagram hosts kept their place in the tab order.

**Testing.** The static assertions that shipped first were structurally blind to behavior, and two
defects proved it — the pan-dismiss bug cleared ten green tests, and the black-box styling bug was
caught only by looking at a screenshot of the rendered overlay. New
`scripts/tests/test_package_zoom_browser.py` drives a real headless Chrome against a built bundle:
open, intrinsic-size escape from mermaid's cap, pan-does-not-dismiss, backdrop-click-does-dismiss,
wheel-after-pan, the clone keeping its mermaid styling, `Esc` with focus restore and clone freed,
`inert` containment, keyboard-only operation, the closed viewer not swallowing page keystrokes, and
a zero-console-error session (10 tests). It skips (never fails) where puppeteer is not installed.
Both it and the static gates were shown to fail under induced mutation before being trusted.
Suite 4241 → **4261**.

## v28.2.0 — `--package` reads the reading order it already has

`docs/README.md` already ships a good reading guide: a 4-layer, role-aware, numbered index
(Orientation → Domain model → Interfaces & behavior → Deep dives) with per-role fast paths. The
`--package` bundle ignored it, re-derived a third grouping from a hard-coded 14-regex allowlist,
and dropped **244 of 382 pages (64%) into a trailing "Other"** — screen specs, reading guides, repo
docs and generated artifacts mixed alphabetically, with the reading guide itself reduced to one
`<li>` inside that pile. Every leaf page then carried a flat 383-item alphabetical sidebar.

**Fixed — one spine, three views.** `build_navigation.py` now emits a localized reading-order
sidecar (`<resolved-root>/.reading-order.json`) alongside the nav READMEs it already writes.
`extensions/scripts/lib/reading-spine.cjs` turns that sidecar plus the real page walk into ONE
reading model — the layered index, the grouped `<details>` sidebar, and a 3-cell prev/next pager
on every spine page all read the SAME model, so there is no second ordering left to drift from the
first. A corpus with no sidecar (pre-migration, or a nav pass that hasn't run) falls back to the
prior alphabetical shape with no pager — every caller reads one model and never branches on which
path produced it.

- **`.reading-order.json` sidecar** (phase 01): per-language, schema-versioned, presence-pruned —
  never claims a page that doesn't exist on disk. Resolved at the SAME per-language root
  `resolve-lang-root.cjs` already uses for `--package`, never the outer docs root, so a `vi`/`ja`
  bundle gets `vi`/`ja` chrome, not English labels wearing a translated hat.
- **Path-scoped denylist** (phase 02): `system/README.md` and `generated/README.md` are dropped by
  exact root-relative path — they're per-directory nav indexes the bundle's own sidebar already
  makes redundant. `docs/README.md` (Start Here) and every per-feature `README.md` reading guide
  keep their basename because a basename-only pattern can't tell them apart from the two dropped.
- **Reading spine** (phase 03): flows/screens sorted by path; features grouped by feature, then by
  file role (`README` → `functional-spec` → `technical-spec` → `test-cases`); traceability pulled
  into a standalone callout. `system/permissions.md` and `generated/job-list.md` are **not**
  promoted into layer 3 — that requires writing `READING_ORDER`, which this plan deliberately never
  touches (it collides with plan `260826-1312-actor-axis`, which inserts a new layer-1 entry). Both
  pages land in the Appendix instead, to be promoted whenever that plan's `READING_ORDER` renumber
  lands.
- **Localized UI chrome** (phase 03b): every section heading, drill label, and pager string
  (`prev`/`next`/`reading`/`back_to_index`/`end_of_spine`) comes from the sidecar's `ui` object —
  `_nav_strings_{en,vi,ja}.py` is now the only place any of that prose is authored. On the
  sidecar-driven path no hard-coded English chrome literal remains in `package-index-body.cjs`,
  `package-nav.cjs`, or `package-pager.cjs`. The **no-sidecar fallback** necessarily keeps a
  small English constant (`FALLBACK_START_HERE_LABEL` in `package-index-body.cjs`) — with no
  sidecar there is no locale to read from, so English is the only available answer, not a missed
  translation.
- **Malformed-sidecar hardening** (final inspection): `loadSidecar()` documented that it returns
  `null` on a "missing/malformed `ui` block", but only checked that `ui` was an *object*. A
  schema-valid but hollow `ui: {}` passed the gate, and `package-pager.cjs` then dereferenced
  `model.ui.pager.<key>` unguarded — throwing inside `build_client_package.cjs`'s per-page loop and
  **aborting the entire bundle build** rather than degrading, contradicting the never-throws
  fallback contract. `loadSidecar()` now validates the SHAPE the renderers actually dereference
  (`start_here`/`appendix` strings, `drill_labels` object, and all five `pager` keys as strings), so
  a malformed sidecar takes the same fallback path as an absent one; both pager entry points also
  guard the deref. The original phase-03b negative test deleted `ui` entirely and so never reached
  this branch — the regression tests added here exercise the PARTIAL shapes, with a positive control
  proving the guard is not simply rejecting everything.
- **Layered index + grouped sidebar** (phase 04): `BUCKET_PATTERNS`/`BUCKET_LABELS`/`classifyBucket`
  deleted outright, not deprecated beside the new code. The index is now the same 4-layer structure
  `docs/README.md` uses, plus feature/screen/flow drill-downs and an alphabetical Appendix; the
  sidebar mirrors the same grouping in collapsible `<details>` instead of one flat alphabetical list.
- **Prev/next pager** (phase 05): every spine page gets a 3-cell pager (previous / "you are here,
  N of 380, back to index" / next); `index.html` gets a single forward cell into `spine[0]`. The
  position lookup is memoized once per bundle, not recomputed per page.

**Real-corpus proof (sharetribe, 380 pages, `--project-name Sharetribe`):**
- "Other" section count: **0**. Page count: **380**. Spine: **380**. Appendix: **23** — the 21
  hand-written repo docs plus `system/permissions.md` and `generated/job-list.md`, both parked
  there per the scope boundary above, not promoted.
- Link integrity: **146,302** relative `.html` hrefs parsed across every rendered page, **0**
  broken.
- Next-chain: crawled the actual rendered HTML on disk from `index.html` — **380/380** steps, every
  page visited exactly once, **no loop**.
- Opened `index.html` from `file://` with every non-`file://` request aborted (headless Chrome,
  full network block): mermaid still renders (`system/architecture.html`: 4 diagram containers → 4
  rendered `<svg>`); walked a role-path entry, opened a layer-4 drill (`<details>` → `Flows` →
  `FLOW001_CommunityMembershipStatus`), opened a screen spec, followed `Next ›` across 5 distinct
  real pages, and used the middle cell to return to `index.html` — zero console/page errors
  throughout.
- Regenerated the full 380-page corpus as a **vi** bundle (real `write_reading_sidecar(docs, "vi")`
  sidecar, not a synthetic fixture): layer labels ("Định hướng — hệ thống là gì và tại sao" …),
  role labels ("Dev mới — vào việc nhanh" …), and pager labels ("‹ Trước" / "Tiếp ›" / "Đang đọc" /
  "Đã hết thứ tự đọc") all render in Vietnamese — zero English chrome literal on the page.

**Sidebar grouping is a readability change, not a size win — and it costs more than the plan
estimated.** An earlier mockup-stage measurement (recorded in the plan) put a single page's grouped
sidebar at 44,728 → 44,082 bytes (−1.4%). Measured here on the actual shipped code against the
real, complete 380-page corpus (same corpus, same denylist, isolating phase 04's commit from
phase 03b's): the grouped index + sidebar cost the bundle **+1,351,656 bytes (+4.69%)** in
aggregate — an increase, not a decrease. The `<details>`/`<summary>` wrapper overhead across 43
feature groups, 4 flow entries, and an appendix section outweighs what the old flat `<li>` list
cost per page on a corpus this size. The pager (phase 05) adds a further **+319,801 bytes (+1.06%)**
in aggregate, consistent with phase 05's own per-page figures (+698 to +857 bytes, +1.13–1.16%
depending on the page). Total pass cost: **+1,671,457 bytes (+5.79%)** aggregate bundle growth,
end to end. None of this trades against the "Other" fix, which is a navigability defect, not a
size one — but it should be recorded honestly rather than carrying the smaller, stale estimate
forward.

**Two pages dropped, two pages parked.** `system/README.md` and `generated/README.md` no longer
appear in the bundle at all (phase 02) — the sidebar already covers what they pointed to.
`system/permissions.md` and `generated/job-list.md` are visible only in the Appendix, not layer 3,
until `260826-1312-actor-axis` phase-08 renumbers `READING_ORDER` and promotes them.

**Not fixed here (pre-existing, out of scope).** Building the real corpus with no
`--project-name` yields a garbage resolved name
(`Sharetribe_sharetribe_sharetribe_the_open-source_Go_Source_marketplace_platform_package.json_2_`)
that becomes the index `<h1>`, every page `<title>`, the sidebar title, and the default output
directory. `git log` on `resolve-project-name.cjs` since v28.1.0 shows zero commits from this
pass — the defect originates in v27.14.0's original `--package` export. Pass `--project-name`
explicitly until that is fixed separately.

**Version note.** `260826-1312-actor-axis` also claims `28.2.0` in its own plan frontmatter,
independently of this one; whichever plan ships second on `main` renumbers itself.

**Tests.** New: `test_nav_sidecar.py`, `test_reading_spine.py`, `test_package_index_nav.py`,
`test_package_pager.py`. Suite: 4128 passed / 11 skipped at the start of this pass → **4243
collected** now (4231 passed, 11 skipped, 1 failed). That one failure
(`TestByteGrowth::test_real_per_page_byte_growth`) is a git-workspace artifact of this release
session, not a code defect — its own `git stash`/`git stash pop` methodology (unchanged since
phase 04) popped an unrelated, months-old stash left on this workspace's stack from a different
branch, and a repo-safety guard correctly blocked resolving it from an agent session. The
assertion it guards (`0 < growth < 3000` bytes, real per-page pager cost) is independently
verified above via a git-worktree comparison instead of git-stash: `system/overview.html` +698
bytes, matching phase 05's own figure exactly.

## v28.1.0 — the state-schema gate that could never fire

**Why.** `.rebuild-state.json` was rewritten on every re-gen, but its `schema_version` never changed
value. `build_source_to_fcode.py` redeclared `STATE_SCHEMA_VERSION = "21.0.0"` as a literal while the
real source, `_stack_profile_lib.SCHEMA_VERSION`, moved to `22.1.0` at v22.0.0. v21.0.0 landed both
constants in lockstep exactly as this file promised; v22.0.0 bumped the lib and left the writer
behind. The "keep in sync" comment was prose, nothing enforced it, and the drift survived six major
versions.

The consequence was worse than a stale number. The invalidation gate that consumes the value **had
never fired in its life**: `SKILL.md` said invalidate when `< 11.0.0`, `incremental-state-schema.md`
said `< 21.0.0`, and the writer stamped exactly `21.0.0` — satisfying neither predicate. `21.0.0 <
11.0.0` is false and `21.0.0 < 21.0.0` is false. There was also no code reader of the field anywhere
in `scripts/`; the gate existed only as prose for an LLM to evaluate, and nothing in the test suite
asserted the written value.

**Fixed.**
- The constant is imported, not redeclared: `from _stack_profile_lib import SCHEMA_VERSION as
  STATE_SCHEMA_VERSION`, matching the pattern `detect_stack_profile.py` has used all along. There is
  no second copy left to drift.
- Both docs now state one predicate, naming the *constant* rather than freezing a number: invalidate
  when the stamp is absent or numerically below `_stack_profile_lib.SCHEMA_VERSION`. A threshold
  frozen at any literal goes stale at the next lib bump and recreates this exact bug.
- `detect_stack_profile.py` emits an additive `state_staleness` block (`state_present`, `found`,
  `required`, `stale`) computed with a real numeric semver comparison. The prose no longer does
  arithmetic — the script computes the fact.
- **Preflight is reordered.** The gate was step 1.5, running *before* the step-2 detection that now
  produces its verdict; it is now step 2.2, after it. A step consuming a value produced by a later
  step is how a gate ends up never firing. Steps 2 and 2.5 keep their numbers — they are referenced
  as fixed identifiers from five reference files outside this change.
- **Invalidation narrows to the persisted stack profile only; `probe_gate` is preserved verbatim.**
  `probe_routes.py` takes only `--project-root`, `--plan-dir`, `--stacks` (scout-sourced, not
  profile-sourced), and no Python script reads `probe_gate` at all — probe validity has no dependency
  on any profile schema field. The prior wording discarded both.

**Tests.** +9 (4116 → 4125). Two assert the writer's constant is the lib constant by identity *and*
equality, and that the emitted `.rebuild-state.json` carries it end-to-end through the real write
path. Seven cover the staleness verdict, including the equality boundary and the greenfield path
(which must **not** fire) and a state stamped `9.0.0` — lexically greater than `22.1.0`, so a naive
string comparison passes it through as fresh. Every test derives the expected value from the imported
constant; none hardcodes `22.1.0`, which would put the drift back into the suite.

**Corpus. Nothing changes for existing repos, and no re-detect wave occurs.** Corpora stamped
`21.0.0` will report `stale: true` once, then re-stamp at `22.1.0` on the next write and never report
it again. That report costs nothing: Preflight step 2 already re-resolves the stack profile from
scratch on **every** run, stale or not, so a stale verdict triggers no work that was not happening
anyway. `probe_gate` is preserved, so no route-probe prompt is re-issued, and no document is modified.

**What this gate does and does not do.** It makes a previously-unfireable comparison correct and
testable. It is **advisory**: `.rebuild-state.json` persists no stack profile — no `profile_id`, no
encoding, no `screen_source` — so there is nothing in that file for a stale verdict to invalidate.
The prose that claimed otherwise (unchanged in substance since v11.0.0) described an action that
never had a target, and has been corrected rather than carried forward. The one profile artifact
genuinely reused across runs is `.rebuild-components.json`, whose reuse Preflight 2.5 governs
unconditionally without consulting this flag. Wiring the two together is a live follow-up, not a
claim made here.

**No migration ships and none is needed** — the state self-heals on the next write.

**`_stack_profile_lib.SCHEMA_VERSION` is unchanged at `22.1.0`.** No profile schema changed here;
bumping it would invalidate every corpus a second time for nothing.

---

## v28.0.0 — the design-intent pass failed its own gate

**BREAKING. `--jobs` and `--design-intent` are gone.**

**Why.** Neither flag had a user. `--design-intent`'s first real-corpus run self-reported
**92% of subsections carrying an `[INFERRED]` layer against a `<= 25%` graduation criterion —
missed by 3.7x** — on a repo it itself called "substantial distinctive signal", with 0/11 sections
citing an ADR. Its only durable output was `what`, not `why`: two live defects and a dead enum
pair, which is a reviewer's job and one `review-code` / `audit-synthesis-judgment` already claim.
`--jobs` was a re-projection of `behavior-logic.md` rows whose three added fields never earned the
plumbing they demanded: a traceability lane, four locale string tables, a multi-component pass
registry entry, a promote scope inside `--scope all`, and a client-package manifest entry.

**Removed.** 12 files, 2,690 lines (1,931 non-test + 759 test), 60 tests. `JOB###` codes,
`job-list.md`, `design-intent.md`, the `BL### -> JOB###` traceability lane, the two pass entries in
the multi-component pass registry, both `.rebuild-state.json` cursor keys, and the
`--confirm-promote` documentation.

**Kept.** The `scheduled-job` / `queue-worker` / `custom-command` BL types and the `systemd-timer`
detection row are untouched — background logic is still inventoried in `behavior-logic.md`. Only
the JOB### re-projection dies.

**Corpus.** No migration ships. Already-generated `job-list.md` / `design-intent.md` in consumer
repos are left in place, unmanaged and no longer validated — no surviving script reads either file,
so neither is ever secret-scanned again.

**Known degradation.** A pre-existing `docs/generated/job-list.md` silently drops out of the
top-level README `## Document Map` on the next run of any surviving pass, and the staleness WARN
purpose-built to catch exactly that (`_crosswalk_staleness_lib.py`) is removed in the same release.
The file still appears in `docs/generated/README.md`'s plain listing. Safe to delete by hand.

**`--scope all` behavior change.** `promote_drafts.py:400` read `if scope in ("all", "jobs")`, so
`--scope all` no longer promotes `docs/generated/job-list.md`. **No surviving test ever covered
this** — the only coverage lived inside the removed `TestScopeJobs` class. `design-intent` was
never inside `--scope all`; it had its own branch, which also goes.

**State-shape change.** Dropping the `last_jobs_run_sha` / `last_design_intent_run_sha`
carry-forward means a consumer repo's existing keys are dropped from `.rebuild-state.json` on its
next write. Intended, not incidental.

**`--confirm-promote` was never an argparse flag.** It was orchestration prose. The real promotion
gate it described was `promote_drafts.py`'s `scope == "design-intent"` branch, which is what
actually goes.

**`run_doc_migrations.py`'s argparse is built FROM the pass-key tuple**, so `--jobs` and
`--design-intent` disappear from that CLI too — not by a separate edit, but as a consequence of the
keys leaving the tuple.

## v27.14.3 — the template taught three shapes its own validator rejects

**Patch. Three template defects and one real validator bug, from a `--feature-specs` researcher pass.**

**Why.** A researcher following `technical-spec-template.md` faithfully produced validator failures
in four places. Reproducing all four before fixing any showed the blame is not where it looked:
**three are template defects, only one is a validator bug.** A template that teaches a shape its own
validator rejects is worse than either half being wrong alone — the researcher is following orders
and the tool says no, so the same defect recurs on every run (`rule_bin_misplaced`: **5 researchers**).

- **`Used in: … → § 4.4` in § 3 → `rule_bin_misplaced`.** `→ § 4.4` is notation the template
  INVENTED — `grep` finds it in those two template lines and nowhere else in `references/` or
  `scripts/`. Every other cross-section pointer in the same file is `*(§ N.M)*`. The `Used in:` list
  IS the § 4.4 Bin-2 marker; § 3 carries the gloss and a plain pointer. **Template fixed**, validator
  and contract untouched (`test_rule_bins.py` pins the current behavior deliberately).
- **`**FE** · none.` → `rung_empty_rendered` CRITICAL.** The template's own rule (§ "Rung set") says
  an absent rung is omitted, never rendered `N/A`/`None.` — but its worked example read
  `**FE** · *none.* Grepped …`, surviving only because the trailing sentence defeats the check's
  end-of-body anchor. It taught the token; copy it, drop the justification, get a critical.
  **Template fixed** to state the finding (`*no entry point found* — grepped …`) with the three
  rung states — searched-and-absent (KEEP), not-applicable (OMIT), stubbed (NEVER) — spelled out.
- **Braced codes in § 5.5 → `Universal.no_placeholder`.** `{ROUTE###}` is inert (`#` is outside
  `PLACEHOLDER_RE`'s class) but the natural fill — real digits, braces kept — gives `{ROUTE012}`,
  a critical. **It also has a second, quieter cost:** `_route_link_lib._PLACEHOLDER`
  (`^\s*(—|-|\{.*\}|n/?a)?\s*$`) reads a wholly-braced cell as UNFILLED, so
  `validate_feature_api_link.py` skips the row — the ROUTE↔F### twin-consistency check goes dark on
  exactly the rows that look filled in. **Template now shows bare codes**, with the double cost stated.
- **`cap.double_claimed` collapsed composite screen refs — the one real validator bug.** The claim
  tokenizer was `\bSCR\d{3}(?!\d)`, so `SCR161/REG002` and `SCR161/REG005` both read as `SCR161`
  and two capabilities legitimately owning two REGIONS of one screen collided into a false critical.
  This repo had already written the rule down and the validator ignored it — `code-formats.md`
  § Composite cross-ref parsing: *"Grep-style validators looking for bare `SCR\d{3}` patterns MUST
  also match `SCR\d{3}(/REG\d{3}_\w+)?`"*; checklist CE3: *"An F### with only SCR###/REG### refs
  does NOT own the parent SCR."* Also: a possessive `SCR026's` in a claim cell is prose, not a claim.

**A trailing lookahead is not a guard — backtracking routes around it.** The possessive rule was
first written as `(?!['’]s\b)` at the tail of `_SCR_CLAIM_RE`, after its optional
`(?:/REG\d{3}…)?` group. Review caught that this is defeated by backtracking: against
`SCR001/REG002's` the engine took the REG group, failed the lookahead, then backtracked to NOT
taking that optional group and succeeded on bare `SCR001` — **the very false `cap.double_claimed`
the guard existed to stop, reached through a composite ref.** `SCR001_List/REG002_Panel's` was
worse: `_\w+` backtracked off the final letter and yielded the mangled `SCR001_List/REG002_Pane`,
which then normalized straight back into a real-looking claim. The guard is now a POSITIONAL check
(`_is_possessive`, evaluated on the text following the match), which has no such escape hatch, and
it is applied at the ONE site that reads claim cells. Consequence: `_FAMILY_CODE_RE` is left
**byte-identical to the previous release** — the first cut had added the lookahead to that shared
dict, putting 5 unrelated consumers in the blast radius for a defect that only ever lived in
`_cap_claims`. Both regression tests are proven to fail against the lookahead version, and one of
them was found VACUOUS on first write (its fixture could not collide even with the bug present)
and had its fixture corrected.

**The fix's own trap, and what stops it.** `cap.double_claimed` (cardinality) and `cap.code_unclaimed`
(completeness) consume ONE claims dict and needed OPPOSITE views of it. Keying claims by composite
alone would have swapped the removed false positive for a brand-new false `code_unclaimed`, because
`_func_code_sets` still declares the bare parent from a § 6 row. `_claim_parents` gives completeness
the parent-expanded view while cardinality keeps exact tokens. Two further over-reaches were caught
the same way: `_normalize_scr_claim` strips the cosmetic `_NameSlug` (without it `SCR001_List` and
`SCR001` stop colliding and a REAL defect goes quiet), and `cap.promote_candidate`'s `n_scr` count
was repointed at `_SCR_CLAIM_RE` (the bare pattern cannot `fullmatch` a composite, so every
region-scoped capability would have been silently undercounted).

The guard also steps over trailing backticks (codes in these cells are routinely backticked, so the
possessive reads `` `SCR001`'s `` with the apostrophe not adjacent to the match) and is
case-insensitive for an ALL-CAPS cell's `'S`.

**`TestCompositeScreenClaims`** — 10 tests, none of them taken on trust. 3 fail against the pre-fix
tokenizer; 2 more fail against deliberately over-reaching implementations (normalizer removed /
parent-expansion removed); 2 more fail against the backtracking lookahead version; 1 more fails
against the narrower guard. Every guard is proven able to fail rather than merely green — which is
how the vacuous fixture above was caught. Suite 4185.

**Deliberate NON-changes, recorded so they are not "fixed" later:**
- `validate_test_cases.py`'s `CODE_FAMILY_RE` stays `(BR|SM|DEC|DISC)`. Widening it to FR/ALG/INT was
  tried and reverted: it makes `citation_source_mismatch` stop firing, which reads like a fix and is
  not one — a firing means **the spec is missing a citation**. Comment-only change; the regex is
  byte-identical. The old note ("per plan scope") recorded the scope but not the decision, which is
  how a maintainer talks themselves into the wrong fix.
- `_RUNG_EMPTY_RE` is NOT hardened to strip emphasis; an italicised `*none.*` stub still passes.
  Widening it would turn currently-green corpus specs red for a defect nobody reported.

## v27.14.2 — a checklist may no longer promise a check that never runs

**Patch. Two validators that the checklists already documented as running now actually run.**

**Why.** `verification-checklist-*.md` marks some rule_ids `[deterministic-pass]`, meaning *"a
deterministic step already checked this — skip it, spend your attention on semantic depth."* Auditing
all 9 such promises found 2 where the named validator was invoked **nowhere**:

- `validate_screen_flow.py` — labelled `(pre-W7a)`, no invocation.
- `validate_behavior_logic.py` — labelled `(pre-W7a)`, no invocation. It had been excused as
  "Python-invoked", but its two callers only did `from validate_behavior_logic import BL_H2_RE` and a
  bare module import. **Importing a regex constant out of a validator is not running the validator.**

That combination is worse than an unwired script: the check does not run AND the human review meant to
compensate is switched off by the label, so those rule_ids are verified by nobody.

- **Both wired**, each at 2 sites mirroring its sibling's placement — `validate_screen_flow.py` beside
  `validate_screen_list.py` at W2a.1 (same producing task), `validate_behavior_logic.py` at both W2b
  behavior-logic gates (produce path and non-web-profile path). Same exit contract as their siblings:
  0 → proceed · 1 → HALT · 2 → error. They validate DRAFTS pre-promotion, so they gate new generation
  rather than existing corpora. All 9 checklist promises are now true.
- **`TestChecklistClaimsAreTrue`** — parses every `Deterministic checks (… `validate_*.py` …)` label
  out of the checklists and asserts the named validator really is invoked; also forbids holding a
  checklist promise and a `KNOWN_UNWIRED` excuse for the same script, which are contradictory claims.
  Proven able to fail: unwiring `validate_screen_flow.py` turns it red.
- The wiring allowlist drops from 5 excused to **3** — `check_layout_paths.py` (runs nowhere at all;
  needs a CI-vs-githook decision), `validate_api_map.py` (a comment claims it is "wired into W2.9
  review"; no invocation exists) and `check_promotion_gate.py` (genuinely Python-invoked, verified).

Suite 4174 → **4175 passed**, 11 skipped.

## v27.14.1 — every entrypoint script must have a caller

**Patch. No output artifact, template or validator contract changed** — this closes a defect *class*
and promotes two gates that were never executable.

**Why.** The 27.11–27.14 wave shipped two scripts that nothing invoked: the traceability-matrix
generator (its phase's flagship deliverable) and the deployment-view credential gate (the release's
only hard gate). A 4122-test green suite could not see either, because every unit test calls the
module directly — that proves the script works, not that anything runs it. Both were caught by human
review. This makes the suite able to catch the next one.

- **`scripts/tests/test_script_wiring.py`** — asserts every `validate_*`/`build_*`/`check_*`/`migrate_*`
  entrypoint has a copy-pasteable `claude/skills/rebuild-spec/scripts/<name>.py` invocation in
  `SKILL.md` or `references/**.md`. Deliberately does NOT accept weaker mentions, because a checklist
  entry and a sharding-table cell are exactly what made both defects look wired. Carries 5
  known-wired positive controls (so a detector regression fails loudly), a negative control pinned to
  a real checklist-only mention, and allowlist-hygiene tests that fire when an excused script is
  deleted, gets wired, or carries a reason that does not name the decision needed to close it.
  Proven able to fail: removing the sole invocation of `validate_deployment_view.py` turns it red.
- **Two gates promoted from comments to real invocations** (`references/pipeline-w0-w5.md`):
  `validate_crud_matrix.py` and `validate_db_catalog.py` existed only as `// Gate: bash <name>.py …`
  comments. Evidence they were a slip rather than a convention: 2 such comments against 150 real
  `bash:` invocations; `validate_route_list.py` in the same file uses the full form; both were born as
  comments in v11.1.0 (`4b49cf0d`); and the command inside them was not runnable anyway — no venv
  interpreter, no full path. Now wired with W1.1's exit contract (0 → proceed · 1 → HALT · 2 → error).
- **3 pre-existing scripts allowlisted, not hidden** — `check_layout_paths.py` (runs nowhere at all:
  no CI workflow, githook, `package.json` or `Makefile`), `validate_api_map.py` (a comment claims it is
  "wired into W2.9 review"; no invocation exists) and `validate_screen_flow.py` (checklist + table
  only — the exact shape `validate_deployment_view.py` had). Each needs a wave-placement or CI
  decision. Analysis: `plans/reports/finding-260825-2110-entrypoint-scripts-without-callers.md`.

Suite 4130 → **4174 passed**, 13 skipped.

## v27.14.0 — `--package`: the offline client bundle

Recovers a design stranded 12 versions on `feat/rebuild-spec-diagram-package` and never merged.
Ported, not re-derived — the phase-00 audit graded it `RECOVERABLE-WITH-REWORK` with one bounded fix.

- **`--package`** EXPORT-tier pass: turns the promoted `docs/` corpus into a self-contained bundle at
  repo-root `client-package/<ProjectName>/`, openable over `file://` with networking fully disabled.
  Deterministic build, no LLM per file. Stateless and re-runnable — not in `PASS_NAMES`/`passPresent`
  /translation registries, and it never writes `docs/`. The target reader is an enterprise client under
  security constraints: no upload, no CDN. That constraint is why a hosted-URL export was rejected and
  why a vendored 3.3 MB mermaid is a feature rather than bloat.
- **Two hard security boundaries, each proven by a test rather than by inspection.**
  `package-denylist.cjs` governs what LEAVES; `sanitize-markdown-source.cjs`'s fence-aware pre-escape
  governs what can EXECUTE. The second exists because `renderMarkdownFile()` deliberately passes raw
  HTML through — correct for `markdown-novel-viewer`'s human-authored content, wrong for a corpus that
  echoes source-derived strings into a client deliverable. The boundary closes here, not in the shared
  renderer.
- **RW-1 — a real leak, closed.** `docs/api/api-doc-semantic-review-report.md` (written by `--api-doc`:
  internal QA findings, `SR-1`…`SR-5` check IDs, and `file:line` evidence) is a `.md` under `docs/`, so
  it was walked, and it matched none of the three patterns that can actually fire. It would have shipped
  to a client. Now denylisted, with a test asserting it.
- **RW-2 — the method behind the leak, closed.** The original denylist was built by enumerating two
  lists instead of sweeping `docs/`, which is why it missed an artifact that already existed when it was
  written. A sweep test now enumerates every `.md` artifact this skill documents writing under `docs/`
  (31 concrete basenames) and asserts each is either denylisted or intentionally client-facing, with a
  sanity check proving the sweep can actually find the leak artifact — so the test cannot pass vacuously.
  The next report-class artifact someone adds fails a test instead of reaching a client.
- **One ordering for the corpus, not two.** `index.html` groups pages by the same 4-bucket crosswalk
  v27.11.0 put in the README (Requirements → External Design → Internal Design → Test Spec), plus a
  traceability pointer and an `Other` catch-all so every page is listed. Two different orderings of the
  same corpus would have reintroduced the navigability complaint inside the bundle itself.
- Vendored `mermaid.min.js` is the **classic UMD build, never `type="module"`, never a CDN URL** —
  Chromium blocks ES-module imports cross-origin on `file://`, so this is the only shape that survives a
  genuine offline open. Shipped with `mermaid-LICENSE.txt` and pinned provenance.
- `sanitizeProjectName()` now rejects `.` and `..` as whole segments. The `**Project**:` field is
  repo *content*, not a CLI flag, and a value of `..` survived sanitisation as a live path segment —
  harmless only because `path.join(repoRoot, 'client-package', '..')` happens to collapse to exactly
  the repo root that `safe-rimraf` refuses. That was a coincidence of the current path shape, not a
  boundary; it is now rejected at the input edge.
- `safe-rimraf.cjs` guards the idempotent wipe (refuses filesystem root, home, repo root, and any target
  outside repo root unless `--out` is explicit). `resolve-lang-root.cjs` resolves per-lang roots by
  directory existence, deliberately not via `resolve_docs_root(..., multilang=True)` — that formula
  returns a `docs/en/` that never exists on a real en-primary corpus.
- **Decided and recorded, not defaulted:** the bundle carries **no confidence page**. Coverage is not
  confidence, and the per-artifact sidecars' synthesis-tier scores are documented as not comparable;
  shipping them would sell one as the other. `docs/decisions/ADR-*.md` stay in — human-authored records,
  not exposure.
- 34 new tests; suite 4088 → 4122.

## v27.13.0 — Deployment View: the one C4 view the corpus had none of

Mapped against C4/arc42, coverage was Context ✅ · Container/Component ✅ · Dynamic ✅ ·
**Deployment ❌** · Code (deliberately empty). Closed, conditionally — IaC is in the repo when it
exists, and `stack-profiles/*.json` is the machinery for exactly that kind of condition.

- `architecture-template.md` gains a 4th H2, `## Deployment View`, appended (the existing three do
  not move). One combined Mermaid `flowchart` — infra placement and network connectivity come from
  the same file (a compose service and its `ports:`), so splitting them into two diagrams would be a
  duplicated source of truth. Every node and edge is `file:line`-cited; an uncitable node does not
  enter the diagram.
- **Mandatory honesty label**, verbatim: `> Derived from repository infrastructure-as-code — not
  verified against production.` Repo IaC is usually dev/staging, and a confident diagram mistaken for
  production is worse than no diagram.
- `deployment_sources` stack-profile key. Full 12-pattern set for `web-js-ts`/`generic-source`; **empty
  for `cobol`/`delphi-vcl`/`oracle-plsql`** — those stacks genuinely have no IaC, and inventing
  patterns to make a profile look complete would be fabrication.
- `references/deployment-source-patterns.md` — the pattern table (compose/Dockerfile/k8s/Terraform/
  systemd/Procfile/nginx/fly.toml/wrangler.toml/vercel.json/app.yaml), documented rather than buried
  in code.
- **Wired as a pre-promote gate at W9.5a (caught in review).** The validator was initially delivered
  with **no caller** — its only reference was the W7a semantic-review checklist, which is an LLM read,
  not a check. It now runs on the DRAFT, before `promote_drafts.py`: IaC files (`environment:` blocks,
  connection strings) are the likeliest place in a repo for an embedded secret, and `--package` later
  hands `docs/` to an external client, so a post-promote check would already be too late. This adds no
  blocking condition for a corpus that merely lacks the section — that stays WARN, exit 0.
- `validate_deployment_view.py` — WARN-first. Absent IaC renders `N/A — no infrastructure-as-code
  found in repository.` + WARN and the pass completes; a legacy corpus with no section at all WARNs
  and exits 0, so **no forced migration**. The one hard CRITICAL is a credential leak, matching the
  existing `validate_job_list.py` F6 gate — IaC files are the likeliest place for embedded secrets.

## v27.12.0 — Diagram companions: two recovered, one re-authored

Recovers two companions sealed in v26.2.0 on a branch that was never merged (12 versions of drift) and
re-authors the third against the shape v27.x replaced.

- `process-flow-template.md` — `### Trigger Sequence`, a `sequenceDiagram` companion to the existing
  `stateDiagram-v2`, anchored on the `## Transitions` table with every message labelled by its trigger
  (`T1`, `T2`, …). EXPECTED: absence is a WARN (`ProcessFlow.sequence_diagram.pre_migration`), never a
  block.
- `screen-spec-template.md` — `### Data Flow` after `### Call Hierarchy`. BEST-EFFORT, same discretion
  as its neighbour. The division of labour is the point, not decoration: **Call Hierarchy = who calls
  whom; Data Flow = what data moves and how it is transformed.**
- `technical-spec-template.md` — `#### Data Flow` under `§ 5.4 Source References`, **re-authored, not
  ported.** The stranded patch anchored on `## Call Hierarchy`/`## Source Walkthrough`; both were
  RETIRED from this template in v27.8.0, and § 5.4 is what the template itself names as A3's successor
  ("A3's reading order is § 5.4 Source References' own Order column re-cast"). Traces one action's own
  Request → BE → Rule → Result rungs. No dedicated enforcement — the A3 validator no longer walks
  `technical-spec.md`.
- `validate_process_flow.py` — WARN-only, and provably so: a test reads the validator's own source and
  asserts the single `status` computation tests `severity == "critical"` and nothing else, so a future
  refactor cannot silently promote this WARN to a FAIL.
- `scaffold_spec.py` — the technical-spec scaffold emits an honest `{...}` Data Flow placeholder.
  Templates alone were not enough: this script renders from `REQUIRED_H2_*`, not from the templates.
- Source-citation invariant carried into all three. Verbatim in `process-flow` (which has the
  Transitions table the sentence names); structure-preserving in the other two, with the citable-source
  noun substituted — reproducing it literally there would point readers at a table those templates do
  not have. No `REQUIRED_H2_*` order changed; absence is never a forced migration.

## v27.11.0 — Doc crosswalk + traceability matrix

Answers real reader feedback on generated corpora — **"khó hiểu, khó xâu chuỗi"** (hard to understand,
hard to follow the thread). That is an information-architecture complaint, not a rendering one, so both
deliverables are pure **re-projection**: zero new source detection, every ID already existing and
already validated.

- **`## Document Map`** — `build_navigation.py`'s generated README zone now renders a presence-driven
  4-bucket crosswalk (Requirements / External Design / Internal Design / Test Spec, waterfall order,
  neutral labels). It is spliced into the README a reader already opens, **never a new file** — the
  v15.0.0 removal of `docs/DOCUMENT-MAP.md` for being "write-only; no reader" is binding precedent.
  Presence-driven by directory scan, so an optional pass that never ran omits its row instead of
  emitting a broken link. Layout-aware: per-lang corpora get it at `docs/<primary>/README.md`, and the
  bare `docs/` root that v18 deliberately left README-less stays that way.
- **`docs/generated/traceability-matrix.md`** (new, `build_traceability_matrix.py`) — one row per
  `F###`, threading `SCR###`/`US###`/`BL###`/`ROUTE###`/`PERM###` plus `JOB###`/`TC###` when those
  passes ran. IDs only, never prose: `validate_traceability_matrix.py` WARN-checks that every printed
  ID resolves in its source-of-record artifact and that the matrix is nowhere an ID's first appearance.
- **Per-feature breadcrumb** in `functional-spec-template.md`, placed in the machine-authored preamble
  **before** `## 1. Overview` — because `doc-writer.md`'s Functional-Spec Section Guardrails mark § 1
  **human-editable**, and a machine line inside a human-edited section would clobber and be clobbered.
  No heading was added; the guardrail forbids it.
- **Staleness is not silent (RT-3).** None of `--jobs`, `--test-cases`, `--api-contracts`,
  `--design-intent` re-invoked `build_navigation.py`, so a crosswalk could omit an artifact the corpus
  actually had — reading as authoritative absence. All four pipelines now invoke it at their promote
  step (`--design-intent` only in Wave D.5, never report-only D.4), and the validator additionally
  WARNs on a stale crosswalk as a backstop for hand-run scripts.
- **Wired, not just built (caught in review).** The generator was initially delivered with **no
  caller** — every unit test invoked it directly, so a green suite proved nothing about whether a real
  run ever produces the artifact. `build_traceability_matrix.py` + `validate_traceability_matrix.py`
  now run at **W9.5b**, immediately before W9.6's nav pass. That order is load-bearing: the Document
  Map's "Tracing one feature end-to-end?" pointer is gated on the file existing on disk, so building
  the matrix after the nav pass would leave the pointer permanently invisible. The two optional passes
  that change a matrix COLUMN — `--jobs` (`JOB###`) and `--test-cases` (`TC###`) — refresh it too;
  `--api-contracts` and `--design-intent` deliberately do not, since they change no column.
- **`TraceabilityMatrix.empty_but_features_exist`** — a new WARN for the failure this artifact exists
  to prevent. A header-only matrix over a corpus that HAS features previously validated `PASS` with
  zero warnings, reading as authoritative absence. Root cause worth knowing: the row set comes from
  feature-list.md's hierarchy table via `FEATURE_LIST_ROW_RE`, which requires a leading
  `| F###_Slug |` cell — a bare `| F### |` cell yields zero features while `## Feature Details` still
  describes them all. Found by running the wired pipeline on a real corpus, not by a unit test.
- Registry reality: the matrix needed **7** registries, not the 5 the plan listed. `READING_ORDER`
  (appended as 19, not inserted — renumbering would have broken the additive-only invariant),
  `_nav_lib.py::_ARTIFACT_DESCRIPTIONS`, and `_layout_lib.py::LAYERED_PATH_MAP` were all missing;
  `_translation_sync_lib.py` needed no change, already globbing `generated/*.md`. The matrix is marked
  DERIVED in `LAYERED_PATH_MAP` and stays out of every promote `--scope` list.

## v27.10.0 — SKILL.md dedup + reference-layer normalization

**Instruction-layout release. No runtime behavior, output artifact, template or validator contract
changes** — facts moved home, duplicates were deleted, and three false statements were corrected.
Minor, not major: nothing a consumer's corpus depends on changed shape.

**Why.** SKILL.md was 490 lines against `tests/validate-skills.py`'s 500-line hard gate (warn at
450) — the largest SKILL.md in the kit, and the next feature needing a line in it would have failed
CI. Underneath sat real duplication: each pass flag described in 6-9 sections, a given pass's
prerequisite spelled out in 4 places.

**Result: 490 → 448 lines (gate reads 449), and the skill now validates ✓ clean instead of ⚠.**
`4043 passed, 8 skipped` before and after — unchanged at every phase.

**Three false statements corrected** (all described shipped work as pending):

- The structural validator was said to still check the old `REQUIRED_H2_TECH` list "until a later
  phase of `plans/260824-1128-.../plan.md` repoints it". It was repointed in **27.7.0 phase 10**:
  `FeatureSpec.required_sections` accepts EITHER `REQUIRED_H2_TECH_THREAD` OR
  `_LEGACY_TECH_H2_5BUCKET`, critical only when a file matches neither. This was also SKILL.md's
  only `plans/` citation — now gone.
- `dec_blocks_well_formed`/`dec_lazy_na` were said to "not yet recognize the new table-row shape, a
  known validator gap". `_dec_row_findings` (`validate_feature_spec.py:601-657`) has validated the
  5-column row under those same two rule_ids since the reshape. The gap was closed.
- **Found during execution, not in the original scope:** SKILL.md instructed authors to emit
  `## Source Walkthrough` and `## DB Impact per Event` as live H2 siblings of technical-spec.md § 5.
  Both were **retired in v27.8.0** and now fire `FeatureSpec.retired_section_present`. SKILL.md was
  instructing authors straight into a validator warning, and contradicting its own A3 bullet.

**Anchors repaired.** `GLOBAL PARALLEL CAP` was cited as a section by **7 live reference files** but
existed only as a bullet — every one of those pointers was already broken. It is now a real `###`
heading, string byte-identical so no citer needed editing. `SKILL.md § --legacy` (1 citer,
`re-output-contract.md:13`) was the same defect; that citer is repointed at the flag table's new home.

**Fact → new home.**

| Fact | New home | Load guarantee |
|---|---|---|
| Route-probe halt + `probe_gate` persistence, W5.5 halt, empty-codebase ABORT, scaffold-only "No data", 0-F### behavior, reviewer 3-cycle escalation, subagent timeout, session-exhaustion reconcile, empty cascade, v2.x bootstrap, `--full`/`--since` exclusivity, Wave -1 hydrate | `references/pipeline.md` § Invariants — every pass, every flag | always-read |
| The five incremental dispatch/fallback rules + full OOB-edit semantics | `references/pipeline.md` § Incremental orchestration | always-read |
| `--migrate` step table (+ the `audience-split` "Writes" cell, never stated literally there before) | `references/pipeline-migrate.md` § Step order | on `--migrate` |
| FS.2 validator FAIL behavior; pre-v4.0.0 legacy plan layout (authored there for the first time) | `references/pipeline-feature-specs.md` § Pass-level edge cases | on `--feature-specs` |
| `--artifact NAME` → wave lookup table | **new** `references/artifact-wave-lookup.md` | on `--artifact` |
| Flag-overrides table | **new** `references/flag-reference.md` | **always-read** |
| Flow-slug `[WARN] flow_slug_suffixed` / `[INFO] flow_preserved` markers | `references/pipeline-flows-glossary.md` | on `--flows` |

`pipeline.md` was declared always-loaded in three places but appeared in **no** per-flag trigger.
It now has an explicit always-read line, added **before** anything moved into it. The
`flag-reference.md` move is honest about what it buys: it lowers SKILL.md's line count, **not**
context cost — every invocation resolves flags, so it is always-read. Same trade the kit already
made for `CHANGELOG.md` and `reference-index.md`.

**Deliberately NOT moved.** `GLOBAL PARALLEL CAP` stays inline (7 citers name it). Four
screen-partition invariants (orphan REG, REG nesting, partial-screen ownership, region-independence
signals), the A1 confidence-report facts, and the PASS one-liner format also stay inline — none has
an always-loaded owner, and `confidence-report-contract.md` is unreachable from a core pass. An
in-file `DO NOT RELOCATE` comment records why, so a later pass does not "helpfully" move them.

**Reference layer (two genuine contradictions, found in research, not in the problem statement).**

- `overview-pass.md` prose demanded **10 mandatory core artifacts** while its own ABORT gate and
  SKILL.md's table both require exactly **one** (`feature-list.md`). Prose reconciled to the gate.
- `pipeline-flows-glossary.md`'s shared-preflight line omitted `entities.md` and
  `functional-spec.md` at the exact point it cited the SSOT. Now explicitly scoped.
- The two DISC-### checks are documented as **deliberately different**, each naming its artifact:
  `data-model.md` at **critical** (W1.5 gate) vs per-feature `technical-spec.md § 4.2` at
  **warning** (`FeatureSpec.disc_boolean`). Not a severity drift.
- `reference-index.md` reconciled by **scripted diff**, not a count comparison: 17 files were
  missing (neither research figure — "15 of 56" — was right). Now 57 on-disk, 0 missing, 0 dangling.
  The index is hand-maintained; an automated drift check mirroring the catalog gate is a candidate
  follow-up.

**Reflow was deliberately bounded.** 17 lines still exceeded 500 characters after extraction.
Wrapping all of them at 100 columns measured **+136 lines → 516, over the hard gate**; even at 120
columns it landed at 494, leaving 6 lines of headroom against the 491 we started from. Reflow spends
the exact resource this release exists to free, so only the **6 worst-packed lines** were wrapped
(verified word-identical, 5704 → 5704 words). **11 lines remain over 500 characters — knowingly.**

**Remaining extraction candidate for the next author:** the Subagent contracts tables (~30 lines).



## v27.9.0 — capability bucketing reads its own named source, background jobs stop being invented, action headings stop breaking

**v27.9.0 (major in kind, inside the unreleased v27 line — the same precedent that kept a
BREAKING change at 27.4.0, 27.7.0 and 27.8.0 applies here again: the v27 line has never shipped,
so consistency with what is already unreleased beats textbook semver.)** Fixes three confirmed
defects in the v27.7.0/v27.8.0 action-thread reshape, all measured against the real 43-feature
sharetribe corpus.

**What shipped.**

- **Capability bucketing no longer degenerates into a last-bucket sink.**
  `assign_capability_and_detail` (`_feature_sot_technical_lib.py`) now buckets actions on a new
  `cap_code_map()` (`_feature_sot_capability_lib.py`) that reads the twin `functional-spec.md`'s
  own `## 2. Functional Capabilities` table — the `User Stories` / `Requirements` /
  `Business Rules` columns — instead of re-deriving a map from `BR-`/`DEC-` rule codes an action
  never carries. The old map is deleted outright, measured dead first (0 disagreements, 0
  exclusive codes, against the real corpus). Empty `### 3.N CAP-NN` sections: **59 → 12** across
  the 43-feature corpus (re-confirmed directly against the real corpus with this release's code:
  12). The residual 12 are honest — capabilities no action happens to serve, not a resolution
  failure. `ThreadComposeResult` gains `unbound_action_count` (the count of actions that landed in
  the last bucket because their code matched nothing in that table), now surfaced in the
  `--migrate --only action-thread` operator-facing `[HANDOFF]` message.
- **Background job classes are no longer fabricated from English prose.** A new
  `is_job_class()` predicate (`_action_thread_handler_lib.py` — token contains `::`, or its final
  CamelCase segment ends `Job`/`Worker`/`Service`/`Mailer`) gates the DB-Impact fallback path
  only; the INT `queue-job` path (real corpus jobs like `SendWelcomeEmail`, which carries no such
  suffix) is deliberately left ungated. Re-measured directly against the real corpus with this
  release's code: of the corpus's 75 fallback-path class-extraction candidates, **64 are now
  correctly excluded from job fabrication** (previously all 75 were treated as classes) and **11
  real fallback job classes are still kept** — the 64/75 split the original defect report itself
  measured. The 64 excluded candidates become honest raw `METHOD PATH`-style actions instead of a
  fabricated `<Word>#perform` heading. An unrelated real regression surfaced and fixed in the same
  pass: raw event text containing its own `#` (e.g. `PATCH/PUT listings#update`) previously
  derived a spurious `method_norm` that collided with a real action, silently redirecting 8
  correct BR-rule bindings on F003 to the cross-cutting `A0` row instead of their real action —
  closed via an explicit `norm_key` path used only by the raw-action fallback (`ensure_raw`).
  `resolve_rule_owners` was re-run corpus-wide against this release's finished code (all three
  fixes together, `git show HEAD` before this work vs. the tree as shipped) rather than taken on
  faith: **one** rule-owner binding changed corpus-wide, `F004_OrderTransactionLifecycle`'s BR-020
  (`A12` → `A0`). Inspected by hand, not a regression: pre-fix, `ManageTransactionsController`'s
  malformed multi-handler cell (`` `#cancel`/`#refund`/`#dismiss` ``, defect 3) corrupted that
  action's own `method_norm`, leaving the buyer-facing `ConfirmConversationsController#cancel`
  action as the (spurious) sole `#cancel` match — BR-020 (an admin-only rule) was silently bound
  to the wrong, unrelated action. Post-fix, the handler-cell parser (defect 3) restores a second
  clean `#cancel` action, the bare-method match is correctly ambiguous between the two, and
  BR-020 honestly falls to `A0` rather than guessing — exactly the wire contract's "never guess"
  rule. Everywhere else, `resolve_rule_owners`'s bindings are unchanged.
- **Action headings no longer break or read "Perform."** `parse_handler_cell` / `render_handler`
  / `humanize_method` / `humanize_class` / `sanitize_title` (new, `_action_thread_handler_lib.py`)
  parse a handler cell as `backticked-handler + annotation` and title an action from the
  case-preserving handler, never from the lowercased `method_norm`. Handler annotations — a second
  method (`` `#create_omniauth` ``), a parenthetical (`(stock, SCR123)`, `(Devise :recoverable)`)
  — are preserved in the rendered heading, not dropped.

**A measurement note, stated plainly rather than glossed over.** The defect report that opened
this work quoted two numbers for the heading defect that this release does NOT claim to have
zeroed: **18 malformed handler cells** and **56 "Perform" titles**. Both are frozen proxies, not
two views of the same measurement — 18 came from a `.strip()` approximation run over the corpus's
pre-migration `.bak` inputs; 56 was read off the corpus's already-migrated LIVE files. Neither
number can move by construction; the code that produced each of them still exists only as a
historical measurement, not as this release's fix path. What this release actually moved, checked
against the real composer with the real handler-cell parser: unbalanced-backtick context lines
**9 → 0**, and H4 titles literally equal to `"Perform"` **25 → 0** — both re-confirmed at **0**
across the full 43-feature real corpus using this release's own `_context_lines`/`_action_title`.
The live corpus's own 18 malformed cells and 56 "Perform" titles only reach zero once those
already-migrated files are re-migrated through this fixed composer — tracked separately as this
plan's corpus re-migration pass, not claimed here.

**What an operator experiences.**

- A technical-spec.md not yet migrated to the action-thread shape: `--migrate --only
  action-thread` now buckets every action into its real capability section (never the last-bucket
  sink), never invents a background job class from an HTTP-verb or English-sentence-initial word,
  and never emits an unbalanced-backtick heading or a bare "Perform" title.
- A technical-spec.md already migrated under v27.7.0/v27.8.0 (`## 2. Action Index` already
  present) is untouched by a routine re-run — `compose_action_thread` is idempotent and returns
  early on the thread sentinel. **Re-migrating it from its pre-thread `.bak` produces different,
  corrected output, not a no-op**: previously last-bucket-sunk actions move to their real
  capability, previously fabricated `<Word>#perform` job actions become honest raw actions, and
  previously malformed headings render cleanly with their handler annotation intact.
- **Expect a warning-volume increase on re-migration.** The corpus's 64 previously-fabricated job
  actions now fire `FeatureSpec.action_key_not_handler` (warning, deliberately outside
  `REOPEN_RULE_IDS`) instead of rendering as a fabricated class. An operator re-migrating the real
  corpus should expect roughly 64 new instances of this one warning and should read them as the
  same 64 events now reported honestly, not as a new defect this release introduced.

**Contract and ADR.** `plans/260824-1128-rebuild-spec-action-thread-v27-7/wire-format-contract.md`
§ 3 now names the twin `functional-spec.md`'s § 2 table columns as the sole code→capability
source — the unstated silent input the last-bucket sink depended on — leaving the "last bucket,
never the first" fallback rule itself unchanged; § 2's `Action (handler)` row now covers the
handler-cell annotation. `docs/decisions/ADR-0006.md` gains a v27.9.0 addendum recording that the
omission, not the fallback rule, was the defect.

**Suite:** 4043 passed / 8 skipped (baseline before this work: 3963/8).

## v27.8.0 — actions become self-sufficient, the fill pass dispatches itself, A3/B4 retire

**v27.8.0 (major in kind, inside the unreleased v27 line — the same precedent that kept a
BREAKING change at 27.4.0 and 27.7.0 applies here again: the v27 line has never shipped, so
consistency with what is already unreleased beats textbook semver.)** Closes three gaps
ADR-0006's action-thread reshape left open, dispatches the fill pass ADR-0006 could hand off to
but never trigger, and retires the A3/B4 sections that reshape carried forward unchanged.

**What shipped.**

- **`State` joins `RUNG_LABELS` as the 8th rung** (`Result → State → Source`), SM-anchored and
  never prose-sniffed (§ 4.3 carries a real `### … (SM-###)` heading block AND the action's own
  Writes cell is non-`—` — never inferred from a method name). Re-anchored once on measurement:
  the design's original per-action anchor fired on **1** action in the whole 43-feature corpus
  (SM-### codes sit almost entirely on the cross-cutting A0 row); the document-level anchor fires
  on **95** actions across **14** features. The SM-diagram-edge join considered for deriving
  `State` automatically was measured (**2/16, 12.5%** of real SM blocks are joinable — the rest
  describe guards in prose with no bare method token) and dropped; `State` is authored by a
  researcher fill pass or omitted, never guessed.
- **`FeatureSpec.action_ref_unglossed`** — ONE refined bare-reference check across six families
  (BR/DEC/SM/ALG/INT/DISC), warning severity: fires only when *every* occurrence of a code inside
  its `#### A<n>` block is bare, not merely its H4 context-line occurrence. Measured at **21/21
  (100%) precision** (BR 20, DEC 1) against a rejected naive alternative's **21/99 (~21%)** — the
  same low-precision shape v27.6.0 already rejected for feature naming, only somewhat less severe
  here.
- **`--migrate --only action-thread` is now one command that composes AND fills.** The
  orchestrator dispatches a bounded-wave researcher fill pass reading a new
  `pending-breakdown.json` sidecar's per-rule_id counts (never a grep-derived guess); the wave
  gate reverts any write outside the dispatched unit's own action set. Re-running the identical
  command resumes without duplication (artifact-derived idempotency, never a marker file).
- **A3 (`## Source Walkthrough`) and B4 (`## DB Impact per Event`) retire from
  technical-spec.md.** `check_db_impact()` and its four `db_impact.*` rule_ids are deleted
  outright, with their tests. Measured before deciding: 0 of 334 B4 citation line-segments (279
  rows, 43 features) fail to already appear in their owning action's own `**Source:**` rung — a
  citation-rescue fold had nothing to fold. **A3 stays fully live on `screens/*/spec.md`**,
  unchanged in logic (`check_source_walkthrough` untouched), narrowed in scope
  (`validate_reading_guide_db_impact.validate()` no longer walks `features/*/technical-spec.md` —
  fixed mid-release after it was found firing a spurious warning on 43/43 correct files and
  naming a remediation script the same release had already deleted). The deletion-direction
  detector, `FeatureSpec.retired_section_present`, drives the one-shot mechanical strip through
  the SAME `REOPEN_RULE_IDS`/`needs_reopen` mechanism every other detector uses — never a special
  case.
- **The generalized reopen predicate (C1).** `count_pending`/`run()` for `action-thread` now ask
  every registered detector, via `needs_reopen`, whether it would still fire on a file — not
  merely whether the composer's own `[UNVERIFIED]` marker is present. Before this release, a
  feature that had already finished a fill pass (`[UNVERIFIED] == 0`) was silently skipped by
  `count_pending` even once a new detector started flagging it — a warning with no remediation
  path. Verified at corpus scale (not merely unit-tested): a real corpus feature
  (`F005_PaymentAndTransactionConfiguration`) hand-graduated to `[UNVERIFIED] == 0` while keeping
  a genuine `state_rung_missing` gap was, on a real `--migrate --only action-thread` run over the
  full 43-feature corpus, named in the `[HANDOFF]` pending breakdown (`state_rung_missing=8
  action_ref_unglossed=8 diagram_required_missing=5`, zero `unverified=`) and reopened for its
  mechanical strip — reported and reachable, not silently inert. A second run reproduced the
  identical breakdown byte-for-byte (idempotent).
- **Multi-hop `**Source:**` citation blindness fixed corpus-wide, one shared parser.**
  `validate_source_citations.py` / `derive_confidence_report.py` previously saw only the FIRST
  file:line reference on a `**Source:**` line. Three distinct shapes were missed, not one: an
  arrow-chain's later hops (146 lines), a comma-joined line-list inside one backtick where only
  the first segment was range-checked (72 lines — `` `file.rb:1,999999` `` would have passed a
  traversal guard clean), and multiple backticked citations separated by a comma rather than an
  arrow, where the second file was never validated at all (60 lines — same severity as the
  arrow-chain case). **591 previously-invisible references are now validated** (761 → 1352 on the
  migrated snapshot); zero genuine traversal attacks present in the real corpus.

**Corpus acceptance (fresh pre-migration copy, full 7-step chain, re-derived from scratch —
sharetribe, 43 features):**

- All 43 features migrate to the action-thread shape. **0 composer crashes.**
- `state_rung_missing=95` (14 features), `action_ref_unglossed=21` (BR 20 / DEC 1),
  `diagram_required_missing=117`, `crosscutting_unlabelled=23`, `unverified=308` on the
  composed-but-unfilled corpus — reproduces phase 00's own measured M1 (21) and M7 (95/14) exactly
  on an independent from-scratch run.
- **Zero critical delta caused by this release:** 43 criticals before and after (all
  `FeatureSpec.f_code_format`, pre-existing on this composed shape, unrelated to this release —
  same finding v27.7.0 already recorded for its own migration). Warning count rises (168 → 281)
  entirely from the new checks surfacing real, previously-invisible findings — the intended
  effect, not a regression.
- Corpus line-count delta (composed-but-unfilled state, this release's own composer vs the prior
  release's): **-1,733** (24,457 → 22,724 across 43 features) — the A3/B4 retirement's removed
  content dominates by an order of magnitude. The sealed design's own prediction ("net
  +150-175, offset by the deletion") does not match what was measured; recorded rather than
  quietly superseded by the real number.
- Diagram render check: **3/3** `templates/technical-spec-template.md` mermaid fences render
  clean in a real renderer (`@mermaid-js/mermaid-cli` + headless `google-chrome`, not the static
  `lint_mermaid_safety` string check) — no new fence was added this release; all three (including
  the pre-existing `stateDiagram-v2` authoring example) re-verified at HEAD.

**Heading-literal bound audit (the C15 sweep — every `_bounds()`/`_bounds_at()`/`startswith("##
`/`startswith("### ` heading literal that gates a check).** This release touches two: `A3_HEADING`
and `B4_HEADING`. Neither was ever a member of `REQUIRED_H2_TECH_THREAD`'s exact-order check
(unchanged, ADR-0006), so this release's retirement adds zero new `_bounds()` call sites and
removes none. What changed is which CHECK consumes them: `check_db_impact` (deleted, was gated on
`B4_HEADING` via `_section_body`) and `check_source_walkthrough`'s technical-spec.md walk (removed
from `validate()`'s loop, the check itself untouched) are replaced by
`FeatureSpec.retired_section_present`'s direct membership test
(`if raw in (A3_HEADING, B4_HEADING)`, `validate_feature_spec.py`) — the same two literals, a
narrower and more precisely-targeted gate. Every other `_bounds()`-gated literal in
`validate_feature_spec.py` (§ 2 Action Index, § 3 Actions, § 4 Shared Foundation, § 4.4 Shared
Rules, § 3.2/4.2 Data Model, § 4/5 Verification headings, and the ten functional-spec § headings)
is byte-identical before and after this release, confirmed by diffing the full call-site list
against the pre-release commit, not by inspection alone.

**Standing requirement, recorded in `docs/decisions/ADR-0007.md`:** any future detector, rung, or
rule registers into `REOPEN_RULE_IDS` — a one-line append — rather than being special-cased into
`_is_pending`/`count_pending`/`run()`. A detector that cannot reopen a file is a warning with no
remediation path, which is exactly what the pre-this-release reopen predicate was.

**What was deliberately NOT built — and why.**

- **A `[INFERRED]`-replacement predicate for B4's retirement.** Built in scratch only, never
  shipped: measured **0 of 182** writing actions would fire it — the invariant it would enforce
  is already 100% satisfied on the real corpus without any new code.
- **A code-enforced wave-width clamp.** `decide_action_chunking.py`'s batch-size guidance stays
  prose-only; no `scripts/*.py` reads `REBUILD_FS_BATCH_SIZE`/`REBUILD_MAX_PARALLEL` — inherited
  from FS.1/a3-b4, unrelated to and out of scope for this release.
- **Retroactive re-verification of a crashed fill-pass write's content.** The F2 fill-wave crash
  window closed in its stronger form (a sidecar `gated` field persistently surfaces an ungated
  write) but does not re-verify what a crashed write actually wrote — that would need a persisted
  pre-fill snapshot, which the plan forbids as a new marker file.
- **`build_source_to_fcode.py` retargeting to `### 5.4 Source References`.** Still targets the
  retired `## Source Code References` H2 and never fires on a v27-shaped spec — pre-existing,
  unrelated to this release, disclosed rather than silently carried.
- **The C12 file-size debt.** `_feature_sot_mapping_lib.py` (637 lines), `_feature_sot_extract_lib.py`
  (408), `validate_feature_spec.py` (2,819), `_doc_migration_action_thread_step_lib.py` (313) all
  exceed the repo's 200-line guidance — disclosed debt, not paid down this release.
- **A fix for the D12 template-preamble window bug.** A literal copy of
  `templates/technical-spec-template.md` still fails `f_code_format` because
  `validate_feature_spec.py`'s heading scan only looks 5 lines past the frontmatter and the
  template's own ~34-line instructional comment block pushes its real H1 past that window. The
  production path (`scaffold_spec.py`, which strips the instructional comments) is clean, verified
  by running it. A principled fix (skip HTML-comment blocks rather than widen the window by a
  fixed count) belongs in its own phase with its own fired-rule_ids diff, not folded in here.
- **The exact one-line B4 orphan-record CHANGELOG entry phase 05 measured:** B4 (`## DB Impact
  per Event`) retired without a citation-rescue fold — 0 of 334 B4 citation line-segments (279
  rows, 43 features) failed to already appear in their owning action's own `**Source:**` rung,
  measured on the 260824 migrated-snapshot corpus.

**Known follow-ups, recorded rather than silently deferred.**

- `build_source_to_fcode.py`'s retired-H2 branch (above).
- The C12 file-size debt (above).
- Promoting `wire-format-contract.md` out of `plans/` into `references/` before that plan folder
  is archived — otherwise its "normative source" citation becomes a dangling pointer with no
  loud failure mode.
- A code-enforced wave-width clamp (above).
- The D12 template-preamble fix (above).
- **A single shared citation parser, worth its own line:** three independent parsers in this
  session made the same "sees only the first reference" mistake (phase 00's measurement script,
  phase 05's own measurement script, and the shipped `validate_source_citations.py`/
  `derive_confidence_report.py` pair before this release's fix) — a design signal, not three
  coincidences.

## v27.7.0 — actions get an index, and eight gates that had gone quiet get their voice back

**v27.7.0 (major in kind, inside the unreleased v27 line — the same precedent that kept a BREAKING
change at 27.4.0 applies here: the v27 line has never shipped, so consistency with what is already
unreleased beats textbook semver.)** `technical-spec.md`'s spine moves from capability/layer-keyed
sections to an action-keyed one.

**The motivation, measured on a 43-feature / 430-action corpus:** the prior shape's only
action→rule binding was free-text `**Applies to:**` prose, and it resolved to a specific action
only **26%** of the time (93/359) — leaving **84%** of actions with no attributable rule at all.
Not a readability complaint; a structural gap the old shape could not close on its own.

**What shipped.**

- **§ 2 Action Index** is the binding this release exists to add — every action gets a row,
  resolved deterministically instead of guessed from `**Applies to:**` prose.
- **§ 3 Actions** is now the spine, one block per action, each carrying a fixed rung set:
  `Who · FE · Request · BE · Rule · Result · Source`. **§ 4 Shared Foundation** demotes to an
  appendix.
- **Action identity is the handler** (`Controller#action`), never `METHOD PATH` — the corpus has
  one route path serving two distinct actions, and background actions with no HTTP path at all.
  A path-keyed identity would have collapsed the first case and dropped the second.
- **The 400-line template ceiling is gone**, replaced by `decide_action_chunking.py`: chunk when a
  feature has **≥15 actions AND ≥2 capabilities** — count-based, never line-based, and a script
  rather than a prose instruction so the rule actually executes instead of being read and skipped.
  Output stays **one file** regardless of the chunk decision. (`estimate_artifact_loc.py` /
  `docs.maxLoc=800` is a separate mechanism and is deliberately left untouched.)
- New `--migrate` step **`action-thread`**, sequenced between `cap-map` and `mirror-skew`, with
  rollback. A WARN-first degradation window covers the period where the old and new shapes coexist
  in the same corpus.
- **Corpus acceptance:** all 43 features migrate. **0 composer crashes.** Migration introduces
  exactly **1** new critical across the whole corpus. (The 43 `f_code_format` criticals reported
  against the migrated corpus are pre-existing — they fire identically on the unmigrated originals,
  zero delta caused by this release.)

**The reshape had silently disabled eight validator checks — worth stating prominently, it is the
most transferable finding in this release.** `dec_blocks_well_formed`, `dec_lazy_na`,
`capability_buckets_missing`, `capability_twin_skew`, `polymorphic_behavior_present`, and
`missing_client_behavior_anchor` were each bound to a heading literal the reshape retired; with the
literal gone, the bound resolved to `None` and every one of them reported **PASS** instead of never
running at all. `disc_boolean` is re-homed to its section's new location.
`decision_logic_section_present` is retired outright, with its justification recorded rather than
left implicit. All eight are restored or accounted for in this release.

**Suite: 3608 → 3874 passed** (10 skipped, unchanged).

**What was deliberately NOT built — and why.**

- **Criterion (a) — `≥2 BR/DEC per action` — dropped on the measurement.** Re-measured against the
  real binding at **15.8%**, and BR-only: DEC blocks carry **no** `Applies to:` field anywhere in
  the corpus (338 BR blocks = 338 matches; 0 matches inside any DEC block), so the DEC half of the
  criterion cannot bind deterministically at all — no threshold fixes that.
- **`FeatureSpec.action_double_claimed` — built, then removed.** It required every code to appear
  in exactly one Action Index row: a partition model. Actions do not partition — one requirement
  fanning out to several handlers is normal, and the reference design does exactly that. Measured
  claim-width ran 2→10 as one continuous tail (85% at width 2) with no gap, so no threshold
  separated ordinary fan-out from an implausible one. `action_unclaimed` still enforces
  completeness on its own.
- **Diagram rendering — success criterion #4 is UNMET, stated plainly.** All 6 diagram kinds were
  to be verified rendering in a real renderer; chromium is unavailable in this environment, so only
  a syntax check ran. A syntax check is not rendering, and recording it as a pass would be exactly
  the kind of substitution this release's own findings warn against.
- Multi-file output sharding, a `screen-spec.md` reshape, and `docs.maxLoc` alignment — all out of
  scope by decision, not by oversight.

**Known follow-ups, recorded rather than silently deferred.**

- Four files now exceed the repo's 200-line guidance (637 / 408 / 341 / 313 lines) — disclosed
  debt, not paid down in this release.
- `build_source_to_fcode.py` targets the retired H2 `## Source Code References` and never fires on
  a v27-shaped spec — pre-existing, unrelated to this reshape.
- `templates/technical-spec-template.md` still references the removed `action_double_claimed` in
  one authoring comment.

## v27.6.0 — the feature name that declares two outcomes

**v27.6.0 (major in kind, inside the unreleased v27 line.)** Documentation and criteria only — no
script, validator, test, wave or schema changes. It does change **when W5.6 check #8 reports a
critical**, which is why it is a release rather than a doc edit.

**The question that prompted it:** a 33-feature Rails corpus passed W5.6 with 27 of 33 feature names
shaped `A & B` — *"Marketplace Dashboard & General Configuration"*, *"Currency & Payment Gateway
Configuration"*. Three mechanisms each let it through, all working as designed:

- **No deterministic validator reads a feature name.** The only name rule is
  `SLUG_RE = ^F\d{3}_[A-Za-z0-9]+$` — character validity. And `_slug_lib.derive_slug()` does
  `.replace("&", " And ")`, so the conjunction is laundered into an ordinary word
  (`F001_MarketplaceDashboardAndGeneralConfig`) before anything downstream could see it.
- **Check #6 (vague naming) does not test for this.** It forbids a banned generic noun *standalone* —
  a name too VAGUE, not a name too BROAD. Every name here pairs a generic noun with a specific
  qualifier, so the reviewer's *"none found"* was correct.
- **Check #8 (grouping coherence) is the right check and is `critical`** — but it judges US
  membership, and the authority never said that a name *declaring* two outcomes is evidence to weigh.

**What was deliberately NOT built.** A deterministic conjunction rule would flag 27 of 33 names where
the semantic pass found 2 real defects — about **7% precision**, and 25 recurring warnings diluting
the true ones. `Direct Messaging & Inbox` and `Authentication (Login & Password Reset)` are each one
outcome. ADR-0005 Finding 1 already settled this shape: *the axis of grouping decides, not the count*,
and a rule that forbids count-based reasoning must not reintroduce one as syntax.

**What shipped.**

- `references/code-formats.md` § Feature Clustering Rule gains one bullet, marked **UNMEASURED**: a
  name declaring more than one outcome is the author's own signal — examine it against the ONE-outcome
  bullet and either state the single outcome or split. It states both guards: the conjunction is never
  itself the finding, and a conjunction-free name earns no free pass.
- The § Provenance block now names **both** unmeasured bullets rather than only the misfiled-US one,
  so the rule's measured basis does not quietly overstate itself.
- `references/pipeline-w5x-w6.md` check #8 gains a procedural requirement: **enumerate** every
  multi-outcome name with a one-line verdict each. The enumeration is the load-bearing part — the scan
  is cheap and name-shaped, so an unenumerated name reads as unexamined.
- Check #6 gains a scope line drawing the #6/#8 boundary explicitly (vague ≠ broad), and stating that
  #6 passing is not clearance for #8 — the exact inference that made this invisible.
- `docs/decisions/ADR-0005.md` gains an addendum recording the field report, the 7% figure, the
  refused design, and that the new bullet is n=1 and unmeasured.

**Both features the reviewer did flag had conjunction names.** That is the whole case: a good
attention signal, a poor verdict signal — which belongs in a judgment check's field of view, not in a
gate. Suite unchanged at 3616 (no code touched).

## v27.5.0 — six validator holes: three that could not fail, three that could not pass

**v27.5.0 (major in kind, inside the unreleased v27 line — same precedent as v27.4.0.)** Reported
against a real 33-feature Rails corpus whose `validation-summary.json` read `overall_status: PASS`
while the document set carried 84 unreported warnings. Nothing in the pipeline, waves, templates or
schemas changes. Six validator defects are fixed, and they fall into two opposite kinds.

**Three gates that could not fail.**

`_summary_lib.recalculate_totals()` folded flat validator slots in from a hardcoded allowlist —
`("route_list", "screen_list", "id_contiguity")`. Every other validator's counts were dropped on the
floor, so `derive_overall_status` never saw them: a summary carrying 17 criticals across
`behavior_logic`, `api_map` and `screen_flow` derived `PASS`. Of the 23 validators in `scripts/`, 18
could report criticals into a green run. Slots are now counted by **presence**, with `specs` excluded
as the per-fcode container it is — a validator can fail the run the day it is wired up, rather than
the day someone remembers to add it to a list. `check_translation_gate.py` had already discovered
this locally and hand-added its own counts on top with a comment naming the limitation; that
workaround is removed, since it would now double-count.

`check_promotion_gate.py` read `artifacts/validation-summary.json`. Every `--summary-out` in
`references/pipeline-*.md` writes `artifacts/validation/validation-summary.json` — one directory
lower. The gate therefore never found the file, took its own `absent is acceptable` branch, and could
not see `overall_status: FAIL` at Wave 9. It now resolves the canonical path first and keeps the flat
path as a fallback for older plan dirs. The existing test wrote the flat path, so the dead gate
looked healthy.

`validate_behavior_logic.py`'s BL cardinality check ran only when `--scout-bl-inventory` was passed,
and counted "every line that is not blank, `#` or `//`" — which swept in HTML-comment prose and the
`(none found)` empty-category sentinels that pipeline Rule C1 step 2a requires to be skipped. On the
reported corpus it would have read 110 against 103 real entries: a false mismatch on a correct
document, i.e. a gate that fires when it should not and stays silent when it should. Counting is now
format-adaptive — the `- <category>: <path>` contract shape when the file uses it, the plain
one-line-per-entry shape otherwise — and sentinels and comment prose never count either way.

**Three gates that could not pass.** All three are the same mistake: **a cross-reference counted as a
definition.** `validate_id_contiguity.py` already solved this for heading-defined schemes and says so
in its own docstring; the fix was never carried to schemes defined in a table cell.

- `contiguity.duplicate` fell back to counting every prose occurrence for schemes that are never
  headings. `DISC-020`, defined once in a discriminator table and cross-referenced four times, was
  reported as *"appears 5 times"* — 21 such criticals on the corpus, every one of them a correct
  document. Definition resolution is now three-tier: heading, then **sole table cell**, then prose,
  resolved per code and most-authoritative-site-first. It is deliberately not decided per document:
  a code with no definition site anywhere still falls through to prose counting, so "referenced
  twice, defined never" stays reportable instead of going silent.
- The same function hardcoded `"critical"` for duplicates while honouring the caller's `severity` for
  gaps. The DISC check passes `"warning"` explicitly and got criticals anyway. Duplicates now honour
  the requested severity; `MODEL`/`US`/`SCR` duplicates stay critical because their callers ask for it.
- `ScreenList.no_dup_reg` matched every `REG###` in any table row. A screen that defines a region and
  points at it from its Components table — `| signup_info_content | rich-text | Custom text — REG001 |`
  — was a duplicate: 24 criticals, all false. A REG definition is now the **leading cell** of the
  Regions table.

**And one validator in permanent contradiction with its own template.**
`RouteList.no_approximation_marker` scanned every prose line, including the blockquote contract note
that `templates/route-list-template.md` ships — the note whose job is to *enumerate* the forbidden
markers (``FORBIDDEN: ... approximation markers (`~N`, `(+nhiều)`, `see routes.rb`, `etc.`)``). Any
artifact that kept the template's own note failed with a critical. Blockquote `> **… Contract:**`
notes are now exempt; table rows, where route data actually lives, are still scanned in full.

**One real defect the corpus was hiding, now reportable.** `references/code-formats.md` mandates
`BL###_NameSlug`, but `BL_H2_RE` is deliberately permissive so a malformed heading is still parsed
rather than vanishing — with the result that nothing ever checked the format. 72 of 103 headings in
the reported corpus used `## BL002: Name`. Any consumer keying on `BL###_` silently saw 31 of 103;
any consumer using a trailing `\b` saw 72, because `_` is a word character. New
`BehaviorLogic.code_format` reports the deviation as a **warning** — it loses no content, but it must
not stay invisible — and the malformed section still receives its other checks.

**Net effect on the reported corpus:** `PASS` (0 criticals, 0 warnings recorded) → `WARN` (0
criticals, 87 warnings: 72 heading-format, 12 missing File Schema, 3 REG gaps). The 45 criticals that
the allowlist fix newly exposed were **all false positives** from the three could-not-pass gates —
fixing only the allowlist would have converted a silent pass into a spurious halt.

**Tests:** suite 3586 → 3616 (+30, all passing). Every fix carries a paired test that the old code
failed, in both directions: the gate no longer fires on the correct document, **and** it still fires
on a genuinely broken one. Several pre-existing tests had encoded the bugs — the promotion-gate test
used the wrong summary path, and `test_summary_lib.py` only ever exercised the three allowlisted
slots — which is why six holes survived this long.

## v27.4.0 — W5 feature clustering: criteria for the generator, and for the critical check that already asked

**v27.4.0 (major in kind, inside the unreleased v27 line):** `references/code-formats.md` gains
`### Feature Clustering Rule (authority)` — one block, seven bullets, no numeric threshold — and
three places now point at it by heading rather than restating it: both W5 clustering entry points
(the single-task branch and the shard branch's grouping-once step), W5.6 **check #8**, and
`build_session_context.py`'s always-read pointer, whose description said only "— code schemas" and
now names the rule so an agent reading the file for schemas is told a prose rule lives there too.

**Nothing was added and nothing was re-severitied.** No new script, test, check, wave, gate, schema
or template. Check #8 was already `critical` and asked exactly the right question — *"No F### should
aggregate unrelated concerns"* — with no definition of "unrelated" and no evidence to apply, which an
LLM reviewer meets by passing everything. It keeps its severity; it gains criteria.

**One behavioural fix ships with it, and it is the reason the criteria are not advisory by accident.**
W5.6's frontmatter contract said `false = halt` but never that a critical *requires* `passed: false`,
and the orchestrator throws only on `passed === false` — it reads `issues` merely to interpolate into
the error message. A reviewer finding a check-#8 critical could therefore write `issues: 1,
passed: true` and proceed to FS.1, with the console printing `[INFO] W5.6 passed (issues: 1,
warnings: 0)` — a log line asserting a pass while reporting a critical. W4.6, the sibling gate one
wave earlier, already carries the missing instruction (*"Halt threshold: passed=false only when
issues > 0"*); W5.6 never got it. That line is now copied across, naming which checks count as
criticals. It is not a new check or gate — it makes the existing critical gate's output contract
consistent with its own sibling — but it does change **when W5.6 halts**, so it is named here rather
than folded into the documentation change.

**Why this is major in kind, and why it still stays inside v27.** A `feature-list.md` that passes
check #8 today can fail it tomorrow — this skill's own major trigger (*"a previously-passing document
can now fail"*). Severity is not the trigger; **outcome** is. But `origin/main` and `origin/dev` are
both still at `26.4.0` while this line runs many commits ahead of them and unmerged (an exact
count is deliberately not stated — the commit that writes it changes it), so **no released build
contains v27 at all** and no installed base can regress. This is the same reasoning v27.3.0 applied
when it added two brand-new criticals (`cap.code_unclaimed`, `cap.double_claimed`) and explicitly
declined to create v28; a change strictly smaller than that one does not get a new major line either.
Re-open as `28.0.0` if the v27 line is released before this ships, at which point the trigger bites a
real installed base.

**Measured basis, with everything that qualifies it.** The judgment form of these criteria scored
**86% precision / 60% recall** over three independent runs, against **30% recall** for the prior
rubric. **n=18**, and the sample is **deliberately enriched** across suspicion bands — its SPLIT rate
is the sample's, never the corpus's. **Fleiss kappa 0.481** (moderate); these labels are not a gold
standard. The rules were searched against those same labels, so every figure is an **upper bound**,
and two of the eighteen (`F020`, `F046`) stand on a 2–1 majority that was never human-adjudicated.
**The misfiled-US bullet is UNMEASURED** — it was the trial's recommendation for its one false
positive and was never itself run; it ships marked UNMEASURED in the authority block and is the first
candidate for removal if a future measurement implicates it.

**No claim is made that W5's output improved.** What is proven is that a critical check now has the
rule it never had. Whether an instruction line changes a one-pass global clustering task over roughly
11,400 lines of input drafts is unmeasured: the A/B that would settle it was designed, found
unrunnable, and **deferred with its harness defect recorded** (it staged inputs outside the repo while
telling one arm to read an unstaged repo file, manufacturing a null result of its own making). Also
recorded as a known limitation: W5/W5.6 skip when `w5_reran === false`, so a `feature-list.md`
generated before this rule carries forward through incremental runs unchecked, with no freshness stamp.

**Retired in the same line:** 710 lines of the v3 over-scope design — untracked until now, so this
removes nothing from any shipped build; the code lands in history and leaves the working tree — (a deterministic screen, its lib,
its tests, and an LLM judge contract) are deleted. The judge scored 100% precision / 30% recall on 3
fires — Wilson 95% CI [43.8%, 100%] — and its rubric was authored from the labelers' own rationales
for the same 18 features it was then scored on. `docs/decisions/ADR-0005.md` records all four designs
attempted against this gap, the three causes of death, and five findings that outlive them — chief
among them that **capability count is not the over-scope signal** (`F039` at CAP=7 was unanimous KEEP;
`F063` at CAP=8 unanimous SPLIT) and that every CAP-bearing rule, including the best-scoring one at
77%/100%, is **unusable at W5/W5.6** because § 2 does not exist until FS.1.

## v27.3.0 — § 2 becomes the enforced capability partition

**Entry reconstructed 2026-08-20.** `SKILL.md` was bumped to `27.3.0` when this work sealed, but no
`CHANGELOG.md` entry was ever written — the record lived only in the repo-level
`docs/project-changelog.md`. The gap is closed here rather than papered over; the content below is
sourced from that entry, not re-derived.

**v27.3.0 (major in kind, inside the unreleased v27 line):** `functional-spec.md § 2 Functional
Capabilities` moves from advisory prose to a deterministically-enforced exhaustive partition — every
declared US/FR/BR/SCR code in a feature must be claimed by exactly one CAP row — closing the gap that
let `F001_Auth`, an entire capability domain, pass validation as a single valid feature. The § 2 schema
widens 5→7 columns (`User Stories`, `Business Rules`), and two new criticals enforce the partition:
`cap.code_unclaimed` (a declared code absent from every CAP row) and `cap.double_claimed` (a code
claimed by more than one row). `cap.claims_unfilled` (warning) covers the post-`cap-map`/pre-fill
window. `cap.analysis_required` (critical) and `cap.review_advised` (warning) trigger review on a
single-CAP feature — per sealed decision D-7 the count never forces a split, it forces a written,
verifiable rationale. `cap.promote_candidate` (warning) is advisory only: it writes no file, renames
nothing, and states that promotion is a human decision with no automated path today. A 7th `--migrate`
step, `cap-map` (ordered `feature-sot → cap-map → mirror-skew`), widens a pre-schema-change corpus and
keeps `mirror-skew` REFUSED until claim cells carry codes; it ships a real `--rollback cap-map`.

**Why it stayed inside v27:** two new criticals can certainly fail a previously-passing document, but
`origin/main` and `origin/dev` were both at `26.4.0` with HEAD hundreds of commits ahead and unmerged,
so widening the schema was additive against every installed base (D-5, verified). No v28 was created.

## v27.2.0 — `--migrate`: finish what a version upgrade leaves behind

**v27.1.0 (minor, not breaking):** `migrate_feature_audience_split.py` never shipped in a
released build before this version — v27.0.0 introduced it but no real corpus could complete a
migration (see `references/migration-audience-split.md` § Provenance and the legacy-marker path
and ADR-0004's amendment). So the JSON run-sentinel format, the new exit code 4
(FAILED==0 but INERT>0 — nothing sealed), and the legacy-marker provenance path change nothing
that a released build already relied on. The `func.dev_token` inline-code exemption and the
source-citation recognizer's wider acceptance are both **relaxations** — a relaxation cannot
fail a document that previously passed, so neither is breaking. Per this skill's own version
policy (major = an artifact renamed/removed or a previously-passing document can now fail;
minor = additive or relaxing capability; patch = no behavior change), this qualifies as minor.
Re-open as a major bump only if a previously-valid document is found to newly fail under the
relaxed rules.

**v27.2.0 (minor, not breaking):** adds `--migrate`, one flag over an ordered step registry
(`audience-split` → `a3-b4` → `a3-screens` → `mirror-skew`) that finishes what a version
upgrade leaves behind on an EXISTING corpus — the A3/B4 deterministic scaffold + researcher
fill, the retained-satellite `[ACTION REQUIRED]` affordance, and the mirror-tree prune +
translate handoff. Every change is additive or a same-severity relaxation: the A3/B4 scaffold
moves a spec from `*.pre_migration` WARN to `*.unmapped` WARN — same severity, still exit 0 —
so no previously-passing document can newly fail; that bump-to-minor holds only because the
scaffold is proven to never write an empty section body (`references/migration-audience-split.md`).
One backward-compatible change is still worth naming: `[SUMMARY]` gains a `retained=N` term and
the run-sentinel JSON gains a `retained` key (`Tally.from_dict` reads it via `data.get(k, 0)`, so
an old sentinel with no `retained` key loads as `0`, never a crash) — a consumer parsing the
summary line by field position, not by name, would notice the new trailing term. Re-open as a
major bump only if a future scaffold shape is found that can leave an empty section body.

**v27.2.0 amended in place (2026-08-18, `plans/260818-1332-rebuild-spec-human-readable-sot`) —
human-readable SOT reshape, version NOT bumped:** client feedback said the v27.0.0 audience
split still read as a code reverse-engineering document, not a Source of Truth a PO/BA/QA/
Designer could use. Fix: the screen spec becomes a 10-numbered-§ body (`## 1. Overview` … `##
10. Responsive Behavior`) + `## Technical Appendix` (6 H2-sibling implementation-detail
sections); `functional-spec.md` renumbers to 13 §§ (net-new: `## 2. Functional Capabilities`,
`## 11. Risks & Known Issues`, `## 12. Dependencies`); `technical-spec.md` retaxonomizes to 5
numbered buckets (`## 1. Technical Overview` … `## 5. Verification & Technical Notes`, with
`## Source Walkthrough` / `## DB Impact per Event` staying unnumbered H2 siblings after § 5).
A new status marker, `[EXPECTED]` (desired/agreed behavior not yet implemented or confirmed),
joins the three existing markers verbatim. Two `--migrate` steps carry both existing corpus
generations forward losing nothing: `screen-sot` (after `a3-screens`) and `feature-sot` (after
`screen-sot`, additive next to `audience-split` — the old v26→v27 composer family is KEPT, not
retired, since it remains the G1→G2 hop `screen-sot`/`feature-sot` compose G2→SOT from).
`STEP_ORDER` is now 6 steps: `audience-split → a3-b4 → a3-screens → screen-sot → feature-sot →
mirror-skew` — `mirror-skew`'s prerequisite moved from `a3-screens` to `feature-sot` so it only
ever prunes/translates a fully-SOT-shaped tree. Each breaking shape ships a WARN-first
`*_pre_sot` rule_id that mutes the other new-shape rules for its own file during the migration
window: `screen.sot_pre_sot` (reviewer-checked, `verification-checklist-screen-spec.md`),
`func.sections_pre_sot`, and `FeatureSpec.tech_sections_pre_sot` (both `validate_feature_spec.py`).
Promotion of the three to `critical` is a recorded follow-up, not part of this change.

**Version stays `27.2.0` — not a new heading, not a major bump.** This skill's own version
policy (stated at the top of this section) would ordinarily call a screen/functional/technical
reshape of this size a major bump (an artifact's required shape changed; a previously-passing
document — the old v27.0.0 shape — can now fail once past the WARN window). It is not, because
**v27.0.0/v27.1.0/v27.2.0 never shipped in a released build** — the branch this reshape landed
on (`feat/rebuild-spec-audience-split-v27`) is the same one still carrying the original
audience-split work, so there is no released consumer whose already-passing document this could
break. Bumping the version or adding a new heading here would document a release that never
happened; the correct record is amending the entries already describing the unreleased version
in place. Re-open as an actual major bump only once v27 ships and a later change breaks a
document that shipped version already accepted.

**Real defects this reshape work found and fixed, recorded honestly:**
- `reshape_data_inventory` (the `Field`→`Display Label` column reshape Mode C runs) was not
  fence-aware and rebuilt its output from ONLY the lines it recognized as table rows — silently
  dropping any prefix, interleaved, or trailing non-table content. This was **active data loss
  in a migration already run over the real corpus**, not a hypothetical; fixed by routing the
  scan through the shared fence-aware primitive and rebuilding line-by-line over the original
  sequence, with inverted characterization tests added as the regression net (there had been
  zero direct tests on this function before).
- The A1 confidence-report refresh fired for a technical-spec step that was merely *requested*
  on the command line but *refused* at runtime on a pending prerequisite — a wasted, cosmetically
  confusing rewrite over content that had not changed. Fixed: the refresh now gates on the
  registry's `ran` set, never on the requested step-name set (dry-run preview is unaffected — it
  has nothing to gate on `ran` yet). See `references/pipeline-migrate.md`.
- Two greenfield authoring format-lints in `references/spec-stage-procedure.md` had been
  silently failing since the renumber landed: a literal `grep '^## 5\. Screens$'` (the template
  now emits `## 6. Screens`) and a literal `grep '^## Artifact References$'` (now `### 5.5
  Artifact References`) — both printed FAIL on every correctly-shaped draft. Fixed to match the
  headings number-agnostically, the same shape `_nav_table_parse_lib.py` and
  `validate_feature_screen_link.py` already used (which is exactly why those two survived the
  renumber untouched while this lint did not).

**Deferred follow-ups, recorded so they are not lost:** promoting `screen.sot_pre_sot`,
`func.sections_pre_sot`, and `FeatureSpec.tech_sections_pre_sot` from `warning` to `critical`
after a release window; the researcher fill pass over the `screen-sot`/`feature-sot` scaffolded
cells (capability regrouping, navigation destinations, system-design cross-reference anchors —
mechanically scaffolded, an LLM's judgment call to complete); regenerating the vi/jp mirrors
from the reshaped primary tree (the existing mirrors still reflect the pre-reshape shape until
`--lang` re-syncs them).

_Moved here from SKILL.md: the skill file points readers at this CHANGELOG for version history, and it was over the 500-line gate `tests/validate-skills.py` enforces in CI. The reasoning is unchanged — only its home._

<!-- layout-exempt: rebuild-spec CHANGELOG — historical version notes; every docs/system|features|generated|flows path here is this skill's own output target, not a consumer assumption -->

# tkm:rebuild-spec — Changelog

Version history for the `rebuild-spec` skill. Current behavior is documented in `SKILL.md`;
this file holds the migration notes and breaking-change rationale for past versions. The most
recent sessions are also captured in `docs/journals/`.

---

## v27.0.0 — Feature-spec audience split: functional-spec (BA/QA) + technical-spec (Dev/QA/SA)

**Major (BREAKING)** — `docs/features/F###/` goes from 4 files to **2**: `functional-spec.md`
(BA/QA — plain-language, 10 numbered H2 sections, every FR/BR/SM/DEC code stated once as a
≤2-line sentence) and a reshaped `technical-spec.md` (Dev/QA/SA — the same codes implemented
once: endpoints, `Source:` citations, pseudocode, state machines). `business-context.md`,
`screens.md`, and `edge-cases.md` are gone, folded into `functional-spec.md`;
`docs/system/business-rules.md` is gone, folded into `docs/generated/behavior-logic.md`. The
screen-spec is reordered BA-first with a dev appendix. See ADR-0004 for the full rationale,
including why the prior 4-file split (commit `ce4c6db6`) failed and what it cost to reverse.

### Added
- **`functional-spec-template.md`** — the BA/QA half of the pair. 10 H2 sections: Overview,
  Open Decisions, Requirements, Business Rules, Screens, User Stories, Scenarios, Edge Cases,
  Edge Behaviours to Verify, Configuration. Forbidden-outside-fences contract (class names,
  `file:line`, HTTP verbs, pseudocode, secret-shaped values); FR/BR/SM/DEC/SCR/US codes are
  expected here (inverted from the old `business-context.md` rule, which forbade them).
- **`migrate_feature_audience_split.py`** + 12 `_audience_split_*_lib.py` modules — the v26→v27
  migration (see Migration below).
- **`references/migration-audience-split.md`** — operational reference for the migration and its
  LLM compaction pass.
- **`claude/skills/rebuild-spec/docs/decisions/ADR-0004.md`** — the genealogy, the migration-
  safety deviation, and the priced regenerate-vs-migrate trade-off.
- Guard test `test_spec_constants_single_source.py` (DRY prep — `SATELLITE_FEATURE_FILES` and
  the 4 heading regexes now have one declaration site in `_spec_block_lib.py`).
- Regression tests for a false-positive-critical regex bug in `validate_feature_spec.py:492`
  (`\bSCR\d{3}\b` never matched the documented `SCR001_Login` slug form — fixed to `(?!\d)`).

### Changed
- **`technical-spec-template.md`** rewritten: the `**Rule:**` and `**user_visible_outcome:**`
  fields are removed — that plain-language content now lives once in `functional-spec.md` § 4;
  this file keeps only what a developer needs to implement or verify a rule (Linked FR, Source,
  Applies to, pseudocode). Cross-Cutting Logic (CCL) ordering is unchanged.
- **Block heading form changed:** `### BR-001_NameSlug` → `### <plain sentence> (BR-001)` (and
  `#### … (DEC-001)`). `LEGACY_BLOCK_HEADING_RE` rejects the old form. Translation Rule 1a: a
  line's trailing `(CODE-###)` tag plus its parentheses is skeleton (byte-identical across
  languages); the sentence prefix is prose (translated).
- **Screen-spec reordered BA-first** with a dev appendix; `## Screen Layout` wrapper removed
  (`### Layout Sketch` moves into the BA body, `### Layout Regions` into the dev appendix);
  `Field` column replaced by `Display Label` in `## Data Inventory`.
- **`_check_functional_spec`** replaces 3 retired checkers in `validate_feature_spec.py` (old 7
  rule_ids ⊆ new 11, plus 2 documented-dropped); `scaffold_spec.py` renders 2 files instead of 4.
- **A1 confidence-report basis:** `functional-spec.md` is excluded from the citation-coverage
  denominator by design — it is prose-driven, not citation-driven; `technical-spec.md` remains
  fully in scope. Guarded by a prose-parsing test
  (`test_confidence_report_functional_spec_exclusion.py`).
- **Screen-spec checklist 4→2 rule merge:** rules 9/10/30/31 merge into
  `screen.layout_sketch_missing` + `screen.layout_regions_missing` (both `critical`).
- **`doc-writer.md`** gains per-**section** (not per-file) guardrails for `functional-spec.md` —
  default-deny; § 1 Overview and § 7 Scenarios are human-editable, the other 8 sections are
  machine-owned. See `## Functional-Spec Section Guardrails`.
- **`audit-doc-parity`** gains a `functional-spec` doc-unit type; `audit-synthesis-judgment`'s
  behavior-logic locator points at `behavior-logic.md`; `migrate-aidd` mirrored to the 2-file set.
- Fixed two silent-pass regressions (`_flow_sm_lib.py`, `validate_test_cases.py`) that had
  re-typed a retired anchored pattern instead of importing it from the single-source constant;
  Phase 00's guard test widened to catch that whole class.
- Fixed a stale cross-reference: `technical-spec-template.md`'s behavior-logic link
  (`docs/system/` → `docs/generated/`) and `screen-spec-template.md`'s screens reference
  (`screens.md` → `functional-spec.md § 5`).

### Removed
- `docs/features/*/business-context.md`, `screens.md`, `edge-cases.md` — folded into
  `functional-spec.md`.
- `docs/system/business-rules.md` — folded into `docs/generated/behavior-logic.md`.
- Templates: `business-context-template.md`, `screens-template.md`, `edge-cases-template.md`,
  `business-rules-template.md` — recorded in `claude/metadata.json` → `deletions` (4 entries).

### Migration
Run `migrate_feature_audience_split.py --docs-root docs/` once per repo to upgrade from the v26
layout. It runs all three modes in one invocation:

- **Mode A** (per feature) — merges `business-context.md` + `screens.md` + `edge-cases.md` +
  `technical-spec.md` into `functional-spec.md` + a reshaped `technical-spec.md`. Deterministic
  content move plus an optional LLM prose-compaction pass, gated by invariants I1–I6 (staging,
  sentinel-as-sole-state-source, atomic swap with a retained pre-swap backup, fail-closed
  hand-edit detection, single run-wide lock, refuse-on-unrecognized-shape).
- **Mode B** (once, project-level) — folds `docs/system/business-rules.md` into
  `docs/generated/behavior-logic.md`.
- **Mode C** (per screen) — reorders `docs/screens/{SCR###}/spec.md` to the BA-first order; pure
  reordering, no LLM pass.

Flags: `--dry-run` (previews Mode A only — Mode B/C previews are not yet included, a documented
limitation, not a silent gap), `--reviewed MANIFEST` (sample-size-gated: a manifest naming fewer
than 10%/minimum 3 of this run's eligible features is treated as absent for the whole run — WARN,
delete skipped everywhere), `--rollback` (undoes partial, sentinel-absent Mode A migrations only —
Modes B/C have no dedicated rollback path; a partial run leaves its pre-swap backup under
`docs/.migrate-v27/` for manual recovery). This script is deliberately unlike the other five
`migrate-*.py` scripts (staging + backup + dry-run, where they rely on in-place idempotency alone)
— see ADR-0004 for why. Customer repos that already ran a prior `rebuild-spec` migration roll back
through their own VCS; there is no kit-level uninstall for this migration.

### Notes
- Effort re-baselined during planning (36h → 68.5h) after a red-team pass surfaced 20 findings
  (17 accepted, 1 rejected, 2 escalated and reaffirmed by the user) — see
  `plans/260814-1106-rebuild-spec-audience-split/red-team-review.md`.
- Density (avg lines/rule) is measured in **lines**, with the evasion-risk (padding a "line" to
  dodge the budget) accepted on record rather than mechanically closed.
- Mode A assumes the source v26 doc is internally self-consistent (every referenced code has a
  declaring row somewhere) and emits the bare `SCR###` code (no slug suffix) in its composed
  Screens table — `validate_feature_screen_link.py`'s prefix-only match still resolves it.

## v26.4.0 — Tracks B/C/D: CICS BMS + COBOL CRUD/datasets + generic ui-sniff fallback (additive)

**Minor (additive)** — completes the COBOL initiative started at `v26.3.0` (Track A): CICS BMS
screen extraction, COBOL file-I/O + EXEC SQL CRUD extraction, and a generic content-sniff
fallback for ANY unrecognized stack (not COBOL-specific). No existing profile's behavior
changes; no migration script; no `metadata.json` deletions (nothing renamed/removed).

### Added — Track B: CICS BMS screens
- `_cobol_bms_lib.py` + `_cobol_bms_grammar_lib.py` — fixed-column HLASM/BMS macro tokenizer
  (DFHMSD/DFHMDI/DFHMDF), MAPSET→source-file index (keyed by the `DFHMSD` label, never by
  filename), `EXEC CICS SEND/RECEIVE MAP` reachability join (across both BMS-macro-shaped
  files and ordinary COBOL calling programs that only reference a map), conditional-assembly
  guard (`AIF`/`AGO` spans exclude their fields from emission entirely rather than fabricating
  merged geometry), symbolic-copybook-only fallback, `mapset_undefined` WARN. Flows through
  the SAME `cobol-screen` router and screen validators Track A shipped — mixed
  SCREEN-SECTION+BMS repos need no `--profile` pin.

### Added — Track C: COBOL CRUD / datasets
- `extract_cobol_data.py` + `_cobol_data_lib.py`/`_cobol_verb_lib.py`/`_cobol_sql_lib.py` —
  file-I/O verb → CRUD classification (WRITE→C, READ→R, REWRITE→U, DELETE→D) with
  OPEN-mode/ACCESS-mode/prior-READ state tracking (illegal-for-mode → WARN, never a false
  classification); `EXEC SQL...END-EXEC` pass (dialect-agnostic DB2/Pro*COBOL shape, cursor
  DECLARE/OPEN/FETCH/CLOSE, dynamic SQL → `[UNVERIFIED]`, never a fabricated table).
- `db_objects.kind` gains `"dataset"` (flat-file/VSAM COBOL data store) alongside the
  existing `"table"` — both `VALID_KINDS` and `SECTION_KIND_MAP` extended (the latter is the
  actual gate; `## Datasets` rows would otherwise be silently dropped) + a `## Datasets`
  section added to the db-object-catalog template.
- `cobol.json`: `crud-matrix`/`db-objects` flipped `skip`→`produce`, `extract_cobol_data`
  added to `extractors` — a real COBOL run now produces cited CRUD/db-objects artifacts.

### Added — Track D: generic content-sniff fallback (any unrecognized stack)
- `_content_sniff_lib.py`/`_content_sniff_signals_lib.py` — stdlib-only UI-evidence scan for
  a repo NO stack-profile recognizes: 9 signal families (C/Python/Perl/Java/VB6/TUI/shell/web
  CGI/COBOL-ish), a menu-loop structural detector, 3-tier confidence (0 silent / 1
  metadata-only / 2 cited-and-gated), false-positive guards, a generic-secret scrub
  (independent of `_sql_parse_lib`'s SQL-shaped scrub — this domain's secrets are CLI flags
  and env-var fallbacks, not connection strings).
- `detect_stack_profile.py`: new advisory `ui_sniff` key (root-level + per-component, only
  computed on a no-match — zero cost on any recognized stack); `SCHEMA_VERSION` → `22.1.0`.
- Preflight step 2 (SKILL.md): a Tier-2 verdict surfaces a 4th, cited, delimited option
  alongside the existing 3 — on ACCEPT, `_ui_sniff_accept_lib.py` builds a sparse
  `_digest_extract_ui_sniff.json` (every entry `unverified: true`) and a session-scoped
  profile override (`screen_source: "ui-sniff"`, never written to a kit profile file) that
  the EXISTING screen-production pipeline consumes unchanged. Non-interactive mode logs
  `[WARN] ui_sniff_tier2` and never prompts. Tier 0/1 → unchanged 3-option flow.
- **Accepted risk:** the content-sniff signal library is research-backed but not yet
  validated against a second real "unclear stack" corpus (none was available this session) —
  ships speculative v1, retune after real usage surfaces false positives/negatives.

### Notes
- Two-release COBOL rollout: `v26.3.0` shipped Track A (SCREEN SECTION) standalone so the
  user's confirmed priority didn't wait on the more speculative Tracks B/C/D; this release
  completes the set.
- Real anonymized fixtures for Tracks A/B (`tests/fixtures/cobol_real_sample/`,
  `tests/fixtures/cobol_screen_section/`, `tests/fixtures/cobol_mixed/`) were sourced from
  the user's actual AcuCOBOL/Micro Focus target repo per this initiative's validated
  fixture-sourcing decision; Track B (CICS BMS) and Track D fixtures are synthesized (the
  confirmed real target uses SCREEN SECTION, not mainframe CICS, and no second
  unrecognized-stack repo was available).

---

## v26.3.0 — Track A: COBOL SCREEN SECTION screen extraction (additive, standalone release)

**Minor (additive)** — brand-new `cobol` stack-profile + SCREEN SECTION screen extraction,
released as its own unit ahead of the full COBOL initiative's remaining tracks (CICS BMS,
CRUD/data extraction, generic-content-sniff fallback — those land together in a later MINOR).
No existing profile's behavior changes; no migration script. (Version note: `v26.2.0` is
already claimed by an unmerged `--package`/diagram-export branch in this repo's history — this
release takes the next free MINOR, `v26.3.0`, to avoid a future collision when that branch
lands.)

### Added
- New `cobol` stack-profile (`references/stack-profiles/cobol.json`) — detects `*.cbl`/`*.cob`/
  `*.cpy`/`*.bms`, `screen_source: "cobol-screen"` (screens-only at this release: crud-matrix/
  db-objects stay `skip` until the CRUD extractor ships).
- `extract_cobol_screen.py` — the COBOL screen router: macro-shaped anchored-regex dispatch
  (BMS-macro-shaped or `EXEC CICS SEND/RECEIVE MAP`-referencing files vs. `SCREEN SECTION`
  files, both-match merge), accumulate-then-`finalize()` contract, per-file byte cap,
  post-decode EBCDIC/binary sanity guard, exit-0-always.
- `_cobol_screen_section_lib.py` — SCREEN SECTION parser: `01`-level record → screen,
  ACCEPT/DISPLAY reachability + entry citation, PERFORM-chain flow edges (Delphi form-nav
  shape), `COPY` resolution against a bounded, realpath-containment-checked in-repo index
  (unresolved/escaped → `unverified` + cited, never a crash).
- `screen-list`/`screen-flow` validators extended (additive) to accept `screen-section` /
  `cics-bms` / `ui-sniff` screen kinds and COBOL source citation extensions.

### Notes
- The router's CICS BMS extraction path (`_cobol_bms_lib.py`) and the CRUD/data extractor
  already exist in this tree (built for engineering-parallelism reasons) but are not yet wired
  into `cobol.json`'s `produce`-declared artifacts — no artifact is declared `produce` whose
  extractor isn't live at this release. They ship in the next MINOR alongside the generic
  content-sniff fallback.
- `_stack_profile_lib.SCHEMA_VERSION` bumped to `22.1.0` (additive `ui_sniff` detection key,
  unrelated to this Track-A release — landed in the same working session).

---

## v26.1.1 — PR #176 review-fix cluster (patch)

**Patch (fix-only)** — closes all accepted findings from the max-level review of the
v25.2.0→v26.1.0 wave (4 Critical, 8 Important, 7 Minor). No template or schema change; no
migration; normal `tkm init` upgrade suffices.

### Fixed — markdown scanning (C1, I1, I3 + minors)
- New shared `scripts/_md_scan_lib.py` (fence-aware iteration for ``` and ~~~, HTML-comment
  strip, escaped-pipe table-row split) — single primitive for the recurring fence-blindness
  bug class.
- `validate_reading_guide_db_impact.py`: section body no longer truncated by `#`-lines inside
  code fences (an unfilled A3/B4 scaffold hidden behind a fence now WARNs instead of passing);
  B4 table extraction fence-masked; `\|` in cells no longer shifts columns; tolerant
  `data_rows()` used for separator-less tables.
- `validate_job_list.py` / `validate_test_cases.py`: fenced example headings/rows and
  HTML-commented template appendices no longer parse as live content.
- `derive_confidence_report.py`: `~~~` fences supported; `<!-- disclaimer:start/end -->`
  boilerplate no longer inflates the Claims↔Evidence table.
- `validate_design_intent_density.py`: `{...}` scaffold placeholders stripped before density
  checks (parity with derive_confidence_report).

### Fixed — credential gate (C4 + minor)
- `_credential_scrub_lib.py` split into recall-focused scrub patterns (adds `auth` vocab —
  `REDIS_AUTH=…` now caught; segment-boundary key matching — `BYPASS_HEALTHCHECK` no longer
  redacted) and precision-focused gate patterns (`assert_no_secrets` flags only
  assignment-shaped literal leaks; Bearer-token / service-account prose no longer fails the
  jobs promotion gate). Quoted `Environment="K=v"` redaction keeps the closing quote.

### Fixed — fan-out integrity (C2, I2, I7)
- `pipeline-jobs.md` J.1-merge reconciles fragment count against `_slice-plan.json` and HALTs
  (no marker, no cleanup) on a partial fragment set; `validate_job_list.py` adds reverse
  `JobList.bl_uncovered` WARN (qualifying BL### without a JOB###) and `JobList.index_drift`
  WARN (Job Index ↔ section parity).
- `pipeline-test-cases.md` TC.2 reconciles per-feature `.test-cases-completed` sentinels and
  the completion handoff reports the actual promoted count from the validation summary.

### Fixed — promotion gates & contracts (C3, I4, I5, I8)
- `pipeline-design-intent.md` D.5 re-reads the validator summary and review report from disk,
  so a fresh `--confirm-promote` invocation gates correctly (mirrors J.5/TC.5).
- Jobs preflight ABORT message names `behavior-logic.md` (was `entities.md`).
- Removed the false "dedup already checked [deterministic-pass]" claim (JOB-S4 semantic review
  remains authoritative for dedup).
- Design-intent contract citations no longer point at an ephemeral `plans/` research file.

### Fixed — citation regexes (I6 + minors)
- `validate_design_intent_density.py` accepts Delphi/Oracle citations
  (`pas|dpr|dfm|sql|pks|pkb|pls`); `validate_test_cases.py` requires a path shape for
  `file:line` citations (bare `Note:1` no longer counts); multi-token `**BL Ref**` values are
  all validated; `migrate-reading-guide-db-impact.py` reports unreadable specs as their own
  tally category (exit-0 contract unchanged).

---

## v26.1.0 — Wave 3: A2 jobs pass + B6 test-cases pass + B5 design-intent pass (additive)

**Additive (minor)** — three new opt-in standalone passes land strictly sequentially
(file-ownership collision on shared files forbids parallel execution) but ship together as
ONE consumer-facing release: one `tkm init` re-run covers all three, not three separate ones.
This entry accumulates sub-entries as each phase lands; do not treat a partial sub-entry list
as the final v26.1.0 shape until all three are present.

### Additive — A2 `--jobs` standalone pass (sub-entry 1 of 3)

- **New standalone pass `--jobs`** (J.1–J.5): scans `docs/generated/behavior-logic.md` for
  BL### entries typed `scheduled-job`/`queue-worker`/`custom-command` and expands each into a
  per-job detail section — inventory table + per-job `## Purpose` / `## Schedule / Trigger` /
  `## Data Touched` / `## Failure / Retry Behavior` — all in ONE artifact,
  `docs/generated/job-list.md`. This is a re-projection of the existing Wave-0 BL inventory, NOT
  a new detection surface (same relationship `--screen-specs` has to `screen-list.md`).
- **No `docs/jobs/` namespace** (reversed from an earlier design during red-team review): a
  dedicated namespace would have added 4 wiring touches (mapping row, `MOVED_LAYERS`,
  `check_layout_paths.py`, layout-exempt audit) for a low-volume artifact. `job-list.md` lives
  under the existing `docs/generated/` namespace, already translation-covered by
  `_translation_sync_lib.py::_DOC_AREAS`. `JOB###` codes are in-file row IDs, file-global (never
  reset per type or directory).
- **New systemd-timer detection row** in `references/bl-source-patterns.md` — the only genuinely
  new detection surface this pass adds (`.service`/`.timer` unit file pairs).
- **New deterministic validator `scripts/validate_job_list.py`**: JOB### regex + file-global
  uniqueness, `**Source**` citation presence, `**BL Ref**` presence/shape/resolution against
  `behavior-logic.md`, and a hard CRITICAL secrets gate wiring
  `_credential_scrub_lib.py::assert_no_secrets()` over the promoted output.
- **`_credential_scrub_lib.py` extended** to recognize `.service`/`.timer` unit files
  (`is_config_file()`) and to redact systemd `Environment=<KEY>=<value>` lines whose KEY carries
  abbreviated credential vocabulary (`pass`/`pwd`/`secret`/`token`/`key`/`credential`/`dsn`) not
  already caught by the pre-existing password/token/secret patterns.
- **Jobs researcher contract** (`references/jobs-researcher-contract.md`): READ-ONLY static
  scan — NEVER executes target build/task tooling (no `rake -T`/`crontab -l`/`systemctl`),
  mirroring `references/structural-extractor-contract.md`'s "never execute" rule. Job
  identifiers are slug-sanitized (mirrors the `FLOW###`/`F###` grammar).
- **New-pass registry wiring**: `scripts/_manifest_pass_status_lib.py::PASS_NAMES`/
  `PASS_PREREQS` gain `jobs` (needs only core — same prereq class as `screen-specs`);
  `references/pipeline.md::passPresent` gains a `jobs` key; `docs/generated/` was already
  covered by the translation discovery registry, so no change was needed there.
  `references/multi-component-runbook.md` Step 1b enumeration gains `jobs`.
- **Promotion wiring**: `promote_drafts.py` gains `--scope jobs` (mirrors `--scope glossary`
  exactly) + `_layout_lib.py::LAYERED_PATH_MAP["job-list.md"]`; `build_source_to_fcode.py` gains
  `--cursor jobs` (advances `last_jobs_run_sha`, refreshes `doc_shas["job-list.md"]`, additive —
  no state-schema migration).
- **Resume & Reconcile**: `jobs-complete.flag` added to the completion-sentinel enumeration;
  `expectedOutput` for this pass = `docs/generated/job-list.md`.
- Nav: `job-list.md` added to `_nav_strings.py::READING_ORDER` (layer 4, conditional) +
  matching `artifact_descriptions["job_list"]` in all three locale modules
  (`_nav_strings_en.py`/`_vi.py`/`_ja.py`) + `_nav_lib.py::_ARTIFACT_DESCRIPTIONS["job-list.md"]`.
- `claude/skills/_shared/docs-canonical-mapping.md` gains one row
  (`Job inventory | docs/generated/job-list.md`) + a proportionate bump-ledger entry (**minor**
  for rebuild-spec; no bump for other consumers — an additive new output path, no existing
  consumer's resolved path changes).
- **Bounded-wave fan-out (F10)**: J.1 counts qualifying BL### entries directly (no
  `estimate_artifact_loc.py` wiring needed for this cheap count over an already-small artifact);
  ≤5 entries dispatches a single researcher task (the common case); >5 dispatches a
  shell+fragment+merge fan-out wave-chained at `min(REBUILD_FS_BATCH_SIZE, REBUILD_MAX_PARALLEL)`
  (reuses the existing env, no new `REBUILD_JOBS_BATCH_SIZE`), each wave `addBlockedBy` ALL prior
  wave task-ids per the v25.1.2 hardening.
- **Not wired in v1** (documented, deliberate scope decision): `job-list.md` does NOT route
  through `estimate_artifact_loc.py`'s pre-gen LOC-estimate/shard-branch machinery (the fan-out
  above triggers on entry COUNT, not estimated LOC), and `JOB###` is NOT registered in
  `_id_schemes_lib.py`'s generic `ARTIFACT_OWNS`/renumber registry. `validate_job_list.py` does
  its own JOB### uniqueness check directly, the same way `validate_behavior_logic.py` and
  `validate_process_flow.py` self-check their own ID schemes. `references/artifact-sharding.md`
  carries a Descriptor Table row documenting this as a known v1 scope boundary, not an oversight.

### Additive — B6 `--test-cases` standalone pass (sub-entry 2 of 3)

- **New standalone pass `--test-cases`** (TC.1–TC.5): derives UT/IT/UAT test-case lists per
  feature by EXPANDING the already-cited `docs/features/{slug}/technical-spec.md` (BR-###/
  SM-###/DEC-###/DISC-### codes) and `edge-cases.md` (already test-case-shaped negative-path
  rows), with optional `screens.md`/`business-context.md` enrichment for UAT scenarios. Output:
  `docs/features/{slug}/test-cases.md`, a 5th per-feature file, **SIDECAR** — never joins the
  `FEATURE_FILES` 4-tuple or the promotion gate. Fan-out shape is identical to FS.1 (one
  researcher per F###, wave-chained ≤`min(REBUILD_FS_BATCH_SIZE, REBUILD_MAX_PARALLEL)` — reuses
  the existing env, no new `REBUILD_TESTCASES_BATCH_SIZE`).
- **TC### ID grammar**: `^TC\d{3}$`, resets per feature (same per-parent-reset exception class as
  `REG###` resetting per `SCR###`) — the ID Contiguity Gate exception sentence in
  `references/artifact-sharding.md` now names `TC###` alongside `REG###`.
- **Citation-source split (anti-hallucination)**: UT/IT rows must cite a `BR-###`/`SM-###`/
  `DEC-###`/`DISC-###` code, a `file:line`, or an `edge-cases.md` row; UAT rows must cite a
  `screens.md`/`business-context.md` section — never a bare code. A mismatch is a CRITICAL
  finding in `scripts/validate_test_cases.py`, not a style nit — it is the exact risk this split
  exists to guard against.
- **New deterministic validator `scripts/validate_test_cases.py`**: TC### regex + per-feature
  uniqueness, Type∈{UT,IT,UAT}, Traces-to presence + citation-source-family match, and a
  coverage-gap WARN cross-referencing every BR/SM/DEC/DISC code in `technical-spec.md` against
  the test cases that trace to it (a code may be deliberately excluded via a `[NO_TEST_CASE]`
  marker in `test-cases.md`'s `## Coverage Notes` section — WARN, non-halting; 100% coverage is
  not always achievable or desired).
- **New-pass registry wiring**: `scripts/_manifest_pass_status_lib.py::PASS_NAMES`/
  `PASS_PREREQS` gain `test-cases` (requires `feature-specs` — same DAG class as flows/glossary);
  `references/pipeline.md::passPresent` gains a `test-cases` key; `docs/features/*/*.md` was
  already covered by the translation discovery registry (`_translation_sync_lib.py::_DOC_AREAS`),
  so no code change was needed there. `references/multi-component-runbook.md` Step 1b
  enumeration gains `test-cases`.
- **Promotion wiring — verified, no new `--scope` literal needed**: `promote_drafts.py`'s
  `--scope features` walks the ENTIRE `artifacts/features/{fcode}/` source directory
  (`os.walk`) and copies whatever is present — directory-scoped, not a fixed filename list.
  Since TC.1 writes ONLY `test-cases.md` into that draft folder, an incremental `--scope
  features` promote copies it into `docs/features/{fcode}/` additively, alongside the
  pre-existing 4 files. `build_source_to_fcode.py` gains `--cursor test-cases` (advances
  `last_test_cases_run_sha`; no `doc_shas` entry — per-feature sidecar, not a single core
  artifact — falls into the same "preserve prior entirely" branch as flows/feature-specs).
- **Resume & Reconcile**: `test-cases-complete.flag` added to the completion-sentinel
  enumeration; `expectedOutput` for this pass = per-feature `docs/features/{slug}/test-cases.md`
  (mirrors FS.7's per-fcode reconcile shape, not J.5's single-file shape).
- Nav: `test-cases.md` added to `scripts/_nav_feature_lib.py::FEATURE_FILE_ORDER` (presence-pruned,
  listed last) + matching `file_purposes["test-cases.md"]` entry in all three locale modules
  (`_nav_strings_en.py`/`_vi.py`/`_ja.py`). No top-level `READING_ORDER` entry needed — it rides
  the existing `features/*/` glob (unlike `job-list.md`, which is a top-level single artifact).
- **Sidecar guardrail (F1/F15)**: `test-cases.md` is explicitly documented as NOT part of
  `_slug_lib.py::FEATURE_FILES`, `check_promotion_gate.py`, or `scaffold_spec.py`'s 4-file
  scaffold — a sidecar note was added to `references/feature-spec-researcher-contract.md`
  mirroring the A1 confidence-report companion precedent. Regression tests assert this boundary
  in both `test_check_promotion_gate.py` and `test_validate_test_cases.py`.
- `claude/skills/_shared/docs-canonical-mapping.md` gains one row
  (`Feature test-cases | docs/features/{slug}/test-cases.md`) + a surgical-edit-rule row +
  a proportionate bump-ledger entry (**minor** for rebuild-spec; no bump for other consumers —
  folded into the same v26.1.0 already recorded for the jobs sub-entry, no separate version
  number).
- **CSV export explicitly OUT OF SCOPE v1**: zero prior CSV precedent anywhere in this kit
  (only `.xlsx` via `--api-doc`); Markdown is the sole primary output.

### Additive — B5 `--design-intent` standalone pass, EXPERIMENTAL (sub-entry 3 of 3)

- **New standalone pass `--design-intent`** (D.1–D.5): infers cross-cutting "why the system was
  built this way" architectural rationale from ADRs (highest-trust, optional), `architecture.md`
  + `business-rules.md`, source-code patterns (`SOURCE CODE: AUTHORIZED`, like FL.1/GL.1), and
  optional `business-context.md` enrichment. Single-file synthesis, NO fan-out — mirrors the
  GL.1–GL.3 glossary shape (the simplest 3-wave precedent), not `--overview`'s cluster fan-out.
  Output: `docs/system/design-intent.md`.
- **EXPERIMENTAL — this is the highest-hallucination-risk pass in the kit ("why" is inherently
  more inferential than every other artifact's structural "what")**, so it ships with three
  deliberate defenses instead of default-promote:
  1. **(F11a) Disclaimer header** — every draft opens with an EXPERIMENTAL/`[INFERRED]`-heavy
     banner (`templates/design-intent-template.md`), wrapped in
     `<!-- disclaimer:start/end -->` markers the density validator relies on to skip it.
  2. **(F11b) Report-only first release — NO auto-promote path anywhere.** D.1–D.4 write and
     review the artifact ONLY inside `plans/<active-plan>/artifacts/design-intent.md`. Promotion
     to `docs/system/design-intent.md` happens ONLY via D.5, reachable exclusively through an
     interactive `AskUserQuestion` "yes" or the explicit `--design-intent --confirm-promote`
     flag. `promote_drafts.py`'s `design-intent` scope is deliberately excluded from `--scope
     all`/`core` — no other pass's promote step can accidentally publish it.
  3. **(F11c) NEW mode-agnostic density validator** `scripts/validate_design_intent_density.py`
     — flags asserted-as-fact, zero-citation paragraphs in ANY run mode. This is a genuinely NEW
     script, NOT a reuse of `re-output-contract.md`'s density check (that check is gated on
     `profile.re_contract`/RE-mode and would never fire for a normal `--design-intent` run — the
     original research suggestion to reuse it did not hold up under review).
- **Citation-or-`[INFERRED]` gate (load-bearing)**: every claim in the researcher contract
  (`references/design-intent-researcher-contract.md`) must cite an ADR, `business-rules.md`,
  `architecture.md`, or a `file:line`, OR be tagged `[INFERRED]` with a one-clause reason.
  Source order is ADR (quote directly, never override) → architecture.md/business-rules.md →
  source code → `business-context.md`. Degrades gracefully when ADRs are absent (the common
  case — most repos have none): leans on code-pattern inference, surfaces the resulting
  ADR-citation ratio in the handoff (e.g. "3/18 claims cite an ADR").
- **Non-duplication boundary (DRY, vs `business-rules.md`/`architecture.md`)**: design-intent
  holds ONLY cross-cutting architectural rationale; it may cite either existing artifact, never
  re-narrate their content. Documented as a Disambiguation note in
  `claude/skills/_shared/docs-canonical-mapping.md` — the same pattern the mapping file already
  uses for `docs/system/architecture.md` vs `docs/system-architecture.md`.
- **New-pass registry wiring**: `scripts/_manifest_pass_status_lib.py::PASS_NAMES`/
  `PASS_PREREQS` gain `design-intent` (needs only core — same prereq class as `jobs`/
  `screen-specs`, no feature-specs dependency); `references/pipeline.md::passPresent` gains a
  `design-intent` key; `docs/system/` was already covered by the translation discovery registry
  (`_translation_sync_lib.py::_DOC_AREAS` globs `system/*.md`), so no code change was needed
  there. `references/multi-component-runbook.md` Step 1b enumeration gains `design-intent`
  (per-component — each component gets its own draft + its own D.4 confirmation gate; see the
  aggregate-tier note below).
- **Promotion wiring**: `promote_drafts.py` gains `--scope design-intent` — structurally
  identical to `--scope glossary`/`--scope jobs` EXCEPT it is deliberately never included in
  `("all", ...)` (F11b) — plus `_layout_lib.py::LAYERED_PATH_MAP["design-intent.md"]`;
  `build_source_to_fcode.py` gains `--cursor design-intent` (advances
  `last_design_intent_run_sha`, refreshes `doc_shas["design-intent.md"]`, additive — no
  state-schema migration; only ever invoked at D.5, post-confirmation).
- **Resume & Reconcile**: `design-intent-complete.flag` added to the completion-sentinel
  enumeration; `expectedOutput` for this pass = the PLAN-DIR draft
  `plans/<active-plan>/artifacts/design-intent.md` (NOT `docs/system/design-intent.md`) — a
  never-promoted, report-only run is a complete, valid pass state. This is the whole point of
  F11b, not a gap.
- Nav: `design-intent.md` added to `_nav_strings.py::READING_ORDER` (layer 4, num 19,
  conditional — appended at the tail alongside `job-list.md` to avoid renumbering every
  downstream entry, mirroring the A2 precedent rather than design-intent's more natural layer-1
  placement) + matching `artifact_descriptions["design_intent"]` in all three locale modules
  (`_nav_strings_en.py`/`_vi.py`/`_ja.py`) + `_nav_lib.py::_ARTIFACT_DESCRIPTIONS["design-intent.md"]`.
  Layer-4 placement means it carries no `reading_why` clause (that block is layer-1-3 only by
  contract — enforced by `test_nav_reading_why.py`).
- `claude/skills/_shared/docs-canonical-mapping.md` gains one row
  (`Design intent (EXPERIMENTAL) | docs/system/design-intent.md`) + the Disambiguation note
  above + a proportionate bump-ledger entry (**minor** for rebuild-spec; no bump for other
  consumers — folded into the same v26.1.0 already recorded for the jobs/test-cases sub-entries,
  no separate version number).
- **Aggregate-tier design-intent = follow-up (Decision 4, scope boundary — NOT built in v1)**:
  a 7th aggregate artifact (system-researcher-authored, cross-component "why", alongside the
  existing `overview`/`component-catalog`/`architecture`/`glossary`/`cross-service-flows`/
  `data-ownership-map` six) is explicitly deferred. v1 is single-component/system-level only —
  each multi-component member gets its own per-component draft via Step 1b, never a
  cross-component synthesis. The 6-artifact aggregate contract itself is untouched.
- **Go/no-go graduation criteria = follow-up gate (F11d, quantified, NOT executed in v1)**: this
  pass graduates from EXPERIMENTAL to default-promote ONLY when, across **3 pilot repos of
  differing stacks**, ALL hold: (1) `[INFERRED]` ratio ≤25% of claims per repo; (2) zero
  fabricated citations — spot-checked via an `audit-doc-parity` run (or equivalent
  citation-existence check) on each pilot output; (3) a human reviewer confirms the artifact is
  useful, not generic boilerplate. Record pilot results before flipping any default — accepted
  trade-off: this pass may stay EXPERIMENTAL longer than a typical additive pass.
- **Multi-component `design-intent` per-component caveat**: `references/multi-component-runbook.md`
  Step 1b's `--batch --pass design-intent` driver step reuses the same per-component
  eligibility/DAG machinery as `jobs`/`test-cases`, but each component's own D.4/D.5 report-only
  → confirm-promote gate is independent — confirming promotion for one component's draft does
  NOT confirm any other component's.

## v26.0.0 — A3 Source Walkthrough + B4 DB Impact per Event (BREAKING)

**BREAKING** — two new REQUIRED sections change the shape of both spec templates, plus a new
dedicated validation gate. Same class as v24.0.0: the WARN-first degradation contract softens
the *rollout* for un-migrated repos, but the kit still calls this BREAKING because the template
shape changed and a new validator was wired into an existing gate (FS.2).

### Breaking — A3 Source Walkthrough + B4 DB Impact per Event

- **`templates/technical-spec-template.md`** gains two new top-level H2 sections, appended
  after `## Unresolved Questions`: `## Source Walkthrough` (A3 — ordered reading list, per-file
  "why start here," call-hierarchy diagram, and a pointer to the `## Source Code References`
  table, which is re-cast in place with a new **Order** column so there is one related-files
  table, never two) and `## DB Impact per Event` (B4 — one row per DB-writing event/endpoint:
  `Event/Endpoint | Table | Columns | Operation | Value Derivation | Source`, `Source` a
  `file:line` citation or `[INFERRED]`; `N/A — read-only feature, no DB writes.` when a feature
  performs zero writes). B4 is a top-level H2, not nested under `## Cross-Cutting Logic` —
  validator symmetry with A3, and keeps `_spec_constants.REQUIRED_CCL_H3` untouched (no reason
  to widen the BREAKING radius onto that exact-order check too).
- **`templates/screen-spec-template.md`** gains `## Source Walkthrough` (A3 only — B4 stays
  feature-spec-only; DB writes are out of ScreenSpec's UI-layer scope). `## Source References`
  is re-cast from a bullet list to a numbered list (the reading order) — same one-list DRY rule.
- **A3 renamed from "Code Reading Guide"** (an earlier working name) to **"Source Walkthrough"**
  to avoid colliding with the unrelated v24 nav "reading guide" feature (per-artifact
  `reading_why` clauses, `_nav_feature_lib.py`).
- **New validator `scripts/validate_reading_guide_db_impact.py`** (WARN-capable, NON-halting):
  covers BOTH families from one script. Degradation contract — absent section on an
  un-migrated doc → WARN `reading_guide.pre_migration` / `db_impact.pre_migration` (never
  breaks the build); present-but-empty or a non-table B4 body (and not `N/A`) → CRITICAL
  `*.malformed` (real drift); present-but-only-placeholder → WARN `*.unmapped`; a B4 row whose
  Source cell is blank (no citation, no `[INFERRED]`) → WARN `db_impact.uncited`. Deliberately
  NEVER added to `_spec_constants.REQUIRED_H2_TECH` — that exact-order check has no degradation
  window (Decision 2, harsher than v24.0.0's own precedent). A permanent regression test
  (`test_spec_constants.py::TestF8RegressionGuard`) asserts the two new headings are never added
  there. Wired into the FS.2 feature-specs gate (mirrors `validate_feature_screen_link.py`'s
  wiring shape exactly, including its scope limitation: a `--screen-specs`-only run that never
  runs `--feature-specs` does not exercise this gate).
- **New migration `scripts/migrate-reading-guide-db-impact.py`** (idempotent, non-destructive):
  unlike the v24 SCR###/Feature migration, A3/B4 content cannot be mechanically backfilled from
  existing doc text — it requires re-reading source, i.e. the researcher, not a script. This
  script only reports which specs still lack the sections (`[WARN] ... requires re-running
  researcher pass`); it never edits a file. Exit 0 always.
- **`scaffold_spec.py::_render_technical_spec` patched** to append the A3/B4 skeletons after
  its `REQUIRED_H2_TECH` render loop — the scaffolder renders from the constants list, not from
  the template files, so without this fix a fresh draft would permanently lack both sections.
  (No screen-spec equivalent exists to patch — `scaffold_spec.py` never renders
  `docs/screens/SCR###/spec.md`.)
- **`references/confidence-report-contract.md`** amended: A3's reading-list entries are
  navigational (file-existence pointers), not factual claims — they cite with `**File:**`, never
  `**Source:**`, so `derive_confidence_report.py`'s `CITATION_RE` (anchored on the literal
  `**Source:**` token) never counts them. No parser code change was needed; the fix lives
  entirely in the authoring contract. B4 rows, by contrast, ARE genuine claims — a B4
  `[INFERRED]` tag correctly counts as an uncited claim, unchanged.
- **Translation contract:** no new skeleton rule needed. B4's table shape is fully covered by
  the existing generic Table Cell Rule (header row verbatim; code/enum/path cells verbatim;
  narrative cells translated) — `Event/Endpoint`/`Table`/`Columns`/`Operation`/`Source` cells are
  code-like or path-like (verbatim); `Value Derivation` is narrative (translated). The recast
  `## Source Code References` `Order` column is a bare digit, likewise already covered.
- Contracts + checklists updated (`feature-spec-researcher-contract.md`,
  `screen-spec-researcher-contract.md`, `pipeline-feature-specs.md`,
  `verification-checklist-feature-spec.md`, `verification-checklist-screen-spec.md`).

**Migration:** run `migrate-reading-guide-db-impact.py --docs-root docs/` (or `docs/<lang>/`)
after upgrading to see which specs still need a researcher re-run; the script makes no changes
itself. Pre-migration repos keep building (validator WARNs, never FAILs, on the absent case).

---

## v25.2.0 — A1 confidence-report sidecar: all passes (additive)

**Non-breaking** — a new deterministic, best-effort companion file per artifact. No template
shape change, no promotion-gate change, no required-file-list change (same class as v24.1.0).

### Added

- **`scripts/derive_confidence_report.py`:** new deterministic script (no LLM, no source
  re-read, no network) that parses ONE promoted artifact's own inline `**Source:** file:line`
  citations (→ `○`) and `[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]` marker tags
  (→ `△`) into a Claims ↔ Evidence table, and writes `confidence-report_<artifact-stem>.md`
  beside the artifact. Per-section exhaustive (not sampled, unlike the acsim precedent it
  improves on). `confidence_derived = claims_with_evidence / claims_total` (`null` when the
  artifact carries no citations or markers). Best-effort: any I/O or parse error is swallowed,
  the script always exits 0, and it never fails the pass that called it.
- **`templates/confidence-report-template.md`** — the companion skeleton (frontmatter +
  self-reported-coverage disclaimer + Claims ↔ Evidence table + Missing Info + Risk Flags). No
  standalone "human reviewer checklist" section — the table is supporting evidence for the
  existing verification-checklist / W7a review flow, not a replacement for it.
- **`references/confidence-report-contract.md`** — the shared derivation contract: status
  mapping, `confidence_derived` formula, per-section exhaustiveness, the A1
  correctness-verification boundary (self-reported citation-coverage stat only — see
  `claude/skills/audit-doc-parity/` for blind truth checks), the prompt-injection rule for any
  future LLM-authored companion prose, and the internal-only/export-exclusion rule.
- **Wired into every promote wave:** core-artifact promote (Wave 9, `pipeline-w7-w9.md`),
  feature-specs promote (FS.7, `pipeline-feature-specs.md`), screen-specs promote (SS.3,
  `pipeline-screen-specs.md`), flows promote (FL.5) and glossary promote (GL.3, both in
  `pipeline-flows-glossary.md`), api-contracts promote (AC.5, `pipeline-api-contracts.md`), and
  system-synthesis promote (`multi-component-runbook.md` § Step 3.5) — each runs the script once
  per just-promoted artifact, immediately after `promote_drafts.py` (or, for system-synthesis,
  immediately after the draft-purge step).
- **`--limitation-note synthesis` flag (in-v1, validated decision):** system-synthesis/aggregate
  companions (`overview`, `component-catalog`, `architecture`, `glossary`, `cross-service-flows`,
  `data-ownership-map`) carry an extra mandatory header caveat — their citation density is
  structurally lower than a per-feature/per-screen artifact's, so the coverage stat is not
  comparable across tiers. See `references/confidence-report-contract.md` § Limitation-note
  header.
- **Reconcile-time advisory:** a primary artifact present with its companion absent (pre-A1
  corpus, or a prior best-effort write failure) emits a one-line, non-gating
  `[WARN] confidence_report_missing` notice on the next reconcile preflight.
- **Reviewer advisory:** `verification-checklist-flows.md` and `verification-checklist-glossary.md`
  now note that a missing companion is advisory, not a defect — reviewers must not flag its
  absence.

### Sidecar contract (never gated)

Treated exactly like `.nav-metadata.json`: always-regenerated, purely advisory, and
deliberately NOT added to `FEATURE_FILES` (`scripts/_slug_lib.py`), `check_promotion_gate.py`,
the `.pending` 4-file liveness check, or `.rebuild-state.json`. Excluded from `--overview` /
doc-writer export (the pass's enrichment reads are an explicit 4-file enumeration, not a
glob). Auto-mirrored by the translation pipeline with zero new skeleton rule — the claims
table reuses existing header/separator/file-path/enum verbatim rules.

### Implementation

- `test_derive_confidence_report.py`: frontmatter math, `○`/`△` legend, disclaimer-header
  presence, best-effort behavior on an unwritable path, a regression guard proving the companion
  never enters `FEATURE_FILES` or the promotion gate, a flows-companion case, a
  glossary-companion case, and the `--limitation-note synthesis` header-injection behavior.
- Verified `_translation_sync_lib.py`'s `_DOC_AREAS` (`system/*.md`, `generated/*.md`,
  `flows/*.md`) already glob-discover companions in `docs/flows/` and `docs/system/` with zero
  code change — same auto-mirror as the core/feature/screen companions.
- No breaking changes to template shapes or validator-stage gates.

**Version bump:** `25.1.2` → **`25.2.0`** (minor, additive).

---

## v25.1.2 — cap clamps + env hygiene (PR-review fixes, patch)

Four findings from the PR #169 external review (APPROVE-with-comments). Orchestration-prose only.

- **W8-family clamp (Medium).** W8/FS.6/FL.4 fix-cycle wave width used `REBUILD_W8_MAX_PARALLEL`
  raw — setting it to 10 exceeded the cap the invariant text promised ("every pass … fix cycles").
  Effective width is now `min(REBUILD_W8_MAX_PARALLEL, REBUILD_MAX_PARALLEL)`; AC.1's
  `REBUILD_SHARD_MAX_PARALLEL` gets the same clamp.
- **Env hygiene (Minor).** `parseInt(env ?? '5')` let junk/`0`/negative envs produce NaN/0 wave
  widths — `idx % NaN` never fires, silently disabling wave rotation (unbounded fan-out). All cap
  env parses now guard: `Math.max(1, parseInt(env ?? '5') || 5)` (junk/0 → default 5; negative →
  clamped to 1 — either way never cap-off). Includes TR.2's `BATCH_SIZE`/`MAX_AGENTS`.
- **Translate derivation rule (Minor).** `langs × agents ≤ 5` was a bare constraint statement; the
  orchestrator now DERIVES `effectiveLangs = max(1, min(TRANSLATE_MAX_PARALLEL, floor(REBUILD_MAX_PARALLEL / TRANSLATE_MAX_AGENTS)))`
  instead of trusting the env pair.
- **Wave-1 headroom warning (Low).** Legacy profiles sit at exactly 5/5 — a maintenance comment at
  Wave1.c now forbids adding a new sibling on `scoutTaskId` (chain new Wave-1 artifacts instead).

## v25.1.1 — global-cap hardening (review fixes for v25.1.0, patch)

Four defects surfaced by a review of v25.1.0 before merge. Orchestration-prose only — no
artifact format change, no migration.

- **Core Wave-1 overflow (Important).** On legacy profiles producing crud-matrix + db-objects,
  SIX Wave-1 tasks were blocked on `scoutTaskId` — exceeding the cap the release declares.
  Wave1.c db-objects is now chained behind Wave1.b crud-matrix
  (`addBlockedBy: [crudMatrixTaskId ?? scoutTaskId]`); the core-pass antichain stays ≤5.
- **Three shard fan-outs missed the SEQUENTIAL wording (Important).** The v25.1.0 inline edits
  covered data-model / route-list / user-stories / feature-list but NOT screen-list+flow /
  behavior-logic / api-map — while this changelog claimed the inverse list. All seven inline
  shard task descriptions now carry "SEQUENTIAL BATCHES … batch i+1 only after ALL of batch i";
  the v25.1.0 entry below is corrected.
- **`REBUILD_MAX_PARALLEL` was a phantom env (Minor).** Documented as an env but read nowhere.
  The wave-rotation pseudocode now reads it (FS.1/FS.5/SS.1/SS.2, aggregate).
- **Wave width conflated with batch size (Minor).** FS.5/SS.1/SS.2 rotated waves on their
  batch-size envs — raising a batch size (workload knob) silently widened concurrency past 5.
  Wave width is now `min(<batch env>, REBUILD_MAX_PARALLEL)` in FS.1 and plain
  `REBUILD_MAX_PARALLEL` for FS.5/SS.1/SS.2 reviewer/batch waves; the aggregate
  system-researcher waves use `REBUILD_MAX_PARALLEL` instead of borrowing
  `REBUILD_W8_MAX_PARALLEL`.

## v25.1.0 — global 5-subagent parallel cap (bounded-wave dispatch)

Field evidence: `--feature-specs` on a 12-feature repo spawned 12 concurrent async researchers —
the FS.1 rule "≤20 F### → flat fan-out" only activated the batch cap above 20 features, and five
other fan-outs had the same shape (batched on paper, unchained in dispatch). New invariant:
**never more than 5 subagents runnable at once, anywhere in the flow** (`REBUILD_MAX_PARALLEL=5`,
SKILL.md § GLOBAL PARALLEL CAP). Orchestration-only change — no artifact format change, no
migration needed.

- **Bounded-wave dispatch (new global rule).** Any pass creating >5 sibling tasks chunks them
  into waves of ≤5; every task of wave i+1 is `addBlockedBy` ALL tasks of wave i (never just the
  last — that lets waves overlap).
- **FS.1** — flat fan-out branch (≤20 F###) removed: per-feature tasks are now wave-chained at
  ≤`REBUILD_FS_BATCH_SIZE` (default 5). The >20 batch branch is unchanged (already sequential).
  Mirrored in `spec-stage-procedure.md` SYSTEM fan-out and SKILL.md § caps.
- **FS.5 / SS.1 / SS.2** — reviewer/batch tasks were all-unblocked-at-once (ceil(N/5) concurrent);
  now wave-chained at ≤5.
- **W8 / FS.6** — `chunk(affectedFiles, REBUILD_W8_MAX_PARALLEL)` was a no-op (every fix task
  shared one blocker); batches now chained.
- **FL.4** — flow fix fan-out was entirely uncapped; now wave-chained at ≤`REBUILD_W8_MAX_PARALLEL`.
- **AC.1** — batches chained on the LAST task of the previous batch only (overlap race); now
  chained on ALL of it.
- **Translate** — `REBUILD_TRANSLATE_MAX_PARALLEL` default 3 → **1** (langs sequential);
  documented constraint: langs × per-lang agents ≤ 5.
- **Shard fan-outs** — batches explicitly SEQUENTIAL and counted toward the global cap
  (`artifact-sharding.md § Batching`, all shard types). Inline task-description wording landed in
  v25.1.0 for data-model / route-list / user-stories / feature-list; the remaining three
  (screen-list+flow / behavior-logic / api-map) were completed in v25.1.1.
- **Aggregate system-researcher** — "one per artifact" capped at 5 concurrent (6 artifacts →
  wave of 5 + wave of 1).

## v25.0.1 — route-link parser/migration hardening (patch)

Five Critical defects surfaced by a max-level adversarial review of v25.0.0's new
`_route_link_lib.py` scanner and `migrate-feature-api-ids.py` writer — all reachable from
ordinary authoring patterns, not contrived input. No format change (route-list.md's Backend
Routes column shape is unchanged); bug-fix only.

- **Fence-scoping (C1).** `_all_backend_routes_tables` (validator/nav) and
  `_locate_backend_routes_tables` (migration) had no awareness of fenced code blocks, so a
  fenced ` ```markdown ` example table shown under `## Backend Routes` (illustrating the
  expected shape) was scanned as a REAL sub-table — leaking a fabricated `ROUTE###`/`F###` into
  the inventory/owner-map, shifting migration's numbering, and risking a spurious
  `link.feature_unresolved` FAIL. Both scanners now skip fenced regions (`_id_schemes_lib
  .segment_text` in the validator/nav path; a new `_fenced_line_indices()` helper reusing the
  same primitive in migration).
- **Pipe-in-cell write corruption (C2).** Migration's `backfill_route_list` split each row on
  `|` and blindly inserted the new columns at a fixed index; an unescaped `|` inside a Path or
  Handler cell (e.g. a regex-alternation route constraint) shifted every cell after it, writing
  a permanently corrupted row. Now: header cell count is captured per table span, and any data
  row whose cell count doesn't match is left byte-identical and reported via a WARN (never
  written corrupted).
- **4-digit code overflow (C3).** `_ROUTE_PREFIX`/`_F_PREFIX` (`\bROUTE\d{3}`/`\bF\d{3}`) lacked
  the `(?![0-9])` boundary `_id_schemes_lib.token_re()` already solved elsewhere, so `ROUTE1000`
  silently truncated to the wrong code `ROUTE100` — a real collision risk past 999 routes. Both
  patterns now reuse `token_re()` (wrapped `re.IGNORECASE` to preserve existing case-insensitive
  matching): a 4+ digit code simply does not match, instead of mismatching.
- **Duplicate ROUTE### last-wins (C4).** `build_route_owner_map` overwrote on a duplicate
  `ROUTE###` across two `### File:` sub-tables, silently dropping the first owner and risking a
  false `link.owner_mismatch` against the legitimate one. `build_route_owner_map_with_dups` now
  unions owners across duplicates and returns the duplicate set; the validator raises a new
  critical `link.route_duplicate` for each (the template's "contiguous and global" ROUTE###
  contract makes a duplicate itself a defect). `build_route_owner_map` remains as a back-compat
  wrapper.
- **Missing-separator row drop (C5).** An unconditional `table[2:]` slice (4 call sites across
  `_route_link_lib.py`, `_nav_route_lib.py`, and migration's positional `pos==1` handling) assumed
  the `|---|` separator row is always present; when hand-edited or malformed input omits it, the
  first real data row was silently dropped, producing a false `link.route_unresolved` FAIL (lib/
  nav) or a corrupted synthetic-separator insertion (migration). New shared `data_rows(table)`
  primitive in `_nav_table_parse_lib.py` checks the separator's shape before skipping; migration
  gained the matching `has_sep` branch.

`_route_link_lib.py` stays at the 200-LOC ceiling (the C5 fix's `table[2:]` sites were replaced
with calls to the new shared `data_rows()`, keeping the module itself lean); `validate_feature_api_link.py`
grew by 4 lines for `link.route_duplicate`. Regression tests reproduce all 5 reviewer fixtures
(fenced example table, pipe-in-path row, `ROUTE1000`, cross-table duplicate, missing-separator
table) across the validator, migration, and nav paths, plus a migrate→validate end-to-end pair
(including a missing-separator variant). 2258 pytest green (2242 prior + 16 new).

---

## v25.0.0 — feature↔API/route ID binding (BREAKING)

**BREAKING** — mirrors the v24.0.0 feature↔screen pattern one layer further out: `route-list.md`
gains a mandatory code column and a mandatory owner column, and a deterministic validator now
enforces both directions plus twin-consistency from day one.

### Breaking — feature↔API/route binding (Phase 1)

- **`route-list-template.md`** Backend Routes table gains two columns:
  `Method | Path | Code | Owner F### | Handler | Middleware`. `Code` is the canonical `ROUTE###`
  (contiguous, global, same shape as `SCR###`/`F###`); `Owner F###` carries the bare feature code
  that claims the route, `—` when unattributable (shared/infra routes), or comma-separated
  multi-owners for rare shared routes (e.g. `F001, F003`).
- **`_id_schemes_lib.py`** gains the `ROUTE` scheme (`WORD###`, global scope) and a new
  `ARTIFACT_OWNS["route-list"] = ["ROUTE"]` entry; `SIBLING_MATRIX["ROUTE"]` is scoped to
  `feature-list.md` + `behavior-logic.md` only — `technical-spec.md` is per-feature (out of this
  global-artifact matrix's reach) and `screen-flow.md` was excluded (no real `ROUTE###` citation,
  only an optional either/or in a `GUARD-###` heading).

### New validator `validate_feature_api_link.py`

- forward — `technical-spec.md` / `behavior-logic.md` `{ROUTE###}` citations (Artifact References'
  Codes Used column) resolve to `route-list.md`'s `Code` column.
- reverse — `route-list.md`'s `Owner F###` cell(s) (multi-owner comma/slash aware) resolve to
  `feature-list.md`.
- twin — a feature's forward `ROUTE###` citation must appear in that route's reverse `Owner F###`
  set; a silent double-claim across features is a real correctness bug, not a WIP state (the
  exact lesson PR #158 forced for feature↔screen, extended one layer out).
- Degradation contract: no `Code`/`Owner F###` columns at all → WARN `link.pre_migration`
  (never breaks the build); a present-but-unresolvable code → critical `link.route_unresolved` /
  `link.feature_unresolved`; a mapped route whose owner disagrees with a citing feature → critical
  `link.owner_mismatch`; an empty/placeholder Owner cell on a migrated table → soft `link.unmapped`
  WARN (an unclaimed `—` owner is NOT a twin-consistency mismatch); either inventory file (
  `route-list.md` / `feature-list.md`) absent entirely → WARN `link.inventory_absent` (missing ≠
  drift). Wired into the FS.2 feature-specs gate right after `validate_feature_screen_link.py`.

### New migration `migrate-feature-api-ids.py`

- Idempotent PER-TABLE backfill: a `route-list.md` can be half-migrated (one `### File:`
  sub-table already coded, another not) — each sub-table's own header decides whether it is
  touched; `ROUTE###` numbering stays globally contiguous by seeding from the highest existing
  code across all sub-tables.
- Ownership is DERIVED, not read from an existing bridge (unlike the screen migration's
  `screen-flow.md` "Owned screens" source): every `docs/features/F###/technical-spec.md`'s
  Artifact References citations are inverted into `{ROUTE### -> [citing F###]}` via the SAME
  shared parser (`_route_link_lib.artifact_ref_cited_routes`) the validator uses, so migration
  attribution and validator citation-detection can never disagree. Zero-citation routes get `—`;
  multi-citing routes get a comma-joined owner list.
- Non-destructive: only inserts the `Code`/`Owner F###` columns, never rewrites existing
  Method/Path/Handler/Middleware cells. No `technical-spec.md` files found (bridge absent) →
  WARN + exit 0, no changes ("run the feature-specs pass first").

### Nav wiring (Phase 4)

- New `_nav_route_lib.py`: per-feature Route/API table, presence-pruned (renders only when the
  feature has ≥1 resolvable `ROUTE###` citation), resolving Method+Path labels across every
  Backend Routes sub-table; every row links to the single shared `../../generated/route-list.md`
  (no per-route spec files exist, unlike screens/`SCR###`/`spec.md`).
- `_nav_feature_lib.py`'s `relationship_legend` gate extended to `{5, 7, 9}` — reuses
  `route-list.md`'s existing reading-order gate number 9, no new gate invented.
- All 3 locale string modules (`_nav_strings_{en,vi,ja}.py`) updated in lockstep: the
  `relationship_map` bullet now names `ROUTE###` explicitly (was a vague "route" mention) and
  states that `api-map.md`/`api-contracts.md` remain separate, unbound views; new
  `feature_readme` keys `routes_heading` / `col_route` / `col_route_owner` / `col_route_spec`.

### Out of scope

- `api-map.md` and `api-contracts.md` are **NOT** bound by this release. They are derived/grouped
  views with their own separate code schemes (`{ROUTE_CODE}`/`{GQL_CODE}`/`{GRPC_CODE}` in
  `api-contracts.md`, no codes at all in `api-map.md`) — cross-checking them against
  `route-list.md` is a candidate follow-up, not part of v25.0.0.

### Contracts + checklists updated

`verification-checklist-core-artifacts.md`, `verification-checklist-feature-spec.md`,
`feature-spec-researcher-contract.md`, `pipeline-feature-specs.md`, `technical-spec-template.md`,
`behavior-logic-template.md`.

**Version bump:** `24.1.0` → **`25.0.0`** (major, breaking — new required schema element + gate,
matching the severity class of v24.0.0's own bump).

---

## v24.1.0 — file-schema field + file-endpoint reading scope + twin-consistency reviewer rule (additive)

**Non-breaking** — purely additive improvements to file-exchange documentation, backend reading scoping, and template consistency checking.

### Added

- **File Schema field (BL + ALG):** `behavior-logic-template.md` (BL blocks) and `technical-spec-template.md` (`### ALG-###_Name` Algorithm blocks) each gain an identical `**File Schema**` field — a `| Column | Type | Required | Notes |` table documenting the internal column/header contract of an import/export file (CSV/XLSX), populated only when the block's Type/description matches file-exchange vocabulary (`import, export, csv, xlsx, upload, download, bulk`); `N/A — not a file-exchange type` otherwise. Byte-identical table format in both templates — no format drift between BL and ALG.
- **Bounded backend-reading exception:** `screen-spec-researcher-contract.md`'s Import Discovery Rule (frontend-only, 1-level-deep) gains a narrow exception — when a screen's server-side action is file-producing/consuming (export/import/download/upload path or multipart/file Content-Type), the researcher MUST follow the backend handler one controller→job/service hop to identify the file schema, then **cross-reference** the feature's `BL-### File Schema` rather than re-deriving the column list (DRY). If the backend file-generation code is unreachable within that bound, the researcher escalates via `## Unresolved Questions` instead of silently omitting.
- **Two new validator rules (both warning-severity, non-halting):**
  - `BehaviorLogic.file_schema_missing` in `validate_behavior_logic.py` — flags a BL block whose own Type + description matches file-exchange vocabulary but whose own `**File Schema**` field is left unpopulated (or misuses the `N/A` string despite the vocab match).
  - `FeatureSpec.alg_file_schema_missing` in `validate_feature_spec.py` — the same check applied to `### ALG-###_Name` blocks in `technical-spec.md`.
  Both share one detection helper (`_file_schema_lib.py`) for the vocabulary match and "populated schema" test — no duplicated heuristic. Both rules registered in `verification-checklist-feature-spec.md`'s Deterministic Validator Coverage table.
- **W7i twin-consistency reviewer rule:** `verification-checklist-screen-spec.md` gains a new reviewer-only rule (`W7i`, no Python validator) enforcing that create/edit screen pairs sharing the same `**Feature**` backlink remain consistent on § A) Client-side validated field names — divergences without a stated reason are flagged as a warning. Registered in the checklist's summary table.
- **Server-side validator-class escalation:** `screen-spec-researcher-contract.md` §4.3 Section B now requires the researcher to first attempt to locate and read the endpoint's backend validator class (FormRequest / request-validator / serializer / DTO) before writing `[UNVERIFIED]` on a server-driven error message. If found, the real message is extracted (no `[UNVERIFIED]`); if the class is genuinely unreachable, `[UNVERIFIED]` stands but MUST be paired with a matching `## Unresolved Questions` entry naming the endpoint and the path that couldn't be reached.

### Implementation

- New shared library `_file_schema_lib.py` for File Schema field parsing and validation across BL + ALG contexts.
- New test files: `test_validate_behavior_logic.py`, `test_validate_feature_spec.py`, and `test_file_schema_lib.py` (21 new test cases covering the two validator rules + shared lib).
- No breaking changes to template shapes or validator-stage gates; all new rules are warning-severity and non-halting.

**Version bump:** `24.0.0` → **`24.1.0`** (minor, additive).

---

## v24.0.0 — feature↔screen ID binding + thickened feature/screen reading guide (BREAKING)

**BREAKING** — the two ID systems are now bound both ways, changing two templates and
adding a validation gate. Additive reading-guide work (A1–A6) ships in the same release.

### Breaking — feature↔screen binding (Phase B)

- **`screens-template.md`** Screen List gains an `SCR###` column:
  `Screen Name | SCR### | What User Sees | What User Can Do`. The code is the canonical
  `SCR###_NameSlug` from `screen-list.md` — the bridge to `docs/screens/SCR###_Name/spec.md`.
- **`screen-spec-template.md`** header gains `**Feature**: F###_Name` — the owning feature,
  the inverse of the SCR### column.
- **New validator `validate_feature_screen_link.py`** (WARN-capable, NON-halting): forward
  (screens.md SCR### ∈ screen-list.md) + reverse (screen-spec **Feature** ∈ feature-list.md).
  Degradation contract: a missing column/backlink on an un-migrated doc → WARN
  `link.pre_migration` (never breaks the build); a present-but-unresolvable code → FAIL
  (`link.scr_unresolved` / `link.feature_unresolved`). Wired into the FS.2 feature-specs gate.
- **New migration `migrate-feature-screen-ids.py`** (idempotent, non-destructive): backfills
  the SCR### column (resolved via screen-list.md by name) and the **Feature** backlink
  (sourced from `screen-flow.md` § Feature Entry Points `**Owned screens**`). Absent bridge →
  reports and exits 0 with no changes. Only inserts a column/line — never rewrites prose cells.
- Contracts + checklists updated (`feature-spec-researcher-contract.md`,
  `screen-spec-researcher-contract.md`, `pipeline-feature-specs.md`,
  `verification-checklist-feature-spec.md`, `verification-checklist-screen-spec.md`).

### Additive — feature/screen reading guide (Phases A1–A6)

- **A1** per-artifact causal "why read this here" clauses (`reading_why`) appended to the
  single-component index layer-1-3 rows (mirrors aggregate `reading_order_rows`).
- **A2** multi-line "how to read a feature" traversal block (`feature_traversal`) replacing the
  single buried note; teaches the feature → screen → SCR### path.
- **A3** static ID-relationship legend (`relationship_map`) — F### ⇄ SCR### ⇄ US### ⇄ route.
- **A4** per-feature `README.md` inside `docs/features/F###_Slug/` — 4-file reading order +
  best-effort Screen → SCR### → spec table (column-aware).
- **A5** `docs/features/README.md` feature index (was suppressed; now generated from F### subdirs).
- **A6** `new_dev` role line now points into the feature traversal (gated on the features entry).
- New modules: `_nav_feature_lib.py`, `_nav_table_parse_lib.py`. All 3 locales
  (`_nav_strings_{en,vi,ja}.py`) edited in lockstep; parity tests enforce skeleton identity.

### Nav refresh on the standalone feature-/screen-specs passes

- The **feature-specs (FS.7)** and **screen-specs (SS.3)** passes now run `build_navigation.py` after
  promote (mirroring the core-pass W9.6 step), so the newly-promoted `docs/features/F###/` +
  `docs/screens/SCR###/` dirs immediately surface in the reading-order README, the per-feature READMEs
  (A4), and the features index (A5). Previously these passes promoted the dirs but left the README
  stale until the next core pass. Primary root is refreshed directly (mode-aware `docs_root`);
  secondary-lang mirrors continue to refresh via the translation auto-sync Step 3.5.

**Migration:** run `migrate-feature-screen-ids.py --docs-root docs/` (or `docs/<lang>/`) once
after upgrading; re-run is a no-op. Pre-migration repos keep building (validator WARNs, never FAILs).

---

## v23.0.0 — component per-lang placement: single-source translate model (BREAKING)

**BREAKING** — three tracks shipped together. `SYNTHESIS_FORMAT_VERSION` → `22.0.0` (trips
`[WARN] stale_digest` on existing aggregate state, forcing re-synthesis after migration).

### Track 1 — Component placement model (P04/P05/P07)

Per-component docs are now written ONCE to the language-resolved source root:
- `docs/components/<name>/` for en single-lang (byte-identical to v22 — no change)
- `docs/<primary>/components/<name>/` for non-en or per-lang repos (v23 BREAKING)

`resolve_component_paths` passes `primary_lang` to `resolve_docs_root` — the same resolver
used by core/system artifacts. **The derived-view projection (ADR-0002 rung-1/2/3) is
deleted.** There is no `docs/<primary>/components/` rebuilt by the aggregate; it is written
directly by `--root`/`--batch` runs.

Secondary-lang component docs at `docs/<L>/components/<name>/` are produced by the
translation pipeline (`--lang <L> --root <name>`) and auto-synced on change via
`translation_sync_gate.py` (`_DOC_AREAS` now includes `"components"`). Every secondary-lang
component doc is a real translation — the rung-3 "dùng tạm" fallback is gone.

### Track 2 — Derived-view shadow purge (P06)

`_component_view_lib.py` and the projection entry-point in `_component_placement_lib.py`
deleted. Test file `tests/test_component_placement.py` removed. All three recorded in
`claude/metadata.json → deletions`.

### Track 3 — Reading-guide / nav fixes (P04/P07)

`build_navigation.py` generates READMEs at the resolved per-lang component path. The
`--aggregate` `system/README.md` reading-guide no longer references a derived-view path.

### One-time migration (existing non-en repos)

`_component_migrate_lib.migrate_components_to_lang` runs automatically on the FIRST
`--aggregate` call when `primary_lang != en` and `docs/components/` still exists (the old
v20/v22 root location). Guarded by sentinel `docs/<primary>/.components-migrated-v23`.

| Scenario | What happens |
|----------|--------------|
| `docs/components/` absent (new or already clean v23 repo) | no-op; sentinel written |
| Only `docs/components/` present | atomic `os.rename` root → lang; sentinel written |
| Both trees present, byte-identical | `shutil.rmtree` root copy; sentinel written |
| Both trees present, files differ | keep both; `[WARN]`; sentinel NOT written — re-run after resolving manually |
| `primary_lang == "en"` | no-op; en source stays at `docs/components/` by design |

**Root `docs/README.md` pruning:** after a successful migration a purely-generated pointer
README at the root is deleted; a hand-written one is never touched.

### ADR

ADR-0002 superseded by **ADR-0003** (`docs/decisions/ADR-0003.md`). ADR-0002 kept as
immutable history with a superseded banner.

---

## v22.0.0 — auto-detect multi-component + shared-layer attachment (BREAKING)

A single `rebuild-spec` run over **one repo holding N independent executables** (Ishindenshin: 20
Delphi `.dpr` under `PG/<MODULE>/` + a shared `PG/Common/` + an Oracle `DB/{TABLE,SP,VIEW}/<MODULE>/`
tree) used to flatten every module into ONE mono doc set — the multi-component machinery was opt-in by
flag and never auto-triggered. v22 closes that gap with three moves, all inside the existing
multi-component machinery.

**BREAKING:** a plain `/tkm:rebuild-spec` over a multi-executable `one-spec-per-unit` repo now
**auto-switches** into the `--emit-manifest`→`--batch`→`--aggregate` loop instead of producing one mono
doc set. Escape hatch: `--mono`.

- **Auto-switch (Phase 03/04).** `detect_stack_profile.py` resolves a `component_profile` — a matched
  `one-spec-per-unit` profile that claims ≥2 component roots — and emits `auto_switch` + `auto_switch_reason`.
  SKILL.md Preflight 2.5 prints `[INFO] multi-component detected (…): switching to --emit-manifest flow`
  and enters the driver loop. Bypasses: `--mono`, an explicit `--root <subrepo>`, an existing
  `.rebuild-components.json` (idempotent).
- **Executable-manifest boundary (Phase 01/02).** New optional profile field `component_boundary_globs`
  (`["*.dpr","*.dproj","*.dpk"]` on `delphi-vcl`) marks a component root by executables only — a dir with
  only `.pas` is no longer claimed. `find_components` gains keyword-only `boundary_globs`/`shared_abspaths`/
  `warnings` (default-None = byte-identical legacy behavior; all existing call sites unaffected).
- **Shared-layer marker (Phase 01/03/05).** New optional profile field `shared_layer_dirs`
  (`["Common","DB"]`) — those dirs are scanned ONCE and attributed to each component, never claimed as
  their own component (Layer-1 exclusion runs before the marker check, defeating the oracle co-detection
  of `DB/`). Surfaced as `detectJson.shared` and written to a SIDECAR `.rebuild-components-shared.json`
  (the component manifest stays a JSON ARRAY — Finding 1). A suppressed dir emits `shared_layer_excluded`
  so a real module named `DB`/`Common` is not silently dropped (Finding 4).
- **Deterministic DB attribution (Phase 05).** `_shared_attribution_lib.matches_module_label` (full-segment
  equality — `POS` ≠ `POSDEN`) drives a per-component FILTERED view of the shared-DB digest, attributing
  `DB/<TYPE>/<MODULE>` objects to `PG/<MODULE>` by the declared module-name convention. The Step-0.4
  shared pre-pass runs at the ROOT plan-dir (distinct from each component's → no `is_extractor_completed`
  collision; the `--out-suffix` idea was dropped).
- **`--profile <id>` (Phase 03).** Pins the authoritative profile when Delphi+Oracle co-detect and a
  DB-heavy tree would otherwise make `oracle-plsql` the hit-count `recommended` (Finding 2).
- **Detect output `schema_version` → 22.0.0.** Additive (new `component_profile`/`auto_switch`/`shared`
  fields); `recommended_profile` unchanged for legacy callers. `SYNTHESIS_FORMAT_VERSION` /
  state schema UNCHANGED (no synthesis-output or state-shape change). New file:
  `scripts/_shared_attribution_lib.py`.

Red-team hardened (`reviewer-260629-1508`): 2 BLOCKERS (manifest-array sidecar, component_profile vs
hit-count winner) + 3 majors folded into the design before build.

## v21.0.1 — extractor + contiguity fixes from real Delphi/Oracle run (patch)

Five bugs surfaced validating v21 on a real Delphi+Oracle (Shift-JIS) ERP repo on a
case-sensitive Linux FS. No output-format change (`SYNTHESIS_FORMAT_VERSION` stays `21.0.0`).

- **Case-insensitive extractor globs.** `fnmatch(fn, glob)` with lowercase globs (`*.sql`,
  `*.pas`) silently skipped uppercase `.SQL`/`.PAS` files on case-sensitive filesystems —
  near-empty digests (1 table instead of 461). Filename is now lowercased before matching in
  `extract_sql_schema.py`, `extract_data_flow.py`, and `_extractor_lib.py` (`source_tree_hash`).
- **Oracle leading-comma columns.** `_COL_DEF` in `_sql_parse_lib.py` required a line to start
  with whitespace, so leading-comma DDL (`,\tCAPTION VARCHAR2(40)`) parsed only the first column.
  `_COL_DEF`/`_COL_SKIP` now accept a leading comma.
- **Contiguity duplicate false-positives (hybrid heading/prose rule).** `validate_id_contiguity.py`
  counted *every* prose occurrence of a code as a definition, so summary-table rows,
  `**Dependencies**:` cross-links, `F001–F045` ranges and format examples all read as duplicates.
  Now: if a code appears as a Markdown **heading** at all, its duplicate count is judged by heading
  occurrences only (table/bullet refs ignored); if it **never** appears as a heading (table-defined
  schemes like `route-list` / `crud-matrix`), it falls back to all-prose counting so genuine
  duplicate rows are still caught. Two headings for one code remains the canonical duplicate.
- **Stack-specific core artifacts promoted.** `crud-matrix.md` and `db-objects.md` (extractor-
  digest-derived) added to `_layout_lib.py`'s layout map and `promote_drafts.py`'s promote list,
  so Delphi/Oracle runs place and promote them like other core artifacts.

Regression tests added: `TestParseColumnLine` (leading-comma), `test_uppercase_extension_detected`,
heading-based duplicate fixtures, plus `test_heading_defined_with_many_refs_not_duplicate` and
`test_table_defined_scheme_duplicate_via_fallback` in `test_validate_id_contiguity.py`. 1955 pytest green.

---

## v21.0.0 — screen-artifact unify (non-web) + IPE stack-aware US generation (BREAKING)

**BREAKING** — non-web stacks now gain a screen artifact. `SYNTHESIS_FORMAT_VERSION` → `21.0.0`.

**Motivation.** On a real Delphi+Oracle ERP repo, `delphi-vcl` skipped the whole
`route-list/screen-list/screen-flow/api-map` cluster (`class: web`) → **no screen artifact**, and
US generation (screen-anchored) starved to **86 US for 440 material forms** (~20–35% coverage). v21
gives desktop stacks a screen artifact and makes US enumeration run per-form, without touching the
(correct) web path.

**What changed:**
- **New profile field `screen_source`** (`route-view` | `dfm-form` | `none`; `form-module` reserved).
  `screen-list`/`screen-flow` are produced **iff** `screen_source != none`, *overriding* their
  `artifact_map.action`. `route-list`/`api-map` stay web-only (governed by `artifact_map`). The
  `produce()` helper is the single source of truth. Profiles: web-js-ts→`route-view`,
  delphi-vcl→`dfm-form`, oracle-plsql/generic-source→`none`.
- **Anti-skip hardening (self-consistency).** First real Delphi run silently skipped screens: the
  orchestrator read `delphi-vcl.json`'s `screen-list/screen-flow → {action:skip, class:web}` and the
  "non-web project → skip web artifacts" heuristic, ignoring the subtle `screen_source` override. Fixed
  three ways so the produce decision is unmissable: (1) `delphi-vcl.json` now sets those two to
  `action:"produce"` — the profile reads truthfully (schema adds a **self-consistency rule**:
  `screen_source != none` ⇒ map them `produce`); (2) an explicit MANDATORY rule at the `produce()`
  binding in `pipeline-dispatch-and-gates.md` — the skip decision is `produce()`/`screen_source` ONLY,
  NEVER `class:web` and NEVER "route-list was skipped"; (3) SKILL.md's artifact→wave table no longer
  lists `route-list.md` as a screen prerequisite for non-web stacks (source is the form-nav digest).
- **Scout `.dfm` root-kind classification** — `object X: TBaseClass` header decides the tag:
  TForm→`screen`, TFrame→`screen-embedded`, TDataModule→`datamodule` (+`[reachable]`). Never by
  extension. `count_screen_files.py` regex tightened (`\tscreen(?![-\w])`) so `screen-embedded`/
  `datamodule` no longer inflate the visual-screen count.
- **New extractor `extract_form_nav.py`** — parses `.pas` Show/ShowModal/CreateForm, resolves
  target form→unit, builds a reachability closure from the `.dpr` root form, emits
  `_digest_extract_form_nav.json` (forms + edges, each citing `file:line`). Unreachable/indirect →
  `reach: unverified` (included, never dropped). Wired into `delphi-vcl` extractors + allowlist.
- **Route/api-map decoupling** (the part that actually unblocks Delphi): W9 `allCoreDocsPromoted`
  asserts route-list/api-map/screen-list/screen-flow only when `produce()`; the W7a reviewer
  artifact list is built from produce()-true artifacts; the verification-checklist SCR→RouteList
  cross-check + service-coverage rule are gated on `produce("route-list")`; `validate_screen_list.py`
  gains `--screen-source` (skips the route-specific `no_wildcard_route` check off route-view, keeps
  all structural checks). Without this, a perfect Delphi run HALTED at Wave 9.
- **Stack-aware templates** — screen-list/screen-flow carry conditional STACK-AWARE directives:
  `dfm-form` omits Routes/URLs, Authentication Flow, Guard Logic, Deep-Link, Unsaved-Changes,
  Extraction Signatures; uses a caller-based Invocation/Entry-form shape (no fork — one template).
- **IPE stack-aware** — Step 1 vocabulary enumerates `.dfm` controls (TButton/TAction/TMenuItem…+
  On* handlers) for dfm-form; Step 3 merge key is per-stack (web=same HTTP endpoint, dfm-form=same
  event-handler proc — NOT same table); materiality filter drops FPrt/FSel/FDlg/FSub/FCal families;
  form-variant dedup collapses `FHotelm`+`FHotelm2`; Oracle PL/SQL reachable logic → system-action
  US in behavior-logic/feature-list. Web split rule textually unchanged. `IPE_MERGE_CANDIDATE`
  reviewer rule updated to the per-stack key.
- **RE citation** — `validate_source_citations.py --re-mode` now counts screen-list/screen-flow
  toward citation density (when present on disk). `[UNVERIFIED]` reachability rows are valid (they
  carry a form-definition `file:line`). Advisory WARN, never HALT.

**Migration.** Existing Delphi docs lack screen-list/screen-flow. On the next run the orchestrator
backfills them: when `produce("screen-list")` is true but `docs/generated/screen-list.md` is absent
while core docs exist, Wave 2 screen-artifact generation is scheduled (see `pipeline.md` §
"v21.0.0 screen-artifact migration"). Additive — no prior artifact is deleted. Web output is
byte-comparable to pre-v21 (regression suite green); oracle-plsql still emits no screen artifact.
Because `screen_source` is a new resolved-profile field, the profile/state schema version bumps in
lockstep: `_stack_profile_lib.SCHEMA_VERSION` and `.rebuild-state.json`'s `STATE_SCHEMA_VERSION`
→ `21.0.0` (RT-F4). On resume, a state `< 21.0.0` invalidates the preflight checkpoint and
re-resolves the profile, so a pre-`screen_source` checkpoint cannot silently fail-close screens to
`"none"`.

**US recovery.** Delphi US count recovers from 86 toward the audited ~150–250 band (post
materiality-merge + variant-dedup), not the 354 1:1 upper bound.

---

## v20.0.0 — per-component language-aware placement: source-vs-derived-view (BREAKING)

**BREAKING** — components layout semantics change. `SYNTHESIS_FORMAT_VERSION` → `20.0.0`.

`--aggregate` now builds a **derived view** `docs/<primary>/components/<name>/` from the
lang-agnostic source `docs/components/<name>/` using a rung-selected per-component slice.
The source is NEVER mutated. Stale orphan dirs are pruned atomically each run.

**Source-vs-derived-view model (ADR-0002):**
- **Source of truth:** `docs/components/<name>/` — per-component `--root`/`--batch` runs
  always write here (unchanged). Lang-agnostic, ping-pong-safe.
- **Derived view:** `docs/<primary>/components/<name>/` — rebuilt atomically each aggregate
  run (temp-dir + rename swap; orphan prune). Not a symlink — a real committed copy.
- **Rung selection:** rung-1 (has `<L>/` mirror → flatten to view root, mirror wins on
  collision); rung-2 (primary_lang == L → copy base, exclude sibling lang dirs); rung-3
  (no `<L>` content → copy primary base + `[WARN] lang_fallback`).
- **Legacy converge:** a stray `docs/<primary>/components/` from a prior v15 run is moved
  back to `docs/components/` (source) on the first aggregate run.

**LANGUAGE_LAYERS split:**
- `MOVED_LAYERS` = `("system", "generated", "flows", "features", "screens")` — flip/relocate
  move ONLY these layers. `components` is no longer relocated by the layout flip.
- `LANGUAGE_LAYERS` kept as backward-compat alias (includes `components`) for rollback.

**Digest collection:** always reads from SOURCE `docs/components/` (lang-agnostic) regardless
of layout mode. Prior v15 code read from `docs/<primary>/components/` in per-lang mode.

See `docs/decisions/ADR-0002` (supersedes ADR-0001's deferred-flatten stance — the flatten
IS done, but only in the derived view, never in the source).

---

## v19.0.0 — aggregate tier: Python is scanner-only (BREAKING)

**BREAKING** — completes v18's Python-removal. Python no longer generates ANY aggregate document
content (prose, tables, OR Mermaid). `SYNTHESIS_FORMAT_VERSION` → `19.0.0`.

`--aggregate` is now purely the scanner: writes `.system-scout-report.md` as **data tables only**
(no Mermaid) + mechanical `per-component-confidence.md`, and creates **no `.draft.md`**. The
**system-researcher** CREATES each of the 6 system docs from `templates/aggregate/<name>-template.md`
+ the scout report + the components' docs — authoring prose, **building tables, and drawing the
Mermaid itself** (topology/layer/saga). Docs-derived edges now appear IN the charts (v18 had them in
prose only, because Python drew the chart from the thin digest before the docs were read — the root
cause of the stale-chart problem).

- **Removed (Python):** `_build_topology_mermaid_block`/`_build_layer_mermaid_block`/
  `_build_saga_sequence_block`, `render_draft_from_template`, `load_aggregate_template` from
  `_synthesis_scout_lib.py`; the 6-draft emission loop from `synthesize_system.py`.
- **Fidelity → review gate + lint** (was mechanical pinning): new `lint_mermaid_safety()` scans
  authored Mermaid fences for unsafe raw chars; `validate_filled_scaffold(draft)` (single-arg) flags
  leftover `{{FILL}}`/`{{SCOUT}}` + lint violations before promote. `SY-R6` rewritten for LLM-drawn
  charts (every edge traces to scout/cited-doc; no phantom edges; `[UNVERIFIED]`+cited; valid+safe).
- **Templates rewritten:** drop `{{SCOUT}}`; `{{FILL}}` now instructs "BUILD the table" / "DRAW the Mermaid".

Validated end-to-end on `wsm_platform` (reviewer `failed:0`; charts now carry the employee Kafka/gRPC
edges). 1906 pytest green.

**Housekeeping (post-v19):** removed the orphaned Phase-08 reused-mirror trió —
`scripts/mirror_reused_component.py` + `scripts/_reused_mirror_lib.py` +
`scripts/tests/test_reused_mirror_lib.py` — and pruned the runbook's "Delete-original gate" prose. The
CLI was implemented + tested but never invoked (no import, no orchestration reference); the live reused
path is `synth_digest_from_docs.py` (Step 0.5). No behaviour change (it was never called). 1889 green.

---

## v18.0.0 — LLM-authored aggregate tier (scout-report + template) + read-reused-docs (BREAKING)

**BREAKING** — the aggregate (`--aggregate`) tier no longer builds its documents in Python.
`SYNTHESIS_FORMAT_VERSION` → `18.0.0` (forces re-synthesis on the next run).

New model: Python computes facts → `.system-scout-report.md` (services table with `reused` flag +
absolute docs path, edge/fan-in-out/entity/correlation/event tables, pinned topology/layer/saga
Mermaid, confidence) → emits the 6 system docs as `<name>.draft.md` from
`templates/aggregate/<name>-template.md` with `{{SCOUT}}` fact-blocks pre-substituted verbatim
(Python-pinned diagrams/tables = provably faithful). The new **system-researcher**
(`references/system-researcher-contract.md`) AUTHORS the `{{FILL}}` prose, then the v17 Step 3.5
review→fix→promote gate runs (now `SY-R1..R8` over 6 authored artifacts).

- **[Critical rule] Read reused docs — never declare "unobserved" blind.** The researcher MUST read
  each component's docs (without exception for any `reused`/docs-derived component) at the scout-report
  docs path and supplement the heuristic edge list. Calling a read-available component
  "isolated/unobserved" = CRITICAL (`SY-R8`). Root cause: `synth_digest_from_docs.py`'s thin digest
  (WSM `ssv-wsm-employee` had `topic=0` → looked isolated; its docs reveal Kafka consume/produce +
  gRPC to auth & gateway).
- **Removed:** Python scaffold builders (`render_system_overview_scaffold` etc., `render_service_catalog`,
  `render_data_ownership_map`, `render_system_architecture`) and the orphaned `_synthesis_render_topology.py`
  (builders moved to new `_synthesis_scout_lib.py`). `data-ownership-map.md` is now authored; only
  `per-component-confidence.md` stays mechanical.
- **Promote gate:** `validate_filled_scaffold` now flags any remaining `{{FILL}}`/`[FILL]`/`{{SCOUT}}`;
  the H2 add/drop lock is dropped.
- **Per-lang root README removed:** `build_navigation.py` no longer writes a root `docs/README.md` in
  per-lang mode (was a ~3-line pointer in v15-v17). `resolve_root_readme_removal()` deletes a
  purely-generated root README, preserves a hand-written one. Sole entry: `docs/<primary>/README.md`.

Validated end-to-end on `wsm_platform` (1905 pytest green; reviewer `failed:0`).

---

## v17.0.0 — aggregate-tier quality: review gate, charts, reasoned nav, entity dedup (BREAKING)

**BREAKING** — the aggregate (`--aggregate`) promote gate changed. Hybrid artifacts are no longer
promoted on narrative-fill alone; a new **review→fix-cycle→promote** stage (Step 3.5) now stands
between fill and promote. A run whose hybrid drafts fail review after `MAX_FIX_CYCLES = 3` preserves
the drafts and escalates instead of promoting. Output paths are unchanged.

Four fixes, sourced from a real `wsm_platform` aggregate run:

- **Review subsystem + wording rubric (D).** New `references/verification-checklist-system-synthesis.md`
  (`SY-R1..SY-R7`: readability, factual consistency vs digests, `[UNVERIFIED]` honesty, entity-name
  sanity, no-empty-glossary-without-reason, chart coherence, read-first reasoning). The aggregate
  narrative-fill now runs a W7a-style `reviewer`→bounded fix-cycle (mirrors `pipeline-w7-w9.md`,
  reuses `_review_report_lib.mutate_review_report`)→promote gate over the 5 hybrid artifacts; the
  mechanical `per-component-confidence.md` / `data-ownership-map.md` are not reviewed. A human-readability
  **wording rubric** (active voice, define terms, no raw symbol dumps, audience = new engineer) is now
  part of the fill contract — the cheapest quality win. Orchestrator-driven; no new Python.
- **Charts for prose sections (B).** `architecture.md` `## Layer Diagram & Data Flows` now carries a
  role-tiered Mermaid `flowchart TB` (gateway → services → frontend); `cross-service-flows.md` sagas now
  carry a Mermaid `sequenceDiagram` — both scaffolded mechanically (injection-safe) before the fill
  narrative, kept under existing H2 so the promote gate's H2-lock holds.
- **Reasoned reading-order + README dedup (C).** Synthesis writes a side-channel
  `docs/<lang>/system/.nav-metadata.json` (ranked by role tier → fan-in, reused last, with a rationale
  key); `system/README.md` renders a "which service to read first + why" section (lang-aware, omitted
  when the metadata is absent). The parent `docs/<lang>/README.md` is now a thin pointer to
  `system/README.md` instead of duplicating the full reading-order table.
- **Entity dedup + dirty-name filter (A).** `entity_ownership` dedups by canonical `(owner, name)` and
  a shared `_canonical_entity_name` helper drops doc-section headings lifted as entity names
  ("Entity Relationship Diagram", "Entities", "Summary", "Validation Rules") and collapses
  `MODELnnn — X` / `X` variants. Filtered at both the parse source (`parse_entities`) and downstream.
  Plus a per-lang **components relocation** fix: a stray `docs/components` left at the root when the
  system dir was already migrated is now relocated to `docs/<lang>/components` (idempotent, reusing
  `_catchup_components`), independent of the `needs_migration` gate that previously skipped it.

New module `scripts/_nav_metadata_lib.py`. No files removed (no `metadata.json` deletions).

## v16.4.0 — docs refactor (multi-component runbook extracted; no behavior change)

Thinned the always-loaded `SKILL.md` by extracting the ~95-line **Multi-component runbook** block and
the 9 multi-component flag rows (`--root`/`--batch`/`--aggregate`/`--emit-manifest`/`--manifest`/
`--primary-lang`/`--force-aggregate`/`--digest-collect`) into a new on-demand reference
`references/multi-component-runbook.md`. `SKILL.md` keeps a ~6-line stub + a single pointer flag row +
a new "On-demand pipeline loading" directive (load the reference when any multi-component flag is set).
Single-repo runs (the common case) no longer carry monorepo-only detail in context. The
recommended-pass-sequence and all single-repo/pass flags (`--legacy`, `--lang`, `--non-interactive`, …)
stay inline. **No pipeline logic changed** — pure documentation reorganization; every gate, flag, and
contract is preserved verbatim in the reference. Synthesis internals remain in
`system-synthesis-contract.md`; the runbook now cross-links to it.

## v16.1.0 — additive (per-pass batch driver)

`--batch` gains `--pass <feature-specs|screen-specs|flows|glossary>` so the multi-component runbook
can auto-loop the remaining passes per component (Step 1b), the same way core is looped — durable
per-pass status, failure-isolation, cross-session resume. Core `--batch` (no `--pass`) is
BYTE-IDENTICAL; manifest entries gain nested `pass_status`/`pass_fail_reason` (absent ≡ pending —
back-compat). DAG: `flows`/`glossary` require `feature-specs`; `feature-specs`/`screen-specs` need
only core done. Reused/excluded components skip every pass; a pass "done" carries NO sha (output is a
disk-verifiable docs tree). Primitives in `scripts/_manifest_pass_status_lib.py`
(`next_pending_pass`/`mark_pass_done`/`mark_pass_failed`/`pass_summary`). `--aggregate` is orthogonal
(consumes only the core digest); `--lang` still runs last, once, over the whole tree.

## v16.0.0 — BREAKING CHANGE (aggregate doc-tier parity)

The `--aggregate` artifact names are renamed to PARITY with the per-component tier:
`system-overview.md`→`overview.md`, `service-catalog.md`→`component-catalog.md`,
`system-glossary.md`→`glossary.md`; the standalone `interaction-graph.md` is FOLDED into a NEW
`architecture.md` (mechanical topology + edges + fan-in/out + self-loops, plus a hybrid narrative
section). `data-ownership-map.md`, `per-component-confidence.md`, `cross-service-flows.md` keep their
names. The component-catalog gains Dependencies + Module-link + Responsibility (hybrid-fill) columns;
the aggregate `system/README.md` is rewritten to a numbered reading-order table + role reading-paths +
components pointer + principles (no more flat `## Files` list). No migration of existing on-disk
aggregate files (none exist — Validation S1); renderers emit the v16 names from the start and
`_is_aggregate_root` detects on `component-catalog.md` (the unique aggregate artifact —
`architecture.md` is shared with the single-component tier). See
`references/system-synthesis-contract.md`.

## v15.0.0 — per-lang aggregate layout / DOCUMENT-MAP removal

`build_navigation.py` no longer writes `docs/DOCUMENT-MAP.md` or `docs/DOCUMENT-MAP.draft.md` (was
write-only; no reader; machine state lives in `docs/.rebuild-state.json`). `META_FILES` still
recognizes both names so migration deletes any stale copies on next run. In per-lang mode the
top-level `docs/README.md` collapses to a ~3-line pointer to `docs/<primary>/README.md`; the whole
`components/` container relocates to `docs/<primary>/components/`. See `docs/decisions/ADR-0001`.

## v13.1.0 — top-level reading-order `docs/README.md` index (additive)

The navigation pass (`build_navigation.py`) writes a top-level `docs/README.md` "Documentation Index —
Reading Order" landing page — for the primary root AND every `docs/<lang>/` mirror (`--lang`).
Per-language labels, a "Read by role" guide (new-dev / reviewer / PM number-paths), per-layer intros,
and an ordered 4-layer table of concrete one-line descriptions render deterministically (no LLM);
absent artifacts (and the role-path numbers pointing at them) are pruned; 2-zone user tail preserved.
Prose lives in per-language locale modules (`_nav_strings_<lang>.py`); structure + role number-paths in
`_nav_strings.py`; the renderer in `_nav_index.py`.

## v13.0.0 — BREAKING CHANGE (system layer: language-mapped + richer)

`--aggregate` now writes the system layer to the **language-mapped** docs root — `docs/system/` for an
en single-lang repo (byte-identical, no change) but `docs/<primary>/system/` for a per-lang project,
with `primary_lang` discovered by majority across the component `.rebuild-state.json` files (conflict →
majority + `[WARN] lang_conflict`; `--primary-lang` overrides). A flat legacy tree on a per-lang project
is auto-migrated (`migrate_docs_layout`) before writing — no orphaned flat copy. The artifact set is
recut (red-team): `interaction-graph.md` gains a Mermaid topology + fan-in/out summary + self-loop note;
`canonical-entity-model.md` is replaced by `data-ownership-map.md` (ownership + correlation + event
producer→consumers); and `system-overview.md`, `system-glossary.md`, `cross-service-flows.md` are
**hybrid** — Python writes `<name>.draft.md` (idempotent; unfilled markers → `[WARN]
unfilled_scaffold`), a narrative-fill agent completes the prose, then the orchestrator promotes to
`<name>.md` after the post-fill validator passes. See `references/system-synthesis-contract.md`.

## v12.0.0 — BREAKING CHANGE (system-of-systems / multi-component)

The run model gains a multi-component shape for monorepo / polyglot microservice repos: **per-sub-repo
run + one root synthesis pass**, instead of a single root run. `detect_stack_profile.py` now ALSO emits
`components[]` (additive — `recommended_profile` is unchanged, so single-repo callers do not break); a
stateless driver `--batch <manifest>` processes one component per invocation; `--aggregate <root>`
synthesizes the system layer (v12 used `service-catalog.md`, `interaction-graph.md`, … — v16 uses
v16-parity names) over the per-component neutral digests. BREAKING is in the multi-component RUN MODEL
(new flags + the per-component `docs/components/<name>/` layout), NOT in the `detect` output shape.
Single-repo runs (no `--root`/`--batch`/`--aggregate`) are unchanged. See
`references/system-synthesis-contract.md`.

## v11.0.0 — BREAKING CHANGE (stack-profile layer)

Preflight no longer hard-aborts on a missing web manifest. A **stack-profile** (data file under
`references/stack-profiles/*.json`) declares detection globs, source encoding, artifact map, and probe
behavior; legacy non-web stacks (Delphi, Oracle PL/SQL) now run. No profile match → AskUserQuestion
(pick / generic / abort), never auto-abort. **State migration (RT-F4):** `.rebuild-state.json` carries
`schema_version`; resuming a pre-11.0.0 state invalidates the preflight checkpoint and re-runs
`detect_stack_profile.py` + profile-resolve before continuing the wave graph. A pass interrupted under
≤10.x re-runs preflight.

## v5.0.0 — BREAKING CHANGE (CORE-only default)

Default run now produces CORE artifacts only (no feature specs, process-flows, or glossary). Use
`--feature-specs`, `--flows`, `--glossary` standalone passes for those outputs. `--features F###` is
redefined as a scoped subset of `--feature-specs` (was: default-pipeline W6 narrowing). Migration: run
core pass first, then the new passes in order.

## v4.0.0 — per-feature 4-file specs

Per-feature specs split into 4 audience-aware files; `docs/system/architecture.md` and
`docs/generated/permissions-matrix.md` are generated/promoted; process-flows synthesized at FL.1 with an
FL.2 liveness validator (historical numbering: W6.8 / W6.85).
