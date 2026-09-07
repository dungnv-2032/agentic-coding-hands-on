---
name: tkm:uiux-model-users
display-name: "SW*-UM"
description: "SW*-UM — Raise the resolution of who you are building for. Turns a vague product idea, research notes, or interview transcripts into structured user models — ペルソナ策定 (personas), エンパシーマップ (empathy maps), カスタマージャーニー (customer journey maps with an emotion curve), ユーザーインサイト (observation→insight→How-Might-We), and ユーザーストーリーマッピング (user story mapping — backbone × release slices) — then emits an editable um-spec.json, builds a self-contained, tabbed HTML viewer (Sun* brand) the user just opens, and can push the result to Figma as frames that match the HTML viewer. Use when the user asks for ペルソナ, ユーザー像, ユーザーモデリング, エンパシーマップ, カスタマージャーニー, ジャーニーマップ, ユーザーインサイト, ユーザーストーリー, ユーザーストーリーマッピング, ストーリーマップ, user persona, empathy map, customer journey, user insight, user story, story mapping, 'who are our users', 'understand the user', wants an editable user-model output, or wants to push the user model to Figma."
category: design
roles: [designer]
license: MIT
metadata:
  author: kitamachishun
  version: "1.3.0"
  portable: "claude, claude-code, codex"
  upstream: "sun-asterisk-internal/takumi-design@8fb425c"
---

# SW\*-UM — User Modeling

## Purpose
Raise the **resolution of the user** before designing anything. The job is to turn fuzzy assumptions about "the user" into concrete, evidence-anchored models so the team designs, prioritizes, and decides for a real person — not an average of everyone.

This skill converts an idea, research notes, or interview transcripts into five connected artifacts:
1. **ペルソナ** — who they are (goals, frustrations, motivations, behaviors, needs, context)
2. **エンパシーマップ** — Says / Thinks / Does / Feels (+ Pains / Gains)
3. **カスタマージャーニー** — stages × actions / touchpoints / thoughts / emotion curve / pain points / opportunities
4. **ユーザーインサイト** — observation → insight → implication → How Might We
5. **ユーザーストーリーマッピング** — backbone (activities → tasks, left→right) × release slices (MVP / Release 2 / Later), each story with persona + priority

These are **not** UI/IA artifacts. This is the *upstream* understanding that feeds [`uiux-design-information-architecture`](../uiux-design-information-architecture) (information architecture) and visual/component design. If the user wants screens, sitemap, or pixels, model the user here first, then hand off.

## The pipeline (input → editable spec → HTML viewer → Figma)
This skill is a 3-stage pipeline. `um-spec.json` (see `references/um-spec-format.md`) is the single source of truth carried between stages.

```
input (idea / research notes / interview transcripts / existing assumptions)
  │  Stage 1: GENERATE  → um-spec.json + markdown, then bin/build-doc.py embeds it into a standalone HTML
  ▼
um-model.html  (data already embedded — the user just opens it; tabbed, read-only)
  │  Stage 2: REVIEW in the browser  (revise: tell Claude Code → it edits um-spec.json → re-run build-doc.py)
  ▼
edited um-spec.json
  │  Stage 3: TO FIGMA  (Figma MCP, see references/figma-output.md) — frames that MATCH the HTML viewer
  ▼
Figma frames (ターゲット/ペルソナ・エンパシー・ジャーニー・インサイト・ストーリーマップ, Sun* brand)
```

- **Stage 1 — Generate:** run the Standard workflow below, emit a valid `um-spec.json` + a markdown summary, then build a ready-to-open HTML so the user never loads JSON manually:
  ```bash
  python3 bin/build-doc.py <path>/um-spec.json     # → <path>/um-model.html (spec embedded) + auto-opens in browser
  ```
  It embeds the spec, inlines any local persona images as data URIs, and **opens the HTML in the default browser automatically** (pass `--no-open` to skip). Report the `um-model.html` path.
