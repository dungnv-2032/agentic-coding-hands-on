# Reviewer — Award System screen (`/awards-information`)

- **Date:** 2026-09-06 · **Branch:** `feat/language-dropdown-open-state` · **Depth:** full (uncommitted working tree)
- **Plan:** [plan.md](../plan.md) · **Decisions:** [clarifications.md](../clarifications.md) · **Tester:** [final verdict](./tester-260906-0851-award-system-final-verdict.md)
- **Stance:** read-only. Nothing in the tree was edited.

## Scope

| File | Lines | Verdict |
|---|---|---|
| `app/awards-information/page.tsx` | 121 | clean |
| `app/awards-information/_components/award-category-nav.tsx` | 146 | W-2 |
| `app/awards-information/_components/award-detail-card.tsx` | 141 | W-1, W-3 |
| `app/awards-information/_components/award-prize-list.tsx` | 71 | clean |
| `app/awards-information/_components/award-system-hero.tsx` | 80 | S-5 |
| `app/awards-information/_components/award-system-icons.tsx` | 103 | clean |
| `lib/award-system.ts` | 32 | S-4 |
| `lib/i18n/messages/{vi,en}-award-system.ts` | 92 / 91 | clean |
| `lib/i18n/messages/dictionary.ts` (+39) | — | S-4 |
| `app/_components/kudos-promo.tsx` (+18/−4) | 79 | S-11, S-12 |
| `lib/i18n/messages/{vi,en}.ts`, `playwright.config.ts` | +2/+2/+1 | clean |

Re-run here: `npx tsc --noEmit` **exit 0**; `npm run lint` **0 errors, 3 warnings** — all three are
pre-existing unused-import warnings in `e2e/homepage.spec.ts` / `e2e/homepage-authed.spec.ts`, none in
files this change touches. `e2e/award-system.spec.ts` lints clean.

## Assessment

**Ship-ready with three fixes worth making first, none of them blocking a desktop release.**
No critical finding. No security finding: the screen is display-only, reads no user data, writes
nothing, and the one piece of attacker-influenced input on it — `location.hash` — is validated against
the frozen slug list *before* it reaches `getElementById` (`award-category-nav.tsx:57`), so an
arbitrary fragment selects nothing and no-ops silently. The Server/Client boundary is correct, the
data/render agreement for the optional prize note is correct **in the code**, and the type-only import
cycle is genuinely type-only.

The three warnings are all in the class the review was asked to hunt: defects that clear a green suite
because the suite only runs Desktop Chrome at 1440×900 and only asserts states that the test itself
drives.

---

## Critical

**None.**

---

## Warning

### W-1 — `HEADER_OFFSET = 112` under-clears the sticky header below `lg`; a menu tap or deep link parks the card title behind it

`app/awards-information/page.tsx:25` · `app/awards-information/_components/award-detail-card.tsx:52`

`HEADER_OFFSET` is documented against a **72px** header (`page.tsx:19-24`), which is the header's
*desktop* height. `app/_components/home-header.tsx:52` is `flex-wrap` and `app/_components/home-nav.tsx:57`
is `flex flex-wrap`, and both carry comments saying the row deliberately wraps below `lg` because the
three nav items measure 333px at min-content. At 375px the header therefore stacks: logo (52) beside a
nav that wraps to three rows of `py-4` links (3 × 52 + 2 × 4 = 164), then the right cluster on its own
wrapped line (~48), plus `py-3` twice — **≈ 235px of sticky header**.

Failure scenario: viewport 375×667, open `/awards-information#mvp` (the exact link
`app/_components/award-card.tsx` puts on every homepage award card), or tap "MVP" in the category
strip. `scrollMarginTop: 112` lands the section top at y=112 — roughly 120px *behind* the sticky
header. The user sees the middle of the 336px badge; the target icon, the card title and the first
lines of the description are all covered. Nothing in the suite catches it: `playwright.config.ts`
pins `devices["Desktop Chrome"]` and ID-7 explicitly re-pins 1440×900.

