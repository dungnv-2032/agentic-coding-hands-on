---
phase: 04
title: GREEN + visual evidence
owner: tester
status: pending
feature: F005
depends_on: [03]
test_policy: e2e-red-first
---

# Phase 04 — GREEN + visual evidence

**Owns:** `e2e/capture-addlink-box-visual.spec.ts`, `playwright.config.ts`, `evidence/*`

## Steps

1. Rerun the exact phase-01 command GREEN:
   `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed` → exit 0, every ID-61..68
   passing and no previously-green test newly red.
2. `npm run typecheck` and `npm run lint` → exit 0.
3. Add an on-demand capture project `addlink-box-visual-capture` (storageState
   `e2e/.auth/kudos-user.json`, dependency `kudos-auth-setup`), mirroring
   `hashtag-dropdown-visual-capture`.
4. Capture three 1440px shots clipped to the dialog, each **asserting** its state before the
   screenshot, never merely photographing it:
   - `addlink-box-empty-1440.png` — freshly opened, both fields empty
   - `addlink-box-errors-1440.png` — after `Lưu` on empty fields, both errors visible
   - `addlink-box-filled-1440.png` — valid text + URL entered, no errors
5. Write `evidence/green-evidence.md` and `evidence/temper-results.json` with real commands and
   exit codes.

## Done when

All four commands exit 0 and the three PNGs exist with their asserted states.
