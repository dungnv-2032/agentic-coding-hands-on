# Phase 09 — Body editor: toolbar, mentions, link dialog

**Track:** A (presentational UI) · **Owner:** `momorph-ui-implementer` · **Depends:** 01, 06 ·
**Effort:** 3h · **test_policy:** `e2e-red-first`

## MoMorph refs:
- Viết Kudo: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/ihQ26W78P2
- Clarifications: plans/260907-0822-viet-kudo/clarifications.md
- testPolicy: e2e-red-first

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) — `rich-text.ts` is the model; this phase is only its UI · [phase-06](phase-06-i18n-kudos-compose-namespace.md)
- [test-contract.md](test-contract.md) § Fields, § Rich-text toolbar, § Mentions
- Tests this phase must satisfy: ID-5, ID-12, ID-13, ID-27, ID-28, ID-29, ID-30, ID-31, ID-32, ID-33, the `Body field: hint present` case
- [clarifications.md](clarifications.md) § Rich text (six operations, mention stores the sunner id, no character counter — **A4**), § The spec CSV … is stale (item `C` is the toolbar, `D.1` is a hint only)
- [design-source-analysis.md](reports/design-source-analysis.md) § 1 (six toolbar node ids), § 3 (the link dialog is a URL prompt, not a wrap-selection), § 8 (textarea 200px/min 120px, border `#998C5F`, radius `0 0 8px 8px`, padding-left 24px; icons 24×24 in 40px-tall buttons)
- [technical-spec.md](spec/viet-kudo/technical-spec.md) § 4.2 (the doc shape), § 4.5 ALG-001

## Overview

**Priority:** P1 · **Status:** completed.

The body field: a plain `<textarea>` under a six-button toolbar, plus a mention autocomplete and a
link dialog. All model logic already exists in `rich-text.ts` — this phase is markup, selection
plumbing and menu behavior, and it must not reimplement a single mark operation.

## Key Insights

1. **A `<textarea>`, not a `contenteditable` — decided in phase 01 § Key Insight 2.** Do not revisit
   it here. The consequence to internalize: **the editor shows plain text**; bold/italic/strike/quote
   /list/link are recorded as marks and rendered on the Live Board card (phase 05). `aria-pressed`
   on the toolbar is the user's only in-editor feedback, and no test asserts more.
2. **Mention detection reads the trailing token, not the caret.** `bodyEditor.fill("Cảm ơn @")`
   (ID-12) and `fill("Cảm ơn @Nguyen")` (ID-33) both set the value programmatically; relying on
   `selectionStart` after a programmatic fill is fragile. Match `/@([^\s@]*)$/` against the whole
   value: an empty capture opens the menu with every colleague, a non-empty capture filters it. The
   documented limitation — a mention can only be started at the end of the text — is deliberate and
   belongs in the file header.
3. **ID-13 reads `bodyEditor.textContent()` and asserts it is truthy.** For a React **controlled**
   `<textarea value={…} onChange={…}>` with no `defaultValue` prop, React assigns
   `node.defaultValue` on every update, and a textarea's `defaultValue` is reflected into its child
   text node — so `textContent` mirrors the value. This is load-bearing and it is a React
   implementation detail, so **step 1 of this phase is a five-minute probe** that confirms it before
   anything else is built. If it does not hold, the fallback is to render the value as the textarea's
   children (`<textarea value={v} onChange={…}>{v}</textarea>` is invalid; the real fallback is
   `defaultValue`-driven with a ref) — and the orchestrator is told, because it changes nothing in
   the contract but everything in this file.
4. **`aria-pressed` must always be present on bold/italic/strike.** ID-27/28/29 assert the attribute
   exists, not its value. Render `aria-pressed={isActive ? "true" : "false"}` — always a string,
   never `undefined`.
5. **Ordered-list, quote and link carry no `aria-pressed`** in the contract. Ordered-list and quote
   are block toggles applied to the lines the selection touches; link opens the dialog.
6. **The link dialog is a URL prompt.** Spec item `C.5`: *"Mở hộp thoại nhập URL … sau đó chèn liên
   kết vào vùng văn bản"*. So: click `toolbar-link` → `link-dialog` appears with `link-url-input` +
   confirm/cancel → confirm applies a `link` mark over the current selection (or inserts the URL as
   its own linked text when the selection is empty). ID-31 asserts only that the dialog and its input
   appear; the apply path still has to be real.
7. **The selection comes from the DOM, and only at the moment a toolbar button is pressed.** Keep a
   ref to the textarea and read `selectionStart`/`selectionEnd` inside the button handler. Do not
   mirror the selection into React state on every `selectionchange` — that is a re-render per
   keystroke for no gain.
