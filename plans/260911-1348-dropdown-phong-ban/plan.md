---
title: "Dropdown Phòng ban — listbox fidelity + lock-in tests (F004/SCR004)"
description: "Fix three frame deviations in the shared filter listbox (centered text, cursor pointer, 348px bounded box) and write the e2e that locks in the department filter behavior that already works but is untested."
status: completed
priority: P2
effort: 3h
branch: feat/dropdown-phong-ban
tags: [momorph, F004, kudos, ui, e2e]
created: 2026-09-11
completed: 2026-09-11
---

# Dropdown Phòng ban (MoMorph `WXK5AYB_rG`)

One shared component, three real class fixes, five new locked-in tests. FR-210/211/212 (click → filter →
close, selected stays highlighted, re-click clears) already run in code — they're untested, not unbuilt.
FR-208/209/213 (centered text, pointer cursor, 348px box) are the genuine deviations.

- Spec delta (requirement source, frozen): `spec/dropdown-phong-ban/spec-delta.md` — FR-208..FR-213
- Clarifications (resolved, do not re-open): `clarifications.md`
- MoMorph: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/WXK5AYB_rG
- testPolicy: `e2e-red-first`

## Phases

| # | Phase | Owner | Status | Evidence |
|---|-------|-------|--------|----------|
| 01 | [RED e2e — department dropdown](phase-01-red-e2e-department-dropdown.md) | tester | done* | [report](reports/tester-260911-1400-red-department-dropdown.md) |
| 02 | [UI — dropdown fidelity fixes](phase-02-ui-department-dropdown-fidelity.md) | momorph-ui-implementer | done | c174d6f |
| 03 | [GREEN + visual evidence](phase-03-green-and-visual-evidence.md) | orchestrator** | done | [report](reports/tester-260911-1445-green-department-dropdown.md) |

*Phase 01: tests written and RED recorded. The tester agent then ran `git checkout` and destroyed the uncommitted K-26..K-30 tests before the run could be certified. Tests were restored from review context by the orchestrator, re-verified from scratch (scoped 6/6, then full-file 30/30), and committed before further work. All verified outcomes are real exit codes.

**Phase 03: Assigned to tester but executed by orchestrator after the above incident. GREEN (exit 0, 6/6), full-file regression (30/30), lint + typecheck clean, three evidence screenshots captured and compared to frame — all match.

## Data flow (unchanged read/filter path)

```
public.departments (52 rows, 50 filter_position)
  → fetchFilterOptions()                     [untouched]
  → kudos-board.tsx  departmentFilterId / matchesFilters()   [untouched]
  → KudosFilterBar  → KudosFilterMenu (scrollable)           [phase 02 only]
  → click option → onSelect → close menu → filteredKudos recomputed
    → HighlightCarousel (max 5 slides) + AllKudosFeed (10/page) both re-render
  → click same option again → departmentFilterId → null → board restored
```

## Key decisions carried in

- No route, table, migration, Server Action, or URL param change. `matchesFilters()`, `fetchFilterOptions()`
  untouched.
- `kudos-filter-menu.tsx` is shared by hashtag + department (same Figma component instance) — FR-208/209
  apply to both listboxes, not just department. Not a side effect; the frame is one component.
- FR-213's `max-h-[348px]` only applies where `scrollable` is already gated (department); the `gap-1`
  removal (needed so 6×56px rows sum to exactly 348px) applies to the shared row container.
- Selected/hover color tokens (`bg-[rgba(255,234,158,0.10)]`, hover `rgba(255,234,158,0.05)`) stay as-is —
  already correct per clarifications.
- e2e assertion department: `STVC - R&D` (12/69 seeded kudos — narrows visibly, still has cards to check).
- FR-210/211/212 get lock-in tests only; the phase-02 owner touches nothing behind them.

## File ownership (no overlap between phases)

| Phase | Owns |
|-------|------|
| 01 | `e2e/kudos-live-board.spec.ts`, `e2e/fixtures/kudos-constants.ts` |
| 02 | `app/kudos/_components/kudos-filter-menu.tsx` |
| 03 | `plans/260911-1348-dropdown-phong-ban/evidence/*` (no source edits) |

Phases are strictly sequential — 02 consumes 01's RED evidence; 03 consumes 02's code.

## Done when

- [x] `npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon` fully green, K-26..K-30 included (exit 0, 30/30).
- [x] `npm run lint` clean (exit 0, 31 pre-existing warnings, none new).
- [x] `npm run typecheck` clean (exit 0).
- [x] `app/kudos/_components/kudos-filter-menu.tsx` under 200 lines (61 lines).
- [x] Evidence screenshots in `evidence/`: closed, open unselected, open with "STVC - R&D" selected.
- [x] Review: 9/10, 0 critical, 0 high.
