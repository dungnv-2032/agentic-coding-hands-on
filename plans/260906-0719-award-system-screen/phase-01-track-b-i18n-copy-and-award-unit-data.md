---
feature: F003 · test_policy: e2e-red-first · owner: implementer
fileKey: 9ypp4enmFmdK3YAFJLIu6C · screenId: zFYDgyj_pD · depends_on: [] · status: complete · effort: 1h
---

> **Delivered 2026-09-06.** All five files on disk as specified; `npm run typecheck` / `npm run lint` /
> `npm run build` exit 0 (`evidence/temper-results.json`). One post-plan addition inside this phase's
> ownership: `navAriaLabel` was added to `Dictionary["awardSystem"]` + both locale files by the
> orchestrator after reviewer S-7 (the nav had been announcing the page's own `h1`). Contract in
> `plan.md` updated to match.

# Phase 01 — Track B: `awardSystem` dictionary namespace + award unit data

## MoMorph refs:
- Hệ thống giải: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/zFYDgyj_pD
- Clarifications: plans/260906-0719-award-system-screen/clarifications.md
- testPolicy: e2e-red-first

## Context Links

- [plan.md](./plan.md) — integration contract (the `awardSystem` shape below is frozen there)
- [clarifications.md](./clarifications.md) § *Resolved from source data* — **the copy source. Verbatim, not paraphrased.**
- [functional-spec.md](./spec/award-system/functional-spec.md) FR-002, FR-205, FR-206, BR-004
- [technical-spec.md](./spec/award-system/technical-spec.md) § 4.2 Data Model
- Shipped pattern to mirror: `lib/i18n/messages/{dictionary,vi,en,vi-home,en-home}.ts`, `lib/awards.ts`
- Test contract: `e2e/award-system.spec.ts` — the `AWARDS` fixture at the top of that file is the exact
  string set this phase must produce for `vi`

## Overview

**Priority:** P1 · **Status:** complete · **Owner:** `implementer` · **Depends on:** — · **Effort:** 1h

Every display string and every structural fact the Award System screen needs, and nothing else. No
component, no route, no test. The phase ends when `npm run typecheck` is clean and the type system can prove
that VN and EN carry the same key set.

## Key Insights

1. **`lib/awards.ts` already holds the identity.** `AWARDS` is frozen in design order and carries the exact
   slugs the shipped homepage deep-links to (`/awards-information#<slug>` in `award-card.tsx`). Redefining
   the slug list here would silently strand those links the first time the two drift. This phase **reuses**
   `AWARDS` and `AwardKey`; it adds only what is genuinely missing.
2. **The one genuinely missing structural fact is the unit.** clarifications puts `unit` on the structural
   side, but FR-002 requires it to change with the locale — `Cá nhân` cannot survive into EN. Both hold if
   *which* unit an award has is structural (`AWARD_UNITS`) and *how that unit reads* is copy
   (`awardSystem.units`). It also removes the 4× repetition of `Cá nhân` in each locale file.
3. **Prize is a list, not two flat fields (BR-004).** `prizes: Array<{ amount, note? }>` — one entry for four
   awards, two for Signature. `note` absent for Best Manager and MVP. This is what lets phase 02 render one
   shape for all six cards with zero per-award branching.
4. **The nav label is not the card title for two awards.** `signature2025Creator` → nav `Signature 2025
   Creator` / card `Signature 2025 - Creator`; `mvp` → nav `MVP` / card `MVP (Most Valuable Person)`. ID-5
   asserts the nav strings, ID-6/ID-7 assert the card strings. Both live in the same card record.
5. **Quantity is a string, not a number.** The design renders `02`, `03`, `01` with the leading zero, and
   ID-6 matches the text exactly. A `number` would print `2`.

## Requirements

**Functional**
- FR-002 — full VN + EN coverage; a key present in one locale and missing in the other is a **compile error**.
- FR-205 — the six awards carry exactly the quantities/units/amounts in clarifications § *The six awards*.
- FR-206 / BR-004 — prize modelled as a list; Best Manager and MVP carry no note.
- Description copy VN is **verbatim** from clarifications § *Description copy (VN, verbatim)*, including the
  curly quotes `“Aim High – Be Agile”`, `“Creator”`, the en-dashes, and `Sun\*` where it appears.

**Non-functional**
- Files stay under the 200-line cap (`development-rules.md`).
- No new dependency, no runtime I/O, no dynamic import — mirror the static `vi`/`en` map already in
  `lib/i18n/dictionaries.ts`.
- kebab-case filenames matching the shipped `{vi,en}-home.ts` convention.

## Architecture

```
lib/awards.ts (existing, untouched)      lib/i18n/messages/dictionary.ts  (edit)
  AWARDS  ─ slug | key | image  ─────┐     AwardKey (existing union) ──┐
                                     │     + Dictionary.awardSystem  ──┤
lib/award-system.ts (new)            │            ▲                     │
  AwardUnitKey                       │            │ satisfies           │
  AWARD_UNITS: Record<AwardKey,      │     ┌──────┴───────┐             │
                      AwardUnitKey> ─┘     │              │             │
                                     lib/i18n/messages/  lib/i18n/messages/
                                     vi-award-system.ts  en-award-system.ts
                                           │              │
                                     lib/i18n/messages/vi.ts   en.ts   (edit: one line each)
                                           └──────┬───────┘
                                        getDictionary(locale) → Dictionary
```

**Data flow:** phase 02's Server Component receives `dictionary` from `getPageContext()`, iterates `AWARDS`
(order + identity), reads `dictionary.awardSystem.cards[award.key]` (copy) and
`dictionary.awardSystem.units[AWARD_UNITS[award.key]]` (unit text). Nothing here is read at runtime by a
Client Component — resolved strings cross that boundary, never the dictionary module.

**Contract produced (frozen in plan.md — phase 02 codes against exactly this):**

```ts
// lib/award-system.ts
export type AwardUnitKey = "individual" | "team" | "individualOrTeam";
export const AWARD_UNITS: Record<AwardKey, AwardUnitKey>;

// lib/i18n/messages/dictionary.ts — new member of `Dictionary`
awardSystem: {
  hero: { eyebrow: string; title: string; wordmarkAlt: string };
  quantityLabel: string;
  prizeLabel: string;
  prizeOr: string;
  units: Record<AwardUnitKey, string>;
  cards: Record<AwardKey, {
    title: string;
    navLabel: string;
    paragraphs: string[];
    quantity: string;
    prizes: Array<{ amount: string; note?: string }>;
  }>;
};
```

## Related Code Files

**Modify**
- `lib/i18n/messages/dictionary.ts` — add the `awardSystem` member (+ import `AwardUnitKey` as a type)
- `lib/i18n/messages/vi.ts` — `import { viAwardSystem }` + `awardSystem: viAwardSystem,`
- `lib/i18n/messages/en.ts` — `import { enAwardSystem }` + `awardSystem: enAwardSystem,`

**Create**
- `lib/award-system.ts`
- `lib/i18n/messages/vi-award-system.ts`
- `lib/i18n/messages/en-award-system.ts`

**Delete** — none.

**Read-only context** (do not edit): `lib/awards.ts`, `lib/i18n/dictionaries.ts`, `lib/i18n/messages/{vi,en}-home.ts`.

## Implementation Steps

1. Create `lib/award-system.ts`: `AwardUnitKey` union + `AWARD_UNITS` keyed by `AwardKey` —
   `topTalent: "individual"`, `topProject: "team"`, `topProjectLeader: "individual"`,
   `bestManager: "individual"`, `signature2025Creator: "individualOrTeam"`, `mvp: "individual"`.
   Import `AwardKey` as a **type-only** import from `./i18n/messages/dictionary`. Do not re-export `AWARDS`.
2. In `dictionary.ts`, add the `awardSystem` member exactly as in the contract above. Follow the file's own
   convention: fields typed `string` (not literals), a doc comment explaining why the record is keyed by
   `AwardKey`, and `note?: string` optional so an absent note is a type-level fact, not an empty string.
3. Create `vi-award-system.ts` exporting `export const viAwardSystem: Dictionary["awardSystem"] = { ... }`.
   Fill from clarifications:
   - `hero.eyebrow` `Sun* Annual Awards 2025` · `hero.title` `Hệ thống giải thưởng SAA 2025` ·
     `hero.wordmarkAlt` `ROOT FURTHER`
   - `quantityLabel` `Số lượng giải thưởng:` · `prizeLabel` `Giá trị giải thưởng:` · `prizeOr` `Hoặc`
   - `units` — `individual: "Cá nhân"`, `team: "Tập thể"`, `individualOrTeam: "Cá nhân hoặc tập thể"`
   - `cards` — six entries; titles/navLabels/quantities/prizes per the table below, `paragraphs` copied
     **verbatim** from clarifications (Signature and MVP get two entries; the other four get one).
4. Create `en-award-system.ts` the same way. Translation rules, mirroring `en-home.ts`: award titles and nav
   labels stay identical (brand names); amounts stay identical (`7.000.000 VNĐ` — design-fixed currency
   formatting); quantities stay identical; everything else is translated —
   `Số lượng giải thưởng:` → `Number of awards:`, `Giá trị giải thưởng:` → `Award value:`, `Hoặc` → `Or`,
   `Cá nhân` → `Individual`, `Tập thể` → `Team`, `Cá nhân hoặc tập thể` → `Individual or team`,
   `cho mỗi giải thưởng` → `per award`, `cho giải cá nhân` → `for the individual award`,
   `cho giải tập thể` → `for the team award`. Descriptions are faithful translations of the VN paragraphs —
   not new marketing prose.
5. Wire both into `vi.ts` / `en.ts` (one import + one member each).
6. `npm run typecheck` then `npm run lint`. Fix only what this phase owns.

**Frozen values (clarifications § The six awards — transcribe, do not recompute):**

| key | title | navLabel | quantity | unit | prizes |
|---|---|---|---|---|---|
| `topTalent` | Top Talent | Top Talent | `10` | individual | `7.000.000 VNĐ` + `cho mỗi giải thưởng` |
| `topProject` | Top Project | Top Project | `02` | team | `15.000.000 VNĐ` + `cho mỗi giải thưởng` |
| `topProjectLeader` | Top Project Leader | Top Project Leader | `03` | individual | `7.000.000 VNĐ` + `cho mỗi giải thưởng` |
| `bestManager` | Best Manager | Best Manager | `01` | individual | `10.000.000 VNĐ`, **no note** |
| `signature2025Creator` | Signature 2025 - Creator | Signature 2025 Creator | `01` | individualOrTeam | `5.000.000 VNĐ` + `cho giải cá nhân`; `8.000.000 VNĐ` + `cho giải tập thể` |
| `mvp` | MVP (Most Valuable Person) | MVP | `01` | individual | `15.000.000 VNĐ`, **no note** |

## Todo List

- [x] `lib/award-system.ts` — `AwardUnitKey` + `AWARD_UNITS`, type-only `AwardKey` import (32 ln)
- [x] `dictionary.ts` — `awardSystem` member added, `note?` optional, doc comment written (+39 ln)
- [x] `vi-award-system.ts` — hero, three labels, three units, six cards (92 ln)
- [x] VN description paragraphs transcribed verbatim — inspection machine-diffed **8/8 chunks** against clarifications
- [x] Signature = 2 paragraphs + 2 prizes; MVP = 2 paragraphs + 1 prize with no note
- [x] Best Manager + MVP carry **no** `note` key at all — reviewer verified across data, type and render (R4)
- [x] `en-award-system.ts` — same key set, translation rules applied (91 ln)
- [x] `vi.ts` / `en.ts` wired (+2 / +2 ln)
- [x] `npm run typecheck` exit 0 · `npm run lint` exit 0 (0 errors; 3 pre-existing warnings in `e2e/homepage*.spec.ts`)
- [x] All three new files under 200 lines
- [x] **PROVEN** (orchestrator, 2026-09-06) — the exhaustiveness spot-check now has a recorded falsification
      run: `evidence/locale-exhaustiveness-proof.json`. Renaming `prizeOr` → `prizeOrTYPO` fails at
      `en-award-system.ts(23,3)` with `TS2353`; renaming `cards.mvp` → `cards.mvpTYPO` fails at `(80,5)` with
      the same code against `Record<AwardKey, …>`. Both exit 1; the file is restored byte-identical and the
      baseline is back to exit 0. FR-002 holds at compile time, as claimed.
      Worth knowing for next time: the first attempt reported `TS1005`/`TS1128` on *every* case including the
      restored baseline — those came from `.next/dev/types/{routes.d.ts,validator.ts}`, corrupted by dev
      servers running concurrently during verification, not from the mutations. `rm -rf .next/dev && npm run
      build` regenerates them. A typecheck run while a dev server is live can report failures that have
      nothing to do with the source under test.

## Success Criteria

- `npm run typecheck` exits 0. Deleting any key from `en-award-system.ts` makes it exit non-zero (spot-check
  once, then restore) — that is FR-002 proved, not asserted.
- `npm run lint` exits 0.
- `AWARD_UNITS` has exactly six keys; TypeScript rejects a seventh because `Record<AwardKey, …>` is exhaustive.
- Grep proves the strings the RED suite needs exist verbatim in `vi-award-system.ts`:
  `Số lượng giải thưởng:`, `Giá trị giải thưởng:`, `Hoặc`, `cho mỗi giải thưởng`, `cho giải cá nhân`,
  `cho giải tập thể`, `Hệ thống giải thưởng SAA 2025`, `Sun* Annual Awards 2025`.
- `cho mỗi giải thưởng` appears **exactly three times** in `vi-award-system.ts` (topTalent, topProject,
  topProjectLeader) — a fourth occurrence means it leaked into Best Manager or MVP and will fail ID-6.
- No new file imports from `app/**`. `lib/` stays independent of the route layer.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Copy drifts from the design (paraphrase, "fixed" punctuation, straight quotes swapped in) | M×H — silently wrong content that no test catches | Transcribe from clarifications only; the file header comment repeats `vi-home.ts`'s "do not paraphrase — this is design copy" instruction. Phase 03 visual validation is the backstop. |
| `note: ""` used instead of omitting the key for Best Manager / MVP | M×H — an empty note line renders and ID-6's count-0 substring assertion fails | `note?: string` is optional in the type; the todo list calls the trap out by name; phase 02 renders the note only when truthy (belt and braces). |
| A second slug/`AwardKey` union defined here | L×H — homepage `#<slug>` deep links silently rot | Ownership forbids editing `lib/awards.ts`; success criteria require reuse. Reviewer checks for a duplicate union. |
| Quantity typed as `number` | L×M — `02` renders as `2`, ID-6 fails | Contract types it `string`; the frozen-values table shows the leading zeros. |
| Adding `awardSystem` to `Dictionary` breaks other locales/screens | L×M | `vi.ts` and `en.ts` are the only two `Dictionary` implementations (`lib/i18n/dictionaries.ts`); both are updated in this phase, so the break window never leaves the phase. |
| `dictionary.ts` grows past 200 lines | L×L — 105 lines now, ~+25 here | Recheck at the end; if it ever crosses, the split is by namespace, not by an "enhanced" copy. |

**Rollback:** delete the three new files and revert the three one-to-two-line edits. Nothing else imports
them until phase 02 lands, so the revert is total and leaves the shipped homepage untouched.

## Security Considerations

None new. This phase adds static, public, season-announcement copy — no user data, no secrets, no input, no
I/O. All strings are rendered as React text nodes by phase 02 (auto-escaped); nothing here is destined for
`dangerouslySetInnerHTML`, and phase 02 is forbidden from introducing it. No auth surface is touched:
`proxy.ts` is untouched and `/awards-information` stays public (FR-001, FR-601, BR-001).

## Next Steps

- **Unblocks:** phase 02 (Track A) — it cannot typecheck until `Dictionary["awardSystem"]` exists.
- **Hand-off:** report the exact exported symbol names (`viAwardSystem`, `enAwardSystem`, `AwardUnitKey`,
  `AWARD_UNITS`) so phase 02 imports them without guessing.
- **Not this phase:** any `app/**` file, any test, any asset, `docs/**`.
