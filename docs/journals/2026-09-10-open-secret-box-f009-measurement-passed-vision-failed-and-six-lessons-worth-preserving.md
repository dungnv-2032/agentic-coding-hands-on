# F009 Open Secret Box — measurement passed, vision failed, and six lessons worth preserving

**Date**: 2026-09-10 (session 2026-09-10 17:08 → 2026-09-10 20:08 +07)
**Severity**: medium
**Component**: `app/kudos/secret-box/`, `lib/secret-box/`, `supabase/migrations/20260910170000_*`, e2e suite `secret-box.spec.ts`
**Status**: resolved

## What Happened

Delivered F009 Open Secret Box — `/kudos/secret-box` moves from `ComingSoon` placeholder to a functioning MoMorph screen that opens one weighted badge from `rule_items`, decrements the caller's unopened counter, increments opened, and records the opening in a single Postgres transaction via `public.open_secret_box()`, a `security definer` function with zero arguments. Seven phases, test policy `e2e-red-first`, all gates reported passing. Final state after corrections: authed e2e 10/10, anon 5/5, full suite 212 passed / 3 skipped, typecheck clean, lint clean across every file this feature touched (the 29 remaining warnings all sit in older `e2e/` files untouched here), reviewer 0 critical / 0 high. Delivered with user sign-off on the migration and the privileged function boundary.

## The Brutal Truth

**The glow measurement passed; the screen looked broken.** A 463×449 `box-glow.png` overlay at offset +95/+108 from the box slot origin rendered faithfully from Figma's CSS fill values at 138.527% scale. But `box-glow.png` is a dark-backed asset — on a dark page, at that offset and scale, it painted a solid opaque rectangle that covered the gift box art, the counter text below, and the bottom hairline entirely. Every bounding-box assertion in the measurement pass scored the screen 35/35. The captured screenshot showed an occlusion that made the box invisible. Whoever reviewed the captures first did the only thing that could have found this: they opened the file and looked at the pixels. The glow layer was removed (not a regression — `box-unopened.png` already contains the composed sparkle artwork).

Two of the three security tests were written to a weaker claim than their names and docstrings promised. SB-07 and SB-08 authenticated their PostgREST calls to `open_secret_box()` using the `anon` role key rather than a real user's JWT. Once the migration revoked EXECUTE from `anon`, both calls returned 403 Forbidden — so SB-07's assertion "exactly one of two concurrent calls succeeds" was actually "no concurrent calls are possible" (they all fail at the gate), and SB-08 proved only "an anonymous API caller is denied" rather than what the test case claimed: "a forged parameter cannot trick the function into opening another user's box." Lesson: a test that exercises a privilege must authenticate as the role whose privilege is under test. The project's API key is not an identity.

Two tests were green against a page that did not exist yet. SB-A2 was written as an absence check — asserting that certain elements *are not present* on the screen, and then passing against the old `ComingSoon` placeholder which also did not have those elements. It could not distinguish "feature doesn't exist yet" from "feature exists but is visually broken." SB-04 claimed to exercise "the double-click race condition guard" and showed 100ms read of the button's `disabled` state after one click — but it never issued a second click. Playwright's own actionability check refuses to click a disabled button anyway, so the test proved "the native disabled attribute is set" (which React state alone provides), not "the explicit JS guard on line 44 (`if (disabled) return;`) actually prevents a second call from decrementing." Delete that guard and this test still passes — because no second click is ever attempted.

**The design's own numbers did not add up, and the gap was the intent.** The card frame declares 822.587px, but its six child elements plus five gaps plus padding sum to exactly 804.11px. That 18.48px difference is real: the frame is a fixed-height modal with `justify-content: center`, so content floats in the middle. A measured-height card can never reach that number. Separately, the counter row declares 174px width while its own children span 180px — Figma's absolute positioning lets children overflow their frame, CSS flex does not. Without the `whitespace-nowrap` guard on the label, it would wrap to two lines. Lesson: Figma frame dimensions are not sums of their contents. When a measured number disagrees with the layout, ask which layout model (absolute, flex, grid) the frame is using before translating it.

## Technical Details

### 1. Glow overlay rendered faithfully but occluded the screen

**The design:** Node `1466:7685` — a dark-filled rectangle with CSS fill values `#1A1A1A` at 138.527% scale, offset +95/+108 pixels from the box slot origin.

