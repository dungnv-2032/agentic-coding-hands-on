"use client";

import type { RefObject, SVGProps } from "react";

import { IconLink } from "@/app/kudos/_components/kudos-icons";
import type { ToggleableBlock, ToggleableInlineMark } from "@/lib/kudos/compose-contract";
import type { Dictionary } from "@/lib/i18n/dictionaries";

/**
 * Five inline glyphs traced from MoMorph's per-button SVG exports
 * (mm:I520:11647;520:9881 / 662:11119 / 662:11213 / 662:10376 / 662:10647),
 * `fill="white"` swapped for `currentColor` (code-rules.md rule 2a) — the
 * raw export's white fill is invisible against this modal's cream/white
 * surfaces. The sixth glyph (link, mm:I520:11647;662:10507) is
 * byte-identical to the already-shipped `IconLink` in kudos-icons.tsx and is
 * reused rather than duplicated (DRY).
 *
 * Icon color: no `fills` data is exposed by MoMorph for these
 * instance-swapped vector slots (`get_node`/`get_node_context` return layout
 * only). `#00101A` is not a guess — it is measured directly from the sibling
 * hint text in the same frame (mm:I520:11647;520:9888, `backgroundColor:
 * rgba(0, 16, 26, 1)`, MoMorph's field name for TEXT-node fill), the same
 * dark foreground already used by every other text element in this modal
 * (title, title-field, recipient input — see `title-field.tsx`).
 */
function IconBold(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M13.5 15.5H10V12.5H13.5C13.8978 12.5 14.2794 12.658 14.5607 12.9393C14.842 13.2206 15 13.6022 15 14C15 14.3978 14.842 14.7794 14.5607 15.0607C14.2794 15.342 13.8978 15.5 13.5 15.5ZM10 6.5H13C13.3978 6.5 13.7794 6.65804 14.0607 6.93934C14.342 7.22064 14.5 7.60218 14.5 8C14.5 8.39782 14.342 8.77936 14.0607 9.06066C13.7794 9.34196 13.3978 9.5 13 9.5H10M15.6 10.79C16.57 10.11 17.25 9 17.25 8C17.25 5.74 15.5 4 13.25 4H7V18H14.04C16.14 18 17.75 16.3 17.75 14.21C17.75 12.69 16.89 11.39 15.6 10.79Z"
        fill="currentColor"
      />
    </svg>
  );
}
function IconItalic(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path d="M10 4V7H12.21L8.79 15H6V18H14V15H11.79L15.21 7H18V4H10Z" fill="currentColor" />
    </svg>
  );
}
function IconStrike(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M7.62432 9.37769C6.42432 7.07769 8.12432 4.37769 10.5243 3.87769C13.6243 2.87769 18.1243 4.27769 18.0243 8.07769H15.0243C15.0243 7.77769 14.9243 7.47769 14.9243 7.27769C14.7243 6.67769 14.3243 6.37769 13.7243 6.17769C12.9243 5.87769 11.6243 5.97769 10.9243 6.47769C9.42432 7.77769 10.8243 9.07769 12.4243 9.57769H7.82432C7.72432 9.47769 7.72432 9.37769 7.62432 9.37769ZM21.4243 12.5777V10.5777H3.42432V12.5777H13.0243C13.2243 12.6777 13.4243 12.6777 13.6243 12.7777C14.2243 13.0777 14.7243 13.2777 14.9243 13.8777C15.0243 14.2777 15.1243 14.7777 14.9243 15.1777C14.7243 15.6777 14.3243 15.8777 13.8243 16.0777C12.0243 16.5777 9.82432 15.8777 9.92432 13.6777H6.92432C6.82432 16.2777 9.02432 18.0777 11.4243 18.3777C15.2243 19.1777 19.7243 16.7777 17.7243 12.4777L21.4243 12.5777Z"
        fill="currentColor"
      />
    </svg>
  );
}
function IconOrderedList(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M7 13V11H21V13H7ZM7 19V17H21V19H7ZM7 7V5H21V7H7ZM3 8V5H2V4H4V8H3ZM2 17V16H5V20H2V19H4V18.5H3V17.5H4V17H2ZM4.25 10C4.44891 10 4.63968 10.079 4.78033 10.2197C4.92098 10.3603 5 10.5511 5 10.75C5 10.95 4.92 11.14 4.79 11.27L3.12 13H5V14H2V13.08L4 11H2V10H4.25Z"
        fill="currentColor"
      />
    </svg>
  );
}
function IconQuote(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path
        d="M12.9999 6V14H14.8799L12.8799 18H18.6199L20.9999 13.24V6M14.9999 8H18.9999V12.76L17.3799 16H16.1199L18.1199 12H14.9999M2.99988 6V14H4.87988L2.87988 18H8.61988L10.9999 13.24V6M4.99988 8H8.99988V12.76L7.37988 16H6.11988L8.11988 12H4.99988V8Z"
        fill="currentColor"
      />
    </svg>
  );
}

