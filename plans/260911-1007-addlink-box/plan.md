---
title: "Addlink Box — the authored two-field link dialog (E09)"
description: "Replace the unauthored one-field link prompt on /kudos/new with the designed Thêm đường dẫn dialog: Nội dung + URL, per-field errors on save, and a display-text insert into the body."
status: completed
priority: P2
effort: 4h
branch: feat/addlink-box
tags: [momorph, F005, viet-kudo, ui, e2e]
created: 2026-09-11
work_type: feature
spec: docs/features/F005_VietKudo/
spec_delta: plans/260911-1007-addlink-box/spec/addlink-box/spec-delta.md
---

# Addlink Box (MoMorph `OyDLDuSGEa`)

One dialog, its validation module, one new rich-text primitive, and their tests. E09
(`link-dialog`) shipped as an explicitly **unauthored** one-field URL prompt — its own doc comment
says so. This frame is the design that was missing: two labelled fields, errors that speak, and a
`Nội dung` value that becomes the link's visible text.

- Spec delta (requirement source, frozen): `spec/addlink-box/spec-delta.md` — FR-213..FR-219, BR-006
- Clarifications (resolved, do not re-open): `clarifications.md`
- MoMorph: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/OyDLDuSGEa
- testPolicy: `e2e-red-first`

## Phases

| # | Phase | Owner | Status | Depends on |
|---|-------|-------|--------|-----------|
| 01 | [RED e2e — two fields, errors, insert](phase-01-red-e2e-addlink-box.md) | tester | **done** — valid RED, exit 1, 9 assertion failures ([evidence](evidence/red-evidence.md)) | — |
| 02 | [Engine — insertLink, validation, contract](phase-02-engine-insert-link-and-validation.md) | implementer | **done** (`ae36f47`) | 01 (valid RED) ✓ |
| 03 | [UI — the authored dialog](phase-03-ui-authored-link-dialog.md) | momorph-ui-implementer | **done** + rework (focus trap, focus-visible border, field extraction) | 02 |
| 04 | [GREEN + visual evidence](phase-04-green-and-visual-evidence.md) | tester | **done** — 73 passed, exit 0 ([evidence](evidence/green-evidence.md)) | 03 |

## Data flow

```
toolbar-link click
  └─ use-body-editor-controller: capture the live textarea selection ONCE, at open
       ├─ linkDialogOpen = true
       └─ linkDialogInitialText = selected substring (or "")
            └─ LinkDialog (two controlled fields, local state, unmounts when closed)
                 ├─ blur on URL      → validateLinkUrl      → url error
                 └─ click Lưu        → validateLinkFields   → { text?, url? } errors
                      ├─ any error   → render them, stay open, insert nothing
                      └─ clean       → onConfirmLink(text, href)
                           └─ dispatch { type: "insertLink", range, text, href }
                                └─ rich-text insertLink: splice text over range,
                                   drop marks overlapping it, add the link mark
```

The selection is read at **open**, not at confirm: focusing the dialog's inputs leaves the
textarea's `selectionStart/End` intact today only by luck, and the new dialog has two inputs to
move focus between. Capturing once removes the luck.

## Key decisions

1. **This is an F005 amendment, not a new feature code.** The frame is the authored design for an
   existing component. No `F###` reservation.
2. **`compose-contract.ts` IS amended** — once, deliberately, by phase 02, which owns the file.
   `onConfirmLink` gains the text argument and `BodyEditorProps` gains `linkDialogInitialText`.
   The frame's second field cannot be expressed through the existing props, and the contract's own
   header says an amendment is the orchestrator's call, never a track's in-place patch. `KudosRun`,
   `KudosDoc` and `ACCEPTED_LINK_SCHEMES` stay frozen.
3. **Validation moves into `lib/kudos/validate-link.ts`**, a pure module. Scheme checking already
   exists in three deliberate defense-in-depth places; this adds no fourth copy — the dialog's
   check simply stops being an inline one-off and becomes importable, so the e2e expectations and
   the component read one rule set.
4. **`insertLink` is a new rich-text primitive**, modelled on `insertMention`. `toggleInlineMark`
   returns unchanged state for an empty range, so a link with no selection is a silent no-op today;
   with a display-text field that is no longer acceptable.
5. **Frozen hooks stay frozen.** `test-contract.md` forbids changing `toolbar-link`, `link-dialog`,
   `link-url-input`. New hooks only: `link-text-input`, `link-text-error`, `link-url-error`,
   `link-confirm`, `link-cancel`.
6. **The disabled-confirm gate is removed.** It is the reason 12 of the frame's FUNCTION test cases
   could never pass — a disabled button fires no click and prints no reason.

## File ownership

| Phase | Owns (writes) | Reads only |
|---|---|---|
| 01 | `e2e/viet-kudo.spec.ts`, `e2e/fixtures/viet-kudo-constants.ts` | the spec delta, the current dialog |
| 02 | `lib/kudos/rich-text.ts`, `lib/kudos/compose-state.ts`, `lib/kudos/compose-contract.ts`, `lib/kudos/validate-link.ts` (new) | phase 01's tests |
| 03 | `app/kudos/new/_components/link-dialog.tsx`, `kudos-body-editor.tsx`, `use-body-editor-controller.ts`, `lib/i18n/messages/{dictionary,vi-kudos-compose,en-kudos-compose}.ts` | phase 02's contract |
| 04 | `e2e/capture-addlink-box-visual.spec.ts`, `playwright.config.ts`, `evidence/*` | everything above |

No two phases write the same file.

## Done when

- `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed` exits 0, including ID-31 and
  every new ID, and no previously-green test turns red.
- `npm run typecheck` and `npm run lint` exit 0.
- Every file touched stays under 200 lines.
- Every visual value in the dialog carries an `mm:` node comment, or is flagged unauthored.
- Three screenshots captured at 1440px: empty, both-fields-invalid, filled-and-valid.

## Rollback

Every change is additive or local to the link path. `git revert` of the feature commit restores
the one-field dialog; no migration, no data, no route to unwind.
