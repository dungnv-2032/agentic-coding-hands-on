# Phase 10 — GREEN + visual validation

**Track:** Test · **Owner:** `tester` · **Effort:** 1.5h
**File ownership:** `evidence/**`, `reports/**` — **no source file, no test file**. A failure here
returns a bounded fix to the owning phase; tests are never weakened to make a run green.

## Context Links

- Phase 02 (the RED command and its recorded exit code — rerun **verbatim**)
- Phase 03 § Success Criteria (the eight security probes)
- `plans/260907-0822-viet-kudo/reports/orchestrator-k25-root-cause.md` (how to read a failure that
  passes alone and fails in company)
- `design/profile.png` (1440×4660) — the visual reference
- `reports/momorph-visual-study.md` — the measured values a mismatch is judged against

## Overview

- **Priority:** P1 — the `e2e-red-first` policy closes here or not at all.
- **Status:** pending
- Rerun the exact RED command for GREEN, then run the whole suite to prove nothing else moved, then
  own the browser/visual evidence.

## Key Insights

- **"Passes alone, fails in company" means shared mutable state, not load.** Three successive
  diagnoses in F004 blamed load and each made the suite slower instead of correct. If the profile
  suite is green alone and red in the full run, look first at session sharing and at leftover
  database rows — not at timeouts.
- **The local database has drifted** (measured today: 63 `kudos` rows against 57 seeded, 15 `sunners`
  against 9 seeded, from previous e2e runs). Run `supabase db reset` before the authoritative run, or
  the seeded numbers in phase 03's probes and phase 05's criteria will not reproduce.
- **`kudos_likes` must be 0 before and after.** The seed deliberately creates none, so any row is
  test residue by definition — that is what makes cleanup-by-`kudos_id` safe.
- Visual validation is a **comparison against measured values**, not an aesthetic opinion. A
  mismatch is only reportable with the `mm:{nodeId}` and the measured value it violates.

## Requirements

Functional: every one of the 30 design test cases either passes or is recorded as a documented
not-honoured case (GUI_001 stars — AMEND-1; GUI_002 badge artwork — AMEND-2; FUN_008's
`kudos_no_self` note — ADV-2). Non-functional: the suite is idempotent across two consecutive full
runs, and `npm run build` succeeds.

## Architecture

```
supabase db reset  →  phase 03's 8 SQL/HTTP probes  →  npx playwright test (RED command, verbatim)
                   →  npx playwright test (all projects)  →  Playwright MCP visual capture
                   →  evidence/*.log + reports/tester-*.md
```

## Related Code Files

Create: `evidence/full-suite-green-run.log`, `evidence/phase-03-security-probes.log`,
`evidence/profile-visual-*.png`, and one tester report under the reports path.
Modify: none. Delete: none.

## Implementation Steps

1. `supabase db reset` (re-applies the phase-03 migration and the seed, and clears e2e residue).
   Confirm: `select count(*) filter (where is_anonymous) from public.kudos` ≥ 1,
   `select count(*) from public.kudos_likes` = 0.
2. Run phase 03's eight probes; capture to `evidence/phase-03-security-probes.log`. Any failure is
   BLOCKED, back to phase 03 — do not proceed.
3. Rerun phase 02's RED command **unchanged**:
   `npx playwright test --project=profile-auth-setup --project=profile-authed --project=anon`.
   Record the exit code. Expect 0.
4. Run every project: `npx playwright test`. Record per-project counts and the total, in the shape
   the K-25 report used (`setup 1, kudos-auth-setup 1, profile-auth-setup 1, anon N, authed 3,
   kudos-authed 61, homepage-authed N`). Confirm `--list` shows each `*-auth.setup.ts` in exactly
   one project.
