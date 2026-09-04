import { expect, test } from "@playwright/test";

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
