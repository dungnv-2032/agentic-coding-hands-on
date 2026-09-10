import { existsSync } from "node:fs";
import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

// WSL2 dev machines frequently lack system shared libraries headless Chromium
// needs (libnspr4, libnss3, libasound2) and `playwright install --with-deps`
// requires interactive root, which is unavailable in this environment. As a
// documented, gitignored, machine-local workaround, the missing libs are
// vendored (via `dpkg-deb -x`, no root needed) under `.playwright-libs/`. If
// that directory is absent (e.g. a machine with the system libs already
// installed, or CI with `--with-deps`), this is a no-op.
const vendoredLibs = path.join(
  __dirname,
  ".playwright-libs/usr/lib/x86_64-linux-gnu",
);
if (existsSync(vendoredLibs)) {
  process.env.LD_LIBRARY_PATH = [vendoredLibs, process.env.LD_LIBRARY_PATH]
    .filter(Boolean)
    .join(":");
}

// Cookie domain must be pinned to 127.0.0.1 everywhere (site_url,
// NEXT_PUBLIC_SITE_URL, this baseURL, and the dev server --hostname below) —
// a session cookie captured for 127.0.0.1 is not sent to localhost.

// ORCH-01/ORCH-07: Pin NEXT_PUBLIC_EVENT_START_AT to a deterministic future date
// for the E2E suite to exercise the live-countdown state. The default in .env.example
// is 2025-12-26 (the real event date, now in the past), so the homepage would render
// 00/00/00 with "Coming soon" hidden. This pin satisfies:
// - 0 < target - now < 100 days (three-digit day would break ID-12/39/40)
// - Pinned via webServer.env so NEXT_PUBLIC_* is inlined correctly
// - reuseExistingServer: false ensures the env is read on every run
const now = new Date();
const futureEventTime = new Date(now.getTime() + 45 * 24 * 60 * 60 * 1000); // 45 days in future
const eventTimeISO = futureEventTime.toISOString().split("T")[0] + "T18:30:00+07:00";

export default defineConfig({
  testDir: "e2e",
  reporter: "list",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  projects: [
    // Setup project — runs auth.setup.ts once before tests
    {
      name: "setup",
      // Excludes the per-suite setups (homepage-auth.setup.ts, kudos-auth.setup.ts, profile-auth.setup.ts)
      // so each runs only in its OWN setup project, not twice.
      testMatch: /^((?!homepage)(?!kudos)(?!profile).)*auth\.setup\.ts$/,
      use: { ...devices["Desktop Chrome"] },
    },
    // Homepage auth setup — creates independent session for homepage-authed tests
    {
      name: "homepage-auth-setup",
      testMatch: /homepage-auth\.setup\.ts$/,
      use: { ...devices["Desktop Chrome"] },
    },
    // Kudos auth setup — independent session for the kudos-authed project, for the
    // same reason homepage has one: authenticated.spec.ts's C9 signs out globally
    // and revokes any session it shares.
    {
      name: "kudos-auth-setup",
      testMatch: /kudos-auth\.setup\.ts$/,
      use: { ...devices["Desktop Chrome"] },
    },
    // Profile auth setup — creates independent session for profile-authed tests
    // for the same reason kudos and homepage have one: authenticated.spec.ts's C9
    // signs out globally and revokes any session it shares.
    {
      name: "profile-auth-setup",
      testMatch: /profile-auth\.setup\.ts$/,
      use: { ...devices["Desktop Chrome"] },
    },
    // Unauthenticated tests (login screen, error paths, open-redirect, callback security, homepage)
    // NOTE: kudos-live-board.spec.ts only (not -authed variant), profile-anon.spec.ts for route guards
    {
      name: "anon",
      testMatch:
        /(?:smoke|login-screen|route-guard|callback-security|homepage|award-system|profile-anon|the-le|floating-action-button|kudos-live-board(?!-authed))\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
      dependencies: ["setup"],
    },
    // Authenticated tests (route guard authed, sign-out) — loads storageState from setup
    // NOTE: homepage-authed.spec.ts runs in its own project with its own session to avoid
    // being affected by authenticated.spec.ts's C9 global sign-out test.
    {
      name: "authed",
      testMatch: /authenticated\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        storageState: "e2e/.auth/user.json",
      },
      dependencies: ["setup"],
    },
    // Kudos authenticated tests (heart toggle, persistence, compose screen) — loads storageState from setup
    // NOTE: kudos-live-board-authed.spec.ts and viet-kudo.spec.ts
    {
      name: "kudos-authed",
      testMatch: /(kudos-live-board-authed|viet-kudo)\.spec\.ts/,
      // 15s instead of the 5s default, scoped to THIS project only. These are
      // the only tests that wait on a server-authoritative Postgres round trip
      // (the heart toggle is deliberately not optimistic — see
      // `kudos-card-actions.tsx`), and under multi-file contention that round
      // trip can exceed 5s. Raising it globally would triple how long every
      // failing assertion takes to fail everywhere else, which matters: a full
      // RED run of the compose suite already takes ~25 minutes.
      expect: { timeout: 15_000 },
      use: {
        ...devices["Desktop Chrome"],
        storageState: "e2e/.auth/kudos-user.json",
      },
      dependencies: ["kudos-auth-setup"],
    },
    // Homepage authenticated tests — independent session, isolated from C9 sign-out
    {
      name: "homepage-authed",
      testMatch: /homepage-authed\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        storageState: "e2e/.auth/homepage-user.json",
      },
      dependencies: ["homepage-auth-setup"],
    },
    // Profile authenticated tests — independent session, isolated from C9 sign-out
    {
      name: "profile-authed",
      testMatch: /profile\.spec\.ts/,
      // 15s instead of the 5s default, scoped to THIS project only. The heart toggle
      // is server-authoritative and under multi-file contention can exceed 5s.
      expect: { timeout: 15_000 },
      use: {
        ...devices["Desktop Chrome"],
        storageState: "e2e/.auth/profile-user.json",
      },
      dependencies: ["profile-auth-setup"],
    },
    // Visual capture project — runs on demand only, not in default suite
    {
      name: "visual-capture",
      testMatch: /capture-homepage-visual\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
      dependencies: ["homepage-auth-setup"],
    },
    // FAB visual capture project — runs on demand only, not in default suite
    {
      name: "fab-visual-capture",
      testMatch: /capture-fab-visual\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: false,
    timeout: 120_000,
    env: {
      NEXT_PUBLIC_EVENT_START_AT: eventTimeISO,
    },
  },
});
