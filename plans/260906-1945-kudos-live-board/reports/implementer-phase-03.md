# Implementer report — phase 03 (seed from frame corpus)

**File touched:** `supabase/seed.sql` (new, then amended for A5). Nothing else.

## Amendment — assumption A5 (department filter was dead)

My first pass seeded every `kudos.receiver_id` as either the viewer or `Huỳnh Dương Xuân` — both
`CEVC10`, which is not a filterable department. The coordinator caught this: it made the
Phòng ban filter return zero rows for all 50 options, contradicting the dropdown spec and K-8.
Fix recorded as **assumption A5** in `clarifications.md`: the seven Spotlight names' departments
(already assigned from the canonical 50, since the frame never states them) are now also used as
**receivers**, not just senders.

Added **Group C** (7 rows): sender = `Huỳnh Dương Xuân` (reused, not invented), receiver = each of
the 7 spotlight sunners in turn (their own already-seeded, distinct department), `campaign`/
`message` reused verbatim, `heart_baseline` 10/15/.../40 (all below Group A's floor of 52, so the
verified top-5 ordering is untouched), `sent_at` further back than Groups A/B. The frame's own
viewer→`Huỳnh Dương Xuân` pair (Group A, including the 1.000-heart card) is unmodified.

While fixing this I also corrected a latent semantic bug in `spotlight_ticker_events`: it
previously pointed each spotlight person's ticker row at a kudos where they were the *sender*,
but the ticker copy reads "... đã nhận được một Kudos mới" (received). It now points at their
Group C row, where they are the *receiver* — verified below (`points_at_own_receipt = t` for all
7).

`kudos` total is now **57** (50 + 7), not 50 — nothing requires the count to stay exactly 50; the
50-row target was for feed pagination (`FEED_PAGE_SIZE=10` → still ≥ 5 pages) and the sidebar's
viewer-scoped counts (unaffected, still exactly 25/25/25/25/25 — reverified below).

## How one frame card became a pageable feed (no invented people)

Frame corpus gives exactly 2 named people (viewer `Huỳnh Dương Xuân Nhật`, receiver
`Huỳnh Dương Xuân`) + 7 spotlight names = 9 people, one campaign, one message body, one gift
line, one timestamp. To reach 50 `kudos` rows (5 feed pages at `FEED_PAGE_SIZE=10`) I reused
those same literals across rows rather than adding people:

- **Group A (25 rows):** sender=viewer, receiver=Xuân, `campaign`/`message` verbatim on every
  row, only `sent_at` and `heart_baseline` vary per row. Row 1 = frame's `1000`; rows 2-25 are
  distinct values ≤ 58 (formula `62 - n*2`), so top-5-by-hearts is unambiguous and always drawn
  from this group.
- **Group B (25 rows):** sender cycles through the other 8 named people (Xuân + 7 spotlight
  names), receiver=viewer, same `campaign`/`message` verbatim, `heart_baseline` fixed at 1 (no
  `kudos_likes` seeded — a like needs a real auth user). This is what makes the sidebar's five
  `25`s land exactly.
- `kudos_hashtags` (generated via `insert…select` + `generate_series`, not literal rows) and
  `kudos_attachments`/`gift_awards`/`spotlight_ticker_events` all recombine the same 13-hashtag
  list / gift line / spotlight names rather than fabricating new ones.

**9 sunners, not 10.** The row-budget table said "10 ... plus 1 more frame name if the sender
mix needs it" — conditional. All four badge tiers (Key Insight 6) are reachable from the 9
already available (viewer, receiver, 7 spotlight names), so I did not add a 10th name the corpus
doesn't supply.

**Departments for the 7 spotlight names** aren't given by the frame (only the two CEVC10 people
have a stated department). I assigned each spotlight sunner one of the 50 already-seeded
dropdown department names (CTO, SPD, FCOV, CEVC1, CEVC2, "STVC - R&D", "CEVC2 - CySS") — reusing
existing literals, not inventing new department names.

**Superseded note:** the department-filter gap flagged here in the original pass was fixed as a
real defect, not left informational — see "Amendment — assumption A5" above.

