# Clarifications — Profile bản thân (F006 / SCR006)

- MoMorph screen: `Profile bản thân` — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/3FoIx6ALVb
- figma node: `362:5037` · 28 specs · 30 test cases
- Design artifacts: `design/specs.csv`, `design/test-cases.csv`, `design/profile.png`
- testPolicy: **`e2e-red-first`** — the screen is dominated by behaviour (route guard, `?id=`
  resolution, a direction dropdown with state, infinite scroll, heart toggle, navigation out).
  Nothing here is a static mapping.
- Discipline: `--auto`. The commission says *"tự động triển khai theo hướng câu trả lời đầu tiên,
  Yes hoặc câu trả lời Recommend mà ko cần hỏi lại"* — every gate below is resolved by taking the
  first/Yes/Recommended option, without asking again.
- Supabase: **local project** (`supabase/migrations`, `supabase/seed.sql`), as instructed.

## Session 2026-09-08

### The three authored premises that do not hold in this repository

The 30 test cases are unusually specific and cite internals by name — but three of those citations
describe a codebase this repo is not. The **requirement** in each case is authoritative; the
**mechanism** is translated to what actually exists here. This is recorded first because it changes
what several test cases mean.

- Q: TC_ACC_001 says `/profile` is private because it is "absent from `PUBLIC_ROUTES` in proxy.ts".
  There is no `PUBLIC_ROUTES` in `proxy.ts` — it carries the *inverse*, an explicit allowlist of
  *guarded* prefixes (`/todo`, exact `/kudos/new`), and everything else falls through public. So
  `/profile` is **currently public** and renders `ComingSoon`. Invert the list, or add `/profile`
  to the guarded allowlist?
  → A: **Add `/profile` to the guarded allowlist** (exact path + `/profile/` subpath, the same
  shape `/kudos/new` already uses). Recommended: inverting to a public-route list would move every
  existing route's access decision in a commission about one screen, and F004's public board
  (`/kudos`, `/kudos/[id]`, `/kudos/secret-box`) is a *ratified* public read path — an inversion
  puts all of it one editing mistake away from being guarded.

- Q: TC_FUN_001–005 treat the profile id as a **UUID** (`?id=99999999-9999-4999-8999-999999999999`,
  "a non-UUID sent to a uuid column raises Postgres 22P02"). This repo's person entity is
  `public.sunners` with `id bigint generated always as identity` — there is no uuid-keyed `profiles`
  table. Keep the UUID contract, or translate to bigint?
  → A: **Translate to bigint.** `?id=` is shape-checked against `/^\d{1,18}$/` before any query is
  issued; anything else (`banana`, `' or 1=1`, `42.5`, a truncated uuid) returns 404. The *defence*
  the test case asks for is preserved exactly — a malformed id never reaches Postgres, so
  `invalid input syntax for type bigint` can never surface as a 500 — only the type changes.

- Q: TC_FUN_001's note sources the `?id=` link to `app/kudos/use-board-interactions.ts -> openProfile`.
  No such file and no such link exist: every `/profile` link in the repo is a **bare** `href="/profile"`
  (`sunner-chip.tsx:69`, `gift-leaderboard.tsx:57`, `account-menu.tsx:93`), and
  `e2e/kudos-live-board.spec.ts:354,356` asserts that exact value. Support `?id=` on the route only,
  or also make the board emit it?
  → A: **Both.** A profile route that nothing links to is dead surface, so `sunner-chip` and
  `gift-leaderboard` start emitting `/profile?id={sunnerId}`. F004's two assertions are amended from
  `toHaveAttribute("href", "/profile")` to a `/profile\?id=\d+$` pattern — a *narrowing*, recorded
  here as a deliberate amendment to a ratified test, never a silent relaxation.

### Route and access

- Q: What guards `/profile` — the proxy only, or the page too?
  → A: **Both.** The proxy redirect is the gate; the page re-resolves the session itself and
  redirects on absence. TC_ACC_001's own note asks for exactly this ("the page also re-checks the
  session itself as defense in depth, so this holds even if the proxy route list is edited").
- Q: `?id=` naming the viewer themselves (FUN_002)?
  → A: **Canonicalize to the SELF view** — identical to `/profile` with no query string: statistics
  card (not a write bar), first-person badge heading, both dropdown directions.
