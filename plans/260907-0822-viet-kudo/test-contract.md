# Test contract — Viết Kudo (`/kudos/new`)

Orchestrator-owned. The E2E spec and the implementation are both bound to this file: `tester` writes
assertions against it, `momorph-ui-implementer` and `implementer` emit exactly these hooks. Neither
side changes a hook unilaterally — a change comes back to the orchestrator. Copy values come from
`clarifications.md`, which is authoritative, and from `design/test-cases.csv` (57 cases).

## Route and access

`/kudos/new` — **auth-guarded** (ID-1), the first guard added since F001. An unauthenticated visitor
is redirected to `/login`. The public Kudos read surface (`/kudos`, `/kudos/[id]`,
`/kudos/secret-box`) is unchanged and must stay public.

`Hủy` and a successful `Gửi` both navigate to `/kudos`.

## Landmarks and copy

| Hook | Kind | Value |
|------|------|-------|
| page `<h1>` | text | `Gửi lời cám ơn và ghi nhận đến đồng đội` |
| `data-testid="compose-form"` | `<form>` | — |
| `data-testid="compose-cancel"` | `<a href="/kudos">` or `<button>` | label `Hủy` |
| `data-testid="compose-submit"` | `<button type="submit">` | label `Gửi`; never carries `disabled` or `aria-disabled`; always pressable; carries `data-submit-ready="true" \| "false"` per § Submit state |

Field order top to bottom (ID-3, plus the `Danh hiệu` row the frame adds at node `1688:10436`):
recipient → **title** → body editor → hashtags → images → anonymous checkbox → footer actions.

## Fields

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="recipient-input"` | `<input>` | placeholder `Tìm kiếm`; required; on invalid submit carries `aria-invalid="true"` |
| `data-testid="recipient-menu"` | `role="listbox"` | appears while typing; `role="option"` children filtered by the query (ID-8, ID-25); leading/trailing whitespace in the query is trimmed (ID-10) |
| `data-testid="recipient-empty"` | text | shown when no name matches (ID-9) |
| `data-testid="recipient-selected"` | element | the chosen person; picking an option fills the field and closes the menu (ID-26) |
| `data-testid="title-input"` | `<input>` | placeholder `Dành tặng một danh hiệu cho đồng đội`; required |
| `data-testid="title-hint"` | text | `Ví dụ: Người truyền động lực cho tôi.` and `Danh hiệu sẽ hiển thị làm tiêu đề Kudos của bạn.` |
| `data-testid="body-editor"` | `contenteditable` or `<textarea>` | placeholder `Hãy gửi gắm lời cám ơn và ghi nhận đến đồng đội tại đây nhé!`; required |
| `data-testid="body-hint"` | text | `Bạn có thể “@ + tên” để nhắc tới đồng nghiệp khác` |
| `data-testid="community-standards-link"` | `<a>` | label `Tiêu chuẩn cộng đồng` |

No character counter is rendered and no maximum body length is enforced (assumption A4).

## Rich-text toolbar

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="toolbar-bold"` | `<button>` | ID-27 · carries `aria-pressed` |
| `data-testid="toolbar-italic"` | `<button>` | ID-28 · carries `aria-pressed` |
| `data-testid="toolbar-strike"` | `<button>` | ID-29 · carries `aria-pressed` |
| `data-testid="toolbar-ordered-list"` | `<button>` | ID-30 |
| `data-testid="toolbar-link"` | `<button>` | ID-31 · opens `link-dialog` |
| `data-testid="toolbar-quote"` | `<button>` | ID-32 |
| `data-testid="link-dialog"` | dialog | a URL input plus confirm/cancel; confirming wraps the selection in a link (ID-31) |
| `data-testid="link-url-input"` | `<input>` | the URL field inside `link-dialog` |

