---
name: tkm:uiux-design-information-architecture
display-name: "SW*-Information Architect"
description: "SW*-Information Architect — Design the information architecture behind a UI and run it through a 3-stage pipeline: generate IA/screen design from an input, emit an editable ia-spec.json, let the user review/edit it in a self-contained HTML editor, then output the edited spec to Figma artboards. Covers upstream IA artifacts — 業務フロー整理 (business-flow swimlanes), ユーザーストーリーマップ (user story mapping), カードソーティング (card sorting), オブジェクトモデリング (object modeling) — plus content hierarchy, sitemap, screen list (画面一覧), screen transitions (画面遷移), per-screen information priority. Use when the user asks for 情報設計, 情報アーキテクチャ, IA, サイトマップ, 画面一覧, 画面遷移, ナビゲーション設計, 画面構成, 業務フロー, ユーザーストーリーマップ, カードソート, オブジェクトモデリング, wants an editable design output, or wants to push a screen structure into Figma. Use when the user mentions editing the design in HTML and exporting to a Figma artboard."
category: design
roles: [designer]
license: MIT
metadata:
  author: kitamachishun
  version: "1.3.0"
  portable: "claude, claude-code, codex"
  upstream: "sun-asterisk-internal/takumi-design@8fb425c"
---

# SW\*-Information Architect — UI Information Architecture Designer

## Purpose
Design the **information architecture (IA)** that a UI sits on top of. The job is to make information findable, decisions easy, and screen relationships obvious — *before* anyone draws pixels.

This skill converts a vague product idea (or a confusing existing screen) into:
1. A clear content hierarchy and navigation model
2. A sitemap / IA tree
3. A screen list (画面一覧) with each screen's role
4. Screen transitions (画面遷移) and user flows
5. Per-screen information priority

The Figma output **mirrors the viewer's rendering** — hi-fi navy wireframe frames + a Sun\* folder-tree sitemap + named user-flows (see `references/figma-output.md` for the exact tokens). Reproduce the viewer; bespoke visual/component design beyond that is out of scope.

## The pipeline (input → editable HTML → Figma)
This skill is a 3-stage pipeline. `ia-spec.json` (see `references/ia-spec-format.md`) is the single source of truth carried between stages.

```
input (idea / spec / existing screen)
  │  Stage 1: GENERATE  → ia-spec.json + markdown, then bin/build-doc.py embeds it into a standalone HTML
  ▼
ia-design.html  (data already embedded — user just opens it; tabbed, inline-editable)
  │  Stage 2: REVIEW & EDIT in the browser → 「ia-spec.json 保存」
  ▼
edited ia-spec.json
  │  Stage 3: TO FIGMA  (Figma MCP, see references/figma-output.md)
  ▼
Figma artboards mirroring the viewer (hi-fi screen frames + folder-tree sitemap + named flows)
```

- **Stage 1 — Generate:** run the Standard workflow below, emit a valid `ia-spec.json` + a markdown summary, then **build a ready-to-open HTML so the user never loads JSON manually**:
  ```bash
  python3 bin/build-doc.py <path>/ia-spec.json     # → <path>/ia-design.html (spec embedded) + auto-opens in browser
  ```
  It embeds the spec and **opens the HTML in the default browser automatically** (pass `--no-open` to skip). Also report the `ia-design.html` path.
  **出典（provenance）:** インプット文書（RFP・仕様書・議事録等）から生成するときは、各要素（screens / inventory / prd 項目 / stories …）に `sources` を記録する — **`{doc, section, quote}` 形式で、`quote`（該当部分の原文抜粋）を必ず含める**（場所だけでは検証できない。原文をそのまま1〜3文、要約しない）。ビューアでホバーすると場所＋該当部分が引用ブロックでツールチップ表示され、アウトプット→インプットの追跡ができる（詳細は `references/ia-spec-format.md` の「出典（sources）」参照）。根拠のない要素は `meta.assumptions` に。
