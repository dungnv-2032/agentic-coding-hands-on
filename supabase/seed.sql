-- Kudos Live Board (F004) — seed data.
--
-- Every string literal below is transcribed verbatim from
-- plans/260906-1945-kudos-live-board/clarifications.md § "Resolved from
-- source data" or copied out of e2e/fixtures/kudos-constants.ts (the same
-- transcription the e2e suite asserts against). Only the *combination* of
-- those literals across rows is composed — reusing the frame's own people,
-- department, campaign, message, and gift line across multiple rows rather
-- than inventing new ones (phase-03 plan, Key Insight 10 / MoMorph rule:
-- "Use Figma design content as mock data source. Do NOT invent data.").
--
-- No write anywhere to the GoTrue-owned auth schema (phase-03 plan
-- § Security Considerations). The seeded frame viewer is a `sunners` row
-- with `auth_user_id` left NULL, and zero `kudos_likes` rows are seeded: a
-- like requires a real authenticated user, which does not exist at seed
-- time.
--
-- `db reset` truncates the whole database before running this file, so
-- plain inserts are re-runnable — no ON CONFLICT needed.

-- ---------------------------------------------------------------------------
-- departments — the 50-entry filter dropdown, copied from
-- e2e/fixtures/kudos-constants.ts DEPARTMENT_OPTIONS in array order
-- (filter_position 1..50), plus CEVC10 (Key Insight 3): the frame's two
-- named people's own department, absent from the dropdown, filter_position
-- null.
-- ---------------------------------------------------------------------------
insert into public.departments (name, filter_position) values
  ('CTO', 1),
  ('SPD', 2),
  ('FCOV', 3),
  ('CEVC1', 4),
  ('CEVC2', 5),
  ('STVC - R&D', 6),
  ('CEVC2 - CySS', 7),
  ('FCOV - LRM', 8),
  ('CEVC2 - System', 9),
  ('OPDC - HRF', 10),
  ('CEVC1 - DSV - UI/UX 1', 11),
  ('CEVC1 - DSV', 12),
  ('CEVEC', 13),
  ('OPDC - HRD - C&C', 14),
  ('STVC', 15),
  ('FCOV - F&A', 16),
  ('CEVC1 - DSV - UI/UX 2', 17),
  ('CEVC1 - AIE', 18),
  ('OPDC - HRF - C&B', 19),
  ('FCOV - GA', 20),
  ('FCOV - ISO', 21),
  ('STVC - EE', 22),
  ('GEU - HUST', 23),
  ('CEVEC - SAPD', 24),
  ('OPDC - HRF - OD', 25),
  ('CEVEC - GSD', 26),
  ('GEU - TM', 27),
  ('STVC - R&D - DTR', 28),
  ('STVC - R&D - DPS', 29),
  ('CEVC3', 30),
  ('STVC - R&D - AIR', 31),
  ('CEVC4', 32),
  ('PAO', 33),
  ('GEU', 34),
  ('GEU - DUT', 35),
  ('OPDC - HRD - L&D', 36),
  ('OPDC - HRD - TI', 37),
  ('OPDC - HRF - TA', 38),
  ('GEU - UET', 39),
  ('STVC - R&D - SDX', 40),
  ('OPDC - HRD - HRBP', 41),
  ('PAO - PEC', 42),
  ('IAV', 43),
  ('STVC - Infra', 44),
  ('CPV - CGP', 45),
  ('GEU - UIT', 46),
  ('OPDC - HRD', 47),
  ('BDV', 48),
  ('CPV', 49),
  ('PAO - PAO', 50),
  ('CEVC10', null);

-- ---------------------------------------------------------------------------
-- hashtags — the 13-entry filter list, copied from
-- e2e/fixtures/kudos-constants.ts HASHTAG_OPTIONS, position 1..13 in exactly
-- that order (K-3 asserts text AND order — alphabetical would fail it).
-- ---------------------------------------------------------------------------
insert into public.hashtags (name, position) values
  ('Toàn diện', 1),
  ('Giỏi chuyên môn', 2),
  ('Hiệu suất cao', 3),
  ('Truyền cảm hứng', 4),
  ('Cống hiến', 5),
  ('Aim High', 6),
  ('Be Agile', 7),
  ('Wasshoi', 8),
  ('Hướng mục tiêu', 9),
  ('Hướng khách hàng', 10),
  ('Chuẩn quy trình', 11),
  ('Giải pháp sáng tạo', 12),
  ('Quản lý xuất sắc', 13);

