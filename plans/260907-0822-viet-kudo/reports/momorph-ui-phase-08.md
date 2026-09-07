# Phase 08 — Form primitives (recipient, title, anonymous) — report

**Status:** implemented, not yet mounted (phase 11 composes). Typecheck 0 errors repo-wide,
lint 0 problems, all 4 files ≤200 lines (31/148/47/59), forbidden-literal grep returns nothing.

## Files

- `app/kudos/new/_components/compose-field.tsx` — the single `field-error-{recipient|title|body|hashtag}` source.
- `app/kudos/new/_components/recipient-picker.tsx` — autocomplete, listbox, keyboard nav.
- `app/kudos/new/_components/title-field.tsx` — `Danh hiệu` input + `title-hint`.
- `app/kudos/new/_components/anonymous-toggle.tsx` — checkbox + reveal-on-check name input.

## `mm:` node map

| Node | What |
|---|---|
| `I520:11647;520:9871` | recipient row, 672×56, 16px gap, flex row |
| `I520:11647;520:9873` | search input shell (componentId `186:2757`), flex-grow, border `#998C5F`, radius 8, padding 16/24, bg white |
| `I520:11647;520:9873;186:2760` | search placeholder text node, 16px/700/Montserrat, letter-spacing 0.15px |
| `zJzaC9GgXt` (companion) | **unpopulated** — design/dev status both empty via `get_frame`/`get_frame_node_tree`. Menu shell borrowed from shipped `kudos-filter-menu.tsx` (bg `#00070C`, border `#998C5F`, radius 8, 6px padding) per the phase's own instruction |
| `I520:11647;1688:10436/10437/10447` | title label(unused, see below)/input shell (514×56, same border/radius/padding as recipient)/hint (16px/700/Montserrat/`#999`, 0.15px, one node, two `\n`-separated lines) |
| `I520:11647;520:14099` / `;520:14097` / `;520:14095` | anonymous row (672×28, 16 gap) / checkbox box (24×24, border 1px `#999`, radius 4) / label text (22px/700/Montserrat, `#999`) |
| anonymous-name-input | **no node** — reveal-on-check field is unauthored (clarifications § Unresolved q4); shell borrowed from the measured recipient/title input |

`get_figma_image` was not called — not needed; every node resolved through `get_node`/`get_overview`/`get_frame`. Re-measured the input row per Step 5 (see below); did not encounter the suspicious 1006px figure — that was on the toolbar, out of this phase's scope.

## Hooks emitted (one instance each, verified by design — components render each exactly once)

`recipient-input`, `recipient-menu`, `recipient-empty`, `recipient-selected`, `title-input`,
`title-hint`, `anonymous-checkbox`, `anonymous-name-input`, `field-error-recipient`,
`field-error-title` (plus `field-error-body`/`field-error-hashtag`, generic via `ComposeField`'s
`field` union — ready for phases 09/10 to reuse).

## Props (exact match to `lib/kudos/compose-contract.ts`, step 7 read-through passed — no widened/added prop)

- `ComposeField({ field, error?, copy })` — `field: "recipient"|"title"|"body"|"hashtag"`; renders `null` when `error` is unset, else `<p data-testid="field-error-{field}" role="alert">{copy[error]}</p>`.
- `RecipientPicker({ copy: {placeholder, emptyLabel}, options, value, query, error?, onQueryChange, onSelect })` — self-contained open/close (`query.trim() !== ""`), local `dismissed`/`activeIndex` UI state only, filters `options` by `fullName.toLowerCase().includes(query.trim().toLowerCase())`.
- `TitleField({ copy: {placeholder, hintExample, hintUsage}, value, error?, onChange })`.
- `AnonymousToggle({ copy: {checkboxLabel, nameInputLabel}, checked, name, onToggle, onNameChange })`.

`use-dismiss-on-outside.ts` reused as-is (not rewritten) for the recipient menu's outside-pointerdown + Escape dismissal.

## Behavior notes for phase 11

- Menu open rule is independent of match count (Insight 1) — `recipient-empty` renders inside the open `recipient-menu` when 0 matches, never unmounts the menu.
- `aria-invalid` is `"true"` or `undefined` (never `"false"`) on both recipient-input and title-input.
- `recipient-picker.tsx` does NOT clear/update `query` after selection — phase 11 must supply a `query` value that reflects the selection (e.g. set local query state to `option.fullName` in its `onSelect` handler) for `recipientInput.inputValue()` to read as filled (ID-26). This component only guarantees the menu itself closes on select.
- `anonymous-name-input` is conditionally rendered (not CSS-hidden), matching `not.toBeVisible()` semantics.

## Unresolved / flagged for orchestrator

1. **No `label` text is threaded to any of the 4 components.** `RecipientPickerCopy`, `TitleFieldCopy`, and `AnonymousToggleCopy` (frozen in `compose-contract.ts`) carry no field-name string (`"Người nhận"`, `"Danh hiệu"`), and `ComposeFormCopy` has no `labels` object either, even though `Dictionary["kudosCompose"].labels` exists and the frame renders a visible label + `*` for every field. Since the frozen contract explicitly forbids widening props, none of the 4 components render a visible field-name label. No test case asserts one. Flagging so phase 11/orchestrator can decide whether `compose-form.tsx` renders the label text itself (it has full `ComposeFormCopy` access) or whether this is accepted as a scope gap.
2. Companion frames `zJzaC9GgXt` (recipient dropdown) and `5c7PkAibyD` (error state) are confirmed still unpopulated in MoMorph (`get_frame_node_tree` → "Frame metadata does not contain node tree information" for both) — matches clarifications § Unresolved question 3, nothing new learned.
3. Error text color (`#CF1322`) and the recipient-menu shell colors are borrowed (from `error-banner.tsx` and `kudos-filter-menu.tsx` respectively), not measured — both companion frames that would define them are empty. Noted per code-rules never-guess policy; these are the least-invented reasonable defaults given shipped precedent.
4. The `MM_MEDIA_Down` chevron icon on the search input (`I520:11647;520:9873;186:2761`) was not rendered — omitted rather than guessed, since no SVG asset was resolved for it and it carries no test hook.

**Status:** DONE
**Summary:** All four form-primitive components built to the frozen `compose-contract.ts` signatures, typecheck/lint clean, every `mm:` value measured live via MCP (two companion frames confirmed still empty). One real prop-contract gap flagged (no field-label text path) for the orchestrator/phase 11 rather than patched locally.
**Concerns/Blockers:** none blocking; see "Unresolved" item 1 above for a decision the orchestrator should make before/during phase 11.
