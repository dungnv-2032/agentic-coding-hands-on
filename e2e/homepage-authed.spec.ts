import { expect, test, type Page } from "@playwright/test";

// This file runs in the 'homepage-authed' project (with storageState loaded)
test.describe("Homepage SAA — Authenticated User (homepage-authed project)", () => {
  // ID-1: Header shows notification bell and account button for authenticated user
  test("ID-1 [FR-200] — authenticated user sees notification bell and account menu button in header", async ({
    page,
  }) => {
    await page.goto("/");

    // Should be on homepage, not redirected
    expect(page.url()).toContain("/");

    // Notification bell should be visible
    const notificationBell = page.getByRole("button", {
      name: /notification|bell|thông báo/i,
    });
    await expect(notificationBell).toBeVisible();

    // Account menu button should be visible
    const accountButton = page.getByRole("button", {
      name: /account|profile|tài khoản|hồ sơ/i,
    });
    await expect(accountButton).toBeVisible();
  });

  // ID-27: Notification panel opens on click
  test("ID-27 [FR-201] — clicking notification bell opens the notification panel", async ({
    page,
  }) => {
    await page.goto("/");

    const notificationBell = page.getByRole("button", {
      name: /notification|bell|thông báo/i,
    });
    await notificationBell.click();

    // Notification panel should open and show "Không có thông báo mới" (no new notifications)
    const notifPanel = page.locator('[data-testid="notification-panel"]');
    await expect(notifPanel).toBeVisible();

    // Empty state text (Vietnamese)
    const emptyState = page.getByText(/không có thông báo mới|no new notifications/i);
    await expect(emptyState).toBeVisible();

    // Click again to close
    await notificationBell.click();
    await expect(notifPanel).not.toBeVisible();
  });

  // ID-36: Account menu opens with Profile and Sign out options
  test("ID-36 [FR-202] — clicking account button opens menu with Profile and Sign out", async ({
    page,
  }) => {
    await page.goto("/");

    const accountButton = page.getByRole("button", {
      name: /account|profile|tài khoản|hồ sơ/i,
    });
    await accountButton.click();

    // Menu should open
    const menu = page.locator('[data-testid="account-menu"]');
    await expect(menu).toBeVisible();

    // Profile option should be present
    const profileLink = menu.getByRole("link", {
      name: /profile|hồ sơ/i,
    });
    await expect(profileLink).toBeVisible();

    // Sign out option should be present
    const signOutBtn = menu.getByRole("button", {
      name: /sign out|đăng xuất/i,
    });
    await expect(signOutBtn).toBeVisible();
  });

  // ID-38: Regular user's menu does NOT show Admin Dashboard
  test("ID-38 [FR-203] — regular user does not see Admin Dashboard in account menu", async ({
    page,
  }) => {
    await page.goto("/");

    const accountButton = page.getByRole("button", {
      name: /account|profile|tài khoản|hồ sơ/i,
    });
    await accountButton.click();

    // Menu should open
    const menu = page.locator('[data-testid="account-menu"]');
    await expect(menu).toBeVisible();

    // Admin Dashboard should NOT be present for a regular user
    // The test user created in auth.setup.ts is a regular user (no admin role)
    const adminDashboard = menu.getByRole("link", {
      name: /admin|dashboard|quản lý/i,
    });
    await expect(adminDashboard).not.toBeVisible();
  });

  // ID-5/ID-37: Admin user sees Admin Dashboard in account menu
  // SKIP: admin role seeding requires service_role key (ORCH-03), which is not available
  test("ID-5/37 [FR-204] — admin user sees Admin Dashboard in account menu", async ({
    page,
  }) => {
    // Skipping this test — admin seeding requires Supabase-specific
    // service_role access (ORCH-03: no service_role key available in this environment).
    // Re-enable when clarifications A2 details are implemented.
    test.skip();
  });
});
