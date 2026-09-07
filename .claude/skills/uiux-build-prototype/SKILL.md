---
name: tkm:uiux-build-prototype
display-name: "SW*-GP"
description: "SW*-GP — Build a grounded, clickable prototype as a real Vite + React + TypeScript + Tailwind + shadcn-style project. Takes um-spec.json (user models), ia-spec.json (information architecture), documents, existing HTML, and a design direction; normalizes the direction into design tokens (shadcn CSS variables); scaffolds from a shipped template; and writes screens as React components over an owned ui/ component kit — so iteration is HMR-fast and the prototype carries straight into implementation. Ships a built-in review shell and a quality gate (grounding trace + UX heuristics + a11y + typecheck/build). `npm run build` emits a single self-contained HTML for stakeholders. Use when the user asks for プロトタイプ, プロト作成, クリッカブルモック, 画面モック, 動くモック, プロトタイピング, prototype, clickable mock, 'make it clickable', 'turn the IA into screens', wants a prototype grounded in personas/IA/specs, wants fast prototype iteration, or wants the prototype to carry into implementation."
category: design
roles: [designer]
license: MIT
metadata:
  author: kitamachishun
  version: "2.2.0"
  portable: "claude-code"
  upstream: "sun-asterisk-internal/takumi-design@8fb425c"
---

# SW\*-GP — Grounded Prototyping (Vite + React + shadcn)

## Purpose
Turn upstream design artifacts into a **clickable, review-ready prototype that is already real code** — without inventing anything. "Grounded" means every screen, label, mock value, and visual token **traces back to an input**: the user model (`um-spec.json` from [`uiux-model-users`](../uiux-model-users)), the information architecture (`ia-spec.json` from [`uiux-design-information-architecture`](../uiux-design-information-architecture)), project documents, existing HTML, or an explicit design direction. Anything not traceable is a **clearly-flagged assumption**, never silent.

The prototype is a **Vite + React + TypeScript + Tailwind v4 project with an owned shadcn-style `ui/` kit**, scaffolded from this skill's `template/`. That buys three things the user cares about:
1. **Fast iteration** — `npm run dev` + HMR; edits to `src/screens/*.tsx` render instantly; feedback loops are seconds, not rebuilds.
2. **Component reuse** — screens compose `components/ui/*` (Button/Card/Input/Badge/Skeleton…) and project `patterns`; quality floor rises, drift falls.
3. **Implementation carry-over** — the deliverable IS a React codebase with shadcn-convention tokens; the team keeps building on it instead of re-implementing a mock.

This is the *downstream* of SW\*-UM → SW\*-IA. If no IA or user model exists, offer to run those first (or proceed with flagged assumptions if declined).

## The pipeline
`pt-spec.json` (see `references/pt-spec-format.md`) carries the grounding: meta/sources, design tokens, requirements, screen metadata (grounding per screen), transitions. Screens themselves live as code in `src/screens/`.

```
inputs (um-spec.json / ia-spec.json / 資料 / 既存HTML / デザイン方針)
  │  Stage 0: GROUND — inventory inputs (meta.sources), build the grounding map,
  │            normalize the design direction into tokens. Gaps → flagged assumptions.
  ▼  Stage 1: SCAFFOLD & GENERATE
  │     bash bin/scaffold.sh <dest> "<product>"     # template copy + npm install
  │     fill pt-spec.json → map design into src/styles/globals.css (:root vars)
  │     write src/screens/<id>.tsx (+ registry, patterns.tsx) per the contract
  ▼  Stage 2: ITERATE & REVIEW — npm run dev (HMR)
  │     #/<screen-id> = pure prototype ／ #/review/* = review shell ／ 右下FAB(dev常時)で往復
  ▼  Stage 3: QUALITY GATE — checklist + `npx tsc --noEmit` + `npm run build` (must pass)
  ▼  Stage 4: SHARE — dist/index.html（単一・自己完結・開くだけ。?switch=1 で切替FAB）
  ▼  Stage 5 (on request): TO FIGMA — references/figma-output.md
      handoff: そのまま実装リポジトリへ（プロトタイプ自体がコード）
```

- **Stage 0 — Ground:** read every input. Build `meta.sources` (one entry with a stable `id` per input), extract:
  - from **ia-spec.json**: screen ids (KEEP them — they are the traceability join key), transitions, labels, `prd.functionalReqs` → `requirements`, per-screen `components`/`infoPriority` → screen content
  - from **um-spec.json**: personas (`vocabulary` → UI copy, `infoOrder` → content order, `decisions` → helper UI), stories (`priority` → scope), journeys (pain points → states & recovery UI)
  - from **documents / HTML**: requirements, terminology, visual patterns
  - from the **design direction**: normalize into `design` tokens (direction word, colors, typography, shape) with `source` attribution
  - **Do NOT invent data.** Mock content comes from the inputs; judgment calls go into `meta.assumptions` / screen `grounding.assumptions`.
