# Phase 06 — `kudosCompose` i18n namespace

**Status:** DONE. Copy-only. Track B/app/e2e untouched.

## Shape decisions (deviations from phase-06.md's sketch, and why)

- `errors` is keyed by `ComposeFieldErrorCode` (`required | tooMany | invalidType | unknown`,
  imported type-only from the FROZEN `lib/kudos/compose-contract.ts`), not the spec sketch's
  `hashtagMax`/`imageType`. This lines up 1:1 with `ComposeFieldProps.copy` and
  `ComposeFormCopy.fieldErrors` (both `Record<ComposeFieldErrorCode, string>`), so phases 08-11
  can pass `dictionary.kudosCompose.errors` straight through with no remapping.
- Dropped `labels.anonymous` and `linkDialog.cancel` from the sketch — both would have duplicated
  an existing literal (`Gửi lời cám ơn và ghi nhận ẩn danh` / `Hủy`) under a second key, which
  violates the phase's own "no VN string under two keys" success criterion. The anonymous
  checkbox's one rendered string lives at `anonymousCheckboxLabel`; the link dialog's cancel
  button is meant to reuse `buttons.cancel` (noted in a doc comment there).
- `compose-contract.ts`'s `TitleFieldCopy`/`BodyEditorProps` have no slot for field *labels* or
  toolbar/link-dialog copy at all — see Unresolved below.

## Keys added (vi / en)

| Key | vi | en |
|---|---|---|
| `title` | Gửi lời cám ơn và ghi nhận đến đồng đội | Send thanks and recognition to a teammate |
| `labels.recipient` | Người nhận | Recipient |
| `labels.title` | Danh hiệu | Title |
| `labels.body`* | Nội dung | Message |
| `labels.hashtag` | Hashtag | Hashtag |
| `labels.image` | Image | Image |
| `placeholders.recipient` | Tìm kiếm | Search |
| `placeholders.title` | Dành tặng một danh hiệu cho đồng đội | Give your teammate a title |
| `placeholders.body` | Hãy gửi gắm lời cám ơn và ghi nhận đến đồng đội tại đây nhé! | Share your thanks and recognition with your teammate here! |
| `placeholders.anonymousName`* | Nhập tên bạn muốn hiển thị | Enter the name you'd like to show |
| `hints.titleLine1` | Ví dụ: Người truyền động lực cho tôi. | Example: The person who motivates me. |
| `hints.titleLine2` | Danh hiệu sẽ hiển thị làm tiêu đề Kudos của bạn. | This title will appear as your Kudos headline. |
| `hints.body` | Bạn có thể "@ + tên" để nhắc tới đồng nghiệp khác (straight quotes, fixture-exact) | You can use "@ + name" to mention a colleague |
| `buttons.addHashtag` | + Hashtag | + Hashtag |
| `buttons.addImage` | + Image | + Image |
| `buttons.max` | Tối đa 5 | Max 5 |
| `buttons.cancel` | Hủy | Cancel |
| `buttons.submit` | Gửi | Send |
| `toolbar.bold`* | Đậm | Bold |
| `toolbar.italic`* | Nghiêng | Italic |
| `toolbar.strike`* | Gạch ngang | Strikethrough |
| `toolbar.orderedList`* | Danh sách đánh số | Ordered list |
| `toolbar.link`* | Liên kết | Link |
| `toolbar.quote`* | Trích dẫn | Quote |
| `linkDialog.heading`* | Chèn liên kết | Insert link |
| `linkDialog.urlLabel`* | URL | URL |
| `linkDialog.confirm`* | Chèn | Insert |
| `errors.required` | Không được để trống | This field is required |
| `errors.tooMany` | Tối đa 5 hashtag | Maximum 5 hashtags |
| `errors.invalidType`** | Định dạng file không được hỗ trợ | This file format isn't supported |
| `errors.unknown`* | Đã có lỗi xảy ra. Vui lòng thử lại. | Something went wrong. Please try again. |
| `recipientEmpty`* | Không tìm thấy người phù hợp. | No matching people found. |
| `communityStandards`** | Tiêu chuẩn cộng đồng | Community standards |
| `anonymousCheckboxLabel` | Gửi lời cám ơn và ghi nhận ẩn danh | Send this Kudos anonymously |
| `anonymousNameLabel`* | Tên hiển thị ẩn danh | Anonymous display name |
| `submitPending`* | Đang gửi... | Sending... |
| `anonymousFallbackName`* | Người ẩn danh | Anonymous |

