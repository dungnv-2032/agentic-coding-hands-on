import { createServerClient } from "@supabase/ssr";
import * as fs from "node:fs";
import * as path from "node:path";

/**
 * Load environment variables from .env.local since Node processes don't
 * automatically load Next.js env files.
 */
function loadEnvVars(): Record<string, string> {
  const envPath = path.join(process.cwd(), ".env.local");
  if (!fs.existsSync(envPath)) {
    throw new Error(
      ".env.local not found. Please create it with Supabase credentials.",
    );
  }

  const envContent = fs.readFileSync(envPath, "utf-8");
  const env: Record<string, string> = {};

  envContent.split("\n").forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) return;

    const [key, ...valueParts] = trimmed.split("=");
    const value = valueParts.join("=").trim();
    env[key] = value;
  });

  return env;
}

/**
 * Create a test session by instantiating Supabase client in Node with an
 * in-memory cookie jar. This captures the exact cookies the library writes
 * (chunking, base64url encoding) without hand-rolling the encoding or touching
 * app code (ORCH-01).
 *
 * Returns the captured cookies and the user's email for storageState setup.
 */
export async function createTestSession() {
  const env = loadEnvVars();
  const supabaseUrl = env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local",
    );
  }

  // In-memory cookie jar as a Map — captures whatever the library writes
  const cookieJar = new Map<string, string>();

  const client = createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return Array.from(cookieJar.entries()).map(([name, value]) => ({
          name,
          value,
        }));
      },
      setAll(cookies) {
        cookies.forEach(({ name, value }) => {
          cookieJar.set(name, value);
        });
      },
    },
  });

  // Create a unique user. The timestamp alone is NOT unique: since the
  // homepage suite got its own setup project (clarifications.md ORCH-12),
  // two setup projects call this fixture concurrently, and when both land in
  // the same millisecond they request the same email — GoTrue then reports
  // the duplicate-key rejection as the opaque "Database error saving new
  // user", which reads like a flake and is not. The pid and random suffix
  // make collisions impossible regardless of how many setups run in parallel.
  const unique = `${Date.now()}-${process.pid}-${Math.random().toString(36).slice(2, 8)}`;
  const email = `e2e-${unique}@example.com`;
  const password = "Test123456!";

  const { data, error } = await client.auth.signUp({
    email,
    password,
  });

  if (error || !data.session) {
    throw new Error(`signUp failed: ${error?.message || "no session returned"}`);
  }

  // Verify the session by calling getUser() — confirms cookies are loadable
  const { data: user, error: userError } = await client.auth.getUser();
  if (userError || !user.user) {
    throw new Error(`getUser verification failed: ${userError?.message}`);
  }

  // For C8: Expire the access token so the proxy is forced to refresh it during
  // the guarded redirect from /login to /todo. This tests that cookie rotation
  // during redirect is handled correctly (plan risk R1). The refresh token remains
  // valid so Supabase can issue a new access token.
  const expiredSession = {
    ...data.session,
    expires_at: Math.floor(Date.now() / 1000) - 60, // expired 1 minute ago
  };

  await client.auth.setSession(expiredSession);

  // Return all captured cookies, user email, and userId for the setup project.
  // `userId` comes from the verified `getUser()` result, not from `signUp`'s
  // `data.user`: the guard above narrows `user.user` to non-null, whereas
  // `signUp` types its `user` as nullable and only `data.session` was checked.
  return {
    cookies: Array.from(cookieJar.entries()).map(([name, value]) => ({
      name,
      value,
    })),
    email,
    userId: user.user.id,
  };
}
