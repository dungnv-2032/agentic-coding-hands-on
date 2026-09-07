# Phase 06 — i18n `kudosCompose` namespace

**Track:** A (presentational UI) · **Owner:** `momorph-ui-implementer` · **Depends:** 01 ·
**Effort:** 1h · **test_policy:** `e2e-red-first`

## MoMorph refs:
- Viết Kudo: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/ihQ26W78P2
- Dropdown list hashtag (companion): https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/p9zO-c4a4x
- Clarifications: plans/260907-0822-viet-kudo/clarifications.md
- testPolicy: e2e-red-first

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (error **codes** — this phase owns the strings they map to)
- [clarifications.md](clarifications.md) § Shared chrome and i18n (full VN + EN, a new namespace, compile-time enforced)
- [test-contract.md](test-contract.md) § Landmarks, § Fields, § Hashtags, § Images, § Anonymous, § Validation — **the copy source of record**
- [design-source-analysis.md](reports/design-source-analysis.md) § 1 (verbatim copy with node ids), § 9 (the only authored error strings)
- `e2e/fixtures/viet-kudo-constants.ts` — the exact strings the suite compares against
- Files to extend: `lib/i18n/messages/dictionary.ts:150-190` (the `kudos` namespace, as the shape to mirror), `lib/i18n/messages/vi.ts`, `en.ts`, and the `vi-kudos.ts`/`en-kudos.ts` split pattern

## Overview

**Priority:** P1 · **Status:** completed.

Every Vietnamese string the screen shows, in one namespace, in both locales, enforced by the
`Dictionary` interface. This is the smallest phase and the one most likely to fail the suite on a
single wrong character, so it is transcribed from the fixture file, not retyped from the design.

## Key Insights

1. **The e2e fixture file is the transcription source, not the design CSV.** `viet-kudo-constants.ts`
   is what the assertions compare against; the design PNG and CSV are one step further from the
   assertion. Copy-paste from the fixture, then confirm each string also appears in
   `design-source-analysis.md § 1`. Two strings will **not** appear there — see insight 3.
2. **A separate namespace, not an extension of `kudos`.** `kudosCompose` keeps the board's copy and
   the form's copy independently editable, which is what clarifications settled. It also means phase
   05's board work and this phase never touch the same dictionary sub-tree.
3. **Two strings in the contract have no design source, and they ship anyway.**
   `Tiêu chuẩn cộng đồng` (the `community-standards-link` label) and
   `Định dạng file không được hỗ trợ` (the image-type error) appear in `test-contract.md` and in the
   RED suite, but **not** in the 26-row spec CSV, not in the frame's TEXT nodes
   (`design-source-analysis.md § 1`) and not in the 57 test cases (§ 9 records that the file-rejection
   error was described behaviorally, never given as a literal). The test contract is authoritative for
   hooks and copy, so both ship — and both are recorded here as unauthored, needing a design/spec
   refresh. Do not "correct" them to something else; the suite compares them character for character.
4. **`Danh hiệu`'s error copy reuses the shared string.** Clarifications settled this explicitly: the
   field is required from the frame's `*` but has no authored error copy, so `field-error-title`
   shows the same `Không được để trống`.
5. **Error copy is keyed by code, not by field.** Phase 01's `ComposeFieldErrors` carries
   `"required" | "tooMany" | "invalidType" | "unknown"`. The dictionary holds one string per code plus
   the two cap-specific strings, so `Không được để trống` is written **once** and reused by four
   fields (DRY — four copies of the same literal is four places to typo it).
6. **EN is a faithful translation, not a placeholder.** `Dictionary` makes a missing key a typecheck
   failure, but it cannot catch `"TODO"`. The EN file is written properly the first time.
7. **The hashtag options are data, not copy.** `Toàn diện`, `Giỏi chuyên môn` etc. come from the
   `hashtags` table (13 seeded rows) and are the same in both locales. The companion frame's
   `#High-perorming` / `#BE PROFESSIONAL` names are the design's mock values and must **not** be
   transcribed — the frame's own spec says the list is "lấy dynamic từ database". Only the `#` prefix
   is presentation.

## Requirements

**Functional:** FR-601's i18n half — every visible string on `/kudos/new` resolves through the
dictionary in both locales. Copy matches `e2e/fixtures/viet-kudo-constants.ts` exactly for VN.

**Non-functional:** each locale file ≤200 lines (hence the separate `vi-kudos-compose.ts` /
`en-kudos-compose.ts` split, mirroring `vi-kudos.ts`); keys identical across locales, enforced by
`Dictionary`; no string duplicated across two keys.

## Architecture

```
lib/i18n/messages/dictionary.ts        + kudosCompose: {
  title            "Gửi lời cám ơn và ghi nhận đến đồng đội"          (the page's only <h1>)
  labels           { recipient, title, body, hashtag, image, anonymous }   Người nhận / Danh hiệu / …
  placeholders     { recipient "Tìm kiếm", title "Dành tặng một danh hiệu cho đồng đội",
                     body "Hãy gửi gắm lời cám ơn và ghi nhận đến đồng đội tại đây nhé!",
                     anonymousName }
  hints            { titleLine1 "Ví dụ: Người truyền động lực cho tôi.",
                     titleLine2 "Danh hiệu sẽ hiển thị làm tiêu đề Kudos của bạn.",
                     body "Bạn có thể “@ + tên” để nhắc tới đồng nghiệp khác" }
  buttons          { addHashtag "+ Hashtag", addImage "+ Image", max "Tối đa 5",
                     cancel "Hủy", submit "Gửi" }
  toolbar          { bold, italic, strike, orderedList, link, quote }      aria-labels
  linkDialog       { heading, urlLabel, confirm, cancel }
  errors           { required "Không được để trống", hashtagMax "Tối đa 5 hashtag",
                     imageType "Định dạng file không được hỗ trợ", unknown }
  recipientEmpty   (the `recipient-empty` text)
  communityStandards "Tiêu chuẩn cộng đồng"
}
lib/i18n/messages/vi-kudos-compose.ts  export const viKudosCompose: Dictionary["kudosCompose"]
lib/i18n/messages/en-kudos-compose.ts  export const enKudosCompose: Dictionary["kudosCompose"]
lib/i18n/messages/vi.ts / en.ts        + kudosCompose: viKudosCompose / enKudosCompose
```

