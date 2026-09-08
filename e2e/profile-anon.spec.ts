import { expect, test } from "@playwright/test";
import { ROUTE, FRAME_RECEIVER_ID } from "./fixtures/profile-constants";

/**
 * Unauthenticated access control tests for Profile bản thân (`/profile`).
 * Test policy: e2e-red-first, visual-contract: access control.
 *
 * Maps to clarifications.md test cases:
 * - TC_WEB_PROFILE_ACC_001: unauthenticated /profile redirects to /login
 * - TC_WEB_PROFILE_ACC_002: unauthenticated /profile?id=1 redirects to /login
 *
 * Runs in the `anon` Playwright project (no session).
 */

test.describe("Profile screen — access control (anon)", () => {
  test("ACC_001 — /profile redirects unauthenticated visitor to /login", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Should be redirected to login
    expect(page.url()).toContain("/login");

    // Assert no profile content is rendered
    await expect(page.getByTestId("profile-hero")).not.toBeVisible();
  });

  test("ACC_002 — /profile?id=1 redirects unauthenticated visitor to /login", async ({
    page,
  }) => {
    await page.goto(`${ROUTE}?id=${FRAME_RECEIVER_ID}`);

    // Should be redirected to login
    expect(page.url()).toContain("/login");

    // Assert no profile content is rendered
    await expect(page.getByTestId("profile-hero")).not.toBeVisible();
  });
});
