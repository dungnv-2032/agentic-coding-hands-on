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
      testMatch: /^((?!homepage).)*auth\.setup\.ts$/,
      use: { ...devices["Desktop Chrome"] },
    },
    // Homepage auth setup — creates independent session for homepage-authed tests
    {
      name: "homepage-auth-setup",
      testMatch: /homepage-auth\.setup\.ts$/,
      use: { ...devices["Desktop Chrome"] },
    },
    // Unauthenticated tests (login screen, error paths, open-redirect, callback security, homepage)
    {
      name: "anon",
      testMatch:
        /(?:smoke|login-screen|route-guard|callback-security|homepage|award-system)\.spec\.ts/,
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
    // Visual capture project — runs on demand only, not in default suite
    {
      name: "visual-capture",
      testMatch: /capture-homepage-visual\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
      dependencies: ["homepage-auth-setup"],
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
