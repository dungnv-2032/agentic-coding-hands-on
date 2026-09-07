# Brainstorming Techniques

The technique library. 28 techniques across 6 categories, selected for **requirement discovery** — generating
feature ideas, digging into a business problem, and surfacing risks and edge cases before they become defects.

**How to use this file.** The index table below is enough to render a menu or to shortlist candidates. Read only
the entries you are actually going to run — each entry has its own facilitation prompts and output shape. Never
present a technique whose entry you have not read; the prompts are the technique.

**Adapt before you present.** Every prompt below is a starting point written in generic terms. Replace the
placeholders with the project's actual domain, roles and terminology (from `glossary.md` and `role-list.md`)
before you say it out loud. A prompt the user cannot picture in their own system generates nothing.

**Energy** means how much creative effort the technique demands of the user: `低` (answers come easily),
`中` (needs thought), `高` (needs the user to leave their comfort zone). Do not chain two `高` techniques
back to back.

---

## Index

| 分類 | 手法 | 向いている場面 | 目安時間 | Energy |
|------|------|---------------|---------|--------|
| structured | SCAMPER | 既存の業務・機能を体系的に改善したい | 20-30分 | 中 |
| structured | Six Thinking Hats | 一つの案を多角的に検証したい | 25-35分 | 中 |
| structured | Mind Mapping | テーマの全体像と抜け漏れを把握したい | 15-25分 | 低 |
| structured | Morphological Analysis | 組み合わせで網羅的に案を出したい | 25-40分 | 高 |
| structured | Constraint Mapping | 制約条件を洗い出して現実解に絞りたい | 20-30分 | 中 |
| deep | Five Whys | 表面的な要望の裏にある真因を知りたい | 15-20分 | 中 |
| deep | Question Storming | 答えではなく問いを大量に出したい | 20-30分 | 低 |
| deep | Assumption Reversal | 暗黙の前提を壊して発想を広げたい | 20-30分 | 高 |
| deep | First Principles | 前例を捨てて本質から組み立て直したい | 25-35分 | 高 |
| deep | Jobs To Be Done | 利用者が「何のために雇う」のかを掴みたい | 20-30分 | 中 |
| deep | As-Is / To-Be Walkthrough | 現行業務と理想業務の差分を機能にしたい | 30-45分 | 中 |
| creative | What If Scenarios | 制約を外して可能性の幅を広げたい | 15-25分 | 中 |
| creative | Analogical Thinking | 他業界の解決策を持ち込みたい | 20-30分 | 中 |
| creative | Reversal / Inversion | 「どうすれば最悪になるか」から考えたい | 15-20分 | 低 |
| creative | Forced Relationships | 無関係な概念を結びつけて飛躍したい | 15-25分 | 高 |
| creative | Time Shifting | 時代・時間軸を変えて見方を変えたい | 15-20分 | 中 |
| role-based | Persona Journey | 特定利用者の一連の体験から機能を導きたい | 25-40分 | 中 |
| role-based | Role Playing | 立場になりきって要望を言語化したい | 20-30分 | 中 |
| role-based | Day in the Life | 業務の実際の一日から接点を拾いたい | 25-35分 | 低 |
| role-based | Stakeholder Round Table | 利害が対立する要望を同時に並べたい | 25-35分 | 中 |
| adversarial | Pre-mortem | リリース後の失敗を先回りで防ぎたい | 20-30分 | 中 |
| adversarial | Failure Analysis | 各処理の失敗パターンを網羅したい | 25-35分 | 中 |
| adversarial | Anti-Solution | 逆転発想で盲点を見つけたい | 15-25分 | 低 |
| adversarial | Edge Case Hunt | 境界値・例外条件を洗い出したい | 25-35分 | 高 |
| adversarial | Abuse & Misuse Storming | 悪用・誤用のシナリオを想定したい | 20-30分 | 中 |
| convergent | Affinity Mapping | 大量のアイデアを意味で束ねたい | 15-25分 | 低 |
| convergent | Dot Voting | 束ねた案に優先順位を付けたい | 10-15分 | 低 |
| convergent | Now / Next / Later | 実行時期で仕分けたい | 10-20分 | 低 |

