import { expect, test } from "@playwright/test";

import {
  FAB_CLOSE_TESTID,
  FAB_MENU_TESTID,
  FAB_TRIGGER_TESTID,
  GEOMETRY_TEST_VIEWPORT_HEIGHT,
  GEOMETRY_TEST_VIEWPORT_WIDTH,
} from "./fixtures/floating-action-button-constants";

/**
 * VISUAL VALIDATION CAPTURE — Floating Action Button (F008)
 * Captures the collapsed pill and the expanded quick-action menu at the design
 * viewport so plans/260910-0907-floating-action-button/evidence/ stays reproducible.
 * Runs on demand only: `npx playwright test --project=fab-visual-capture`.
 * The FAB is visible to anonymous visitors, so no auth session is needed.
 */

const EVIDENCE_DIR = "plans/260910-0907-floating-action-button/evidence";

test.describe("Visual Capture — Floating Action Button", () => {
  test("capture collapsed pill and expanded menu at 1440x1024", async ({
    page,
  }) => {
    await page.setViewportSize({
      width: GEOMETRY_TEST_VIEWPORT_WIDTH,
      height: GEOMETRY_TEST_VIEWPORT_HEIGHT,
    });
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    const trigger = page.getByTestId(FAB_TRIGGER_TESTID);
    await expect(trigger).toBeVisible();

    await page.screenshot({ path: `${EVIDENCE_DIR}/fab-collapsed-1440.png` });
    console.log("✓ Collapsed pill captured");

    await trigger.click();
    await expect(page.getByTestId(FAB_MENU_TESTID)).toBeVisible();
    await expect(page.getByTestId(FAB_CLOSE_TESTID)).toBeVisible();

    await page.screenshot({ path: `${EVIDENCE_DIR}/fab-expanded-1440.png` });
    console.log("✓ Expanded menu captured");
  });
});
