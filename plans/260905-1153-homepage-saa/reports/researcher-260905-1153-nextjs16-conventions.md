# Next.js 16.3.4 conventions for `app/page.tsx` marketing homepage

Source: local docs only, `node_modules/next/dist/docs/01-app/`. Confirmed against actual project files (`app/layout.tsx`, `app/page.tsx`, `app/login/_components/login-header.tsx`, `app/globals.css`).

## 1. `page.tsx` / `layout.tsx` signatures

`01-app/03-api-reference/03-file-conventions/page.md`, `.../layout.md`, `01-app/01-getting-started/03-layouts-and-pages.md`

- Both `params` and `searchParams` are **Promises** since v15.0.0-RC (must `await`).
- Global typed helpers `PageProps<'/route'>` and `LayoutProps<'/route'>` are auto-generated (`next dev`/`build`/`next typegen`) — **no import needed**, already used in this repo's `app/layout.tsx`: `RootLayout({ children }: LayoutProps<"/">)`.
- **Page with no params** (our case, static homepage at `/`):
  ```tsx
  export default function Page() {
    return <h1>Hello Next.js!</h1>
  }
  ```
  Or, using the helper (static routes resolve `params` to `{}`):
  ```tsx
  export default async function Page(props: PageProps<'/'>) {
    return <h1>Hello</h1>
  }
  ```
- **Page with `searchParams`** (not needed for a static marketing page, but for reference):
  ```tsx
  export default async function Page({
    searchParams,
  }: {
    searchParams: Promise<{ [key: string]: string | string[] | undefined }>
  }) {
    const filters = (await searchParams).filters
  }
  ```
  Using `searchParams` forces dynamic rendering — avoid it on a static homepage.
- Layout must accept `children`; root layout must render `<html>`/`<body>` (already correct in `app/layout.tsx`).

## 2. `next/image`

`01-app/03-api-reference/02-components/image.md`, `01-app/01-getting-started/12-images.md`

- Required: `src`, `alt`. `width`/`height` required unless static import or `fill`.
- **`preload` (new in v16, replaces `priority`)**: `preload={true}` inserts a `<link>` preload in `<head>`. Use for the LCP/hero/above-fold image only.
- **`priority` is DEPRECATED as of v16** in favor of `preload` — "in order to make the behavior clear" (image.md line 291-293).
  - **Finding**: `app/page.tsx` (current starter code) still uses `priority` on the Next.js logo `<Image>` — this is deprecated and should become `preload` when the homepage is rebuilt.
  - `app/login/_components/login-header.tsx` already correctly uses `preload` (no `priority`) — follow that pattern.
- `fill`: boolean, image expands to fill positioned parent (`position: relative/fixed/absolute` required on parent); use `sizes` alongside `fill`.
- `sizes`: use when `fill` or responsive CSS is applied; omitting it defaults browser assumption to `100vw` (over-fetches).
- Local `/public` images: reference by root-relative path, e.g. `src="/images/hero.png"` — matches `login-header.tsx`'s `src="/images/login/saa-logo.png"`. No import required (static `import` is also supported and gives automatic width/height/blurDataURL).
- `quality` default is `75`; **v16 requires `qualities` array configured in `next.config.js`** if you use non-default quality values — unconfigured values are coerced to the nearest allowed one (breaking change vs pre-16).
- Deprecated: `onLoadingComplete` (use `onLoad`), `domains` config (use `remotePatterns`).

## 3. `next/font` (Google fonts) + Tailwind v4

`01-app/03-api-reference/02-components/font.md`, `01-app/01-getting-started/13-fonts.md`

- Declare once, top-level, per font:
  ```tsx
  import { Geist } from 'next/font/google'
  const geistSans = Geist({ subsets: ['latin'], variable: '--font-geist-sans' })
  ```
- Project already does this correctly in `app/layout.tsx` (`Geist`, `Geist_Mono` with `variable`).
- `variable` option declares a CSS custom property name; apply `.variable` class(es) on `<html>` or `<body>`.
- Tailwind v4 wiring — bridge the CSS var into Tailwind's theme via `@theme inline` in `globals.css` (already set up in this project):
  ```css
  @import "tailwindcss";
  @theme inline {
    --font-sans: var(--font-geist-sans);
    --font-mono: var(--font-geist-mono);
  }
  ```
  Project's `globals.css` already extends this pattern with `--font-montserrat` / `--font-montserrat-alternates` — reuse the same convention for any new homepage font, don't invent a parallel mechanism.
- Preloading is scoped: a font called in a unique page preloads only on that route; called in root layout it preloads everywhere.

## 4. Server vs Client Components

`01-app/01-getting-started/05-server-and-client-components.md`, `01-app/02-guides/server-and-client-boundary.md`, `01-app/03-api-reference/01-directives/use-client.md`, `01-app/03-api-reference/04-functions/cookies.md`

