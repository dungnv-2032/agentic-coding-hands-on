# Analysis Checklist

What must be settled in each section of `project/02_requirements/functions/function-{No}-{slug}.md`, and the
definition of done for each. Work the sections in order — later sections depend on earlier ones.

Legend for the "Ask?" column:

- **Derive** — the answer is already in a document you have read. State it and cite the source; do not ask a
  three-option question. It is still signed off by the user at the section closing gate.
- **3 options** — the answer is a genuine decision. Apply the decision protocol: three concrete options with one
  recommended, **plus the standing fourth option `保留（お客様に確認）`**.
- **Confirm** — you can draft it, but the user must approve the draft before it is written.

Whatever the category, nothing reaches the file without the user's explicit agreement — either through the
question itself or through the section closing gate. And whenever the answer is 保留, the section is left empty
apart from its `<!-- 未確定: qa.md QA-xxx 参照 -->` marker.

---

## §1 機能情報

| Field | Source | Ask? |
|-------|--------|------|
| 機能ID | The `F-ID` from `function-list.md` | Derive |
| 機能名 | The `Function name` column | Derive |
| 概要 | One sentence: who does what, to what end | Confirm |
| 優先度 | The `Priority` column — copied **verbatim** in REQ's own vocabulary (`must` / `should` / `could`). Never translated to 必須 / 推奨 / 任意 | Derive |
| 対象ロール | Must be `ROLE-xxx` IDs from `role-list.md` | 3 options only when the feature could plausibly serve different role sets |
| 承認者 / 承認日 | Leave blank — the PM fills these at review time | — |

**Done when:** every cell is filled except 承認者 / 承認日, and every 対象ロール value resolves to a real
`role-list.md` ID. A role named in prose but absent from `role-list.md` is a gap — report it, do not invent it.

---

## §2 背景・目的

Answer three questions in 3–5 sentences:

1. **Which problem does this solve?** Cite the specific problem or objective in `system-overview.md`.
2. **What happens if we do not build it?** The cost of absence — this is what justifies the priority.
3. **How will we know it worked?** The business outcome, not the technical one. This foreshadows §6.

**Done when:** the section cites at least one statement from `system-overview.md`, and contains no sentence that
merely restates the feature name ("This feature allows users to log in" adds nothing).

---

## §3 ユースケース・業務フロー

The core section. Nothing downstream is trustworthy if this is vague.

### Header table

| Field | What must be settled | Ask? |
|-------|---------------------|------|
| アクター | Who performs it — a `ROLE-xxx` ID, plus the system itself when a step is automated | Derive from §1, confirm if ambiguous |
| トリガー | What starts the flow: a user action, a schedule, an external event, another feature completing | 3 options when more than one is plausible |
| 事前条件 | What must be true before the flow can start (authentication state, data that must exist, prior feature completed) | Confirm a draft |

### 基本フロー (the happy path)

- A **numbered** list of steps, each a single observable action.
- Each step names **who acts** — the actor or the system. "The data is validated" hides the actor; "The system
  validates the entered data" does not.
- Between 3 and 10 steps. Fewer than 3 usually means the flow is under-analyzed; more than 10 usually means the
  feature should be split — raise that with the user rather than writing a 20-step flow.
- The last step states the **completed state**: what has changed, and what the actor sees.

### 代替・例外フロー

At minimum, decide and record:

- **At least one alternate flow** — a legitimate variation of the happy path (a different role taking the same
  action, an optional step skipped, a second entry point).
- **At least one exception flow** — what happens when it fails. For each: the trigger condition, what the system
  does, what the actor sees, and whether the state is rolled back.
- Walk the happy path step by step and ask "what if this step fails?" — every step that touches data,
  permissions or an external system needs an answer.

**Done when:** the header table is complete, the happy path is numbered with a named actor per step and ends in
a stated completed state, and there is at least one alternate and one exception flow. Every exception names its
observable outcome — "an error is displayed" is not an outcome; "the form is redisplayed with the message X and
no data is saved" is.

**Closing gate:** render the drafted flow and get the user's explicit 確定 before starting §4. A flow the user
never approved is the most expensive thing to discover wrong later — everything downstream is built on it.

---

## §4 入力・出力

Every item the feature consumes or produces, with its constraints.

For each row of the table:

| Column | What must be settled |
|--------|---------------------|
| 項目 | The item name, using `glossary.md` terminology |
| 種別 | 入力 or 出力 |
| 内容・制約 | Type, required/optional, length or range, format, allowed values, default |

Cover all four sources, not just the obvious one:

1. **User input** — what the actor enters or selects
2. **System output** — what is displayed, generated or returned
3. **Persisted data** — what is written and what is read
4. **External data** — anything exchanged with another system or feature

**Done when:** every item in the flows of §3 appears here; every input states required/optional and its
constraint; and every constraint that came from a non-functional requirement cites it. Detailed field layout is
**out of scope** — that is `04_screen-design/`. Note the boundary rather than crossing it.

**Closing gate:** render the drafted table and get the user's explicit 確定 before starting §5. Constraints the
user has not seen are constraints the customer never agreed to.

---

## §5 業務ルール・制約

The rules that govern behavior, separate from the flow itself. Four categories — check all four, and write
"該当なし" explicitly where a category does not apply, so a reader can tell it was considered rather than
forgotten:

1. **Validation** — what makes input invalid, and what happens then. Consult `references/option-patterns.md` →
   validation timing, error surfacing.
2. **Permission control** — which roles may do what, and what a role that may not see encounters. Consult
   option-patterns → authorization model.
3. **Business logic** — calculations, derivations, state transitions, uniqueness rules. Write them so two
   readers reach the same result on the same input.
4. **Constraints from `non-function-list.md`** — retention, timeouts, audit logging, concurrency, volume limits.
   These are frequently missed because they are invisible in the happy path.

**Done when:** all four categories are addressed or explicitly marked 該当なし; every rule is stated so that its
outcome is unambiguous; and no rule contradicts §3 or `non-function-list.md`. Ambiguous quantifiers — "quickly",
"a large number", "appropriately" — must be replaced with a number or raised in `qa.md`. A number the user
cannot confirm is a 保留, not a guess: retention periods, timeouts and limits are exactly the values a customer
must sign off on.

**Closing gate:** render the drafted rules and get the user's explicit 確定 before starting §6. The acceptance
criteria are derived from these rules, so approving them out of order produces criteria for rules nobody agreed to.

---

## §6 受入条件 (Acceptance Criteria)

The conditions under which the feature can be called complete.

Each criterion must be:

- **Observable** — verifiable by a person operating the system, without reading code
- **Binary** — it either passes or it does not
- **Traceable** — each maps to a flow in §3 or a rule in §5

Coverage requirement: at least one criterion for the happy path, one per exception flow in §3, and one per
permission rule in §5. Consistency requirement: no criterion may contradict `01_management/define-dod.md` when
that file exists — read it and reconcile.

Write them in a "given / when / then" shape or as a plain checkable statement, but consistently within the file.

**Done when:** the coverage requirement above is met, every criterion is observable and binary, and none uses
an unmeasurable adjective.

**Closing gate:** render the drafted criteria and get the user's explicit 確定 before writing the file. This is
the section the customer will be held to at acceptance — it must never be written on the AI's own judgement.
A criterion whose rule is parked in `qa.md` is parked too: mark it, do not invent a criterion for an undecided
rule.

---

## §7 関連ドキュメント

Always include the link back to `../function-list.md`. Add links to related features under `functions/` where
scope adjoins, and to `04_screen-design/screen-list.md` / `03_basic-design/system-design/api-design/api-list.md`
where those entries already exist. Do not fabricate links to documents that have not been written yet.

**Done when:** the table has at least the `function-list.md` row, and every link resolves to a file that exists.

---

## §8 改訂履歴

One row: today's date (`currentDate`), the author, and 初版作成 — or a one-line description of what changed if
you are updating an existing document.

**Done when:** the row is present and dated.

---

## Final gate before writing the file (Step 5)

Refuse to write until all of these hold:

1. Every section satisfies its definition of done above, **and every core section (§3–§6) has passed its closing
   gate** — the user said 確定 on the content as drafted.
2. No section is left as a bare template placeholder. A section that is genuinely blocked is **empty apart from**
   an explicit `<!-- 未確定: qa.md QA-xxx 参照 -->` marker naming the question that blocks it — and that question
   exists as a row in `## 1. Items for Confirmation` of `qa.md`, with a matching entry in `## Open Items` of
   `ba-memory.md`.
3. Nothing in a blocked section pretends to be an answer: no provisional value, no recommended option written in
   "for now", no list of the options. Those ride in the QA row's `Question` cell, where the customer will choose
   between them.
4. Every actor resolves to a `role-list.md` ID, or is recorded as a gap.
5. Every domain term matches `glossary.md`, or has been proposed as an addition to it.
6. No unmeasurable adjective survives anywhere in §4–§6.
7. Nothing in the document contradicts `non-function-list.md`.

---

## Reflecting an answer (Mode B) — propagation checklist

An answer almost never touches one section only. After editing the section resolved in B-1 (the `Reflect into`
cell in `ba-memory.md`, or the QA row's `Subject`) and removing its marker, walk the ripple:

| The answer changed | Re-check |
|--------------------|----------|
| §3 flow, trigger or precondition | §4 (items the new steps consume or produce), §6 (a criterion per new flow), and any §5 rule that referred to the old step order |
| §4 an item or its constraint | §5 (validation on that item), §6 (a criterion that asserts the constraint) |
| §5 a rule — validation, permission, calculation, state transition | §3 (the exception flow when the rule is violated), §4 (constraints the rule implies), §6 (a criterion per rule, and per permission case) |
| §6 a criterion | §5 — a criterion with no rule behind it means the rule was never written down |
| Anything at all | §8 改訂履歴 gets a row naming the QA-ID and the sections touched |

Rules for the ripple:

- Only the sections the answer actually reaches get edited. Do not reopen the whole document because one rule
  changed.
- Anything the ripple newly makes undecided goes through the full decision protocol — three options, a
  recommendation, and `保留（お客様に確認）` — exactly as in a fresh analysis. A follow-up question raised this
  way references its parent QA-ID.
- The feature becomes `✅` only when **no `未確定` marker remains anywhere in the document**. One reflected
  answer out of three still leaves it `⏸ blocked`.