Fix — keep one constant for the `lg` path where the number was measured, and let Tailwind carry the
responsive offset for the scroll target:

```tsx
// award-detail-card.tsx — drop the inline style, add the class
<section
  id={award.slug}
  data-testid={`award-detail-${award.slug}`}
  className={`scroll-mt-[248px] sm:scroll-mt-[160px] lg:scroll-mt-28 flex w-full flex-col gap-20 ${isLast ? "" : "border-b border-[#2E3940] pb-20"}`}
>
```

`lg:scroll-mt-28` is 112px, so the desktop geometry the tester measured is byte-unchanged; the
`headerOffset` prop then only feeds the observer and the sticky `top`, both of which are `lg`-only
concerns anyway (the nav is `lg:sticky` — `award-category-nav.tsx:121` — so its inline `top` is inert
below that breakpoint). Confirm the two mobile numbers against a real 375px and 768px render rather
than against my arithmetic.

*Alternative if you want one number instead of three:* measure the header once on mount in the nav
effect and publish it as a CSS custom property on the page wrapper, with the sections reading
`style={{ scrollMarginTop: "var(--award-header-offset, 112px)" }}`. Costs a client measurement and a
resize listener; the static-class version is KISS and I'd take it.

### W-2 — an interrupted programmatic scroll leaves the wrong item lit, permanently (FR-402)

`app/awards-information/_components/award-category-nav.tsx:72` (the discard) · `:101-111` (the lock)

`clickLock` suppresses the observer for a flat 700ms and the callback **discards** what it saw
(`if (clickLock.current) return;`). The lock's release is a bare timer — nothing re-reads geometry
when it expires, and `IntersectionObserver` only delivers on a *change*. So any intersection change
that happens inside the window is lost with no recovery.

Failure scenario, inputs → state → wrong behaviour:
1. Load `/awards-information` at the top. Active = `top-talent`.
2. Click "MVP". `setActiveSlug("mvp")` (line 100), `clickLock = true`, smooth scroll starts.
3. At t≈100ms the user wheel-scrolls upward — this cancels the browser's smooth scroll — and comes to
   rest back on Top Talent by t≈300ms.
4. The `top-talent` intersection change fires at ~t=150ms, **inside** the lock, and is dropped at line 72.
5. At t=700ms the lock clears. The user is at rest, so no further intersection change ever fires.
6. **The nav shows MVP gold with its underline while Top Talent fills the viewport, and stays wrong
   until the user happens to cross another card boundary.**

This violates FR-402 ("menu tự cập nhật theo hạng mục đang hiện trên màn hình") and BR-002's
resolution order — the click is no longer "the most recent input", the wheel is. The suite cannot see
it: ID-9/11 clicks and then waits, never interrupting, and Playwright's auto-retry hides even the
transient flicker on a long hop (clicking MVP from the top is ~5,000px of smooth scroll, which
outlives the 700ms lock, so the highlight walks through the intermediate cards before settling —
correct final state, visibly noisy transit).

Fix — release the lock on the first user-initiated scroll input, and resolve from real geometry
instead of waiting for the next delivery:

```tsx
const resolveActive = useCallback(() => {
  const bandTop = headerOffset;
  const bandBottom = window.innerHeight * 0.45;   // mirrors the -55% rootMargin
  let best: { slug: string; d: number } | null = null;
  for (const slug of slugKey.split(",")) {
    const rect = document.getElementById(slug)?.getBoundingClientRect();
    if (!rect || rect.bottom <= bandTop || rect.top >= bandBottom) continue;
    const d = Math.abs(rect.top - bandTop);
    if (!best || d < best.d) best = { slug, d };
  }
  if (best) setActiveSlug(best.slug);
}, [slugKey, headerOffset]);

const releaseLock = useCallback(() => {
  if (!clickLock.current) return;
  clickLock.current = false;
  if (lockTimer.current) clearTimeout(lockTimer.current);
  resolveActive();
}, [resolveActive]);

useEffect(() => {
  // A wheel/touch/key scroll during the settle window means the user overrode
  // the click — hand the active state straight back to the scroll position.
  const opts = { passive: true } as const;
  window.addEventListener("wheel", releaseLock, opts);
  window.addEventListener("touchstart", releaseLock, opts);
  window.addEventListener("keydown", releaseLock);
  return () => {
    window.removeEventListener("wheel", releaseLock);
    window.removeEventListener("touchstart", releaseLock);
    window.removeEventListener("keydown", releaseLock);
  };
}, [releaseLock]);
```

