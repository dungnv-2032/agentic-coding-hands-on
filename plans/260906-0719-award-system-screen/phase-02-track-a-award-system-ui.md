---
feature: F003 · test_policy: e2e-red-first · owner: momorph-ui-implementer
fileKey: 9ypp4enmFmdK3YAFJLIu6C · screenId: zFYDgyj_pD · depends_on: [01] · status: complete · effort: 3h
mode: screen
---

> **Delivered 2026-09-06 — but not the file list this phase predicted.** Two deviations, recorded rather
> than edited away:
> 1. **Six `_components/*`, not five.** `use-award-scroll-spy.ts` (196 ln) was split out of
>    `award-category-nav.tsx` (89 ln) when the W-2 fix pushed the nav past the 200-line cap. The file's own
>    header comment records the reason. ORCH-02 single-owner still held.
> 2. **`app/_components/kudos-promo.tsx` was edited**, which this phase listed as read-only. It self-caps at
>    `max-w-[1224px]`, so no wrapper could widen it and the body copy ran under the KUDOS logo here. The
>    orchestrator granted an explicit exception, now on the record as **ORCH-05**: one optional
>    `maxWidthClass` prop, union-typed `"max-w-[1224px]" | "max-w-[1440px]"` after reviewer S-11. Homepage
>    passes nothing and was measured byte-identical (card 252→1188, w936) — cleared on measurement, not
>    inference.
>
> Post-review fixes also landed in this phase's files: **W-1** (responsive header offset), **W-2**
> (interrupted-scroll staleness), **W-3** (`h2` + `aria-labelledby`), plus S-5, S-8, S-9, S-11, S-7 and the
> OBS-1 hero fallback. See `reports/reviewer-260906-0905-award-system.md`.

# Phase 02 — Track A: hero, category nav, detail cards, page assembly

## MoMorph refs:
- Hệ thống giải: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/zFYDgyj_pD
- Clarifications: plans/260906-0719-award-system-screen/clarifications.md
- testPolicy: e2e-red-first

## Context Links

- [plan.md](./plan.md) — integration contract + test hooks (frozen)
- [clarifications.md](./clarifications.md) — layout alternation, nav mechanics, shared-chrome reuse, ORCH-02/03
- [functional-spec.md](./spec/award-system/functional-spec.md) FR-101, FR-102, FR-201..208, FR-401..403, BR-002, BR-003, DEC-002
- [technical-spec.md](./spec/award-system/technical-spec.md) § 3.1 A1/A2, § 4.5 ALG-001
- [design/award-system.png](./design/award-system.png) (1440×6410)
- **Bound contract: `e2e/award-system.spec.ts`** — read every assertion before writing a line. Do not edit it.
- Shipped patterns to match: `app/page.tsx`, `app/_components/{home-hero,awards-grid,award-card,kudos-promo}.tsx`
- RED evidence: [award-system-red-run.log](./evidence/award-system-red-run.log) — exit 1, 11 failed / 2 passed

## Overview

**Priority:** P1 · **Status:** complete · **Owner:** `momorph-ui-implementer` (screen mode, ORCH-02) ·
**Depends on:** 01 · **Effort:** 3h

Build the whole visible screen at `/awards-information`, replacing the `ComingSoon` stub. One worker owns
the entire UI surface — the screen is one cohesive column of six structurally identical cards, so a section
fan-out would just put six workers on one card component.

## Key Insights

1. **Playwright's text engine returns only the innermost match.** An element is dropped when a child also
   matches, so `<div><Icon/><p>Top Talent</p></div>` resolves to the `<p>` alone. What is *not* safe is two
   **sibling** nodes carrying the same text inside one section. `Số lượng giải thưởng:` is asserted with no
   `.first()`, so it must appear exactly once per card. `Giá trị giải thưởng:` **is** asserted with
   `.first()` — which is the test telling us the design's Signature card really does repeat that label per
   prize row (confirmed in the frame). Render the label inside the prize row, not above the list.
