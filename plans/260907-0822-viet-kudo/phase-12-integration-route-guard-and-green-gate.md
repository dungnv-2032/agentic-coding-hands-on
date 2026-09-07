# Phase 12 — Integration, route guard & GREEN gate

**Track:** Shared · **Owner:** `implementer` · **Depends:** 02, 05, 07, 11 ·
**Effort:** 2.5h · **test_policy:** `e2e-red-first`

## Context Links

- [plan.md](plan.md) · [phase-02](phase-02-red-gate-defect-repair.md) (the repaired gate) · [phase-05](phase-05-board-surface-doc-and-anonymity.md) · [phase-07](phase-07-write-path-validation-and-actions.md) (the two actions) · [phase-11](phase-11-compose-form-assembly.md) (the form)
- [clarifications.md](clarifications.md) § Route, auth, and the modal question · § Shared chrome and i18n
- [test-contract.md](test-contract.md) § Route and access
- [technical-spec.md](spec/viet-kudo/technical-spec.md) § 3.1 A1, § 4.4 A0 (the auth gate), § 5.4 rows 1–3
- Files to change: `app/kudos/new/page.tsx:1-15` (the `ComingSoon` placeholder), `proxy.ts:41-46` (the guard list)
- Composition to mirror exactly: `app/kudos/page.tsx:47-98` (`getPageContext()` + `HomeHeader` + `main` + `SiteFooter`, actions passed as props)
- Next 16.3.4 docs read for this phase: `01-app/03-api-reference/03-file-conventions/proxy.md`

## Overview

**Priority:** P1 · **Status:** completed.

Two files, then the gate. `page.tsx` becomes the real screen and `proxy.ts` gains one prefix; then
the whole suite runs and the commission is either done or it is not.

## Key Insights

1. **The guard must be narrow.** `/kudos` and every other Kudos read surface stay public — that is a
   ratified F004 property and half of `kudos-live-board.spec.ts` depends on it. Match
   `pathname === "/kudos/new" || pathname.startsWith("/kudos/new/")`, not
   `startsWith("/kudos")`, and add it to the **existing** `!user` branch beside `/todo` rather than
   introducing a second mechanism.
2. **The redirect must reuse the rotated session cookies.** `proxy.ts` already solves this with
   `redirectWithSessionCookies`, and its comment explains exactly why a bare
   `NextResponse.redirect` silently logs the user out (single-use refresh tokens, plan risk R1, E2E
   case C8). Call the existing helper. Do not write a second redirect.
3. **`page.tsx` is the only place both tracks meet.** It reads (`getPageContext()`,
   `getComposeOptions()`), composes the chrome, and passes `createKudos` and `uploadKudosImage` down
   as props — the shipped `signOutAction`/`toggleLike` pattern. No Track A component imports either
   action directly, which is what made the two tracks parallelisable.
4. **The chrome is composed, not rebuilt** (clarifications § Shared chrome): `montserrat` fonts,
   `HomeHeader` with the four booleans from `getPageContext()`, `main`, `SiteFooter`. No
   `FloatingWidget`, no `KudosPromo` — the frame shows neither, exactly as `/kudos` decided.
5. **The Supabase `user` object never crosses into a Client Component.** `getPageContext()` returns
   only `locale`/`dictionary`/`isAuthenticated`/`isAdmin`, and that rule
   (`app/_page-context.ts:22-25`) holds here too.
6. **`metadata.title` stays.** The placeholder already sets
   `"Sun* Kudos New — Sun* Annual Awards 2025"`; keep it rather than inventing a new one.
7. **Run the suites in the right order and give the full run its 30 minutes.** Narrow slices during
   development; for the gate: the compose suite, then `route-guard`, then every shipped suite. A full
   RED-era run took ~30 minutes because each failing test burnt its timeout — a **green** run is far
   faster, so a slow run is itself a signal that something is still failing.
8. **`npx supabase db reset` runs once, before the gate, never between suites.** Mid-suite it
   truncates `auth.users` and bounces the live browser to `/login`. After the reset the composed rows
   from earlier development runs are gone, which is also the cleanup phase 02 documented.
9. **The e2e user gets provisioned during the run**, so the authed board's sidebar switches from the
   seeded viewer's 25/25/25/25/25 to that user's own zeroes once ID-46/47 has run. Verified: K-18 is
   in the `anon` project and asserts labels, not values, so nothing breaks — but if a future test
   asserts sidebar numbers for an authed viewer, this is where it will bite.

## Requirements

**Functional:** FR-101/FR-601 (the guard), FR-102 (the route renders the screen), the whole feature
composed end to end. The definition of done from `plan.md`.