---

## structured — 型に沿って漏れなく出す

Use when the topic is already concrete (an existing process, an existing feature) and the risk is **omission**
rather than lack of ideas.

### SCAMPER

*Seven fixed lenses applied to an existing thing, one at a time.*

- **Best for:** improving a process or feature that already exists. Weak on greenfield topics — there has to be
  something to transform.
- **How to run:**
  1. Name the target precisely (one process, one screen, one rule — not "the whole system").
  2. Walk the seven lenses in order, one per turn: 置換 (Substitute) / 結合 (Combine) / 応用 (Adapt) /
     修正 (Modify) / 転用 (Put to other use) / 削除 (Eliminate) / 逆転 (Reverse).
  3. Do not skip a lens because it "doesn't apply" — ask the question anyway; the empty-looking lenses are
     where the surprises live. 削除 in particular is the most under-used and most valuable.
- **Facilitation prompts:**
  - 「この作業の一部を、別のやり方に**置き換える**としたら何をどう変えますか？」
  - 「今は分かれている二つの作業を**結合**したら、誰が楽になりますか？」
  - 「この手順を一つ**削除**しても業務が回るとしたら、どれを消しますか？」
- **Output shape:** ideas tagged with the lens that produced them (`[置換]`, `[削除]` …).
- **Duration / Energy:** 20-30分 / 中

### Six Thinking Hats

*One idea examined six times, each time from a single deliberately restricted point of view.*

- **Best for:** stress-testing a candidate solution the user is already leaning toward, without it turning into
  an argument. Also good when several stakeholders disagree — it separates "this is a fact" from "I don't like
  it".
- **How to run:**
  1. Pick the single idea or plan to examine.
  2. Go through the hats, one per turn, and hold the user to the current hat: 白 (facts and data only) /
     赤 (gut feeling, no justification allowed) / 黒 (risks, why it fails) / 黄 (benefits, why it works) /
     緑 (alternatives and variations) / 青 (process: what did we learn, what next).
  3. 青 goes last and produces the conclusion.
- **Facilitation prompts:**
  - 「**白帽**です。この件について、意見ではなく**事実として分かっていること**は何ですか？」
  - 「**黒帽**です。これが半年後に失敗しているとしたら、原因は何だと思いますか？」
  - 「**緑帽**です。同じ目的を、まったく別のやり方で達成するとしたら？」
- **Output shape:** six labelled blocks, plus the 青帽 conclusion.
- **Duration / Energy:** 25-35分 / 中

### Mind Mapping

*Radiate outward from the theme to see its shape and its holes.*

- **Best for:** the opening move of a session when the topic is broad and nobody knows where the boundaries are.
  Cheap, low-effort, and it makes the gaps visible.
- **How to run:**
  1. Put the theme at the centre and get 4-6 first-level branches from the user (not from you).
  2. Expand one branch at a time to depth 2-3.
  3. Then explicitly ask about **the thin branches** — a branch with one child is usually an unexplored area,
     not a small one.
- **Facilitation prompts:**
  - 「このテーマを大きく分けると、どんな塊になりますか？ 4〜6 個挙げてください」
  - 「『{枝}』の中身をもう一段細かくすると？」
  - 「今『{薄い枝}』だけ枝が少ないですが、本当に小さい領域ですか、それともまだ見えていないだけですか？」
- **Output shape:** an indented tree rendered as a nested list.
- **Duration / Energy:** 15-25分 / 低

### Morphological Analysis

*Break the problem into independent axes, list the options on each, then combine.*

- **Best for:** exhaustively covering a design space with a real combinatorial structure — notification
  (トリガー × 宛先 × 手段 × タイミング), permissions (ロール × 操作 × 対象範囲).
- **How to run:**
  1. Decide 3-4 **independent** axes with the user. If two axes are correlated, merge them — that is what makes
     this technique collapse.
  2. List 3-5 concrete options on each axis.
  3. Present a handful of combinations, deliberately including implausible-looking ones — those are the point.
  4. Keep the combinations that turn out to describe a real business need.
