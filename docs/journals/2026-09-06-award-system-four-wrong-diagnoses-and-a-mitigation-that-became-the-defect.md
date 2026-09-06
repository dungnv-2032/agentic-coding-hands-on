# Four wrong diagnoses and a mitigation that became the defect — Award System screen

**Date**: 2026-09-06 11:52
**Severity**: high
**Component**: Award System screen (F003_AwardSystem / SCR003, `/awards-information`), E2E test architecture
**Status**: ongoing

## What Happened

`/awards-information` shipped under `/tkm:takumi --auto` with `test_policy: e2e-red-first`. Strict RED: `npx playwright test e2e/award-system.spec.ts --project=anon` → exit 1, **11 failed / 2 passed** (`evidence/award-system-red-run.log`), the lead failure being `getByRole('heading', { name: 'Hệ thống giải thưởng SAA 2025', level: 1 })` — element(s) not found. GREEN on the byte-identical command: **14 passed** (`--list` settles what that number is: 13 tests in `e2e/award-system.spec.ts` plus 1 from the dependency `setup` project — "Total: 14 tests in 2 files"), homepage **22/22**, full anon project **54/54**, all exit 0 (`evidence/seal-*.log`). Four scoped commits `1d21af4 → 4de429f`, nothing pushed.

That is the status line, and it is the least useful thing here. The real record is that **four diagnoses were wrong on the first pass**, one of the plan's own risk mitigations *became* a defect, and three defects cleared a fully green suite.

## The Brutal Truth

Every wrong diagnosis was confident, specific, and had a number attached. That is what makes them worth writing down — none of them looked like guesses. The orchestrator relayed one of them to the implementer as a fix instruction, and the implementer had to push back with evidence to stop a cosmetic flash being traded for a real hydration regression.

The bite: the suite was green the whole time, and the worst defect — a menu item stuck lit on the wrong award **permanently** — was found by a reviewer reading code, not by any of the 13 screen tests. The suite runs Desktop Chrome 1440×900 with synthetic input. All three escaped defects live outside exactly that box.

## Technical Details

**Three defects that cleared a green suite.**

1. **W-2 — the plan's own R2 mitigation became the defect.** A 700 ms `clickLock` in `award-category-nav.tsx` suppressed the IntersectionObserver *and discarded* what it saw. The observer only fires on *change*: interrupt a programmatic scroll, come to rest, and no further intersection ever fires — the wrong item stays lit forever. FR-402 violated. Fixed with live-geometry `resolveActive()` plus lock release on wheel/touch/key, proven with a no-interrupt control probe.
2. **W-1 — `HEADER_OFFSET = 112`** documented against a **72px** header (`page.tsx:19-24`). Measured header at 375px: **245px**. Fixed by a runtime-measured `--award-header-offset` (112 / 117 / 165 / 285 / 341 across widths) with `lg` pinned at 112 so desktop geometry never moved.
3. **W-3** — six award sections on a 6410px page with **no heading and no accessible name**.

**And one nobody flagged until pixels were measured:** every 336×336 badge rendered `object-fit: fill` into a flex row at `align-items: stretch`, inheriting the text column's height. Signature came out **336×966 — 2.88× distortion**, a circle rendered as an ellipse. ID-7 asserted the image and its alt text, not its geometry, so the suite was green and the artwork was wrong. Now locked by an exact 336×336 assertion.

## What We Tried

**1. The 290 ms deep-link flash → "smooth-scroll duration."** Wrong. The deep-link path was already `behavior: "auto"`, and there is no `scroll-behavior`/`scroll-smooth` anywhere in `app/` or `lib/`. Real cause: hydration latency — a URL fragment never reaches the server, so SSR necessarily ships `items[0]` active. Measured `[[0,"award-nav-top-talent"],[290,"award-nav-mvp"]]`. It is a fixed cost, which is why `--repeat-each=10` was *stable* rather than jittery. Recorded as ORCH-04 with the rejected alternatives: a lazy `useState` initialiser reading `location.hash` renders `top-talent` server / `mvp` client — a hydration mismatch that fails ID-13's zero-console-errors assertion; `useSyncExternalStore` with `getServerSnapshot` still yields `AWARDS[0]`; CSS `:target` fixes first paint but leaves `aria-current` lagging.

**2. `text-justify` flagged as a deviation → retracted.** A direct pixel scan of the frame's D.2 description block: left edge holds at **443–445**, right holds flush across **ten-plus consecutive lines**, ragged only on the last. Justified. Retracted, not carried forward.

