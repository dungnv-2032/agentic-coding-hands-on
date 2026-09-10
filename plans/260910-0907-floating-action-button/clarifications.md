# Clarifications — Floating Action Button (quick-action menu)

- MoMorph screens (two states of ONE component):
  - collapsed — `Floating Action Button - phim nổi chức năng` — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/_hphd32jN2 · node `313:9137` · 3 specs · `spec_status: done`
  - expanded — `Floating Action Button - phim nổi chức năng 2` — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/Sv7DFwBw1h · node `313:9139` · 3 specs · `design_status: done`, `spec_status: done`
- Design artifacts: `design/specs-collapsed.csv`, `design/specs-expanded.csv`, `design/geometry.md`
- Test cases downloaded: **0** on both screens (`download_test_cases` → `status: empty`). The test
  contract below is therefore derived from the spec descriptions, not from a test-case CSV.
- testPolicy: **`e2e-red-first`** — the component's whole point is a state transition
  (collapsed → expanded → collapsed) plus two navigations. That is behaviour, not a static mapping,
  so the auto-selection rule in `.claude/rules/momorph/momorph-development.md` picks strict E2E.
  Runner present and executable: `@playwright/test ^1.62.1`, `npx playwright test`. Web, not mobile.
- Discipline: `--auto`. The commission says *"nếu có vấn đề gì cần confirm với tôi, tự động triển
  khai theo hướng câu trả lời đâu tiên, Yes hoặc câu trả lời Recommend mà ko cần confirm tôi"* —
  every gate below is resolved by taking the first / Yes / Recommended option without asking.
- Supabase: **local project** (`supabase/config.toml`, `supabase/migrations`), as instructed.
- spec_lang: `vi` — inherited from `docs/.rebuild-state.json → primary_lang`, no prompt.

## Session 2026-09-10

### What the design is, and what the repository already has

`app/_components/floating-widget.tsx` already ships a collapsed pill — but as **two direct links**
(`/kudos`, `/standards`) split by a `/` glyph, with no menu. Its own docblock records why:

