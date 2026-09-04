import { NextResponse, type NextRequest } from "next/server";

import { createClient } from "@/lib/supabase/server";

const OAUTH_FAILED_REDIRECT = "/login?error=oauth_failed";
const DEFAULT_NEXT = "/todo";
const FALLBACK_ORIGIN = "http://127.0.0.1:3000";

/**
 * The canonical origin every redirect from this route is built on.
 *
 * Deliberately NOT derived from the incoming request. Two traps sit here:
 *
 *  1. `request.nextUrl.origin` (and `new URL(request.url)`, which NextRequest
 *     builds FROM the normalized nextUrl) is unusable, because NextURL
 *     rewrites any loopback hostname — 127.0.0.1, [::1] — to the literal
 *     string "localhost" (node_modules/next/dist/server/web/next-url.js,
 *     REGEX_LOCALHOST_HOSTNAME). This project pins its session cookie and the
 *     Supabase redirect allow-list to 127.0.0.1, so that rewrite would send
 *     users to a host that does not carry their session.
 *
 *  2. The raw `Host` header dodges trap 1, but it is client-controlled. This
 *     route is reachable unauthenticated, so building a redirect from it is an
 *     open redirect (CWE-644): `Host: evil.com` on the error branch below would
 *     307 the victim straight to evil.com. `x-forwarded-host` is no better.
 *
 * `NEXT_PUBLIC_SITE_URL` is the same value `app/login/actions.ts` builds the
 * OAuth `redirectTo` from, so using it here keeps the entire round-trip pinned
 * to one origin that the deployment — not the caller — chooses.
 */
function resolveSiteOrigin(): string {
  const configured = process.env.NEXT_PUBLIC_SITE_URL;

  if (configured) {
    try {
      return new URL(configured).origin;
    } catch {
      // A malformed env var must never silently become a redirect target.
    }
  }

  return FALLBACK_ORIGIN;
}

/**
 * Resolves the `next` query param to a same-origin path (case C10, FR-401).
 *
 * Parsing the candidate against our own origin and comparing the result is
 * what makes this airtight: it rejects absolute URLs, protocol-relative
 * `//evil.com`, and backslash variants like `/\evil.com` — which the WHATWG
 * URL parser normalizes to `//evil.com` for special schemes, so a naive
 * `startsWith("//")` check misses them.
 */
function resolveNextPath(rawNext: string | null, origin: string): string {
  if (!rawNext) return DEFAULT_NEXT;

  try {
    const candidate = new URL(rawNext, origin);
    if (candidate.origin !== origin) return DEFAULT_NEXT;
    return `${candidate.pathname}${candidate.search}${candidate.hash}`;
  } catch {
    return DEFAULT_NEXT;
  }
}

/**
 * Google OAuth callback (FR-401, FR-402, DEC-002). Two branches, both fixed
 * redirects — the provider's raw error text is never reflected to the user
 * or into the URL, only the app's own fixed `error=oauth_failed` code:
 *   - `code` present and exchange succeeds  → `next` (default `/todo`)
 *   - `error` present, or exchange fails, or neither param is present
 *                                            → `/login?error=oauth_failed`
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  const { searchParams } = request.nextUrl;
  const origin = resolveSiteOrigin();
  const code = searchParams.get("code");
  const error = searchParams.get("error");
  const next = resolveNextPath(searchParams.get("next"), origin);

  // Cancel path: Google sends `error` (e.g. access_denied) with no `code`
  // when the user declines consent. Skip the exchange entirely.
  if (error) {
    return NextResponse.redirect(`${origin}${OAUTH_FAILED_REDIRECT}`);
  }

  if (code) {
    const supabase = await createClient();

    // exchangeCodeForSession reaches out to GoTrue over the network, so a
    // transport failure throws rather than returning an error — without this
    // guard that surfaces as an unhandled 500 instead of the specified
    // "login failed, try again" screen.
    try {
      const { error: exchangeError } =
        await supabase.auth.exchangeCodeForSession(code);

      if (!exchangeError) {
        return NextResponse.redirect(`${origin}${next}`);
      }
    } catch {
      // Fall through to the shared failure redirect below.
    }
  }

  // No code and no error, or a failed exchange: same fixed failure redirect.
  return NextResponse.redirect(`${origin}${OAUTH_FAILED_REDIRECT}`);
}
