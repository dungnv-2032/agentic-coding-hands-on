"use client";

import { useEffect, useRef, useState, type ChangeEvent } from "react";

import { isAcceptedImageType } from "@/lib/kudos/validate-compose";
import {
  MAX_IMAGES,
  type ComposeAttachedImage,
  type ComposeFieldErrorCode,
  type UploadKudosImage,
} from "@/lib/kudos/compose-contract";

/**
 * `lib/kudos/compose-contract.ts`'s `ImagePickerProps` sketch is
 * `{ copy, images, error, onFilesSelected, onRemove }` — a bare
 * files-in/files-out shape with no room for this phase's upload
 * orchestration. phase-10.md's Key Insights 7/9/10 and its Implementation
 * Steps assign the upload plumbing to THIS component (reject-before-preview
 * type check, optimistic blob preview, `uploadImage` call, resolve/rollback)
 * so phase 11 can await pending uploads at submit by reading `imageUrl ===
 * null` off the shared reducer state — a bare `onFilesSelected` cannot
 * express that. This file's props follow the later, detailed phase-10.md
 * architecture instead; surfaced to the orchestrator alongside the hashtag
 * copy gap (see hashtag-picker.tsx's doc comment).
 */
export interface ImagePickerCopy {
  /** Contains both "Image" and "Tối đa 5" (test-contract.md § Images). */
  addLabel: string;
  /** `errors.invalidType` — shown when a picked file fails the MIME check. */
  invalidTypeError: string;
}

export function buildImagePickerCopy(copy: {
  buttons: { addImage: string; max: string };
  errors: Record<ComposeFieldErrorCode, string>;
}): ImagePickerCopy {
  return { addLabel: `${copy.buttons.addImage} ${copy.buttons.max}`, invalidTypeError: copy.errors.invalidType };
}

export interface ImagePickerProps {
  copy: ImagePickerCopy;
  images: readonly ComposeAttachedImage[];
  /** `"invalidType"` renders `image-error`; any other value is ignored here. */
  error?: ComposeFieldErrorCode;
  uploadImage: UploadKudosImage;
  onAdd: (image: ComposeAttachedImage) => void;
  onResolve: (id: string, imageUrl: string) => void;
  onRemove: (id: string) => void;
  onError: (error: ComposeFieldErrorCode) => void;
}

/**
 * mm:I520:11647;520:9896 (`mms_F_Frame 537`, 672px row, 16px gap) ·
 * mm:I520:11647;662:9197 (thumb, 80×80, border `#998C5F`, radius 18px, bg
 * white) · mm:I520:11647;662:9287 (remove control, 20×20, full-round,
 * `#D4271D`) · mm:I520:11647;662:9133 (add button, 48px tall, border
 * `#998C5F`, radius 8px, bg white — same component as `hashtag-add`).
 *
 * `image-input` stays mounted and hidden even past the cap (ID-46/47 call
 * `setInputFiles` without waiting on the add button); `image-add` only
 * unmounts (never `disabled`) once five images are present (ID-19, ID-20,
 * ID-38, ID-54) and returns after a removal (ID-40). A rejected file never
 * reaches `onAdd` — no thumb, `image-error` only (ID-23/24/55). Files are
 * never deduped and `input.value` resets after every change, so five picks
 * of the identical fixture give five thumbs (ID-18/19).
 */
export function ImagePicker({ copy, images, error, uploadImage, onAdd, onResolve, onRemove, onError }: ImagePickerProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  // Blob preview URLs, keyed by the same client-only `id` the reducer
  // tracks. State, not a ref (react-hooks/refs forbids reading a ref during
  // render): `ComposeAttachedImage.imageUrl` stays `null` while the upload
  // is in flight (compose-contract.ts's own doc comment), so the thumb's
  // `src` falls back to this map until `onResolve` fires.
  const [previewUrls, setPreviewUrls] = useState<ReadonlyMap<string, string>>(new Map());
  // Mirrors `previewUrls` for the unmount-only revoke sweep below, so that
  // effect doesn't need `previewUrls` in its deps (which would re-run it,
  // and thus re-register the cleanup, on every preview change).
  const previewUrlsRef = useRef(previewUrls);

  useEffect(() => {
    previewUrlsRef.current = previewUrls;
  }, [previewUrls]);

  useEffect(() => {
    return () => {
      previewUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    };
  }, []);

  function releasePreview(id: string) {
    setPreviewUrls((prev) => {
      const url = prev.get(id);
      if (!url) return prev;
      URL.revokeObjectURL(url);
      const next = new Map(prev);
      next.delete(id);
      return next;
    });
  }

  async function processFile(file: File) {
    if (!isAcceptedImageType(file.type)) {
      onError("invalidType");
      return;
    }
    const id = crypto.randomUUID();
    setPreviewUrls((prev) => new Map(prev).set(id, URL.createObjectURL(file)));
    onAdd({ id, fileName: file.name, imageUrl: null });
    try {
      const result = await uploadImage(file);
      releasePreview(id);
      onResolve(id, result.imageUrl);
    } catch {
      releasePreview(id);
      onRemove(id);
      onError("unknown");
    }
  }

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const files = event.target.files ? Array.from(event.target.files) : [];
    // Reset immediately (Key Insight 5) so re-picking the same path fires a
    // fresh `change` — a native input suppresses the event on an identical
    // value otherwise.
    event.target.value = "";
    void Promise.all(files.map((file) => processFile(file)));
  }

  function handleRemove(id: string) {
    releasePreview(id);
    onRemove(id);
  }

  return (
    <div className="flex flex-col gap-2">
      {/* mm:I520:11647;520:9896 */}
      <div className="flex flex-wrap items-center gap-4">
        {images.map((image) => {
          const src = image.imageUrl ?? previewUrls.get(image.id) ?? "";
          return (
            // mm:I520:11647;662:9197
            <div
              key={image.id}
              data-testid="image-thumb"
              className="relative h-20 w-20 overflow-hidden rounded-[18px] border border-[#998C5F] bg-white"
            >
              {/* eslint-disable-next-line @next/next/no-img-element -- blob: preview URLs cannot be optimized by next/image, and the same element later carries the resolved Storage URL, so one <img> covers both states (kudos-attachments.tsx keeps next/image for the read-only board). */}
              <img src={src} alt={image.fileName} className="h-full w-full object-cover" />
              <button
                type="button"
                data-testid="image-thumb-remove"
                aria-label={`Remove ${image.fileName}`}
                onClick={() => handleRemove(image.id)}
                // mm:I520:11647;662:9287
                className="absolute top-0 right-0 flex h-5 w-5 items-center justify-center rounded-full bg-[#D4271D] text-xs text-white"
              >
                ✕
              </button>
            </div>
          );
        })}

        {images.length < MAX_IMAGES && (
          <button
            type="button"
            data-testid="image-add"
            onClick={() => inputRef.current?.click()}
            // mm:I520:11647;662:9133
            className="flex h-12 items-center gap-2 rounded-lg border border-[#998C5F] bg-white px-2 text-left text-[11px] leading-4 font-bold tracking-[0.5px] text-[#999]"
          >
            {copy.addLabel}
          </button>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        multiple
        data-testid="image-input"
        onChange={handleChange}
        className="sr-only"
      />

      {error === "invalidType" && (
        <p data-testid="image-error" className="text-sm font-semibold text-[#D4271D]">
          {copy.invalidTypeError}
        </p>
      )}
    </div>
  );
}
