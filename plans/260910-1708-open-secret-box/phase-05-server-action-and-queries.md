---
phase: 05
title: "Track B — server action, queries, profile button unlock"
status: complete
owner: implementer
track: B
test_policy: e2e-red-first
effort: 1.5h
depends_on: [02, 03]
---

# Phase 05 — Track B: server action, queries, profile unlock

## Context Links

- [technical-spec](spec/open-secret-box/technical-spec.md) § 3.1, § 3.2 — the read and the write
- [functional-spec](spec/open-secret-box/functional-spec.md) FR-201, FR-601, FR-602, BR-001, BR-004
- [clarifications.md](clarifications.md) — `resolveViewer()` only; profile button enabled on one's
  own profile
- [phase-02](phase-02-shared-contract.md) — `OpenSecretBoxResult` is this action's return type
- [phase-03](phase-03-data-layer-migration.md) — the RPC's shape and its three errcodes
- Precedents: `app/kudos/_actions/toggle-kudos-like.ts`, `app/kudos/new/_actions/create-kudos.ts`,
  `lib/rules/queries.ts`, `lib/profile/profile-queries.ts`

## Overview

- **Priority:** P1 — the behaviour half of the feature.
- **Status:** pending
- One read module, one Server Action, and the profile stats card's button turned from `disabled`
  into a real link. Runs **concurrently with phase 04**; the two share no file.

## Key Insights

- `resolveViewer()` is the only identity source here. `resolveSidebarSunnerId()` is a display-only
  seed fallback — using it would let a session with no roster row read (and appear to own) the
  seeded frame viewer's boxes.
- **The action takes no arguments.** Everything is derived from the session inside Postgres. A
  parameter would be a forgery surface the database does not need (SB-08).
- The RPC `returns table (...)`, so supabase-js hands back an **array**: read `data?.[0]` and treat
  an empty array as `reason: "failed"`.
- Map errors by `code`, never by message text: `28000` → `unauthenticated`, `P0002` → `no-boxes`,
  anything else → `failed` (with a server-side `console.error`, no raw text to the client).
- `revalidatePath` for `/kudos/secret-box`, `/kudos` and `/profile` — three surfaces print this
  counter and must not disagree. The board sidebar and the profile stats card both read it.
- **The profile stats card only renders on one's own profile**: `getProfileData()` returns
  `stats: null` for another Sunner and `page.tsx` renders `WriteKudoBar` instead. So "enabled on my
  own profile, disabled on someone else's" resolves in practice to *enabled where the card exists,
  and the card does not exist elsewhere*. Do not add an `isSelf` prop to re-derive what the data
  layer already decided (SC-002) — and do not weaken that branch to make an "other profile,
  disabled button" case reachable.
- Enabling the button is **not** conditional on owning boxes: the screen handles zero boxes
  gracefully, and a button that disables at zero would contradict the screen it points at.

## Requirements

Functional:
- `lib/secret-box/queries.ts` → `fetchUnopenedCount(supabase, sunnerId): Promise<number>` — one
  `select secret_box_unopened_count ... eq id ... maybeSingle()`; a missing row is `0`, not a throw.
- `app/kudos/secret-box/_actions/open-secret-box.ts` — `"use server"`,
  `openSecretBox(): Promise<OpenSecretBoxResult>`; no parameters; calls
  `supabase.rpc("open_secret_box")`; maps the result/errors as above; revalidates the three paths on
  success only.
- `app/profile/_components/profile-stats-card.tsx` — the `<button disabled>` becomes a
  `<Link href="/kudos/secret-box">` keeping `data-testid="profile-secret-box-button"`, the accessible
  name exactly `Mở Secret Box`, the gift glyph `aria-hidden`, and every existing class token
  (`bg-[#FFEA9E]`, `rounded-lg`, `px-4 py-4`, the 22px bold label). Replace the stale
  "deferred commission" docblock with the current reading.

Non-functional: files under 200 lines; no `any`; the action never returns a Supabase error object;
`npm run typecheck` and `npm run lint` exit 0.

## Architecture

```
Client opener (phase 04) ─ props.openAction() ─> openSecretBox()   "use server"
                                                   ├─ createClient()            (cookie-bound)
                                                   ├─ rpc("open_secret_box")    no arguments
                                                   ├─ error.code → reason       28000 | P0002 | *
                                                   ├─ data[0] → { badge, unopenedCount, openedCount }
                                                   └─ revalidatePath ×3 (secret-box, kudos, profile)

page.tsx (phase 06) ─ resolveViewer() ─ fetchUnopenedCount() ─> { unopenedCount, canOpen, showSignIn }
```

