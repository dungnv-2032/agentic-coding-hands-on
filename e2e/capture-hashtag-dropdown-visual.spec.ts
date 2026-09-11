import { expect, test } from "@playwright/test";

import {
  ROUTE,
  TEST_HASHTAG_1,
  TEST_HASHTAG_2,
  TEST_HASHTAG_3,
  TEST_HASHTAG_4,
  TEST_HASHTAG_5,
} from "./fixtures/viet-kudo-constants";

/**
 * VISUAL VALIDATION CAPTURE — Dropdown list hashtag (MoMorph `p9zO-c4a4x`)
 * Captures the open menu in its three meaningful states — empty, one selected,
 * and at the 5-hashtag cap — so the evidence folder stays reproducible.
 * Runs on demand only: `npx playwright test --project=hashtag-dropdown-visual-capture`.
 * `/kudos/new` is route-guarded, so this rides the kudos-authed session.
 */

const EVIDENCE_DIR = "plans/260911-0707-dropdown-list-hashtag/evidence";

/**
 * The menu opens downward from a control that sits low on a long form, so a
 * plain full-page shot clips it at the fold. Clip to the menu's own box plus a
 * margin — that keeps the trigger, the chips and the error line in frame while
 * guaranteeing the whole list is actually visible in the evidence.
 */
async function captureMenu(
  page: import("@playwright/test").Page,
  fileName: string,
) {
  const box = await page.getByTestId("hashtag-menu").boundingBox();
  if (!box) throw new Error("hashtag-menu has no bounding box");
  const margin = 60;
  await page.screenshot({
    path: `${EVIDENCE_DIR}/${fileName}`,
    clip: {
      x: Math.max(0, box.x - margin),
      y: Math.max(0, box.y - margin),
      width: box.width + margin * 2,
      height: box.height + margin * 2,
    },
  });
}

test.describe("Visual Capture — Dropdown list hashtag", () => {
  test("capture empty, one-selected and at-cap states", async ({ page }) => {
    // Taller than the design viewport so the downward-opening menu fits whole.
    await page.setViewportSize({ width: 1440, height: 1400 });
    await page.goto(ROUTE);

    const trigger = page.getByTestId("hashtag-add");
    const menu = page.getByTestId("hashtag-menu");
    await expect(trigger).toBeVisible();

    // 1) Menu open, nothing selected — every row unselected, slots empty.
    await trigger.click();
    await expect(menu).toBeVisible();
    await page.getByTestId("hashtag-add").scrollIntoViewIfNeeded();
    await captureMenu(page, "hashtag-dropdown-empty-1440.png");

    // 2) One selected — check icon and lifted background on that row only.
    await menu.locator('[role="option"]').filter({ hasText: TEST_HASHTAG_1 }).click();
    await trigger.click();
    await expect(menu).toBeVisible();
    await expect(
      menu.locator('[role="option"][data-selected="true"]'),
    ).toHaveCount(1);
    await captureMenu(page, "hashtag-dropdown-one-selected-1440.png");

    // 3) At the cap — unselected rows dimmed and disabled, error standing.
    for (const tag of [
      TEST_HASHTAG_2,
      TEST_HASHTAG_3,
      TEST_HASHTAG_4,
      TEST_HASHTAG_5,
    ]) {
      await menu.locator('[role="option"]').filter({ hasText: tag }).click();
      await trigger.click();
      await expect(menu).toBeVisible();
    }
    await expect(page.getByTestId("hashtag-error")).toBeVisible();
    // Prove the cap state, not just photograph it.
    const unselected = menu.locator('[role="option"]:not([data-selected="true"])');
    await expect(unselected.first()).toBeDisabled();
    await captureMenu(page, "hashtag-dropdown-at-cap-1440.png");
  });
});
