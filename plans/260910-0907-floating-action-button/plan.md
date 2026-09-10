---
title: "Floating Action Button — quick-action menu"
description: "Convert the homepage floating pill from two direct links into a real disclosure trigger opening Thể lệ / Viết KUDOS / Hủy at measured MoMorph geometry."
status: complete
priority: P2
effort: 4.5h
branch: main
tags: [momorph, homepage, ui, e2e-red-first, i18n]
created: 2026-09-10
work_type: feature
spec: docs/features/F008_FloatingActionButton/
test_policy: e2e-red-first
momorph_screens: ["_hphd32jN2", "Sv7DFwBw1h"]
momorph_file_key: 9ypp4enmFmdK3YAFJLIu6C
---

# Floating Action Button — quick-action menu

Converts `app/_components/floating-widget.tsx` from two `<Link>`s into a disclosure trigger
(`fab-trigger`) revealing `Thể lệ` → `/standards`, `Viết KUDOS` → `/kudos/new`, and a round red
`Hủy`. Both destinations already ship (F007, F005). Authoritative inputs, never re-litigated:
[clarifications.md](clarifications.md) · [design/geometry.md](design/geometry.md) ·
[technical-spec](spec/floating-action-button/technical-spec.md) ·
[functional-spec](spec/floating-action-button/functional-spec.md) ·
[evidence/study-context.json](evidence/study-context.json)

## Phases

| # | Phase | Owner | Track | Status | Effort |
|---|-------|-------|-------|--------|--------|
| 01 | [Strict RED e2e gate](phase-01-red-e2e-gate.md) | `tester` | gate | complete | 1h |
| 02 | [i18n copy + pen icon asset](phase-02-i18n-and-icon-assets.md) | `momorph-ui-implementer` | A | complete | 0.5h |
| 03 | [Disclosure conversion](phase-03-floating-widget-disclosure.md) | `momorph-ui-implementer` | A | complete | 1.5h |
| 04 | [Adapt the-le FUN_003](phase-04-adapt-the-le-fun-003.md) | `tester` | gate | complete | 0.5h |
| 05 | [GREEN + visual validation](phase-05-green-and-visual-validation.md) | `tester` | gate | complete | 1h |

## Dependencies

```
01 (RED, must be first) ──> 02 ──> 03 ──┬──> 05 (GREEN + visual)
                                  04 ───┘
```

- 01 blocks everything: no UI code before a valid assertion RED. 03 needs 02's dictionary
  keys and the dark pen fill. 04 owns only `e2e/the-le.spec.ts`, green once 03 lands.
- Fixed command, RED and GREEN alike: `npx playwright test e2e/floating-action-button.spec.ts --project=anon`

## File ownership (no phase overlaps another)

| Phase | Owns |
|-------|------|
| 01 | `e2e/floating-action-button.spec.ts`, `e2e/fixtures/floating-action-button-constants.ts`, `playwright.config.ts` |
| 02 | `lib/i18n/messages/{dictionary.ts,vi-home.ts,en-home.ts}`, `public/images/home/widget-pen-icon.svg` |
| 03 | `app/_components/floating-widget.tsx` |
| 04 | `e2e/the-le.spec.ts`, `e2e/fixtures/the-le-constants.ts` (docblock only) |
| 05 | `evidence/**`; post-review also `e2e/capture-fab-visual.spec.ts` + its `fab-visual-capture` project |

## Track B — empty, deliberately

No new Supabase table, column or migration; no Server Action; no endpoint; no data model. The FAB
neither reads nor writes. Its two destinations are the surfaces that touch Supabase and both are
already shipped. Nothing was invented to fill the Track B shape.

## Out of scope

- `/standards`, `/kudos/new` and the `proxy.ts` guard are read-only navigation targets.
- FAB renders on `/` only; `app/page.tsx` unchanged (`Dictionary["home"]["widget"]` still fits).
- `public/images/rules/close-icon.svg` reused byte-identical; no second copy authored.

## Acceptance criteria (evidence/study-context.json) → phase

AC1 trigger with `aria-expanded` → 03 · AC2 three buttons revealed → 03 · AC3 `/standards` renders
→ 03/04 · AC4 anonymous `/kudos/new` → `/login` → 03 · AC5 Hủy/Escape/outside collapse → 03 ·
AC6 measured geometry reproduced → 03/05 · AC7 fixed command exits 0 → 05 · AC8 typecheck + lint
exit 0 → 05. Every AC is asserted first in the phase-01 RED spec.

## Delivery record

All five phases delivered, gates green. A post-review correction round (2026-09-10) fixed one
High finding (focus return on `Hủy`), pinned both menu items' accessible names, replaced a
fictitious `toBeCloseTo` pixel tolerance with a real one, and deleted two throwaway capture
specs that were breaking `npm run typecheck` while phase 05 reported it clean. Account:
[green-evidence.md](evidence/green-evidence.md) § "Post-review correction round" ·
[reviewer report](../reports/reviewer-260910-1506-floating-action-button.md).
