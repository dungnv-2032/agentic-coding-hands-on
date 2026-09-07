"use client";

import { useRef } from "react";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { BodyEditorCopy, BodyEditorProps } from "@/lib/kudos/compose-contract";

import { LinkDialog } from "./link-dialog";
import { MentionMenu } from "./mention-menu";
import { RichTextToolbar } from "./rich-text-toolbar";

/**
 * `mms_D_text filed` + `mms_C_Chức năng` (mm:I520:11647;520:9876) — the
 * toolbar row sits directly above the textarea with no gap, sharing one
 * visual border box (toolbar top corners rounded, textarea bottom corners
 * rounded — see below). A plain controlled `<textarea>`, not
 * `contenteditable` (phase 01 § Key Insight 2, re-affirmed here): marks
 * never render in-editor, `aria-pressed` is the only in-editor feedback.
 *
 * Step-1 probe (this phase's own gate, recorded in full in this phase's
 * report): React 19.2's shipped `react-dom-client.development.js` sets
 * `element.defaultValue = value` on every update for a controlled textarea
 * with no `defaultValue` prop (`updateTextarea()`,
 * node_modules/react-dom/cjs/react-dom-client.development.js:1842-1854) —
 * confirmed by reading the actual shipped bundle, not memory. Per the
 * WHATWG spec a textarea's `defaultValue` IDL setter replaces the element's
 * descendant text content, so `textContent` mirrors `value` — this is
 * exactly what `ID-13` depends on. This component therefore renders
 * `<textarea value={text} onChange={...}>` with no `defaultValue` prop and
 * no children, deliberately.
 *
 * No selection/range logic lives in this file. `BodyEditorProps`'s
 * `onToggleInlineMark`/`onToggleBlock`/`onInsertMention` callbacks carry no
 * range or insertion index, and this component is never given
 * `RichTextState.inline`/`blocks` — only `text` — so it cannot call
 * `toggleInlineMark`/`toggleBlockMark`/`insertMention` itself (the success
 * criteria's "zero reimplementation" requirement is satisfied by omission,
 * not by a local call). See this phase's report for the recommended
 * wiring: the caller of these callbacks (phase 11/12) reads the current
 * selection from the DOM via `document.querySelector('[data-testid="body-
 * editor"]')` at the moment a toolbar button fires, since that testid is
 * the one stable, public hook this component guarantees.
 *
 * `mentionQuery`/`mentionOptions` are likewise parent-computed (the trailing
 * `/@([^\s@]*)$/` match against `state.body.text`, Key Insight #2) — this
 * component only renders what it is given.
 *
 * Copy: `BodyEditorCopy` (frozen, `compose-contract.ts`) covers the
 * textarea's own placeholder/hint/community-standards label. It has no room
 * for the toolbar's six aria-labels or the link dialog's four strings, so
 * `KudosBodyEditorCopy` widens it locally via `Dictionary["kudosCompose"]`
 * slices (test-contract.md's "Copy plumbing" ratification explicitly
 * authorizes each phase to type its own slice) — flagged in this phase's
 * report as the one place `BodyEditorProps` needed more than the frozen
 * `BodyEditorCopy` carries.
 */
export interface KudosBodyEditorCopy extends BodyEditorCopy {
  toolbar: Dictionary["kudosCompose"]["toolbar"];
  linkDialog: Dictionary["kudosCompose"]["linkDialog"];
  /** `Dictionary["kudosCompose"].buttons.cancel` — reused, not a second "Hủy" key. */
  cancelLabel: string;
}

export interface KudosBodyEditorProps extends Omit<BodyEditorProps, "copy"> {
  copy: KudosBodyEditorCopy;
}

export function KudosBodyEditor({
  copy,
  text,
  activeInlineMarks,
  activeBlock,
  mentionQuery,
  mentionOptions,
  linkDialogOpen,
  error,
  onTextChange,
  onToggleInlineMark,
  onToggleBlock,
  onMentionQueryChange,
  onInsertMention,
  onOpenLinkDialog,
  onConfirmLink,
  onCloseLinkDialog,
}: KudosBodyEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const linkButtonRef = useRef<HTMLButtonElement>(null);

  return (
    <div className="relative flex w-full flex-col gap-1">
      {/* mm:I520:11647;520:9876 — toolbar row + community-standards link flush together, 672px total */}
      <div className="flex w-full">
        <RichTextToolbar
          copy={copy.toolbar}
          activeInlineMarks={activeInlineMarks}
          activeBlock={activeBlock}
          onToggleInlineMark={onToggleInlineMark}
          onToggleBlock={onToggleBlock}
          onOpenLinkDialog={onOpenLinkDialog}
          linkButtonRef={linkButtonRef}
        />
        {/* mm:I520:11647;3053:11619 (`Button`) + mm:I520:11647;3053:11621 (text,
            character "Tiêu chuẩn cộng đồng", color rgba(228,96,96,1) —
            MoMorph's field name for TEXT-node fill). Directly measured this
            pass: this "unauthored" link (test-contract.md ratification item
            6) does have a real node — it sits flush after the quote button,
            filling the toolbar row's remaining 336px, and its own
            border-radius (0 8px 0 0) is what closes the bar's top-right
            corner. The sibling `Title` instance (mm:I520:11647;3053:10121,
            1069-1403) is genuinely clipped outside the 672px parent and is
            NOT rendered — that is the real "1006px" artifact
            (clarifications.md § Unresolved question 6). */}
        <a
          href="#"
          data-testid="community-standards-link"
          className="-ml-px flex h-10 flex-1 items-center justify-center rounded-tr-lg border border-[#998C5F] bg-[rgba(255,234,158,0.10)] px-4 text-base leading-6 font-bold tracking-[0.15px] text-[#E46060]"
        >
          {copy.communityStandardsLabel}
        </a>
      </div>
      {/* mm:I520:11647;520:9886 — h-[200px] min-h-[120px] border-[#998C5F] rounded-b-lg pl-6 */}
      <textarea
        ref={textareaRef}
        data-testid="body-editor"
        placeholder={copy.placeholder}
        value={text}
        aria-invalid={error ? "true" : undefined}
        onChange={(event) => onTextChange(event.target.value)}
        className={`h-[200px] min-h-[120px] w-full resize-none rounded-b-lg border bg-white py-4 pl-6 text-base font-bold tracking-[0.15px] text-[#00101A] outline-none placeholder:font-bold placeholder:text-[#999999] ${
          error ? "border-[#CF1322]" : "border-[#998C5F]"
        }`}
      />
      <MentionMenu
        open={mentionQuery !== null}
        options={mentionOptions}
        onSelect={onInsertMention}
        onDismiss={() => onMentionQueryChange(null)}
        anchorRef={textareaRef}
      />
      {/* mm:I520:11647;520:9888 */}
      <p data-testid="body-hint" className="text-base leading-6 font-bold tracking-[0.15px] text-[#00101A]">
        {copy.hint}
      </p>
      <LinkDialog
        open={linkDialogOpen}
        copy={{ ...copy.linkDialog, cancel: copy.cancelLabel }}
        onConfirm={onConfirmLink}
        onCancel={onCloseLinkDialog}
        triggerRef={linkButtonRef}
      />
    </div>
  );
}
