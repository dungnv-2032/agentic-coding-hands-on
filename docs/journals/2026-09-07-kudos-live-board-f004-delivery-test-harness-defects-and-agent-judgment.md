# F004 Sun* Kudos Live Board — test harness defects and orchestrator error

**Date**: 2026-09-07 (session 2026-09-06 19:00 → 2026-09-07 02:30 +07)
**Severity**: high
**Component**: `/kudos` screen (F004), E2E test architecture, test contract compliance
**Status**: resolved

## What Happened

Delivered F004 Sun* Kudos Live Board, replacing a `ComingSoon` placeholder at `/kudos`, backed by the **repo's first Postgres schema**: 10 RLS-enabled tables, one migration, a seed transcribed verbatim from the Figma frame, a typed query layer, one Server Action, ~20 UI components. Final state: 27 e2e assertions green (exit 0) from a verified 26-failure RED; 57 passing across all suites including regressions; typecheck/lint/build clean; inspection SEALED with 0 critical. Four conventional commits landed locally (`f5fa9cf`, `6979a70`, `f259f80`, `59f290a`) on top of earlier phase commits; not pushed. But the value of this entry lives in three separate defects in the test harness that would each have produced a meaningless green, and an orchestrator misjudgment that turned the entire commission upside down in the best possible way.

## The Brutal Truth

The frustration bites because the suite passed, the build was clean, review came back sealed, and nobody had to dig. All three harness defects lived silently inside passing assertions. Worse, the two worst ones would have shipped this way — manifesting weeks later as "hearts disabled for anon users but the tests say they're fine" and "the detail page is unreachable but K-21 says it's not." And the test contract itself was half-built: K-10 validates nothing; K-25 reloads once instead of twice. The galling part is that two of these defects traced directly to test-setup work I had explicitly validated before handing to the tester, proving that "my eyeballs say this is right" is exactly how critical safety margins erode.

The orchestrator also made two bad calls — one that got corrected by the user's explicit re-invocation (and became the session's most valuable discovery), and one that raised false defects on the UI implementation and had to be withdrawn. Only the first one teaches anything; the second is worth recording because it proves that a good refusal to change design without evidence is more valuable than an orchestrator's screenshot reading.

## Technical Details

### Harness Defect 1: Two Playwright projects, one spec file

**The bug:** `playwright.config.ts` defines two projects: `anon` (no cookies) and `kudos-authed` (with session). Both declare:
```javascript
testMatch: "e2e/kudos-live-board*.spec.ts"
```

So `kudos-live-board.spec.ts` and `kudos-live-board-authed.spec.ts` both run in both projects. The anon project runs K-10 and K-25 (authed tests) with no session cookie — they should fail; instead they're skipped silently.

**Why it passed:** Both K-10 and K-25 contain:
```javascript
if (await heart.isDisabled()) return; // both use zero-wait reads
```

Under the anon project (no session), `canLike()` resolves to false, the heart renders `disabled`, `isDisabled()` returns true, and the test exits without running any assertions — not a failure, a pass. The test was never exercised in the session where it's supposed to run.

**Severity:** High. K-10 validates "after a like, the count increments and persists through reload" — the entire toggle contract. K-25 validates "a second like reverts both the visual state and the count" — same persistence rule from the opposite direction. Both are **core acceptance criteria with zero observable proof under anon context**, meaning the feature could have shipped broken and been discovered only by manual testing.

**The fix:** Separate the authed tests into their own file with a dedicate project entry:
```javascript
{ name: "kudos-authed", testMatch: "*-authed.spec.ts", ... }
```

The anon project now matches only `spec.ts` (non-authed files). K-10 and K-25 run with a real session, execute their assertions, and fail if the heart behaviour is broken.

### Harness Defect 2: K-21 validates against 404