2. **`toBeVisible()` ≠ in viewport.** ID-3 asserts all six sections visible at once; that only needs a
   non-empty box. `toBeInViewport()` (ID-9/13, deep link) is the one that really measures the viewport, at
   Desktop Chrome 1280×720.
3. **The sticky header is a hit-test hazard, not just a cosmetic one.** ID-10 calls `item.hover()` then
   asserts `el.matches(":hover")`. If the 72px sticky header covers a menu item, Playwright's actionability
   check fails or the hover lands on the header. The nav must stick *below* the header, and sections need
   `scroll-mt` so a hash jump doesn't park a card title underneath it. Next's own docs say Next skips
   sticky/fixed elements when picking a scroll target and recommends exactly this `scroll-margin-top` fix.
4. **ID-13 asserts zero console errors** — that makes a React hydration warning a test failure. The nav's
   first client render must be byte-identical to the server's: initial `activeSlug` is `AWARDS[0].slug`, and
   `location.hash` is read only inside `useEffect`.
5. **`aria-current` is present-or-absent, not `"true"`-or-`"false"`.** `activeNavItems` counts
   `[aria-current="true"]`; rendering `aria-current="false"` on the other five would still be one match, but
   `not.toHaveAttribute("aria-current","true")` is cleaner and the invariant is stronger with the attribute
   simply omitted.
6. **The Kudos block must remain the only `<section>` containing the exact text `Sun* Kudos`.** `KudosPromo`
   already is one. So no ancestor `<section>` may wrap it — `<main>` and plain `<div>`s only above it.
7. **`Sun* Annual Awards 2025` currently exists in the DOM only as `alt`/`aria-label` on the two logos.**
   `getByText` ignores attributes, so the hero eyebrow will be the sole text match (ID-4). Keep it that way:
   do not add a second visible copy of that string.

## Requirements

**Functional**
- FR-201 page order: header → hero → award body (nav + six cards) → Kudos → footer.
- FR-202 hero: keyvisual + `ROOT FURTHER` wordmark + centered eyebrow / hairline / gold `<h1>`.
- FR-203 sticky six-item left menu, each with a 24×24 icon; active = gold text + gold underline.
- FR-204/205/206 six cards: 336×336 rounded gold-bordered image, icon-prefixed title, description
  paragraph(s), quantity line, prize list (BR-004).
- FR-207 `KudosPromo` composed unchanged. FR-208 no `FloatingWidget`.
- FR-401 click → smooth scroll + `history.replaceState` of `#<slug>` (**replace**, never push).
- FR-402 scroll-spy keeps exactly one item active. FR-403 `prefers-reduced-motion` → instant jump.
- FR-102 / DEC-002 deep link `#<slug>` seeds the active item; unknown hash → first item, no jump, no error.
- FR-101 header selected state: already correct via `usePathname()` — **change nothing** (ORCH-03).

**Non-functional**
- Every file under 200 lines. kebab-case names. No `"use client"` above the nav leaf.
- No hardcoded display strings — everything from `dictionary.awardSystem`.
- No `dangerouslySetInnerHTML`. No new dependency. No new global CSS.
- Colours/sizes/offsets come from the frame or from tokens the shipped components already use
  (`#00101A`, `#FFEA9E`, `#2E3940`) — invent nothing.

## Architecture

```
app/awards-information/page.tsx            (Server Component, edit in place)
  await getPageContext() → { locale, dictionary, isAuthenticated, isAdmin }
  <div font-montserrat bg-[#00101A]>       ← mirrors app/page.tsx's root wrapper
    <HomeHeader …/>                        ← composed unchanged  → role=banner
    <main>
      <AwardSystemHero hero={…}/>          ← the page's only <h1>
      <div class="… lg:flex lg:gap-16">    ← plain div, NOT <section> (insight 6)
        <AwardCategoryNav items={…}/>      ← "use client"; nav[data-testid=award-nav]
        <div class="flex flex-col">
          AWARDS.map(AwardDetailCard)      ← <section id data-testid>, alternating sides
        </div>
      </div>
      <KudosPromo home={dictionary.home}/> ← composed unchanged → the Kudos <section>
    </main>
    <SiteFooter dictionary={…}/>           ← composed unchanged  → role=contentinfo
  </div>
```