**Note on the `“ ”` in the body hint:** `viet-kudo-constants.ts` writes it with straight quotes
(`'Bạn có thể "@ + tên" …'`) while the frame renders curly ones. The **fixture wins** — the assertion
is `toHaveText(BODY_HINT)`. Copy the fixture's exact characters.

## Related Code Files

**Create:** `lib/i18n/messages/vi-kudos-compose.ts` · `lib/i18n/messages/en-kudos-compose.ts`
**Modify:** `lib/i18n/messages/dictionary.ts` · `lib/i18n/messages/vi.ts` · `lib/i18n/messages/en.ts`
**Delete:** none
**Read only:** `e2e/fixtures/viet-kudo-constants.ts`, `test-contract.md`,
`lib/i18n/messages/vi-kudos.ts` (the pattern), `lib/kudos/compose-contract.ts` (the error codes)

## Implementation Steps

1. Add the `kudosCompose` interface to `dictionary.ts` in the shape above, with a doc comment naming
   the screen (`ihQ26W78P2`) and stating that hashtag names are data, not copy.
2. Write `vi-kudos-compose.ts` by **copy-pasting** each VN string from
   `e2e/fixtures/viet-kudo-constants.ts`. For anything not in that file (labels, aria-labels, the
   link dialog, `recipient-empty`), take it from `design-source-analysis.md § 1` where it exists and
   translate faithfully where it does not — flagging the latter in a comment.
3. Write `en-kudos-compose.ts` with a real translation of every key.
4. Wire both into `vi.ts` / `en.ts`.
5. `npm run typecheck` — this is the compile-time locale gate; a missing or misspelled key fails here.
   Then `npm run lint`.
6. Verify the strings against the assertions mechanically, before any component exists:
   ```
   node -e "const c=require('fs').readFileSync('e2e/fixtures/viet-kudo-constants.ts','utf8');
            const v=require('fs').readFileSync('lib/i18n/messages/vi-kudos-compose.ts','utf8');
            for (const s of ['Gửi lời cám ơn và ghi nhận đến đồng đội','Tìm kiếm',
              'Dành tặng một danh hiệu cho đồng đội','Ví dụ: Người truyền động lực cho tôi.',
              'Danh hiệu sẽ hiển thị làm tiêu đề Kudos của bạn.','Không được để trống',
              'Tối đa 5 hashtag','Tiêu chuẩn cộng đồng','Hủy','Gửi'])
              if(!v.includes(s)) { console.error('MISSING: '+s); process.exitCode=1; }"
   ```
   Extend the list to every string the suite compares; the check must print nothing.

## Todo List

- [x] `kudosCompose` added to `Dictionary` with the documented shape
- [x] `vi-kudos-compose.ts` — every asserted string copy-pasted from the fixture file
- [x] Unauthored strings (`Tiêu chuẩn cộng đồng`, `Định dạng file không được hỗ trợ`) present and commented as unauthored
- [x] `Không được để trống` written once, reused by all four fields
- [x] `en-kudos-compose.ts` — full faithful translation, no placeholders
- [x] `vi.ts` / `en.ts` wired
- [x] Hashtag names deliberately absent (they are data)
- [x] `npm run typecheck && npm run lint` clean
- [x] Step 6 string check prints nothing

## Success Criteria

- `npm run typecheck` passes, proving both locales carry identical keys.
- Step 6 finds every asserted string present in the VN file.
- `grep -n "High-perorming\|BE PROFESSIONAL" lib/i18n/` returns nothing — no mock hashtag names leaked
  into copy.
- No VN string appears under two different keys.
- Each new locale file is ≤200 lines.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| A single wrong character (diacritic, curly vs straight quote, trailing space) fails an exact-text assertion | **High** × High | Copy-paste from the fixture, never retype; step 6 checks mechanically before any component is built |
| `dictionary.ts` edit breaks typecheck repo-wide | Med × High | Additive namespace only; nothing existing is touched; typecheck is run immediately |
| EN ships as placeholders because nothing asserts it | Med × Med | Explicit requirement, and the todo list names it; a reviewer can spot `TODO`/duplicated VN text |
| Mock hashtag names from the companion frame get transcribed as copy | Med × Med | Insight 7 plus a grep in the success criteria |
| The unauthored two strings get "corrected" later and silently break the suite | Med × High | Both carry an in-file comment naming the test contract as their source and this phase as the ruling |

**Rollback:** revert the three modified files and delete the two new ones. Nothing consumes
`kudosCompose` until phase 08.

## Security Considerations

- Copy only. No user input, no interpolation, no `href` built from a dictionary value — the
  `community-standards-link` target is a fixed literal (`/standards`) chosen in phase 08, never a
  translated string.
- Error strings are static and locale-resolved; a server error code can never inject text, because the
  action returns codes and this file owns the words (phase 01 § Security).

## Next Steps

08, 09, 10 and 11 all consume slices of `kudosCompose` as a `copy` prop. Confirm to the orchestrator
that the two unauthored strings shipped, so they land in the promote-time spec refresh.
