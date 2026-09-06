# Implementer report — phase 03 (seed from frame corpus)

**File touched:** `supabase/seed.sql` (new, 257 lines). Nothing else.

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

**Note (not a defect, flagging for later phases):** every `kudos.receiver_id` in this seed is
either the viewer or Xuân, and both are `CEVC10` — a department outside the 50-entry filter
dropdown. So no seeded card's receiver ever matches a filterable department; a department-filter
selection will always show zero results against this data. No test in phase 03's scope (K-0..25)
exercises "select a department filter, expect non-empty results" — only K-3 (option count) touches
department at all — so this doesn't fail anything now, but a later phase adding such an assertion
would need either a broader receiver-department mix or a documented exception.

**Frame's own hashtag row text** (`#Dedicated #Inspring…`) is NOT what I attached to
`kudos_hashtags` — those two words aren't in the 13-entry `hashtags` table (which, per phase's
own Architecture/Key Insight 2, holds only the 13-item filter list, and `kudos_hashtags.hashtag_id`
FKs into it). I attached combinations of the 13 canonical hashtags instead, since that's the only
set the schema and `K-8`/filter-click semantics can reference. Recorded here as the resolution
of a genuine corpus ambiguity, per task instructions.

## Verification (real database, `npx supabase db reset`)

Exit code: **0** (both the working run and a re-run after a comment edit).

```
t                        | count
hashtags                 | 13
departments              | 51
departments_filterable   | 50
sunners                  | 9
kudos                    | 50
kudos_likes              | 0
gift_awards              | 10
ticker                   | 7
```

Step-10 single-row check: `dept_filterable=50, hashtags=13, kudos=50, likes=0, top_hearts=1000, ticker=7` — all match.

Top-5 hearts, strictly descending & distinct: `1000, 58, 56, 54, 52` (id 1..5).

`board_stats`: `(1, 388)`.

Badge tiers reachable from seeded `kudos_received_baseline` (raw column, before the app adds
real received-row counts): `0` → New Hero (Đỗ hoàng Hiệp, viewer), `10`/`15` → Rising Hero
(Dương thúy An, Lê Kiều Trang), `20`/`30`/`45` → Super Hero (Mai phương Thúy, Nguyễn Bá Chức,
Nguyễn Hoàng Linh), `50` → Legend Hero (Huỳnh Dương Xuân). The viewer's runtime tier is
`baseline(0) + 25 real received rows = 25` → Super Hero, per Key Insight 6 — the raw-baseline
table above shows it as 0/New Hero because it's pre-aggregation.

Sidebar arithmetic for the frame viewer: `received_count=25, sent_count=25, hearts_received=25,
secret_opened=25, secret_unopened=25` — all five `25`s.

`Toàn diện` on 7 kudos rows (≥ 3 required). All 13 hashtags used (7-8 rows each).

`grep -ci "auth.users\|auth.identities" supabase/seed.sql` → **0** (had to reword a header
comment that named those tables in prose, which the literal grep also caught — fixed).

## Deviations from the row-budget table

- `sunners`: 9, not 10 (see above — the "+1" was conditional and not needed).
- `kudos_hashtags`: 101 rows generated (1-3 tags/kudos via `1 + id%3`, not the plan's "1-5, ~150
  estimate") — still satisfies every stated requirement (≥3 `Toàn diện`, all 13 used, ≤5 per
  card) with a simpler, fully set-based generator.

## Unresolved questions

None blocking. The department/receiver-diversity note above is informational for whichever
later phase might add a department-filter-results assertion.

**Status:** DONE
