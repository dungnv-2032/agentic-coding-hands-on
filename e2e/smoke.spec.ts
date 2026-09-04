import { expect, test } from "@playwright/test";

// Infra canary — proves the harness itself (browser launch, dev server,
// baseURL wiring) is healthy, independent of any application feature. This
// file stays in the suite permanently: a future RED here means the harness
// broke, not that a feature regressed. Nothing about login belongs here.
test("dev server responds and renders a non-empty page", async ({ page }) => {
  const response = await page.goto("/");

  expect(response?.status()).toBe(200);
  await expect(page.locator("body")).not.toBeEmpty();
});
