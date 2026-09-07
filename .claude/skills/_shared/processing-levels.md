---
name: processing-levels
description: "Canonical processing level spec — reference convention loaded by skills that accept --level low|medium|high|max."
type: reference
version: "1.0.0"
---

# Processing Levels (kit-internal reference)

Single source of truth for the `--level low|medium|high|max` parameter. Not a tool — a **reference convention** that other skills import, analogous to `confidence`. Loaded by every skill that accepts `--level`. Update this file FIRST when changing level semantics — drift here counts as a breaking change for every consumer.

## Overview

`low/medium/high` appears in two distinct, unrelated contexts. They MUST NOT be confused:

- **Processing level** (input `--level`): controls **how hard the skill works** — depth, agent count, validation passes. The subject of this file.
- **Finding severity** (output labels `[LOW]/[MEDIUM]/[HIGH]/[CRITICAL]`): classifies **how bad a discovered finding is**. Unrelated to processing effort.

## Canonical Level Table

| Level   | Effort     | Parallel agents | User gates | Typical use                       |
|---------|------------|-----------------|------------|-----------------------------------|
| low     | Minimal    | None            | None       | Quick iteration, draft review     |
| medium  | Balanced   | Optional        | None       | Standard (default for all skills) |
| high    | Thorough   | Yes             | Pre-final  | Pre-merge, important decisions    |
| max     | Exhaustive | Multiple        | Multiple   | Security audits, critical releases|

## Model & Effort per Level (tiered agents only)

For the two reasoning-heavy agents that ship capability-tier variants — **`brainstormer`** and
**`planner`** — `--level` selects not only depth but the **model + reasoning effort** the agent runs on.
This is the single source of truth for that mapping; every caller that spawns these agents reads it here
rather than restating it. On claude-code the **model alone** carries the tier (haiku‹sonnet‹opus‹fable), and
each agent runs at the **user's own session reasoning effort** — we do not pin it. On codex the model derives
from that tier via `takumi-cli`'s model taxonomy, plus an explicit `codexReasoningEffort` — because codex has
one fewer model rung (no `fable`: both `opus` and `fable` map to `sol`), so effort is the only thing that
separates the top codex tier from the default.

| `--level` | Variant spawned | claude-code `model` | claude-code effort | codex `model` | codex `model_reasoning_effort` |
|-----------|-----------------|---------------------|--------------------|---------------|--------------------------------|
| `low` | `brainstormer-lite` / `planner-lite` | `sonnet` | session default | `gpt-5.6-terra` | `medium` |
| `medium` *(default)* | `brainstormer` / `planner` | `opus` | session default | `gpt-5.6-sol` | `high` |
| `high` | `brainstormer` / `planner` | `opus` | session default | `gpt-5.6-sol` | `high` |
| `max` | `brainstormer-max` / `planner-max` | `fable` | session default | `gpt-5.6-sol` | `xhigh` |

- **Effort is a codex-only, opt-in frontmatter key: `codexReasoningEffort`.** It is deliberately NOT `effort`
  (the key claude-code reads) — a shared key would also pin claude-code's effort and force, e.g., `fable` to
  `xhigh`, burning credits for no real gain since `fable` is already the top model. Claude-code keeps the
  user's session effort; codex reads `codexReasoningEffort`.
- `medium` and `high` share the default variant — they differ only by the depth/parallelism this file already
  defines, not by model. `high`/`max` buy more parallelism, not just a heavier model.
- Only these two agents are tiered. Every other agent keeps its single pinned model; `--level` changes only
  their processing depth (below), never their model. Non-tiered agents set no `codexReasoningEffort`, so codex
  keeps its own default for them (no blast radius).
- The values live in the agent files' frontmatter; this table documents the level→variant routing a caller
  applies when it spawns one.

## Default Rule

`medium` is the default for **every** skill unless the user explicitly specifies `--level`.

## Behavior Guidelines per Category

**Discovery skills** (`research`, `scan-codebase`, `brainstorm`):

- `low` → reduce source/agent count, skip cross-validation
- `medium` → standard depth
- `high` → more sources/agents, cross-validate, spawn parallel subagents
- `max` → exhaustive, multiple parallel subagents, adversarial probing

**Analysis/validation skills** (`review-code`, `audit-security`, `debug-code`, `predict-risks`):

- `low` → run quick-pass only (Stage 1 or equivalent)
- `medium` → standard pipeline (Stages 1+2 or equivalent)
- `high` → full pipeline including edge-case scan
- `max` → full pipeline + adversarial/auto-fix layers

## Integration Guide

Each consuming skill adds this section (replace the bracketed table with skill-specific behavior):

```markdown
## Processing Level

Accepts `--level low|medium|high|max` (default: `medium`).
See `_shared/processing-levels.md` for global semantics.

| Level | [Skill-specific behavior columns] |
|-------|-----------------------------------|
| `low` | ... |
| `medium` *(default)* | ... |
| `high` | ... |
| `max` | ... |
```

The `argument-hint` in the skill's YAML frontmatter must also append `[--level low|medium|high|max]`.

## Naming Collision Warning

`--level` (processing effort, **input**) and severity labels (**output**) share the words low/medium/high. Keep them separate:

- `--level max` = processing effort (input) — highest computational depth.
- `[CRITICAL]` = finding severity (output) — highest severity label.
- `[HIGH]` severity (output) ≠ `--level high` processing effort (input). A `--level low` quick pass can still report a `[CRITICAL]` finding.

When writing skill docs and output, never let one shadow the other.