## Mentions

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="mention-menu"` | `role="listbox"` | appears after `@` is typed and narrows as the name continues (ID-12, ID-33) |
| `data-testid="mention-option"` | `role="option"` | choosing one inserts that colleague into the body (ID-13) |

The chosen person is stored as a `mention` inline run carrying the sunner id, so re-display does not
re-resolve the name.

## Hashtags

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="hashtag-add"` | `<button>` | label contains `Hashtag` and `Tối đa 5`; opens `hashtag-menu` |
| `data-testid="hashtag-menu"` | `role="listbox"` | the options from companion frame `p9zO-c4a4x` |
| `data-testid="hashtag-chip"` | element | one per chosen tag (ID-34, ID-35); each has its own remove control |
| `data-testid="hashtag-chip-remove"` | `<button>` | removes exactly that chip and leaves the others (ID-36) |
| `data-testid="hashtag-error"` | text | `Tối đa 5 hashtag` when a sixth is attempted; the sixth is NOT added (ID-17, ID-53) |

At the limit the add button **stays visible** and refuses the sixth with the error above — this is
deliberately different from the image limit below, and the difference is what the test cases specify.

## Images

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="image-add"` | `<button>` / label wrapping `<input type="file">` | label contains `Image` and `Tối đa 5`; **hidden entirely once 5 images are present** (ID-19, ID-20, ID-38), and visible again after one is removed (ID-40) |
| `data-testid="image-input"` | `<input type="file" accept>` | accepts image types; multiple allowed |
| `data-testid="image-thumb"` | element | one per attached image, showing **that file**, each with a remove control (ID-37) |
| `data-testid="image-thumb-remove"` | `<button>` | removes exactly that image (ID-39) |
| `data-testid="image-error"` | text | shown when the chosen file is not an accepted image type; the file is NOT attached (ID-23, ID-24, ID-55) |

A `.jpg` and a `.png` upload successfully (ID-21, ID-22). A `.pdf` is rejected (ID-23). Files are
uploaded to Supabase Storage — the thumbnail shows the user's real file, never a substituted sample
(clarifications § Images).

## Anonymous

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="anonymous-checkbox"` | `<input type="checkbox">` | label `Gửi lời cám ơn và ghi nhận ẩn danh`; **unchecked by default** (ID-6) |
| `data-testid="anonymous-name-input"` | `<input>` | **hidden when unchecked, revealed when checked** (ID-43), hidden again when unchecked (ID-44); optional |

A kudos sent anonymously renders on the Live Board with the anonymous display name — or a neutral
label when none was given — in place of the sender chip. The receiver is always shown.

