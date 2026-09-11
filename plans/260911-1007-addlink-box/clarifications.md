# Clarifications — Addlink Box (MoMorph `OyDLDuSGEa`)

**MoMorph refs**
- Addlink Box: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/OyDLDuSGEa
- Parent screen: SCR005 Viết Kudo (`/kudos/new`), feature F005
- specs: 10 design items (A, B, B.1, B.2, C, C.1, C.2, D, D.1, D.2) — `spec_status: done`
- test cases: 25 rows published (2 ACCESSING, 11 GUI, 12 FUNCTION)
- testPolicy: `e2e-red-first` — the frame carries form validation, required-field errors and
  modal open/close transitions, which `intent-detection.md` auto-selects strict E2E for.

**Standing authority.** User granted auto-resolution: "nếu có vấn đề gì cần confirm với tôi,
tự động triển khai theo hướng câu trả lời đâu tiên, Yes hoặc câu trả lời Recommend mà ko cần
confirm tôi." Every decision below is taken on the Recommended option without a blocking question.

## Session 2026-09-11

- Q: The frame is a modal, not a route. Where does it live? → A: **It is the design authority for
  the already-shipped `app/kudos/new/_components/link-dialog.tsx` (F005/SCR005).** Rationale: that
  file's own doc comment says "No MoMorph node backs this dialog either (ratification item 6 lists
  it as unauthored)" — this frame is exactly the missing source. No new route, no new `F###`
  reservation; an F005 amendment, keeping feature-code contiguity clean.

- Q: The shipped dialog has ONE field (`link-url-input`). The frame specifies TWO — B "Text"
  (`Nội dung`, 1–100 chars) and C "Link" (`URL`, 5–2048 chars, URL format). Which wins? → A: **The
  frame wins — the dialog gains a second field.** Rationale: `momorph-development.md` rule 1 makes
  MCP design data authoritative, and the shipped one-field shape was explicitly marked unauthored
  guesswork rather than a decision anyone made.

- Q: What does the new `Nội dung` field DO to the document? The rich-text model's link run is
  `{ type: "link"; text; href }`, but today `onConfirmLink(href)` only marks the current textarea
  selection — there was no text to supply. → A: **`Nội dung` is the link's display text: on save it
  REPLACES the current selection (or inserts at the caret when the selection is empty) and the
  inserted text carries the link mark.** Rationale: it is the only reading under which a "Text"
  field on a link dialog means anything, and it matches `KudosRun`'s existing
  `{ type: "link"; text; href }` shape without touching the frozen contract's run types.

- Q: Does `Nội dung` prefill from the current selection? → A: **Yes — a non-empty selection
  prefills it; an empty selection opens the field blank.** Rationale: it preserves the shipped
  "select text, then link it" gesture (ID-31's world) instead of silently breaking it, and the user
  can still overwrite the prefill.

- Q: The new primitive replaces a text range. What happens to marks (bold/mention) sitting inside
  the replaced region? → A: **They are dropped, not re-anchored.** Rationale: verbatim reuse of the
  policy `rich-text.ts` already states for `remapMarks` — "drops any mark touching the edited region
  rather than re-anchoring by guesswork — deliberate, not a bug". One policy, not two.

- Q: The shipped dialog gates saving by DISABLING the confirm button while the URL is invalid. The
  frame's test cases require an error MESSAGE on save (`e5632ac7`: "Error is displayed for each
  invalid or empty field"; `3912184e`, `adb699ca`, `7d85997d`, `97dc4028`, `db2ca333`, `aad5791a`).
  A disabled button fires no click, so no message would ever appear. → A: **Drop the disabled gate:
  `Lưu` is always clickable, the click validates both fields, per-field errors render, and the modal
  stays open.** Rationale: a disabled button that never says why is precisely the failure the 25
  test cases were written against; the save is still blocked, just audibly.

- Q: URL format — validate on blur as well as on save? → A: **Yes, both.** Verbatim from item C
  `description`: "Blur: Kiểm tra định dạng URL và hiển thị lỗi nếu không hợp lệ", and TC `db2ca333`
  step 2 reads "Blur the field or click save".

- Q: Accepted URL schemes — the frame says http/https, the frozen contract's
  `ACCEPTED_LINK_SCHEMES` is `http/https/mailto`. Narrow it? → A: **No — keep the existing
  allow-list.** Rationale: that constant is the shared security boundary re-checked by
  `parseKudosDoc` and the renderer; narrowing it here would desync the dialog from the parser for a
  scheme the frame never mentions either way. `javascript:`/`data:`/`vbscript:` remain impossible,
  which is the property that actually matters.

- Q: Copy for the two locales. The frame image reads Vietnamese ("Thêm đường dẫn", "Nội dung",
  "URL", "Hủy", "Lưu") while spec item A calls the title "Add link". → A: **vi takes the frame image
  verbatim; en takes the spec's own English ("Add link", "Text", "URL", "Cancel", "Save").**
  Rationale: the app is bilingual and both strings are authored design content — neither is invented.
  `Hủy` keeps reusing `buttons.cancel` as it does today rather than growing a second "Hủy" key.

- Q: Button styling — the frame shows `Hủy` small+bordered with an X icon and `Lưu` large+yellow
  with a link icon, filling the row. → A: **Implement as drawn** (TC `b13a3dcc`, `096b9346`):
  `Hủy` is auto-width with a border and an X glyph; `Lưu` takes the remaining width on a `#FFEA9E`
  ground with a link glyph. Icons come from the repo's existing `app/_components/icons.tsx`
  convention — no new icon dependency.

- Q: ESC and click-outside close? → A: **Already satisfied and kept** — `useDismissOnOutside`
  handles both (TC `48467d34` step 3). No new hook.

- Q: Can two modals stack (TC `1a55a427`)? → A: **Structurally impossible** — `linkDialogOpen` is a
  single boolean in `use-body-editor-controller.ts`, and the dialog unmounts when false.

- Q: Auth gating (TC `70006b13`)? → A: **Already satisfied** — `/kudos/new` is route-guarded by
  F001/F005; an anonymous visitor never reaches the toolbar that opens this dialog.
  `e2e/profile-anon.spec.ts`-style guard coverage already exists; no new work.

- Q: Supabase local — the user asked for it explicitly, but this dialog touches no table. → A:
  **No migration, no query, no Server Action.** Local Supabase is used as it already is: it backs
  the authenticated `kudos-authed` Playwright session the strict E2E gate runs under, and the body
  the link lands in is persisted by F005's existing `createKudos` write path. Nothing is invented
  and nothing new is seeded.

## Unresolved

- None. Every gap above was resolved under the standing authority.
