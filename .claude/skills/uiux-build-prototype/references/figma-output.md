# Stage 5 — push the prototype to Figma (match the React screens)

Goal: reproduce **what the prototype shows** as Figma frames — the screens in the **product's own
design tokens** (from `pt-spec.design`, NOT Sun\*), laid out by flow with transition connectors — so
designers can take over in their tool without losing fidelity or grounding.

## Prerequisites
- Figma MCP connected (`use_figma`, `get_metadata`, `get_screenshot`, `create_new_file`).
- **Load the `/figma-use` skill FIRST when available — mandatory before any `use_figma` call.** If it
  isn't registered, call `use_figma` directly and follow this playbook.
- Have the final project: `pt-spec.json` (grounding/tokens) + `src/screens/*.tsx` (the screens themselves).

## How it is triggered
A chat instruction, e.g. 「このプロトタイプを Figma に出して」「画面を Figma に」.
Confirm the target Figma file (new via `create_new_file`, or an existing fileKey) before creating.
Scope to the request: all screens (default), one flow, or named screens.

## Design tokens — use the PRODUCT's, not Sun\*'s
Every value comes from `pt-spec.design`（= `globals.css :root` と同値）:

| Figma property | pt-spec source |
|---|---|
| frame background | `design.colors.bg` |
| card/surface fills | `design.colors.surface`, 1px stroke `design.colors.border` |
| text fills | `design.colors.text` / `textSub`; on-primary text `primaryText` |
| primary buttons / accents | `design.colors.primary` (+ `accent` if set) |
| status colors | `success` / `warning` / `danger` |
| font | `design.typography.family` (fallback chain below), sizes from `typography.scale` |
| corner radius | `design.shape.radius` |
| shadow effect | `design.shape.shadow` |
| padding rhythm | `design.shape.density` — comfortable=16 / compact=10 |

## Mapping (pt-spec → Figma)
| pt-spec | Figma |
|---|---|
| each `screens[]` | one **screen frame** at device size (mobile 390×844 / tablet 834×1194 / desktop 1280×800, from `device`), rebuilt with auto-layout to match `src/screens/<id>.tsx` — same content, same mock data, same order. Frame name = `id — name`. |
| `screens[].states` beyond default | OPTIONAL variant frames (`id — empty` …) to the right of the default frame; build on request or when a state is central to the review. |
| `transitions` | **connector arrows** between frames (or thin line+triangle vectors if connectors are unavailable): solid = `kind:main`, dashed = `sub`, label = `condition`. Arrange frames left→right per `flow`, one row per flow, flow name as a section title. |
| `grounding` | a small **annotation card** under each frame (muted): IA screen / personas / reqs / assumptions — the trace stays visible in Figma. |
| `design` | one **token sheet frame** first: color swatches (name + hex), type scale samples, radius/shadow/density samples, `notes`, `source`. |

## Procedure
1. **Load `/figma-use` if available** (mandatory before `use_figma`); else call `use_figma` directly.
2. Confirm target file; read existing content (`get_metadata`) and place new frames below it.
3. Build: token sheet → screens grouped by flow (left→right, connectors + condition labels) → grounding annotation cards.
4. Verify with `get_metadata` (structure, JP text not tofu) and `get_screenshot` — compare against the dev-server screens.
5. Return the **Figma file URL** and note any fidelity compromises.

## use_figma implementation notes (learned in practice)
- `use_figma` runs **Plugin-API JavaScript**. Embed a reduced spec as a JSON string in the code; the
  `code` arg caps ~50000 chars — split into multiple calls (token sheet / per-flow batches) if large.
- **Japanese fonts:** never assume "Inter". Call `figma.listAvailableFontsAsync()`, pick the first
  available of `[design.typography.family, "Noto Sans JP", "Noto Sans CJK JP", "Hiragino Kaku Gothic ProN",
  "Hiragino Sans", "Yu Gothic", "Meiryo", "Inter"]`, and load its real Regular + Bold style names before
  setting any `characters`.
- Use **auto-layout** (`layoutMode`, `itemSpacing`, `padding*`) for every card/list; `layoutAlign:'STRETCH'`
  + `textAutoResize:'HEIGHT'` wraps text.
- **`createPage` may not persist** in headless MCP — append to `figma.currentPage` and offset new frames
  below existing content with a title text node.
- Screens are React components — do NOT try to parse TSX in plugin code. Instead, **you** (the agent)
  read each `src/screens/<id>.tsx` (+ the components it composes) and hand-translate its structure into frame-building code (regions → auto-layout
  frames, rows → child frames, text → text nodes with the right token fills). Fidelity target: a reviewer
  can't tell the Figma frame from a prototype screenshot at a glance.

## Notes
- This stage is **high-fidelity by design** — match the prototype, in the product's brand.
- If the Figma MCP is unavailable, tell the user to run this where the Figma MCP is connected.
