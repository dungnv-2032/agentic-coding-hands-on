---
name: authenticated-visual-capture
description: How to capture authenticated screenshots/computed styles in this repo — the shipped visual-capture project only covers the homepage, so use a throwaway config plus an existing e2e/.auth session
metadata:
  type: project
---

Browser/visual evidence for an authenticated screen is captured with a **throwaway Playwright
config outside `e2e/`**, reusing a session file another suite's setup project already wrote
(`e2e/.auth/profile-user.json`, `kudos-user.json`, `homepage-user.json`).

**Why:** `playwright.config.ts` ships exactly one `visual-capture` project and it is wired to
`capture-homepage-visual.spec.ts`. Adding a durable capture spec for every screen would put
non-test files in `e2e/` that no suite runs, and phase-scoped agents usually do not own that
directory anyway. A throwaway config keeps the capture reproducible without leaving anything behind.

**How to apply:**
- Put the config + spec in a scratch dir, set `use.storageState` to the absolute path of the
  `e2e/.auth/*.json` you want, and give it its own `webServer` block copied from
  `playwright.config.ts` (including the `NEXT_PUBLIC_EVENT_START_AT` pin — `reuseExistingServer` is
  `false`, so it starts its own dev server).
- A spec **outside the repo tree cannot resolve `@playwright/test`**. Symlink the repo's
  `node_modules` into the scratch dir, or keep the probe inside the repo and delete it after.
- Park the pointer (`page.mouse.move(2, 2)`) and blur the active element before every shot, or a
  stray hover/focus state ends up in the "reference" capture.
- Read tokens with `getComputedStyle` on the element you actually mean. Measuring a `<button>` when
  the frame's type spec belongs to its label `<span>` produces a false discrepancy — this cost one
  wasted round trip on the F006 Secret Box button.
- Every full-page screenshot from `npm run dev` carries Next's dev indicator disc in the
  bottom-left. It is not application UI; say so rather than reporting it.
