# Worked example — フリーランス向け請求・入金管理アプリ「Sokin」

A full user model produced by SW\*-UM from a concept + 8 interviews. The machine-readable
output is `samples/freelance-invoicing.um-spec.json`; build it to see the viewer:

```bash
python3 bin/build-doc.py examples/samples/freelance-invoicing.um-spec.json
```

This shows how raw research becomes the five connected artifacts.

The sample also demonstrates **input traceability**: interviews / logs are registered in
top-level `sources[]`, and derived items are annotated as `{ "text": ..., "src": "<id>" }` —
in the viewer these items get a dashed underline, and hovering shows the input source
(label + raw excerpt) in a tooltip.

## 1. 誰のために / 前提
- **プロダクト目的:** 個人事業主の請求・入金業務を最小化し、月額課金への定着を高める
- **対象ユーザー層:** 個人で活動するフリーランス（デザイナー・エンジニア・ライター）
- **対象外 (anti):** 専任経理を持つ法人 — 個人向け軽量アプリでは要件を満たさない
- **根拠:** ユーザーインタビュー n=8 / 行動ログ / サポート問い合わせ分析
- **前提・仮定（未検証）:** 年商1,000万円未満 / 確定申告は本人 / スマホ中心利用

## 2. ペルソナ
- **佐藤 美咲（primary）** — 制作に集中したい29歳デザイナー。経理が苦手で毎月の請求が憂鬱。
  代表的な声:「デザインは好きだけど、請求書づくりだけは毎月憂鬱になる。」
- **山田 健（secondary）** — 効率重視の42歳エンジニア。会計連携と自動化を求めるヘビーユーザー。
- **経理担当のいる法人（anti）** — 専任経理がいる組織は対象外。スコープを締めるための anti-persona。

## 3. エンパシーマップ（佐藤 美咲）
- **Says:** 「先月のをコピーして使ってる」「入金、たぶん来てると思う」
- **Thinks:** 催促したら関係が悪くなるかも / 本当は制作だけしたい / 確定申告が不安
- **Does:** PDFを複製して金額だけ修正 / 月末にまとめて入金確認 / 未入金は放置しがち
- **Feels:** 憂鬱 / 気まずい / 不安
- **Pains:** 突き合わせが手作業・催促の心理的ハードル / **Gains:** 制作に集中できる安心

> Says（「たぶん来てると思う」）と Thinks（「催促したくない」）のギャップが、後述のインサイトの源泉。

## 4. カスタマージャーニー（今月分を請求し入金されるまで）
請求準備 → 請求書発行 → 入金待ち → 未入金フォロー → 入金完了 の5フェーズ。
感情曲線は「入金待ち」で最低（-2）に落ち込み、「入金完了」でようやく回復(+1)。
各低点に改善機会を紐付け（例: 入金待ち → 口座連携で自動消込＋入金通知）。

## 5. ユーザーインサイト
1. **「催促」は機能でなく感情の問題**（impact: high）— 未入金放置の理由は「やり方が分からない」ではなく「関係を壊したくない」。
   HMW: 気まずさを感じさせずに未入金を回収するには？
2. **請求と入金が別タスクに分断**（high）— ユーザーの頭では一連の流れなのにツールが分かれている。
3. **事務は『最小化』が価値、ゼロは怖い**（medium）— 全自動より「自動準備＋本人承認」の半自動が安心される。

## 6. ユーザーストーリーマッピング
バックボーン（ユーザーの行動の流れ）: **請求する → 入金を管理する → 未入金に対応する → 記帳する**。
各アクティビティをタスクに分け、ストーリーを **MVP / Release 2 / Later** のリリース帯にスライス。

| バックボーン | MVP | Release 2 | Later |
|---|---|---|---|
| 請求する（請求書を作成・送付） | 案件からワンタップ発行 (Must/佐藤) | 源泉・消費税の自動計算 (Should/山田) | |
| 入金を管理する（消込） | 口座連携で自動消込・通知 (Must/佐藤) | | |
| 未入金に対応する（催促） | | 催促文の自動下書き＋本人承認 (Should/佐藤) ← インサイト1直結 | |
| 記帳する（会計連携） | | | 会計ソフトへ自動連携 (Could/山田) |

MVP帯はバックボーンを端から端まで薄く貫く「ウォーキングスケルトン」（発行→消込まで一連が回る最小機能）。

## なぜこの形か
- 感情曲線が「入金待ち」の谷を可視化 → そこに最重要 Must ストーリー（自動消込）が対応。
- anti-persona がスコープ（個人向け・軽量）を明示し、会計連携を Could に抑える判断を支える。
- インサイト1（催促＝感情）が、単なる「催促リマインダー」ではなく「下書き＋本人承認」という解の方向性を決めている。
