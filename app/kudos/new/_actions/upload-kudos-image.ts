"use server";

/**
 * Server Action, not a browser-side Storage call (test-contract.md §
 * Blueprint ratification #7 / plan Key Insight 1): a plain client function
 * cannot cross the RSC boundary as a prop without a Track A file importing
 * a Track B module, and a Server Action puts MIME validation where the
 * client cannot skip it (server half of BR-004).
 *
 * The exported signature matches `UploadKudosImage` (`compose-contract.ts`,
 * frozen) exactly: `(file: File) => Promise<UploadResult>` — that type
 * carries no error variant, so failure is signalled by rejecting with
 * `UploadKudosImageError`, a typed error carrying the same
 * `ComposeFieldErrorCode` the rest of the contract uses, never an opaque
 * throw. Track A (phase 10) catches it and reads `.code` to render
 * `image-error` — same discipline `toggleKudosLike` uses for its own
 * never-crash-the-caller contract, adapted to this frozen return type.
 */

import type { ComposeFieldErrorCode, UploadResult } from "@/lib/kudos/compose-contract";
import { isAcceptedImageType } from "@/lib/kudos/validate-compose";
import { createClient } from "@/lib/supabase/server";

const BUCKET = "kudos-attachments";

/** Derived from the validated MIME, never the attacker-controlled filename. */
const EXTENSION_BY_MIME: Record<string, string> = {
  "image/jpeg": "jpg",
  "image/png": "png",
  "image/gif": "gif",
  "image/webp": "webp",
};

export class UploadKudosImageError extends Error {
  constructor(public readonly code: ComposeFieldErrorCode) {
    super(`uploadKudosImage failed: ${code}`);
    this.name = "UploadKudosImageError";
  }
}

export async function uploadKudosImage(file: File): Promise<UploadResult> {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    throw new UploadKudosImageError("unknown");
  }

  // `file` arrives across the Server Action boundary from a caller that
  // could POST directly (forms.md:9-10) — re-check its shape and MIME here,
  // where the client cannot skip it, regardless of what the picker already
  // filtered.
  if (!(file instanceof File) || !isAcceptedImageType(file.type)) {
    throw new UploadKudosImageError("invalidType");
  }

  const extension = EXTENSION_BY_MIME[file.type] ?? "bin"; // unreachable: an unmapped MIME already failed isAcceptedImageType above.
  // Unique per upload so five picks of the same file become five distinct
  // objects (ID-18/19) — the uid prefix is what the storage policy checks.
  const path = `${user.id}/${Date.now()}-${crypto.randomUUID()}.${extension}`;

  const { error: uploadError } = await supabase.storage
    .from(BUCKET)
    .upload(path, file, { contentType: file.type });

  if (uploadError) {
    console.error("uploadKudosImage: storage upload failed", uploadError);
    throw new UploadKudosImageError("unknown");
  }

  const { data: publicUrlData } = supabase.storage.from(BUCKET).getPublicUrl(path);
  return { imageUrl: publicUrlData.publicUrl };
}
