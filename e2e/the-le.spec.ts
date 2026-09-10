import { expect, test } from "@playwright/test";

import {
  CLOSE_LABEL,
  COLLECTIBLE_CAPTIONS,
  COLLECTIBLE_ICON_COUNT,
  COMPOSE_ROUTE,
  HERO_TIER_COUNT,
  HERO_TIER_DESCRIPTIONS,
  HERO_TIER_LABELS,
  PANEL_TITLE,
  ROUTE,
  SECTION_2_CLOSING_BODY,
  SECTION_BODIES,
  SECTION_COUNT,
  SECTION_HEADINGS,
  WIDGET_STANDARDS_LABEL,
  WRITE_KUDOS_LABEL,
} from "./fixtures/the-le-constants";

/**
 * Screen-level E2E for Thể lệ (SCR007, `/standards`) — MoMorph screen
 * `b1Filzi9i6`, frame `3204:6051`.
 *
 * Test policy: **e2e-red-first**. This file is written and driven to a valid
 * assertion RED BEFORE any of `/standards` is implemented, and phase 08 reruns
 * the identical command for GREEN. The command is fixed:
 *
 *     npx playwright test e2e/the-le.spec.ts --project=anon
 *
 * Runs in the `anon` project: `/standards` is public — `proxy.ts` guards only
 * `/todo`, exact `/kudos/new` and `/profile` — so no session, no storageState,
 * no `createTestSession()`. The spec writes NO data, so it needs no cleanup
 * block; the feature's own seed rows are its fixture.
 *
 * Source test-case coverage (`design/test-cases.csv`, 9 cases):
 *
 * | Source case        | Here                       | Note |
 * |--------------------|----------------------------|------|
 * | TC_THELE_GUI_001   | GUI_001/002/005/006        | structure split by requirement |
 * | TC_THELE_GUI_002   | FUN_003 + FUN_004          | footer controls exist and act; their *styling* is a visual-contract concern |
 * | TC_THELE_GUI_003   | `test.skip` (DEC-002)      | asserts a disabled state this screen has none of |
 * | TC_THELE_GUI_004   | not asserted here          | hover restyle — clarifications.md assigns hover to the visual pass, not strict E2E |
 * | TC_THELE_FUN_001   | FUN_001                    | |
 * | TC_THELE_FUN_002   | FUN_002                    | |
 * | TC_THELE_FUN_003   | FUN_003 + FUN_003b         | history-return and deep-link fallback |
 * | TC_THELE_FUN_004   | FUN_004                    | DEC-001 — the compose surface is a route, not a modal |
 * | TC_THELE_FUN_005   | `test.skip` (DEC-002)      | same disabled state that does not exist |
 *
 * Every `data-testid` used below is fixed by
 * `plans/260909-0838-the-le-rules-panel/clarifications.md § "Test contract"`.
 * Vietnamese copy is read from `./fixtures/the-le-constants`, never inlined.
 */

