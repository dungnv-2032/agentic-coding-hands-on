# Report — Addlink Box UI (`link-dialog.tsx` rebuild)

Phase 03, F005 spec-delta (`OyDLDuSGEa`). Rebuilt `LinkDialog` two-field per
the frame, wired the controller's capture-at-open/insert-on-confirm contract,
and closed the two typecheck errors phase 02 left at the `BodyEditorProps`
boundary.

## Files changed

- `app/kudos/new/_components/link-dialog.tsx` — full rewrite: title, two
  labeled rows (`Nội dung`/`URL`), always-clickable `Lưu`, per-field errors,
  `Hủy` with X icon.
- `app/kudos/new/_components/kudos-body-editor.tsx` — destructure/pass
  `linkDialogInitialText`; `LinkDialog` now keyed on open/closed and called
  with `initialText`/`onConfirmLink`.
- `app/kudos/new/_components/use-body-editor-controller.ts` — added
  `linkDialogInitialText` + a `linkRangeRef`; `onOpenLinkDialog` captures the
  live selection range and its substring once; `onConfirmLink(text, href)`
  dispatches `insertLink` with the range captured at open, never re-reading
  the DOM selection at confirm time.
- `lib/i18n/messages/dictionary.ts` — `kudosCompose.linkDialog` reshaped to
  `{ heading, textLabel, urlLabel, confirm, errors: Record<LinkFieldError, string> }`.
- `lib/i18n/messages/vi-kudos-compose.ts` / `en-kudos-compose.ts` — updated to
  the new shape (vi: "Thêm đường dẫn"/"Nội dung"/"URL"/"Lưu"; en: "Add
  link"/"Text"/"URL"/"Save"), plus the four `LinkFieldError` strings in each
  locale.
- `app/kudos/new/_components/compose-form.tsx` — untouched; its prior
  typecheck error resolved once the controller supplied `linkDialogInitialText`.

No new sibling file was needed — every owned file stayed under 200 lines.

## Design evidence

All visual values came from `plans/260911-1007-addlink-box/design/momorph-node-values.md`
(this session's own `get_node` reads, prompt-supplied). Every value in
`link-dialog.tsx` carries an `mm:` node-ID comment citing that file. Nodes
used: `1002:12682` (panel), `1002:12500` (title), `1002:12501`/`1002:12502`/
`1002:12503` (text row/label/input), `1002:12652`/`1002:12653`/`1002:12654`
(URL row/label/input), `1002:12543`/`1002:12544`/`1002:12545` (button row,
Hủy, Lưu), `1002:12544;186:2761` (close icon slot), `1002:12545;186:1766`
(link icon slot, reused from `IconLink`).

`get_media_file(fileKey, "186:2761")` was attempted live this session to
fetch the real `MM_MEDIA_Close` SVG and returned `401 Unauthorized` — recorded
in the file's doc comment. Fell back to a hand-drawn Material "close" glyph,
same precedent as `IconExpand`/`IconPanZoom` in `kudos-icons.tsx`.

## Unauthored values (flagged in code)

- Error message copy and styling (`#CF1322`, small text under the field) —
  the frame carries no error state.
- The close-icon SVG path (see above).
- The dimmed overlay (`fixed inset-0 bg-black/40`) — unchanged from before,
  the frame is the panel alone.

## A note on the "unmounts when closed" property

The previous file's doc comment claimed the dialog "unmounts entirely while
closed" purely from `if (!open) return null`, which is not true by itself —
the parent renders `<LinkDialog .../>` unconditionally, so returning `null`
does not reset hook state on its own. Rather than reach for a
`setState`-in-`useEffect` reset (which `react-hooks/set-state-in-effect`
correctly flagged as a lint error), `kudos-body-editor.tsx` now keys the
element on `linkDialogOpen ? "open" : "closed"`, forcing a genuine remount
every time the dialog opens — `text`/`url`/both error slots are seeded once
via lazy `useState` initializers with no effect involved. This actually
delivers the property the old comment only asserted.

## Checks

- `npx tsc --noEmit` — exit 0, tree-wide (confirmed both call-site errors
  phase 02 left, at `compose-form.tsx:130` and `kudos-body-editor.tsx:147`,
  are gone).
- `npm run lint` — 0 errors, 31 pre-existing warnings in files outside this
  phase's ownership (e2e fixtures/specs, unrelated `.spec.ts` files).
- Did not run the e2e suite per task instructions (phase 04/tester owns
  GREEN + visual evidence).

## Unresolved / handed to tester

- None from this phase's own scope. The one open item is environmental: the
  `get_media_file` 401 above means the `Hủy` close icon is a faithful
  hand-drawn stand-in, not the traced MoMorph export — worth a follow-up if
  MCP media access is restored.