-- ---------------------------------------------------------------------------
-- sunners — clarifications.md § "Frame dataset" (viewer + receiver) and
-- § "SPOTLIGHT BOARD" (the 7 word-cloud names). 9 rows: the badge-tier and
-- sender-mix requirements (Key Insight 6) are reachable without a 10th
-- invented name, so no extra row is added (phase-03 plan's "plus 1 more
-- frame name if the sender mix needs it" is conditional, and it is not
-- needed here — see report).
--
-- Frame viewer `Huỳnh Dương Xuân Nhật`: auth_user_id NULL (never linked to a
-- real auth user — Key Insight 5), both secret-box counters at 25
-- (Key Insight 4 table), kudos_received_baseline 0 — combined with the 25
-- real "received" kudos rows below, this lands the viewer on Super Hero
-- (>= 20 received) without a fabricated baseline.
--
-- Frame receiver `Huỳnh Dương Xuân`: kudos_received_baseline 50 → Legend
-- Hero, matching the frame's badge on that person exactly.
--
-- Two of the spotlight names get baselines placed at 0 and 10 so New Hero
-- and Rising Hero are also reachable among visible senders (Key Insight 6);
-- the rest are spread across the remaining range for variety. Departments
-- for the spotlight names are not given by the frame, so each reuses one of
-- the 50 dropdown department literals already seeded above rather than
-- inventing a new one. Avatar path is the single committed sample (A3),
-- fixed here and in phase 05 § Architecture.
-- ---------------------------------------------------------------------------
insert into public.sunners
  (full_name, department_id, avatar_url, kudos_received_baseline, secret_box_opened_count, secret_box_unopened_count)
values
  ('Huỳnh Dương Xuân Nhật', (select id from public.departments where name = 'CEVC10'), '/images/kudos/sample-avatar.png', 0, 25, 25),
  ('Huỳnh Dương Xuân', (select id from public.departments where name = 'CEVC10'), '/images/kudos/sample-avatar.png', 50, 0, 0),
  ('Đỗ hoàng Hiệp', (select id from public.departments where name = 'CTO'), '/images/kudos/sample-avatar.png', 0, 0, 0),
  ('Dương thúy An', (select id from public.departments where name = 'SPD'), '/images/kudos/sample-avatar.png', 10, 0, 0),
  ('Mai phương Thúy', (select id from public.departments where name = 'FCOV'), '/images/kudos/sample-avatar.png', 20, 0, 0),
  ('Nguyễn Văn Quy', (select id from public.departments where name = 'CEVC1'), '/images/kudos/sample-avatar.png', 5, 0, 0),
  ('Lê Kiều Trang', (select id from public.departments where name = 'CEVC2'), '/images/kudos/sample-avatar.png', 15, 0, 0),
  ('Nguyễn Bá Chức', (select id from public.departments where name = 'STVC - R&D'), '/images/kudos/sample-avatar.png', 30, 0, 0),
  ('Nguyễn Hoàng Linh', (select id from public.departments where name = 'CEVC2 - CySS'), '/images/kudos/sample-avatar.png', 45, 0, 0);

-- ---------------------------------------------------------------------------
-- kudos — Group A: 25 rows sent by the frame viewer to the frame's receiver
-- (Key Insight 4: the edit pen renders on every ALL KUDOS card in the frame,
-- so the viewer is the sender, not the receiver). campaign, message, and the
-- newest sent_at are all verbatim from clarifications.md § "Frame dataset".
-- Row 1 carries the frame's own heart count (1.000); the other 24 are
-- distinct values <= 60 so the top-5 highlight ordering is unambiguous
-- (Key Insight 9) and none can tie or overtake row 1.
-- ---------------------------------------------------------------------------
insert into public.kudos (sender_id, receiver_id, campaign, message, sent_at, heart_baseline)
select
  (select id from public.sunners where full_name = 'Huỳnh Dương Xuân Nhật'),
  (select id from public.sunners where full_name = 'Huỳnh Dương Xuân'),
  'IDOL GIỚI TRẺ',
  'Cảm ơn người em bình thường nhưng phi thường :D Cảm ơn sự chăm chỉ, cần mẫn của em đã tạo động lực rất nhiều cho team, để luôn nhắc mình luôn phải nỗ lực hơn nữa trong công việc. <3 và cuộc sống...',
  timestamptz '2025-10-30 10:00:00+07' - (n - 1) * interval '6 hours',
  case when n = 1 then 1000 else 62 - (n * 2) end
from generate_series(1, 25) as n;