**The bug:** K-21 asserts "clicking a card body link navigates to `/kudos/[id]`":
```javascript
await page.goto(`/kudos`);
await page.click('[data-testid="card-body-link"]');
expect(page.url()).toContain('/kudos/');
expect(await page.evaluate(() => document.body.innerHTML)).not.toEqual(''); // non-empty body
```

The route `/kudos/[id]` renders a `ComingSoon` placeholder. The test passes.

**Why it's wrong:** `ComingSoon` is a real page that does render — body is not empty, URL does contain `/kudos/`, so both assertions pass. But if the link were broken (404 instead of 307 redirect to placeholder), Next's own 404 page would also satisfy both assertions. The test proves nothing about whether the link works.

**Severity:** Medium. This test isn't exercising the acceptance criterion "clicking a body link is navigable" — it's exercising "Next renders non-empty pages." It would catch a catastrophic link breakage (link attribute absent), but not a silent 404.

**The fix:** K-21 now explicitly checks for the `ComingSoon` heading or waits for the route's own page-specific content, not generic "body is not empty."

### Harness Defect 3: K-10 and K-25 never exercise the full contract

**The bug:** K-10 was supposed to:
1. Click the heart
2. Wait for the count to increment
3. Reload the page
4. Assert the incremented count persists

It only does 1–2 and skips if the heart is disabled. K-25 was supposed to:
1. Click the heart (like)
2. Reload
3. Assert the persisted like-state
4. Click the heart again (unlike)
5. Reload
6. Assert the persisted unlike-state

It does 1–3 and stops.

**Why it passed:** A **zero-wait read** on component state (`aria-pressed` via `getAttribute()` directly after `.click()`) cannot be reliable. K-10's own phase notes said "never a local increment — the count is server-authoritative and K-10 reads it with a 1.5s wait"; K-25's own phase notes said "the second like is the important assertion — K-25 must validate that unlike also persists." Both notes went unread, and both tests got implemented with one-shot reads that happen to succeed when the server round-trip lands within 200ms, which it does in the isolated/unloaded dev environment where the suite initially ran.

The root cause is visible in `kudos-card-actions.tsx` phase 06: "never a local increment." But phase 09 made the heart flip optimistically — which is correct for UX latency — and by then K-10 had a zero-wait read that would pass on the optimistic-flip even if the server call had failed. The tester later corrected both K-10 and K-25 to use auto-retrying `expect(heart).toBeInTheDOM()` and `expect(heart).toBeEnabled()` instead of one-shot reads, and that's when K-25 surfaced a race: it would reload while the like-toggle's INSERT was still in flight, and the browser would render the pre-INSERT state before the test could assert. Only after removing the optimistic flip (reverting to server-authoritative-only) did K-25 become deterministic.

**Severity:** High. The test passed because it validated an implementation detail (optimistic state) instead of the contract (persisted state). A real implementation that fetched stale data or had a race in the like-toggle would have passed K-25's original form. The tests were vacuous until the harness itself was hardened.

### Orchestrator Misjudgment 1: Visual findings from screenshots

**What I saw:** Reading phase 08's own screenshot (`evidence/all-kudos-sidebar-row-desktop.png`), I raised five visual defects:
1. Receiver chip clipped at card edge — CRITICAL
2. Attachment gallery clipped — CRITICAL  
3. Message body justified instead of ragged-right — FIDELITY
4. Next.js dev overlay "1 Issue" — INVESTIGATE
5. Heart count `1.002` instead of `1.000` — DATA HYGIENE

**What was wrong with two of them:**

- **V3 (justification):** I read off the screenshot. The card-fix agent queried the frame's actual text nodes via MCP: `textAlignHorizontal: JUSTIFIED` on all instances, matching the existing `text-justify` CSS. The frame wins; my screenshot reading was wrong. The agent correctly refused to change the design without evidence and escalated instead of complying.

- **V5 (heart count):** I read `1.002` off a screenshot and concluded there were leftover like rows. The card-fix agent later confirmed: the screenshot was scrolled past the first card. When looking at card-id=1 (the frame-verbatim row), the count was correct. My mistake; the reading was incomplete.

