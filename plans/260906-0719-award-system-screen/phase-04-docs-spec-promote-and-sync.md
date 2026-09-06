---
feature: F003 · test_policy: e2e-red-first · owner: doc-writer
fileKey: 9ypp4enmFmdK3YAFJLIu6C · screenId: zFYDgyj_pD · depends_on: [03] · status: in-progress · effort: 0.5h
---

> **In progress, 2026-09-06 — `doc-writer` running now.** Gate cleared: phase 03 is GREEN on evidence
> (14/14 · 22/22 · 54/54, all exit 0), so this phase is released to write. **No `docs/` artifact has been
> verified by delivery tracking**, so nothing below is ticked. Not complete until the created/modified list
> exists on disk and the codes are registered exactly once.
>
> Three facts the shipped tree added after this phase was written, which the promoted specs must carry:
> - The screen ships **six** `_components/*`, not five — `use-award-scroll-spy.ts` is the sixth. Any
>   `TBD (draft)` component path in § 4.1 / § 4.2 must resolve against the real seven-file surface.
> - `app/_components/kudos-promo.tsx` gained an optional `maxWidthClass` prop (**ORCH-05**) — a shared
>   component F002 also owns. Note it wherever F002's component inventory lives.
> - Accessibility structure changed with W-3: six `<h2>` + `aria-labelledby`, and the category `<nav>` is
>   named from `awardSystem.navAriaLabel`. If the draft describes the title as a `<p>`, the code wins.

# Phase 04 — Docs: promote the F003 spec draft and sync the generated inventories

## MoMorph refs:
- Hệ thống giải: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/zFYDgyj_pD
- Clarifications: plans/260906-0719-award-system-screen/clarifications.md
- testPolicy: e2e-red-first

## Context Links

- [plan.md](./plan.md) — `spec_draft: plans/260906-0719-award-system-screen/spec/award-system/`
- [spec/award-system/functional-spec.md](./spec/award-system/functional-spec.md) · [technical-spec.md](./spec/award-system/technical-spec.md) · [screens/SCR-award-system/spec.md](./spec/award-system/screens/SCR-award-system/spec.md)
- `.claude/rules/documentation-management.md` — the rule that makes this phase mandatory
- Precedent to mirror exactly: `docs/features/F002_HomepageSaa/`, `docs/screens/SCR002_Homepage/`
- `docs/_canonical-fcodes.json`, `docs/generated/{feature-list,screen-list,route-list,user-stories}.md`

## Overview

**Priority:** P2 · **Status:** in progress · **Owner:** `doc-writer` · **Depends on:** 03 (GREEN, cleared) · **Effort:** 0.5h

**Why this phase exists (the justification for going past three):** the F003 spec is a *draft* living inside
the plan folder, and it says so in three places — `status: draft`, the `TBD (draft)` source references, and
its own note that `US007`/`US008`/`SCR003_AwardSystem` are "ghi sẵn mã dự kiến; việc đăng ký chính thức vào
state file diễn ra lúc promote". Without a promote step the codes stay unregistered, `docs/generated/*`
keeps describing `/awards-information` as a `ComingSoon` placeholder, and the next feature draft picks
`US007` again. `documentation-management.md` also requires a docs refresh after every feature ships. This is
bookkeeping the shipped code has already invalidated, not new scope.

Note the project's docs layout is spec-driven (`docs/features/F###`, `docs/screens/SCR###`,
`docs/generated/*`) and has **no** `development-roadmap.md` / `project-changelog.md` file. Do not create
them here — sync the artifacts that actually exist.

## Key Insights

1. **Codes are registered at promote, not at draft.** `F003` is already reserved; `US007`, `US008` and
   `SCR003_AwardSystem` are the next free codes (user-stories stops at `US006`, screen-list at `SCR002`).
   Registering them is this phase's whole point.
2. **`docs/generated/*` is a machine-owned layer** — edit rows surgically, do not regenerate or rewrite the
   files wholesale, and invent nothing that is not in the shipped code.
3. **Two rows are now factually wrong**: `route-list.md` line 30 still shows `/awards-information` as
   `Page → <ComingSoon />` owned by F002, and the "five `ComingSoon` placeholders" sentence below it is now
   four. Both must change or the docs actively mislead.
4. **`docs/_canonical-fcodes.json` currently lists `/awards-information` under F002's routes.** It moves to
   F003. F002 keeps the four routes it still owns.
5. **The draft's `TBD (draft)` source references can now be filled** — the code exists. Fill only what was
   actually built; leave anything unbuilt as-is rather than inventing a path.