- **Stage 2 — Review & edit:** the HTML opens as a **readable, tabbed document** styled to the **Sun\* brand** (Sun Red `#FF2200` single accent, Noto Sans JP). No header bar — a **left sidebar** holds the product title and the navigation as a **vertical tab list**; content renders on the right. Tabs:
  Tab order: PRD / ジャーニー / 業務フロー / ストーリーマップ / 情報構造 / サイトマップ / 画面一覧 / 画面遷移 / ワイヤー. Designed line-icons (not emoji).
  - **PRD** — product requirements as **16:9 slides**: プロダクト概要 / ゴール・非ゴール / ペルソナ / ユーザーストーリー / スコープ / 機能要件(+関連画面) / **トレーサビリティ（機能要件×画面）matrix + uncovered-req warnings** / 非機能要件 / 成功指標・リスク / マイルストーン. Optional `prd` object; per-screen `covers` feeds the matrix. **ペルソナ／ユーザーストーリーは想像しやすいよう色付きアバター（inline SVG, 名前/役割で色が決まる）付きカードで描画**。`prd.personas` をオブジェクトにすると **ユーザー理解カード**（who=どんな人 / goal=目的・達成したいこと / context=状況 / needs=知る必要 / infoOrder=見たい順番 / vocabulary=自然な言葉 / decisions=迷い・判断ポイント）を表示（文字列「名前: 状況」も可）。`prd.userStories` は「〜として、〜したい。なぜなら〜」形式だと役割が強調される。
  - **ジャーニー** — integrated UX view: PRD goals/stories → main-flow screens left→right (role icon, mini wireframe, action, key info) → 分岐・例外 (sub) flows → KPI/risks.
  - **業務フロー** — **業務フロー整理**: swimlane diagram from `businessFlow`（`lanes`＝担い手のレーン × `steps`＝順序つきの作業, type=start/action/decision/system/end, branch=条件）. レーンをまたぐ段差がハンドオフを表す。
  - **ストーリーマップ** — **ユーザーストーリーマップ**: `userStoryMap`（`activities`＝バックボーン → `tasks` → `stories`）を横軸＝行動の流れ・縦軸＝`releases`（MVP/Release 2/Later）でスライス。各ストーリーに priority。
  - **情報構造** — IA-upstream: **棚卸し→グルーピング**（`inventory`）／ **カードソーティング**（`cardSort`：項目をカテゴリへ分類, method=open/closed/hybrid＋未分類）／ **オブジェクトモデル**（`objects`：エンティティ＋主要属性＋親子/関連、例 顧客└商談└見積/契約/請求）。サイトマップtabには **ナビゲーション設計**（`navigation.patterns`）と **ラベリング**（`labels`：候補/採用/根拠）も付帯。
  - **サイトマップ** — visual **top-down hierarchy tree** with connector lines at every level: Product hero → section cards (screen-count badge) → screen cards nested under their section, → **sub-screens nested under a parent screen at arbitrary depth** (`screens[].parent`), each level indented with elbow connectors and progressively de-emphasized (smaller/lighter). Role icons + one-line summaries, priority as a left-rail accent.
  - **画面一覧** — decision-oriented **table** (画面 / 目的 / 主要情報 / 主操作 / 状態). No layout-blocks, no role/priority/section, no helper prose.
  - **画面遷移** — **left→right user-flow** so the user journey is imaginable: main-flow steps are **mini screen cards** (low-fi thumbnail + role icon + name + ▸主操作) connected by condition-labeled arrows; サブフロー branches below (`transition.kind`=main/sub). Read-only.
  - **ワイヤー** — high-fidelity mock in a health-app tone (navy `#3A4A66` on light-grey, rounded white cards). **Device switch (Mobile / Tablet / Desktop)** renders the matching frame — mobile/tablet = phone/tablet shell (status bar + bottom tab bar; FAB only on screens with `fab: true`), desktop = left-sidebar app layout. **Web+アプリ両方のプロジェクトでは `screens[].platform: "web"`** でその画面をブラウザ想定に切替 — mobile/tablet = URLバー付き・下タブ無し, desktop = **top-nav website layout**. 混在スペックでは Device の隣に **Platform 切替（すべて / Webサイト / アプリ）** が現れ、詳細・一覧・キャンバス全ビューをその platform の画面だけに絞り込める. **View toggle 詳細 / 一覧 / キャンバス**: 詳細 = one screen (横スクロール階層セレクタ + 目的コールアウト + 遷移元→現在→遷移先チップ + 仕様/コンポーネント); 一覧 = all screens as a scaled-frame gallery; **キャンバス = transition overview — every wireframe laid out left→right by flow with arrows (solid=main / dashed=sub / labels=condition), click a node → detail**. Rich widgets are **domain-neutral**, driven by each screen's `components`/items.
  **出典ツールチップ**: `sources` を持つ要素（画面カード・PRD項目・棚卸し・ストーリー等）にホバーすると「出典（インプット）」ツールチップが出る（点線下線＝出典あり）。
  The viewer is **read-only** — edits are made by instructing **Claude Code** (update `ia-spec.json`, re-run `build-doc.py`). No save / Figma / import / sample buttons. PRD renders on white (no black slides). ペルソナ/ユーザーストーリーは `prd.personas[].image`（ローカルパス可。build-doc が data URI 化）で顔写真アイコン表示、ストーリーは役割語 or `persona` で該当ペルソナに紐付く。
  - **注釈モード (Agentation, opt-in)** — open `ia-design.html?annotate=1` to load the Agentation visual-feedback toolbar (React + agentation from esm.sh) and sync annotations to the local Agentation MCP server (`endpoint` query overrides the default `http://localhost:4747`). Default (no flag) loads nothing external — the doc stays self-contained & offline. Requires internet (esm.sh) + the MCP server running; once the user annotates and clicks Send, read feedback via the `agentation_get_all_pending` / `agentation_watch_annotations` MCP tools.
