# Technique Selection Modes

Four ways to decide **which** techniques a session runs. The mode is itself a decision, so it is presented with
`AskUserQuestion` in Step 3 following the three-options rule — except that here there are four named modes, so
present all four with one marked `(Recommended)`.

Handing the choice of mode to the user is deliberate. Someone who has run brainstorming sessions before wants to
pick the technique; someone who has not wants to be told. Guessing which kind of user you have is worse than
asking.

---

## Choosing which mode to recommend

Recommend based on what you learned in Step 2, in this order:

| Situation | Recommend |
|-----------|-----------|
| The user has no strong preference, or this is their first session | **A. AI 推奨** |
| The user named a technique themselves, or asked what techniques exist | **B. ユーザー選択** |
| A previous session on the same topic already used 2+ techniques and stalled | **C. ランダム** |
| The session has 60+ minutes and needs to end with a concrete action list | **D. 段階フロー** |

State the reason for the recommendation in one sentence, grounded in something the user actually said. "AI 推奨
がおすすめです" with no reason is not a recommendation.

The `AskUserQuestion` call in Step 3 looks like this — recommended option first, each description naming its
trade-off:

```
question: どの方法で手法を選びますか？
header:   手法の選び方
options:
  - AI 推奨（おすすめ）      — Step 2 の目的から相性のよい手法を 2〜3 個提案します。迷う時間がゼロで済む一方、選択肢の全体像は見えません。
  - 自分で選ぶ              — 6 分類 28 手法から見て選びます。納得感が高い代わりに、選ぶのに数分かかります。
  - ランダム                — あえて意外な組み合わせを引きます。行き詰まりを破れますが、空振りの可能性もあります。
  - 段階フロー              — 発散→深掘り→収束→行動計画を一通り回します。行動計画まで出ますが 60 分以上かかります。
```

---

## A. AI 推奨 (AI-recommended)

*The facilitator proposes; the user approves or adjusts.*

**Recommend when:** the default. Especially for a first session, or when the user's answer in Step 2 was a
concrete business problem rather than a request for exploration.

### Selection logic

Map the session type from Step 2 to categories, then pick within them:

| Step 2 session type | Primary categories | Typical opening technique |
|---------------------|--------------------|---------------------------|
| 発散重視 (generate ideas) | `creative` + `structured` | Mind Mapping, then What If Scenarios |
| 課題解決 (solve a stated problem) | `deep` + `structured` | Five Whys, then As-Is / To-Be Walkthrough |
| リスク洗い出し (surface risks) | `adversarial` + `role-based` | Pre-mortem, then Failure Analysis |

Then adjust for four things before finalising:

1. **Time available.** Under 30 min → 1 technique. 30-60 min → 2. Over 60 min → 3, or use mode D instead.
2. **Energy.** Never chain two `高` techniques. If the plan has two, replace the second with a `中` or `低` one
   from the same category.
3. **How much the project already knows.** If `system-overview.md` and `function-list.md` are empty, avoid
   techniques that operate on an existing thing (SCAMPER, Six Thinking Hats, Edge Case Hunt) — there is nothing
   for them to bite on.
4. **What previous sessions used.** Check the files in `project/09_wip_plan/`. Do not propose a technique that
   the last session on the same topic already ran, unless the user asks to go deeper with it.

### How to present

Three phases, each with one technique:

```
🔍 Step 2 の「{目的}」に対して、次の 3 段階を提案します。

【第1段階】発散 — {手法名}（{目安時間}）
  なぜこの手法か: {system-overview.md / Step 2 の発言 / 前回セッション を引用した 1 文}
  期待する成果:   {何が出てくるか}

【第2段階】深掘り — {手法名}（{目安時間}）
  ...

【第3段階】収束 — {手法名}（{目安時間}）
  ...

合計の目安: {合計時間}
```

Then `AskUserQuestion`: `この計画で始める（おすすめ）` / `一部の手法を変えたい` / `別の選び方に戻る`.

### Rules

- **`なぜこの手法か` must cite something real** — a sentence in `system-overview.md`, a phrase the user used in
  Step 2, a feature in `function-list.md`, or a previous session file. "一般的に有効です" is not a reason, and
  a plan with no citations means you skipped Step 1's context load.
- **Read the entry in `techniques.md` before proposing it.** Durations and energy levels come from the index
  table, never from your own estimate.
- If the user says 一部を変えたい, ask which phase, then offer 3 alternatives from the same category with the
  same energy level.

---

## B. ユーザー選択 (User-selected)

*The user browses; the facilitator does not steer.*

**Recommend when:** the user named a technique, asked what is available, or has facilitated before.

### How to present — two levels

**Level 1 — category.** Since `AskUserQuestion` takes at most 4 options and there are 6 categories, render the
category list as a numbered list in the message body and let the user answer freely (a number, a category name,
or a technique name directly). **The counts must match the index table in `techniques.md`.**

```
🔍 28 手法を 6 分類でご用意しています。

1. structured  (5) 型に沿って漏れなく出す      — SCAMPER / Six Thinking Hats / Mind Mapping ほか
2. deep        (6) 一点を掘り下げる            — Five Whys / Question Storming / First Principles ほか
3. creative    (5) 発想を飛ばす                — What If / Analogical Thinking / Reversal ほか
4. role-based  (4) 立場から出す                — Persona Journey / Role Playing / Day in the Life ほか
5. adversarial (5) 壊れ方から出す              — Pre-mortem / Failure Analysis / Edge Case Hunt ほか
6. convergent  (3) 束ねて絞る（整理フェーズ用） — Affinity Mapping / Dot Voting / Now / Next / Later

番号でも手法名でも構いません。分類の説明が必要でしたらお知らせください。
```

