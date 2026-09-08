import { test as setup } from "@playwright/test";
import { createTestSession } from "./fixtures/supabase-session";
import { PROFILE_SESSION_META_FILE } from "./fixtures/profile-constants";
import fs from "node:fs";
import path from "node:path";

const authFile = "e2e/.auth/profile-user.json";

/**
 * PROFILE AUTHENTICATED SESSION SETUP
 *
 * The profile-authed test suite (profile.spec.ts) must have its own independent Supabase session,
 * isolated from the shared `e2e/.auth/user.json` used by authenticated.spec.ts.
 *
 * Root cause: authenticated.spec.ts's C9 test calls signOut() with default
 * scope:'global', which revokes the ONE shared session for every test in the
 * authed project. Under worker concurrency, profile-authed tests fail
 * nondeterministically depending on whether their page-load happens before or
 * after C9's revocation. This setup creates a separate, fresh session that C9
 * cannot touch, giving profile-authed tests session isolation and deterministic
 * pass/fail.
 *
 * See: plans/260907-0822-viet-kudo/reports/orchestrator-k25-root-cause.md
 */
setup("profile: create independent session", async () => {
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

  // The sparse self profile (clarifications A4: signed in, no `sunners` row)
  // renders the JWT identity fallback `lib/profile/profile-data.ts` copies from
  // `create_kudos()` — `user_metadata.full_name` -> `.name` -> the email
  // LOCAL-PART. A signUp through `createTestSession()` sets no metadata, so the
  // local-part is what the hero's <h1> must read. Written to a SIDECAR rather
  // than into `authFile`, which Playwright parses as storageState and must keep
  // its exact shape. The address itself is recorded because the local-part is
  // derived from it; both are gitignored with the rest of `e2e/.auth/`, and no
  // test ever asserts the full address is ON the page (SEC_004 asserts the
  // opposite).
  fs.writeFileSync(
    PROFILE_SESSION_META_FILE,
    JSON.stringify({ email, emailLocalPart: email.split("@")[0] }, null, 2),
  );

  console.log(`✓ Profile session created and saved to ${authFile}`);
  console.log(`  Test user email: ${email}`);
  console.log(`  Auth token cookie: ${authTokenCookie.name}`);
});
