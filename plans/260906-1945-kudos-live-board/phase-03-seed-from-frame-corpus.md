# Phase 03 — Seed from the frame corpus

**Track:** B (behavior/backend) · **Owner:** `implementer` · **Depends:** 02 ·
**Effort:** 2.5h · **test_policy:** `e2e-red-first`

## Context Links

- [plan.md](plan.md) · [phase-02](phase-02-kudos-schema-and-rls.md) (the tables being filled)
- [clarifications.md](clarifications.md) § "Resolved from source data" — **the corpus, verbatim**;
  § "Schema decisions"; assumptions A3, A4
- [test-contract.md](test-contract.md) § "Seed dependency" — the suite asserts against seeded rows
- `e2e/fixtures/kudos-constants.ts` — the transcription the tests actually compare against
- [Supabase study](../reports/researcher-260906-1958-supabase-data-layer.md) § 2 (seed + `auth.users` hazard)

## Overview

**Priority:** P1 · **Status:** delivered.

`supabase/seed.sql` — the frame's content as real rows. Every string comes from the frame corpus;
only the *combinations* are composed, and only as far as assumption A4 requires. Sized so the feed
pages five times, the top-5 highlight ordering is unambiguous, and all four badge tiers appear.

## Key Insights

1. **The department list is 50 entries, not 48.** `clarifications.md` labels it "(48 entries)" but
   the list it prints has 50 members, and `e2e/fixtures/kudos-constants.ts` transcribed all 50.
   K-3 asserts `toHaveCount(DEPARTMENT_OPTIONS.length)` — that is **50**. Seeding 48 fails the
   test. The prose count is a miscount of the correct list; the list wins.
2. **K-3 also asserts hashtag *text and order*** — `toHaveText(HASHTAG_OPTIONS)` compares the array
   element-by-element, so `hashtags.position` must be 1..13 in exactly the frame's order
   (`Toàn diện` first, `Quản lý xuất sắc` last). Alphabetical ordering fails.
3. **`CEVC10` is a 51st department with `filter_position = null`.** The frame's two named people
   belong to it and it is not in the dropdown list.
4. **The frame viewer is the *sender*, not the receiver.** The edit pen renders on own posts, and
   the frame shows it on every ALL KUDOS card — so `Huỳnh Dương Xuân Nhật` is the seeded frame
   viewer (`auth_user_id is null`), and the `1.000`-heart card is one they **sent**. This is what
   makes all five sidebar `25`s land exactly:

   | Sidebar row | Frame value | How the seed produces it |
   |---|---|---|
   | `Số Kudos bạn nhận được:` | 25 | 25 kudos rows with `receiver_id` = frame viewer, `kudos_received_baseline = 0` |
   | `Số Kudos bạn đã gửi:` | 25 | 25 kudos rows with `sender_id` = frame viewer |
   | `Số tim bạn nhận được:` | 25 | each of those 25 received rows carries `heart_baseline = 1`, no seeded likes |
   | `Số Secret Box bạn đã mở:` | 25 | stored column `secret_box_opened_count = 25` |
   | `Số Secret Box chưa mở:` | 25 | stored column `secret_box_unopened_count = 25` |

   50 kudos rows total — which is also exactly what assumption A4 wants (`FEED_PAGE_SIZE = 10`
   → five pages, so the sentinel fires four times).
5. **`seed.sql` may not touch `auth.users`.** GoTrue owns it (study § 2). The seeded viewer is a
   `sunners` row with `auth_user_id is null`; no `kudos_likes` rows are seeded at all, because a
   like requires a real auth user. Every displayed heart count therefore starts at its baseline —
   exactly the frame's `1.000` — and K-25's first click writes the first real like row in the
   database.
6. **Badge tiers come from `kudos_received_baseline`.** Set them so all four tiers exist and the
   frame's two named people match the frame: `Huỳnh Dương Xuân` baseline `50` → `Legend Hero`;
   the frame viewer `0` (+25 received) → `Super Hero`; one sunner at `0` → `New Hero`; one at
   `10` → `Rising Hero`. Every badge and every tooltip variant becomes observable.
7. **`388 KUDOS` is not seedable and must not be faked into a table.** K-13 asserts the literal
   `388 KUDOS`, and `count(*) from kudos` is 50. It is the frame's rendered TEXT node with no
   queryable source; inventing a one-row settings table to hold it would be a fake data source
   wearing a schema. It ships as `kudos` dictionary copy in phase 05 and is recorded there.
8. **K-8 needs the first hashtag option to match real rows.** It selects
   `HASHTAG_OPTIONS[0]` = `Toàn diện` and reads the pagination. Seed `Toàn diện` onto **at least
   three** kudos so the filtered carousel is non-empty and the reset-to-slide-1 assertion is
   meaningful rather than vacuous.
