# Phase 10 — Hashtag & image pickers

**Track:** A (presentational UI) · **Owner:** `momorph-ui-implementer` · **Depends:** 01, 06 ·
**Effort:** 2.5h · **test_policy:** `e2e-red-first`

## MoMorph refs:
- Viết Kudo: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/ihQ26W78P2
- Dropdown list hashtag (companion, authored spec): https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/p9zO-c4a4x
- Clarifications: plans/260907-0822-viet-kudo/clarifications.md
- testPolicy: e2e-red-first

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (caps, reducer semantics) · [phase-06](phase-06-i18n-kudos-compose-namespace.md) · [phase-07](phase-07-write-path-validation-and-actions.md) (`isAcceptedImageType`, `UploadKudosImage`)
- [test-contract.md](test-contract.md) § Hashtags, § Images
- Tests this phase must satisfy: ID-15, ID-16, ID-17, ID-18, ID-19, ID-20, ID-21, ID-22, ID-23, ID-24, ID-34, ID-35, ID-36, ID-37, ID-38, ID-39, ID-40, ID-53, ID-54, ID-55
- [clarifications.md](clarifications.md) § Validation (max 5 hashtags, the sixth **refused with an error**), § Images (max 5, the add button **hidden** at 5 — hidden, not disabled; real files, real Storage)
- [design/specs-p9zO-c4a4x.csv](design/specs-p9zO-c4a4x.csv) — the companion frame's own spec, which **conflicts with ID-17**; see § Key Insights 2
- [design-source-analysis.md](reports/design-source-analysis.md) § 5 (`F.5`: "Nếu đã 5 ảnh: ẩn"), § 8 (thumbs 80×80 with a 20×20 close button; `+ Hashtag` 48px tall, border `#998C5F`, radius 8px)

## Overview

**Priority:** P1 · **Status:** completed.

Two pickers, twenty tests — the highest test density in the commission, and the two places where the
authored design and the authored test cases disagree. Both disagreements are resolved here in favour
of the test cases, with the design's visual intent preserved where it can be.

## Key Insights

1. **The two caps behave differently on purpose.** Hashtags: the add button **stays visible** and the
   sixth is refused with `Tối đa 5 hashtag` (ID-17, ID-53). Images: the add button is **hidden
   entirely** at five (ID-19, ID-20, ID-38, ID-54) and returns when one is removed (ID-40). Hidden,
   not disabled — `not.toBeVisible()` is the assertion, and a `disabled` button is still visible.
2. **CONFLICT — the hashtag menu must NOT disable its options at the limit, and it must NOT toggle.**
   The companion frame's own spec says *"khi tổng số lựa chọn đạt 5 thì các nhãn chưa chọn bị
   disable"* and describes each row as a click-to-toggle. But ID-17/ID-53 add the five tags, then
   click `hashtagOptions.first()` — which is an **already-selected** row — and expect the error plus
   *still five chips*. Under toggle semantics that click would deselect and leave four. Under
   `disabled` semantics Playwright's click would never fire, because click actionability waits for
   the `enabled` state. So: options are **add-only**, never `disabled`, and any click at the limit
   surfaces the error and changes nothing. The design's visual intent survives — dim the
   already-selected and, at the limit, the unselected rows — but they stay clickable. Ruling recorded;
   the test cases win, as clarifications' precedence rule requires.
3. **The hashtag menu closes on every selection.** ID-16 loops five times, each iteration clicking
   `hashtag-add` and then awaiting `hashtag-menu` to be visible. If the menu stayed open, the second
   click on the add button would toggle it shut and the `toBeVisible()` wait would fail. Close on
   select, reopen on the next add click.
4. **`hashtag-error` lives outside the menu**, in the field row, so it survives the menu closing.
5. **Five copies of the same file are five images.** ID-18/19/20/54 call
   `imageInput.setInputFiles("./e2e/fixtures/test-image.jpg")` in a loop with the identical path and
   expect the thumb count to climb to 3 and 5. Therefore: the change handler **appends** and never
   dedupes (by name, size or hash), and it resets `input.value = ""` after reading the files so
   selecting the same file again fires a fresh `change`.
6. **`image-input` must stay mounted even when `image-add` is hidden.** ID-46/47 calls
   `setInputFiles` without first waiting for the add button, and at five images the button is gone.
   Keep the `<input type="file">` outside the conditional — always in the DOM, always visually
   hidden. `setInputFiles` does not require visibility.
7. **The thumbnail shows the real picked file immediately, then the real Storage URL.** A blob URL
   (`URL.createObjectURL`) gives an instant, honest preview (ID-37 wants *that file*); the upload
   resolves and the thumb's `src` becomes the returned public URL, which is what gets submitted.
   Failure removes the optimistic thumb and shows `image-error`. Revoke each object URL on removal
   and unmount.
8. **The blob preview uses a plain `<img>`, not `next/image`.** `next/image` cannot optimize a
   `blob:` URL. Use `<img>` with a targeted `eslint-disable-next-line @next/next/no-img-element` and
   a comment naming the reason — the board's own thumbnails still go through `next/image`
   (`kudos-attachments.tsx`, untouched).