and call `resolveActive()` from the existing lock timer's callback too, so the non-interrupted path
also ends on measured geometry rather than on the optimistic value.

*Alternative:* replace the timer entirely with the `scrollend` event (Chrome 114+, Firefox 109+,
Safari 26) — `window.addEventListener("scrollend", …)` clears the lock exactly when the scroll
actually stops, interrupted or not, with the timer kept as the fallback for older Safari. Cleaner
semantics, one more capability check.

**Related, smaller, same root:** the `nearest` reduce at `:75-79` only ranks the entries *in this
batch*, not every currently-intersecting section, and `entry.boundingClientRect` is the rect sampled
at change time, not at callback time. Under a fast flick that can pick a section that has already left
the band. `resolveActive()` above fixes this too, since it measures live rects.

### W-3 — the six award sections carry no heading and no accessible name

`app/awards-information/_components/award-detail-card.tsx:49-53` (the section) · `:95` (the title)

The card title is a `<p className="text-2xl …">`. Grepped across the whole rendered tree, the page's
headings are exactly: `h1` (hero, `award-system-hero.tsx:72`) → `h2` ("Sun* Kudos",
`kudos-promo.tsx:50`). The six award blocks — the entire substance of the screen — contribute nothing.

Failure scenario: a screen-reader user follows the homepage deep link to
`/awards-information#signature-2025-creator`. Heading navigation (`H`, or the rotor) shows two
headings for a 6,410px page and jumps from the page title straight to the Kudos promo. Landmark
navigation is no better: a `<section>` with no accessible name maps to `generic`, not `region`, so the
six sections are not landmarks either. The user has no structural way to reach or identify an award.

Fix — promote the title and name the section:

```tsx
<section
  id={award.slug}
  aria-labelledby={`${award.slug}-title`}
  data-testid={`award-detail-${award.slug}`}
  …
>
  …
  <h2 id={`${award.slug}-title`} className="text-2xl leading-8 font-bold text-[#FFEA9E]">
    {card.title}
  </h2>
```

Checked against the frozen test contract before proposing it: ID-4 asserts
`getByRole("heading", { level: 1 })` and `toHaveText` — still exactly one `h1`, still exactly its own
string. ID-6 reads the title with `section.getByText(award.title, { exact: true })`, which matches an
`<h2>` identically. ID-3's `documentOrder` walk and ID-7's image lookup are untouched. The homepage
suite never renders this component. Visual result is unchanged — the class list is carried over
verbatim and Tailwind Preflight already zeroes heading margins and font-size.

Two smaller a11y items in the same file, folded in rather than listed separately:
`alt={card.title}` (`:78`) duplicates the adjacent visible title, so the badge is announced twice;
the contract freezes it, so leave it, but with the `h2` in place `alt=""` would be the more honest
call if the contract is ever reopened. And there is no `focus-visible` ring on the nav anchors
(`award-category-nav.tsx:133-137`) — the UA default ring survives (Preflight does not strip outlines),
so this is not a defect, but an explicit `focus-visible:outline-2 focus-visible:outline-offset-2
focus-visible:outline-[#FFEA9E]` would match the screen's own token instead of the browser's.

---

## Suggestion

### S-4 — the `dictionary.ts` ↔ `award-system.ts` cycle is avoidable, not just harmless

`lib/i18n/messages/dictionary.ts:11` · `lib/award-system.ts:1`

