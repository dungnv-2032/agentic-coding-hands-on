---
phase: 04
owner: momorph-ui-implementer
mode: screen
testPolicy: e2e-red-first
---

# Phase 04 — Track A: /login screen UI

## Design evidence (real MCP calls, this session)

- `get_node(GzbNeVGJHz, 662:14387)` — root frame size/bg
- `query_section(662:14391, depth 6)` — header + language selector full subtree
- `query_section(662:14755, depth 6)` — intro text + login button subtree
- `query_section(662:14447, depth 4)` — footer
- `get_node(662:14390)`, `get_node(662:14392)` — the two gradient overlay rectangles
- `query_section(662:14393, depth 3)` — content wrapper / Frame 487 / key-visual positions
- `get_node(662:14395)` — key-visual frame wrapping the wordmark
- `get_figma_image(fileKey, ["662:14389"], png)` — **the one permitted retry** of the hero
  render endpoint (see below)
- Plus the pre-supplied `design/design-notes.md`, `design/specs.csv`,
  `design/test-cases.csv`, `design/login-screen.png` (read as image) and
  `spec/login/screens/SCR-login/spec.md`.

All colors, spacing, font sizes/weights, border-radius and gradient stops in the
components below are copied verbatim from these calls — none guessed.

## Components created (all under `app/login/`)

| File | Design node(s) | Notes |
|---|---|---|
| `page.tsx` | `662:14387` (root) | Server Component. Reads `NEXT_LOCALE` via `await cookies()`, `error` via `PageProps<'/login'>`, loads `Montserrat`/`Montserrat_Alternates` via `next/font/google`, composes the 4 regions. |
| `_components/hero-background.tsx` | `662:14389`, `662:14392`, `662:14390` | Full-bleed hero layer + the two decorative gradient rectangles (header-side readability scrim and bottom/footer scrim). |
| `_components/login-header.tsx` | `662:14391` | Logo (non-interactive, `next/image`) + `LanguageSelector`. `justify-between` keeps logo left / selector right at any width. |
| `_components/language-selector.tsx` | `I662:14391;186:1696` subtree | Client component. `role="listbox"`/`role="option"` dropdown, Escape + outside-click to close, defaults to VN. Calls the `setLocale` Server Action via `startTransition`. |
| `_components/icons.tsx` | `MM_MEDIA_VN`, `MM_MEDIA_Down`, `MM_MEDIA_Google` | Inlined SVGs per code-rules 2a. Chevron converted to `currentColor` (was hardcoded white, mono icon); flag and Google "G" keep their original multi-color palettes. |
| `_components/login-content.tsx` | `662:14393`/`662:14755` | ROOT FURTHER wordmark image, subtitle+tagline text, conditional `ErrorBanner`, and the `<form action={signInWithGoogle}>` wrapping `GoogleSignInButton`. |
| `_components/error-banner.tsx` | DEC-001 (no dedicated node) | `role="alert"` + explicit `aria-live="assertive"`, rendered only when `?error` is present. |
| `_components/google-sign-in-button.tsx` | `662:14426` | Client component; `useFormStatus()` drives disabled+loader (SM-001) and `hover:shadow-lg`. Google icon sits right of the label per design-notes.md's correction. |
| `_components/login-footer.tsx` | `662:14447` | Top-level `<footer>` (kept as a direct sibling of `<main>`, not nested inside it) so it keeps the `contentinfo` landmark role. |

`app/globals.css`: added `--font-montserrat` / `--font-montserrat-alternates` theme
vars alongside the existing Geist vars (same pattern), nothing else touched.

All 9 files are 20–114 lines — the phase's 200-line ceiling was never close.

## `next/image` — `preload`, not `priority`

Confirmed via `node_modules/next/dist/docs/01-app/03-api-reference/02-components/image.md`
(v16.0.0 changelog: "`priority` prop deprecated" in favor of `preload`). Both
`next/image` usages — the header logo and the ROOT FURTHER wordmark — use
`preload` (boolean) and explicit `width`/`height` (52×48, 451×200) since both
are string `src` paths. `priority` does not appear anywhere in the diff.

## Hero layer (RISK-01 / ORCH-05)

