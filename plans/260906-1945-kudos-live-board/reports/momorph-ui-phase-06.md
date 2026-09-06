# Phase 06 — Kudos card family — implementation report

## Files (all new, all ≤200 lines)
- `app/kudos/_components/sunner-chip.tsx` (75 lines)
- `app/kudos/_components/kudos-hashtag-row.tsx` (49 lines)
- `app/kudos/_components/kudos-attachments.tsx` (37 lines)
- `app/kudos/_components/kudos-card-actions.tsx` (124 lines)
- `app/kudos/_components/kudos-card.tsx` (137 lines)

## MoMorph calls
`get_overview` ×1 · `query_section` ×7 · `get_node` ×2 · `list_media_nodes` ×1. No `get_figma_image`
call needed — `query_section`/`get_node` gave exact styles for every node touched.

## mm:{nodeId} map (key nodes; full list in-file)
- `256:4830` sunner chip (`3106:17694` badge, `256:4734` avatar) → `sunner-chip.tsx`
- `256:4857`/`256:5645`/`256:5194` info/content/action rows, `256:5147` send glyph,
  `2234:33038`/`33040` campaign+pen, `662:11382` message box, `256:5176` attachments,
  `256:5158` hashtag row, `256:5175` hearts, `256:5216` copy-link, `335:9663` "Xem chi tiết"
  → `kudos-card.tsx` / `kudos-card-actions.tsx` / `kudos-attachments.tsx` / `kudos-hashtag-row.tsx`
- `335:9620` (KUDO - Highlight, 528px/4px border/16px radius) vs `256:5231` (C.3_KUDO Post, no
  border/24px radius) — confirmed by direct query, not assumed; encoded as `VARIANT_SHELL`.

## Test hooks emitted (14/14 per test-contract.md)
`kudos-card`, `kudos-sender`, `kudos-receiver`, `sunner-badge`, `sunner-badge-receiver`,
`kudos-time`, `kudos-campaign`, `kudos-body`, `kudos-image`, `kudos-hashtag`, `kudos-heart`,
`kudos-heart-count`, `kudos-copy-link`, `kudos-detail-link`, `kudos-edit`. Verified via grep: each
appears exactly once per element path, no element carries two testids.

## Key decisions
- **`kudos-edit` gated `variant === "feed" && isOwnedByViewer`**, not just `isOwnedByViewer`. The
  frame's highlight component (`335:9620`) draws the campaign row as a bare `TEXT` node; the feed
  component (`256:5231`) draws it as a `FRAME` wrapping the text *and* `MM_MEDIA_Pen`. The design
  itself never shows the pen on a highlight card — confirmed by direct node query, not inferred.
- **`kudos-detail-link` icon**: node `186:2691` (componentSet `178:1020`, same set as the carousel
  arrows) carries no `MM_MEDIA_*` name and no exportable geometry beyond generic "IC". Reused the
  already-shipped `IconArrowRight` rather than hand-drawing a near-duplicate glyph (YAGNI).
- **Message box color**: sampled CSS var `rgba(255,234,158,0.4)` over card bg `#FFF8E1` flattens
  to `#FFF2C6`, matching clarifications.md's resolved literal exactly — used the literal directly.
- **Heart/count state**: seeded from `card.likedByViewer`/`card.hearts`, overwritten only by
  `toggleLike`'s resolved `{liked, hearts}` — never a local increment, per the Supabase amendment's
  "not component-local state" rule. `disabled={!card.canLike}` verbatim, no recomputation.
- **Copy Link clipboard-denied path** (recorded open question, clarifications § Copy link): catch
  the rejection and call `onCopyLink(false)` instead of throwing; `onCopyLink(true)` on success.
  Chose a boolean over silent swallow because the dictionary already ships both
  `toast.copySuccess`/`copyFailure` — phase 07 can pick either without a second callback.
- **No `"use client"`** on `kudos-card-actions.tsx` or `kudos-hashtag-row.tsx`, per plan.md's
  explicit instruction for the former, applied consistently to the latter (same onClick
  constraint). Both are documented as reachable only through phase 07's future client boundary;
  `kudos-card.tsx` stays a plain server-composable function importing them directly.

## Checks
- `npm run typecheck` → **0 errors**, exit 0 (repo-wide).
- `npm run lint` → exit 0. 21 pre-existing warnings in `e2e/*.spec.ts` (unused testid-locator vars
  for hooks not yet asserted, and `e2e/homepage*.spec.ts` unused `Page` import) — none in owned
  files, none introduced by this phase.
- Asset coverage: every `mm:` comment present (grep count: 15/9/9/3/3 across the five files);
  every raster src (`avatarUrl`, `imageUrl`) is prop-driven from `KudosCardView`, never hardcoded.
- Confirmed no file imports these five components yet (`app/kudos/page.tsx` unchanged, still
  `ComingSoon`) — e2e stays RED for the expected reason (25 failed / 2 passed, unchanged).

## Unresolved questions
1. Badge pill background: the frame's tier badges use per-tier raster/gradient fills with no
   `MM_MEDIA_*` export tag (same gap phase 05 hit for `IconFlame`/`IconExpand`). Rendered as a
   flat `bg-black/30` + gold border approximation instead. Flagged for the tester's visual pass,
   not a functional gap.
2. Card width on `feed` variant: design shows a fixed 680px card inside a 1152px column; kept
   `w-full` since phase 07 (the board/list) owns the actual column width the card sits in.

**Status:** DONE
**Mode:** section
**Test policy:** e2e-red-first
**Files changed:** `app/kudos/_components/kudos-card.tsx`, `app/kudos/_components/sunner-chip.tsx`, `app/kudos/_components/kudos-card-actions.tsx`, `app/kudos/_components/kudos-attachments.tsx`, `app/kudos/_components/kudos-hashtag-row.tsx`
**MoMorph calls:** get_overview ×1, query_section ×7, get_node ×2, list_media_nodes ×1
**Design evidence:** live MCP queries above; `plans/260906-1945-kudos-live-board/clarifications.md`; `plans/260906-1945-kudos-live-board/test-contract.md`
**Compile/typecheck:** `npm run typecheck` — exit 0, 0 errors
**Lint:** `npm run lint` — exit 0, no new warnings/errors
**Asset coverage:** manual grep verification — mm: comments and 14/14 test hooks confirmed present, no duplicate testids
**Visual evidence:** delegated — components not yet mounted (phase 09 wires the page); tester owns the visual pass once phase 07/09 compose them
**RED evidence:** validated — redTestFiles/redCommand/redExitCode/redFailure as given in task prompt; confirmed unchanged (no file in this phase is imported anywhere yet)
**GREEN handoff:** not-applicable this phase — GREEN depends on phase 07 (composition) and phase 09 (page wiring); tester reruns `npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts --reporter=list` once those land
**Concerns/blockers:** none blocking; two open items noted above (badge pill art, feed card width) left for the tester's visual pass
