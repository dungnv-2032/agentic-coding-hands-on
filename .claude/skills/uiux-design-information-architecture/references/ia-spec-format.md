# ia-spec.json — the interchange format

`ia-spec.json` is the single source of truth that flows: **generate → edit in HTML → push to Figma.**
Every stage reads and writes this exact shape. Keep it valid JSON.

```jsonc
{
  "meta": {
    "product": "string",
    "users": "string",
    "primaryGoal": "string",
    "businessGoal": "string",
    "device": "mobile | desktop | responsive | tablet",
    "stage": "idea | MVP | redesign | production",
    "assumptions": ["string", "..."]
  },
  "navigation": {
    "model": "flat | hierarchical | hub-and-spoke | tabbed | faceted | wizard",
    "global": ["top-level nav label", "..."],
    "notes": "string",
    "patterns": [   // OPTIONAL — wayfinding design (情報構造/サイトマップ tab)
      { "type": "グローバルナビ|サイド|タブ|パンくず|検索|フィルタ|関連リンク|CTA", "where": "どこに置くか", "notes": "string" }
    ]
  },

  // ---- IA-upstream artifacts (all OPTIONAL; shown in the 情報構造 / サイトマップ tabs) ----
  "inventory": [   // 棚卸し→グルーピング: raw information/functions clustered into meaningful groups
    { "item": "顧客情報", "type": "page|content|function|field|status|notification|permission|flow", "group": "顧客" }
  ],
  "objects": [     // オブジェクト関係図: entities + key attributes + relations (parent/child & associations)
    { "name": "顧客", "attributes": ["氏名","会社"], "relations": [ { "to": "商談", "kind": "has-many|has-one|relates" } ] }
  ],
  "labels": [      // ラベリング: user-facing name decisions (avoid internal jargon)
    { "term": "商談", "alternatives": ["案件","プロジェクト"], "rationale": "現場の呼称に合わせる" }
  ],
  "cardSort": {    // カードソーティング: 棚卸し項目をユーザー感覚でカテゴリへ分類した結果（情報構造 tab）
    "method": "open | closed | hybrid",   // open=分類名も利用者が決める / closed=既定カテゴリへ振り分け
    "categories": [ { "name": "カテゴリ名", "cards": ["項目","項目"], "rationale": "なぜまとまるか" } ],
    "unsorted": ["まだ分類されていない項目"]
  },
  "businessFlow": {  // 業務フロー整理: スイムレーン図（業務フロー tab）
    // 形式A（単一フロー）: title / lanes / steps を直接持つ
    // 形式B（As-Is / To-Be 併記）: asIs と toBe をそれぞれ { title?, lanes[], steps[] } で持つ → 上下2段で表示
    "title": "フローの説明（任意）",
    "lanes": ["申請者","承認者","経理","システム"],   // 担い手＝レーン（行）。省略時は steps の lane 出現順から導出。lane 名がペルソナ名と一致すると顔写真、システム/アプリ系はシステムアイコンを表示
    "steps": [   // 配列順＝時間順（左→右の列）。レーンをまたぐ段差がハンドオフ
      { "id": "b1", "lane": "申請者", "name": "申請を作成", "type": "start|action|decision|system|end", "branch": "分岐条件（任意）" }
    ]
    // 例（As-Is/To-Be）: "asIs": { "title": "現状", "lanes": [...], "steps": [...] }, "toBe": { "title": "提案", "lanes": [...], "steps": [...] }
  },
  "userStoryMap": {  // ユーザーストーリーマップ（ストーリーマップ tab）
    "releases": ["MVP","Release 2","Later"],   // 縦軸のリリース帯（行）。省略時は stories の release から導出。先頭＝MVP
    "activities": [   // 横軸のバックボーン。activity に persona(名前/index/役割語) を付けると、ストーリーマップがペルソナごとに分割表示される（未指定なら単一マップ）
      { "name": "アクティビティ", "persona": "出品者",   // OPTIONAL — prd.personas と照合してペルソナ別マップに振り分け
        "tasks": [
        { "name": "ユーザータスク", "stories": [ { "title": "〜できる", "release": "MVP", "priority": "Must|Should|Could" } ] }
      ] }
    ]
  },
  "screens": [
    {
      "id": "kebab-id",                // unique; referenced by transitions & sitemap
      "name": "画面名",
      "summary": "一覧で表示する一文の役割説明",  // optional; if omitted, derived from role + primaryAction + infoPriority
      "section": "グローバルナビ名",      // optional; which navigation.global entry this screen sits under (drives the sitemap tree). Empty/omitted = 未分類
      "parent": "screen-id",             // OPTIONAL — 親画面ID。指定すると、その画面の子（サブ画面）としてサイトマップに任意の深さで入れ子表示される。section は親から継承（指定不要）
      "role": "inform|decide|input|compare|manage|confirm|recover|complete",
      "platform": "web | app",         // OPTIONAL — Web+アプリ両方を作るプロジェクト用。"web"=ブラウザで見る画面（モバイル/タブレット=URLバー付き・下タブ無し、デスクトップ=トップナビ型サイト）。省略/"app"=ネイティブアプリ画面（下タブ・サイドバー）
      "standalone": false,             // OPTIONAL — true にすると ワイヤーでアプリのナビ枠（デスクトップ=左サイドバー / モバイル=ステータスバー・下タブ）を描画しない。ログイン/認証/スプラッシュ等、ログイン前の画面向け
      "fab": false,                    // OPTIONAL — true にすると下タブ中央に FAB（＋ボタン）を表示。新規追加/作成が主操作のアプリ画面のみに付ける（既定は非表示）
      "priority": "Must | Should | Could",
      "infoPriority": ["最優先情報", "補助情報", "詳細"],
      "primaryAction": "string",
      "states": ["empty", "loading", "error", "success", "permission-restricted"],
      "layoutBlocks": ["Header", "Main content", "Action area"],  // top→bottom regions
      "components": [                  // OPTIONAL — for accurate hi-fi mock. If omitted, the viewer infers components from layoutBlocks + infoPriority.
        // items は具体的で現実的な内容にする（「項目1」等のプレースホルダは避ける）。form/table の items＝フィールド/列の実ラベル（例「氏名」「金額」「更新日」「状態」）にすると、
        // ビューアが意味に応じた現実的なサンプル値（山田太郎 / ¥12,000 / 2026/07/21 / 承認待 …）を自動で埋め、検討可能な"入力済み"ワイヤーになる。
        { "type": "header|tabs|search|form|list|table|calendar|cards|button|image|text|footer", "label": "見出し", "items": ["表示項目1", "表示項目2"] }
        // calendar = 月間カレンダーの7列グリッド表示。items＝各日に載せる献立チップの元ネタ（例「白米・味噌汁」）。table より予定・献立の俯瞰に向く
      ],
      "covers": ["この画面が充足する prd.functionalReqs の文言"],  // OPTIONAL — feeds the PRD traceability matrix (要件×画面). Match the requirement text exactly.
      "sources": ["rfp.md › 3.2 決済要件"]   // OPTIONAL — 出典（この画面の根拠となったインプット）。ホバーでツールチップ表示（下記「出典」参照）
    }
  ],
  "transitions": [
    { "from": "screen-id", "to": "screen-id", "condition": "string (optional)", "kind": "main | sub", "flow": "フロー名（任意）" }  // kind drives the left→right flow: main = primary path, sub = branch. Default main. flow = optional name to group/label flows in 画面遷移 (e.g. 購入フロー / 出品フロー); same kind+flow render together under one labelled block.
  ],
  "sitemap": null,  // optional explicit tree; if null, derive from navigation.global + screens

  "prd": {          // OPTIONAL — product requirements, shown in the PRD tab (all fields optional)
    "background": "背景・課題（なぜ作るか）",
    "goals": ["ゴール / 成功の定義"],
    "nonGoals": ["やらないこと"],
    "personas": [   // 文字列「名前: 状況」でも、ユーザー理解を構造化したオブジェクトでも可
      {
        "name": "出品者 / 田中さん（22・学生）",   // どんな人（属性込み）
        "image": "assets/p1.jpg | data:image/jpeg;base64,...",  // OPTIONAL — 顔写真/イラストをアバターに使用。未指定時は名前から色が決まるSVGアバター。ローカルパス（specからの相対 or 絶対）を書けば build-doc.py が自動で data URI に埋め込み自己完結HTML化する（.jpg/.png/.gif/.webp/.svg 対応）。data URI 直書きも可
        "who": "家の不要品を売りたい学生。出品は初めて",  // 人物像
        "goal": "不要品を手間なく現金化したい",          // 何の目的で / 何を達成したいか
        "context": "通学や家事の合間にスマホで",         // どんな状況で使うか
        "needs": ["相場価格", "送料の目安"],            // そのために何を知る必要があるか
        "infoOrder": ["商品写真", "価格", "状態"],       // どの順番で情報を見たいか（順序つき）
        "vocabulary": ["出品", "らくらく発送"],          // 自然に理解できる言葉
        "decisions": [ { "point": "価格設定", "note": "相場が分からず迷う" } ]  // どこで迷い・判断するか（string でも可）
      }
    ],
    "userStories": [   // 文字列「〜として、〜したい。なぜなら〜」でも、{ as, want, why, persona } オブジェクトでも可
      "個人コレクターとして、最小入力で鑑定したい。なぜなら離脱するから",  // 役割語が personas の名前/ロールと一致すれば、そのペルソナの写真アイコンで表示
      { "as": "投資ユーザー", "want": "Pop分布を見たい", "why": "資産価値を判断したいから", "persona": "高額保有/投資ユーザー" }  // persona=名前 or 配列index で明示紐付け
    ],
    "scopeIn": ["対象"], "scopeOut": ["対象外"],
    "functionalReqs": ["機能要件"], "nonFunctionalReqs": ["非機能要件"],
    "metrics": ["成功指標 / KPI"], "risks": ["リスク・前提"], "milestones": ["時期 / 内容"]
  }
}
```

