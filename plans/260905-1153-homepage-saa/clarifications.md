# Clarifications — Homepage SAA 2025

- **Screen:** Homepage SAA — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/i87tDx10uM
- **fileKey:** `9ypp4enmFmdK3YAFJLIu6C` · **screenId:** `i87tDx10uM` · **figma node:** `2167:9026`
- **Design revision:** `aee225995cef1ad70ed504a9d02799d0` · spec_status `done`, dev_status `none`
- **Source data:** 46 spec items, 62 test cases, 35 `MM_MEDIA_*` nodes (fetched live via MoMorph MCP)
- **Frame image:** `design/homepage-saa.png` (1512×4480)
- **testPolicy:** `e2e-red-first`
- **Mode:** `/tkm:takumi --auto` — user directed "tự động triển khai theo hướng Recommend mà ko cần hỏi lại".
  Every gap below is therefore resolved by the orchestrator on the recommended option and recorded here.
  This file is authoritative and not re-openable by sub-agents.

## Session 2026-09-05

- Q: Screen scope — the design links out to Awards Information, Sun* Kudos and Tiêu chuẩn chung, none of which exist. → A: **Homepage `/` only.** Those three screens are out of scope. To keep test ID-59 ("no broken links") honest, ship four minimal placeholder routes (`/awards-information`, `/kudos`, `/standards`, `/profile`) built from one shared `ComingSoon` component that reuses the real header/footer. They are placeholders by declaration, not stand-ins for homepage behavior.
- Q: The boilerplate `create-next-app` page currently occupies `app/page.tsx`. → A: **Replace it.** Homepage SAA becomes `/`. `proxy.ts` already lets `/` through untouched (public — test ID-0), so no guard change is needed.
- Q: Header is shared between `/login` and `/`, but `LanguageSelector` + `setLocale` live under `app/login/`. → A: **Promote to shared.** Move `language-selector.tsx` and `icons.tsx` to `app/_components/`, and `setLocale` to `app/_actions/locale.ts`; `/login` imports from the new home. DRY beats duplication; `revalidatePath` widens from `/login` to `/` (layout scope) so both screens re-render on switch.
- Q: Notification bell (A1.6) — there is no notification backend. → A: **Presentational panel, empty state.** Bell renders only for an authenticated user; click toggles a panel showing "Không có thông báo mới". No badge, because there is no unread source to drive one (test ID-29 — "no badge when nothing unread" — is the state we ship; ID-28 is deferred with the backend).
- Q: Account menu (A1.8) options Profile / Sign out / Admin Dashboard. → A: **All three, role-gated.** Admin Dashboard appears only when `user.app_metadata.role === "admin"` (test ID-37/ID-38). Sign out reuses the existing `/todo` sign-out server action, promoted to `app/_actions/auth.ts`. Profile and Admin Dashboard point at placeholder routes.
- Q: Countdown target time (B1) — "configurable via env var, ISO-8601". → A: **`NEXT_PUBLIC_EVENT_START_AT`**, documented in `.env.example`, default `2025-12-26T18:30:00+07:00` (the date shown in the design). Unparseable value → render `00/00/00`, hide "Coming soon", log one console warning, never throw (test ID-60).
- Q: Countdown tick cadence and hydration. → A: **1-second `setInterval` recomputing from `Date.now()`** (self-correcting against drift; satisfies ID-39's one-minute assertion). Server renders padded `00` placeholders; the client fills real values in `useEffect` after mount — no server/client time mismatch, no `suppressHydrationWarning`.
- Q: Awards grid responsive columns — spec item C2 (English row) says 1 column on mobile, but test ID-16 says 2 columns on tablet **and** mobile. → A: **Follow the test cases:** 3 columns ≥1024px, 2 columns below. Test cases outrank the prose row.
- Q: Widget button (item 6) — "opens a quick-action menu", options unspecified. → A: **No menu — two direct links.** The design's own node names settle it: `icon viết kudos` → `/kudos`, `icon thể lệ saa` → `/standards`, separated by the `/` glyph. Nothing is invented.
- Q: Award card destinations. → A: `/awards-information#<slug>` with slugs `top-talent`, `top-project`, `top-project-leader`, `best-manager`, `signature-2025-creator`, `mvp`. Whole card is one link (image + title + "Chi tiết" all navigate — ID-47/48/49).
- Q: i18n coverage for the new copy. → A: **Full VN + EN.** Extend `Dictionary` with `header`, `home` and footer link keys. VN copy verbatim from the design; EN is a translation of the same. No new i18n library.
- Q: Fonts. → A: **Montserrat + Montserrat Alternates**, declared the same way `/login` already does it (`next/font/google`, `--font-montserrat` variables already wired into `globals.css` `@theme inline`).
- Q: Test policy. → A: **`e2e-red-first`.** The screen carries real state transitions — language menu open/close/Esc/outside-click, account menu, notification panel, countdown ticking, navigation — so the policy auto-selects strict. `@playwright/test` 1.62.1 already exists with a working config, so the runner precondition is met; nothing is installed or scaffolded.

## Resolved from source data (no decision needed)

- Six award categories, in design order: Top Talent, Top Project, Top Project Leader, Best Manager, Signature 2025 - Creator, MVP (Most Valuable Person).
- Event info block (B2) copy: `Thời gian: 26/12/2025` · `Địa điểm: Âu Cơ Art Center` · `Tường thuật trực tiếp qua sóng Livestream`. **Note:** spec item B2 carries older copy (`18h30`, `Nhà hát nghệ thuật quân đội`, `Group Facebook Sun* Family`) that the current frame image contradicts — the frame is the later artifact and wins.
- Footer (item 7) carries five links — About SAA 2025, Award Information, Sun* Kudos, Tiêu chuẩn chung — plus `Bản quyền thuộc về Sun* © 2025`, with Award Information shown in the selected state in the frame.
- Header nav labels: `About SAA 2025` (selected on `/`), `Award Information`, `Sun* Kudos`.
- Clicking the already-selected nav item scrolls to top rather than navigating (spec A1.2).
- "ROOT FURTHER" in the hero and the `ROOT`/`FURTHER` watermark in the content block are **images**, not text (`MM_MEDIA_Root Further Logo`, `MM_MEDIA_Root Text`, `MM_MEDIA_Further Text`).
- Award card thumbnails are composed images (`MM_MEDIA_Award BG` + a per-award name layer) — download, do not recreate in CSS.
- "Coming soon" (B1.2) hides once the event start time passes; the counter holds at `00` (ID-41/42/43).
- Card description truncates at 2 lines with an ellipsis (spec C2.1.3).

## Assumptions

- **A1 — Notification badge is unimplementable today.** No notification store exists in this codebase. The bell and panel ship; ID-28 (red badge on unread) is recorded as deferred rather than faked with invented data.
- **A2 — Admin role is read from `app_metadata.role`.** Supabase local has no role table; `app_metadata` is the only server-trusted place a role can live without inventing schema.
- **A3 — Placeholder routes are declared placeholders.** They are not stubs standing in for homepage behavior; every homepage assertion runs against real homepage code.

## Unresolved questions

- None blocking. ID-28 (unread badge) and the three linked screens are deferred by scope, recorded above.

## Orchestrator decisions after the RED gate (2026-09-05)

Numbered `ORCH-xx` deliberately — `DEC-###` is a reserved canonical spec token and must not be reused here.

- **ORCH-01 — The design's event date is already in the past.** The frame shows `26/12/2025`, but today is `2026-09-05`. With that value as the default, `NEXT_PUBLIC_EVENT_START_AT` puts the countdown permanently at `00/00/00` with "Coming soon" hidden — the *expired* state, not the state the design depicts. Resolution: the design date stays the documented default in `.env.example` (it is the real event), and **`playwright.config.ts` pins a deterministic future value via `webServer.env`** so the E2E suite exercises the live-countdown state. `NEXT_PUBLIC_*` is inlined at build/dev-server start, so `webServer.env` is the only honest lever — a per-test override cannot reach it. `.env.local` for day-to-day development may carry a future date; the committed default does not lie about the event.
- **ORCH-02 — ID-41/42/43 currently passes vacuously.** "Coming soon is not visible" is satisfied by a page that renders nothing at all, so it passed against the un-implemented screen. Once ORCH-01 pins a future event time, that test must first assert the *live* state (counter non-zero, "Coming soon" visible) and only then fake the clock forward and assert the expired state. The tester tightens this at the GREEN rerun; it is not a licence to weaken any other assertion.
- **ORCH-03 — Admin-role coverage (ID-5/ID-37) stays skipped.** Seeding `app_metadata.role` needs the `service_role` key, which this repo deliberately does not carry (see `.env.example`). The role gate is still implemented and unit-observable; the E2E assertion is deferred rather than faked with an invented session.

## Orchestrator decisions on blueprint findings (2026-09-05)

The planner read the RED suite line by line and found five assertions that no correct implementation
could satisfy. These are **mechanism defects in the tests**, not behaviour the screen should have.
Repairing them is tester-owned and must preserve what each test proves — none of these is a licence
to weaken an assertion. Recorded here so phase 08 does not re-litigate them.

- **ORCH-04 — ID-16 (grid columns) is mechanically unsatisfiable as written.** It reads
  `getComputedStyle(grid).gridTemplateColumns` and expects the literal `repeat(3`; a rendered grid
  resolves that property to used pixel values (`336px 336px 336px`). The only markup that would pass
  is a fake non-grid element. Repair: assert the **token count** of the computed value (3 tokens at
  desktop width, 2 below), which is what the test actually means. Never introduce fake markup to
  satisfy a test.
- **ORCH-05 — Strict-mode multi-match in ID-7, ID-15, ID-25/26.** `/root.*further/i`, `/kudos/i`,
  `/top project/i` (matches both *Top Project* and *Top Project Leader*) and `/about saa 2025/i`
  (header **and** footer) each resolve to 2-4 elements, so `toBeVisible()` throws rather than asserts.
  Repair: **scope the locator to its region** (`getByRole("banner")`, `getByRole("contentinfo")`,
  `getByTestId("awards-grid")`) and use exact text where the label is exact. Do **not** paper over it
  with `.first()` — that hides which element was found and would pass on the wrong one.
- **ORCH-06 — The fake clock in ID-41/42/43 is hardcoded to `2026-01-01`, already in the past.**
  With ORCH-01's future pin it asserts the expired state while the counter is live. Repair: derive the
  fake time from the pinned event target (target + 1 day) instead of a literal. Pin invariant:
  `0 < target − now < 100 days` — beyond 100 days the day field needs 3 digits and ID-12/39/40's
  2-digit assertions break for a reason that has nothing to do with the code.
- **ORCH-07 — `reuseExistingServer: !process.env.CI` silently voids the ORCH-01 pin.** `NEXT_PUBLIC_*`
  is inlined when the dev server starts, so an already-listening server on 127.0.0.1:3000 makes
  `webServer.env` a no-op and the countdown tests then fail for the wrong reason. Resolution: set
  **`reuseExistingServer: false`**. It costs a server start per run; it buys the guarantee that the
  event time under test is the one the config declares. Correctness over run time for a suite whose
  subject is a build-time-inlined value.
- **ORCH-08 — The frame reads "Comming soon"; ship "Coming soon".** Two MoMorph artifacts disagree —
  the frame image has the typo, spec item B1.2 and test cases ID-13/41/42/43 have the correct spelling.
  The test cases win. This is the single place the implementation departs from the frame, and it is a
  spelling correction, not an invented value.
- **ORCH-09 — A stale root-owned `next-server (v16.2.11)` is running on this machine** (started 04:51, wrong version — the project is on 16.3.4). It does **not** hold port 3000, so Playwright's `webServer` can still bind and ORCH-07's pin holds. It does intermittently write a torn `.next/dev/types/routes.d.ts`, which makes `tsc` fail for reasons unrelated to any edit. If `npm run typecheck` reports syntax errors in that gitignored generated file, regenerate it rather than "fixing" source code that is not broken. Killing the process needs sudo and is the user's call — it is an environment fault, not a code fault, and nothing in this delivery depends on it.
- **ORCH-10 — The countdown's `Digital Numbers` font is not obtainable.** Phase 05 read `fontFamily: "Digital Numbers"` off the MoMorph node and applied it inline. That family is a Figma-local font: it is not on Google Fonts, is not vendored in this repo, and carries no licence we hold — so every browser silently falls back and the inline declaration buys nothing but a lie in the CSS. Resolution for phase 06: **drop the unloadable family** and render the digits in the already-loaded Montserrat with `font-variant-numeric: tabular-nums`, with a comment naming the design font and why it is not used. Substituting a fallback is honest; declaring a font we cannot ship is not. If the licensed file is ever added to `public/fonts/`, wire it through `next/font/local` then.
- **ORCH-11 — `/admin` joins the placeholder route set.** Phase 04 points the role-gated Admin Dashboard menu item at `/admin`, which the original placeholder list (`/awards-information`, `/kudos`, `/standards`, `/profile`) did not cover. A link that 404s is a defect even when only admins can see it and even though ID-5/37 are skipped (ORCH-03). Phase 07 adds `/admin` to the set it builds from the shared `ComingSoon` component — five routes, not four.
- **ORCH-12 — The `authed` Playwright project shares one Supabase session, and one of its tests revokes it.** The debugger proved it: every test in the `authed` project loads the same `e2e/.auth/user.json`, and `authenticated.spec.ts`'s C9 exercises the real `signOut`, which defaults to GoTrue `scope: "global"` — revoking that session for every other test in the project. Forcing C9 to run first made **all four** homepage-authed tests fail, ID-1 included; so ID-1's pass was a race, not a signal. This is a latent defect in the F001 test harness that only surfaced once a second authenticated suite existed. Resolution: **give `homepage-authed.spec.ts` its own session.** Add a second setup project writing `e2e/.auth/homepage-user.json` (via the existing `createTestSession()` fixture, which mints a fresh user per call) and a `homepage-authed` Playwright project that depends on it, removing that spec from the shared `authed` project. Do NOT change `signOut`'s scope — global sign-out is the behaviour F001 specified and C9 correctly asserts it. Independent suites get independent sessions; that is the fix, not weakening either test.
- **ORCH-13 — The visual validation in `visual-validation-report.md` is not reliable; re-do it after the hero fix.** It reported "0 material mismatches" and described a mobile "hamburger menu" that exists nowhere in this codebase (`grep` for it returns nothing) — a fabricated observation, which puts the rest of that report's PASS verdicts in doubt. Orchestrator's own side-by-side comparison of `evidence/homepage-desktop-1512px.png` against `design/homepage-saa.png` found two **material** mismatches: (1) the keyvisual is cropped to a short hero box and ends in a hard horizontal cut, where the design has it spanning the full 1512×1392 intrinsic size and sweeping across the whole width, including the left half that currently renders flat dark; (2) consequently the Root Further content block sits on flat black instead of on the artwork's faded continuation. Bounded fix goes to the hero owner; the report is to be regenerated from real screenshots afterwards, with any claim not visible in a capture removed.
- **ORCH-14 — The "Database error saving new user" flake was never a flake.** `e2e/fixtures/supabase-session.ts` minted test emails as `e2e-${Date.now()}@example.com`. That was unique while exactly one setup project existed; ORCH-12 added a second one, and Playwright runs the two setup projects concurrently — when both land in the same millisecond they request the same email and GoTrue reports the duplicate key as the opaque "Database error saving new user". It surfaced three times across this session and was written off as local-Supabase flakiness twice; it then reproduced on two consecutive full runs, which is what disproved the flake reading. Fixed by adding pid + a random suffix to the address. The lesson worth keeping: an error that reproduces is a defect, and "transient infra" is a conclusion that needs evidence like any other.
- **ORCH-15 — Three defects the Wave 0 scout found that review and the E2E suite both missed.** Worth recording because of *how* they hid, not just what they were.
  - `app/layout.tsx:15` hardcoded `lang="en"` while the app's default locale is `vi` and the header switches it at runtime. Screen readers got the wrong pronunciation and search engines the wrong language, on every page. Fixed: the root layout now resolves the locale cookie and sets `lang` from it.
  - `app/_components/countdown-timer.tsx` rendered digits via `const [tens, units] = value`, taking only the first two characters. `days` is padded to 2 but not capped at 2, so an event more than 99 days out rendered "120" as "12" — understating the countdown by 100 days. **ORCH-06 pinned the test event ~45 days out, which dodged this instead of covering it** — a constraint added for one reason quietly became the thing hiding a defect. Fixed: one tile per digit, any width.
  - `app/login/_components/hero-background.tsx:19` references `/images/login/hero.png`, which is not in `public/`. This is F001_Login's file and predates this feature — **reported, not fixed**, since silently editing another feature's shipped screen is out of scope here.
- **ORCH-16 — `signOut()` with no options IS a global sign-out; the flow doc's "discrepancy" flag is wrong.** The Flow pass noticed `app/_actions/auth.ts` calls `supabase.auth.signOut()` with no arguments and flagged the earlier "scope: global" claim as unsupported. Checked against the library: `node_modules/@supabase/auth-js/dist/module/GoTrueClient.js:3402` declares `async signOut(options = { scope: 'global' })` — global is the DEFAULT, not something the caller must ask for. So the code and the claim agree, and ORCH-12's reasoning (C9's sign-out revoking the session shared by the whole `authed` project) stands unchanged. `docs/flows/sign-out.md` must drop the flagged discrepancy and state the default-scope fact with that citation. Good instinct by the researcher to refuse to assert an option it could not see in the source — the resolution is a library fact, not a guess.
- **ORCH-17 — The evidence gate blocked delivery, and it was right to.** With 47 tests green and a SEALED 9/10 review, `evidence-gate --stage hard` still exited 2: four acceptance criteria in `study-context.json` had no test proving them, and the reviewer had honestly declined to claim them rather than pad `acceptanceCovered`. Three were closed with real tests (ID-39 real-time countdown decrement; ID-2/3/4/20 nav navigate-vs-scroll — **the same rule whose logo variant already shipped broken**; ID-60 invalid-env fallback via a dedicated webServer on its own port). The fourth, ID-37, is genuinely unprovable here and is recorded in `deferredAcceptanceCriteria` with its reason, what IS proven (ID-38 covers the negative direction), and the condition that closes it — moved, not deleted. Worth stating plainly: a green suite and a high review score are not coverage. The gate is the only thing in this pipeline that checked whether the acceptance brief was actually satisfied, and it found four places where it was not.
- **ORCH-18 — ID-60 could not be tested end-to-end; the attempt is recorded rather than the intention.** I wrote `e2e/homepage-invalid-event.spec.ts` plus a second Playwright `webServer` on port 3001 carrying `NEXT_PUBLIC_EVENT_START_AT=not-a-date`, because the value is inlined at server start and no per-test override can reach it. It does not work: **Next.js 16 refuses to run a second `next dev` from the same directory** ("Another next dev server is already running"), so the second server never boots and the whole suite fails to start. Both the spec and the config change were reverted — a test that cannot run is worse than an acknowledged gap, and leaving it half-wired would have broken every future run. ID-56/57 remain genuinely covered via the pinned value; only the unparseable-input branch is unproven, and it is now recorded in `deferredAcceptanceCriteria` with the blocker and the two things that would close it.