- **Facilitation prompts:**
  - 「この問題を構成する『独立して選べる要素』を 3〜4 個に分けるとしたら？」
  - 「『{軸}』には、どんな選択肢がありますか？」
  - 「『{A} × {B} × {C}』という組み合わせは、業務として成立しますか？ 成立するなら誰のためですか？」
- **Output shape:** an axis table, then a shortlist of viable combinations.
- **Duration / Energy:** 25-40分 / 高

### Constraint Mapping

*Surface every constraint first, then find what is still possible inside them.*

- **Best for:** a session where ideas keep dying in "that's not possible anyway". Naming the constraints up
  front converts the objection into a shared boundary — and often reveals that half the "constraints" are
  assumptions (hand those to Assumption Reversal).
- **How to run:**
  1. Collect constraints in four buckets: 予算・期間 / 技術・既存システム / 法令・社内規程 / 体制・運用.
  2. For each, ask whether it is **hard** (externally imposed) or **soft** (a decision someone could revisit).
  3. Generate ideas that live entirely inside the hard constraints.
  4. Separately, list what would become possible if one named soft constraint were lifted — that list is
     negotiation material, not waste.
- **Facilitation prompts:**
  - 「絶対に動かせない制約はどれですか？ それは誰が決めたものですか？」
  - 「この制約の中でできることに絞ると、どんな案が残りますか？」
  - 「もし『{ソフト制約}』が外れたら、何が可能になりますか？」
- **Output shape:** a hard/soft constraint table plus two idea lists (inside constraints / unlocked if lifted).
- **Duration / Energy:** 20-30分 / 中

---

## deep — 一点を掘り下げる

Use when there is already a stated need or complaint and the risk is **solving the wrong problem**.

### Five Whys

*Ask why five times to get from the requested solution to the actual problem.*

- **Best for:** a customer request phrased as a solution ("Excel 出力が欲しい"). The fifth answer is usually a
  different — and better — feature.
- **How to run:**
  1. Start from the stated request, not from a problem statement.
  2. Ask why, once per turn, and feed the user's own words back into the next question.
  3. Stop when the answer becomes a business objective rather than a mechanism, or when it starts repeating.
  4. Restate: "so the real need is X, and Excel output was one way to get it". Then ask what else would.
- **Facilitation prompts:**
  - 「なぜ『{要望}』が必要なのでしょうか？」
  - 「その『{回答}』ができないと、今は誰がどう困っていますか？」
  - 「つまり本当に解決したいのは『{真因}』ということでしょうか？ 他の手段もありそうですか？」
- **Output shape:** a why-chain (5 levels) ending in a root need, plus alternative solutions to that need.
- **Duration / Energy:** 15-20分 / 中

### Question Storming

*Generate questions instead of answers.*

- **Best for:** the very start of a project, when the team knows too little to have opinions. Lowers the barrier
  dramatically — people who cannot propose a solution can always ask a question. Feeds `qa.md` directly.
- **How to run:**
  1. Set a target (e.g. 30 questions) and forbid answering any of them during the round.
  2. Collect questions only. If the user answers one, write the answer down and ask for the next question.
  3. Afterwards, sort into 自分たちで答えられる / お客様に聞くしかない / 調査が必要.
- **Facilitation prompts:**
  - 「このテーマについて、**答えではなく疑問**を挙げてください。答えは後で考えます」
  - 「まだ誰も聞いていない、聞きにくい質問は何ですか？」
  - 「この 30 個のうち、お客様に確認しないと決められないものはどれですか？」
- **Output shape:** a numbered question list, then a 3-way sort. The 「お客様に聞くしかない」 bucket becomes
  `qa.md` rows in Step 8.
- **Duration / Energy:** 20-30分 / 低

### Assumption Reversal

*List what everyone takes for granted, then negate each one.*

- **Best for:** a domain where "it has always been done this way" is blocking ideas. Pairs naturally after
  Constraint Mapping (reverse the soft constraints).
- **How to run:**
  1. Get 5-8 statements the user considers obviously true about the domain.
  2. Negate each one literally and ask what world that would be.
  3. For each negation, ask whether any part of it could actually be adopted.