**Confirmed safe as written.** Both edges are `import type`, TypeScript erases them unconditionally,
`isolatedModules: true` (`tsconfig.json`) guarantees the per-file transpile can do that erasure, and
`dictionary.ts` exports nothing but `type AwardKey` and `interface Dictionary` — grepped, there is no
`export const`/`export function` in it. There is no runtime edge from `dictionary.ts` to
`award-system.ts`, so `AWARD_UNITS` cannot participate in an initialization cycle. `tsc --noEmit`
exits 0. No action strictly required.

That said, `AwardKey` — the sibling concept — is already declared in `dictionary.ts:18`. Declaring
`AwardUnitKey` beside it and having `lib/award-system.ts` import both removes the cycle outright,
follows the file's own precedent, and stops the i18n contract from depending on a domain module. Also:
`dictionary.ts:11` uses a relative `"../../award-system"` where the rest of the repo reaches for
`@/lib/…`.

### S-5 — the hero's content column is 288px wider than the body's above a 1728px viewport

`award-system-hero.tsx:19` puts `lg:px-36` on the `<section>` and `max-w-[1440px]` on the inner div at
`:48`, so the padding sits *outside* the cap. `page.tsx:79` and `kudos-promo.tsx:33` put both on the
same element, so the cap includes the padding. At the 1440 artboard all three resolve to 1152 and
agree. At 1920 the hero renders **1440** of content while the card column and Kudos render **1152** —
the hero's hairline divider (`award-system-hero.tsx:68`) overhangs the card column's rules by 144px on
each side. Visible on any 1920 or 2560 monitor; the tester measured at 1440, where it cannot appear.

Fix: `award-system-hero.tsx:48` → `max-w-[1152px]`. Do **not** move the cap onto the `<section>` — the
keyvisual at `:29` is `absolute inset-x-0` against it and must stay full-bleed.

### S-6 — `metadata.title` is a hardcoded English string on a locale-switched screen

`page.tsx:16`. In the VI locale every visible string is Vietnamese while the browser tab reads
"Award Information — Sun* Annual Awards 2025". `app/layout.tsx:9` has the same issue, so this is the
established pattern rather than a regression — worth fixing here or noting as a follow-up.

`generateMetadata` can read the cookie, but note the trap: it runs in a separate pass from the page,
so a naive `await getPageContext()` inside it **doubles the `supabase.auth.getUser()` round-trip per
request**. Wrap `getPageContext` in React `cache()` first (`app/_page-context.ts:27`) — that is a
one-line change that also benefits `/` — and only then add `generateMetadata`.

### S-7 — the category nav's accessible name is the page's own `h1`

`page.tsx:85` passes `ariaLabel={awardSystem.hero.title}`, so the nav announces as
"Hệ thống giải thưởng SAA 2025, navigation" — it repeats the page title and says nothing about what
the navigation *is*. There are three `<nav>` landmarks on this page (`home-nav.tsx:57`,
`site-footer.tsx:45`, and this one) and only this one is labelled at all, which is the right
direction; give it its own key, e.g. `awardSystem.navAriaLabel` = "Danh mục giải thưởng" /
"Award categories". This is also the one string on the screen that is composed in `page.tsx` rather
than sourced from the dictionary as itself.

### S-8 — `preventDefault()` is unconditional, so modifier-clicks on a category link are swallowed

`award-category-nav.tsx:97`. Cmd/Ctrl+click and Shift+click on `#mvp` are legitimate — they open the
screen in a new tab/window already scrolled to that award. Today they scroll the current tab instead.
Guard before the `preventDefault`:

```tsx
if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
```

(Middle-click already works: React does not fire `onClick` for it.)

### S-9 — a ~600-character paragraph is used as a React key

`award-detail-card.tsx:100`, `key={paragraph}`. Unique today only because no award repeats a
paragraph. A future locale or copy edit that repeats one produces a duplicate-key React warning —
which **ID-13 asserts against** (`consoleErrors).toEqual([])`), so the failure mode is a red suite on a
copy change. The list is static and never reordered; `key={index}` is correct here.

### S-10 — `w-[60px]` on the unit is a VI measurement applied to both locales

