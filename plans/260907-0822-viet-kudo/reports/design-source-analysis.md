# Viết Kudo (`ihQ26W78P2`) — design-source analysis

Rewritten pass. Previous version (`git show` history / prior file content) was built from the
PNG alone with zero MoMorph MCP access — its field/column mapping was flagged as pure inference.
This pass has real MCP access: `download_specs` (26 items), `download_test_cases` (57 cases),
`get_frame_node_tree`, `list_frames` (174 frames), `get_frame`, `get_node` (measured CSS),
`list_media_nodes`. Every claim below either carries a `mm:{nodeId}` citation or is explicitly
marked unknown. Raw sources on disk:

- `plans/260907-0822-viet-kudo/design/specs.csv` — 26 design items for `ihQ26W78P2`, verbatim.
- `plans/260907-0822-viet-kudo/design/test-cases.csv` — 57 test cases, verbatim.
- `plans/260907-0822-viet-kudo/design/specs-p9zO-c4a4x.csv` — 10 design items for the in-scope
  "Dropdown list hashtag" companion frame, verbatim.
- `plans/260907-0822-viet-kudo/design/viet-kudo.png` — 1440×1024 frame image (already present).

## 1. Copy inventory (verbatim, with node IDs)

Modal instance root: `mm:520:11647` ("Viết KUDO"), placed inside frame `mm:520:11602`.

| Copy | Node |
|---|---|
| `Gửi lời cám ơn và ghi nhận đến đồng đội` (title) | `mm:I520:11647;520:9870` |
| `Người nhận` + red `*` (label) | `mm:I520:11647;520:9872` |
| `Tìm kiếm` (search placeholder) | `mm:I520:11647;520:9873` (component `mms_B.2_Search`) |
| Toolbar icons B / I / S / numbered-list / link / quote | `mm:I520:11647;520:9881`, `662:11119`, `662:11213`, `662:10376`, `662:10507`, `662:10647` |
| `Hãy gửi gắm lời cám ơn và ghi nhận đến đồng đội tại đây nhé!` (textarea placeholder) | `mm:I520:11647;520:9886` |
| `Bạn có thể "@ + tên" để nhắc tới đồng nghiệp khác` (helper) | `mm:I520:11647;520:9888` |
| `Hashtag` + red `*` (label) | `mm:I520:11647;520:9891` |
| `+ Hashtag` button, note `Tối đa 5` | `mm:I520:11647;662:8911` (button), spec item E |
| `Image` (label) | `mm:I520:11647;520:9897` |
| `+ Image` button, note `Tối đa 5` | `mm:I520:11647;662:9132` |
| 5 sample image thumbnails, each with a close ("x") button | `mm:I520:11647;662:9197/9393/9439/9495/9561` |
| `Gửi lời cám ơn và ghi nhận ẩn danh` (checkbox label) | `mm:I520:11647;520:14099` |
| `Hủy` button | `mm:I520:11647;520:9906` |
| `Gửi` button | `mm:I520:11647;520:9907` |

These are confirmed live TEXT-node values from `get_frame_node_tree`, not just the PNG — the PNG
read in the prior pass got every string right. No additional off-canvas copy (tooltips, inline
error text) is present in the node tree; error copy exists only in the test-case CSV (see § 9).

## 2. Field-by-field table — spec-confirmed

Source: `specs.csv` rows A–H. `required` here is the spec CSV's own `required` column, which is
**inconsistent with its own prose** in three places — flagged inline.

