# Phase 01 — Foundation & integration contract

**Track:** Shared · **Owner:** `implementer` · **Depends:** — ·
**Effort:** 2.5h · **test_policy:** `e2e-red-first`

## Context Links

- [plan.md](plan.md) · [clarifications.md](clarifications.md) § Rich text, § Validation, § Images ·
  [test-contract.md](test-contract.md) (every hook name)
- [technical-spec.md](spec/viet-kudo/technical-spec.md) § 4.2 (the `KudosDoc` shape, verbatim), § 4.4 BR-002/BR-004, § 4.5 ALG-001
- [write-path study](reports/write-path-conventions.md) § 2 (no validation library — hand-rolled predicates), § 6 (JSON document model, ranked first)
- Patterns to copy: `lib/kudos/view-model.ts` (frozen-contract file header), `lib/kudos/derive.ts:1-9` (the zero-dependency, client-bundle-safe module comment)
- F004 precedent: [phase-01](../260906-1945-kudos-live-board/phase-01-foundation-and-integration-contract.md)

## Overview

**Priority:** P1 · **Status:** completed.

Three pure modules, nothing else. They are the only thing Track A and Track B both depend on, so
they are written once, first, and then frozen. No file in the repo imports them at the end of this
phase — the tree compiles exactly as it does today, which is what makes this phase risk-free and
un-rollback-able-by-accident.

## Key Insights

1. **The doc model is closed over six toolbar operations, and nothing more.** `paragraph`,
   `ordered-list-item`, `quote` as blocks; `bold`, `italic`, `strike`, `link`, `mention` as inline
   runs. No nesting. That shape is transcribed from `technical-spec.md § 4.2` — do not "improve" it.
2. **`body-editor` is a `<textarea>`, not a `contenteditable`.** `test-contract.md § Fields` permits
   either. The textarea wins on three counts: `bodyEditor.fill(...)` (used by 12 tests) is reliable
   on a controlled textarea and fragile on a React-managed contenteditable; the design's own body
   node is literally a textarea (`mm:I520:11647;520:9886`, `height:200px`, square top corners under
   the toolbar); and **no test asserts that formatting renders inside the editor** — ID-27/28/29
   assert only that `aria-pressed` exists, ID-30/32 only that the button exists. Formatting is
   therefore captured as **marks over the plain text** and rendered for real on the Live Board card
   (phase 05). The cost — no in-editor WYSIWYG preview — is a deliberate, recorded trade-off
   (§ Next Steps), not an oversight.
3. **Mark remapping must be dumb on purpose.** When the text changes, marks are shifted by a single
   common-prefix/common-suffix diff; a mark whose range collapses is dropped. Anything cleverer is
   an editor engine, which is not this commission.
4. **`parseKudosDoc` treats the database as untrusted input.** It is the read-side boundary for
   content that anonymous visitors see. It validates every block type, every run type, and every
   `link.href` scheme against an allow-list (`http:`, `https:`, `mailto:`), and returns `null` on
   anything unexpected so the caller can fall back to rendering the raw string as plain text. There
   is no sanitizer dependency in this repo and there will not be one — safety comes from only ever
   emitting known elements (phase 05).
5. **Component props live in the contract, not in the components.** Because 08, 09 and 10 run in
   parallel and 11 composes their output, the props interfaces must exist before any of them start.
   This is the artifact that lets the four Track A phases proceed without talking to each other.
6. **`compose-state.ts` carries the reducer so `compose-form.tsx` can stay under 200 lines.** The
   aggregate form state has nine fields; a component holding both the state machine and the JSX
   would breach the cap immediately.

## Requirements

**Functional:** the type surface behind FR-201–FR-207, FR-402, BR-002, BR-003, BR-004, DEC-001,
DEC-002, ALG-001. `isSubmitReady` encodes DEC-002 exactly (recipient AND title AND non-empty body
AND ≥1 hashtag). `buildPayload` produces the `ComposePayload` the action consumes.

**Non-functional:** each file ≤200 lines; **zero runtime imports** — no React, no
`next/*`, no `@/lib/supabase/*`, no `Intl` (the hydration-drift rule from `derive.ts:1-9`); pure
functions only, so both the server action and the client bundle can import them; no `any`.

## Architecture

