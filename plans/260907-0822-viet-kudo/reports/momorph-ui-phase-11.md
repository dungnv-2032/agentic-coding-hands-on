# Phase 11 report — compose form assembly

**Status:** implemented, not yet mounted (phase 12 wires `page.tsx`). Typecheck 0 errors
repo-wide, lint 0 problems in my files, `compose-form.tsx` exactly 200 lines (the hard cap),
others well under.

## Files

- `app/kudos/new/_components/compose-form.tsx` (200 ln) — the single client boundary: owns
  `useReducer(composeReducer, …)` + `useActionState(createKudos, …)`, renders the card and every
  field in DOM order, computes `isSubmitReady`, submits via `handleSubmit`.
- `app/kudos/new/_components/compose-actions.tsx` (53 ln) — the footer (`compose-cancel`,
  `compose-submit`), never `disabled`/`aria-disabled`.
- `app/kudos/new/_components/compose-form-helpers.tsx` (41 ln) — `mergeErrors` (client-precedence)
  and `FieldRow` (label-left/field-right, matches the frame's measured two-column rows), split out
  purely to keep `compose-form.tsx` at the 200-line cap.
- `app/kudos/new/_components/use-body-editor-controller.ts` (121 ln) — the body editor's
  selection-dependent wiring (mention detection, active-mark computation, link-dialog state) that
  phase 09 flagged as unresolved. Reads the live textarea's DOM selection at the moment a toolbar
  button fires, per phase 09's own recommendation; reuses `isMarkActive` (`rich-text.ts`, frozen).

All four new — no existing owned files from phases 08/09/10 touched (`git status` confirms only
`app/kudos/new/_components/` additions).

## Re-measured live (MCP), not trusted from the report

`get_node(520:11647)` → `752×1012px`, padding 40, gap 32, radius 24, `#FFF8E1` — confirmed exactly.
`get_overview` confirmed the live field order (title → recipient → Danh hiệu → Content(body+
hashtag+image, gap 24) → anonymous → footer) and that the recipient/hashtag/image label nodes sit
visually left of their field (measured X ranges), which is why `FieldRow` renders label-then-field.
Footer row confirmed `gap:24px`, `flex-start` (not `space-between`) — Hủy hug-content + 24px + Gửi
502px = 672px, matching the card's inner width exactly. `get_figma_image`/`get_media_file` were not
needed (no new assets); not attempted, so no 401/500 to report.

## Deviations from `compose-contract.ts`'s `ComposeFormProps` sketch (advisory, not binding — Wave-2 ruling #2)

1. **`copy: Dictionary["kudosCompose"]`**, not the frozen `ComposeFormCopy`. Every field this
   component composes (labels, placeholders, hints, buttons, toolbar, linkDialog, errors,
   recipientEmpty, communityStandards, anonymous*, submitPending) is needed by one child or
   another — using the whole resolved namespace is the honest "slice" here, not a workaround.
2. **No `isSubmitReady: boolean` prop** — the frozen sketch has `page.tsx` compute it, but only
   this component holds `ComposeState`; `isSubmitReady(state)` is computed internally instead.
3. **No `cancelHref: string` prop** — hardcoded `"/kudos"` locally (`CANCEL_HREF`), same treatment
   as `community-standards-link`'s `/standards` in `kudos-body-editor.tsx` (Key Insight 10).

## Submit ordering (Insight 3) and `data-submit-ready`

`handleSubmit` is an async `<form action>` handler. If any `state.images[].imageUrl === null` at
click time, it sets `awaitingUploads` (drives `ComposeActions`' `pending` label) and polls a
`stateRef` mirror of `state` every 50ms until every image resolves (or is removed by `ImagePicker`'s
own failure path) before building the payload — never silently drops an in-flight attachment.
`stateRef` is mirrored via a ref-only `useEffect` (not a `setState`-in-effect), required to satisfy
`react-hooks/set-state-in-effect`, which rejected the first draft's reactive-effect-plus-boolean
approach. `compose-submit` carries no `disabled`/`aria-disabled` anywhere (`grep -n "disabled"
compose-actions.tsx` → doc-comment only); `data-submit-ready` reflects `isSubmitReady(state)`
continuously, with `opacity-50` styling the not-ready state without ever making it inert.

## What `page.tsx` (phase 12) must pass

```tsx
<ComposeForm
  copy={dictionary.kudosCompose}
  options={await getComposeOptions()}
  createKudos={createKudos}          // app/kudos/new/_actions/create-kudos.ts, no adapter
  uploadKudosImage={uploadKudosImage} // app/kudos/new/_actions/upload-kudos-image.ts, no adapter
/>
```
Wrapped inside the standard `HomeHeader`/`SiteFooter` chrome exactly as `/kudos`'s `page.tsx` does
(`<main className="flex flex-1 flex-col">` is enough — `ComposeForm` supplies its own centering
wrapper). Nothing else: no `cancelHref`, no `isSubmitReady` — both are internal now (see above).

## Checks

- `npm run typecheck` — 0 errors, exit 0. `npm run lint` — 0 errors repo-wide (28 pre-existing
  warnings elsewhere, none in my files), exit 0.
- `grep -n "disabled" compose-actions.tsx` → doc-comment only. `grep -c "useReducer\|useActionState"
  compose-form.tsx` → 2. `grep -n "composeReducer\|isSubmitReady\|buildPayload\|validateCompose"
  compose-form.tsx` → calls only, no redefinitions.
- Not mounted (phase 12's job) — suite stays RED as expected; not rerun by me (page still points
  at `ComingSoon`).

## Unresolved

1. Selection-tracking (`document.addEventListener("selectionchange", …)`) and the 50ms upload-wait
   poll in `use-body-editor-controller.ts`/`compose-form.tsx` are reasonable, self-contained choices
   but untested by any assertion (ID-27/28/29 only check the attribute exists) — flagging for
   phase 12/tester's real-browser pass in case either fights native selection/timing.
2. `FieldRow`'s label width is shrink-to-content, not pixel-matched per field (recipient measures
   146px, Danh hiệu 139px) — the frame doesn't appear to enforce one shared column width. Flagging
   for the visual pass rather than guessing a shared constant.