> *"a fixed bottom-right pill holding two direct links split by a `/` glyph — no quick-action menu
> (clarifications.md: the design's own node names … settle it)"*

That reading was made under F002 from the *collapsed* frame alone. This commission supplies the
**second frame**, and it overturns the reading: node `313:9138`'s own `navigation.linkedFrameId` is
`313:9139` — the collapsed pill links to the *expanded* state, not to a destination. The spec text
says so outright: *"click: Mở 2 option chọn xem thể lệ hoặc viết kudos"*. So this feature converts
the pill from a link pair into a real disclosure trigger.

Both destinations already exist and are shipped: `/standards` (F007 Thể lệ) and `/kudos/new`
(F005 Viết Kudo). Nothing downstream has to be built.

### Resolved gaps

- Q: The collapsed pill is currently two `<Link>`s. Convert it to one disclosure trigger, or keep
  the links and add a menu alongside?
  → A: **Convert it.** Recommended: the design's own navigation edge (`313:9138` → `313:9139`)
  makes the pill a trigger, and keeping direct links plus a menu would give the same two
  destinations two different affordances on one screen. The two icons and the `/` stay exactly as
  drawn — they become the trigger's content, not two hit targets.

- Q: `Thể lệ` and `Viết KUDOS` say *"Mở modal/section"*. Modal, or navigate?
  → A: **Navigate — `/standards` and `/kudos/new`.** Recommended, and it is the same translation
  F007 already recorded and shipped (`clarifications.md` of `260909-0838-the-le-rules-panel`:
  *"Navigate to `/kudos/new`. That IS the compose surface in this repo"*). `/standards` renders the
  Thể lệ drawer over its own route, so "open the Thể lệ section" is satisfied literally. Building a
  second, in-page copy of either surface would duplicate two shipped screens.

- Q: `Viết KUDOS` → `/kudos/new` is guarded by `proxy.ts`. What does an anonymous user get?
  → A: **The existing guard, untouched** — `proxy.ts` redirects to `/login`. No new auth logic, and
  the menu item is not hidden or disabled for anonymous users: the design shows no such state, and
  `TC_THELE_FUN_004`'s repo precedent already relies on the guard doing this.

- Q: Which pages render the FAB?
  → A: **Only the homepage `/`, unchanged.** Recommended: that is the only page composing
  `FloatingWidget` today, and `/awards-information`, `/kudos`, `/kudos/new` and `/standards` each
  carry an explicit docblock stating their frame shows none. Widening the surface is not in the
  commission.

- Q: Close affordances beyond the red `Hủy` button?
  → A: **Also Escape and outside-pointerdown**, via the repo's existing
  `app/_components/use-dismiss-on-outside.ts`. Recommended: every other popover on the screen
  (notification bell, account menu, language selector) already honours that contract, and the hook
  costs nothing to reuse. Escape returns focus to the trigger; an outside click does not move focus.

- Q: Supabase — the commission says "use Supabase local project", but every design item has an
  empty `databaseTable` / `databaseColumn`. New tables?
  → A: **No new tables, no new migration.** Recommended: the FAB persists nothing and reads nothing;
  its two destinations are the surfaces that talk to Supabase (`/standards` reads `rule_sections` /
  `rule_items`, `/kudos/new` writes kudos). "Use Supabase local project" is honoured as the
  environment the feature is developed and tested against — the E2E run boots the local stack and
  `Thể lệ` is asserted to land on the database-backed panel. Inventing a table to satisfy the words
  would add schema nothing reads.

- Q: The FAB label copy — new dictionary keys, or reuse `home.widget`?
  → A: **Reuse and extend `home.widget`.** It already holds `writeKudos` / `standards`; the menu
  needs the on-button labels exactly as drawn (`Thể lệ`, `Viết KUDOS`) plus a trigger and a close
  label. Keys are added to the one existing block rather than a new namespace, in both `vi` and `en`.
  The drawn Vietnamese strings are the `vi` values; `en` gets equivalents, matching how every other
  block in `lib/i18n/messages/` is structured.

- Q: `get_frame_image` returns the Thể lệ drawer for BOTH FAB screens, not the FAB.
  → A: **Ignore the render, use the measured node geometry.** `get_node` / `get_node_context` return
  exact bounds, radii, colours and typography for every item (recorded in `design/geometry.md`), and
  MCP design data is authoritative per `.claude/rules/momorph/momorph-development.md` rule 1. Visual
  validation at the end is against those numbers, not against the misrendered thumbnail.

- Q: Responsive — the frames are desktop 1440 only.
  → A: **Keep the current responsive posture**: same fixed bottom-right anchor, buttons shrink to
  content on narrow viewports rather than holding 149/214px. Recommended: the repo's five shipped
  screens all degrade this way, and no mobile frame exists to contradict it. Widths are treated as
  minimums at ≥1024px, not hard sizes.

### Test contract (fixed here; the RED spec and the implementation both bind to it)

`data-testid` values, fixed so tester and UI implementer cannot drift:

| testid | Element |
|--------|---------|
| `fab-trigger` | collapsed pill (`aria-expanded`, `aria-controls`) |
| `fab-menu` | expanded group |
| `fab-standards` | `Thể lệ` button → `/standards` |
| `fab-write-kudos` | `Viết KUDOS` button → `/kudos/new` |
| `fab-close` | round red `Hủy` button |

Command (fixed for both RED and GREEN):

    npx playwright test e2e/floating-action-button.spec.ts --project=anon

Runs in `anon`: the homepage is public, and the `/kudos/new` guard redirect to `/login` is itself
one of the assertions. The spec writes no data, so it needs no cleanup block.

### Late finding — an existing test is coupled to the old shape (in scope, must be adapted)

`e2e/the-le.spec.ts` FUN_003 (F007) earns its history entry by clicking the homepage widget as a
**link**:

```ts
const standardsShortcut = page.getByRole("link", { name: WIDGET_STANDARDS_LABEL }); // "Thể lệ SAA"
await standardsShortcut.click();
```

After this conversion there is no such link on `/` — the destination sits behind the trigger.

- Q: Adapt FUN_003, or preserve a hidden link so it keeps passing?
  → A: **Adapt FUN_003** — open the FAB, then click `fab-standards`. Recommended: it is the same
  assertion (a real client-side history entry, then `Đóng` returns to `/`), reached through the
  interaction the design now specifies. Keeping a shadow link purely to satisfy a test would leave
  two affordances for one destination — exactly what the first resolved gap rules out. This is an
  adaptation of the *route to* the assertion, not a weakening of the assertion; FUN_003's
  expectations are unchanged.
- `e2e/fixtures/the-le-constants.ts` `WIDGET_STANDARDS_LABEL` stays as the accessible name of the
  menu item, so the constant survives — only the role and the two-step path change.

### Local Supabase — verified reachable

`npx supabase status`: DB `postgresql://postgres:postgres@127.0.0.1:54322/postgres`, REST
`http://127.0.0.1:54321`. `rule_sections` responds `200` over REST, so the `/standards` destination
this feature navigates to is genuinely database-backed in the environment the E2E runs against.
(`imgproxy`, `edge_runtime` and `pooler` are stopped; none is used by this app.)
