# Option Patterns

The option library that makes the decision protocol cheap to honor. Each entry is a decision that recurs across
almost every feature, with its canonical three shapes, the axis they trade off on, and which document should
decide it.

**How to use this file.** These are starting points, not scripts. Adapt the wording to the actual feature and to
the project's domain before presenting them — an option the user cannot picture in their own system is not a
real option. Never present the three shapes generically ("soft delete") when you can present them concretely
("a deleted order disappears from the list but stays visible to admins for 30 days, then is purged").

**Before you ask.** Check whether `non-function-list.md`, `role-list.md` or an already-analyzed sibling feature
under `functions/` has already decided it. If so, state the answer, cite the source, and move on. Asking a
question the project has already answered wastes the user's attention.

**Recommending.** The "recommend when" column is a heuristic, not an answer. The recommendation must be
justified from *this* project's documents, and stated in one sentence.

---

## The standing fourth option

Every entry in this file is three options. Every question you build from them is **four**: the three, plus
`保留（お客様に確認）` last. It is not a fallback for when the entry does not fit — it is always on the list,
because the person in front of you may simply not have the authority to decide, and a requirement decided by
the wrong person costs more than an open question.

When the user picks it, the three options travel into the `Question` cell of the `qa.md` row **verbatim**,
`<br>`-separated. That register is what the customer reads, so the question has to stand on its own:

- **Business language, no jargon.** The customer has not read the detail document and will not open it.
  「削除した申請を後から元に戻せる必要はありますか」 works; 「論理削除にしますか」 does not.
- **Each option states what the customer would experience**, not what the system does internally. Reuse the
  "What the user experiences" column of these entries — that is exactly what it is for.
- **Name the consequence of each option**, not only the behavior: what it costs, what it makes impossible later.
  A customer choosing between three sentences with no consequences attached will pick whichever sounds nicest.
- **Say what is blocked.** The `Blocking` cell in `ba-memory.md` is how the next session understands why this
  matters enough to chase now.
- **One question, one decision.** Two decisions in one QA row come back as one ambiguous answer.

If the follow-up you must not skip (the last bullet of most entries below) also cannot be decided, fold it into
the **same** QA row — it is part of the same decision, and splitting it produces two questions the customer
cannot answer independently.

---

## 1. Authorization model

*Who is allowed to act on a record.*

| # | Option | What the user experiences |
|---|--------|---------------------------|
| A | **Per-role** — permission depends only on the actor's role | Any manager can edit any record in scope |
| B | **Per-resource-owner** — permission depends on the relationship to the record | Only the creator (or assignee) can edit it, regardless of role |
| C | **Hybrid** — owners act on their own records, elevated roles act on all | Creators edit their own; admins edit anything, with an audit trail |

- **Trade-off axis:** simplicity and predictability vs. precision of control.
- **Decided by:** `role-list.md` (does it define ownership relationships?) and any access-control row in
  `non-function-list.md`.
- **Recommend when:** A if `role-list.md` has few roles and no ownership concept; C once records are personal
  or sensitive and an admin still needs to intervene; B only when admin override is genuinely unacceptable.
- **Follow-up you must not skip:** what a user who lacks permission sees — an error, or no trace of the record
  at all. These differ in what they leak.

---

## 2. Validation timing

*When the user learns their input is wrong.*

| # | Option | What the user experiences |
|---|--------|---------------------------|
| A | **On submit only** | Fill everything, submit, see all errors at once |
| B | **On field exit, plus on submit** | Each field flags itself as you leave it; submit re-checks everything |
| C | **Live as you type, plus on submit** | Feedback per keystroke |

- **Trade-off axis:** immediacy of feedback vs. interruption and noise while typing.
- **Decided by:** usability rows in `non-function-list.md`; the length and complexity of the form in §4.
- **Recommend when:** B for most forms — errors surface early without punishing half-typed input; A for very
  short forms; C only for fields with a rule the user must satisfy incrementally (password strength, an
  availability check on a chosen ID).
- **Always true regardless of the choice:** server-side validation happens on submit. That is a security
  property, not a UX option — never present "client-side only" as an option.

---

## 3. Error surfacing

*How a failure is communicated.*

| # | Option | What the user experiences |
|---|--------|---------------------------|
| A | **Inline, next to the field** | The message sits beside the offending input |
| B | **Summary banner at the top** | One block lists every problem, with links to the fields |
| C | **Blocking dialog** | A modal must be dismissed before continuing |

- **Trade-off axis:** locality of the fix vs. certainty the user noticed.
- **Decided by:** whether the error is per-field (A), whole-form (B), or destructive/irreversible (C).
- **Recommend when:** A for field-level validation, usually combined with B when the form is long enough that
  an error can scroll out of view; C only when proceeding would lose data or trigger something irreversible.

---

## 4. List retrieval

*How a collection is presented when it grows.*

