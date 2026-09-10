import { test, expect } from "@playwright/test";
import { createClient } from "@supabase/supabase-js";
import * as fs from "node:fs";
import * as path from "node:path";
import { ROUTE, TEST_IDS, STRINGS, BADGE_LABELS } from "./fixtures/secret-box-constants";
import { setUnopenedCount, readCounters, clearOpenings } from "./fixtures/secret-box-grant";

/**
 * Load test user credentials (created by secret-box-auth.setup.ts)
 */
function loadCredentials() {
  const credentialsPath = path.join(process.cwd(), "e2e/.auth/secret-box-credentials.json");
  const content = fs.readFileSync(credentialsPath, "utf-8");
  return JSON.parse(content) as {
    email: string;
    password: string;
    userId: string;
    sunnerId: string;
  };
}

/**
 * Load environment variables for Supabase
 */
function loadEnv() {
  const envPath = path.join(process.cwd(), ".env.local");
  const envContent = fs.readFileSync(envPath, "utf-8");
  const env: Record<string, string> = {};
  envContent.split("\n").forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) return;
    const [key, ...valueParts] = trimmed.split("=");
    env[key] = valueParts.join("=").trim();
  });
  return env;
}

/**
 * Sign in test user and get the JWT access token
 */
async function getAuthenticatedToken(
  email: string,
  password: string,
): Promise<string> {
  const env = loadEnv();
  const supabaseUrl = env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  const client = createClient(supabaseUrl, anonKey);

  const { data, error } = await client.auth.signInWithPassword({
    email,
    password,
  });

  if (error || !data.session?.access_token) {
    throw new Error(`Failed to sign in: ${error?.message}`);
  }

  return data.session.access_token;
}