-- ---------------------------------------------------------------------------
-- kudos — Group B: 25 rows received by the frame viewer, so the sidebar's
-- five verbatim `25`s resolve exactly (Key Insight 4 table: 25 received +
-- heart_baseline 1 each = 25 hearts received, alongside the two stored
-- secret-box counters above). Senders cycle through the frame's other named
-- people (the receiver plus the 7 spotlight names) so all four badge tiers
-- are visible among ALL KUDOS senders, not just the frame viewer's own
-- Super Hero tier on Group A. heart_baseline fixed at 1 keeps every one of
-- these rows well under Group A, so they can never enter the top-5.
-- ---------------------------------------------------------------------------
insert into public.kudos (sender_id, receiver_id, campaign, message, sent_at, heart_baseline)
select
  (select id from public.sunners where full_name = senders.name),
  (select id from public.sunners where full_name = 'Huỳnh Dương Xuân Nhật'),
  'IDOL GIỚI TRẺ',
  'Cảm ơn người em bình thường nhưng phi thường :D Cảm ơn sự chăm chỉ, cần mẫn của em đã tạo động lực rất nhiều cho team, để luôn nhắc mình luôn phải nỗ lực hơn nữa trong công việc. <3 và cuộc sống...',
  timestamptz '2025-10-30 10:00:00+07' - (25 + m) * interval '6 hours',
  1
from generate_series(1, 25) as m
cross join lateral (
  select (array[
    'Huỳnh Dương Xuân', 'Đỗ hoàng Hiệp', 'Dương thúy An', 'Mai phương Thúy',
    'Nguyễn Văn Quy', 'Lê Kiều Trang', 'Nguyễn Bá Chức', 'Nguyễn Hoàng Linh'
  ])[((m - 1) % 8) + 1] as name
) as senders;

-- ---------------------------------------------------------------------------
-- kudos — Group C: 7 rows, one per spotlight name as RECEIVER, so the
-- Phòng ban filter is alive (clarifications.md assumption A5). The frame
-- never states these seven's departments — only the viewer/receiver pair is
-- CEVC10 — so assigning them the canonical department already on their
-- `sunners` row (seeded above) fills a blank the frame leaves rather than
-- overriding one it states. Sender is the frame's own receiver
-- (`Huỳnh Dương Xuân`, already a corpus person) reused, not invented.
-- heart_baseline stays well under Group A's floor (52) so the verified
-- top-5 ordering is untouched. Group A's viewer→receiver pair (including
-- the frame's own 1.000-heart card) is unmodified by this group.
-- ---------------------------------------------------------------------------
insert into public.kudos (sender_id, receiver_id, campaign, message, sent_at, heart_baseline)
select
  (select id from public.sunners where full_name = 'Huỳnh Dương Xuân'),
  (select id from public.sunners where full_name = recipients.name),
  'IDOL GIỚI TRẺ',
  'Cảm ơn người em bình thường nhưng phi thường :D Cảm ơn sự chăm chỉ, cần mẫn của em đã tạo động lực rất nhiều cho team, để luôn nhắc mình luôn phải nỗ lực hơn nữa trong công việc. <3 và cuộc sống...',
  timestamptz '2025-10-30 10:00:00+07' - (60 + recipients.rank) * interval '6 hours',
  10 + (recipients.rank * 5)
from (values
  ('Đỗ hoàng Hiệp', 0),
  ('Dương thúy An', 1),
  ('Mai phương Thúy', 2),
  ('Nguyễn Văn Quy', 3),
  ('Lê Kiều Trang', 4),
  ('Nguyễn Bá Chức', 5),
  ('Nguyễn Hoàng Linh', 6)
) as recipients(name, rank);

-- ---------------------------------------------------------------------------
-- kudos — Group D: ONE anonymous row, so the masking the reader view
-- (20260908100000_profile_reader_view.sql) enforces is observable at all.
-- Measured before adding it: `select count(*) filter (where is_anonymous)
-- from public.kudos` returned 0, which made GUI_006's masking and SEC_001's
-- premise untestable — the mask had no row to mask.
--
-- Sender `Huỳnh Dương Xuân` is an existing corpus person (the frame's own
-- receiver, already reused as Group C's sender), not an invented one.
-- Receiver `Huỳnh Dương Xuân Nhật` is the frame viewer, so the row is
-- reachable at `/profile?id=1` — a masked row on an empty profile would prove
-- nothing.
--
-- `anonymous_name` stays NULL ON PURPOSE. The design CSV publishes no
-- anonymous display name, so inventing one would be inventing design data;
-- leaving it NULL exercises the shipped fallback
-- ANONYMOUS_FALLBACK_LABEL = 'Ẩn danh' (`lib/kudos/board-data.ts`).
--
-- heart_baseline 1 matches Group B, keeping this row far below Group A's
-- floor of 52 — it can never enter the top-5 highlight carousel and so cannot
-- move F004's `.first()`-based K-9. campaign and message are the same frame
-- literals every other group reuses.
--
-- sent_at continues Group C's `- (n) * interval '6 hours'` walk (Group C used
-- 60..66) at 67, so total ordering stays deterministic and this row sorts
-- oldest.
--
-- Verified safe against F004's suite: no e2e assertion fixes an absolute
-- `kudos-card` count, and SIDEBAR_STATS asserts labels only, not the verbatim
-- `25`s.
-- ---------------------------------------------------------------------------
insert into public.kudos
  (sender_id, receiver_id, campaign, message, sent_at, heart_baseline, is_anonymous, anonymous_name)