```
lib/kudos/compose-contract.ts   types + caps + props interfaces  (imported by EVERY later phase)
        ├── KudosDoc / KudosBlock / KudosRun / MessageFormat
        ├── ComposeOptionsView { recipients: ComposeSunnerOption[]; hashtags: ComposeHashtagOption[] }
        ├── ComposePayload { receiverId, title, doc, plainText, hashtagIds, imageUrls, isAnonymous, anonymousName }
        ├── ComposeFieldErrors { recipient?, title?, body?, hashtag?, form? }  (error CODES, not copy)
        ├── CreateKudosState / CreateKudos / UploadKudosImage / UploadResult
        ├── MAX_HASHTAGS=5 · MAX_IMAGES=5 · ACCEPTED_IMAGE_MIME · ACCEPTED_LINK_SCHEMES
        └── props: RecipientPickerProps, TitleFieldProps, BodyEditorProps, HashtagPickerProps,
                   ImagePickerProps, AnonymousToggleProps, ComposeFieldProps, ComposeFormProps

lib/kudos/rich-text.ts          the document model
        ├── RichTextState { text; inline: InlineMark[]; blocks: BlockMark[] }
        ├── toggleInlineMark(state, kind, range, href?) · toggleBlockMark(state, kind, range)
        ├── insertMention(state, at, label, sunnerId) · isMarkActive(state, kind, range)
        ├── remapMarks(state, nextText)        ← prefix/suffix diff, drops collapsed marks
        ├── serializeToDoc(state): KudosDoc    ← split on "\n", slice runs at mark boundaries
        ├── docToPlainText(doc): string        ← the validation + fallback source
        └── parseKudosDoc(raw: string): KudosDoc | null   ← untrusted-input boundary

lib/kudos/compose-state.ts      the client state machine
        ├── ComposeState { recipient; title; body: RichTextState; hashtags; images; isAnonymous;
        │                  anonymousName; errors; imageError; hashtagError }
        ├── composeReducer(state, action)      ← one switch, exhaustive by TS
        ├── isSubmitReady(state): boolean      ← DEC-002, the ONLY definition of it
        └── buildPayload(state): ComposePayload
```

**Error codes, not copy.** `ComposeFieldErrors` values are `"required" | "tooMany" | "invalidType" |
"unknown"`. The dictionary (phase 06) maps them to `Không được để trống` / `Tối đa 5 hashtag` /
`Định dạng file không được hỗ trợ`. One string, one owner — the server never returns Vietnamese.

## Related Code Files

**Create:** `lib/kudos/compose-contract.ts` · `lib/kudos/rich-text.ts` · `lib/kudos/compose-state.ts`
**Modify:** none · **Delete:** none
**Read only:** `lib/kudos/view-model.ts`, `lib/kudos/derive.ts`, `spec/viet-kudo/technical-spec.md § 4.2`,
`test-contract.md`

## Implementation Steps

1. `lib/kudos/compose-contract.ts` — transcribe `KudosDoc`/`KudosBlock`/`KudosRun` from
   `technical-spec.md § 4.2` character for character. Add `MessageFormat = "plain" | "doc"`. Declare
   the caps as `const` (not magic numbers scattered later). `ACCEPTED_IMAGE_MIME` = `["image/jpeg",
   "image/png", "image/gif", "image/webp"]` — jpeg/png are the tested pair (ID-21/22), gif/webp are
   the honest remainder of "image types"; the rejected fixtures are `.pdf`, `.mp4`, `.txt`.
2. Declare `ComposeOptionsView`, `ComposePayload`, `ComposeFieldErrors`, `CreateKudosState`
   (`{ errors: ComposeFieldErrors } | { ok: true }`-shaped, mirroring `forms.md:147-161`), and the
   two action function types.
3. Declare one props interface per Track A leaf component, each taking its copy slice as a `copy`
   prop (never importing `Dictionary` deeply) and reporting upward through callbacks only.
4. `lib/kudos/rich-text.ts` — the model. `serializeToDoc` splits `text` on `\n` into blocks, assigns
   each line's type from `blocks` overlap (default `paragraph`), then cuts each line into runs at
   inline-mark boundaries. An empty line produces a `paragraph` with a single empty text run so
   round-tripping does not silently eat blank lines.
5. `parseKudosDoc` — `JSON.parse` inside `try`/`catch`, then structural validation: `blocks` is an
   array; every block `type` is one of the three; every run `type` is one of the three; `link.href`
   parses as a URL whose protocol is in `ACCEPTED_LINK_SCHEMES`; `mention.sunnerId` is a finite
   number. Any failure → `null`.
6. `lib/kudos/compose-state.ts` — the reducer. Actions: `setRecipient`, `setTitle`, `setBody`,
   `toggleMark`, `insertMention`, `addHashtag`, `removeHashtag`, `addImage`, `resolveImage`,
   `removeImage`, `setAnonymous`, `setAnonymousName`, `setErrors`, `setImageError`,
   `setHashtagError`. `addHashtag` at `MAX_HASHTAGS` sets `hashtagError` and returns the set
   unchanged (ID-17/53). `addImage` never dedupes — five copies of the same file are five images
   (ID-18/19 set the identical fixture five times).
