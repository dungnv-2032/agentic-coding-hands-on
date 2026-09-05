---
feature: F002
owner: implementer
depends_on: []
status: completed
effort: 1h
completed: 2026-09-05
---

# Phase 02 — Track B: i18n copy, awards data module, env documentation

## Context Links

- Plan + frozen contract: [plan.md](./plan.md) · Decisions: [clarifications.md](./clarifications.md) ("i18n coverage", "Award card destinations", "Countdown target time", ORCH-01)
- Spec: FR-202, FR-204, FR-205, FR-206, FR-207, FR-405, § 4.6 Configuration in [technical-spec.md](./spec/homepage-saa/technical-spec.md)
- Copy source: [design/homepage-saa.png](./design/homepage-saa.png) — read it with the Read tool and transcribe VN copy character for character
- Test contract: [test-contract.md](./evidence/test-contract.md) (ID-14, ID-17, ID-25/26)

## Overview

- **Priority:** P1 · **Owner agent:** `implementer` · **Status:** pending · **Effort:** 1h
- **Depends on:** nothing. **Runs concurrently with:** 01, 03. Track A (04-06) reads the key list below.
- Every string and every piece of non-visual data the homepage needs, landed before the UI phases
  need to import it. No component, no styling, no layout in this phase.

## Key Insights

- `Dictionary` is compile-time enforced: `en.ts` is typed against the same interface, so a key added
  in VN and forgotten in EN is a build error, not a runtime blank. That property is the whole reason
  the type is shared — keep it.
- The homepage copy is far larger than the login copy. Putting it all in `vi.ts` would push that file
  past the project's 200-line limit, so the module splits: the interface into `dictionary.ts`, the
  homepage copy into `vi-home.ts` / `en-home.ts`, composed back in `vi.ts` / `en.ts`.
- Award cards need two different kinds of data: **copy** (title, description — translatable) and
  **identity** (slug, image path, order — not translatable). Splitting them keeps the slug list a
  single source of truth for `/awards-information#<slug>` (FR-405) and the E2E `data-testid` contract.
- The design frame reads **"Comming soon"**. FR-202 and tests ID-13/ID-41 expect `Coming soon`; ship
  the corrected spelling in both locales. This is the one place copy deliberately departs from the frame.
- Spec item B2 carries stale event copy (`18h30`, `Nhà hát nghệ thuật quân đội`); the frame is the later
  artifact and wins (clarifications, "Resolved from source data"). ID-14 asserts the frame's values.
- Nav labels stay English in both locales (`About SAA 2025`, `Award Information`, `Sun* Kudos`) — they
  are design copy, like `LOGIN With Google` already is.

## Requirements

- FR-202/FR-204/FR-205/FR-206/FR-207 — every visible string exists in VN and EN.
- FR-405 — six slugs, in design order, one definition.
- BR-004 / ORCH-01 — `NEXT_PUBLIC_EVENT_START_AT` documented in `.env.example` with the real event date.
- Non-functional: each file under 200 lines; no new i18n dependency (clarifications).

## Architecture

```
lib/i18n/messages/dictionary.ts   interface Dictionary { login, footer, todo, header, home, comingSoon }
        ├── vi.ts  = { …login/footer/todo (existing), header, comingSoon, home: viHome }
        │      └── vi-home.ts   long homepage prose (hero, rootFurther, awards, kudos, widget)
        └── en.ts  = same shape, en-home.ts

lib/awards.ts  AWARDS = [{ slug: "top-talent", key: "topTalent", image: "/images/home/award-top-talent.png" }, …×6]
                        ─► award-card.tsx zips AWARDS[i] with dictionary.home.awards.cards[key]
```

## Related Code Files

**Create:** `lib/i18n/messages/dictionary.ts`, `lib/i18n/messages/vi-home.ts`,
`lib/i18n/messages/en-home.ts`, `lib/awards.ts`
**Modify:** `lib/i18n/messages/vi.ts`, `lib/i18n/messages/en.ts`, `lib/i18n/dictionaries.ts`
(import the interface from its new home; keep re-exporting `Dictionary`), `.env.example`
**Delete:** none
**Not owned:** every file under `app/` (01, 04-07), `playwright.config.ts` (08).

## Implementation Steps

1. Move `interface Dictionary` out of `vi.ts` into `lib/i18n/messages/dictionary.ts` unchanged, then
   extend it with the three new namespaces (existing `login`, `footer`, `todo` untouched):
   - `header`: `logoAlt`, `about`, `awardInformation`, `kudos`, `notificationsLabel`,
     `notificationsEmpty`, `accountLabel`, `profile`, `signOut`, `adminDashboard`
   - `home`: `wordmarkAlt`, `comingSoon`, `days`, `hours`, `minutes`, `eventTimeLabel`,
     `eventTimeValue`, `eventVenueLabel`, `eventVenueValue`, `eventLivestream`, `ctaAwards`,
     `ctaKudos`, `rootFurther: { rootAlt, furtherAlt, paragraphs: string[], quote, quoteSource }`,
     `awards: { eyebrow, title, detailLabel, cards: Record<AwardKey, { title, description }> }`,
     `kudos: { eyebrow, title, subtitle, body, cta }`, `widget: { writeKudos, standards }`
   - `footer`: add `standards` next to the existing `copyright`
   - `comingSoon`: `title`, `body`
   `AwardKey` is a string-literal union declared in `dictionary.ts` (`"topTalent" | "topProject" | …`)
   so a missing card is a compile error.