**3. Locale-exhaustiveness spot-check → contaminated.** First attempt reported TS1005/TS1128 for every mutation *including the restored baseline*. The errors came from `.next/dev/types/{routes.d.ts,validator.ts}`, corrupted by dev servers running concurrently during verification. `rm -rf .next/dev && npm run build` regenerated them; only then did the test measure anything, giving the real result — `TS2353: ... 'prizeOrTYPO' does not exist in type` at the exact source line (`evidence/locale-exhaustiveness-proof.json`).

**4. The evidence gate → "blocked by classifier."** Reported to the user as blocked; a different path form ran fine. It then blocked on our *own* artifacts, because the verdict schema was guessed instead of read from `.claude/hooks/lib/verdict-findings-location.cjs`:
```
inspection-verdict findings[i] is Accept but has no valid location (want path:NNN or path:NN-MM)
inspection-verdict riskGate must be an object
```
Both would have shipped had the gate been skipped.

**5. A false negative the tester caught in itself.** The first W-2 probe looked like a failure — nav stayed on MVP. It hadn't failed: `scrollY` was still **4683**, the MVP landing position. Synthetic CDP `mouse.wheel()` **does not abort Chrome's programmatic smooth scroll**, so no interruption ever happened and the nav was correctly reporting the card on screen. Re-run with trusted keyboard input. The dead-end log was kept on purpose: `evidence/delivery-w2-probe-round1.log`.

**6. A test bug caught by its own new assertion.** The W-3 structure lock failed first run — it asserted `award-nav` as a *descendant* of the labelled `<nav>`, but the testid and the `aria-label` sit on the same element:
```
Locator: getByRole('navigation', { name: 'Danh mục giải thưởng', exact: true }).getByTestId('award-nav')
Expected: visible — element(s) not found
```
Product right, test wrong. Corrected to assert **identity** (a stronger claim); the red run kept in `evidence/seal-award-system-run-failed-assertion.log`.

**7. Design-vs-test conflict, settled on evidence.** MoMorph test cases named the route `/he-thong-giai` and required an anon→login redirect. The frame's own header renders "Award Information" *selected*, the shipped homepage deep-links all six cards to `/awards-information#<slug>`, and six green anon tests navigate there unauthenticated. Route adopted as `/awards-information`; ID-1 deliberately unimplemented and recorded as open decision **D001**, not dropped.

## Root Cause Analysis

Two roots, both cheap to name and easy to repeat.

**Coverage shape.** The suite tests one viewport, one browser, synthetic input. W-1 (mobile), W-2 (real user scroll) and W-3 (accessible tree) each sit precisely in that blind spot. Green measured the axes we chose, and we read it as "correct."

**Guessing artifacts instead of reading them.** The verdict schema, the scroll cause, the frame's text alignment — three separate wrong calls, all from inference where a file or a pixel was available. Every one collapsed the moment someone actually looked.

And underneath both: **a mitigation written into a plan inherits the plan's authority without earning it.** R2's click lock was never tested as a state machine, only as an intention.

## Lessons Learned

- Symptom timing is not mechanism. 290 ms *looks* like an animation. Measure the mechanism before prescribing a fix — the relayed diagnosis nearly traded a cosmetic flash for a hydration mismatch.
- Kill dev servers before typecheck. Generated `.next/dev/types` will report failures that have nothing to do with the source under test, including on a clean baseline.
- Read the validator; don't guess the schema. `verdict-findings-location.cjs` and `verdict-risk-gate.cjs` are 60 lines each.
- `IntersectionObserver` + a suppression window is a state machine with no recovery path unless you write one. It fires on *change*; suppress the change and the state is simply lost.
- Retract findings loudly and keep dead-end logs. Both saved rework here.
- When a new assertion fails, suspect the assertion first — then make it *stronger*, not looser.

## Next Steps

1. **Phase 04 docs** — doc-writer in flight. Done = F003/SCR003/US007/US008 registered, `/awards-information` off `ComingSoon`, D001 + ID-14 carried verbatim.
2. **FUP-01** — sticky header `rgba(16,20,23,0.8)` with `backdrop-filter: none`; gold prize text bleeds through at 375px. Pre-existing shared chrome, measurably worse on `/` (22% vs 10% bleed). **Owner: unassigned — needs a ticket**, judged against `/` first.
3. **FUP-02** — `w-[60px]` unit column cramps EN. Deliberately skipped (`max-w-[88px]` collapses the VI wrap the frame specifies). **Owner: unassigned**, revisit at the EN visual pass.
4. **OBS-1** — at the hero the menu retains an arbitrary previous item; one-condition fix, invariant preserved. Unowned.
5. **D001** (ID-1 anon→login) and **ID-14** (`/kudos` still a placeholder) need a product owner.
6. Four commits unpushed. Push is the user's call.