test.describe("Thể lệ panel (/standards) — anon", () => {
  test("GUI_001 — FR-201: panel is a labelled dialog whose <h1> reads Thể lệ", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    await expect(page.getByRole("heading", { level: 1 })).toHaveText(PANEL_TITLE);

    const panel = page.getByTestId("rules-panel");
    await expect(panel).toBeVisible();
    await expect(panel).toHaveAttribute("role", "dialog");
    // AMENDED (phase 08 review): the panel must NOT claim `aria-modal`. It
    // implements no focus containment and deliberately lets a keyboard user
    // tab out to the header/footer — correct for a route rather than an
    // overlay — so declaring modality told assistive tech the rest of the
    // page did not exist while it stayed reachable. Asserted as absent so the
    // attribute cannot creep back in. See clarifications.md § Test contract.
    await expect(panel).not.toHaveAttribute("aria-modal", /.*/);
  });

  test("GUI_002 — FR-202/BR-001: three prose sections render in position order", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const sections = page.getByTestId("rules-section");
    await expect(sections).toHaveCount(SECTION_COUNT);

    // Comparing the i-th rendered section against the i-th designed heading is
    // what proves `order by position` (BR-001) — a set-membership check would
    // pass on any permutation.
    for (let i = 0; i < SECTION_COUNT; i++) {
      await expect(sections.nth(i)).toContainText(SECTION_HEADINGS[i]);
      await expect(sections.nth(i)).toContainText(SECTION_BODIES[i]);
    }

    // Section 2's closing line renders AFTER the icon grid, inside section 2.
    await expect(sections.nth(1)).toContainText(SECTION_2_CLOSING_BODY);
  });

  test("GUI_005 — FR-203/BR-001: four Hero tiers render in position order, each with artwork", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const tiers = page.getByTestId("rules-hero-tier");
    await expect(tiers).toHaveCount(HERO_TIER_COUNT);

    for (let i = 0; i < HERO_TIER_COUNT; i++) {
      const tier = tiers.nth(i);
      await expect(tier).toContainText(HERO_TIER_LABELS[i]);
      await expect(tier).toContainText(HERO_TIER_DESCRIPTIONS[i]);
      // FR-205 — badge pill served from `public/images/rules/`, path stored on the row.
      await expect(tier.locator("img")).toHaveCount(1);
    }
  });

  test("GUI_006 — FR-204/BR-001: six collectible icons render in position order, each with artwork", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const icons = page.getByTestId("rules-collectible-icon");
    await expect(icons).toHaveCount(COLLECTIBLE_ICON_COUNT);

    for (let i = 0; i < COLLECTIBLE_ICON_COUNT; i++) {
      const icon = icons.nth(i);
      await expect(icon).toContainText(COLLECTIBLE_CAPTIONS[i]);
      await expect(icon.locator("img")).toHaveCount(1);
    }
  });

  test("FUN_001 — FR-403: the content column scrolls independently when content overflows", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const content = page.getByTestId("rules-panel-content");
    await expect(content).toBeVisible();

    const metrics = await content.evaluate((el) => ({
      scrollHeight: el.scrollHeight,
      clientHeight: el.clientHeight,
    }));
    expect(metrics.scrollHeight).toBeGreaterThan(metrics.clientHeight);

    // "Scrolls and reaches the end of the content" — scroll to the bottom and
    // confirm the column actually moved and landed at the end, then back up.
    await content.evaluate((el) => el.scrollTo(0, el.scrollHeight));
    const bottom = await content.evaluate((el) => el.scrollTop);
    expect(bottom).toBeGreaterThan(0);
    expect(bottom).toBeGreaterThanOrEqual(metrics.scrollHeight - metrics.clientHeight - 2);

    await content.evaluate((el) => el.scrollTo(0, 0));
    expect(await content.evaluate((el) => el.scrollTop)).toBe(0);

    // FR-403 — the PAGE must not be what scrolls.
    const pageScrollable = await page.evaluate(
      () => document.documentElement.scrollHeight > document.documentElement.clientHeight + 2,
    );
    expect(pageScrollable).toBe(false);
  });

  test("FUN_002 — FR-403: no scroll distance when the panel is taller than its content", async ({
    page,
  }, testInfo) => {
    // The seeded content is longer than the 553x~900 design frame, so the
    // "content fits" precondition CANNOT be produced by deleting rows (that
    // would test an empty panel, not this requirement). It is produced by
    // raising the viewport, per the phase plan's ladder. Every measurement
    // taken is attached to the run so the real numbers are recorded rather
    // than guessed in a comment.
    const VIEWPORT_LADDER = [2400, 3200, 4000];
    const measurements: string[] = [];
    let metrics = { scrollHeight: 0, clientHeight: 0 };

    for (const height of VIEWPORT_LADDER) {
      await page.setViewportSize({ width: 1440, height });
      await page.goto(ROUTE);

      const content = page.getByTestId("rules-panel-content");
      await expect(content).toBeVisible();

      metrics = await content.evaluate((el) => ({
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight,
      }));
      measurements.push(
        `viewport 1440x${height} -> scrollHeight=${metrics.scrollHeight} clientHeight=${metrics.clientHeight}`,
      );
      if (metrics.scrollHeight <= metrics.clientHeight) break;
    }

    await testInfo.attach("fun_002-viewport-ladder", {
      body: measurements.join("\n"),
      contentType: "text/plain",
    });

    // Unconditional — if no viewport on the ladder ever fits the content, this
    // fails loudly with the last real measurement instead of silently passing.
    expect(metrics.scrollHeight).toBeLessThanOrEqual(metrics.clientHeight);
  });

  test("FUN_003 — FR-401: Đóng returns to the page the visitor came from", async ({ page }) => {
    // A genuine client-side history entry, not `page.goBack()` (that would test
    // the browser, not the button) and not a faked `history.pushState`. The
    // homepage's floating widget is now a disclosure trigger (phase 03) that
    // opens a menu holding the `/standards` shortcut behind it. See
    // `clarifications.md` § "Late finding — an existing test is coupled to the old shape".
    await page.goto("/");

    const trigger = page.getByTestId("fab-trigger");
    await expect(trigger).toBeVisible();
    await trigger.click();

    const standardsShortcut = page.getByTestId("fab-standards");
    await expect(standardsShortcut).toBeVisible();
    await expect(standardsShortcut).toHaveAccessibleName(WIDGET_STANDARDS_LABEL);
    await standardsShortcut.click();
    await expect(page).toHaveURL(new RegExp(`${ROUTE}$`));

    const closeButton = page.getByTestId("rules-close-button");
    await expect(closeButton).toBeVisible();
    await expect(closeButton).toContainText(CLOSE_LABEL);
    await closeButton.click();

    await expect(page).toHaveURL("http://127.0.0.1:3000/");
  });

  test("FUN_003b — BR-004: on a deep link with no history, Đóng falls back to /", async ({
    page,
  }) => {
    // Straight to the route with nothing behind it — the fallback branch of
    // FR-401. "Never a dead end."
    await page.goto(ROUTE);

    const closeButton = page.getByTestId("rules-close-button");
    await expect(closeButton).toBeVisible();
    await closeButton.click();

    await expect(page).toHaveURL("http://127.0.0.1:3000/");
  });

  test("FUN_004 — FR-402/BR-005: Viết KUDOS is an anchor pointing at the compose route", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const link = page.getByTestId("rules-write-kudos-link");
    await expect(link).toBeVisible();
    await expect(link).toContainText(WRITE_KUDOS_LABEL);

    // Asserted by ATTRIBUTE, deliberately not by navigating: under `anon` a
    // real click hits `proxy.ts`'s guard on `/kudos/new` and lands on `/login`,
    // which would turn a content test into a guard test. BR-005 — this screen
    // does not duplicate that rule, and `route-guard.spec.ts` already owns it.
    await expect(link).toHaveAttribute("href", COMPOSE_ROUTE);
  });

  // DEC-002 — `TC_THELE_GUI_003` asserts a footer button rendered dimmed in a
  // disabled state. NOT APPLICABLE to this screen: `Đóng` always closes and
  // `Viết KUDOS` always navigates; no state, loading included, makes either
  // unavailable. Building a `disabled` prop nothing can set would be dead code,
  // and staging a fake dimmed button to turn this green is exactly what
  // `primary-workflow.md` forbids. Carried here as a skip so the gap shows in
  // the suite output instead of vanishing.
  test.skip("GUI_003 — TC_THELE_GUI_003: disabled footer button is dimmed (DEC-002: no disabled state exists on this screen)", () => {});

  // DEC-002 — `TC_THELE_FUN_005`, the click half of the same non-existent
  // disabled state. Same reason, same treatment.
  test.skip("FUN_005 — TC_THELE_FUN_005: disabled footer button rejects clicks (DEC-002: no disabled state exists on this screen)", () => {});
});