**Non-functional:** `page.tsx` ≤200 lines (it will be ~70); `proxy.ts` grows by one condition;
`npm run typecheck`, `npm run lint` and `npm run build` all exit 0; no shipped assertion weakened
beyond phase 02's ratified amendments.

## Architecture

```
proxy.ts  (one condition added to the existing !user branch)
  const isGuarded = pathname.startsWith("/todo")
    || pathname === "/kudos/new" || pathname.startsWith("/kudos/new/");
  if (!user && isGuarded) return redirectWithSessionCookies("/login");
  if (user && pathname.startsWith("/login")) return redirectWithSessionCookies("/todo");

app/kudos/new/page.tsx  (~70 lines, server component)
  export const metadata = { title: "Sun* Kudos New — Sun* Annual Awards 2025" };
  export default async function KudosComposePage() {
    const [{ locale, dictionary, isAuthenticated, isAdmin }, options] =
      await Promise.all([getPageContext(), getComposeOptions()]);
    return (
      <div className={`${montserrat.variable} … bg-[#00101A] font-montserrat`}>
        <HomeHeader locale dictionary isAuthenticated isAdmin signOutAction={signOut} />
        <main className="flex flex-1 flex-col items-center …">   {/* dimmed page, centred card */}
          <ComposeForm options={options} copy={dictionary.kudosCompose}
                       createKudos={createKudos} uploadImage={uploadKudosImage} />
        </main>
        <SiteFooter dictionary={dictionary} />
      </div>
    );
  }
```

**End-to-end flow, all phases joined:**
```
anon → /kudos/new → proxy → /login                                    (ID-1)
authed → /kudos/new → page reads options → ComposeForm renders        (ID-0 … ID-44)
  pick image → uploadKudosImage → Storage object → public URL → thumb (ID-21/22/37)
  submit → validate (client) → createKudos → validate (server)
         → rpc create_kudos → provision sunner → kudos + hashtags + attachments (one txn)
         → redirect("/kudos") → board re-renders → new card, newest first (ID-46/47)
  cancel → <a href="/kudos">                                          (ID-45)
