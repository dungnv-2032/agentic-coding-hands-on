import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";

/**
 * Supabase client for Server Components, Server Actions and Route Handlers.
 *
 * Must be created per request — never hoist this into a module-level constant,
 * or one request's session leaks into another.
 */
export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            for (const { name, value, options } of cookiesToSet) {
              cookieStore.set(name, value, options);
            }
          } catch {
            // Server Components cannot write cookies. This is expected and safe
            // to ignore: proxy.ts refreshes the session on every request, so the
            // refreshed tokens still reach the browser.
          }
        },
      },
    },
  );
}
