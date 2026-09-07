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
  MAX_IMAGES,
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

  // Symmetric with the hashtag cap above (BR-003). `ComposeFieldErrors`
  // (frozen contract) has no `image` slot — the picker's own per-attempt
  // `image-error` is client-only state, never part of this server shape —
  // so `form` is the closest field-specific bucket available; `create_kudos`
  // still re-checks the same cap independently (`p_image_urls` CHECK), this
  // is what turns that DB rejection into a specific code before the RPC
  // round-trip rather than the generic `{form:"unknown"}` fallback.
  if (payload.imageUrls.length > MAX_IMAGES) {
    errors.form = "tooMany";
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
 * Magic-number signatures for every `ACCEPTED_IMAGE_MIME` value.
 * `File.type` is caller-declared and cannot be trusted alone (an attacker
 * can label arbitrary bytes `image/jpeg`), so `uploadKudosImage` sniffs
 * these against the actual leading bytes before the object is ever written
 * to the public `kudos-attachments` bucket. WEBP's "WEBP" marker sits at
 * byte 8, after a 4-byte RIFF size field this signature deliberately does
 * not constrain — one non-contiguous signature is why each entry is a list
 * of `(offset, bytes)` pairs rather than one prefix.
 */
const IMAGE_SIGNATURES: Record<string, readonly { offset: number; bytes: readonly number[] }[]> = {
  "image/jpeg": [{ offset: 0, bytes: [0xff, 0xd8, 0xff] }],
  "image/png": [{ offset: 0, bytes: [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a] }],
  // "GIF8" covers both GIF87a and GIF89a.
  "image/gif": [{ offset: 0, bytes: [0x47, 0x49, 0x46, 0x38] }],
  "image/webp": [
    { offset: 0, bytes: [0x52, 0x49, 0x46, 0x46] }, // "RIFF"
    { offset: 8, bytes: [0x57, 0x45, 0x42, 0x50] }, // "WEBP"
  ],
};

/** How many leading bytes a caller must read before calling {@link matchesImageSignature}. */
export const IMAGE_SIGNATURE_SNIFF_LENGTH = 12;

/**
 * True when `bytes` (the file's leading `IMAGE_SIGNATURE_SNIFF_LENGTH`
 * bytes) actually starts with `mime`'s magic number. An unrecognized `mime`
 * matches nothing — this is a whitelist, never a "no signature means trust
 * it" fallback.
 */
export function matchesImageSignature(mime: string, bytes: Uint8Array): boolean {
  const signature = IMAGE_SIGNATURES[mime];
  if (!signature) return false;
  return signature.every(({ offset, bytes: expected }) =>
    expected.every((byte, index) => bytes[offset + index] === byte),
  );
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
