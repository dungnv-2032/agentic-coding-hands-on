/**
 * Frozen integration contract for Viết Kudo (F005, `/kudos/new`).
 *
 * Types + caps + Track A prop interfaces only — no React, no `next/*`, no
 * `@/lib/supabase/*`, no `Intl` (`derive.ts:1-9`'s hydration-drift rule).
 * Track B (03/04/07) PRODUCES `ComposeOptionsView` and satisfies
 * `CreateKudos`/`UploadKudosImage`; Track A (06/08-11) CONSUMES the props
 * below; phase 12 wires both at `app/kudos/new/page.tsx`. Neither track
 * imports the other. A missing field is escalated to the orchestrator, who
 * amends this once and notifies both tracks — never patched inside a track.
 */

// Rich-text document model (technical-spec.md § 4.2, verbatim).
export interface KudosDoc { blocks: KudosBlock[] }

export type KudosBlock =
  | { type: "paragraph"; runs: KudosRun[] }
  | { type: "ordered-list-item"; runs: KudosRun[] }
  | { type: "quote"; runs: KudosRun[] };

export type KudosRun =
  | { type: "text"; text: string; bold?: boolean; italic?: boolean; strike?: boolean }
  | { type: "link"; text: string; href: string }
  | { type: "mention"; sunnerId: number; label: string };

/** `kudos.message_format`. `'plain'` is F004's 57 seeded rows, unchanged. */
export type MessageFormat = "plain" | "doc";
/** Toggled by the quote/ordered-list buttons; `paragraph` is the untoggled default. */
export type ToggleableBlock = "ordered-list-item" | "quote";
/** Toggled by the bold/italic/strike/link buttons; `mention` is inserted, never toggled. */
export type ToggleableInlineMark = "bold" | "italic" | "strike" | "link";

// Caps & accepted values (BR-002, BR-003, BR-004).
export const MAX_HASHTAGS = 5;
export const MAX_IMAGES = 5;
/** jpeg/png are the tested pair (ID-21/22); gif/webp are the honest remainder of "image types". */
export const ACCEPTED_IMAGE_MIME = ["image/jpeg", "image/png", "image/gif", "image/webp"] as const;
export type AcceptedImageMime = (typeof ACCEPTED_IMAGE_MIME)[number];
/** `javascript:`, `data:` and `vbscript:` never survive this allow-list. */
export const ACCEPTED_LINK_SCHEMES = ["http:", "https:", "mailto:"] as const;
export type AcceptedLinkScheme = (typeof ACCEPTED_LINK_SCHEMES)[number];

// Options fetched once, filtered client-side (ALG-001).
export interface ComposeSunnerOption { id: number; fullName: string; avatarUrl: string }
export interface ComposeHashtagOption { id: number; name: string }
export interface ComposeOptionsView { recipients: ComposeSunnerOption[]; hashtags: ComposeHashtagOption[] }

/** A2 uploads it; `id` is client-only list identity, never a server id. `imageUrl` is `null` while A2's upload is in flight. */
export interface ComposeAttachedImage {
  id: string;
  fileName: string;
  imageUrl: string | null;
}

export interface ComposePayload {
  receiverId: number;
  title: string;
  doc: KudosDoc;
  plainText: string;
  hashtagIds: number[];
  imageUrls: string[];
  isAnonymous: boolean;
  anonymousName: string | null;
}

/** Codes, never copy — one string, one owner: phase 06's dictionary. */
export type ComposeFieldErrorCode = "required" | "tooMany" | "invalidType" | "unknown";
export interface ComposeFieldErrors {
  recipient?: ComposeFieldErrorCode;
  title?: ComposeFieldErrorCode;
  body?: ComposeFieldErrorCode;
  hashtag?: ComposeFieldErrorCode;
  form?: ComposeFieldErrorCode;
}

export type CreateKudosState = { errors: ComposeFieldErrors } | { ok: true };
export type CreateKudos = (prevState: CreateKudosState, payload: ComposePayload) => Promise<CreateKudosState>;
export interface UploadResult { imageUrl: string }
export type UploadKudosImage = (file: File) => Promise<UploadResult>;

