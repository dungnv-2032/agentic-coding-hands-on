---
phase: 02
title: Engine — insertLink primitive, link validation, contract amendment
owner: implementer
status: pending
feature: F005
depends_on: [01]
---

# Phase 02 — Engine

**Context:** `../spec/addlink-box/spec-delta.md` (FR-214, FR-215, FR-217, BR-006)
**Owns:** `lib/kudos/rich-text.ts`, `lib/kudos/compose-state.ts`, `lib/kudos/compose-contract.ts`,
`lib/kudos/validate-link.ts` (new)

## 1. `lib/kudos/validate-link.ts` (new, pure, no React / no I/O)

```ts
export const LINK_TEXT_MIN = 1;   export const LINK_TEXT_MAX = 100;
export const LINK_URL_MIN  = 5;   export const LINK_URL_MAX  = 2048;
export type LinkFieldError = "required" | "tooShort" | "tooLong" | "invalidUrl";
export function validateLinkText(value: string): LinkFieldError | undefined
export function validateLinkUrl(value: string): LinkFieldError | undefined
export function validateLinkFields(text: string, url: string): { text?: LinkFieldError; url?: LinkFieldError }
```

- `validateLinkText`: `required` when trimmed is empty (covers whitespace-only, item B verbatim);
  `tooLong` above 100. Length is measured on the raw value, emptiness on the trimmed one.
- `validateLinkUrl`: `required` when trimmed empty; `tooShort` under 5; `tooLong` over 2048;
  `invalidUrl` when `new URL(value)` throws **or** its protocol is outside `ACCEPTED_LINK_SCHEMES`
  (imported from `compose-contract.ts` — no second allow-list).

## 2. `insertLink` in `rich-text.ts`

`insertLink(state: RichTextState, range: TextRange, text: string, href: string): RichTextState`

Splices `text` over `[range.start, range.end)`. Marks ending at or before `range.start` are kept;
marks starting at or after `range.end` shift by `text.length - (range.end - range.start)`; marks
overlapping the replaced span are **dropped** — the published `remapMarks` policy, restated in the
doc comment, not re-derived. Adds `{ kind: "link", start: range.start, end: range.start + text.length, href }`.
An empty `text` is a no-op (the caller validates first, but the primitive does not assume it).

## 3. Reducer action

`| { type: "insertLink"; range: TextRange; text: string; href: string }` → `insertLink(...)`.
The existing `toggleMark` link path stays for the toolbar's own toggle-off behavior.

## 4. Contract amendment (the one deliberate widening)

In `BodyEditorProps`: `linkDialogInitialText: string` and
`onConfirmLink: (text: string, href: string) => void`. Note in the file header that this amendment
was made by the orchestrator for the Addlink Box frame, per the header's own rule.

## Done when

- `npm run typecheck` exits 0 across the tree (phase 03 will still be red in the UI; that is fine
  only if the failures are the dialog's, not this module's).
- Every file under 200 lines. No new dependency.
