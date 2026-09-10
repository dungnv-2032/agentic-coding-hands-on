---
title: "Open Secret Box (chưa mở) — the box screen and its server-side draw"
description: "Replace the /kudos/secret-box placeholder with the MoMorph box screen and a single security-definer open_secret_box() that draws one weighted badge, decrements the counter and records the opening."
status: complete
priority: P1
effort: 9h
branch: feat/open-secret-box
tags: [momorph, secret-box, kudos, supabase, e2e-red-first, security-definer, i18n]
created: 2026-09-10
work_type: feature
spec: plans/260910-1708-open-secret-box/spec/open-secret-box/
test_policy: e2e-red-first
momorph_screens: ["J3-4YFIpMM"]
momorph_file_key: 9ypp4enmFmdK3YAFJLIu6C
delivered: 2026-09-10 1916
---

# Open Secret Box (chưa mở) — F009

`/kudos/secret-box` stops being `ComingSoon`: it renders MoMorph frame `1466:7676` (title, box art,
unopened counter, close glyph) and, for a signed-in Sunner holding boxes, opens one through
**exactly one write path** — `public.open_secret_box()`, `security definer`, no identity argument.
Authoritative inputs, never re-litigated: [clarifications.md](clarifications.md) ·
[design/geometry.md](design/geometry.md) ·
[functional-spec](spec/open-secret-box/functional-spec.md) ·
[technical-spec](spec/open-secret-box/technical-spec.md) ·
[permissions](spec/system/permissions.md)

## Phases

| # | Phase | Owner | Track | Status | Effort |
|---|-------|-------|-------|--------|--------|
| 01 | [Strict RED e2e gate](phase-01-red-e2e-gate.md) | `tester` | gate | complete | 2h |
| 02 | [Shared contract — dictionary + result types](phase-02-shared-contract.md) | `implementer` | contract | complete | 0.5h |
| 03 | [Data layer — migration, odds, db:types](phase-03-data-layer-migration.md) | `implementer` | B | complete | 1.5h |
| 04 | [Presentational screen components](phase-04-presentational-components.md) | `momorph-ui-implementer` | A | complete | 2h |
| 05 | [Server action, queries, profile unlock](phase-05-server-action-and-queries.md) | `implementer` | B | complete | 1.5h |
| 06 | [Integration — page.tsx](phase-06-integration-page.md) | `implementer` | integration | complete | 0.5h |
| 07 | [GREEN + visual + adapted assertions](phase-07-green-visual-and-adapted-assertions.md) | `tester` | gate | complete | 1h |

## Dependencies

```
01 (RED, must be first) ──┬──> 02 ──┬──> 04 (Track A) ──┐
                          │         │                   ├──> 06 ──> 07
                          └──> 03 ──┴──> 05 (Track B) ──┘
```

- **01 blocks everything** (no product code before a valid assertion RED); **02 is the seam** — copy
  and types only, so **04 ∥ 05** compile independently and run concurrently with no merge barrier.
- **05 knowingly reds** `TC_WEB_PROFILE_GUI_005` (it enables the button that test asserts disabled);
  07 re-aims it. Do not revert 05 to make it green.
- Fixed gate command, RED and GREEN identical:
  `npx playwright test e2e/secret-box.spec.ts --project=secret-box-authed`
  Companion (anon face, same phases): `npx playwright test e2e/secret-box-anon.spec.ts --project=anon`

## File ownership (no phase overlaps another)

| Phase | Owns |
|-------|------|
| 01 | `e2e/secret-box.spec.ts`, `e2e/secret-box-anon.spec.ts`, `e2e/secret-box-auth.setup.ts`, `e2e/fixtures/secret-box-{constants,grant}.ts`, `e2e/fixtures/supabase-session.ts` (additive), `playwright.config.ts` |
| 02 | `lib/secret-box/contract.ts`, `lib/i18n/messages/{dictionary.ts,vi-secret-box.ts,en-secret-box.ts,vi.ts,en.ts}` |
| 03 | `supabase/migrations/20260910170000_secret_box_open_path.sql`, `supabase/seed.sql`, `lib/supabase/database.types.ts` |
| 04 | `app/kudos/secret-box/_components/**` |
| 05 | `lib/secret-box/queries.ts`, `app/kudos/secret-box/_actions/open-secret-box.ts`, `app/profile/_components/profile-stats-card.tsx` |
| 06 | `app/kudos/secret-box/page.tsx` |
| 07 | `evidence/**`, `e2e/kudos-live-board.spec.ts` (K-21 title only), `e2e/profile.spec.ts` (GUI_005 only) |