Retried `get_figma_image(fileKey, ["662:14389"], "png")` once this session —
**still HTTP 500**, consistent with design-notes.md's diagnosis that the
render endpoint is down service-wide, not rejecting this node specifically. I
did not retry again per the phase's "retry once" instruction and the
coordinator's note that it has been down all session.

Implemented per the frozen decision: `hero-background.tsx` renders an
absolutely-positioned `1441×1022` layer at `top: 2px; left: 0` with
`background-color: #00101A` (the root frame's own fallback color, from
`get_node(662:14387)`) plus `background-image: url(/images/login/hero.png)`
at the recorded `background-position: -440px -217.975px` /
`background-size: 159.763% 133.371%` / `no-repeat`. Since `background-image`
paints over `background-color` only once it resolves, the navy fallback shows
today and dropping `hero.png` into `public/images/login/` later requires
touching zero code — confirmed this is genuinely a file-drop, not a
config/path change, since the URL is already wired to that exact path.

## Accessibility note (addressed per coordinator's flag)

Checked every interactive element in this screen against the "no English
`aria-label` masking localized visible text" rule the coordinator raised for
`/todo`'s sign-out button:

- **Language selector trigger**: `aria-label={`${labels.language}: ${currentLabel}`}`
  — e.g. `"Ngôn ngữ: VN"` in the default locale. `labels.language` is the
  *localized* dictionary string (`login.languageLabel` — "Ngôn ngữ" / "Language"),
  and `currentLabel` is exactly the visible child text ("VN"/"EN" — these two
  are literal brand abbreviations, identical in both locales in the
  dictionary, not translated words). So the accessible name is fully
  localized **and** contains the visible label verbatim in both locales —
  compliant with WCAG 2.5.3, not the mismatch pattern flagged on `/todo`.
- **Dropdown options, Google sign-in button, logo/wordmark alt text**: no
  `aria-label` overrides anywhere — accessible name comes straight from
  visible text/localized dictionary strings.

No changes needed on my side; flagging this explicitly in case a future pass
wants to simplify the trigger's aria-label to just `currentLabel` (it isn't
required to be more verbose than that).

## Checks

- `npx next typegen && npx tsc --noEmit` — clean, exit 0.
- `npm run lint` — clean, exit 0.
- `npm run test:e2e` (full suite, after Track B/05 landed) — **12/12 passed**,
  including C1–C5 (this screen's cases) and C6–C10 (route guard / auth /
  callback, owned by Track B, unaffected by this work).
- Asset coverage: all `mm_media_*` nodes in the assigned subtree
  (`MM_MEDIA_Logo`, `MM_MEDIA_VN`, `MM_MEDIA_Down`, `MM_MEDIA_Root Further Logo`,
  `MM_MEDIA_Google`) are rendered from the pre-downloaded files in
  `public/images/login/`; the one node with no exportable asset (`662:14389`,
  the hero artwork) is handled per RISK-01 above.

## Deviations from a literal 1:1 reading of the spec (all pre-resolved, not new calls)

- Google icon right of the label, not left — design-notes.md's correction over
  the spec CSV's `buttonType: icon_text`.
- Login button left-aligned with the description column, not centered — same
  file's correction over test case `6ae76d15`.
- "ROOT FURTHER" rendered as `next/image`, never text/webfont.
- Logo and footer are plain non-interactive elements (no button/link wrapper).

## Concerns

- None blocking. The screen does not implement a separate responsive
  breakpoint pass (the plan's phase list has no dedicated polish phase; the
  task's only responsive requirement — logo top-left / selector top-right at
  every width — is satisfied structurally via `justify-between` and verified
  visually at phase 06 by the tester).
- RISK-01 stays open (hero artwork still not exportable) — no action needed
  from Track A once the real file is dropped in.

**Status:** DONE
**Summary:** `/login` is implemented across 9 files under `app/login/`, all faithful to MoMorph node data (colors/spacing/typography queried live, not guessed), with the hero built on the agreed dark-navy-fallback contract (RISK-01/ORCH-05) and the frozen Track B contract imported cleanly. `npx tsc --noEmit` and `npm run lint` are clean; the full `npm run test:e2e` suite is 12/12 green including this screen's C1–C5.
**Concerns/Blockers:** none.