// Track A leaf component props — each takes its copy slice as `copy` (never
// importing `Dictionary` deeply) and reports upward via callbacks only.

/** Backs `data-testid="field-error-{recipient|title|body|hashtag}"`. */
export interface ComposeFieldProps {
  field: "recipient" | "title" | "body" | "hashtag";
  error?: ComposeFieldErrorCode;
  copy: Record<ComposeFieldErrorCode, string>;
}

export interface RecipientPickerCopy { placeholder: string; emptyLabel: string }
export interface RecipientPickerProps {
  copy: RecipientPickerCopy;
  options: readonly ComposeSunnerOption[];
  value: ComposeSunnerOption | null;
  query: string;
  error?: ComposeFieldErrorCode;
  onQueryChange: (query: string) => void;
  onSelect: (option: ComposeSunnerOption) => void;
}

export interface TitleFieldCopy { placeholder: string; hintExample: string; hintUsage: string }
export interface TitleFieldProps {
  copy: TitleFieldCopy;
  value: string;
  error?: ComposeFieldErrorCode;
  onChange: (title: string) => void;
}

export interface BodyEditorCopy { placeholder: string; hint: string; communityStandardsLabel: string }
/** Marks never render in-editor — only `aria-pressed` reflects `activeInlineMarks`/`activeBlock`. */
export interface BodyEditorProps {
  copy: BodyEditorCopy;
  text: string;
  activeInlineMarks: readonly ToggleableInlineMark[];
  activeBlock: ToggleableBlock | null;
  mentionQuery: string | null;
  mentionOptions: readonly ComposeSunnerOption[];
  linkDialogOpen: boolean;
  error?: ComposeFieldErrorCode;
  onTextChange: (text: string) => void;
  onToggleInlineMark: (mark: ToggleableInlineMark) => void;
  onToggleBlock: (block: ToggleableBlock) => void;
  onMentionQueryChange: (query: string | null) => void;
  onInsertMention: (option: ComposeSunnerOption) => void;
  onOpenLinkDialog: () => void;
  onConfirmLink: (href: string) => void;
  onCloseLinkDialog: () => void;
}

/** `addLabel` contains both "Hashtag" and "Tối đa 5" (test-contract.md § Hashtags). */
export interface HashtagPickerCopy { addLabel: string }
export interface HashtagPickerProps {
  copy: HashtagPickerCopy;
  options: readonly ComposeHashtagOption[];
  selected: readonly ComposeHashtagOption[];
  error?: ComposeFieldErrorCode;
  onAdd: (option: ComposeHashtagOption) => void;
  onRemove: (id: number) => void;
}

/** `addLabel` contains both "Image" and "Tối đa 5" (test-contract.md § Images). */
export interface ImagePickerCopy { addLabel: string; invalidTypeError: string }
export interface ImagePickerProps {
  copy: ImagePickerCopy;
  images: readonly ComposeAttachedImage[];
  error?: ComposeFieldErrorCode;
  onFilesSelected: (files: readonly File[]) => void;
  onRemove: (id: string) => void;
}

export interface AnonymousToggleCopy { checkboxLabel: string; nameInputLabel: string }
export interface AnonymousToggleProps {
  copy: AnonymousToggleCopy;
  checked: boolean;
  name: string;
  onToggle: (checked: boolean) => void;
  onNameChange: (name: string) => void;
}

export interface ComposeFormCopy {
  h1: string;
  cancelLabel: string;
  submitLabel: string;
  recipient: RecipientPickerCopy;
  title: TitleFieldCopy;
  body: BodyEditorCopy;
  hashtag: HashtagPickerCopy;
  image: ImagePickerCopy;
  anonymous: AnonymousToggleCopy;
  fieldErrors: Record<ComposeFieldErrorCode, string>;
}
/** `isSubmitReady` backs `data-submit-ready`, never `disabled`/`aria-disabled` (test-contract.md § Blueprint ratification). */
export interface ComposeFormProps {
  copy: ComposeFormCopy;
  options: ComposeOptionsView;
  createKudos: CreateKudos;
  uploadKudosImage: UploadKudosImage;
  cancelHref: string;
  isSubmitReady: boolean;
}