8. **No character counter, and no `maxLength`.** A4 is explicit: `D.1`'s name promises a counter the
   frame does not draw and no test asserts, and no maximum is authored anywhere. Building either
   would be inventing a rule.
9. **The mention list is the same `recipients` array the recipient picker uses.** One server read
   (phase 07), two consumers. Do not add a second fetch.
10. **`mention-menu` and `mention-option` are separate hooks**, and the option locator is scoped
    inside the menu (`getByTestId("mention-menu").locator('[role="option"]')`), so the options must
    be descendants of the menu element.

## Requirements

**Functional:** FR-203 (body + hint), FR-204 (the six toolbar operations), FR-202's mention half
(ID-12/13/33, ALG-001 filtering), the link dialog (ID-31). A4 — no counter, no max length.

**Non-functional:** each file ≤200 lines; `"use client"`; `mm:{nodeId}` on arbitrary Tailwind
values; all copy and all aria-labels through the `copy` prop; zero reimplementation of
`rich-text.ts`; the dialog is keyboard-dismissible and focus lands in `link-url-input` when it
opens.

## Architecture

```
app/kudos/new/_components/kudos-body-editor.tsx      (~150 lines, "use client")
  props: BodyEditorProps { state: RichTextState, recipients, error, copy,
                           onChange(next: RichTextState), onMention(sunnerId, label) }
  ├─ <RichTextToolbar …/>                       (sibling component, below)
  ├─ <textarea data-testid="body-editor" ref value={state.text}
  │            placeholder={copy.placeholders.body}
  │            aria-invalid={error ? "true" : undefined}
  │            onChange → remapMarks(state, nextText) → onChange(...)>
  │            mm:I520:11647;520:9886 — h-[200px] min-h-[120px] border-[#998C5F] rounded-b-lg pl-6
  ├─ hint  data-testid="body-hint"  {copy.hints.body}
  └─ mention: /@([^\s@]*)$/ on state.text → <MentionMenu …/>

app/kudos/new/_components/rich-text-toolbar.tsx      (~95 lines, "use client")
  six buttons, mm:I520:11647;520:9881 / 662:11119 / 662:11213 / 662:10376 / 662:10507 / 662:10647
  toolbar-bold | toolbar-italic | toolbar-strike   → aria-pressed always rendered
  toolbar-ordered-list | toolbar-quote            → block toggles
  toolbar-link                                    → onOpenLinkDialog()
  each button: type="button" (a bare <button> inside a <form> submits it — this would fire
  createKudos on every formatting click), 24×24 icon in a 40px-tall box, aria-label from copy

app/kudos/new/_components/mention-menu.tsx           (~70 lines, "use client")
  data-testid="mention-menu" role="listbox"; children <li role="option" data-testid="mention-option">
  filter: recipients.filter(r => r.fullName.toLowerCase().includes(query.toLowerCase()))
  click → insertMention(state, …) via onSelect; menu closes

app/kudos/new/_components/link-dialog.tsx            (~70 lines, "use client")
  data-testid="link-dialog" role="dialog" aria-modal="true"
  data-testid="link-url-input"; confirm → onConfirm(url); cancel/Escape → onCancel()
  autofocus the input; confirm disabled until the URL parses with an allow-listed scheme
```

**Data flow:** textarea `onChange` → `remapMarks` → `onChange(nextState)` → phase 11's reducer →
back down as `state`. Toolbar press → read selection from the ref → `toggleInlineMark` /
`toggleBlockMark` → `onChange`. Mention pick → `insertMention` → `onChange`. Every transition goes
through `rich-text.ts`; this file computes nothing about marks itself.

## Related Code Files

**Create:** `app/kudos/new/_components/kudos-body-editor.tsx` · `rich-text-toolbar.tsx` ·
`mention-menu.tsx` · `link-dialog.tsx`
**Modify:** none · **Delete:** none
**Read only:** `lib/kudos/rich-text.ts`, `lib/kudos/compose-contract.ts`,
`app/_components/use-dismiss-on-outside.ts`, `app/kudos/_components/kudos-icons.tsx` (icon style
precedent)

## Implementation Steps

1. **The probe, before anything else.** Stand up a throwaway route or scratch page with a single
   controlled `<textarea value={v} onChange>`, drive it with
   `npx playwright test` or a one-off script that fills it and reads `textContent()`, and confirm the
   text comes back non-empty. Record the result in the phase report. If it fails, stop and report to
   the orchestrator before writing the editor — ID-13 depends on it.
2. `rich-text-toolbar.tsx`. Six buttons, `type="button"` on every one, icons drawn in the shipped
   `kudos-icons.tsx` style (inline SVG, `currentColor`, sized by className).
