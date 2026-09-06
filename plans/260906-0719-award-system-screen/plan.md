---
title: "Award System screen — Hệ thống giải at /awards-information"
description: "Phased blueprint for the SAA 2025 award system screen: awardSystem i18n namespace, unit data module, hero + sticky category nav + six detail cards, then the e2e-red-first GREEN gate."
status: in-progress
priority: P1
effort: 6h
branch: feat/language-dropdown-open-state
tags: [award-system, saa2025, nextjs16, i18n, scroll-spy, e2e, momorph]
created: 2026-09-06
work_type: feature
spec_draft: plans/260906-0719-award-system-screen/spec/award-system/
test_policy: e2e-red-first
momorph: { fileKey: 9ypp4enmFmdK3YAFJLIu6C, screenId: zFYDgyj_pD }
red_evidence:
  redTestFiles: e2e/award-system.spec.ts
  redCommand: npx playwright test e2e/award-system.spec.ts --project=anon
  redExitCode: 1
  redFailure: "getByRole('heading', { name: 'Hệ thống giải thưởng SAA 2025', level: 1 }) — Expected: visible; element(s) not found"
  redCounts: "11 failed, 2 passed (ID-0/2 green pre-implementation — routing + header selected-state already ship; judge GREEN by the other 11)"
green_evidence:
  greenCommand: npx playwright test e2e/award-system.spec.ts --project=anon   # byte-identical to redCommand
  greenExitCode: 0
  greenCounts: "14 passed / 0 failed · homepage 22/22 · full anon project 54/54 — all exit 0; typecheck, lint, build exit 0"
---

# Award System screen — Implementation Plan

Decisions: [clarifications.md](./clarifications.md) — authoritative, not re-openable (ORCH-01..05). Spec draft: [functional](./spec/award-system/functional-spec.md) · [technical](./spec/award-system/technical-spec.md) · [SCR-award-system](./spec/award-system/screens/SCR-award-system/spec.md)
Trail: RED [red-run.log](./evidence/award-system-red-run.log) → [tester final verdict](./reports/tester-260906-0851-award-system-final-verdict.md) → [reviewer](./reports/reviewer-260906-0905-award-system.md) → [tester delivery + seal](./reports/tester-260906-0935-award-system-delivery-verification.md) · [temper-results.json](./evidence/temper-results.json) · [inspection-verdict.json](./evidence/inspection-verdict.json) · Contract: [e2e/award-system.spec.ts](../../e2e/award-system.spec.ts) · Design: [award-system.png](./design/award-system.png) (1440×6410)

## Phases

| # | Phase | Owner | Dep | Status | Evidence for that status |
|---|-------|-------|-----|--------|--------------------------|
| 01 | [Track B — awardSystem dictionary + unit data](./phase-01-track-b-i18n-copy-and-award-unit-data.md) | implementer | — | **complete** | `lib/award-system.ts` + `{vi,en}-award-system.ts` on disk, `Dictionary.awardSystem` wired into `vi.ts`/`en.ts`; typecheck + lint exit 0 |
| 02 | [Track A — hero, nav, detail cards, page assembly](./phase-02-track-a-award-system-ui.md) | momorph-ui-implementer | 01 | **complete** | 6 `_components/*` + `page.tsx` shipped (plan predicted 5 — see Deviations); build exit 0 |
| — | Inspection — reviewer pass (**unplanned, added mid-flight**) | reviewer | 02 | **complete** | 0 critical / 3 warning / 11 suggestion; all 3 warnings fixed + independently verified; `inspection-verdict.json` 9.6, `SEALED` |
| 03 | [Tester — GREEN rerun + visual validation](./phase-03-tester-green-rerun-and-visual-validation.md) | tester | 02 | **complete** | award-system **14/14**, homepage **22/22**, full anon **54/54**, all exit 0; visual PASS after 4 fix rounds |
| 04 | [Docs — spec promote + generated-inventory sync](./phase-04-docs-spec-promote-and-sync.md) | doc-writer | 03 | **in progress** | doc-writer running 2026-09-06; **no `docs/` artifact verified — nothing here claims 04 output** |

`01 ──► 02 ──► [inspection] ──► 03 ──► 04`. **ORCH-01** Track B first (Track A imports its `Dictionary` extension). **ORCH-02** one Track A worker, no fan-out. 04 is the only phase allowed to touch `docs/`.

## Integration contract (frozen — reviewer: "Met in full")

```ts
// Dictionary["awardSystem"] in lib/i18n/messages/dictionary.ts — bare fields are `string`
awardSystem: {
  hero: { eyebrow; title; wordmarkAlt }; navAriaLabel;            // navAriaLabel added post-review (S-7)
  quantityLabel; prizeLabel; prizeOr; units: Record<AwardUnitKey, string>;   // "Số lượng…:" · "Giá trị…:" · "Hoặc"
  cards: Record<AwardKey, { title; navLabel; paragraphs: string[]; quantity;
    prizes: Array<{ amount: string; note?: string }> }>;          // keyed by the EXISTING AwardKey
}
```

`lib/award-system.ts` exports `AwardUnitKey = "individual" | "team" | "individualOrTeam"` + `AWARD_UNITS: Record<AwardKey, AwardUnitKey>`. Slug/key/image identity **reused from `lib/awards.ts`**, never redefined. Unit *identity* structural, unit *text* dictionary copy (FR-002).

Test hooks (`e2e/award-system.spec.ts` — bound, never weakened):

