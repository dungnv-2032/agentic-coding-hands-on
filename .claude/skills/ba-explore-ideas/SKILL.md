---
name: tkm:ba-explore-ideas
category: business-analysis
roles: [analyst]
description: |
  Facilitate an idea-generation session on a chosen theme.
  Pick a technique out of a 28-technique library through one of four selection modes
  (AI recommendation / user choice / random / staged flow), then diverge ideas interactively.
  Anything that cannot be decided on the spot is deferred and recorded — options intact —
  in section 8 (Open items) of the session file; nothing is filed into qa.md, so confirmation
  items stay self-contained inside the session record.
  Organize and prioritize the result into project/09_wip_plan/brainstorming-{YYYY-MM-DD}-{N}.md,
  then propose how the ideas split into feature candidates and risks.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - AskUserQuestion
---

# ba-explore-ideas Skill

Facilitate an idea-generation session on one theme: pick the techniques together, draw the ideas out of the
user, then organize them into something the project can act on.

## Purpose

- Generate ideas **before** there is a function list — this skill runs on a blank project, which is what makes
  it different from `FA` / `ba-analyze-requirement`
- Make the user the source of the ideas, and the facilitator the source of the structure
- Choose techniques from a defined library of 28, with the user deciding **how** the choice is made
- Record what could not be decided as `## 8. 未確定事項` **inside the session file**, options intact
- Write the session to `project/09_wip_plan/brainstorming-{YYYY-MM-DD}-{N}.md` (shape defined in
  `references/skeletons.md`) and propose which ideas should become feature candidates or risks

This skill does **not** create the feature list (that is `REQ` / `pm-gather-requirements`), does **not** analyze
a feature in depth (that is `FA` / `ba-analyze-requirement`), and does **not** write into `function-list.md`,
`qa.md` or `risk-list.md` itself. **The session file is self-contained**: its ideas, its decisions and its open
questions all live in one document, and nothing leaves it until the user decides to carry it into the official
requirements.

## Reference Documents

Read as needed during execution:

- `references/skeletons.md` — the literal shape of the session document (`## 1`–`## 8-2`) and the rules that go
  with it. **This is the only definition of that structure** — read it before Step 7
- `references/techniques.md` — the technique library: 28 techniques in 6 categories, each with what it is for,
  how to run it, its facilitation prompts, its output shape and its duration
- `references/selection-modes.md` — the four ways to choose techniques (AI 推奨 / ユーザー選択 / ランダム /
  段階フロー), how to present each, and what each mode forbids

## Facilitation stance

These four rules decide whether the session produces the user's ideas or yours. They outrank efficiency.

- **You are the facilitator, not the idea generator.** Every round starts by drawing ideas out of the user.
  Only once they have genuinely run dry do you add your own — and when you do, mark them (`[AI案]`) so the
  session document stays honest about where each idea came from. A transcript that is 80% AI ideas is a failed
  session, however good the ideas are.
- **Pivot domains every ~10 ideas.** Left alone, both you and the user drift into one semantic cluster and
  mistake it for exhaustion. Every ten ideas, deliberately move to a different domain — 業務 → 運用 →
  データ → エンドユーザー → リスク → コスト — and say that you are doing it.
- **Aim for volume before quality.** Roughly 15-20 ideas per technique, 60+ per session, before any organizing.
  This is a target for the session, not a request to dump a list: they should be developed with the user, one
  exchange at a time.
- **No premature convergence.** Do not evaluate, rank, merge or reject anything during Steps 4-5. When the user
  starts judging their own idea mid-flow, note the concern and park it — evaluation begins in Step 6 and not
  before.

## The decision protocol (options + 保留)

> **Hard rule.** For every **decision about the session** — the framing, the selection mode, which technique,
> the prioritization axis, where an idea should be routed — never ask an open-ended question. Present concrete
> options, mark **one as recommended**, and give the reason.

- Deliver with `AskUserQuestion`. Recommended option **first**, its label suffixed `（おすすめ）`. Each option's
  description states its trade-off, not just a restatement of the label.
- The recommendation must cite something real: a sentence in `system-overview.md`, something the user said
  earlier in this session, a previous session file in `09_wip_plan/`. "一般的にこれが有効です" is not a reason.
- **Add a standing `保留（お客様に確認）` option, last**, whenever the decision is one the person in front of you
  may not have the authority to make — anything touching scope, priority, business rules or what the customer
  will accept. Its description names what stays blocked until the answer arrives. Session mechanics (which
  technique to run, when to take a break) do not need it.
- **The decision is never yours.** "おまかせします" is not a decision — it is 保留. Never write a settled-looking
  value into the session document for something the user did not explicitly agree to.
