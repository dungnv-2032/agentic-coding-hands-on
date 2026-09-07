import { test as setup } from "@playwright/test";
import { createTestSession } from "./fixtures/supabase-session";
import fs from "node:fs";
import path from "node:path";

const authFile = "e2e/.auth/kudos-user.json";

/**
 * KUDOS AUTHENTICATED SESSION SETUP
 *
 * The kudos-authed test suite (kudos-live-board-authed.spec.ts + viet-kudo.spec.ts) must have its own independent Supabase session,
 * isolated from the shared `e2e/.auth/user.json` used by authenticated.spec.ts.
 *
 * Root cause: authenticated.spec.ts's C9 test calls signOut() with default
 * scope:'global', which revokes the ONE shared session for every test in the
 * authed project. Under worker concurrency, kudos-authed tests fail
 * nondeterministically depending on whether their page-load happens before or
 * after C9's revocation. This setup creates a separate, fresh session that C9
 * cannot touch, giving kudos-authed tests session isolation and deterministic
 * pass/fail.
 *
 * Same root cause, rediscovered for the kudos suites: they were wired to the
 * shared `e2e/.auth/user.json` and so passed when run alone but failed whenever
 * `authenticated.spec.ts` ran in the same invocation. K-25 in particular looked
 * like a load/timing flake for two commissions before this turned out to be a
 * revoked session, not a slow one.
 *
 * See: plans/260905-1153-homepage-saa/reports/debugger-260905-1353-authed-e2e-failures.md
 * and plans/260907-0822-viet-kudo/reports/orchestrator-k25-root-cause.md
 */
setup("kudos: create independent session", async () => {
  // Create a fresh test session (different user than auth.setup.ts creates)
  const { cookies, email } = await createTestSession();

  // Verify at least one auth token cookie was captured
  const authTokenCookie = cookies.find((c) =>
    c.name.endsWith("-auth-token"),
  );
  if (!authTokenCookie) {
    throw new Error(
      "No -auth-token cookie found in captured cookies. This indicates a problem with the Supabase fixture.",
    );
  }

  // Convert Supabase cookies to Playwright format
  // Domain must be 127.0.0.1 to match baseURL in playwright.config.ts
  const playwrightCookies = cookies.map((cookie) => ({
    name: cookie.name,
    value: cookie.value,
    domain: "127.0.0.1",
    path: "/",
    sameSite: "Lax" as const,
    secure: false,
    // Supabase session cookies expire in 3600s; give some buffer
    expires: Math.floor(Date.now() / 1000) + 3600,
  }));

  // Create the storage state object (Playwright's standard format)
  const storageState = {
    cookies: playwrightCookies,
    origins: [],
  };

  // Ensure directory exists
  const authDir = path.dirname(authFile);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  // Write storageState to file
  fs.writeFileSync(authFile, JSON.stringify(storageState, null, 2));

  console.log(`✓ Kudos session created and saved to ${authFile}`);
  console.log(`  Test user email: ${email}`);
  console.log(`  Auth token cookie: ${authTokenCookie.name}`);
});
