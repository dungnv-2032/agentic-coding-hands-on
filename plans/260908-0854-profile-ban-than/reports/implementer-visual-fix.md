# Visual fix — keyvisual datum + direction copy — implementer report

**Date:** 2026-09-08 · **Agent:** `implementer` · **Scope:** `app/profile/page.tsx` only
**Source of the task:** `reports/tester-phase-10-green.md` D1 + D5

## Headline

Both defects are addressed inside `app/profile/page.tsx` (187 lines). The GREEN gate survives,
twice, once from a pristine `db reset`:

```
$ npx playwright test --project=profile-auth-setup --project=profile-authed --project=anon
  108 passed (2.6m)      EXIT=0      # accumulated DB
  108 passed (2.7m)      EXIT=0      # after npx supabase db reset
$ npx playwright test --project=anon           81 passed (1.7m)   EXIT=0
$ npx playwright test --project=kudos-authed    62 passed (1.5m)   EXIT=0
```

`npm run typecheck` **EXIT=0** · `npm run lint` **EXIT=0** (0 errors, 29 warnings, all
pre-existing e2e unused-locals) · `npm run build` **EXIT=0**, 13 routes, all `ƒ (Dynamic)`.
No test file, fixture or `playwright.config.ts` was touched. No `app/profile/_components/*` file
was touched. The `select on public.kudos` revoke was re-read after the reset: `postgres`,
`service_role` only.

**One correction to the mandate, measured, not argued: D5's stated cause is wrong.** The `Đã gửi`
string in another Sunner's payload does **not** come from `page.tsx:131`. It comes from the shared
chrome's whole-`Dictionary` prop, and it is present on `/kudos` and `/awards-information` too, for
an anonymous visitor, on pages that never render the direction menu. Detail in § D5. The page-level
narrowing was still made — it is what the mandate asked for and it is correct defence-in-depth —
but it does not remove the string from the payload, and no change confined to `app/profile/page.tsx`
can.

---

## Defect 1 — where the 76px came from, and why the fix is not a negative margin

### The measurement, all three faces, four widths

`evidence/visual-fix-measurements-before.json` / `-after.json`, captured with a throwaway probe
(pointer parked at (2,2), focus cleared), authenticated session, dev server.

`HomeHeader` is `sticky top-0` **and in normal flow**, so `<main>` starts at its bottom edge and
`ProfileKeyvisual` — `absolute top-0` inside the hero's `relative isolate` section — starts there
too. The 76px is not padding or line-height: it is the header's **whole box**, and it is **not a
constant**:

| viewport | header height | measured cause |
|---|---|---|
| 1440 | **76px** | one row: `py-3` (24) + the 52px logo |
| 1024 | **124px** | the right cluster wraps below the left one (`flex-wrap`) |
| 768 | **124px** | same wrap |
| 375 | **244px** | three rows — logo, nav, then the bell/language/account cluster |

A hardcoded `-mt-[76px]` would therefore have been wrong at three of the four widths I measured,
by up to 168px. That is the reason the fix names no header height anywhere.

### The two facts that decide the shape of the fix

Both come from the frame, and the second is the one the mandate could not see from prose:

1. The banner is drawn from page `y0` (`mm:I1210:12622;2167:5140`, 1440×512, absolute top 0) with
   the translucent header floating over it.
2. The frame puts the hero content **184px below the banner's top** — avatar `y184`, banner `y0`.
   The hero component uses `pt-[104px]`, which is the frame's *header-band-to-hero* gap (`y80 → y184`).
   That is the right number measured from the **wrong datum**: the component's padding-box top edge
   *is* the banner's top edge, because the component anchors the banner to itself.

Fact 2 is why **a pure pull-up cannot fix this defect**, and this is worth stating plainly because
both the tester's report and the mandate assume it can: the banner and the hero content are glued to
the same box, so moving the hero as a whole (negative margin, overlay, spacer — any of them) changes
*nothing* about where the circles sit relative to the artwork. Measured, pre-fix: circle top 63px
**above** the banner's bottom edge at 1440, and at 375 too (19px there, because the header's extra
height had already pushed the wash's opaque end past them). The frame has them 16px **below** it.
The missing 80px has to be inserted **between the banner's top edge and the hero's content**, and
inside that box the only lever is the section's own top padding.

