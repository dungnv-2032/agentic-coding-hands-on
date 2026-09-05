import { test as setup, expect } from "@playwright/test";
import { chromium } from "@playwright/test";
import { createTestSession } from "./fixtures/supabase-session";
import fs from "node:fs";
import path from "node:path";

const authFile = "e2e/.auth/user.json";

/**
 * CLIENT BUNDLE WARMUP: Playwright's webServer config considers the server
 * ready when "/" responds (SSR is fast). However, client bundles for "/login"
 * and "/todo" are only compiled on-demand when a real browser first loads
 * them. The SSR HTML arrives ~474ms, but React hydration happens later — a
 * race condition that causes subsequent tests to interact with pre-hydration
 * markup (no event handlers attached), resulting in C3/C5 timeouts.
 *
 * This setup step warms the client bundles in a real browser, ensuring
 * hydration is complete before test assertions run. The time cost is front-loaded
 * once per suite, not per test. See git log for evidence: cold suite run
 * (no warmup) 46.8s with C3/C5 failures; warm run (after touching pages
 * once) 11.6s all passing, 4× speedup + zero failures.
 */
async function warmupClientBundles() {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();

    // Warm /login: navigate and wait for language selector to be interactive
    await page.goto("http://127.0.0.1:3000/login", {
      waitUntil: "networkidle",
    });
    // Target by aria-haspopup, not an accessible-name regex: /VN|EN|language/i
    // also matches the Next dev-tools button, and the resulting strict-mode
    // violation was being swallowed by the catch below — so this "warmup" was
    // only ever warming by side effect of goto(), never verifying hydration.
    const langSelector = page.locator('button[aria-haspopup="listbox"]');
    await expect(langSelector).toBeVisible();
    // Opening the listbox needs a React handler, so this proves hydration
    // rather than merely proving the markup arrived.
    await langSelector.click();
    await expect(page.getByRole("listbox")).toBeVisible();

    // /todo deliberately is NOT warmed here. Its sign-out control is a plain
    // form submit inside a server component, so it needs no hydration to work
    // — only /login has "use client" components whose handlers the tests race.

    await page.close();
  } catch (error) {
    // Deliberately rethrown. A silent warmup failure re-opens the exact
    // cold-start race this function exists to close, and the caller used to
    // print "hydration complete" straight after swallowing it.
    throw new Error(
      `Client bundle warmup failed — the cold-start race is not closed: ${error}`,
    );
  } finally {
    await browser.close();
  }
}

setup("authenticate and save state", async () => {
  // Create a test session in Node using the Supabase fixture
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

  console.log(`✓ Test session created and saved to ${authFile}`);
  console.log(`  Test user email: ${email}`);
  console.log(`  Auth token cookie: ${authTokenCookie.name}`);

  // Warm client bundles for /login and /todo to ensure React hydration
  // completes before test assertions run. This avoids race conditions
  // where tests interact with pre-hydration markup.
  console.log("Warming client bundles...");
  await warmupClientBundles();
  console.log("✓ Client bundles warmed (hydration complete)");

  // Second warmup for /todo with authenticated session
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    // Apply the authenticated session cookies
    await page.context().addCookies(playwrightCookies);
    // Navigate to /todo and wait for sign-out button
    await page.goto("http://127.0.0.1:3000/todo", {
      waitUntil: "networkidle",
    });
    const signOutButton = page.getByRole("button", {
      name: /sign.?out|đăng\s+xuất/i,
    });
    await expect(signOutButton).toBeVisible();
    await signOutButton.focus(); // Verify hydration
    await page.close();
  } catch (error) {
    console.warn("Authenticated route warmup encountered an issue:", error);
  } finally {
    await browser.close();
  }
});