- **Facilitation prompts:**
  - 「この業務について『当たり前すぎて誰も疑わないこと』を挙げてください」
  - 「もし『{前提}』が成り立たないとしたら、業務はどう変わりますか？」
  - 「その世界の要素で、**実際に取り入れられそうな部分**はありますか？」
- **Output shape:** a table of 前提 / 反転した世界 / 使えそうな要素.
- **Duration / Energy:** 20-30分 / 高

### First Principles

*Strip the problem to elements that cannot be reduced further, then rebuild.*

- **Best for:** replacing a legacy system, where the existing implementation is being mistaken for the
  requirement. Expensive but it is the technique that finds the 30% of features nobody actually needs.
- **How to run:**
  1. List what is being carried over from the current way of working.
  2. For each item, ask whether it is a **business necessity** or an **artefact of how it was built**.
  3. Keep only the necessities, then rebuild the flow from those alone.
  4. Compare the rebuild with the current process and name the differences explicitly.
- **Facilitation prompts:**
  - 「この業務が成立するために、**絶対に欠かせない要素**だけを挙げるとしたら？」
  - 「『{手順}』は業務上必要ですか、それとも今のシステムの都合ですか？」
  - 「その必須要素だけで組み直すと、どんな流れになりますか？」
- **Output shape:** 必須要素リスト → 再構成した業務フロー → 現行との差分.
- **Duration / Energy:** 25-35分 / 高

### Jobs To Be Done

*Ask what job the user "hires" the system to do.*

- **Best for:** deciding priority between features that all look reasonable. A feature that serves no job is
  the first thing to cut.
- **How to run:**
  1. Frame each need as 「{状況}のとき、{動機}したいので、{期待する結果}を得たい」.
  2. Ask what the user does **today** to get that result, and what is unsatisfying about it.
  3. Ask what "hiring" the new system instead would have to beat.
- **Facilitation prompts:**
  - 「利用者はどんな状況のときに、この機能を使おうと思いますか？」
  - 「今その目的を、システムなしでどうやって達成していますか？」
  - 「その今のやり方の、いちばん不満な点は何ですか？」
- **Output shape:** JTBD statements plus, for each, the current workaround and its pain point.
- **Duration / Energy:** 20-30分 / 中

### As-Is / To-Be Walkthrough

*Walk the current process step by step, then walk the ideal one, and turn the gap into features.*

- **Best for:** the highest-yield technique for offshore requirement work — it produces feature candidates that
  map almost one-to-one onto `function-list.md` rows.
- **How to run:**
  1. Walk the As-Is process one step at a time. For each step capture: 誰が / 何を使って / どれくらい時間が
     かかるか / どこが辛いか.
  2. Do not propose anything during the As-Is pass. Finish it first.
  3. Walk the To-Be process at the same granularity.
  4. Diff them step by step. **Each difference is a feature candidate** — name it as one.
- **Facilitation prompts:**
  - 「今、この業務は誰が何から始めますか？ その次は？」
  - 「その手順で、いちばん時間がかかる／間違いが起きるのはどこですか？」
  - 「理想的には、この手順はどうなっていてほしいですか？ その差を埋めるのが機能になります」
- **Output shape:** two numbered flows side by side, plus a 差分 → 機能候補 table.
- **Duration / Energy:** 30-45分 / 中

---

## creative — 発想を飛ばす

Use when ideas have stopped coming, or when everything proposed so far is an incremental variation of the same
thing. These are the domain-pivot tools.

### What If Scenarios

*Remove one constraint entirely and see what appears.*

- **Best for:** breaking a stall. Fast, needs no setup, works on any topic.
- **How to run:**
  1. Pose one extreme hypothetical per turn — do not stack them.
  2. Collect ideas from the impossible world.
  3. Then bring each one back: what is the 10%-cost version of that idea that is actually buildable?
- **Facilitation prompts:**
  - 「もし予算と期間が無制限だったら、この業務をどうしますか？」
  - 「もしこの作業を担当者が一切操作しなくてよいとしたら、何が起きていますか？」
  - 「その案の、今の予算でできる縮小版はどんな形ですか？」