**Data flow (server → client boundary):** `getPageContext()` reads the locale cookie and session once.
`AwardCategoryNav` receives a plain serializable array `{ slug, label }[]` plus the shared offset constant —
never the `Dictionary` object, never the Supabase user. `AwardDetailCard` is a Server Component: it zips
`AWARDS[i]` (identity) with `dictionary.awardSystem.cards[key]` (copy) and
`dictionary.awardSystem.units[AWARD_UNITS[key]]` (unit text). All six cards and the menu are server-rendered
HTML, so the screen reads correctly before hydration (spec § 3.2 edge case).

**ALG-001 — scroll-spy (`award-category-nav.tsx`)**

```
const HEADER_OFFSET = 112            // px; ONE constant. lg:top-28 · scroll-mt-28 · rootMargin below
state activeSlug = items[0].slug     // identical on server and client (insight 4)
clickLock = useRef(false)

useEffect(mount, once):
  slug = slugFromHash(location.hash)         // "" or no match → do nothing (DEC-002)
  if (slug) { setActive(slug); section(slug).scrollIntoView({ behavior: "auto", block: "start" }) }

useEffect(observe):
  new IntersectionObserver(cb, { rootMargin: `-${HEADER_OFFSET}px 0px -55% 0px`, threshold: 0 })
  cb(entries):
    if (clickLock.current) return                       // BR-002 — the click wins
    visible = entries.filter(e => e.isIntersecting)
    if (!visible.length) return                         // keep the current item (ALG-001)
    setActive(minBy(visible, e => Math.abs(e.boundingClientRect.top)).target.id)
  cleanup: observer.disconnect()

onClick(e, slug):
  e.preventDefault()                                    // FR-401 — no history push
  reduced = matchMedia("(prefers-reduced-motion: reduce)").matches      // BR-003
  setActive(slug); clickLock.current = true
  section(slug).scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" })
  history.replaceState(null, "", `#${slug}`)            // replace, never push
  setTimeout(() => { clickLock.current = false }, reduced ? 0 : SCROLL_SETTLE_MS /* 700 */)
