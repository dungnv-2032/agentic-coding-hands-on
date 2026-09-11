# Clarifications — Dropdown list hashtag (MoMorph `p9zO-c4a4x`)

**MoMorph refs**
- Dropdown list hashtag: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/p9zO-c4a4x
- Parent screen: SCR005 Viết Kudo (`/kudos/new`), feature F005
- specs: 10 design items (A, A.1, A.2, B, B.1, B.2, C, C.1, C.2, D) — `spec_status: done`
- test cases: none published for this frame (0 rows)
- testPolicy: `e2e-red-first`

**Standing authority.** User granted auto-resolution: "nếu có vấn đề gì cần confirm với tôi,
tự động triển khai theo hướng câu trả lời đầu tiên, Yes hoặc câu trả lời Recommend mà ko cần
confirm tôi." Every decision below is therefore taken on the Recommended option without a
blocking question.

## Session 2026-09-11

- Q: The frame is a companion dropdown, not a standalone route. Where does it live? → A: **It is
  the open state of the existing `+ Hashtag` menu in `app/kudos/new/_components/hashtag-picker.tsx`
  (F005/SCR005).** Rationale: `mm:1002:13102` is already cited in that component's header as the
  companion `Dropdown-List`; no new route, no new `F###` reservation — this is an F005 amendment,
  keeping feature-code contiguity clean.

- Q: The frame spec says a row **toggles** select/deselect (items A, B, C, D `userAction`), but the
  shipped component is add-only and e2e ID-17/ID-53 click the *first* option at the cap and expect
  the "Tối đa 5 hashtag" error with the chip count unchanged. `TEST_HASHTAG_1 = "Toàn diện"` is DB
  position 1, so at the cap `options.first()` is an already-selected row — toggle would deselect it
  and drop the count to 4. Which contract wins? → A: **The MoMorph frame wins on interaction
  (toggle in, toggle out); ID-17/ID-53 are re-pointed at an unselected row, which is what "the 6th
  hashtag" actually means.** Rationale: `momorph-development.md` rule 1 makes MCP design data
  authoritative, and the re-point strengthens the tests rather than weakening them — the cap is
  still asserted, just against the row the cap actually governs.

- Q: The frame says that at 5 selected the unselected rows are disabled and do not respond to click
  (item D `validationNote`), while BR-002 in `docs/features/F005_VietKudo/functional-spec.md` says a
  6th attempt is refused *with the message* "Tối đa 5 hashtag". A disabled button fires no click, so
  the message would never appear. → A: **Do both — at the cap the unselected rows are `disabled`
  and dimmed, and `hashtag-error` renders "Tối đa 5 hashtag" as the standing reason.** Rationale:
  the message becomes the explanation for the disabled state instead of the reaction to a refused
  click; BR-002 and the frame are both satisfied and no user is left guessing why rows went inert.

- Q: Does the menu stay open after a row is toggled? → A: **No — it keeps the shipped close-on-select
  behaviour.** Rationale: the frame spec is silent on open/close, so there is nothing to violate;
  ID-16 reopens the menu via `hashtag-add` on every round and would fail if a second trigger click
  merely toggled an already-open menu shut.

- Q: Are selected rows hoisted to the top of the list, as the frame image shows? → A: **No — DB
  `position` order is preserved.** Rationale: item A.1 states the list is loaded dynamically from the
  database and says nothing about re-ordering; the image simply happens to have the first three rows
  selected. Re-sorting under the cursor would also move a row out from under a click.

- Q: The unselected check-icon slot — hide it or reserve the space? → A: **Reserve a 24×24 slot.**
  Verbatim from item A.2: "khoảng trống 24x24px (không có icon) khi unselected", so rows never
  reflow as selection changes.

- Q: Data source for the option list? → A: **Local Supabase `public.hashtags`, already fetched by
  `getComposeOptions()` (`lib/kudos/compose-options.ts`) ordered by `position`.** Rationale: the user
  asked for the local Supabase project and the read path already exists — no new query, no invented
  data. The frame's own labels (`#High-perorming`, `#BE PROFESSIONAL`, …) are Figma mock content and
  are NOT seeded over the real 13 rows.

## Unresolved

- None. Every gap above was resolved under the standing authority.
