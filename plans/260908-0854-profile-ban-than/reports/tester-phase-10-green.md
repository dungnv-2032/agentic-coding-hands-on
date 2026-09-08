# Phase 10 — GREEN gate + visual validation — tester report

**Date:** 2026-09-08 · **Agent:** `tester` · **Policy:** `e2e-red-first`
**MoMorph:** `Profile bản thân` — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/3FoIx6ALVb

## Headline

`e2e-red-first` closes. Phase 02's RED command, rerun verbatim, is **GREEN**:

```
$ npx playwright test --project=profile-auth-setup --project=profile-authed --project=anon
  108 passed (2.5m)      EXIT=0
```

All five inherited failures are settled, and three tests that were **passing vacuously** now
actually exercise their subject. No assertion was weakened; no source file was touched.

## Files edited — all three are mine, and they are the only files that moved

| File | Change |
|---|---|
| `e2e/profile.spec.ts` | 671 → 921 lines. FUN_002 and GUI_001 rewritten; FUN_010/FUN_012/SEC_002 locators scoped; FUN_013, FUN_015, SEC_002, SEC_004 rewritten from vacuous to load-bearing; one shared `directionOption` helper; `cleanupAnonymousKudo` replaced by a precise `cleanupComposedKudo` |
| `e2e/profile-auth.setup.ts` | 69 → 84 lines. Writes a sidecar `e2e/.auth/profile-user-meta.json` with the signed-up address and its local-part, so the sparse hero's name can be asserted **exactly** rather than by pattern |
| `e2e/fixtures/profile-constants.ts` | 45 → 89 lines. Five new measured constants + the `DIRECTION_LABELS` strict-mode trap written down where the next author will hit it |

`git status`: nothing under `app/`, `lib/`, `supabase/` moved this phase, and
`playwright.config.ts` is byte-identical to what phase 09 left (it was already `M` at session
start). **Test count unchanged at 26** — no test added, renumbered, skipped or removed.

Gates: `npm run typecheck` **exit 0** · `npm run lint` **exit 0** (0 errors, 29 warnings, all
pre-existing e2e unused-locals — one *fewer* than before) · `npm run build` **exit 0**, 13 routes,
all `ƒ (Dynamic)`.

## Suite runs — real commands, real summary lines, real exit codes

| Command | Result |
|---|---|
| `npx playwright test --project=profile-auth-setup --project=profile-authed` | `27 passed (2.1m)` **EXIT=0** |
| **`npx playwright test --project=profile-auth-setup --project=profile-authed --project=anon`** | **`108 passed (2.5m)` EXIT=0** |
| `npx playwright test --project=anon` | `81 passed (2.2m)` **EXIT=0** |
| `npx playwright test --project=kudos-authed` | `62 passed (2.4m)` **EXIT=0** |
| same target command, 2nd consecutive run | `108 passed (2.6m)` **EXIT=0** — identical |
| same target command, 3rd run, from a pristine `db reset` | `108 passed (2.4m)` **EXIT=0** |
| `npm run build` | **EXIT=0** |

**No F004/F005 regression.** `81` and `62` are exactly phases 04/05/09's totals.
`callback-security.spec.ts:91` did not flake on any run.

`--list` confirms each `*-auth.setup.ts` lives in exactly one project (`auth.setup.ts` → `setup`,
`profile-auth.setup.ts` → `profile-auth-setup`), and 81 + 26 + 1 = 108 accounts for every test.

**Database.** Found at exactly the state phase 09 handed over (`kudos=58 anon=1 sunners=9 linked=0
kudos_likes=0 auth_users=0`), so **no reset was needed to start**. `npx supabase db reset` was then
run once (exit 0) before the security probes and the third GREEN run. After that run the DB reads
`kudos=58 anon=1 sunners=9 linked=0 kudos_likes=0` — the profile suite leaves **zero** rows behind,
including the one it composes. Only `auth.users` grows (2 per run, one per setup project), which is
how every suite in this repo behaves.