| # | Option | What the user experiences |
|---|--------|---------------------------|
| A | **Paginated** | Numbered pages, fixed page size, a total count |
| B | **Infinite scroll / load more** | Rows append as the user scrolls |
| C | **Load everything** | The whole set at once, filtered client-side |

- **Trade-off axis:** predictable navigation and a stable total vs. fluid browsing.
- **Decided by:** the expected volume — ask for the realistic maximum row count if `non-function-list.md` does
  not state it — plus any response-time row there.
- **Recommend when:** A when the user needs to navigate to a known position, cite a total, or export a page —
  and for anything administrative; B for feeds and search results browsed casually; C only when the set is
  bounded and small (say, under a few hundred rows) and stays that way.
- **Follow-up you must not skip:** the default sort order, and what happens when the set is empty.

---

## 5. Destructive actions

*What "delete" actually means.*

| # | Option | What the user experiences |
|---|--------|---------------------------|
| A | **Hard delete** | The record is gone permanently and immediately |
| B | **Soft delete** | It disappears from normal views but is still retrievable by an administrator |
| C | **Archive with restore** | The user moves it to an archive they can browse and restore from themselves |

- **Trade-off axis:** cleanliness and privacy compliance vs. recoverability from mistakes.
- **Decided by:** data-retention and personal-data rows in `non-function-list.md` — these can make A mandatory
  (a deletion right) or forbid it (an audit obligation). Check before offering.
- **Recommend when:** B for most business records — mistaken deletion is common and recovery is cheap; C when
  users routinely remove things they later want back; A when retention rules require genuine erasure.
- **Follow-up you must not skip:** the retention period before purge (a number, not "a while"), whether related
  records cascade, and whether the deletion is audit-logged.

---

## 6. Concurrent edits

*What happens when two people edit the same record.*

| # | Option | What the user experiences |
|---|--------|---------------------------|
| A | **Last write wins** | The later save silently overwrites the earlier one |
| B | **Optimistic locking** | The later save is rejected with "this was changed by someone else"; the user reloads and reapplies |
| C | **Pessimistic locking** | Opening for edit locks the record; others see it as locked and by whom |

- **Trade-off axis:** simplicity vs. protection against silent data loss.
- **Decided by:** how many roles in `role-list.md` can edit the same record, and whether the data is one users
  would notice losing.
- **Recommend when:** B when more than one person can realistically edit the same record — silent loss is the
  worst failure mode and B is cheap; A when edits are effectively single-user; C only for long-form work where
  losing an edit session is expensive, and only with a lock timeout decided alongside it.
- **Follow-up if C:** how long the lock lasts, and who can break it.

---

## 7. State modelling

*How a record's lifecycle is represented.*

| # | Option | What the user experiences |
|---|--------|---------------------------|
| A | **Boolean flags** | Independent switches (approved / published / cancelled) |
| B | **Explicit status enum** | One named status at a time, with defined legal transitions |
| C | **Status plus an event log** | A current status, and a full history of who changed it, when and why |

- **Trade-off axis:** ease of modelling vs. ability to answer "how did it get here?".
- **Decided by:** audit rows in `non-function-list.md`; whether §3 has an approval, review or cancellation flow.
- **Recommend when:** B for almost anything with a lifecycle — flags drift into impossible combinations
  (approved *and* cancelled) that nobody defined; C when there is an approval chain or an audit obligation; A
  only for genuinely independent attributes.
- **Follow-up if B or C:** the full list of statuses, the legal transitions between them, and who may perform
  each transition. Record this as a table in §5 — it is business logic, not a design detail.

---

## 8. Notification timing

*When someone is told that something happened.*

| # | Option | What the user experiences |
|---|--------|---------------------------|
| A | **Synchronous** | The notification is sent during the action; a send failure fails the action |
| B | **Queued** | The action completes immediately; the notification goes out shortly after and retries on failure |
| C | **Batched digest** | Events accumulate and are delivered on a schedule |

- **Trade-off axis:** immediacy vs. resilience and recipient attention.
- **Decided by:** response-time and availability rows in `non-function-list.md`; the urgency of the event.
- **Recommend when:** B for nearly everything — the user should not wait on an email server, and a failed send
  should not fail their work; C for high-frequency, low-urgency events where per-event delivery becomes noise;
  A only when the action is meaningless unless the recipient is notified right now.
- **Follow-up you must not skip:** what happens after repeated delivery failure — is it visible to anyone, or
  does it disappear silently?

---

## Adding to this file

When a decision comes up that is not here and will clearly recur across features, add it in the same shape:
three named options with what the user experiences, the trade-off axis, the document that decides it, and a
"recommend when" heuristic. Keep entries about **business behavior**, not implementation technique — this file
is read while writing requirements, not code.

A decision that ends up parked in `qa.md` more often than it gets decided in the room is a strong candidate:
write it here so the next feature can raise the customer question in one step instead of rediscovering the
options.
