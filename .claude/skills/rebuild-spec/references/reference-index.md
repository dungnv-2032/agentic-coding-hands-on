<!-- layout-exempt: rebuild-spec reference index — docs/ paths named here are this skill's own targets -->
# Reference Index

Full catalog of `rebuild-spec`'s reference files, moved here from `SKILL.md`'s `## References`
section (phase-13, `plans/260818-1332-rebuild-spec-human-readable-sot`) to keep `SKILL.md` under
`tests/validate-skills.py`'s 500-line CI gate. Nothing here changed meaning by moving — load this
file when hunting a specific reference by topic; `SKILL.md` keeps only the handful of
always-relevant entries inline (see its `## References` pointer).

- `references/stack-profiles/_schema.md` — stack-profile data schema (detection globs, source encoding, artifact map, extractor allowlist, trust boundary). `scripts/detect_stack_profile.py` + `scripts/_stack_profile_lib.py` load/match/validate; preflight resolves a profile here (ask-don't-abort).
- `references/multi-component-runbook.md` — multi-component / system-of-systems **runbook**: the `--emit-manifest`→`--batch`→`--aggregate` driver loop (incl. Step 1b per-pass auto-loop), the Product-group / Reused sub-root gates, the v18 scout-report→template→author flow (Step 3) + the review→fix→promote gate (Step 3.5), and the multi-component flag table (`--root`/`--batch`/`--aggregate`/`--emit-manifest`/`--manifest`/`--primary-lang`/`--force-aggregate`/`--digest-collect`). Load when any multi-component flag is set. Synthesis internals live in `system-synthesis-contract.md`.
- `references/system-synthesis-contract.md` — system-of-systems synthesis: neutral-digest schema, per-stack adapter convention (`scripts/_topology_adapter_{spring,nestjs,go}.py` + `extract_service_topology.py`), entity-correlation algorithm (independent heuristic, all-`[UNVERIFIED]` + consent gate, glossary as OUTPUT), Markdown-sanitize + Mermaid-injection + config credential-scrub gates, language-mapped output path + auto-migration, the v19 **scanner-only scout-report→author→review→promote** contract (Python emits FACTS data only — no Mermaid, no documents; the system-researcher CREATES the drafts and authors prose+tables+Mermaid after reading each component's docs; fidelity via review gate + a Mermaid-safety lint), run model (`--emit-manifest`/`--batch`/`--aggregate`, `_components_manifest_lib.py` atomic+lock). Synthesis: `scripts/synthesize_system.py` (+ `_system_synthesis_lib.py`, `_synthesis_scout_lib.py`, `_synthesis_render_lib.py`, `_synthesis_narrative_lib.py`, `_nav_metadata_lib.py`).
- `references/system-researcher-contract.md` — the **system-researcher** authoring contract (v18): inputs (scout report + templates + each component's docs), the 6 authored artifacts, the **[CRITICAL] read-the-components'-docs / never-declare-"unobserved"-blind** rule (`SY-R8`), fidelity rules (embed pinned `{{SCOUT}}` blocks verbatim), wording rubric, and reuse/update behaviour. Injected into the Step 3 researcher prompt.
- `references/verification-checklist-system-synthesis.md` — semantic review rules (`SY-R1..SY-R7`) for the aggregate review stage (Step 3.5): loaded ONLY by the `reviewer` that gates the 5 hybrid artifacts (overview / component-catalog / architecture / glossary / cross-service-flows) before promote. Mechanical artifacts are not reviewed.
- `references/re-output-contract.md` — RE-mode provenance contract (citation-mandatory + `[UNVERIFIED]` + citation-density check); active when `profile.re_contract` or `--legacy`. `scripts/build_navigation.py` (README per dir; v15.0.0: DOCUMENT-MAP generation removed) + `scripts/_path_lib.py` (`_resolve_guarded`, shared write-safety). `validate_source_citations.py --re-mode` runs the density check.
- `references/structural-extractor-contract.md` — Wave 0.6 structural-extractor plug-point: digest schema, `extract_sql_schema.py`/`extract_data_flow.py` (+ `_sql_parse_lib.py`/`_sql_dml_lib.py`/`_extractor_lib.py`), credential scrub (RT-F7), parse-coverage/dynamic-SQL (RT-F8), regex safety (RT-F9), identifier sanitize (RT-F10), checkpoint/manifest/stale (RT-F11). Drives `crud-matrix.md` + `db-objects.md`; validators `validate_crud_matrix.py` + `validate_db_catalog.py`.
- `references/code-formats.md` — F###/US###/SCR###/BL###/PERM### schema + valid criteria
- `references/verification-checklist-universal.md` — universal rules + Pending Marker Rule
- `references/verification-checklist-core-artifacts.md` — W7a core artifact rules (11 artifacts + Composite Detection)
- `references/verification-checklist-feature-spec.md` — FS.5 feature spec rules (Deterministic Validator Coverage + Failure Trap)
- `references/verification-checklist-screen-spec.md` — SS.2 screen spec rules
- `references/verification-checklist-quality-gates.md` — W4.5 / W5.6 targeted gates
- `references/pipeline.md` — wave dep graph, wave -2/planner/branch-on-mode, reconcile pattern, artifact paths (always loaded)
- `references/pipeline-w0-w5.md` — W0–W5 dispatch bodies (load before W0–W5)
- `references/pipeline-w5x-w6.md` — W5.5 feature existence gate + W5.6 FeatureList quality gate (load before those waves)
- `references/pipeline-w7-w9.md` — W7a/W7.5/W8/W9 core review/fix/promote dispatch bodies (load before those waves)
- `references/pipeline-feature-specs.md` — Feature-specs pass FS.1–FS.7 (load when `--feature-specs` or `--features` flag set)
- `references/pipeline-flows-glossary.md` — Flows pass FL.1–FL.5 + Glossary pass GL.1–GL.3 (load when `--flows` or `--glossary` flag set)
- `references/pipeline-test-cases.md` — Test-cases pass TC.1–TC.5 (load when `--test-cases` flag set); `references/test-cases-researcher-contract.md` — TC.1 mandatory rules (UT/IT vs UAT citation-source split); `references/verification-checklist-test-cases.md` — TC.3 semantic rules (TC-S1..TC-S6)
- `references/pipeline-screen-specs.md` — Screen-Specs pass SS.1–SS.3 (load when `--screen-specs` flag set)
- `references/feature-spec-researcher-contract.md` — FS.1 mandatory rules; `references/bl-source-patterns.md` — per-stack BL file patterns (10 stacks incl. systemd-timer, Mode A+B)
- `references/spec-authoring-contract.md` — takumi greenfield spec authoring rules (draft frontmatter, authoring-mode inputs, gap schema, screen-spec scope, state-registration handoff)
- `references/spec-stage-procedure.md` — shared Stage 1.5 spec-authoring orchestration; consumed by takumi Stage 1.5 + tkm-plan spec gate. Step 0: enumerate-first scope assessment — (B) CLOSED conjunction smell-flag (ALWAYS-fire → force SYSTEM; NEVER-fire CRUD pairs → enumerate; gray zone → enumerate) then (A) intent enumeration (count ≥2 → SYSTEM default; =1 → SINGLE; `--fast` → always SINGLE). Emits `plans/<plan_dir>/spec/.intent-enum.json` as chokepoint artifact. Steps 0a–0b: feature-list draft + quality gate (SYSTEM only). Rest Point 1.5a: confirm feature set (BLOCKING incl. `--auto`). Steps 1–2.5: slug resolution, researcher fan-out, shape verification. Step 3: gap clarification + approval gate.
- `references/process-flow-researcher-contract.md` — FL.1 process-flow synthesis contract
- `references/canonical-fcode-schema.md` — fcode JSON schema + slug grammar + folder lifecycle; `references/incremental-state-schema.md` — state/index/plan JSON schemas
- `scripts/incremental_planner.py` — cascade-aware incremental planner (decision oracle for selective dispatch)
- `scripts/build_source_to_fcode.py` — per-pass reverse-index + state emitter; `--cursor` arg controls which state cursor is advanced (core: `last_rebuild_sha`; feature-specs: `last_feature_spec_run_sha`; flows: `last_flows_run_sha`; glossary: `last_glossary_run_sha`; test-cases: `last_test_cases_run_sha`)
- `references/pipeline-translate.md` — Translate pass TR.0–TR.5 + auto-sync entry. Auto-sync now driven by `scripts/translation_sync_gate.py` (plan + finalize modes); handoff line emitted by script, not LLM. Load when `--lang` targets a secondary language, OR on any primary pass when `translations` in state is non-empty — see On-demand pipeline loading.
- `references/translation-contract.md` — Subagent rules for prose-only translation with skeleton preservation
- `scripts/validate_translation_skeleton.py` — Skeleton-identity + ±LOC body-ratio validator for translation mirrors
- `scripts/_lang_lib.py` — Language resolution helpers (`normalize_lang` w/ ISO alias de-aliasing, `resolve_docs_root` mode-aware, `detect_layout_mode`, `looks_unusual`)
- `scripts/migrate_docs_layout.py` — one-time single-lang→per-lang docs flip (`docs/`→`docs/<primary>/`), atomic+idempotent (sentinel + lock); `--rollback`, `--rename-alias jp:ja`
- `scripts/check_layout_paths.py` — recurring guard: fails on hardcoded `docs/system|features|generated|flows` without a `layout-exempt` annotation
- `agents/translator.md` — Haiku-bound prose-only translation worker (TR.2/TR.3/auto-sync)
- `scripts/` — deterministic validators (`validate_feature_existence.py`, `validate_feature_spec.py`, `validate_source_citations.py`, `validate_process_flow.py`, `validate_feature_screen_link.py` — v24 feature↔screen ID-link, WARN-capable, `validate_feature_api_link.py` — v25 feature↔API/route ID-link + twin-consistency, WARN-capable); shared libs (`_slug_lib.py`, `_summary_lib.py`, `_layout_lib.py`, `_nav_table_parse_lib.py`, `_route_link_lib.py`, `_nav_route_lib.py`); migration: `migrate-behavior-logic-rename.py`, `migrate_docs_layout.py`, `migrate-feature-screen-ids.py` (v24 SCR###-column + Feature backlink), `migrate-feature-api-ids.py` (v25 ROUTE###-column + Owner F### backfill); stdlib-only, no pip
- Canonical docs mapping: `claude/skills/_shared/docs-canonical-mapping.md` — single source of truth for topic → file ownership, stub rule, surgical-edit policy

## New in this plan (`plans/260818-1332-rebuild-spec-human-readable-sot`) — human-readable SOT reshape

- `references/pipeline-migrate.md` — the `--migrate` pipeline reference; also documents the two
  newest steps below (`screen-sot`, `feature-sot`) alongside the pre-existing `audience-split` /
  `a3-screens` / `mirror-skew`. (**`a3-b4` was listed here until v27.8.0 retired the step** —
  A3/B4 left `technical-spec.md` and its guard machinery was rescoped to the screens family as
  `_a3_fill_guard_lib.py` / `_a3_citation_target_lib.py`. See `docs/decisions/ADR-0007.md`. Read
  `_doc_migration_registry_lib.STEP_ORDER` for the live chain — this index is prose, not the
  source of truth.)
- `scripts/_screen_sot_compose_lib.py` (+ sibling `_screen_sot_{sections,elements,actions,table,appendix,extract}_lib.py`) — the sole composer for the screen-spec SOT target order (10 numbered §§ + `## Technical Appendix`); driven by the `screen-sot` registry step, `scripts/_doc_migration_screen_sot_step_lib.py`.
- `scripts/_feature_sot_functional_lib.py` / `scripts/_feature_sot_technical_lib.py` — the sole composers for the functional-spec (13 §§) and technical-spec (5-bucket) SOT target orders; driven by the `feature-sot` registry step, `scripts/_doc_migration_feature_sot_step_lib.py`.
- `references/confidence-report-contract.md` — carries the `[EXPECTED]` marker's `△` mapping (§ Derivation rules) alongside the pre-existing three markers.
- `references/verification-checklist-screen-spec.md` § Degradation contract (`screen.sot_pre_sot`) — the screen-spec WARN-first rule for a still-pre-SOT-shaped spec.
- `scripts/validate_feature_spec.py` (`func.sections_pre_sot`, `FeatureSpec.tech_sections_pre_sot`) — the functional-/technical-spec WARN-first rules for a still-pre-SOT-shaped feature pair.


## Previously unindexed (reconciled by scripted diff, v27.10.0)

Every `.md` under `references/` now has an entry; verified by diffing the on-disk set against this file rather than by comparing counts. Hand-maintained — an automated drift check is a candidate follow-up.

- `references/api-contract-researcher-contract.md` — the **api-contract-researcher** authoring contract for the `--api-contracts` pass (AC.1)
- `references/api-contract-source-patterns.md` — per-stack REST/GraphQL/gRPC source signals for API-contract extraction (non-exhaustive; `[SIGNAL_INFERRED]` fallback)
- `references/api-pass.md` — `--api-doc` pass: client-facing Sun* API Design `.xlsx` (BM-2-901-52) via template clone + lint (B1) + optional semantic review (B2)
- `references/artifact-sharding.md` — pre-gen LOC estimate → shell/fan-out/merge sharding, `REBUILD_SHARD_MAX_PARALLEL` batching (clamped by the global cap)
- `references/artifact-wave-lookup.md` — `--artifact NAME` → wave + upstream-required lookup table (loaded on `--artifact` only)
- `references/composite-screen-detection.md` — H1–H6 composite-screen rules, execution order, 2-of-3 gate, tab short-circuit, wizard sub-classification, REG### wave scoping
- `references/flag-reference.md` — flag-override semantics for every flag (**always read** — flags resolve before any flag-gated reference loads)
- `references/migration-audience-split.md` — the v26→v27 `audience-split` migrate step: functional/technical spec split mechanics
- `references/overview-pass.md` — `--overview` pass: client-facing System Overview (`.md` + styled `.docx`), 11-section structure, token-leak gate
- `references/pipeline-package.md` — `--package` pass: offline `file://` client HTML bundle (`client-package/<ProjectName>/`), denylist + XSS sanitizer boundaries, vendored UMD mermaid
- `references/pipeline-api-contracts.md` — AC.1 dispatch bodies for the `--api-contracts` pass (load on that flag)
- `references/pipeline-dispatch-and-gates.md` — binds `profile`/`produce()` and defines the canonical Renumber + Contiguity gate (load with W0–W5)
- `references/screen-spec-researcher-contract.md` — the **screen-spec researcher** authoring contract (SS.1), incl. the `[EXPECTED]` marker rules
- `references/spec-state-registration.md` — `docs/.rebuild-state.json` registration recipe for promoted specs
- `references/tier2-ui-sniff-accept.md` — Tier-2 UI sniff acceptance criteria for screen detection
- `references/user-stories-ipe-protocol.md` — US### IPE (inference-provenance-evidence) protocol for the W4 user-stories artifact
- `references/verification-checklist-flows.md` — semantic review rules for the `--flows` pass (FL.3)
- `references/verification-checklist-glossary.md` — semantic review rules for the `--glossary` pass (GL.2)