- Pages/layouts are Server Components **by default**. Only add `"use client"` at the top of a file (before imports) for the specific interactive leaf (e.g. a client-side dropdown/carousel), not the whole page — reduces client JS.
- Passing props Server→Client: props must be serializable (no functions/event handlers, except a `"use server"` Server Function reference). Passing rendered Server Component output as `children`/other props into a Client Component works (interleaving pattern) and keeps the Server Component's code out of the client bundle.
- `cookies()` from `next/headers` is an **async function** — `await cookies()` — since v15.0.0-RC. Calling it in a layout/page opts the route into dynamic rendering. Layouts cannot access the raw request otherwise (no `headers`/`cookies` without going async); a Suspense boundary is needed if isolating dynamic reads from a static shell.
- For a static marketing homepage: keep `page.tsx`/`layout.tsx` as Server Components, no `cookies()`/`searchParams` usage, to stay statically prerenderable.

## 5. Environment variables

`01-app/02-guides/environment-variables.md`

- `.env*` values load into `process.env` automatically; only `NEXT_PUBLIC_`-prefixed vars are inlined into the client bundle at **build time** (`next build`) — non-prefixed vars are server-only and become empty string if referenced from client code.
- Reading in a Server Component: `process.env.MY_VAR` directly works at build/render time. For a **runtime** (not build-time-frozen) read, must opt into dynamic rendering first via `await connection()` from `next/server` (otherwise the value gets baked in during static prerender).
- Dynamic property lookups (`process.env[varName]`) are **not** statically inlined — must use literal `process.env.NEXT_PUBLIC_X`.
- For a static homepage with no personalization, plain `process.env.X` reads in a Server Component are fine and get resolved at build time.

## 6. `next/link`

`01-app/03-api-reference/02-components/link.md`

- `<Link href="/path">` — no wrapping `<a>` needed since v13.
- Hash anchors work natively: `<Link href="/dashboard#settings">` renders `<a href="/dashboard#settings">`; disable scroll-to-top with `scroll={false}`.
- `prefetch` prop: default `"auto"`/`null` — full route prefetched if static, partial if dynamic (only in production builds). Cross-references `transitionTypes` (new in v16.2.0) for `<ViewTransition>` animation hints — not required for a plain marketing page.
- `onNavigate` (v15.3.0+) fires only on client-side same-origin nav — distinct from `onClick`.
- No breaking changes to basic `href` handling for internal nav; the `as`/`shallow` props are Pages-Router-only (not relevant here, App Router project).

## 7. Metadata API

`01-app/01-getting-started/14-metadata-and-og-images.md`, `01-app/03-api-reference/04-functions/generate-metadata.md`

- Static metadata: export a `Metadata`-typed const from `page.tsx` or `layout.tsx` (Server Components only):
  ```tsx
  import type { Metadata } from 'next'
  export const metadata: Metadata = {
    title: 'Page Title',
    description: '...',
  }
  ```
- Already used correctly in `app/layout.tsx` (`title: "Create Next App"` — replace with real homepage copy).
- Metadata from ancestor layout + page is shallow-merged; nested objects (`openGraph`, `robots`) from a child **fully replace** the parent's, not deep-merge — pull shared nested fields into a separate exported const if reuse is needed.
- `themeColor`, `colorScheme`, `viewport` metadata fields are deprecated since v14 — use the separate `generateViewport` export instead (not covered in depth here, out of scope for a basic marketing page).
- `generateMetadata` (dynamic) not needed for a static homepage — use the plain `metadata` object.

## 8. Deprecation notices touching the above

| Item | Status | Doc |
|---|---|---|
| `priority` prop on `next/image` | Deprecated in v16.0.0, use `preload` | `image.md` |
| `onLoadingComplete` on `next/image` | Deprecated in v14 | `image.md` |
| `domains` config on `next/image` | Deprecated since v14 | `image.md` |
| `themeColor`/`colorScheme`/`viewport` in `metadata` object | Deprecated since v14 | `generate-metadata.md` |
| Synchronous `params`/`searchParams`/`cookies()` access | Still works but "will be deprecated in the future" (compat shim from pre-v15) | `page.md`, `layout.md`, `cookies.md` |
| `qualities` unrestricted access on `next/image` | Now **required allowlist** starting v16 (breaking, not deprecation) | `image.md` |

## Unresolved / out of scope

- Did not read `04-functions/generate-viewport.md` (theme-color/viewport metadata) — flag if homepage needs a custom theme-color meta tag.
- Did not verify Cache Components / PPR config state for this project (`next.config.ts` not inspected) — relevant only if the homepage later adds dynamic data.

**Status:** DONE
**Summary:** Read all 8 requested Next.js 16.3.4 doc areas directly from `node_modules/next/dist/docs/01-app/`, cross-checked against this repo's existing `app/layout.tsx`/`app/page.tsx`/`login-header.tsx`; found one live deprecation violation (`priority` prop still used in `app/page.tsx`, should be `preload`) to fix when rebuilding the homepage.
