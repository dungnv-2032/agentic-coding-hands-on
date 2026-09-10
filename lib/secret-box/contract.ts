/**
 * Shared contract for Open Secret Box (F009, MoMorph screen `J3-4YFIpMM`).
 *
 * Types + `formatBoxCount` only — no React, no `next/*`, no `@/lib/supabase/*`
 * import. Track A (phase 04's Client Components) and Track B (phase 05's
 * `open_secret_box` Server Action) both compile against this module without
 * importing each other, per plan.md's dependency graph (`02 ──> 04 ∥ 05`).
 */

/**
 * One badge drawn from `rule_items` (`kind = 'collectible_icon'`),
 * technical-spec.md § 3.2 step 6 (`rule_item_id`, `label`, `image_path`).
 */
export interface SecretBoxBadge {
  ruleItemId: number;
  label: string;
  imagePath: string;
}

/**
 * The `openSecretBox` Server Action's return shape (technical-spec.md § 3.2).
 * A discriminated union on `ok` so a caller can never read `badge` off a
 * failure — TypeScript enforces the narrowing, not a runtime convention.
 *
 * `reason` is closed to the three cases the SQL function and the Server
 * Action can actually produce:
 * - `unauthenticated` — `auth.uid()` is null (errcode `28000`).
 * - `no-boxes` — the guarded `UPDATE ... WHERE secret_box_unopened_count > 0`
 *   found no row (errcode `P0002`); BR-004, the concurrent-open race (R1).
 * - `failed` — anything else (network, unexpected SQL error).
 */
export type OpenSecretBoxResult =
  | { ok: true; badge: SecretBoxBadge; unopenedCount: number; openedCount: number }
  | { ok: false; reason: "unauthenticated" | "no-boxes" | "failed" };

/**
 * Two-digit, zero-padded box count (`05`, `00`), left as-is at three digits
 * or more (`123`) — the design's fixed counter format (mm:1466:7693). One
 * implementation shared by phase 04's counter render and phase 07's e2e
 * assertions, so the padding rule cannot drift between the two.
 *
 * `n` is expected to be a non-negative integer — `sunners.secret_box_*_count`
 * can never go below 0, since `open_secret_box()`'s guarded `UPDATE` is the
 * only writer (technical-spec.md § 3.2 step 3).
 */
export function formatBoxCount(n: number): string {
  return String(n).padStart(2, "0");
}
