# Skeletons

The literal shape of every file this skill owns. **This is the only definition of the session document's
structure** — do not copy the headings out of an earlier session file, and do not invent sections. When Step 7
writes a session, it writes exactly the headings below, in this order.

Fill the placeholders; delete nothing. A section that genuinely has no content keeps its heading and carries
`該当なし` or `（なし）` on its own line, so a reader can tell it was considered rather than dropped.

---

## `project/09_wip_plan/brainstorming-{YYYY-MM-DD}-{N}.md`

`{YYYY-MM-DD}` is the session date and `{N}` is the session number **for that date**, starting at 1 — so the
first session of 2026-08-24 is `brainstorming-2026-08-24-1.md`. Check with `Glob` before choosing `{N}`.

```markdown
---
status: in-progress   # in-progress while the session is running / done once Step 7 completes
date: YYYY-MM-DD
session_no: 1
topic: <テーマを一文で>
session_type: 発散重視   # 発散重視 / 課題解決 / リスク洗い出し
techniques: []          # 使用した手法名のリスト
idea_count: 0
---

# ブレインストーミング記録: <テーマ>

## 1. セッション概要

| 項目 | 内容 |
| --- | --- |
| テーマ | <一文。Step 2 で確定したもの> |
| 目的（良い結果とは） | <機能候補の洗い出し / 方針の決定 / リスク一覧 など> |
| セッション種別 | <発散重視 / 課題解決 / リスク洗い出し> |
| 実施日 | YYYY-MM-DD |
| 所要時間 | <予定 / 実績> |
| 参加者 | <ファシリテーター: BA、参加者: …> |
| 前提資料 | <system-overview.md など。無ければ「なし（ユーザーの説明のみ）」> |

## 2. 使用した手法

| # | 手法 | カテゴリ | 所要時間 | 出たアイデア | なぜこの手法か |
| --- | --- | --- | --- | --- | --- |
| 1 | <techniques.md の手法名> | <structured / creative / adversarial …> | <分> | #1-#12 | <引用元を挙げた一文> |

## 3. アイデア一覧

<!-- 番号はセッション中に付けた番号のまま。出所が AI のものは必ず [AI案] を付ける。 -->

| # | アイデア | 内容 | なぜ新しいか | 領域 | 出所 |
| --- | --- | --- | --- | --- | --- |
| #1 | <短い見出し> | <一文> | <現状との差分> | <業務 / 運用 / データ / エンドユーザー / リスク / コスト> | <ユーザー / [AI案]> |

## 4. グルーピング

<!-- Affinity Mapping の結果。どのグループにも入らなかった案は「その他」に残す（消さない）。 -->

### <グループ名（ユーザーの言葉で）>

- #1, #4, #9 — <このグループが何をまとめているか一文>

### その他（未分類）

- #17 — <理由>

## 5. 優先順位付け

**評価軸:** <影響度 × 工数 / Now・Next・Later / MoSCoW / 保留（順位付けは行わなかった）>

| 順位 | # | アイデア | 評価 | 選んだ理由 |
| --- | --- | --- | --- | --- |
| 1 | #4 | <見出し> | <軸に応じた値> | <三ヶ月後にスコープを説明できる理由> |

**必須として落とせないもの:** <法令・既存業務の代替・契約上の約束。無ければ「なし」>

## 6. 次のアクション

<!-- Step 8 の三つのバスケット。この記録は提案までで、他ファイルへの書き込みは行わない。 -->

### ① 候補機能 → `project/02_requirements/function-list.md`（PM / `tkm:pm-gather-requirements`）

| # | 機能名（案） | 概要 | 想定 Priority | 想定ロール |
| --- | --- | --- | --- | --- |
| #4 | <案> | <一文> | <must / should / could> | <ROLE-xxx が分かれば> |

### ② 確認事項 → このファイルの `## 8`（振り分け先なし・報告のみ）

未回答 <n> 件 / 回答者: <誰に聞けば決まるか>。内容は `## 8` にあり、ここには転記しない。

### ③ リスク → `project/01_management/risks-problems/risk-list.md`（PM / `RISK`）

| # | リスク | 影響 | 気付いた手法 |
| --- | --- | --- | --- |
| #22 | <案> | <一文> | <手法名> |

## 7. 参照した資料

| 資料 | 使い方 |
| --- | --- |
| `project/02_requirements/system-overview.md` | <推奨の根拠に使った箇所。読めなければ「なし」> |

## 8. 未確定事項

<!-- このセッションの確認事項の登録簿。qa.md には起票しない（qa.md は REQ / FA が持つ要件フェーズの登録簿）。
     状態: 未回答 / 回答済 / 反映済（`## 3`-`## 6` に反映済み） -->

| BQ-ID | 質問 | 対象 | 状態 | 記録日 | 回答 | 回答日 | 回答者 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BQ-001 | <お客様がそのまま答えられる一文> | <#4 / 優先順位 / スコープ など> | 未回答 | YYYY-MM-DD | | | |

## 8-2. 未確定事項の詳細

<!-- 選択肢を提示した保留は必ずここに詳細ブロックを持つ。選択肢は提示したまま（要約しない）。 -->

### BQ-001: <質問の見出し>

- **質問:** <`## 8` と同じ一文>
- **選択肢:**
  - A案: <提示したとおり>
  - B案: <提示したとおり>
  - C案: <提示したとおり>
- **推奨:** <A案 など> — <根拠として引用した資料・発言>
- **ブロック内容:** <これが決まるまで何が決められないか>
- **状態:** 未回答
```

### Rules that go with this skeleton

- **`## 8` is the register of record for the session.** Never route its items into
  `project/02_requirements/qa.md`, and never assign them `QA-xxx` IDs — `BQ-nnn`, numbered within this file.
- **`## 6 ②` carries the count and who to ask, nothing else.** The questions themselves live in `## 8` and are
  not duplicated there.
- **`## 3` keeps the session numbering.** An idea that was `#7` during the session is `#7` in the file, in
  `## 4`, in `## 5` and in `## 6`.
- **Frontmatter `status`** is `in-progress` for a session written mid-flow (Step 7 still runs) and `done` once
  the session finished through Step 6. Step 1 resumes only from `in-progress`.
- **Nothing here is written into another file.** `## 6` is a proposal; `function-list.md` and `risk-list.md`
  belong to their owning skills.