- **Stage 1 — Scaffold & generate:**
  ```bash
  bash bin/scaffold.sh <dest-dir> "<プロダクト名>"   # copies template/, sets name/title, npm install
  ```
  Then, in the scaffolded project:
  1. Write `pt-spec.json` (meta / design / requirements / screens metadata / transitions).
  2. Map `design` into `src/styles/globals.css` **`:root` only** — the vars follow shadcn conventions (`--primary`, `--background`, `--muted-foreground`, `--radius`…), so restyling is a one-block edit and the tokens carry into implementation.
  3. Write each screen as `src/screens/<id>.tsx` per the contract in `references/pt-spec-format.md` and the craft rules in `references/ui-craft.md` (both mandatory): compose `components/ui/*`, navigate with `useGoto()`, branch on the `state` prop, responsive via Tailwind **container-query variants** (`@3xl:` = 768px — the review device frames are `@container`s, so Mobile/Tablet/Desktop previews real breakpoints; never viewport `md:`).
  4. Register screens in `src/screens/index.ts`; put recurring patterns in `src/components/*` and catalog them in `src/components/patterns.tsx` (name + **usage rule** + `tier`(molecule/organism) + usedIn + live specimen). Global chrome (header / tab bar) belongs in the catalog too — organisms.
  5. `npm run dev` — report the URL. **Iteration = edit the .tsx → HMR reflects instantly**; spec-level changes (grounding, requirements, tokens) edit `pt-spec.json` / `globals.css`.
