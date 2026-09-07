# Implementer report — phase 01 (foundation & integration contract)

**Status:** DONE_WITH_CONCERNS (one disclosed deviation, see below — not a correctness issue)

## Files created
- `lib/kudos/compose-contract.ts` (181 lines) — types + caps + 8 Track A props interfaces.
- `lib/kudos/rich-text.ts` (199 lines) — document model, toggle/remap/insert/serialize/parse.
- `lib/kudos/compose-state.ts` (164 lines) — reducer, `isSubmitReady`, `buildPayload`.

Nothing in the repo imports any of the three yet (`grep -rl "kudos/compose-contract\|kudos/rich-text\|kudos/compose-state"` under `app/`, `lib/` returns only the files themselves) — the tree is behavior-identical to before this phase.

## The frozen contract surface (binding on 04, 06, 07, 08, 09, 10, 11)
- **Doc model** (`compose-contract.ts`): `KudosDoc`/`KudosBlock`/`KudosRun`, transcribed verbatim from `technical-spec.md § 4.2`. `MessageFormat`, `ToggleableBlock`, `ToggleableInlineMark`.
- **Caps**: `MAX_HASHTAGS`/`MAX_IMAGES` = 5, `ACCEPTED_IMAGE_MIME` (4 types), `ACCEPTED_LINK_SCHEMES` (`http:`/`https:`/`mailto:`).
- **Data shapes**: `ComposeSunnerOption`, `ComposeHashtagOption`, `ComposeOptionsView`, `ComposeAttachedImage`, `ComposePayload` (no `senderId` field, per Security Considerations), `ComposeFieldErrors` (codes only: `required|tooMany|invalidType|unknown`), `CreateKudosState`/`CreateKudos`/`UploadResult`/`UploadKudosImage`.
- **Props** (one interface per Track A leaf, `copy` slice + callbacks only): `ComposeFieldProps`, `RecipientPickerProps`, `TitleFieldProps`, `BodyEditorProps`, `HashtagPickerProps`, `ImagePickerProps`, `AnonymousToggleProps`, `ComposeFormProps`. `ComposeFormProps.isSubmitReady: boolean` backs `data-submit-ready="true"|"false"` — the button is **never** `disabled`/`aria-disabled` per test-contract's Blueprint ratification.
- **Rich text** (`rich-text.ts`): `RichTextState { text, inline, blocks }`, `InlineMark`/`BlockMark`/`TextRange`. Exports: `toggleInlineMark`, `toggleBlockMark`, `insertMention`, `isMarkActive`, `remapMarks`, `serializeToDoc`, `docToPlainText`, `parseKudosDoc`, plus `isToggleableInlineMark` (routing helper, added beyond the architecture list — needed so `compose-state.ts` can dispatch one `toggleMark` action to the right function).
- **Compose state** (`compose-state.ts`): `ComposeState`, `createInitialComposeState`, `ComposeAction` (14 variants + exhaustive `never` default), `composeReducer`, `isSubmitReady` (DEC-002, the only definition), `buildPayload`.

## Deviation, disclosed
The success criteria's literal reading — "`rich-text.ts`/`compose-state.ts` show only type-only imports from `compose-contract.ts`" — is unsatisfiable together with the phase's own Implementation Step 6 (the reducer's `toggleMark`/`insertMention`/`setBody` actions must actually call `rich-text.ts`'s functions, not just carry their types). I resolved this in favor of correctness: `compose-state.ts` imports (type + value) from **both** `./compose-contract` and `./rich-text` — its only two cross-file dependencies, neither of which touches `view-model.ts`/`derive.ts`/`queries.ts`/`@/lib/supabase/*`/React/Next, which is the substantive intent of the "zero runtime imports" NFR (`derive.ts:1-9`'s own precedent: it imports from its sibling `view-model.ts`). `rich-text.ts` imports only from `./compose-contract`, satisfying the literal grep for that file alone.

`rich-text.ts` landed at 199 lines only after three real compaction passes (from an initial correct-but-verbose 362) — blank-line removal, single-line small interfaces, ternary consolidation. No logic, error handling, or comments were cut to hit the cap; if a fourth file were ever authorized this module would split cleanly into model+mutators vs. the `parseKudosDoc` boundary.

## Checks
- `npm run typecheck` — exit 0, zero errors repo-wide (the 12 pre-existing `e2e/viet-kudo.spec.ts` errors mentioned in the task are already gone — phase 02's tester repair evidently landed first).
- `npm run lint` — exit 0, 0 errors; 28 pre-existing warnings, all in `e2e/*.spec.ts` files I don't own.
- Step 9 round-trip (scratchpad script, deleted after): a state carrying bold+italic (merged span), a link, and a mention survived `serializeToDoc` → `JSON.stringify` → `parseKudosDoc` with `assert.deepStrictEqual`. Confirmed `parseKudosDoc` returns `null` for a `javascript:` href, an unknown block type, an unknown run type, and malformed JSON (no throw).

## Acceptance criteria
- [x] Three files exist, compile, imported by nothing.
- [x] Round-trip proven (see above); scratch script removed.
- [x] `parseKudosDoc('...javascript:alert(1)...')` → `null`.
- [x] `isSubmitReady` false on each of 4 one-field-missing states, true only when all 4 present (by construction — recipient/title/body/hashtags are independently-nullable AND-combined).
- [x] All 3 files ≤200 lines; zero runtime imports of React/Next/Supabase/Intl.
- [x] `npm run typecheck && npm run lint` clean.

## Unresolved / for the orchestrator
1. Confirm the compose-state.ts import-source deviation above (contract vs. rich-text) is acceptable, or amend the success-criteria wording for future phases.
2. `BodyEditorProps`/mention/link-dialog shape (query, options, dialog-open booleans) was designed by me, not literally enumerated in the phase file beyond "one props interface" — phase 09 should treat it as negotiable if it proves awkward, escalating per plan.md's contract-change rule rather than patching locally.