The +1 `kudos` / +1 `sunners` observed after the *second* run was traced, not assumed: kudos 61,
`is_anonymous = false`, campaign `Người truyền động lực cho tôi`, sender the 07:57 e2e user — i.e.
`viet-kudo.spec.ts`'s ID-46/47, whose row accumulation is ratified by phase 02 of F005. Ids 59 and
60 are *missing* from the sequence, which is the positive proof that SEC_002's compose-and-delete
cycle ran and cleaned up on both runs.

## Phase 03's nine security probes — all pass

Full transcript: `evidence/phase-03-security-probes.log`.

| # | Probe | Result |
|---|---|---|
| 1 | `kudos_readable` in `pg_views` | `1` |
| 2 | anon `GET /rest/v1/kudos?select=id,sender_id` | **HTTP 401**, `42501 permission denied for table kudos` — an error, not a 200 |
| 3 | anon reads kudos 58 (seeded anonymous) through the view | all five `sender_*` columns `null`; `is_anonymous: true`; `receiver_id: 1` present |
| 4 | anon reads kudos 1 (non-anonymous) | `sender_full_name: "Huỳnh Dương Xuân Nhật"`, receiver 2 = `"Huỳnh Dương Xuân"` — **named, and different from the receiver**; case C of the probe report (receiver in the sender slot) did not happen |
| 5 | the same anonymous row read as its own sender | `sender_id: 2`, `sender_full_name: "Huỳnh Dương Xuân"` — the per-row CASE discloses to the sender only |
| 6 | `select id from public.kudos where sender_id = 1` as `anon` | `permission denied for table kudos` — no filter oracle |
| 7 | `insert into public.kudos_likes` as `authenticated` | succeeds — heart toggle alive after the revoke |
| 8 | `select public.create_kudos(…)` as `authenticated` | returned id `59` (rolled back) — F005 write path alive |
| 9 | seed carries an anonymous row | `grep -c is_anonymous supabase/seed.sql` = 2; `count(*) filter (where is_anonymous)` = 1 |

**The revoke is intact, re-read live:** `select on public.kudos` → `postgres`, `service_role` only.
`anon`/`authenticated` hold `select on public.kudos_readable` plus the single `select (id)` column
grant `INSERT … RETURNING` needs. Nothing was restored.

## The five inherited failures — what each turned out to be, and how it was settled

### 1–3. `FUN_010`, `FUN_012`, `SEC_002` — ambiguous `getByText("Đã gửi")`

Confirmed exactly as phase 09 diagnosed. Fixed with one shared helper, stricter than what was there:

```ts
const directionOption = (page: Page, label: string): Locator =>
  page.getByTestId("profile-direction-option").filter({ hasText: label });
```

The label must now be on an **option**, not merely somewhere on the page. Each site also pins
`toHaveCount(1)` before clicking.

**The whole file was swept, as instructed.** Every remaining bare `getByText` on a
`DIRECTION_LABELS` constant is gone; `SEC_001`'s surviving `expect(body).not.toContainText(sent)` is
a *negative* body assertion and cannot raise strict mode, so it stayed. The trap is now recorded in
`profile-constants.ts` beside the constants themselves, including the part the earlier repair
missed: **`getByText` defaults to `exact: false`, which is case-INsensitive**, so `"Đã gửi"` matches
the statistics label `Số Kudos bạn đã gửi:` on a lower-case `đã gửi`. That is why the repair
report's harness — which contained only the dropdown — declared these three "verified unaffected"
and was wrong. Verified this time against the **real page**, which is what the mandate asked.

### 4–5. `FUN_002`, `GUI_001` — the false premise, settled by clarification A4

Both assumed the `profile-authed` session **is** seeded sunner 1. It never is, and A4 makes the
fresh-signup session the *normal* authenticated case rather than a fixture defect. Neither test was
linked to `sunners.id = 1`: linking mutates shared fixture state, and it would have retired the
sparse self view that A4 calls reality and `GUI_009` covers.