- Q: `?id=` well-formed but matching no `sunners` row (FUN_003)?
  → A: **`notFound()`** — the 404 page, never a 500 and never a half-rendered profile.
- Q: `?id=` empty, repeated, or accompanied by unknown params (FUN_005)?
  → A: Empty (`?id=`) → **self view** (a cleared query string is not an error). Repeated
  (`?id=1&id=2`) → **404**; choosing one of two different ids would hide the caller's mistake.
  Unknown params → **ignored, self view**. That last one is load-bearing and is *not* in the test
  cases: `kudos-hero.tsx:77` ships a live GET form with `action="/profile"` and `name="q"`, so
  `/profile?q=anything` is already a reachable URL today. Returning 404 for an unrecognised param
  would turn the shipped Sunner-search box into a 404 generator. (Building the search *result* is a
  separate commission; this screen only refuses to break it.)

### Viewer identity

- Q: `resolveViewer()` returns `sunnerId: null` for a signed-in session with no `sunners` row — and
  the e2e auth setup signs up a brand-new user every run, so that is the *normal* case, not an edge
  one. `sunners` rows are only provisioned by `create_kudos()` on first write. Does the self view
  404, or provision a row on read, or render without one?
  → A: **Render without one** — name and avatar from the JWT via the same fallback chain
  `create_kudos()` already uses (`user_metadata.full_name` → `.name` → email local-part;
  `avatar_url` → `picture` → the sample avatar), zero counters, empty feeds, six greyed badge slots,
  no tier badge and no stars. Recommended over the alternatives: a 404 for a legitimately signed-in
  user is wrong, and provisioning a row would make a GET perform a write. This is also exactly the
  `GUI_009` sparse-profile rendering path, so one code path serves both.
  **Note the email nuance:** the third fallback is the email *local-part*, not an address — the same
  value `create_kudos()` already stores — so a name identical to the one a write would have produced
  is shown, while `SEC_004`'s "no email address in the payload" still holds.

### Statistics card (mms_B)

- Q: How are the five counters derived, given F004's baseline idiom?
  → A: Follow the shipped idiom so the board and the profile can never disagree:
  received = `sunners.kudos_received_baseline + count(kudos where receiver_id = me)`;
  sent = `count(kudos where sender_id = me)` (there is no sent baseline column);
  hearts received = `sum(heart_baseline + count(kudos_likes))` over the Kudos I received.
- Q: GUI_004 wants each value to be "the viewer's actual counters", GUI_005 wants both Secret Box
  rows to read 0. Hardcode 0, or read the columns?
  → A: **Read the real columns** (`secret_box_opened_count`, `secret_box_unopened_count`). These are
  not in conflict: both columns default to 0, and a session with no `sunners` row reads 0 for both,
  so the e2e viewer genuinely shows `0`/`0` without a single hardcoded number.
- Q: The `Mở Secret Box` button (mms_B.6)?
  → A: **Rendered and `disabled`**, exactly as the board sidebar's deferred prize rows — the honest
  rendering of a deferred feature. Clicking does nothing: no dialog, no navigation, no error.

### Badge collection and hero tier

- Q: TC_GUI_001's note says the Hero tier is keyed on **distinct senders** while the hoa-thi stars
  are keyed on **total received** (10/20/50). `lib/kudos/derive.ts:badgeTierFor()` — shipped and
  ratified in F004 — keys the tier on **total received** at those same 10/20/50 thresholds. Follow
  the note, or the shipped function?
  → A: **The shipped function.** `badgeTierFor()` is reused untouched. A Sunner showing `Super Hero`
  on the live board and `Rising Hero` on their own profile would be a defect, and there is one
  function for one rule (DRY). The note is recorded as not honoured, deliberately.
- Q: The hoa-thi stars, then?
  → A: **Derived from the tier**, not from a second count: `starCountFor(tier)` → 0/1/2/3. Since the
  tier already uses the 10/20/50 thresholds the note assigns to the stars, deriving stars from the
  tier satisfies the requirement and makes the two structurally incapable of disagreeing.
- Q: The six badge slots B2–B7 (GUI_002)?
  → A: **All six rendered, all desaturated**, in the design's fixed order, using the real badge
  artwork rather than blank placeholders — driven by an `unlockedBadgeIds` list that is always empty
  today, so a slot lights up later with no reshaping. No slot hidden, none unlocked.
