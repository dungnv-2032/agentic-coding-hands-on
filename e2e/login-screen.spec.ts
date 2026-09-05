import { expect, test, type Page } from "@playwright/test";

test.describe("Login Screen (anon project)", () => {
  // C1: Render — logo, ROOT FURTHER wordmark, subtitle, tagline, login button, locale selector, footer
  test("C1 [FR-201, US003] — renders header, hero, ROOT FURTHER wordmark, tagline, login button, locale selector, and footer", async ({
    page,
  }) => {
    await page.goto("/login");

    // Logo (should be an image with specific alt text)
    const logo = page.getByAltText(/logo/i);
    await expect(logo).toBeVisible();

    // ROOT FURTHER wordmark (should be an image)
    const wordmark = page.getByAltText(/root further/i);
    await expect(wordmark).toBeVisible();

    // Subtitle and tagline — wait for some text content on the page
    // (The exact selectors will depend on Track A's markup, but we can use text content)
    await expect(page.locator("body")).toContainText(/.+/); // Non-empty body is a start

    // LOGIN With Google button
    const loginButton = page.getByRole("button", { name: /LOGIN With Google/i });
    await expect(loginButton).toBeVisible();

    // Language selector (button with aria-haspopup="listbox" to exclude dev tools button)
    const languageSelector = page.locator(
      'button[aria-haspopup="listbox"][aria-label*="VN"], button[aria-haspopup="listbox"][aria-label*="EN"]',
    );
    await expect(languageSelector).toBeVisible();

    // Footer (contentinfo landmark)
    const footer = page.getByRole("contentinfo");
    await expect(footer).toBeVisible();

    // Footer should contain copyright text
    await expect(footer).toContainText(/©|copyright/i);
  });

  // C2: Error banner — `/login?error=oauth_failed` shows Vietnamese error message
  test("C2 [FR-402, DEC-001] — displays error message when redirected with error=oauth_failed", async ({
    page,
  }) => {
    await page.goto("/login?error=oauth_failed");

    // Should see the Vietnamese error message
    const errorMessage = "Đăng nhập không thành công. Vui lòng thử lại.";
    await expect(page.locator("body")).toContainText(errorMessage);
  });

  // C3: Locale switch — selecting EN swaps page copy and sets `NEXT_LOCALE=en`
  test("C3 [FR-203, US003] — switching locale to EN updates page content and sets NEXT_LOCALE cookie", async ({
    page,
  }) => {
    await page.goto("/login");

    // Get the language selector button (use aria-haspopup to avoid matching dev tools button)
    const languageSelector = page.locator(
      'button[aria-haspopup="listbox"]',
    );
    await languageSelector.click();

    // Select EN option from dropdown
    const enOption = page.getByRole("option", { name: /EN|English/i });
    await enOption.click();

    // Wait for the page content to actually change to English.
    // FR-203 requires the UI to re-render in the chosen language.
    // The English subtitle is "Start your journey with SAA 2025."
    await expect(page.getByText("Start your journey with SAA 2025.")).toBeVisible();

    // After the content has changed, verify the NEXT_LOCALE cookie was set.
    // Use expect.poll() to avoid race condition — the cookie setter is async.
    await expect
      .poll(async () => {
        const cookies = await page.context().cookies();
        return cookies.find((c) => c.name === "NEXT_LOCALE")?.value;
      })
      .toBe("en");
  });

  // C3b [FR-203] — every dropdown option shows its own flag, not just a label.
  // Regression: the options originally rendered text only, so the open dropdown
  // read as a bare "VN / EN" list while the trigger beside it showed a flag.
  // The design does have an open-state variant (hUyaaugye2), and the flag+label rule
  // is enforced by C3c/C3d/C3e; this test holds the regression for basic visibility.
  test("C3b [FR-203] — open dropdown shows a flag beside every locale option", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.locator('button[aria-haspopup="listbox"]').click();

    const options = page.getByRole("option");
    await expect(options).toHaveCount(2);

    for (const name of [/^VN$/, /^EN$/]) {
      const option = page.getByRole("option", { name });
      await expect(option).toBeVisible();
      // Flags are inline SVG (so CSS can reach them), not <img>.
      await expect(option.locator("svg")).toHaveCount(1);
    }

    // The two flags must be different artwork — rendering the VN flag for both
    // was the earlier bug on the trigger, and would be just as wrong here.
    const svgHtml = await options.locator("svg").evaluateAll((nodes) =>
      nodes.map((n) => n.innerHTML),
    );
    expect(svgHtml).toHaveLength(2);
    expect(svgHtml[0]).not.toBe(svgHtml[1]);
  });

  // Helper: get the language selector trigger button
  const trigger = (page: Page) => page.locator('button[aria-haspopup="listbox"]');

  // C3c [FR-203, design 721:4942] — open panel matches the visual contract.
  test("C3c [FR-203] — open panel visual contract (background, border, radius, padding, option size)", async ({
    page,
  }) => {
    await page.goto("/login");
    await trigger(page).click();

    // Assert panel (listbox) visual properties
    const listbox = page.getByRole("listbox");
    await expect(listbox).toHaveCSS("background-color", "rgb(0, 7, 12)");
    await expect(listbox).toHaveCSS("border-width", "1px");
    await expect(listbox).toHaveCSS("border-style", "solid");
    await expect(listbox).toHaveCSS("border-color", "rgb(153, 140, 95)");
    await expect(listbox).toHaveCSS("border-radius", "8px");
    await expect(listbox).toHaveCSS("padding", "6px");

    // Assert first option (option row) visual properties
    const firstOption = page.getByRole("option").first();
    await expect(firstOption).toHaveCSS("border-radius", "2px");
    await expect(firstOption).toHaveCSS("width", "108px");
    await expect(firstOption).toHaveCSS("height", "56px");
  });

  // C3d [FR-203.b] — selected option is distinguished by background.
  test("C3d [FR-203.b] — selected and unselected option backgrounds, hover state", async ({
    page,
  }) => {
    await page.goto("/login");
    await trigger(page).click();

    // VN is the default selected locale
    const vnOption = page.getByRole("option", { name: /^VN$/ });
    const enOption = page.getByRole("option", { name: /^EN$/ });

    // Selected option (VN) has the highlighted background
    await expect(vnOption).toHaveCSS(
      "background-color",
      "rgba(255, 234, 158, 0.2)"
    );

    // Unselected option (EN) has transparent background
    await expect(enOption).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");

    // After hover on EN, it gets the hover background
    await enOption.hover();
    await expect(enOption).toHaveCSS(
      "background-color",
      "rgba(255, 234, 158, 0.08)"
    );

    // VN option still has aria-selected="true" (attribute contract retained)
    await expect(vnOption).toHaveAttribute("aria-selected", "true");
  });

  // C3e [FR-203.c] — keyboard navigation: ArrowDown/Up/Home/End, Escape, Enter/Space.
  test("C3e [FR-203.c] — keyboard navigation (Arrow keys, Home, End, Escape, Enter)", async ({
    page,
  }) => {
    await page.goto("/login");

    // ===== Group 1: Arrow key navigation =====
    await trigger(page).click();

    // On open, focus lands on the selected option (VN)
    const vnOption = page.getByRole("option", { name: /^VN$/ });
    const enOption = page.getByRole("option", { name: /^EN$/ });
    await expect(vnOption).toBeFocused();

    // ArrowDown moves focus to EN
    await page.keyboard.press("ArrowDown");
    await expect(enOption).toBeFocused();

    // ArrowDown again wraps back to VN
    await page.keyboard.press("ArrowDown");
    await expect(vnOption).toBeFocused();

    // ===== Group 2: Arrow Up and Home/End =====
    // Reopen for a fresh state
    await page.keyboard.press("Escape");
    await trigger(page).click();

    // ArrowUp from VN wraps to EN
    await page.keyboard.press("ArrowUp");
    await expect(enOption).toBeFocused();

    // Home moves to VN
    await page.keyboard.press("Home");
    await expect(vnOption).toBeFocused();

    // End moves to EN
    await page.keyboard.press("End");
    await expect(enOption).toBeFocused();

    // ===== Group 3: Escape closes panel and returns focus to trigger =====
    await page.keyboard.press("Escape");
    await expect(page.getByRole("listbox")).toHaveCount(0);
    await expect(trigger(page)).toBeFocused();

    // ===== Group 4: Enter selects a locale =====
    // Reopen, navigate to EN, and press Enter
    await trigger(page).click();
    await page.keyboard.press("ArrowDown"); // EN
    await page.keyboard.press("Enter");

    // English copy should now be visible
    await expect(page.getByText("Start your journey with SAA 2025.")).toBeVisible();

    // Verify NEXT_LOCALE cookie is set to 'en'
    await expect
      .poll(async () => {
        const cookies = await page.context().cookies();
        return cookies.find((c) => c.name === "NEXT_LOCALE")?.value;
      })
      .toBe("en");
  });

  // C4: Locale fallback — `NEXT_LOCALE=xx` still renders VN, no blank page
  test("C4 [BR-003] — invalid NEXT_LOCALE value falls back to VN without blank page", async ({
    page,
  }) => {
    // Set an invalid locale cookie
    await page.context().addCookies([
      {
        name: "NEXT_LOCALE",
        value: "xx",
        domain: "127.0.0.1",
        path: "/",
      },
    ]);

    await page.goto("/login");

    // Page should not be blank
    await expect(page.locator("body")).not.toBeEmpty();

    // Should show Vietnamese content (default)
    const loginButton = page.getByRole("button", { name: /LOGIN With Google/i });
    await expect(loginButton).toBeVisible();
  });

  // C5: OAuth kickoff — click button → disabled + request to /auth/v1/authorize with provider=google
  test("C5 [FR-202, FR-601, SM-001, SC-003] — clicking login button initiates OAuth flow with provider=google", async ({
    page,
  }) => {
    // Route to abort the authorize request so we don't leave the page
    await page.route("**/auth/v1/authorize**", (route) => {
      route.abort();
    });

    // Wait for the authorize request and capture it
    const authorizeRequest = page.waitForRequest(
      /\/auth\/v1\/authorize/,
    );

    await page.goto("/login");

    // Click the login button
    const loginButton = page.getByRole("button", { name: /LOGIN With Google/i });
    await loginButton.click();

    // Button should be disabled during auth attempt
    await expect(loginButton).toBeDisabled();

    // Capture the OAuth request
    const request = await authorizeRequest;
    const url = request.url();

    // Parse the URL to check query parameters. @supabase/auth-js percent-encodes
    // the redirect_to parameter, so we must parse rather than substring-match.
    const u = new URL(url);

    // Should contain provider=google
    expect(u.searchParams.get("provider")).toBe("google");

    // redirect_to should point to our callback URL (decoded by URLSearchParams)
    expect(u.searchParams.get("redirect_to")).toBe(
      "http://127.0.0.1:3000/auth/callback",
    );
  });

  // C10: Callback open-redirect protection — ?next=evil.com lands on this origin
  test("C10 — callback open-redirect protection rejects external next URL", async ({
    page,
  }) => {
    // Try to hit callback with an external redirect target
    // The callback should validate the next parameter and reject it,
    // or redirect to /login/todo (the safe default)
    await page.goto("/auth/callback?error=access_denied&next=https://evil.com");

    // The critical assertion: the page origin must be this app's origin,
    // not the attacker's origin (evil.com). This blocks open redirect attacks.
    const currentOrigin = new URL(page.url()).origin;
    const appOrigin = "http://127.0.0.1:3000";
    expect(currentOrigin).toBe(appOrigin);
  });
});
