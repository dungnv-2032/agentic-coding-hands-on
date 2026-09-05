# Doc-writer verdict — SAA 2025 Homepage docs impact

**Verdict: update needed.** Found real drift beyond the three assigned items — all fixed below.
Every claim was checked against source before being written (file:line cited in each edit).

## Files changed (11)

| File | What changed | Why |
|---|---|---|
| `docs/flows/sign-out.md` | Removed the wrong "not global sign-out" discrepancy flag; states `signOut()` **is** global scope because GoTrue's own default is `{ scope: 'global' }` | `node_modules/@supabase/auth-js/dist/module/GoTrueClient.js:3402` confirms `async signOut(options = { scope: 'global' })` — no options passed means that default applies (ORCH-16) |
| `docs/generated/user-stories.md` | None needed | Already correctly renumbered F002 to US005/US006 with a traceability note — this file was right, the feature specs were wrong |
| `docs/features/F002_HomepageSaa/functional-spec.md` | Renumbered US001→US005, US002→US006 (added traceability note); fixed FR-002/Scope/§10 from "4 route placeholder" to "5" (`/admin` missing); fixed `status: draft`→`implemented`; fixed SCR002 "draft" marker; closed RISK-02 (assets confirmed exported); fixed F001 dependency wording (no longer "after promote") | `US###` is a global code (`code-formats.md`) — local numbering collided with F001's US001-004. Code has 5 `ComingSoon` routes incl. `/admin` (`app/admin/page.tsx`, confirmed by code comment "the five ComingSoon placeholders" in `use-scroll-to-top-if-current.ts`). `public/images/home/*` has all 15 referenced assets |
| `docs/features/F002_HomepageSaa/technical-spec.md` | Same US renumbering; removed all `(planned)`/`TBD (draft)` markers, replaced with real file:line citations per action (A1-A3); expanded Components table with real files; A3 now lists 5 routes; rewrote §5.2-5.5 (Assumptions/Unresolved Questions/Source References/Artifact References) to reflect as-built code | Task items #2 and #3 — file described "planned"/"chưa có source code" for fully shipped code |
| `docs/features/F001_Login/functional-spec.md` | Fixed `SCR-login`→`SCR001_Login` in two places (§2 CAP-01 row, §6 Screens table), removed stale "draft — mã chính thức cấp khi promote" | Screen was already promoted to `SCR001_Login` (`docs/screens/SCR001_Login/` exists) |
| `docs/features/F001_Login/technical-spec.md` | Removed all `(planned)`/`TBD (draft)` markers across all 6 actions (A1-A6), Components table, SM-001, INT-001, A0; **fixed a wrong claim** — A4's Result said `setLocale` needs no manual `revalidatePath` call, but the code explicitly calls `revalidatePath("/", "layout")` (`app/_actions/locale.ts:26`, required now that F002 also depends on it); enriched A2/A3 descriptions with real security logic (fail-fast on missing site URL, open-redirect defenses); rewrote §5.2-5.5 | Task item #3, plus one genuine factual error found while verifying |
| `docs/screens/SCR002_Homepage/spec.md` | Fixed `status: draft`→`implemented`, removed stale "draft" marker; **fixed a real bug** — E10 "Admin Dashboard" was documented as navigating to `/profile (placeholder)`; code (`account-menu.tsx:99-107`) links it to `/admin`, a separate route; split the Navigation Exits row accordingly | Verified against `app/_components/account-menu.tsx` |
| `docs/flows/homepage-browse-and-navigate.md` | Cleaned up a confused "5 route đích (4 route placeholder + ...)" intro line and a step-11 "4 route đích còn lại... và cả /admin tuy không nằm trong danh sách 4 điểm gốc" into a plain, consistent "5 route placeholder" statement | Same 4-vs-5 route drift as the feature specs, propagated into the flow doc |
| `docs/system/permissions.md` | Fixed intro note claiming `docs/generated/permissions-matrix.md` "doesn't exist yet" (it does, with PERM001-005) and cited those 5 codes inline where each boundary is described | `docs/generated/permissions-matrix.md` itself says the system-layer file "predates this Core pass and should be reconciled against this one" |
| `docs/setup/local-development.md` | Added `NEXT_PUBLIC_EVENT_START_AT` to the env-var table; rewrote §5 (was "19 test case, 3 project") to the current 6 projects / 51 tests (`setup`, `anon`, `authed`, `homepage-auth-setup`, `homepage-authed`, `visual-capture`), noting `visual-capture` is on-demand only | Verified live via `npx playwright test --list` (51 tests, 10 files) — cross-checked against `git diff -- playwright.config.ts` to rule out a mid-edit race from a concurrent session (an earlier read caught a since-reverted `invalid-event` project; the diff confirmed 6 projects is the real, stable state) |
| `README.md` | Fixed `http://localhost:3000`→`http://127.0.0.1:3000` (the doc's own setup guide says `localhost` silently looks logged-out — the README was contradicting itself); added a "Homepage" section describing F002, the 5 placeholder routes, and the shared header/sign-out | `app/page.tsx` is no longer the create-next-app boilerplate; no README section existed for it |

## Files assessed, left alone (with reason)

- **`docs/system/architecture.md`** — already accurate; already documents 5 placeholder pages and the shared component surface correctly (Core-pass reconciled).
- **`docs/generated/route-list.md`, `feature-list.md`, `entities.md`, `api-map.md`, `behavior-logic.md`, `permissions-matrix.md`, `screen-list.md`** — spot-checked, already correct (route-list.md already lists all 5 routes incl. `/admin` with the no-server-check note).
- **`docs/flows/google-oauth-sign-in.md`, `session-refresh-and-route-guarding.md`, `locale-switching.md`** — spot-checked for stale flags/wrong US codes; clean.
- **`docs/screens/SCR001_Login/spec.md`** — frontmatter already `status: implemented`; no wrong facts found (unlike SCR002's E10 bug). Still carries 17 `TBD (draft)` source citations, same as SCR002. Left alone: these are honest "not yet reconciled" placeholders, not false claims — reconciling them file-wide is `rebuild-spec` scale (>3 changed source files implicated), not a spot-fix. **Advisory:** `Run /tkm:rebuild-spec --artifact SCR001_Login,SCR002_Homepage` to close out the remaining TBD sources.
- **`docs/troubleshooting/login-oauth-gotchas.md`** — scoped explicitly to `proxy.ts`/callback gotchas; verified all 4 entries still match code exactly (cookie-rotation copy, origin-pinning, hero.png RISK-01 — confirmed still missing from `public/images/login/`, nonce check). No homepage-specific gotcha rises to this file's bar yet.
- **`docs/system/overview.md`, `glossary.md`** — grepped for staleness markers, none found.
- **`docs/decisions/`, `docs/journals/`** — not opened (out of scope per instructions).

## Note on one moving target

While checking Playwright projects, an initial read of `playwright.config.ts` showed a 7th
project (`invalid-event`) and a dual webServer (port 3001) that a second read moments later did
not have. `git diff -- playwright.config.ts` confirmed the working tree was mid-edit from a
concurrent session; the settled diff has 6 projects and one webServer. Docs now describe that
settled state. If `invalid-event` reappears and stabilizes, `docs/setup/local-development.md` §5
and `docs/features/F002_HomepageSaa/functional-spec.md` FR-402 should get a follow-up.

**Status:** DONE
**Summary:** 11 files updated. Fixed all 3 assigned items (sign-out global-scope flag, US###
collision, stale "planned"/technical-spec staleness in both F001 and F002) plus 4 additional
verified defects found while reading source: a wrong Admin Dashboard destination in
SCR002_Homepage's spec, a wrong "no revalidatePath needed" claim in F001's technical-spec, a
README `localhost` instruction that contradicted the project's own setup guide, and a stale
"permissions-matrix.md doesn't exist" note in `docs/system/permissions.md`.
**Concerns/Blockers:** None blocking. Two screen specs (SCR001_Login, SCR002_Homepage) still carry
many honest `TBD (draft)` source citations — flagged above as an advisory for a future
`rebuild-spec` pass, not left silently.
