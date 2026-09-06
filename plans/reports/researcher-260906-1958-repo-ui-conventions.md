# Repo UI/i18n conventions — for `/kudos` (matching F003 award-system precedent)

Skill check: no listed skill fits raw in-repo convention extraction (not a tech
trade-off, not external lib docs) — read the repo directly per fallback.

**IMPORTANT FINDING:** `app/kudos/page.tsx` already exists — it's the `ComingSoon`
placeholder shell (app/kudos/page.tsx:1-14), `title: "Sun* Kudos — Sun* Annual
Awards 2025"`. Building `/kudos` means REPLACING this file's body, same route,
same metadata title convention.

## 1. Screen anatomy
- `page.tsx` = async Server Component, single responsibility: call
  `getPageContext()` (app/_page-context.ts:27) once, destructure
  `{locale, dictionary, isAuthenticated, isAdmin}`, compose shared chrome +
  screen `_components/`. See app/awards-information/page.tsx:55-126.
- `_components/` = screen-local pieces, one dir per route
  (`app/awards-information/_components/`). Shared cross-screen chrome lives in
  `app/_components/` (home-header, site-footer, coming-soon, award-card,
  awards-grid, kudos-promo, icons.tsx, language-selector, account-menu…).
- Client/server split: ONLY components with real interactivity get
  `"use client"` — home-header.tsx:1 (dropdown/menu state),
  award-category-nav.tsx:1 (scroll-spy state, the ONLY client component on the
  award-system screen per its own comment at award-category-nav.tsx:22-23),
  use-award-scroll-spy.ts:1 (hook, client-only). `page.tsx`,
  award-detail-card, award-system-hero, award-prize-list are server
  components — plain data-to-markup, no hooks.
- `metadata` = static `export const metadata: Metadata = {...}` object per
  page, title-only, pattern `"<Screen Name> — Sun* Annual Awards 2025"`
  (awards-information/page.tsx:16; kudos/page.tsx:5).
- Shared session/locale read: `getPageContext()` is the ONE place cookies +
  Supabase session are read; only two booleans (`isAuthenticated`, `isAdmin`)
  cross into the Client Component `HomeHeader` — Supabase `user` object never
  does (app/_page-context.ts:22-25, enforced by comment + code, not a lint
  rule).

## 2. Styling — Tailwind v4, confirmed
- `postcss.config.mjs` loads `@tailwindcss/postcss` (postcss.config.mjs:1-5);
  `package.json` has `"tailwindcss": "^4"`. `app/globals.css:1` is
  `@import "tailwindcss";` + a `@theme inline` block mapping `--color-*`/
  `--font-*` CSS vars — NOT the old `tailwind.config.js` (v4 CSS-first config).
  No CSS modules, no styled-components anywhere in the screen files read.
- Colors are NOT tokenized beyond `--background`/`--foreground` — every
  design-specific hex is an arbitrary-value Tailwind class inline, e.g.
  `bg-[#00101A]` (page background, awards-information/page.tsx:67),
  `text-[#FFEA9E]` / `border-[#FFEA9E]` (gold accent,
  award-category-nav.tsx:78-79), `bg-[rgba(16,20,23,0.8)]` (header glass,
  home-header.tsx:47). Every arbitrary class carries an `mm:{nodeId}` comment
  citing the Figma node it was measured from (code-rules.md rule 1 — MoMorph
  1-1 node mapping is enforced project-wide, not just award-system).
- File-size discipline (repo rule: 200-line cap) IS observed: page.tsx 126,
  award-category-nav.tsx 89, award-detail-card.tsx 154,
  award-prize-list.tsx 71, award-system-hero.tsx 86,
  award-system-icons.tsx 103, use-award-scroll-spy.ts 196 (right at the
  ceiling — its own comment at use-award-scroll-spy.ts:9 says it was split
  out of award-category-nav.tsx specifically to keep both files under 200).
  Shared `_components/`: all ≤188 lines (language-selector.tsx 188 is the
  largest). No violations found.

## 3. i18n — compile-time-enforced dual-locale dictionary
- `lib/i18n/messages/dictionary.ts` declares one `interface Dictionary` with
  every namespace (`login`, `footer`, `header`, `home`, `awardSystem`,
  `comingSoon`, dictionary.ts:26-152). Fields are plain `string`/typed
  objects — a key present in `vi` but missing in `en` fails
  `npm run typecheck`, not a runtime fallback (comment at dictionary.ts:1-9).