- **This rule does not apply while ideas are being generated.** During Step 5, open questions are the whole
  point — "他にはありますか？" is correct there and canned options would be wrong.

When the user picks 保留, record it **immediately** in the session document's `## 8. 未確定事項`, numbered
`BQ-001`, `BQ-002`, … — the question, the options you had presented **verbatim**, the recommendation and its
reason, and what it blocks. Do not summarize the options away; whoever answers has to be able to do it from that
block alone.

**`## 8` is the register of record for this session, and it lives in the session file.** This skill does not
write to `project/02_requirements/qa.md` and does not assign `QA-xxx` IDs — brainstorming is the pre-decision
stage, and its open questions belong with the session that raised them. `qa.md` is the *requirements* register,
filled by `REQ` and `FA`; the two are separate on purpose. If an answer arrives later, it is recorded in `## 8`
and reflected back into `## 3`-`## 6` of the same file.

## Interaction Guidelines

- **One decision per turn.** Never batch several questions into one message.
- Keep the BA persona (🔍 prefix) if this skill was invoked from the `business-analyst` agent.
- Talk in business terms, not implementation terms. An idea is 「承認者が不在でも申請が止まらない」, not
  「承認フローに代理承認テーブルを追加」.
- Number every idea as it appears (`#1`, `#2`, …) and keep the numbering stable for the whole session — Steps 6
  and 8 refer back to these numbers.
- After each technique, show a short running tally: how many ideas so far, which domains are covered, which are
  still untouched.
- Match the user's language. The session document is written in Japanese regardless.

## Main Flow

### Step 1: Preconditions and resume

`Glob project/09_wip_plan/brainstorming-*.md`. If any file has `status: in-progress` in its frontmatter, read it
and offer to resume with `AskUserQuestion`: `前回の続きから（おすすめ）` / `新しいセッションを始める` /
`過去のセッションを一覧で見る`. When resuming, load its ideas and numbering and continue from where it stopped —
never re-ask what is already recorded there.

Then read whatever project context exists, to ground the recommendations later:

- `project/02_requirements/system-overview.md` — the background and objectives
- `project/02_requirements/function-list.md` — what is already in scope, so ideas are not re-proposals
- `project/02_requirements/glossary.md` — the fixed terminology to phrase ideas in

**Missing files are not an error here.** Unlike `FA`, this skill is designed to run on a blank project — that is
its main use. Note what is missing, say so in one line, and continue. When there is no context at all, the
session is grounded purely in what the user tells you in Step 2, and your recommendations must cite that.

### Step 2: Frame the question

A wrong frame wastes the whole session, so settle it before anything else.

1. Restate the theme in **one sentence** and get confirmation. If the user gave a vague topic
   (「業務効率化について」), narrow it with them until it names a subject and a boundary
   (「経理部の月次締め作業のうち、請求書処理の部分」).
2. Ask what a good outcome looks like — a list of feature candidates? a decision? a risk list?
3. Choose the session type with `AskUserQuestion`, recommending based on how the user described the theme:
   - **発散重視** — 案の幅を広げたい。まだ何を作るか決まっていない段階
   - **課題解決** — 困りごとがはっきりしていて、その解き方を探したい
   - **リスク洗い出し** — 方針は決まっていて、失敗しそうな点を先に潰したい
4. Ask how much time is available. It decides how many techniques fit, and it is the single most common reason
   a session ends badly.

### Step 3: Choose the selection mode

Present the four modes with `AskUserQuestion` as described in `references/selection-modes.md`, with the
recommended one first and the reason for recommending it in one sentence.

Read the corresponding section of `references/selection-modes.md` before executing the chosen mode — each one
has its own rules, and mode B in particular forbids the steering that comes naturally in mode A.

### Step 4: Confirm the technique plan

Present the resulting plan: 1-3 techniques, each with its name, its duration from the index table in
`references/techniques.md`, and **なぜこの手法か** citing a real source. Show the total time against the budget
from Step 2.

Read each chosen technique's full entry in `references/techniques.md` before starting it — the facilitation
prompts *are* the technique, and running one from memory produces a generic conversation.

Let the user adjust before starting: `この計画で始める（おすすめ）` / `手法を変えたい` / `選び方から戻る`.

### Step 5: Facilitation loop

For each technique in the plan:

1. **Open.** Say the technique's name, what it will do in one sentence, and the first facilitation prompt from
   its entry — adapted to the project's actual domain and terminology.
2. **Draw ideas out.** One exchange at a time. Ask, wait, record, build on the answer. When an answer is thin,
   ask about it rather than moving on — the second layer of an idea is usually where the requirement is.
