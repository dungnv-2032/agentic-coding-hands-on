# um-spec.json — the interchange format

`um-spec.json` is the single source of truth that flows: **generate → build-doc.py → review in HTML.**
The viewer (`viewer/um-viewer.html`) renders exactly this shape. Keep it valid JSON.

```jsonc
{
  "meta": {
    "product": "string",                 // プロダクト / サービス名
    "segment": "string or [string]",     // 対象ユーザー層（誰のためか）。配列にすると ターゲット像スライドで箇条書き表示。文字列でも ＋/＆/、 等の強い区切りで複数像に自動分割（／・は分割しない）
    "businessGoal": "string or [string]", // ビジネス上の狙い。概要カードは配列→箇条書き、長い文字列は「。」で文単位に自動分割して箇条書き表示（読みやすさ優先）
    "researchBasis": "string or [string]", // 根拠（インタビュー n=8 / アンケート / 行動ログ / 仮説 など）。上と同様に箇条書きサマリー表示
    "stage": "discovery | concept | growth",  // どのフェーズの理解か
    "assumptions": ["明示した仮定", "..."]      // データ未検証の前提は必ずここに
  },

  // ---- 出典レジストリ（インプット・トレーサビリティ）----  OPTIONAL
  // インタビュー・アンケート・行動ログ等の「インプット」をここに登録し、各項目から `src` で参照する。
  // ビューアでは src 付き項目が破線下線になり、ホバーで label + excerpt がツールチップ表示される。
  "sources": [
    {
      "id": "iv1",                              // 参照キー（短く一意に: iv1, sv2, log1 …）
      "label": "インタビュー#1（田中氏・法人営業）",  // 出典の表示名（何のインプットか）
      "excerpt": "毎月末の請求書づくりで2時間は消える。コピペミスも怖い。"  // OPTIONAL 原文抜粋（短く。ツールチップに引用表示）
    }
  ],

  // ---- ペルソナ（ユーザー像）----  少数精鋭（primary 1–2 + secondary）。anti=対象外像。
  "personas": [
    {
      "name": "田中 翔 / 28・法人営業",        // 名前（属性込みでも可）
      "type": "primary | secondary | anti",  // 位置づけ。省略時 primary
      "image": "p1",                          // OPTIONAL 顔写真。同梱の汎用プール参照（"p1"〜"p12" / "pool:7" / "p7.jpg"）が手軽。任意のローカルパス・data URI・httpも可。未指定なら build-doc.py がプールから順番に自動割当（顔が既定で表示）。プール一覧は references/persona-pool.md
      "tagline": "短いキャッチ（一言で表す像）",
      "quote": "代表的な生の発言（一人称）",
      "bio": "人物像の説明文（背景・日常）",
      "demographics": { "年齢": "28", "職種": "法人営業", "居住地": "東京", "家族": "独身", "ITリテラシー": "中" },
      "goals": ["達成したいこと / ゴール"],          // 各リストは最も鋭い2件まで（1スライドに収める）
      "frustrations": ["不満・障壁・ペイン"],         // 同上: 最大2件
      "motivations": ["動機・原動力"],               // 同上: 最大2件
      "behaviors": ["行動特性・習慣"],               // 同上: 最大2件
      "needs": ["満たすべきニーズ"],                 // 同上: 最大2件
      "channels": ["利用チャネル / 主なタッチポイント"], // 同上: 最大2件
      "scenario": "代表的な利用シーン"
    }
  ],

  // ---- エンパシーマップ ----  OPTIONAL。persona は personas[].name と一致させるとアバター表示
  "empathyMaps": [
    {
      "persona": "田中 翔",
      "says":   ["言っていること（観察された発言）"],
      "thinks": ["考えていること（口に出さない本音）"],
      "does":   ["していること（観察された行動）"],
      "feels":  ["感じていること（感情）"],
      "pains":  ["痛み・障害・恐れ"],
      "gains":  ["得たいもの・成功の定義"]
    }
  ],

  // ---- カスタマージャーニー ----  OPTIONAL。stages の配列順 = 時間順（左→右）
  "journeys": [
    {
      "persona": "田中 翔",
      "scenario": "シナリオ名（例: 初めて契約するまで）",
      "stages": [
        {
          "name": "認知",                       // フェーズ名
          "goal": "このフェーズでのユーザー目標",
          "actions": ["行動"],
          "touchpoints": ["接点 / チャネル"],
          "thoughts": ["思考・期待・疑問"],
          "emotionScore": 1,                    // -2..2（感情曲線用）。2=最高 / 0=普通 / -2=最悪
          "emotion": "期待で前向き",             // OPTIONAL 感情の一言ラベル
          "painPoints": ["課題・障壁・離脱要因"],
          "opportunities": ["改善機会 / 打ち手"]
        }
      ]
    }
  ],

  // ---- ユーザーインサイト ----  OPTIONAL。観察→気づき→示唆 の構造
  "insights": [
    {
      "title": "インサイトの見出し",
      "persona": "田中 翔",                    // OPTIONAL 紐づくペルソナ
      "observation": "観察された事実（何が起きているか）",
      "insight": "本質的な気づき（なぜそうなるか）",
      "evidence": ["根拠データ・生の発言"],
      "implication": "プロダクトへの示唆",
      "hmw": "How Might We …?（解くべき問い）",
      "impact": "high | medium | low"
    }
  ],

  // ---- ユーザーストーリーマッピング ----  OPTIONAL。横軸＝行動の流れ(backbone) × 縦軸＝リリース帯
  "storyMap": {
    "releases": ["MVP", "Release 2", "Later"],  // 縦軸のリリース帯（行）。省略時は story.release から導出。先頭＝最優先(赤)
    "activities": [   // 横軸のバックボーン（ユーザーの行動の流れ。配列順＝左→右の時系列）
      {
        "name": "請求する",            // アクティビティ（大きな行動）
        "tasks": [                     // そのアクティビティ内のユーザータスク（各タスク＝1列）
          {
            "name": "請求書を作成・送付する",
            "stories": [
              {
                "title": "案件から請求書をワンタップで発行できる",  // ストーリー本文（〜できる）
                "soThat": "毎月のコピペとミスをなくす",            // 価値（任意。→ で表示）
                "persona": "佐藤 美咲",                          // 紐づくペルソナ（アバター表示）。as でも可
                "release": "MVP",                               // どのリリース帯に置くか（releases の値と一致）
                "priority": "Must | Should | Could"             // 左罫色: Must=赤 / Should=金 / Could=灰
              }
            ]
          }
        ]
      }
    ]
  }
}
```

