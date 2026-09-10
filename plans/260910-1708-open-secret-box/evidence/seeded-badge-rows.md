# Seeded badge rows — measured, not assumed

`docker exec supabase_db_my-app psql -U postgres -d postgres -c "select id, position, label, image_path from public.rule_items where kind='collectible_icon' order by position;"`
run 2026-09-10 against the local Supabase:

```
 id | position |        label        |                 image_path
----+----------+---------------------+--------------------------------------------
  5 |        1 | REVIVAL             | /images/rules/icon-revival.png
  6 |        2 | TOUCH OF LIGHT      | /images/rules/icon-touch-of-light.png
  7 |        3 | STAY GOLD           | /images/rules/icon-stay-gold.png
  8 |        4 | FLOW TO HORIZON     | /images/rules/icon-flow-to-horizon.png
  9 |        5 | BEYOND THE BOUNDARY | /images/rules/icon-beyond-the-boundary.png
 10 |        6 | ROOT FURTHER        | /images/rules/icon-root-further.png
```

Two things the odds-seed migration has to respect:

1. **Labels are UPPERCASE.** A join written against `'Stay Gold'` matches nothing and silently
   seeds zero rows. Match on `'STAY GOLD'`, or on `upper(label)`.
2. **`id` values start at 5, not 1** — the hero tiers took 1–4 from the same identity sequence.
   So the seed must resolve ids through a join on `label`, never hardcode them; a fresh
   `supabase db reset` on a machine whose sequence ran differently would otherwise wire the
   weights onto the wrong badges.

Weight mapping the seed must produce (BR-003):

| label | weight |
|---|---|
| STAY GOLD | 30 |
| FLOW TO HORIZON | 25 |
| TOUCH OF LIGHT | 20 |
| BEYOND THE BOUNDARY | 10 |
| REVIVAL | 10 |
| ROOT FURTHER | 5 |
