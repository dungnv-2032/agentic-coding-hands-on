# Phase 03 — GREEN, visual validation, regression, doc sync

## Context Links

- Plan overview: [plan.md](plan.md)
- RED evidence: [phase-01-red-e2e-open-state-and-keyboard.md](phase-01-red-e2e-open-state-and-keyboard.md)
- Implementation: [phase-02-implement-open-state-and-keyboard.md](phase-02-implement-open-state-and-keyboard.md)
- Spec delta to fold into docs: [spec/language-dropdown/spec-delta.md](spec/language-dropdown/spec-delta.md)
- Design: MoMorph `hUyaaugye2` — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/hUyaaugye2
- Doc targets: `docs/features/F001_Login/functional-spec.md`, `docs/screens/SCR001_Login/spec.md`

## Overview

- **Priority:** P1
- **Status:** completed
- **Owner:** `tester` (steps 1–5) → `doc-writer` (steps 6–8)
- **Effort:** 45m
- **Description:** Prove GREEN on the same command that produced RED, confirm the rendered
  panel actually matches the design by eye, prove C1/C3/C3b/C4 did not regress, then fold
  the spec delta into the feature and screen specs.

## Key Insights

- Under `e2e-red-first`, GREEN must come from the **exact same command** as RED. A different
  file filter, project, or grep is not the same proof.
- `tester` owns browser evidence for every policy. `momorph-ui-implementer` does not close
  its own loop.
- SCR001 §7 and §9 currently carry `TBD (draft)` and `[EXPECTED]` markers for E02. spec-delta
  §2 supplies the replacement text ready-made — copy it, do not re-author it (DRY).
- This repo has no `docs/project-changelog.md` or `docs/development-roadmap.md`. Do **not**
  create them for a single component change (YAGNI). The feature and screen specs are the
  documentation of record here.

## Requirements

**Functional**

- C3c, C3d, C3e pass.
- C1, C2, C3, C3b, C4, C5, C10 still pass — the whole file green in one run.
- The rendered open panel visually matches MoMorph `hUyaaugye2`.
- `docs/features/F001_Login/functional-spec.md` carries FR-203.a/.b/.c and the three new
  US003 acceptance criteria.
- `docs/screens/SCR001_Login/spec.md` §7 has real rows for the four E02 actions and §9 has a
  real accessibility contract instead of `[EXPECTED]` for the dropdown.

**Non-functional**

- No test is weakened, skipped, `.fixme`'d, or retried into passing.
- `spec-delta.md` frontmatter flips `status: draft` → `status: applied`.

## Architecture

```
tester
 ├─ 1. npm run typecheck && npm run lint          → both exit 0
 ├─ 2. npx playwright test e2e/login-screen.spec.ts --project=anon   → exit 0, 10/10
 ├─ 3. Playwright MCP: open /login, click trigger, screenshot open panel
 ├─ 4. compare screenshot ↔ hUyaaugye2  (bg, border, radius, selected row, 108×56)
 └─ 5. keyboard walk by hand: Tab → Enter → ArrowDown → Escape
        ↓ verdict: GREEN | mismatch → bounded fix back to momorph-ui-implementer
doc-writer
 ├─ 6. functional-spec.md ← spec-delta §1
 ├─ 7. SCR001 spec.md §7 / §9 ← spec-delta §2
 └─ 8. spec-delta.md frontmatter status: applied
```

## Delivery Status (2026-09-05)

**Tester work complete (steps 1–7):**

- **GREEN on identical command:** `npx playwright test e2e/login-screen.spec.ts --project=anon` exits 0, 10/10 pass
- **Regression held:** C1, C2, C3, C3b, C4, C5, C10 all pass (C3b explicitly confirmed — container migration to `div`/`button` kept SVG assertions intact)
- **Full suite:** 23/23 tests pass when run against both `anon` and `authed` projects
- **Typecheck + Lint:** Both exit 0, no issues
- **Visual validation:** All tokens verified — panel bg `#00070C`, border `1px solid #998C5F`, radius 8px, padding 6px, option size 108×56, radius 2px, selected bg `rgba(255,234,158,0.2)`, unselected transparent, hover `rgba(255,234,158,0.08)`, focus ring `#998C5F`
- **Keyboard accessibility:** ArrowDown/Up/Home/End, Escape + focus return, Enter/Space select all verified by manual walk
- **Screenshots captured:** panel-open.png, panel-hover-en.png, panel-focus-en.png, header-in-context.png in `evidence/` directory
- **Evidence recorded:** `evidence/visual-validation.json`, `evidence/red-evidence.json`, `evidence/visual-capture.json`, `evidence/tester-visual-validation-summary.md`

**Doc-writer work in progress (steps 6–8):**

- Waiting for doc sync to complete: `functional-spec.md` (FR-203 criteria + US003 acceptance), `SCR001_Login/spec.md` (§7 actions + §9 accessibility), `spec-delta.md` (status: applied)
- Once doc-writer finishes, this phase will close and plan status will flip to "completed"

## Related Code Files

**Modify**

- `docs/features/F001_Login/functional-spec.md` — append FR-203.a/.b/.c under FR-203
  (line ~54) and the three acceptance checkboxes under `### US003_LanguageSelection`
  (line ~112). Update the FR-203 line in the traceability section (~line 181) to mention
  the open-state contract.
- `docs/screens/SCR001_Login/spec.md` — §7 Conditional UI / §4 User Actions rows for E02
  (lines ~72–73) get the real `Source` value `design 721:4942`; §9 Accessibility rows for
  ARIA / Keyboard / Focus (lines ~135–137) lose `[EXPECTED]`.
- `plans/260905-1010-language-dropdown-open-state/spec/language-dropdown/spec-delta.md` —
  frontmatter `status: draft` → `status: applied`.