## Plan-level decisions (not in any spec; recorded here once)

- **DEC-01 — awarded badge:** inside the `557×557` box slot at `50%` of the slot width, centered,
  box art retained beneath, `alt` = `rule_items.label`. The *đã mở* frame is `in_progress`, so this
  is the minimum satisfying test case `7c3c912f` without inventing a layout.
- **DEC-02 — page shell:** no `HomeHeader` / `SiteFooter`; the frame draws a standalone card and the
  close glyph is the exit. The card centers on a full-height `#00101A` page, and the `<h1>` lives
  **inside `<main>`** — K-21 asserts `main h1`, which `/standards`'s empty `<main>` would not satisfy.
- **DEC-03 — odds rows live in `supabase/seed.sql`, not the migration** (deviation from
  technical-spec § 4): `rule_items` content is seeded there too (`seed.sql:392-397`) and `db reset`
  runs migrations *before* seed, so a label-joined insert in the migration matches zero rows on a
  fresh database. The function raises on an empty odds table instead of decrementing for nothing.

## Out of scope

The *đã mở* / *action bấm mở* celebration screens (MoMorph `in_progress`); how a Sunner **earns** a
box (separate commission — the e2e setup grants them with a runtime-read service-role key, and no
product code gains a test-only branch); `proxy.ts`, `rule_items`, `gift_awards` and
`resolveSidebarSunnerId()`, all untouched.

## Delivery Record — Reconciliation vs. Plan

### Deviations Recorded in Phase Files

**Phase 01 — RED E2E Gate:**
- SB-07 and SB-08 re-aimed post-RED to authenticate via real credentials instead of anon key (correctness fix per PERM018)
- SB-08's forged-parameter test re-aimed to match the actual function (zero parameters, no `p_sunner_id` to forge)
- Three fixture type/runtime defects fixed: service-role client `Database` generic, `ensureSunner` return type, `readCounters` invalid column filter

**Phase 04 — Presentational Components:**
- Glow overlay (node `1466:7685`) deliberately not rendered; initial render showed it as opaque rectangle occluding the box, counter, and hairline; removed per visual-capture verdict; `box-unopened.png` is fully composed artwork including sparkle
- Three fidelity fixes landed post-capture: `min-h-[822.59px]` + `justify-center` to hit design's 822.587px height exactly, box slot `aspect-square` + `max-w-[557px]` to prevent horizontal overflow on phones, counter row `whitespace-nowrap` to prevent label wrapping

**Phase 07 — GREEN & Visual:**
- SB-04 test strengthened to force real second click during pending state (race-condition coverage)
- SB-A3 unused `page` parameter fixed (lint)

### Verified Final State (Phase 07 Evidence)

- ✓ E2E suites: `secret-box.spec.ts` 10/10, `secret-box-anon.spec.ts` 5/5 (user-confirmed prior run)
- ✓ Full suite: 212 passed, 3 skipped, exit 0 (no previously-green tests newly red)
- ✓ Type & lint: `typecheck` clean, `lint` 30 warnings (29 pre-existing + 1 new from phase 07 fixes)
- ✓ Visual: geometry validated at 1440×1024 and 390×844; 35/38 measurement rows PASS, 3 VERIFY (glow caveat, non-blocking)
- ✓ Regression: K-21 (anon), GUI_005 (authed profile), `the-le` (asset share), `smoke` (sanity) — all green

### Risk Gate Status

One open item awaiting user sign-off: the migration (`20260910170000_secret_box_open_path.sql`) and the `security definer` function represent new privileged surface. Reviewer found no defects (PERM016/017/018 all verified live), but both decisions are noted as `riskGate.signoffRequired: true` in the technical spec (see `spec/system/permissions.md`). Delivery complete pending your approval to merge.