3. **Record each idea** in this shape:
   ```
   **[#7] 承認者不在時の自動エスカレーション**
   内容: 承認待ちが 3 営業日を超えたら、上位者に自動で回る
   なぜ新しいか: 現状は申請者が個別に催促しており、止まっていることに誰も気づけない
   ```
   `なぜ新しいか` is what stops the list filling with restatements of the obvious.
4. **Pivot every ~10 ideas.** Announce the shift: 「ここまで業務手順の話が続いたので、運用と保守の観点に移り
   ます」. This is the anti-bias rule and it is not optional.
5. **Check energy every 4-5 exchanges.** If answers are getting shorter, say so and offer a break, a switch, or
   a lighter technique — do not push through a flat session.
6. **Close the technique** with a tally, then `AskUserQuestion`:
   - `この手法をもう少し続ける` — まだ出そうな手応えがある
   - `次の手法に移る` — 計画の次へ
   - `特定のアイデアを深掘りする` — 一つ選んで具体化する
   - `整理フェーズに進む` — 発散を終えて Step 6 へ

   **Default toward continuing.** Only move to Step 6 when the user chooses it, or when there are 60+ ideas and
   the last round produced nothing new. Say plainly what you see: 「まだ 20 案です。もう一巡すると質の違う案が
   出やすいのですが、いかがしますか？」

### Step 6: Organize and prioritize

Divergence is over; evaluation is now allowed. Say so explicitly — the user has been told not to judge for the
whole session so far.

1. **Group** with Affinity Mapping: propose a grouping, let the user move things, name each group in their
   words. Keep the orphans visible — they are often the most original ideas.
2. **Choose the prioritization axis** with `AskUserQuestion` under the decision protocol:
   - **影響度 × 工数** — 費用対効果で決めたい。実装可否の見当が付いているとき
   - **Now / Next / Later** — 今回のスコープを切りたい。案件の範囲を決める場面向き
   - **MoSCoW** — Must／Should／Could／Won't で分けたい。`function-list.md` の `Priority` 欄
     （`must` / `should` / `could`）にそのまま渡せる唯一の軸
   - **保留（お客様に確認）** — 優先順位を決める権限がこの場にない。順位付けは行わず、グループ分けまでで止める
3. **Rank** along the chosen axis. Ask explicitly whether anything that ranked low is nonetheless mandatory
   (法令、既存業務の代替、契約上の約束) — those must not fall off.
4. **Record the reason** for every item that ended up in the top group. That reason is what defends the scope
   three months from now.
5. **Park what could not be settled.** Any idea whose priority, scope or business rule the user declined to fix
   goes to `## 8. 未確定事項` with its options intact — not into the ranking with a guessed position. An idea
   sitting in 保留 is a known unknown; the same idea ranked on your assumption is a false record.

### Step 7: Write the session document

Path: `project/09_wip_plan/brainstorming-{YYYY-MM-DD}-{N}.md`, where `{YYYY-MM-DD}` is today and `{N}` is the
session number **for that date**, starting at 1 (check with `Glob` first). The first session of 2026-08-24 is
therefore `brainstorming-2026-08-24-1.md`.

- **Write the headings exactly as `references/skeletons.md` defines them** (`## 1. セッション概要` through
  `## 8-2. 未確定事項の詳細`), and write the content in **Japanese** — the document lives in the Japanese
  `project/` tree even though this skill is written in English. There is no template file in `09_wip_plan/` and
  you must never copy the structure out of an earlier session file: those carry a real topic, real ideas and
  `status: done`, and copying one is how a finished session gets overwritten.
- Fill the frontmatter: `status: done`, the date, the session number, the topic, the session type, the
  techniques used and the idea count.
- Every idea keeps the number it had during the session.
- Mark AI-originated ideas `[AI案]` in the 分類 column. Do not quietly launder them into the user's list.
- **Fill `## 8. 未確定事項` from the 保留 decisions collected during the run**, numbered `BQ-001` onward, 状態
  `未回答`, with the 記録日 set to today. Every 保留 that had options presented also gets a
  `## 8-2. 未確定事項の詳細` block carrying those options verbatim. `## 6 ②` holds only the count and who to
  ask — the content lives in `## 8` and nowhere else.
- **Never overwrite an existing file silently.** If the path exists, summarize what would change and ask first.

If the session is interrupted before Step 6, still write the file with `status: in-progress` and whatever ideas
exist. An unwritten session is a lost session — Step 1 can resume from a partial file, but not from nothing.

### Step 8: Route the ideas and hand off

Sort the prioritized ideas into three baskets and present them **as a proposal**:

| Basket | Source | Goes to | Who does it |
|--------|--------|---------|-------------|
| ① 候補機能 | the top of the Step 6 ranking | `project/02_requirements/function-list.md` | PM, via `REQ` / `pm-gather-requirements` |
| ② 確認事項 | `## 8. 未確定事項` | **stays in this file** | nobody — it is already recorded |
| ③ リスク | ideas from `adversarial` techniques | `project/01_management/risks-problems/risk-list.md` | PM, via `RISK` |

**Do not write into `function-list.md` or `risk-list.md` from this skill.** Each has an owning process and
writing behind its back breaks traceability. Present the rows you would add, name the menu item that adds them,
and stop.

**② is not a routing at all — it is a report.** The open questions were already written into `## 8` and that is
where they stay. Do not open `qa.md`, do not propose `QA-xxx` rows, do not ask the user whether to raise them
there. Just state how many are `未回答`, what each one blocks, and who needs to answer. `qa.md` becomes relevant
only much later, when `REQ` or `FA` turns one of these ideas into an actual requirement — and that is those
skills' job, not this one's.

Then update `plans/business-analysis/ba-memory.md` — add a row to `## Brainstorming Sessions` with the date,
theme, status, file path and how many ideas are still unrouted, plus how many `未回答` items sit in its `## 8`.
Do not copy the questions themselves into memory — point at the session file. Refresh `## What To Do Next` and
`Last updated`. Create the file from the skeleton in the `business-analyst` agent if it does not exist.

Finally report:

1. The file written, the techniques used, and the idea count
2. The top-ranked ideas with the reason each is there
3. The three baskets, and the menu item that carries each one forward
4. The single recommended next action — **and then stop**, without starting it

## Error Handling

| Situation | What to do |
|-----------|------------|
| `project/` does not exist at all | Continue — this is the expected first-run state. Create `09_wip_plan/` when writing in Step 7 and say so |
| There is no template to copy in `09_wip_plan/` | Expected — there never is one. `references/skeletons.md` is the structure; never copy an earlier session file |
| `system-overview.md` missing or still a template | Continue, but say once that recommendations will be grounded only in what the user says in Step 2, not in project documents |
| The user gives a theme too vague to work on | Do not start. Narrow it with them in Step 2 until it names a subject and a boundary; a vague theme produces vague ideas that cannot be routed |
| The user asks you to just generate the ideas | Say once that a list you wrote alone is not usable as a requirement source, then offer a middle path: you propose 5 seed ideas, and the session builds on them together |
| Ideas dry up early (under ~15) | Do not proceed to organizing. Switch technique — a `creative` one if the last was `structured`, or Reversal / Inversion, which is the reliable unsticker |
| The user starts evaluating during Step 5 | Record the concern against that idea number, say evaluation comes in Step 6, and continue diverging |
| The user says 「おまかせします」 to a scope or priority decision | Treat it as 保留, not as approval. Record it in `## 8` with the options you offered, and continue — never write your own choice in as though it were theirs |
| A 保留 duplicates a question already answered in an earlier session file | Do not re-raise it. Cite the earlier `BQ-xxx` and its answer, and move on |
| The user asks you to file the open questions into `qa.md` | Say that `qa.md` is the requirements register, filled by `REQ` / `FA` when an idea actually becomes a requirement, and that `## 8` is where they belong for now. If the user repeats the request, it is their call — but tell them the BA's `QA` menu item is what does it, not this skill |
| The session runs out of time mid-flow | Go straight to Step 7 with `status: in-progress` and write what exists. Do not skip the write to save time |
| The target session file already exists | Increment `{N}`; if the user meant to update the existing one, show what would change and ask |
| An idea contradicts a feature already in `function-list.md` | Keep it, and flag the contradiction in ② 確認事項. This skill does not resolve scope conflicts |

## Related Files

- `project/09_wip_plan/brainstorming-{YYYY-MM-DD}-{N}.md` — the output. Its structure is defined in
  `references/skeletons.md`; there is no template file in that folder, and an earlier session is never copied
- `project/02_requirements/system-overview.md` — background and objectives; the source for recommendations
- `project/02_requirements/function-list.md` — read to avoid re-proposing what is already in scope
- `project/02_requirements/glossary.md` — fixed terminology to phrase ideas in
- `project/02_requirements/qa.md` — the **requirements** confirmation register. Read-only context at most; this
  skill never writes to it. Session-level open questions go to `## 8` of the session file instead
- `project/01_management/risks-problems/risk-list.md` — where basket ③ goes (written by `RISK`, not by this skill)
- `plans/business-analysis/ba-memory.md` — the BA agent's working notes (created on first run)
- `references/skeletons.md` — the session document's `## 1`–`## 8-2` shape
- `references/techniques.md` — the 28-technique library
- `references/selection-modes.md` — the four ways to choose techniques
