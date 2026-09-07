---
title: "Viết Kudo (/kudos/new) — compose screen over the first write path"
description: "Replace the /kudos/new placeholder with the guarded compose form, the repo's first multi-table write, real Storage uploads and a rich-text document model."
status: completed
priority: P1
effort: 27h
branch: feat/award-system-screen
tags: [kudos, momorph, supabase, storage, rich-text, e2e-red-first, screen]
created: 2026-09-07
work_type: feature
spec: docs/features/F005_VietKudo/
system_doc_drafts:
  - plans/260907-0822-viet-kudo/spec/system/architecture.md
  - plans/260907-0822-viet-kudo/spec/system/permissions.md
test_policy: e2e-red-first
---

# Viết Kudo — implementation blueprint

**Goal** Replace the `ComingSoon` body at `app/kudos/new/page.tsx` with the real compose screen (MoMorph `ihQ26W78P2`, frame `520:11602`), behind the first auth guard since F001, over the repo's first multi-table write.
**Done when** `npx playwright test e2e/viet-kudo.spec.ts e2e/route-guard.spec.ts --reporter=list` exits 0 with nothing weakened and every shipped suite stays green (§ Blast radius).
**Settled, not re-openable:** [clarifications](clarifications.md) · [test-contract](test-contract.md) · [spec](spec/viet-kudo/technical-spec.md) · [write-path](reports/write-path-conventions.md) + [design](reports/design-source-analysis.md) studies · [RED gate](reports/tester-red-gate.md) · [F004](../260906-1945-kudos-live-board/plan.md)
**Three contract conflicts were found and resolved — read [phase-02 § Key Insights](phase-02-red-gate-defect-repair.md) before touching a test file:** ID-48 vs ID-56 are irreconcilable, six assertions are unpassable as written, F004's K-21 contradicts the new guard.

## Phases
`01+02+03` start together → `04→05` and `07` (Track B) run **concurrently** with `06→{08|09|10}→11` (Track A) → all converge on `12`. 08, 09, 10 are mutually independent.

| # | Phase | Status | Track | Owner | Depends | Effort |
|---|-------|--------|-------|-------|---------|--------|
| 01 | [Foundation & integration contract](phase-01-foundation-and-integration-contract.md) | completed | Shared | `implementer` | — | 2.5h |
| 02 | [RED-gate defect repair](phase-02-red-gate-defect-repair.md) | completed | Test | `tester` | — | 1.5h |
| 03 | [Schema, RLS, Storage, image host](phase-03-schema-rls-storage-and-image-host.md) | completed | B | `implementer` | — | 2h |
| 04 | [Board contract & read mapping](phase-04-board-contract-and-read-mapping.md) | completed | B | `implementer` | 01, 03 | 2h |
| 05 | [Board surface: doc + anonymity](phase-05-board-surface-doc-and-anonymity.md) | completed | A | `momorph-ui-implementer` | 04 | 1.5h |
| 06 | [i18n `kudosCompose` namespace](phase-06-i18n-kudos-compose-namespace.md) | completed | A | `momorph-ui-implementer` | 01 | 1h |
| 07 | [Write path: validation & actions](phase-07-write-path-validation-and-actions.md) | completed | B | `implementer` | 01, 03, 04 | 3.5h |
| 08 | [Form primitives: recipient, title, anonymous](phase-08-form-primitives-recipient-title-anonymous.md) | completed | A | `momorph-ui-implementer` | 01, 06 | 2.5h |
| 09 | [Body editor: toolbar, mentions, link](phase-09-body-editor-toolbar-mentions-link.md) | completed | A | `momorph-ui-implementer` | 01, 06 | 3h |
| 10 | [Hashtag & image pickers](phase-10-hashtag-and-image-pickers.md) | completed | A | `momorph-ui-implementer` | 01, 06 | 2.5h |
| 11 | [Compose form assembly](phase-11-compose-form-assembly.md) | completed | A | `momorph-ui-implementer` | 08, 09, 10 | 2.5h |
| 12 | [Integration, route guard & GREEN gate](phase-12-integration-route-guard-and-green-gate.md) | completed | Shared | `implementer` | 02, 05, 07, 11 | 2.5h |

## File ownership — disjoint by file, never by glob
| Phase | Owns (write) |
|---|---|
| 01 | `lib/kudos/{compose-contract,compose-state,rich-text}.ts` |
| 02 | `e2e/viet-kudo.spec.ts`, `e2e/kudos-live-board.spec.ts`, `e2e/fixtures/viet-kudo-constants.ts`, `test-contract.md` |
| 03 | `supabase/migrations/20260907*_viet_kudo_write_path.sql`, `next.config.ts` |
| 04 | `lib/supabase/database.types.ts`, `lib/kudos/{view-model,queries,board-data}.ts` |
| 05 | `app/kudos/_components/{kudos-message-body,anonymous-sender-chip,kudos-card}.tsx` |
| 06 | `lib/i18n/messages/{dictionary,vi,en,vi-kudos-compose,en-kudos-compose}.ts` |
| 07 | `lib/kudos/{validate-compose,compose-options}.ts`, `app/kudos/new/_actions/{create-kudos,upload-kudos-image}.ts` |
| 08 | `app/kudos/new/_components/{compose-field,recipient-picker,title-field,anonymous-toggle}.tsx` |
| 09 | `app/kudos/new/_components/{kudos-body-editor,rich-text-toolbar,mention-menu,link-dialog}.tsx` |
| 10 | `app/kudos/new/_components/{hashtag-picker,image-picker}.tsx` |
| 11 | `app/kudos/new/_components/{compose-form,compose-actions}.tsx` |
| 12 | `app/kudos/new/page.tsx`, `proxy.ts` |

