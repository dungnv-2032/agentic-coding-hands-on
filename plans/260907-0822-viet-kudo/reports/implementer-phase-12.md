# Phase 12 report — integration, route guard & GREEN gate

**Status:** DONE_WITH_CONCERNS

## Files touched
- `app/kudos/new/page.tsx` (61 ln) — cutover, `ComingSoon` → real composition per § Architecture.
- `proxy.ts` (65 ln) — `/kudos/new` added to the existing `!user` guard branch, exact-match/subpath
  form, reuses `redirectWithSessionCookies`.
- `app/kudos/new/_actions/upload-kudos-image.ts` (81 ln) — **1-line build-error repair**, see below.
- `app/kudos/new/_components/use-body-editor-controller.ts` (145 ln) — **coordinator-authorized
  cross-phase fix**, ID-33 diacritic bug, see below.
- `app/kudos/new/_components/recipient-picker.tsx` (155 ln) — same fix applied for consistency
  (coordinator's "your call" note; done for one shared normalizer instead of a second one).

## Two out-of-scope fixes, both disclosed loudly per the escalation rules

### 1. `upload-kudos-image.ts` — build-breaking, one-line, self-authorized
`next build` failed: `UploadKudosImageError` (phase 07) was an **exported class** in a `"use
server"` file — Next 16 only allows async-function exports there. `grep -rn "UploadKudosImageError"`
confirmed nothing outside that file imports it (no `instanceof`/`.code` check anywhere — the picker's
catch block is bare). Dropped the `export` keyword only; behavior, signature and the
throw-to-signal-failure contract (Wave-2 ruling #3) are unchanged. This is the "unambiguous one-line
fix in a file no other agent is holding" exception in my brief.

### 2. Mention-menu diacritic matching — coordinator-authorized, not self-authorized
First GREEN attempt: 61/62 passed, `ID-33` ("typing @Nguyen filters mention menu") failed
deterministically (reproduced twice). Root cause: `use-body-editor-controller.ts`'s mention filter
did a plain `.toLowerCase().includes()` substring check; seeded names are `Nguyễn ...` (diacritics),
the authored test types `@Nguyen` (none). `recipient-picker.tsx` had the identical gap but no test
exercises it with an unaccented query. I reported this to the coordinator rather than touching
`_components/**` myself; the coordinator confirmed the test is faithful to `design/test-cases.csv`
and explicitly authorized a bounded fix in those two files. Added one exported helper,
`foldVietnameseText` (NFD-normalize, strip combining marks `U+0300`–`U+036F`, fold `đ/Đ` explicitly
since Vietnamese treats those as base letters, not diacritics), used by both the mention filter and
`recipient-picker.tsx` (one normalizer, not two). Verified against seed data including `Đỗ Hoàng Hiệp`.

## Checks
- `npm run typecheck` — exit 0, 0 errors (after both fixes).
- `npm run lint` — exit 0, 0 errors, 28 pre-existing warnings in tester-owned `e2e/*.spec.ts`.
- `npm run build` — exit 0. `/kudos/new` compiles as `ƒ` (dynamic), same as every other route.
- `grep -rn "_actions" app/kudos/new/_components/` → nothing (Track A/B separation intact).

## GREEN gate
```
npx playwright test e2e/viet-kudo.spec.ts e2e/route-guard.spec.ts --reporter=list
```
- Attempt 1 (fresh `db reset`): 61 passed / 1 failed — `ID-0` (see flake note below).
- Attempt 2 (no reset): **62 passed, exit 0.**
- Attempt 3 (no reset, idempotency proof): **62 passed, exit 0.**

Saved: `evidence/viet-kudo-green-run.log` = attempt 3, exit code `0` on the last line.

**`ID-0` flake, disclosed not hidden:** "This page couldn't load" once, caused by
`getComposeOptions (sunners) failed: JWT issued at future` — a GoTrue/Postgres clock-skew message
that appears only on the very first authenticated request immediately after a fresh `db reset`
(containers just restarted). Reproduced twice in isolation (fails right after reset, passes on
immediate retry with no code change, passes again on a second reset+retry cycle). Not caused by
`page.tsx`/`proxy.ts` — it is the same code path every subsequent request in the same run uses
successfully. Recorded as an environmental flake, not swept under the rug: two consecutive clean 62/62
runs are the actual gate evidence.

## Blast-radius regression
```
npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts \
  e2e/authenticated.spec.ts e2e/callback-security.spec.ts e2e/login-screen.spec.ts \
  e2e/homepage.spec.ts e2e/homepage-authed.spec.ts e2e/award-system.spec.ts e2e/smoke.spec.ts
```
Final run: **86 passed / 1 failed** (`K-25`, `kudos-live-board-authed.spec.ts`), exit 1. Saved:
`evidence/viet-kudo-regression-run.log`.

**`K-25` is a pre-existing flake, not a regression from this phase — evidence:**
- `K-25` and `award-system` ID-3 both failed once in an earlier full-suite attempt; run in isolation
  (`kudos-live-board-authed.spec.ts` + `award-system.spec.ts` alone, 2 workers) both passed clean.
- Reproduced the `K-25` failure **three separate times**, always under the same condition: many spec
  files across 2 Playwright workers contending for CPU/DB, never in isolation. The assertion that
  fails is the test's own final "click heart back to original, expect count reverted" step timing out
  under load — nothing in `viet-kudo.spec.ts` or my two files touches `kudos_likes`.
- `kudos-live-board-authed.spec.ts` and `award-system.spec.ts` are outside this task's file scope; not
  touched.

## Idempotency (step 7)
Two consecutive `viet-kudo.spec.ts` + `route-guard.spec.ts` runs, no reset in between: both 62/62,
exit 0.

## Database proof (step 8)
```
 id | campaign                      | message_format | is_anonymous | tags | imgs | sender (email-local) | dept
 60 | Người truyền động lực cho tôi | doc             | f            | 1    | 1    | e2e-...-40izyq        | Unassigned
 59 | ...                           | doc             | f            | 1    | 1    | e2e-...-q5vadu        | Unassigned
 58 | ...                           | doc             | f            | 1    | 1    | e2e-...-lvm42c        | Unassigned
```
Three rows (one per compose-gate attempt run after the last `db reset`), each `message_format='doc'`,
1 hashtag, 1 attachment, sender auto-provisioned into `Unassigned` (A1). Storage object for kudos 60
confirmed publicly readable: `curl -o /dev/null -w "%{http_code}" <public url>` → `200`.

**Row accumulation:** `kudos` count 57 → 60 (+3), `sunners` 9 → 12 (+3 provisioned e2e users). Matches
"one row per successful compose-gate run since last reset," as the contract accepts (no DELETE
policy by design).

## Step 9 — `kudos_likes` invariant
`select count(*) from kudos_likes` → **1**, not 0. Traced to the `K-25` flake above: its final
toggle-back click didn't land within the assertion's retry window in a loaded run, leaving one
dangling like on the top HIGHLIGHT card. This is `kudos-live-board-authed.spec.ts`'s own pre-existing
test artifact, not something `viet-kudo.spec.ts` or my two files write to. Reported per instruction
("state it, don't hide it") rather than deleted — deleting it via the verification `psql` session
felt like erasing the evidence of the flake rather than fixing its cause.

## Other observations (not blocking, flagged for follow-up)
- `[browser] An async function with useActionState was called outside of a transition` — a React
  console warning from `compose-form.tsx:87` (phase 11's file, not touched). No test currently fails
  on it; flagging since `ComposeForm`'s own report already listed submit-ordering as unverified by any
  assertion.
- `⨯ upstream image ... hostname resolved to private IP ["127.0.0.1"]` — Next 16's SSRF guard logs
  this once per newly-created attachment because local dev's `NEXT_PUBLIC_SUPABASE_URL` is
  `127.0.0.1:54321`. Never failed a test (ID-46/47 don't assert the `<img>` actually paints), but the
  new attachment's thumbnail likely doesn't render on `/kudos` locally. `next.config.ts` is phase 03's
  file, out of my scope; local-dev-only (a real Supabase host in prod isn't a private IP), so left
  unfixed and flagged rather than touched.

## Acceptance criteria
- [x] `proxy.ts` guards `/kudos/new` only (exact/subpath), via `redirectWithSessionCookies`; header
  comment records the rest of `/kudos` stays public.
- [x] `page.tsx` composes the shipped chrome; both actions passed as props; `metadata` kept.
- [x] `grep -rn "_actions" app/kudos/new/_components/` → nothing.
- [x] `typecheck && lint && build` all exit 0.
- [x] `db reset` run before the gate (twice, total, across the debugging cycle — never mid-suite).
- [x] Compose gate exits 0, twice consecutively, no reset between (62/62 both times).
- [ ] Regression gate: 86/87 pass; `K-25` is a disclosed pre-existing flake (evidence above), not
      fixed (out of scope, not caused by this phase).
- [x] DB proof: `doc`, ≥1 tag, ≥1 image, `Unassigned` sender, object publicly readable (200).
- [ ] `kudos_likes` = 1, not 0 — traced to the same `K-25` flake, disclosed above.
- [x] Report written with real exit codes throughout.

## Unresolved / for the orchestrator
1. `K-25`'s load-triggered flake (`kudos-live-board-authed.spec.ts`) should go to whoever owns F004's
   test maintenance — likely needs a slightly longer assertion timeout or a retry, since the root
   cause is UI-round-trip timing under contention, not application logic.
2. The `useActionState`-outside-transition warning in `compose-form.tsx` (phase 11) — cosmetic today,
   worth a look before this ships to a stricter React version.
3. `images.dangerouslyAllowLocalIP` (next.config.ts, phase 03) — local-dev-only wrinkle for freshly
   uploaded attachment thumbnails; doesn't affect any current assertion or production behavior.
