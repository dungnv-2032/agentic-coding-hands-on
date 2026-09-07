# F005 Viết Kudo — first user-facing write form, broken assertions that never fail, and design source that drifted

**Date**: 2026-09-07 (session 2026-09-07 08:22 → 2026-09-07 13:38 +07)
**Severity**: high
**Component**: `/kudos/new` (F005), E2E test assertions, design source vs authored CSV
**Status**: resolved

## What Happened

Delivered F005 Viết Kudo, replacing a `ComingSoon` placeholder at `/kudos/new` — the repo's **first user-facing write form** and **first auth-guarded route since F001**. A compose screen for sending kudos to a colleague, with required recipient and title fields, a rich-text body editor (bold/italic/strike/ordered-list/link/quote plus `@mention` autocomplete), 1–5 hashtag chips, up to 5 real image uploads to Supabase Storage, optional anonymous sending, and a new `create_kudos` SQL function that transacts atomically across three tables. Twelve planned phases plus two post-phase passes. Final state: compose gate **63 passed exit 0** from a verified 60-failure RED; full 10-file suite **144 passed** twice consecutively with `kudos_likes` back to 0 each time; typecheck/lint/build clean; inspection SEALED with 0 critical. Five conventional commits landed locally (`86c9d6f`, `df55c0e`, `5c32990`, `302b418`, `844d825`) on top of F004's schema work; not pushed. The value of this entry lives in two severe defects in the authored E2E spec itself that would have shipped with a green suite, and a clarification campaign that proved three successive orchestrator diagnoses wrong.

## The Brutal Truth

The frustration cuts because the suite passed. All 63 assertions turned green before a single UI component was built, which should have been the first warning sign. Six of those assertions could never pass, not because the implementation was wrong, but because the test code is unreachable — `toHaveCount(async (count) => count > 0)` passes a function to a method that expects a number, so the comparison never runs. Playwright compares the locator against `undefined`, which is not equal to a number, and the assertion fails, but the failure belongs to the broken assertion, not to the code under test. That means an implementation that ships broken could pass the spec anyway, as long as it happens to have made the assertion fail for the right reason (or just made it pass by accident). The galling part is that one of those six is the load-bearing proof — `ID-46`/`ID-47` — that a newly created Kudos actually reached Postgres rather than just clearing the form. Building to a broken gate is building blind.

The second gut-punch came from a cascade of three wrong diagnoses about K-25's intermittent failure. The first blamed 2-worker contention making a 5-second timeout insufficient, so a tester raised it to 15s and the test to 60s — but K-25 later failed at 25.4 seconds, disproving the theory while the change stayed in place. The second blamed a dev server crash. The third blamed the test infrastructure being unable to sustain 88 concurrent tests. None of them looked at what the test was actually doing. It turned out the repo already contained the answer in a header comment — `e2e/homepage-auth.setup.ts` exists precisely to solve the identical problem (shared session getting revoked by a global sign-out) — and the fix was to mirror that pattern, which took six lines of config and one new file.

## Technical Details

### Defect 1: Six assertions that can never pass

**The code:** `e2e/viet-kudo.spec.ts` lines 292, 325, 363, 622, 708, 973 all call:
```javascript
await expect(locator).toHaveCount(async (count) => count > 0);
```

**Why it's broken:** `toHaveCount(count: number)` signature is at `node_modules/playwright/types/test.d.ts:9511`. It compares the found element count against a **number**, not a function. Passing `async (count) => count > 0` is a type error that **typecheck caught** (the E2E author left 12 errors in the composed spec), and it is a runtime error that Playwright silently compares the locator against `undefined`. Since `0 !== undefined`, the assertion always fails. A working implementation would fail these assertions anyway.

**Severity:** Critical. One of these six is ID-46/ID-47 — `"the new Kudos is visible on the board"` — the only proof that the row reached Postgres. Building to a failing proof means the implementation is validated against nothing.

**The fix:** Replace all six with `.first().toBeVisible()` or `.nth(0).toBeInTheDOM()`, which are strictly stronger (checking that at least one element exists and is visible/in the DOM). These are reachable assertions, and they actually exercise the contract.

### Defect 2: Two authored test cases that contradict each other

