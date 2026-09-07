# Phase 08 — Form primitives: field shell, recipient, title, anonymous

**Track:** A (presentational UI) · **Owner:** `momorph-ui-implementer` · **Depends:** 01, 06 ·
**Effort:** 2.5h · **test_policy:** `e2e-red-first`

## MoMorph refs:
- Viết Kudo: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/ihQ26W78P2
- Dropdown list người nhận (companion, no authored spec): https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/zJzaC9GgXt
- Lỗi chưa điền đủ thông tin (companion, no authored spec): https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/5c7PkAibyD
- Clarifications: plans/260907-0822-viet-kudo/clarifications.md
- testPolicy: e2e-red-first

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (props interfaces, reducer) · [phase-06](phase-06-i18n-kudos-compose-namespace.md) (copy)
- [test-contract.md](test-contract.md) § Fields, § Anonymous, § Validation
- Tests this phase must satisfy: ID-4, ID-6, ID-8, ID-9, ID-10, ID-25, ID-26, ID-41, ID-42, ID-43, ID-44, the `Title field` case, plus the error slots for ID-7/11/14/50/51/52/56
- [design-source-analysis.md](reports/design-source-analysis.md) § 1 (copy + node ids), § 8 (measured CSS — input border `#998C5F`, radius 8px, padding 16px/24px, white background; checkbox 24×24, border `#999`, radius 4px)
- [technical-spec.md](spec/viet-kudo/technical-spec.md) § 3.1 DEC-001, § 4.5 ALG-001
- Patterns to copy: `app/kudos/_components/kudos-filter-menu.tsx` (listbox/option markup already shipped), `app/_components/use-dismiss-on-outside.ts` (outside-click dismissal, already shipped — reuse, do not rewrite)

## Overview

**Priority:** P1 · **Status:** completed.

Four leaf components: the shared label+required+error row, the recipient autocomplete, the title
field with its two hint lines, and the anonymous checkbox with its reveal-on-check name input. Each
is a client component that owns no aggregate state — every value and every callback arrives through
the props interface phase 01 froze.

## Key Insights

1. **`recipient-menu` must be visible even with zero matches.** ID-9 fills `@#$%^&`, asserts the menu
   `toBeVisible()` **and** asserts zero `role="option"` children. So the menu opens whenever the query
   is non-empty, and it contains `recipient-empty` instead of options when nothing matches. A menu
   that unmounts on no-match fails ID-9.
2. **Whitespace is trimmed before matching, not before display.** ID-10 fills `"  Nguyễn  "` and
   expects matches. The query is `value.trim().toLowerCase()` for comparison; the input keeps what the
   user typed (ALG-001).
3. **Picking an option fills the input and closes the menu** (ID-26), and `recipient-selected` renders
   the chosen person. Three separate observable effects from one click — all three are asserted.
4. **`aria-invalid` is a string, and only present when invalid.** ID-7/50 assert
   `toHaveAttribute("aria-invalid", "true")`. Render `aria-invalid={error ? "true" : undefined}` so
   the attribute is absent rather than `"false"` when valid — an always-present `"false"` would pass
   these tests but lies to a screen reader.
5. **`title-hint` is ONE element containing BOTH lines.** The `Title field` case reads
   `titleHint.textContent()` and asserts it contains both `Ví dụ: …` and `Danh hiệu sẽ hiển thị …`.
   Two sibling elements each carrying the testid would make the locator strict-mode ambiguous.
6. **The anonymous name input must not merely be hidden — it must be absent or `hidden`.** ID-43/44
   assert visible/not-visible. Conditional rendering (`{isAnonymous && <input …/>}`) is the simplest
   correct answer and also keeps an unchecked form from submitting a stale name.
7. **The checkbox is unchecked by default** (ID-6) and is a real `<input type="checkbox">`, so
   `toBeChecked()`/`not.toBeChecked()` work natively.
8. **The recipient dropdown's design frame has no authored spec** (`zJzaC9GgXt`, 0 items). Its
   behavior comes from ID-8/9/10/25/26 and its visual shell from the search input's own measured
   values (§ 8). Every borrowed value carries its `mm:` id; nothing is invented silently.
