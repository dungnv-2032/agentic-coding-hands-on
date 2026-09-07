"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type {
  ComposeSunnerOption,
  ToggleableBlock,
  ToggleableInlineMark,
} from "@/lib/kudos/compose-contract";
import type { ComposeAction, ComposeState } from "@/lib/kudos/compose-state";
import { isMarkActive, type TextRange } from "@/lib/kudos/rich-text";

const INLINE_MARKS: readonly ToggleableInlineMark[] = ["bold", "italic", "strike", "link"];
const BLOCK_MARKS: readonly ToggleableBlock[] = ["ordered-list-item", "quote"];
/** Trailing `@query` at the cursor end — the same rule clarifications.md's "real autocomplete" describes. */
const MENTION_TRIGGER = /@([^\s@]*)$/;

/**
 * Diacritic-insensitive fold for Vietnamese name search. The authored test
 * data (design/test-cases.csv ID-33) types `@Nguyen` — no diacritics —
 * against seeded names like `Nguyễn Văn Quy`; a plain `.toLowerCase()`
 * substring check never matches. `normalize("NFD")` decomposes most
 * precomposed Vietnamese letters into base + combining mark, which the
 * regex then strips, but `đ`/`Đ` is a distinct base letter in Vietnamese
 * (not a base letter plus a mark), so NFD alone doesn't fold it — handled
 * explicitly (seed has `Đỗ Hoàng Hiệp`). Exported so `recipient-picker.tsx`
 * can reuse the same fold rather than a second, possibly-divergent one.
 */
const COMBINING_MARK_LOW = 0x0300;
const COMBINING_MARK_HIGH = 0x036f;

export function foldVietnameseText(value: string): string {
  const withoutMarks = Array.from(value.normalize("NFD"))
    .filter((char) => {
      const code = char.codePointAt(0) ?? 0;
      return code < COMBINING_MARK_LOW || code > COMBINING_MARK_HIGH;
    })
    .join("");
  return withoutMarks.replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();
}

function readBodySelection(): TextRange {
  const el = document.querySelector<HTMLTextAreaElement>('[data-testid="body-editor"]');
  return el ? { start: el.selectionStart ?? 0, end: el.selectionEnd ?? 0 } : { start: 0, end: 0 };
}

export interface BodyEditorController {
  activeInlineMarks: readonly ToggleableInlineMark[];
  activeBlock: ToggleableBlock | null;
  mentionQuery: string | null;
  mentionOptions: readonly ComposeSunnerOption[];
  linkDialogOpen: boolean;
  onTextChange: (text: string) => void;
  onToggleInlineMark: (mark: ToggleableInlineMark) => void;
  onToggleBlock: (block: ToggleableBlock) => void;
  onMentionQueryChange: (query: string | null) => void;
  onInsertMention: (option: ComposeSunnerOption) => void;
  onOpenLinkDialog: () => void;
  onConfirmLink: (href: string) => void;
  onCloseLinkDialog: () => void;
}

/**
 * Owns the selection-dependent wiring `BodyEditorProps` needs but
 * `kudos-body-editor.tsx` deliberately doesn't compute itself (phase 09's
 * report: its callbacks carry no range/index, and `mentionQuery`/
 * `mentionOptions` are parent-computed). Reads the live textarea's own
 * selection from the DOM at the moment a toolbar button fires — the one
 * stable hook the editor guarantees — exactly phase 09's recommended wiring.
 * Reuses `isMarkActive` (rich-text.ts, frozen) rather than reimplementing
 * mark detection.
 */
export function useBodyEditorController(
  state: ComposeState,
  dispatch: (action: ComposeAction) => void,
  recipients: readonly ComposeSunnerOption[],
): BodyEditorController {
  const [selection, setSelection] = useState<TextRange>({ start: 0, end: 0 });
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [mentionDismissed, setMentionDismissed] = useState(false);

  useEffect(() => {
    function handleSelectionChange() {
      const el = document.querySelector<HTMLTextAreaElement>('[data-testid="body-editor"]');
      if (el && document.activeElement === el) setSelection(readBodySelection());
    }
    document.addEventListener("selectionchange", handleSelectionChange);
    return () => document.removeEventListener("selectionchange", handleSelectionChange);
  }, []);

  const mentionMatch = useMemo(() => MENTION_TRIGGER.exec(state.body.text), [state.body.text]);
  const mentionQuery = mentionDismissed ? null : (mentionMatch?.[1] ?? null);
  const mentionOptions = useMemo(
    () =>
      mentionQuery === null
        ? []
        : recipients.filter((r) => foldVietnameseText(r.fullName).includes(foldVietnameseText(mentionQuery))),
    [recipients, mentionQuery],
  );

  const onTextChange = useCallback(
    (text: string) => {
      dispatch({ type: "setBody", text });
      setMentionDismissed(false);
    },
    [dispatch],
  );

  const onInsertMention = useCallback(
    (option: ComposeSunnerOption) => {
      if (!mentionMatch) return;
      // Removes the trailing "@query" the user typed, then inserts the real
      // mention run at the same position — a bare `insertMention` alone would
      // leave both the typed "@" and the inserted one (rich-text.ts inserts,
      // it never replaces).
      const at = mentionMatch.index;
      const text = state.body.text.slice(0, at) + state.body.text.slice(at + mentionMatch[0].length);
      dispatch({ type: "setBody", text });
      dispatch({ type: "insertMention", at, label: option.fullName, sunnerId: option.id });
      setMentionDismissed(true);
    },
    [dispatch, mentionMatch, state.body.text],
  );

  return {
    activeInlineMarks: INLINE_MARKS.filter((mark) => isMarkActive(state.body, mark, selection)),
    activeBlock: BLOCK_MARKS.find((block) => isMarkActive(state.body, block, selection)) ?? null,
    mentionQuery,
    mentionOptions,
    linkDialogOpen,
    onTextChange,
    onToggleInlineMark: (mark) => dispatch({ type: "toggleMark", kind: mark, range: readBodySelection() }),
    onToggleBlock: (block) => dispatch({ type: "toggleMark", kind: block, range: readBodySelection() }),
    onMentionQueryChange: (query) => {
      if (query === null) setMentionDismissed(true);
    },
    onInsertMention,
    onOpenLinkDialog: () => setLinkDialogOpen(true),
    onConfirmLink: (href) => {
      dispatch({ type: "toggleMark", kind: "link", range: readBodySelection(), href });
      setLinkDialogOpen(false);
    },
    onCloseLinkDialog: () => setLinkDialogOpen(false),
  };
}
