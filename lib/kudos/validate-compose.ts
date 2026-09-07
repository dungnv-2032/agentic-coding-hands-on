/**
 * Pure validation predicates for Viết Kudo's write path (phase 07).
 *
 * Zero runtime dependencies: no I/O, no React, no `Intl` — reachable from
 * the client bundle (phase 10 imports `isAcceptedImageType` for the
 * client-side half of BR-004), the same rule `derive.ts` documents for
 * itself. Importing only types + plain constants from the sibling
 * `compose-contract.ts` keeps that guarantee, mirroring `compose-state.ts`'s
 * precedent of importing its siblings only.
 *
 * This module is a convenience, never the boundary: `create-kudos.ts` and
 * `upload-kudos-image.ts` are the actual boundary, and re-run every
 * predicate here regardless of what a client already checked, because
 * Server Functions are POST-reachable directly (forms.md:9-10).
 */

import {
  ACCEPTED_IMAGE_MIME,
  MAX_HASHTAGS,
  type ComposeFieldErrors,
  type ComposePayload,
} from "./compose-contract";

function isPositiveInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value > 0;
}

/**
 * Collects every failing required field into one object — never
 * early-returns (ID-56: all required-field errors show simultaneously).
 */
export function validateCompose(payload: ComposePayload): ComposeFieldErrors {
  const errors: ComposeFieldErrors = {};

  if (!isPositiveInteger(payload.receiverId)) {
    errors.recipient = "required";
  }

  if (payload.title.trim() === "") {
    errors.title = "required";
  }

  if (payload.plainText.trim() === "") {
    errors.body = "required";
  }

  const hashtagIds = payload.hashtagIds;
  if (hashtagIds.length === 0) {
    errors.hashtag = "required";
  } else if (hashtagIds.length > MAX_HASHTAGS) {
    errors.hashtag = "tooMany";
  } else if (!hashtagIds.every(isPositiveInteger)) {
    // Shape-invalid ids (a lying client) — distinct from the count errors above.
    errors.hashtag = "invalidType";
  }

  return errors;
}

/**
 * `ACCEPTED_IMAGE_MIME` membership — the single definition, shared by
 * `upload-kudos-image.ts` (server) and phase 10's picker (client).
 */
export function isAcceptedImageType(mimeOrName: string): boolean {
  return (ACCEPTED_IMAGE_MIME as readonly string[]).includes(mimeOrName);
}

/**
 * A client-supplied image URL is only trusted when it resolves to this
 * project's own Storage bucket — checked by origin AND path prefix, never
 * by extension. An attacker-hosted URL (`evil.com/x.png`) fails the origin
 * check; a renamed non-image cannot reach `kudos-attachments` at all,
 * because `uploadKudosImage` validates the MIME type before the object
 * ever exists.
 */
export function isOwnStorageUrl(url: string, supabaseOrigin: string): boolean {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return false;
  }
  return (
    parsed.origin === supabaseOrigin &&
    parsed.pathname.startsWith("/storage/v1/object/public/kudos-attachments/")
  );
}
