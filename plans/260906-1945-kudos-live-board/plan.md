---
title: "Sun* Kudos Live Board (/kudos) — Supabase-backed screen"
description: "Replace the /kudos placeholder with the full Kudos Live Board over the repo's first Postgres schema, driving 26 sealed e2e assertions from RED to GREEN."
status: delivered
priority: P1
effort: 18.5h
branch: feat/award-system-screen
tags: [kudos, momorph, supabase, e2e-red-first, screen]
created: 2026-09-06
work_type: feature
spec: docs/features/F004_KudosLiveBoard/
system_doc_drafts:
  - plans/260906-1945-kudos-live-board/spec/system/architecture.md
  - plans/260906-1945-kudos-live-board/spec/system/permissions.md
test_policy: e2e-red-first
---

# Sun* Kudos - Live board — implementation blueprint

**Goal** Replace the `ComingSoon` body at `app/kudos/page.tsx` with the real screen (MoMorph
`MaZUn5xHXZ`, 1440×5862, five sections), on the first Postgres schema this repo owns.
**Done when** `npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts --reporter=list`
exits 0 — 26 assertions GREEN, none weakened — after a pre-suite `npx supabase db reset`.

**Settled inputs, not re-openable:** [clarifications.md](clarifications.md) ·
[test-contract.md](test-contract.md) · [spec/](spec/kudos-live-board/technical-spec.md) ·
[supabase](../reports/researcher-260906-1958-supabase-data-layer.md) + [UI](../reports/researcher-260906-1958-repo-ui-conventions.md) studies · [RED gate](../reports/tester-260906-1958-kudos-red-gate.md)

## Phases
| # | Phase | Status | Track | Owner | Depends | Effort |
|---|-------|--------|-------|-------|---------|--------|
| 01 | [Foundation & contract](phase-01-foundation-and-integration-contract.md) | delivered | Shared | `implementer` | — | 1h |
| 02 | [Kudos schema & RLS](phase-02-kudos-schema-and-rls.md) | delivered | B | `implementer` | 01 | 1.5h |
| 03 | [Seed from frame corpus](phase-03-seed-from-frame-corpus.md) | delivered | B | `implementer` | 02 | 2.5h |
| 04 | [Typed data layer & like action](phase-04-typed-data-layer-and-like-action.md) | delivered | B | `implementer` | 03 | 2h |
| 05 | [UI foundation: i18n/icons/hero/sidebar](phase-05-ui-foundation-i18n-icons-hero-sidebar.md) | delivered | A | `momorph-ui-implementer` | 01 | 2.5h |
| 06 | [UI: kudos card family](phase-06-ui-kudos-card-family.md) | delivered | A | `momorph-ui-implementer` | 05 | 2.5h |
| 07 | [UI: board — filters, carousel, feed](phase-07-ui-board-filters-carousel-feed.md) | delivered | A | `momorph-ui-implementer` | 06 | 3h |
| 08 | [UI: spotlight board](phase-08-ui-spotlight-board.md) | delivered | A | `momorph-ui-implementer` | 05 | 2h |
| 09 | [Integration & GREEN gate](phase-09-integration-and-green-gate.md) | delivered | Shared | `implementer` | 04, 07, 08 | 1.5h |

## Delivered

**Final verified state** (evidence gates: temper-results.json, inspection-verdict.json, 4× idempotent suite runs):

