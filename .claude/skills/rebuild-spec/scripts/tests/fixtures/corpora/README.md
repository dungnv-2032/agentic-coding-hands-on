# Committed corpus fixtures — provenance and shape index

Built by phase-00 of `plans/260819-1016-rebuild-spec-capability-map`. These replace a
hardcoded `/tmp/<session-uuid>/...` scratch path that `test_run_doc_migrations_cli.py`
used to depend on — a path that disappears on any other machine, in CI, or once `/tmp`
is cleared, at which point a file-level `pytestmark = pytest.mark.skipif(...)` quietly
turned 23 "load-bearing" tests into 23 skips while the suite still reported green.
These fixtures are committed to git: they cannot vanish, so they cannot silently
convert a real assertion into a skip.

10 feature dirs total, across three families below (the phase's own cap is ≤10).

## Derivation

`pristine-small` and `post-small` are trimmed, real-corpus derivatives: 3 feature dirs
(`F001_Auth`, `F005_MarketplaceCreation`, `F051_TransactionStateMachine` — the last one
`type=background`, satisfying Requirement 2's "one `type=background` feature with BL
codes" shape on its own) plus 3 screen dirs (`SCR001_Homepage`, `SCR020_LoginPage`,
`SCR021_SignupPage`), copied from a previous session's `st-pristine`/`st-post` scratch
corpora (themselves full copies of a real client corpus — see "Security scrub" below).
Every pending/composed count these fixtures produce was **measured by actually running
`run_doc_migrations.py` against them**, never hand-computed — see
`test_run_doc_migrations_cli.py` for the exact commands and asserted output.

`sot-shapes/` is **hand-built**, not derived: as of this phase, no corpus anywhere in
this repo's real or scratch copies carries a `## 2. Functional Capabilities` heading
(every one is still pre-SOT, `## 2. Open Decisions`), so there was nothing to trim
these four shapes from. Each one starts from a real, fully-composed SOT pair (the
`F001_Auth` functional/technical-spec pair after every migration step actually ran
against it — see "How `sot-shapes` was built" below), then hand-edited to pin one
specific shape.

## Shape index

| Fixture | Shape it pins | Dependent rule id(s) | Derivation |
|---|---|---|---|
| `pristine-small/docs/features/{F001_Auth,F005_MarketplaceCreation,F051_TransactionStateMachine}` | v26 four-file (pre-audience-split): `business-context.md` + `screens.md` + `technical-spec.md` + `edge-cases.md`, no `functional-spec.md` | `audience-split` count_pending/run | Trimmed copy of `st-pristine` |
| `post-small/docs/features/{F001_Auth,F005_MarketplaceCreation,F051_TransactionStateMachine}` | v27 pre-SOT: `functional-spec.md` + `technical-spec.md` pair exists (audience-split done), `functional-spec.md` still carries `## 2. Open Decisions` (not yet SOT) | `a3-b4`, `a3-screens`, `screen-sot`, `feature-sot` count_pending/run/refuse chains | Trimmed copy of `st-post`, plus its `.migrate-v27/` staging sentinels (see below) |
| `post-small/docs/screens/{SCR001_Homepage,SCR020_LoginPage,SCR021_SignupPage}` | v27 pre-SOT screen spec (no `## 2. Screen Layout` yet) | `a3-screens`, `screen-sot` count_pending/run/refuse chains | Trimmed copy of `st-post` |
| `post-small/docs/features/F001_Auth/confidence-report_technical-spec.md` | **Deliberately stale** A1 companion (content edited after copying so it no longer matches its sibling `technical-spec.md`) | `test_only_audience_split_runs_and_reports_already_on_sealed_corpus` — proves the always-regenerate A1 refresh actually rewrites a stale companion, not just "would rewrite nothing because it already matched" | Hand-edited (one HTML-comment marker line appended, then removed by the real `derive_confidence_report.derive()` call when the test runs) |
| `sot-shapes/F901_CapabilitiesHeaderOnly` | v27 SOT, 7-column `## 2. Functional Capabilities` header (`ID \| Capability \| What the user can do \| User Stories \| Requirements \| Business Rules \| Screens`) + **zero data rows** (SA-2 bypass shape — `reports/red-team-260819-1300-adjudication.md` SA-2) | `cap.code_unclaimed` (29 criticals — every US###/FR-###/BR-family/SCR### declared in §§ 4-7, since `claim_state` resolves `"absent"` here, not `"unfilled"`), `func.capabilities_empty` | This IS the real `_doc_migration_feature_sot_step_lib.py` composer's own scaffold output (5-col), widened by hand to the phase-04 7-col header — see `test_corpora_fixture_shapes.py::TestF901CapabilitiesHeaderOnly` |
| `sot-shapes/F900_CapabilitiesPopulated` | v27 SOT, 7-column `## 2. Functional Capabilities` with 5 capability rows (`CAP-01..05`) that exhaustively and exclusively claim every US###/FR-###/BR-family/SCR### declared in §§ 4-7 — the clean baseline | Zero `cap.*` issues (`claim_state` = `"filled"`); `func.capability_fr_dangling` stays silent because every Requirements-cell FR-### also appears in § 4 | Same composer output as F901, hand-filled with 5 rows — see `test_corpora_fixture_shapes.py::TestF900CapabilitiesPopulated` |
| `sot-shapes/F902_CapabilitiesEmptyCells` | v27 SOT, 7-column header, has data rows (`CAP-01`, `CAP-02`) but every non-ID cell — including the new User Stories/Business Rules columns — is blank (AD-1/FM-4 fill-pending shape: the table was widened but nobody filled a claim cell yet) | `cap.claims_unfilled` (exactly 1 warning, `claim_state` = `"unfilled"`); `cap.code_unclaimed`/`cap.double_claimed` correctly muted while unfilled | Same composer output, hand-edited to blank cells across all 7 columns — see `test_corpora_fixture_shapes.py::TestF902CapabilitiesEmptyCells` |
| `sot-shapes/F903_DuplicateOpenDecisions` | v27 SOT (populated 7-column `## 2. Functional Capabilities`, same content as F900 except DEC-002 is deliberately left off CAP-02's Business Rules cell) **plus** a stray, out-of-position `## 2. Open Decisions` heading injected inside § 12 Dependencies (SA-3 mute-abuse shape — `is_pre_sot` requires BOTH the pre-SOT sentinel AND the absence of `## 2. Functional Capabilities`, so a stray sentinel alongside the real heading does not mute) | `is_pre_sot` resolves `False`; exactly 1 `cap.code_unclaimed` critical fires on DEC-002 — proof the check is reachable on this file, not silently muted by the stray heading | Same composer output, hand-edited with one stray heading + DEC-002 dropped from its claim cell, each with an explanatory HTML comment — see `test_corpora_fixture_shapes.py::TestF903DuplicateOpenDecisions` |

## Why no `vi`/`jp` mirrors

`post-small`/`pristine-small` register no secondary languages in `.rebuild-state.json`
(no `translations` key). `mirror-skew`'s `count_pending` (`_mirror_skew_lib.py`) reads
`state["translations"]` and returns an empty skew list — 0 pending — when that key is
absent, by design (`_mirror_skew_detect_lib.detect_skew`'s own docstring: "Empty list,
never a raise, when `.rebuild-state.json` is absent/malformed or carries no
secondaries"). Trimming 66 `vi`/66 `jp` mirror dirs down to 3 each, keeping them
consistent with `.rebuild-state.json`'s per-screen SHA map, was out of scope for what
this file's own test suite needs (mirror-skew orchestration wiring — refusal, the
translate handoff refusal message, the `count_pending`/`run` registry contract — none
of which require a REAL stale mirror to exercise). The two
`test_opportunistic_full_scale_corpus_*` tests in `test_run_doc_migrations_cli.py`
cover the real 2-language-stale count end to end, at full scale, when the scratch
corpus happens to be present.

## How `sot-shapes` was built

1. Copied `post-small`'s `F001_Auth` functional/technical-spec pair.
2. Ran the real migration chain against it (`--only a3-b4`, `--only a3-screens`,
   `--only screen-sot`, `--only feature-sot`) so both files reached the genuine,
   composer-produced v27 SOT shape (13-section functional-spec, 5-bucket
   technical-spec) — never hand-typed.
3. Renamed the internal `F001_Auth` references to each variant's own slug/number
   (`F900`–`F903`).
4. Hand-edited only the `## 2. Functional Capabilities` table (and, for F903, injected
   one stray heading) per the shape index above. Everything else — § 1 Overview, § 4
   Requirements' FR-### codes, § 6 Screens' SCR### codes, § 12 Dependencies — is real,
   unedited composer/audience-split output.
5. Phase 04 later widened § 2 to 7 columns (`User Stories` + `Business Rules` joined
   `Requirements`/`Screens`) and phase 05 implemented the `cap.*` checks that read the
   new claim columns. The four fixtures above were re-hand-edited at that point to
   carry the 7-column header and populate/empty/omit the new columns per the shape each
   one pins — see `test_corpora_fixture_shapes.py` for the pinned `claim_state` and
   `cap.*` issue set per fixture, verified against the real `_check_capabilities_section`.

Verified against the real, phase-05 `cap.*` checks (not hand-computed — see
`test_corpora_fixture_shapes.py`, run `validate_feature_spec.py` directly against each):
F900 emits zero `cap.*` issues (the clean baseline); F901 emits 29 `cap.code_unclaimed`
criticals (`claim_state` = `"absent"`); F902 emits exactly one `cap.claims_unfilled`
warning (`claim_state` = `"unfilled"`); F903 emits exactly one `cap.code_unclaimed`
critical on its deliberately-unclaimed DEC-002, proving the SA-3 stray heading does not
mute the check. All four still carry only pre-existing content warnings otherwise
(`func.user_story_shape`, inherited from the real `F001_Auth` prose) plus, for F901,
the pre-existing `func.capabilities_empty` warning.

6. rebuild-spec 27.7.0 (action-thread reshape, phase 10): each fixture's
   `technical-spec.md` (the § 2 Functional Capabilities checks' `cap.*` family live
   entirely on the `functional-spec.md` side, above, and never read the tech-spec's
   shape) was re-run through the real `_feature_sot_technical_lib.compose_action_thread`
   composer — never hand-edited — reshaping it from the 5-bucket v27 SOT shape to the
   current action-thread shape, so these fixtures stay representative of what a real
   fully-migrated feature dir looks like. The `functional-spec.md` side (and every
   hand-edited § 2 shape it pins) is untouched. `test_corpora_fixture_shapes.py` and
   `test_doc_migration_cap_map_step.py` both still pass unchanged, confirming the
   `cap.*` checks/`cap-map` step genuinely never depend on the tech-spec's own shape.

## Security scrub

All fixtures derive from a real client corpus. Before committing:

- The client's product name was replaced with a generic placeholder (`Sharetribe` →
  `Marketplace`, case-preserved) throughout every fixture file, including the
  `.migrate-v27/` staging snapshots.
- Scanned for API-key/secret/password/token-shaped values, PEM key headers, AWS access
  key patterns, and email addresses — none found. The handful of `recaptcha_secret_key`
  / `auth_token` occurrences are **variable-name references** in prose describing code
  structure ("no `recaptcha_secret_key` → skip validation"), not real credential
  values — structure, not content, per this phase's security requirement.
- No `vi`/`jp` mirror content is committed (see above), so no translated-prose surface
  exists to scrub twice.

## `feature-split-labels/` — the over-scope yardstick

Three files pinning the only non-circular answer this repo has to *"does this feature
actually need splitting?"*: `packets.md` (the 18 blind packets), `labels.json` (votes +
majority + adjudication), `feature-metrics.json` (US/SCR/BL/CAP counts for all 66).

**Why it exists.** The first attempt at an over-scope rule reported "100% precision" —
measured against `cap.promote_candidate`, itself an unvalidated threshold rule, and from
which the new rule had been derived by dropping one term. Two rules agreeing tautologically
says nothing about whether either is right. Scored against these labels instead, that rule
lands at **60% precision / 30% recall**. `measure_feature_split_rules.py` re-runs the whole
comparison from this fixture; `test_feature_split_labels.py` pins it.

**How the labels were made.** Three independent LLM labelers, one shared prompt, no
cross-talk, each **blind to** `cap.promote_candidate`, every threshold, which features any
rule had flagged, and the § 2 CAP partition. They were restricted to a single file **outside
this repo** — `plan.md` here names the flagged features, so an unrestricted labeler could
have read the answer key. The 18 span five suspicion bands (flagged / near-miss / high-CAP /
background / small control); the three small controls came back unanimously KEEP at high
confidence, which is the evidence the labelers were not simply split-happy.

**Limitations, which travel with every number derived from this fixture:**

- **n = 18, and the sample is deliberately enriched.** Its 56% SPLIT rate is the *sample's*,
  never the corpus's. Precision measured on a random sample would be lower.
- **Fleiss kappa = 0.481** (moderate); 11/18 unanimous. Three competent labelers disagreed
  on 7 of 18 — the question is genuinely ambiguous at the boundary. This is why the gate
  built on it proposes rather than auto-splits.
- **The user adjudicated 5 of the 7 disputed calls** (2026-08-20). All five matched the
  majority, so the label set is unchanged and its confidence is raised. `F020` and `F046`
  were left on majority.
- Rules were searched against these same 18 labels, so any figure is an **upper bound**
  until validated on held-out features.

Scrubbed per "Security scrub" above (client product name → generic placeholder; the one
`confirmation_token=...` hit is a route pattern with a literal placeholder — structure, not
content). Both properties are enforced by tests, not just asserted here.

## Regenerating or extending

Do not hand-edit `post-small`/`pristine-small` in place to add a new shape — trim a
fresh feature dir from a real corpus copy instead, run `validate_feature_spec.py`
against the result, and add a row to the shape index above. For a new SOT-only shape,
follow "How `sot-shapes` was built" above rather than writing raw markdown by hand —
the composer's real output is the only way to be sure the shape is what `feature-sot`
actually produces, not what this file's author guessed it produces.
