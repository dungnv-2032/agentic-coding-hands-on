# PostgREST FK inference through a masked view — measured, not assumed

The spec author flagged one fact it could not establish from a spec-author position: whether
PostgREST still resolves the `sender_id → sunners` foreign key when the view exposes that column
through a `CASE` expression. The entire anonymity fix rests on it, so it was tested against the
running local stack over HTTP with the browser anon key, rather than reasoned about.

All probe views were dropped and the one mutated row restored at the end of the run — verified: **0
anonymous rows, 0 probe views remaining.**

## What was run

Four requests through Kong at `127.0.0.1:54321` with the `NEXT_PUBLIC_SUPABASE_ANON_KEY`, against
seeded row `kudos.id = 1`, whose real values are **`sender_id = 1`, `receiver_id = 2`**.

| # | View shape | Request | Result |
|---|---|---|---|
| A | plain `select k.sender_id` | `select=id,sender:sunners!kudos_sender_id_fkey(...)` | **200** — `sender.id: 1`, correct |
| B | `case when is_anonymous then null else sender_id end` | same FK-hinted embed | **PGRST200** — *"Searched for a foreign key relationship between 'probe_masked' and 'sunners' using the hint 'kudos_sender_id_fkey' … no matches were found"* |
| C | same masked view | `select=id,sunners(...)` — hint dropped | **200 — and WRONG.** Returned `sunners.id: 2` |
| D | view pre-joins sender, exposes flat masked columns | `select=id,sender_full_name,receiver:sunners!kudos_receiver_id_fkey(...)` | **200** — sender name flat and correct, receiver embed still resolves |

## The three conclusions

1. **A `CASE`-masked column is not traceable, so FK inference fails.** B settles the spec author's
   question: the answer is no. PostgREST maps view columns back to base columns through the view's
   dependency graph, and an expression is not a column reference.

2. **Case C is the dangerous one, and it must be written down loudly.** Dropping the FK hint does
   not error — it returns `200` with `sunners.id: 2`, which is the row's **receiver** presented in
   the position where the caller asked for the sender. PostgREST fell back to the only traceable FK
   left on the view. An implementer who hits B's error and "fixes" it by removing the hint gets a
   green query, a plausible-looking name, and the wrong person on every card. This is a
   silent-wrong-data failure, not a crash, and no test that merely asserts "a sender name rendered"
   would catch it.

3. **The design must therefore not embed the sender at all.** The view performs the join itself and
   exposes flat, pre-masked sender columns (`sender_id_visible`, `sender_full_name`,
   `sender_avatar_url`, …). D proves this works and — importantly — that the **receiver** embed keeps
   working, because `receiver_id` stays a plain traceable column. So only the sender relationship
   changes shape; the rest of the query is untouched.

## The hole itself, demonstrated rather than asserted

With `kudos.id = 1` temporarily flipped to `is_anonymous = true`, the same anon key that ships to
every browser returned, from the **base table**:

```
GET /rest/v1/kudos?select=id,is_anonymous,sender_id&id=eq.1
[{"id":1,"is_anonymous":true,"sender_id":1}]
```

That is the sender of an anonymous Kudos, disclosed to an unauthenticated caller. Through the
candidate view, the same row returns:

```
GET /rest/v1/probe_flat?select=id,is_anonymous,sender_id_visible,sender_full_name,anonymous_name&id=eq.1
[{"id":1,"is_anonymous":true,"sender_id_visible":null,"sender_full_name":null,"anonymous_name":"Người giấu tên"}]
```

The mask holds over the wire, and `anonymous_name` still comes through so the card can render its
alias. This is the difference between anonymity as a rendering convention in `view-model.ts` and
anonymity as a property of the data the client is able to fetch.

## Consequence for the blueprint

- The reader view exposes **flat masked sender columns**, never a maskable FK column intended for
  embedding. `receiver_id` stays plain.
- The migration must include `notify pgrst, 'reload schema'` (or the equivalent), since PostgREST
  caches the schema and the probe needed a reload before the new view was visible.
- The caller-identity predicate belongs inside the view's `CASE`, so "unless the caller is the
  sender" is evaluated per row by the database, not by the application.
- A test must assert the sender is the **right** person, not merely that a name is present —
  case C would pass the weaker assertion.

## Note on view security semantics

A view created without `security_invoker = true` runs with the privileges of its owner, so the
underlying `kudos` RLS is not re-applied through it. That is the intended behaviour here (the board
is public read by design, and the view *is* the narrowing), but it means the view's own `CASE` is the
only thing standing between a caller and the sender column — which is why the predicate must live in
the view and not in application code.