## Validation

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="field-error-recipient"` | text | `Không được để trống` (ID-11, ID-50); the input also carries `aria-invalid="true"` and a red border |
| `data-testid="field-error-title"` | text | `Không được để trống` |
| `data-testid="field-error-body"` | text | `Không được để trống` (ID-14, ID-51) |
| `data-testid="field-error-hashtag"` | text | `Không được để trống` (ID-52) |

Submitting an empty form shows **all** required-field errors at once, not the first only (ID-56), and
does not submit. Every rule is re-checked server-side in the action; the client-side state is a
convenience, never the boundary.

## Submit state

`compose-submit` is **never `disabled` and never `aria-disabled`** — it is always pressable (phase-02 repair).
It carries `data-submit-ready="false"` while any required field is empty (ID-48) and `data-submit-ready="true"` 
once recipient, title, body and at least one hashtag are present (ID-49). The readiness signal is observable 
and asserted; styling may render the not-ready state dimmed, but it must not render it inert. Pressing the 
button on an incomplete form is how the designed error state (frame `5c7PkAibyD`) is reached.

On submit: a loading/pending state appears, and on success the browser lands on `/kudos` with the new
Kudos visible on the board (ID-46, ID-47). That last part is the load-bearing proof — it is what
demonstrates the row actually reached Postgres rather than the form merely clearing.

## Out of contract (deliberately not asserted)

Editing or deleting a Kudos (no UPDATE/DELETE policy is created), a character counter (assumption
A4), a body maximum length, `Danh hiệu` error copy beyond the shared `Không được để trống` string,
and the unauthored companion frames' visual detail — all recorded in `clarifications.md`
§ Unresolved questions with the reason.

## Blast radius the suite must protect

- `proxy.ts` gains a guard — `e2e/route-guard.spec.ts`, `e2e/authenticated.spec.ts` and
  `e2e/callback-security.spec.ts` must stay green, and `/kudos` must stay public.
- `kudos.message_format`, `is_anonymous` and `anonymous_name` are added — F004's 57 seeded rows stay
  `'plain'` and non-anonymous, so every `e2e/kudos-live-board*.spec.ts` assertion must stay green.
- `lib/i18n/messages/dictionary.ts` is shared by every screen; a malformed namespace breaks
  typecheck repo-wide.

---

## Blueprint ratification (orchestrator, 2026-09-07b)

The blueprint surfaced eight conflicts between the authoritative artifacts and asked for
ratification on one. Ruled on here — this section is authoritative over anything above it that it
names.

### RATIFIED — § Submit state is amended: the button is never `disabled`

The blueprint is right that `ID-48` and `ID-56` cannot both hold, and I verified it independently:
`ID-48` asserts `toBeDisabled()` on a pristine form, while `ID-56` calls `.click()` on that same
button on that same pristine form with no `force`. Playwright's `click()` waits for actionability —
the negation of the very predicate `toBeDisabled()` asserts — so no markup satisfies both, and
`aria-disabled` does not escape it either, because `toBeDisabled()` matches that too.

**`ID-48` is the assertion that changes, and the design settles which way.** The file ships an
authored frame for exactly this state — `5c7PkAibyD`, "Lỗi chưa điền đủ thông tin đã ấn gửi"
("error: pressed send without filling in enough information"). That frame can only exist if `Gửi`
is pressable on an incomplete form. Seven further tests also depend on clicking submit with a field
empty. A `disabled` button would make the designed error state unreachable.

So the § Submit state row is replaced:

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="compose-submit"` | `<button type="submit">` | label `Gửi`. **Never carries `disabled` and never `aria-disabled`** — it is always pressable, because pressing it on an incomplete form is how the designed error state is reached. It carries `data-submit-ready="true" \| "false"`: `false` while any required field is empty, `true` once recipient, title, body and ≥1 hashtag are present. |

`ID-48` asserts `data-submit-ready="false"` on a pristine form; `ID-49` keeps its existing
assertions **and gains** `data-submit-ready="true"` — so the readiness signal stays observable and
asserted, and `ID-49` gets stronger rather than weaker. Styling may still render the not-ready state
dimmed; it must not render it inert.

### RATIFIED — six assertions that can never pass are repaired

`e2e/viet-kudo.spec.ts` lines 292, 325, 363, 622, 708 and 973 call
`toHaveCount(async (count) => …)`. `toHaveCount(count: number, …)` compares against a **number**, so
a function argument can never match — verified against `node_modules/playwright/types/test.d.ts:9511`.
These six could never go green whatever was built, and they include the load-bearing `ID-46`/`ID-47`
board check. They are repaired to `.first()` visibility assertions, which are strictly stronger than
"count > 0". This is a repair of a broken assertion, not a weakening of a working one.

**Also blocking and not previously reported: the same file leaves `npm run typecheck` with 12
errors** (the `toHaveCount` type mismatches plus implicit-`any` parameters). A repo whose typecheck
is red cannot gate any implementation phase. Phase 02 fixes this to zero.

### RATIFIED — F004's `K-21` is scoped off `/kudos/new`

