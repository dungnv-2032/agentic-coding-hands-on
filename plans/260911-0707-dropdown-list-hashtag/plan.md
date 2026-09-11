---
title: "Dropdown list hashtag — stateful multi-select open state (E13)"
description: "Turn the add-only hashtag menu on /kudos/new into a toggleable, selection-aware list that disables unselected rows at the 5-hashtag cap."
status: completed
priority: P2
effort: 3h
branch: feat/dropdown-list-hashtag
tags: [momorph, F005, viet-kudo, ui, e2e]
created: 2026-09-11
---

# Dropdown list hashtag (MoMorph `p9zO-c4a4x`)

One component plus its tests. E13 (`hashtag-menu`) is add-only today; the frame specifies a
stateful multi-select: visible selected state per row, click to toggle, unselected rows inert at
the cap with "Tối đa 5 hashtag" standing as the reason.

- Spec delta (requirement source, frozen): `spec/dropdown-list-hashtag/spec-delta.md` — FR-207..FR-211
- Clarifications (resolved, do not re-open): `clarifications.md`
- MoMorph: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/p9zO-c4a4x
- testPolicy: `e2e-red-first`

## Phases

| # | Phase | Owner | Status | Depends on |
|---|-------|-------|--------|-----------|
| 01 | [RED e2e — toggle, selected state, cap](phase-01-red-e2e-hashtag-dropdown.md) | tester (completed by orchestrator) | **done** — valid RED, exit 1, 5 assertion failures ([evidence](reports/tester-260911-0916-red-hashtag-dropdown.md)) | — |
| 02 | [UI — stateful hashtag option rows](phase-02-ui-stateful-hashtag-rows.md) | momorph-ui-implementer (completed by orchestrator) | **done** | 01 (valid RED) ✓ |
| 03 | [GREEN + visual evidence](phase-03-green-and-visual-evidence.md) | tester (completed by orchestrator) | **done** — targeted GREEN + 3 screenshots ([evidence](reports/tester-260911-0928-green-hashtag-dropdown.md)); full-suite run outstanding | 02 |

## Data flow (unchanged read path)

```
public.hashtags (13 rows, ORDER BY position)
  → getComposeOptions()            [untouched]
  → compose-form.tsx  options.hashtags / state.hashtags
  → HashtagPicker  options + selected
  → row click → isSelected ? onRemove(id) : onAdd(option)
  → dispatch removeHashtag | addHashtag  (compose-state.ts, untouched)
  → selected → chips (E14) + row affordance + cap-derived hashtag-error (E15)
```

## Key decisions carried in

- No route, table, migration, or Server Action. `getComposeOptions()` is unchanged.
- `compose-contract.ts` stays frozen: the toggle reuses the existing `onAdd`/`onRemove` callbacks.
- Menu still closes after every toggle (keeps ID-16 green).
- Row order = DB `position`. No hoisting of selected rows.
- At the cap: unselected rows `disabled` + dimmed **and** `hashtag-error` renders as the standing
  reason. Selected rows stay clickable — the only exit from the full state.
- ID-17 / ID-53 are **re-pointed** from `options.first()` (an already-selected row at the cap) to an
  *unselected* row, and additionally assert that row is `disabled`. This **strengthens** the tests:
  the cap is now asserted against the row the cap actually governs, plus a disabled-state assertion
  that did not exist before. Nothing is removed.

## File ownership (no overlap between phases)

| Phase | Owns |
|-------|------|
| 01 | `e2e/viet-kudo.spec.ts`, `e2e/fixtures/viet-kudo-constants.ts` |
| 02 | `app/kudos/new/_components/hashtag-picker.tsx` (+ new `hashtag-option-row.tsx` if needed) |
| 03 | `plans/260911-0707-dropdown-list-hashtag/evidence/*` (no source edits) |

Phases are strictly sequential — do not run 01 and 02 in parallel; 02 consumes 01's RED evidence.

## Done when

- `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed` is fully green, including the
  re-pointed ID-17/ID-53 and the new ID-57..ID-60.
- `npm run lint` and `npm run typecheck` clean.
- Every file touched stays under 200 lines.
- Evidence screenshots of the open menu in the empty / 1-selected / 5-selected states are in
  `evidence/`.

## Rollback

Each phase is one commit and reverts alone. Reverting 02 restores add-only behavior (01's new
assertions go red again but nothing else regresses); reverting 01 restores the old ID-17/ID-53
bodies. No data, schema, or contract change exists to migrate back.