**`FUN_002`** now asserts its real subject — that an explicit `?id=` is resolved *against the
viewer's own identity*, and that the resolution never redirects nor rewrites the URL. Both faces run
in one session, so no degenerate resolver satisfies both:

```ts
await page.goto(`${ROUTE}?id=${FRAME_VIEWER_ID}`);
expect(new URL(page.url()).pathname).toBe(ROUTE);
expect(new URL(page.url()).searchParams.getAll("id")).toEqual(["1"]);   // verbatim, one occurrence
await expect(heroElement(page)).toContainText(FRAME_VIEWER_NAME);
await expect(writeBar(page)).toBeVisible();
await expect(statCard(page)).toHaveCount(0);      // a resolver that treats a null viewer id as
                                                  // "matches anything" fails here
await page.goto(ROUTE);
expect(new URL(page.url()).search).toBe("");
await expect(statCard(page)).toBeVisible();
await expect(writeBar(page)).toHaveCount(0);      // a resolver that never resolves self fails here
```

Not vacuous, and stricter than the old `expect(page.url()).toMatch(/\?id=1/)`: the old form accepted
any URL merely *containing* that substring and asserted nothing about which face rendered.

**`GUI_001`** now asserts **both** heroes instead of the frame viewer's name on somebody else's
page. Populated (`?id=1`): `<h1>` exactly `Huỳnh Dương Xuân Nhật`, department `CEVC10`, an avatar
image, and `profile-tier-badge` exactly `Super Hero`. Sparse (bare route): `<h1>` exactly the
session's email local-part read from the setup's sidecar, an avatar image, `profile-tier-badge`
**count 0** (GUI_009's rule — hidden at zero received, not "New Hero"), and no seeded department
anywhere in the hero (a null department hides the text and the 4×4 dot together). That is four
measured facts per face against one `toContainText` before.

**One coverage gap is reported, not faked.** `resolve-profile-id.ts:74`'s canonicalization branch
(`parsed === viewerSunnerId` → `{kind:"self"}`) is **unreachable** for a session with no roster row,
so nothing durable exercises it. Reaching it needs the e2e session to own a `sunners` row, which
changes what every other case in this file exercises — phase 09's unresolved question 1, still a
test-design call above this phase. The branch is written into the test's own comment so it is not
mistaken for covered.

## The three tests that were passing without asserting anything

Fixing the five failures would have left these three green and hollow. They are the reason a truthful
GREEN needed more than locator repairs.

### `FUN_015` — the entire body was being skipped

It looked for the hashtag as `card.locator("a")`, but `kudos-hashtag-row.tsx:32` renders a
`<button>` (test-contract.md § Kudos card mandates buttons). The locator resolved to nothing,
`isVisible()` was false, and both URL assertions were skipped. **It would have kept passing if the
link were deleted outright.**

Rewritten to assert the destination the way phase 09 proved it — not by the URL, which passes on a
half-truth, but by the board's own **filter state** and the contents of what it left on screen:

```ts
const hashtag = feed(page).getByTestId("kudos-hashtag").first();
await expect(hashtag).toBeVisible();                      // unconditional
const rendered = (await hashtag.innerText()).trim();
expect(rendered).toMatch(/^#\S/);
const tagName = rendered.slice(1);
await hashtag.click();
await page.waitForURL((url) => url.pathname === "/kudos");
expect(new URL(page.url()).searchParams.getAll("hashtag")).toEqual([tagName]);   // BARE name, once
await page.getByTestId("filter-hashtag").click();
await expect(menu.getByRole("option", { selected: true })).toHaveCount(1);
await expect(menu.getByRole("option", { selected: true })).toHaveText(tagName);
// ...then every card ALL KUDOS left on screen carries that tag
```

Phase 09's correction was honoured: the tag **name carries no `#`** (`hashtags.name` is
`Toàn diện`; the row renders the `#`), so `?hashtag=` gets the bare name and nothing was "fixed"
into `?hashtag=#tag`. The board sweep is scoped to `all-kudos-section` because the highlight
carousel renders the same filtered set again and its flanks are `aria-hidden`.