- **Stage 3 — To Figma:** reproduce the viewer as Figma artboards — **hi-fi screen frames** matching the ワイヤー mock (navy health-app tokens, status/tab bars or desktop top-nav) + a **folder-tree sitemap** + **named user-flows** with wireframe-thumbnail cards. Match the viewer's look (see `references/figma-output.md`). Requires a **write-capable Figma MCP** (`use_figma`); the read-only Framelink MCP can't create content. Trigger = a **chat instruction** (e.g.「Figma に出して」); the skill reads `ia-spec.json` directly (the viewer has no Figma button — it stays read-only). **Always load `/figma-use` FIRST when available (mandatory before any `use_figma` call); if it isn't in the skill catalog, call the Figma MCP `use_figma` tool directly** following `references/figma-output.md`. Scope to what the user asks (all screens / only the sitemap / named screens). Confirm the target Figma file before creating. Implementation note: `use_figma` runs Plugin-API JS — pick a JP-capable font via `listAvailableFontsAsync`; `createPage` may not persist in headless MCP, so append to `figma.currentPage` and offset below existing content.

Run only the stages the user asks for. If they just want the design, stop after Stage 1. Always emit `ia-spec.json` in Stage 1 so the later stages remain possible.

## When to use
Trigger on: 情報設計 / 情報アーキテクチャ / IA / サイトマップ / 画面一覧 / 画面遷移 / ナビゲーション設計 / コンテンツ構造 / 画面構成 / グローバルナビ設計 / 業務フロー整理 / ユーザーストーリーマップ / カードソート / オブジェクトモデリング / 既存UIの構造レビュー / "organize this content" / "what screens do I need" / "how should navigation work".

Hand off (do **not** lead with this skill) when the user wants pure visual styling, color/typography, component-level UI code, or pixel-perfect Figma replication.

## Core principles
1. **Structure before surface.** Never start from layout or visuals. Start from content and tasks.
2. **One screen, one job.** Every screen must have a single primary role: inform, decide, input, compare, manage, confirm, recover, or complete.
3. **Findability beats decoration.** If the user can't locate or understand information, no visual polish saves it.
4. **Match the user's mental model**, not the org chart or the database schema.
5. **Minimize interaction cost** — fewer steps, less hesitation, less rework.
6. **Separate MVP from later.** Mark scope explicitly.

