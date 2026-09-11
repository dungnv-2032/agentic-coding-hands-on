import { expect, test, type Page, type Locator } from "@playwright/test";

import { ROUTE } from "./fixtures/viet-kudo-constants";

/**
 * VISUAL VALIDATION CAPTURE — Addlink Box (MoMorph `OyDLDuSGEa`)
 * Captures the dialog in its three meaningful states — empty, errors visible,
 * and filled with valid content — so the evidence folder stays reproducible.
 * Runs on demand only: `npx playwright test --project=addlink-box-visual-capture`.
 * `/kudos/new` is route-guarded, so this rides the kudos-authed session.
 */

const EVIDENCE_DIR = "plans/260911-1007-addlink-box/evidence";

// Helpers to locate dialog elements
const linkDialog = (page: Page): Locator => page.getByTestId("link-dialog");
const linkTextInput = (page: Page): Locator => page.getByTestId("link-text-input");
const linkUrlInput = (page: Page): Locator => page.getByTestId("link-url-input");
const linkTextError = (page: Page): Locator => page.getByTestId("link-text-error");
const linkUrlError = (page: Page): Locator => page.getByTestId("link-url-error");
const linkConfirm = (page: Page): Locator => page.getByTestId("link-confirm");
const linkCancel = (page: Page): Locator => page.getByTestId("link-cancel");
const toolbarLink = (page: Page): Locator => page.getByTestId("toolbar-link");

/**
 * The dialog is centered on the page with a backdrop, so a plain full-page shot
 * is fine. However, clip to the dialog panel itself plus a small margin to keep
 * the focus tight and exclude distracting page content.
 */
async function captureDialog(
  page: Page,
  fileName: string,
) {
  const box = await linkDialog(page).boundingBox();
  if (!box) throw new Error("link-dialog has no bounding box");
  const margin = 20;
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

test.describe("Visual Capture — Addlink Box", () => {
  test("capture empty, errors, and filled states", async ({ page }) => {
    // Set to 1440px width to match the design capture size
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(ROUTE);

    await expect(toolbarLink(page)).toBeVisible();

    // 1) Dialog open, both fields empty — validate state before screenshot
    await toolbarLink(page).click();
    await expect(linkDialog(page)).toBeVisible();
    await expect(linkTextInput(page)).toBeVisible();
    await expect(linkUrlInput(page)).toBeVisible();
    await expect(linkTextInput(page)).toHaveValue("");
    await expect(linkUrlInput(page)).toHaveValue("");
    await expect(linkTextError(page)).not.toBeVisible();
    await expect(linkUrlError(page)).not.toBeVisible();
    await captureDialog(page, "addlink-box-empty-1440.png");

    // 2) Click Lưu on empty fields — both errors should appear
    await linkConfirm(page).click();
    await expect(linkTextError(page)).toBeVisible();
    await expect(linkUrlError(page)).toBeVisible();
    await expect(linkDialog(page)).toBeVisible(); // Dialog stays open
    await captureDialog(page, "addlink-box-errors-1440.png");

    // 3) Close and reopen the dialog for fresh state, then fill with valid data
    await linkCancel(page).click();
    await expect(linkDialog(page)).not.toBeVisible();

    // Reopen and fill with valid data
    await toolbarLink(page).click();
    await expect(linkDialog(page)).toBeVisible();
    await linkTextInput(page).fill("Valid text");
    await linkUrlInput(page).fill("https://www.example.com");
    // Blur the URL field to validate it and trigger error clearing if needed
    await linkUrlInput(page).blur();
    // Verify errors are not visible
    await expect(linkTextError(page)).not.toBeVisible();
    await expect(linkUrlError(page)).not.toBeVisible();
    await captureDialog(page, "addlink-box-filled-1440.png");

    // Clean up — close the dialog
    await linkCancel(page).click();
  });
});
