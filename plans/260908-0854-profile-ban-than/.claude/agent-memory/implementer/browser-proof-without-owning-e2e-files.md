---
name: browser-proof-without-owning-e2e-files
description: How to get real browser evidence for behaviour whose e2e file another phase owns — a throwaway Playwright config under a repo-local .probe-tmp/, run with --config, then deleted
metadata:
  type: project
---

Phase-scoped ownership regularly forbids editing (or adding to) `e2e/**` while still demanding
"prove it works end to end". The way that works here:

1. Put BOTH the config and the specs under a repo-local `.probe-tmp/` — **not** the scratchpad. A
   config outside the repo cannot resolve `@playwright/test` and dies with `MODULE_NOT_FOUND`
   before it ever reads `testDir` (measured in F006 phase 09).
2. Copy `playwright.config.ts`'s `.playwright-libs` `LD_LIBRARY_PATH` block into the probe config,
   set `webServer.cwd` to the repo root (it defaults to the config's directory), and reuse the
   project's `storageState` files (`e2e/.auth/*.json`) for an authenticated probe.
3. Set an explicit `testMatch` — the default only matches `*.spec.ts`, so a `*.probe.ts` file
   yields the misleading `Error: No tests found`.
4. Run with `npx playwright test --config=.probe-tmp/probe.config.ts --project=…`, then
   `rm -rf .probe-tmp test-results` and confirm `git status` shows no trace.
5. Save the transcript AND the probe source under `evidence/` as `.log`, same reason as
   [[proving-code-without-a-unit-runner]] step 5.

**Why:** it satisfies RED-first for a change whose only durable test belongs to another phase (the
probe was run against the unchanged code first and captured failing), and it keeps a genuinely
end-to-end claim — clicking the real element, following the real navigation, reading the real
server-action response body — out of the owner's test file.

**How to apply:** reach for it when a verification list says "prove X works end to end" and X's
spec file is on the do-not-touch list. Assert observable STATE, not just the URL: F006's whole
hashtag-deep-link risk was a URL-only assertion passing on an unfiltered board.