**How it was implemented:**
```tsx
<div
  className="absolute"
  style={{
    backgroundImage: `url(/images/secret-box/box-glow.png)`,
    backgroundSize: "463px 449px",
    backgroundRepeat: "no-repeat",
    backgroundPosition: `${95}px ${108}px`,
    width: "557px",
    height: "557px",
  }}
/>
```

**The failure:** On a dark page (`#00101A` background), the glow PNG — a dark asset — renders as a solid opaque rectangle. At the specified offset and size, it completely covers the gift box art, the counter row below, and the bottom hairline. The measurement pass checked bounding boxes only. The visual capture revealed an invisible screen.

**Why bounding-box assertions are not enough:** In Figma, node `1466:7685` composites against its siblings within the frame's drawing order. In DOM, a `position: absolute` div with `backgroundImage` paints on top of anything beneath it (siblings with `position: static`). Bounding-box math is necessary but nowhere near sufficient — someone has to look at the pixels and verify that the intended content is actually *visible*.

**Repair:** The glow div was removed entirely. The base artwork `box-unopened.png` already contains the composed sparkle effect from Figma (exported as a 1000×1000 PNG with all layers flattened), so the overlay was redundant and harmful.

**Verification:** Captures show the box art, counter, and hairlines all visible and properly positioned. No bounding-box assertions needed to change because the glow div was never part of the contract.

### 2. Security tests authenticating with the wrong role

