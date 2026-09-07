---
name: tkm:momorph-implement-design
category: momorph
roles: [engineer]
description: Use this skill to code UI pixel-perfect with Figma designs on MoMorph (web or mobile). ACTIVATE when user provides a momorph URL like `https://momorph.ai/files/{fileKey}/screens/{screenId}`, gives a `fileKey`+`screenId` pair, or mentions keywords "momorph", "figma design", "code from design", "implement figma screen", "reproduce UI", "translate design to code", "pixel-perfect Figma", "code app from figma".
---

# MoMorph Implement Design

Code UI from Figma designs on MoMorph — pixel-perfect and parallel. Both web (React/Vue/Next/Svelte) and mobile (React Native, Flutter, SwiftUI, Compose).

## Philosophy: incremental query, explicit verification, assets in background

DO NOT dump entire frame to file (context overflow). Query incrementally via MCP as needed. The dedicated `momorph-ui-implementer` calls MoMorph tools directly with the `nodeId` it is coding. Generic `implementer` is never used by this skill.

```
Phase 0:  select visual-contract or e2e-red-first policy
Phase 1:  overview + node tree + media files (parallel)    ← layout + names + asset URLs
Phase 2:  plan-only assets.md + bg downloader              ← assets planned immediately
         + spawn N momorph-ui-implementer agents           ← after policy gate clears
Phase 3:  compose root + tester validation                 ← pixel-perfect + GREEN evidence
Phase 4:  polish (responsive + hover/focus + transition)   ← REQUIRED for web (default-on)
```

## Principles

1. **Figma = source of truth** — never guess. Get values via MCP tools.
2. **Media node = asset** — name contains `mm_media_` (case-insensitive). DO NOT code subtree, render asset element from `assets.md`.
3. **MCP tree once, branch locally** — call `get_frame_node_tree` once, extract compact section branches, and embed only the assigned branch in each agent prompt.
4. **Asset path is a PLAN** — `assets.md` is written immediately from `media_files.json` (no need to wait for download). Files land progressively in the background.
5. **Maximize parallelism** — bundle every independent I/O into a single turn.

## Input

`fileKey` + `screenId` — extracted from URL `https://momorph.ai/files/{fileKey}/screens/{screenId}`. Reference: `.claude/rules/momorph/momorph-awareness.md`.

Stack/styling/naming → infer from project files. If unclear → AskUserQuestion.

---

## Execution agent

Every UI edit in this workflow uses `Agent(subagent_type="momorph-ui-implementer")` with one explicit mode:

| Mode | Ownership |
|------|-----------|
| `section` | Initial or corrective work inside one bounded section; leaf mode, never delegates |
| `screen` | Root composition or corrections spanning sections; may delegate only section-mode UI work and tester verification |
| `polish` | Responsive, focus/hover/pressed, and restrained transitions; leaf mode, never delegates |

The agent has MoMorph MCP plus the restricted delegation allowlist
`Agent(momorph-ui-implementer, tester)`. Only `screen` mode may use `Agent`: it
may create same-agent workers with `mode: section` and call `tester` for
verification. `section` and `polish` are leaf modes and must never invoke
`Agent`. `tester` owns RED/GREEN execution and Playwright or native screenshot
validation. Do not route section, screen correction, or polish work to generic
`implementer`.

## Phase 0 — Verification policy gate

Choose exactly one policy before spawning any UI coding agent. Record it as `testPolicy` in every agent prompt and report.

| Policy | Select when | Ordering |
|--------|-------------|----------|
| `visual-contract` (default) | Static/presentational fidelity with no new observable behavior | Code first, then compile/lint + coverage + tester visual validation. This is explicitly not TDD. |
| `e2e-red-first` | A web task adds interaction/flow behavior, or the user explicitly requires test-first web UI | `tester` creates a durable test and proves genuine RED before any UI edit; the same test must pass GREEN afterward. |

If the request mixes visual fidelity and behavior, or its policy is otherwise unclear, ask one clarification question before either track starts. Never silently switch policies.