`award-detail-card.tsx:123`. In EN, "Individual" is ~87px at 14px Montserrat Bold and overflows its
60px box; "Individual or team" wraps to three lines with the first overflowing. There is no
`overflow-hidden` and the row has spare width, so nothing clips or collides — it is a ragged edge, not
a break. But the design value was carried across without an EN check. `max-w-[88px]` (or
`basis-[60px]`) preserves the VI wrap the frame specifies while letting EN sit inside its box.

### S-11 / S-12 — `kudos-promo.tsx`

**S-11, the prop's type.** `maxWidthClass?: string` (`:25`) is an unconstrained class string. The
default preserves homepage behaviour exactly — verified two ways: the default literal at `:28` is the
same `max-w-[1224px]` the old hardcoded class used, and the tester measured `/` at
`section width 1224 · card width 936`, identical to the pre-change record. Tailwind scanning is safe
because **both** values appear as complete literals in source (`:28` and `page.tsx:115`). The residual
risk is the next caller: `maxWidthClass={`max-w-[${n}px]`}` compiles, is never emitted by the scanner,
and the section silently loses its cap. Make that a compile error —
`maxWidthClass?: "max-w-[1224px]" | "max-w-[1440px]"`.

**S-12, `sizes`.** `:41` declares `(min-width: 1024px) 1224px, 100vw`. The real rendered width of the
`fill` image is 936px on `/` and 1152px on `/awards-information` (the `p-10 sm:p-16` on the positioned
parent does not reduce the fill box, but the container padding does). Over-declaring only over-fetches
— it never under-resolves, so there is no blur and no bug. If bytes matter:
`sizes="(min-width: 1440px) 1152px, (min-width: 1024px) 936px, 100vw"`.

### S-13 — the deep-link path does not implement the mechanism clarifications records

`award-category-nav.tsx:55-59`. clarifications.md states, for FR-102/DEC-002: *"The nav mounts, reads
`location.hash`, and seeds the active item from it."* The effect as written **only scrolls** — the
comment at `:52-54` says so explicitly — and hands the active state to the observer's first async
delivery at `:80`.

I am not reopening the accepted 290ms transient; the tester's hydration measurement stands and
dominates. But the question asked was whether the mechanism is what it is claimed to be, and it is
not: the current path adds an IntersectionObserver-delivery hop *on top of* hydration, and makes the
seeded value a function of observer timing rather than of the hash. One line at `:57` implements the
recorded design, keeps R3 intact (it runs inside an effect, never during render, so the SSR/first
client render still agree on `items[0]`), and makes the deep-link result deterministic:

```tsx
if (!slug || !slugKey.split(",").includes(slug)) return;
setActiveSlug(slug);                                   // ← the recorded mechanism
document.getElementById(slug)?.scrollIntoView({ behavior: "auto", block: "start" });
```

Either implement it, or amend clarifications.md so the record matches the code. Right now they
describe two different designs.

### S-14 — a public, entirely static screen still pays a Supabase auth round-trip per request

`page.tsx:49` → `app/_page-context.ts:31`. Every render of a page whose content is six paragraphs of
frozen copy calls `supabase.auth.getUser()` over the network, to produce two booleans consumed only by
the header. This is the shipped homepage pattern (`app/page.tsx:25`), not a regression introduced
here, and composing `HomeHeader` unchanged was the right DRY call (ORCH-03). Recording the cost, not
asking for it to be undone in this change. Wrapping `getPageContext` in `cache()` (see S-6) is the
cheap half of the improvement.

---

## Edge cases turned up in the scouting pass

Cases the diff does not show, walked and **cleared**:

- **Can the "exactly one active" invariant break to 0 or 2?** No. `activeSlug` is a single string
  (`:41`) and is only ever assigned `items[0].slug` or an observed `entry.target.id`, and the observed
  set is exactly the slugs in `items`. It is an invariant of the state shape, as the comment claims —
  not a cleanup step that could be skipped. W-2 is about the value being *stale*, never about the count.
