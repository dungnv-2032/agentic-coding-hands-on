# Subagent Prompt Template

Template for `momorph-ui-implementer` work. The orchestrator fills in real values and spawns `Agent(subagent_type="momorph-ui-implementer")`; generic `implementer` is never used for section, screen correction, or polish work.

## Template

```
## Task
Implement the assigned MoMorph UI contract, following Figma pixel-perfect with a 1-1 mapping from nodeId to element.

## Execution contract
- mode: {section|screen|polish}
- workKind: {initial|composition|correction|polish}
- testPolicy: {visual-contract|e2e-red-first}
- ownedFiles: {exact_paths_this_agent_may_edit}
- projectRoot: {project_root}
- stack: {stack}

Mode boundaries:
- `section`: implement/correct only `{sectionId}` and its assigned component files.
- `screen`: compose the root or correct a discrepancy spanning assigned sections.
- `polish`: apply `polish-rules.md` only to the supplied pixel-perfect files.

Delegation boundary:
- `screen` is the only mode that may invoke `Agent`. It may delegate only
  `Agent(momorph-ui-implementer)` tasks carrying `mode: section`, plus
  `Agent(tester)` verification tasks.
- `section` and `polish` must never invoke `Agent` or recurse, even though the
  shared agent frontmatter exposes the restricted allowlist.
- Never delegate to generic `implementer`, another `screen`/`polish` worker, or
  any agent type outside `momorph-ui-implementer` and `tester`.

Do not edit before all contract fields are present. Do not change files outside `ownedFiles`.

## Section
- fileKey: {fileKey}
- screenId: {screenId}
- sectionId: {sectionId}
- sectionName: {sectionName}
- Output file: {component_path}/{section-slug}.{ext}
- Project assets dir: {project_assets_out}    ← used for fallback asset save (see code procedure step 2)
- Asset code-path prefix: {code_path_prefix}  ← import path prefix (e.g. `/home`, `@/assets/home`)

Stack/styling/naming → infer from project files.

## Slim subtree (extracted from get_frame_node_tree)
```json
{embed_section_slim_tree_from_overview}
```
↑ This tree shapes the layout and identifies media nodes early. Style/details → query MCP when needed.

For `screen` or `polish` mode, replace this block with the relevant section reports, current file list, visual-diff findings, and breakpoint convention. Do not provide an unrelated full-frame dump.

## Asset mapping
File: {plan_dir}/data/assets.md (mapping nodeId → file path).
Path is a **plan** — file may still be downloading in the background. Use the path as-is, no need to check existence.

## Verification contract

- testRunner: {runner_name|none}
- redEvidence: {not-applicable (visual-contract)|validated}
- redTestFiles: {paths|not-applicable}
- redCommand: {exact_command|not-applicable}
- redExitCode: {non_zero_integer|not-applicable}
- redFailure: {expected_missing_behavior_assertion|not-applicable}
- plannedChecks: {compile_or_typecheck, lint, asset_coverage, visual_validation}
- visualState: {initial|post_interaction_description|not_applicable}
- setupSteps: {ordered_actions_before_screenshot|none}

Rules:
- `visual-contract`: code-first is intentional and is not TDD. Require `redEvidence: not-applicable (visual-contract)` and complete every available post-code check.
- `e2e-red-first`: do not edit until all RED fields are present and the failure is an expected assertion caused by missing behavior. Dependency, syntax, environment, or server-start failures do not qualify.
- No runner under strict policy: return `BLOCKED`; never scaffold one or downgrade policy.
- `e2e-red-first` is web-only. For mobile, return `BLOCKED` and request an explicit switch to `visual-contract`; do not downgrade automatically or substitute browser Playwright.
- `tester`, not this agent, owns RED/GREEN execution and Playwright/native screenshot evidence.
- Visual evidence is valid only when tester executes `setupSteps` and captures
  the same `visualState` represented by the reference image.
- Respect the mode-specific delegation boundary above. A `section` or `polish`
  agent must not recurse; a `screen` agent may delegate only same-agent
  `mode: section` work and `tester` verification.

## MCP toolkit (REQUIRED — DO NOT guess values)

| Tool | When to use |
|------|-------------|
| `mcp__momorph__get_frame_node_tree(screenId, includeSpecs?)` | One fallback full-tree call when the embedded branch is insufficient; filter locally and do not repeat |
| `mcp__momorph__get_node(screenId, nodeId)` | Full node detail INCLUDING STYLE (color, font, padding, radius, shadow...) |
| `mcp__momorph__get_node_context(screenId, nodeId, includeSiblingStyles?)` | Node + parent + siblings + optional sibling styles — when role is unclear |
| `mcp__momorph__list_design_items(screenId)` | List design items when a component or variant must be located |
| `mcp__momorph__get_related_design_items(screenId, designItemId, limit?)` | Find related variants after choosing a design item |
| `mcp__momorph__get_figma_image(fileKey, nodeIds, format?, outputType?, scale?)` | **ONLY for fallback case**: a node named `mm_media_*` with NO row in `assets.md`. Pass `nodeIds` as a list, using `format='svg'` for icons or `'png'` for raster. Save the file to `{project_assets_out}/` named `{slug-from-node-name-strip-mm_media_}.{ext}`. |

**DO NOT call** `get_overview` (already embedded), `get_media_files` (orchestrator already handled it).
**DO NOT call** `get_figma_image` outside the fallback case above (Figma rate limits are strict). DO NOT use it for preview/screenshot reference.

## Code procedure

1. Validate `mode`, `testPolicy`, owned files, and verification evidence. Under strict policy, stop before edits if RED is invalid.
2. Read the mode context:
   - `section`: embedded slim subtree → shape the layout + identify media nodes (`mm_media_*`).
   - `screen`: section reports/components + visual finding → compose or correct only assigned files.
   - `polish`: current pixel-perfect files + breakpoint convention → follow `polish-rules.md` without redesign.
3. For `section` mode, recurse the tree:
   - Media node (`mm_media_*`) → look up `assets.md` for the path:
     - **Raster (png/jpg/webp)** → emit `<img>` / `next/image` / native `Image` element.
     - **SVG icon (web stack)** → read the SVG file content with the `Read` tool → inline into JSX → replace solid fill/stroke with `currentColor` → wrap in a component (see rule 2a in `code-rules.md`). Set `color` from the icon node's Figma `fills` (query `get_node` to get the color).
     - **SVG (mobile stack)** → use `react-native-svg` / `flutter_svg` / `Image.template` with a color prop from the Figma fills.
   - **Fallback** — `mm_media_*` node has NO row in `assets.md` (file not yet uploaded to Figma cloud):
     - Call `mcp__momorph__get_figma_image(fileKey, nodeIds=[nodeId], format='svg' for icons | 'png' for raster)` → receive URL/bytes.
     - Save the file to `{project_assets_out}/{slug-from-node-name-strip-mm_media_}.{ext}` (download the URL if a URL is returned, or write bytes directly). Use `bash curl` or the `Write` tool.
     - Code imports from `{code_path_prefix}/{slug-from-node-name-strip-mm_media_}.{ext}` (same convention).
     - Note in the report: "Fallback get_figma_image: [list of nodeIds]" so the orchestrator is aware.
   - STOP recursion into children of media nodes.
   - FRAME with children → wrapper element + recurse.
   - TEXT → text element with `characters` from `get_node` + style.
4. For every node needing styles → `mcp__momorph__get_node(screenId, nodeId)` → apply real values. For SVG icons, also query the node's `fills` to obtain the color and apply it on the parent (CSS `color`).
5. Slim subtree not deep enough → call `mcp__momorph__get_frame_node_tree(screenId, includeSpecs?)` once, then filter the needed branch locally.
6. Confused about a node's role (e.g. background vs overlay?) → `mcp__momorph__get_node_context(screenId, nodeId, includeSiblingStyles?)`.
7. Run the assigned compile/typecheck, lint, and coverage checks. Record exact commands and exit codes; do not run or self-certify GREEN.

## Required rules

Read + follow: `.claude/skills/momorph-implement-design/references/code-rules.md`

Summary:
- Each element has a **comment marker** immediately before (universal, NO runtime leak): `// mm:{nodeId}` (every stack) or `{/* mm:{nodeId} */}` (JSX inline). DO NOT use `data-mm-id`/`accessibilityLabel`.
- Raster media → `<img>`/`Image`. **SVG media (web) → inline JSX + `currentColor` + parent `color` from Figma `fills`** (rule 2a — DO NOT use `<img>` for SVG icons).
- Wrapper around an asset must match its shape (radius/shadow follow the asset).
- TEXT keeps `characters` exactly, DO NOT translate.
- Root frame defaults to FILL (full width), do not fix design width.