### `SEC_002` — from unfailable to the durable owner of `revealOwnAnonymous`

The old form wrapped every compose step in `if (await x.isVisible())` against locators that matched
nothing (`input[placeholder*="tìm"]`, a `<input type=checkbox>` filtered by `hasText`), then asserted
only `expect(feedArea).toBeVisible()` — true whether or not any Kudo was composed.

It now composes **one real anonymous Kudo through the real form** and asserts *both* directions of
the guarantee against that one row:

- **the author's own Sent list names the author** — `kudos-sender` present with the author's own
  name, `Ẩn danh` absent, receiver named, and the heart **disabled** (`canLike:false` — a revealed
  row is still not a likeable row);
- **the same row on the public board, read with no session at all** (`browser.newContext({
  storageState: undefined })`), is the redacted stub — `kudos-sender` **count 0**, `Ẩn danh` present,
  the author's name absent.

That second half is what makes the first a security statement rather than a rendering one: an
over-broad reveal passes the Sent-list assertions and fails there. **Neither half can pass
vacuously** — they are positive count assertions on the *same* row, and they demand opposite
renderings, so the test produced a contradiction that only a working per-caller mask can satisfy.
This is phase 05's M3b–M3g arriving as a durable test, which is what phase 05 asked for.

Recipient is sunner 9 (`Nguyễn Hoàng Linh`), deliberately not the frame viewer or receiver: the
composed row moves its recipient's received count, and no other case reads anything about sunner 9.
The name is also unambiguous in the picker's substring search, unlike `Huỳnh Dương Xuân`, which is a
prefix of sunner 1's name. Cleanup deletes by the run-unique campaign token and by the author's own
address — never "every anonymous kudos" or "every `e2e-%` sunner", which would reach into rows
another Playwright project owns while it is still running.

### `FUN_013` and `SEC_004` — smaller versions of the same disease

`FUN_013`'s end-of-feed check sat inside `if (await endMessage.isVisible())`. It now asserts the
sentinel is mounted and the end message absent on page 1, drives the keyset feed with a bounded
loop, then asserts **unconditionally**: the end message visible with its exact copy, the card count
strictly greater than page 1's, and the sentinel unmounted (which is what actually stops the
observer).

`SEC_004` checked one face for a uuid. It now checks **both** faces for a uuid **and** for an
`@`-bearing address, with per-URL failure messages. Both pass — the sparse hero's name is the email
**local-part**, which is not an address.

## Visual validation

I own browser evidence for both policies. Captured at 1440px, authenticated, with the pointer moved
to (2,2) and focus cleared before every shot, so no hover or focus state contaminates the reference.
Throwaway capture probe, run and deleted; nothing durable was added to `e2e/`.

Evidence: `evidence/profile-visual-id1-populated.png` (1440×7345),
`evidence/profile-visual-self-sparse.png` (1440×1687),
`evidence/profile-visual-id2-other.png` (1440×7865),
`evidence/phase-10-visual-measurements.json`, `evidence/phase-10-visual-measurements-2.json`,
`evidence/phase-10-sec001-payload.json`.

**No deterministic pixel metric is available** — the design authority is a 1440×4660 Figma export of
a *different data state* (a populated self profile with 25s), and no live face reproduces it. So the
verdict below is **token-by-token computed-style comparison plus qualitative screenshot judgment**,
not a zero-difference claim. Nothing here is called "exact" beyond the individual measured values,
each of which is quoted.

### Measured values — every one from step 7 of the phase file

