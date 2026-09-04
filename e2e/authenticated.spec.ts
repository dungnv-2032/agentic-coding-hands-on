import { expect, test } from "@playwright/test";

// This file runs in the 'authed' project (with storageState loaded)
test.describe("Authenticated Routes (authed project)", () => {
  // C7: Authenticated /login access redirects to /todo
  test("C7 [FR-102, SC-002] — authenticated access to /login redirects to /todo", async ({
    page,
  }) => {
    await page.goto("/login");

    // Should have been redirected to /todo
    expect(page.url()).toContain("/todo");

    // /todo page should be visible (at least some content)
    await expect(page.locator("body")).not.toBeEmpty();
  });

  // C8: Cookie preservation — guarded redirect from /login forces token refresh,
  // then two further /todo loads must stay authenticated. This tests that rotated
  // cookies from the redirect are preserved by the proxy (plan risk R1).
  test("C8 [SC-001, proxy-cookie-rotation] — after guarded /login→/todo redirect with token refresh, subsequent requests stay authenticated", async ({
    page,
  }) => {
    // First, hit /login while authenticated with an expired access token.
    // The fixture sets expires_at in the past, forcing a refresh during this redirect.
    // The proxy must forward the Set-Cookie header from the refresh response,
    // otherwise the next request will be logged out.
    await page.goto("/login");

    // The guarded redirect should have landed on /todo
    expect(page.url()).toContain("/todo");

    // Second load to /todo (should still be authenticated with refreshed cookies)
    await page.goto("/todo");
    expect(page.url()).toContain("/todo");
    await expect(page.locator("body")).not.toBeEmpty();

    // Third load to /todo (should still be authenticated)
    await page.goto("/todo");
    expect(page.url()).toContain("/todo");
    await expect(page.locator("body")).not.toBeEmpty();
  });

  // C9: Sign-out flow — /todo → sign out → /login, then /todo bounces to /login
  test("C9 [FR-403, US004] — signing out redirects to /login and /todo thereafter bounces to /login", async ({
    page,
  }) => {
    // Navigate to /todo while authenticated
    await page.goto("/todo");
    expect(page.url()).toContain("/todo");

    // Locate the sign-out button by its LOCALIZED accessible name. The page
    // renders `todo.signOut` from the dictionary and deliberately carries no
    // English aria-label override (that would break WCAG 2.5.3 "Label in
    // Name"), so this must match the real visible copy. Default locale is vi
    // ("Đăng xuất"); "Sign out" covers a run with NEXT_LOCALE=en.
    const signOutButton = page.getByRole("button", {
      name: /đăng xuất|sign.?out/i,
    });
    await signOutButton.click();

    // Wait for the redirect to /login to settle (don't just check URL immediately)
    await page.waitForURL(/\/login/);
    expect(page.url()).toContain("/login");

    // Try to access /todo again — should redirect back to /login
    await page.goto("/todo");
    await page.waitForURL(/\/login/);
    expect(page.url()).toContain("/login");
  });
});