```

## Related Code Files

**Modify:** `app/kudos/new/page.tsx` · `proxy.ts`
**Create:** none · **Delete:** none
**Read only:** `app/kudos/page.tsx` (the composition to mirror), `app/_page-context.ts`,
`app/_actions/auth.ts`, `app/_fonts.ts`, phase 07's actions, phase 11's `compose-form.tsx`

## Implementation Steps

1. `proxy.ts` — the one condition from § Architecture, plus one sentence in the file's header comment
   recording that `/kudos/new` is guarded and that the rest of `/kudos` is deliberately public.
2. `app/kudos/new/page.tsx` — replace the `ComingSoon` body with § Architecture's composition. Keep
   the `metadata` export. Write the header doc-comment in the shipped style, naming the screen
   (`ihQ26W78P2`), the two-track split, and why both actions arrive as props.
3. `npm run typecheck && npm run lint && npm run build`. The build is the gate for `next.config.ts`'s
   `remotePatterns` and for any accidental server-only import in a client component.
4. `npx supabase db reset`, once.
5. The compose gate, exactly as the definition of done states it:
   ```
   npx playwright test e2e/viet-kudo.spec.ts e2e/route-guard.spec.ts --reporter=list
   ```
   Must exit 0. Capture the output to `evidence/viet-kudo-green-run.log`.
6. The blast-radius gate — every shipped suite, unchanged:
   ```
   npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts \
     e2e/authenticated.spec.ts e2e/callback-security.spec.ts e2e/login-screen.spec.ts \
     e2e/homepage.spec.ts e2e/homepage-authed.spec.ts e2e/award-system.spec.ts \
     e2e/smoke.spec.ts --reporter=list
   ```
   Must exit 0. Capture to `evidence/viet-kudo-regression-run.log`.
7. Idempotency: re-run step 5 **without** a db reset in between. It must exit 0 again. The second run
   starts with one extra kudos row and a provisioned sunner already present, which is the state a
   real second run has — if the suite only passes from a pristine database, say so rather than
   papering over it.
8. Prove the write reached Postgres, not just the DOM:
   ```
   docker exec supabase_db_my-app psql -U postgres -d postgres -c \
     "select k.id, k.campaign, k.message_format, k.is_anonymous,
             (select count(*) from kudos_hashtags h where h.kudos_id = k.id) tags,
             (select count(*) from kudos_attachments a where a.kudos_id = k.id) imgs,
             s.full_name sender, d.name dept
        from kudos k join sunners s on s.id = k.sender_id
        join departments d on d.id = s.department_id
       where k.campaign = 'Người truyền động lực cho tôi' order by k.id desc limit 3;"
   ```
   Expect `message_format = 'doc'`, `tags >= 1`, `imgs >= 1`, and a sender whose department is
   `Unassigned` — the provisioned identity. Also confirm the Storage object exists and is publicly
   readable via its URL.
9. Confirm the `kudos_likes` invariant F004 relies on is untouched:
   `select count(*) from kudos_likes;` must be 0 after the run (K-10/K-25 both toggle back).
10. Write the phase report to `reports/` with the four captured logs referenced, the exit codes, and
    the answers to steps 7–9.

## Todo List

- [x] `proxy.ts` guards `/kudos/new` only, through the existing `redirectWithSessionCookies` helper
- [x] Header comment records that the rest of `/kudos` stays public
- [x] `page.tsx` composes the shipped chrome; both actions passed as props; `metadata` kept
- [x] No Track A component imports a Track B module (`grep` the `_components` dir for `_actions`)
- [x] `npm run typecheck && npm run lint && npm run build` all exit 0
- [x] `npx supabase db reset` once, before the gate
- [x] Step 5 compose gate exits 0; log captured
- [x] Step 6 regression gate exits 0; log captured
- [x] Step 7 second run exits 0 with no reset (idempotent)
- [x] Step 8 database proof: `'doc'`, tags, images, `Unassigned` sender, object publicly readable
- [x] Step 9 `kudos_likes` back to 0
- [x] Phase report written with exit codes and the three answers

## Success Criteria

- `npx playwright test e2e/viet-kudo.spec.ts e2e/route-guard.spec.ts --reporter=list` exits **0**,
  with 59 + ID-1 tests and nothing skipped.
- Every shipped suite in step 6 exits 0.
- Step 5 passes twice in a row without a database reset.
- The composed row exists in Postgres with `message_format='doc'`, at least one hashtag, at least one
  attachment, and a sender in the `Unassigned` department.
- `/kudos` is still reachable and fully rendered without a session; `/kudos/new` without a session
  lands on `/login`.
- `npm run build` exits 0.
- `grep -rn "_actions" app/kudos/new/_components/` returns nothing.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| The guard is written as `startsWith("/kudos")` and takes the public board private | Med × **High** | Exact-match plus trailing-slash form, spelled out in § Architecture; step 6's board suite fails loudly if it happens |
| A bare `NextResponse.redirect` drops the rotated refresh token and logs users out | Med × **High** | Reuse `redirectWithSessionCookies`; `callback-security.spec.ts` and `authenticated.spec.ts` in step 6 are the detectors |
| The full run is slow and gets abandoned half-way | **High** × Med | Narrow slices during development; the gate is budgeted at ~30 min and a slow *green* run is itself a signal |
| The suite only passes from a pristine database | Med × High | Step 7 makes the second run a criterion, not an afterthought |
| A server-only module reaches a client component and only `next build` catches it | Med × Med | Step 3 runs `build`, not just typecheck |
| ID-46/47's board check fails because the new card is not on the first feed page | Low × High | Feed is `sent_at desc` and `FEED_PAGE_SIZE` is 10, so a just-created row is first; step 8 confirms the row independently of the DOM |
| A test that passed in a narrow slice fails in the full run because of cross-test state | Med × Med | `fullyParallel: false` already serialises; step 7's rerun is the real check |
| Phase 02's amendment was never ratified and ID-48 still asserts `toBeDisabled()` | Med × **High** | Confirm ratification before starting; otherwise this gate cannot pass and the blocker is contractual, not technical |

**Rollback:** revert `page.tsx` to the `ComingSoon` placeholder and drop the `proxy.ts` condition.
The route resolves, the board is untouched, and every earlier phase's code sits dormant — the
cutover really is two files.

## Security Considerations

- The guard is the first new one since F001. It must protect exactly `/kudos/new` and nothing more;
  over-guarding is as much a defect here as under-guarding.
- `/auth/callback` stays unguarded — guarding it would make the OAuth round trip structurally
  impossible (`proxy.ts`'s own comment, plan risk R2).
- The Supabase `user` object stops at `getPageContext()`; only booleans reach `HomeHeader`.
- Both Server Actions are reachable by POST regardless of the guard, which is exactly why phase 07
  validates and phase 03's RLS re-checks. The guard is a UX affordance, not the security boundary.
- No `service_role` key anywhere in the run; step 8's `psql` access is the local container's
  superuser, used only for verification, never by application code.

## Next Steps

Hand off to `reviewer`, then to `doc-writer`/promote: `spec/viet-kudo/` and the two
`spec/system/` drafts become the real docs, the `F###` code is allocated at promote, and
clarifications' six unresolved questions plus this commission's three resolved conflicts travel with
them. The anonymous card still has no automated coverage (phase 05) — flag it as the first
follow-up.