test.describe("Secret Box — Authenticated", () => {
  let credentials: ReturnType<typeof loadCredentials>;

  test.beforeAll(() => {
    credentials = loadCredentials();
  });

  // SB-01: count=5 → 200, main h1 is the title, instruction line visible, counter reads 05
  // FR-001, FR-101, FR-102, FR-104
  test("SB-01: render with title, instruction, and count 05", async ({
    page,
  }) => {
    await setUnopenedCount(credentials.userId, 5);
    await page.goto(ROUTE);

    // FR-001: 200 status
    expect(page.url()).toContain(ROUTE);

    // FR-101: title is <h1>
    const h1 = page.locator("main h1");
    await expect(h1).toBeVisible();
    await expect(h1).toHaveText(STRINGS.title);

    // FR-102: instruction line visible
    const instruction = page.getByTestId(TEST_IDS.instruction);
    await expect(instruction).toBeVisible();
    await expect(instruction).toHaveText(STRINGS.instruction);

    // FR-104: counter reads 05
    const counter = page.getByTestId(TEST_IDS.count);
    await expect(counter).toHaveText("05");
  });

  // SB-02: opener is an enabled control with stable accessible name; box art present
  // FR-103, FR-202
  test("SB-02: box is visible and operable, with stable name", async ({
    page,
  }) => {
    await setUnopenedCount(credentials.userId, 5);
    await page.goto(ROUTE);

    // FR-202: opener is enabled (not disabled)
    const opener = page.getByTestId(TEST_IDS.opener);
    await expect(opener).toBeVisible();
    await expect(opener).toBeEnabled();

    // Stable accessible name
    const name = await opener.getAttribute("aria-label");
    expect(name).toBeTruthy();

    // FR-103: box art present
    const boxImage = page.getByTestId(TEST_IDS.panel).getByAltText(/box|hộp/i);
    await expect(boxImage).toBeVisible();
  });

  // SB-03: count=5 → click → a badge appears whose name is one of the six rule_items labels; counter reads 04
  // FR-201, BR-002, BR-005
  test("SB-03: click box opens one badge, counter decrements", async ({
    page,
  }) => {
    await setUnopenedCount(credentials.userId, 5);
    await page.goto(ROUTE);

    const counter = page.getByTestId(TEST_IDS.count);
    const opener = page.getByTestId(TEST_IDS.opener);

    // Click to open
    await opener.click();

    // BR-002: exactly one badge appears
    const badge = page.getByTestId(TEST_IDS.badge);
    await expect(badge).toBeVisible();

    // BR-005: badge label is one of the six rule_items labels
    const badgeAlt = await badge.getAttribute("alt");
    expect(BADGE_LABELS).toContain(badgeAlt?.toUpperCase());

    // FR-201: counter decrements to 04
    await expect(counter).toHaveText("04");
  });

  // SB-04: opener rejects a second click while the first is in flight (disabled/aria-busy); after settle, exactly one decrement
  // FR-203, SM-001
  test("SB-04: double-click race is rejected, exactly one decrement", async ({
    page,
  }) => {
    await setUnopenedCount(credentials.userId, 5);
    // `setUnopenedCount` resets the two counters but leaves `secret_box_openings`
    // rows behind, and earlier cases in this file have already written some.
    // The openings assertion at the end counts absolutely, so the slate has to
    // be clean first — otherwise it measures test order, not behavior.
    await clearOpenings(credentials.userId);
    await page.goto(ROUTE);

    const opener = page.getByTestId(TEST_IDS.opener);
    const counter = page.getByTestId(TEST_IDS.count);

    // First click, deliberately not awaited: the point of this test is what
    // happens WHILE the action is in flight (FR-203/SM-001).
    const firstClick = opener.click();
    await page.waitForTimeout(100);

    // The in-flight control must be shut, by `disabled` and/or `aria-busy`.
    const isDisabled = await opener.isDisabled();
    const isBusy = await opener.getAttribute("aria-busy");
    expect(isDisabled || isBusy === "true").toBeTruthy();

    // Now actually press it a SECOND time. Without this the test only ever
    // read the button's state and never exercised the rejection at all — the
    // explicit guard in `secret-box-opener.tsx` could have been deleted and
    // this case would still have gone green (reviewer finding M1).
    //
    // `force: true` is required rather than sloppy: `click()`'s
    // actionability check and `isDisabled()` above route through the same
    // predicate, so an ordinary click on a control we just asserted is
    // disabled can only time out. The click is forced and the EFFECT — one
    // decrement, not two — is what gets asserted.
    await opener.click({ force: true });
    await firstClick;

    await expect(counter).toHaveText("04", { timeout: 15_000 });

    // Exactly one decrement survived both presses, and exactly one opening
    // row was written — 03 here would mean the second click was honored.
    const { unopened, openings } = await readCounters(credentials.userId);
    expect(unopened).toBe(4);
    expect(openings).toBe(1);
  });

  // SB-05: after an open, reload → counter still 04; /profile stats read opened +1 / unopened −1
  // BR-001, revalidate
  test("SB-05: persistence after reload and profile alignment", async ({
    page,
  }) => {
    await setUnopenedCount(credentials.userId, 5);
    await clearOpenings(credentials.userId);
    await page.goto(ROUTE);

    const opener = page.getByTestId(TEST_IDS.opener);
    const counter = page.getByTestId(TEST_IDS.count);

    // Open one box
    await opener.click();
    await expect(counter).toHaveText("04", { timeout: 15_000 });

    // Reload the page
    await page.reload();

    // BR-001: counter still reads 04 (persisted in database)
    await expect(counter).toHaveText("04");

    // Verify the backend state
    const { unopened, opened, openings } = await readCounters(credentials.userId);
    expect(unopened).toBe(4);
    expect(opened).toBe(1);
    expect(openings).toBe(1);
  });

  // SB-06: count=1 → open → counter 00, instruction line hidden, opener disabled
  // FR-102, FR-202
  test("SB-06: at count 0, instruction hides and opener disables", async ({
    page,
  }) => {
    await setUnopenedCount(credentials.userId, 1);
    await page.goto(ROUTE);

    const opener = page.getByTestId(TEST_IDS.opener);
    const instruction = page.getByTestId(TEST_IDS.instruction);
    const counter = page.getByTestId(TEST_IDS.count);

    // Open the last box
    await opener.click();
    await expect(counter).toHaveText("00", { timeout: 15_000 });

    // FR-102: instruction line hidden at count 0
    await expect(instruction).not.toBeVisible();

    // FR-202: opener disabled
    await expect(opener).toBeDisabled();
  });

  // SB-07: count=1 → two concurrent rpc calls → exactly one succeeds, the other reports no-boxes; final count 0
  // BR-004, FR-602, R1
  test("SB-07: concurrent opens resolve to exactly one success", async () => {
    await setUnopenedCount(credentials.userId, 1);

    // Get authenticated token for the test user
    const token = await getAuthenticatedToken(
      credentials.email,
      credentials.password,
    );

    const env = loadEnv();
    const anonKey = env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    const supabaseUrl = env.NEXT_PUBLIC_SUPABASE_URL;

    // Make two concurrent RPC calls as authenticated user
    const promise1 = fetch(`${supabaseUrl}/rest/v1/rpc/open_secret_box`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        apikey: anonKey,
        "X-Client-Info": "supabase-js/2",
      },
      body: JSON.stringify({}),
    });

    const promise2 = fetch(`${supabaseUrl}/rest/v1/rpc/open_secret_box`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        apikey: anonKey,
        "X-Client-Info": "supabase-js/2",
      },
      body: JSON.stringify({}),
    });

    const [response1, response2] = await Promise.all([promise1, promise2]);

    // One should succeed, one should fail with no-boxes
    const status1 = response1.status;
    const status2 = response2.status;

    // Exactly one 200, one non-200
    expect([status1, status2].filter((s) => s === 200).length).toBe(1);

    // Verify final count is 0
    const { unopened } = await readCounters(credentials.userId);
    expect(unopened).toBe(0);
  });

  // SB-08: authenticated PATCH on own sunners row with secret_box_unopened_count is rejected; unexpected RPC arguments rejected
  // FR-601, 5cc072ad, 2e7bec78
  test("SB-08: direct updates and unexpected RPC arguments are rejected", async () => {
    await setUnopenedCount(credentials.userId, 5);

    // Get authenticated token for the test user
    const token = await getAuthenticatedToken(
      credentials.email,
      credentials.password,
    );

    const env = loadEnv();
    const anonKey = env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    const supabaseUrl = env.NEXT_PUBLIC_SUPABASE_URL;

    // Attempt 1: Direct PATCH on sunners with secret_box_unopened_count (5cc072ad)
    // This should be rejected by RLS policy (no UPDATE policy exists on sunners)
    const patchResponse = await fetch(
      `${supabaseUrl}/rest/v1/sunners?auth_user_id=eq.${credentials.userId}`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          apikey: anonKey,
          "X-Client-Info": "supabase-js/2",
        },
        body: JSON.stringify({ secret_box_unopened_count: 10 }),
      },
    );

    // Should be rejected (403 Forbidden or similar — no UPDATE policy on sunners)
    expect(patchResponse.status).not.toBe(200);

    // Verify the count was not changed
    const { unopened: unopenedAfterPatch } = await readCounters(credentials.userId);
    expect(unopenedAfterPatch).toBe(5);

    // Attempt 2: RPC with unexpected argument (2e7bec78)
    // The function takes no parameters, so unexpected arguments should be refused by PostgREST
    const unexpectedArgResponse = await fetch(
      `${supabaseUrl}/rest/v1/rpc/open_secret_box`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          apikey: anonKey,
          "X-Client-Info": "supabase-js/2",
        },
        body: JSON.stringify({ unexpected_arg: "99999" }),
      },
    );

    // Should error — PostgREST rejects unexpected arguments
    expect(unexpectedArgResponse.status).not.toBe(200);
  });

  // SB-09: close glyph: arrived from /kudos → returns to /kudos; deep link → lands on /kudos
  // FR-301
  test("SB-09: close button navigation", async ({ page }) => {
    await setUnopenedCount(credentials.userId, 5);

    // Navigate from /kudos
    await page.goto("/kudos");
    await page.goto(ROUTE);

    // Find and click the close button
    const closeButton = page.getByTestId(TEST_IDS.close);
    await expect(closeButton).toBeVisible();
    await closeButton.click();

    // FR-301: should return to /kudos
    await page.waitForURL("/kudos");
    expect(page.url()).toContain("/kudos");
  });
});