### What I changed

Two things, both in `app/profile/page.tsx`:

1. **The header leaves the flow from `lg` up** — a wrapper with
   `contents lg:fixed lg:inset-x-0 lg:top-0 lg:z-20 lg:block`. `fixed` is what `sticky top-0`
   already looks like at any scroll offset > 0, so there is no behaviour change (verified: after
   scrolling to `scrollY=1500` the header's `getBoundingClientRect().top` is **0** at 1440, 1024,
   768 and 375, and `elementFromPoint` mid-viewport still resolves to page content, so nothing is
   swallowing clicks). `contents` below `lg` (not a static wrapper) keeps `HomeHeader` a direct
   child of the page column, so its own `sticky` keeps a full-page containing block to travel in —
   a wrapper exactly as tall as the header would have pinned it and it would have scrolled away.
   **Only from `lg`** because the hero content lands at a fixed 184px: at ≥1024 the header is at
   most 124px so it can never reach the content, while at 375 it is 244px tall and must keep its
   own space.
2. **`[&>section]:pt-[184px]` on the hero's wrapper** — the frame's banner-top-to-content distance,
   replacing the 104px measured from the header band. This is the same correct value in **both**
   regimes, which is what makes it responsive-safe: the hero's padding-box top edge is the banner's
   top edge whether that edge is page `y0` (≥lg) or the header's bottom (<lg).

### Result — measured, all three faces, four widths

| face | width | banner | `<h1>` | badge circles | verdict |
|---|---|---|---|---|---|
| `?id=1` | 1440 | `0…512` | `416` | `529…593` | 17px **below** the banner |
| `?id=1` | 1024 | `0…512` | `416` | `529…593` | 17px below |
| `?id=1` | 768 | `124…636` | `540` | `653…717` | 17px below |
| `?id=1` | 375 | `244…756` | `660` | `817…881` | 61px below |
| self (sparse) | 1440 | `0…512` | `416` | `501…565` | overlaps the banner's last 11px |
| `?id=2` | 1440 | `0…512` | `416` | `529…593` | 17px below |

Frame reference: banner `0…512`, avatar `184`, `<h1>` `416`, circles `528…592`, caption `624`.
At ≥lg the rendered page now reproduces those absolute y values (±1px of sub-pixel in the name row).

**Proof the circles are on the page background, not artwork** — pixel sample at x=430 (immediately
left of the circle row, same rows), deviation from `#00101A` summed over RGB:

| row | before | after |
|---|---|---|
| y490 | `rgb(110,109,54)` dev **231** | `rgb(2,17,27)` dev **4** |
| y510 | `rgb(88,91,49)` dev **186** | `rgb(0,16,26)` dev **0** |
| y530 | `rgb(37,44,21)` dev **70** | `rgb(0,16,26)` dev **0** |
| y550 | dev 8 | dev **0** |

The sparse face's 11px overlap is invisible for a measured reason, not an assumed one: the wash is
solid `#00101A` for the banner box's bottom 8.6% (44px), and the sample at y500 reads
`rgb(1,16,27)`, dev **2**.

The `<h1>` improved but is **not** frame-clean, and I am not claiming it is: at its rows the backdrop
went from dev 313/291/271 (y420/430/440) to **220/194/171**, against the frame export's 63/45/29.
With the geometry now identical, the residual is the artwork itself: the live banner renders roughly
twice as bright as the export in the ribbon bands at *every* y (see the side-by-side column in
§ Observations). That is `profile-keyvisual.tsx`'s `object-cover` crop versus Figma's
`background-size: 101.245% 393.038%` fill transform, it is pre-existing, and it is untouched by this
fix — the banner box is the same 1440×512 with the same crop, only its page y moved.

