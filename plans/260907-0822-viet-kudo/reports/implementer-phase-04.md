# Phase 04 — Board contract & read mapping — Implementer report

**Status:** completed. Commit `60958c2`.

## View-model surface added (phases 05, 07 hold to this)

`lib/kudos/view-model.ts` — `KudosCardView` gains, additively:

```ts
messageFormat: MessageFormat;        // "plain" | "doc", imported as a type from compose-contract.ts
anonymousSenderLabel: string | null; // non-null ⇒ card renders the anonymous chip in place of `sender`
```

No other field's meaning changed. `sender` stays `SunnerView`; for an anonymous row it now holds a
**redacted** `SunnerView` (`id: 0, fullName: <label>, department: "", avatarUrl:
"/images/kudos/sample-avatar.png", badge: "New Hero", badgeTooltip: null`) — real identity never
enters this object. `receiver` is always the real sunner (A3: anonymity hides the giver only).

## Files touched

- `lib/supabase/database.types.ts` — regenerated (`npm run db:types`), +22/-1. Confirmed
  `message_format`, `is_anonymous`, `anonymous_name` on `kudos` Row/Insert/Update, and the
  `create_kudos(...)` RPC signature. Not hand-edited.
- `lib/kudos/view-model.ts` (+14) — two new `KudosCardView` fields, header note naming this phase.
- `lib/kudos/queries.ts` (+4/-1) — `fetchKudos` select string and `KudosFeedRow` both extended with
  `message_format, is_anonymous, anonymous_name`. Nothing else in the query changed (same order,
  same FK hints, same `likes:kudos_likes(count)`).
- `lib/kudos/board-data.ts` (+37/-21, now exactly 200 lines) — `ANONYMOUS_FALLBACK_LABEL = "Ẩn danh"`,
  `toAnonymousSenderView(label)`, and the `rows.map` extended per spec: `anonymousSenderLabel`
  computed once per row (`row.anonymous_name?.trim() || ANONYMOUS_FALLBACK_LABEL` when
  `is_anonymous`, else `null`), `sender` branches on that label, `messageFormat` narrowed by
  `row.message_format === "doc" ? "doc" : "plain"` (comparison, never a cast). `canLike` /
  `isOwnedByViewer` still read `row.sender.id` (the raw query row), never the redacted stub's `id: 0`.

## Checks

- `npm run db:types` — ran clean against the applied phase-03 migration; `\d public.kudos` confirmed
  the 3 columns before running.
- `npm run typecheck` — **0 errors** repo-wide.
- `npm run lint` — **0 errors**; 28 pre-existing warnings, all in `e2e/*.spec.ts` files outside this
  task's scope (unused fixture locators, not touched here).
- Real-data probe (`/tmp/.../scratchpad/probe-board-data-read-path.ts`, run via a Node ESM loader
  that strips TS and stubs `next/headers` — no cookies ⇒ unauthenticated viewer): inserted one
  `message_format='doc', is_anonymous=true, anonymous_name='Người bí ẩn'` row via `psql`, called the
  real `getKudosBoard()`, then deleted the probe row. Output:
  ```
  kudos count: 58
  top-5 highlight heart totals: [ 1000, 58, 56, 54, 52 ]

  --- one 'plain' row (seeded, non-anonymous) ---
  { id: 1, messageFormat: 'plain', anonymousSenderLabel: null,
    sender: { id: 1, fullName: 'Huỳnh Dương Xuân Nhật', department: 'CEVC10', badge: 'Super Hero', ... },
    receiver: { id: 2, fullName: 'Huỳnh Dương Xuân' }, canLike: false, isOwnedByViewer: false }

  --- one 'doc' row (PHASE04 PROBE, anonymous) ---
  { id: 58, messageFormat: 'doc', anonymousSenderLabel: 'Người bí ẩn',
    sender: { id: 0, fullName: 'Người bí ẩn', department: '', badge: 'New Hero', badgeTooltip: null },
    receiver: { id: 2, fullName: 'Huỳnh Dương Xuân' },
    message: '{"blocks":[{"type":"paragraph","runs":[{"type":"text","text":"probe","bold":true}]}]}',
    canLike: false, isOwnedByViewer: false }
  payload contains real sender name? (should be false): false
  ```
  Real sender for the probe row (verified via `psql`) was `Huỳnh Dương Xuân Nhật` — confirmed absent
  from the mapped payload's `sender`. Post-delete count back to **57**.
  `canLike`/`isOwnedByViewer` reading the real id (not the `id: 0` stub) is additionally verified by
  code inspection — both lines read `row.sender.id`, the raw query row, never the mapped `sender`
  object — since the anonymous probe viewer here is unauthenticated, both flags are `false`
  regardless and can't distinguish the two ids by output alone.
- `npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts --reporter=list`
  — **27 passed** (1.8m). Port 3000 was free before the run (`ss -ltnp`, no leftover `next dev`).

## Acceptance criteria

- [x] Migration confirmed applied, `db:types` regenerated with the 3 columns.
- [x] `KudosCardView` gains `messageFormat` + `anonymousSenderLabel`, header updated.
- [x] `queries.ts` select string and `KudosFeedRow` both extended; nothing else in the query changed.
- [x] `board-data.ts` redacts sender for anonymous rows, keeps real id for `canLike`/`isOwnedByViewer`.
- [x] `message_format` narrowed by comparison, never cast.
- [x] `board-data.ts` ≤200 lines (exactly 200).
- [x] Probe: anonymous label renders (`Người bí ẩn`), receiver unaffected, real name absent from payload.
- [x] Probe deleted; `kudos-live-board.spec.ts` + `kudos-live-board-authed.spec.ts` green (27/27).
- [x] `getKudosBoard()` satisfies the extended contract with no cast, no `any`.
- [x] Seeded rows: `messageFormat === "plain"`, `anonymousSenderLabel === null`, sender mapping unchanged.

## Handoff note for phase 05

A `'doc'` row's `message` currently reaches the card as the raw serialized JSON string (see the probe
output above) — `board-data.ts` does not parse or render it, by design (§ Overview: "producer-only").
Phase 05 is the renderer.

## Notes

- `e2e/kudos-live-board.spec.ts` showed as modified in `git status` at session start/throughout — not
  touched by this task (e2e is tester-owned); some other concurrent process edited it.
- `lib/i18n/messages/{en,vi}-kudos-compose.ts` appeared during this session (phase 06, concurrent) —
  not read or touched.

## Unresolved questions

None blocking. `Ẩn danh` as the neutral fallback label is data placed in `board-data.ts` per the
plan's explicit instruction (Key Insight 4) — clarifications.md's own "Unresolved question 4" only
covers `Danh hiệu` field authoring, not this fallback string, so no open question carries forward from
this phase.

**Status:** DONE
**Summary:** Regenerated `database.types.ts` and extended `queries.ts`/`board-data.ts`/`view-model.ts`
additively for `message_format`, `is_anonymous`, `anonymous_name`; typecheck/lint clean, real-data
probe confirmed correct redaction and F004-identical `'plain'` mapping, and both Kudos Live Board
Playwright suites stayed green (27/27) after cleanup.
**Concerns/Blockers:** None.
