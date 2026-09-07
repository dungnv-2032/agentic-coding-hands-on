# `action-thread-shapes/` — provenance

Built by phase 10 of `plans/260824-1128-rebuild-spec-action-thread-v27-7`. Four
technical-spec.md/functional-spec.md pairs pinning four post-migration
action-thread shapes, consumed by `tests/test_action_thread_shapes_corpus.py`.

**All four `technical-spec.md` files are the REAL, unedited-content output of
`_feature_sot_technical_lib.compose_action_thread`** — never hand-authored (the
repo's own precedent: a hand-authored fixture once produced 2785 green tests over a
script that could never run, because it defaulted the one field the real producer
never writes).

| Fixture | Source | Shape it pins |
|---|---|---|
| `F950_CleanMigrated` | sharetribe corpus `F022_AdminDashboardAndAnalytics` | A normal migrated feature: real actions, a populated Action Index, no zero-action shape, no diagram gap. The fewest post-composition findings (one `rung_order`) of all 43 real sharetribe features scanned — see the test file's own docstring for why zero findings is not achievable on real content with actual actions. |
| `F951_UnresolvedRules` | sharetribe corpus `F024_AnalyticsIntegration` | 8 `[UNVERIFIED]` markers (7 `carried from **Applies to:**` + 1 `no resolvable owner`) — a real feature whose `Applies to:` free text mostly does not bind to a declared action (D2's known limitation, C11). |
| `F952_NoActionsData` | already-committed `tests/fixtures/action_thread/F017_technical-spec.md` (sharetribe `F017_TransportAndCookieSecurity`, C2's own zero-action example) | § 2 Action Index carries ONLY the mandatory `A0` row — zero declared HTTP/RPC endpoints AND zero DB-Impact rows. Validates with zero criticals. |
| `F953_MissingDiagram` | already-committed `tests/fixtures/action_thread/F011_technical-spec.md` (sharetribe `F011_ListingModeration`, the plan's own acceptance fixture) | A9 (`ExportListingsJob#perform`, background/queue-driven) is over the diagram threshold (`_action_thread_diagram_lib.is_over_threshold`) but its capability bucket carries no `mermaid sequenceDiagram` fence — fires `FeatureSpec.diagram_required_missing`. |

## How each fixture was built

1. Copied the real `technical-spec.md` + `functional-spec.md` pair verbatim from the
   source above (F950/F951: a fresh checkout of the sharetribe fork at
   `~/github/sharetribe/docs/features/`; F952/F953: the already-committed, already
   security-scrubbed `tests/fixtures/action_thread/` copies — reused rather than
   re-copied, to avoid a second independent copy of the same real content).
2. Renamed every internal `F0##_Name`/`F0##` self-reference to the variant's own
   `F95#`/`F95#_Name` slug (mechanical string substitution, full-slug first then bare
   code — same convention `sot-shapes/` already uses for its own `F001_Auth` -> `F90#`
   renames).
3. Rewrote the title line from the sharetribe corpus's own shape
   (`# Technical Spec — F0##_Name`) to this repo's `FCODE_HEADING_RE` shape
   (`# F0##_Name — Technical Spec`) — a pre-existing, out-of-scope cross-repo format
   mismatch (same class as the plan's own C8 finding) that would otherwise fail
   `FeatureSpec.f_code_format` on all four regardless of which scenario each one is
   meant to demonstrate. Never previously caught because `tests/fixtures/action_thread/`
   was only ever run through the composer, never through the full validator.
4. Ran the real `compose_action_thread(tech_text, func_text)` composer and wrote its
   `.text` output back as the fixture's `technical-spec.md` — no other edit.
   `functional-spec.md` is the untouched twin (steps 1-2 only; step 3/4 do not apply
   to it).

No secrets: scanned for API-key/secret/password/token/PEM-block/Bearer-token shapes
before committing — all matches are field/variable NAMES with blank or placeholder
values (e.g. `admin_intercom_access_token = ""`), the same pattern
`tests/fixtures/action_thread/README.md` already documents for its own two files.