**Side effect budget:** the KUDOS section moves from y788 to y792 at 1440 (+4px), the footer by the
same. Nothing else on the page moves. Hero content never slides under the header: clearance from
header bottom to avatar top is **108px** at 1440, **60px** at 1024, **184px** at 768 and 375.

### Evidence

- `evidence/visual-fix-measurements-before.json`, `-after.json` — 3 faces × 4 widths, box geometry
  and computed styles.
- `evidence/profile-visual-{id1-populated,self-sparse,id2-other}-{before,after}.png` — 1440,
  full-page, same capture discipline as phase 10's, saved beside them.
- `evidence/profile-hero-before-after-design.png` — before | after | `design/profile.png`, top 760px.
- `evidence/visual-fix-payload-and-scroll.json` — scroll/pinning behaviour at all four widths.

### Would this transfer to `/kudos` (F004)? Not as-is — and I did not touch it.

The header half transfers verbatim; `kudos-hero.tsx` anchors its own keyvisual the same way, so
`/kudos` would get its banner back to page `y0` from the same wrapper. The second half does **not**
transfer: 184px is SCR006's banner-top-to-content distance, and `/kudos`'s frame (`2940:13431`) has
its own. Anyone fixing F004 must re-measure that number from its own frame — copying 184px would
just move the compromise. Flagging only; F004 is out of scope and unmodified.

---

## Defect 2 (D5) — narrowed as asked, but the leak path was misattributed

**What I changed:** on another Sunner's profile the page now hands
`{ receivedLabel, sentLabel: "" }` instead of the whole `profile.direction` block. `sentLabel` is a
required `string` in phase 08's frozen `KudosDirectionCopy`, so the label is emptied rather than the
contract widened; the option that would render it does not exist on that face
(`isSelf && counts.sent !== null` in `profile-direction-menu.tsx`). The self view passes the same
object it always did.

**Verified, at payload level** (`evidence/visual-fix-payload-and-scroll.json`):

| face | rendered options | trigger | `counts` in payload | `Đã gửi` in rendered text |
|---|---|---|---|---|
| self (bare route) | `Đã nhận (0)`, `Đã gửi (0)` — **2, unchanged** | `Đã nhận (0)` | `{received:0,sent:0}` | n/a (self) |
| `?id=1` | `Đã nhận (26)` — 1 | `Đã nhận (26)` | `{received:26,sent:null}` | absent |
| `?id=2` | `Đã nhận (75)` — 1 | `Đã nhận (75)` | `{received:75,sent:null}` | absent |

SEC_001 still holds at the data layer: `"sent":null`, and sunner 2's real sent total (12) appears
nowhere as a `sent` value. The section's own serialized prop now reads `"sentLabel":""`.

**But the string is still in the payload, and page.tsx is not why.** Grepping the served HTML of
`/profile?id=2` after the change leaves exactly one hit, at a *different* offset from the one my
change fixed:

```
…"nhận đến {name}"},"direction":{"receivedLabel":"Đã nhận ({count})","sentLabel":"Đã gửi ({count})"},"feed":{"emptyRec…
```

That is the whole `dictionary.profile` block, and the decisive probe is that it appears where no
profile component renders at all:

| page | session | `Đã gửi` hits in HTML |
|---|---|---|
| `/kudos` | authenticated | **1** |
| `/kudos` | **anonymous** | **1** |
| `/awards-information` | anonymous | **1** |

Five shared client components take the whole `Dictionary` — `home-header.tsx`, `home-nav.tsx`,
`account-menu.tsx`, `notification-bell.tsx`, `site-footer.tsx` — and `page.tsx` must pass
`dictionary` because that is their prop contract. So this is F004-era shared chrome, every page, every
visitor; not `page.tsx:131`.

This also explains the arithmetic that made D5 look like a one-line page fix: before my change,
`copy.direction` was *the same object reference* as the dictionary's, so React's flight serializer
emitted a pointer to it, not a second copy. That is why the tester counted **one** hit and
attributed it to the page. The one they measured was the header's.