**Level 2 — technique.** Show every technique in the chosen category as a table taken verbatim from the index,
plus one sample facilitation prompt per technique so the user can tell what it actually feels like:

```
🔍 deep — 一点を掘り下げる（6 手法）

| # | 手法 | 向いている場面 | 目安時間 | Energy |
|---|------|---------------|---------|--------|
| 1 | Five Whys | 表面的な要望の裏にある真因を知りたい | 15-20分 | 中 |
| ... |

例）Five Whys はこんな質問から始まります:
  「なぜ『Excel 出力』が必要なのでしょうか？」
```

Then let the user pick 1-3 techniques. Confirm the resulting plan and its total time before starting.

### Rules

- **Do not recommend, rank, or hint in this mode.** No `(おすすめ)` labels, no "個人的には X が合いそうです".
  The user chose this mode precisely to make the choice themselves. Answering a direct "どれがいいと思う？" is
  fine — that is the user handing the choice back.
- Describing what a technique does is not steering; describing what you would choose is.
- If the user picks a `convergent` technique for the divergence phase, say once that those are designed for
  Step 6 and ask whether they want it there instead. If they confirm, run it where they asked.
- If the user picks three `高` energy techniques, say so once and let them decide.

---

## C. ランダム (Random)

*Draw techniques deliberately unplanned, and use the surprise.*

**Recommend when:** the topic has been discussed before and every session reached the same conclusions, or the
user explicitly wants to break out of a pattern.

### Selection logic

1. Draw 2-3 techniques from **different categories** — same-category draws produce no contrast, which is the
   entire point of the mode.
2. Exclude `convergent` from the draw (those belong to Step 6).
3. Total duration must fit the session; redraw the longest one if it does not.
4. At most one `高` energy technique in the draw.

### How to present

```
🔍 🎲 引いた組み合わせはこちらです

  1. {手法名}（{分類} / {目安時間}）— {向いている場面}
  2. {手法名}（{分類} / {目安時間}）— {向いている場面}

この組み合わせの面白いところ:
  {この 2 つを続けて回すと何が起きそうかを 1〜2 文で}
```

Then `AskUserQuestion`: `この組み合わせで始める` / `引き直す` / `別の選び方に戻る`.

### Rules

- The 「面白いところ」 line must be about **this particular pairing**, not a restatement of what each technique
  does. If you cannot say why the combination is interesting, redraw.
- Cap redraws at three. After the third, say plainly that random is not landing and suggest mode A.
- Random applies to the *technique*, never to the topic or to the ideas. Do not improvise facilitation prompts
  in this mode to match the playful framing — use the ones in `techniques.md`.

---

## D. 段階フロー (Progressive flow)

*A fixed four-phase journey from wide open to a concrete action list.*

**Recommend when:** there is 60+ minutes available and the session must end with decisions the user can act on —
a kickoff workshop, a phase-planning session, a customer-facing meeting.

### The journey

| Phase | 目的 | 分類 | 既定の手法 | 目安 |
|-------|------|------|-----------|------|
| 1. 発散 | 幅を広げる | `creative` | Mind Mapping → What If Scenarios | 20-30分 |
| 2. 深掘り | 本質と背景を掴む | `deep` | Five Whys または As-Is / To-Be Walkthrough | 25-40分 |
| 3. 収束 | 束ねて絞る | `convergent` | Affinity Mapping → Dot Voting | 20-30分 |
| 4. 行動計画 | 次の一手を決める | `convergent` | Now / Next / Later | 10-20分 |

### How to present

```
🔍 4 段階のフローで進めます。

  【1】発散     {手法}          約{n}分   幅を広げる
        ↓ ここで出た案を材料に
  【2】深掘り   {手法}          約{n}分   なぜそれが必要かを掘る
        ↓ 掘った結果を並べて
  【3】収束     {手法}          約{n}分   意味でまとめ、優先度を付ける
        ↓ 上位の案について
  【4】行動計画 Now/Next/Later  約{n}分   今回やる／次回やる／寝かせる

  合計の目安: 約{合計}分
```

Then `AskUserQuestion`: `このフローで始める` / `各段階の手法を変えたい` / `短縮版にしたい` / `別の選び方に戻る`.

### Variants

- **短縮版 (~45分):** phases 1, 3, 4 only — drop 深掘り. Use when time is tight but an action list is still
  required.
- **拡張版 (~120分):** two techniques in phase 1 and two in phase 2.
- **カスタマイズ:** swap the technique in any phase for another from the same category. Never swap the
  *category* — the phase ordering 発散 → 深掘り → 収束 → 行動計画 is what makes this mode work.

### Rules

- **Announce every phase transition explicitly** ("ここまでが発散です。ここから深掘りに移ります") and state
  what changes about the rules. Phase 3 is where evaluation becomes allowed; the user needs to be told, or they
  will keep self-censoring in phases 1-2.
- Do not let phase 1 run short because the ideas seem sufficient. This mode's value is that the convergence has
  enough raw material; a thin phase 1 makes phases 3-4 hollow.
- If phase 1 and 2 overrun badly, drop a technique from phase 3 rather than cutting phase 4. Ending without an
  action list defeats the mode.

---

## After the mode is chosen

Whichever mode ran, Step 4 always ends the same way: a confirmed technique plan, with each technique's name,
duration and the reason it is there, agreed by the user before facilitation starts. Record that plan in the
session document's `## 2. 使用した手法` section as you go, including the mode used — a later session reading the
file needs to know both what was run and how it was chosen.
