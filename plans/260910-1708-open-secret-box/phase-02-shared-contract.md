---
phase: 02
title: "Shared contract — dictionary copy + result types"
status: complete
owner: implementer
track: contract
test_policy: e2e-red-first
effort: 0.5h
depends_on: [01]
---

# Phase 02 — Shared contract (dictionary + result types)

## Context Links

- [plan.md](plan.md) § Dependencies — this phase is the seam that lets Track A (04) and Track B (05)
  compile independently and run concurrently
- [design/geometry.md](design/geometry.md) — the drawn strings, verbatim
- [clarifications.md](clarifications.md) — the frame's text wins over the spec CSV
- [technical-spec](spec/open-secret-box/technical-spec.md) § 3.2 — the `OpenSecretBoxResult` shape
- Precedent: `lib/i18n/messages/vi-rules.ts` / `en-rules.ts` and their `dictionary.ts` block;
  `lib/kudos/compose-contract.ts` for a types-only contract module

## Overview

- **Priority:** P1 — two phases wait on it, and it is half an hour of work.
- **Status:** pending
- Ships **copy and types only**: the `secretBox` dictionary block in both locales and
  `lib/secret-box/contract.ts`. No component, no query, no SQL. After this phase, phase 04 can write
  the UI against `SecretBoxCopy`/`OpenSecretBoxResult` while phase 05 writes the action returning
  the same type, and neither waits on the other.

## Key Insights

- The dictionary is a **compile-time safety net**: a key in `vi-secret-box.ts` missing from
  `en-secret-box.ts` is a `npm run typecheck` error, not a runtime blank. That is the intended
  behaviour — do not widen the interface to dodge it.
- Copy is design text, not prose to improve. `KHÁM PHÁ SECRET BOX CỦA BẠN`, `Click vào box để mở`
  and `Secretbox chưa mở` are transcribed exactly, including the unspaced "Secretbox"
  ([clarifications.md](clarifications.md): the frame wins over the CSV).
- `OpenSecretBoxResult` is a **discriminated union**, so a caller cannot read `badge` off a failure.
  The four failure reasons are closed: `unauthenticated | no-boxes | failed`, plus `ok: true`.
- The type module carries no `"use server"`, no Supabase import and no React import — it must be
  importable from a Client Component and from a Server Action alike.

## Requirements

Functional:
- `Dictionary["secretBox"]` exists with: `title`, `instruction`, `countLabel`, `openerLabel`
  (accessible name of the box control), `closeLabel`, `signInPrompt`, `signInCta`, `badgeAltPrefix`,
  `errorGeneric`.
- `vi-secret-box.ts` carries the drawn Vietnamese; `en-secret-box.ts` carries an English equivalent
  for every key (no key missing, none extra).
- `vi.ts` and `en.ts` wire the new block in, matching how `rules` is wired.
- `lib/secret-box/contract.ts` exports `SecretBoxBadge { ruleItemId: number; label: string; imagePath: string }`
  and `OpenSecretBoxResult = { ok: true; badge: SecretBoxBadge; unopenedCount: number; openedCount: number } | { ok: false; reason: "unauthenticated" | "no-boxes" | "failed" }`.
- It also exports `formatBoxCount(n: number): string` — the two-digit, zero-padded form (`05`,
  `00`), left as-is at three digits. One implementation, used by the panel and asserted by e2e.

Non-functional: no runtime dependency added; both files well under 200 lines; `npm run typecheck`
and `npm run lint` exit 0 at the end of this phase (nothing imports the new module yet, which is
fine).

## Architecture

```
lib/i18n/messages/vi-secret-box.ts ─┐
lib/i18n/messages/en-secret-box.ts ─┼─> dictionary.ts (`secretBox` block, the compile-time contract)
                                     └─> vi.ts / en.ts (wiring)

lib/secret-box/contract.ts   (types + formatBoxCount, zero imports)
   ├── imported by phase 04's client components (prop types)
   └── imported by phase 05's Server Action (return type)
```

Data flow: nothing at runtime yet. This phase only fixes the shape that phases 04, 05 and 06 all
write against, so the seam cannot drift while the two tracks run in parallel.

## Related Code Files

Create: `lib/i18n/messages/vi-secret-box.ts`, `lib/i18n/messages/en-secret-box.ts`,
`lib/secret-box/contract.ts`.

Modify: `lib/i18n/messages/dictionary.ts` (add the `secretBox` interface block),
`lib/i18n/messages/vi.ts`, `lib/i18n/messages/en.ts` (wire the block).

Read for context: `lib/i18n/messages/vi-rules.ts`, `lib/kudos/compose-contract.ts`,
`design/geometry.md`.

Delete: none.

## Implementation Steps

1. Write `vi-secret-box.ts` with the nine keys, the four drawn strings copied verbatim from
   `design/geometry.md`, and a header docblock naming the frame node ids as the source.
2. Write `en-secret-box.ts` with the same keys.
3. Add the `secretBox` block to the `Dictionary` interface, each field documented with the node id
   it renders at (`title` → `mm:1466:7678`, `instruction` → `mm:1466:7683`,
   `countLabel` → `mm:1466:7692`).
4. Wire `secretBox: viSecretBox` / `enSecretBox` into `vi.ts` / `en.ts`.
5. Write `lib/secret-box/contract.ts`: the two types plus `formatBoxCount`.
6. `npm run typecheck && npm run lint`.

## Todo List

- [x] `vi-secret-box.ts` created, strings verbatim from the frame
- [x] `en-secret-box.ts` created with an identical key set
- [x] `Dictionary["secretBox"]` block added with node-id comments
- [x] `vi.ts` and `en.ts` wired
- [x] `contract.ts` exports both types and `formatBoxCount`
- [x] typecheck + lint exit 0

## Success Criteria

- Deleting one key from `en-secret-box.ts` makes `npm run typecheck` fail (spot-check once, then
  restore) — proof the safety net is live.
- `formatBoxCount(5) === "05"`, `formatBoxCount(0) === "00"`, `formatBoxCount(123) === "123"`.
- `git diff --stat` shows exactly the six files above and nothing under `app/` or `supabase/`.
- `grep -r "KHÁM PHÁ SECRET BOX"` finds the string in `vi-secret-box.ts` and in the e2e constants
  file only — never inlined in a component.

## Risk Assessment

| Risk | L×I | Countermeasure |
|------|-----|----------------|
| Copy "corrected" (e.g. `Secret box chưa mở` for the drawn `Secretbox chưa mở`) → e2e text mismatch | M×M | Strings transcribed from `design/geometry.md`; phase 01's constants file is the second witness |
| The union widened to an optional `badge?` for convenience → a failure path reads a badge | L×H | Discriminated union is a stated requirement; phase 05's action must be unable to compile a half-result |
| Two-digit padding re-implemented in the component and the test with different rules | M×M | One `formatBoxCount` here, imported by phase 04 |
| Contract module grows a Supabase or React import and stops being importable from both sides | L×M | Zero-import rule stated above; lint will not catch it, so the phase's diff review must |
| English copy invented where the design has none | L×L | An English string is a translation, not a new requirement; keep it literal |

## Security Considerations

- Copy and types only: no session, no key, no data access. Nothing here can leak.
- `OpenSecretBoxResult` deliberately carries **no** identity field — no `sunnerId`, no `userId`. The
  browser never needs either, and `app/_page-context.ts`'s boundary rule stays intact.

## Next Steps

- Unblocks phase 04 (Track A) immediately and phase 05 (Track B, together with phase 03).
- Rollback: self-contained; reverting these six files removes an unused block and an unused module.
