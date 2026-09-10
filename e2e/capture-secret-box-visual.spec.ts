import { expect, test } from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";

import {
  TEST_IDS,
  GEOMETRY_VIEWPORT,
  ROUTE,
} from "./fixtures/secret-box-constants";
import {
  setUnopenedCount,
  clearOpenings,
} from "./fixtures/secret-box-grant";

/**
 * Load test user credentials (created by secret-box-auth.setup.ts)
 */
function loadCredentials() {
  const credentialsPath = path.join(process.cwd(), "e2e/.auth/secret-box-credentials.json");
  const content = fs.readFileSync(credentialsPath, "utf-8");
  return JSON.parse(content) as {
    email: string;
    password: string;
    userId: string;
    sunnerId: string;
  };
}

/**
 * VISUAL VALIDATION CAPTURE — Secret Box (F009)
 * Captures the authed states at the design viewport so
 * plans/260910-1708-open-secret-box/evidence/ stays reproducible.
 * Runs on demand only with explicit environment flag: RUN_CAPTURE_TESTS=1 npx playwright test capture-secret-box-visual.
 *
 * States captured:
 * - Authed with boxes (grant 5, count 05, instruction visible, box interactive)
 * - Authed after one open (badge awarded and centered, count decremented, re-render)
 * - Mobile viewport (390×844) at authed with boxes
 */

const EVIDENCE_DIR = "plans/260910-1708-open-secret-box/evidence";

(process.env.RUN_CAPTURE_TESTS !== "1" ? test.describe.skip : test.describe)(
  "Visual Capture — Secret Box (chưa mở)",
  () => {
  let credentials: ReturnType<typeof loadCredentials>;

  test.beforeAll(() => {
    credentials = loadCredentials();
  });

  test("capture authed with unopened boxes at 1440x1024", async ({
    page,
  }) => {
    await page.setViewportSize({
      width: GEOMETRY_VIEWPORT.width,
      height: GEOMETRY_VIEWPORT.height,
    });

    // Grant 5 unopened boxes via the service-role fixture
    await setUnopenedCount(credentials.userId, 5);
    await clearOpenings(credentials.userId);

    // Navigate to the secret box screen
    await page.goto(ROUTE);
    await page.waitForLoadState("networkidle");

    const panel = page.getByTestId(TEST_IDS.panel);
    await expect(panel).toBeVisible();

    // Authed with boxes: count 05, instruction visible, opener interactive
    const count = page.getByTestId(TEST_IDS.count);
    await expect(count).toContainText("05");

    const instruction = page.getByTestId(TEST_IDS.instruction);
    await expect(instruction).toBeVisible();

    const opener = page.getByTestId(TEST_IDS.opener);
    await expect(opener).toBeEnabled();

    await page.screenshot({ path: `${EVIDENCE_DIR}/secret-box-entitled-1440.png` });
    console.log("✓ Authed with boxes captured at 1440x1024");
  });

  test("capture authed after opening one box at 1440x1024", async ({
    page,
  }) => {
    await page.setViewportSize({
      width: GEOMETRY_VIEWPORT.width,
      height: GEOMETRY_VIEWPORT.height,
    });

    // Grant 2 unopened boxes so we can open one and still see count > 0
    await setUnopenedCount(credentials.userId, 2);
    await clearOpenings(credentials.userId);

    // Navigate to the secret box screen
    await page.goto(ROUTE);
    await page.waitForLoadState("networkidle");

    // Click the opener to trigger the open action
    const opener = page.getByTestId(TEST_IDS.opener);
    await expect(opener).toBeVisible();
    await opener.click();

    // Wait for the server action to complete and the badge to render
    await page.waitForLoadState("networkidle");
    const badge = page.getByTestId(TEST_IDS.badge);
    await expect(badge).toBeVisible();

    // Verify counter decremented
    const count = page.getByTestId(TEST_IDS.count);
    await expect(count).toContainText("01");

    await page.screenshot({ path: `${EVIDENCE_DIR}/secret-box-opened-1440.png` });
    console.log("✓ Opened state captured at 1440x1024");
  });

  test("capture authed with boxes at 390x844 (mobile viewport check)", async ({
    page,
  }) => {
    await page.setViewportSize({
      width: 390,
      height: 844,
    });

    // Grant boxes
    await setUnopenedCount(credentials.userId, 5);
    await clearOpenings(credentials.userId);

    // Navigate to the secret box screen
    await page.goto(ROUTE);
    await page.waitForLoadState("networkidle");

    const panel = page.getByTestId(TEST_IDS.panel);
    await expect(panel).toBeVisible();

    const count = page.getByTestId(TEST_IDS.count);
    await expect(count).toContainText("05");

    // Capture the mobile viewport state (card has fixed max-w of 651.5px,
    // so horizontal overflow on 390px viewport is expected)
    await page.screenshot({ path: `${EVIDENCE_DIR}/secret-box-entitled-390.png` });
    console.log("✓ Mobile viewport captured at 390x844");
  });
  }
);