| Field | Spec `required` | Spec `dataType` | Validation note (verbatim) | Candidate table.column (F004 schema) | Schema can hold it today? |
|---|---|---|---|---|---|
| Recipient search (B.2, `mm:I520:11647;520:9873`) | `true` | `string` | "Trường bắt buộc Chọn người nhận từ danh sách (autocomplete) Tối thiểu 1 ký tự" | `kudos.receiver_id` → `sunners.id` | **Yes** — `receiver_id bigint not null` exists. |
| Toolbar/body field C (`mm:I520:11647;520:9877`) | `true` | `string` | none | n/a — see § 3, this row is the toolbar container, not the message itself | n/a |
| Message textarea D (`mm:I520:11647;520:9886`) | `true` | `string` | "Cho phép '@' + tên để nhắc đồng nghiệp Bắt buộc" | `kudos.message` | **Yes** — `message text not null` exists. |
| Hashtag field E (`mm:I520:11647;520:9890`) | `true` | `string` | "Tối thiểu 1 tag. Tối đa 5 hashtag Trường bắt buộc" | `kudos_hashtags` (join, ≤5 rows per kudos) | **Yes** — table exists, no row-count constraint enforced by schema (business rule only). |
| Image field F (`mm:I520:11647;520:9896`) | `false` | (none) | "Tối đa 5 ảnh" | `kudos_attachments` (`image_url`, `position`) | **Yes** — table exists, unconstrained count. |
| Anonymous checkbox G (`mm:I520:11647;520:14099`) | `false` | `boolean` | none | **no column** | **No** — see § 6, hard schema gap. |
| Danh hiệu / "title" field | — | — | — | **Not a field on this frame.** | n/a |

**Correction to the prior pass:** there is **no `Danh hiệu` field on this frame.** The prior
PNG-only report invented a "Danh hiệu" title-input field with helper copy "Danh hiệu sẽ hiển thị
làm tiêu đề Kudos của bạn." — that string does not exist anywhere in the 26-row spec CSV, the
frame's TEXT nodes, or the test-case CSV. It was very likely a PNG-misread (possibly bleed-through
from an adjacent frame in the file, given this Figma file contains 174 frames covering multiple
Kudos surfaces). **G1 from the prior pass is therefore moot** — `kudos.campaign` is not this
screen's concern; `campaign` was already resolved by the Live Board commission as the *sender's*
tag on an existing kudos, not something entered here. Delete this from the clarification backlog.

Three required-flag inconsistencies worth flagging for the clarification gate (not resolved
here):
1. Item **C** (`mm:I520:11647;520:9877`, the format-toolbar container) is itself marked
   `dataType: string, required: true` in the CSV — almost certainly a spec-authoring error
   (a toolbar has no data value), not a real requirement on the toolbar itself. The textarea it
   sits above (item D) is separately and correctly marked required.
2. Item **E.2** ("Tag Group", the chip container) duplicates E's `required: true` — consistent,
   not a conflict.
3. `Người nhận` **label** (B.1) is marked `required: false` in its own row (labels never carry
   `required`), while the **input** (B.2) correctly carries `required: true` — this is normal
   spec structure (label rows are decorative), not a conflict.

None of the 26 rows carry a `databaseTable` or `databaseColumn` value — every one of those two
columns is empty across the whole CSV. The table/column mapping above is therefore **cross-
referenced against the already-shipped F004 schema, not asserted by this screen's own spec.**

## 3. Rich text — spec-confirmed, storage format still undefined

Item C (`mm:I520:11647;520:9877`) description, verbatim: *"Các chức năng hỗ trợ format text
trong phần nhập liệu, bao gồm Bold, Italic, Stroke, Number, Link, Quote"* — six affordances:
Bold (C.1), Italic (C.2), Stroke/strikethrough (C.3), Number-list (C.4), Link (C.5), Quote (C.6).
C.5's own description: *"Click: Mở hộp thoại nhập URL và tùy chọn mở trong tab mới, sau đó chèn
liên kết vào vùng văn bản"* — link insertion is a URL-prompt dialog, not just a wrap-selection.

**Storage format is silent in the spec.** No row states HTML vs. Markdown vs. a delta/JSON doc
format, and `kudos.message` is plain `text` in the shipped migration with no format/markup
column alongside it. This is an unresolved gap (§ 10), not something I can infer from six toolbar
buttons.

## 4. `@mention` — spec-confirmed as real autocomplete, not just a typing convention

Item D's own validation note: *"Cho phép '@' + tên để nhắc đồng nghiệp"* (required). Item D.1
(`mm:I520:11647;520:9887`), the helper line, is separately confirmed real display copy: *"Bạn có
thể '@ + tên' để nhắc tới đồng nghiệp khác"*.

