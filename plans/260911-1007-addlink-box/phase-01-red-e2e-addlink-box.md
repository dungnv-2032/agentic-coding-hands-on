---
phase: 01
title: RED e2e — two fields, per-field errors, display-text insert
owner: tester
status: pending
feature: F005
test_policy: e2e-red-first
---

# Phase 01 — RED e2e

**Context:** `../spec/addlink-box/spec-delta.md` (FR-213..FR-219) · `../clarifications.md`
**MoMorph refs:** Addlink Box — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/OyDLDuSGEa
**Owns:** `e2e/viet-kudo.spec.ts`, `e2e/fixtures/viet-kudo-constants.ts`

## Goal

One durable screen-level RED proving the dialog the frame specifies does not exist yet. The RED
must be caused by real assertions about the dialog, never by a missing dependency, browser or
dev server.

## New hooks the tests may assume (phase 03 will provide)

`link-text-input`, `link-text-error`, `link-url-error`, `link-confirm`, `link-cancel`.
Frozen and unchanged: `toolbar-link`, `link-dialog`, `link-url-input`.

## Tests to add (continue the ID-nn numbering, currently at ID-60)

| ID | Asserts | FR |
|----|---------|----|
| ID-61 | dialog shows title `Thêm đường dẫn`, both inputs visible and empty, both labels present | 213/214/215 |
| ID-62 | clicking the `Nội dung` label focuses `link-text-input` | 213 |
| ID-63 | selecting body text then opening the dialog prefills `link-text-input` with it | 214 |
| ID-64 | `Lưu` with both fields empty → both errors visible, dialog still open | 216 |
| ID-65 | whitespace-only `Nội dung` → text error; 101 chars → text error; 1 char accepted | 214 |
| ID-66 | `invalid-url` then **blur** → url error without pressing `Lưu`; `www` → min-length error | 215 |
| ID-67 | valid text + `https://www.example.com` + `Lưu` → dialog closes, the text appears in `body-editor` | 216/217 |
| ID-68 | `link-cancel`, `Escape` and an outside click each close and discard; reopening shows empty fields | 218 |

ID-31 stays, and is extended to assert `link-text-input` alongside `link-url-input`.

## Constraints

- Every Vietnamese literal goes in `e2e/fixtures/viet-kudo-constants.ts`, imported by name.
- `page.getByTestId` only; `await page.goto(ROUTE)` at the top of each test, no `beforeEach`.
- Run: `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed`

## Done when

- The command above exits non-zero with failures that name the new assertions.
- `red-evidence.md` records `redCommand`, `redExitCode`, and each failing assertion verbatim.
- No previously-green test in the file was edited except ID-31's added line.
