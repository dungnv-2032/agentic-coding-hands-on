import { expect, test } from "@playwright/test";

// This file runs in the 'anon' project (unauthenticated)
test.describe("Route Guards (anon project)", () => {
  // C6: Unauthenticated /todo access redirects to /login
  test("C6 [FR-101, FR-602, SC-001] — unauthenticated access to /todo redirects to /login", async ({
    page,
  }) => {
    await page.goto("/todo");

    // Should have been redirected to /login
    expect(page.url()).toContain("/login");

    // Login page should be visible
    const loginButton = page.getByRole("button", { name: /LOGIN With Google/i });
    await expect(loginButton).toBeVisible();
  });
});