- This file and `plan.md` — phase statuses.

**Read only**

- `app/login/_components/language-selector.tsx`, `e2e/login-screen.spec.ts`

**Create / delete:** none. Do **not** create a changelog or roadmap file.

## Implementation Steps

1. `npm run typecheck` — must exit 0.
2. `npm run lint` — must exit 0.
3. `npx playwright test e2e/login-screen.spec.ts --project=anon` — must exit 0 with every
   test in the file reported passed. Record the summary line verbatim.
4. Confirm the regression set by name in that output: C1, C2, C3, **C3b**, C4, C5, C10.
   C3b is the one most exposed by the `ul` → `div` container change — call it out explicitly.
5. Visual validation via Playwright MCP:
   - navigate to `http://127.0.0.1:3000/login`
   - click `button[aria-haspopup="listbox"]`
   - screenshot the open panel
   - compare against MoMorph `hUyaaugye2`: panel background near-black `#00070C`, thin gold
     `#998C5F` border, 8px corners, 6px inset, VN row visibly lighter than EN, both rows
     `108 × 56` with the flag left of a centered label
   - screenshot again with the mouse over the EN row (hover tint must be clearly weaker than
     the VN selected tint)
6. Manual keyboard walk (record pass/fail per step): Tab to the trigger → Enter opens →
   focus is visibly on VN → ArrowDown moves to EN → Escape closes → focus is back on the
   trigger with a visible indicator.
7. **If anything mismatches:** treat the phase as incomplete. Send a bounded fix list back to
   `momorph-ui-implementer` naming the exact property and expected value. Never adjust a test
   to accommodate the UI.
8. Doc sync (`doc-writer`): apply spec-delta §1 to `functional-spec.md` and §2 to
   `SCR001_Login/spec.md` — surgical edits to the named rows only, no regeneration of the
   file, no reflowing of untouched sections. Then flip spec-delta frontmatter to
   `status: applied`.
9. Update the phase table in `plan.md` to `completed` and set the plan frontmatter
   `status: completed`.

## Todo List

**Tester (steps 1–7):**

- [x] `npm run typecheck` exit 0
- [x] `npm run lint` exit 0
- [x] `npx playwright test e2e/login-screen.spec.ts --project=anon` exit 0
- [x] C3c / C3d / C3e pass (were RED in phase 01)
- [x] C1 / C2 / C3 / C3b / C4 / C5 / C10 still pass — C3b confirmed by name
- [x] Playwright MCP screenshot of the open panel captured
- [x] Screenshot compared against `hUyaaugye2` — panel, border, radius, padding, row size
- [x] Hover tint visibly weaker than the selected tint
- [x] Manual keyboard walk recorded step by step

**Doc-writer (steps 6–8) — in progress:**

- [ ] `functional-spec.md` — FR-203.a/.b/.c + US003 acceptance added
- [ ] `SCR001_Login/spec.md` §7 rows and §9 accessibility contract replaced
- [ ] `spec-delta.md` → `status: applied`

## Success Criteria

| Criterion | How it is observed |
|---|---|
| GREEN on the identical command | Same `redCommand` string, exit code 0 |
| No test weakened | `git diff e2e/login-screen.spec.ts` between phase 01 and now is empty |
| No skips | Playwright summary reports 0 skipped, 0 flaky |
| Regression held | C3b named as passed in the run output |
| Visual match | Screenshot attached to the phase report; each of the 6 checked properties marked ✔ |
| Keyboard walk | 6/6 steps recorded pass |
| Docs true to code | `grep -c "TBD (draft)" docs/screens/SCR001_Login/spec.md` drops by the E02 rows; no `[EXPECTED]` remains on the ARIA/Keyboard/Focus rows |
| Delta closed | `spec-delta.md` frontmatter reads `status: applied` |

## Risk Assessment

| Risk | Likelihood | Impact | Countermeasure |
|---|---|---|---|
| Tests pass but the panel looks wrong (CSS asserted, layout not) | Medium | High | Step 5 exists precisely for this. `toHaveCSS` cannot see a mis-stacked flag or a clipped row. |
| A retry turns a flaky failure green | Low | High | `playwright.config.ts` sets no retries outside CI. If a test needs a rerun to pass, report it as flaky, not as GREEN. |
| Docs edited by regenerating the whole spec file | Medium | Medium | Surgical row edits only; the spec layer is machine-generated and must not be rewritten wholesale. |
| A changelog/roadmap file gets invented to satisfy the docs rule | Medium | Low | Neither file exists in this repo. Do not create one for a single-component change. |
| Vietnamese doc rows get rewritten in English | Low | Medium | `functional-spec.md` and `SCR001` are Vietnamese. spec-delta §1/§2 is already Vietnamese — copy it verbatim. |
| Bounded fix loop widens into a redesign | Low | Medium | The fix list must name property + expected value only, and may not add scope beyond spec-delta §3. |

## Security Considerations

- Screenshots are taken on `/login` while unauthenticated — no session token, no email, no
  Supabase key can appear in the captured image. Do not capture on an authenticated route.
- Do not paste `.env` values, cookie jars, or Supabase project refs into the phase report or
  the doc updates.
- The doc edits describe behavior only; no credentials or endpoint secrets belong in
  `functional-spec.md` or `SCR001_Login/spec.md`.

## Next Steps

- **Depends on:** phase 02 implementation complete.
- **Follow-up (out of scope, log only):** if the same open-panel pattern is wanted elsewhere,
  a shared listbox primitive could be extracted — but not for a single two-option dropdown.
- **Closes:** the `TBD (draft)` debt on SCR001 §7 for E02 and the `[EXPECTED]` accessibility
  rows for the dropdown.
