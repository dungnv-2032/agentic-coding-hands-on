---
name: tkm:ba-analyze-requirement
category: business-analysis
roles: [analyst]
description: |
  Analyze one feature picked from the function list (function-list.md) in depth.
  Settle its business flow, inputs/outputs, business rules and acceptance criteria interactively,
  presenting every decision as 3 options + a recommendation + a standing "defer (confirm with the customer)"
  choice for the user to pick from.
  Whatever cannot be settled on the spot is filed into qa.md with its options intact, leaving the
  corresponding section blank with a marker.
  Once the customer has answered, the "reflect answers" mode writes the answer back into that section
  and flips the qa.md row's Status to Reflected.
  The result is written to project/02_requirements/functions/function-N-*.md, and a link is written
  back into the matching row of function-list.md.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# ba-analyze-requirement Skill

One feature at a time: take a single row out of the function list and turn it into a specification an engineer
can build from and a customer can accept against.

## Purpose

- Deepen **one** feature from [`project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md)
  into a complete detail document under `project/02_requirements/functions/`
- Make every decision **an informed choice by the user**, not an assumption by the AI — always three concrete
  options with one recommendation, plus a standing fourth option to defer
- Keep the result traceable: every actor resolves to a `role-list.md` ID, every term to `glossary.md`, every
  constraint-driven rule to `non-function-list.md`
- Push what cannot be decided into `qa.md` **at the moment it comes up** — with its options intact, so the
  customer can answer it directly — instead of inventing an answer
- Close the loop: once the customer has answered, reflect that answer back into the detail document through the
  **回答反映 mode**, so a parked question never rots in the register

This skill does **not** create features (that is `REQ` / `pm-gather-requirements`), and it does **not** design
screens or APIs (those are `04_screen-design/` and `03_basic-design/`).

## Reference Documents

Read as needed during execution:

- `references/skeletons.md` — the literal shape of the detail document (§1–§8), and how a row is appended to
  the `qa.md` REQ owns. **Read it before Step 5** — there is no template file under `functions/` to copy from
- `references/analysis-checklist.md` — what must be decided in each of the 8 sections, and the definition of
  done for each
- `references/option-patterns.md` — the option library: recurring requirement decisions with their canonical
  three shapes and which non-functional requirement decides them

## Decision protocol

> **Hard rule 1.** For **every** analysis decision, never ask an open-ended question. Present **three concrete
> options** plus the standing fourth option `保留（お客様に確認）`, and mark **one of the three as recommended**,
> with the reason grounded in a cited project document.
>
> **Hard rule 2.** Never write a decision into the document that the user has not explicitly chosen. There is no
> implicit default, no "I will assume A for now". If the user goes silent on a point, answers ambiguously, or
> says "you decide" — that is **保留**, and it goes to `qa.md`. The AI supplies options and a recommendation;
> the user supplies the decision.

- Deliver with `AskUserQuestion`. Put the **recommended option first** and suffix its label with
  `(Recommended)`; make the fourth option `保留（お客様に確認）` last. The tool accepts 2–4 options and appends
  "Other" automatically, so this fits exactly with room for the user's own answer.
- Each option's `description` states its **trade-off** — what you gain and what you give up — not just a
  restatement of the label. The 保留 option's description names **what stays blocked** until the customer answers.
- When the options are structural (a flow, a rule set, a state model, a set of validation messages), put the
  concrete shape in the option's `preview` field so the user can compare them side by side. Previews are
  single-select only.
- The recommendation must cite a source: a row in `non-function-list.md`, a role in `role-list.md`, a statement
  in `system-overview.md`, a sibling feature already analyzed, or a decision the user made earlier in this
  session. "It is the common approach" is not a reason.
- **Escape hatch:** if fewer than three options are genuinely viable, say so explicitly, give the reason, and
  offer the ones that exist — but `保留` always stays on the list. Do not pad with filler options nobody would pick.
- If the user picks "Other", restate their answer in your own words and confirm it before writing it into the
  document.
- If the user picks `保留`, run **"Parking a decision"** below immediately, then carry on with the next decision.
- **When the user asks you to decide for them** ("just pick one", "do whatever is standard"): do not. Restate the
  recommended option and its cited reason and ask them to confirm it — a confirmation is a decision — or record
  it as 保留. A requirement the customer never agreed to is worse than an open question.

## Interaction Guidelines

- **One decision per turn.** Never batch several questions into one message.
- Options are described in **business terms**, not implementation terms. "Deleted records stay visible to admins
  for 30 days" — not "soft delete with a `deleted_at` column".
- When the answer is already determined by a document you have read, **do not ask a three-option question** —
  state the answer and cite the source. It still needs the user's explicit sign-off, but that happens once per
  section at the **section closing gate** (Step 4) rather than as a separate question. Interrogating the user
  about something the project has already answered wastes their attention; writing it in without any sign-off
  breaks Hard rule 2.
- Keep the BA persona (🔍 prefix) if this skill was invoked from the `business-analyst` agent.
- Between sections, show a short running summary of what has been decided so far so the user can course-correct
  cheaply before you write the file.

## Shared conventions

### The two schemas, and which one wins

- **Files REQ (`tkm:pm-gather-requirements`) owns — `function-list.md` and `qa.md` — are English-headed.** Use
  their column names and cell vocabulary verbatim; append, never re-shape, never start a parallel register. A
  value with no column to go in (there is no `更新日`, no `反映先`) goes where the schema already has room — the
  `Revision History` table, or the BA's own notes — **never into a new column**, which shifts every cell after
  it and corrupts a file `SCH` and `REP` read.
- **Files this skill owns — `functions/function-{No}-{slug}.md` — are Japanese**, but values carried over from
  `function-list.md` (the `F-ID`, the `Priority` value, the `ROLE-xxx` IDs) are copied **verbatim**, untranslated.

`references/skeletons.md` holds both shapes.

### Exact strings

These are shared with `qa.md`, `business-analyst.md` and the reference files. Use them **verbatim** — the
reflection mode finds work by matching on them.

| Thing | Exact form |
|-------|-----------|
| Marker for a blocked section in a detail document | `<!-- 未確定: qa.md QA-xxx 参照 -->` (with the real ID) |
| `qa.md` §1 columns | `QA-ID` / `Subject` / `Question` / `Status` / `Raised on` / `Answer` / `Answer date` / `Respondent` — REQ's shape, unchanged |
| `Status` values REQ writes | `Unanswered` / `Answered` |
| `Status` values this skill adds | `Reflected` (the answer is carried into the detail document) / `Deferred` (parked by agreement). REQ writes neither and treats anything that is not `Unanswered` as out of its hands |
| `Subject` for a feature-level question | `F-001 §5` — the F-ID plus the detail document's section number. **This is what Mode B resolves the reflection target from**, since `qa.md` has no `反映先` column |
| Where a parked question's options live | inside the `Question` cell, `<br>`-separated, so the customer can choose one without opening another document |
| Where the reflection target and what it blocks live | `## Open Items` in `plans/business-analysis/ba-memory.md` — the BA's own notes, never a second table in `qa.md` |
| `Priority` values in `function-list.md` | `must` / `should` / `could` (REQ's skeleton). Never 必須 / 推奨 / 任意 |
| The standing fourth option | `保留（お客様に確認）` |

## Main Flow

### Step 0: Choose the mode

`Read` [`project/02_requirements/qa.md`](../../../project/02_requirements/qa.md) and
`plans/business-analysis/ba-memory.md` **first** — before touching the function list — because they decide what
is worth doing in this session. Neither may exist yet; that is a normal first run, not an error.

Then present the mode with `AskUserQuestion`:

| Mode | What it does | Flow |
|------|--------------|------|
| `A. 新規分析` | Analyze a feature that has no detail document yet | Steps 1–8 |
| `B. 回答反映` | Reflect customer answers already recorded in `qa.md` back into the detail documents | "Mode B" section below |
| `C. 継続` | Resume a feature left `🔄 in progress`, from its first incomplete section | Steps 3–8, skipping decisions already recorded |

Recommend in this order:

1. **`B`** if `qa.md` holds at least one row whose `Status` is `Answered`, or whose `Answer` cell is filled
   while `Status` still says `Unanswered`. Those answers are already paid for — reflecting them is the cheapest way to unblock
   a feature, and a stale answer is the easiest thing in the project to lose.
2. **`C`** if `ba-memory.md` marks a feature `🔄 in progress`.
3. **`A`** otherwise.

State the count behind the recommendation ("3 features unanalyzed, 2 answers waiting to be reflected") so the
user is choosing with the same information you have.

### Step 1: Preconditions

Read [`project/02_requirements/function-list.md`](../../../project/02_requirements/function-list.md).

- **If the file does not exist** → stop. Tell the user the requirements phase has not started, and that
  `REQ` (`pm-gather-requirements`) must produce the feature list first.
- **If every row is still a template placeholder** → stop with the same message. Judge by the
  **`Function name` column** of `## 2. Functions`, not the `F-ID` column: REQ's skeleton already contains a
  literal `F-001` in the ID cell, so a row whose `Function name` is empty or is only an
  `<!-- e.g. … -->` HTML comment is unfilled. This skill deepens an existing feature; it does not invent the
  feature list.
- Otherwise continue.

### Step 2: Feature selection

Render the `## 2. Functions` rows of `function-list.md` as a table, adding an **Analysis status** column.
Derive the status by checking the row's `Detail document` cell with `Read` / `Glob` (REQ leaves it blank or
`TBD`, so a blank cell means "not analyzed", not "file missing"):

| Status | Meaning |
|--------|---------|
| `✅ analyzed` | The file exists and its sections contain real content |
| `🔄 partial` | The file exists but some sections are still empty or template placeholders |
| `⬜ not started` | The file does not exist, or contains only the template's HTML comments |

Sort so that `Priority = must` rows that are `⬜` appear first, then `should`, then `could` — that is where the
risk sits. (`must` / `should` / `could` is the vocabulary REQ's skeleton writes; if a project has hand-edited the
column into different values, sort by what is actually in the file and say so rather than matching nothing.) Ask
the user which feature to analyze; accept an `F-ID`, a feature name, or a fuzzy match. Confirm the single feature
in scope.

**One feature per run.** If the user asks for several, present the priority-ordered list and analyze only the
one they confirm, then stop and report.

If the chosen feature is `🔄 partial`, read the existing file first and **resume from the first incomplete
section** rather than re-asking decisions that are already recorded there.

### Step 3: Ground the analysis

Read, and keep in context for the rest of the run:

- `role-list.md` — the actors. Every actor you name in §3 must resolve to a `ROLE-xxx` ID here. If the feature
  needs an actor that does not exist, flag it as a gap rather than inventing a role.
- `glossary.md` — the fixed terminology. Use these terms verbatim; if you need a term that is missing, propose
  adding it.
- `non-function-list.md` — the constraints. These decide many business rules (retention, response time, audit,
  authentication strength), so consult them before offering options rather than after.
- `system-overview.md` — the background and objectives; the "why" that justifies a recommendation.
- Sibling files already written under `functions/` (via `Glob`) — to stay consistent with decisions made for
  related features and to catch scope overlap.

Then restate the feature in 2–3 sentences — what it does, for whom, and why the system needs it — and get the
user's confirmation before going deeper. A wrong framing here wastes the entire rest of the run.

### Step 4: Section-by-section analysis loop

Walk the sections of the detail template **in order**, using `references/analysis-checklist.md` for what must be
decided in each and `references/option-patterns.md` for the option library. Every decision follows the decision
protocol, and every core section ends at its closing gate.

| Section | What you are settling | Effort |
|---------|----------------------|--------|
| §1 機能情報 | ID, name, summary, priority, target roles | Mostly mechanical — carry over from `function-list.md` |
| §2 背景・目的 | Why this feature exists, which problem from `system-overview.md` it solves | Short, but must cite |
| §3 ユースケース・業務フロー | Actor, trigger, preconditions, the numbered happy path, alternate and exception flows | **Core** |
| §4 入力・出力 | Every input and output item with its constraints | **Core** |
| §5 業務ルール・制約 | Validation, permission control, calculation logic, state transitions | **Core** |
| §6 受入条件 | Observable conditions under which the feature is done | **Core** |
| §7 関連ドキュメント | Cross-links to function-list, and to screens / APIs when they exist | Mechanical |
| §8 改訂履歴 | Today's date, the author, "初版作成" | Mechanical |

Sections 3–6 are where the real work is. Do not rush them to reach the file write.

#### Section closing gate (§3–§6)

Do not slide from one core section into the next on your own. When a section's decisions are settled, render the
**drafted section as it will appear in the file** and close it with `AskUserQuestion`:

| Option | Meaning |
|--------|---------|
| `この内容で確定 (Recommended)` | The section is agreed as shown |
| `修正したい箇所がある` | The user names what is wrong; you revise and re-present the gate |
| `この点は保留にする` | Something in it cannot be decided yet → run "Parking a decision", then re-present the gate for the rest |

This gate is what makes derived and drafted content legitimate: items marked **Derive** or **Confirm** in
`references/analysis-checklist.md` never get their own question, so this is where the user signs off on them.
A section that has not passed its gate must not be written to the file.

### Step 5: Write the output file

Path: `project/02_requirements/functions/function-{No}-{slug}.md`

- `{No}` is the numeric part of the `F-ID` (`F-001` → `1`), and `{slug}` is a short kebab-case English slug of
  the feature name (`ログイン・ログアウト` → `login`), per
  [`skills/_shared/extras/pm-skills/function-breakdown.md`](../_shared/extras/pm-skills/function-breakdown.md).
- **Write the headings and tables exactly as `references/skeletons.md` defines them**, in **Japanese**. There is
  no template file under `functions/` to copy from — REQ leaves that folder empty on purpose, so the skeleton is
  the only source of the structure — and values carried over from `function-list.md` (`F-ID`, `Priority`,
  `ROLE-xxx`) are copied verbatim: do not translate `must` into 必須.
- Keep the cross-reference line at the top pointing at `../function-list.md`, and at
  `../../04_screen-design/screen-list.md` / the API list **only where those files already exist**.
- **Completeness gate before writing:** every section must either satisfy its definition of done in
  `references/analysis-checklist.md`, or be **left empty except for an explicit
  `<!-- 未確定: qa.md QA-xxx 参照 -->` marker** naming the question that blocks it. A bare template placeholder —
  a section that is neither done nor marked — is never acceptable.
- **A blocked section stays empty.** Do not write the recommended option in as a provisional value, and do not
  list the options in the document. The options live in `qa.md` §2; the document carries the marker and nothing
  else, so no reader can mistake an unanswered question for a settled requirement.
- A file written with markers still counts as progress — but the feature is `🔄 partial` / `⏸ blocked`, **never
  `✅`**, until every marker is gone.
- **Never overwrite an existing file silently.** If the target path already exists, summarize what would change
  and ask before writing.

### Step 6: Write back to `function-list.md`

`function-list.md` is REQ's file, and its `## 2. Functions` table has **these columns and no others**:

```
| F-ID | FG-ID | Function name | Summary | Priority | Target roles | Related WBS ID | Detail document |
```

`Edit` **only** the analyzed feature's row, and only these cells:

- `Detail document` → a link to the file you just created. This is the cell REQ deliberately left blank or `TBD`.
- `Summary` / `Priority` / `Target roles` → correct them **only if the analysis actually settled them**, in
  REQ's own vocabulary (`Priority` stays `must` / `should` / `could`).

**There is no `更新日` / "Last updated" column — do not invent one** (see "The two schemas"). The date of your
change goes into `## 3. Revision History` as one appended row:
`| YYYY-MM-DD | ba-analyze-requirement skill | F-001 の詳細ドキュメントを作成 |`.

Leave every other row, `## 1. Function Groups`, and `Related WBS ID` untouched. If the analysis changed the
feature's scope enough to affect its function group or its WBS ID, report it rather than editing — those belong
to the PM's `SCH` work.

### Step 7: Reconcile the markers against `qa.md`

Parking happens **during** the analysis, not here (see "Parking a decision" below). This step is the audit that
the two files agree:

1. Every `<!-- 未確定: qa.md QA-xxx 参照 -->` marker in the file you just wrote names a QA-ID that **exists** as
   a row in `## 1. Items for Confirmation` of `qa.md`, and whose `Question` cell still carries the options you
   presented.
2. Every QA-ID you raised this session has a row in `## Open Items` of `ba-memory.md` whose `Reflect into`
   points back at the **exact file and section** you marked, and whose `Subject` in `qa.md` names the same
   section (`F-001 §5`).
3. No QA-ID is referenced by a marker that no longer exists (you resolved it later in the session but left the
   row open) — if one is, close the loop now rather than leaving a question the customer would answer for nothing.

Fix any mismatch immediately; a marker with no question, or a question with no marker, is how a requirement gets
silently lost.

### Step 8: Update memory and summarize

Update `plans/business-analysis/ba-memory.md` — the feature's status, the sections filled, any new open items,
the `What to do next` list, and `Last updated`. Create it from the skeleton in the `business-analyst` agent if
it does not exist.

Then report:

1. The file written, and the sections completed
2. Decisions the user made that are worth re-reading (the ones with consequences downstream)
3. `qa.md` rows raised, what each blocks, and — plainly — **that the feature cannot be called done until the
   customer answers them and the answers are reflected with 回答反映 mode**
4. The suggested next step — either the highest-priority feature still `⬜`, or 回答反映 if answers have arrived
   in the meantime — **and then stop**, without starting it

## Parking a decision

Run this the moment the user picks `保留（お客様に確認）`, or the moment a decision turns out to depend on one
that is already parked. Do it **there and then**, not at the end of the run: a question written down while the
context is fresh is answerable by the customer; one reconstructed an hour later is not.

`qa.md` is **REQ's register, shared with the whole requirements phase** — one file, one table. Append to it in
the shape REQ created; never add a section, a column or a second table (see "Shared conventions").

1. **Check for a duplicate.** Read `qa.md` and look for an open question with the same `Subject` or on the same
   topic. If one exists, reuse that QA-ID — add your section to its `Open Items` row in `ba-memory.md` instead
   of raising a second row.
2. **Allocate the ID.** Highest existing `QA-nnn` + 1, zero-padded to three digits. The numbering is shared with
   every other question REQ raised, so never restart it.
3. **Add one row to `## 1. Items for Confirmation`,** in REQ's columns:
   - `Subject` = `F-001 §5` — the F-ID and the section, which is how Mode B finds its way back.
   - `Question` = the question **in business language, addressed to the customer and answerable without opening
     the detail document**, followed by the three options **verbatim as you presented them**, `<br>`-separated,
     with the recommended one marked and the document you cited for it. The customer decides between the
     options, so they must survive the trip into the register unedited.
   - `Status` = `Unanswered`, `Raised on` = today (`currentDate`). Leave `Answer` / `Answer date` /
     `Respondent` empty.
4. **Append one row to `## 2. Revision History`:** today's date, `ba-analyze-requirement skill`, `Raised QA-014`.
5. **Mark the document.** The affected section holds `<!-- 未確定: qa.md QA-xxx 参照 -->` and **nothing else** —
   no provisional value, no option list, no "probably A". See Step 5.
6. **Record the internal half in memory.** `qa.md` is customer-facing and has no room for it, so the reflection
   target and the blocking scope go to `## Open Items` in `plans/business-analysis/ba-memory.md`: the QA-ID, its
   `Status`, `Reflect into` (file + section — the marker this answer clears) and what it blocks. Set the feature
   to `⏸ blocked` when the parked point sits in a core section (§3–§6). **This row is what makes the question
   reflectable**; a QA row with no `Open Items` entry is a question nobody can carry back.
7. **Keep going.** 保留 pauses one decision, not the session. If a later decision genuinely depends on the parked
   one, park it too — say the dependency out loud, name the parent QA-ID in the dependent question, and record
   the dependency in its `Blocking` cell in `ba-memory.md` so it is visible that one answer unblocks both.

Tell the user, in one line, what you just registered and what it blocks. They are the one who has to raise it
with the customer, so they need to leave the session knowing it exists.

## Mode B: 回答反映 (reflecting the customer's answers)

The other half of the loop. The customer has answered; this mode carries the answers into the documents and
retires the questions.

### B-1. Collect what is answerable

Read `qa.md` — REQ's table, `## 1. Items for Confirmation` — and take every row that is either:

- `Status` = `Answered`, or
- `Status` = `Unanswered` **but the `Answer` cell is filled** — someone recorded the answer without updating the
  status; treat it as answered and fix the status as you go.

Rows already `Reflected` are done; rows `Deferred` are parked by agreement — leave both alone.

Then work out **where each answer goes**, in this order. `qa.md` has no `反映先` column, so never filter on one:

1. The row's QA-ID appears in `## Open Items` of `ba-memory.md` → its `Reflect into` cell is the target.
2. Otherwise the `Subject` cell names it (`F-001 §5` → `functions/function-1-*.md`, §5).
3. Otherwise `Grep` the `functions/` tree for `<!-- 未確定: qa.md QA-xxx 参照 -->` and use the section that
   carries the marker.
4. If none of the three resolves — the question is a REQ-raised one about `system-overview.md` or `role-list.md`
   rather than about a feature — it is **not this skill's work.** List it separately and say it belongs to REQ.

If nothing qualifies, say so plainly, list the questions still `Unanswered` with their age, and offer to switch
to `新規分析` instead.

### B-2. Pick one

Present the candidates as a table — QA-ID / `Subject` / `Question` / `Answer` / the target you resolved in B-1
(and how you resolved it) — and let the user choose.
**One QA-ID at a time**, all the way through B-3…B-7, before returning here for the next. Batch reflection is
how contradictions get written in unnoticed.

### B-3. Map the answer to a decision

`Read` the target file and the QA row's `Question` cell, so you have the original three options in front of
you. Then decide what the customer actually chose:

- **The answer clearly selects one option** → restate it in one sentence ("A案 — 削除後30日は管理者のみ復元可")
  and confirm it with the user before editing.
- **The answer is ambiguous, partial, or matches none of the options** → **do not guess.** Present up to three
  readings of what the customer meant, plus `保留（お客様に再確認）`, with `AskUserQuestion`. If the user picks
  保留, raise a **new** QA-ID whose `Question` names the ambiguity and references the parent QA-ID, and leave the
  marker in place.
- **The answer contradicts `non-function-list.md` or a decision already written in another feature** → surface
  the conflict before anything else, with the citation, and offer three ways to resolve it plus 保留. Never
  reconcile it silently in either direction.

### B-4. Edit the target section

Write the agreed content into the section resolved in B-1, **remove the marker**, and keep the section's own definition of done
in `references/analysis-checklist.md` satisfied — a marker is not replaced by half a sentence.

Then propagate. An answer rarely lands in one section only: a new rule in §5 usually implies an exception flow
in §3, a constraint in §4 and an acceptance criterion in §6. Walk the propagation checklist at the end of
`references/analysis-checklist.md`, and run any **new** decision it exposes through the normal protocol — three
options, a recommendation, and 保留 on the table.

### B-5. Retire the question in `qa.md`

- `## 1. Items for Confirmation` row: `Status` → `Reflected`. Fill `Answer date` / `Respondent` from what the
  user tells you; if they do not know, ask once rather than inventing them, and leave them blank if the answer
  is genuinely unknown. Leave the `Question` cell — options and all — exactly as it is.
- `## 2. Revision History`: append today's date, `ba-analyze-requirement skill`, and where the answer landed —
  `Reflected QA-014 into functions/function-1-login.md §5`.
- Do not delete the row. The register is the audit trail of what the customer agreed to.

### B-6. Record it in the document's history

Add a row to §8 改訂履歴 of the detail document: today's date, the author, and what changed — e.g.
`QA-004 の回答を §5 業務ルール・§6 受入条件に反映`.

### B-7. Update memory and report

Remove the item from `## Open Items` in `ba-memory.md` (or update it if a follow-up QA was raised), and move the
feature's status: `⏸ blocked` → `🔄 in progress`, or → `✅ done` **only when the detail document contains no
`未確定` marker at all**. Refresh `What to do next` and `Last updated`.

Then report: which QA-ID was reflected and where, what else changed as a consequence, which questions are still
open, and what you recommend next — and **stop**.

## Error Handling

| Situation | What to do |
|-----------|------------|
| `function-list.md` missing or all-template | Stop at Step 1; direct the user to `REQ` (`pm-gather-requirements`) |
| `role-list.md` missing or empty | Continue, but say so: actors cannot be traced to IDs, so record them by name and raise a `qa.md` item to reconcile later |
| `non-function-list.md` missing | Continue, but flag that constraint-driven rules (retention, timeouts, audit) are being decided without a source — mark them for review |
| The target `functions/*.md` already exists | Show what would change and ask before overwriting; never write silently |
| The feature needs a role that `role-list.md` does not define | Do not invent it. Report the gap and raise it in `qa.md` |
| The user cannot decide a core-section point | Run "Parking a decision": one row in `qa.md` (options in its `Question` cell), the marker in the section, an `## Open Items` row + `⏸ blocked` in memory — then carry on with the next decision |
| The user asks to analyze several features at once | Present the priority-ordered list, analyze only the one they confirm, then stop |
| The user tells you to decide for them | Do not. Restate the recommended option with its citation and ask them to confirm it, or record it as 保留 (Decision protocol, Hard rule 2) |
| `qa.md` does not exist | Create it from **REQ's** skeleton (`pm-gather-requirements/SKILL.md` → "Recording Open Items": `## 1. Items for Confirmation` / `## 2. Revision History`), never from a shape of your own — then append your row and tell the user you created the register REQ also writes to |
| `qa.md` exists but in a different shape (hand-edited, or an older kit) | Append **in the shape that is already there**, continuing its QA-ID numbering, exactly as REQ does. Say once which shape you found. Never rewrite the file into the current schema on your own — it is customer-facing |
| A customer answer contradicts `non-function-list.md` or another feature | Do not apply it silently. Show the conflict with its citation and offer three ways to resolve it plus 保留 (B-3) |
| The marker for a QA-ID is gone (the file was hand-edited) | Locate the section from the QA row's `Subject`, show its current content, and get confirmation before editing — someone may have already answered it by hand |
| An answered QA row has no `Open Items` entry and its `Subject` names no feature | It is a REQ-raised question about `system-overview.md` / `role-list.md`, not a feature detail. Report it and leave it to REQ; do not reflect it yourself |
| A customer answer is ambiguous or matches none of the options | Do not guess. Offer up to three readings plus `保留（お客様に再確認）`; on 保留, raise a follow-up QA-ID referencing the parent (B-3) |

## Related Files

- `project/02_requirements/function-list.md` — the input: the feature list and its priorities. Owned by REQ;
  this skill edits only the `Detail document` cell of the row it analyzed, plus a `## 3. Revision History` row
- `project/02_requirements/functions/function-{No}-{slug}.md` — the output. Its structure is defined in
  `references/skeletons.md`; there is no template file in that folder to copy from
- `project/02_requirements/role-list.md` — actors; every actor must resolve to a `ROLE-xxx` ID
- `project/02_requirements/glossary.md` — fixed terminology
- `project/02_requirements/non-function-list.md` — constraints that decide business rules
- `project/02_requirements/system-overview.md` — background and objectives; the source for §2
- `project/02_requirements/qa.md` — the customer confirmation register **owned by REQ**. One table,
  `## 1. Items for Confirmation`, in REQ's columns; a parked question's options ride in its `Question` cell and
  its reflection target lives in `ba-memory.md`. Both the parking and the reflection loop run through it
- `plans/business-analysis/ba-memory.md` — the BA agent's working notes (created on first run)
- `references/skeletons.md` — the detail document's §1–§8 shape, and how a row is appended to REQ's `qa.md`
- `references/analysis-checklist.md` — per-section decisions and definitions of done
- `references/option-patterns.md` — the option library for recurring decisions
- `skills/pm-gather-requirements/SKILL.md` — the owner of `function-list.md` and `qa.md`; its
  "Recording Open Items" section is the authoritative `qa.md` skeleton
