import { test } from "@playwright/test";

/**
 * VISUAL VALIDATION CAPTURE
 * Captures homepage at desktop and mobile widths for visual comparison against design.
 * This test uses the homepage-authed session so screenshots show the authenticated header.
 */

test.describe("Visual Capture — Homepage", () => {
  test("capture desktop (1512px) and mobile (375px) screenshots", async ({
    page,
  }) => {
    // Navigate to homepage
    await page.goto("/");

    // Desktop capture at 1512px (design width)
    await page.setViewportSize({ width: 1512, height: 2160 });
    await page.waitForLoadState("networkidle");

    await page.screenshot({
      path: "plans/260905-1153-homepage-saa/evidence/homepage-desktop-1512px.png",
      fullPage: true,
    });
    console.log("✓ Desktop screenshot captured: 1512px width");

    // Mobile capture at 375px
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    await page.screenshot({
      path: "plans/260905-1153-homepage-saa/evidence/homepage-mobile-375px.png",
      fullPage: true,
    });
    console.log("✓ Mobile screenshot captured: 375px width");
  });
});