9. **The top-hearted card must be unambiguous.** K-25 acts on `kudos-card` `.first()` — the active
   highlight slide, i.e. the top-hearted kudos. Give it `heart_baseline = 1000` and cap every
   other row at `≤ 60`, so a ±1 like can never reorder the carousel between the click and the
   reload.
10. **Composition rule, stated once:** every literal — name, department, campaign, message,
    hashtag, gift line, timestamp, image path — is drawn from the frame corpus. Rows recombine
    those literals; nothing invents a new one. That is what A4 sanctions and what the MoMorph
    rule "use Figma design content as mock data source, do NOT invent data" permits.

## Requirements

**Functional:** FR-001. The seed must satisfy, by content alone: K-3 (13 + 50 options in order),
K-4/K-5/K-6/K-7 (≥ 5 kudos so the carousel has five slides and a next arrow), K-8 (`Toàn diện`
matches ≥ 3), K-9 (the first card has sender, receiver, badge, campaign, timestamp, hashtags),
K-17 (feed non-empty), K-18 (five sidebar rows resolve), K-20 (gift leaderboard non-empty),
K-24 (cards render for anon), K-25 (a likeable top card).

**Non-functional:** pure SQL, no procedural blocks beyond `insert … select` where it removes
repetition; re-runnable under `db reset` (fresh database each time, so no `on conflict` needed);
readable — grouped by table with a comment naming the clarifications section each block is
transcribed from.

## Architecture

**Data flow:** `supabase/seed.sql` → `db reset` → nine `public` tables → phase 04 reads them via
PostgREST → phase 09 renders. One direction, no runtime writes from this phase.

**Row budget:**

| Table | Rows | Content source |
|---|---|---|
| `departments` | 51 | the 50 dropdown entries in `kudos-constants.ts` order (`filter_position 1..50`) + `CEVC10` (`null`) |
| `hashtags` | 13 | clarifications § hashtag filter list, `position 1..13` |
| `sunners` | 10 | `Huỳnh Dương Xuân Nhật` (frame viewer, `CEVC10`), `Huỳnh Dương Xuân` (`CEVC10`), the 7 spotlight names, plus 1 more frame name if the sender mix needs it |
| `kudos` | 50 | 25 sent by the frame viewer (one with `heart_baseline = 1000`), 25 received by them (`heart_baseline = 1` each) |
| `kudos_hashtags` | ~150 | 1–5 per kudos, `position` 1..n; `Toàn diện` on ≥ 3 |
| `kudos_attachments` | ~25 | 5 on each of five feed kudos, one committed sample image (A3) |
| `kudos_likes` | **0** | a like needs a real auth user; K-25 writes the first row |
| `gift_awards` | 10 | `Huỳnh Dương Xuân` / `Nhận được 1 áo phông SAA`, verbatim, descending `awarded_at` |
| `spotlight_ticker_events` | 7 | one per spotlight name; the most recent is `Nguyễn Bá Chức` (the red just-updated node); the ticker renders the 6 most recent |

Seven events give the frame's exact numbers at once: 7 word-cloud nodes, 6 ticker rows, 1 red node.

**Timestamps:** `sent_at` values spread backwards from the frame's `10:00 - 10/30/2025` so the feed
has a deterministic newest-first order and `formatSentAt` renders the frame's string on the card
the frame shows.

## Related Code Files

**Create:** `supabase/seed.sql` — **one file, nothing else**
**Modify:** none
**Owned elsewhere:** `public/images/kudos/sample-avatar.png` and
`public/images/kudos/sample-attachment.png` are written by phase 05 (Track A owns every asset
export). This phase writes only those two **paths** as `image_url` / `avatar_url` strings; the
paths are fixed here and in phase 05 § Architecture so neither track waits on the other.
**Read only:** `e2e/fixtures/kudos-constants.ts` (the transcription to match), `clarifications.md`
**Delete:** none

## Implementation Steps

1. Copy the 50 department names **out of `e2e/fixtures/kudos-constants.ts`** (not out of the
   clarifications prose) so the seed and the assertion share one transcription. Insert with
   `filter_position` 1..50 in array order, then `CEVC10` with `null`.
2. Insert the 13 hashtags with `position` 1..13 in array order.
3. Insert the 10 sunners. Frame viewer: `auth_user_id null`, `secret_box_opened_count 25`,
   `secret_box_unopened_count 25`, `kudos_received_baseline 0`. Set the other baselines per
   Key Insight 6. `avatar_url` is the single committed sample path for every row (A3).
4. Insert 25 kudos sent by the frame viewer — one with `heart_baseline 1000`, the rest `≤ 60` and
   all distinct so the top-5 ordering is total. `campaign = 'IDOL GIỚI TRẺ'`, `message` the frame's
   verbatim body, `sent_at` descending from `2025-10-30 10:00`.
