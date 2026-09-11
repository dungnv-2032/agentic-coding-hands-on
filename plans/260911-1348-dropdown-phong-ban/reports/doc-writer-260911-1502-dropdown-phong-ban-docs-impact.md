# Docs impact — Dropdown Phòng ban (MoMorph WXK5AYB_rG)

Verdict: **updated 3 files**.

## Verified before writing
- Read `app/kudos/_components/kudos-filter-menu.tsx` (61 lines) directly — confirmed
  `text-center`, `cursor-pointer`, `max-h-[348px]` gated on `scrollable`, no `gap-1`,
  header comment cross-referencing both `JWpsISMAaM` (hashtag) and `WXK5AYB_rG` (phòng ban)
  to the same Figma component `mms_A_Dropdown-List`.
- Note: clarifications.md said hover would get `transition-colors` added; the shipped
  className has no such class. Did **not** document a transition-colors claim — went with
  what the code actually shows.

## Changed

1. `docs/features/F004_KudosLiveBoard/functional-spec.md` (292→300 lines)
   - Added **FR-208..FR-213** to the `Kudos Live Board (2xx)` band (Requirements section,
     machine-owned, row-level add — no code family renumbered/removed).
   - Added FR-208..FR-213 to CAP-01's Requirements column.
   - Added 2 lines to "Edge Behaviours to Verify" for FR-211 (persistent highlight) and
     FR-213 (348px scroll bound).
   - Left FR-203/DEC-002 wording untouched — decided **not** to duplicate FR-210/FR-212 into
     Business Rules since DEC-002 already states the same select/toggle-off contract; the new
     FRs add listbox-level specificity (immediacy, presentation), not a new rule.

2. `docs/features/F004_KudosLiveBoard/technical-spec.md` (313 lines, no length change —
   substitutions only)
   - Action Index row A1 and § 3.1 header: added FR-208..FR-213 to the codes list.
   - DEC-002 table row "What user sees" cell: appended "dropdown đóng ngay khi chọn (FR-210)".

3. `docs/screens/SCR004_KudosLiveBoard/spec.md` (99→100 lines)
   - Added one UI-States row for the `open` state of `filter-menu-hashtag`/
     `filter-menu-department`, since the table previously had no row for the dropdown's own
     open/visual state — sourced to the real file
     `app/kudos/_components/kudos-filter-menu.tsx`.

## Left alone (with reason)

- `docs/flows/kudos-live-board-view-and-heart.md` — describes the read *sequence*
  (matchesFilters, reset paging, RLS), not listbox presentation. FR-208/209/213 are visual/
  layout facts already covered structurally by step 5's `FR-203`/`DEC-002` reference; no
  sequence change occurred (click→select→close→filter→re-click-clears was already the
  documented behavior). Adding presentational detail here would duplicate the screen spec.
- `docs/generated/route-list.md`, `feature-list.md`, `screen-list.md`, `entities.md`,
  `permissions-matrix.md`, `api-map.md`, `user-stories.md` — grepped for
  `filter-menu|dropdown|Dropdown` first; only hit was `behavior-logic.md:516`, an unrelated
  note about `filter_position NULL` departments never entering the dropdown (still true,
  untouched by this delta). No new route, entity, permission, or screen — confirmed against
  spec-delta § "Ngoài phạm vi" and against the actual diff (one component file + one e2e spec
  file). Per memory `project_stale-generated-artifacts.md`, `entities.md`/`overview.md`/
  `user-stories.md` are already known-frozen and correct-don't-regenerate; this delta gives no
  reason to touch them anyway.
- `docs/_canonical-fcodes.json` — not touched, per the task's own framing: no new F-code.
- `docs/system/architecture.md`, `docs/system/glossary.md`, `docs/system/permissions.md` —
  no new guard, no new permission code, no new architectural pattern; skipped.
- FR-203 itself — left verbatim rather than rewritten, since FR-208..213 are additive
  specificity, not a correction of FR-203.

## Unresolved
- None blocking. One observation only: clarifications.md documents a `transition-colors`
  decision that never made it into the shipped className — flagging for whoever owns the
  code, not fixing docs to match an aspiration the code doesn't have.

**Status:** DONE
**Summary:** Added FR-208..FR-213 (centered text, pointer/hover, immediate close, persistent
highlight, toggle-off, 348px bound) to F004's functional-spec and technical-spec surgically,
plus one UI-state row to SCR004's screen spec sourced to the real component file. Generated
layer, flows, and system docs confirmed unaffected — no new route/entity/permission/F-code.
**Concerns/Blockers:** None.
