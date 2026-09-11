---
phase: 03
title: UI — the authored Thêm đường dẫn dialog
owner: momorph-ui-implementer
status: pending
feature: F005
depends_on: [02]
test_policy: e2e-red-first
---

# Phase 03 — UI

**MoMorph refs:** Addlink Box — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/OyDLDuSGEa
**Clarifications:** `../clarifications.md` · **Spec:** `../spec/addlink-box/spec-delta.md`
**Owns:** `app/kudos/new/_components/link-dialog.tsx`, `kudos-body-editor.tsx`,
`use-body-editor-controller.ts`, `lib/i18n/messages/{dictionary,vi-kudos-compose,en-kudos-compose}.ts`

## Goal

Rebuild `LinkDialog` as the frame draws it. Read every visual value from MCP design data
(`get_node` on the frame's children) and cite it as `mm:NODE-ID`; flag anything the design does not
carry as unauthored rather than inventing it silently.

- Title `Thêm đường dẫn` (item A) · two rows, label LEFT of input (items B.1/B.2, C.1/C.2).
- `Nội dung` label is a real `<label htmlFor>` so clicking it focuses the input (item B.1).
- Buttons at the bottom (item D): `Hủy` narrow + border + X icon; `Lưu` filling the rest,
  `#FFEA9E`, link icon. Reuse `IconLink` from `app/kudos/_components/kudos-icons.tsx`.
- `Lưu` is **never** `disabled`. Click → `validateLinkFields` → render `link-text-error` /
  `link-url-error` and stay open, or call `onConfirmLink(text, href)`.
- URL field validates on blur as well (item C).
- Controller: capture the textarea's selected substring at open into `linkDialogInitialText`;
  `onConfirmLink` dispatches `insertLink` with the range captured at the same moment.

## Constraints

- Error copy comes from the dictionary — all three i18n files move in lockstep, `// Unauthored`
  comments on any string the design does not name.
- Frozen hooks unchanged: `toolbar-link`, `link-dialog`, `link-url-input`.
- Every file under 200 lines; extract a sibling rather than overflow.
- Do NOT edit `e2e/*` or `lib/kudos/*` — phases 01 and 02 own them.

## Done when

- `npm run typecheck` and `npm run lint` exit 0.
- Handoff names each `mm:` node used and every unauthored value.
