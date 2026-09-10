import { expect, test } from "@playwright/test";

import {
  BOX_TOLERANCE_PX,
  BUTTON_BORDER_RADIUS,
  BUTTON_GAP,
  BUTTON_YELLOW_BG,
  CLOSE_BUTTON_RED_BG,
  FAB_CLOSE_TESTID,
  CLOSE_BUTTON_BORDER_RADIUS_MIN,
  CLOSE_BUTTON_HEIGHT,
  CLOSE_BUTTON_WIDTH,
  CLOSE_LABEL,
  COMPOSE_ROUTE,
  FAB_MENU_TESTID,
  FAB_STANDARDS_TESTID,
  FAB_TRIGGER_TESTID,
  FAB_WRITE_KUDOS_TESTID,
  GEOMETRY_TEST_VIEWPORT_HEIGHT,
  GEOMETRY_TEST_VIEWPORT_WIDTH,
  LABEL_FONT_SIZE,
  LABEL_FONT_WEIGHT,
  LABEL_LINE_HEIGHT,
  LABEL_TEXT_COLOR,
  LOGIN_ROUTE,
  MENU_HEIGHT,
  MENU_STANDARDS_LABEL,
  MENU_WIDTH,
  MENU_WRITE_KUDOS_LABEL,
  STANDARDS_ARIA_LABEL,
  STANDARDS_BUTTON_HEIGHT,
  STANDARDS_BUTTON_WIDTH,
  STANDARDS_ROUTE,
  TRIGGER_LABEL,
  WRITE_KUDOS_ARIA_LABEL,
  WRITE_KUDOS_BUTTON_HEIGHT,
  WRITE_KUDOS_BUTTON_WIDTH,
  HOME_ROUTE,
} from "./fixtures/floating-action-button-constants";

/**
 * Screen-level E2E for Floating Action Button (FAB) — MoMorph screens
 * `9ypp4enmFmdK3YAFJLIu6C` (collapsed: `_hphd32jN2`, expanded: `Sv7DFwBw1h`).
 *
 * Test policy: **e2e-red-first**. This file is written and driven to a valid
 * assertion RED BEFORE any FAB component is implemented, and phase 05 reruns
 * the identical command for GREEN. The command is fixed:
 *
 *     npx playwright test e2e/floating-action-button.spec.ts --project=anon
 *
 * Runs in the `anon` project: the homepage is public — `proxy.ts` guards only
 * `/todo`, exact `/kudos/new`, and `/profile` — so no session, no storageState,
 * no `createTestSession()`. The spec writes NO data, so it needs no cleanup
 * block; the feature's own state machine is its fixture.
 *
 * Test cases derived from `plans/260910-0907-floating-action-button/clarifications.md`
 * (0 test cases downloaded from MoMorph for both screens). Every `data-testid`
 * used below is fixed by clarifications.md § "Test contract". Vietnamese copy
 * is read from `./fixtures/floating-action-button-constants`, never inlined.
 */

/**
 * Pixel comparison with a real ±px budget. `expect().toBeCloseTo(expected, n)`
 * reads its second argument as a NUMBER OF DECIMAL DIGITS, not a tolerance, so
 * passing `BOX_TOLERANCE_PX` there demanded exactness — the opposite of the ±1px
 * budget design/geometry.md intends, and red on any one-pixel platform drift.
 */
function expectWithinTolerance(actual: number, expected: number) {
  expect(Math.abs(actual - expected)).toBeLessThanOrEqual(BOX_TOLERANCE_PX);
}

