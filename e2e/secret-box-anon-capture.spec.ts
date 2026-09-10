import { expect, test } from "@playwright/test";

import {
  TEST_IDS,
  GEOMETRY_VIEWPORT,
  ROUTE,
} from "./fixtures/secret-box-constants";

/**
 * VISUAL VALIDATION CAPTURE — Secret Box Anonymous State (F009)
 * Captures the anonymous/unauthenticated state at the design viewport.
 * Runs on demand in the anon project: `npx playwright test --project=anon capture-secret-box-anon-visual.spec.ts`.
 * Or as part of the capture suite: `npx playwright test --project=secret-box-visual-capture-anon`.
 */

const EVIDENCE_DIR = "plans/260910-1708-open-secret-box/evidence";

test.describe("Visual Capture — Secret Box Anonymous State", () => {
  test("capture anonymous state at 1440x1024", async ({ page }) => {
    await page.setViewportSize({
      width: GEOMETRY_VIEWPORT.width,
      height: GEOMETRY_VIEWPORT.height,
    });
    await page.goto(ROUTE);
    await page.waitForLoadState("networkidle");

    const panel = page.getByTestId(TEST_IDS.panel);
    await expect(panel).toBeVisible();

    // Anonymous: count 00, no instruction, sign-in link visible
    const count = page.getByTestId(TEST_IDS.count);
    await expect(count).toContainText("00");

    const instruction = page.getByTestId(TEST_IDS.instruction);
    await expect(instruction).not.toBeVisible();

    const signIn = page.getByTestId(TEST_IDS.signIn);
    await expect(signIn).toBeVisible();

    await page.screenshot({ path: `${EVIDENCE_DIR}/secret-box-anon-1440.png` });
    console.log("✓ Anonymous state captured at 1440x1024");
  });
});