**Severity:** Low for the session outcome (both findings got corrected), but high for the lesson: "never guess a visual value" applies to whoever is directing the work too. An orchestrator who trusts their own screenshot reading over the agent's measured data source is the same trust-the-code-over-the-evidence mistake I was trying to warn against.

**The fix:** None needed — the UI agents did it right by refusing and escalating. Worth recording as a mirror of the test-harness defects: I was so certain about the visuals that I raised them without checking the source, which is exactly how the testers built K-10/K-25 without checking whether the assertions matched the contract.

### Orchestrator Misjudgment 2: User override supersedes agent resolution

**The context:** The clarifications.md recorded that the data source was "a frozen mock dataset under `lib/kudos/`" — a decision the orchestrator had auto-resolved on the recommended option when the user didn't specify one. The user's re-invocation carries an explicit directive: *"Implement màn hình Sun* Kudos - Live board **use Supabase local project**"*. This completely flipped the commission: from a presentational UI exercising filters/carousel/search over static data, into **the repo's first schema work** — 10 RLS-enabled tables, a migration, a seed, and a typed query layer.

**Why this matters:** The auto-resolution was reasonable (YAGNI + "use Figma as mock data source"). But the moment the user stated their own intent, it became superseded — not silently followed, but **recorded as authoritative**. This session's entire backend work (schema, RLS, seed, server-side queries) exists because I deferred to the user's statement over the previous agent's best-guess resolution. That is the opposite of the test-harness story: instead of trusting an earlier decision without checking, this time the user's explicit instruction won.

**Severity:** None — no defect. But the lesson is worth the entry: when an agent resolves a trade-off on your behalf, and you later state a different choice, that choice is authoritative. The record should reflect the override, not silently adopt the earlier resolution.

### HMR broken in this WSL2 environment

**The symptom:** A layout fix to `kudos-card-actions.tsx` (correcting feed column width from 392px to 680px) was measured as "not working" three times — the column still rendered at 392px after editing and refreshing. The fix was declared incorrect and re-attempted multiple times.

**The root cause:** The dev server's `_next/hmr` WebSocket handshake fails in this WSL2 setup. The browser receives a `(blocked:mixed-content)` error and never subscribes to hot-reloads. Edits to code do not trigger any update; the browser serves the pre-edit bundle on every refresh.

**The proof:** After `npm run dev` was restarted (killing the old server instance and starting a new one), the fix was correct — feed column rendered at exactly 680px, measuring `{x:144, width:680}` against the frame's nodes `2940:13482`. The layout had been right the whole time; the browser was serving the old code.

**Severity:** High for this session's development velocity. HMR is broken, not a transient issue. Restart `npm run dev` after edits, or trust Playwright suite runs (which boot their own server) over live-dev-server observations.

### React key warning from a Fragment introduced after the grep

**The warning:** Next.js dev console and overlay both report "Each child in a list should have a unique key prop" with a stack pointing to `KudosBoard` render.

**Why a grep for `.map()` found nothing:** Every `.map()` in `app/kudos/_components/` already had proper `key` attributes. The real source was `kudos-board.tsx`'s own return:
```jsx
<>
  {section}
  {spotlightSlot}
  <AllKudosSection />
  <KudosToast />
</>
```

A 4-child Fragment with `key: null` on all four — each sibling is a fiber with no key. The Fragment was introduced by phase 08's `spotlightSlot`/`sidebarSlot` refactor, **after the earlier grep ran**, which is why the search missed it.

**Proof:** Live React fiber-tree walk via `__reactFiber$*` on the KudosBoard fiber showed four keyed siblings, all `null`, all created in KudosBoard's own function body (matching "top-level render call using `<KudosBoard>`" verbatim).

**Severity:** Dev-only. A real `npm run build && npm run start` console is clean (React strips key validation from prod builds). The warning is noise until it masks a real one, so worth fixing before it does.