5. Insert 25 kudos received by the frame viewer, each `heart_baseline 1`, senders drawn from the
   other sunners so all four badge tiers appear among the visible cards.
6. Insert `kudos_hashtags` 1–5 per kudos with `position`; `Toàn diện` on ≥ 3 rows, and each of the
   13 used at least once where it costs nothing.
7. Insert 5 `kudos_attachments` on each of five kudos, `position` 1..5.
8. Insert 10 `gift_awards` and 7 `spotlight_ticker_events` (each event pointing at a real
   `kudos_id`, `occurred_at` descending, `Nguyễn Bá Chức` newest).
9. `npx supabase db reset` — migrations then seed, one command.
10. Verify the counts that the tests depend on:
    ```
    docker exec supabase_db_my-app psql -U postgres -d postgres -c "select
      (select count(*) from departments where filter_position is not null) as dept_filterable,
      (select count(*) from hashtags) as hashtags,
      (select count(*) from kudos) as kudos,
      (select count(*) from kudos_likes) as likes,
      (select max(heart_baseline) from kudos) as top_hearts,
      (select count(*) from spotlight_ticker_events) as ticker;"
    ```
    Expect `50, 13, 50, 0, 1000, 7`.
11. Verify the sidebar arithmetic resolves to the frame's five `25`s with a single query over the
    frame viewer's row (received count, sent count, sum of `heart_baseline` on received, and the
    two stored counters).
12. `npm run typecheck && npm run lint`.

## Todo List

- [ ] 50 filterable departments in `kudos-constants.ts` order + `CEVC10` unfilterable
- [ ] 13 hashtags, `position` 1..13, frame order
- [ ] 10 sunners; frame viewer `auth_user_id null` with both secret-box counters at 25
- [ ] Badge baselines produce all four tiers, `Huỳnh Dương Xuân` = `Legend Hero`
- [ ] 25 sent + 25 received for the frame viewer; top card `heart_baseline 1000`, others ≤ 60, distinct
- [ ] `Toàn diện` on ≥ 3 kudos
- [ ] 5 attachments on five feed kudos; 10 gift rows; 7 ticker events with real `kudos_id`
- [ ] **Zero** `kudos_likes` rows and **zero** `auth.*` writes
- [ ] `db reset` clean; step 10 counts match `50, 13, 50, 0, 1000, 7`
- [ ] Sidebar arithmetic yields 25/25/25/25/25

## Success Criteria

- `npx supabase db reset` exits 0 with the seed applied.
- Step 10's counts match exactly; step 11 yields five 25s.
- `grep -ci "auth.users\|auth.identities" supabase/seed.sql` → 0.
- Every string literal in `seed.sql` traces to `clarifications.md` § "Resolved from source data"
  or to `e2e/fixtures/kudos-constants.ts`. A reviewer can point at the source line for each one.
- No e2e assertion changes state yet — the screen is still unbuilt.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Seeding 48 departments from the prose label instead of 50 from the list | **High** × High | Step 1 forbids the prose as a source; step 10 counts 50 |
| Hashtag order drifts from `HASHTAG_OPTIONS`, so K-3's `toHaveText` fails on ordering | Med × High | `position` assigned in array order, copied from the same file the test imports |
| The seed's ~150 `kudos_hashtags` rows written by hand and drifting | Med × Med | Generate them with `insert … select` over the kudos ids rather than 150 literal rows; keeps the file readable and the pattern DRY |
| Seed references `public/images/kudos/sample-*.png` before phase 05 exports them | **High** × Low | Only the string is stored, so the seed is valid immediately; the image 404s in the browser until phase 05 lands, and phase 09 will not run its GREEN gate before both phases are complete. The two paths are frozen in both phase files, so no coordination round trip is needed |
| A future `db reset` run mid-suite wipes `auth.users` and signs the browser out | Med × **High** | Reset is a pre-suite step only (plan § Hard constraints). No test, script, or `package.json` entry may call it; `test:e2e` stays untouched |
| Feed of 50 rows plus embeds exceeds a comfortable payload | Low × Low | Well under `max_rows = 1000`; attachments are only on five rows |

**Rollback:** delete `supabase/seed.sql` and `npx supabase db reset`. Local-only data, nothing to
migrate back.

## Security Considerations

- No secrets, keys, tokens, or real personal data. Every name is the frame's sample content, and
  A3 records that the artwork is placeholder art inside the design itself.
- No `auth.users` / `auth.identities` insert — an attempt would be both unsupported and a
  fabricated identity.
- No `kudos_likes` rows, so no like is ever attributed to a person who did not perform it.
- `seed.sql` must never be pointed at a linked/remote project; `db reset` without `--linked` stays
  local, and this plan uses no `--linked` anywhere.

## Next Steps

Unblocks phase 04 (`npm run db:types` needs the applied schema; the query layer needs rows to read
back). Track A continues in parallel and is unaffected.