- **Observer cleanup.** `observer.disconnect()` on unmount and on every `slugKey`/`headerOffset`
  change (`:85`); the settle timer is cleared both on re-click (`:105`) and on unmount (`:88-90`).
  No leak, no double-observe.
- **Empty/degenerate `items`.** `slugKey = ""` → `"".split(",")` is `[""]` → `getElementById("")` is
  `null` → filtered → `targets.length === 0` → early return (`:68`). The deep-link effect's `includes`
  guard rejects any real slug against `[""]`. Both paths no-op rather than throw.
- **Hostile fragment.** `#<img src=x onerror=…>`, `#%6Dvp`, `#../../etc` — all fail the `includes`
  check at `:57` before any DOM call. No `innerHTML`, no selector interpolation anywhere in the change.
- **`history.replaceState(null, "", "#slug")`** (`:103`) is exactly the pattern Next 16 documents at
  `node_modules/next/dist/docs/01-app/01-getting-started/04-linking-and-navigating.md:414` — the
  patched method merges with router state, so `usePathname`/`useSearchParams` stay in sync and no
  back-button reload is introduced. Correct, and correctly `replace` rather than `push`.
- **`preload` on `<Image>`** (`award-system-hero.tsx:57`) is right for this version:
  `docs/…/components/image.md:293` records `priority` as deprecated in favour of `preload` as of
  Next 16. Not a stale API.
- **Server/Client boundary.** `"use client"` appears exactly once in the change, on the nav leaf.
  Everything crossing into it is a plain array of `{slug,label}` strings plus a string and a number.
  `HomeHeader` receives the two booleans and the plain dictionary object, never the Supabase `user` —
  confirmed at `app/_page-context.ts:36-41`, which returns only `user !== null` and a role comparison.
  `award-system-icons.tsx` is imported from both a Client and a Server Component; that is a dual-use
  plain function module and bundles independently on each side without issue.
- **Prize `note` absence, verified in code rather than in the test result.** The key is *omitted*, not
  empty, at `vi-award-system.ts:65` and `:89` and `en-award-system.ts:64` and `:88`; the type makes it
  `note?: string` (`dictionary.ts`); the render guards with `{prize.note && …}` at
  `award-prize-list.tsx:61`, which emits nothing at all — no empty `<p>`, no wrapper. All three layers
  agree. R4 is met by construction.
- **`prefers-reduced-motion`** is read fresh at click time (`:98`), so a mid-session OS change is
  honoured; the deep-link path is already `behavior: "auto"`. FR-403 met.
- **Very short viewports.** The band is `[112px, 0.45 × viewportHeight]`; it inverts only below a
  ~249px-tall viewport, at which point the observer reports nothing and the nav stays on the first
  item. Not reachable in a real browser window; noting the boundary, not raising it.
- **`playwright.config.ts` blast radius.** The `testMatch` widening pulls `award-system.spec.ts` into
  the `anon` project; the tester ran the whole project (53/53, exit 0) rather than only the new file,
  which is the right check for that edit.

## Acceptance criteria