### RED gate for `e2e-red-first`

Delegate `Agent(subagent_type="tester")` with a RED-only task. The tester may edit only the owned test file(s), never the UI implementation. Require all fields below before Phase 2 UI agents start:

- `testRunner`: existing compatible runner
- `redTestFiles`: durable test files created or changed
- `redCommand`: exact command executed
- `redExitCode`: non-zero
- `redFailure`: expected assertion failure caused by missing behavior, not syntax, dependency, environment, or server-start failure

Pass those fields unchanged to every `momorph-ui-implementer` prompt. A log-only probe or unrelated command failure is not RED evidence.

### No runner and mobile

- Do not install or scaffold a runner without separate user approval.
- If `e2e-red-first` is selected for web and no compatible runner exists, stop `BLOCKED`: ask the user to approve runner setup or choose `visual-contract`. No automatic downgrade.
- `e2e-red-first` is web-only. If selected for mobile, stop `BLOCKED` and ask for an explicit switch to `visual-contract`; never switch silently or substitute browser Playwright.
- Mobile uses `visual-contract` and may proceed without a native runner; record `testRunner: none`, `redEvidence: not-applicable (visual-contract)`, then require compile/lint and simulator/emulator screenshot evidence.

For `visual-contract`, every UI prompt carries `redEvidence: not-applicable (visual-contract)` plus its planned post-code checks.

---

## MCP toolkit

| Tool | When to use |
|------|-------------|
| `get_overview(screenId, maxDepth?)` | **First call** — bounded overview tree. Grasp layout and identify sections. |
| `get_frame_node_tree(screenId, includeSpecs?)` | Full frame node tree. Call once, then extract compact branches locally for agents. |
| `list_design_items(screenId)` | List design items when component/variant information is needed. |
| `get_related_design_items(screenId, designItemId, limit?)` | Find related variants after selecting a design item. |
| `get_node(screenId, nodeId)` | Full node detail (with style). Use when accurate styling is needed. |
| `get_node_context(screenId, nodeId, includeSiblingStyles?)` | Node + parent + siblings + optional sibling styles. Understand layer composition. |
| `get_media_files(screenId)` | Map `{nodeId: download_url}` for downloading assets. **Required** in Phase 1. |
| `get_frame_image(screenId, outputType?, showDesignItems?)` | Design screenshot — only for final visual diff, not in Phase 1. |
| `get_figma_image(fileKey, nodeIds, format?, outputType?, scale?)` | **ONLY for subagent fallback case**: `mm_media_*` node has NO URL in `get_media_files`. Pass `nodeIds` as a list. DO NOT use otherwise (rate-limit). |

**Recommended subagent workflow:**
read embedded section branch → encounter node needing full style → `get_node(screenId, nodeId)` → encounter node needing role context → `get_node_context(screenId, nodeId, includeSiblingStyles?)`. For variants: `list_design_items(screenId)` → `get_related_design_items(screenId, designItemId, limit?)`.

---

## Phase 1 — Overview + media URLs + media names (3 parallel MCP calls)

This phase is mandatory for initial screen work. Specs/test-case CSVs are
behavioral inputs, not a replacement for design evidence. Do not edit UI and do
not report `DONE` until these calls complete successfully or the prompt already
contains equivalent node-tree/media-map artifacts from the orchestrator.

Within **a single message**, call in parallel:

| Tool | Output |
|------|--------|
| `get_overview(screenId, maxDepth?)` | Bounded hierarchy — read directly |
| `get_frame_node_tree(screenId, includeSpecs=false)` | Full node tree — extract sections and `{nodeId: name}` locally |
| `get_media_files(screenId)` | File path → `media_files.json` (note path) |

From the node tree, identify **sections** = direct children of root frame, skip nodes named `mm_media_*`.

Filter media nodes from the node tree and build map `{nodeId: name}` (save to `data/node_names.json`) → asset_downloader uses it to name files by node name → 2 nodes with same name = 1 file (dedup).

