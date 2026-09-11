import { expect, test } from "@playwright/test";

import { ROUTE, TEST_DEPARTMENT } from "./fixtures/kudos-constants";

/**
 * VISUAL VALIDATION CAPTURE — Dropdown Phòng ban (MoMorph `WXK5AYB_rG`)
 * Captures the department listbox closed, open-unselected and open-selected so
 * the evidence folder stays reproducible.
 * Runs on demand only: `npx playwright test --project=department-dropdown-visual-capture`.
 * `/kudos` is public, so this needs no session.
 */

const EVIDENCE_DIR = "plans/260911-1348-dropdown-phong-ban/evidence";

/**
 * Clip to the listbox plus a margin: a full-page shot of `/kudos` renders the
 * 348px menu too small to judge centring or the selected row's glow against
 * the frame.
 */
async function captureMenu(
  page: import("@playwright/test").Page,
  fileName: string,
) {
  const box = await page.getByTestId("filter-menu-department").boundingBox();
  if (!box) throw new Error("filter-menu-department has no bounding box");
  const margin = 80;
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

test.describe("Visual Capture — Dropdown Phòng ban", () => {
  test("capture closed, open-unselected and open-selected states", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 1400 });
    await page.goto(ROUTE);

    const trigger = page.getByTestId("filter-department");
    const menu = page.getByTestId("filter-menu-department");
    await expect(trigger).toBeVisible();

    // 1) Both filter triggers closed.
    const triggerBox = await trigger.boundingBox();
    if (!triggerBox) throw new Error("filter-department has no bounding box");
    await page.screenshot({
      path: `${EVIDENCE_DIR}/department-dropdown-closed.png`,
      clip: {
        x: Math.max(0, triggerBox.x - 420),
        y: Math.max(0, triggerBox.y - 80),
        width: triggerBox.width + 500,
        height: triggerBox.height + 160,
      },
    });

    // 2) Menu open, nothing selected — centred labels in the bounded box.
    await trigger.click();
    await expect(menu).toBeVisible();

    // Prove the geometry, not just photograph it: the frame shows six 56px
    // rows in a 348px box, and these rows are flex children of a scroll
    // container, so they could shrink without the container changing size.
    const menuBox = await menu.boundingBox();
    const rowBox = await menu.locator('[role="option"]').first().boundingBox();
    expect(menuBox?.height).toBe(348);
    expect(rowBox?.height).toBe(56);

    await captureMenu(page, "department-dropdown-open-unselected.png");

    // 3) Open with TEST_DEPARTMENT selected — persistent highlight + glow.
    await menu.getByRole("option", { name: TEST_DEPARTMENT, exact: true }).click();
    await expect(menu).not.toBeVisible();
    await trigger.click();
    await expect(menu).toBeVisible();
    await expect(
      menu.getByRole("option", { name: TEST_DEPARTMENT, exact: true }),
    ).toHaveAttribute("aria-selected", "true");
    await captureMenu(page, "department-dropdown-open-selected.png");
  });
});
