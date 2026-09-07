# Skeletons

The literal shape of every file this skill owns. **This is the only definition of the detail document's
structure** — there is no template file under `functions/` to copy from (`tkm:pm-gather-requirements` leaves
that folder empty on purpose), so Step 5 writes the headings below verbatim, in this order.

`references/analysis-checklist.md` says what must be *decided* in each section and when it is done; this file
says what the section *looks like*. Read both.

The document is written in **Japanese** — it lives in the Japanese `project/` tree even though this skill is
written in English. Values carried over from `function-list.md` (the `F-ID`, the `Priority` value, the
`ROLE-xxx` IDs) are copied **verbatim**, in the vocabulary REQ wrote them in.

---

## `project/02_requirements/functions/function-{No}-{slug}.md`

`{No}` is the numeric part of the `F-ID` (`F-001` → `1`) and `{slug}` is a short kebab-case English slug of the
feature name (`ログイン・ログアウト` → `login`), per
[`skills/_shared/extras/pm-skills/function-breakdown.md`](../../_shared/extras/pm-skills/function-breakdown.md).

```markdown
# F-001 <機能名>

> 関連: [機能一覧](../function-list.md) ／ [画面一覧](../../04_screen-design/screen-list.md) ／
> [API一覧](../../03_basic-design/system-design/api-design/api-list.md)
> （存在しないドキュメントへのリンクは書かない）

## 1. 機能情報

| 項目 | 内容 |
| --- | --- |
| 機能ID | F-001 |
| 機能名 | <function-list.md の Function name を転記> |
| 概要 | <誰が・何を・何のために、を一文で> |
| 優先度 | <function-list.md の Priority をそのまま転記: must / should / could> |
| 対象ロール | <ROLE-001, ROLE-002 — role-list.md に実在する ID のみ> |
| 承認者 | |
| 承認日 | |

## 2. 背景・目的

<system-overview.md のどの課題・目的に対応するかを引用したうえで、3〜5 文。
 作らなかった場合に何が起きるか、成功をどう判断するかまで書く。>

## 3. ユースケース・業務フロー

| 項目 | 内容 |
| --- | --- |
| アクター | <ROLE-xxx（自動処理はシステム）> |
| トリガー | <何をきっかけに始まるか> |
| 事前条件 | <開始前に成立していなければならないこと> |

### 3.1 基本フロー

1. <アクター>が<行動>する
2. システムが<処理>する
3. …（3〜10 ステップ。最後のステップは完了状態を書く）

### 3.2 代替フロー

**A-1: <条件>**

1. …

### 3.3 例外フロー

**E-1: <発生条件>**

1. システムが<検知>する
2. <利用者に見えること>／<状態が戻るかどうか>

## 4. 入力・出力

| 項目 | 種別 | 内容・制約 |
| --- | --- | --- |
| <glossary.md の用語> | 入力 | <型 / 必須・任意 / 桁・範囲 / 形式 / 既定値。NFR 由来なら NFR-xxx を引用> |
| <…> | 出力 | <表示・生成・返却されるもの> |

<!-- 画面上の項目配置は対象外（04_screen-design/ の領域）。 -->

## 5. 業務ルール・制約

### 5.1 入力チェック

- <不正の条件 → そのとき何が起きるか>

### 5.2 権限制御

- <ROLE-xxx は…／権限のないロールに何が見えるか>

### 5.3 業務ロジック

- <計算・導出・状態遷移・一意性。同じ入力なら二人の読み手が同じ結果に至る書き方で>

### 5.4 非機能要件由来の制約

- <NFR-xxx: 保持期間 / タイムアウト / 監査ログ / 同時実行 / 上限値>

<!-- 該当しないカテゴリは削除せず「該当なし」と書く。 -->

## 6. 受入条件

| # | 受入条件 | 対応する §3 フロー / §5 ルール |
| --- | --- | --- |
| AC-1 | <観測可能で、合否が二択に決まる条件> | 3.1 基本フロー |
| AC-2 | <例外フローごとに 1 件> | 3.3 E-1 |
| AC-3 | <権限ルールごとに 1 件> | 5.2 |

## 7. 関連ドキュメント

| ドキュメント | 関連 |
| --- | --- |
| [機能一覧](../function-list.md) | この機能の元行 |
| <[F-002 …](./function-2-xxx.md)> | <スコープが隣接する機能> |

## 8. 改訂履歴

| 日付 | 更新者 | 内容 |
| --- | --- | --- |
| YYYY-MM-DD | <ba-analyze-requirement skill / ペルソナ名> | 初版作成 |
```

### Rules that go with this skeleton

- **A blocked section is empty apart from its marker.** `<!-- 未確定: qa.md QA-xxx 参照 -->` and nothing else —
  no provisional value, no option list. See `analysis-checklist.md` → "Final gate before writing the file".
- **Every `ROLE-xxx` resolves** to a row in `role-list.md`; every domain term matches `glossary.md`.
- **`優先度` is REQ's value, not a translation.** `function-list.md` writes `must` / `should` / `could`; copy
  the cell verbatim rather than mapping it to 必須 / 推奨 / 任意.
- **Do not create a template file under `functions/`.** This skeleton is the template; the folder holds only
  real analyzed features.

---

## `project/02_requirements/qa.md` — **not owned by this skill**

`qa.md` belongs to `tkm:pm-gather-requirements` (REQ) and its skeleton lives in that skill's `SKILL.md` under
"Recording Open Items". This skill **appends to it in that exact shape** and never re-shapes it:

```markdown
## 1. Items for Confirmation

| QA-ID | Subject | Question | Status | Raised on | Answer | Answer date | Respondent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QA-001 | (system-overview §2 etc. / F-ID) | (question addressed to the customer) | Unanswered | YYYY-MM-DD | | | |

## 2. Revision History

| Date | Updated by | Content |
| --- | --- | --- |
| YYYY-MM-DD | pm-gather-requirements skill | Raised QA-001 |
```

When the file does not exist yet, create it from **REQ's** skeleton (read
[`skills/pm-gather-requirements/SKILL.md`](../../pm-gather-requirements/SKILL.md) → "Recording Open Items"),
then append your row. A parked decision's three options go **inside the `Question` cell**, separated by `<br>`,
so the customer can pick one without opening another document:

```
QA-014 | F-001 §5 | 削除した申請書の保持期間について確認させてください。<br>A案: 30日間は管理者のみ復元可（推奨 / NFR-012 の監査要件）<br>B案: 即時完全削除<br>C案: 無期限保持 | Unanswered | 2026-08-24 | | | |
```

The internal side of the question — the reflection target, what it blocks, the citation behind the
recommendation — is **not** a second table in `qa.md`. It goes to `## Open Items` in
`plans/business-analysis/ba-memory.md`. See "Shared conventions" in `SKILL.md`.
