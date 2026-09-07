---
name: tkm:rebuild-spec
description: "Reverse-engineer an existing codebase into structured documentation — 11 core doc artifacts (architecture, data models, API specs, flows, etc.) plus per-feature specs (2 files/feature), process-flows, and glossary synthesis via separate standalone passes. Uses parallel agents: scanner, researcher, reviewer, doc-writer."
argument-hint: "[--feature-specs] [--features F001,..] [--flows] [--glossary] [--test-cases] [--overview] [--api-doc] [--package] [--html] [--migrate] [--only <step>]"
metadata:
  author: takumi-agent-kit
  version: "28.3.0"
module: documentation-knowledge
triggers: ["document existing codebase", "reverse engineer", "spec from code", "what does this code do"]
---

# tkm:rebuild-spec

Reverse-engineer existing codebase → structured spec artifacts by composing existing skills.
Zero third-party CLI dependencies. Output lands in layered `docs/` paths (system/, generated/, flows/, features/).

**`--html`:** after the markdown artifacts are written, also render a self-contained editorial HTML companion
of the run's primary overview (the architecture / spec summary) next to its markdown — same stem, `.html` —
using [`../_shared/references/editorial-report-html.md`](../_shared/references/editorial-report-html.md). The
markdown docs stay primary; the HTML is a readable single-file view, not a replacement.

**Version history & breaking-change migration notes:** see [`CHANGELOG.md`](./CHANGELOG.md).


**Principles:** YAGNI, KISS, DRY | Compose, don't reinvent | Template-first.

## Usage

<!-- layout-exempt: usage block — all docs/ paths are rebuild-spec's own output targets -->
```
/tkm:rebuild-spec                         # Incremental if .rebuild-state.json present; full otherwise. Reconcile preflight; auto-resume. Produces CORE artifacts only (v5.0.0+). Knowledge Graph ON by default (incl. the disable path): see Preflight step 5.
/tkm:rebuild-spec --full                  # Force full rebuild ignoring state. Alone → core artifacts; combined with a pass flag → that pass ignores its cursor and regenerates all outputs.
/tkm:rebuild-spec --since abc123          # Override diff base SHA (custom incremental starting point)
/tkm:rebuild-spec --dry-run               # Print planner decision JSON to stdout; no file writes
/tkm:rebuild-spec --feature-specs         # Standalone pass: generate/refresh all per-feature specs (2 files/feature).
/tkm:rebuild-spec --features F001,F002    # Scoped subset of --feature-specs pass (warn + proceed). Was: default-pipeline W6 narrowing.
/tkm:rebuild-spec --flows                 # Standalone pass: synthesize process-flows.
/tkm:rebuild-spec --glossary              # Standalone pass: synthesize glossary.
/tkm:rebuild-spec --test-cases            # Standalone pass: derive UT/IT/UAT test-case lists per feature.
/tkm:rebuild-spec --screen-specs          # Standalone pass: generate screen specs.
/tkm:rebuild-spec --api-contracts         # Standalone pass: synthesize API contracts (REST/GraphQL/gRPC). Off by default.
/tkm:rebuild-spec --overview              # Standalone pass: client-facing System Overview (.md + styled .docx) from promoted docs/.
/tkm:rebuild-spec --api-doc               # Standalone pass: client-facing Sun* API Design .xlsx (BM-2-901-52).
/tkm:rebuild-spec --artifact route-list   # Regenerate single core artifact (reuses upstream if present)
/tkm:rebuild-spec --resume                # Reconcile-only: sync TaskList against disk, close stale in_progress tasks whose outputs already exist. No new work dispatched.
/tkm:rebuild-spec --probe-routes          # Explicit Wave 0.4 bootability gate: AskUserQuestion → Tier-1 CLI probe → write _route-probe.json sidecar used by W1 route-list. Auto-triggered when lockfile present; this flag forces the gate even if no lockfile found.
/tkm:rebuild-spec --legacy                # RE preset for legacy non-web (Delphi/Oracle): bootable=false + RE output contract + profile extractors. Additive over the resolved profile.
/tkm:rebuild-spec --lang vi               # First run: vi becomes PRIMARY, generated inline at docs/vi/. Later run: translates from primary.
/tkm:rebuild-spec --lang jp               # jp de-aliases to ja. Adding the first secondary flips an en-primary repo docs/ → docs/en/, then translates → docs/ja/ (skeleton-identity + ±LOC gates).
/tkm:rebuild-spec --migrate                # Version-upgrade backfill over an EXISTING corpus
/tkm:rebuild-spec --migrate --dry-run      # Per-step pending counts; writes nothing
/tkm:rebuild-spec --migrate --only a3-screens # One step; refuses an unmet prerequisite
```

**`--migrate` flag composition:** see its row in `references/flag-reference.md`.

**Multi-component runbook (monorepo / polyglot microservices):** when running across multiple sub-repos
(`--root` / `--batch` / `--aggregate` / `--emit-manifest`) — OR when a plain single run **auto-switches**
(Preflight 2.5: `detectJson.auto_switch == true` on a one-spec-per-unit multi-executable repo) — the full
driver loop (Steps 0–3 incl. the per-pass auto-loop), the Product-group / Reused sub-root gates, the
Shared-layer pre-pass, the narrative-fill contract, and the multi-component flag table all live in
[`references/multi-component-runbook.md`](./references/multi-component-runbook.md) — loaded on-demand (see
"On-demand pipeline loading"). **A genuinely single-component repo** (no `component_profile` → `auto_switch=false`,
or `--mono`) **ignores this entirely** — run `/tkm:rebuild-spec` as before.

**End-of-pass handoff (authoritative):** Every pass ends by printing its own "Pass-completion
handoff prompt" — defined in that pass's reference file, not here. Each handoff includes an optional
`/ask-expert` review line (e.g.
`/ask-expert "Is the core architecture & data-model documentation accurate and complete?"`) before
the next-pass guidance. When printing the handoff, reproduce the canonical block from the pass file
verbatim — never regenerate it. Handoff sources: core → `references/pipeline-w7-w9.md`;
feature-specs → `references/pipeline-feature-specs.md`; flows & glossary →
`references/pipeline-flows-glossary.md`; test-cases → `references/pipeline-test-cases.md`;
api-contracts → `references/pipeline-api-contracts.md`; screen-specs →
`references/pipeline-screen-specs.md`; overview → `references/overview-pass.md`; api-doc →
`references/api-pass.md`.