**`app/kudos/new/page.tsx` belongs to phase 12 alone** — the data-fetch + action-wiring seam, so no Track A file imports a Track B module. Until 12 the route keeps rendering `ComingSoon`: every earlier phase leaves the tree compiling, and the cutover reverts by reverting one file.

## Integration contract — written in 01, then frozen
`lib/kudos/compose-contract.ts` declares `KudosDoc`/`KudosBlock`/`KudosRun`, `MessageFormat`,
`ComposeOptionsView`, `ComposePayload`, `ComposeFieldErrors`, `CreateKudosState`, the action types
`CreateKudos`/`UploadKudosImage`, the caps, and one props interface per Track A leaf component. Track
B produces the data and satisfies the action types; Track A consumes them as props; 12 wires them by
passing both Server Actions down — the shipped `signOutAction`/`toggleLike` pattern. `compose-state.ts`
(pure reducer, `isSubmitReady`, `buildPayload`) and `rich-text.ts` (mark toggling, `serializeToDoc`,
`parseKudosDoc`) hold that logic so no component reimplements it.

## Blast radius the suite must protect
- `proxy.ts` gains a guard → `route-guard`/`authenticated`/`callback-security` stay green, `/kudos`, `/kudos/[id]` and `/kudos/secret-box` stay public, and F004's **K-21 is scoped off `/kudos/new`** (phase 02).
- Three `kudos` columns are added; the 57 seeded rows stay `'plain'` and non-anonymous. `Unassigned` carries `filter_position NULL`, so K-3's 50 department options are untouched.
- `lib/i18n/messages/dictionary.ts` and `next.config.ts` are repo-wide — a bad edit breaks typecheck, or every image on the board.
- Composing provisions a real `sunners` row for the e2e user, switching the sidebar to that user's own counters. No assertion reads those numbers — verified, not assumed.

## Hard constraints
`npx supabase db reset` is pre-suite only. A full RED run burns ~30 min on timeouts — per phase run only that phase's narrow slice; the full-suite run belongs to 12.
Files ≤200 lines · arbitrary Tailwind values carry `mm:{nodeId}` · both locales enforced by `Dictionary` · per phase `npm run typecheck && npm run lint`.

## Delivered

**Compose gate (63 passed, exit 0):** `npx playwright test e2e/viet-kudo.spec.ts e2e/route-guard.spec.ts` — 62 compose assertions + auth setups + 2 route-guard cases all green.

**Full suite (144 passed, exit 0 twice):** All 10 spec files green on consecutive runs with `kudos_likes` reset to 0 each time — `viet-kudo.spec.ts`, `route-guard.spec.ts`, `kudos-live-board.spec.ts`, `kudos-live-board-authed.spec.ts`, `homepage.spec.ts`, `award-system.spec.ts`, `login-screen.spec.ts`, `authenticated.spec.ts`, `smoke.spec.ts`, `callback-security.spec.ts`. F004 regression protected: all 57 seeded rows remain `message_format='plain'` and `is_anonymous=false`.

**Verification (temper-results.json):** typecheck 0 errors repo-wide · lint 0 errors · build exit 0 (dynamic `/kudos/new` route compiled correctly) · db reset successful · RLS proven live via adversarial psql (anon blocked, sender forgery blocked, auto-provisioning idempotent).

**Inspection (inspection-verdict.json):** 21 acceptance criteria SEALED with real evidence · 0 critical findings · 3 Low findings (file-size boundary at 200 lines, image-count cap enforcement layering, MIME check trusting client type) — all three **CLOSED by post-phase hardening pass** (image-cap check field-specific in validateCompose, MIME sniffing via magic bytes in upload-kudos-image, both files trimmed under 200 lines).

**Post-phase K-25 root-cause:** Session revocation fixed via dedicated `e2e/kudos-auth.setup.ts` + `kudos-auth-setup` project. Full suite now runs idempotently.

**Still open, NOT delivered:** Six unresolved questions in `clarifications.md` — `Danh hiệu` spec/test gap, `D.1` character counter, two spec-less companion frames, anonymous display-name field's unauthored design, deliberate absence of edit/delete, 1006px toolbar measurement. Reviewer notes RLS INSERT-policy shape is now the precedent for future write tables and deserves a second pair of eyes.
