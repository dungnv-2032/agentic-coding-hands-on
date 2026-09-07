# Changelog — `audit-synthesis-judgment`

All notable changes to this skill. Versioning follows the kit convention (semver in SKILL.md `metadata.version`).

## 2.0.0 — 2026-08-26

**BREAKING.** rebuild-spec 28.0.0 retires its `--design-intent` pass. This skill audited that
pass's artifact as one of its four scopes; with the artifact gone, the axis is removed rather than
left as guarded dead weight.

### Removed

- **`--scope design-intent`.** Gone from all four CLIs — `locate_synthesis_artifacts.py`,
  `coverage_engine.py`, `judgment_engine.py`, `estimate_judgment_run.py`. It is no longer a
  tolerated value: argparse now **exits 2 with an error**, it does not silently degrade. The skill
  takes **three artifact scopes** (`feature-list`, `user-stories`, `system`) plus `all`, down from
  four. A new `scripts/tests/test_scope_choices_parity.py` pins all four CLIs to the same
  `choices` tuple by `ast` inspection plus a live exit-2 probe, so the four can never drift apart
  again.
- **Engine 3's `restates-w/o-why` dimension and its `RESTATES` verdict — end to end.** Not
  deprecated, removed: `_extract_restatement_candidates` read only artifacts with
  `kind == "design-intent"`, so with that artifact gone the dimension could never produce a
  candidate. Leaving the verdict in the taxonomy would document an outcome the tool can never
  emit. Engine 3 now judges **four** dimensions (was five): `inference-validity`, `naming`,
  `granularity`, `capability-intent`.