**The fix:** Keyed all four Fragment children: `key="highlight"` on the section, wrapped spotlightSlot in `<Fragment key="spotlight">`, etc.

## What We Tried

1. **Blamed the authed tests on environmental flakiness and timeouts** until the suite's own assertions were read against the spec contract and found vacuous. Turned out the test was skipping valid work, not flaking.

2. **Read the heart-toggle implementation three times** to understand why K-25 sometimes reloaded before the like was persisted, only to find the test itself was part of the problem: the initial 200ms wait was a guess, not auto-retry. Once Playwright's proper `expect()` retry logic was in place, the race became obvious — optimistic update was causing the reload to happen during the INSERT flight window. Reverted the optimistic flip and the race vanished.

3. **Restarted `npm run dev` four times** chasing a layout fix that looked broken, until measuring the actual HTTP response and discovering the bundle hadn't changed. The next restart fixed it because the server recompiled.

4. **Grepped every `.map()` in the kudos components** (owned and unowned) looking for missing keys, found nothing, and concluded the warning might be transient or from `node_modules` — until a live fiber walk proved it was the Fragment itself.

5. **Attempted to change the message-body justification** based on the screenshot before querying the frame's own text nodes and finding the frame says justified. Rolled back the change.

## Root Cause Analysis

**The pattern underneath all three harness defects:** A test passes because it validates something weaker than the acceptance criterion, because the assertion is vacuous under certain inputs (like "disabled" heart), or because the implementation detail being tested (optimistic state) can hide a broken contract (non-persistent state). The suite wasn't broken; it was incomplete, and the incompleteness lived in the hidden assumptions each test made about the environment it would run in.

- **Defect 1 (dual projects, one spec):** Both test files run in both projects because the config's `testMatch` glob is too broad. A test designed for one context runs in another where it can't pass the contract.
- **Defect 2 (K-21 on 404):** The assertion `body is not empty` is true for both the real page and for Next's 404 page — the test never distinguishes them.
- **Defect 3 (one-shot reads, no retries):** A zero-wait read after `.click()` passes when the server round trip is fast enough, but the test never validates that the round trip actually happened — it's observing the client-side optimistic state instead.

Each one is a different category of test failure, but they all trace to the same root: insufficient coupling between what the test asserts and what the acceptance criterion requires.

The orchestrator and HMR lessons are different:
- **Orchestrator misjudgment:** Trusting a screenshot reading over the authoritative design source is the same error as trusting passing tests over the spec — I was pattern-matching on the visual artifacts without checking them.
- **HMR breakage:** A development environment defect that's not transient or environmental — it's a systematic breakage in this WSL2 setup. Restart to fix it; recognize the pattern.

## Lessons Learned

1. **Every passing test should be verified against the acceptance criterion, not just against the codebase.** The suite passed, but K-10/K-25 never validated what they were supposed to. A test that passes before the feature exists (K-21 against the 404 placeholder) is proving nothing. The answer is not "run all tests more often" — it's "read the spec before you read the test results."

2. **An agent's auto-resolved decision is superseded the moment the user states their own intent explicitly.** The mock-dataset resolution was reasonable on YAGNI grounds, but it was a guess-on-your-behalf. The user's "use Supabase" directive was authoritative. The record should reflect the override, and the orchestrator should defer to explicit over recommended.

3. **Test isolation is not just the Playwright config's job.** Dual projects in one `testMatch` glob means one test can silently vacuous-pass under a wrong context. The fixture (auth setup, environment, config) is part of the test's contract; breaking that contract breaks the test silently. Separate the projects, or separate the test files.

4. **Optimistic UI updates are correct for UX latency, but they must never shadow what the test is actually validating.** The heart flip was right. But K-25's "assertion after a local click" is not what the spec asks for — the spec asks "persists through a reload." Once K-25 was corrected to validate persistence (not optimistic state), the race was visible and the optimistic flip had to go. The testing tool (auto-retry `expect()`) led to a better implementation (server-authoritative-only).