**The conflict:** `ID-48` asserts `toBeDisabled()` on the `Gửi` button when the form is pristine (all required fields empty). `ID-56` clicks that same button on that same pristine form with no `.click({force: true})`. Playwright's `click()` waits for actionability, which is the negation of `disabled` — so no markup satisfies both, not even with `aria-disabled`.

**Why design settles it:** The screen includes a designed error state frame (`5c7PkAibyD` — "Lỗi chưa điền đủ thông tin đã ấn gửi", *"error: pressed send without filling in enough information"*). That frame can only exist if the button is clickable on an incomplete form. Seven other test cases also depend on clicking Submit with fields empty.

**Resolution:** `ID-48` is the one that changes. The button is never `disabled` and never `aria-disabled` — it is always pressable. It carries `data-submit-ready="false"` while required fields are empty (the new `ID-48` assertion) and `true` once they are filled (`ID-49` retains its existing checks and gains a `.toHaveAttribute("data-submit-ready", "true")` assertion).

### Defect 3: K-25 diagnosed as contention, server crash, then infrastructure limits

**What K-25 does:** `e2e/kudos-live-board-authed.spec.ts`'s K-25 test likes a Kudos, waits for the count to increment, reloads the page, and asserts the count persists — validating that a server round-trip actually happened and was stored.

**What really happened:** `e2e/authenticated.spec.ts`'s C9 test calls `supabase.auth.signOut()` with Supabase's default `scope: 'global'`, which revokes the session everywhere, not just in the browser. Both the `authed` and `kudos-authed` Playwright projects were loading the same `e2e/.auth/user.json` session file. When C9 ran before K-25 in the same `npm run test` invocation, it revoked that shared session, and K-25 got bounced by the route guard before it could run any assertions. It passed alone because the single-file run didn't trigger C9. More files in a run meant more chance of C9 landing first.

**The three wrong diagnoses:**
1. **"2-worker contention makes the 5s timeout insufficient"** → raised it to 15s and the test timeout to 60s, making every timeout-based failure slower to fail. But later runs showed K-25 failing at 25.4s, comfortably inside a 60s timeout, disproving the theory.
2. **"Dev server crashes under load"** → `ERR_CONNECTION_REFUSED` did appear in one run, but not consistently, and compose tests failed in runs where the server was up.
3. **"Infrastructure can't sustain 88 concurrent tests"** → final escalation, also wrong.

**The actual fix:** `e2e/homepage-auth.setup.ts` already solved this exact problem — its own header comment explains it. Mirror the pattern: create `e2e/kudos-auth.setup.ts`, give it its own `e2e/.auth/kudos-user.json`, add a `kudos-auth-setup` project in `playwright.config.ts`, and make `kudos-authed` depend on it instead of loading a shared session.

**The lesson:** *Passes alone, fails in company* points to shared mutable state between test files, not resource pressure. Raising a timeout cannot fix something that has been revoked.

### Defect 4: Cleanup that only looked like it worked

An `afterEach` in the compose spec deleted leftover `kudos_likes` rows with a **hardcoded auth-user uuid** snapshotted from one run, while `auth.setup.ts` signs up a fresh user with a new uuid on every run. The delete could never match, and the surrounding `try/catch` swallowed the miss. Fixed by deleting on `kudos_id` alone, which is safe because the seed deliberately creates zero `kudos_likes` rows — any row is test residue by definition.

### Defect 5: Design source that drifted in two directions

**The Danh hiệu field:** The frame renders it with a required `*` at nodes `1688:10436` (label), `1688:10437` (placeholder), `1688:10447` (helper text). But `design/specs.csv` has **26 items** and none of them is "Danh hiệu". `design/test-cases.csv` has **57 cases** and doesn't mention it either. **The CSV was authored before the field was added to the frame.** Verified live via `query_by_type(TEXT)` on the screen — the real node tree is authoritative. Frame wins. Recorded as an unresolved gap: no test case covers this field.

**The Tiêu chuẩn cộng đồng link:** `reports/design-source-analysis.md` (written early) claimed it had "no design source at all." An implementer re-measured and found it at nodes `I520:11647;3053:11619` / `I520:11647;3053:11621`, parented by a Button, at exactly x 805–996 on the toolbar's right side — exactly where the frame renders it. The report was wrong. **Measured design data outranks any prose summary of it, including the orchestrator's.**

### Defect 6: `@Nguyen` vs `Nguyễn`