## The IA practice (guide the user through this — it is the core experience)
Information architecture is deciding *what to show, in what order, in what categories, under what names, and where the user goes next.* Three viewpoints govern every decision:
- **ユーザーの頭の中に合わせる** — group/name by the user's mental model, not the org chart or DB schema.
- **目的から逆算する** — derive needed information from what the user wants to accomplish, don't just list everything.
- **増えても破綻しない構造** — design so future content/features still fit.

Work the five elements through a five-step process, capturing each as a concrete artifact in `ia-spec.json`:

| Step | Activity | IA element | Artifact (field → tab) |
|---|---|---|---|
| 1. ユーザー理解 | 誰が・何の目的で・どんな状況で／何を達成したいか・何を知る必要が・どの順で見たいか・自然な言葉・どこで迷い判断するか | — | `prd.personas`（who/goal/context/needs/infoOrder/vocabulary/decisions）, `prd.userStories`, `businessFlow`, `userStoryMap` → PRD/業務フロー/ストーリーマップ |
| 2. 棚卸し | 必要な情報・機能を洗い出す（ページ/コンテンツ/機能/入力項目/ステータス/通知/権限/業務フロー） | 情報の整理 | `inventory` → 情報構造 |
| 3. グルーピング | 似た目的の情報をまとめる（カードソーティング/オブジェクトモデリング） | 情報の整理 | `inventory[].group`, `cardSort`, `objects` → 情報構造 |
| 4. 構造化 | 親子・関連を決める（顧客└商談└見積/契約/請求） | 構造設計 | `objects` (relations), `navigation`, `sitemap`, `screens[].section` → 情報構造/サイトマップ |
| 5. ナビ＆ラベル＆優先順位 | 導線・名前・見せる順序を決める | ナビゲーション設計 / ラベリング / 優先順位 | `navigation.patterns`, `labels`, `infoPriority`/`priority` → サイトマップ/画面一覧 |
| 6. 画面に落とす | 一覧か・詳細か・タブか・検索か・要約(ダッシュボード)か | — | `screens`, `transitions`, `components` → 画面一覧/遷移/ワイヤー |

When the user brings a vague idea, **walk these steps**: surface gaps (untyped inventory items, ungrouped info, objects without relations, internal-jargon labels, no priority order, dead-end navigation), propose options, and fill `ia-spec.json` accordingly.

## Required inputs
If enough is known, **proceed without interrogating the user**. Fill gaps with clearly-labeled assumptions. Try to identify:

- Product / service name and type (app, SaaS, LP, internal tool, marketplace, dashboard…)
- Target users + their primary goal and pain points
- Business goal
- Main use cases / tasks
- Device & context (desktop, mobile, responsive, kiosk…)
- Stage (idea, MVP, redesign, production)
- Desired output (sitemap, screen list, flow, IA review…)

Ask **at most one** blocking question at the start, and only if a true blocker exists. Save smaller clarifications for the end.

## Standard workflow
Run in order unless the user requests a specific output mode.

### Step 1 — Reframe the objective
Summarize in 4–6 lines:
- プロダクト目的:
- 主要ユーザー:
- ユーザーの主目標:
- ビジネス目標:
- 設計上の課題:

### Step 2 — Inventory content & tasks
List what information exists and what the user is trying to do. Don't jump to screens yet.

| User task | Intent | Information needed | Main action | Success state |
|---|---|---|---|---|

### Step 3 — Group & label content (the core IA work)
Cluster content into meaningful groups. Choose an organizing scheme (see `references/ia-patterns.md`): by task, by audience, by topic, by sequence, or hybrid. Name groups in the **user's language**.

- Content groups + rationale:
- Naming notes (avoid jargon, avoid internal terms):

### Step 4 — Navigation model
Decide how users move through the structure.

- Global navigation (top-level entries):
- Secondary / local navigation:
- Contextual / utility navigation:
- Cross-links & shortcuts:
- Navigation depth (target ≤ 3 levels to any key screen):

### Step 5 — Sitemap / IA tree
```text
Product
├── Section
│   ├── Screen
│   └── Screen
└── Section
    ├── Screen
    └── Screen
```

