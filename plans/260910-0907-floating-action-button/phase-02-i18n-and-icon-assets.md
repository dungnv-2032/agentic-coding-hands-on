---
phase: 02
title: "i18n copy + pen icon asset"
status: complete
owner: momorph-ui-implementer
track: A
test_policy: e2e-red-first
effort: 0.5h
depends_on: [01]
momorph_screens: ["_hphd32jN2", "Sv7DFwBw1h"]
momorph_file_key: 9ypp4enmFmdK3YAFJLIu6C
---

# Phase 02 — i18n copy + pen icon asset

## Context Links

- [plan.md](plan.md) · [clarifications.md](clarifications.md) § "Resolved gaps" (reuse and extend
  `home.widget`; vi values are the drawn strings)
- [design/geometry.md](design/geometry.md) § "Icon colour — measured, and it corrects a shipped bug"
- [functional-spec](spec/floating-action-button/functional-spec.md) FR-001
- Phase that consumes this: [phase-03](phase-03-floating-widget-disclosure.md)

## Overview

- **Priority:** P2 — pure foundation, no visible behaviour on its own.
- **Status:** pending
- Extend the existing `home.widget` dictionary block with the four labels the menu needs, in both
  locales, and correct `widget-pen-icon.svg` from `fill="white"` to the measured `#00101A`.

## Key Insights

- `widget-pen-icon.svg` ships `fill="white"` and the shipped pill paints it on `#FFEA9E` — white
  on light yellow, near-invisible. Measured design says every mark in that row is `#00101A`. This
  feature owns the file, so the bug is fixed here rather than worked around in the component.
- `home.widget.standards` (`"Thể lệ SAA"`) and `writeKudos` (`"Viết kudos"`) **must not change**:
  `e2e/fixtures/the-le-constants.ts` `WIDGET_STANDARDS_LABEL` binds to the first, and phase 04
  keeps it as the menu item's accessible name.
- The drawn on-button labels (`Thể lệ`, `Viết KUDOS`) differ from those accessible names, so they
  are new keys, not renames. `"Thể lệ SAA"` contains the visible `"Thể lệ"`, so WCAG 2.5.3
  Label-in-Name still holds when the visible label and the `aria-label` differ.
- The kudos glyph `widget-saa-kudos-glyph.svg` is authored `20×19` and correctly `#00101A`
  already. It is **not** edited here — the 24×24 slot is a layout concern, resolved in phase 03.
- `public/images/rules/close-icon.svg` (24×24, white on the red button) is reused unchanged. Do
  not author a second copy.

## Requirements

Functional:
- FR-001: `Dictionary["home"]["widget"]` gains `trigger`, `menuStandards`, `menuWriteKudos`,
  `close` — typed in `dictionary.ts`, valued in `vi-home.ts` and `en-home.ts`.
- The pen glyph renders dark on the yellow pill in both collapsed and expanded states.

Non-functional:
- `npm run typecheck` and `npm run lint` exit 0 after the change.
- No key removed or renamed; additive only.

## Architecture

```
dictionary.ts (type)  ──┬── vi-home.ts (drawn vi strings)
                        └── en-home.ts (en equivalents)
                                   │
                          app/page.tsx passes dictionary.home.widget  (UNCHANGED)
                                   │
                          FloatingWidget (phase 03) reads all six keys
```

Key table:

| Key | vi | en | Used as |
|-----|----|----|---------|
| `writeKudos` *(existing)* | `Viết kudos` | `Write kudos` | `aria-label` of `fab-write-kudos` |
| `standards` *(existing)* | `Thể lệ SAA` | `SAA standards` | `aria-label` of `fab-standards` |
| `trigger` *(new)* | `Hành động nhanh` | `Quick actions` | `aria-label` of `fab-trigger` |
| `menuStandards` *(new)* | `Thể lệ` | `Standards` | visible label on `fab-standards` |
| `menuWriteKudos` *(new)* | `Viết KUDOS` | `Write kudos` | visible label on `fab-write-kudos` |
| `close` *(new)* | `Hủy` | `Cancel` | `aria-label` of the icon-only `fab-close` |

## Related Code Files

Modify:
- `lib/i18n/messages/dictionary.ts` — `home.widget` block (currently lines ~98-101), add four
  `string` fields.
- `lib/i18n/messages/vi-home.ts` — `widget` object (~line 77).
- `lib/i18n/messages/en-home.ts` — `widget` object (~line 74).
- `public/images/home/widget-pen-icon.svg` — the single `<path fill="white">` becomes
  `fill="#00101A"`. Nothing else in the file changes (`width/height/viewBox` stay `24`).

Create: none. Delete: none.

Explicitly NOT touched: `public/images/home/widget-saa-kudos-glyph.svg`,
`public/images/rules/close-icon.svg`, `app/page.tsx`, any file owned by phases 01/03/04.

## Implementation Steps

1. Add the four fields to the `widget` block in `dictionary.ts`, keeping the two existing ones.
2. Add the vi values verbatim as drawn (`Thể lệ`, `Viết KUDOS`, `Hủy`) plus `Hành động nhanh`.
3. Add the en equivalents in the same key order.
4. Change the pen path's `fill="white"` → `fill="#00101A"`.
5. `npm run typecheck` — the dictionary type change proves both locale files were updated.
6. `npm run lint`.

## Todo List

- [ ] `dictionary.ts` `home.widget` carries six keys
- [ ] `vi-home.ts` values match the drawn strings byte-for-byte
- [ ] `en-home.ts` has the four new equivalents
- [ ] `widget-pen-icon.svg` fill is `#00101A`, geometry untouched
- [ ] `npm run typecheck` exits 0
- [ ] `npm run lint` exits 0

## Success Criteria

- Both commands exit 0.
- `grep -c "Thể lệ SAA" lib/i18n/messages/vi-home.ts` still returns 1 — the existing accessible
  name survived.
- The SVG diff is one attribute; `git diff --stat` shows 1 insertion / 1 deletion on that file.

## Risk Assessment

| Risk | L×I | Countermeasure |
|------|-----|----------------|
| Renaming `standards`/`writeKudos` instead of adding keys → breaks `the-le` FUN_003 constant | M×H | Additive-only rule stated above; success criterion greps for the old value |
| Only one locale file updated | M×M | The `Dictionary` type makes typecheck fail loudly — step 5 is the gate |
| SVG edited beyond the fill (path rewritten, viewBox changed) | L×M | One-attribute diff enforced by the `git diff --stat` criterion |
| Someone "fixes" the kudos glyph file to 24×24 here | L×M | Explicitly out of ownership; sizing is a phase-03 layout decision |

## Security Considerations

- Copy and a static asset only: no user input, no auth surface, no data access.
- No secret, token or environment value is introduced; nothing here reaches Supabase.
- SVG is hand-edited on an existing trusted asset — no third-party file is imported, so no
  script-bearing SVG risk.

## Next Steps

- Unblocks phase 03 (the component cannot typecheck without these keys).
- The RED from phase 01 stays red; this phase does not attempt to move it.
