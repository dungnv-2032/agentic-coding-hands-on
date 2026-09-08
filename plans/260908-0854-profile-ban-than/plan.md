---
title: "F006 Profile bản thân (SCR006)"
description: "Auth-gated /profile with ?id= resolution, hero + badges, stats-or-write-bar, keyset KUDOS feed, and the migration that makes Kudos anonymity a data-layer guarantee."
status: completed
priority: P1
effort: 18.5h
branch: main
tags: [f006, profile, momorph, security, rls, e2e-red-first]
created: 2026-09-08
spec: docs/features/F006_ProfileBanThan/
---

# F006 — Profile bản thân

Spec input: `spec/F006_ProfileBanThan/{functional,technical}-spec.md` + `spec/SCR006_ProfileBanThan/spec.md`.
Authority: `clarifications.md` (31 decisions + 4 amendments) · visuals `reports/momorph-visual-study.md` · MoMorph https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/3FoIx6ALVb · testPolicy `e2e-red-first`.

## Three measured facts that change the plan (read before phase 03)

1. **The revoke as specified breaks two shipped write paths.** `revoke select on public.kudos from
   anon, authenticated` makes the heart toggle AND `create_kudos()` fail with
   `permission denied for table kudos`. Both measured; fix set + probe transcript in phase 03.
2. **`/kudos` reads no query string.** The hashtag filter is `useState` in `kudos-board.tsx`, so
   FR-405's "hashtag click → filtered board" needs a deliberate `?hashtag=` read added (phase 09).
3. **`GiftRowView` carries no sunner id**, so `gift-leaderboard` cannot emit `?id=` without a
   contract change (phase 09, via the plain `gift_awards.sunner_id` column — no new embed).

## Phases

| # | Phase | Track | Owner | Effort | Status |
|---|-------|-------|-------|--------|--------|
| 01 | [Integration contract + `profile` i18n block](phase-01-contract-and-i18n.md) | Foundation | implementer | 1h | complete |
| 02 | [E2E RED gate: own session, own project](phase-02-e2e-red-gate.md) | Test | tester | 2h | complete (RED, exit 1) |
| 03 | [Reader view, revoke, policy repair, seed](phase-03-reader-view-and-revoke.md) | B | implementer | 2.5h | complete (concerns) |
| 04 | [Repoint the three call sites + shared card mapper](phase-04-repoint-read-path.md) | B | implementer | 1.5h | complete (concerns) |
| 05 | [Profile data layer + keyset server action](phase-05-profile-data-layer.md) | B | implementer | 2.5h | complete |
| 06 | [Route guard + `?id=` resolver](phase-06-route-guard-and-id-resolver.md) | B | implementer | 0.5h | complete |
| 07 | [Hero, badge row, stats card, write-Kudo bar](phase-07-track-a-hero-and-stats.md) | A | momorph-ui-implementer | 2.5h | complete (concerns) |
| 08 | [KUDOS section — dropdown, feed, infinite scroll](phase-08-track-a-kudos-section.md) | A | momorph-ui-implementer | 3h | complete (concerns) |
| 09 | [Integration: page wiring, board `?id=` links, F004 amendment](phase-09-integration-and-board-links.md) | Integration | implementer | 2h | complete (concerns) |
| 10 | [GREEN + visual validation](phase-10-green-and-visual-validation.md) | Test | tester | 1.5h | complete (GREEN 108/0) |

## Dependency graph

```
01 ──┬─> 02 ──┬─> 03 ──> 04 ──> 05 ──┐
     │        ├─> 06 ────────────────┤
     │        ├─> 07 (Track A) ──────┼─> 09 ──> 10
     │        └─> 08 (Track A) ──────┘
```

- **01 blocks everything** — it freezes `ProfileViewModel` so both tracks build against one boundary.
- **02 blocks both tracks** (`e2e-red-first`): a valid RED caused by the profile assertions — not by
  config, browser install or dev server — is the release gate for 03–08.
- **03 → 04 → 05** is strictly sequential (schema → read path → profile reads).
- **03, 04, 05, 06** run concurrently with **07, 08**; ownership is disjoint by construction.
- **09 alone touches `app/profile/page.tsx`**, and alone edits F004's shared board files after 04.

## File-ownership map (no two concurrent phases share a path)

| Phase | Owns |
|---|---|
| 01 | `lib/profile/profile-view-model.ts`, `lib/i18n/messages/{dictionary,vi,en,vi-profile,en-profile}.ts` |
| 02 | `e2e/profile{,-anon}.spec.ts`, `e2e/profile-auth.setup.ts`, `e2e/fixtures/profile-constants.ts`, `playwright.config.ts` |
| 03 | `supabase/migrations/20260908*_profile_reader_view.sql`, `supabase/seed.sql`, `lib/supabase/database.types.ts` |
| 04 | `lib/kudos/{queries,board-data,map-kudos-card,view-model}.ts`, `app/kudos/_actions/toggle-kudos-like.ts` |
| 05 | `lib/profile/{profile-queries,profile-data}.ts`, `app/profile/_actions/fetch-profile-kudos-page.ts` |
| 06 | `proxy.ts`, `lib/profile/resolve-profile-id.ts` |
| 07 | `app/profile/_components/{profile-keyvisual,profile-hero,profile-badge-row,profile-stats-card,write-kudo-bar}.tsx` |
| 08 | `app/profile/_components/{kudos-direction-section,profile-direction-menu,profile-kudos-feed}.tsx` |
| 09 | `app/profile/page.tsx`, `app/kudos/_components/{sunner-chip,gift-leaderboard,kudos-board}.tsx`, `e2e/kudos-live-board.spec.ts`, + inherits 04's four files |
| 10 | `evidence/`, `reports/` (no source files) |

## Standing constraints

- **Heart stays server-authoritative.** `toggleKudosLike` is reused untouched; no optimistic flip (K-25).
- **200-line cap** per file — every split is named in its phase, not discovered later.
- **No new npm dependency, no new E2E runner.** `@playwright/test` is already present.
- **`spotlight_ticker_events.sunner_id` is always the RECEIVER** (measured 7/7). Never write a sender there.
- Rollback notes: phase 03 § Risk (migration + revoke), phase 09 § Risk (board contract).