### Step 6 — Screen list (画面一覧)
| Screen | Role (1 of: inform/decide/input/compare/manage/confirm/recover/complete) | Key content | Primary action | Priority (Must/Should/Could) |
|---|---|---|---|---|

### Step 7 — Screen transitions & flow (画面遷移)
```text
Entry point
→ Screen / action
→ Decision point
  ├─ Case A → next
  └─ Case B → next
→ Completion
```
Cover: happy path, key branches, recovery path, drop-off risks, and where each state (empty/loading/error/success) appears.

### Step 8 — Per-screen information priority
For each Must screen:

**Screen name** — role:
1. 最優先で見せる情報
2. 補助情報
3. 詳細/オプション情報

Required states: empty / loading / error / success / permission-restricted (list only those that apply).

### Step 9 — Emit `ia-spec.json` + build the HTML doc
Produce a valid `ia-spec.json` per `references/ia-spec-format.md` (meta, navigation, every screen with `layoutBlocks` as low-fi regions, transitions). Then run `python3 bin/build-doc.py <path>/ia-spec.json` to embed it into a standalone `ia-design.html`. Report both paths. This is what the user opens to review.

### Step 10 — Review against the IA checklist
Run `references/review-checklist.md` and report pass/issues.

### Step 11 — (On request) → Figma
- Trigger: a chat instruction (「Figma に出して」). The viewer is read-only — no Figma button.
- **Load `/figma-use` FIRST when available** (mandatory before `use_figma`); otherwise call the Figma MCP `use_figma` directly. Follow `references/figma-output.md` to build artboards from `ia-spec.json`. Confirm the target Figma file before creating.

## Output modes
Pick the smallest mode that satisfies the request.

- **Mode A — Idea → IA:** Steps 1–8 (+9 if asked). Default for "design the screens/structure".
- **Mode B — IA-only:** Steps 1, 3, 4, 5, 6. For "sitemap / navigation / content structure" requests.
- **Mode C — Existing UI review:** Identify current structure → issues by severity (Critical blocks task / High causes confusion / Medium weakens clarity / Low polish) → proposed IA + screen list → checklist.
- **Mode D — Screen list & transitions only:** Steps 6–7. For 画面一覧/画面遷移 requests.

## Feedback collection
`bin/build-doc.py` counts builds and prints `[feedback]` lines once the skill has been used a few times (3rd build, then every 10th). **When you see `[feedback]` in the build output, append a short one-line ask + the feedback link at the END of your final answer** — e.g.「スキル改善のため、フィードバックがあれば Issue でお寄せください: <link>」. Do NOT show the link when no `[feedback]` line appeared (don't nag every run). The viewer sidebar also has a permanent「フィードバックを送る」link for designers reviewing the HTML.
Feedback: https://github.com/sun-asterisk-internal/takumi-design/issues

## Response rules
- Reply in **Japanese** unless the user writes in another language or asks otherwise.
- Use **tables** for screen/task lists, **text trees** for IA, **text flow diagrams** for transitions.
- Always state each screen's single role.
- Mark assumptions in an **「前提・仮定」** section.
- Keep MVP vs. later scope separated.
- Be concrete enough to act on. Avoid abstract UX jargon.
- Don't over-design; don't drift into visual styling.

## Final answer template
```markdown
# 情報設計 / IA 案

## 1. 前提・目的
- プロダクト目的 / ユーザー / 主目標 / ビジネス目標 / 設計課題
- 前提・仮定:

## 2. コンテンツ & タスク整理
| User task | Intent | Information needed | Main action | Success state |

## 3. 情報グルーピング & 命名
- グループと根拠 / 命名メモ

## 4. ナビゲーション設計
- グローバル / ローカル / コンテキスト / 深さ

## 5. サイトマップ (IA tree)
（text tree）

## 6. 画面一覧
| Screen | Role | Key content | Primary action | Priority |

## 7. 画面遷移
（text flow）

## 8. 主要画面の情報優先度
（per-screen）

## 9. （補助）ワイヤー/Figmaヒント
## 10. レビュー結果
```

See `references/ia-patterns.md` for organizing schemes and navigation patterns, and `examples/` for a worked example.