- **The `experimental` WARN-cap path.** `_severity(dimension, text, experimental)` loses its third
  parameter. Worth stating plainly: **the cap was already inert.** `_severity` accepted the flag
  and never read it, and Engine 3 is WARN-only for every dimension regardless (Iron Law #1), so
  the cap's only real effect was a suffix on the report. Removing it changes no severity any run
  would have produced.
- **Iron Law #7** ("NEVER emit a FAIL for a design-intent finding") — it guarded a pass that no
  longer exists, and Iron Law #1 already forbids any non-Engine-1 FAIL.

### Kept

- **`inference-validity` survives.** Its user-story branch — the `so that {benefit}` clause — is
  independent of the removed artifact; only the `[INFERRED]`-tag branch, which read
  design-intent.md exclusively, goes with it.
- Every other engine and degradation contract is unchanged.
- **Not** unchanged, and easy to miss: retiring the locator's design-intent chain also
  dropped `locate()`'s `ambiguities` output-schema key and the refuse-to-guess-a-plan-dir
  contract it carried, and left `--plan-dir` accepted-but-ignored by `locate()` (it stays
  live for Engine 1's plan-dir validator subset). No surviving consumer read any of the
  three, so nothing breaks — but the `### Removed` list above is not exhaustive without
  them.

### Tests

126 -> 131 passing. The removal deletes design-intent cases and net-adds the four-way `choices`
parity suite.

## 1.1.0 — 2026-08-19

### Added

- **Engine 3's fifth dimension: `capability-intent` (`CAP_MULTI_INTENT`).** Judges whether a
  single § 2 `functional-spec.md` CAP row claiming `>= 3` user stories really represents ONE
  primary business outcome, or several bundled under one capability row (the judgment half of
  rebuild-spec's deterministic `cap.analysis_required`/`cap.review_advised` checks, which can only
  ask "was a decision recorded?", never "was it the right one?"). Anchored to the Python-computed
  US-title set (§ 2 + § 7 headings) — the `**Single-capability rationale:**` line, when present, is
  placed in the candidate's judge-visible `text` as evidence only, **never** in the anchor (Iron
  Law #2) and **never** in the new `severity_text` field.
- **`_feature_metrics` re-axised to `max(US claimed by any single § 2 CAP row)`** (this
  changelog's first entry for that work — the granularity axis had gone quiet on a real 66-feature
  corpus under the old per-feature-length metric). `functional-spec.md` registered in
  `_SCOPE_ARTIFACTS`; new `scripts/_cap_map_lib.py` is this skill's sanctioned second § 2 parser,
  pinned to rebuild-spec's `_cap_table_lib` by `tests/test_cap_map_lib_parity.py` — extended this
  release with `cap_rows`, `section7_us_titles`, and `single_capability_rationale` for the new
  dimension, still the ONE § 2 reading this skill performs.
- **`severity_text` (SA-4): severity is Python-composed, never a keyword scan over judge-visible
  prose the audited party authored.** `_severity()` now scans `cand.get("severity_text") or
  cand.get("text", "")` — the four pre-existing dimensions set no `severity_text`, so their
  behaviour is byte-identical to before. `capability-intent` sets it to the CAP row's claimed
  `FR-###`/`BR-###`/`SCR###` codes plus their matching declaration line from the twin
  `technical-spec.md`, so an author cannot deflate an auth capability's severity by writing bland
  prose, nor inflate a settings capability's by mentioning a blast-radius word in its rationale.
- **`capability_intent_status`/`capability_intent_note` (FM-5), mirroring `granularity_status`
  exactly** — `"OK"`/`"SKIPPED"`, same note-carries-reason-and-path convention. `"SKIPPED"` when no
  located § 2 row claims any US at all (the half-migrated state), distinguishing it from a
  well-partitioned corpus where every row legitimately falls under the `>= 3` threshold. Surfaced
  in `assemble_judgment_report.py` beside `granularity_note`; `_result()` stays untouched — Engine
  3 never influences the overall verdict.
- **Known coverage gap recorded, not silently accepted:** candidate selection is US-keyed, so
  `type=background` features (CAP rows claiming `BL###` instead of `US###`) are entirely outside
  `capability-intent`'s reach — documented in `references/judgment-rubric.md` rather than left to
  read as full coverage.
- Measured on the phase 07b filled reference corpus (66 features, 151 CAP rows): granularity found
  2 coarse outliers (median 1.0, MAD 0.0); capability-intent found exactly 10 CAP rows claiming
  `>= 3` US (F015, F018, F020, F022, F030, F031, F033, F035, F036, F048) and, judged against the
  rubric question, endorsed all ten as single-outcome (0 `CAP_MULTI_INTENT` findings) — a valid
  clean result, not a dead backstop: a planted fixture (one CAP row bundling sign-in, password
  reset, account deletion, data export, and billing history under a rationale that PASSES
  rebuild-spec's own three deterministic conditions) proves the dimension fires when the bundle
  really does span unrelated outcomes.

## 1.0.0 — 2026-07-21

### Added

- **The fourth audit axis for rebuild-spec's synthesis tier — judgment soundness.** Not coverage
  (A1 confidence-report), not truth (audit-doc-parity, which its Iron Law #6 forbids from grading a
  judgment), but whether the feature partition is well-drawn, the user-story enumeration sound, the
  inferred "why" a valid inference, and the artifact set complete + non-redundant. Report-only;
  emits `judgment-report.md` with machine-readable PASS/FAIL frontmatter.
- **Three engines layered by objectivity:**
  - **Engine 1 — deterministic coverage (the ONLY FAIL source).** `coverage_engine.py` +
    `_graph_state_lib` (absent/empty/partial/stale classification) + `_coverage_orphan_lib`
    (code-level orphans, symbol-level materiality, empty-index guard) + `_coverage_phantom_lib`
    (citation→graph-node resolution, graph-completeness gated) + `_redundancy_lib` (literal
    duplicate-artifact FAIL only). Advisory roll-up of an enumerated validator subset. Loud
    `coverage_status` — a no-graph / core-only / partial-graph run degrades to UNVERIFIABLE, never a
    silent PASS. `--strict-coverage` turns a missing graph on a `graphable` stack into a hard FAIL.
  - **Engine 2 — protocol-conformance boundary check (WARN).** `boundary_conformance.py` +
    `_ipe_parse_lib` + `_ipe_conformance_lib`. Parses the promoted `user-stories.md` and audits
    conformance to the per-stack IPE Step-3 merge rule + Step-4 anti-CRUD rule — catching the
    86-vs-354 over/under-merge deterministically, citing the violated clause. No re-synthesis.
  - **Engine 3 — adversarial judgment residue (WARN).** `judgment_engine.py` (`prepare`/`assemble`)
    + `_granularity_lib` (MAD outlier stat with a mean-AD fallback). LLM judges on inference
    validity (Toulmin), naming, granularity, and "restates w/o added why"; no finding stands without
    surviving a ≥2-refuter majority refutation pass (single-pass only at `--level low`). design-intent
    findings WARN-capped (EXPERIMENTAL upstream).
- **Load-bearing invariant:** every FAIL/WARN anchors to a computed signal; FAIL is Engine-1
  deterministic computation alone — a stochastic Engine-2/3 signal never increments a FAIL count.
- **Prompt-injection defense** (`references/prompt-injection-defense.md`): scanned doc/code prose is
  inert DATA; Engine-3 judge/refuter output is schema-constrained so an injected `<!-- SYSTEM: … -->`
  cannot change a verdict (tested).
- **`--plan-dir`** locates an un-promoted `design-intent.md`; the locator refuses to guess when the
  flag is absent and multiple candidate plan dirs exist.
- Wired **optional / non-blocking / off-by-default** into five rebuild-spec pass handoffs
  (`pipeline-w7-w9`, `pipeline-feature-specs`, `pipeline-flows-glossary`, `pipeline-jobs`,
  `pipeline-design-intent`). Core-pass advisory points at `--scope user-stories` with a timing note
  (code-level coverage needs `--feature-specs` first).

### Notes

- **`_citation_lib.py` is COPIED from `audit-doc-parity`** (not imported) so this skill is
  self-contained / independently installable — `audit-doc-parity` may not be present, whereas
  `rebuild-spec` (whose output this audits) always is. The copy still resolves `rebuild-spec`'s
  `_lang_lib` as a sibling for layout-aware docs-root resolution. A test asserts the copied
  `CITATION_RE` matches parity's behavior; keep the two in sync when parity's citation/path-guard
  logic changes.
- Added a `graphable: true|false` field to the five stack-profile JSONs (`web-js-ts`,
  `generic-source` → true; `cobol`, `delphi-vcl`, `oracle-plsql` → false) — consumed by
  `--strict-coverage`.
