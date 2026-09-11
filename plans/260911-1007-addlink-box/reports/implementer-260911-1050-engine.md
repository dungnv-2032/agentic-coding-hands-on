# Implementer report — phase 02 (engine: insertLink + validation)

## Files touched
- `lib/kudos/validate-link.ts` (new, 45 lines) — `LINK_TEXT_MIN/MAX`, `LINK_URL_MIN/MAX`,
  `LinkFieldError`, `validateLinkText`, `validateLinkUrl`, `validateLinkFields`. Imports
  `ACCEPTED_LINK_SCHEMES` from `compose-contract.ts`, no second scheme list.
- `lib/kudos/rich-text.ts` (195 lines, was 199) — added `insertLink`, restated the
  drop-overlapping-marks policy in its doc comment instead of re-deriving it, updated the file
  header to mention the phase-02 addition. Reflowed a couple of frozen parse-loop bodies onto
  one line each (formatting only, no behavior change) to stay under the 200-line cap after the
  addition.
- `lib/kudos/compose-state.ts` (168 lines, was 165) — added `insertLink` to `ComposeAction`,
  imported `insertLink` from `rich-text.ts`, added the reducer case. `toggleMark`'s link-toggle-off
  path is untouched. Switch stays exhaustive (`never` default compiles).
- `lib/kudos/compose-contract.ts` (187 lines, was 182) — `BodyEditorProps` gained
  `linkDialogInitialText: string`; `onConfirmLink` widened to `(text: string, href: string) => void`.
  Added an amendment note to the file header per its own "amend once, notify both tracks" rule.
  Nothing else in the file changed.

## Design notes
- `validateLinkText`/`validateLinkUrl` check required (trimmed) → length (raw) → format, so the
  most specific message wins, per the phase file.
- `insertLink` splices `text` over `[range.start, range.end)`: marks ending at/before `range.start`
  pass through unchanged, marks starting at/after `range.end` shift by `text.length - (range.end -
  range.start)`, and any mark overlapping the replaced span is dropped — mirroring `remapMarks`'
  published policy verbatim rather than re-deriving a second one. Empty `text` is a no-op.
- The reducer's `insertLink` case does not touch `state.errors` — this mirrors `insertMention`
  (also a body-mutating action) rather than `setBody`, since neither of those two toggle body field
  errors on their own.

## Checks
- Typecheck (`npx tsc --noEmit`): errors **only** in files outside this task's scope, exactly the
  two call sites the widened contract was expected to break:
  - `app/kudos/new/_components/compose-form.tsx:130` — `KudosBodyEditorProps` object literal is
    missing the new `linkDialogInitialText` field.
  - `app/kudos/new/_components/kudos-body-editor.tsx:147` — `onConfirm={onConfirmLink}` no longer
    matches the link-dialog's `(href: string) => void` prop; `onConfirmLink` is now
    `(text, href) => void`.
  Zero errors inside the four owned files.
- Lint (`npm run lint`): 0 errors, 31 pre-existing warnings all in `e2e/*.spec.ts` (unused vars/
  imports) — none from the four files touched here, no new warnings introduced.

## Call sites phase 03 must update
1. `app/kudos/new/_components/use-body-editor-controller.ts:59` — local prop type
   `onConfirmLink: (href: string) => void;` needs to become `(text: string, href: string) => void;`.
2. `app/kudos/new/_components/use-body-editor-controller.ts:139` — the `onConfirmLink: (href) => {`
   handler body needs the new `text` argument threaded through to call `insertLink`/dispatch the
   `insertLink` action instead of (or alongside) the existing `toggleMark` link path.
3. `app/kudos/new/_components/kudos-body-editor.tsx:83,147` — receives `onConfirmLink` from props
   and forwards it to the link dialog's `onConfirm`; the dialog itself needs a second input field
   and must call `onConfirm(text, href)`.
4. `app/kudos/new/_components/compose-form.tsx:130` — the `KudosBodyEditorProps` object literal
   passed into the body editor needs a `linkDialogInitialText` value (FR-214: prefilled from the
   current selection's text when non-empty, else `""`).

None of these four were touched by this task; they are exactly what the phase file predicted
would break, and are in scope for phase 03 (`app/kudos/new/_components/*`).

## Unresolved questions
- None. The phase file's semantics for `validateLinkText`/`validateLinkUrl`/`insertLink` were
  unambiguous and were followed as written.
