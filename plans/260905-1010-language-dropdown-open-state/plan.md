---
title: "Language dropdown — real open-state visual contract + keyboard nav"
description: "Replace the invented open-panel styling on the login language selector with the MoMorph hUyaaugye2 contract and add full listbox keyboard navigation."
status: completed
priority: P2
effort: 3h
branch: main
tags: [login, ui, momorph, a11y, e2e]
created: 2026-09-05
---

# Language dropdown open state (E02)

The login page already toggles a VN/EN dropdown, but the open panel was styled with
invented values (`bg-[#0B0F12]`, no border, no selected-row distinction) because the
design had never drawn it. MoMorph screen `hUyaaugye2` now supplies the real contract.

**Scope:** one component (`app/login/_components/language-selector.tsx`), one e2e spec
file, one doc sync. Nothing else moves.

## Sources

- Spec (authoritative tokens): [spec/language-dropdown/spec-delta.md](spec/language-dropdown/spec-delta.md) §3
- Decisions (do not revisit): [clarifications.md](clarifications.md)
- Design: MoMorph `hUyaaugye2` — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/hUyaaugye2
- testPolicy: **`e2e-red-first`** — runner is the existing `@playwright/test` project. Do NOT scaffold a new one.

## Phases

| # | Phase | Owner | Effort | Status |
|---|---|---|---|---|
| 01 | [RED e2e for open-state contract + keyboard nav](phase-01-red-e2e-open-state-and-keyboard.md) | `tester` | 45m | completed |
| 02 | [Implement open-state visual contract + listbox keyboard nav](phase-02-implement-open-state-and-keyboard.md) | `momorph-ui-implementer` | 1h30 | completed |
| 03 | [GREEN, visual validation, regression, doc sync](phase-03-green-visual-validation-and-doc-sync.md) | `tester` → `doc-writer` | 45m | completed |

## Dependencies

```
P01 (RED, must fail on a real assertion)
 └─> P02 (implementation — receives redCommand/redExitCode/redFailure read-only)
      └─> P03 (GREEN rerun + visual validation + C1/C3/C3b/C4 regression + doc sync)
```

Strictly sequential. No parallelism — all three phases touch overlapping evidence and
P02 is the only phase that writes component code.

## File ownership

| Phase | Owns (writes) | Reads only |
|---|---|---|
| 01 | `e2e/login-screen.spec.ts` | `app/login/_components/language-selector.tsx`, `playwright.config.ts` |
| 02 | `app/login/_components/language-selector.tsx` (+ split file if >200 lines) | `e2e/login-screen.spec.ts`, `icons.tsx`, spec-delta.md |
| 03 | `docs/features/F001_Login/functional-spec.md`, `docs/screens/SCR001_Login/spec.md`, `spec/language-dropdown/spec-delta.md` (status flip) | everything above |

P02 must NOT edit the spec file; P01/P03 must NOT edit the component. This keeps the
RED evidence honest.

## Key constraints

- Panel stays a drop-below (`absolute top-full`) — **user decision, settled, not open**.
- Edit `language-selector.tsx` **in place**. No "enhanced" copy.
- Tokens in spec-delta §3 are used **verbatim**. No re-derivation, no rounding.
- Reuse `IconFlagVn` / `IconFlagEn` / `IconChevronDown` from `icons.tsx`.
- Every code file under 200 lines — split rule and exact path named in phase 02.
- Existing C1, C3, C3b, C4 must stay green. C3b asserts one distinct `<svg>` per option.

## Rollback

Single-commit-per-phase. P02 reverts by `git checkout -- app/login/_components/language-selector.tsx`
(plus deleting the split file if created); P01 and P03 revert by reverting their own
file. No schema, no cookie format, no API surface is touched, so rollback is total and
carries no data migration.

## Known gaps & deferred items

**Deferred per user decision (2026-09-05):**

- **Tab-to-close panel gap** (Medium severity, FR-203.c non-functional gap) — pressing Tab while focus sits on an option inside the open panel does not close the panel or return focus to the trigger. The panel remains mounted while focus moves past it (classic "orphaned popup" pattern). Not in the executable test contract (C3e does not cover Tab), so not a broken acceptance criterion. Recommended as a follow-up: close the panel on Tab/Shift+Tab without stealing focus back (match the outside-click "no forced focus return" behavior). Deferred by user; log as known gap for a later phase.

**Pre-existing (noted by reviewer, low severity, out of scope):**

- **`aria-controls` dangling ID while panel closed** — trigger carries `aria-controls={listboxId}` pointing at a conditionally-rendered panel, so the ID doesn't exist while closed. Pre-existing, not introduced by this change. Cheap fix if picked up: keep panel always mounted (hidden when closed) or drop `aria-controls` when `!open`. Logged for backlog; does not block this seal.

- **`IconFlagEn` hand-drawn asset, not MoMorph-sourced** — the EN flag icon added in this phase is a new hand-drawn SVG (geometry matched to `IconFlagVn` by hand) rather than a design source. Necessary to satisfy FR-203.a (each option shows its own flag) and C3b (two visibly distinct SVGs). Honestly labeled in the code (`// No MoMorph counterpart...`). Reviewer recommended one-line traceability note in clarifications.md; this has not yet been added and should be folded into the next project maintenance pass.

## Definition of done

`npx playwright test e2e/login-screen.spec.ts --project=anon` exits 0 with all of
C1, C2, C3, C3b, C3c, C3d, C3e, C4, C5, C10 passing; `npm run typecheck` and
`npm run lint` clean; SCR001 §7/§9 no longer say `TBD (draft)` / `[EXPECTED]` for E02.
