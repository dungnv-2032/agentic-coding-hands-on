---
feature: F002 · test_policy: e2e-red-first · owner: momorph-ui-implementer
fileKey: 9ypp4enmFmdK3YAFJLIu6C · screenId: i87tDx10uM · depends_on: [02, 03] · status: completed · effort: 1.5h
completed: 2026-09-05
---
# Phase 05 — Track A: hero and countdown
## MoMorph refs:
- Homepage SAA: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/i87tDx10uM
- Clarifications: plans/260905-1153-homepage-saa/clarifications.md
- testPolicy: e2e-red-first

**Goal:** render R2 — keyvisual background, `ROOT FURTHER` wordmark image, "Coming soon", the three countdown units, the event info block and the two CTAs. Delivers FR-202, FR-401, FR-402, BR-003, BR-004, ALG-001.

**Owns (only):** `app/_components/home-hero.tsx`, `app/_components/countdown-timer.tsx`.
**Out of scope:** `app/page.tsx` (06 passes `eventStartAt` in), header files (04), `lib/i18n/**` (02), `public/images/home/**` (03), `e2e/**` and `playwright.config.ts` (08).
**Contract:** `CountdownTimer({ eventStartAt?: string, labels })` — the page reads `process.env.NEXT_PUBLIC_EVENT_START_AT` as a literal and passes it down, so server and client see the same value.

**Must hold (the RED suite locates by these):**
- Exactly one element per unit carries `data-testid="countdown-value"`, and its **textContent is exactly two digits** — ID-12/39/40 test `/^\d{2}$/` on the raw string, untrimmed. Two digit tiles are fine as inner spans (textContent concatenates), but no whitespace, separator glyph or unit label may sit inside that element.
- Labels `DAYS`, `HOURS`, `MINUTES` are three separate elements, each the only text node matching its word.
- Ship the spelling **"Coming soon"** — the frame's "Comming soon" is a typo and ID-13/41 assert the corrected form.
- No hydration mismatch: the server renders `00`/`00`/`00` and renders the "Coming soon" label whenever the env value parses; the client's first render must produce the same markup, and only `useEffect` fills real values (clarifications, "tick cadence and hydration"). No `suppressHydrationWarning`.
- Tick: one `setInterval` at 1s recomputing the whole diff from `Date.now()` (never accumulating), cleared on unmount. `diff <= 0` → hold `00` and hide "Coming soon" (BR-003).
- Missing or unparseable `eventStartAt` → `00/00/00`, "Coming soon" hidden from the first paint, exactly one `console.warn`, never a throw (BR-004, ID-60).
- Event info copy comes from `dictionary.home.event*` — ID-14 asserts `26/12/2025`, `Âu Cơ Art Center` and the livestream line are all visible.
- The two CTAs must expose **`role="button"`** with accessible names `ABOUT AWARDS` / `ABOUT KUDOS` (ID-44/45 queries `getByRole("button")`) while still being real `next/link` navigations to `/awards-information` and `/kudos` — use `<Link role="button">`, not a router-push handler.
- Keyvisual and wordmark are images from phase 03's manifest with explicit width/height, `preload` on the hero image only. Every colour, size and offset from MoMorph; the hero background is never re-created as a CSS gradient.

**Done:** typecheck + lint clean, both files under 200 lines, ID-12/13/14/39/40/41/42/43/44/45 pass at phase 08.
**Rollback:** delete both files; only 06 imports them.