## 出典（`sources`）— インプットとのトレーサビリティ
アウトプットの各要素に、根拠となったインプット（RFP・仕様書・議事録・ヒアリング等）を記録できる。ビューアでその要素に**ホバーすると出典がツールチップ表示**される — 場所（📄 ファイル › 見出し）＋**該当部分（原文の抜粋 = `quote`）が引用ブロック**で出る。

- **形式**: オブジェクトの配列を基本とし、**`quote`（該当部分の原文抜粋）を必ず入れる** — 場所だけでは検証できない。文字列も可（場所のみになるため非推奨）。
  ```jsonc
  "sources": [
    { "doc": "rfp.md", "section": "3.2 決済要件", "quote": "決済はクレジットカードと請求書払いに対応すること" },
    "rfp.md › 3.2 決済要件"   // 文字列: 場所の一行のみ（quote 無し・非推奨）
  ]
  ```
  `quote` は該当箇所の**原文をそのまま**1〜3文で抜粋する（要約・言い換えをしない — 読者が原文と突き合わせて検証するための引用）。
- **付けられる場所**: `screens[]` / `inventory[]` / `objects[]` / `labels[]` / `cardSort.categories[]`（と cards のオブジェクト形式）/ `businessFlow.steps[]` / `userStoryMap` の stories / `navigation.patterns[]` / `prd.personas[]`・`prd.userStories[]`（オブジェクト形式）。
- **PRD の文字列リスト**（goals / nonGoals / scopeIn / scopeOut / functionalReqs / nonFunctionalReqs / metrics / risks / milestones）は、項目を `{ "text": "…", "sources": [...] }` のオブジェクトにすると出典を付けられる（文字列のままでも可）。`functionalReqs` をオブジェクトにした場合も、`screens[].covers` は **text の文言**と照合される。
- インプット文書から生成する場合は付与を推奨。根拠のない要素（仮定）には付けず、`meta.assumptions` に記載する。

## Rules
- All upstream artifacts (`inventory`, `cardSort`, `objects`, `labels`, `businessFlow`, `userStoryMap`) are **optional** — omit a key entirely if not designing that artifact; its tab then shows a guidance hint.
- `businessFlow.steps` order **is** the timeline (left→right columns); `userStoryMap.activities[].tasks[]` order **is** the horizontal backbone order.
- `screens[].id` is unique and stable — it is the join key for `transitions` and `sitemap`.
- `layoutBlocks` are **low-fidelity** content regions (top to bottom). No colors, no pixels.
- Omit empty arrays rather than inventing content.
- The HTML editor (`viewer/ia-editor.html`) reads/writes exactly this shape; do not add fields it can't round-trip without also updating the editor.

## Explicit sitemap (optional)
If you need a hand-authored hierarchy instead of the derived one:
```jsonc
"sitemap": {
  "name": "Product",
  "children": [
    { "name": "Section", "children": [ { "name": "画面名", "ref": "screen-id" } ] }
  ]
}
```