5. Run it a second time and confirm the same result and `kudos_likes` back to 0 — idempotence.
6. `npm run build`.
7. Visual validation with Playwright MCP at 1440px, authenticated: `/profile` (self, sparse) and
   `/profile?id=1` (populated). Capture both, then compare against `design/profile.png` and the
   measured values: page `#00101A`; 512px banner; 200×200 avatar with a 4px white ring; name 36/44
   bold `#FFEA9E`; department 22/28 white; 4×4 `#999` dot at 40%; tier pill `border-[#FFEA9E]`
   `rounded-[48px]`; six 64×64 `#323231` circles with 2px white borders at 16px gaps; stats card
   680px, `p-10`, `border-[#998C5F]`, `bg-[#00070C]`, `rounded-[17px]`, `#2E3940` divider between
   rows 3 and 4; labels 22/28 white and values 32/40 `#FFEA9E`; gold `Mở Secret Box` button,
   disabled; "KUDOS" 57/64 `#FFEA9E`; feed single column, 680px cards, `#FFF8E1`, `rounded-[24px]`,
   24px gap.
8. Also capture `/profile?id=2` and confirm by full-page text search that `Đã gửi` appears nowhere.
9. Write the report: per-test-case pass/fail against the traceability table, the security probe
   results, the visual comparison, and anything returned to an owning phase.

## Todo List

- [ ] `supabase db reset` run; seeded anonymous row present; `kudos_likes` = 0
- [ ] Eight security probes pass, captured to `evidence/`
- [ ] RED command rerun verbatim → exit 0
- [ ] Full suite → exit 0, per-project counts recorded
- [ ] `--list` shows each auth setup in exactly one project
- [ ] Second full run identical; `kudos_likes` back to 0
- [ ] `npm run build` exits 0
- [ ] Visual capture for self-sparse, `?id=1`, `?id=2`
- [ ] `Đã gửi` absent from `?id=2`'s full page text
- [ ] All 30 test cases dispositioned; the three not-honoured cases cited to AMEND-1/AMEND-2/ADV-2
- [ ] Report written

## Success Criteria

- Two consecutive full-suite runs exit 0 with identical counts, and the previous total (144 passing
  at the end of F005) plus the new profile tests are all accounted for — no test silently skipped.
- F004's `--project=anon` and `--project=kudos-authed`, and F001's `--project=authed`, are green:
  the new project did not disturb C9's session.
- The anon key cannot read `sender_id` from `public.kudos` (probe 2) and reads `null` for the seeded
  anonymous row through the view (probe 3), while a non-anonymous row returns the **named expected
  person**, different from the receiver (probe 4).
- Every visual value in step 7 matches, or a mismatch is reported with its `mm:{nodeId}`.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Green reached by weakening a test | L × **H** | This phase owns no test file; a failure returns a bounded fix to the owning phase |
| Profile suite green alone, red in the full run | M × H | Key Insight 1: suspect the session file and residual rows first; verify `--list` project assignment before theorising about timing |
| Timeout raised to paper over the server-authoritative heart | M × M | The 15s allowance is already scoped to the profile project in phase 02; raising it globally is forbidden (a full RED run takes ~25 min) |
| Residual e2e rows make probe numbers irreproducible | **H** × L | Step 1's reset is mandatory and its output is captured |
| Visual "mismatch" reported as taste | M × L | Only measured values with an `mm:` id count as findings |
| A not-honoured case read as a defect | M × L | AMEND-1, AMEND-2 and ADV-2 are cited by name in the report |

**Rollback.** Nothing to roll back — this phase writes only evidence. If the gate cannot close, the
rollback is the owning phase's (03 § Risk for the migration, 09 § Risk for the board contract).

## Security Considerations

- SEC_004 is verified here against the real response body: no `@`-bearing email and no uuid-shaped
  string in the HTML for either face of the route.
- SC-003 (Sent list self-scoping) is verified by sending two different `targetSunnerId` values in one
  session and diffing the responses — not by reading the UI.
- Evidence files must not contain a session token or the anon key; redact before writing.

## Next Steps

- On GREEN: hand to `reviewer`, then `doc-writer` to reconcile `docs/system/architecture.md` and
  `docs/system/permissions.md` from `spec/system/*.md` (PERM011/PERM012/PERM013 get their real codes
  at promote), then `delivery-tracker` for the roadmap and changelog.
- Carry forward: ADV-1 (two paging strategies), ADV-2 (`kudos_no_self`), and the new advisory from
  phase 03 (no composite keyset index yet).