9. **The type check runs client-side first, and it is the same function the server uses.** Import
   `isAcceptedImageType` from `lib/kudos/validate-compose.ts` (phase 07). A rejected file must produce
   `image-error` and **no thumbnail at all** (ID-23/24/55 assert `toHaveCount(0)`), which means the
   check happens before the optimistic thumb is created.
10. **In-flight uploads must be awaited at submit.** ID-46/47 clicks submit immediately after
    `setInputFiles`. This picker therefore exposes its pending uploads to phase 11 through the
    reducer (an image entry is `{ id, previewUrl, url: null }` until it resolves), and phase 11's
    submit awaits them. Silently submitting without the attachment would pass the test and drop the
    user's file — the dishonest outcome the project rules forbid.
11. **Hashtag options are data with a `#` prefix.** The 13 seeded names arrive as props; the option
    renders `#{name}`. The tests locate by substring (`text=Toàn diện`), so the prefix is safe, and
    the frame's own `#High-perorming` mock names are never used.

## Requirements

**Functional:** FR-205 (hashtags, BR-002's max half), FR-206 (images, BR-003, BR-004's client half),
ID-15–24, ID-34–40, ID-53–55.

**Non-functional:** each file ≤200 lines; `"use client"`; `mm:{nodeId}` on arbitrary Tailwind values;
copy via the `copy` prop; object URLs revoked; no duplicate type-check logic.

## Architecture

```
app/kudos/new/_components/hashtag-picker.tsx        (~135 lines, "use client")
  props: HashtagPickerProps { options, selected, error, fieldError, copy, onAdd, onRemove }
  ├─ button data-testid="hashtag-add" type="button"
  │         label = `${copy.buttons.addHashtag} ${copy.buttons.max}`  → contains "Hashtag" + "Tối đa 5"
  │         ALWAYS visible, even at 5                       mm:I520:11647;662:8911
  ├─ menu   data-testid="hashtag-menu" role="listbox"  (open/close local state)
  │         <li role="option" data-selected> #{name} </li>  — add-only, never `disabled`
  │         click → onAdd(id); menu closes  (reducer refuses the 6th and sets the error)
  ├─ chips  data-testid="hashtag-chip" ×n, each with data-testid="hashtag-chip-remove"
  └─ error  data-testid="hashtag-error" {copy.errors.hashtagMax}   ← outside the menu

app/kudos/new/_components/image-picker.tsx          (~150 lines, "use client")
  props: ImagePickerProps { images, error, copy, uploadImage: UploadKudosImage,
                            onAdd, onResolve, onRemove, onError }
  ├─ input  data-testid="image-input" type="file" accept="image/*" multiple
  │         ALWAYS mounted, visually hidden, value reset after each change
  ├─ button data-testid="image-add" type="button" → input.click()
  │         label contains "Image" + "Tối đa 5"; rendered only while images.length < 5
  ├─ thumbs data-testid="image-thumb" ×n (80×80, mm:I520:11647;662:9197)
  │         <img src={url ?? previewUrl}>  + data-testid="image-thumb-remove" (20×20, mm:…;662:9287)
  └─ error  data-testid="image-error" {copy.errors.imageType}

  onChange(files):
    for each file → isAcceptedImageType(file.type)
      ? onAdd({ id, previewUrl: URL.createObjectURL(file) })
        then uploadImage(fd) → "url" in r ? onResolve(id, r.url) : (onRemove(id), onError())
      : onError()            ← no thumb created (ID-23/24/55)
    finally input.value = ""
```

## Related Code Files

**Create:** `app/kudos/new/_components/hashtag-picker.tsx` · `app/kudos/new/_components/image-picker.tsx`
**Modify:** none · **Delete:** none
**Read only:** `lib/kudos/compose-contract.ts`, `lib/kudos/validate-compose.ts`,
`app/kudos/_components/kudos-hashtag-row.tsx` (shipped chip styling), `app/_components/use-dismiss-on-outside.ts`

## Implementation Steps

1. `hashtag-picker.tsx`. Markup and testids, then the add-only click rule, then close-on-select, then
   the chips and their individual remove buttons. Chip visual style follows the shipped
   `kudos-hashtag-row.tsx` rather than a new invention.
2. Verify ID-36's semantics precisely: removing one chip leaves the others **and their order**
   intact. The reducer filters by id (phase 01) — do not remove by index.
3. `image-picker.tsx`. Order: the always-mounted hidden input, then the conditional add button, then
   the change handler's reject-before-preview sequence, then the upload plumbing, then removal with
   `URL.revokeObjectURL`.