## ⚠️ Anti-pitfall checklist (REQUIRED before reporting DONE)

These 5 errors account for 90% of failures. **MUST** verify all 5 before returning DONE:

1. **FONT** — every TEXT node has been queried with `get_node` for real `fontFamily`/`fontSize`/`fontWeight`/`lineHeight`/`letterSpacing` + font loaded via the proper loader (next/font, expo-font, pubspec, ...)? DO NOT leave defaults.
2. **WRAPPER RADIUS** — every wrapper around media (with shadow/border/background) has `border-radius` matching the inner asset? When unsure → `get_node_context(screenId, asset_nodeId, includeSiblingStyles=true)` to compare `cornerRadius` of parent vs asset.
3. **ALIGNMENT** — every auto-layout FRAME has been queried for `primaryAxisAlignItems` + `counterAxisAlignItems` → applied `justify-content`/`align-items` correctly. TEXT with `textAlignHorizontal` → applied `text-align`. DO NOT default to left.
4. **FILL VIEWPORT + CONTAINERED LAYOUT** — two sides of the same rule:
   (a) Root section **DOES NOT** hardcode `width: {designWidth}px` → use `width: 100%` so the background fills the viewport.
   (b) If a section contains a FIXED-width node narrower than the artboard and centered (parent `counterAxisAlignItems: CENTER`) → that's a **content container** → use `max-width: Npx + margin: 0 auto + width: 100%` (NOT a rigid `width: Npx`).
   Common bug: using `width: Npx` for a content container → content sticks to the left / off-center. See rule 3 + Containered layout in `code-rules.md`.