- **Stage 2 — Review:** the HTML opens as a **read-only, tabbed document** styled to the **Sun\* brand** (Sun Red `#FF2200` single accent, Noto Sans JP). A **left sidebar** holds the brand (`SW*-UM`) + product title and a vertical tab list; content renders on the right.
  Tab order: **概要 / ペルソナ / エンパシーマップ / ジャーニー / インサイト / ストーリーマップ**.
  - **概要** — model premise: 対象ユーザー層 / ビジネスの狙い / 根拠(調査・データ) / フェーズ, artifact counts, and 前提・仮定 (flagged as unverified).
  - **ペルソナ** — a **vertically-scrolling slide deck** (each slide numbered NN / total). Slide 1 = **ターゲットユーザー像**: the 対象ユーザー層 lead, ビジネスの狙い, the primary/secondary line-up (avatar + type badge + tagline), and 対象外（アンチペルソナ）. Slides 2+ = one **persona** each: a real portrait from the shipped **persona pool** (auto-assigned, or set `image:"p7"`; see `references/persona-pool.md`) — falls back to a generated SVG avatar only if the pool is unavailable — type badge (primary / secondary / anti-persona), tagline, demographics, bio, columns for goals / frustrations / behaviors / needs + a 利用シーン box. (quote / motivations / channels are intentionally not shown — kept compact so a persona reads in one slide.)
  - **エンパシーマップ** — 4-quadrant grid (SAYS / THINKS / DOES / FEELS) per persona, plus a Pains / Gains band.
  - **ジャーニー** — per scenario: an **emotion curve** (SVG line with 😣→😄 faces, plotted from `emotionScore` -2..2) above a row of stage cards; each card colored by emotion (gold=positive / ink=neutral / red=pain) with 行動 / 接点 / 思考 / 課題 / 改善機会.
  - **インサイト** — cards showing the **観察→気づき→示唆** flow with a dashed connector, evidence (生の声), a highlighted **How Might We** question, impact badge, and linked persona.
  - **ストーリーマップ** — a Jeff-Patton story map: the **backbone** (activities as a dark row, tasks as a tinted row, left→right user flow) above **release bands** (rows; MVP highlighted). Each story is a compact card placed at its task column × release row, with persona avatar, priority left-rail (Must=red / Should=gold / Could=grey), and an optional value (→ soThat). Horizontally scrollable.
  - **出典ツールチップ（input traceability)** — items annotated with `src` (see `references/um-spec-format.md` → 出典アノテーション) render with a dashed underline; hovering shows a tooltip with the **input source** (label + raw excerpt) the item was derived from. This makes 「この記述はどのインタビュー／データから来たか」 visible in place.
  The viewer is **read-only** — to change anything, instruct Claude Code to update `um-spec.json` and re-run `build-doc.py`. The sidebar footer carries a small **「フィードバックを送る」** link to the skill-improvement GitHub Issues page (same URL as the `[feedback]` prompt in `build-doc.py`).

### Visual feedback with Agentation (optional)
The viewer ships an **opt-in Agentation toolbar** so the user can annotate the model visually (click a persona, a journey stage, a story-map cell) and the agent reads that feedback automatically. It stays off by default — the HTML is self-contained unless explicitly enabled.

- **Enable:** build with `--annotate` (opens with `?annotate=1`), or just append `?annotate=1` to the URL of an already-built `um-model.html`:
  ```bash
  python3 bin/build-doc.py <path>/um-spec.json --annotate
  ```
  When on, it loads React + `agentation` from esm.sh and syncs annotations to the local **Agentation MCP server** (default `http://localhost:4747`). Needs internet (for esm.sh) + the MCP server running. Override the endpoint with `&endpoint=...`.
- **Pick up feedback (agent side):** read annotations with the Agentation MCP tools — `agentation_get_all_pending` (one-shot) or `agentation_watch_annotations` (block until new ones arrive, for hands-free loops). For each, **edit `um-spec.json`**, re-run `build-doc.py`, then call `agentation_resolve` with the annotation ID and a one-line summary of the change. Only resolve annotations the user accepted; leave rejected ones open.
- This is the visual counterpart to "tell Claude Code what to fix" — same outcome (edit the spec, rebuild), driven by on-page annotations instead of chat.

- **Stage 3 — To Figma (on request):** turn what the viewer shows into **Figma frames that match the HTML display** — same Sun\* brand, same card layouts (high-fidelity, not low-fi). Trigger = a chat instruction (「Figma に出して」). The skill reads `um-spec.json` directly (the viewer is read-only — no Figma button). **Always load `/figma-use` FIRST when available (mandatory before any `use_figma` call); if it isn't registered, call the Figma MCP `use_figma` directly.** Follow `references/figma-output.md`: it lists the exact design tokens (colors/font/card style) and the per-artifact frame construction so Figma lines up with `um-model.html`. Confirm the target Figma file before creating; scope to what the user asks (all artifacts / only personas / etc.).

Always emit `um-spec.json` in Stage 1 so the later stages stay reproducible. Run only the stages and artifacts the user asks for — every section of the spec is optional except `meta` + `personas`. If the user just wants the model, stop after Stage 1/2.

## When to use
Trigger on: ペルソナ / ユーザー像 / ユーザーモデリング / ターゲット定義 / エンパシーマップ / カスタマージャーニー / ジャーニーマップ / 体験設計の前段 / ユーザーインサイト / インサイト抽出 / ユーザーストーリー / ユーザーストーリーマッピング / ストーリーマップ / "who are our users" / "understand our users" / "build a persona" / "map the customer journey" / "story mapping" / "what insights from this research".