9. **No `<label htmlFor>` collisions.** Four fields, four ids, all prefixed `compose-` — the page also
   renders `HomeHeader`, which has its own inputs.
10. **Outside-click dismissal is already solved in this repo.** `use-dismiss-on-outside.ts` ships and
    is used by the account menu and the filter menus. Import it; do not write a second one (DRY).

## Requirements

**Functional:** FR-201 (recipient autocomplete), FR-202 (ALG-001 filtering), the `Danh hiệu` field
(A2), FR-205/DEC-001 (anonymous reveal), and the four `field-error-*` slots that ID-56 lights up
simultaneously.

**Non-functional:** each file ≤200 lines; `"use client"` where interactivity demands it; every
arbitrary Tailwind value carries `mm:{nodeId}`; all copy through the `copy` prop, never a literal;
keyboard-reachable — `role="listbox"`/`role="option"`, `aria-expanded` on the input, Escape closes
the menu, Enter picks the active option.

## Architecture

```
app/kudos/new/_components/compose-field.tsx        (~55 lines, "use client" not needed)
  ComposeField({ label, required, htmlFor, error, errorTestId, children })
    <div>
      <label htmlFor>{label}{required && <span aria-hidden className="text-red-…">*</span>}</label>
      {children}
      {error && <p data-testid={errorTestId} className="…">{error}</p>}
    </div>
  ← the ONLY place a field-error element is created, so all four error slots are one code path

app/kudos/new/_components/recipient-picker.tsx     (~120 lines, "use client")
  props: RecipientPickerProps { recipients, selected, query, error, copy,
                                onQueryChange, onSelect }
    input   data-testid="recipient-input"  placeholder={copy.placeholders.recipient}
            role="combobox" aria-expanded aria-controls aria-invalid={error?"true":undefined}
            className: red border when error (ID-7/50), else mm:I520:11647;520:9873 border #998C5F
    menu    data-testid="recipient-menu" role="listbox"  — rendered whenever query.trim() !== ""
            matches.length > 0 ? matches.map(<li role="option" data-…>)
                               : <p data-testid="recipient-empty">{copy.recipientEmpty}</p>
    chosen  data-testid="recipient-selected"  (avatar + name, shown when selected !== null)
    filter  recipients.filter(r => r.fullName.toLowerCase().includes(query.trim().toLowerCase()))

app/kudos/new/_components/title-field.tsx          (~55 lines)
  input  data-testid="title-input"  placeholder={copy.placeholders.title}
  hint   data-testid="title-hint" — ONE element, both lines as two <span className="block">

app/kudos/new/_components/anonymous-toggle.tsx     (~60 lines, "use client")
  checkbox  data-testid="anonymous-checkbox"  type=checkbox  + label text
  name      {checked && <input data-testid="anonymous-name-input" … />}   ← DEC-001
```

**Data flow:** `compose-form` (phase 11) holds the reducer state → passes `query`/`selected`/`error`
down → each component reports upward through its `on*` callbacks → the reducer updates → re-render.
No component reads or writes another's state, which is what lets 08, 09 and 10 be built in parallel.

## Related Code Files

**Create:** `app/kudos/new/_components/compose-field.tsx` · `recipient-picker.tsx` ·
`title-field.tsx` · `anonymous-toggle.tsx`
**Modify:** none · **Delete:** none
**Read only:** `lib/kudos/compose-contract.ts`, `lib/i18n/messages/dictionary.ts`,
`app/kudos/_components/kudos-filter-menu.tsx`, `app/_components/use-dismiss-on-outside.ts`

## Implementation Steps

1. `compose-field.tsx` first — every other component in this phase and in 10 wraps itself in it, so
   the four error testids come from one place.
2. `recipient-picker.tsx`. Order the work: markup and testids, then the filter (ALG-001), then the
   open/close rule from insight 1, then keyboard handling, then the error styling.
3. `title-field.tsx` — trivial, but get the single `title-hint` element right (insight 5).
4. `anonymous-toggle.tsx` — conditional render, not CSS hiding.
5. Re-measure the visual values from the frame rather than trusting the report's suspicious 1006px
   toolbar note (clarifications § Unresolved question 6 applies to the toolbar, but re-measure the
   input row too while the MCP session is open). Cite each with `mm:`.