export type RichTextToolbarCopy = Dictionary["kudosCompose"]["toolbar"];

/**
 * mm:I520:11647;520:9877 (`mms_C_Chức năng`) — six 56×40px buttons, flush
 * against each other (`-ml-px` collapses the shared 1px borders), each
 * `type="button"` (a bare `<button>` inside `compose-form`'s `<form>` would
 * submit it on every formatting click). No selection/range logic lives
 * here or anywhere in this phase's files: `onToggleInlineMark`/
 * `onToggleBlock` carry no range in the frozen `BodyEditorProps`, and this
 * component never receives the full `RichTextState.inline`/`blocks` needed
 * to call `toggleInlineMark`/`toggleBlockMark` itself — see this phase's
 * report for the resolved wiring recommendation.
 */
export interface RichTextToolbarProps {
  copy: RichTextToolbarCopy;
  activeInlineMarks: readonly ToggleableInlineMark[];
  activeBlock: ToggleableBlock | null;
  onToggleInlineMark: (mark: ToggleableInlineMark) => void;
  onToggleBlock: (block: ToggleableBlock) => void;
  onOpenLinkDialog: () => void;
  linkButtonRef?: RefObject<HTMLButtonElement | null>;
}

const BUTTON = "flex h-10 w-14 shrink-0 items-center justify-center border border-[#998C5F] text-[#00101A]";

export function RichTextToolbar({
  copy,
  activeInlineMarks,
  activeBlock,
  onToggleInlineMark,
  onToggleBlock,
  onOpenLinkDialog,
  linkButtonRef,
}: RichTextToolbarProps) {
  const isBold = activeInlineMarks.includes("bold");
  const isItalic = activeInlineMarks.includes("italic");
  const isStrike = activeInlineMarks.includes("strike");
  return (
    // mm:I520:11647;520:9877
    <div className="flex shrink-0">
      {/* mm:I520:11647;520:9881 */}
      <button
        type="button"
        data-testid="toolbar-bold"
        aria-label={copy.bold}
        aria-pressed={isBold ? "true" : "false"}
        onClick={() => onToggleInlineMark("bold")}
        className={`${BUTTON} rounded-tl-lg`}
      >
        <IconBold className="h-6 w-6" aria-hidden />
      </button>
      {/* mm:I520:11647;662:11119 */}
      <button
        type="button"
        data-testid="toolbar-italic"
        aria-label={copy.italic}
        aria-pressed={isItalic ? "true" : "false"}
        onClick={() => onToggleInlineMark("italic")}
        className={`${BUTTON} -ml-px`}
      >
        <IconItalic className="h-6 w-6" aria-hidden />
      </button>
      {/* mm:I520:11647;662:11213 */}
      <button
        type="button"
        data-testid="toolbar-strike"
        aria-label={copy.strike}
        aria-pressed={isStrike ? "true" : "false"}
        onClick={() => onToggleInlineMark("strike")}
        className={`${BUTTON} -ml-px`}
      >
        <IconStrike className="h-6 w-6" aria-hidden />
      </button>
      {/* mm:I520:11647;662:10376 — block toggle, no aria-pressed (test-contract.md
          § Rich-text toolbar). `data-active` styling (not aria) uses
          `--Details-ButtonSecondary-Hover` (rgba(255,234,158,0.40)), a real
          token from this file's variable set, not an invented color. */}
      <button
        type="button"
        data-testid="toolbar-ordered-list"
        aria-label={copy.orderedList}
        data-active={activeBlock === "ordered-list-item" ? "true" : undefined}
        onClick={() => onToggleBlock("ordered-list-item")}
        className={`${BUTTON} -ml-px data-[active=true]:bg-[rgba(255,234,158,0.40)]`}
      >
        <IconOrderedList className="h-6 w-6" aria-hidden />
      </button>
      {/* mm:I520:11647;662:10507 — opens link-dialog, no aria-pressed */}
      <button
        ref={linkButtonRef}
        type="button"
        data-testid="toolbar-link"
        aria-label={copy.link}
        onClick={onOpenLinkDialog}
        className={`${BUTTON} -ml-px`}
      >
        <IconLink className="h-6 w-6" aria-hidden />
      </button>
      {/* mm:I520:11647;662:10647 — measured square (no border-radius on this
          node; the frame's own top-right rounding belongs to the
          community-standards link that follows it, see kudos-body-editor.tsx) */}
      <button
        type="button"
        data-testid="toolbar-quote"
        aria-label={copy.quote}
        data-active={activeBlock === "quote" ? "true" : undefined}
        onClick={() => onToggleBlock("quote")}
        className={`${BUTTON} -ml-px data-[active=true]:bg-[rgba(255,234,158,0.40)]`}
      >
        <IconQuote className="h-6 w-6" aria-hidden />
      </button>
    </div>
  );
}