- Pattern to add a namespace (mirrors award-system):
  1. Add the namespace shape to `Dictionary` in `dictionary.ts`.
  2. Create `lib/i18n/messages/vi-<namespace>.ts` exporting
     `export const vi<Namespace>: Dictionary["<namespace>"] = {...}` (see
     vi-award-system.ts:15).
  3. Create the matching `en-<namespace>.ts`.
  4. Wire both into `vi.ts` / `en.ts` as `<namespace>: vi<Namespace>`
     (vi.ts:45).
  5. `lib/i18n/dictionaries.ts:16` maps `{vi, en}` by `Locale`; `getDictionary
     (locale)` returns the whole object.
- Reading pattern: NOT context, NOT a hook — plain prop drilling of the
  already-resolved `dictionary` object (or a destructured sub-slice) from the
  async server `page.tsx` down through props
  (`award={award} card={awardSystem.cards[award.key]}` at
  awards-information/page.tsx:100-105). Server Component reads the dictionary
  once; Client Components receive plain resolved strings, never the
  dictionary module itself (dictionaries.ts:11-14).
- Locale resolution: cookie-based, `NEXT_LOCALE` (locales.ts:14),
  `resolveLocale()` defaults to `"vi"` on anything unrecognized
  (locales.ts:22-24). No `[locale]` route segment (see §7).

## 4. Icons/assets
- SVG icons = inline React components, NOT `<img src=".svg">`. One file per
  screen's icon set: `award-system-icons.tsx` exports `IconTarget`,
  `IconDiamond`, `IconLicense`, each a literal `<svg>` with paths using
  `fill="currentColor"` (award-system-icons.tsx:33-49) so the parent
  className controls color (gold active vs white inactive) — this is a hard
  project rule, not a local choice
  (.claude/skills/momorph-implement-design/references/code-rules.md rule 2a:
  never `<img>` for icons, always inline + `currentColor`, extract to a
  component if reused ≥2×). Shared multi-screen icons live in
  `app/_components/icons.tsx` (IconChevronDown used by award-card.tsx:6,56).
- Raster images live under `public/images/<feature>/` (`public/images/home/`,
  `public/images/login/`) and ARE referenced via `next/image`'s `<Image>`
  (home-header.tsx:3,55-61; award-card.tsx:1,38-44), always with explicit
  `width`/`height` and a real `alt` (award title text doubles as alt, per
  award-card.tsx:14-19 comment — no separate name overlay).
- Every element traces to a Figma node via `// mm:{nodeId}` or
  `{/* mm:{nodeId} */}` comments (award-system-icons.tsx:21-32 etc.) — repo-
  wide MoMorph convention, keep it for `/kudos` if building from a MoMorph
  screen.

## 5. Client interaction (use-award-scroll-spy.ts)
- Hook file: co-located inside the route's `_components/`, not a global
  `hooks/` dir (`app/awards-information/_components/use-award-scroll-spy.ts`).
  Naming: `use-<verb-object>.ts` kebab-case file, `useCamelCase` export
  matching filename (`useAwardScrollSpy`, use-award-scroll-spy.ts:30). Same
  pattern for shared hooks: `app/_components/use-dismiss-on-outside.ts`,
  `use-scroll-to-top-if-current.ts`.
  `"use client"` is the file's first line (use-award-scroll-spy.ts:1).
- State management: plain `useState`/`useRef`/`useCallback`/`useEffect` —
  no external state library, no `useReducer` even for the fairly complex
  scroll-spy logic (multi-effect: IntersectionObserver + click-lock +
  hash-deep-link, use-award-scroll-spy.ts:30-196). Hook returns a small
  `{activeSlug, activate}` API consumed by the one client component that
  needs it (award-category-nav.tsx:39).
- Hydration-safety rule stated explicitly: first client render must byte-match
  SSR output; anything reading `location.hash`/`matchMedia`/`history` is
  confined to effects/handlers, never render body
  (award-category-nav.tsx:24-29).

