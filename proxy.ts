import { NextResponse, type NextRequest } from "next/server";
import { updateSession } from "@/lib/supabase/update-session";

/**
 * Next.js 16 renamed the `middleware` convention to `proxy`.
 * See node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/proxy.md
 *
 * Refreshes the Supabase session on every request, then guards two explicit
 * route prefixes (FR-101/FR-602, FR-102): unauthenticated visitors are bounced
 * off `/todo` to `/login`, and authenticated sessions are bounced off `/login`
 * to `/todo`. Everything else — `/`, `/auth/callback` in particular — falls
 * through untouched: guarding the OAuth callback would make the round-trip
 * structurally impossible (clarifications.md, plan risk R2).
 */
export async function proxy(request: NextRequest) {
  const { response, user } = await updateSession(request);
  const { pathname } = request.nextUrl;

  /**
   * `updateSession()` builds a brand-new `NextResponse.next({ request })`
   * inside its cookie `setAll` callback every time GoTrue rotates a refresh
   * token, and writes the rotated `Set-Cookie` headers onto that object. A
   * bare `NextResponse.redirect(...)` here would be a *third* response that
   * never saw those headers — the rotated tokens are dropped, and because
   * Supabase refresh tokens are single-use, the browser is left holding an
   * already-consumed token and gets silently logged out on its very next
   * request (plan risk R1, E2E case C8). Do not "simplify" this away by
   * redirecting directly — the cookie copy is the whole point.
   */
  const redirectWithSessionCookies = (pathname: string) => {
    const url = request.nextUrl.clone();
    url.pathname = pathname;
    url.search = "";
    const redirectResponse = NextResponse.redirect(url);
    for (const cookie of response.cookies.getAll()) {
      redirectResponse.cookies.set(cookie);
    }
    return redirectResponse;
  };

  if (!user && pathname.startsWith("/todo")) {
    return redirectWithSessionCookies("/login");
  }
  if (user && pathname.startsWith("/login")) {
    return redirectWithSessionCookies("/todo");
  }

  return response;
}

export const config = {
  matcher: [
    // Everything except Next internals and static assets. Without this the proxy
    // also runs on CSS, JS and images, which needlessly slows every asset fetch.
    "/((?!_next/static|_next/image|favicon\\.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|avif|ico|woff2?)$).*)",
  ],
};