| Criterion | Status |
|---|---|
| R1 — strict-mode single-node strings | **Met.** `Số lượng giải thưởng:` renders once per card (`award-detail-card.tsx:116`); `Giá trị giải thưởng:` renders per prize row and the suite uses `.first()`. |
| R2 — one offset, three consumers | **Met at `lg`, not below.** See W-1. |
| R3 — no hydration mismatch | **Met.** Initial state is `items[0]` (`:41`); `location.hash`, `matchMedia`, `history` are confined to effects and handlers. |
| R4 — no note line for Best Manager / MVP | **Met**, verified across data, type and render. |
| R5 — icons | **Met.** Three inline SVGs, `currentColor`, no `<title>` (which would have broken the nav's `toHaveText`). |
| R6 — ID-1 not implemented | **Met**, recorded in clarifications and in the functional spec as D001/RISK-01, not silently dropped. |
| Integration contract (frozen) | **Met in full** — section `id` + `data-testid`, `award-nav` with exactly six links, `aria-current` present-or-absent, `alt === card.title`, single `h1`, document order. |
| Contract compatibility | **Changed, additively.** `Dictionary` gains a required `awardSystem`; both implementers (`vi.ts`, `en.ts`) are updated in the same change, and `tsc` exits 0. `KudosPromo` gains an optional prop with a default proven identical by measurement. `playwright.config.ts` widens a project. Nothing breaks. |

## Done well

- The Server/Client split is genuinely minimal, and the "no Supabase user across the boundary" claim
  is true in the code, not just in the comment.
- `AWARDS` stayed the single source of order, slug and image; `Record<AwardKey, …>` exhaustiveness in
  three separate places means a seventh award cannot compile until every layer declares it. The
  temptation to redefine the slug list locally was explicitly refused, and `lib/award-system.ts:6-11`
  says why.
- `note?` omitted rather than `""` — a type-level statement of a design fact, with the reasoning
  written down in the interface. That is the right shape and it is rare to see it chosen.
- The comments say *why* and carry `mm:` node ids in the house style, including the ones that record a
  defect already fixed (`award-detail-card.tsx:60-69` on `self-start`/`aspect-square`) so it cannot be
  refactored back in.
- Hash validated against a frozen list before any DOM call — the security-relevant instinct on a
  screen where nobody would have looked for it.
- Every file well under the 200-line cap, kebab-case throughout, zero `any`, zero `@ts-ignore`, zero
  `eslint-disable`.
- The tester's decision to measure the homepage Kudos block directly rather than infer it from a green
  suite is the correct standard for a shared-component change, and it is why S-11 is a type suggestion
  rather than a warning.

## Actions in order

1. **W-1** — responsive scroll offset. Highest real-user impact; mobile deep links from the homepage
   are a primary entry path.
2. **W-2** — release the click lock on user scroll input and resolve from live geometry. Fixes both
   the permanent stale state and the batch-only `nearest` reduce.
3. **W-3** — `h2` + `aria-labelledby` on the six sections. Verified safe against the frozen contract.
4. **S-13** — either seed `activeSlug` from the hash or amend clarifications.md. Pick one; do not
   leave the record and the code describing different designs.
5. **S-5, S-9, S-8** — one-line each: hero cap `1152`, `key={index}`, modifier-click guard.
6. **S-4, S-6, S-7, S-10, S-11, S-12, S-14** — housekeeping, safe to batch or defer.

## Numbers

- Typecheck: **exit 0**, `strict: true`, no `any`/`@ts-ignore`/`@ts-expect-error` in the change.
- Lint: **0 errors**, 3 warnings, all pre-existing and all outside the changed files.
- E2E (tester, re-verified from the report, not re-run here): award-system 13/13, homepage 22/22,
  full anon project 53/53 — all exit 0.
- Code files added/changed: 12. Largest file 146 lines against a 200-line cap.
- Findings: **0 critical · 3 warning · 11 suggestion.**

## Still unresolved

- **Where W-1's mobile offsets should actually land.** My 235px figure is arithmetic from the wrap
  rules in `home-header.tsx` / `home-nav.tsx`, not a measurement. Someone should render 375px and
  768px and read the real header height before pinning `scroll-mt-[…]`.
- **Whether the category screen should be exercised at a mobile viewport at all.** The whole suite is
  Desktop Chrome; W-1 exists precisely in that gap. Adding one 375px projection of ID-9 would close
  it, but that is a suite-scope decision and `e2e/**` is outside this change's file ownership.
- **S-13's disposition** is a decision, not a defect: implement the recorded mechanism, or amend the
  record. Both are legitimate; leaving them divergent is not.
- Carried forward from clarifications, untouched here: test case ID-1 (anon → login) contradicts
  shipped behaviour and awaits a product owner; ID-14 targets `/kudos`, still a `ComingSoon`
  placeholder; `Hoặc` at `#2E3940` on `#00101A` (1.64:1) is faithful to the frame and remains a
  designer question, not a code finding.