- Q: The badge-row heading (GUI_003)?
  → A: **First-person on the self view** (`Bộ sưu tập icon của tôi` / `My icon collection`), neutral
  on another's (`Bộ sưu tập icon` / `Icon collection`). Two distinct keys, parity-gated.

### KUDOS section

- Q: Dropdown contents per face of the route (FUN_009 / SEC_001)?
  → A: Self view → **both** `Đã nhận (N)` and `Đã gửi (M)`, Received active first, trigger showing
  the *active* direction. Another Sunner's profile → **Received only**; no `Đã gửi` option, label or
  count anywhere on the page.
- Q: Why is that a security case rather than a display choice?
  → A: Because their sent count includes Kudos they sent **anonymously**, which no feed will ever
  show. Publishing that number — or a Sent list that contradicts it — discloses how many anonymous
  Kudos they sent. The leak is closed by **removing the surface**, not by adjusting the count.
- Q: My own Sent list and my own anonymous Kudos (SEC_002)?
  → A: The Sent list **includes** them and shows **me** as the author (the masked alias is for other
  people's view of them, not mine), while still marking them as sent anonymously. A naive
  `sender_id = me AND NOT is_anonymous` filter would silently under-report against the counter
  printed beside it.
- Q: Card shape in the feed (GUI_006)?
  → A: **The board's mapper, unchanged** — same column list, same masking, same heart/Copy-Link
  behaviour, so the two surfaces cannot diverge. An anonymous sender on a *Received* list renders the
  masked alias, with identity, department and counters all withheld.
- Q: Paging (FUN_013), direction switch (FUN_010/011), empty states (FUN_012)?
  → A: Infinite scroll, 10 at a time, reusing `FEED_PAGE_SIZE` and a keyset cursor so no card is
  duplicated or skipped; end-of-feed message on the last page. Switching direction loads page 1 of
  the new list and **discards** the pages accumulated for the old one, with the trigger label
  updating only once the new page has actually loaded. Re-picking the active direction is a
  **no-op** — no request, no blank list. Each direction has its **own** empty copy (received:
  `Hiện tại chưa có Kudos nào.`, verbatim from the board; sent: `Bạn chưa gửi Kudos nào.`).
- Q: Card interactions (FUN_014 / FUN_015)?
  → A: Heart reuses F004's existing server action **untouched** and stays server-authoritative — the
  count shown is the one the server reports, never a locally incremented one (this is the K-25
  lesson from F004, recorded in `plans/260906-1945-kudos-live-board/`). Hearting your own Kudo is
  refused with the board's message. A hashtag click navigates to the board filtered by that tag —
  the profile has no hashtag filter of its own. Copy Link reuses the board's toast.
- Q: The orange Spam chip (mms_D.3.1_Status, GUI_007)?
  → A: **Never rendered.** No moderation model exists in the schema or the specs. A typed `status`
  field is carried on the card shape so the chip can be switched on later without reshaping anything.

### Write-Kudo bar (the other face of mms_B)

- Q: What occupies the statistics slot on another Sunner's profile (FUN_006)?
  → A: The **whole** statistics card is replaced by a write-Kudo bar naming them
  (`Gửi lời cảm ơn và ghi nhận đến {name}`). No counter row and no `Mở Secret Box` button appears
  anywhere on that page. Driven by **one** data-level branch — `stats` is null for anyone but the
  caller — so the self/other distinction is decided once, in the data layer, not re-tested in each
  component.
- Q: FUN_007 says the bar "opens the existing Viet Kudo modal" with the recipient prefilled. F005
  shipped Viết Kudo as a **page** (`/kudos/new`), not a modal.
  → A: Translate to the page: the bar links to **`/kudos/new?receiverId={id}`**, which preselects
  that Sunner as recipient, leaves the field **editable**, and does **not** pop the suggestion list
  open over an untouched field. Implemented as an optional prop defaulting to null so the homepage
  and board compose entries are unchanged.
- Q: A write-Kudo bar on your own profile (FUN_008)?
  → A: **None** — the statistics card holds that slot instead. FUN_008's note claims the database
  also refuses a self-Kudo via `kudos_no_self`; **no such constraint exists in this repo** —
  neither `20260906140914_kudos_live_board.sql` nor `20260907025909_viet_kudo_write_path.sql`
  defines it, and `create_kudos()` does not compare receiver to sender. So the refusal here is the
  surface declining to invite the attempt, and nothing more. Logged as advisory **ADV-2** rather
  than fixed inside this commission: adding a check constraint to F005's table is a change to
  another feature's schema and wants its own pass over the seed data first.

### Security — the finding that changes the design

- Q: SEC_001 hides another Sunner's sent count so that anonymous sends cannot be counted. Does the
  data layer actually support that claim today?
  → A: **No — and this is the most important thing found in this study.** `kudos_select_all` is
  `for select to anon, authenticated using (true)`, and `queries.ts:fetchKudos` embeds
  `sender:sunners!kudos_sender_id_fkey(...)` for *every* row including anonymous ones. Masking
  happens in `view-model.ts`, at the **render** layer. Anyone holding the anon key — it ships to the
  browser by design — can issue `select sender_id, is_anonymous from kudos` and de-anonymize every
  anonymous Kudos in the table. Hiding a count in the UI while that query is open is theatre, and
  shipping SEC_001 on top of it would be a security control that does not hold.
  → A (decision): **Close it in this commission**, because the fix is bounded and this screen's two
  headline security cases are false without it. A `security definer` reader view exposes
  `sender_id` (and the sender embed) as NULL for an anonymous Kudos unless the caller *is* the
  sender; direct `select` on `public.kudos` is revoked from `anon` and `authenticated`; the **three**
  existing `.from("kudos")` call sites (`lib/kudos/queries.ts:53`,
  `app/kudos/_actions/toggle-kudos-like.ts:26,73`) are repointed at the view. Three call sites is
  the whole blast radius — measured, not estimated. This makes SEC_001 and SEC_002 true statements
  about the system rather than about the markup.
- Q: Does anything else pair an identity with a Kudos and re-open the same hole?
  → A: `spotlight_ticker_events` carries `(sunner_id, kudos_id)` under a `using (true)` select
  policy, which would re-derive the sender of an anonymous Kudos by join. The planner must check
  the seeded rows and either exclude anonymous Kudos from that table or mask the pairing. Carried as
  a **blocking design question for the blueprint**, not an advisory.
- Q: Any write or edit surface on this screen (SEC_004)?
  → A: **None.** Read-only apart from F004's pre-existing heart action. No edit affordance on name,
  avatar or department on either face of the route — editing is ruled out even though the schema
  permits it. Only the allowed profile columns are ever selected; `resolveViewer().userId` stays
  server-only exactly as F004 guarantees, so no auth uuid and no email address reaches the payload.

### Localization

- Q: GUI_008 and GUI_003 place the copy in `locales/{vi,en}/profile.json` with "key-set parity
  asserted by an automated test". This repo has no `locales/` directory — copy lives in
  `lib/i18n/messages/{vi,en}-*.ts` behind the `Dictionary` interface.
  → A: Use the repo's mechanism: a `profile` block on the `Dictionary` interface, with
  `lib/i18n/messages/vi-profile.ts` and `en-profile.ts`. The parity requirement is satisfied more
  strongly than the test case asks — a key present in one locale and missing from the other is a
  **compile error** under `npm run typecheck`, not a runtime blank caught by a test. Counts and the
  recipient name are substituted through the same interpolation the board already uses, and the
  statistics labels match the board sidebar's wording.

### Assumptions (not derivable from the design; recorded for the record)

- **A1** — `?id=` is the `sunners.id` bigint. The design shows no URL, so the parameter name and
  type come from this repo's schema and from the test cases' intent, not from the frame.
- **A2** — Stars are derived from the tier rather than counted separately (see above). If a later
  commission gives the tier a different denominator, `starCountFor` must be revisited with it.
- **A3** — The six badge slots' artwork order is taken from the frame's node order B2→B7. No spec
  row names the individual badges, so the order is the design's, and it is fixed.
- **A4** — A signed-in session with no `sunners` row renders a zero-state self profile rather than
  404. No test case covers this because the authored preconditions all assume a roster row; the e2e
  auth setup makes it the common case.
- **A5** — `/profile?q=…` (the shipped Sunner-search form's target) renders the self view. The
  search-results screen is a separate commission.

### Resolved against the live database (2026-09-08, before blueprinting)

The blocking question above was answered by querying the running local Supabase rather than reasoning
about the SQL. Every number below is a measured `select`, not an estimate:

| Probe | Result | What it settles |
|-------|--------|-----------------|
| `spotlight_ticker_events` total rows | 7 | — |
| rows whose `sunner_id` = the Kudos' **receiver** | **7 / 7** | `sunner_id` is *always* the receiver |
| rows whose `sunner_id` = the Kudos' **sender** | **0** | the pairing cannot expose a sender |
| rows joined to an anonymous Kudos | 0 | no live leak today (`is_anonymous` count is 0) |
| `kudos` rows with `sender_id = receiver_id` | 0 | a `kudos_no_self` constraint would apply cleanly |
| constraints on `public.kudos` | `heart_baseline_check`, `pkey`, `sender_id_fkey`, `receiver_id_fkey`, `message_format_check` | **no** `kudos_no_self` — ADV-2 confirmed |
| distinct `(opened, unopened)` Secret Box pairs | `0/0` × 14 sunners, `25/25` × 1 | GUI_005 holds by reading the real columns |

→ **`spotlight_ticker_events` needs no change.** It names receivers, and a receiver is public on an
anonymous Kudos anyway — only the sender is masked. The blueprint must instead record the *invariant*
("`sunner_id` is the receiver") so a later writer does not put a sender there and quietly re-open the
hole. Question 1 is closed; it is not a blueprint input any more.

→ The `25/25` row is the frame viewer (Huỳnh Dương Xuân Nhật), whose seeded counters are the frame's
verbatim `25`s. So the statistics card shows `0`/`0` for the e2e viewer and `25`/`25` on that
Sunner's profile — both correct, neither hardcoded.

### Amendments from the measured visual study (2026-09-08, `reports/momorph-visual-study.md`)

The MoMorph study measured the frame node-by-node and came back with three facts that **retire two
decisions recorded above**. They are amended here rather than edited in place, so the change of mind
stays visible. (Standing rule in this project: an implementer disagreeing with the orchestrator on a
*measured* fact has been right every time. These are measured.)

- **AMEND-1 — the hoa-thị stars do not exist in this design.** `mms_A.2_Name` (`362:5054`) contains
  exactly four things: the name (`362:5055`), the department (`362:5057`), a 4×4 separator dot
  (`362:5060`) and **one** tier-badge pill instance (`3053:6061`). There is no star node anywhere on
  the row. → **The stars are not implemented.** `TC_GUI_001`'s "hoa-thị stars on one row" is recorded
  as **not sourceable from the design authority**, and `TC_GUI_009`'s "no hoa-thị stars" is satisfied
  trivially. This **retires decision D11 and assumption A2** — there is no `starCountFor(tier)`, and
  the tier badge alone carries the received-count signal. Less invented surface, and the frame is
  the authority on what renders.
- **AMEND-2 — the badge slots carry no artwork, and they live inside the hero.** All six slots
  (`362:5066`–`362:5071`) render an identical flat `#323231` circle: 64×64, `border: 2px solid #FFF`,
  `border-radius: 100px`, 16px gap, fixed order left→right. `list_media_nodes` found 30 media nodes
  on the frame and **none** of them is a badge. → **Implement exactly that:** six flat grey circles.
  `TC_GUI_002`'s "6 slots, fixed order, all locked, none hidden, none unlocked" is fully satisfied;
  its "showing its real badge image desaturated" is **not**, because no such image exists to
  desaturate. Inventing badge artwork would be inventing design data. Also: region `A.3` is a *child*
  of `mms_A_Info` (`362:5052`), so the badge row sits **inside** the hero identity block directly
  under the name — not in a separate section below it, as `GUI_002`'s step wording implies.
- **AMEND-3 — the feed card is full reuse, not a new token.** The study flagged `#FFF8E1` as possibly
  new; it is not. `app/kudos/_components/kudos-card.tsx:114` already renders `bg-[#FFF8E1]`, the same
  value the frame measures. → `TC_GUI_006` ("identical in shape and behaviour to the same Kudo on the
  live board") holds with **zero** conflict: the board's card component is reused outright.
- **Recorded so nobody "corrects" it back:** the frame's dropdown trigger (`362:5089`) is captured
  showing `Đã gửi (5)`. That is the mock's state, not the default. `TC_FUN_009` mandates **Received**
  active first, and the test case governs behaviour where the frame only captures one moment.

Everything else in the study corroborated the plan: the statistics card's tokens
(`#998C5F` border, `#00070C` fill, `rounded-[17px]`, the `#2E3940` divider, the 22px white label /
32px `#FFEA9E` value rows) and the `Mở Secret Box` button are **already implemented verbatim** in
`kudos-sidebar.tsx`, so the card is a re-layout of shipped parts at 680px rather than new work.

### Resolved by probe: the reader view exposes flat sender columns, never an embeddable FK

The spec author correctly refused to assert whether PostgREST can still resolve
`sender:sunners!kudos_sender_id_fkey(...)` through a `CASE`-masked `sender_id`, and flagged it for
verification. It was tested over HTTP against the running stack with the browser anon key — full
evidence in `reports/orchestrator-postgrest-masked-view-probe.md`. Three results:

- A `CASE`-masked column is **not** traceable to its base column, so the FK-hinted embed fails with
  `PGRST200`.
- **Dropping the hint does not error — it returns the wrong person.** On `kudos.id = 1`
  (`sender_id = 1`, `receiver_id = 2`), the un-hinted embed returned `sunners.id: 2`: PostgREST fell
  back to the only traceable FK left and presented the **receiver** where the sender was asked for.
  A green query, a plausible name, the wrong human. Any implementer who "fixes" the `PGRST200` by
  removing the hint ships that.
- → **Decision:** the view performs the sender join **itself** and exposes flat, pre-masked columns
  (`sender_id_visible`, `sender_full_name`, `sender_avatar_url`, …). Probed working, and the
  **receiver** embed keeps resolving because `receiver_id` stays a plain column — so only the sender
  relationship changes shape. The migration must also `notify pgrst, 'reload schema'`, and the
  caller-identity predicate lives inside the view's `CASE` so the database evaluates it per row.
  A test must assert the sender is the **right** person, since the weaker "a name rendered"
  assertion passes the broken case.

The same probe **demonstrated the hole** rather than asserting it: with one row flipped to
`is_anonymous`, the anon key read `{"id":1,"is_anonymous":true,"sender_id":1}` straight off the base
table. All probe views were dropped and the row restored (verified: 0 anonymous rows, 0 probe views).

### Accepted correction from the spec author

The brief told the author to continue a global FR/BR numbering series from F005. It measured all five
shipped `functional-spec.md` files, found that **each restarts locally**, and used per-feature
numbering instead — flagging the conflict rather than silently picking one. That is the right call
and the repo's actual convention; the brief was wrong. Recorded because it is the fourth time in this
project an agent has corrected the orchestrator on a measured fact and been right.

### CORRECTION — the revoke's blast radius was wrong, and it was my error

Recorded above, in the security decision: *"the **three** existing `.from("kudos")` call sites … Three
call sites is the whole blast radius — measured, not estimated."* **That claim is wrong.** It was
measured at the **application** layer (a grep for `.from("kudos")`) and then asserted as if it covered
the database. The blueprint measured the SQL layer and found four more dependants. Verified
independently before accepting the correction:

```
psql:  revoke select on public.kudos from anon, authenticated;
       set local role authenticated;
       insert into public.kudos_likes (kudos_id, user_id) values (1, …);
ERROR: permission denied for table kudos
HINT:  Grant the required privileges to the current role with: GRANT SELECT ON public.kudos TO authenticated;
```

Three INSERT policies join `public.kudos` inside their own `WITH CHECK`
(`kudos_likes_insert_own`, `kudos_hashtags_insert_own`, `kudos_attachments_insert_own`), and RLS
policy expressions evaluate with the **caller's** privileges — so revoking the caller's `select`
disarms the policy that depends on it. Separately, `create_kudos()` is deliberately
`security invoker` and ends in `INSERT … RETURNING id`, which needs `select` on the returned column.
So the naive revoke would have taken down **F004's heart toggle** — the very action this feature
reuses "untouched" — and **F005's entire write path**.

One refinement found while verifying, which matters for the implementer: the proposed
`grant select (id)` is **not sufficient on its own**. Re-running P1 with only that grant still fails,
because `kudos_likes_insert_own` reads `k.sender_id` as well as `k.id`. The load-bearing half of the
fix is the `security definer public.is_kudos_sender(bigint)` helper, which moves the policy's read
*inside* a definer boundary so the policy stops touching `public.kudos` as the caller at all; the
column grant exists only for `RETURNING id`. With both in place the privilege barrier is gone — the
same two statements then fail only on a synthetic uuid absent from `auth.users`, which is my probe's
limitation, not the fix's. Phase 03's acceptance probes must therefore run as a **real** signed-up
user, not a fabricated uuid.

And the control does what it is for: under the revoke, as `anon`, **both**
`select count(*) from kudos where sender_id = 1` and even `select id from kudos limit 1` return
`permission denied`. The de-anonymization query is closed, not narrowed.

*(Fifth time in this project an agent has corrected the orchestrator on a measured fact and been
right. The pattern is specific: the correction is always from someone who ran the thing. "Measured"
is only true of the layer you actually measured — I measured TypeScript and wrote it down as if I
had measured Postgres.)*

### Answers to the blueprint's four open questions (auto-resolved: first / Yes / Recommended)

- **FR-602's "internal marking" of my own anonymous sent Kudo** → **Accept the planner's reading.**
  `KudosCardView` gains `sentAnonymously: boolean` and it renders **nothing**. The frame has no such
  element and AMEND-3 mandates full card reuse, so a visible chip would be inventing design data —
  the same reasoning that retired the stars and the badge artwork. Observability is Sent-list count
  parity, which is what `SEC_002` actually asserts.
- **SEC_002's coupling to F005's compose flow** → **Accepted.** A fresh e2e user has no `sunners` row
  and no sent Kudos, so the only honest path to a populated Sent list is composing an anonymous Kudo
  through `/kudos/new` first. A test that fabricated the row directly would not be exercising the
  system. One isolated test with runtime-resolved cleanup, and the coupling documented.
- **`Mở Secret Box` is not literal reuse** → **Accepted, and the visual study's wording is corrected
  here:** the *pixels* are already implemented verbatim in `kudos-sidebar.tsx`; the *behaviour* is
  not. The board ships `<a href="/kudos/secret-box">` (asserted by K-19); this screen requires a
  `disabled` no-op per `GUI_005`. Reuse the styling, distinct testid, no shared component.
- **Advisories** → **Carried, not fixed:** ADV-1 (two paging strategies now coexist), ADV-2 (no
  `kudos_no_self`), ADV-3 (no composite `(receiver_id, sent_at desc, id desc)` index — unnecessary at
  57 seeded rows). None blocks delivery; all three are named so a later reader inherits them
  deliberately rather than by accident.

### Two blueprint findings that change shipped behaviour (accepted)

- **`/kudos` reads no query string.** `kudos-board.tsx:61` holds `hashtagFilterId` in `useState`, so
  a `Link href="/kudos?hashtag=X"` would land on an **unfiltered** board. FR-405's hashtag navigation
  therefore requires a deliberate `useSearchParams` read defaulting to `null`, and its assertion must
  check the board's **filter state**, not the URL — a URL-only assertion would pass a half-truth.
  (Same failure shape as F004's K-21, which passed against Next's 404 page by asserting only the URL.)
- **`GiftRowView` carries no sunner id.** `fetchGifts` selects `sunner:sunners(full_name)` only, so
  `gift-leaderboard.tsx` cannot emit `?id=` today. Fix is adding the plain non-null
  `gift_awards.sunner_id` to the select — no new embed, no nullability change.

## Unresolved Questions
2. **ADV-1** (advisory, out of scope): F004's `fetchKudos` reads the entire `kudos` table per request
   and pages client-side; the profile feed uses a keyset cursor instead. The two paging strategies now
   coexist. Worth reconciling when the table outgrows a few hundred rows.
3. **ADV-2** (advisory, out of scope): no `kudos_no_self` constraint exists; a self-Kudos is refused
   only by the absence of a surface offering it. Adding the constraint belongs with F005's schema.