Test case `ID-33` has authored `Test_Data` as `"@Nguyen"` (no diacritics), but seeded sunners are `Nguyễn …` (with diacritics). A diacritic-sensitive filter found nothing and the test failed correctly. Fixed with an NFD fold — a Unicode normalization that decomposes `ễ` and `đ`/`Đ` into base + combining mark, so both match.

### Defect 7: Security decisions worth recording

- **`create_kudos` takes no `sender_id` parameter** — the actor is resolved from `auth.uid()` inside the function body. A forged sender is unrepresentable, not merely rejected. Confirmed live: `prosecdef = f` (verified via `pg_functions`) means RLS policies still apply inside the function — it's not a privilege-escalation hole.
- **XSS in the rich-text renderer:** Never touches `dangerouslySetInnerHTML`. `parseKudosDoc` walks the document into React elements and checks link schemes against an allow-list (`http:`/`https:`/`mailto:`) **twice** — once in the parser, once again at render time. Verified by reading the code, not a report.
- **Route guard is exact-path:** `isGuarded` checks `pathname === "/kudos/new"`, never a bare `startsWith()`. Cannot catch `/kudos`, `/kudos/[id]`, or `/kudos/secret-box` — the public read surface stays public.
- **Anonymity is display-layer only:** `sender_id` is still stored in the database, so it's not anonymity from the system — just from the public board. Documented in `docs/system/permissions.md` deliberately.

### Defect 8: Study's recommendation overridden on evidence

The write-path study recommended reusing committed sample images rather than building real Storage upload. That study had no MCP access and so hadn't seen test cases `ID-37`, `ID-21`/`ID-22`, `ID-23`/`ID-24`. They require:
- `ID-37`: the *picked file* appears as a thumbnail (not a stock image)
- `ID-21`/`ID-22`: a real `.jpg` and `.png` upload successfully
- `ID-23`/`ID-24`: a `.pdf` is rejected with a format error

Substituting a sample image would have made the thumbnail a lie and would have made `ID-37` fail honestly. Implemented real Storage upload with magic-byte sniffing — `matchesImageSignature()` checks JPEG `FF D8 FF`, PNG `89 50 4E 47 0D 0A 1A 0A`, GIF `47 49 46 38`, WEBP `RIFF`...`WEBP` against the first 12 bytes of the file. A `.pdf` with bytes `25 50 44 46` is now rejected even if the browser declares it `image/jpeg`.

## What We Tried

1. **Blamed K-25 on 2-worker contention and timeouts** until a later run showed it failing at 25.4s inside a raised 60s timeout, disproving the load theory. The timeout changes stayed but didn't fix the issue.

2. **Blamed a dev server crash** until other test suites passed in the same invocation where K-25 failed, proving the server was up.

3. **Escalated to "infrastructure can't sustain 88 concurrent tests"** until reading `e2e/homepage-auth.setup.ts`'s own header comment and realizing the fix was a two-line session isolation.

4. **Grepped the compose spec for the `toHaveCount` calls** until the full import was re-read and the actual assertion signature was verified against Playwright's type definitions.

5. **Debugged the diacritic-matching filter** by adding a test case with `"@Nguyễn"` and confirming it matched the existing `@Nguyen` query — leading to the NFD normalization fix.

## Root Cause Analysis

**Three patterns converge:**

1. **Assertions broken at authorship, not implementation:** The E2E author wrote `toHaveCount(async fn)` calls that are unreachable by Playwright's own type signature. Typecheck caught 12 errors and they were fixed before implementation, but six assertions stayed broken because they still typed-check — the method signature accepts no-argument overloads that do different things, and the `async fn` form is a red herring. Testing against the wrong assertion is worse than no test, because the suite can be green while the thing being tested is broken.

2. **The repo's own answer was written down but not referenced:** `e2e/homepage-auth.setup.ts` solved the shared-session problem, and its comment says so explicitly. But three successive diagnoses invented new theories instead of reading that header.

3. **Design source diverged from authored CSV:** The frame evolved, but the spec and test-case CSVs were not refreshed. Multiple sources of truth for the same screen (frame, CSV, authoritative file path) means the CSVs age while the frame stays live. Measured data (MCP query results) beats any report's prose summary.

## Lessons Learned

1. **A passing test does not mean the assertion is reachable.** Playwright has multiple method overloads (e.g. `toHaveCount(count)` vs `toHaveCount(callback)` in the docs, but only one in the actual `.d.ts`), and passing the wrong one gives a confusing failure. Verify the type signature against the `.d.ts` before trusting the assertion structure — especially for load-bearing tests.

