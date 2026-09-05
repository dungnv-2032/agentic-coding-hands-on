---
feature: F002 · test_policy: e2e-red-first · owner: momorph-ui-implementer
fileKey: 9ypp4enmFmdK3YAFJLIu6C · screenId: i87tDx10uM · depends_on: [04, 05] · status: completed · effort: 3h
completed: 2026-09-05
---
# Phase 06 — Track A: body sections, footer, widget, page assembly
## MoMorph refs:
- Homepage SAA: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/i87tDx10uM
- Clarifications: plans/260905-1153-homepage-saa/clarifications.md
- testPolicy: e2e-red-first

**Goal:** render R3-R7 (Root Further block, awards grid, Sun* Kudos promo, floating widget, footer) and assemble `/`, replacing the create-next-app boilerplate. Delivers FR-203, FR-204, FR-205, FR-206, FR-207, FR-405 and the A1 render path.

**Owns (only):** `app/page.tsx`, `app/layout.tsx`, `app/_fonts.ts`, `app/_page-context.ts`, `app/globals.css`, `app/_components/{root-further-block,awards-grid,award-card,kudos-promo,floating-widget,site-footer}.tsx`.
**Out of scope:** header/hero/countdown files (04, 05 — compose them, never edit), `lib/**` (02), `public/images/home/**` (03), `proxy.ts` and `lib/supabase/**` (nobody), `app/login/**`, `e2e/**` (08).
**Contract:** `app/_page-context.ts` exports `getPageContext(): Promise<{ locale, dictionary, isAuthenticated, isAdmin }>` — `await cookies()` → `resolveLocale` → `getDictionary`, plus `createClient()` → `auth.getUser()` → `isAdmin = user.app_metadata?.role === "admin"`. `app/page.tsx` and phase 07's placeholder pages both call it, and **only** the two booleans reach `HomeHeader`; the user object never crosses into a Client Component. `app/_fonts.ts` exports the shared Montserrat / Montserrat Alternates instances (`next/font/google`, `--font-montserrat*` already wired in `globals.css`); `/login` keeps its own declaration — do not refactor it.

**Must hold (the RED suite locates by these):**
- Sections are siblings, never nested: exactly one `<section>` contains "Hệ thống giải thưởng" (ID-7 uses `section:has-text`), and the awards section contains no "Kudos" text while the hero section contains no "Chi tiết" link (ID-53 scopes by `section:has-text(/kudos/i)`).
- Awards grid: container `data-testid="awards-grid"`, exactly six elements with `data-testid="award-card"`, each wrapping one `<Link data-testid="award-card-<slug>" href="/awards-information#<slug>">` that covers image, title and "Chi tiết" — one element cannot hold two testids, so the generic id sits on the outer card and the slug id on the inner link (FR-405, ID-47/48/49/50/52).
- Grid columns: 3 at ≥1024px, 2 below (clarifications overrides spec item C2). Card description clamps to 2 lines with an ellipsis (C2.1.3).
- Footer is the `contentinfo` landmark and carries at least one `<img>`, links named `About SAA 2025` (→ `/`), `Award Information`, `Sun* Kudos`, `Tiêu chuẩn chung` (→ `/standards`) with one match each inside the footer, and `footer.copyright`. No `href="#"` placeholders — ID-55/59 walks every footer link for a non-4xx response.
- Floating widget is fixed, overlays R4-R6, and holds two links (`/kudos`, `/standards`) split by the `/` glyph — no menu (clarifications). Its accessible names must not collide with the hero's `ABOUT KUDOS` button.
- `ROOT`/`FURTHER` watermarks are images from phase 03; body prose comes from `dictionary.home.rootFurther.paragraphs`.
- `app/layout.tsx`: replace the `Create Next App` metadata with the homepage title/description. `globals.css` is expected to stay untouched — the dark page background belongs on the page root, as `/login` does it.
- Split before growing: one component per section, every file under 200 lines. All visual values from MoMorph.

**Done:** `npm run build` succeeds, typecheck + lint clean, `/` renders all seven regions in design order, ID-7/9/15/16/17/25/26/53/55/59 pass at phase 08.
**Rollback:** `git checkout -- app/page.tsx app/layout.tsx app/globals.css` and delete the six components plus `app/_fonts.ts`.