---

## Phase 2 — Asset plan + Spawn N subagents (1 message)

Within **a single message**, in parallel:

### Detect asset dir in PROJECT (first time only)

Assets are NO LONGER stored in plan_dir — write directly to project so code can import them.

| Stack | `--out` (filesystem) | `--code-path-prefix` (manifest path) |
|-------|---------------------|--------------------------------------|
| Next.js / Vue / Svelte (web) | `public/{screen-slug}/` | `/{screen-slug}` |
| Vite React | `public/{screen-slug}/` | `/{screen-slug}` |
| React Native | `src/assets/{screen-slug}/` | `@/assets/{screen-slug}` (per project alias) |
| Flutter | `assets/{screen-slug}/` | `assets/{screen-slug}` (remember to add to `pubspec.yaml`) |
| SwiftUI / Compose | `Resources/Momorph/{ScreenSlug}/` | filename only (use `Image("logo")`) |

If the project has a different convention (`./docs/code-standards.md` or an existing assets folder) → follow it.

### A. Bash chain — write data + plan asset (with name-based dedup)

```bash
mkdir -p {plan_dir}/data && mkdir -p {project_assets_out} && \
cp {media_files_result_path} {plan_dir}/data/media_files.json && \
# node_names.json: {nodeId: name} — filtered from get_frame_node_tree (Phase 1)
echo '{embed_node_names_json}' > {plan_dir}/data/node_names.json && \
.claude/skills/.venv/bin/python3 .claude/skills/momorph-implement-design/scripts/asset_downloader.py \
  {plan_dir}/data/media_files.json \
  --names {plan_dir}/data/node_names.json \
  --out {project_assets_out} \
  --code-path-prefix {code_path_prefix} \
  --plan-only \
  --manifest {plan_dir}/data/assets.md
```

`--plan-only` writes the full `assets.md` IMMEDIATELY (subagents read it right away). `--names` enables dedup by node name. `--code-path-prefix` makes manifest paths **import-ready** — code can use the path from the manifest as-is, no edits needed.

### B. Bash background — actually download files into project dir

```bash
# run_in_background=true
.claude/skills/.venv/bin/python3 .claude/skills/momorph-implement-design/scripts/asset_downloader.py \
  {plan_dir}/data/media_files.json \
  --names {plan_dir}/data/node_names.json \
  --out {project_assets_out} \
  --code-path-prefix {code_path_prefix} \
  --workers 8 \
  --manifest {plan_dir}/data/assets.md
```

### C. Spawn N MoMorph UI agents (same message, `run_in_background=true`)

One section → one `Agent(subagent_type="momorph-ui-implementer", run_in_background=true)` with `mode: section`, the selected policy, owned output files, and RED evidence or the visual-contract marker. Prompt template: `references/subagent-prompt-template.md`.

Only the top-level orchestrator or a `screen`-mode UI agent fans out section
agents. A `screen` agent may delegate only same-agent `mode: section` tasks and
`tester` tasks. A `section` or `polish` agent must not invoke `Agent` or recurse.

Under `e2e-red-first`, do not make this call until the Phase 0 RED gate is complete.

**Resource guardrail:** N ≤ 6 per batch. > 6 sections → batch in groups of 5–6.

### Section too large?

Inspect the section branch extracted from `get_frame_node_tree`. If it has many large sub-sections, split it into 2–3 compact agent assignments.

---

## Phase 3 — Compose + validate

### 3.1 — Compose screen root

Spawn `Agent(subagent_type="momorph-ui-implementer")` with `mode: screen` to create the root file per project convention, importing N section components in design order. Give it exclusive ownership of the root file and the same verification contract used for the sections.

### 3.2 — Validate coverage (auto)

```bash
.claude/skills/.venv/bin/python3 .claude/skills/momorph-implement-design/scripts/validate_coverage.py \
  --assets {plan_dir}/data/assets.md \
  --code {component_dir}
```

