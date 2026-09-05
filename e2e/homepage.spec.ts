import { expect, test, type Page } from "@playwright/test";

test.describe("Homepage SAA — Anonymous Visitor (anon project)", () => {
  // ID-0: Homepage loads publicly for an unauthenticated visitor
  test("ID-0 [FR-100] — homepage loads publicly without authentication", async ({
    page,
  }) => {
    await page.goto("/");
    // Should not redirect to login
    expect(page.url()).toBe("http://127.0.0.1:3000/");
    // Body should have content
    await expect(page.locator("body")).not.toBeEmpty();
  });

  // ID-7: Overall structure — header, hero, countdown, awards grid, Kudos section, floating widget, footer
  test("ID-7 [FR-101] — page structure includes header, hero, countdown, awards grid, Kudos section, and footer", async ({
    page,
  }) => {
    await page.goto("/");

    // Header (should contain nav)
    const header = page.getByRole("banner");
    await expect(header).toBeVisible();

    // Hero section — check for the ROOT FURTHER wordmark image or the countdown section
    const mainContent = page.locator("main");
    const countdown = page.getByText(/days/i);
    await expect(countdown).toBeVisible();

    // Countdown section (will contain DAYS / HOURS / MINUTES)
    const hoursLabel = page.getByText(/hours/i);
    await expect(hoursLabel).toBeVisible();

    // Awards grid (should contain at least one award category)
    const awardGrid = page.getByTestId("awards-grid");
    await expect(awardGrid).toBeVisible();

    // Kudos section (Sun* Kudos heading) — scope to main content to avoid footer match
    const kudosSection = mainContent.locator("section").filter({
      has: page.getByText("Sun* Kudos", { exact: true })
    });
    await expect(kudosSection).toBeVisible();

    // Footer (contentinfo landmark)
    const footer = page.getByRole("contentinfo");
    await expect(footer).toBeVisible();
  });

  // ID-9: "About SAA 2025" nav item rendered in the selected state
  test("ID-9 [FR-102] — About SAA 2025 nav item is marked as selected on homepage", async ({
    page,
  }) => {
    await page.goto("/");

    // Find the "About SAA 2025" link in the header nav — should have selected styling (border-b)
    const header = page.getByRole("banner");
    const aboutLink = header.getByRole("link", { name: "About SAA 2025" });
    await expect(aboutLink).toBeVisible();

    // Check for selected state — the SELECTED_CLASS has "border-b border-[#FFEA9E]"
    const hasSelectedBorder = await aboutLink.evaluate((el) => {
      const classes = el.className || "";
      return classes.includes("border-b") && classes.includes("FFEA9E");
    });

    expect(hasSelectedBorder).toBeTruthy();
  });

  // ID-12: Countdown renders three 2-digit units labelled DAYS / HOURS / MINUTES
  test("ID-12 [FR-103] — countdown displays three 2-digit units labeled DAYS, HOURS, MINUTES", async ({
    page,
  }) => {
    await page.goto("/");

    // Find the countdown section
    const daysLabel = page.getByText(/days/i);
    const hoursLabel = page.getByText(/hours/i);
    const minutesLabel = page.getByText(/minutes/i);

    await expect(daysLabel).toBeVisible();
    await expect(hoursLabel).toBeVisible();
    await expect(minutesLabel).toBeVisible();

    // Each unit should show a 2-digit value (00-99)
    const countdownValues = page.locator("[data-testid='countdown-value']");
    const count = await countdownValues.count();
    expect(count).toBeGreaterThanOrEqual(3);

    // Verify each value is 2 digits
    for (let i = 0; i < Math.min(3, count); i++) {
      const text = await countdownValues.nth(i).textContent();
      expect(text).toMatch(/^\d{2}$/);
    }
  });

  // ID-13: "Coming soon" visible while the event is in the future
  test("ID-13 [FR-104] — Coming soon label visible when event is in the future", async ({
    page,
  }) => {
    await page.goto("/");

    // Event start time from clarifications is 2025-12-26, which is in the future
    // "Coming soon" should be visible
    const comingSoon = page.getByText(/coming soon/i);
    await expect(comingSoon).toBeVisible();
  });

  // ID-14: Event info block copy (26/12/2025, Âu Cơ Art Center, livestream note)
  test("ID-14 [FR-105] — event information block displays correct date, venue, and livestream note", async ({
    page,
  }) => {
    await page.goto("/");

    // Date: 26/12/2025
    const dateText = page.getByText(/26\/12\/2025|26.12.2025/);
    await expect(dateText).toBeVisible();

    // Venue: Âu Cơ Art Center
    const venueText = page.getByText(/âu cơ art center/i);
    await expect(venueText).toBeVisible();

    // Livestream note
    const livestreamText = page.getByText(/livestream|tường thuật/i);
    await expect(livestreamText).toBeVisible();
  });

  // ID-15: Awards grid shows 6 cards
  test("ID-15 [FR-106] — awards grid displays all 6 award category cards", async ({
    page,
  }) => {
    await page.goto("/");

    // Scope to the awards grid to avoid multi-match issues
    const awardGrid = page.getByTestId("awards-grid");
    await expect(awardGrid).toBeVisible();

    // Check that we have exactly 6 award cards with data-testid
    const awardCards = awardGrid.locator("[data-testid^='award-card-']");
    const cardCount = await awardCards.count();
    expect(cardCount).toBe(6);
  });

  // ID-16: Awards grid responsive — 3 columns at desktop, 2 columns at tablet/mobile
  test("ID-16 [FR-107] — awards grid is responsive: 3 columns at desktop, 2 columns at tablet/mobile", async ({
    page,
  }) => {
    await page.goto("/");

    // Set desktop viewport (>= 1024px)
    await page.setViewportSize({ width: 1280, height: 800 });

    // Check grid layout at desktop — should have 3 columns
    const awardCards = page.locator("[data-testid='award-card']");
    const cardCount = await awardCards.count();
    expect(cardCount).toBe(6);

    // Check CSS grid columns for desktop — count space-separated tokens in gridTemplateColumns
    // A rendered grid resolves grid-cols-3 to "336px 336px 336px" (3 tokens), not the literal "repeat(3"
    const gridContainer = page.locator("[data-testid='awards-grid']");
    const gridColsDesktopTokens = await gridContainer.evaluate((el) => {
      const style = window.getComputedStyle(el);
      const cols = style.gridTemplateColumns.trim().split(/\s+/).length;
      return cols;
    });
    expect(gridColsDesktopTokens).toBe(3);

    // Set tablet viewport (< 1024px, >= 768px)
    await page.setViewportSize({ width: 800, height: 600 });
    await page.waitForTimeout(500); // Allow layout to recalculate

    // Check CSS grid columns for tablet — should have 2 tokens
    const gridColsTabletTokens = await gridContainer.evaluate((el) => {
      const style = window.getComputedStyle(el);
      const cols = style.gridTemplateColumns.trim().split(/\s+/).length;
      return cols;
    });
    expect(gridColsTabletTokens).toBe(2);

    // Set mobile viewport (< 768px)
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);

    // Check CSS grid columns for mobile — should have 2 tokens
    const gridColsMobileTokens = await gridContainer.evaluate((el) => {
      const style = window.getComputedStyle(el);
      const cols = style.gridTemplateColumns.trim().split(/\s+/).length;
      return cols;
    });
    expect(gridColsMobileTokens).toBe(2);
  });

  // ID-17: Footer contains logo, nav links, and copyright text
  test("ID-17 [FR-108] — footer displays logo, navigation links, and copyright text", async ({
    page,
  }) => {
    await page.goto("/");

    const footer = page.getByRole("contentinfo");
    await expect(footer).toBeVisible();

    // Logo may be present in footer; if not found, that's a separate concern
    // but we can check for its presence
    const logoCount = await footer.locator("img").count();
    expect(logoCount).toBeGreaterThan(0);

    // Footer nav links (About SAA 2025, Award Information, Sun* Kudos, etc.)
    const aboutLink = footer.getByRole("link", { name: /about saa 2025/i });
    const awardLink = footer.getByRole("link", { name: /award information/i });
    const kudosLink = footer.getByRole("link", { name: /kudos/i });

    await expect(aboutLink).toBeVisible();
    await expect(awardLink).toBeVisible();
    await expect(kudosLink).toBeVisible();

    // Copyright text: "Bản quyền thuộc về Sun* © 2025"
    const copyright = footer.getByText(/bản quyền.*sun.*©.*2025|copyright.*sun.*2025/i);
    await expect(copyright).toBeVisible();
  });

  // ID-18: Header logo navigates to home from non-home route
  test("ID-18 [FR-108b] — header logo navigates to home from non-home route", async ({
    page,
  }) => {
    // Navigate to a non-home route (e.g., awards-information)
    await page.goto("/awards-information");
    expect(page.url()).toContain("/awards-information");

    // The logo's accessible name is dictionary.header.logoAlt, which is the
    // same string in vi and en. Matched exactly rather than by /logo|saa/i,
    // which also matches the nav's "About SAA 2025" link and would force a
    // .first() — the masking ORCH-05 forbids.
    const header = page.getByRole("banner");
    const headerLogoLink = header.getByRole("link", {
      name: "Sun* Annual Awards 2025",
      exact: true,
    });
    await expect(headerLogoLink).toBeVisible();

    // Click the header logo link — should navigate to home
    await headerLogoLink.click();
    await page.waitForURL("/");
    expect(page.url()).toBe("http://127.0.0.1:3000/");
  });

  // ID-19: Footer logo navigates to home from non-home route
  test("ID-19 [FR-108c] — footer logo navigates to home from non-home route", async ({
    page,
  }) => {
    // Navigate to a non-home route (e.g., awards-information)
    await page.goto("/awards-information");
    expect(page.url()).toContain("/awards-information");

    // Exact accessible name, same reasoning as ID-18 — the footer also
    // carries an "About SAA 2025" nav link that a loose regex would match.
    const footer = page.getByRole("contentinfo");
    const footerLogoLink = footer.getByRole("link", {
      name: "Sun* Annual Awards 2025",
      exact: true,
    });
    await expect(footerLogoLink).toBeVisible();

    // Click the footer logo link — should navigate to home
    await footerLogoLink.click();
    await page.waitForURL("/");
    expect(page.url()).toBe("http://127.0.0.1:3000/");
  });

  // ID-39: Countdown values decrease in real time without a page reload
  test("ID-39 [FR-109] — countdown decreases in real time without a page reload", async ({
    page,
  }) => {
    // Navigate to homepage
    await page.goto("/");

    // Read initial countdown state — record all three to handle any timing scenario
    const countdownValues = page.locator("[data-testid='countdown-value']");
    const samples: Array<{ days: string; hours: string; minutes: string }> = [];

    // Collect samples over ~3 seconds to capture at least one interval tick
    for (let i = 0; i < 6; i++) {
      const days = await countdownValues.nth(0).textContent();
      const hours = await countdownValues.nth(1).textContent();
      const minutes = await countdownValues.nth(2).textContent();
      samples.push({ days: days || "", hours: hours || "", minutes: minutes || "" });

      // Wait 500ms between samples
      if (i < 5) await page.waitForTimeout(500);
    }

    // Verify at least 2 distinct countdown states across the samples
    // This proves the component updated without a page reload
    const distinctStates = new Set(samples.map((s) => `${s.days}:${s.hours}:${s.minutes}`));
    expect(distinctStates.size).toBeGreaterThan(1);
  });

  // ID-2/ID-3/ID-4/ID-20: Nav item behaviour — navigate from non-home, scroll-to-top when already selected
  test("ID-2/3/4/20 [FR-117] — nav items navigate to home from non-home route; clicking selected nav item scrolls to top instead of navigating", async ({
    page,
  }) => {
    // Part 1: From a non-home route, clicking "About SAA 2025" navigates to home (ID-2)
    await page.goto("/awards-information");
    expect(page.url()).toContain("/awards-information");

    // Click "About SAA 2025" in the header nav
    const header = page.getByRole("banner");
    const aboutLink = header.getByRole("link", { name: "About SAA 2025" });
    await aboutLink.click();

    // Should navigate to home
    await page.waitForURL("/");
    expect(page.url()).toBe("http://127.0.0.1:3000/");

    // Part 2: On home, clicking already-selected "About SAA 2025" scrolls to top instead of navigating (ID-3)
    // First scroll down
    await page.evaluate(() => window.scrollTo(0, 500));
    const scrollBefore = await page.evaluate(() => window.scrollY);
    expect(scrollBefore).toBeGreaterThan(0);

    // Click the already-selected "About SAA 2025" link
    await aboutLink.click();

    // URL should remain unchanged (no navigation)
    expect(page.url()).toBe("http://127.0.0.1:3000/");

    // Should have scrolled to top
    await page.waitForTimeout(500); // Wait for smooth scroll
    const scrollAfter = await page.evaluate(() => window.scrollY);
    expect(scrollAfter).toBeLessThan(scrollBefore);
  });

  // ID-20: Footer logo scrolls to top when on home
  test("ID-20 [FR-118] — footer logo scrolls to top when clicked on homepage", async ({
    page,
  }) => {
    // Navigate to homepage
    await page.goto("/");

    // Scroll down
    await page.evaluate(() => window.scrollTo(0, 500));
    const scrollBefore = await page.evaluate(() => window.scrollY);
    expect(scrollBefore).toBeGreaterThan(0);

    // Click the footer logo — find by href="/" in footer
    const footer = page.getByRole("contentinfo");
    // The footer logo link has href="/" and aria-label matching the logo alt text
    // Use a CSS selector to find it: footer a[href="/"]
    const footerLogoLink = footer.locator('a[href="/"]').first();
    await footerLogoLink.click();

    // URL should remain unchanged (no navigation because smooth scroll intercepts the default)
    expect(page.url()).toBe("http://127.0.0.1:3000/");

    // Should have scrolled to top — wait for smooth scroll animation to complete
    await page.waitForTimeout(800); // Wait longer for smooth scroll to complete
    const scrollAfter = await page.evaluate(() => window.scrollY);
    expect(scrollAfter).toBeLessThan(scrollBefore);
  });

  // ID-41/42/43: "Coming soon" hidden and counter at 00 once event time has passed
  test("ID-41/42/43 [FR-110] — when event time passes, Coming soon hides and countdown holds at 00", async ({
    page,
  }) => {
    // ORCH-02/ORCH-06: Test that "Coming soon" label's visibility is tied to event time.
    // When event time is in the future, label is visible; when past, it's hidden.

    // Navigate to homepage
    await page.goto("/");

    // Install the clock before first navigation so we control all time
    await page.clock.install();

    // Get the NEXT_PUBLIC_EVENT_START_AT value from the page's environment
    // For now, we know it's pinned to ~45 days in the future by playwright.config.ts
    // Set the clock to now (initial state before time travel)
    await page.clock.setFixedTime(new Date());

    // Reload with clock installed to assert LIVE state
    await page.reload();

    // Assert LIVE state: "Coming soon" should be visible
    const comingSoonLive = page.getByText(/coming soon/i);
    await expect(comingSoonLive).toBeVisible();

    // Now fast-forward 50 days into the future (beyond the pinned event time)
    const futureTime = new Date();
    futureTime.setDate(futureTime.getDate() + 50);
    await page.clock.setFixedTime(futureTime);

    // Reload the page with the future clock time
    await page.reload();

    // Assert EXPIRED state: "Coming soon" should be hidden
    const comingSoonExpired = page.getByText(/coming soon/i);
    await expect(comingSoonExpired).not.toBeVisible();

    // Countdown values should all be 00
    const countdownValuesExpired = page.locator("[data-testid='countdown-value']");
    const countExpired = await countdownValuesExpired.count();
    for (let i = 0; i < Math.min(3, countExpired); i++) {
      const text = await countdownValuesExpired.nth(i).textContent();
      expect(text).toBe("00");
    }
  });

  // ID-24/ID-30..35: Language menu — click opens, click closes, outside click closes, Enter/Space open, Esc closes
  test("ID-24/30-35 [FR-111] — language menu: click opens/closes, outside click closes, Enter/Space open, Esc closes", async ({
    page,
  }) => {
    await page.goto("/");

    // Find language button by aria-haspopup="listbox" — more specific than just role
    const langButton = page.locator('button[aria-haspopup="listbox"]');
    await expect(langButton).toBeVisible();

    // Click to open
    await langButton.click();
    const listbox = page.getByRole("listbox");
    await expect(listbox).toBeVisible();

    // Click to close
    await langButton.click();
    await expect(listbox).not.toBeVisible();

    // Open again
    await langButton.click();
    await expect(listbox).toBeVisible();

    // Outside click closes
    await page.locator("main").click({ position: { x: 100, y: 300 } });
    await expect(listbox).not.toBeVisible();

    // Test keyboard: Space opens
    await langButton.focus();
    await page.keyboard.press("Space");
    await expect(listbox).toBeVisible();

    // Esc closes
    await page.keyboard.press("Escape");
    await expect(listbox).not.toBeVisible();

    // Test keyboard: Enter opens
    await langButton.focus();
    await page.keyboard.press("Enter");
    await expect(listbox).toBeVisible();
  });

  // ID-25/ID-26: Selecting EN switches the interface to English and back to VN
  test("ID-25/26 [FR-112] — selecting EN in language menu switches UI to English, selecting VN reverts to Vietnamese", async ({
    page,
  }) => {
    await page.goto("/");

    // Default should be Vietnamese — check for Vietnamese content (awards section title)
    // "Hệ thống giải thưởng" is the Vietnamese awards grid title
    await expect(page.getByText("Hệ thống giải thưởng")).toBeVisible();

    // Open language selector
    const langButton = page.locator('button[aria-haspopup="listbox"]');
    await langButton.click();

    // Select EN
    const enOption = page.getByRole("option", { name: /en|english/i });
    await enOption.click();

    // Wait for content to re-render in English — check for English awards title
    await expect(page.getByText("Award System")).toBeVisible();

    // Verify NEXT_LOCALE cookie is set to "en"
    await expect
      .poll(async () => {
        const cookies = await page.context().cookies();
        return cookies.find((c) => c.name === "NEXT_LOCALE")?.value;
      })
      .toBe("en");

    // Switch back to VN
    await langButton.click();
    const vnOption = page.getByRole("option", { name: /vn|vietnamese/i });
    await vnOption.click();

    // Wait for Vietnamese content to return — check for Vietnamese awards title
    await expect(page.getByText("Hệ thống giải thưởng")).toBeVisible();

    // Verify NEXT_LOCALE cookie is back to "vi"
    await expect
      .poll(async () => {
        const cookies = await page.context().cookies();
        return cookies.find((c) => c.name === "NEXT_LOCALE")?.value;
      })
      .toBe("vi");
  });

  // ID-44/ID-45: CTA buttons navigate to Awards Information and Sun* Kudos
  test("ID-44/45 [FR-113] — CTA buttons navigate to Awards Information and Kudos routes", async ({
    page,
  }) => {
    await page.goto("/");

    // Find "ABOUT AWARDS" button and click
    const aboutAwardsBtn = page.getByRole("button", {
      name: /about awards|award information/i,
    });
    await aboutAwardsBtn.click();
    await page.waitForURL(/\/awards-information/);
    expect(page.url()).toContain("/awards-information");

    // Go back to homepage
    await page.goto("/");

    // Find "ABOUT KUDOS" button and click
    const aboutKudosBtn = page.getByRole("button", {
      name: /about kudos|sun.*kudos/i,
    });
    await aboutKudosBtn.click();
    await page.waitForURL(/\/kudos/);
    expect(page.url()).toContain("/kudos");
  });

  // ID-47/48/49/50/52: Award card navigates — image, title, and "Chi tiết" all link to /awards-information#<slug>
  test("ID-47/48/49/50/52 [FR-114] — award card (image, title, Chi tiết) navigates to /awards-information#<slug>", async ({
    page,
  }) => {
    await page.goto("/");

    // Expected award slugs from clarifications
    const awards = [
      "top-talent",
      "top-project",
      "top-project-leader",
      "best-manager",
      "signature-2025-creator",
      "mvp",
    ];

    for (const slug of awards) {
      // Find the award card for this slug
      const card = page.locator(`[data-testid='award-card-${slug}']`);
      await card.click();

      // Verify navigation to /awards-information#<slug>
      await page.waitForURL(/\/awards-information/);
      expect(page.url()).toContain(`/awards-information`);
      expect(page.url()).toContain(`#${slug}`);

      // Go back to homepage
      await page.goto("/");
    }
  });

  // ID-53: Kudos "Chi tiết" navigates to kudos route
  test("ID-53 [FR-115] — Kudos section Chi tiết button navigates to /kudos", async ({
    page,
  }) => {
    await page.goto("/");

    // Find the Kudos section by scoping to the section that contains "Sun* Kudos" text
    // Use exact match to scope to the Kudos promo section, not other elements
    const kudosSection = page.locator("section").filter({
      has: page.getByText("Sun* Kudos", { exact: true })
    });
    await expect(kudosSection).toBeVisible();

    // Find and click the "Chi tiết" link within that section
    const detailLink = kudosSection.getByRole("link", { name: /chi tiết/i });
    await detailLink.click();

    // Verify navigation to /kudos
    await page.waitForURL(/\/kudos/);
    expect(page.url()).toContain("/kudos");
  });

  // ID-55/ID-59: Every footer link resolves — assert no 404s
  test("ID-55/59 [FR-116] — all footer links resolve without 404 errors", async ({
    page,
  }) => {
    await page.goto("/");

    const footer = page.getByRole("contentinfo");
    const links = footer.getByRole("link");
    const linkCount = await links.count();

    expect(linkCount).toBeGreaterThan(0);

    // Track response status for each link
    for (let i = 0; i < linkCount; i++) {
      const link = links.nth(i);
      const href = await link.getAttribute("href");

      if (!href || href.startsWith("javascript:") || href.startsWith("#")) {
        // Skip non-navigable links
        continue;
      }

      // Check if link is internal
      if (href.startsWith("/")) {
        const response = await page.goto(href);
        expect(response?.status()).toBeLessThan(400);

        // Go back to homepage
        await page.goto("/");
      }
    }
  });
});
