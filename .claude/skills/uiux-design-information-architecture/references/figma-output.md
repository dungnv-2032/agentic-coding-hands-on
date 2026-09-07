# Stage 3 — push ia-spec.json to Figma artboards (`/figma-use`)

Goal: reproduce **what the viewer shows** as Figma artboards — the **hi-fi wireframe mock** (navy health-app tone), the **folder-tree sitemap**, and the **named user-flow** with wireframe-thumbnail cards. The Figma output should look like the `ia-design.html` viewer, not a grey skeleton.

> Fidelity = **visual match to the viewer** (`viewer/ia-editor.html` is the source of truth for colours, radii, shadows, and per-component widgets). Mirror its CSS values below.

## Prerequisites
- A **write-capable** Figma MCP (`use_figma` — Plugin-API JS). The read-only Framelink MCP (`get_figma_data` / `download_figma_images`) **cannot create content**; if only that is connected, tell the user to connect the `use_figma` MCP.
- **Load the `/figma-use` skill FIRST when available — mandatory before any `use_figma` call.** If `/figma-use` is NOT in the skill catalog, call `use_figma` directly and follow this playbook.
- Have the final `ia-spec.json` (the viewer embeds it; the file also sits next to `ia-design.html`).

## How it is triggered
- A **chat instruction** in Claude Code / Codex, e.g. 「このサイトマップ/画面を Figma に出して」, optionally with a Figma file URL. The skill reads `ia-spec.json` directly. The viewer is read-only — there is **no Figma button**.

## Design tokens — copy the viewer (Figma fills are 0–1 RGB; convert from hex)
**Hi-fi wireframe (navy / health-app — used for every screen frame):**
- navy `#3A4A66`, navy-dark `#2E3A52`, navy-soft `#EEF1F6`
- ink `#2F3A52`, mut `#9AA1AD`, faint `#B9BFC9`
- line `#EDEEF2`, line2 `#F3F4F7`, app-bg `#F3F4F7`, card `#FFFFFF`
- radii: card 16, small 12, pill 999; device-frame 34 (mobile) / 26 (tablet) / 12 (desktop)
- shadow (cards): y2 blur10 rgba(46,58,82,.06) + y1 blur3 rgba(46,58,82,.05) → Figma DROP_SHADOW effect
- fonts: load a JP face (see notes); titles 800 weight, body 500–700

**Sitemap + flow (Sun\* brand — used for the sitemap & flow frames):**
- Sun red `#FF2200`, darkred `#AD0C00`, gold `#B69256`, tint `#FFEEEC`
- ink `#1B1B20`, mut `#6B6B73`, faint `#9A9AA2`, border `#E7E7EC`, border2 `#F1F1F4`, bg `#FAFAFB`
- radii: 6 (cards) / 8 (large); red is the single accent — not a flood fill

## Mapping (ia-spec → Figma) — mirror the viewer tab-for-tab
| ia-spec | Figma artboard (looks like the viewer) |
|---|---|
| `meta.device` | device frame: mobile 375×812, tablet 834×1112, desktop/responsive 1440×1024. Rounded device shell with navy app-bg, same as the viewer's `.hf-frame`. |
| each `screens[]` | one frame titled `name`, built from **`components[]`** (header/search/list/table/cards/form/button/image/text/footer) stacked top→bottom as the viewer's hi-fi widgets (see widget specs). If `components` absent, infer from `layoutBlocks` + `infoPriority`. |
| screen header | `.hf-header`: round back button + bold 19px title + 11.5px subtitle (`summary`). |
| mobile/tablet | top **status bar** (time + signal/battery) and bottom **tab bar** from `navigation.global` (navy active item). Center **FAB only when `screens[].fab: true`**. `platform:"web"` screens: **browser URL bar** below the status bar instead of a tab bar. |
| desktop | app screens (`platform` absent/`"app"`): **left sidebar nav** from `navigation.global`. `platform:"web"` screens: **top nav** website layout (logo mark + nav links, active = navy-soft pill + round account avatar). No browser chrome. |
| `screens[].primaryAction` | navy filled **button** (`.hf-btn`, radius 15, white text) near the bottom. |
| `screens[].role`+`priority` | small tag on the frame title; priority also tints a top accent on the sitemap card (Must=red, Should=gold, Could=grey). |
| `navigation.global`+`section`+`parent` | **Sitemap** frame as a **folder tree**: red root pill → tinted section cards (folder icon + "N画面") → white screen cards (priority top-accent + mini wireframe thumbnail + name). Connector lines **drop from under each folder/parent icon** and elbow to children (any depth via `parent`). |
| `transitions[]` | **flow** frames grouped by `flow` name: each flow = a label header (red bar + name + メイン/サブ tag) then wireframe-thumbnail cards (`flowCard`: name + mini wire + ▸primaryAction) connected by arrows labelled with `condition`. `kind:"sub"` uses the gold/サブ styling; unnamed subs render as individual from→to branch rows. |
| `prd.personas[]` | (only if the user asks for PRD frames) persona card with round avatar — use `image` (data URI / path) as an image fill, else a tinted initial. |