- **27 e2e assertions GREEN** — exact RED-to-GREEN command exits 0, run 4 times including once with no db reset between runs. `kudos_likes` returns to 0 each run, idempotent.
- **57 passed across every shipped suite** — no regression in login, homepage, award-system, auth, route-guard, callback-security.
- **typecheck / lint / build all exit 0** — real type coverage, no `any` or syntax errors.
- **Inspection verdict: SEALED, 0 critical** — 2 low cosmetic findings (test spec size, stale comment), 1 deferred suggestion (error handling). All acceptance criteria verified, 9 regression vectors checked.
- **Schema:** 10 tables (9 domain + `board_stats`), RLS on all 10, select-all for anon/authenticated, write-only on `kudos_likes` via auth identity.
- **Seed:** 57 kudos (50 + 7 department-diverse Group C), 13 hashtags, 50 filterable departments, 7 spotlight nodes, 6 ticker rows, 10 gift awards, baseline counts verified.
- **Outstanding:** Four unresolved questions deferred per clarifications § "Unresolved questions" — auth-guard test case 71b3ef43 (route stays public), special-day ×2 heart accrual (out of scope), account-balance persistence (out of scope), hero Sunner-search destination (points to `/profile` ComingSoon).

## Dependency graph
```
01 ─┬─ 02 ─ 03 ─ 04 ─────────┐  Track B: schema → seed → data layer + action
    └─ 05 ─┬─ 06 ─ 07 ───────┼─ 09  integration → GREEN
           └─ 08 ────────────┘  Track A: presentational UI
```
Track A and Track B run **concurrently** after 01; 07 and 08 may also run concurrently.

## File ownership — disjoint by file, not by glob (`lib/kudos/`, `app/kudos/` are split)
| Phase | Owns (write) |
|---|---|
| 01 | `lib/kudos/view-model.ts`, `lib/kudos/derive.ts`, `app/kudos/new/page.tsx`, `app/kudos/secret-box/page.tsx`, `app/kudos/[id]/page.tsx`, `package.json` |
| 02 | `supabase/migrations/**` |
| 03 | `supabase/seed.sql` |
| 04 | `lib/supabase/database.types.ts`, `lib/kudos/{queries,board-data,viewer}.ts`, `app/kudos/_actions/toggle-kudos-like.ts` |
| 05 | `lib/i18n/messages/{dictionary,vi,en,vi-kudos,en-kudos}.ts`, `app/kudos/_components/{kudos-icons,kudos-hero,kudos-sidebar,gift-leaderboard}.tsx`, `public/images/kudos/**` |
| 06 | `app/kudos/_components/{kudos-card,sunner-chip,kudos-card-actions,kudos-attachments,kudos-hashtag-row}.tsx` |
| 07 | `app/kudos/_components/{kudos-board,kudos-filter-bar,kudos-filter-menu,highlight-carousel,all-kudos-feed,kudos-toast}.tsx`, `use-infinite-feed.ts` |
| 08 | `app/kudos/_components/{spotlight-board,spotlight-word-cloud,spotlight-ticker}.tsx`, `spotlight-layout.ts` |
| 09 | `app/kudos/page.tsx`, `spec/kudos-live-board/technical-spec.md` (ERD id reconciliation) |

**`app/kudos/page.tsx` belongs to phase 09 alone** — the data-fetch + composition seam, so Track A
never imports Track B. Until 09 it keeps rendering `ComingSoon`: every earlier phase leaves the
tree compiling and the app working, and the cutover reverts by reverting one file.

## Integration contract — written in 01, then frozen
`lib/kudos/view-model.ts` declares `KudosBoardViewModel`, `KudosCardView`, `SunnerView`,
`SidebarCountsView`, `SpotlightNodeView`, `KudosLikeResult`, `ToggleKudosLike`. Track B
**produces** it (`board-data.ts` returns it; the action satisfies `ToggleKudosLike`), Track A
**consumes** it as props, 09 wires them — passing the action down as a prop, the `signOutAction`
pattern already shipped at `app/_components/coming-soon.tsx:29`.

## Hard constraints
- `npx supabase db reset` is **pre-suite only** — mid-suite it truncates `auth.users` and bounces
  the live browser to `/login` (phase 03 § Risk).
- `test-contract.md` hooks are two-way; additions only where a phase's § Key Insights records one.
- Files ≤200 lines · arbitrary Tailwind values carry `mm:{nodeId}` · both locales, enforced by
  `Dictionary` · per phase `npm run typecheck && npm run lint`.