```

Deliberately **not** used: `scrollend` (Chromium-only timing that would still need the fallback — YAGNI), a
scroll-position state machine (SM-###), and `next/link` for the six menu items. These are same-document
fragment anchors: a bare `<a href="#slug">` is what the test asserts, keeps the App Router out of a
non-navigation, and does not trip `@next/next/no-html-link-for-pages` (that rule targets page routes, not
fragments).

**Responsive:** at `lg` (1024px, the E2E width is 1280) the body is two columns — nav left, cards right,
`items-start` so the sticky nav can pin. Below `lg` it is one column: nav first as a horizontally scrollable
row, then the cards, each card image above its text (clarifications). Card side alternation is index-based:
even index → image left, odd index → image right, via `lg:flex-row` / `lg:flex-row-reverse`.

## Related Code Files

**Modify**
- `app/awards-information/page.tsx` — replace `<ComingSoon />` with the real screen; keep the existing
  `metadata` export *(delivered: 126 ln)*
- `app/_components/kudos-promo.tsx` — **unplanned; ORCH-05 exception granted mid-phase.** Optional
  `maxWidthClass?: "max-w-[1224px]" | "max-w-[1440px]"`, defaulting to the homepage's existing cap
  *(delivered: 79 ln, +18/−4)*

**Create** (all under `app/awards-information/_components/`, a private folder — not routable)
- `award-system-hero.tsx` — keyvisual, wordmark, eyebrow, hairline, `<h1>` *(86 ln)*
- `award-category-nav.tsx` — `"use client"`, the only client leaf on this screen *(89 ln)*
- `use-award-scroll-spy.ts` — **unplanned split.** ALG-001's geometry + timing, lifted out of the nav when
  the W-2 fix crossed the 200-line cap; nav keeps presentation *(196 ln)*
- `award-detail-card.tsx` — one `<section>`: image, `<h2>` title (W-3), paragraphs, quantity line *(154 ln)*
- `award-prize-list.tsx` — prize rows + `Hoặc` separator (BR-004) *(71 ln)*
- `award-system-icons.tsx` — `IconTarget`, `IconDiamond`, `IconLicense` (24×24, `aria-hidden`) *(103 ln)*

**Delete** — none. `app/_components/coming-soon.tsx` stays: `/kudos`, `/standards`, `/profile`, `/admin`
still render it.

**Read-only imports** (never edit): `app/_page-context.ts`, `app/_fonts.ts`, `app/_actions/auth.ts`,
`app/_components/{home-header,site-footer,kudos-promo}.tsx`, `lib/awards.ts`, `lib/award-system.ts`,
`lib/i18n/**`. **Hard-locked** (ORCH-03): `app/_components/{home-nav,site-footer}.tsx`, `proxy.ts`,
`e2e/**`, `playwright.config.ts`.

## Implementation Steps

1. **Icons first.** Try MoMorph MCP for the three 24×24 `MM_MEDIA_*` nodes (Target, Diamond, License). If
   they do not come back as usable vectors, hand-author inline SVG in `award-system-icons.tsx` matching the
   frame's stroke weight and the `#FFEA9E` gold. Every icon takes `aria-hidden` and carries **no `<title>`**
   — a `<title>` would add text content and break ID-5's `toHaveText` array and ID-7's img-role count.
2. **`award-system-hero.tsx`.** Copy `home-hero.tsx`'s keyvisual technique exactly: an `aria-hidden`
   absolutely-positioned aspect-ratio box with `<Image fill sizes="100vw" preload>` on
   `/images/home/keyvisual-hero-bg.png` plus the gradient overlay; `root-further-hero-wordmark.png` with
   explicit `width/height` and `alt={hero.wordmarkAlt}`. `preload` — **not** the deprecated `priority`
   (Next 16). Then the centered title block: `<p>{hero.eyebrow}</p>`, `<div aria-hidden class="h-px …">`,
   `<h1>{hero.title}</h1>`. The `<h1>` contains that string and nothing else — no nested span, no icon.
3. **`award-prize-list.tsx`.** `prizes.map((prize, i) => <Fragment>{i > 0 && <p>{prizeOr}</p>}<div>` label
   row (`IconLicense` + `<p>{prizeLabel}</p>`), `<p>{prize.amount}</p>`, `{prize.note && <p>{prize.note}</p>}`
   `</div></Fragment>)`. The `note` guard is what keeps ID-6's count-0 substring assertion true for Best
   Manager and MVP. Never render `note` as an empty `<p>`.
4. **`award-detail-card.tsx`.** `<section id={slug} data-testid={"award-detail-" + slug} class="scroll-mt-28 …">`
   containing: `<Image src={award.image} alt={card.title} width={336} height={336}>` (rounded, gold border —
   same treatment as `award-card.tsx`), the title row (`IconTarget` + `<p>{card.title}</p>`),
   `card.paragraphs.map(p => <p key={p}>{p}</p>)`, the quantity row (`IconDiamond` +
   `<p>{quantityLabel}</p>` + `<span>{card.quantity}</span>` + `<span>{unitText}</span>`), then
   `<AwardPrizeList/>`. **Each of `quantity` and `unit` sits in its own leaf element** — ID-6 matches each
   exactly and separately.
5. **`award-category-nav.tsx`.** `"use client"`. Props: `items: { slug: string; label: string }[]`.
   `<nav data-testid="award-nav" aria-label={…}>` wrapping exactly six `<a href={"#" + slug}
   data-testid={"award-nav-" + slug} aria-current={active ? "true" : undefined}>` with `IconTarget` +
   label text. Nothing else inside that `<nav>`. Implement ALG-001 above verbatim. Sticky:
   `lg:sticky lg:top-28 lg:self-start`.
6. **`page.tsx`.** Keep `export const metadata`. Make the default export `async`, call `getPageContext()`,
   compose per the tree above. Import `signOut` for `HomeHeader` exactly as `app/page.tsx` does. Iterate
   `AWARDS` for both the nav items and the cards so the two lists cannot drift.
7. `npm run typecheck` → `npm run lint` → `npm run build`. Then run the bound command once yourself:
   `npx playwright test e2e/award-system.spec.ts --project=anon`. **Phase 03 owns the verdict**, but a
   failing run here is yours to fix — never by touching the spec.

## Todo List

- [x] `award-system-icons.tsx` — 3 icons, `aria-hidden`, no `<title>`; hand-authored (no MCP export), tester measured all four card icons `rgb(255,255,255)` = frame
- [x] `award-system-hero.tsx` — keyvisual + wordmark + eyebrow + hairline + the page's only `<h1>`
- [x] `<h1>` text is exactly `Hệ thống giải thưởng SAA 2025`, no nested text nodes — ID-4 green
- [x] `award-prize-list.tsx` — label per row, `Hoặc` between rows, note rendered only when present
- [x] `award-detail-card.tsx` — `id` + `data-testid`; image `alt` === card title, pinned 336×336 by ID-7
- [x] ~~`scroll-mt-28`~~ → **superseded by W-1**: `scrollMarginTop: var(--award-header-offset, 112px)`, runtime-measured, `lg` pinned at 112px in the cascade
- [x] Quantity number and unit each in their own leaf element
- [x] Alternation: even index image-left, odd index image-right; single column below `lg`
- [x] `award-category-nav.tsx` — 6 `<a>`, correct `href`/`data-testid`, `aria-current` present-or-absent
- [x] Initial `activeSlug` = `AWARDS[0].slug` on server and client; hash read only in `useEffect` (R3 held; ~290 ms deep-link transient accepted as ORCH-04)
- [x] Click: `preventDefault` + `scrollIntoView` + `history.replaceState` + click lock — **but the lock as designed was defect W-2**; now released on wheel/touch/key and resolved from live geometry
- [x] `prefers-reduced-motion` → `behavior: "auto"`, lock timeout 0
- [x] `IntersectionObserver` disconnected on cleanup; unknown hash is a silent no-op
- [x] `page.tsx` composes `HomeHeader` / `SiteFooter` unchanged, **no `FloatingWidget`**; `KudosPromo` composed with the ORCH-05 prop
- [x] No `<section>` ancestor wraps `KudosPromo`
- [x] `preload` used, `priority` not used (Next 16 deprecation) — reviewer confirmed against the shipped Next 16 docs
- [x] All **seven** files under 200 lines (largest: `use-award-scroll-spy.ts` at 196) · typecheck, lint, build exit 0
- [x] Added post-review, not in the original list: `<h2>` + `aria-labelledby` per section (W-3), `navAriaLabel` (S-7), hero cap `max-w-[1152px]` (S-5), modifier-click guard (S-8), `key={index}` (S-9), `focus-visible` ring, OBS-1 hero fallback

## Success Criteria

- `npm run typecheck`, `npm run lint`, `npm run build` all exit 0. **Met** (`evidence/temper-results.json`).
- `npx playwright test e2e/award-system.spec.ts --project=anon` exits 0 — ~~**13 passed**~~ → **14 passed**
  after phase 03 added the ID-7 geometry lock and the W-3 structure lock. All 11 previously-RED tests green:
  ID-3, ID-4, ID-5, ID-6, ID-7, ID-8, ID-9/11, ID-10, ID-12, ID-13, deep-link.
- `/awards-information` no longer renders `ComingSoon`; `/kudos`, `/standards`, `/profile`, `/admin` still do.
- The shipped homepage suite stays green (`e2e/homepage.spec.ts` — six tests navigate into this route).
- Zero console errors and zero page errors on load (ID-13 measures this).
- Every visible string traces to `dictionary.awardSystem`; grepping the six new files for `Cá nhân`,
  `VNĐ`, or `Hệ thống` returns nothing.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Strict-mode violation: two sibling nodes with the same exact text inside one section | **H×H** — the single most likely failure | One leaf per asserted string. `Số lượng giải thưởng:` exactly once per card (no `.first()` in the test); `Giá trị giải thưởng:` may repeat only because Signature's design repeats it. Verify by running the suite before reporting. |
| Sticky header overlays a nav item → ID-10 `hover()` fails the actionability check | **M×H** | `lg:top-28` (112px) clears the 72px header; `scroll-mt-28` on every section. One `HEADER_OFFSET` constant feeds nav offset, scroll margin and `rootMargin` so they cannot drift apart. |
| Hydration mismatch logs a console error → ID-13 fails | M×H | Initial state is `AWARDS[0].slug` on both sides; `location.hash`, `matchMedia` and `history` are touched only inside effects/handlers. No `suppressHydrationWarning`. |
| Deep link `#mvp` lands, then layout shift pushes MVP out of the viewport | M×H | Every image has explicit `width`/`height` or an aspect-ratio box, so there is no CLS after paint; the mount effect additionally performs an instant `scrollIntoView` when the hash matches, making the landing position independent of native-anchor timing. |
| An empty note `<p>` renders for Best Manager / MVP | M×H | `{prize.note && …}` guard; phase 01 omits the key entirely rather than setting `""`. ID-6's assertion is a *substring* count of 0 — a hidden or whitespace-only node still fails. |
| Scroll-spy flickers mid-smooth-scroll and the active item is wrong when asserted | M×M | Click lock for `SCROLL_SETTLE_MS`; `activeSlug` is a single value, so "exactly one active" is a type invariant, not a cleanup step (BR-002). |
| Icons hand-drawn because no asset was exported → visual mismatch | M×L | Try MoMorph MCP first; otherwise flag it in the phase report so phase 03's visual pass judges it explicitly. Bounded follow-up, not a blocker (clarifications A1). |
| A `<section>` wrapper around the body also matches the Kudos filter, breaking ID-3's single-element resolution | L×H | The two-column body wrapper is a `<div>`. Stated in the architecture tree and in the todo list. |
| File creeps past the 200-line cap (`award-detail-card.tsx` is the likeliest) | M×L | The prize list is already a separate module; if the card still overflows, split the quantity row out — never create an "enhanced" duplicate. |
| The test suite itself is wrong somewhere | L×M | **Do not design around it.** Nothing found so far: all 11 assertions are satisfiable as specified. If the implementer hits one that is not, it escalates to phase 03/the orchestrator — weakening an assertion is forbidden. |

**Rollback:** revert `app/awards-information/page.tsx` to `export default function Page() { return <ComingSoon />; }`
and delete `app/awards-information/_components/`. The route returns to its shipped placeholder, every
homepage link still resolves, and no other screen is touched — the whole phase is contained inside one
route folder.

## Security Considerations

- **Auth:** none added, by decision. `/awards-information` stays public; `proxy.ts` is not in this phase's
  ownership and is not edited (FR-001, FR-601, BR-001, ORCH-03). Test case ID-1 is deliberately not
  implemented — see plan.md R6.
- **Server → client boundary:** `AwardCategoryNav` receives only plain `{ slug, label }` strings. The
  Supabase user object never crosses into a Client Component (the same invariant `app/page.tsx` documents);
  `HomeHeader` keeps receiving only `isAuthenticated` / `isAdmin` booleans.
- **Injection:** all copy renders as React text nodes. No `dangerouslySetInnerHTML`, no `eval`, no
  `innerHTML`.
- **`history.replaceState`** writes only `#<slug>` values drawn from the frozen `AWARDS` list — never from
  user input. Hash *read* on mount is compared against that same list and discarded when it does not match,
  so an attacker-supplied fragment can neither select a scroll target nor reach the DOM.
- No new network call, no new env var, no new dependency, no secret.

## Next Steps

- **Unblocks:** phase 03 (tester GREEN rerun + visual validation).
- **Hand-off:** report the six file paths, the local `npx playwright test …` result, and any icon that was
  hand-authored rather than exported, so phase 03's visual pass knows where to look hardest.
- **Not this phase:** editing `e2e/**` or `playwright.config.ts`, browser/visual evidence capture (tester
  owns it), `docs/**` (phase 04), any backend or data-model work (there is none — clarifications A2).