| Measured value (`mm:` node) | Frame | Rendered | Verdict |
|---|---|---|---|
| Page background (`362:5037`) | `#00101A` | `rgb(0, 16, 26)`, width 1440, Montserrat | match |
| Keyvisual (`I1210:12622;2167:5140`) | 1440×512 | 1440×512, `object-fit: cover` | match (origin — see D1) |
| Avatar (`362:5053`) | 200×200, 4px `#FFF` ring, x620–820 | 200×200, `border 4px rgb(255,255,255)`, x620, `cover` | match |
| Name (`362:5055`) | 36/44/700 `#FFEA9E`, centred | `36px / 44px / 700 / rgb(255,234,158)` centre | match |
| Department (`362:5057`) | 22/28/700 white | `22px / 28px / 700 / rgb(255,255,255)` | match |
| Separator dot (`362:5060`) | 4×4 `#999` @ 40% | 4×4, `rgb(153,153,153)`, `opacity 0.4` | match |
| Tier pill (`3053:6061`) | h19, `border-radius 48px`, `#FFEA9E` border, 12.821px/700 white, `0 0 1.3px #FFF` glow | h19, `48px`, `rgb(255,234,158)`, `12.821px / 17px / 700`, `rgb(255,255,255) 0 0 1.3px` | match (border width — see D3) |
| Badge circles (`362:5066`–`5071`) | six 64×64, 2px white, `#323231`, slots x440–520 … x920–1000 | six 64×64, `border 2px rgb(255,255,255)`, `rgb(50,50,49)`, circles x448 and x928 → slot boxes x440 and x920 | match, exact to the pixel |
| Badge slot gap | 16px between 80px slots | 32px between 64px circles = 8 + 16 + 8 | match (same geometry, different datum) |
| Badge caption (`3053:10052`) | 22/28/700 white centred | `22px / 28px / 700 / rgb(255,255,255)` centre, y622 vs circles y525 | match, **below** the circles |
| Stats card (`362:5074`) | 680 wide, `p-40`, 1px `#998C5F`, `#00070C`, `rounded-[17px]` | 680 at x380, `padding 40px`, `1px rgb(153,140,95)`, `rgb(0,7,12)`, `17px` | match |
| Divider (`362:5079`) | 600×1 `#2E3940`, between rows 3 and 4 | 598×1 `rgb(46,57,64)`, exactly one, between rows 3 and 4 | match (598 — see D4) |
| Stat label / value | 22/28 white · 32/40 `#FFEA9E` | `22px/28px/700` white · `32px/40px/700 rgb(255,234,158)` | match |
| `Mở Secret Box` (`362:5082`) | 600×60, `rounded 8px`, `#FFEA9E` on `#00101A`, 22/700 label + 24×24 glyph | 598×60, `8px`, `rgb(255,234,158)`, `rgb(0,16,26)`, label `22px/28px/700`, glyph 24×24, **disabled** | match |
| `KUDOS` (`362:5088`) | 57/64/700 `#FFEA9E`, tracking −0.25px | `57px / 64px / 700 / rgb(255,234,158) / -0.25px`, x380 | match |
| Direction trigger (`362:5089`) | 1px `#998C5F`, `rounded 4px`, `rgba(255,234,158,0.10)`, padding 16/24, 16/700 white, gap 8 | all seven identical | match |
| Feed (`362:5091`) | 680px, single column, 24px gap, items-start | 680 at x380, `column`, `row-gap 24px`, `flex-start`, all 3 cards at x380 | match |
| Feed card | `#FFF8E1`, `rounded 24px`, padding 40/40/16 | `rgb(255,248,225)`, `24px`, `40px / 40px / 16px`, w680 | match |
| Region rhythm | 64px hero→B and B→C | `pt-16` + section `py-16` = 64px both | match |
| `?id=2` has no `Đã gửi` | required absent | absent from rendered text; dropdown offers exactly 1 option | match (payload — see D5) |

The two pre-adjudicated divergences are confirmed present and are **not** reported as defects: the
badge caption sits **below** the circle row (the frame and `design/profile.png` agree; the study and
`docs/screens/SCR006_ProfileBanThan/spec.md` are the wrong ones), and the keyvisual starts lower
than the frame's `y0`.