- **Stage 2 — Iterate & review:** the app has two faces:
  - **`#/<screen-id>[/<state>]`** — the pure prototype, full-viewport, clickable end-to-end. What a stakeholder sees.
  - **`#/review/…`** — the review shell (Sun\* chrome; the prototype renders in the product's own tokens): **概要** (meta/sources/assumptions/coverage) / **プロトタイプ** (screen・device・state switches, 遷移元→現在→遷移先, 根拠パネル) / **フロー** (main=実線・sub=破線, clickable thumbnails) / **トレーサビリティ** (requirements×screens matrix + uncovered warnings + per-screen grounding) / **デザインシステム** (Atomic Design構成: トークン＝**その場でカラー/角丸をライブ調整**でき contrast 検査つき・確定値は「:root CSSをコピー」で globals.css へ還元 / Atoms＝ui/キット全バリアント / Molecules・Organisms＝patterns.tsx を tier でグルーピング / Pages＝全画面一覧から proto へ).
  - The **round FAB** (bottom-right) toggles pure ⇄ review keeping the current screen — always visible under `npm run dev`; in the built file only with `?switch=1`.
- **Stage 3 — Quality gate:** run `references/review-checklist.md` AND verify `npx tsc --noEmit` and `npm run build` pass. Blocking issues (uncovered Must requirement, untraceable screen, missing error state on a data screen, contrast failure, build error) get fixed before handover.
- **Stage 4 — Share:** `npm run build` → `dist/index.html` — a **single self-contained HTML** (vite-plugin-singlefile). Opens from file://, works offline, hash-routes work. Tell the user: plain URL = プロトタイプのみ / `#/review/...` = レビュー / `?switch=1` = 切替FAB. (Offline/self-contained holds only when images are **embedded** — the default; if the user opted into **external image URLs** per `references/ui-craft.md` §9, the built file needs internet — say so.)
- **Stage 5 — To Figma (on request):** 「Figma に出して」 → **load `/figma-use` FIRST when available (mandatory before any `use_figma` call)**; follow `references/figma-output.md` (reads `pt-spec.json` + `src/screens/*.tsx`, uses the product's tokens). Confirm the target file before creating.

Always keep `pt-spec.json` in sync with the code — it is what makes the prototype *grounded* (the review shell renders it live, so drift is visible).

## When to use
Trigger on: プロトタイプ / プロト / プロトタイピング / クリッカブルモック / 動くモック / 画面モック / ハイファイモック / 「IAを画面にして」 / 「ペルソナとIAからプロトタイプを」 / prototype / clickable mock / "make it clickable" / "turn these specs into screens" / 「プロトタイプを速く回したい」 / 「実装に繋がる形で」.

Hand off (do **not** lead with this skill) when the user wants user understanding (→ `uiux-model-users`), screen structure / IA (→ `uiux-design-information-architecture`), or production feature work on an existing app (→ implementation workflow). If neither um-spec nor ia-spec exists, propose running those first; proceed only with the user's OK and heavy assumption flagging.

## Core principles
1. **Grounded or flagged.** Every screen, label, mock value, and token traces to a source — or is listed as an assumption. No silent invention.
2. **The spec IDs are the thread.** Reuse ia-spec screen ids; reference persona names and story titles verbatim.
3. **Tokens before pixels.** `design` → shadcn CSS vars in one `:root` block; screens use token utilities (`bg-primary`, `text-muted-foreground`) — one edit restyles everything, and the vars are implementation-real.
4. **Components before screens.** Recurring patterns live once in `components/` with a usage rule in `patterns.tsx`; screens compose, not copy.
5. **States are part of the screen.** A data screen without empty/loading/error is unfinished; journey pain points name the recovery states that matter.
6. **Speak the persona's language.** Copy uses `vocabulary`; order follows `infoOrder`; helper UI sits at `decisions` points.
7. **Iteration speed is a feature.** Small files, HMR, typecheck — the loop from feedback to fixed screen should be minutes.
8. **Quality is a gate, not a hope.** Checklist + typecheck + build run every time; blocking issues are fixed before delivery.

## Required inputs
If enough is known, **proceed without interrogating the user**. Fill gaps with clearly-labeled assumptions. Try to identify: upstream artifact paths (um-spec / ia-spec), other documents or reference HTML, the design direction, target device (responsive is the default), scope (all Must screens? one flow?), and where the project should live. Ask **at most one** blocking question at the start, and only if a true blocker exists.

## Standard workflow
1. **Inventory the inputs** (Stage 0) — sources list + 4–6 line summary + what's missing → assumptions.
2. **Normalize design → tokens + kit plan** — fill `design` (direction/colors/typography/shape/notes/source); plan the pattern catalog (which recurring components this product needs) BEFORE writing screens.
3. **Scaffold** — `bash bin/scaffold.sh <dest> "<product>"`.
4. **Select and scope screens** from the IA (default: all Must screens covering the main flow end-to-end), fill `pt-spec.json` screens metadata (id/name/role/states/grounding/mock) + transitions.
5. **Write tokens** into `globals.css :root`, **write components** (`components/*` + `patterns.tsx`), **write screens** (`screens/*.tsx` + registry) — following `references/ui-craft.md` (mandatory) and the contract.
6. **Run** `npm run dev`, walk every flow and state, fix visually.
7. **Quality gate** — `references/review-checklist.md` + `npx tsc --noEmit` + `npm run build`; fix blocking issues.
8. **Deliver** — report: dev URL, `dist/index.html` path (+ URL forms), coverage result, gate outcome, assumptions.

## Output modes
- **Mode A — Full prototype:** the whole workflow. Default for 「プロトタイプを作って」.
- **Mode B — One-flow prototype:** scoped to a named flow.
- **Mode C — Restyle:** edit `globals.css :root` (+ `design` in spec), verify contrast, rebuild.
- **Mode D — Iterate:** edit named screens/components on an existing project (HMR loop); keep `pt-spec.json` grounding in sync; re-run the gate.
- **Mode E — To Figma:** Stage 5.

## Response rules
- Reply in **Japanese** unless the user writes in another language or asks otherwise.
- **Separate grounded from assumed** — every deliverable ends with a 「前提・仮定」 section mirroring `meta.assumptions`.
- Always report: sources used, requirement coverage, quality-gate outcome (incl. typecheck/build), dev URL and share-file path.
- Never present invented data as input content. Input conflicts are surfaced, not silently resolved.
- Don't drift upstream (user modeling, IA restructuring) — send suggestions back instead.
- **Feedback — once per project.** ある程度スキルを使い終えたタイミング＝**初回デリバリー報告（Stage 4 / テンプレート §7）の末尾**で一度だけ、フィードバック用の GitHub Issues リンクを提示して協力を依頼する。イテレーション（Mode C/D）や同一プロジェクトの後続報告では繰り返さない。回答は任意である旨を一言添える。
  リンク: https://github.com/sun-asterisk-internal/takumi-design/issues
  なお、レビューシェルのサイドバー下部フッターにも同リンクが常設されている（`template/src/review/review-layout.tsx` の `FEEDBACK_URL` — 生成時に削除しないこと）。

## Final answer template
```markdown
# グラウンデッド・プロトタイプ

## 1. インプットと前提
- ソース一覧（id / 種別 / パス） / 前提・仮定（未検証）

## 2. デザイントークン & コンポーネント
- direction / 主要トークン / パターンカタログ / 出典

## 3. 画面とフロー
- 画面一覧（id / 役割 / 状態 / 根拠） / フロー（main / sub）

## 4. 成果物
- プロジェクト: <path>（npm run dev — HMRで即編集反映）
- 共有用: dist/index.html（開くだけ ／ #/review/… ＝レビュー ／ ?switch=1 ＝切替FAB）

## 5. 品質ゲート結果
- 要件カバレッジ / ヒューリスティック / a11y / typecheck・build

## 6. 次の一手
- イテレーション方法（「◯◯画面の△△を変えて」→ 即反映）・実装への引き継ぎ・Figma出力

## 7. フィードバックのお願い（初回デリバリー時のみ）
- SW*-GP スキル改善のため、よろしければ GitHub Issues でフィードバックをお寄せください（任意）:
  https://github.com/sun-asterisk-internal/takumi-design/issues
```

See `references/pt-spec-format.md` (schema + screen contract), `references/ui-craft.md` (mandatory craft rules), `references/review-checklist.md` (quality gate), `references/figma-output.md`, and `examples/` for working samples — `hashiru-react/` (mobile-app・toC), `keihi-react/` (web-app・toB), `tomarie-react/` (web-app・CtoCマーケットプレイス、リッチなマイクロインタラクションの手本). `examples/legacy-html/` holds the pre-v2 HTML artifacts for reference.
