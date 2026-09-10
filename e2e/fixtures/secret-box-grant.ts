/**
 * Secret Box test grant fixture — service-role operations
 *
 * Grants unopened boxes to test users and manages the unopened counter
 * using the service-role key read at runtime from `npx supabase status -o json`.
 *
 * No key is committed; granting is test-infrastructure only.
 */

import { createClient } from "@supabase/supabase-js";

import type { Database } from "@/lib/supabase/database.types";
import { execFileSync } from "node:child_process";
import * as path from "node:path";
import * as fs from "node:fs";

// Typed with `Database`, the same generic every product-side client carries
// (`lib/supabase/server.ts`, `lib/kudos/queries.ts`). Without it `.from()`
// resolves its row type to `never` and every column access is a type error.
let serviceRoleClient: ReturnType<typeof createClient<Database>> | null = null;

/**
 * Get or create the service-role Supabase client.
 * Reads the service-role key once at runtime from `npx supabase status -o json`.
 */
function getServiceRoleClient() {
  if (serviceRoleClient) return serviceRoleClient;

  try {
    const statusJson = JSON.parse(
      execFileSync("npx", ["supabase", "status", "-o", "json"], {
        encoding: "utf-8",
      }),
    );

    const serviceRoleKey = statusJson.SERVICE_ROLE_KEY;
    if (!serviceRoleKey) {
      throw new Error(
        "SERVICE_ROLE_KEY not found in `npx supabase status -o json`",
      );
    }

    // Get NEXT_PUBLIC_SUPABASE_URL from .env.local
    const envPath = path.join(process.cwd(), ".env.local");
    if (!fs.existsSync(envPath)) {
      throw new Error(
        ".env.local not found. Please create it with Supabase credentials.",
      );
    }

    const envContent = fs.readFileSync(envPath, "utf-8");
    const envMap: Record<string, string> = {};
    envContent.split("\n").forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) return;
      const [key, ...valueParts] = trimmed.split("=");
      const value = valueParts.join("=").trim();
      envMap[key] = value;
    });

    const supabaseUrl = envMap.NEXT_PUBLIC_SUPABASE_URL;
    if (!supabaseUrl) {
      throw new Error("NEXT_PUBLIC_SUPABASE_URL not found in .env.local");
    }

    serviceRoleClient = createClient<Database>(supabaseUrl, serviceRoleKey);
    return serviceRoleClient;
  } catch (error) {
    if (error instanceof Error && error.message.includes("Supabase is not running")) {
      throw new Error(
        "Supabase is not running. Start it with `npx supabase start` and try again. This is an infrastructure failure, not a test failure.",
      );
    }
    throw error;
  }
}

/**
 * Ensure the user has a sunners row; create one if absent.
 * Returns the sunnerId.
 *
 * `sunners.id` is `bigint generated always as identity`, which the generated
 * `Database` types surface as `number` — not the auth uuid `string` that
 * `userId` is. The two identifiers are deliberately different types here so
 * one can never be passed where the other is meant.
 */
export async function ensureSunner(userId: string): Promise<number> {
  const client = getServiceRoleClient();

  // Check if sunners row already exists
  const { data: existing, error: queryError } = await client
    .from("sunners")
    .select("id")
    .eq("auth_user_id", userId)
    .single();

  if (queryError && queryError.code !== "PGRST116") {
    // PGRST116 = "no rows found" — expected if the row doesn't exist
    throw new Error(`Failed to query sunners: ${queryError.message}`);
  }

  if (existing?.id) {
    return existing.id;
  }

  // Ensure the "Unassigned" department exists
  let departmentId: number;
  const { data: deptData, error: deptQueryError } = await client
    .from("departments")
    .select("id")
    .eq("name", "Unassigned")
    .single();

  if (deptQueryError?.code === "PGRST116") {
    // Department doesn't exist, create it
    const { data: newDept, error: deptInsertError } = await client
      .from("departments")
      .insert([{ name: "Unassigned" }])
      .select("id")
      .single();

    if (deptInsertError) {
      throw new Error(`Failed to create Unassigned department: ${deptInsertError.message}`);
    }

    departmentId = newDept.id;
  } else if (deptQueryError) {
    throw new Error(`Failed to query departments: ${deptQueryError.message}`);
  } else {
    departmentId = deptData.id;
  }

  // Create a new sunners row
  // Note: provisioning mirrors create_kudos() (clarifications.md)
  const { data: newRow, error: insertError } = await client
    .from("sunners")
    .insert([
      {
        auth_user_id: userId,
        full_name: `Test User ${userId.slice(0, 8)}`,
        department_id: departmentId,
        avatar_url: "/images/kudos/sample-avatar.png",
        secret_box_unopened_count: 0,
        secret_box_opened_count: 0,
      },
    ])
    .select("id")
    .single();

  if (insertError) {
    throw new Error(`Failed to create sunners row: ${insertError.message}`);
  }

  return newRow.id;
}

/**
 * Set the unopened count absolutely (and reset opened to 0).
 * Useful for resetting state before each test.
 */
export async function setUnopenedCount(
  userId: string,
  count: number,
): Promise<void> {
  const client = getServiceRoleClient();

  const { error } = await client
    .from("sunners")
    .update({
      secret_box_unopened_count: count,
      secret_box_opened_count: 0,
    })
    .eq("auth_user_id", userId);

  if (error) {
    throw new Error(
      `Failed to set unopened count for user ${userId}: ${error.message}`,
    );
  }
}

/**
 * Read the current counters for a user.
 */
export async function readCounters(userId: string): Promise<{
  unopened: number;
  opened: number;
  openings: number;
}> {
  const client = getServiceRoleClient();

  const { data, error } = await client
    .from("sunners")
    .select("secret_box_unopened_count, secret_box_opened_count")
    .eq("auth_user_id", userId)
    .single();

  if (error) {
    throw new Error(
      `Failed to read counters for user ${userId}: ${error.message}`,
    );
  }

  // `secret_box_openings` references `sunners(id)`, NOT `auth.users(id)` —
  // there is no `auth_user_id` column on it to filter by. Resolve the sunner
  // first, then count that sunner's rows.
  const sunnerId = await ensureSunner(userId);
  const { data: openings, error: openingsError } = await client
    .from("secret_box_openings")
    .select("id")
    .eq("sunner_id", sunnerId);

  if (openingsError) {
    throw new Error(
      `Failed to read openings for user ${userId}: ${openingsError.message}`,
    );
  }

  return {
    unopened: data.secret_box_unopened_count,
    opened: data.secret_box_opened_count,
    openings: openings?.length || 0,
  };
}

/**
 * Clear all opening records for a user (for test isolation).
 */
export async function clearOpenings(userId: string): Promise<void> {
  const client = getServiceRoleClient();

  const sunnerId = await ensureSunner(userId);

  const { error } = await client
    .from("secret_box_openings")
    .delete()
    .eq("sunner_id", sunnerId);

  if (error) {
    throw new Error(
      `Failed to clear openings for user ${userId}: ${error.message}`,
    );
  }
}
