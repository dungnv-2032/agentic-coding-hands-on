"use client";

import { useEffect, useRef, useState, type KeyboardEvent, type RefObject, type SVGProps } from "react";

import { useDismissOnOutside } from "@/app/_components/use-dismiss-on-outside";
import { LinkDialogField } from "./link-dialog-field";
import { IconLink } from "@/app/kudos/_components/kudos-icons";
import { validateLinkFields, validateLinkUrl, type LinkFieldError } from "@/lib/kudos/validate-link";

/**
 * The link toolbar button's dialog — rebuilt against the Addlink Box frame
 * (`mm:1002:12682`, `design/momorph-node-values.md`, all values below cite
 * that file's node IDs). Supersedes the earlier one-field/disabled-confirm
 * shape per `clarifications.md` § "The shipped dialog has ONE field".
 *
 * Panel `mm:1002:12682`: 752×388, padding 40, gap 32 (column), radius 24,
 * `#FFF8E1`. Rows B/C: 672×56, gap 16, centered — labels are NOT a fixed-width
 * column (107px "Nội dung" vs 47px "URL"), so no aligned label column is
 * rendered here, just a plain flex row. Row D: 672×60, gap 24.
 */
export interface LinkDialogCopy {
  heading: string;
  textLabel: string;
  urlLabel: string;
  confirm: string;
  cancel: string;
  /** Unauthored — the frame carries no error state (design/momorph-node-values.md § "Not in the design"). */
  errors: Record<LinkFieldError, string>;
}

export interface LinkDialogProps {
  open: boolean;
  copy: LinkDialogCopy;
  /** The textarea selection captured at the moment the dialog opened (controller-owned). */
  initialText: string;
  onConfirmLink: (text: string, href: string) => void;
  onCancel: () => void;
  triggerRef?: RefObject<HTMLButtonElement | null>;
}

/** Unauthored icon — `get_media_file` for `MM_MEDIA_Close` (`mm:...;186:2761`) 401'd this
 * session; hand-drawn Material "close" glyph, same precedent as `IconExpand`/`IconPanZoom`
 * in `kudos-icons.tsx`. */
function IconClose(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M6.4 19L5 17.6L10.6 12L5 6.4L6.4 5L12 10.6L17.6 5L19 6.4L13.4 12L19 17.6L17.6 19L12 13.4L6.4 19Z"
        fill="currentColor"
      />
    </svg>
  );
}

export function LinkDialog({ open, copy, initialText, onConfirmLink, onCancel, triggerRef }: LinkDialogProps) {
  // Lazy initializers, not an effect: the caller (`kudos-body-editor.tsx`)
  // keys this component on open/closed, so every open is a genuinely fresh
  // mount — `Nội dung` seeds from the range captured at open (FR-214), `URL`
  // and both error slots always start blank (FR-218), with no setState-in-
  // effect needed to force the reset.
  const [text, setText] = useState(initialText);
  const [url, setUrl] = useState("");
  const [textError, setTextError] = useState<LinkFieldError>();
  const [urlError, setUrlError] = useState<LinkFieldError>();
  const rootRef = useRef<HTMLDivElement>(null);
  const textInputRef = useRef<HTMLInputElement>(null);
  const fallbackTriggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) textInputRef.current?.focus();
  }, [open]);

  useDismissOnOutside(open, rootRef, triggerRef ?? fallbackTriggerRef, onCancel);

  if (!open) return null;

  function handleUrlBlur() {
    // FR-215: URL format is checked on blur as well as on Lưu.
    setUrlError(validateLinkUrl(url));
  }

  /**
   * `aria-modal="true"` promises focus is confined here, and `useDismissOnOutside`
   * only covers pointer-outside + Escape. Without this, Shift+Tab from the first
   * input lands on the live `body-editor` behind the dialog: the user can edit the
   * body, tab back, and confirm against the range captured at open — which now
   * points into different text. Trapping Tab is what makes the captured range safe
   * (the controller also clamps it, belt and braces).
   */
  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key !== "Tab") return;
    const focusable = rootRef.current?.querySelectorAll<HTMLElement>("input, button");
    if (!focusable || focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function handleConfirm() {
    const fieldErrors = validateLinkFields(text, url);
    setTextError(fieldErrors.text);
    setUrlError(fieldErrors.url);
    if (fieldErrors.text || fieldErrors.url) return;
    onConfirmLink(text, url);
  }

  return (
    // mm: unauthored overlay — the frame is the panel alone (design/momorph-node-values.md).
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/40">
      {/* mm:1002:12682 */}
      <div
        ref={rootRef}
        data-testid="link-dialog"
        role="dialog"
        aria-modal="true"
        aria-label={copy.heading}
        onKeyDown={handleKeyDown}
        className="flex w-full max-w-[752px] flex-col items-start gap-8 rounded-3xl bg-[#FFF8E1] p-10"
      >
        {/* mm:I1002:12682;1002:12500 */}
        <h2 className="w-full text-left text-[32px] leading-10 font-bold text-[#00101A]">{copy.heading}</h2>

        {/* mm:I1002:12682;1002:12501 */}
        <LinkDialogField
          id="link-text-input"
          label={copy.textLabel}
          value={text}
          type="text"
          interactiveLabel
          error={textError}
          errorCopy={copy.errors}
          inputRef={textInputRef}
          onChange={setText}
        />

        {/* mm:I1002:12682;1002:12652 */}
        <LinkDialogField
          id="link-url-input"
          label={copy.urlLabel}
          value={url}
          type="url"
          interactiveLabel={false}
          error={urlError}
          errorCopy={copy.errors}
          onChange={setUrl}
          onBlur={handleUrlBlur}
        />

        {/* mm:I1002:12682;1002:12543 */}
        <div className="flex w-full items-start gap-6">
          {/* mm:I1002:12682;1002:12544 */}
          <button
            type="button"
            data-testid="link-cancel"
            onClick={onCancel}
            className="flex h-[60px] items-center gap-2 rounded border border-[#998C5F] bg-[rgba(255,234,158,0.10)] px-10 py-4 text-base font-bold text-[#00101A]"
          >
            {copy.cancel}
            {/* mm:I1002:12682;1002:12544;186:2761 */}
            <IconClose className="h-6 w-6" aria-hidden />
          </button>
          {/* mm:I1002:12682;1002:12545 — never disabled (FR-216) */}
          <button
            type="button"
            data-testid="link-confirm"
            onClick={handleConfirm}
            className="flex h-[60px] flex-1 items-center justify-center gap-2 rounded-lg bg-[#FFEA9E] p-4 text-base font-bold text-[#00101A]"
          >
            {copy.confirm}
            {/* mm:I1002:12682;1002:12545;186:1766 */}
            <IconLink className="h-6 w-6" aria-hidden />
          </button>
        </div>
      </div>
    </div>
  );
}