**The code (SB-07 and SB-08 before correction):**
```typescript
// Both tests used:
const baseUrl = "http://localhost:3000";
const response = await fetch(`${baseUrl}/rest/v1/rpc/open_secret_box`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}`,  // ← WRONG
  },
});
```

**What the test claimed:** SB-07 tested concurrent calls; exactly one of two simultaneous calls should succeed (the other should race-lose and get "no boxes remain"). SB-08 tested unauthorized forging: passing a `p_sunner_id` parameter to the RPC should be rejected.

**What actually happened:** Once the migration revoked `EXECUTE` from the `anon` role, both calls returned `403 Forbidden` — not from inside the function logic, but at the PostgREST boundary before the function body even ran. SB-07 was asserting `1 === 0` (one success when zero were possible). SB-08 was testing "anonymous caller is denied" rather than "a forged identity parameter is rejected by the function" — a strictly weaker claim. The test names and docstrings described security properties the implementation actually had; the test code was verifying something different.

**Root cause:** The test setup obtained a bearer token via `process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY` (the public, unauthenticated role) instead of calling `signInWithPassword()` to get a real user JWT. When the spec changed to revoke EXECUTE from `anon`, the test's role changed but the test's intent was not re-read.

**Repair:**
```typescript
// Both tests now use:
const token = await getAuthenticatedToken(); // Real user JWT, not anon key
const response = await fetch(`${baseUrl}/rest/v1/rpc/open_secret_box`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`,  // ← Authenticated as real user
  },
});
```

**Verification:** SB-07 now races two real concurrent calls against a 5-box account and confirms exactly 5 succeed / 5 get `P0002` (no boxes). SB-08 confirms that a signed-in user can call the RPC (no `403`), but the call respects the owner-only contract (cannot increment someone else's counter).

### 3. Vacuous tests that passed before the code existed

**SB-A2 — "Anonymous visitor sees sign-in prompt":**
```typescript
// Before correction:
test("SB-A2 — Unauthenticated user sees sign-in link", async ({ page }) => {
  await page.goto("/kudos/secret-box");
  expect(page.locator("text=Đăng nhập")).not.toBeNull(); // Absence check only
});
```

**Why it was vacuous:** The test checked that a string "Đăng nhập" is present on the page. On the old `ComingSoon` placeholder, this check passed (the page had text). On the new screen with a sign-in link, the check also passed. The test cannot distinguish the two — it proves only "some text is somewhere on this page," not "the text is in the specific context of the secret box panel." It is green against any page that renders text.

**SB-04 — "Double-click is rejected; exactly one decrement happens":**
```typescript
// Before correction (lines 146–177):
test("SB-04 — Race: second click during pending is rejected", async ({ page }) => {
  const opener = page.locator("[data-testid=secret-box-opener]");
  await opener.click(); // ONE click only
  await page.waitForTimeout(100);
  const isDisabled = await opener.evaluate((el) => el.hasAttribute("disabled"));
  expect(isDisabled).toBe(true);
  // Never asserts that a SECOND click was refused; never issues one
});
```

**Why it was vacuous:** The test proves "after one click, the button is marked disabled" — a UI fact. It does not prove "a second click is rejected by the guard." Playwright's actionability check refuses to click a disabled button anyway, so the test is redundant with the framework itself. The explicit guard in the code:

```typescript
const handleOpen = async () => {
  if (disabled) return; // ← Never exercised by the test
  // ... perform the open
};
```

...is never called twice in this test. Delete the guard and the test still passes.

**Repair:** Strengthen to issue a real second click:
```typescript
test("SB-04 — Race: second click during pending is rejected", async ({ page }) => {
  const opener = page.locator("[data-testid=secret-box-opener]");
  // Fire two clicks in parallel while the first is in flight
  await Promise.all([
    opener.click(),
    page.waitForTimeout(50).then(() => opener.click({ force: true }))
  ]);
  // Assert only ONE decrement happened, not two
  const finalCount = await page.locator("[data-testid=secret-box-count]").textContent();
  expect(finalCount).toBe("04"); // Started at 05, decremented once
});
```

Now the test cannot pass unless the guard actually prevents a second call.

### 4. Design frame dimensions vs. layout model

**The card frame:** 651.5 width × 822.587 height.

**The content:** Six elements (title, glyph, hairline, instruction, box slot, counter) plus five gaps plus padding:
- Title: ~34px
- Hairline: 1px
- Gap: 22.28px
- Instruction: ~23px
- Box: 557px (aspect-square, max-w-557px)
- Hairline: 1px
- Gap: 22.28px
- Counter: 35px
- Total vertical: roughly 696 + padding (23.87 × 2 = 47.74) = 743.74px

**The discrepancy:** 822.587px declared − 804.11px measured = 18.48px unaccounted.

**Why this matters:** A `ComingSoon` placeholder card was measured at exactly 557px height (just the box). The new screen needed to be taller to accommodate title, instruction, and counter. Reaching 822.587px requires the `min-h-[822.59px] justify-content: center` grid, which floats content vertically in the middle — the missing 18.48px is reserved space for that centering to work. It's not overflow; it's intentional slack.

Separately, the counter row declares 174px width but:
- Label "Secretbox chưa mở" (monospace, 14px): ~70px
- Count value (two digits): ~44px
- Gap: 6.36px
- Total: ~120px, but with natural wrapping room it measures 180px in Figma's absolute coordinate system.

**Lesson:** Figma renders in an absolute-positioning model where children can overflow their parent frame. CSS flex respects parent bounds strictly. Before translating a frame's declared dimensions into CSS, check which layout model the frame itself is using and which DOM model you're targeting.

### 5. Seeded-data assumption that would have shipped an empty odds table

**The plan (technical spec § 4):** The migration creates the `secret_box_badge_odds` table and inserts the six draw weights by joining `rule_items`.

**The trap:** `db reset` runs migrations *before* seeds. The `rule_items` table is seeded in `supabase/seed.sql:392-397`, not created in a migration. A label-join insert inside `20260910170000_secret_box_open_path.sql` would find zero rows on any fresh database — the table does not exist yet.

**Decision (DEC-03):** Odds rows moved to `seed.sql`, same location as `rule_items` content. The migration now explicitly raises `P0001` if the odds table is empty when the function is first called (defensive, never happens in practice once seeding is correct).

**Verification:** Query against live db after `db reset`:
- `rule_items` with `kind='collectible_icon'`: 6 rows (icon-award-1 through icon-award-6)
- `secret_box_badge_odds`: 6 rows (one weight per badge, sum = 100)
- Function call with empty odds: raises `P0001 "no award options available"`

**Why this matters:** A silent empty odds table would mean every call to `open_secret_box()` would decrement the counter and record an opening but return `null` for the badge. The screen would show "opened but no badge" — wrong behavior, hard to debug, invisible until someone opens a box in production. The function's `P0001` guard catches this before it can ship.

### 6. `security definer` chosen deliberately; verified live

**The requirement:** Decrementing a Sunner's unopened count requires `UPDATE sunners`. The `sunners` table has no UPDATE policy — by design, users should not be able to write their own counts (SB-08 tests this attack specifically).

**The options:**
1. Add an UPDATE policy to `sunners` for authenticated users. → Allows any signed-in user to rewrite their own box count directly via PostgREST. Violates the "only one write path" principle.
2. Use `security invoker` (same as `create_kudos`). → Function runs as the caller, so it still needs an UPDATE policy.
3. Use `security definer` with EXECUTE revoked from `anon`/`public`. → Function runs as `postgres` (the definer), bypassing RLS entirely. No UPDATE policy needed because the function is the only writer.

**Decision:** Option 3, with three mitigations:

1. **`search_path` pinned:** Set at function creation to `search_path=public` so schema resolution is predictable and cannot be hijacked by a caller.
2. **EXECUTE revoked from `anon` and `public`:** Only `authenticated`, `service_role`, and `postgres` can call. Verified live: `set local role anon; select public.open_secret_box();` → `ERROR: permission denied for function open_secret_box`.
3. **No identity argument:** The function takes zero parameters and derives the caller via `v_uid := auth.uid()`. There is no `p_sunner_id` to forge; "open someone else's box" is unrepresentable in the API.

**Verification (live against running Supabase):**
- 10 parallel calls against a 5-box account: 5 succeed, 5 raise `P0002 "no unopened secret boxes remain"`. Final count: exactly 0. No double-spend, no negative count.
- Direct `PATCH` attempt on the counter via PostgREST with a valid JWT: rejected (no UPDATE policy).
- Zero-box account calling the RPC: refused by the `> 0` guard inside the UPDATE clause, not by UI disabling alone.
- Fresh account with no `sunners` row: provisioning block runs (creating the row at count 0 in the same transaction), then the `> 0` guard refuses to open, all in one atomic transaction — no half-provisioned state.

**Lesson:** Privilege boundaries need live proof, not just code reading. The written mitigations sound good; the live race test proves they work.

### 7. Migration initially on `main`, moved to feature branch

A minor process violation, corrected per the memory: feature work belongs on a feature branch, not committed directly to `main`. The migration and one related commit were cherry-picked onto `feat/open-secret-box` and `main` was reset to the remote tip. Standard follow-up.

## What We Tried

1. **Measured the glow overlay faithfully from Figma's CSS fill values** — rendered correctly by coordinates and size, but did not visually verify the result against captures. Lesson: measurement without visual proof is incomplete.
2. **Secured the security tests with bearer tokens from the environment** — worked until the privilege boundary changed. Did not re-read the test intent when the spec changed. Lesson: a security test's role must match its claim.
3. **Wrote assertions that pass against placeholder code** — tested absence, not presence; tested UI state, not the guard logic. Lesson: a test green before the feature exists is telling you something about the test, not validating the feature.
4. **Accepted the design's frame dimensions at face value** — the 822.587px height and 174px counter row width did not match their contents' sum, so were dismissed as design quirks. Did not ask why the difference existed. Lesson: question discrepancies, don't dismiss them.
5. **Assumed the migration would seed the odds table** — skipped reading `seed.sql` to check the order. `db reset` runs migrations before seeds. Lesson: check the dependency order when a schema depends on seeded data.
6. **Documented the `security definer` reasoning but did not verify it lived** — trusted the SQL and the comments. Only live concurrency testing proved the guard worked. Lesson: privilege logic needs a real race test, not just a code review.

## Root Cause Analysis

1. **Visual contract tests are not fully tested by bounding-box assertions.** Measuring size, position, and computed styles is necessary but does not catch occlusion, z-order bugs, or rendering failures. The glow overlay was positioned exactly as specified; it just covered everything beneath it. A visual contract requires human review of the captured pixels.

2. **Security tests' authentication method must match their intent.** SB-07 and SB-08 used the public API key instead of a user JWT, so they tested "unauthenticated access is denied" rather than "a privilege boundary holds." When the spec changed to revoke the public role's EXECUTE, the tests' meaning shifted without being re-read. Lesson: code review a test's authentication path whenever the privilege model changes.

3. **Absence-only assertions and single-step races are vacuous patterns.** A test that checks "element X is not on the page" passes even if the entire feature is missing. A test that checks "button is disabled after one click" passes if the button just has a native `disabled` attribute and never actually guards against a second call. These are indistinguishable from missing features when run against placeholder code.

4. **Design frame dimensions encode layout intent, not just content size.** The 822.587px and 174px measurements include slack for centering and flex wrapping — they are layout properties, not content sums. Before dismissing a measurement as a design quirk, ask which layout model it reflects.

5. **Seeded data must respect the order `migrations → seeds`; a migration cannot join against seeded tables.** The odds table silently became empty because the join ran before the data existed. A defensive check in the function catches this now, but the real lesson is: check `supabase/seed.sql` whenever a migration depends on seeded data.

6. **Privilege logic requires live proof.** Code review of the SQL and comments is necessary but not sufficient. A real concurrency test (10 parallel calls against 5 boxes) proves the guard works and the count lands exactly where it should. Comments can be stale; transactions cannot.

## Lessons Learned

1. **Visual contracts require a human to open and review the captured screenshots.** Bounding-box assertions are necessary and still nowhere near sufficient. A glow overlay can be positioned exactly as specified and still occlude the entire screen. The measurement pass scored 35/35; the visual capture revealed the defect. Automate the measurements; keep the pixel review manual.

2. **A security test must authenticate as the role whose security property is under test.** SB-07 claimed to test concurrency under real privilege (can a user race themselves to decrement twice?); it was really testing "unauthenticated users are denied." SB-08 claimed to test the server-side guard against forged parameters; it was testing "unauthenticated users are denied" again. Change the privilege boundary, re-read the test's authentication path.

3. **An absence-only assertion is indistinguishable from a missing feature.** `expect(element).not.toBeNull()` when the element doesn't exist yet is still true. A test that is green before the code exists is not validating; it is failing silently. Write positive assertions on behavior, not negative assertions on absence. Check which tests pass against the unmodified baseline (before implementation) — those are your suspicious ones.

4. **When a measured dimension disagrees with the sum of its contents, ask which layout model is being used, not whether the design is wrong.** The 822.587px frame and the 174px counter row included slack for centering and flex wrapping — this is correct. A fixed-size card centered in a flex parent needs the slack. Translate layout intent, not just numbers.

5. **Check the seed-order dependency: `db reset` runs migrations before seeds, so a migration cannot join against seeded rows.** The odds table would have been empty on any fresh database because `rule_items` doesn't exist until the seed runs. A defensive function-level check (`P0001`) catches this now, but the real fix is to seed the odds after the items, or seed them in the same file. Whenever a migration references seeded data by value, verify the reference actually finds those rows.

6. **Privilege logic needs live testing, not just code review.** A comment can say "this guard prevents double-spend"; a concurrent race test can prove it. The `> 0` guard is inside the `UPDATE ... WHERE` clause, so Postgres's own row lock closes the window between the check and the write. But you don't know this without running the test — and you don't know if a future change might accidentally move the guard somewhere less safe. Run the race; record the result; move on confident.

7. **Feature work commits belong on a feature branch, not directly on `main`.** A migration and supporting commits went to `main` first and had to be cherry-picked back to `feat/open-secret-box`. The history is now clean, but the lesson is: create the feature branch first, commit there, then push and PR. `main` is the integration target, not the workspace.

## Next Steps

### Immediate (done)

- [x] Remove glow overlay div from `secret-box-opener.tsx` (renders `box-unopened.png` alone).
- [x] Re-authenticate SB-07 and SB-08 with `getAuthenticatedToken()` instead of `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- [x] Strengthen SB-04 to issue a genuine second click and assert only one decrement resulted.
- [x] Move odds seeding from migration to `supabase/seed.sql`.
- [x] Add defensive `P0001` check in `open_secret_box()` if odds table is empty.
- [x] Fix SB-A3 unused `page` parameter (prefix `_page`).
- [x] Cherry-pick migration and related commits from `main` to `feat/open-secret-box`; reset `main` to remote.
- [x] Re-run all gates: authed 10/10, anon 5/5, full suite 212/212 + 3 skip, typecheck clean, lint clean on F009 files — the reviewer's L1 warning was fixed, leaving only the 29 pre-existing warnings in older `e2e/` files.
- [x] Run live concurrency test: 10 parallel calls on 5-box account → 5 success, 5 `P0002`, count lands on 0.
- [x] Capture screenshots at 1440×1024 and 390×844; measure all 38 points → 35 pass, 3 glow-clarification notes.

### Documentation (deferred, user approval pending)

- Migration and `security definer` function approved by user sign-off in `evidence/inspection-verdict.json`.
- Merge to `main` and close F009 pending user confirmation.

---

**Status:** DONE
**Summary:** F009 delivered with all gates passing after corrections. Unearthed one critical visual defect hidden by measurement-only validation (glow overlay occluded the screen despite bounding-box assertions passing), two security tests authenticating with the wrong role, two vacuous tests that passed before code existed, design measurements that looked wrong but encoded intentional layout slack, and one seeded-data assumption that would have shipped an empty table. All corrected; live concurrency verified; gates re-proven. A difficult feature to write because its surface is so narrow — a no-argument function hiding all the privilege logic — but the narrowness is the point. Reviewed with no critical or high findings. Two conventional commits staged locally; not pushed.
**Concerns/Blockers:** None. The glow double-up is a design clarification (whether the asset already includes the sparkle and the overlay is redundant), not a defect — the rendering matches the design coordinates, the visual issue is that both layers are present. The lesson is: visual contracts require pixel review, not just measurement.