### Pass ordering & prerequisites

Single source of truth for the pass dependency chain. Each pass preflight ABORTs (see
its reference file) if its prerequisite is missing.

<!-- layout-exempt: pass dependency table — docs/ paths are rebuild-spec's own output targets and prerequisites -->
| Pass | Prerequisite (must exist) | Produced by |
|------|---------------------------|-------------|
| core | source code | — |
| `--feature-specs` | `docs/generated/feature-list.md` | core |
| `--flows` | `docs/features/*/technical-spec.md` + `docs/generated/entities.md` | feature-specs + core |
| `--glossary` | `docs/features/*/functional-spec.md` + `docs/generated/entities.md` | feature-specs + core |
| `--test-cases` | `docs/features/*/technical-spec.md` (+ `functional-spec.md` § 8 Edge Cases, promoted alongside) | feature-specs + core |
| `--api-contracts` | `docs/generated/route-list.md` + `entities.md` + `api-map.md` + `docs/system/permissions.md` | core (parallel-safe w/ others) |
| `--screen-specs` | `docs/generated/screen-list.md` | core (parallel-safe w/ others) |
| `--overview` | `docs/generated/feature-list.md` (+ optional system/, flows/, features/ enrichment) | core (presentation pass — re-shapes promoted docs/) |
| `--api-doc` | `docs/generated/route-list.md` (swagger/api-map/api-contracts optional enrichment) | core (deliverable pass — independent of `--api-contracts`) |

**Force restart:** delete `plans/<active>/artifacts/` → next no-args invocation starts fresh.

**`--artifact route-list` and probe manifest:** When re-running `--artifact route-list` after a prior probe (status `passed` or `skipped`), the orchestrator reuses the existing `_route-probe.json` sidecar without re-prompting. The probe gate is only re-issued when `probe_gate.status == "awaiting_user"` (resumed from halt) or when `--full` is combined with a bootable stack or `--probe-routes` flag. This ensures the Tier-1 manifest enriches W1 route-list even on partial re-runs.

## Preflight

