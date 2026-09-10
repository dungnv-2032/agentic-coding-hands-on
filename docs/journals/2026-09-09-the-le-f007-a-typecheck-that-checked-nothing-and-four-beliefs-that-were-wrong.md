# F007 Thể lệ — a typecheck that checked nothing, and four beliefs that were wrong

**Date**: 2026-09-09 (session 2026-09-09 08:38 → 2026-09-09 15:42 +07)
**Severity**: high
**Component**: `/standards` (F007/SCR007), `.next/dev` type artifacts, E2E navigation contract, dialog semantics
**Status**: resolved

## What Happened

Delivered F007 Thể lệ / SCR007. `/standards` stopped being a `ComingSoon` placeholder and became a 553px right-hand drawer — three prose sections, four hero-badge tiers, six collectible icons, a pinned footer holding `Đóng` and `Viết KUDOS`. Test policy `e2e-red-first`. The editorial copy is read per request from two new tables, `public.rule_sections` and `public.rule_items` — **the first time editorial content lives in Postgres in this repo**.

Final state: `npx supabase db reset`, `npm run typecheck`, `npm run lint`, `npm run build` all exit 0; `npx playwright test e2e/the-le.spec.ts --project=anon` → **10 passed / 2 skipped, exit 0**, reproduced three times, up from a verified 9-failed RED. Inspection SEALED, score 9.5, 0 critical. Six conventional commits on `main` (`ac507bf` … `44e9844`); not pushed.

The build went to plan. What earns this entry is the set of things that were *believed* and turned out false.

## The Brutal Truth

The one that still bothers me: **`npm run typecheck` returned exit 0 while checking nothing at all.** A `next dev` killed mid-write left a spliced fragment in `.next/dev/types/routes.d.ts`. The parse error aborted the whole program check, and `tsc` exited clean — repo-wide, not just on F007 paths. Every green typecheck in that window was worthless.

It was found by accident. An agent deliberately broke a `Dictionary` type expecting an error, and no error came. If that agent had been slightly less rigorous, four phases of code would have been built on a compiler that had quietly stopped compiling. This is the same class of failure the 2026-09-06 award-system entry recorded (`TS1005`/`TS1128` out of `.next/dev/types`) — different symptom, same rotten artifact. We knew and it still got us.

The galling one is `ROOT FUTHER`. The verbatim-transcription rule was right, and it was defended in **three** places — a seed comment, a fixture header, and a component doc-comment — all defending a misreading. Confident prose, repeated, is not evidence.

## Technical Details

### 1. Corrupt build artifact masking every type error

Symptom: `npm run typecheck` → exit 0 on a tree containing a known-broken type. Cause: a truncated/spliced `.next/dev/types/routes.d.ts` from a dev server killed mid-write. Repair: `npx next typegen`.

Verification is the part worth copying — a **canary type error** in `e2e/fixtures/the-le-constants.ts`:

```
canary present  -> npx tsc --noEmit -p tsconfig.json  exit 2
canary removed  -> npx tsc --noEmit -p tsconfig.json  exit 0
```

This was re-run at the end of phase 02, because a Playwright run kills the dev server on exit — the exact condition that caused it. Both `npx tsc --noEmit -p tsconfig.json` and `npm run typecheck` were re-proven.

### 2. `ROOT FUTHER` vs `ROOT FURTHER` — right rule, wrong field

`clarifications.md` transcribed node `I3204:6088;737:20392` as `ROOT FUTHER`. That is the Figma **`itemName`** — the LAYER name. The rendered copy lives in **`character`**, and reads `ROOT FURTHER`. The exported bitmap `public/images/rules/icon-root-further.png` bakes the typo, so the two MoMorph artifacts genuinely contradict each other.

Caught by the tester diffing `design/the-le.png` against the seed rather than trusting the recorded rationale. Seed, fixture and `clarifications.md` now carry `ROOT FURTHER`; the amendment is written into `clarifications.md` as an amendment, not a silent edit. User-visible copy on a public page — a one-letter typo in a Postgres row.

### 3. `window.history.length` cannot distinguish a deep link from a soft navigation

Measured in a driven Chromium (`app/standards/_components/rules-panel-dismiss.tsx:18-31`):

```
fresh newPage()          -> url about:blank, history.length = 1
after goto("/standards") -> url /standards,  history.length = 2
```

A deep link therefore reported `length = 2`, took `router.back()`, and landed the user on `about:blank` — precisely the dead end BR-004 forbids. Caught by `FUN_003b`. Fix: feature-detect the Navigation API, keep `history.length` as fallback.

```ts
if (typeof navigation?.canGoBack === "boolean") return navigation.canGoBack;
return window.history.length > 1;
```

Assumption A1 was rewritten from "holds" to **disproved**. This is RED-first paying for itself in one test.

### 4. `aria-modal` declared without focus containment

The panel carried `role="dialog"` + `aria-modal="true"` with **no focus trap, nothing `inert`**, and header/footer still in the tab order. Three input modes disagreeing: the `z-40` scrim blocks the mouse over a `sticky z-20` header, the keyboard passes straight through, and the screen reader is told the page is empty.

`/standards` is a route, not an overlay on live content — tabbing out to the header is correct. So the attribute was **dropped**, and `e2e/the-le.spec.ts` now asserts its **absence** so it cannot creep back. Note this amended a *frozen* test contract: recorded explicitly in `clarifications.md` and FR-201, not quietly loosened to make a build pass.

### 5. The design frame contradicted itself twice — measurement won both times