values (
  (select id from public.sunners where full_name = 'Huỳnh Dương Xuân'),
  (select id from public.sunners where full_name = 'Huỳnh Dương Xuân Nhật'),
  'IDOL GIỚI TRẺ',
  'Cảm ơn người em bình thường nhưng phi thường :D Cảm ơn sự chăm chỉ, cần mẫn của em đã tạo động lực rất nhiều cho team, để luôn nhắc mình luôn phải nỗ lực hơn nữa trong công việc. <3 và cuộc sống...',
  timestamptz '2025-10-30 10:00:00+07' - 67 * interval '6 hours',
  1,
  true,
  null
);

-- ---------------------------------------------------------------------------
-- kudos_hashtags — generated, not 150 hand-written literal rows (phase-03
-- plan § Risk Assessment: keeps the file readable and the pattern DRY).
-- Each kudos gets 1-3 tags; tag_position cycles by kudos.id so every one of
-- the 13 hashtags is used at least once across all seeded kudos, and
-- 'Toàn diện' (hashtag position 1) lands on more than the 3 rows Key
-- Insight 8 requires (verified below in the verification queries).
-- ---------------------------------------------------------------------------
insert into public.kudos_hashtags (kudos_id, hashtag_id, position)
select k.id, h.id, gs.pos
from public.kudos k
cross join lateral generate_series(1, 1 + (k.id % 3)) as gs(pos)
join public.hashtags h on h.position = ((k.id + gs.pos - 2) % 13) + 1;

-- ---------------------------------------------------------------------------
-- kudos_attachments — 5 images on each of the five highest-hearted kudos
-- (ids 1..5 by construction above — the same five rows the highlight
-- carousel surfaces), one committed sample image path per A3.
-- ---------------------------------------------------------------------------
insert into public.kudos_attachments (kudos_id, image_url, position)
select k.id, '/images/kudos/sample-attachment.png', gs.pos
from public.kudos k
cross join lateral generate_series(1, 5) as gs(pos)
where k.id <= 5;

-- ---------------------------------------------------------------------------
-- gift_awards — clarifications.md § "Sidebar (D)" gives exactly one gift
-- row (`Huỳnh Dương Xuân` / `Nhận được 1 áo phông SAA`); it is reused
-- verbatim across all 10 rows (composition rule) rather than inventing new
-- gift lines, with distinct descending awarded_at so the leaderboard has a
-- real order.
-- ---------------------------------------------------------------------------
insert into public.gift_awards (sunner_id, gift_label, awarded_at)
select
  (select id from public.sunners where full_name = 'Huỳnh Dương Xuân'),
  'Nhận được 1 áo phông SAA',
  timestamptz '2025-10-30 10:00:00+07' - (n - 1) * interval '1 day'
from generate_series(1, 10) as n;

-- ---------------------------------------------------------------------------
-- spotlight_ticker_events — one row per spotlight name (clarifications.md
-- § "SPOTLIGHT BOARD"), each pointing at a real kudos_id where that sunner
-- is the RECEIVER (Group C above) — the ticker line reads "... đã nhận
-- được một Kudos mới" (received a new kudos), so the referenced row should
-- be the one where they received, not sent. occurred_at descending with
-- `Nguyễn Bá Chức` as the most recent — the frame's red just-updated node.
-- ---------------------------------------------------------------------------
insert into public.spotlight_ticker_events (sunner_id, kudos_id, occurred_at)
select
  s.id,
  (
    select k.id
    from public.kudos k
    join public.sunners sk on sk.id = k.receiver_id
    where sk.full_name = names.name
    order by k.id
    limit 1
  ),
  timestamptz '2025-10-30 10:00:00+07' - names.rank * interval '10 minutes'
from (values
  ('Nguyễn Bá Chức', 0),
  ('Nguyễn Hoàng Linh', 1),
  ('Lê Kiều Trang', 2),
  ('Nguyễn Văn Quy', 3),
  ('Mai phương Thúy', 4),
  ('Dương thúy An', 5),
  ('Đỗ hoàng Hiệp', 6)
) as names(name, rank)
join public.sunners s on s.full_name = names.name;

-- ---------------------------------------------------------------------------
-- board_stats — the frame's `388 KUDOS` Spotlight canvas heading
-- (test-contract.md § "Blueprint ratification" > "Overridden"): data, not
-- i18n copy, and not a live count(*) over the seeded kudos rows.
-- ---------------------------------------------------------------------------
insert into public.board_stats (id, spotlight_kudos_total) values (1, 388);