Test cases confirm this is a real autocomplete, not prose: **ID-12** ("Mention functionality
(@)") — input `Cảm ơn @` → *"Hiển thị danh sách gợi ý tên đồng nghiệp / Có thể chọn để mention"*;
**ID-13** — selecting `NguyenVanA` from the suggestion list → *"Tên được mention chính xác trong
textarea"*. This is a resolving picker over real people, matching the `Người nhận` search's
Sunner autocomplete pattern. What is **not** stated: whether a resolved mention is stored as a
plain `@name` substring inside `kudos.message` (current schema, zero extra work) or as a
structured reference needing a join table. No spec row or test case addresses storage — flagged
as a gap (§ 10).

## 5. Image attachments — spec-confirmed cap and behavior; format/size undefined

Field F (`mm:I520:11647;520:9896`) validation note: *"Tối đa 5 ảnh"* (max 5, not required).
F.5 description: *"Nếu đã 5 ảnh: ẩn"* (the `+ Image` button hides once 5 are attached).

Test cases add concrete acceptance criteria the spec CSV itself doesn't state:
- **ID-21/22** accept `.jpg` and `.png`; **ID-23/24/55** reject `.pdf`, `.mp4`, `.txt` with an
  "invalid format" error. This is real evidence of an accept-list, but the CSV never enumerates
  it — the list above is only what the *test cases* exercise, not a confirmed exhaustive spec.
- No `databaseNote`, size limit, or dimension constraint appears anywhere in the 26 spec rows —
  the `Tối đa 5 ảnh` note is the only quantitative constraint in the source data.
- The 5 pre-populated thumbnails in the frame (`mm:I520:11647;662:9197` etc., each 80×80px, see
  § 8) are the frame's own mock/example state for design purposes, not evidence of a default
  starting count — test case ID-37/ID-19 both describe starting from zero and uploading up to 5.

If this maps to `kudos_attachments`, that table already supports arbitrary `position`-ordered
rows; the "5" cap is a UI/business-rule constraint layered on top, not a schema constraint.

## 6. Anonymous checkbox — real UI consequence, confirmed hard schema gap

Item G (`mm:I520:11647;520:14099`) description, verbatim: *"Cho phép người gửi chọn ẩn danh; nhãn
hiển thị 'Gửi lời cám ơn và ghi nhận ẩn danh'. Function: - Click: Bật/tắt ẩn danh trước khi gửi -
Bật: Hiển thị text field điền tên ẩn danh"* — checking it **reveals an additional text field for
typing an anonymous display name.** Test cases ID-43/ID-44 confirm this show/hide behavior
exactly. **No such extra text field exists in the frame's own node tree or spec rows** — item G
has exactly two children in the tree (`Check box` frame + label text, `mm:I520:11647;520:14099`),
no third child for a name input. This is a real gap between the spec's prose ("Bật: Hiển thị text
field điền tên ẩn danh") and the frame ("hiện có" only checkbox + label) — not resolvable here.

Schema: `kudos` (migration lines 55–62) has exactly `id, sender_id, receiver_id, campaign,
message, sent_at, heart_baseline`. **No `is_anonymous`/`sender_hidden` column, confirmed again on
this pass.** The Live Board card (F004, already shipped) always renders a sender chip sourced
from `sender_id` — there is no "hide sender" branch in that rendering. Building this checkbox for
real therefore needs either (a) a migration adding a nullable flag/name column plus a Live Board
follow-up to actually suppress the sender chip when set, or (b) explicit descoping to
UI-only/no-op. This is unchanged from the prior pass's conclusion and remains gap G2 (§ 10).

One clarifying distinction worth recording precisely, because the shipped F004 docs use "ẩn
danh" for something unrelated: `docs/features/F004_KudosLiveBoard/technical-spec.md` BR-004 uses
"khách ẩn danh" to mean an **unauthenticated viewer** of the Live Board (falls back to a seeded
Sunner row with `auth_user_id IS NULL`) — that is a *different* concept from this screen's
"gửi ẩn danh" checkbox, which is about hiding the **sender's identity on a kudos they are
composing**. Do not conflate the two; `sunners.auth_user_id IS NULL` is not a mechanism this
checkbox can reuse.

## 7. Submit / cancel — spec-confirmed behavior, destination undefined

Item H (`mm:I520:11647;520:9905`) description, verbatim: *"Click 'Hủy': đóng modal, huỷ thay đổi
— Click 'Gửi': validate form và gửi dữ liệu, show loading, đóng modal khi thành công — State:
'Gửi' disabled nếu các trường bắt buộc chưa được điền"*.

- **Validation order:** not enumerated field-by-field in the spec, but test cases ID-48/49/56
  establish the three gating fields as Người nhận, Nội dung (message), Hashtag — image is not
  gating. ID-56 shows all three error simultaneously when submitted empty, i.e. **not** a
  stop-at-first-error validator; every unmet required field shows its own inline error at once.
- **Hủy (H.1, `mm:I520:11647;520:9906`):** *"Đóng modal và bỏ mọi thay đổi, không gửi dữ liệu —
  State: luôn enabled khi hiển thị"* — confirmed **no confirm-before-discard dialog**; it closes
  and discards silently. Test case ID-45 confirms: click "Hủy" after entering data → "Modal đóng
  / Dữ liệu không được lưu", two steps, no intermediate confirm step.
  **This corrects the prior pass**, which left "does Hủy confirm first?" as an open gap — it is
  now spec-confirmed: no.
- **Gửi (H.2, `mm:I520:11647;520:9907`):** validate → loading state → close on success. **No
  success toast, confirmation screen, or navigation destination is named anywhere** in the 26
  spec rows or 57 test cases — `transitionNote`/`linkedFrameId` are empty on every row of this
  frame's CSV. This remains an open gap (§ 10) exactly as the prior pass found, now confirmed by
  reading the actual (empty) navigation columns rather than inferring their absence.

## 8. Measured visual values (from `get_node`, CSS as authored — `get_figma_image` was not
attempted this pass since prior session logs confirm it 500s file-wide; all values below come
from `get_node`/`list_media_nodes`, which returned real computed styles)