`K-21` (anon) asserts `/kudos/new` returns 200 with a `main h1`; `ID-1` asserts an anonymous visitor
is redirected to `/login`. `ID-1` wins — the route is now a write surface and is guarded. `K-21`
keeps its assertions for `/kudos/secret-box` and `/kudos/[id]`, which remain public placeholders, and
coverage of `/kudos/new` moves to `ID-1` plus `ID-0`. Coverage moves; it does not shrink.

### RATIFIED as proposed

| # | Change | Ruling |
|---|--------|--------|
| 4 | `Danh hiệu` exists and ships | **Ratified.** `reports/design-source-analysis.md § 2` claims the field is a PNG misread; that section is stale. `clarifications.md` verified it live at nodes `1688:10436` / `1688:10437` / `1688:10447`. Clarifications is later and authoritative. Do not let the denial propagate into the promoted spec. |
| 5 | Hashtag options are add-only and never `disabled` | **Ratified.** The companion frame's toggle/disable behavior cannot satisfy `ID-17`/`ID-53`, which add five, click an already-selected row, and expect the error with still five chips. The design's dimming survives as styling only. |
| 6 | `Tiêu chuẩn cộng đồng` and the file-format error string have no design source | **Ratified and recorded as unauthored.** They appear in this contract and the RED suite but in none of the 26 spec rows, the frame's TEXT nodes, or the 57 test cases. They ship because the contract binds them; noted so nobody later mistakes them for spec-confirmed copy. |
| 7 | Image upload transport becomes a Server Action | **Ratified.** `clarifications.md` fixed *real upload*, not the transport. A browser-side Storage call cannot cross the RSC boundary as a prop without a Track A file importing Track B, and a Server Action puts MIME validation where the client cannot skip it. |
| 8 | A `security invoker` `create_kudos(...)` SQL function carries the multi-table write | **Ratified.** PostgREST cannot transact across `kudos`, `kudos_hashtags` and `kudos_attachments`, and there is deliberately no DELETE policy to compensate with. Doing it in one SQL function makes a forged `sender_id` unrepresentable rather than merely rejected. |
| — | `images.remotePatterns` for the Storage host | **Ratified.** Without it the first Storage-hosted attachment crashes `next/image` and takes all of `/kudos` down with it. Derived from `NEXT_PUBLIC_SUPABASE_URL`, shipped in phase 03. |

### Accepted limitations, recorded rather than fixed

- **`ID-46`/`ID-47` leave their created rows behind.** Real cleanup is unavailable by design — there
  is no DELETE policy, and putting a `service_role` key in the suite would be worse than a few extra
  rows. Accumulation is accepted; verified that `kudos-live-board.spec.ts` asserts no exact card
  count, so the F004 suite does not drift as rows pile up.
- **Provisioning the e2e user changes the authed sidebar** from the seeded viewer's five `25`s to
  that user's own zeroes. Checked: `K-18` is an anon test and asserts the row labels, not the values,
  so nothing breaks today. Worth remembering before anyone asserts sidebar numbers under a session.
- **The anonymous card has no automated coverage** anywhere in the 57 authored cases. Phase 05 proves
  it by hand and records the evidence; it is not left merely asserted.

### Copy plumbing (orchestrator, resolving phase 06's flag)

Phase 06 correctly flagged that `lib/kudos/compose-contract.ts` has no slot for field labels or
toolbar/link-dialog copy, and asked whether phases 08–11 should read `dictionary.kudosCompose`
directly or amend the frozen contract. **Neither: follow the F004 precedent.**

Components take a `copy` prop whose type is a **slice of `Dictionary["kudosCompose"]`**, imported as
a type from `@/lib/i18n/dictionaries`. That is exactly what the shipped board does —
`kudos-board.tsx` receives `copy: { eyebrow, sections, filters, card, toast }` and
`kudos-card-actions.tsx` types its own slice with
`Pick<Dictionary["kudos"]["card"], "copyLink" | "viewDetail">`. The route resolves the dictionary
once via `getPageContext()` and passes **resolved strings** down; no component imports the dictionary
module itself.