- section `<section id="<slug>" data-testid="award-detail-<slug>" aria-labelledby="<slug>-title">` + `<h2 id="<slug>-title">` = card title (W-3)
- menu `<nav data-testid="award-nav" aria-label="Danh mục giải thưởng">` — exactly 6 `<a href="#<slug>" data-testid="award-nav-<slug>">`; active → `aria-current="true"`, else attribute absent
- image `<img alt="{card title}">` one per section, **336×336** (ID-7 lock) · only `<h1>` = `Hệ thống giải thưởng SAA 2025` · order banner → h1 → award-nav → 6 sections (design order) → Kudos `<section>` → contentinfo

Slugs frozen: `top-talent`, `top-project`, `top-project-leader`, `best-manager`, `signature-2025-creator`, `mvp`. Composed unchanged: `HomeHeader`, `SiteFooter`, `getPageContext`, `_fonts`; no `FloatingWidget` (FR-208). `KudosPromo` composed **with one prop** — ORCH-05, see Deviations.

## File ownership (as delivered)

- **01** `lib/i18n/messages/{dictionary,vi,en}.ts`, `lib/i18n/messages/{vi,en}-award-system.ts`, `lib/award-system.ts`
- **02** `app/awards-information/page.tsx`; `_components/{award-system-hero,award-category-nav,award-detail-card,award-prize-list,award-system-icons}.tsx` **+ `_components/use-award-scroll-spy.ts`** (unplanned split); **+ `app/_components/kudos-promo.tsx`** (unplanned, ORCH-05 exception — optional `maxWidthClass` prop)
- **03** `evidence/**`, `visuals/**`, **and `e2e/award-system.spec.ts`** (two assertions added — exceeds the phase's written "never touch `e2e/**`"; orchestrator-directed, additions only) · **04** `docs/**`, `spec/**`
- Untouched as planned: `proxy.ts`, `app/_components/{home-nav,site-footer}.tsx` (ORCH-03), `playwright.config.ts` (its `testMatch` +1 predates the phases, made at RED), `app/_components/coming-soon.tsx` (still used by `/kudos`, `/standards`, `/profile`, `/admin`)

## Deviations — what the plan predicted vs what shipped

- **Track A files 5 → 6.** `use-award-scroll-spy.ts` (196 ln) split out of `award-category-nav.tsx` (89 ln) when the W-2 fix pushed the nav past the 200-line cap. The size estimate was wrong; ORCH-02 single-owner was not.
- **`KudosPromo` predicted "zero edits" → edited.** It self-caps at `max-w-[1224px]`, so no wrapper could widen it and the body copy ran under the logo here. ORCH-05 grants an optional `maxWidthClass`, union-typed after S-11; homepage default measured byte-identical (card 252→1188, w936).
- **The plan's own R2 mitigation became defect W-2.** The 700 ms click lock discarded observer deliveries with no recovery → wrong item lit permanently (FR-402). Replaced by live-geometry `resolveActive()` + lock release on wheel/touch/key, proven with a no-interrupt control.
- **Suite 13 → 14 tests.** Phase 03's "13 passed" criterion is superseded by ID-7's 336×336 lock and the W-3 structure lock. Both strengthen; nothing was relaxed to pass.
- **Not predicted anywhere:** the six sections shipped with no heading/accessible name (W-3, now `h2` + `aria-labelledby`); Playwright MCP was unavailable all run (`chrome` channel absent) so every capture went through the project's own Chromium.

## Key risks — outcome

| Risk | Hit? | Resolution |
|---|---|---|
| **R1** strict-mode single-node strings | No | Reviewer "Met": `Số lượng giải thưởng:` once per card; `Giá trị giải thưởng:` per prize row, test uses `.first()`. |
| **R2** sticky header overlays nav / scroll target | **Yes, twice** | (a) **W-1** — `HEADER_OFFSET=112` under-cleared below `lg` (real header 245px @375). Fixed: runtime-measured `--award-header-offset` (112/117/165/285/341 across widths) with `lg` pinned at 112px in the cascade; desktop geometry unmoved. (b) **OBS-2** — 80%-opaque header lets content bleed through; pre-existing shared chrome, worse on `/` → deferred as FUP-01. |
| **R3** hydration mismatch fails ID-13 | No | Initial state `items[0]` on both sides; zero console errors in every run. Deep-link seeding costs a ~290 ms post-hydration transient, accepted as ORCH-04. |
| **R4** note line on Best Manager / MVP | No | Met across data (key omitted), type (`note?`) and render (`{prize.note && …}`). |
| **R5** no exported icon assets | Partly | Three inline SVGs hand-authored, `currentColor`, no `<title>`; tester measured all four card icons `rgb(255,255,255)` = frame. No re-export needed (A1 closed). |
| **R6** ID-1 anon→login not implemented | By design | Recorded in clarifications + spec D001/RISK-01; six green homepage tests depend on the route staying public. |

## Next steps

1. **04 docs** — doc-writer, in flight. Done = F003/SCR003/US007/US008 registered, `/awards-information` row off `ComingSoon`, D001 + ID-14 carried forward verbatim.
2. **FUP-01** — opaque fill or `backdrop-blur` on `app/_components/home-header.tsx`. **Owner: unassigned, needs a ticket** (ORCH-03 read-only here). Done = judged against `/` first, where it is measurably worse (22% vs 10% bleed @375).
3. **FUP-02** — `w-[60px]` unit column cramps EN (S-10). Deliberately skipped: `max-w-[88px]` collapses the VI wrap the frame specifies. **Owner: unassigned.** Done = revisited at the EN visual pass.
4. Open, unowned: Playwright per-test `timeout` headroom for cold WSL compiles (tester recommendation, not applied); ID-1 (D001) and ID-14 (`/kudos` placeholder) await a product owner.