| Element | Node | Values |
|---|---|---|
| Modal container | `mm:520:11647` | `width: 752px`, `height: 1012px`, `padding: 40px`, `gap: 32px`, `border-radius: 24px`, `background-color: rgba(255, 248, 225, 1)` (`#FFF8E1`) |
| Title text | `mm:I520:11647;520:9870` | `font-family: Montserrat`, `font-weight: 700`, `font-size: 32px`, `line-height: 40px`, `text-align: center`, `color: rgba(0, 16, 26, 1)` (`#00101A`), box `672×80px` |
| Recipient search input | `mm:I520:11647;520:9873` | component `186:2757` (set `186:1426` — same shared button/input component family reused for Hủy, Gửi, +Hashtag, +Image), `border: 1px solid #998C5F`, `border-radius: 8px`, `padding: 16px 24px`, `background: #FFF`, `flex: 1 0 0` |
| Dropdown-arrow icon on search | `mm:I520:11647;520:9873;186:2761` | `24×24px` |
| Toolbar container | `mm:I520:11647;520:9877` | `width: 1006px`, `height: 40px`, `justify-content: flex-end` — **note:** this exceeds the 752px modal width; likely an unresolved-auto-layout artifact in the source file (the component's raw absolute width vs. its flex-clipped rendered width), not a real 1006px toolbar — flag for the implementer, do not hard-code 1006px |
| Toolbar icons (B/I/S/list/link/quote) | `mm:I520:11647;520:9881` etc. | each `24×24px`, each icon's own button box `40px` tall |
| Message textarea | `mm:I520:11647;520:9886` | `height: 200px`, `min-height: 120px`, `border: 1px solid #998C5F`, `background: #FFF`, `border-radius: 0 0 8px 8px` (top corners square — sits directly under the toolbar), `padding-left: 24px` |
| `+ Hashtag` button | `mm:I520:11647;662:8911` | `height: 48px`, `padding: 4px 8px`, `gap: 8px`, `border: 1px solid #998C5F`, `border-radius: 8px`, `background: #FFF` |
| Image thumbnails | `mm:I520:11647;662:9197/9393/9439/9495/9561` | `80×80px`, `aspect-ratio: 1/1` (from `list_media_nodes`) |
| Thumbnail close ("x") button | e.g. `mm:I520:11647;662:9197;662:9287` | button box `20×20px`, icon `MM_MEDIA_Close Tiny` `17×17px` |
| Anonymous checkbox | `mm:I520:11647;520:14099;520:14097` | `24×24px`, `border: 1px solid #999`, `border-radius: 4px`, `background: #FFF` |
| Cancel ("Hủy") button | `mm:I520:11647;520:9906` | `padding: 16px 40px`, `gap: 8px`, `border: 1px solid #998C5F`, `border-radius: 4px`, `background: rgba(255, 234, 158, 0.10)` |
| Submit ("Gửi") button | `mm:I520:11647;520:9907` | `width: 502px`, `height: 60px`, `padding: 16px`, `border-radius: 8px`, `background: rgba(255, 234, 158, 1)` (`#FFEA9E`, solid gold — matches the Live Board's gold token from `plans/260906-1945-kudos-live-board/clarifications.md`), `justify-content: center` |
| Send icon on submit button | `mm:I520:11647;520:9907;186:1766` | `24×24px` |

All hex/rgba values above are read directly from computed CSS via `get_node`, not sampled from
the PNG — none are guessed.

## 9. Verbatim error copy (from test cases, spec CSV has none)

Test-case CSV supplies the only literal error strings in the source data:
- `"Không được để trống"` — used for empty Nội dung (ID-51) and empty Hashtag (ID-52).
- Người nhận empty: no literal string given, only *"Hiển thị viền đỏ và thông báo lỗi"* — the
  message text itself is not specified (ID-7, ID-50).
- `"Tối đa 5 hashtag"` — hashtag cap exceeded (ID-17, ID-53).
- Image invalid type / hashtag-cap-6th / image-cap-6th: described behaviorally ("Hiển thị thông
  báo lỗi định dạng file không hợp lệ") but no literal string given (ID-23/24/55).

## 10. Companion frames (`list_frames`, 174 total in this fileKey)

Filtered by name-relevance, cross-checked against `get_frame`, `download_specs`, and
`get_frame_node_tree`/`get_overview` where those returned data (several in-progress frames have
**no cached node tree or image at all** — `get_frame_node_tree`/`get_frame_image` returned "no
data" for them; judged by name + `get_frame` metadata only, flagged below).

### In scope for this compose screen

| screenId | name | figma node | design/spec status | Evidence | Persisted specs? |
|---|---|---|---|---|---|
| `p9zO-c4a4x` | Dropdown list hashtag | `1002:13013` | `done`/`done` | `download_specs` returned 10 real items describing a checkbox-style multi-select list (`#High-perorming`, `#BE PROFESSIONAL`, `#BE OPTIMISTIC`, `#Be A Team`, `#THINK OUTSIDE THE BOX`, `#GET RISKY`, `#GO FAST`, `#WASSHOI` — real hashtag values, "danh sách hashtag được lấy dynamic từ database", max 5, disables remaining rows at 5). Its top child `Frame 541 → Button` reuses **the exact same component instance** (`componentId 186:2757`) as this screen's `+ Hashtag` trigger (`mm:I520:11647;662:8911`, also inside a `Frame 541`) — same trigger, same picker. **High confidence.** | Yes — `design/specs-p9zO-c4a4x.csv` |
| `zJzaC9GgXt` | Dropdown list người nhận | `1002:15464` | `in_progress`/`in_progress` | Name and node-ID range (`1002:xxxx`, adjacent to the hashtag dropdown `1002:13013`) strongly suggest the paired recipient-search dropdown for B.2's `mm:I520:11647;520:9873` (spec: "open dropdown/autocomplete list of Sunners"). `download_specs` returned **0 items** — the frame exists but has no authored spec content yet. **Medium-high confidence on scope, zero content to persist.** | No — empty (`item_count: 0`) |
| `5c7PkAibyD` | Viết KUDO - Lỗi chưa điền đủ thông tin đã ấn gửi | `662:13035` | `in_progress`/`none` | Name literally states "Viết KUDO — error, not enough info filled, Gửi pressed" — a validation-error state of *this exact modal*. Node ID `662:13035` sits in the same `662:xxxx` range as this screen's own internal components (toolbar icons, hashtag/image buttons). **High confidence this is the same screen's error-state variant**, not a separate commission. `download_specs` returned **0 items**. | No — empty (`item_count: 0`) |

### Checked and judged out of scope (own commission)

| screenId | name | figma node | status | Why out of scope |
|---|---|---|---|---|
| `419VXmMy6I` | Màn Sửa bài viết- edit mode | `1949:13746` | `in_progress`/`none` | Already resolved as a separate commission by the Live Board clarifications (`plans/260906-1945-kudos-live-board/clarifications.md`: *"Màn Sửa bài viết- edit mode frame is a separate commission"*), re-confirmed here — node ID range (`1949:xxxx`) is unrelated to this screen's `520:xxxx`/`662:xxxx` nodes. |
| `p9vFVBE_tc` | Ẩn danh | `2099:9148` | `in_progress`/`none` | Name suggests it could relate to § 6's checkbox, but `download_specs` returned 0 items and no node tree/image is cached (`get_frame_node_tree`/`get_frame_image` both "no data"). Node ID (`2099:xxxx`) is unrelated to this frame's ranges. Cannot confirm scope from name alone — insufficient evidence either way, not claimed in-scope. |
| `lZRNrgb04V` | Image | `513:8441` | `in_progress`/`none` | Generic name, 0 spec items, no cached tree/image, unrelated node range (`513:xxxx`). Not linked to this screen's `+ Image` picker (which is inline on this frame, not a separate picker frame — F.5 `mm:I520:11647;662:9132` opens a native file picker per its own description, not another MoMorph frame). |
| `QIMJNgFb8K` | Dropdown list người nhận muốn gửi lời chúc | `828:10943` | `in_progress`/`in_progress` | Name suggests a recipient dropdown but for a *different* verb ("gửi lời chúc" vs. this screen's "gửi lời cám ơn"), node range `828:xxxx` matches the separate `Gửi lời chúc Kudos` frames (`RO7O6QOhfJ` `828:13433`, `JsTvi8KVQA` `1612:5056`) — those read as an older/alternate compose screen, not this one. Judged a different commission's companion, not this screen's. |
| `JWpsISMAaM` | Dropdown Hashtag filter | `721:5580` | `done`/`done` | Already resolved by F004: this is the Live Board's filter dropdown, not the compose-modal's tag picker. Confirmed not this screen's companion. |
| `MaZUn5xHXZ` | Sun* Kudos - Live board | `2940:13431` | `done`/`done` | Already shipped as F004; the compose bar there deep-links to *this* screen (`ihQ26W78P2`) per F004's own clarifications, but the Live Board frame itself is not part of this commission. |
| `onDIohs2bS` | View Kudo | `520:18779` | `in_progress`/`none` | Detail view of an existing kudos, not a compose-time surface. |
| Admin/Campaign frames (`Nj4PY0mUJJ`, `cb7kD3-Xr6`, `FVA7A5f8z8`, `htgRaDTO2f`, `rMY1QfgSYp`) | Action - Campaign, Admin - Setting - add/edit Campaign, Popup delete campaign | various | `in_progress`/`none` | Admin/campaign-management surfaces; unrelated to composing a kudos. |
| All `[iOS] Sun*Kudos_*` frames (14 frames under node ranges `6885:xxxx`/`6891:xxxx`, including `[iOS] Sun*Kudos_Gửi lời chúc Kudos` `PV7jBVZU1N` done/done) | — | — | — | Native mobile variant of the whole Kudos feature, a separate platform commission (this task's `stack` is Next.js web). Listed for completeness — the iOS compose screen (`PV7jBVZU1N`, done/done) could be read later if a mobile build of this screen is ever commissioned, but is out of scope now. |
| `Qhg3SUg_8L`, `49Qr2oIjMV`, `n56Yyp7Klu`, `JYHZJyOwT-` | "KUDO", "KUDO - Highlight", "KUDO spam" | various | `in_progress`/mixed | Generic/ambiguous names, no spec content fetched (not investigated further — read as card-level components on other boards, not compose-modal companions; flagged as unresolved-by-name if a future pass needs to check them). |

## Gaps for the clarification gate

1. **Corrected, not a gap:** the prior pass's "Danh hiệu" field does not exist on this frame —
   remove it from any backlog; there is no title/headline input here (§ 2).
2. Rich-text storage format (HTML / Markdown / delta-JSON) — undefined in spec; `kudos.message`
   is plain `text` today (§ 3).
3. `@mention` storage — confirmed real autocomplete over Sunners (§ 4), but whether a resolved
   mention becomes a plain `@name` substring in `kudos.message` or a structured reference
   (needing a join table) is undefined.
4. Image accept-list and size limits — only inferable from test cases (jpg/png accepted; pdf/mp4/
   txt rejected), never stated as a spec row or `databaseNote` (§ 5).
5. **The anonymous checkbox's own spec description promises a reveal-on-check name text field
   that does not exist anywhere in the frame's node tree** (§ 6) — is that a stale spec sentence,
   or a missing frame element that needs designing before build?
6. Anonymous checkbox has no backing column in the shipped `kudos` schema (§ 6, unchanged from
   prior pass) — needs a migration decision, and a Live Board follow-up to actually suppress the
   sender chip if built.
7. Post-`Gửi` success state — toast vs. silent close vs. navigate — and any post-submit
   destination are unstated in all 26 spec rows and 57 test cases (§ 7).
8. Literal error-message copy for the Người nhận field, and for the two file-rejection cases
   (invalid image type, 6th hashtag/image attempt) is described behaviorally in test cases but
   never given as an exact string (§ 9).
9. `zJzaC9GgXt` (Dropdown list người nhận) and `5c7PkAibyD` (Viết KUDO error state) are judged
   in-scope companions by name/node-range evidence but carry **zero authored spec content** — an
   implementer building against them has no source-of-truth beyond this screen's own B.2/H specs
   and the 57 test cases. Confirm before assuming their detailed behavior beyond what test cases
   ID-8/9/10/25/26 (recipient dropdown) and the general "Gửi disabled + red border" pattern
   already establish.
10. Toolbar container's measured `1006px` width (`mm:I520:11647;520:9877`) exceeds the 752px
    modal — flagged in § 8 as likely a Figma auto-layout measurement artifact; do not hard-code
    it without visually confirming layout intent.
11. Whether this compose screen is meant to write real rows at all: `kudos` currently has **only
    a SELECT policy** (no INSERT grant/policy exists on `kudos`, `kudos_hashtags`, or
    `kudos_attachments`), matching F004's own decision to ship Track B as read-only/mock. Building
    a working `Gửi` therefore requires standing up write-path RLS as a prerequisite, not something
    this frame's spec addresses.

**Status:** DONE
**Summary:** Persisted `specs.csv` (26 items), `test-cases.csv` (57 cases) for `ihQ26W78P2`, plus `specs-p9zO-c4a4x.csv` (10 items) for the in-scope Hashtag-picker companion frame; identified 3 in-scope companions and 20+ checked-and-excluded frames from the file's 174 total; rewrote the analysis report with every claim carrying a `mm:{nodeId}` citation or explicit unknown-marker, correcting the prior pass's invented "Danh hiệu" field and confirming/denying its other open questions against real spec data.
**Concerns/Blockers:** none — no CSS-value guesses were made; two in-scope companion frames (`zJzaC9GgXt`, `5c7PkAibyD`) exist but have zero authored spec content, and the anonymous-checkbox spec text describes a reveal-on-check name field that is absent from the actual node tree — both flagged as gaps 5 and 9 above for the clarification gate rather than resolved here.