## 出典アノテーション（`{text, src}` 形式）
表示されるテキスト項目は、プレーン文字列の代わりに **`{ "text": "...", "src": ... }`** オブジェクトでも書ける。
`src` は `sources[].id`（または id の配列）、あるいはインラインの自由記述（`"インタビュー#3: 「…」"`）。

```jsonc
// 例: ペルソナの frustration をインタビュー発言に紐づける
"frustrations": [
  { "text": "請求書作成が毎月2時間かかり、ミスが怖い", "src": "iv1" },   // sources の id 参照
  { "text": "入金確認を手作業で照合している", "src": ["iv1", "sv2"] },  // 複数出典
  "テンプレ管理が属人化している"                                        // 出典なしは従来どおり文字列
]
```

**対応フィールド**（ビューアがツールチップ表示するもの）:
- すべてのリスト項目 — persona の goals / frustrations / motivations / behaviors / needs / channels、empathyMaps の says / thinks / does / feels / pains / gains、journey stage の actions / touchpoints / thoughts / painPoints / opportunities、insights の evidence、meta.assumptions
- スカラー項目 — persona の tagline / bio / scenario、journey stage の goal / emotion、insight の title / observation / insight / implication / hmw、story の title / soThat

名前・ID 系（`personas[].name`、stage `name`、`release`、`priority` など構造を担う値）はプレーン文字列のまま。

## Rules
- Only `meta` and `personas` are expected to be present; `empathyMaps` / `journeys` / `insights` / `storyMap` are **optional** — omit a key entirely if not modeling it, and its tab shows a guidance hint.
- `storyMap.activities[].tasks[]` order **is** the horizontal backbone (left→right user flow); `storyMap.releases` order **is** the vertical slices (top = highest priority release).
- `personas[].type`: keep the set **small** — 1–2 `primary`, a few `secondary`, optional `anti` (who it is NOT for). Don't model everyone.
- `personas[]` の goals / frustrations / motivations / behaviors / needs / channels は**各最大2件**。全部を並べず、最も鋭い2件を選ぶ（ビューア／Figmaとも1スライドに収める前提。3件以上あっても表示は先頭2件で切られる）。
- `journeys[].stages[]` order **is** the timeline (left→right). `emotionScore` (-2..2) drives the感情曲線; include it on every stage you want plotted.
- `empathyMaps[].persona` / `journeys[].persona` / `insights[].persona` / story `persona` join to `personas[].name` (leading token match) to show the right avatar/photo. No match = a generated avatar from the string.
- Mark anything not grounded in real data as an **assumption** (`meta.assumptions`), not as fact.
- **Trace outputs to inputs when real research exists:** register each input in `sources[]` and annotate derived items with `{text, src}`. Keep `excerpt` short (1–2 sentences of the raw quote/data). Don't annotate invented/assumed content — that belongs in `meta.assumptions`.
- Omit empty arrays rather than inventing content.
- The viewer renders exactly this shape; do not add fields it can't render without also updating `viewer/um-viewer.html`.