3. `kudos-body-editor.tsx`. Markup and testids first, then `onChange` → `remapMarks`, then the
   trailing-token mention rule, then the toolbar wiring through the selection ref.
4. `mention-menu.tsx` and `link-dialog.tsx`. Reuse `use-dismiss-on-outside.ts` for both.
5. Re-measure the toolbar row via MCP rather than trusting the report's 1006px figure — the modal is
   752px and clarifications § Unresolved question 6 flags that number explicitly. Cite what you
   measure.
6. `npm run typecheck && npm run lint`.
7. Props-contract read-through against `compose-contract.ts`, same as phase 08 step 7.

## Todo List

- [x] Step 1 probe run and recorded: a controlled textarea's `textContent` reflects its value
- [x] Six toolbar buttons, all `type="button"`, correct testids, `mm:` citations
- [x] `aria-pressed` always rendered on bold/italic/strike; absent on the other three
- [x] `body-editor` has the exact placeholder; `body-hint` matches copy exactly
- [x] No `maxLength`, no character counter anywhere (A4)
- [x] Mention menu opens on a trailing `@`, filters as the name continues, options inside the menu
- [x] Mention pick routes through `insertMention` and stores the sunner id
- [x] Link dialog opens with a focused `link-url-input`; confirm applies a scheme-checked link mark
- [x] Escape and outside-click dismiss both menus; `use-dismiss-on-outside` reused
- [x] Zero mark logic reimplemented — every operation calls `rich-text.ts`
- [x] Each file ≤200 lines; `npm run typecheck && npm run lint` clean
- [x] Toolbar row re-measured, 1006px not propagated

## Success Criteria

- The step-1 probe result is recorded in the phase report, either way.
- `grep -c "type=\"button\"" app/kudos/new/_components/rich-text-toolbar.tsx` returns 6.
- Each of `body-editor`, `body-hint`, `mention-menu`, `link-dialog`, `link-url-input` and the six
  `toolbar-*` testids appears exactly once per render; `mention-option` appears once per option and
  is a descendant of `mention-menu`.
- `grep -rn "toggleInlineMark\|toggleBlockMark\|insertMention\|remapMarks" app/kudos/new/_components/`
  shows only calls, never definitions.
- `grep -rn "maxLength\|maxlength" app/kudos/new/_components/kudos-body-editor.tsx` returns nothing.
- Props match `compose-contract.ts` exactly; typecheck and lint clean.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| A toolbar `<button>` without `type="button"` submits the form on every formatting click | **High** × High | Explicit in § Architecture, in the todo list, and greppable in the success criteria |
| ID-13's `textContent()` returns empty because React does not reflect the value | Med × **High** | Step 1 probes it before any code is written; failure escalates instead of being discovered in phase 12's 30-minute run |
| Mention detection built on `selectionStart` and broken by Playwright's programmatic `fill` | **High** × High | Trailing-token regex on the whole value; ID-12 and ID-33 both exercise it |
| The mark model gets reimplemented inside the component and drifts from `rich-text.ts` | Med × High | Success criteria greps for definitions; phase 01 owns the model |
| The editor's lack of a formatting preview is read as an unfinished feature | Med × Med | Recorded in phase 01 § Next Steps and repeated in insight 1; no test asserts otherwise and the frame draws a plain textarea |
| A `selectionchange` listener in React state causes a re-render per keystroke | Med × Low | Selection read from a ref, only inside button handlers |
| The 1006px toolbar measurement gets hard-coded and overflows the 752px modal | Med × Med | Step 5 re-measures; clarifications already flags the figure |
| `link-url-input` accepts a `javascript:` URL | Low × High | Confirm is gated on a parsed, allow-listed scheme; `rich-text.ts` and phase 05's renderer check again |

**Rollback:** delete the four files. Nothing imports them until phase 11.

## Security Considerations

- The link URL is user input that becomes an `href`. It is scheme-checked three times: here (confirm
  gating), in `parseKudosDoc` on read, and in the renderer (phase 05). This is the one field on the
  screen that can become executable markup if all three fail.
- Mentions store a sunner **id** plus the label captured at insert time; the label is text on
  re-display and is never used to build a link or a lookup.
- The mention list carries only the fields the recipient option shape carries — no email, no
  `auth_user_id`.
- No `dangerouslySetInnerHTML`, and the textarea's value never becomes markup on this screen.

## Next Steps

Phase 11 composes this with 08's and 10's output. Report the step-1 probe result to the orchestrator
regardless of outcome — it is the single riskiest assumption in the Track A half of the commission.