`*` = unauthored, faithful inference, no design/spec source. `**` = unauthored per
test-contract.md ratification item 6 (ships anyway, contract-bound).

## Verification

- `npm run typecheck` → **0 errors** repo-wide.
- **Gate proof:** commented out `en-kudos-compose.ts`'s `submitPending` line, reran typecheck →
  `TS2741: Property 'submitPending' is missing in type ... required in type ...` at
  `en-kudos-compose.ts(12,14)`. Restored the line, reran → 0 errors again. The dual-locale gate is
  real, not assumed.
- `npm run lint` → 0 errors; 28 pre-existing warnings, all in `e2e/**` (tester-owned), none in
  files I touched.
- Step-6 mechanical check: all 17 fixture-critical strings (page h1, all placeholders, both title
  hints, body hint w/ straight quotes, checkbox label, Hashtag/Tối đa 5/Tối đa 5 hashtag, Image,
  Không được để trống, Tiêu chuẩn cộng đồng, Hủy, Gửi, Định dạng file không được hỗ trợ) found
  verbatim in `vi-kudos-compose.ts`.
- `grep -rn "High-perorming\|BE PROFESSIONAL" lib/i18n/` → clean, no mock hashtag names leaked.
- Duplicate-literal scan across `vi-kudos-compose.ts`'s 37 string values → no duplicates.
- File sizes: `vi-kudos-compose.ts` 82 lines, `en-kudos-compose.ts` 64 lines — both ≤200.

## Files changed

- `lib/i18n/messages/dictionary.ts` — added `kudosCompose` interface + type-only import of
  `ComposeFieldErrorCode` from `lib/kudos/compose-contract.ts` (read-only reference, not edited).
- `lib/i18n/messages/vi-kudos-compose.ts` (new)
- `lib/i18n/messages/en-kudos-compose.ts` (new)
- `lib/i18n/messages/vi.ts`, `lib/i18n/messages/en.ts` — wired `kudosCompose` in.

Nothing imports `kudosCompose` yet, so `npx playwright test e2e/viet-kudo.spec.ts
e2e/route-guard.spec.ts` stays RED as expected (untouched, unrun by me — `e2e/**` is tester-owned).

## Unresolved questions

1. `compose-contract.ts`'s `TitleFieldCopy` (`{ placeholder, hintExample, hintUsage }`) has no
   slot for the field's own visible label ("Danh hiệu"), and `BodyEditorProps` has no `copy` slot
   at all for toolbar aria-labels or link-dialog copy. Phases 08-11 will need to either read
   `dictionary.kudosCompose.{labels,toolbar,linkDialog}` directly (bypassing those narrow Copy
   types) or escalate an amendment to the frozen contract per its own stated process ("A missing
   field is escalated to the orchestrator, who amends this once"). Flagging now so it isn't
   discovered mid-phase-08.
2. `labels.body` ("Nội dung") is my own inferred label — the frame's node tree has no separate
   label text for the message field (design-source-analysis.md § 1 confirms only placeholder +
   hint exist). If a design refresh adds one, this key should absorb it verbatim.
3. Toolbar aria-labels (`toolbar.*`) are adapted from clarifications.md's abbreviated Vietnamese
   toolbar names ("in đậm", "in nghiêng", "chèn liên kết", "trích dẫn") — "strike"/"thẻ số" had no
   given Vietnamese equivalent, so `Gạch ngang`/`Danh sách đánh số` are my own faithful choices.
