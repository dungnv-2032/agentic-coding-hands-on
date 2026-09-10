# Clarifications — Open secret box (chưa mở)

**MoMorph refs**
- Open secret box- chưa mở: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/J3-4YFIpMM
- fileKey: `9ypp4enmFmdK3YAFJLIu6C` · screenId: `J3-4YFIpMM` · frame `1466:7676`
- Specs: 4 rows (A_Title, B_Group 396, C_Box image, D_Số box chưa mở) · Test cases: 19
- testPolicy: **e2e-red-first** (behavioral: click→open state transition, modal close, counter mutation; `@playwright/test` is an existing project runner)

## Session 2026-09-10

The commission instructed: resolve every open question automatically with the first /
recommended answer, no confirmation round. Each line below is a decision taken under that
standing instruction, not a question still open.

- Q: The spec CSV calls the title `MỞ SECRET BOX THÀNH CÔNG`, but the rendered frame draws
  `KHÁM PHÁ SECRET BOX CỦA BẠN` and the instruction line `Click vào box để mở` (the CSV says
  `Click vào box để tiếp tục mở`). Which wins? → A: **The frame wins.** `get_node` on
  `1466:7678` / `1466:7683` returns the two strings verbatim from the design; the CSV prose was
  written against the *đã mở* sibling and leaked into this row. MoMorph design data is
  authoritative (momorph-development.md rule 1), and node text is the most direct form of it.
- Q: Where does this screen live in the app? → A: **`/kudos/secret-box`**, the route the shipped
  Kudos sidebar already links to (`kudos-sidebar.tsx`, asserted by e2e K-19). It renders
  `ComingSoon` today; this commission replaces that placeholder, exactly as F004→F005/F006/F007
  each replaced theirs.
- Q: The ACCESSING test case wants the modal closed to anonymous visitors, but `proxy.ts` and
  e2e `K-21` both ratify `/kudos/secret-box` as a public 200. Guard the route? → A: **No proxy
  change.** The route stays public and still returns 200 with a `<main>` and an `<h1>`, so K-21
  survives. Entitlement is enforced *inside* the screen: with no session, or with a session that
  owns no `sunners` row, the box renders inert (no open affordance, instruction line hidden,
  counter `00`) and a sign-in link is offered. "The modal does not open; access is denied,
  unavailable" is satisfied without contradicting a ratified route contract.
- Q: The instruction line hides at 0 unopened boxes, and the box disables. What does an entitled
  user with 0 boxes see? → A: The same inert state as above, minus the sign-in link — title,
  box art, `00`. No error, no redirect, no empty screen.
- Q: Where do the six badges live? → A: **Reuse `rule_items` where `kind = 'collectible_icon'`**
  (the Thể lệ migration already seeds all six with their artwork under
  `public/images/rules/icon-*.png`). A second badge catalogue would be a duplicate source of
  truth. Draw weights are the secret box's own concern, so they go in a new join table
  `secret_box_badge_odds (rule_item_id, weight)` rather than a column bolted onto `rule_items`.
- Q: Weights — 30/25/10/5/20/10 sums to 100. Store as percentages or relative weights? → A:
  **Relative integer weights**, drawn as `random() * sum(weight)`. Percentages that must sum to
  exactly 100 are a constraint the database would have to police on every write; relative
  weights are correct by construction and reproduce the same distribution.
- Q: Client-side or server-side draw? → A: **Server-side only**, in one `open_secret_box()`
  plpgsql function. Two of the 19 test cases (`5cc072ad`, `2e7bec78`) exist precisely to prove
  the client cannot influence the count or the badge. The function resolves the actor from
  `auth.uid()` and takes no identity argument, so forging one is unrepresentable — the idiom
  `create_kudos()` already established.
- Q: `security invoker` or `security definer`? → A: **`security definer`**. Unlike
  `create_kudos()`, this call must decrement a counter on `sunners`, and no UPDATE policy on
  `sunners` exists or should exist — granting one would let any authenticated user write their
  own box count directly through PostgREST, which is the exact attack `5cc072ad` tests. The
  function is the only writer, `search_path` is pinned, and it re-derives the actor internally.
- Q: A freshly signed-up user has no `sunners` row. Provision one here? → A: **Yes**, mirroring
  `create_kudos()`'s provisioning block (Unassigned department, JWT-derived name/avatar). A
  provisioned row starts at `secret_box_unopened_count = 0`, so provisioning grants nothing —
  it only gives the counter something to be zero *on*.
- Q: How does the E2E suite obtain a user who actually owns unopened boxes, given nothing in the
  product grants them yet? → A: **The test setup grants them**, using the local service-role key
  read at runtime from `npx supabase status -o json`. No key is committed, no product code gains
  a test-only branch, and no business rule about *earning* boxes is invented — earning is a
  separate, unspecified commission.
- Q: After a successful open, what does the user see? The sibling *đã mở* / *action bấm mở*
  screens are still `design_status: in_progress` with no spec. → A: **Stay on this screen and
  show the awarded badge inside the box frame**, with the counter decremented — the minimum that
  satisfies `7c3c912f` ("the modal refreshes to display the new badge") without inventing a
  layout for an unspecified frame. The celebration screen is a follow-up commission.
- Q: The profile stats card's Secret Box button is `disabled` with the comment "deferred
  commission". Enable it? → A: **Yes, on one's own profile only** — leaving it inert would make
  the app contradict itself now that the box exists. On another Sunner's profile it stays
  disabled: opening one's own box from someone else's page is not a flow any frame draws.
- Q: Invalid/corrupt badge data (`43badf5d`). → A: The badge always arrives as a `rule_items`
  row selected by the database, so a corrupt id is unrepresentable; the residual case is a
  missing image file, handled by rendering the box art alone rather than a broken `<img>`.

## Unresolved

None. Every gap above was closed under the standing auto-resolve instruction.

## Sign-off — 2026-09-10

- Q: The evidence gate holds a `riskGate.signoffRequired: true` on this change, because it adds a
  migration and the repository's first `security definer` function — a write path that bypasses RLS
  by design. Does the user sign off? → A: **Yes, signed off, commit to `feat/open-secret-box`**
  (no push, no pull request). This was the one decision NOT taken under the session's standing
  auto-resolve instruction: the gate exists so that a privileged change cannot authorize itself, so
  flipping `humanSignedOff` without asking would have forged the very approval it records.
  `evidence/inspection-verdict.json` carries the flag; the gate then returned
  `SEALED (hard) — evidence verified`, exit 0.