---

## Carry-over defects the orchestrator logged for this phase (added 2026-09-08, after phases 03/07)

1. **`TC_WEB_PROFILE_GUI_005` is unsatisfiable as written — test-side fix belongs here.**
   It asserts `toBeDisabled()` on `profile-secret-box-button`, then calls `button.click()`.
   Playwright routes both through one predicate (`elementState` → `getAriaDisabled` =
   `isNativelyDisabled(el) || hasExplicitAriaDisabled(el)`, `playwright-core/lib/coreBundle.js`),
   so anything that satisfies the assertion fails `click()`'s enabled-actionability check and times
   out. `aria-disabled` does not escape it. The spec says the button IS disabled, so phase 07
   implemented the design and left the test alone. Fix on the test side: `click({ force: true })`,
   or replace the click with a no-navigation assertion. Do NOT enable the button to make it pass.

2. **Do not judge any F004 suite run before phase 04 lands.** Phase 03's `revoke select on
   public.kudos` breaks `/kudos` and the heart toggle by design until phase 04 repoints the three
   `.from("kudos")` call sites onto `kudos_readable`. A red F004 before phase 04 is expected and
   must never be "fixed" by restoring the table grant.

3. **Keyvisual origin, if the visual diff flags it.** The frame draws the banner from `y0` with the
   header over it; `HomeHeader` is sticky and in flow, so the banner starts ~64px lower — the same
   compromise `/kudos` already ships. If it needs correcting, the fix belongs in `app/profile/page.tsx`
   (phase 09), not in phase 07's five component files.

4. **Two authority documents misplace the badge caption.** `mm:3053:10052` — TEXT
   "Bộ sưu tập icon của tôi", 22px/28px white — sits at y624–652, *below* the circle row (y528–592).
   `reports/momorph-visual-study.md` ("A.3 = 6 slots only") and
   `docs/screens/SCR006_ProfileBanThan/spec.md` ("không phải một node mm", "phía trên hàng") are both
   wrong; `design/profile.png` confirms below. Phase 07 followed the measured frame. Expect the visual
   diff to match the frame, not those two documents.

5. **`FUN_009` and `FUN_011` are unpassable as written — test-side fix, same class as GUI_005.**
   Both open the dropdown then call `page.getByText("Đã nhận")`. With the menu open that substring
   exists in two nodes by design: the trigger (which `FUN_009` asserts on the line before) and the
   received option. `getByText` defaults to `exact: false`
   (`playwright-core/types/types.d.ts:3256`) and two matches is a strict-mode violation (`:15968`).
   Making the strings differ is not available: SCR006 § 3 assigns the same `direction.receivedLabel`
   key to both C.3 and C.3.1, and DEC-002 requires the active option to stay listed. `FUN_010` /
   `FUN_012` are unaffected (they match "Đã gửi" while the trigger reads "Đã nhận"). Fix with
   `getByTestId("profile-direction-option").filter({ hasText })` or
   `getByRole("option", { name })` — both *stricter* than the current locator, not weaker.
   Phase 08 could not execute it to confirm (`browserType.launch` fails in the WSL2 sandbox), so
   confirm the diagnosis here before applying.

6. **`profile-feed-end` renders on a short first page.** Phase 08 read that as correct. If the spec
   meant "only after a subsequent fetch", it is a one-line change in
   `app/profile/_components/kudos-direction-section.tsx`. Decide from the assertion, don't guess.

---

## Resolved before this phase started (2026-09-08) — do not redo

**Items 1 and 5 above are FIXED**, plus a fourth instance of the same defect class that those notes
missed. See `reports/tester-profile-testcase-repair.md`.

- `GUI_005` — now `click({ force: true })`, with the URL pinned to its exact pre-click value and the
  disabled state re-asserted after the forced click. Stricter than before, which only checked that
  the URL *contained* `ROUTE`.
- `FUN_009`, `FUN_011` — the bare `getByText(DIRECTION_LABELS.received)` is now scoped to
  `getByTestId("profile-direction-option").filter({ hasText })`. Stricter: the old locator was
  satisfiable by the trigger alone.
- `SEC_001` (`e2e/profile.spec.ts`, the one-option case) carried the identical defect — the trigger
  also renders `"Đã nhận (N)"`, so `getByText` resolved to 2 elements even with one option present.
  Patched by the orchestrator with the same scoped locator. Typecheck 0, lint 0.
- `FUN_010`, `FUN_012`, `SEC_002` match `"Đã gửi"` against a trigger reading `"Đã nhận"` — verified
  unaffected, untouched.

**Evidence quality note:** the repair was proven with a real-Chromium DOM-equivalence harness
(markup copied from `profile-stats-card.tsx` and `profile-direction-menu.tsx`), because on the real
spec an *earlier* element-absent assertion fails first and the defective line is never reached — the
defects were latent and would have detonated on this phase's first GREEN attempt. Harness before:
exit 1, both predicted failure modes verbatim. After: exit 0. The real spec stayed at the same honest
RED (exit 1) across the edit, which is the correct outcome while `page.tsx` is unwired.

**The WSL2 browser blocker recorded elsewhere in this plan is FALSE — Chromium launches fine here.**
The system libs really are missing (`ldd` shows `libnspr4.so`, `libnss3.so`, `libnssutil3.so`,
`libasound.so.2`, `libsmime3.so` not found), but they are vendored under `.playwright-libs/` and
`playwright.config.ts:12-20` puts them on `LD_LIBRARY_PATH`. So `npx playwright test` works
unmodified; only *standalone* scripts need the variable exported. Phase 08's report claims otherwise
— that claim is wrong.

**Trap for the next author:** `e2e/fixtures/profile-constants.ts` holds `DIRECTION_LABELS` as bare
labels (`"Đã nhận"`) while the UI renders `"Đã nhận ({count})"`. Any new bare `getByText` on those
constants will hit the same strict-mode violation.

## Handed over from phase 05 (2026-09-08)

- **`TC_WEB_PROFILE_SEC_002` cannot fail as written.** At `e2e/profile.spec.ts:568` its only
  post-switch assertion is `expect(feedArea).toBeVisible()`, which passes whether or not the composed
  card is in the list. **This phase must tighten it.** Phase 05 proved the underlying behavior end to
  end — a real signup composed a real anonymous Kudo through `create_kudos()`, and the real server
  action returned it in that user's own Sent list naming them (`sender.id: 10`,
  `anonymousSenderLabel: null`, `sentAnonymously: true`, `canLike: false`) while the same row read by
  anyone else came back as the redacted stub. That is the assertion this test should carry;
  `revealOwnAnonymous` has no other durable owner (the repo has no unit-test runner).
- **Known flake, not a regression:** `e2e/callback-security.spec.ts:91` failed once during phase 05's
  first full `--project=anon` run (80 passed / 1 failed), then passed 8/8 alone and 81/81 on both
  later full runs. No phase-05 code reaches it. Re-run before calling it a regression.
- **Baselines to match:** `--project=anon` → `81 passed` EXIT=0; `--project=kudos-authed` →
  `62 passed` EXIT=0. Both held at the end of phases 04 and 05.
- **New advisory ADV-4:** `fetchReceivedAggregate` (`lib/profile/profile-queries.ts`) reads every
  received row to sum hearts, so it would silently truncate past PostgREST's `max_rows = 1000`. Not a
  defect at seed scale (58 rows); record it, do not fix it here.
- **Phase file defect worth knowing:** phase 05's Key Insight 1 justified the keyset predicate by
  claiming the seed generates duplicate `sent_at` values. It generates none
  (`group by sent_at having count(*) > 1` → 0 rows), so the phase's own no-duplicate/no-skip
  criterion passes identically for the degraded `sent_at.lt`-only form — the risk table's
  countermeasure does not work. Phase 05 implemented the correct predicate anyway and proved it
  load-bearing on 12 constructed rows sharing one timestamp across the page boundary: correct
  predicate returns 3 rows on page 2, `sent_at.lt` alone returns 1 (rows 60 and 59 vanish silently).
  If this phase re-verifies pagination, construct a tie — the seed cannot expose the bug.