### Discrepancies, reported honestly

**D1 (material, belongs to phase 09) — the keyvisual origin has a visible consequence nobody costed.**
The offset is **76px**, not the ~64px the phase file estimated (`HomeHeader` measures 76px tall and
is in flow). Everything *inside* the hero is exact — `pt-[104px]` reproduces the frame's
header-band-to-hero gap verbatim. But shifting the whole block down by 76px moves the badge circle
row from y528–592 to **y525–589**, while the banner now ends at **y588** instead of y512. In the
frame the six locked circles sit on the page background; live they sit **on top of the bright
keyvisual artwork**, and the gold `<h1>` (y412–456) lands on the brightest ribbons instead of the
darker band. Both are legible but visibly off the design, and the contrast on the `#323231` circles
is materially worse. The wash (`I1210:12622;1210:12612`) is implemented correctly and is not the
cause — over the frame's own 957px rect it is already fully transparent inside the banner box.
**The fix belongs in `app/profile/page.tsx` (phase 09); I did not patch it.** The cheapest correction
is a negative top offset on the hero equal to the header height, or pulling the banner up under the
header the way the frame draws it.

**D2 (data, not implementation) — feed cards render no attachments.** The frame's card shows five
thumbnails; the seeded rows carry none, so `KudosAttachments` renders nothing. Not a defect.

**D3 (rendering engine) — the tier pill's border computes as 1px, not the frame's 0.5px.**
`profile-hero.tsx:101` declares `border-[0.5px]` per the frame; Chromium floors a sub-pixel border to
one device pixel at DPR 1. The source matches the frame; the engine does not. No action.

**D4 (measurement model) — the stats divider and Secret Box button are 598px, not the frame's 600.**
The card is 680 with `p-10` and a 1px border under `box-sizing: border-box`, so content is
680 − 2 − 80 = 598. Figma's 600 does not subtract the border. 2px, no action.

**D5 (advisory, `app/profile/page.tsx`) — the `Đã gửi` label string reaches another Sunner's
payload; the number does not.** Rendered text on `/profile?id=2` contains no `Đã gửi` and the
dropdown offers exactly one option, so `SEC_001` and the phase file's step 8 both hold. But the
string appears **once** in the HTML, inside the serialized client props:
`"direction":{"receivedLabel":"Đã nhận ({count})","sentLabel":"Đã gửi ({count})"}` — because
`page.tsx:131` passes the whole `profile.direction` copy block across the boundary. The protected
asset is intact, verified at payload level: `"counts":{"received":75,"sent":null}`, and sunner 2's
real sent total (12, measured) appears nowhere as a `sent` value. So this is static translation
copy, not information — but the clarifications' phrasing "the string cannot reach the DOM at all" is
not literally true of the copy, only of the option. One-line fix if wanted (pass only
`receivedLabel` when `!isSelf`); it is phase 09's file, so it is reported, not patched.

**D6 (observation) — `body` stays at `globals.css`'s white default.** `rgb(255,255,255)`; the page's
own root div paints `#00101A` over `min-h-svh` and grows with content, so no white band appears in
any of the three full-page captures. Same as the shipped `/kudos`. No action.

**D7 (dev-mode artifact) — the bottom-left "N" disc in every screenshot** is Next's dev indicator
from `npm run dev`, not the application. It is absent from a production build.

**Third-party surfaces inside the card** — the sender/receiver chips' small tier pill is F004's
shipped `sunner-chip.tsx`, not the hero's gold pill. `GUI_006`/AMEND-3 require the profile card to
*be* the board's component, so this is required reuse, not drift.

## Test-case disposition — all 30

**Passing and load-bearing (27 of the 30):** `ACC_001`, `ACC_002` (in `profile-anon.spec.ts`, `anon`
project) · `FUN_001`–`FUN_015` · `GUI_002`–`GUI_007`, `GUI_009` · `SEC_001`, `SEC_002`, `SEC_004`.