2. `vi-home.ts` exports `viHome` typed as `Dictionary["home"]`, transcribed from the frame:
   `eventTimeLabel` "Thời gian:", `eventTimeValue` "26/12/2025", `eventVenueLabel` "Địa điểm:",
   `eventVenueValue` "Âu Cơ Art Center", `eventLivestream` "Tường thuật trực tiếp qua sóng Livestream",
   `ctaAwards` "ABOUT AWARDS", `ctaKudos` "ABOUT KUDOS", `comingSoon` "Coming soon",
   `days` "DAYS", `hours` "HOURS", `minutes` "MINUTES", `awards.eyebrow` "Sun* annual awards 2025",
   `awards.title` "Hệ thống giải thưởng", `awards.detailLabel` "Chi tiết", the six card titles
   (`Top Talent`, `Top Project`, `Top Project Leader`, `Best Manager`, `Signature 2025 - Creator`,
   `MVP (Most Valuable Person)`) with their descriptions, `kudos.title` "Sun* Kudos", and the
   Root Further prose paragraphs plus the quote "A tree with deep roots fears no storm" /
   "(Cây sâu bén rễ, bão giông chẳng nề - Ngạn ngữ Anh)". Read the frame for anything not listed here.
3. `en-home.ts` mirrors it as a translation. Keep untranslatable design copy identical:
   `ABOUT AWARDS`, `ABOUT KUDOS`, `DAYS/HOURS/MINUTES`, `Coming soon`, `Sun* Kudos`, the six card
   titles, `Sun* annual awards 2025`, and the English quote.
4. `vi.ts` / `en.ts` import their `*-home.ts` and compose; add `header`, `footer.standards`,
   `comingSoon`. `header.about` = "About SAA 2025" in both locales.
5. `lib/i18n/dictionaries.ts` — import `Dictionary` from `./messages/dictionary`, keep the
   `export type { Dictionary }` re-export so existing `@/lib/i18n/dictionaries` imports still resolve.
6. `lib/awards.ts` — `export type AwardSlug = …` (six literals), `export const AWARDS` as a
   `readonly` array of `{ slug: AwardSlug; key: AwardKey; image: string }` in design order. Image
   paths point at `public/images/home/` names recorded by phase 03's manifest.
7. `.env.example` — append `NEXT_PUBLIC_EVENT_START_AT=2025-12-26T18:30:00+07:00` with a comment
   stating: ISO-8601, read by the client countdown, an invalid or missing value renders `00/00/00`
   and hides "Coming soon"; the E2E suite pins its own future value via `playwright.config.ts`
   (ORCH-01), and a developer wanting a live countdown locally sets a future date in `.env.local`.
8. `npm run lint && npm run typecheck` clean.

## Todo List

- [x] `Dictionary` moved to `dictionary.ts`, extended with `header` / `home` / `comingSoon` / `footer.standards`
- [x] `vi-home.ts` transcribed from the frame; "Coming soon" spelled correctly
- [x] `en-home.ts` mirrors every key; build fails if one is missing
- [x] `lib/awards.ts` exports six slugs in design order
- [x] `.env.example` documents `NEXT_PUBLIC_EVENT_START_AT`
- [x] every file under 200 lines; lint + typecheck clean

## Success Criteria

- Deleting any single key from `en-home.ts` makes `npm run typecheck` fail (proof the type gate works).
- `AWARDS.map(a => a.slug)` equals exactly the six slugs frozen in plan.md, in design order.
- `grep -c "" lib/i18n/messages/*.ts` shows no file at 200 lines or more.

## Risk Assessment

| ID | Risk | Likelihood | Impact | Countermeasure |
|----|------|-----------|--------|----------------|
| R2-1 | Copy transcribed from memory instead of the frame; ID-14 fails on venue/date text | Medium | High | Step 2 pins the ID-14 strings verbatim; the frame is the only source for the rest |
| R2-2 | Splitting the dictionary breaks an existing import of `Dictionary` from `./vi` | Medium | Medium | Step 5 keeps the `dictionaries.ts` re-export; typecheck catches the rest |
| R2-3 | EN translation of `awards.title` removes "giải thưởng", which ID-25/26 uses as the VN marker | Low | Medium | Intended — the VN assertion runs only in VN mode; do not leave VN strings in the EN dictionary |
| R2-4 | `vi.ts` still grows past 200 lines | Low | Low | Prose lives in `vi-home.ts`; move more out if it does |

## Security Considerations

- `NEXT_PUBLIC_EVENT_START_AT` is a public build-time value by design — an event date, no secret.
  Nothing else may be added to `.env.example` in this phase, and no real key values ever land there.
- Dictionaries hold static copy only; no user input, no interpolation of untrusted values.

## Rollback

Revert the phase commit. `lib/i18n` returns to its login-only shape and `/login` keeps working, since
this phase only adds keys and moves a type.

## Next Steps

Track A phases 04-06 consume `header.*` / `home.*` and `AWARDS`; phase 07 consumes `comingSoon.*`.