No Supabase row shape crosses into a component: the action returns the phase-02 contract type, and
the query returns a plain number.

## Related Code Files

Create: `lib/secret-box/queries.ts`, `app/kudos/secret-box/_actions/open-secret-box.ts`.

Modify: `app/profile/_components/profile-stats-card.tsx` (the button only).

Read for context: `lib/kudos/viewer.ts`, `lib/supabase/server.ts`,
`app/kudos/_actions/toggle-kudos-like.ts`, `lib/profile/profile-data.ts` (the `stats: null` branch),
`lib/secret-box/contract.ts`.

Delete: none. Not modified: `lib/profile/**`, `app/profile/page.tsx`, `proxy.ts`, any e2e file.

## Implementation Steps

1. Write `lib/secret-box/queries.ts` following `lib/rules/queries.ts` — client passed in, `Row<>`
   alias from the generated types, an explanatory docblock.
2. Write the action. Map by `error.code`; log the unmapped case server-side with enough context to
   debug and nothing more.
3. Revalidate only after a successful open — a failed call must not invalidate three route caches.
4. Rewrite the profile button as a `<Link>`, preserving the testid, the accessible name and the
   token set. Update the docblock to say the Secret Box now exists.
5. `npm run typecheck && npm run lint`.
6. Expect `TC_WEB_PROFILE_GUI_005` to go red here — that is the intended consequence and phase 07
   re-aims it. Do not revert this change to restore green.

## Todo List

- [x] `fetchUnopenedCount` written, missing row → `0`
- [x] Action is parameterless and typed to `OpenSecretBoxResult`
- [x] Error mapping keyed on `code`, not message text
- [x] `data?.[0]` handled; empty array → `failed`
- [x] Three `revalidatePath` calls, success path only
- [x] Profile button is a `<Link>` with the testid, name and tokens intact; docblock refreshed
- [x] typecheck + lint exit 0

## Success Criteria

- `grep -n "resolveSidebarSunnerId" lib/secret-box app/kudos/secret-box` → no match.
- The action's signature is `(): Promise<OpenSecretBoxResult>` — no parameter of any kind.
- Opening from the running app decrements the stored counter by exactly one and appends one
  `secret_box_openings` row (`psql` check).
- `/profile` shows an enabled Secret Box link that navigates to `/kudos/secret-box`.
- `git diff --name-only` lists exactly the three files above.

## Risk Assessment

| Risk | L×I | Countermeasure |
|------|-----|----------------|
| Action grows a `sunnerId` parameter "for convenience" → forgery surface | L×**H** | Parameterless is a success criterion; SB-08 probes a forged argument |
| Error mapped by message text, so a Postgres wording change silently becomes `failed` | M×M | Map on `code`; the three codes are fixed by phase 03 |
| `revalidatePath` omitted → the sidebar and profile keep a stale count and contradict the screen | M×M | Three paths listed; SB-05 asserts the profile agrees after an open |
| Profile button enabled on another Sunner's page | L×M | Impossible by construction — `stats: null` there means the card never renders; do not "fix" it by adding a branch |
| `TC_WEB_PROFILE_GUI_005` red is read as this phase's defect and reverted | **H**×M | Called out in step 6, in plan.md § Dependencies, and owned by phase 07 |
| Raw Supabase error text surfaced to the browser | L×M | Only `reason` codes cross the boundary; copy comes from the dictionary |
| Written against stale generated types because phase 03 was skipped | L×**H** | `depends_on: [02, 03]`; a missing table type is a compile error, not a warning |

## Security Considerations

- The action is the only client-reachable write path, and it carries no identity input. The database
  re-derives the actor from `auth.uid()`.
- `fetchUnopenedCount` reads through the cookie-bound anon client under `sunners_select_all`; it is
  given a `sunnerId` that came from `resolveViewer()`, never from a URL or a form field.
- Nothing logs the session, the JWT or the email. The unmapped-error log records the errcode only.
- Enabling the profile link exposes no data: the destination enforces its own entitlement in-screen.

## Next Steps

- With phase 04, unblocks phase 06.
- Rollback: reverting the action and query is clean; reverting the profile button restores
  `TC_WEB_PROFILE_GUI_005` as originally written, so revert 05 and 07's profile edit together.