**Documented not-honoured (3), each cited to its amendment:**

- `GUI_001`'s "hoa-thị stars on one row" — **AMEND-1**: no star node exists anywhere in
  `mms_A.2_Name`; the row is name, department, a 4×4 dot and one tier pill. Not sourceable from the
  design authority, so not invented. The rest of `GUI_001` is asserted, on both faces.
- `GUI_002`'s "showing its real badge image desaturated" — **AMEND-2**: `list_media_nodes` returns
  30 media nodes on this frame and not one is a badge. Six flat `#323231` circles is the whole of
  what the frame contains, and all six render, in fixed order, none hidden.
- `FUN_008`'s `kudos_no_self` note — **ADV-2**: no such constraint exists on `public.kudos`
  (re-confirmed by probe 9's constraint read in clarifications). Advisory, not this phase's.

`SEC_003` has no `TC_` row of its own; its content (Sent-list self-scoping) is enforced server-side
in `fetch-profile-kudos-page.ts` and is exercised by `SEC_002`, which reads a Sent list that names
only its own caller.

## Returned to an owning phase — nothing else

1. **D1, keyvisual origin → phase 09 (`app/profile/page.tsx`).** The 76px offset is visible and it
   pushes the badge row onto the banner. Fact H is no longer merely open; it has a measured
   consequence.
2. **D5, the `Đã gửi` label in another Sunner's payload → phase 09 (`app/profile/page.tsx:131`).**
   Advisory. The number is null; only the static copy crosses.

Neither was patched here. No implementation defect was found behind any of the five failures — all
five were test-side, exactly as phase 09 said.

## Carried forward, unchanged by this phase

- **ADV-1** two paging strategies (board client-side slice vs profile keyset).
- **ADV-2** no `kudos_no_self` constraint.
- **ADV-3** no composite keyset index yet.
- **ADV-4** `fetchReceivedAggregate` reads every received row to sum hearts, so it truncates at
  PostgREST's `max_rows = 1000`. Not a defect at 58 rows.
- `anon`/`authenticated` still hold blanket `INSERT`/`UPDATE`/`DELETE` on `public.kudos` and
  `public.kudos_readable`, inert under RLS. The `SELECT` revoke — the thing this feature exists to
  deliver — was re-read live and is intact.
- **Pagination was not re-verified with a constructed tie.** Phase 05 measured that the seed
  generates no duplicate `sent_at`, so `FUN_013` cannot distinguish the correct keyset predicate
  from the degraded `sent_at.lt`-only form. Phase 05 proved the predicate load-bearing on 12
  constructed rows; that proof stands and was not re-run. Named as a gap rather than implied.

## Unresolved questions

1. **Does D1 get fixed?** It is a real visual divergence with a knock-on contrast cost, and `/kudos`
   ships the same compromise — so fixing it here makes the two screens disagree. That is a design
   call, not a test call.
2. **Canonicalization (`?id={me}` → self) has no durable test**, and cannot have one until somebody
   decides whether the `profile-authed` session should own a `sunners` row. Making it own one
   retires the sparse-self coverage A4 calls the common case; leaving it means one resolver branch
   is exercised by nothing. Phase 09's unresolved question 1, unchanged.
3. **`FUN_013` scrolls with a bounded `waitForTimeout` loop.** Deterministic here (3 pages, 12
   iterations of headroom) but time-based. A `waitForResponse` on the server action would be firmer;
   judged not worth the coupling to an action's internal request shape. Named, not hidden.
4. **`cleanupTestLikes(1)` in `afterEach` was left alone on purpose.** Widening it to "delete every
   `kudos_likes` row" would match the file header's own invariant, but Playwright can run
   `kudos-authed` concurrently with `profile-authed` across workers, and that suite's heart tests own
   like rows while they run. Narrow and slightly incomplete beats broad and destructive.