5. **ICON COLOR** — every SVG icon (`mm_media_*`, file `.svg`) on web stack has been:
   (a) inlined as JSX (NOT `<img>`),
   (b) solid `fill`/`stroke` replaced with `currentColor` (preserve `none`, gradients, multi-color),
   (c) `color: <hex>` from Figma `fills` (query `get_node` of the icon node or the closest ancestor with a fill) applied on the parent.
   → Default white / wrong color = FAIL. See rule 2a in `code-rules.md`.

In the report write: `Anti-pitfall: ✓ font ✓ radius ✓ alignment ✓ fill-viewport+container ✓ icon-color` (or note clearly which item is not OK).

## Output report

- Files created: [paths]
- Mode: [section | screen | polish]
- Test policy: [visual-contract | e2e-red-first]
- Component tree: [brief summary]
- Props/data interface: [if external data is needed]
- Anti-pitfall: [✓ font ✓ radius ✓ alignment ✓ fill-viewport+container ✓ icon-color]
- MCP calls: [number of calls per tool — for performance debugging]
- Compile/typecheck: [command + exit code | unavailable + reason]
- Lint: [command + exit code | unavailable + reason]
- Asset coverage: [command + exit code | not applicable]
- Visual evidence: [visualState + setupSteps + reference/actual paths | pending tester]
- RED evidence: [validated summary | not-applicable (visual-contract)]
- GREEN handoff: [original tester command | not-applicable]
- Blockers: [if any]

**Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
**Summary:** [1-2 sentences]

## MoMorph refs:
- {screen name}: https://momorph.ai/files/{fileKey}/screens/{screenId}
- Clarifications: {plan_dir}/clarifications.md (if any)

## Work context
Work context: {project_root}
Reports: {plan_dir}/reports/
Plans: {plan_dir}/
```

## Guidance for orchestrator when spawning

- **Same message:** N `Agent(subagent_type="momorph-ui-implementer")` calls in parallel with the asset_downloader bg job after the policy gate clears.
- **Embed the slim section subtree:** before spawning, extract the section branch from the `get_frame_node_tree` output (Phase 1) → paste a compact JSON into the prompt → subagent avoids another full-tree call.
- **Mode:** use `section` for initial components and bounded corrections, `screen` for root/cross-section work, and `polish` for the Phase 4 pass.
- **Evidence:** copy tester RED fields verbatim for `e2e-red-first`; never synthesize or summarize away the failure cause.
- **Resource:** N ≤ 6 per batch.
- **Status handling:** see "Subagent status" in SKILL.md.
