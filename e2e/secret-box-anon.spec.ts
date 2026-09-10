import { test, expect } from "@playwright/test";
import { ROUTE, TEST_IDS, STRINGS, GEOMETRY, GEOMETRY_VIEWPORT } from "./fixtures/secret-box-constants";
import path from "node:path";
import fs from "node:fs";

test.describe("Secret Box — Anonymous", () => {
  // SB-A1: 200, main and main h1 visible, title correct (K-21's contract, restated)
  // FR-001, FR-101
  test("SB-A1: route returns 200, main h1 visible, title correct", async ({
    page,
  }) => {
    // FR-001: route is public, returns 200
    const response = await page.goto(ROUTE);
    expect(response?.status()).toBe(200);

    // FR-101: <h1> inside <main> with correct title text
    const main = page.locator("main");
    await expect(main).toBeVisible();

    const h1 = main.locator("h1");
    await expect(h1).toBeVisible();
    await expect(h1).toHaveText(STRINGS.title);
  });

  // SB-A2: counter reads 00, instruction line absent, opener not operable, sign-in link present
  // FR-105, FR-202
  test("SB-A2: anonymous face shows 00, instruction hidden, opener disabled, sign-in link visible", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Panel must be visible
    const panel = page.getByTestId(TEST_IDS.panel);
    await expect(panel).toBeVisible();

    // FR-105: counter reads 00 and is visible
    const counter = page.getByTestId(TEST_IDS.count);
    await expect(counter).toBeVisible();
    await expect(counter).toHaveText("00");

    // FR-105 & FR-102: instruction line absent (hidden at count 0)
    const instruction = page.getByTestId(TEST_IDS.instruction);
    await expect(instruction).not.toBeVisible();

    // FR-202: opener present AND disabled (not operable)
    const opener = page.getByTestId(TEST_IDS.opener);
    await expect(opener).toBeVisible();
    await expect(opener).toBeDisabled();

    // FR-105: sign-in link present and visible
    const signInLink = page.getByTestId(TEST_IDS.signIn);
    await expect(signInLink).toBeVisible();
  });

  // SB-A3: anon rpc('open_secret_box') with anon key is refused (no execute grant)
  // PERM018
  test("SB-A3: anon rpc call is refused by permissions", async () => {
    // Get the anon key
    const envPath = path.join(process.cwd(), ".env.local");
    const envContent = fs.readFileSync(envPath, "utf-8");
    let anonKey = "";
    envContent.split("\n").forEach((line) => {
      const trimmed = line.trim();
      if (trimmed.startsWith("NEXT_PUBLIC_SUPABASE_ANON_KEY")) {
        const [, ...valueParts] = trimmed.split("=");
        anonKey = valueParts.join("=").trim();
      }
    });

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "http://127.0.0.1:54321";

    // PERM018: anon role has no EXECUTE grant on open_secret_box
    const response = await fetch(
      `${supabaseUrl}/rest/v1/rpc/open_secret_box`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${anonKey}`,
          "X-Client-Info": "supabase-js/2",
        },
        body: JSON.stringify({}),
      },
    );

    // Should be refused (403 Forbidden or 401 Unauthorized)
    expect(response.status).toBeGreaterThanOrEqual(400);
    expect(response.status).toBeLessThan(500);
  });

  // SB-A4: geometry at 1440 × 1024 against design/geometry.md
  // design contract
  test("SB-A4: card geometry matches design at 1440 × 1024", async ({
    page,
  }) => {
    // Set viewport to the design spec size
    await page.setViewportSize({
      width: GEOMETRY_VIEWPORT.width,
      height: GEOMETRY_VIEWPORT.height,
    });

    await page.goto(ROUTE);

    // Get the main card panel
    const panel = page.getByTestId(TEST_IDS.panel);
    await expect(panel).toBeVisible();

    // Assert card width and height (with small tolerance for fractional rendering)
    const box = await panel.boundingBox();
    expect(box).toBeTruthy();

    if (box) {
      const tolerance = 2; // px tolerance for rounding
      expect(Math.abs(box.width - GEOMETRY.frameWidth)).toBeLessThan(tolerance);
      expect(Math.abs(box.height - GEOMETRY.frameHeight)).toBeLessThan(tolerance);
    }

    // Assert border radius (via computed style)
    const borderRadius = await panel.evaluate((el) =>
      window.getComputedStyle(el).borderRadius,
    );
    // MoMorph design: 12.73px border-radius
    expect(borderRadius).toContain("12");

    // Assert background color
    const bgColor = await panel.evaluate((el) =>
      window.getComputedStyle(el).backgroundColor,
    );
    // Verify it's dark (close to #00101A, which is rgb(0, 16, 26))
    expect(bgColor).toMatch(/rgb\(0,\s*\d{1,2},\s*\d{1,2}\)/);

    // Assert title is visible and styled
    const title = panel.locator("h1");
    await expect(title).toHaveText(STRINGS.title);
    const titleColor = await title.evaluate((el) =>
      window.getComputedStyle(el).color,
    );
    // Verify yellow-ish color (#FFEA9E = rgb(255, 234, 158))
    expect(titleColor).toMatch(/rgb\(255,/);

    // Assert box image is present and sized
    const boxImage = panel.getByAltText(/box|hộp/i);
    await expect(boxImage).toBeVisible();
    const boxImageBox = await boxImage.boundingBox();
    if (boxImageBox) {
      const imageTolerance = 2;
      expect(Math.abs(boxImageBox.width - GEOMETRY.boxImage.size)).toBeLessThan(
        imageTolerance,
      );
      expect(Math.abs(boxImageBox.height - GEOMETRY.boxImage.size)).toBeLessThan(
        imageTolerance,
      );
    }

    // Assert counter section is centered and readable
    const counter = page.getByTestId(TEST_IDS.count);
    await expect(counter).toHaveText("00");
    const counterText = await counter.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return {
        color: style.color,
        fontSize: style.fontSize,
      };
    });
    expect(counterText.color).toMatch(/rgb\(255,/); // Yellow, like #FFEA9E
  });
});