Exit `0` = ok. Exit `2` = some asset missing → prints missing nodeIds → spawn `momorph-ui-implementer` in `section` or `screen` mode, matching the correction boundary.

### 3.3 — Visual diff (web — Playwright + native vision)

**Web stack** (Next/React/Vue/Svelte): Playwright/browser execution belongs to `tester`; the MoMorph UI agent never receives the Playwright MCP.

```
1. Pull design image (once — run parallel with dev-server spawn)
   mcp__momorph__get_frame_image(screenId, outputType?, showDesignItems?)
   → cp to {plan_dir}/data/preview.png

2. Start dev server (Bash run_in_background=true)

3. Delegate `tester` to capture the actual UI at `{designWidth}x{designHeight}`
   and write `{plan_dir}/data/actual.png`. Its prompt MUST include
   `visualState` and ordered `setupSteps` derived from the design/test cases
   (for example, click a button before capturing a post-interaction frame).
   The tester executes those steps before the screenshot, then neutralizes
   transient pointer/focus state unless hover/focus is part of the reference.
   The report must name its command/tool, exit status, route, viewport, setup
   steps, and screenshot path.

4. Tester compares both images (and the orchestrator may inspect them with Read):
   Read(data/preview.png) + Read(data/actual.png)
   Check 5 categories: FONT / BORDER RADIUS (wrapper matches asset?) /
   ALIGNMENT / SPACING / correct ASSET.

5. Large diff → query MCP for the wrong region → spawn `momorph-ui-implementer`
   with the narrowest `section` or `screen` correction mode → tester repeats step 3.
```

**Optimization:** cap at ≤ 2 visual-diff rounds (1 initial + 1 post-fix). Accept small diffs.

An actual screenshot alone is not visual evidence. Completion requires both the
MoMorph reference image and the tester-captured actual image, plus an explicit
comparison result in the same `visualState`. Missing either path or capturing a
different interaction state is `DONE_WITH_CONCERNS` at best, never `DONE`.
If the report itself names different expected and actual values, it is a
discrepancy — never mark that row PASS.
When a deterministic image comparator is available, record its metric. The word
`exact` is reserved for a zero-difference metric; model-vision-only comparison
must be labeled qualitative and must list observed differences.

**Mobile stack** (RN/Flutter/SwiftUI/Compose): delegate simulator/emulator capture (`xcrun simctl`, `adb screencap`, or project equivalent) to `tester`, which reports the command, exit code, device/viewport, and screenshot path.

### 3.4 — GREEN evidence

For `e2e-red-first`, delegate the original `redCommand` to `tester` after implementation. Completion requires:

- `greenCommand`: same targeted test command unless the tester explains a necessary equivalent
- `greenExitCode: 0`
- `greenTestFiles`: the durable tests exercised
- `greenResult`: passing assertion summary plus artifact paths, including screenshots/traces when produced

For `visual-contract`, record `GREEN: not-applicable (visual-contract)`; compile/lint, coverage, and visual evidence remain mandatory.

### 3.5 — Hand-off to Phase 4 (web stack — DO NOT skip)

After visual diff passes, the screen is **pixel-perfect but not done**. Proceed directly to Phase 4. Do NOT report the screen as completed yet. Do NOT pause for user confirmation unless user explicitly opted out earlier.

---

## Phase 4 — Polish (REQUIRED for web)

Run AFTER Phase 3 visual diff has passed. This is a **restrained additive** step, NOT a re-edit of pixel-perfect output.

**Trigger:** ⚠️ **Default-on for web stack** — orchestrator MUST run Phase 4 before declaring the screen done. Do NOT skip. Do NOT wait for the user to ask. Pixel-perfect alone is NOT a complete screen — interactive states + responsive breakpoints are part of the deliverable.

**Skip only when:** user explicitly says "skip polish" / "no responsive" / "static only", OR mobile native stack with single device viewport (still apply hover→pressed mapping where applicable).

### Scope (see `references/polish-rules.md` for details)