## 6. Test hooks (data-testid)
- Convention: `data-testid="<component>"` for the generic case,
  `data-testid="<component>-<slug>"` when repeated — enforced rule "one
  element cannot hold two testids" (award-card.tsx:20-26). Examples:
  `award-card` (outer wrapper) + `award-card-${award.slug}` (inner Link)
  (award-card.tsx:31,33); `award-nav` (nav container) +
  `award-nav-${item.slug}` (per item) (award-category-nav.tsx:61,73); section
  contract from the e2e spec: `id="<slug>"` + `data-testid="award-detail-<slug>"`
  per award section (e2e/award-system.spec.ts:17-22).
- Active-state a11y: `aria-current="true"` present-or-absent, never
  `"true"/"false"` toggle, because the e2e suite counts
  `[aria-current="true"]` and expects exactly one (award-category-nav.tsx:74,
  comment at :31-34).
- E2E spec structure: constants for route/labels transcribed verbatim from
  `clarifications.md`, explicit comment "nothing here is invented"
  (e2e/award-system.spec.ts:8-9). For `/kudos`, same discipline: pull literal
  copy from the dictionary/spec, don't paraphrase in the test.

## 7. Locale routing
- NO `[locale]` dynamic segment anywhere under `app/`. Locale is a cookie
  (`NEXT_LOCALE`, `LOCALE_COOKIE` in locales.ts:14), read once server-side in
  `app/layout.tsx:22-23` (sets `<html lang>`) and again in
  `getPageContext()` (app/_page-context.ts:33). `/kudos` needs ZERO route
  restructuring for locale — just call `getPageContext()` like every other
  screen, same as `/awards-information`.

## Copy-these-patterns checklist for `/kudos`
1. Replace `app/kudos/page.tsx` body in place — keep the `Metadata` export
   pattern (`"Sun* Kudos — Sun* Annual Awards 2025"` already present, kudos/page.tsx:5).
2. `async function Page()` → `getPageContext()` once → compose `HomeHeader` +
   `<main>` + `SiteFooter`, `bg-[#00101A]` wrapper, `font-montserrat` +
   both variable fonts on the outer div (mirror
   awards-information/page.tsx:66-68).
3. Put screen-local pieces in `app/kudos/_components/`; reuse
   `app/_components/kudos-promo.tsx` if the block overlaps the homepage's
   Kudos section (it already exists and is reused across homepage +
   award-system, kudos-promo.tsx).
4. Add a `kudos` namespace: extend `Dictionary` in `messages/dictionary.ts`,
   create `vi-kudos.ts` / `en-kudos.ts`, wire into `vi.ts`/`en.ts` — do not
   put new copy in `home.kudos` (that's the homepage teaser, different
   namespace already at dictionary.ts:90-96).
5. New icons → inline SVG components with `currentColor`, one file
   `kudos-icons.tsx` if ≥2 icons, extracted per code-rules.md rule 2a.
6. Any client interactivity → dedicated `use-<name>.ts` hook co-located in
   `_components/`, plain `useState`/`useEffect`, `"use client"` only on the
   file(s) that truly need it.
7. `data-testid` per the `component` / `component-slug` split; keep
   `aria-current="true"` present-or-absent if there's an active-item pattern.
8. Every hex/spacing value gets an inline Tailwind arbitrary-value class with
   an `mm:{nodeId}` comment citing the source Figma node — don't invent a
   token file.
9. Keep every new file ≤200 lines; split hooks out like
   use-award-scroll-spy.ts did if a component nears the cap.
10. No locale routing work needed — cookie-based, already global.

## Unresolved / left uncovered
- `docs/code-standards.md` cited in the task brief does not exist at that
  path; the closest is `docs/system/architecture.md` (not read in depth —
  out of scope for this pass, worth a follow-up read before implementation
  if architecture-level conventions beyond UI are needed).
- Did not read `award-detail-card.tsx` / `award-prize-list.tsx` /
  `award-system-hero.tsx` bodies in full detail (only line counts + inferred
  role from page.tsx usage) — read them before copying card/hero layout
  specifics if `/kudos` needs a similar card grid.
- Did not confirm whether `docs/features/F003_AwardSystem/technical-spec.md`
  or `docs/screens/SCR003_AwardSystem/spec.md` contain reusable
  conventions doc (found but not opened) — check if a written "conventions"
  doc exists there before assuming this report is the only source.
- Did not check if a Kudos-specific MoMorph screenId/fileKey exists yet —
  `app/kudos/page.tsx` is still the declared placeholder; no F00x spec for
  Kudos was found under `docs/features/`.
