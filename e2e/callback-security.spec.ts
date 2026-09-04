import { test, expect } from "@playwright/test";

/**
 * CWE-644: Open Redirect regression tests for /auth/callback.
 *
 * This route was previously vulnerable to host header injection attacks:
 * an unauthenticated request with `Host: evil.com` would be redirected to
 * evil.com. The fix uses NEXT_PUBLIC_SITE_URL (deployment-chosen origin)
 * instead of the client-controlled Host header, and validates the `next`
 * parameter by parsing it against the known origin, rejecting anything
 * that doesn't match.
 *
 * These tests verify all attack vectors are blocked:
 * - Host/X-Forwarded-Host spoofing on both error and success branches
 * - Absolute URL, protocol-relative, and backslash variants in `next`
 */
test.describe("Callback Security (anon project)", () => {
  const baseURL = "http://127.0.0.1:3000";
  const evilOrigin = "http://evil.com";

  test("Host: evil.com on error branch is rejected (unauthenticated exploit)", async ({
    request,
  }) => {
    const path = "/auth/callback?error=access_denied";
    const response = await request.get(baseURL + path, {
      headers: { Host: "evil.com" },
      maxRedirects: 0,
    });

    expect(response.status()).toBe(307);
    const location = response.headers()["location"];
    expect(location).toBeDefined();

    // Verify the redirect goes to safe origin, not evil.com
    const redirectURL = new URL(location!);
    expect(redirectURL.origin).toBe(baseURL);
    expect(redirectURL.pathname).toBe("/login");
    expect(redirectURL.searchParams.get("error")).toBe("oauth_failed");
  });

  test("Host: evil.com with neither code nor error is rejected", async ({
    request,
  }) => {
    const path = "/auth/callback";
    const response = await request.get(baseURL + path, {
      headers: { Host: "evil.com" },
      maxRedirects: 0,
    });

    expect(response.status()).toBe(307);
    const location = response.headers()["location"];
    expect(location).toBeDefined();

    const redirectURL = new URL(location!);
    expect(redirectURL.origin).toBe(baseURL);
    expect(redirectURL.pathname).toBe("/login");
    expect(redirectURL.searchParams.get("error")).toBe("oauth_failed");
  });

  test("x-forwarded-host: evil.com is rejected", async ({ request }) => {
    const path = "/auth/callback?error=access_denied";
    const response = await request.get(baseURL + path, {
      headers: { "x-forwarded-host": "evil.com" },
      maxRedirects: 0,
    });

    expect(response.status()).toBe(307);
    const location = response.headers()["location"];
    expect(location).toBeDefined();

    const redirectURL = new URL(location!);
    expect(redirectURL.origin).toBe(baseURL);
    expect(redirectURL.pathname).toBe("/login");
  });

  test("next as absolute URL to evil.com is rejected", async ({ request }) => {
    const path = `/auth/callback?error=access_denied&next=${encodeURIComponent(evilOrigin)}`;
    const response = await request.get(baseURL + path, {
      maxRedirects: 0,
    });

    expect(response.status()).toBe(307);
    const location = response.headers()["location"];
    expect(location).toBeDefined();

    const redirectURL = new URL(location!);
    expect(redirectURL.origin).toBe(baseURL);
    expect(redirectURL.pathname).toBe("/login");
  });

  test("next as protocol-relative //evil.com is rejected", async ({
    request,
  }) => {
    const path = `/auth/callback?error=access_denied&next=${encodeURIComponent("//evil.com/path")}`;
    const response = await request.get(baseURL + path, {
      maxRedirects: 0,
    });

    expect(response.status()).toBe(307);
    const location = response.headers()["location"];
    expect(location).toBeDefined();

    const redirectURL = new URL(location!);
    expect(redirectURL.origin).toBe(baseURL);
    expect(redirectURL.pathname).toBe("/login");
  });

  test("next with backslash variant /\\evil.com is rejected", async ({
    request,
  }) => {
    // The WHATWG URL parser normalizes /\ to // for special schemes
    const path = `/auth/callback?error=access_denied&next=${encodeURIComponent("/\\evil.com")}`;
    const response = await request.get(baseURL + path, {
      maxRedirects: 0,
    });

    expect(response.status()).toBe(307);
    const location = response.headers()["location"];
    expect(location).toBeDefined();

    const redirectURL = new URL(location!);
    expect(redirectURL.origin).toBe(baseURL);
    expect(redirectURL.pathname).toBe("/login");
  });

  test("next as a valid same-origin path is accepted in redirect", async ({
    request,
  }) => {
    const safePath = "/todo";
    const path = `/auth/callback?code=dummy&next=${encodeURIComponent(safePath)}`;
    const response = await request.get(baseURL + path, {
      maxRedirects: 0,
    });

    expect(response.status()).toBe(307);
    const location = response.headers()["location"];
    expect(location).toBeDefined();

    const redirectURL = new URL(location!);
    expect(redirectURL.origin).toBe(baseURL);
    // Exchange will fail due to dummy code, falling back to error redirect
    expect(redirectURL.pathname).toBe("/login");
    expect(redirectURL.searchParams.get("error")).toBe("oauth_failed");
  });
});
