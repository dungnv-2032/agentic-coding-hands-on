# Phase 10 report — hashtag & image pickers

**Files:** `app/kudos/new/_components/hashtag-picker.tsx` (153 lines) ·
`app/kudos/new/_components/image-picker.tsx` (193 lines)

## Contract deviation — read before wiring phase 11 (compose-form.tsx)

`lib/kudos/compose-contract.ts`'s `HashtagPickerProps`/`ImagePickerProps` sketches don't
support what test-contract.md + phase-10.md's Key Insights require, so I typed my own
Props/Copy locally in each file (exported) rather than importing the frozen ones —
consistent with the ratification's "each phase types its own copy slice." Reusing only the
frozen **data** types (`ComposeHashtagOption`, `ComposeAttachedImage`, `ComposeFieldErrorCode`,
`UploadKudosImage`, `MAX_HASHTAGS`, `MAX_IMAGES`).

- **`HashtagPickerCopy`**: `{ addLabel: string; maxError: string }` — the frozen version has
  only `addLabel`, no slot for "Tối đa 5 hashtag" (`errors.tooMany`), unlike `ImagePickerCopy`
  which already carries `invalidTypeError`. Exported `buildHashtagPickerCopy(copy)` composes
  it from `Dictionary["kudosCompose"].buttons`/`.errors`.
- **`ImagePickerProps`**: `{ copy, images, error, uploadImage, onAdd, onResolve, onRemove,
  onError }` instead of the frozen `{ copy, images, error, onFilesSelected, onRemove }`. The
  frozen shape can't express phase-10's optimistic-preview / await-pending-upload flow (Key
  Insights 7, 9, 10): the reducer's `imageUrl: null` IS the "still uploading" signal phase 11
  needs at submit, and only the picker — which sees the raw `File` — can create the blob
  preview and call `uploadImage`. Exported `buildImagePickerCopy(copy)` mirrors the hashtag
  helper.

Both dictionaries already exist and match 1:1 (`lib/i18n/messages/{vi,en}-kudos-compose.ts`):
`buttons.addHashtag`/`addImage`/`max`, `errors.required`/`tooMany`/`invalidType`/`unknown`.

## Hooks / props / nodes

| Hook | Component | Notes |
|---|---|---|
| `hashtag-add` | button, always visible | `mm:I520:11647;662:8911` — 48px, border `#998C5F`, radius 8, bg white |
| `hashtag-menu` | `role="listbox"`, open on click, closes on every `onAdd` | `mm:1002:13102` (companion `p9zO-c4a4x`) — 318px, border `#998C5F`, bg `#00070C`, radius 8, pad 6 |
| option rows | `role="option"`, add-only, never `disabled` | `mm:1002:13185` selected (bg `rgba(255,234,158,.2)`) / `mm:1002:13104` unselected; dimmed via `opacity-50` when `selected.length >= MAX_HASHTAGS` (styling only — no design node for this exact state, inferred) |
| `hashtag-chip` / `hashtag-chip-remove` | text style matches shipped `kudos-hashtag-row.tsx` (`text-[#D4271D]`, `tracking-[0.5px]`) | removal filters by `id`, order preserved (ID-36) |
| `hashtag-error` | shown only when `error === "tooMany"` | `copy.maxError` |
| `image-add` | conditional on `images.length < MAX_IMAGES` (unmount, not `disabled`) | `mm:I520:11647;662:9133` — same button styling as hashtag-add |
| `image-input` | always mounted, `sr-only`, `value` reset in `handleChange` before async work | `accept="image/*" multiple` |
| `image-thumb` / `image-thumb-remove` | `mm:I520:11647;662:9197` (80×80, radius 18, border `#998C5F`) / `mm:I520:11647;662:9287` (20×20, full-round, `#D4271D`) |
| `image-error` | shown only when `error === "invalidType"` | `copy.invalidTypeError` |

`field-error-hashtag` is **not** rendered by `hashtag-picker.tsx` — phase-10.md's own Success
Criteria only requires `hashtag-add/menu/error` from this file; the required-field case
(`errors.hashtag`/"required") is the generic `ComposeField` wrapper's job (phase 08's
`compose-field.tsx`), sibling-wrapped around `<HashtagPicker>` in `compose-form.tsx`.

## Identical-file re-pick & the always-mounted input

`handleChange` reads `event.target.files` then resets `event.target.value = ""`
**synchronously**, before any `await`, so a same-path `setInputFiles` call always fires a
fresh native `change` event and the reset survives even if an upload hangs. `image-input` is
rendered unconditionally (outside the `images.length < MAX_IMAGES` branch that hides
`image-add`), so `setInputFiles` works whether or not the add button is visible.

Per-image blob preview is `useState<ReadonlyMap<string,string>>`, not a ref — `react-hooks/refs`
(eslint) forbids reading `.current` during render, so the map is state, mirrored into a ref
(updated via effect) purely for the unmount revoke sweep. `ComposeAttachedImage.imageUrl`
stays `null` (per the frozen type's own doc comment) until `onResolve` fires; the thumb's `src`
is `image.imageUrl ?? previewUrls.get(image.id)`.

## Checks

- `npm run typecheck` — **0** errors repo-wide.
- `npx eslint app/kudos/new/_components/{hashtag,image}-picker.tsx` — clean, 0 problems.
- `grep -n "disabled" hashtag-picker.tsx` — one hit, inside a doc comment explaining the
  no-`disabled` ruling; no `disabled` attribute anywhere in the file.
- `grep -c "eslint-disable" image-picker.tsx` → 1 (the `<img>` line only).
- `grep -n "revokeObjectURL" image-picker.tsx` → 2 hits (resolve/error/remove path + unmount).
- `grep -n "isAcceptedImageType" image-picker.tsx` → import + one call, not reimplemented.
- Fixtures: `test-image.jpg` (image/jpeg), `test-image.png` (image/png), `test-file.pdf`,
  `test-video.mp4`, `test-file.txt` all present and non-empty; `test-image-1..5.jpg/png` (used
  by ID-18/19) also present.
- Not mounted anywhere yet (phase 11/12's job) — `e2e/viet-kudo.spec.ts` and
  `route-guard.spec.ts` stay RED as expected; no browser/visual evidence owned by this task.

## Unresolved

1. **Contract deviation above** needs the orchestrator's ruling recorded in the promote-time
   spec refresh, same as § Key Insight 2's hashtag menu ruling.
2. Upload failure surfaces `onError("unknown")` (generic) rather than a dedicated code —
   `ComposeFieldErrorCode` has no "upload failed" variant distinct from `invalidType`; phase-10.md
   doesn't specify one either. `image-error` will render only for `invalidType`, so an upload
   failure currently shows no inline text unless phase 11 also renders `unknown` through the
   same slot — worth confirming with phase 11.
3. The "dim unselected rows at the cap" hashtag-menu styling has no measured design node (the
   companion frame's own disable-at-cap state was overridden per ratification item 5); I used
   `opacity-50` as a reasonable stand-in, not a measured value.