Also trigger on: 「Figma に出して」/「Figmaで見たい」/「Figma に合わせて」 once a model exists (Stage 3 → frames matching the HTML viewer).

Hand off (do **not** lead with this skill) when the user wants screen structure / IA / navigation (→ `uiux-design-information-architecture`), or pure visual / component / UI design.

## Core principles
1. **Model real people, not averages.** A persona is a sharp, specific individual — not a demographic bucket.
2. **Evidence over invention.** Anchor models in research. Anything not grounded in data goes in `meta.assumptions`, clearly flagged.
3. **Few, sharp personas.** 1–2 primary + a couple secondary. Add an **anti-persona** (who it's NOT for) — it sharpens scope more than another primary.
4. **Goals and emotions, not just attributes.** Age/job alone don't drive design; what they want, fear, and feel does.
5. **Pain points are opportunities.** Every journey low point and frustration should imply a design opportunity.
6. **Insight ≠ observation.** An observation is *what* happened; an insight is *why* it matters. Push every observation to a "so what" and a How-Might-We.
7. **Trace stories to personas.** Every user story names the persona it serves and the value it delivers.

## The modeling practice (guide the user through this — it is the core experience)
User modeling is deciding *who you are building for, what they are trying to do, how they feel along the way, and what that means for the product.* Work these five elements, capturing each as a concrete artifact in `um-spec.json`. See `references/modeling-methods.md` for the how-to of each.

| Step | Activity | Artifact (field → tab) |
|---|---|---|
| 1. 対象を絞る | 誰のためか／誰のためでないか を決める | `meta.segment`, persona `type` (primary/secondary/anti) → 概要/ペルソナ |
| 2. ペルソナ策定 | 代表的ユーザーを goals/frustrations/motivations/behaviors/needs/context で立体化 | `personas` → ペルソナ |
| 3. 共感の深掘り | Says/Thinks/Does/Feels と Pains/Gains で内面を捉える | `empathyMaps` → エンパシーマップ |
| 4. 体験の時系列化 | フェーズ別の行動・接点・思考・感情曲線・課題・機会 | `journeys` → ジャーニー |
| 5. 気づきの抽出 | 観察→本質的な気づき→示唆(HMW) に変換 | `insights` → インサイト |
| 6. 要求の構造化 | 目的を「〜として、〜したい。なぜなら〜」に落とし、行動の流れ×リリースでマッピング | `storyMap` → ストーリーマップ |

When the user brings a vague idea or raw research, **walk these steps**: surface gaps (no anti-persona, attribute-only personas with no goals, journeys with no emotion or no opportunities, observations that never reach an insight, stories with no persona/acceptance), propose options, and fill `um-spec.json` accordingly.

## Required inputs
If enough is known, **proceed without interrogating the user**. Fill gaps with clearly-labeled assumptions (`meta.assumptions`). Try to identify:

- Product / service and its purpose
- Who it is for (and a guess at who it is NOT for)
- Business goal
- What research exists (interviews, surveys, analytics, support tickets) — or note "仮説ベース" if none
- Stage (discovery / concept / growth)
- Which artifacts the user wants (all five, or a subset)

Ask **at most one** blocking question at the start, and only if a true blocker exists (e.g. no idea what the product is). Save smaller clarifications for the end. If the user pastes interview transcripts or notes, mine them directly — quotes become `quote` / `empathyMaps.says` / `insights.evidence`.

## Standard workflow
Run in order unless the user requests a specific artifact.

### Step 1 — Frame who & why
Summarize in 4–6 lines: プロダクト目的 / 対象ユーザー層 / 対象外（anti） / ビジネス目標 / 根拠(調査) / 不明点（→仮定）.

### Step 2 — Personas
For each persona: name (+attributes), type (primary/secondary/anti), tagline, a representative first-person quote, demographics, bio, and goals / frustrations / motivations / behaviors / needs / channels + a 利用シーン. **Cap each of these lists to at most 2 items — pick the 2 sharpest, highest-signal ones rather than listing everything, so a persona reads in one slide.** Keep the set small. Always include ≥1 anti-persona when scope is unclear. Set `image` to a **fitting** pool portrait (`"p1"`…`"p12"` — match age/gender/vibe; see `references/persona-pool.md`); if omitted, a pool face is auto-assigned by order.

### Step 3 — Empathy maps (for primary personas)
Fill Says / Thinks / Does / Feels from observed behavior and quotes; distill Pains / Gains. Distinguish *says* (observable) from *thinks* (inferred inner voice).

### Step 4 — Customer journey (per key scenario)
List stages in time order. Per stage: goal, actions, touchpoints, thoughts, `emotionScore` (-2..2), pain points, opportunities. The emotion curve makes lows visible — every low should have an opportunity.

### Step 5 — Insights
Convert observations into insights: 観察された事実 → 本質的な気づき(なぜ) → プロダクトへの示唆 → How Might We. Attach evidence (quotes/data) and an impact rating.

### Step 6 — User story mapping
Lay stories out as a map, not a flat list. Build the **backbone** first: `activities` = the user's flow of large actions (left→right, mirror the journey stages), each broken into `tasks`. Then write `stories` under each task (「〜として、〜したい。なぜなら〜」 → `title` + `soThat`), link a `persona`, set `priority` (Must/Should/Could), and slice them across `releases` (MVP / Release 2 / Later) via each story's `release`. The MVP row should be a thin, end-to-end walking skeleton across the backbone. Stories trace back to journey opportunities and insights.

### Step 7 — Emit `um-spec.json` + build the HTML
Produce a valid `um-spec.json` per `references/um-spec-format.md`. **When the input includes real research (transcripts, notes, survey data, logs), register each input in top-level `sources[]` (`{id, label, excerpt}`) and annotate the items derived from it as `{ "text": "...", "src": "<id>" }`** — the viewer then shows the source on hover (dashed underline → tooltip). Annotate the highest-signal items (frustrations, insights' observation/evidence, journey painPoints…) rather than everything; never annotate invented content (that goes to `meta.assumptions`). Then run `python3 bin/build-doc.py <path>/um-spec.json` to embed it into a standalone `um-model.html`. Report both paths. This is what the user opens.

**Feedback:** `build-doc.py` tracks usage and, once the user has built models from a few distinct specs, prints a one-time `[feedback]` line containing the GitHub Issues URL. If that line appears in the script output, **relay it to the user** at the end of your final answer — e.g. 「🙏 SW\*-UM をご利用いただきありがとうございます。スキル改善のため、GitHub Issues でフィードバックをお寄せください: <URL from the [feedback] line>」. Do not skip it, and do not show the feedback link when the script didn't print it.

### Step 8 — Review against the checklist
Run `references/review-checklist.md` and report pass/issues (especially: evidence vs. assumption, anti-persona present, lows have opportunities, stories trace to personas).

### Step 9 — (On request) → Figma
- Trigger: a chat instruction (「Figma に出して」). The viewer is read-only — no Figma button.
- **Load `/figma-use` FIRST when available** (mandatory before `use_figma`); otherwise call the Figma MCP `use_figma` directly. Follow `references/figma-output.md` to build frames from `um-spec.json` that **match the HTML viewer** (Sun\* brand, card layouts). Confirm the target Figma file before creating.

## Output modes
Pick the smallest mode that satisfies the request.

- **Mode A — Full model:** Steps 1–7. Default for "model our users" / "ユーザー理解を深めたい".
- **Mode B — Persona only:** Steps 1–2 (+3). For "ペルソナを作って".
- **Mode C — Journey only:** Steps 1 (brief) + 4. For "カスタマージャーニーを描いて".
- **Mode D — Insight extraction:** Steps 1 (brief) + 5 from pasted research. For "このインタビューからインサイトを" .
- **Mode E — Story map only:** Steps 1 (brief) + 6. For "ユーザーストーリーマッピングして" / "ストーリーマップを作って".
- **Mode F — To Figma:** Step 9 (after a model exists). For "Figma に出して" / "Figmaで見たい" — frames matching the HTML viewer.

## Response rules
- Reply in **Japanese** unless the user writes in another language or asks otherwise.
- **Separate evidence from assumption.** Mark unverified content in a **「前提・仮定」** section and in `meta.assumptions` — never present a guess as a finding.
- Use **persona cards / quotes** for personas, **quadrants** for empathy, the **emotion curve** for journeys.
- Keep personas few and sharp; always state each persona's type (primary/secondary/anti).
- Be concrete enough to act on. Avoid abstract UX jargon and demographic filler.
- Don't over-model; don't drift into screens, IA, or visual design — hand off to `uiux-design-information-architecture`.

## Final answer template
```markdown
# ユーザーモデリング

## 1. 誰のために / 前提
- プロダクト目的 / 対象ユーザー層 / 対象外(anti) / ビジネス目標 / 根拠(調査)
- 前提・仮定（未検証）:

## 2. ペルソナ
（persona cards: type / goals / frustrations / motivations / context / quote）

## 3. エンパシーマップ
（Says / Thinks / Does / Feels / Pains / Gains）

## 4. カスタマージャーニー
（stages × actions / touchpoints / thoughts / emotion / pain / opportunity）

## 5. ユーザーインサイト
（observation → insight → implication → HMW + evidence + impact）

## 6. ユーザーストーリーマッピング
（backbone: activity → task ／ release帯（MVP/Release 2/Later）× story: title / persona / priority）

## 7. レビュー結果
（→ um-model.html のパス）
```

See `references/modeling-methods.md` for each method's how-to, `references/um-spec-format.md` for the schema, and `examples/` for a worked example.