- Node `3204:6093` (`Đóng`) declares CSS summing to **112px**; its bbox measures **94px**; the build renders **115px**. Phase 05 followed the declared CSS and let width follow content. Documented, not a defect.
- The collectible icons ship as **80×104 / 80×88 PNGs with captions baked into the bitmap** (`icon-beyond-the-boundary.png` 80×104, `icon-revival.png` 80×88, …). The planned `h-20 w-20 rounded-full` would have cropped the artwork and rendered **every caption twice**. Caught by an agent measuring the assets instead of trusting the phase file.

### 6. The evidence gate had never actually run

F006's plan carries **neither** `temper-results.json` **nor** `inspection-verdict.json` — its hard gate was never exercised. This session's gate blocked correctly, twice: first on both artifacts missing, then on `riskGate.signoffRequired: true` (a DB migration). That second block required the user's explicit sign-off and **could not be self-approved** — `humanSignedOff: true` in `evidence/inspection-verdict.json` is a real human decision.

## What We Tried

1. **Trusted a green `npm run typecheck`** — until a deliberately broken `Dictionary` produced no error. Repaired with `npx next typegen`, then proven with a canary rather than assumed.
2. **Trusted the recorded `ROOT FUTHER` rationale**, restated in three files — until the design render was cropped and read directly.
3. **Shipped `history.length > 1` as the deep-link discriminator** — until `FUN_003b` put the user on `about:blank`.
4. **Considered building a focus trap** to make `aria-modal` honest — rejected as YAGNI for a route-level drawer; dropped the attribute and asserted its absence instead.
5. **Ran the full suite for a clean sweep** — got 70 passed / 26 failed / 94 did not run instead (below).

## Root Cause Analysis

**One pattern underneath four of the five:** a written claim was trusted in place of a measurement.

- The exit code claimed the types were checked. It was reporting on a dead program.
- The clarification claimed the copy. It had recorded the wrong field of the node.
- The phase file claimed `h-20 w-20`. The PNG had a caption in it.
- The contract claimed modality. The DOM had no trap.

The `history.length` case is different in kind: not a misread record, but a genuinely wrong mental model of session history under automation. `about:blank` is a real entry. That one could only be found by driving a browser, which is exactly why the RED gate exists.

The `routes.d.ts` corruption has a specific trigger worth naming: **killing `next dev` mid-write**, which includes every Playwright run that boots its own server and tears it down. This repo's workflow does that constantly.

## Lessons Learned

1. **On this repo, a green typecheck after any dev-server crash or Playwright run is suspect.** Re-prove it with a canary — insert a deliberate type error, confirm exit 2, remove it, confirm exit 0. `npx next typegen` is the repair. Exit 0 alone proves nothing.
2. **When transcribing from a design tool, name the FIELD, not "the text node."** `itemName` is the layer name; `character` is the rendered copy. Every future clarification entry should say which one it read.
3. **Rationale repeated in three files is still one rationale.** Repetition is not corroboration — it just makes a misreading expensive to dislodge.
4. **`window.history.length` is not a deep-link test.** Use `navigation.canGoBack` with `history.length` as fallback. A driven browser carries `about:blank`.
5. **Don't claim an ARIA contract you don't implement.** Either build the trap or drop the attribute — and if you drop it, assert the absence so it cannot return. Amend the contract in writing; never loosen an assertion silently.
6. **Measure the asset before you style it.** An 80×104 PNG with baked-in caption is not a 80×80 avatar.

## Next Steps

### Blocking nothing, but real

**Full-suite E2E is inconclusive, not green.** `evidence/full-suite-run.txt`: **70 passed / 26 failed / 1 skipped / 94 did not run, EXIT=1, 29.5m**. Every one of the 26 is a **30s/35s timeout**, not an assertion mismatch — there is no expected-vs-received diff anywhere in the log. The head of the list is `[setup] e2e/auth.setup.ts`, and its failure is why 94 tests never ran.

Proven **not** an F007 regression:

| Probe | Result |
|---|---|
| `npx playwright test --project=setup --timeout=180000` | exit 0, same test passing in **3.9s** |
| `npx playwright test --project=setup` (default timeout, isolated) | exit 0, **5.0s** |
| `git log -- e2e/auth.setup.ts` | unchanged since `8a02795`, weeks before F007 |

The same failures reproduce in isolation, including `e2e/smoke.spec.ts`, which predates this feature. The 30s budget is too tight for a cold `next dev` on this box. **The timeout was deliberately NOT widened to hide it** — that would convert a harness defect into an invisible one. This needs its own commission. Owner: next session. The 94 unrun tests are **unverified, not verified-good**.

### Recorded, deferred

- **Two valid homes for editorial copy, no rule arbitrating.** F003 hardcodes its copy in `lib/*.ts`; F007 puts it in Postgres. Both are defensible; nothing in the repo says which to pick. Honest architectural gap, written into `docs/system/architecture.md:50-54`. Needs a decision before the next content-bearing screen.
- **`anon` holds `TRUNCATE` on every public table** via Supabase's `alter default privileges`. RLS denies the writes, but `TRUNCATE` sits outside RLS. PostgREST exposes no path to it and it reproduces on F004's `board_stats`, so it is pre-existing and repo-wide. **Deliberately not patched as a one-table special case** — the right shape is a repo-wide migration.
- **Visual V-1 / V-2 returned as bounded fixes**: collectible captions render 147px wide against the frame's ~80px so they never wrap where the design wraps; the hero-tier block is missing its ~19px left indent (frame x=946, build x=927), which compresses row pitch to 80px against the frame's 88px.
- **The ❤️ emoji renders monochrome in every capture** — this headless Chromium has no colour-emoji font. **Indeterminate**, not a defect. Needs eyes on a real desktop browser.
- `lib/rules/queries.ts:50` — empty-table and query-error branches have no committed test; the repo has no unit-test runner. Traced by hand, exercised via throwaway stub-client probes. Deferred.

### Push

Six commits sit on local `main`, unpushed. Nothing blocks the push; it just did not happen this session.