7. `isSubmitReady` returns `recipient !== null && title.trim() !== "" &&
   docToPlainText-of-body.trim() !== "" && hashtags.length >= 1`.
8. `npm run typecheck && npm run lint`.
9. Prove the model without any UI: a throwaway script under the scratchpad that builds a state,
   toggles bold over a range, inserts a mention, serializes, `JSON.stringify`s, feeds the string
   back through `parseKudosDoc`, and asserts deep equality. Delete the script afterwards; the point
   is the round-trip, not a committed test.

## Todo List

- [x] `compose-contract.ts` — doc types transcribed from § 4.2, caps as consts, no magic numbers
- [x] `ComposeFieldErrors` carries **codes**, never Vietnamese copy
- [x] One props interface per Track A leaf component, all declared before 08/09/10 start
- [x] `rich-text.ts` — toggle / remap / insertMention / serialize / docToPlainText / parseKudosDoc
- [x] `parseKudosDoc` rejects a bad block type, a bad run type, and a `javascript:` href
- [x] `compose-state.ts` — reducer, `isSubmitReady` (DEC-002), `buildPayload`
- [x] `addHashtag` refuses the 6th with an error; `addImage` never dedupes
- [x] All three files ≤200 lines, zero runtime imports
- [x] `npm run typecheck && npm run lint` clean
- [x] Step 9 round-trip proven, scratch script removed

## Success Criteria

- The three files exist, compile, and are imported by **nothing** — `git stash` on this phase leaves
  the app byte-identical in behavior.
- A state carrying every mark kind survives `serializeToDoc` → `JSON.stringify` → `parseKudosDoc`
  unchanged.
- `parseKudosDoc('{"blocks":[{"type":"paragraph","runs":[{"type":"link","text":"x","href":"javascript:alert(1)"}]}]}')`
  returns `null`.
- `isSubmitReady` is false for each of the four one-field-missing states and true only when all four
  are present.
- No file exceeds 200 lines; `grep -n "import" lib/kudos/rich-text.ts lib/kudos/compose-state.ts`
  shows only type-only imports from `compose-contract.ts`.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| The doc shape drifts from `technical-spec.md § 4.2`, so the spec and the code disagree at promote | Med × High | Transcribed verbatim in step 1; § 4.2 is cited in the file header so a future editor sees the source |
| Mark remapping mangles marks on ordinary typing, corrupting stored content | **High** × Med | Deliberately dumb prefix/suffix diff; a collapsed mark is dropped, never re-anchored by guesswork. Documented in the file header as a known limitation |
| `parseKudosDoc` accepts a hostile `href` and phase 05 renders it | Low × **High** | Scheme allow-list in the parser AND in the renderer (phase 05) — two independent layers, per BR-004's own defense-in-depth reasoning |
| Props interfaces prove wrong once a component is real, forcing a contract edit mid-parallel-work | Med × Med | A contract change is escalated to the orchestrator, amended once, and both tracks notified — never patched inside a track (F004's rule, `view-model.ts:11-13`) |
| Somebody adds a runtime import here and breaks the client bundle | Low × Med | The `derive.ts:1-9` header comment is copied onto all three files; success criteria greps for it |

**Rollback:** delete the three files. Nothing imports them, so the tree is untouched.

## Security Considerations

- `parseKudosDoc` is the read boundary for content shown to **anonymous** visitors (`kudos_select_all`
  grants `anon` SELECT). It is written defensively, and it returns `null` rather than a partially
  trusted object.
- The `href` scheme allow-list lives here and is re-applied in the renderer. `javascript:`, `data:`
  and `vbscript:` never survive either layer.
- `ComposeFieldErrors` carries codes only, so a server error can never smuggle attacker-controlled
  text into the UI as "copy".
- Nothing in these modules touches Supabase, cookies or `auth`; there is no identity here to leak.
- `ComposePayload` deliberately has **no** `senderId` field. The actor is derived from the session
  (phase 07); the shape must not even offer the client a place to put one.

## Next Steps

04, 06, 07, 08, 09, 10 all unblock on this phase. Recorded for the orchestrator: **the editor shows
no inline formatting preview** — marks are stored and rendered on the board, but the textarea itself
displays plain text. The design draws a plain textarea and no test asserts otherwise, so this ships;
if a WYSIWYG preview is wanted it is a follow-up commission, not a defect of this one
(clarifications § Unresolved questions is the right home for it).