| Item | Content |
|------|---------|
| Responsive | Mobile/tablet/desktop breakpoint adaptation. Containered → mobile padding; multi-col → stack; hero text scale |
| Hover/focus/pressed | Button/link/card/input — default pattern (200ms ease) or Figma variant if available |
| Transition | `opacity`/`transform`/`background`/`shadow` 150–300ms ease. Respect `prefers-reduced-motion` |
| Entrance | Optional: fade-in/slide-up for hero. Use sparingly |

### DO NOT

- Redesign away from Figma (changing layout/colors/typography)
- Complex animation (parallax, scroll-jacking, GSAP timelines)
- Drag/swipe/gesture, advanced micro-interactions
- Business logic, validation, loading/skeleton states

### Procedure

1. Read pixel-perfect file list from Phase 2/3 reports.
2. Read project breakpoint convention (Tailwind config / MUI theme / CSS vars).
3. Spawn `Agent(subagent_type="momorph-ui-implementer")` with `mode: polish`, the selected policy, exact file ownership, stack, and breakpoints. Whole-screen ownership is required because responsive rules cross sections.
4. Delegate post-polish validation to `tester` at 375 / 768 / 1280 (web). Mobile native: check rotation + tablet if applicable.
5. Require compile + lint results and rerun the strict GREEN test when `testPolicy: e2e-red-first`. Report states added, breakpoint changes, tester evidence, and commands with exit codes.

**Common bug check** (always check after diff):
- **UI not filling viewport**, fixed at design width (e.g. `390px`) → empty side gutters on larger screens. Root component must be `width: 100%`, DO NOT hardcode design width. See rule 3 `Sizing` + Anti-pitfall #4.
- **Containered layout misuse** (web design uses 1440 artboard + 1200 centered content) → agent applies `width: 1200px` rigidly → content sticks to the left. Must use `max-width: 1200px + margin: 0 auto + width: 100%`. See rule 3 Containered layout in `code-rules.md`.
- Wrapper element missing `border-radius` matching the inner asset → shadow exposes a rectangle (rule 2b in code-rules.md).
- **SVG icon wrong color** (e.g. shows white) → asset rendered as `<img>` instead of inline component → CSS can't control color. Convert to inline SVG + `currentColor` + parent `color` from Figma `fills`. See rule 2a + Anti-pitfall #5.
- Multiple nodeIds mapped to the same `assets.md` filename but code imports 2 different files → re-check asset paths.

---

## Subagent status

| Status | Action |
|--------|--------|
| `DONE` | Note files, continue |
| `DONE_WITH_CONCERNS` | Correctness concern → fix; observational → continue |
| `BLOCKED` | Provide more context / split task → re-spawn once. Still BLOCKED → escalate |
| `NEEDS_CONTEXT` | Provide missing context → re-spawn |

Never retry blindly 3 times.

---

## Code rules

`references/code-rules.md` — shared by orchestrator and subagents.

## When to stop and ask

- Missing `fileKey` / `screenId`.
- Section too large (sub-sections > 5 levels deep) → confirm splitting.

## Resources

| File | Purpose |
|------|---------|
| `scripts/asset_downloader.py` | Plan + parallel asset download. Supports `--plan-only` |
| `scripts/validate_coverage.py` | Auto check asset coverage |
| `scripts/README.md` | Script details |
| `references/code-rules.md` | General code rules (Phase 2) |
| `references/polish-rules.md` | Responsive + hover/focus + transition (Phase 4) |
| `references/subagent-prompt-template.md` | `momorph-ui-implementer` prompt template |
| `.claude/agents/momorph-ui-implementer.md` | Dedicated UI agent contract and modes |
| `references/mcp-template.json` | Sample momorph MCP config |

## Scope

**DO:** code static/presentational UI (web + mobile), pull assets, validate coverage. **Phase 4 polish (REQUIRED for web):** responsive + hover/focus + light transition.

**DO NOT:** backend/API, business logic, complex state, complex animation (parallax, scroll-jacking), redesign away from the design.