So `compose-contract.ts` stays frozen and does not duplicate copy types — copy is not part of the
Track A↔B data contract, it is presentation the route injects. Phases 08–11 each type their own
`copy` slice this way. Do not add a second source of truth for strings, and do not thread the whole
dictionary object through the tree.

### Wave-2 rulings (orchestrator, 2026-09-07c)

Three phases disclosed gaps in phase 01's frozen contract rather than quietly widening it. All three
were right to escalate; ruled on here.

**1. Field labels are the FORM's job, not the field components' (phase 08's flag).**
`compose-field.tsx` turned out to be error-text only — it renders `field-error-*` and nothing else —
so nothing currently renders the visible `Người nhận` / `Danh hiệu` labels the frame draws. The gap is
real. **Resolution: phase 11 (`compose-form.tsx`) renders each field's label**, reading
`dictionary.kudosCompose.labels.*` (phase 06 already authored them in both locales), and places it
beside the field component. This matches the design, where the label is a sibling of the input in a
two-column row rather than part of the control, and it avoids reopening phase 08's completed files.
Phase 08's components keep owning their input, its `aria-invalid` and its red-border state.

**2. Copy and callback shapes are NOT part of the frozen contract (phase 10's deviation — ratified).**
Phase 10 found `HashtagPickerProps` / `ImagePickerProps` insufficient — no slot for the hashtag
cap-error copy, and no upload-orchestration callbacks for the await-pending-uploads submit rule — so
it typed local `Props`/`Copy` interfaces while **reusing the frozen data types**. That is exactly the
right split and is consistent with `### Copy plumbing` above: the Track A↔B contract governs **data**,
while copy and component callbacks are presentation the form injects. `lib/kudos/compose-contract.ts`
stays frozen for data; its copy/props sketches are **advisory, not binding**. Phase 11 binds to the
components' own exported prop types.

**3. `uploadKudosImage` signals failure by throwing (phase 07's divergence — ratified).**
The frozen `UploadKudosImage` type is `(file: File) => Promise<UploadResult>` with no error slot, so
phase 07 rejects with an exported `UploadKudosImageError` carrying `.code: ComposeFieldErrorCode`
instead of returning `{error}`. Verified that `image-picker.tsx` already wraps the call in
`try/catch`, so Track A and Track B agree. Phase 11 and 12 must treat a rejected upload as the
error channel — do not look for a returned error field. Worth noting the honest trade-off: a typed
throw is a weaker contract than a returned result because the type system does not force the caller
to handle it, which is precisely why it is written down here rather than left to discovery.

### Correction to ratification item 6 (orchestrator, 2026-09-07d)

Phase 09 re-measured the toolbar row and found that **`Tiêu chuẩn cộng đồng` DOES have a real design
node** — `I520:11647;3053:11619` / `I520:11647;3053:11621`, parented by a `Button`. Ratification item
6 above claimed it had "no design source at all"; that was wrong, and phase 09 was right to push back.

Confirmed independently: the orchestrator's own earlier `query_by_type(TEXT)` on `ihQ26W78P2` returned
`I520:11647;3053:11621` at x 805–996, y 394–418 — exactly where the frame renders that link, on the
toolbar's right-hand side. The claim originated in `reports/design-source-analysis.md`, which was
written before the node tree had been queried in full; that section is stale and should not be
propagated.

**Item 6 is amended:** `Tiêu chuẩn cộng đồng` is **spec-confirmed and carries an `mm:` node id**. Only
the invalid-file-type error string remains genuinely unauthored — it appears in this contract and the
RED suite but in none of the 26 spec rows, the frame's TEXT nodes, or the 57 test cases, and it ships
because the contract binds it.

Worth stating plainly, since it has now happened three times in this commission: an implementer
disagreeing with the orchestrator on a measured fact has been correct every time. Measured design data
outranks any report's prose summary of it, including this file's.
