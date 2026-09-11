# GREEN — Dropdown Phòng ban (MoMorph `WXK5AYB_rG`)

Run by the orchestrator. The phase-03 tester agent destroyed the uncommitted
K-26..K-30 source with a `git checkout` before it could certify; the tests were
restored from review context, re-verified from scratch, and committed before any
further agent touched the tree. Every number below is a real exit code from a
command run after the restore.

## RED → GREEN pair (commands byte-identical)

| | Command | Exit |
|---|---|---|
| RED (pre-fix) | `npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon -g "K-26\|K-27\|K-28\|K-29\|K-30"` | **1** |
| GREEN (post-fix) | same command | **0** — 6 passed (1.7m) |

RED failures were genuine assertion failures, not environment:
- K-26 — computed `text-align` "left" ≠ "center"; computed `cursor` "default" ≠ "pointer"
- K-27 — `boundingBox().height` 320 ≠ 348; computed `max-height` "320px" ≠ "348px"
- K-28 / K-29 / K-30 — passed from the start: the select → close → filter → toggle-off
  behaviour already shipped in `kudos-board.tsx`. They stand as regression guards, and
  are the first tests ever to assert it.

## Full-file regression (mandatory — the listbox is shared with the hashtag filter)

`npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon` → **30 passed (1.5m)**.
K-3 (hashtag: 13 options, exact text) green, so the shared-component change did not
regress the other listbox.

## Static gates

- `npm run typecheck` — exit 0
- `npm run lint` — exit 0, 31 pre-existing warnings, none new
- `wc -l app/kudos/_components/kudos-filter-menu.tsx` — 61 lines, under the 200 ceiling

## Geometry check (orchestrator-requested, beyond the phase file)

The option rows are flex children of an `overflow-y-auto` column, so they could have
shrunk — leaving the container at 348px while showing more than the frame's six rows.
Asserted inline in the capture spec and passing:

- `filter-menu-department` boundingBox height = **348** (exact)
- first `[role="option"]` boundingBox height = **56** (exact)

Six rows, as the frame draws them. The concern is disproven, not assumed away.

## Visual evidence

`npm run test:e2e -- --project=department-dropdown-visual-capture` → 1 passed.

- `evidence/department-dropdown-closed.png` — both triggers closed
- `evidence/department-dropdown-open-unselected.png` — 6 centred labels in the bounded box
- `evidence/department-dropdown-open-selected.png` — "STVC - R&D" on the lighter fill with the gold glow

Frame comparison (`WXK5AYB_rG`): dark `#00070C` box, gold hairline border, rounded
corners, centred bold white labels, six rows visible, selected row on a lighter fill
with a gold text glow — all present. No material mismatch.

## Unresolved questions

None.
