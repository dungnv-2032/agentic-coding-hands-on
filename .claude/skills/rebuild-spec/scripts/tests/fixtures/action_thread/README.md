# Action-thread composer fixtures — provenance

**These eight files are VERBATIM copies of real, already-migrated (v27-shaped)
corpus output.** Copied 2026-08-24 (F011/F017/F026) and 2026-08-25 (F002) from the
sharetribe corpus checked out locally at `~/github/sharetribe/docs/`, unedited.
Never hand-author a fixture for this composer (see phase-05-sot-composer.md's Risk
Assessment — this repo once shipped 2785 green tests over a script that could never
run because a hand-authored fixture defaulted the one field the real producer never
writes).

| File | Source | Why this feature |
|---|---|---|
| `F011_technical-spec.md` | `docs/features/F011_ListingModeration/technical-spec.md` | The plan's own acceptance feature — 8 declared routes, 1 background job, 6 BR + 3 DEC blocks, 1 capability. Matches `plans/260824-1101-technical-spec-bv-sample/technical-spec.md` (the hand-written target-shape sample) so the composer's output can be compared against it structurally. |
| `F011_functional-spec.md` | `docs/features/F011_ListingModeration/functional-spec.md` | F011's twin — supplies the `## 2. Functional Capabilities` CAP-01 bucket order `compose_action_thread` reads. |
| `F017_technical-spec.md` | `docs/features/F017_TransportAndCookieSecurity/technical-spec.md` | One of the three corpus features with **zero** `### 3.4` data rows AND zero `## DB Impact per Event` rows (measured in `reports/preflight-260824-1145-verified-facts.md` C2, alongside F016/F029) — genuinely zero actions. Smallest of the three (277 lines). Exercises the mandatory-`A0`-even-at-zero-actions path (merge blocker #1). |
| `F017_functional-spec.md` | `docs/features/F017_TransportAndCookieSecurity/functional-spec.md` | F017's twin. |
| `F026_technical-spec.md` | `docs/features/F026_TransactionalEmailSettings/technical-spec.md` | Phase 11 real-corpus acceptance's ONE genuine composer defect: `SM-001` (§ 3.3 State Management's `### Sender-address verification lifecycle (SM-001)`) has NEITHER a `### 4.N` capability-bucket home (SM blocks never do) NOR a § 2 `Functional -> Technical Mapping` completeness row (unlike F011's SM-001/SM-002 below, which both do) — so it was invisible to `assign_codes` entirely and fired `FeatureSpec.action_unclaimed`. Also carries `ALG-001`/`INT-001`/`INT-002`, none of which have a mapping row either, exercising the same fallback for those families. |
| `F026_functional-spec.md` | `docs/features/F026_TransactionalEmailSettings/functional-spec.md` | F026's twin — CAP-01 row declares `SM-001` (among the BR/DEC codes), which is what made the miss a real, corpus-observed `action_unclaimed` critical rather than a merely-theoretical gap. |
| `F002_technical-spec.md` | `docs/.migrate-v27/action-thread/F002_AuthenticationAndSession/technical-spec.md.bak` — the PRE-migration (5-bucket, `_TECH_PRE_THREAD_SENTINEL`-bearing) input, not the already-reshaped live `technical-spec.md` next to it. | Copied 2026-08-25, plans/260825-1010-rebuild-spec-action-thread-migration-defects. Single richest defect carrier in the 43-feature corpus, exercising all three confirmed migration defects at once (which is why one fixture, not three): (1) **bucketing** — 6 CAP rows, current distribution `[0,0,0,0,0,16]` (5 empty buckets) vs. the twin's § 2 table distribution `[2,2,2,2,1,7]` (0 empty); (2) **fabricated job classes** — `Any#perform`, `Authenticated#perform`, `PATCH#perform`, `Legacy#perform`, `Scheduled#perform`, `OAuth#perform`, none of which are real `Delayed::Job` classes; (3) **malformed headings** — interior-backtick handler cells (`` `devise/sessions#new` (stock, SCR123) ``, `` `devise/passwords#new`/`#edit` (Devise `:recoverable`) ``, `` `OmniauthController#:provider`/`#create_omniauth` ``), the corpus's only lowercased `#### A10 · New` (stock, scr123)` H4, and several fallback-derived H4 titles literally reading "Perform". The generated A11 mermaid sequence (`OmniauthController → OmniauthService`) also corroborates that the fabricated `OAuth#perform` is a misroute of the existing A7 `OmniauthController#create_omniauth`, not merely a bad name — evidence phase 04 uses against `_resolve_db_event`. |
| `F002_functional-spec.md` | `docs/features/F002_AuthenticationAndSession/functional-spec.md` | F002's twin — **copied POST-fill** (this is the corpus's current, already-completed functional-spec, not a mechanically-composed twin): its `## 2. Functional Capabilities` § 2 table supplies the complete code→capability mapping that fixes defect 1's bucketing (measured `[0,0,0,0,0,16] → [2,2,2,2,1,7]` above). |

**Do not edit these files by hand.** If the corpus's real shape ever changes, re-copy
from the source path above rather than patching the fixture in place — a hand-edit is
exactly the failure mode these fixtures exist to rule out.

**Corpus-content note:** these are real (if publicly-observable, open-source Sharetribe)
business docs, kept to the minimum needed for a real-shape regression test. If the
reviewer decides corpus-derived text should not live in this repo's history at all,
exclude this directory from the commit and replace these tests with skips — do not
replace the fixtures with hand-authored text (that reintroduces the exact risk above).
