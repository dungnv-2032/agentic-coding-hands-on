import { test as setup } from "@playwright/test";
import { createTestSession } from "./fixtures/supabase-session";
import { ensureSunner } from "./fixtures/secret-box-grant";
import fs from "node:fs";
import path from "node:path";

const authFile = "e2e/.auth/secret-box-user.json";
const credentialsFile = "e2e/.auth/secret-box-credentials.json";

/**
 * SECRET BOX AUTHENTICATED SESSION SETUP
 *
 * The secret-box test suite needs its own independent Supabase session,
 * isolated from authenticated.spec.ts's global sign-out (C9).
 *
 * This setup:
 * 1. Creates a fresh test user via createTestSession()
 * 2. Ensures the user has a sunners row (via ensureSunner)
 * 3. Saves the storageState to e2e/.auth/secret-box-user.json
 * 4. Saves credentials to e2e/.auth/secret-box-credentials.json for direct API calls
 */
setup("secret-box: create independent session", async () => {
  // Create a fresh test session
  const { cookies, email, userId } = await createTestSession();

  // Verify at least one auth token cookie was captured
  const authTokenCookie = cookies.find((c) =>
    c.name.endsWith("-auth-token"),
  );
  if (!authTokenCookie) {
    throw new Error(
      "No -auth-token cookie found in captured cookies. This indicates a problem with the Supabase fixture.",
    );
  }

  // Ensure the user has a sunners row (grants nothing — just sets up the infrastructure)
  const sunnerId = await ensureSunner(userId);

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

  // Write credentials for direct API calls (no secrets in the file — just the email and userId)
  fs.writeFileSync(
    credentialsFile,
    JSON.stringify(
      {
        email,
        password: "Test123456!",
        userId,
        sunnerId,
      },
      null,
      2,
    ),
  );

  console.log(`✓ Secret Box session created and saved to ${authFile}`);
  console.log(`  Test user email: ${email}`);
  console.log(`  Test user ID: ${userId}`);
  console.log(`  Sunner ID: ${sunnerId}`);
  console.log(`  Auth token cookie: ${authTokenCookie.name}`);
});