Recommend routing "the copy dictionary should not cross wholesale into shared chrome" to whoever owns
F004's chrome, as its own bounded task. Sizing it: the fix is per-component copy slices, five call
sites plus every page that renders them. I did not start it — outside this task's ownership, and it
would touch files three phases own.

---

## Concerns, honestly

1. **`[&>section]:pt-[184px]` overrides a frozen component's measured value from outside.** It
   satisfies the letter of the mandate (the change is in `page.tsx`) but it is action at a distance:
   a future reader of `profile-hero.tsx` sees `pt-[104px]` and is misled. **The durable home is that
   component**, and the change there is one token — `pt-[104px]` → `pt-[184px]`, with the datum named
   in the comment ("from the banner's top edge, which is this box's top edge") — after which the
   wrapper here should be deleted. I did not make it because phases 07/08 are frozen and the mandate
   said to report rather than edit. This is the single thing I would most like ratified.
2. **The header is out of flow only at `lg` and up**, so below `lg` the banner still starts at the
   header's bottom. The frame exists at 1440 only and the contrast defect is fixed at every width, so
   this is a deliberate stop, not an oversight: below `lg` the header is 124–244px tall and must keep
   its space unless the hero's padding becomes width-dependent, which would be a new invented
   responsive rule with no design authority behind it.
3. **`position: fixed` versus `sticky` at ≥lg.** Visually identical (a top-anchored sticky header is
   pinned at every scroll offset), verified at four widths after scrolling. One theoretical
   difference: in a browser with classic (non-overlay) scrollbars the fixed box is sized by the
   layout viewport. Measured header width equals the viewport width at all four widths in Chromium
   here (1440/1024/768/375), and the suite is Chromium-only.

## Observations, none of them mine to fix

- **The banner artwork renders ~2× brighter than the frame export.** With the banner boxes now
  aligned at `0…512` in both, x=430 reads (design → live): y260 274→421, y320 173→360, y340 152→321,
  y420 63→220, y440 29→171, and from y480 down both are flat (≤6). Structure and y-positions line up;
  amplitude does not. Suspect `object-cover` versus the frame's fill transform in
  `profile-keyvisual.tsx`. Pre-existing, unchanged by this fix, and it is what keeps the `<h1>`'s
  backdrop off the frame even with the geometry exact.
- **Horizontal overflow at 375px**: `document.scrollWidth` is **469** on every profile face, before
  and after. The badge row is 6×64 + 5×32 = 544px wide and does not wrap. Pre-existing, not mine
  (`profile-badge-row.tsx`), and identical in the before capture.
- **`next/image` dev warning** on `kv-background.png` ("width or height modified, but not the
  other") fires on every profile and kudos render, before and after. Phase 07's file.

## Database

Found at the phase 10 handback (`kudos=58 anon=1 sunners=9 kudos_likes=0`), so **no reset was needed
to start**. After the three suite runs it read `kudos=59 sunners=10`; traced, not assumed — kudos 62,
`is_anonymous=false`, campaign `Người truyền động lực cho tôi`, sender sunner 13
(`e2e-1788857878693-519885-ps9ehf`), i.e. `viet-kudo.spec.ts`'s ID-46/47 accumulation that phase 02
of F005 ratifies; ids 59–61 are absent, which is the positive proof SEC_002 composed and cleaned up.
**`npx supabase db reset` was then run once** (EXIT=0) and the target command re-run GREEN from that
pristine state. Handed back at `kudos=58 anon=1 sunners=9 kudos_likes=0`, `auth_users=2` (the two
setup projects of the final run), revoke re-verified after the reset.

## Unresolved questions

1. **Does concern 1 get ratified** — should `pt-[184px]` move into `profile-hero.tsx` and the wrapper
   here be deleted? Until it does, one measured value for this screen lives in two files.
2. **Who takes the shared-chrome dictionary narrowing?** It is a real defence-in-depth gap on every
   page for every visitor, and it is the actual owner of D5's symptom.
3. **Should the keyvisual's crop be re-derived from the frame's fill transform** (§ Observations)?
   That, not geometry, is what stands between the `<h1>` and the export now.