## Requirements

**Functional**
- Promote the draft into `docs/features/F003_AwardSystem/{functional-spec.md,technical-spec.md}` and
  `docs/screens/SCR003_AwardSystem/spec.md`, mirroring F002's structure.
- Flip `status: draft` → the promoted status F002's promoted specs use.
- Register `F003`, `SCR003_AwardSystem`, `US007`, `US008` and route ownership across the generated
  inventories and `docs/_canonical-fcodes.json`.
- Correct the `/awards-information` route row and the placeholder count.
- Carry forward the two unresolved items verbatim: test case ID-1 (D001 / RISK-01) and ID-14 (`/kudos` is
  still a placeholder). They are open product decisions, not defects to quietly close.

**Non-functional**
- Every statement must be verified against the shipped code before it is written.
- Keep each file under `docs.maxLoc: 800`; split before exceeding rather than truncating.
- No file under `docs/journals/` — that is `journal-writer`'s lane, not this phase's.

## Architecture

```
plans/260906-0719-award-system-screen/spec/award-system/
  functional-spec.md ─┐
  technical-spec.md ──┼─ promote (status flip + TBD(draft) → real paths) ─┐
  screens/SCR-award-system/spec.md ─┘                                      │
                                                                           ▼
                        docs/features/F003_AwardSystem/{functional,technical}-spec.md
                        docs/screens/SCR003_AwardSystem/spec.md
                                                                           │
   surgical row edits ◄────────────────────────────────────────────────────┤
     docs/generated/feature-list.md   + F003 row + detail block            │
     docs/generated/screen-list.md    + SCR003 block                       │
     docs/generated/route-list.md     /awards-information: F002→F003,      │
                                      ComingSoon → real page; 5→4 count    │
     docs/generated/user-stories.md   + US007, US008                       │
     docs/_canonical-fcodes.json      + F003 entry; move the route off F002 ┘
```

**Data flow:** the plan's spec draft is the source; the shipped code is the arbiter. Where the two disagree,
the code wins and the spec text is corrected — never the reverse.

## Related Code Files

**Create**
- `docs/features/F003_AwardSystem/functional-spec.md`
- `docs/features/F003_AwardSystem/technical-spec.md`
- `docs/screens/SCR003_AwardSystem/spec.md`

**Modify**
- `docs/generated/feature-list.md`, `screen-list.md`, `route-list.md`, `user-stories.md`
- `docs/_canonical-fcodes.json`
- `plans/260906-0719-award-system-screen/spec/award-system/*.md` — mark promoted

**Consider only if the shipped behavior actually changed them** (check, then edit or state "no change"):
`docs/generated/behavior-logic.md`, `docs/generated/permissions-matrix.md`, `docs/system/architecture.md`,
`docs/system/permissions.md`, `docs/flows/`. The technical spec § 4.6 predicts **no change** to all of these.

**Delete** — none. **Never touch:** `app/**`, `lib/**`, `e2e/**`, `docs/journals/**`.

## Implementation Steps

1. Read phase 03's GREEN evidence. If GREEN was not reached, stop — do not document unshipped behavior.
2. Read the shipped files (`app/awards-information/**`, `lib/award-system.ts`,
   `lib/i18n/messages/{vi,en}-award-system.ts`) and confirm every claim before writing it.
3. Copy the three draft specs into their `docs/` homes; flip the status field and replace each
   `TBD (draft)` component/file placeholder in § 4.1 / § 4.2 / § 5.4 with the real path that shipped.
4. Register `SCR003_AwardSystem` in the screen spec and in `screen-list.md` (route `/awards-information`,
   states: `default`, `hash-seeded`, `reduced-motion`).
5. Add the F003 row + detail block to `feature-list.md`, status `implemented`, related screen `SCR003`,
   route `/awards-information`.
6. Append `US007_BrowseAwardSystem` and `US008_JumpToAwardCategory` to `user-stories.md` in the file's
   existing format.
7. Fix `route-list.md`: the `/awards-information` row now points at the real page component and belongs to
   F003; update the placeholder-count sentence from five to four.
8. Update `docs/_canonical-fcodes.json`: add the F003 entry (`slug F003_AwardSystem`, `screens
   [SCR003_AwardSystem]`, `user_stories [US007, US008]`, `routes ["/awards-information"]`) and remove that
   route from F002's list.
9. Mark the plan-folder draft as promoted (a one-line pointer to the `docs/` home) so the two copies cannot
   be mistaken for rivals.