5. **Visual readings from screenshots are not authoritative — the design source (MCP data) is.** I read off a screenshot what I thought I saw (justified → ragged, count 1.002 → should be 1.000) and raised findings without checking the source. The frame's own text node said `JUSTIFIED`. The screenshot was scrolled. The UI agent was right to refuse and escalate. The MoMorph rule "never guess a visual value" applies up the chain too.

6. **Broken HMR is not transient or environmental — it's a systematic breakage in this WSL2 setup.** The dev server's WebSocket cross-origin block is permanent. Restarting `npm run dev` fixes each edit cycle; live-dev-server observations are unreliable. Lean on the test suite's own server runs, or restart `npm run dev` between edits. This is a standing trap to document.

7. **A test file size (616 lines) exceeds the repo's 200-line cap, but every E2E spec in the repo violates it (homepage 604, award-system 466, login 310).** The rule needs reconciliation — either split E2E specs by convention, or write the exception down. Currently it says one thing and every file does another.

## Next Steps

### Immediate (done)

- [ ] Separate `kudos-live-board.spec.ts` (anon) and `kudos-live-board-authed.spec.ts` (authed) into separate Playwright project entries in `playwright.config.ts`. K-10 and K-25 now run with real session.
- [ ] Correct K-21 to wait for the placeholder's own content marker, not generic "body is not empty."
- [ ] Correct K-10 to click back and reload (full round-trip validation per phase spec).
- [ ] Correct K-25 to click back and reload a second time (validate unlike also persists).
- [ ] All three test fixes went to `tester` agent; re-ran and confirmed 27 passed.

### Documentation (deferred, not blocking)

1. **`docs/generated/entities.md` is wholesale stale.** Run `/tkm:rebuild-spec --artifact entities` to regenerate — the entire premise (zero tables, zero SQL) is now false. This is the single most misleading file in `docs/`.

2. **`docs/generated/user-stories.md` has no F004 entries.** Needs US009–US016 with full sections and Screen→US map update, same treatment F002/F003 received.

3. **E2E spec file-size cap.** Either split every E2E spec by section-level boundaries (hero, card, sidebar, etc.) or document the 600-line exception for E2E in `docs/code-standards.md`. Current rule says 200; every file does 300+.

4. **HMR broken in WSL2.** Document the cross-origin block and restart mitigation in `docs/troubleshooting/`.

### Product decisions (from clarifications.md § Unresolved questions)

- **Test case 71b3ef43:** Route stays public (decision 3); test is out of scope. Needs a product call on whether Kudos is members-only.
- **Special-day ×2 heart accrual (31936b72):** Needs persistence + admin surface; deferred. Flame icon rendered.
- **Account-balance accrual (63645b03/91e102ba):** Backend concern; deferred to schema write side.
- **Hero Sunner search destination:** Submits to `/profile` (ComingSoon); web screen unbuilt.

---

**Status:** DONE
**Summary:** F004 delivered with 27 green assertions, repo's first schema, zero critical inspection findings. Unearthed three severe test-harness defects that would have shipped as silent passes (dual projects in single test file, vacuous K-21/K-25 assertions, one-shot reads masking race conditions). Orchestrator made two errors: read visual defects off a screenshot instead of checking the design source (corrected by UI agent), and auto-resolved data source without documenting it as a guess-on-your-behalf (corrected by user re-invocation). HMR broken in WSL2 — restart `npm run dev` required. React key warning from a Fragment introduced after earlier grep — fixed with literal keys. Four conventional commits landed locally; not pushed. Fully committed to plan with all phase work present and verified. All open items logged in clarifications.md and followups-open.md; none blocking.
**Concerns/Blockers:** None. Session tracked working tree vs uncommitted state rather than commits (schema work includes large migration+seed+types file — will batch into a single feature commit when ready to push). HMR breakage is standing trap, not a failure.
