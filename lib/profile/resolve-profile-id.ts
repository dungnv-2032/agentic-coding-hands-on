/**
 * Pure `?id=` resolver for the Profile bản thân screen (F006, FR-401/FR-402).
 *
 * No `next/*`, no Supabase client, no `async` — this module only classifies
 * the raw query-param value the page already read via Next 16's async
 * `searchParams`. Whether a well-formed id actually matches a `sunners` row
 * is a database question and belongs to the data layer (see
 * `docs/features/F006_ProfileBanThan/technical-spec.md` § A1 / `getProfileData`),
 * not here — this module never touches I/O.
 *
 * clarifications.md § "Route and access", § "The three authored premises
 * that do not hold in this repository" is the authority for every branch
 * below.
 */

export type ProfileIdResolution =
  | { kind: "self" }
  | { kind: "other"; id: number }
  | { kind: "not-found" };

/**
 * `sunners.id` is `bigint generated always as identity`. 18 decimal digits
 * is the widest a bigint can print (max value has 19 digits, but capping at
 * 18 keeps every accepted string safely inside `Number.MAX_SAFE_INTEGER`
 * (16 digits) with headroom, so `Number()` below never silently loses
 * precision). Anything that doesn't match this shape is rejected before it
 * can reach a query — the injection boundary FUN_004 asks for.
 */
const SUNNER_ID_PATTERN = /^\d{1,18}$/;

/**
 * Resolves the `?id=` query parameter into one of three verdicts.
 *
 * @param raw - `searchParams.id` as Next hands it back: `undefined` when
 *   absent, a `string` for one occurrence, or `string[]` when the param was
 *   repeated (`?id=1&id=2`).
 * @param viewerSunnerId - the signed-in caller's own `sunners.id`, or `null`
 *   for a signed-in session with no roster row (A4) — never treated as a
 *   match for any `id`.
 */
export function resolveProfileId(
  raw: string | string[] | undefined,
  viewerSunnerId: number | null,
): ProfileIdResolution {
  // Repeated params: identical values collapse to one; differing values name
  // two different pages in one request, which is not a request we can honor
  // by silently picking a side (FUN_005) — so it is not-found, not self and
  // not the first/last value.
  let value: string | undefined;
  if (Array.isArray(raw)) {
    const distinct = new Set(raw);
    if (distinct.size > 1) {
      return { kind: "not-found" };
    }
    value = raw[0];
  } else {
    value = raw;
  }

  // Absent or cleared (`?id=`) is not an error — it's the self view (FUN_005).
  // This branch also covers every unrecognised param (`?q=…` from the
  // shipped kudos-hero search form, A5): callers only ever pass us the `id`
  // value, so a request that never set `id` lands here regardless of what
  // else is on the query string.
  if (value === undefined || value === "") {
    return { kind: "self" };
  }

  if (!SUNNER_ID_PATTERN.test(value)) {
    return { kind: "not-found" };
  }

  const parsed = Number(value);
  if (viewerSunnerId !== null && parsed === viewerSunnerId) {
    // Canonicalize to self — identical rendering to no query string at all,
    // no redirect (FUN_002).
    return { kind: "self" };
  }

  return { kind: "other", id: parsed };
}