Optional extra frames if the user asks: 業務フロー (swimlane from `businessFlow`), ストーリーマップ (`userStoryMap` grid), 情報構造 (`cardSort` / `objects`), PRD slides.

## Widget specs (match `.hf-*` in the viewer)
- **cards/stat**: white rounded-16 card, soft shadow, label (mut 10.5px) + big number (800, 26px) + optional progress bar (navy fill on line2 track).
- **list rows**: white rounded-12 row, left avatar (navy-soft square, initial), title (700) + meta (mut), right chevron / `.hf-badge` (navy-soft pill).
- **form fields**: 46px rounded-14 input, label with navy `*`, placeholder in faint; password shows dots + eye.
- **table**: header row line2 bg + mut caps; cells with optional inline bars.
- **search**: rounded pill input with leading magnifier glyph.
- **image**: rounded card with diagonal hatch + centered icon.
- Keep widgets **domain-neutral**, driven by each component's `items` (labels, sample values) — same as the viewer.

## Procedure
1. **Load `/figma-use` if available** (mandatory before `use_figma`); otherwise call `use_figma` directly.
2. Decide target: a new file (`create_new_file`) or the file the user names (extract `fileKey` from the URL; for an existing file, `get_metadata` to find current content bottom-Y and **offset new content below it** with a clear section title).
3. **One frame per screen** (default: all `screens[]`, or only those named). Build each at device size with the navy hi-fi styling above: status/tab bars (or top nav for desktop), header, stacked component widgets, primary-action button.
4. Arrange frames in reading order (Must → Should → Could), wrapping into rows; keep parent screens left of their sub-screens.
5. Add the **Sitemap** frame as the folder tree (red root → tinted section folders → screen cards with mini wireframes + priority accents + connector lines from under folder icons).
6. Add the **flow** frames grouped by `flow` name (label header + wireframe-thumbnail cards + condition-labelled arrows; sub = gold).
7. Return the **Figma file URL**; optionally `get_screenshot` to confirm it matches the viewer.

## use_figma implementation notes (learned in practice)
- `use_figma` executes **Plugin-API JavaScript**. Build frames programmatically from the spec rather than via a prose brief — more reliable.
- **Japanese fonts:** never assume "Inter". Call `figma.listAvailableFontsAsync()`, pick the first available of `["Noto Sans JP","Noto Sans CJK JP","Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic","Meiryo","Inter"]`, and load its real Regular + Bold style names before creating any text (set `fontName` before `characters`).
- **Colours:** convert each hex token above to `{r,g,b}` 0–1 floats for `fills`. Apply card radius via `cornerRadius`, and the card shadow via an `effects` DROP_SHADOW entry.
- **`createPage` may not persist** in a headless MCP run — append to `figma.currentPage`, read existing content first (`get_metadata`), and offset the new block below it; add a clear title text.
- Embed a **reduced** spec (only the fields used) as a JSON string inside the code (the `code` arg caps at 50000 chars). For many screens, split across several `use_figma` calls (e.g. per section / per batch of frames).
- Use auto-layout (`layoutMode`) for screen internals; `layoutAlign:'STRETCH'` + `textAutoResize:'HEIGHT'` makes text wrap inside blocks.
- Verify with `get_metadata` (structure + that JP text isn't tofu) and optionally `get_screenshot` (compare against the viewer).

## Notes
- **Visual fidelity = match the viewer.** Use the brand colours, radii, and shadows above — this is intentional (the viewer is the design reference), not free-form visual design. Do not invent a new look; reproduce `ia-editor.html`.
- Scope to the user's request: if they only want the sitemap, build only the Sitemap frame; if only specific screens, build only those.
- If no write-capable Figma MCP is connected, tell the user to run it where `use_figma` is available.
