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
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