2. **Read the existing code before theorizing.** K-25's diagnosis would have taken two minutes to resolve by reading `homepage-auth.setup.ts`. Instead it took three wrong theories and two timeout escalations.

3. **Shared session state between test files is a defect waiting.** Every auth-gated feature now needs its own Playwright setup project so one test's sign-out cannot revoke another's session. This is a pattern now, not a one-off fix.

4. **Design source beats prose.** When a frame, a CSV, a report, and a test case all say different things, the authoritative source is the one that was measured most recently — in this case, the live node tree queried via MCP. Update the CSV or mark it stale, but don't let old prose block the real source.

5. **The Danh hiệu gap is real.** This field is in the frame but not in the spec CSV or test cases. It ships on the frame's authority alone. Before the next write form lands, refresh the spec sheets to catch up with the design.

## Next Steps

### Immediate (done)

- [x] Repair six `toHaveCount(async fn)` assertions to `.first().toBeVisible()` — strictly stronger, actually reachable.
- [x] Fix test-case contradiction: button is never `disabled`, carries `data-submit-ready` signal instead.
- [x] Add `kudos-auth.setup.ts` and give `kudos-authed` its own session to isolate from `authenticated.spec.ts`'s global sign-out.
- [x] Fix `afterEach` to delete by `kudos_id` instead of a stale hardcoded `auth_user_id`.
- [x] Implement real Storage upload with magic-byte sniffing (closes reviewer's Finding 2).
- [x] Add image-cap check to `validateCompose()` for field-specific errors (closes reviewer's Finding 1).
- [x] Trim `compose-form.tsx` and `board-data.ts` under 200 lines (closes reviewer's Finding 3).
- [x] All 63 compose tests re-confirmed green. Full 10-file suite 144 passed, twice consecutively.

### Documentation (deferred, not blocking)

1. **Spec sheets are stale.** `design/specs.csv` is 26 items and missing `Danh hiệu`. `design/test-cases.csv` is 57 cases and doesn't mention it either. Run `/tkm:rebuild-spec --artifact specifications` to regenerate from the live frame.

2. **Test cases are incomplete.** The 57 cases cover the form's behavior but leave `Danh hiệu` untested, anonymous display-name untested, and the two companion frames (`zJzaC9GgXt` recipient dropdown, `5c7PkAibyD` error state) untested. Needs a design/spec pass to close these gaps.

3. **`docs/generated/entities.md` is wholesale stale.** The premise (zero tables) is now false after F004. Run `/tkm:rebuild-spec --artifact entities`.

4. **`docs/generated/user-stories.md` has no F005 entries.** Add US017–US022 plus Screen→US map.

5. **INSERT-policy precedent.** This migration's RLS shape is now the pattern every later write table will copy. Worth a human review before it propagates.

### Unresolved (recorded in clarifications.md)

- `Danh hiệu` error copy and max length unauthored
- Character counter promised in spec but not drawn (`D.1` is stale)
- Anonymous display-name field's label/placeholder/validation unauthored
- Editing and deletion deliberately absent (separate commissions)
- Form-level errors have no UI surface (`errors.form` is set but unrendered)

---

**Status:** DONE
**Summary:** F005 delivered with 63-test compose gate passing twice consecutively, 144-test full suite green, zero inspection critical findings. Unearthed two severe E2E defects in authored assertions (six unreachable `toHaveCount(async fn)` calls, two contradictory test cases on button disabled state) and one cascade of three wrong K-25 diagnoses (contention/timeout, server crash, infrastructure limits) when the actual cause was shared session state — already solved by a pattern in `homepage-auth.setup.ts` that was written but not consulted. Design source diverged from authored CSV in two directions (Danh hiệu added to frame but not spec, Tiêu chuẩn cộng đồng called unauthored when it has a real node). All findings closed; all open gaps recorded in clarifications.md. Five conventional commits landed locally; not pushed. Full delivery tracking and evidence in `plans/260907-0822-viet-kudo/`.
**Concerns/Blockers:** None. Session tracked working tree vs uncommitted state (migration+seed+types is ~4000 lines — will batch into feature commit when ready to push). Spec sheets need refresh to catch up with design evolution.
