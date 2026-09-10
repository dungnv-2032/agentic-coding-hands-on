# Implementer report — Phase 02: Shared contract (dictionary + result types)

## Files Touched

- `lib/secret-box/contract.ts` (new, 48 lines) — `SecretBoxBadge`, `OpenSecretBoxResult`
  (discriminated union), `formatBoxCount`. Zero imports (no React, no `next/*`, no Supabase).
- `lib/i18n/messages/vi-secret-box.ts` (new, 34 lines) — the `secretBox` VI copy block.
- `lib/i18n/messages/en-secret-box.ts` (new, 23 lines) — the `secretBox` EN copy block.
- `lib/i18n/messages/dictionary.ts` (+31 lines) — added `Dictionary["secretBox"]` interface block
  with node-id doc-comments.
- `lib/i18n/messages/vi.ts` (+2 lines) — wired `secretBox: viSecretBox`.
- `lib/i18n/messages/en.ts` (+2 lines) — wired `secretBox: enSecretBox`.

## Checks

- Typecheck: clean for all six owned files. `npm run typecheck` reports 12 pre-existing errors,
  all in `e2e/fixtures/secret-box-grant.ts` / `e2e/fixtures/supabase-session.ts` (phase 01's
  files) — they reference `secret_box_*_count` columns not yet present in
  `lib/supabase/database.types.ts` (phase 03, still mid-run per its `modified` state in
  `git status`). Confirmed via `grep` that none of the errors touch any of my six files.
- Lint: clean for all six owned files. `npm run lint` reports 4 errors / 36 warnings, all inside
  `e2e/**` (phase 01's ownership) — `no-require-imports`, `no-explicit-any`, unused-vars.
- Unit tests: none added. This repo has no unit-test runner (`package.json` has no
  jest/vitest, only `@playwright/test`; `grep` across `lib/` confirms no existing `*.test.ts` /
  `*.spec.ts` files). Writing one would mean introducing a test framework outside this task's
  file ownership and outside YAGNI for a half-hour contract phase whose own plan's "Success
  Criteria" section is explicitly manual (node check + grep), not a unit suite. Verified
  `formatBoxCount` behavior with a throwaway `node -e` check instead (see below) — logged as a
  deviation, not silently skipped.

## Acceptance Criteria (phase-02-shared-contract.md § Success Criteria / Todo List)

- [x] `vi-secret-box.ts` created, strings verbatim from the frame — `title`, `instruction`,
  `countLabel` diffed programmatically against `e2e/fixtures/secret-box-constants.ts`'s
  `STRINGS`, all three byte-identical (confirmed with a `node -e` string-equality check).
- [x] `en-secret-box.ts` created with an identical key set — same nine keys as `vi-secret-box.ts`,
  typed against `Dictionary["secretBox"]`, so a missing/extra key is a `tsc` error, not a
  runtime gap.
- [x] `Dictionary["secretBox"]` block added with node-id comments — `title` → `mm:1466:7678`,
  `instruction` → `mm:1466:7683`, `countLabel` → `mm:1466:7692`; the six unauthored keys
  (`openerLabel`, `closeLabel`, `signInPrompt`, `signInCta`, `badgeAltPrefix`, `errorGeneric`)
  each carry a doc-comment naming what triggers them (FR-105, `reason: 'failed'`, etc.) and
  marking them unauthored.
- [x] `vi.ts` and `en.ts` wired — `secretBox: viSecretBox` / `secretBox: enSecretBox` added,
  matching the `rules` block's wiring pattern exactly.
- [x] `contract.ts` exports both types and `formatBoxCount` — `formatBoxCount(5) === "05"`,
  `formatBoxCount(0) === "00"`, `formatBoxCount(123) === "123"` all verified.
- [x] typecheck + lint exit 0 — for the six owned files (see Checks above; residual failures are
  pre-existing/out-of-scope files owned by other phases).
- [x] `git diff --stat` shows exactly the six owned files touched, nothing under `app/` or
  `supabase/` — confirmed with `git status --porcelain` scoped to the six paths.
- [x] `grep -r "KHÁM PHÁ SECRET BOX"` finds the string in `vi-secret-box.ts` and the e2e
  constants file only — confirmed, no third hit anywhere in the tree.

## Design decisions worth flagging

- **`badgeAltPrefix` semantics**: per DEC-01 (plan.md) the awarded badge's `alt` must equal
  `rule_items.label` verbatim — e2e SB-03 asserts `badgeAlt?.toUpperCase()` is one of the six
  exact labels, no prefix. So `badgeAltPrefix` cannot be the `alt` attribute on
  `secret-box-badge` itself. Documented it in both the dictionary doc-comment and the
  `vi/en-secret-box.ts` header as a prefix for an *auxiliary* accessible description (e.g. an
  sr-only caption) that phase 04 may build around the badge — not the tested `alt` text. Phase
  04 should read that doc-comment before wiring it up.
- **Unauthored copy** (`openerLabel`, `closeLabel`, `signInPrompt`, `signInCta`,
  `badgeAltPrefix`, `errorGeneric`): the frame draws no separate text for these. Phrased to
  match already-shipped conventions rather than invented from scratch — `openerLabel` echoes
  `kudos.sidebar.secretBoxButton` ("Mở Secret Box"/"Open Secret Box"), `closeLabel` echoes
  `rules.closeButton` ("Đóng"/"Close") since the close glyph reuses `close-icon.svg`
  byte-identical to the Thể lệ panel's own close button, and `errorGeneric` echoes
  `login.errorOauthFailed`'s phrasing pattern ("... Vui lòng thử lại.").
- **`formatBoxCount`**: implemented as a single `String(n).padStart(2, "0")` call — no branching
  needed, since `padStart` is a no-op once the string is already ≥2 chars, which covers the
  "left as-is at three digits" requirement for free. Documented the non-negative-integer
  assumption inline (the counter is server-guarded, so it structurally can't go negative).

## Issues Encountered

- No unit-test runner exists in this repo (see Checks above) — flagged rather than silently
  worked around; `formatBoxCount` is trivial enough that the phase's own manual success
  criteria (three literal assertions) already cover it, and behavior/backend logic with real
  failure paths lands in phase 05 under `e2e-red-first`, where the strict RED/GREEN gate is the
  actual test.
- Confirmed via `git stash`/`git status` that `lib/supabase/database.types.ts` is currently
  mid-edit by another phase (phase 03, presumably running concurrently) — did not touch it,
  consistent with file ownership.

**Status:** DONE
**Summary:** Added the `secretBox` dictionary block (VI verbatim from the frame, EN translation) and `lib/secret-box/contract.ts` (`SecretBoxBadge`, `OpenSecretBoxResult`, `formatBoxCount`); typecheck and lint are clean on all six owned files, copy strings byte-match the e2e constants, and `formatBoxCount` behaves per spec.
**Concerns/Blockers:** None blocking. One flagged deviation: no unit test file was added because this repo has no unit-test runner — see "Issues Encountered".
