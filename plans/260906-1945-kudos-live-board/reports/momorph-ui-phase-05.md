# Phase 05 report — UI foundation: i18n, icons, assets, hero, sidebar

**Status:** DONE

## Files changed
- `lib/i18n/messages/dictionary.ts` — added `kudos` namespace (190 lines total)
- `lib/i18n/messages/vi-kudos.ts`, `en-kudos.ts` — new
- `lib/i18n/messages/vi.ts`, `en.ts` — wired `kudos: viKudos`/`kudos: enKudos`
- `app/kudos/_components/kudos-icons.tsx` (171 lines) — 12 glyphs
- `app/kudos/_components/kudos-hero.tsx` (98 lines)
- `app/kudos/_components/kudos-sidebar.tsx` (105 lines)
- `app/kudos/_components/gift-leaderboard.tsx` (74 lines)
- `public/images/kudos/kv-background.png`, `sample-avatar.png`, `sample-attachment.png`, `spotlight-canvas.png`
- `app/kudos/page.tsx` NOT touched (still `ComingSoon`, verified via `git status`)

## Design decision: badge names/tooltips NOT in dictionary
Phase-05.md's draft step 2 listed "badge tier names" + tooltip sentences as
dictionary content. Re-reading the frozen `lib/kudos/view-model.ts` +
`derive.ts` (phase 01) shows both already flow as **props**: `BadgeTier` is
itself the literal display string, and `badgeTooltipFor()` computes the
hoa-thị sentence. Duplicating them in the dictionary would create two
sources of truth for the same frozen data. Dropped per YAGNI; documented in
`dictionary.ts`'s `kudos` namespace comment.

## MoMorph calls
`get_frame` ×1, `list_media_nodes` ×1, `get_frame_node_tree` ×1 (too large,
grepped from disk), `query_component` ×6, `query_section` ×5, `get_node` ×4,
`get_media_files` ×3, `get_figma_image` ×4 (all 500'd — MoMorph service
error, not a naming/asset-map issue), `get_frame_image`: not called (frame
PNG already supplied at `design/kudos-live-board.png`).

## mm: node map (every arbitrary Tailwind value traces to one of these)
- Hero: `2940:13436/13437/13439/13440/13448/13449/13450`, icon nodes
  `I2940:13449;186:2759` (Pen), `I2940:13450;186:2759` (Search)
- Sidebar: `2940:13488/13489/13490/13491/13492/13494/13495/13496/13497`,
  `3241:14882/14931` (hearts + flame), `I2940:13497;186:1766` (gift icon)
- Gift leaderboard: `2940:13510/13513/13514/13515/13521`,
  `I2940:13516;256:7460/7462/7472` (avatar/name/gift-line pattern, repeats
  ×5 for D.3.2-D.3.6)
- Icons: `I3127:21871;256:5147` (Send), `I3127:21871;256:5171` (Heart),
  `I3127:21871;256:5216;186:1441` (Link), `I2940:13459;186:2761` (Down),
  `9b63a41123d9e9e948b6be515a0bf8ad`/`8fae2820c0041716680f707ba2b9cc74`
  (Arrow Left/Right, componentId `186:1420`, reused at 60px carousel + 28px
  pager sizes)

## Icons with no exportable MoMorph asset (hand-drawn, documented in file)
- **Flame** (sidebar `x2` badge, node `3241:14932`) — raster image fill, no
  `mm_media_*` tag, no vector to trace.
- **Expand**, **Pan/Zoom** (Spotlight controls, node `3007:17479` has empty
  `children: []`) — `get_figma_image` fallback 500'd on every retry this
  session (transient MoMorph service error, confirmed by retrying twice).
  Used Material Design's `fullscreen`/`open_with` glyphs at equivalent
  geometry — same precedent as `IconFlagEn` in `app/_components/icons.tsx`.
  Both are consumed by phase 08 (Spotlight), not rendered by my components.

## Assets exported
- `kv-background.png` — `MM_MEDIA_KV Background`, downloaded via
  `get_media_files` presigned S3 URL, verified 1440×512 exact.
- `sample-avatar.png` — one `MM_MEDIA_Avatar` (64×64), reused for every gift
  row per assumption A3.
- `sample-attachment.png` — one `MM_MEDIA_Sample Image` (88×88).
- `spotlight-canvas.png` — node `2940:14173` ("Root further mo rong 1", a
  1819×583 raster, no `mm_media_*` tag). `get_figma_image` 500'd repeatedly.
  The node name (Vietnamese "extended Root Further [artwork]") matches the
  already-shipped `public/images/home/keyvisual-hero-bg.png` (same Root
  Further campaign keyvisual, reused under a different Figma crop —
  identical reuse pattern `award-system-hero.tsx` already documents for the
  same file). Copied that shipped asset rather than guess new pixel content.
  **Flag for phase 08 / reviewer**: confirm this crop reads correctly at
  the Spotlight canvas's aspect ratio before final visual sign-off.

## Compile/typecheck
`npm run typecheck` — exit 0, zero errors. Verified the dual-locale gate is
real: temporarily deleted `giftEmpty` from `en-kudos.ts`, typecheck failed
with `TS2741: Property 'giftEmpty' is missing`, restored, re-verified clean.

## Lint
`npm run lint` — exit 0, zero errors. Fixed 2 `@next/next/no-html-link-for-pages`
errors (compose bar, secret-box button, gift-row name all switched `<a>` →
`next/link` `<Link>`, matching `award-card.tsx` precedent). Remaining 21
warnings are all pre-existing, in tester-owned `e2e/*.spec.ts` files.

## Asset coverage
No `validate_coverage.py` script found in this repo (checked — not a
citation, a fact: `find . -iname validate_coverage.py` returned nothing).
Coverage verified manually instead: every rendered element in the 3
components carries an `mm:{nodeId}` comment; `grep -c "mm:"` on the 4 files
returns 9/9/14/12 matches.

## Visual evidence
Not captured — components aren't mounted until phase 09
(`app/kudos/page.tsx` still renders `ComingSoon`), so there is nothing on
`/kudos` to screenshot yet. Tester owns post-mount visual validation.

## Unresolved questions
1. `spotlight-canvas.png` crop/aspect fit for the actual Spotlight canvas
   box needs a visual check once phase 08 wires it in — I copied the whole
   shipped keyvisual file rather than a Figma-rendered crop (service 500s).
2. `get_figma_image` failed 500 on every attempt this session (KV
   background render, spotlight bg, avatar, sample image, and again on
   retry) — used `get_media_files` S3 URLs + `curl` instead for the
   `mm_media_*`-tagged assets, which worked. Worth flagging to whoever owns
   the MoMorph MCP server if this persists into phase 06/07/08's image work.