4. Add the single targeted eslint-disable for the `<img>`, with the blob-URL reason in a comment.
5. `npm run typecheck && npm run lint`. Confirm the disable is the **only** one in the diff.
6. Props-contract read-through against `compose-contract.ts`, as in phases 08 and 09.
7. Sanity-check the fixtures this phase's tests depend on:
   `ls -l e2e/fixtures/test-image.jpg e2e/fixtures/test-image.png e2e/fixtures/test-file.pdf
   e2e/fixtures/test-video.mp4 e2e/fixtures/test-file.txt` — all five must exist and be non-empty.
   Then confirm `file --mime-type` reports `image/jpeg` and `image/png` for the first two, because a
   1×1 file the browser reports as something else would fail ID-21/22 for a reason that has nothing
   to do with this code.

## Todo List

- [x] `hashtag-add` always visible, label contains both "Hashtag" and "Tối đa 5"
- [x] Menu options add-only, never `disabled`, dimmed for visual parity with the frame
- [x] Menu closes on every selection (ID-16's loop depends on it)
- [x] Sixth attempt shows `Tối đa 5 hashtag` outside the menu and leaves five chips (ID-17/53)
- [x] Chips removable individually, by id not index (ID-36)
- [x] `image-input` always mounted and hidden; `value` reset after each change
- [x] `image-add` rendered only below 5, so it is genuinely not visible at 5 (ID-19/20/38/54)
- [x] Add button returns after a removal (ID-40)
- [x] Same file five times gives five thumbs — no dedupe anywhere (ID-18/19)
- [x] Rejected type shows `image-error` and creates **no** thumb (ID-23/24/55)
- [x] Type check imported from `validate-compose.ts`, not reimplemented
- [x] Thumb shows the blob preview then the Storage URL; object URLs revoked
- [x] Exactly one eslint-disable in the diff, with its reason
- [x] Each file ≤200 lines; `npm run typecheck && npm run lint` clean
- [x] Step 7 fixtures confirmed present with the right MIME types

## Success Criteria

- Props match `compose-contract.ts` exactly.
- Each of `hashtag-add`, `hashtag-menu`, `hashtag-error`, `image-input`, `image-error` appears exactly
  once per render; `hashtag-chip`, `hashtag-chip-remove`, `image-thumb`, `image-thumb-remove` once per
  item.
- `grep -n "disabled" app/kudos/new/_components/hashtag-picker.tsx` shows no `disabled` on an option.
- `grep -rn "isAcceptedImageType" app/kudos/new/_components/image-picker.tsx` shows an import, not a
  definition.
- `grep -c "eslint-disable" app/kudos/new/_components/image-picker.tsx` returns 1.
- `grep -n "revokeObjectURL" app/kudos/new/_components/image-picker.tsx` returns at least one hit.
- The five fixtures exist and the two images report image MIME types.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Hashtag options rendered `disabled` at the limit, so ID-17/53's click times out | **High** × High | Ruling in § Key Insights 2, restated in the todo list, greppable in the success criteria |
| Toggle semantics deselect on ID-17's click, leaving four chips | **High** × High | Add-only click handler; the reducer is the only place a cap is enforced |
| The menu stays open and ID-16's second add-click closes it, failing the visibility wait | Med × High | Close-on-select, called out in insight 3 |
| Files deduped by name, so five identical picks give one thumb | **High** × High | Explicit no-dedupe rule in phase 01's reducer and here; ID-18/19 exercise it |
| `input.value` not reset, so picking the same file twice fires no `change` | **High** × High | Reset in a `finally`; the same tests catch it |
| `image-add` disabled instead of unmounted | Med × High | `not.toBeVisible()` is the assertion; conditional render, not a `disabled` attribute |
| `image-input` unmounted with the add button, so ID-46/47's `setInputFiles` finds nothing | Med × High | Input lives outside the conditional, stated in insight 6 |
| Submit fires before uploads resolve and the attachment is silently dropped | Med × **High** | Images carry `url: null` until resolved; phase 11 awaits them. Called out in insight 10 as a correctness, not a test, requirement |
| A leaked object URL per removed thumb | Med × Low | `revokeObjectURL` on removal and on unmount; greppable |
| A 1×1 fixture whose MIME the browser reports oddly fails ID-21/22 | Low × High | Step 7 checks the real MIME before any debugging starts |

**Rollback:** delete the two files. Nothing imports them until phase 11.

## Security Considerations

- The client-side type check is a convenience for the immediate error; the authority is the upload
  action's own MIME check and the Storage policy (phase 07/03). Both layers exist by design, and this
  one is never the boundary.
- The file's name is never used to build the stored path — the action derives the extension from the
  validated MIME, so `x.png.html` cannot influence anything.
- Blob URLs are same-origin, ephemeral and revoked; they never reach the server or the database.
- Only URLs returned by our own upload action enter the payload, and the action re-checks their
  origin before writing `kudos_attachments`.
- Hashtag ids travel as numbers and are re-checked server-side against the `hashtags` table.

## Next Steps

Phase 11 composes this with 08's and 10's output and owns the await-pending-uploads rule at submit.
Report the § Key Insights 2 ruling to the orchestrator so it lands in the promote-time spec refresh
alongside the companion frame's stale prose.