**Frame's own hashtag row text** (`#Dedicated #Inspring…`) is NOT what I attached to
`kudos_hashtags` — those two words aren't in the 13-entry `hashtags` table (which, per phase's
own Architecture/Key Insight 2, holds only the 13-item filter list, and `kudos_hashtags.hashtag_id`
FKs into it). I attached combinations of the 13 canonical hashtags instead, since that's the only
set the schema and `K-8`/filter-click semantics can reference. Recorded here as the resolution
of a genuine corpus ambiguity, per task instructions.

## Verification (real database, `npx supabase db reset`, post-A5-fix)

Exit code: **0**.

**Filter is alive** (proof query from the coordinator):
```
     name     | filter_position | count
--------------+-----------------+-------
 STVC - R&D   |               6 |     1
 CTO          |               1 |     1
 CEVC2        |               5 |     1
 SPD          |               2 |     1
 FCOV         |               3 |     1
 CEVC2 - CySS |               7 |     1
 CEVC1        |               4 |     1
(7 rows)
```
7 distinct filterable departments now return a real, non-empty result.

**Counts (re-verified):**
```
t                        | count
hashtags                 | 13
departments              | 51
departments_filterable   | 50
sunners                  | 9
kudos                    | 57      (was 50 — +7 for Group C)
kudos_likes              | 0
gift_awards              | 10
ticker                   | 7
```

Top-5 hearts, strictly descending & distinct — **unchanged**: `1000, 58, 56, 54, 52` (id 1..5).
Group C's heart_baselines (10-40) never enter the top-5.

`board_stats`: `(1, 388)` — unchanged.

Badge tiers reachable from seeded `kudos_received_baseline` (raw column) — unchanged: New Hero
(0), Rising Hero (10, 15), Super Hero (20, 30, 45), Legend Hero (50, `Huỳnh Dương Xuân`). Viewer's
runtime tier is still `baseline(0) + 25 real received rows = 25` → Super Hero.

Sidebar arithmetic for the frame viewer — **re-verified, unchanged**: `received_count=25,
sent_count=25, hearts_received=25, secret_opened=25, secret_unopened=25`. Group C uses
`Huỳnh Dương Xuân` as sender and the spotlight names as receiver — it never touches the viewer's
own sent/received rows, so this couldn't have moved, and I checked it anyway rather than assume.

`Toàn diện` now on 9 kudos rows (was 7; still ≥ 3 required) — Group C added 2 more via the same
generator, which runs over all seeded kudos including Group C.

Ticker events now point at the semantically-correct row (`points_at_own_receipt = t` for all 7):
```
 full_name         | kudos_id | points_at_own_receipt | occurred_at
 Nguyễn Bá Chức     |       56 | t                      | 2025-10-30 03:00:00+00  (most recent)
 Nguyễn Hoàng Linh  |       57 | t                      | 2025-10-30 02:50:00+00
 Lê Kiều Trang      |       55 | t                      | 2025-10-30 02:40:00+00
 Nguyễn Văn Quy     |       54 | t                      | 2025-10-30 02:30:00+00
 Mai phương Thúy    |       53 | t                      | 2025-10-30 02:20:00+00
 Dương thúy An      |       52 | t                      | 2025-10-30 02:10:00+00
 Đỗ hoàng Hiệp      |       51 | t                      | 2025-10-30 02:00:00+00
```

`grep -ci "auth.users\|auth.identities" supabase/seed.sql` → **0**.

## Deviations from the row-budget table

- `sunners`: 9, not 10 (see above — the "+1" was conditional and not needed).
- `kudos_hashtags`: generated (1-3 tags/kudos via `1 + id%3`, not the plan's "1-5, ~150
  estimate") — still satisfies every stated requirement (≥3 `Toàn diện`, all 13 used, ≤5 per
  card) with a simpler, fully set-based generator.
- `kudos`: 57, not 50 — the extra 7 (Group C) exist solely to make the department filter
  observable per assumption A5; see amendment above.

## Unresolved questions

None blocking.

**Status:** DONE
