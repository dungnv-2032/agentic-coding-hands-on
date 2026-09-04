"use server";

import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

/**
 * Ends the session (FR-403, US004) and lands on `/login`.
 *
 * `supabase.auth.signOut()` resolves with `{ error }` rather than throwing —
 * that error is deliberately not surfaced: an already-expired or
 * already-invalidated session must still land the user on `/login` rather
 * than get stuck on an error screen. `redirect()` throws `NEXT_REDIRECT`
 * internally, so the call sits outside any try/catch — wrapping it would
 * swallow the navigation and report a false error instead.
 */
export async function signOut(): Promise<void> {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect("/login");
}
