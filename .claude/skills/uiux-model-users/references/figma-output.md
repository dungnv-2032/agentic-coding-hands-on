# Stage 3 — push um-spec.json to Figma (match the HTML viewer)

Goal: reproduce **what the `um-model.html` viewer shows** as Figma frames — same Sun\* brand,
same card layouts — so the Figma output and the HTML display line up. This is **not** low-fidelity:
match the viewer's visual design as closely as the Plugin API allows.

## Prerequisites
- Figma MCP connected (`mcp__claude_ai_Figma__*`: `use_figma`, `get_metadata`, `get_screenshot`, `create_new_file`).
- **Load the `/figma-use` skill FIRST when available — mandatory before any `use_figma` call.** If it isn't registered, call `use_figma` directly and follow this playbook.
- Have the final `um-spec.json` (it sits next to `um-model.html`).

## How it is triggered
- A **chat instruction**, e.g. 「このユーザーモデルを Figma に出して」「ペルソナを Figma に」. The viewer is read-only — there is no Figma button; the skill reads `um-spec.json` directly.

## Design tokens — copy the viewer exactly
These mirror `viewer/um-viewer.html`. Use them for every frame.

| token | value |
|---|---|
| Sun Red (primary accent) | `#FF2200` |
| dark red | `#AD0C00` |
| gold (secondary / positive) | `#B69256` |
| ink (text / dark headers) | `#1A1A1A` (journey stage header `#2B2B30`) |
| muted text | `#666666` / micro-labels `#A3A3AB` |
| card border | `#ECECEF` ・ hairline divider `#F2F2F5` |
| page bg / chips bg | `#F7F7F7` |
| tint (red wash) | `#FFEEEC` ・ gold wash `#F4ECD9` |
| font | **Noto Sans JP** (Bold 700/800 for headings, Regular 400 body) |
| card | white fill, 1px `#ECECEF` border, **4px** corner radius, soft shadow `0 1px 6px rgba(0,0,0,.06)` |
| priority / emotion left accent | 3px bar — Must/pain `#FF2200`, Should/positive `#B69256`, Could/neutral `#C4C4CC` |
| type badge pill | 99px radius; primary = tint bg + dark-red text, secondary = gold wash + brown text, anti = grey |

Layout rhythm: generous padding (card 18–26px), section micro-headers are 9–10px uppercase, letter-spacing ~.08em, muted.

## Mapping (um-spec → Figma frames)
Build **one section per artifact present**, laid left→right or top→down on the canvas. Skip artifacts absent from the spec.

| um-spec | Figma frame (match the tab) |
|---|---|
| `meta` + `personas` | **ターゲットユーザー像** card: segment as a big lead (24px/800) — but if it splits into multiple segments (array, or a string with ＋/＆/、 top-level separators) render a **bulleted list** (one line per 像, red square marker) instead of one run-on title; then a business-goal pill, then a line-up row — one card per non-anti persona (avatar circle + name + type badge + tagline, left accent by type). Anti personas in a muted "対象外" strip below. |
| each `personas[]` | one **persona card** (mirror the ペルソナ slide): avatar (photo via `image` else a tinted circle with initial), name + type badge, demographics row, bio (muted), then a 2-col grid of goals / frustrations / behaviors / needs(chips), and a 利用シーン box. **Omit the quote, motivations, and channels — they are intentionally not shown** (keeps a persona readable in one slide). **Cap each list to the first 2 items (overflow hidden, no "+N")** — same as the viewer. Top border 3px by type (primary red / secondary gold / anti grey). |
| each `empathyMaps[]` | **エンパシーマップ**: persona header, a 2×2 grid (SAYS / THINKS / DOES / FEELS) each a bordered card with an icon chip + bullet list, then a Pains (tint) / Gains (gold wash) two-column band. |
| each `journeys[]` | **カスタマージャーニー**: an **emotion curve** — a polyline across the stages plotted from `emotionScore` (-2..2, y), dots colored gold(+)/red(−)/white-ink(0) with a face emoji (😣🙁😐🙂😄) above each; below it a row of **stage cards** (dark header with name+goal, body with an inner left accent line in the emotion color, groups 行動/接点/思考/課題(red)/改善機会(gold)). |
| each `insights[]` | **インサイト** card: title + impact pill (high red / medium gold / low grey), a vertical 観察→気づき→示唆 flow (dotted connector, colored dots), an evidence box (muted, italic quotes), and a **How Might We** box on tint. |
| `storyMap` | **ストーリーマップ** grid: top dark **activity** row (spanning its tasks) + tint **task** row (backbone, left→right), then one **release band** per `releases` (first = red "MVP" pill). Each cell holds story cards (left accent by priority, persona avatar + title + → soThat). |

Avatars: if a persona has `image`, place it (`create_new_file`/`upload_assets` or an ellipse image fill from the data URI); otherwise a tinted circle with a person glyph or the name's initial — same as the viewer's generated SVG avatar.

## Procedure
1. **Load `/figma-use` if available** (mandatory before `use_figma`); else call `use_figma` directly.
2. Target: a new file (`create_new_file`) or an existing file the user names (extract `fileKey` from the URL). Confirm before creating.
3. Scope to the request: all artifacts (default) or only those named (e.g. only personas). Build each present artifact as its own frame using the tokens above.
4. Arrange frames in tab order — ターゲット/ペルソナ → エンパシー → ジャーニー → インサイト → ストーリーマップ — as titled sections down the canvas.
5. Return the **Figma file URL**; optionally `get_screenshot` to confirm it matches the HTML.

## use_figma implementation notes (learned in practice)
- `use_figma` runs **Plugin-API JavaScript**. Build frames programmatically from a reduced spec embedded as a JSON string (the `code` arg caps ~50000 chars — split into multiple calls per artifact if large).
- **Japanese fonts:** never assume "Inter". Call `figma.listAvailableFontsAsync()`, pick the first available of `["Noto Sans JP","Noto Sans CJK JP","Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic","Meiryo","Inter"]`, and load its real Regular + Bold style names before any text (set `fontName` before `characters`).
- **Color emoji** (journey faces): Figma may not render color emoji; if tofu, fall back to a small colored dot + a JP label, or draw a simple SVG face — keep the emotion read.
- Use **auto-layout** (`layoutMode`, `itemSpacing`, `padding*`) for cards and grids; `layoutAlign:'STRETCH'` + `textAutoResize:'HEIGHT'` wraps text. Corner radius 4, strokes `#ECECEF`, the soft shadow as an effect.
- **`createPage` may not persist** in headless MCP — append to `figma.currentPage`; read existing content bottom (`get_metadata`) and offset new frames below it with a title.
- Verify with `get_metadata` (structure + JP text not tofu) and `get_screenshot` (compare against `um-model.html`).

## Notes
- This stage is **high-fidelity by design** — match the viewer's brand and layout. (Contrast: the sibling IA skill ships low-fi skeletons.)
- If the Figma MCP is unavailable, tell the user to run it where Figma MCP is connected.
