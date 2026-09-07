/**
 * Client-side compose state for Viết Kudo (F005, phase 01, frozen).
 *
 * Zero React, zero I/O — pure reducer + selectors so a later phase's
 * `compose-form.tsx` can stay under 200 lines by delegating the state
 * machine here instead of reimplementing it (Key Insight #6). Imports are
 * limited to this module's two siblings: `compose-contract.ts` (the shared
 * shapes/caps) and `rich-text.ts` (the body's mark-toggling engine) — never
 * `view-model.ts`/`derive.ts`/`queries.ts` (F004's read-side files) or
 * `@/lib/supabase/*`.
 */
import {
  MAX_HASHTAGS,
  MAX_IMAGES,
  type ComposeAttachedImage,
  type ComposeFieldErrorCode,
  type ComposeFieldErrors,
  type ComposeHashtagOption,
  type ComposePayload,
  type ComposeSunnerOption,
  type ToggleableBlock,
  type ToggleableInlineMark,
} from "./compose-contract";
import {
  docToPlainText,
  insertMention,
  isToggleableInlineMark,
  remapMarks,
  serializeToDoc,
  toggleBlockMark,
  toggleInlineMark,
  type RichTextState,
  type TextRange,
} from "./rich-text";

export interface ComposeState {
  recipient: ComposeSunnerOption | null;
  title: string;
  body: RichTextState;
  hashtags: ComposeHashtagOption[];
  images: ComposeAttachedImage[];
  isAnonymous: boolean;
  anonymousName: string;
  errors: ComposeFieldErrors;
  imageError?: ComposeFieldErrorCode;
  hashtagError?: ComposeFieldErrorCode;
}

export function createInitialComposeState(): ComposeState {
  return {
    recipient: null,
    title: "",
    body: { text: "", inline: [], blocks: [] },
    hashtags: [],
    images: [],
    isAnonymous: false,
    anonymousName: "",
    errors: {},
  };
}

export type ComposeAction =
  | { type: "setRecipient"; recipient: ComposeSunnerOption | null }
  | { type: "setTitle"; title: string }
  | { type: "setBody"; text: string }
  | { type: "toggleMark"; kind: ToggleableInlineMark | ToggleableBlock; range: TextRange; href?: string }
  | { type: "insertMention"; at: number; label: string; sunnerId: number }
  | { type: "addHashtag"; hashtag: ComposeHashtagOption }
  | { type: "removeHashtag"; id: number }
  | { type: "addImage"; image: ComposeAttachedImage }
  | { type: "resolveImage"; id: string; imageUrl: string }
  | { type: "removeImage"; id: string }
  | { type: "setAnonymous"; anonymous: boolean }
  | { type: "setAnonymousName"; name: string }
  | { type: "setErrors"; errors: ComposeFieldErrors }
  | { type: "setImageError"; error: ComposeFieldErrorCode | undefined }
  | { type: "setHashtagError"; error: ComposeFieldErrorCode | undefined };

/** One switch, exhaustive by TS — every `ComposeAction` variant is handled. */
export function composeReducer(state: ComposeState, action: ComposeAction): ComposeState {
  switch (action.type) {
    case "setRecipient":
      return { ...state, recipient: action.recipient, errors: { ...state.errors, recipient: undefined } };
    case "setTitle":
      return { ...state, title: action.title, errors: { ...state.errors, title: undefined } };
    case "setBody":
      return { ...state, body: remapMarks(state.body, action.text), errors: { ...state.errors, body: undefined } };
    case "toggleMark": {
      const body = isToggleableInlineMark(action.kind)
        ? toggleInlineMark(state.body, action.kind, action.range, action.href)
        : toggleBlockMark(state.body, action.kind, action.range);
      return { ...state, body };
    }
    case "insertMention":
      return { ...state, body: insertMention(state.body, action.at, action.label, action.sunnerId) };
    case "addHashtag":
      if (state.hashtags.length >= MAX_HASHTAGS) return { ...state, hashtagError: "tooMany" };
      return {
        ...state,
        hashtags: [...state.hashtags, action.hashtag],
        hashtagError: undefined,
        errors: { ...state.errors, hashtag: undefined },
      };
    case "removeHashtag":
      return { ...state, hashtags: state.hashtags.filter((h) => h.id !== action.id) };
    case "addImage":
      // MAX_IMAGES is enforced by hiding `image-add` (test-contract.md § Images) — a call past the
      // cap is a stale-UI race, not a user error, so it no-ops rather than surfacing `imageError`.
      if (state.images.length >= MAX_IMAGES) return state;
      return { ...state, images: [...state.images, action.image] };
    case "resolveImage":
      return {
        ...state,
        images: state.images.map((img) => (img.id === action.id ? { ...img, imageUrl: action.imageUrl } : img)),
      };
    case "removeImage":
      return { ...state, images: state.images.filter((img) => img.id !== action.id) };
    case "setAnonymous":
      return { ...state, isAnonymous: action.anonymous, anonymousName: action.anonymous ? state.anonymousName : "" };
    case "setAnonymousName":
      return { ...state, anonymousName: action.name };
    case "setErrors":
      return { ...state, errors: action.errors };
    case "setImageError":
      return { ...state, imageError: action.error };
    case "setHashtagError":
      return { ...state, hashtagError: action.error };
    default: {
      const exhaustive: never = action;
      return exhaustive;
    }
  }
}

/** DEC-002, the ONLY definition of it: recipient AND title AND non-empty body AND ≥1 hashtag. */
export function isSubmitReady(state: ComposeState): boolean {
  return (
    state.recipient !== null &&
    state.title.trim() !== "" &&
    docToPlainText(serializeToDoc(state.body)).trim() !== "" &&
    state.hashtags.length >= 1
  );
}

/**
 * Produces the `ComposePayload` the action consumes. Callers must check
 * `isSubmitReady` first — `receiverId` falls back to `0` (never a real
 * sunner id) if called on an incomplete state; the server re-validates
 * regardless (BR-002's defense-in-depth), so a stray `0` is rejected, not
 * trusted.
 */
export function buildPayload(state: ComposeState): ComposePayload {
  const doc = serializeToDoc(state.body);
  return {
    receiverId: state.recipient?.id ?? 0,
    title: state.title.trim(),
    doc,
    plainText: docToPlainText(doc),
    hashtagIds: state.hashtags.map((h) => h.id),
    imageUrls: state.images.map((img) => img.imageUrl).filter((url): url is string => url !== null),
    isAnonymous: state.isAnonymous,
    anonymousName: state.isAnonymous && state.anonymousName.trim() !== "" ? state.anonymousName.trim() : null,
  };
}