1. Detect project root = CWD (must be under git control).
2. **Stack-profile detection (v11.0.0 — ask-don't-abort).** Verify the working tree is non-empty
   (empty → ABORT with clear hint), then resolve a stack-profile rather than demanding a web manifest:
   ```
   const r = bash(`.claude/skills/.venv/bin/python3 \
     claude/skills/rebuild-spec/scripts/detect_stack_profile.py --root .`)
   if (r.exitCode === 2) { /* corrupt KIT profile — fatal, not a project condition */
     throw new Error("rebuild-spec: stack-profile load failed — fix the kit profile:\n" + r.stderr) }
   const detectJson = JSON.parse(r.stdout)  // exit 0 for every detection outcome incl. no-match
   ```
   - **≥1 profile matched** → use `detectJson.recommended_profile` (highest hits). Multiple matches →
     keep the `[MULTI_STACK]` annotation built from `detectJson.matched[]`; note it. A matched
     `web-js-ts` profile reproduces the prior web behavior exactly (regression-free).
   - **No profile matched** → do NOT abort. Behavior depends on interactivity:
     - Interactive → **`AskUserQuestion`** with three options: (a) pick a profile manually from
       `references/stack-profiles/`, (b) "treat as generic source" → `generic-source` profile, (c) abort.
       - **Tier-2 sniff sub-branch (Phase 09, Track D accept-path).** Tier 0/1 leaves the 3-option flow
         above completely unchanged. Only when `detectJson.ui_sniff.tier == 2` (cited, structurally-
         corroborated UI evidence) does a 4th option — **(d) "investigate as CLI/TUI"** — get added, with
         its untrusted-citation handling, `_ui_sniff_accept_lib.py` accept-path, and decline fall-through.
         Full procedure: load [`references/tier2-ui-sniff-accept.md`](./references/tier2-ui-sniff-accept.md).
     - **Non-interactive** (`--non-interactive` flag OR `REBUILD_NON_INTERACTIVE=1`) → apply
       `generic-source`, print `[WARN] non_interactive_fallback`, do NOT prompt, do NOT run any
       stack-specific extractor. If `detectJson.ui_sniff.tier == 2`, ADDITIONALLY print
       `[WARN] ui_sniff_tier2` with the cited signals (advisory log line only) — still NEVER prompts and
       NEVER invokes `_ui_sniff_accept_lib` (the accept-path digest is never built non-interactively).
   - Record the resolved `profile_id` + `detectJson.encoding` + `detectJson.detected_language_heading`;
     pass them to Wave 0.5 (`build_session_context.py --profile-id <id> --encoding <enc>`). Honor any
     `detectJson.warnings` (`file_cap_reached` → result partial; `encoding_unverified` → advisory;
     `component_group:` → a co-deployed frontend+backend product — see the **Product-group gate** in
     `references/multi-component-runbook.md`; on a single-component run it is advisory only).
2.2. **State-schema gate (ADVISORY).** Read `detectJson.state_staleness.stale` — computed by
   step 2's `detect_stack_profile.py` run above, so no semver arithmetic belongs here. `true` →
   the checkpoint in `docs/.rebuild-state.json` was stamped under an older profile schema than
   this code expects. Report it (`found` vs `required` are both in the block) and continue; step 2
   has already re-resolved the profile from scratch this run, so the fresh `detectJson` is
   authoritative either way.
   **Scope, stated honestly:** no stack profile is persisted to `.rebuild-state.json` — it carries
   no `profile_id`, encoding, or `screen_source` key (see `references/incremental-state-schema.md`),
   and step 2 re-detects unconditionally on every run. So this gate has nothing to invalidate on the
   single-component path; it is a signal, not a trigger. The one profile artifact that IS reused
   across runs is `.rebuild-components.json`, and step 2.5 governs its reuse unconditionally without
   consulting this flag. Do NOT write prose here describing an invalidation this gate does not
   perform. `probe_gate` is untouched. `false` → resume from the checkpoint as normal.
2.5. **Multi-component auto-switch (v22.0.0).** A plain single run over a multi-executable repo
   (e.g. a Delphi repo with 20 `.dpr` under `PG/<MODULE>/` + shared `Common/` + a `DB/` tree) must
   NOT flatten every module into one mono doc set. The detector reports this via `detectJson.auto_switch`.
   - **IF** `detectJson.auto_switch === true` **AND** the user did NOT pass `--root <subrepo>` **AND**
     `.rebuild-components.json` does not already exist (idempotency — a prior run already switched):
     ```
     [INFO] multi-component detected ({detectJson.auto_switch_reason}): switching to --emit-manifest flow. Use --mono to override.
     ```
     Then proceed **as if the multi-component flags were set** — load `references/multi-component-runbook.md`
     and run the driver loop from Step 0 (`--emit-manifest` → `--batch` → `--aggregate`). The detector
     already emitted the component manifest + shared sidecar shapes; the runbook's Shared-layer pre-pass
     (Step 0.4) consumes `detectJson.shared`.
   - **ELSE** continue the legacy single-repo path below (steps 3–4).
   - `--mono` forces `auto_switch=false` at the detector (escape hatch — treat the repo as one
     monolithic component). `--root <subrepo>` is an explicit single-component scope and never auto-switches.
     `--profile <id>` pins the authoritative profile when Delphi+Oracle co-detect (sets `component_profile`).
   - **Idempotency:** if `.rebuild-components.json` already exists, load it and resume — do NOT re-detect/re-switch.
3. Resolve active plan path from `## Plan Context` hook; if none, fallback to `plans/<timestamp>-rebuild-spec/`.
3.5. **Bootstrap detection (v2.x upgrade):** If `.rebuild-state.json` absent AND `docs/specs/system-overview.md` or `feature-list.md` present AND `git log -1 -- docs/specs/` returns a SHA ≠ HEAD → prompt user to bootstrap state from git history or force full rebuild. See `references/pipeline.md` § Wave -2.
4. Ensure output dirs exist: `docs/system/`, `docs/generated/`, `docs/flows/`, `docs/features/`, `plans/<active>/artifacts/`.  <!-- layout-exempt: preflight step 4 — output dirs are this skill's own targets -->
5. **[GRAPHIFY-INTEGRATION] Knowledge Graph — ON BY DEFAULT, runs BEFORE Wave 0.** Always run exactly ONE command to build/refresh the graph (idempotent; lazily installs `graphifyy` into the kit venv if missing, (re)indexes the repo, updates `.gitignore` — all CODE-enforced). The script self-gates on config `graphify.enabled` (default true) and no-ops when disabled, so it is safe to run every time:
   ```
   .claude/skills/.venv/bin/python3 .claude/skills/rebuild-spec/scripts/graph_preflight.py
   ```
   (If the kit venv python is unavailable, use `python3`.) **When graphify is disabled** (config `graphify.enabled=false`, or env `GRAPHIFY_DISABLE=1` / `REBUILD_NO_GRAPH=1`) the script no-ops — no graph is built, nothing is installed, and every downstream wave behaves byte-identically to vanilla. It prints one status line; on any failure it degrades to "no graph" (vanilla). *(Note: PyPI package is `graphifyy` with double-y; module/command is `graphify`.)* When a graph results, downstream waves use it automatically:
   - **Wave 0 is REPLACED for $0**: `scripts/graph_to_scout.py` generates a contract-complete `scout-report.md` straight from `graph.json` (file inventory + BL grep), so the LLM scout subagent (the most expensive discovery step, 1-3M tokens) is skipped entirely — see `references/pipeline-w0-w5.md` Wave 0 block.
   - **W1 starts from machine-true drafts**: `scripts/graph_to_drafts.py` emits `_graph-drafts/{data-model,architecture}-draft.md` (class inventory with file:line + inherits; module-level Mermaid import graph) so those researchers verify & complete instead of building structure from scratch (best-effort; missing drafts → researchers work from templates as before).
   - **Post-promote coverage proof**: `scripts/graph_spec_coverage.py` (advisory, never blocks) machine-verifies the promoted spec against graph ground truth — every model class in code appears in `entities.md`, every route file in `route-list.md` — see `references/pipeline-w7-w9.md`.
   - The shared `_session-context.md` (built by `scripts/build_session_context.py`) emits graphify-first guidance gated on `graphify-out/graph.json` (suppressed when `REBUILD_NO_GRAPH=1`).
   No graph → behavior is byte-identical to vanilla. Output contract is unchanged in all cases: same 11 artifacts, same templates, same quality gates and reviewer checklist.

## Pipeline

Load on demand (not inlined here):
- `references/pipeline.md` — wave graph + always-loaded core. Load on-demand: pipeline-w0-w5.md, pipeline-dispatch-and-gates.md, pipeline-w5x-w6.md, pipeline-w7-w9.md, pipeline-screen-specs.md, pipeline-feature-specs.md, pipeline-flows-glossary.md
- `references/pipeline-dispatch-and-gates.md` — shared `profile`/`produce()` binding, Wave 0.6 structural extraction, and the canonical Renumber+Contiguity Gate. Loaded with pipeline-w0-w5.md (and any pass that applies the canonical gate).
- `references/artifact-sharding.md` — descriptor table, merge recipe, fragment contract, ID contiguity gate (renumber + validate after every sharded merge). Loaded when pre-gen estimate exceeds threshold for any artifact.
- `references/code-formats.md` — shared schema; pass to researcher
- `references/verification-checklist-universal.md` — universal rules + Pending Marker Rule (always load with any checklist file)
- `references/verification-checklist-core-artifacts.md` — W7a: 11 core artifact sections + Composite Detection + Failure Trap
- `references/verification-checklist-feature-spec.md` — FS.5: FeatureSpec + Deterministic Validator Coverage + Failure Trap
- `references/verification-checklist-screen-spec.md` — SS.2: ScreenSpec + Composite Detection + Failure Trap
- `references/verification-checklist-quality-gates.md` — W4.5 / W5.6 targeted gates only

### On-demand pipeline loading
Always, before any dispatch and regardless of flags: Read `references/flag-reference.md` (flag-override semantics — flags resolve before any flag-gated reference loads) AND `references/pipeline.md` (wave dep graph + the run-wide invariants and incremental orchestration below).
Before dispatching W0–W5: Read `references/pipeline-w0-w5.md` AND `references/pipeline-dispatch-and-gates.md` (the latter binds `profile`/`produce()` + defines the canonical Renumber+Contiguity Gate the task chain applies by name).
Before dispatching W5.5 (feature existence gate): Read `references/pipeline-w5x-w6.md`.
Before dispatching W7a/W7.5/W8/W9 (core review/fix/promote): Read `references/pipeline-w7-w9.md`.
When `--feature-specs` or `--features` flag is set: Read `references/pipeline-feature-specs.md`.
When `--flows` flag is set: Read `references/pipeline-flows-glossary.md`.
When `--glossary` flag is set: Read `references/pipeline-flows-glossary.md`.
When `--test-cases` flag is set: Read `references/pipeline-test-cases.md`.
When `--api-contracts` flag is set: Read `references/pipeline-api-contracts.md`.
When `--screen-specs` flag is set: Read `references/pipeline-screen-specs.md`.
When `--overview` flag is set: Read `references/overview-pass.md`.
When `--api-doc` flag is set: Read `references/api-pass.md`.
When `--package` flag is set: Read `references/pipeline-package.md`.
When any multi-component flag is set (`--root` / `--batch` / `--aggregate` / `--emit-manifest` /
`--manifest` / `--digest-collect` / `--primary-lang` / `--force-aggregate`) **OR when
`detectJson.auto_switch === true` (Preflight 2.5 — a plain flagless run that auto-switches)**: Read
`references/multi-component-runbook.md` (driver loop + Product-group/Reused gates + the **v19
scanner-only** flow — `--aggregate` emits ONLY `.system-scout-report.md` (FACTS data, no Mermaid) +
`per-component-confidence.md` and creates NO documents; the **system-researcher** then CREATES the 6
`<name>.draft.md` from `templates/aggregate/` + the scout report + each component's docs, authoring
the prose, **tables, AND Mermaid** (drawing charts from scout edges + docs-derived `[UNVERIFIED]`
edges, safe labels) per `references/system-researcher-contract.md` (never declaring a read-available
component "unobserved") + the **aggregate review→fix-cycle→promote gate** (Step 3.5 — a W7a-style
`reviewer` pass over the 6 authored artifacts against
`references/verification-checklist-system-synthesis.md`, `SY-R1..R8`, + a mechanical Mermaid-safety
lint) + the multi-component flag table).
When `--artifact <NAME>` is set: Read `references/artifact-wave-lookup.md`.
When `--migrate` flag is set: Read `references/pipeline-migrate.md`.
When `--lang <code>` targets a secondary language (translate path): Read `references/pipeline-translate.md`.
**[lang-sync-fix] ALSO read `references/pipeline-translate.md` on ANY primary pass when `docs/.rebuild-state.json` has a non-empty `translations` object** — primary passes run `translation_sync_gate.py` (plan + finalize) in their post-promote steps, echo the finalize stdout `Secondary languages:` line VERBATIM in their completion handoff, and MUST run `check_translation_gate.py --pass <name>` before writing the completion flag (exit 1 blocks completion). Without loading pipeline-translate.md, the invocation contract is missing and secondary mirrors silently stay primary-only. Check: `translations = JSON.parse(readFile("docs/.rebuild-state.json")).translations ?? {}`; if `Object.keys(translations).length > 0`, load the file before the pass's promote step.

Composite screen detection is automatic. See `references/composite-screen-detection.md` for the H1-H6 rules, execution order, 2-of-3 gate, tab short-circuit, and wizard sub-classification.

BehaviorLogic stability enforced via scout BL inventory (Wave 0) + 1-BL-per-file cardinality contract (Wave 2b) + reviewer cardinality cross-check (Wave 7a). See `references/bl-source-patterns.md`.

**A1 confidence-report companions (v25.2.0):** every promoted artifact across ALL passes — core, feature-specs, screen-specs, flows, glossary, api-contracts, and system-synthesis (aggregate) — gets a `confidence-report_<stem>.md` sidecar, deterministically derived from the artifact's own inline citations/markers (`scripts/derive_confidence_report.py` — no LLM, best-effort, never gates a pass). System-synthesis companions additionally carry a `--limitation-note synthesis` header caveat (their citation density is structurally lower — not comparable to per-feature scores). Advisory and internal-only, like `.nav-metadata.json` — excluded from `--overview`/doc-writer export. See `references/confidence-report-contract.md`.

**A3 Source Walkthrough (v26.0.0, BREAKING; B4 DB Impact per Event retired from
technical-spec.md in v27.8.0):** two required sections technical-spec.md used to carry
alongside screen-spec.md; B4 and the technical-spec.md side of A3 retired in v27.8.0
when the action-thread reshape (`--only action-thread`) absorbed both into § 2 Action
Index + per-action `Source` rung. **A3 stays fully live on the screen-spec side**
(`screens/*/spec.md`, via the `a3-screens` migrate step). Original two-section shape,
retirement rationale, the `REQUIRED_H2_TECH_THREAD` degradation-window note, and the
A1-stat `**File:**` citation rule: `references/pipeline-migrate.md` § A3 Source
Walkthrough — original shape and retirement.

**Default flow (no flags) — CORE artifacts only.** Wave DAG + per-wave dispatch bodies live in the
on-demand refs (always-loaded `references/pipeline.md` § Waves; `references/pipeline-w0-w5.md` for
W0–W5 + gates; `references/pipeline-w5x-w6.md` for W5.5/W5.6; `references/pipeline-w7-w9.md` for
review/fix/promote). Ordered shape:

0. **Profile manifest** — print produce/skip map; every `skip`-mapped wave's task + gate is NOT dispatched (`pipeline-w0-w5.md` § "Profile-driven dispatch").
1. **W0** scout → **W0.6** structural extraction (only when `profile.extractors` non-empty) → **W0.4** route probe (only when `profile.probe.bootable`) → **W0.5** `_session-context.md`.
2. **W1–W5** researcher chain (`blockedBy` per dep graph), with halt gates: **W1.5** DataModel, **W1.1** RouteList, **W2a.1** ScreenList, **W4.5** UserStories, **W5.5** existence, **W5.6** FeatureList.
3. **W7a** reviewer (11 core artifacts, parallel w/ W5 completion) → **W7.5** structural-fixer → **W8** fix fan-out (`REBUILD_W8_MAX_PARALLEL`; ≤`MAX_FIX_CYCLES=3`) → **W9** promote (`promote_drafts.py` + W9.5 reverse-index + `wave9-complete.flag` + Core Pass-completion handoff).

**Review zone (W7a-core):** LLM semantic checks on 11 core artifacts. **Pre-fix zone (W7.5):** deterministic structural safety net.

<!-- layout-exempt: standalone passes — docs/ paths are rebuild-spec's own input/output targets -->
**Standalone passes (separate invocations — NOT part of the default flow):**
- **`--feature-specs`:** FS.1–FS.7 fan-out, per-feature 2-file specs. See `references/pipeline-feature-specs.md`.
- **`--flows`:** FL.1–FL.5 process-flow synthesis. See `references/pipeline-flows-glossary.md`.
- **`--glossary`:** GL.1–GL.3 glossary synthesis. See `references/pipeline-flows-glossary.md`.
- **`--test-cases`:** TC.1–TC.5 per-feature UT/IT/UAT test-case lists (`docs/features/{slug}/test-cases.md`, 3rd SIDECAR file). An EXPAND-DETAILS pass over the already-cited `technical-spec.md`/`functional-spec.md` § 8 Edge Cases — fan-out shape identical to FS.1. See `references/pipeline-test-cases.md`.
- **`--screen-specs`:** SS.1–SS.3 screen specs. See `references/pipeline-screen-specs.md`.
- **`--overview`:** OV.1–OV.4 client-facing System Overview deliverable (`docs/<ProjectName>_System_Overview.md` + `.docx`). Presentation pass — re-shapes promoted `docs/`, never reads source. See `references/overview-pass.md`.
- **`--api-doc`:** Sun* API Design workbook (`docs/api/<System> - API Design.xlsx`, BM-2-901-52) via bundled-template clone + deterministic lint (B1) + optional LLM semantic review (B2). Distinct from `--api-contracts`. See `references/api-pass.md`.
- **`--package`:** EXPORT-tier offline client HTML bundle at `client-package/<ProjectName>/` — deterministic,
  `file://`-openable with networking disabled, vendored UMD mermaid, denylist + XSS-sanitizer boundaries.
  Requires `docs/generated/feature-list.md`. See `references/pipeline-package.md`.


**`--migrate` step order (`STEP_ORDER`, `_doc_migration_registry_lib.py`) — 7 steps, each step's prerequisite is the one before it (`audience-split` → `a3-screens` → `screen-sot` → `feature-sot` → `cap-map` → `action-thread` → `mirror-skew`). Full table with per-step Writes and A1-refresh membership: `references/pipeline-migrate.md` § Step order.**

`cap-map` and `action-thread` are the only two steps with `--rollback` implemented.
Rollback mechanics, the `_TECH_SPEC_STEPS` A1-refresh membership (`action-thread` is in
it, `cap-map` is not), and the WARN-first old-shape degradation contract: see
`references/pipeline-migrate.md` § Step-order table — rollback, degradation, and
`_TECH_SPEC_STEPS` notes.

**`action-thread`'s one-command UX (v27.8.0):** `--migrate --only action-thread`
composes AND fills every pending feature's rule ownership in one idempotent command —
re-running it never duplicates work. Full behavior: `references/pipeline-migrate.md` §
`action-thread`'s one-command UX.

Full contract, including the newest steps' pending predicate, `needs_llm_fill`→INERT→exit-4
contract, the researcher fill pass, and `cap-map`/`action-thread`'s rollback: `references/pipeline-migrate.md`.

## Subagent contracts

**Core pass subagents:**

| Wave | Subagent | Input | Output |
|------|----------|-------|--------|
| 0 | `/tkm:scan-codebase` | target dirs | `plans/<active>/artifacts/scout-report.md` |
| 0.4 | orchestrator (AskUserQuestion + probe_routes.py) | bootable lockfiles + `probe_gate` state | `_route-probe.json` sidecar + `probe_gate` in `.rebuild-state.json`; HALTS on `awaiting_user` |
| 0.5 | orchestrator (scripts) | scout-report.md + stackNote | `_session-context.md` + `_scout-bl-inventory.md` |
| 1–5 | `researcher` | scout report + template + `code-formats.md` | `plans/<active>/artifacts/<artifact>.md` |
| 1.1 | orchestrator (`validate_route_list.py`) | `route-list.md` | `validation-summary.json`; HALTS before W2 on critical |
| 1.5 | `reviewer` | `data-model.md` only | `data-model-review.md` (frontmatter: `passed`, `issues`, `warnings`); halts W2 on critical |
| 2a.1 | orchestrator (`validate_screen_list.py`) | `screen-list.md` | `validation-summary.json`; HALTS before W2b/W3 on critical |
| 4.5 | `reviewer` | `user-stories.md` only | `user-stories-review.md` (frontmatter: `passed`, `issues`, `warnings`); halts W5 on critical |
| 5.6 | `reviewer` | `feature-list.md` + US### headers + SCR### index | `feature-list-review.md` (frontmatter: `passed`, `issues`, `warnings`); halts core review on critical |
| 7a | `reviewer` | 11 core artifacts + `_scout-bl-inventory.md` + `verification-checklist-core-artifacts.md` | `core-review-report.md` → merged into `review-report.md` + `TaskUpdate(status=completed)` |
| 7.5 | orchestrator (`structural_fixer.py`) | core artifacts + review-report.md | fixed artifacts + `structural-fix-report.json` + decremented review-report |
| 8 | `implementer` | review-report.md + affected core drafts | updated drafts |
| 9 | `promote_drafts.py` + `doc-writer` | approved core drafts | layered paths per `docs-canonical-mapping.md` + `_promoted-sha256.txt` + `wave9-complete.flag`; calls `TaskUpdate(status=completed)` |

**Feature-specs / flows / glossary / test-cases pass subagents** — full per-wave contract tables live in their pass references (loaded on flag, per "On-demand pipeline loading"): `references/pipeline-feature-specs.md` (FS.1–FS.7), `references/pipeline-flows-glossary.md` (FL.1–FL.5 flows + GL.1–GL.3 glossary), `references/pipeline-test-cases.md` (TC.1–TC.5 test-cases).

**Screen-specs pass subagents (`--screen-specs`; see `references/pipeline-screen-specs.md`):**

| Wave | Subagent | Input | Output |
|------|----------|-------|--------|
| SS.1 | `researcher` (5/batch, batches wave-chained ≤5; standalone) | screen-list.md + data-model.md + screen-spec-template.md + contract | `plans/<active>/artifacts/screens/SCR###_Name/spec.md` |
| SS.2 | `reviewer` (5/batch, batches wave-chained ≤5; standalone) | ScreenSpec batches + `verification-checklist-screen-spec.md` | `screen-review-batch-NN.md` + `TaskUpdate(status=completed)` |

All subagents read `_session-context.md` first; only artifact-specific reads listed in Input column happen afterward.

## Task management

A plan file outlives the session; a task does not. So hydrate each wave as a chain
of tasks, and keep anything that must survive in the plan file.
Where the Task tools are missing — the VSCode extension, for one — fall back to `TodoWrite`.
See `references/pipeline-w0-w5.md` for `TaskCreate` examples.

## Resume & Reconcile

Three defenses against mid-pipeline context loss: (1) **Self-closing subagents** (FS.1, FL.1, GL.1,
TC.1, W7a, W9) call `TaskUpdate(status=completed)` before returning. (2) **Completion
sentinels** — `wave9-complete.flag` (core), `fs7-complete.flag` (feature-specs),
`flows-complete.flag` (flows), `glossary-complete.flag` (glossary), `test-cases-complete.flag`
(test-cases, F9 — `expectedOutput` = per-feature `docs/features/{slug}/test-cases.md`)
are disk-level truth per pass. (3) **Reconcile preflight** — on every invocation, closes
`in_progress` tasks whose expected output already exists on disk. For Wave 9 (core): checks flag OR
all core docs promoted (no feature dirs required — v5.0.0). `--resume` runs preflight only. For FS.1
per-feature tasks, reconcile checks 2-file completeness + no `.pending`; partial output stays
`in_progress`.
See `references/pipeline.md` → "Reconcile pattern" for `TaskList`/`TaskUpdate` examples.

## Edge Cases

- **Run-wide invariants and incremental-mode orchestration have moved** to the always-loaded `references/pipeline.md` (§ Invariants — every pass, every flag; § Incremental orchestration): route-probe halt + `probe_gate` persistence, W5.5 validator halt, empty-codebase ABORT, scaffold-only "No data", 0-F### behavior, reviewer 3-cycle escalation, subagent timeout, session-exhaustion reconcile, empty cascade, v2.x bootstrap, `--full`/`--since` exclusivity, Wave -1 hydrate, and the five incremental dispatch/fallback rules incl. OOB-edit semantics.
- **Orphan `.pending` marker** → FS.1 partial: 2-file write incomplete OR researcher did not remove the marker on success. FS.5 emits `MISSING` for that fcode, FS.7 pre-flight gate blocks promotion. Recovery: rerun FS.1 for the affected fcode OR (after manually verifying both files are complete) remove `.pending` and rerun FS.5. See `references/canonical-fcode-schema.md § Folder Lifecycle` + `references/verification-checklist-universal.md § Pending Marker Rule`.
- **PASS one-liner format** — reviewer reports use `✓ <rule_id> @ <fcode>` line format under `## Passed Checks`. W7-merge rolls up consecutive same-rule fcodes into ranges.
- **A1 confidence-report companion absent (v25.2.0, non-gating):** `incremental_planner.py`'s `_detect_confidence_report_missing()` scans core/feature/screen artifacts on every planner invocation, alongside (but structurally independent of) the OOB-edit scan below — a primary artifact present on disk whose `confidence-report_<stem>.md` sidecar is missing (pre-A1 corpus, or a prior best-effort write failure) prints `[CONFIDENCE_REPORT_MISSING] <artifact path>` to stderr. Unlike `[OUT_OF_BAND_EDIT]`, this NEVER feeds `_build_payload()` and NEVER triggers a fallback-to-full — print-only, zero effect on mode/exit code. See `references/confidence-report-contract.md`.
- **A3 absent on an un-migrated screen spec (v26.0.0, WARN-first; B4 retired from technical-spec.md in v27.8.0):** `validate_reading_guide_db_impact.py` (wired at FS.2) WARNs `reading_guide.pre_migration` on any technical-spec.md or screen spec.md missing `## Source Walkthrough`, and exits 0 — never blocks a build. For a screen spec, run `/tkm:rebuild-spec --migrate --only a3-screens` to enumerate and scaffold what still needs a researcher re-run (it cannot backfill the content itself). `db_impact.*` (the B4 rule family) and its `check_db_impact` check retired this release — `FeatureSpec.retired_section_present` now flags a technical-spec.md still carrying either retired heading instead.
- **Language-adaptive scanning scope**: Wave 0 scout detects project language from manifest files and outputs flat file inventory + scanned dirs. Wave 2 follows imports one level deep using language-specific mechanisms (see `references/pipeline-w0-w5.md` W2 task for full rules). Reviewer cross-validates via scout-report.md inventory — no hardcoded extension globs. Pure UI/presentational components with no service calls are automatically compliant.
<!-- DO NOT RELOCATE the bullets below. Each is a global invariant with no always-loaded owner: composite-screen-detection.md (screen partition) and confidence-report-contract.md (A1) are read on core W2 / flag-gated passes but are NOT among the four always-loaded files (pipeline.md, code-formats.md, verification-checklist-universal.md, _shared/docs-canonical-mapping.md). Moving them to a flag-gated file would silently unenforce them whenever that flag is absent. The W7-merge rollup in the PASS one-liner bullet has no owner anywhere. See plan 260825-1359 Phase 05. -->
- **REG### scoping**: every REG must have parent SCR in same ScreenList. Orphan REG (no parent SCR) → critical.
- **REG nesting**: forbidden. REG inside REG → critical.
- **Partial-screen ownership**: F### with SCR###/REG### ref owns REG only, not the parent SCR. Screen shell must be owned by a separate F### with bare SCR### ref.
- **Region independence signals**: REG### is justified by any ≥1 of — distinct API endpoint (read or write), independent loading state, independent scroll container, independent auth / permission gate, distinct business workflow, distinct mutation surface / API cluster (distinct write endpoints or POST/PUT/DELETE namespace — even if the initial GET payload is shared), distinct validation / action path. Shared initial payload alone does NOT disqualify a split (see verification-checklist Trap 1 + Trap 3).
- **Feature specs (v27.0.0 audience split; v27.7.0 action-thread reshape — see
  `docs/decisions/ADR-0006.md` for rationale):** `functional-spec.md` (BA/QA audience, 13 numbered
  H2 sections) and `technical-spec.md` (Dev/QA/SA audience, ACTION-first spine: Technical Overview →
  Action Index → Actions → Shared Foundation → Verification & Technical Notes). **Both shapes are
  defined by their templates — author from `templates/functional-spec-template.md` and
  `templates/technical-spec-template.md`, never from this summary.** Every code (FR/BR/SM/DEC) is
  stated ONCE in `functional-spec.md` and implemented ONCE in `technical-spec.md` — neither is a
  derived view of the other (ADR-0004). `### 5.5 Artifact References` replaces the legacy standalone
  `## Artifact References` H2 — CRITICAL immediately on the legacy shape once past the `*_pre_sot`
  degradation window (see `--migrate` step `feature-sot`). **Validator shape acceptance (repointed
  in 27.7.0 phase 10):** `FeatureSpec.required_sections` accepts EITHER the action-thread shape
  (`REQUIRED_H2_TECH_THREAD`) OR the legacy 5-bucket shape (`_LEGACY_TECH_H2_5BUCKET`, the
  `feature-sot` migrate step's own output — a real intermediate a repo may sit in before running the
  `action-thread` step), firing critical only when a file matches NEITHER. Author to the TARGET
  shape above regardless.
- **Decision Logic (DEC-###, v3.2.4+; reshaped v27.7.0):** `DEC-###` is a 5-column table row inline in the gating action's
  `**Rule**` rung in `technical-spec.md § 3. Actions` (row shape:
  `templates/technical-spec-template.md`) — captures user-facing decisions with
  business-outcome scope (source-location-agnostic: component, saga, controller all valid Sources).
  3 subtypes: `render`, `interaction`, `flow`. The 1-sentence business-outcome justification lives
  in `functional-spec.md § 5` instead of a per-DEC field. Structural correctness is enforced by
  `validate_feature_spec.py` under `FeatureSpec.dec_blocks_well_formed`/`dec_lazy_na` for BOTH
  shapes: the pre-thread H4-block scan and a second independent table-row scan (`_dec_row_findings`)
  validating the 5-column shape under those same two rule_ids. W7h reviewer rule covers semantic
  validation.
- **DISC-### scope (v3.2.4+ updated D6):** DISC-### is for enum discriminators only — ≥2 distinct values with different behavioral outcomes. Boolean fields (`true`/`false` only) belong in Business Rules, NOT DISC. On per-feature `technical-spec.md § 4.2`, `validate_feature_spec.py` **warns** on boolean DISC entries; the separate W1.5 gate on `data-model.md` treats the same shape as **critical** (`references/pipeline-w0-w5.md` Check 2) — different artifacts, deliberately different severities (`FeatureSpec.disc_boolean`). Clean boundary: multi-value enum → DISC; boolean flag → BR; multi-predicate / interaction / flow → DEC.
- **Output language — first run sets primary (v5.1.0):** `--lang vi` on a fresh repo → vi IS the primary, generated inline from source (no "run English first" step). A later `--lang jp` translates FROM vi. The primary language is recorded in `state.primary_lang` (set once, first run). Default (no `--lang`) → primary=en. Dispatch: `eff_lang == primary_lang` → inline generation (Path A); else → translate-from-primary (Path B). **Location is mode-aware** (v10, via `resolve_docs_root`): single-lang en-primary → `docs/` root; per-lang (≥1 secondary registered, or the `docs/<primary>/.layout-migrated` sentinel present) → `docs/<lang>/` for every language incl. the primary. The first secondary on an en-primary-at-root repo triggers a one-time atomic flip `docs/` → `docs/en/` (`migrate_docs_layout.py`). English skeleton (headings, code tokens, field labels, table headers, fenced code, frontmatter) preserved in ALL languages so existing validators run unchanged.
- **Translation behavior (auto-sync, both `--lang` guards, skeleton-identity gate, Haiku worker, the rebuild-spec-only scope carve-out):** see `references/pipeline-translate.md` — loaded on `--lang` AND, per `[lang-sync-fix]` above, on ANY primary pass with a non-empty `state.translations`. The kit-wide carve-out is in the always-loaded `_shared/docs-canonical-mapping.md` § Language Layout.

### GLOBAL PARALLEL CAP
- **GLOBAL PARALLEL CAP (v25.1.0, hardened v25.1.1):** `REBUILD_MAX_PARALLEL` (default 5) — never
  more than 5 subagents runnable at once, across the ENTIRE flow and every pass (core,
  feature-specs, screen-specs, flows, test-cases TC.1, translate, aggregate, fix cycles).
  Enforcement pattern = **bounded-wave dispatch**: whenever a pass creates more than 5 sibling
  tasks, chunk them into waves of ≤`REBUILD_MAX_PARALLEL` and chain each wave on ALL task ids of the
  previous wave via `addBlockedBy`. This env IS read by the wave-rotation pseudocode
  (FS.1/FS.5/SS.1/SS.2, aggregate) — wave width is always
  `min(<per-pass batch env>, REBUILD_MAX_PARALLEL)`, so raising a batch-size env (workload per
  agent) can never widen concurrency past the cap. Do not raise `REBUILD_MAX_PARALLEL` above 5
  without also verifying rate-limit headroom. Core Wave 1 additionally chains Wave1.c db-objects
  behind Wave1.b crud-matrix so legacy profiles (6 Wave-1 artifacts) stay ≤5.
- **FS.1 fan-out** → `REBUILD_FS_BATCH_SIZE` (default 5; legacy `REBUILD_W6_BATCH_SIZE` a deprecated alias). Chained-wave formula and the >20-F### batching rule: `references/pipeline-feature-specs.md` (FS.1).
- **W8 parallel cap:** `REBUILD_W8_MAX_PARALLEL=5`, clamped to `min(REBUILD_W8_MAX_PARALLEL, REBUILD_MAX_PARALLEL)` in W8/FS.6/FL.4 — fix cycles are NOT exempt. See `references/pipeline-w7-w9.md`.
- **Shard parallel cap:** `REBUILD_SHARD_MAX_PARALLEL=5`, clamped by the global cap in AC.1. See `references/artifact-sharding.md`.
- **Action-chunk threshold (v27.7.0):** `REBUILD_ACTION_CHUNK_THRESHOLD=15` — the action-count gate `scripts/decide_action_chunking.py` reads to choose single-pass vs chunked-by-capability generation. See `references/verification-checklist-feature-spec.md`.
- **Env hygiene (v25.1.2):** every cap env parse guards junk values — `Math.max(1, parseInt(env ?? '5') || 5)` — so NaN/`0`/negative degrades to the default instead of silently disabling wave rotation (a broken env must never mean unbounded fan-out).

## Output

<!-- layout-exempt: output section — all docs/ paths are rebuild-spec's own promote targets -->
- Persistent:
  - `docs/system/{overview,architecture,glossary,permissions}.md` — curated
  - `docs/generated/{route-list,api-map,permissions-matrix,entities,user-stories,feature-list,behavior-logic}.md` — raw (behavior-logic.md absorbs the former per-rule curated system doc's content, v27.0.0 — see ADR-0004)
  - `docs/generated/{crud-matrix,db-objects}.md` — extractor-digest-derived (stack-specific; produced when the profile's `extractors` run — Delphi/Oracle). CRUD matrix = feature×table C/R/U/D; DB-object catalog = tables/views/procs/sequences/triggers.
  - `docs/flows/<slug>.md` — AI-drafted cross-feature flows
  - `docs/features/<slug>/{functional-spec,technical-spec}.md` — per feature (2 files, v27.0.0 audience split)
  - `docs/generated/traceability-matrix.md` — F###-keyed ID thread (v27.11.0, `--pass-complete` re-projection; conditional)
  - `docs/decisions/ADR-*.md` — human only
- Drafts + reports: `plans/<active-plan>/artifacts/` (kept for audit).
- **Navigation layer (v11.2.0, updated v15.0.0; v24.0.0 extends to feature-/screen-specs):** at the END of
  a completed pass the orchestrator runs `scripts/build_navigation.py --pass-complete` — **every** pass that
  writes to `docs/` (core W9.6, **feature-specs FS.7, screen-specs SS.3**, and per-lang mirrors via translate
  Step 3.5), so the just-promoted `features/F###/` + `screens/SCR###/` dirs immediately surface in the
  reading-order README, the per-feature READMEs, and the features index → a `README.md` per `docs/` subdir (2-zone: only the
  region between `<!-- generated by rebuild-spec navigation -->` and `<!-- end-generated -->` is
  rewritten; user content below `end-generated` is preserved). **Root README behavior (v18.0.0):** in
  per-lang mode there is **no top-level `docs/README.md`** — a purely-generated root README is removed
  and a hand-written one is left untouched; the single entry point is `docs/<primary>/README.md`
  (was a ~3-line pointer in v15-v17). Single-lang behavior is unchanged. **DOCUMENT-MAP
  removed (v15.0.0):** `build_navigation.py` no longer writes `docs/DOCUMENT-MAP.md` or
  `docs/DOCUMENT-MAP.draft.md` (was write-only; no reader; machine state lives in `docs/.rebuild-state.json`).
  `META_FILES` still recognizes both names so migration deletes any stale copies on next run. `--pass-complete`
  is retained as an accepted no-op argument for backward compatibility. **Per-lang `components/` placement (v23.0.0 — single-source translate model):**
  component docs are written ONCE to the language-resolved source root: `docs/components/<name>/`
  for en single-lang; `docs/<primary>/components/<name>/` for non-en or per-lang repos.
  `resolve_component_paths` passes `primary_lang` to `resolve_docs_root` — the same resolver used
  by core/system artifacts. Secondary-lang component docs (`docs/<L>/components/<name>/`) are
  produced by the translation pipeline (`--lang <L> --root <name>`) and auto-synced on change;
  there is NO derived-view projection. The nav pass generates READMEs at the resolved component
  path. All writes go through `_resolve_guarded` (RT-F14). See `docs/decisions/ADR-0003`.
- **Navigability + diagrams (v27.11.0-v27.13.0):** `build_navigation.py` also renders a `## Document Map`
  4-bucket crosswalk (Requirements/External Design/Internal Design/Test Spec) into the SAME generated
  README zone, presence-driven; `scripts/build_traceability_matrix.py` emits the F###-keyed matrix
  (re-projection only — run after any pass that changes SCR/US/BL/ROUTE/PERM/TC membership; all
  optional passes now re-invoke nav themselves). Templates gain three A3 diagram companions —
  process-flow `### Trigger Sequence` (EXPECTED, WARN if absent), screen-spec and technical-spec
  `Data Flow` (BEST-EFFORT) — and `architecture.md` gains `## Deployment View` (merged infra+network
  flowchart from repo IaC, mandatory honesty label, `N/A` + WARN when no IaC). All WARN-first: no new
  hard gate, no `REQUIRED_H2_*` change, no forced migration.
- Journal: auto-invoke `/tkm:write-journal` on completion (optional — skip silently if skill unavailable).

## References

Full catalog (load on demand by reference name/topic): [`references/reference-index.md`](./references/reference-index.md).
Always read: `references/flag-reference.md` (flag-override semantics — flags resolve first) · `references/pipeline.md` (wave dep graph + run-wide invariants + incremental orchestration) · `references/code-formats.md`
(F###/US###/SCR###/BL###/PERM### schema) · `references/verification-checklist-universal.md`
(universal validator rules) · canonical docs mapping `claude/skills/_shared/docs-canonical-mapping.md`
(topic → file ownership, stub rule, surgical-edit policy).