10. Re-read every edited file end to end for broken links, wrong counts and stale cross-references.

## Todo List

- [ ] GREEN evidence confirmed before any doc is written
- [ ] Claims verified against shipped code, not against the draft
- [ ] `docs/features/F003_AwardSystem/{functional,technical}-spec.md` created, status promoted
- [ ] `docs/screens/SCR003_AwardSystem/spec.md` created
- [ ] `TBD (draft)` component/file references replaced with real shipped paths
- [ ] `feature-list.md` — F003 row + detail block
- [ ] `screen-list.md` — SCR003 block
- [ ] `route-list.md` — `/awards-information` row corrected, F002→F003, placeholder count 5→4
- [ ] `user-stories.md` — US007, US008
- [ ] `_canonical-fcodes.json` — F003 added, route moved off F002
- [ ] D001 / RISK-01 (test ID-1) and ID-14 (`/kudos` placeholder) carried forward verbatim
- [ ] `behavior-logic.md`, `permissions-matrix.md`, `architecture.md`, `permissions.md`, `flows/` checked; "no change" stated explicitly if unchanged
- [ ] Plan-folder draft marked promoted
- [ ] Links, dates and counts verified; every file under 800 lines

## Success Criteria

- `docs/features/F003_AwardSystem/` and `docs/screens/SCR003_AwardSystem/` exist and match F002's structure.
- Grepping `docs/` for `ComingSoon` no longer returns `/awards-information`.
- `docs/_canonical-fcodes.json` parses as valid JSON, contains F003, and lists `/awards-information` exactly
  once across all features.
- `US007`/`US008` appear exactly once each; no code is reused or skipped.
- Every relative link in the new and edited files resolves.
- The two unresolved items are still findable in `docs/` after promotion — not silently dropped.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Documenting behavior that did not ship | M×H — docs become fiction | Step 1 gates on GREEN; step 2 requires reading the shipped files. Where draft and code disagree, code wins. |
| Code collision — a parallel feature also claims `US007` or `SCR003` | L×H | `_canonical-fcodes.json` is the registry; check it immediately before writing and take the next free code if it moved. |
| Wholesale regeneration of a machine-owned `docs/generated/*` file churns unrelated rows | M×M | Surgical row edits only, per `documentation-management.md`. Diff must show only F003-related lines. |
| Creating `development-roadmap.md` / `project-changelog.md` because the rule names them | M×L — two orphan files nobody maintains | This project has no such files; sync the artifacts that exist and say so in the completion report. |
| The `/awards-information` route row is fixed but the placeholder-count sentence is not | M×L — internally contradictory docs | Both are named as one step (step 7) and one todo line. |
| The two open items get "resolved" by a documentarian's tidying instinct | L×H — a product decision silently made by a docs edit | They are carried forward **verbatim**; closing either is a product decision, out of this phase's authority. |
| Duplicate rival specs left in both the plan folder and `docs/` | M×M | Step 9 marks the plan copy promoted with a pointer to its `docs/` home. |

**Rollback:** `git checkout -- docs/` plus deleting the two new directories. Documentation-only — no runtime
impact, and the tested code is untouched by anything this phase does.

## Security Considerations

- No secret, token, credential, `.env` value, Supabase key or internal URL may enter `docs/`. The feature
  itself introduces none, so any appearance is a copy-paste accident.
- Documenting that `/awards-information` is public is a deliberate, correct statement of shipped design — it
  exposes no attack surface, since the screen carries only season-announcement copy (FR-601, BR-001).
- Do not document the ID-1 auth question as a "known auth hole". It is a product decision recorded as open
  (D001 / RISK-01), and framing it as a vulnerability would misrepresent the system's threat model.
- `permissions-matrix.md` / `docs/system/permissions.md` must stay accurate: no new permission, no new gate.

## Next Steps

- **Unblocks:** nothing — this is the terminal phase.
- **Hand-off:** report `Docs impact: major` with the file list, plus the codes registered (`F003`,
  `SCR003_AwardSystem`, `US007`, `US008`).
- **Follow-ups for a later plan, not this one:** the real `/kudos` screen (ID-14); the ID-1 auth decision
  (D001); **FUP-01** (opaque/blurred sticky header — `home-header.tsx`, hits `/` harder than this screen);
  **FUP-02** (`w-[60px]` unit column vs EN copy). No award-image re-export is needed — assumption A1 closed,
  the tester measured all six badges at exactly 336×336 against the frame.