6. `npm run typecheck && npm run lint`.
7. These components cannot render until phase 11 composes them, so verification here is
   typecheck + lint + a **props-contract read-through**: confirm each component's signature matches
   its interface in `compose-contract.ts` exactly, with no widened or added prop. A mismatch found
   now costs minutes; found in phase 11 it costs a re-dispatch.

## Todo List

- [x] `compose-field.tsx` is the single source of the four `field-error-*` elements
- [x] `recipient-input` has the exact placeholder, `role="combobox"`, `aria-expanded`
- [x] `aria-invalid="true"` only when invalid, absent otherwise
- [x] Red border on error (ID-7/50)
- [x] `recipient-menu` visible for any non-empty query, with `recipient-empty` when no match (ID-9)
- [x] Filtering trims and case-folds the query (ID-10), matching on substring (ALG-001)
- [x] Picking fills the input, closes the menu, renders `recipient-selected` (ID-26)
- [x] Escape closes; Enter picks; `use-dismiss-on-outside` reused, not rewritten
- [x] `title-hint` is one element containing both hint lines
- [x] `anonymous-checkbox` unchecked by default; name input conditionally **rendered** (ID-43/44)
- [x] Every arbitrary Tailwind value carries `mm:{nodeId}`; all copy via the `copy` prop
- [x] Each file ≤200 lines; `npm run typecheck && npm run lint` clean
- [x] Step 7 props-contract read-through done, no signature drift

## Success Criteria

- Each component's props exactly match its `compose-contract.ts` interface.
- Every testid this phase owns appears exactly once per rendered instance:
  `recipient-input`, `recipient-menu`, `recipient-empty`, `recipient-selected`, `title-input`,
  `title-hint`, `anonymous-checkbox`, `anonymous-name-input`, `field-error-recipient`,
  `field-error-title`, `field-error-body`, `field-error-hashtag`.
- `grep -n "Không được để trống\|Tìm kiếm\|Dành tặng" app/kudos/new/_components/` returns nothing —
  no hard-coded copy.
- No file exceeds 200 lines; typecheck and lint clean.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| `recipient-menu` unmounts when there are no matches, failing ID-9 | **High** × High | Insight 1 is called out twice; the open rule is `query.trim() !== ""`, independent of match count |
| `aria-invalid="false"` always rendered — tests pass but accessibility is wrong | Med × Med | `undefined` when valid, stated in insight 4 and in the todo list |
| Two elements share `title-hint`, making the locator strict-mode ambiguous | Med × High | One element, two `<span className="block">` children |
| The name input is CSS-hidden rather than unmounted, so a stale name submits | Med × Med | Conditional render; the reducer also clears `anonymousName` on uncheck (phase 01) |
| A second outside-click hook is written, duplicating shipped code | Med × Low | `use-dismiss-on-outside.ts` named in § Context Links and the todo list |
| Visual values propagated from the report's suspicious measurements | Med × Med | Step 5 re-measures via MCP; clarifications § Unresolved question 6 already warns about the 1006px figure |
| Props drift from the frozen contract while 09/10 build in parallel | Med × High | Step 7's read-through; any real change is escalated to the orchestrator, never patched locally |

**Rollback:** delete the four files. Nothing imports them until phase 11.

## Security Considerations

- The recipient list arrives as props from a server read (phase 07) and carries only `id`,
  `fullName`, `avatarUrl`, `department` — no `auth_user_id`, no email. Do not add fields to the
  option shape.
- The chosen recipient travels as an **id**, and the server re-checks that it exists; the displayed
  name is never trusted as the identity.
- `anonymous-name-input` is free text rendered later as text only (phase 05); it is trimmed and
  capped in the reducer and again in the action.
- No `dangerouslySetInnerHTML`, no `href` built from user input anywhere in this phase.

## Next Steps

Phase 11 composes these four with 09's and 10's output. Report to the orchestrator if any props
interface needed a change, so 09/10/11 are notified in the same breath.