- **Output shape:** ideal-world ideas, each paired with a feasible reduction.
- **Duration / Energy:** 15-25分 / 中

### Analogical Thinking

*Borrow a solved solution from a different industry.*

- **Best for:** UX and operational-flow problems, where another industry has spent years solving the same shape
  of problem (承認フロー, 予約, 在庫, 通知疲れ).
- **How to run:**
  1. Describe the problem in **abstract terms**, stripped of the domain ("many people must approve in order,
     and it stalls when one is absent").
  2. Find 2-3 industries that solve that abstract problem.
  3. Describe how they solve it, then translate the mechanism back — not the surface.
- **Facilitation prompts:**
  - 「この問題を業界の言葉を使わずに言い換えると、どんな問題ですか？」
  - 「同じ形の問題を、{別業界}はどう解いていますか？」
  - 「その仕組みのどの部分が、この業務にそのまま持ち込めそうですか？」
- **Output shape:** 抽象化した問題 → 参照した業界と仕組み → 移植した案.
- **Duration / Energy:** 20-30分 / 中

### Reversal / Inversion

*Ask how to make it as bad as possible, then invert the answers.*

- **Best for:** getting a quiet or unconfident user talking. People find it far easier to describe failure than
  success, and every failure inverts into a requirement.
- **How to run:**
  1. Ask how to make the process maximally painful, slow, or error-prone.
  2. Let it get playful — the exaggeration is what makes it productive.
  3. Invert each item into a positive requirement.
  4. Check honestly which "worst" items already describe the current system. Those are the priorities.
- **Facilitation prompts:**
  - 「この業務を**最悪に使いにくくする**には、どんな仕様にすればいいですか？」
  - 「担当者が絶対にミスするようにするには？」
  - 「今挙がった『最悪』のうち、**すでに現状そうなっているもの**はどれですか？」
- **Output shape:** a 最悪版 → 反転した要件 table, with current-state items flagged.
- **Duration / Energy:** 15-20分 / 低

### Forced Relationships

*Connect the topic to a deliberately unrelated concept.*

- **Best for:** the highest-variance technique here. Use it as a deliberate domain pivot when the last 10 ideas
  have all been in one semantic cluster.
- **How to run:**
  1. Pick a concrete unrelated object or system (コンビニ / 図書館 / 空港の保安検査 / 料理のレシピ).
  2. Ask what it has in common with the topic — force at least three connections before judging any.
  3. Convert the connections that survive into ideas.
- **Facilitation prompts:**
  - 「この業務と『{無関係なもの}』の共通点を、無理やり 3 つ挙げてください」
  - 「『{無関係なもの}』の仕組みをこの業務に持ち込むと、どうなりますか？」
- **Output shape:** ideas annotated with the connection that produced them.
- **Duration / Energy:** 15-25分 / 高

### Time Shifting

*Move the topic along the time axis.*

- **Best for:** finding requirements that only appear at a different scale or era — and for separating "needed
  at launch" from "needed eventually".
- **How to run:**
  1. Ask how this was done 30 years ago, on paper. Manual processes expose the business rules that software
     hides.
  2. Ask how it would work 10 years from now.
  3. Ask what happens when volume is 100× today's.
- **Facilitation prompts:**
  - 「30 年前、紙と電話だけでこの業務をどう回していましたか？ その頃のルールは今も生きていますか？」
  - 「10 年後、この業務はまだ人がやっていますか？」
  - 「取引量が今の 100 倍になったら、最初に壊れるのはどの手順ですか？」
- **Output shape:** ideas tagged 過去 / 未来 / 規模, with the 規模 items feeding non-functional requirements.
- **Duration / Energy:** 15-20分 / 中

---

## role-based — 立場から出す

Use when the system has several distinct user roles, or when the requirements so far only reflect one person's
point of view. Every actor named here should resolve to a `ROLE-xxx` in `role-list.md`; if it does not, that is
itself a finding.

### Persona Journey

*Follow one user from trigger to outcome and collect what they need at each step.*

- **Best for:** producing a coherent, ordered feature set rather than a scattered list. Pairs well with
  `04_screen-design/` later.
- **How to run:**
  1. Fix one persona: role, goal, how skilled they are, how often they do this.
  2. Walk the journey: 認知 → 開始 → 実行 → 確認 → 完了 → 事後.
  3. At each stage ask what they need to know, what they need to do, and what could go wrong.
- **Facilitation prompts:**
  - 「{ペルソナ}がこの業務を始めるきっかけは何ですか？」
  - 「その段階で、{ペルソナ}は何が分かっていないと先に進めませんか？」
  - 「この段階で失敗するとしたら、どんな失敗ですか？」
- **Output shape:** a stage × (必要な情報 / 必要な操作 / 失敗しうる点) table.
- **Duration / Energy:** 25-40分 / 中

### Role Playing

*Speak as the role, in the first person.*

- **Best for:** getting past sanitised, official-sounding requirements to the real complaints. The first person
  matters — it changes what people are willing to say.
- **How to run:**
  1. Pick a role from `role-list.md` and have the user answer **as** that person, in the first person.
  2. Ask about frustrations before asking about wishes.
  3. Switch roles and ask the same questions — the contradictions between roles are the valuable output.
- **Facilitation prompts:**
  - 「あなたは今『{ロール}』です。この業務で毎日いちばんイライラすることは何ですか？」
  - 「『{ロール}』として、システムに一つだけお願いできるとしたら何にしますか？」
  - 「では『{別ロール}』の立場だと、今の要望はどう見えますか？」
- **Output shape:** per-role wish lists, plus an explicit list of conflicts between roles.
- **Duration / Energy:** 20-30分 / 中

### Day in the Life

*Narrate an actual working day, hour by hour.*

- **Best for:** discovering the touchpoints nobody lists in a requirements meeting — the morning check, the
  end-of-month scramble, the Excel file passed by email. Low effort for the user because it is pure recall.
- **How to run:**
  1. Walk from arrival to leaving, in time order.
  2. At each point, ask which system or tool is touched, and where the waiting happens.
  3. Then ask about the days that are **not** typical: 月末, 繁忙期, 担当者不在の日.
- **Facilitation prompts:**
  - 「朝出社してから、この業務に最初に触れるのは何時ごろ、何をするときですか？」
  - 「その作業の途中で、誰かの返事を待つ時間はありますか？」
  - 「月末や繁忙期は、この一日はどう変わりますか？」
- **Output shape:** a timeline with touchpoints, waits, and exception days.
- **Duration / Energy:** 25-35分 / 低

### Stakeholder Round Table

*Put every stakeholder's demand on the table at once and let them conflict.*

- **Best for:** projects where requirements arrive from several departments and the conflicts have not yet been
  named. Surfacing a conflict early is worth more than any single idea.
- **How to run:**
  1. List the stakeholders, including the ones with no voice in the project (現場のパート社員, 情報システム部,
     監査, エンドユーザーの顧客).
  2. State each one's top demand in one sentence.
  3. Find the pairs that contradict, and name the trade-off explicitly.
  4. Do **not** resolve the conflicts here — record them. Resolution is a decision for the customer.
- **Facilitation prompts:**
  - 「この機能に意見を持つ人を、決裁者以外も含めて挙げてください」
  - 「『{立場}』がいちばん求めることは何ですか？ 一文でお願いします」
  - 「『{A}』の要望と『{B}』の要望は両立しますか？」
- **Output shape:** a stakeholder × 要望 table, plus a numbered conflict list. Conflicts go to `qa.md`.
- **Duration / Energy:** 25-35分 / 中

---

## adversarial — 壊れ方から出す

Use when the happy path is already clear. These produce business rules, error handling and acceptance
conditions — the sections that are always thin in requirement documents.

### Pre-mortem

*Assume the project has already failed, then explain why.*

- **Best for:** the risk-discovery session opener. Assuming failure as a fact removes the social cost of
  raising it, so people say things they would not say in a risk review.
- **How to run:**
  1. State it as fact: "it is six months after release and the system is not being used".
  2. Ask for causes — do not let the user hedge into "it might possibly".
  3. Group the causes: 要件 / 設計 / 運用 / 体制.
  4. For each, ask what could be decided **now** to prevent it.
- **Facilitation prompts:**
  - 「半年後、このシステムは現場でまったく使われていません。何が起きましたか？」
  - 「その原因は、いつの時点の判断が招いたものですか？」
  - 「今の段階でそれを防ぐには、何を決めておく必要がありますか？」
- **Output shape:** 失敗シナリオ → 原因 → 今打てる手. The 今打てる手 column becomes requirements or risks.
- **Duration / Energy:** 20-30分 / 中

### Failure Analysis

*Take each step of the flow and ask how it fails.*

- **Best for:** turning a happy path into complete business rules. This is the technique that fills §5 業務ルール
  and §3's 例外フロー in a function detail document.
- **How to run:**
  1. Take the flow step by step (reuse the As-Is/To-Be output if you have it).
  2. For each step ask three things: 入力が不正なら / 途中で中断したら / 外部連携が失敗したら.
  3. For each failure, decide who notices, and what they can do about it.
- **Facilitation prompts:**
  - 「『{手順}』で、入力が想定外だったら何が起きるべきですか？」
  - 「この処理の途中でブラウザを閉じたら、データはどうなっているべきですか？」
  - 「その失敗に**誰が気づきますか**？ 気づいた人は何ができますか？」
- **Output shape:** a 手順 × 失敗パターン × あるべき挙動 × 気づく人 table.
- **Duration / Energy:** 25-35分 / 中

### Anti-Solution

*Design the system that guarantees the opposite of the goal, then invert.*

- **Best for:** a lighter, faster cousin of Pre-mortem. Good when energy is dropping — it is playful and needs
  no setup.
- **How to run:**
  1. Ask for the design that would reliably prevent the project's goal from being achieved.
  2. Invert each item.
  3. Flag any anti-solution item that resembles a decision already made.
- **Facilitation prompts:**
  - 「このプロジェクトの目的を**確実に達成させない**システムを設計するとしたら？」
  - 「利用者に二度と使いたくないと思わせるには、どんな仕様にしますか？」
  - 「今出た中で、うっかりそうなりかけている決定はありませんか？」
- **Output shape:** an inverted requirement list, with self-check flags.
- **Duration / Energy:** 15-25分 / 低

### Edge Case Hunt

*Systematically probe the boundaries of every rule.*

- **Best for:** the most detail-productive technique here, and the most tiring. Run it on **one** feature at a
  time, never on a whole system.
- **How to run:**
  1. Take one rule or one input at a time.
  2. Probe five axes in order: 数量 (0件 / 1件 / 上限 / 上限超え) / 時間 (同時 / 深夜 / 年度またぎ / 締切直後) /
     権限 (権限なし / 権限が途中で変わる / 退職者) / 状態 (処理中 / キャンセル済 / 削除済) /
     文字 (空白 / 絵文字 / 全角半角 / 極端に長い).
  3. For each, decide the expected behaviour — "エラーにする" is not enough; name the message and who sees it.
- **Facilitation prompts:**
  - 「この一覧に **0 件**のとき、画面には何が表示されますか？」
  - 「申請中に承認者が異動になったら、その申請はどうなりますか？」
  - 「締切の 1 秒前に登録された場合は、有効ですか？」
- **Output shape:** an 観点 × 境界条件 × 期待挙動 table. Unanswered rows go straight to `qa.md`.
- **Duration / Energy:** 25-35分 / 高

### Abuse & Misuse Storming

*Ask how the system gets used wrongly — deliberately or accidentally.*

- **Best for:** security, audit and data-integrity requirements. Note the distinction: **misuse** (well-meaning
  people doing the wrong thing) usually produces more requirements than **abuse** (deliberate attack), and is
  the part teams forget.
- **How to run:**
  1. Misuse first: how does a busy, undertrained user get the wrong result while trying to do the right thing?
  2. Then abuse: how does someone extract, alter or destroy something they should not?
  3. For each, decide: 防ぐ / 検知する / 記録だけ残す. All three are valid answers — say which.
- **Facilitation prompts:**
  - 「悪意はないが忙しい担当者が、この機能をいちばん間違えやすいのはどこですか？」
  - 「退職予定の社員が、この機能で何を持ち出せますか？」
  - 「それは**防ぐ**べきですか、**検知**できれば十分ですか、**記録**だけ残せばよいですか？」
- **Output shape:** a シナリオ × 誤用/悪用 × 対応方針(防止/検知/記録) table.
- **Duration / Energy:** 20-30分 / 中

---

## convergent — 束ねて絞る

Use only in Step 6, after divergence is finished. Running these too early kills the session — see the
"no premature convergence" rule in `SKILL.md`.

### Affinity Mapping

*Group ideas by meaning, then name the groups.*

- **Best for:** always the first convergent move. The group **names** matter more than the grouping — a name
  the user struggles to write usually means the group is two groups.
- **How to run:**
  1. Present all ideas and propose a grouping, but let the user move things — it is their mental model, not
     yours.
  2. Name each group in the user's own words, in a noun phrase.
  3. Note the ideas that fit nowhere. Orphans are often the most original ideas, not the worst ones — do not
     let them be discarded silently.
- **Facilitation prompts:**
  - 「この {n} 個を仮に {m} 個のグループに分けました。動かしたいものはありますか？」
  - 「このグループに名前を付けるとしたら？」
  - 「どこにも入らなかったこの 3 つは、捨ててよいものですか？」
- **Output shape:** named groups with member idea numbers, plus an orphan list.
- **Duration / Energy:** 15-25分 / 低

### Dot Voting

*Spend a limited budget of votes.*

- **Best for:** ranking after grouping, when there are more good ideas than capacity. The scarcity is the whole
  mechanism — do not let the budget expand.
- **How to run:**
  1. Give a fixed budget (e.g. 5 votes across all groups; stacking on one item is allowed).
  2. Ask for the allocation, then ask **why** for the top item only.
  3. Explicitly ask what got zero votes and whether any of it is nonetheless mandatory (法令, 既存業務の代替).
     Mandatory-but-unpopular items must not fall off the list.
- **Facilitation prompts:**
  - 「5 票を自由に配ってください。1 つに集中させても構いません」
  - 「いちばん票を入れたものについて、その理由を一言で教えてください」
  - 「0 票のもので、それでも**やらなければならない**ものはありますか？」
- **Output shape:** a ranked list with vote counts, plus a flagged 必須だが低票 list.
- **Duration / Energy:** 10-15分 / 低

### Now / Next / Later

*Sort by when, not by whether.*

- **Best for:** finishing a session without anyone's idea being rejected. "Later" is much easier to accept than
  "no", and it keeps the idea retrievable.
- **How to run:**
  1. Three buckets: **Now** (この案件のスコープ) / **Next** (次フェーズ・次期案件) / **Later** (アイデア置き場).
  2. Force a decision — nothing sits between buckets.
  3. For each **Now** item, ask what makes it Now rather than Next. That reason is what protects the scope
     later.
- **Facilitation prompts:**
  - 「この案は今回の案件に入れますか、次フェーズですか、アイデアとして置いておきますか？」
  - 「それを『今回』にする理由は何ですか？ 次フェーズでは困りますか？」
  - 「Now が多すぎませんか。この中で本当に外せないのはどれですか？」
- **Output shape:** three buckets, with a one-line justification on every Now item. Now items become the
  候補機能 basket in Step 8.
- **Duration / Energy:** 10-20分 / 低

---

## Adding to this file

When you find a technique that repeatedly earns its place in requirement sessions, add it in the same shape:
a category, an italic one-line description, **Best for** (including when *not* to use it), **How to run** as
3-4 concrete steps, 2-3 **Facilitation prompts** written in Japanese as you would actually say them,
an **Output shape**, and a **Duration / Energy** figure.

Two rules for additions:

1. **Add the row to the index table at the same time.** Any column shown in a menu must have a real value here —
   never leave the facilitator to invent a duration.
2. **Keep it usable in a customer-facing offshore context.** A technique that would be awkward to run in front
   of a Japanese client does not belong here, however creative it is.