test.describe("Floating Action Button (FAB) — anon", () => {
  test("FAB-01 — AC1: homepage renders collapsed trigger, aria-expanded=false, no menu", async ({
    page,
  }) => {
    await page.goto(HOME_ROUTE);

    const trigger = page.getByTestId(FAB_TRIGGER_TESTID);
    await expect(trigger).toBeVisible();
    await expect(trigger).toHaveAccessibleName(TRIGGER_LABEL);
    await expect(trigger).toHaveAttribute("aria-expanded", "false");

    const menu = page.getByTestId(FAB_MENU_TESTID);
    await expect(menu).not.toBeAttached();
  });

  test("FAB-02 — AC1, AC2: click trigger → menu opens, trigger aria-expanded=true, aria-controls matches menu id", async ({
    page,
  }) => {
    await page.goto(HOME_ROUTE);

    const trigger = page.getByTestId(FAB_TRIGGER_TESTID);
    await trigger.click();

    const menu = page.getByTestId(FAB_MENU_TESTID);
    await expect(menu).toBeVisible();

    // Menu contains all three buttons
    const standards = page.getByTestId(FAB_STANDARDS_TESTID);
    await expect(standards).toBeVisible();
    await expect(standards).toContainText(MENU_STANDARDS_LABEL);
    // `aria-label` overrides the visible text as the accessible name — pin both
    // so a copy change can't quietly alter what assistive tech announces.
    await expect(standards).toHaveAccessibleName(STANDARDS_ARIA_LABEL);

    const writeKudos = page.getByTestId(FAB_WRITE_KUDOS_TESTID);
    await expect(writeKudos).toBeVisible();
    await expect(writeKudos).toContainText(MENU_WRITE_KUDOS_LABEL);
    await expect(writeKudos).toHaveAccessibleName(WRITE_KUDOS_ARIA_LABEL);

    const close = page.getByTestId(FAB_CLOSE_TESTID);
    await expect(close).toBeVisible();
    await expect(close).toHaveAccessibleName(CLOSE_LABEL);

    // Trigger state and aria-controls
    await expect(trigger).toHaveAttribute("aria-expanded", "true");
    const menuId = await menu.getAttribute("id");
    const ariaControls = await trigger.getAttribute("aria-controls");
    expect(ariaControls).toBe(menuId);
  });

  test("FAB-03 — AC3: click standards button → navigate to /standards, rules-panel-content visible", async ({
    page,
  }) => {
    await page.goto(HOME_ROUTE);

    const trigger = page.getByTestId(FAB_TRIGGER_TESTID);
    await trigger.click();

    const standards = page.getByTestId(FAB_STANDARDS_TESTID);
    await standards.click();

    await expect(page).toHaveURL(new RegExp(`${STANDARDS_ROUTE}$`));

    const panel = page.getByTestId("rules-panel-content");
    await expect(panel).toBeVisible();
  });

  test("FAB-04 — AC4: anonymous user clicking write-kudos → redirects to /login, not /kudos/new", async ({
    page,
  }) => {
    await page.goto(HOME_ROUTE);

    const trigger = page.getByTestId(FAB_TRIGGER_TESTID);
    await trigger.click();

    const writeKudos = page.getByTestId(FAB_WRITE_KUDOS_TESTID);
    await writeKudos.click();

    // Should redirect to /login due to proxy.ts guard, not land on /kudos/new
    await expect(page).toHaveURL(new RegExp(`${LOGIN_ROUTE}$`));
    expect(page.url()).not.toContain(COMPOSE_ROUTE);
  });

  test("FAB-05 — AC5: click close button → menu detached, trigger visible, aria-expanded=false", async ({
    page,
  }) => {
    await page.goto(HOME_ROUTE);

    const trigger = page.getByTestId(FAB_TRIGGER_TESTID);
    await trigger.click();

    const menu = page.getByTestId(FAB_MENU_TESTID);
    await expect(menu).toBeVisible();

    const close = page.getByTestId(FAB_CLOSE_TESTID);
    await close.click();

    // Menu is detached from DOM
    await expect(menu).not.toBeAttached();

    // Trigger is still visible and reset
    await expect(trigger).toBeVisible();
    await expect(trigger).toHaveAttribute("aria-expanded", "false");

    // Focus returns to the trigger: `Hủy` is a deliberate dismissal from inside
    // the menu, like Escape (FAB-06). Without this a keyboard user is dropped on
    // `document.body` when the menu unmounts. Contrast FAB-07, where the user
    // aimed elsewhere on the page and focus must NOT be pulled back.
    const focused = await page.evaluate(() => document.activeElement?.getAttribute("data-testid"));
    expect(focused).toBe(FAB_TRIGGER_TESTID);
  });

  test("FAB-06 — AC5: Escape key → menu closed, fab-trigger is focused", async ({
    page,
  }) => {
    await page.goto(HOME_ROUTE);

    const trigger = page.getByTestId(FAB_TRIGGER_TESTID);
    await trigger.click();

    const menu = page.getByTestId(FAB_MENU_TESTID);
    await expect(menu).toBeVisible();

    // Press Escape
    await page.keyboard.press("Escape");

    // Menu is detached
    await expect(menu).not.toBeAttached();

    // Trigger is focused
    const focused = await page.evaluate(() => document.activeElement?.getAttribute("data-testid"));
    expect(focused).toBe(FAB_TRIGGER_TESTID);
  });

  test("FAB-07 — AC5: pointerdown on page background → menu closed, fab-trigger NOT focused", async ({
    page,
  }) => {
    await page.goto(HOME_ROUTE);

    const trigger = page.getByTestId(FAB_TRIGGER_TESTID);
    await trigger.click();

    const menu = page.getByTestId(FAB_MENU_TESTID);
    await expect(menu).toBeVisible();

    // Click on the page background (e.g., center)
    await page.click("body", { position: { x: 100, y: 100 } });

    // Menu is detached
    await expect(menu).not.toBeAttached();

    // Trigger is NOT focused (outside click does not return focus)
    const focused = await page.evaluate(() => document.activeElement?.getAttribute("data-testid"));
    expect(focused).not.toBe(FAB_TRIGGER_TESTID);
  });

  test("FAB-08 — AC6: geometry at viewport 1440×1024", async ({ page }) => {
    await page.setViewportSize({
      width: GEOMETRY_TEST_VIEWPORT_WIDTH,
      height: GEOMETRY_TEST_VIEWPORT_HEIGHT,
    });
    await page.goto(HOME_ROUTE);

    const trigger = page.getByTestId(FAB_TRIGGER_TESTID);
    await trigger.click();

    const menu = page.getByTestId(FAB_MENU_TESTID);
    const standards = page.getByTestId(FAB_STANDARDS_TESTID);
    const writeKudos = page.getByTestId(FAB_WRITE_KUDOS_TESTID);
    const close = page.getByTestId(FAB_CLOSE_TESTID);

    await expect(menu).toBeVisible();
    await expect(standards).toBeVisible();
    await expect(writeKudos).toBeVisible();
    await expect(close).toBeVisible();

    // Menu container dimensions
    const menuBox = await menu.boundingBox();
    expect(menuBox).not.toBeNull();
    if (menuBox) {
      expectWithinTolerance(Math.round(menuBox.width), MENU_WIDTH);
      expectWithinTolerance(Math.round(menuBox.height), MENU_HEIGHT);
    }

    // Standards button dimensions
    const standardsBox = await standards.boundingBox();
    expect(standardsBox).not.toBeNull();
    if (standardsBox) {
      expectWithinTolerance(Math.round(standardsBox.width), STANDARDS_BUTTON_WIDTH);
      expectWithinTolerance(Math.round(standardsBox.height), STANDARDS_BUTTON_HEIGHT);
    }

    // Write kudos button dimensions
    const writeKudosBox = await writeKudos.boundingBox();
    expect(writeKudosBox).not.toBeNull();
    if (writeKudosBox) {
      expectWithinTolerance(Math.round(writeKudosBox.width), WRITE_KUDOS_BUTTON_WIDTH);
      expectWithinTolerance(Math.round(writeKudosBox.height), WRITE_KUDOS_BUTTON_HEIGHT);
    }

    // Close button dimensions
    const closeBox = await close.boundingBox();
    expect(closeBox).not.toBeNull();
    if (closeBox) {
      expectWithinTolerance(Math.round(closeBox.width), CLOSE_BUTTON_WIDTH);
      expectWithinTolerance(Math.round(closeBox.height), CLOSE_BUTTON_HEIGHT);
    }

    // Vertical gaps (standards.bottom + 20 === write-kudos.top)
    if (standardsBox && writeKudosBox) {
      const gap1 = writeKudosBox.y - (standardsBox.y + standardsBox.height);
      expectWithinTolerance(Math.round(gap1), BUTTON_GAP);
    }

    // Vertical gaps (write-kudos.bottom + 20 === close.top)
    if (writeKudosBox && closeBox) {
      const gap2 = closeBox.y - (writeKudosBox.y + writeKudosBox.height);
      expectWithinTolerance(Math.round(gap2), BUTTON_GAP);
    }

    // Right alignment (all share same x + width)
    if (standardsBox && writeKudosBox && closeBox) {
      const standardsRight = standardsBox.x + standardsBox.width;
      const writeKudosRight = writeKudosBox.x + writeKudosBox.width;
      const closeRight = closeBox.x + closeBox.width;

      expectWithinTolerance(Math.round(standardsRight), Math.round(writeKudosRight));
      expectWithinTolerance(Math.round(writeKudosRight), Math.round(closeRight));
    }

    // Computed styles — standards button
    const standardsStyles = await standards.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        backgroundColor: computed.backgroundColor,
        borderRadius: computed.borderRadius,
      };
    });
    expect(standardsStyles.backgroundColor).toBe(BUTTON_YELLOW_BG);
    expect(standardsStyles.borderRadius).toBe(BUTTON_BORDER_RADIUS);

    // Computed styles — write kudos button
    const writeKudosStyles = await writeKudos.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        backgroundColor: computed.backgroundColor,
        borderRadius: computed.borderRadius,
      };
    });
    expect(writeKudosStyles.backgroundColor).toBe(BUTTON_YELLOW_BG);
    expect(writeKudosStyles.borderRadius).toBe(BUTTON_BORDER_RADIUS);

    // Computed styles — close button
    const closeStyles = await close.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      const borderRadius = parseFloat(computed.borderRadius);
      return {
        backgroundColor: computed.backgroundColor,
        borderRadius,
      };
    });
    expect(closeStyles.backgroundColor).toBe(CLOSE_BUTTON_RED_BG);
    expect(closeStyles.borderRadius).toBeGreaterThanOrEqual(CLOSE_BUTTON_BORDER_RADIUS_MIN);

    // Computed styles — labels (check the first label in standards button)
    const labelStyles = await standards.evaluate((el) => {
      // Find the text node/element within the button
      const textElement = Array.from(el.querySelectorAll("*")).find(
        (child) => child.textContent && child.textContent.includes("Thể lệ"),
      );
      if (!textElement) {
        return null;
      }
      const computed = window.getComputedStyle(textElement);
      return {
        fontWeight: computed.fontWeight,
        fontSize: computed.fontSize,
        lineHeight: computed.lineHeight,
        color: computed.color,
      };
    });

    // Non-null first: a missing label element would otherwise skip every
    // typography assertion below and still report the test as passed.
    expect(labelStyles).not.toBeNull();
    expect(labelStyles?.fontWeight).toBe(LABEL_FONT_WEIGHT);
    expect(labelStyles?.fontSize).toBe(LABEL_FONT_SIZE);
    expect(labelStyles?.lineHeight).toBe(LABEL_LINE_HEIGHT);
    expect(labelStyles?.color).toBe(LABEL_TEXT_COLOR);
  });
});
