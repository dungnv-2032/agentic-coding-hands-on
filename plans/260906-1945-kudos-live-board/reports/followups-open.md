# Open follow-ups after F004 delivery

Nothing here blocks the delivered feature. All of it is recorded so it does not quietly disappear.

## Docs debt the doc-writer deliberately did not half-fix

1. **`docs/generated/entities.md` is wholesale stale — run `/tkm:rebuild-spec --artifact entities`.**
   Its entire premise is "this repo owns zero tables, zero migrations, zero SQL, every Supabase call
   is `auth.*`". F004 makes all four claims false: 10 RLS-enabled tables, a migration and a seed.
   That is not a row-level edit, so `doc-writer` correctly refused to surgically patch it. This is
   the single most misleading file in `docs/` right now.
2. **`docs/generated/user-stories.md` has no F004 entries at all** (US001–US008 stop at F003), while
   `docs/features/F004_KudosLiveBoard/functional-spec.md` defines 8 stories locally numbered
   US001–US008 that collide with F001's codes. They need renumbering to US009–US016, full sections,
   and a Screen→US map update — the same treatment F002 received. Needs a dedicated add pass.

## Product decisions still open (from `clarifications.md` § Unresolved questions)

These were deliberately not built, and each is recorded there with its reason:

3. **Test case `71b3ef43`** wants an unauthenticated visitor redirected to `/login`, which
   contradicts the shipped public-route design. Needs a product call on whether the whole Kudos
   surface is members-only.
4. **Special-day ×2 heart accrual** (`31936b72`) and the **account-balance half of the heart rules**
   (`63645b03` / `91e102ba`) need persistence plus the `Admin - Setting` configuration surface.
   The `x2` flame on the sidebar is displayed per the frame, not simulated.
5. **The hero Sunner search has no destination screen** — it submits to `/profile` (`ComingSoon`)
   with the query. The real search-results screen exists for iOS only.
6. **Spec CSV `qa` note on C.4.1** — distinguishing a normal like from a special-day like so the
   right number of hearts is revoked — is a backend concern with no client-side expression. It
   belongs to whichever commission builds the write side of Kudos.

## Reviewer's low findings

7. **`e2e/kudos-live-board.spec.ts` is 616 lines**, over the repo's 200-line cap. Not a regression:
   `homepage.spec.ts` (604), `award-system.spec.ts` (466) and `login-screen.spec.ts` (310) already
   exceed it, so E2E specs are an established (undocumented) exception. Worth either splitting the
   specs by section or writing the exception down in `docs/code-standards.md` — currently the rule
   says one thing and every spec in the repo does another.
8. The stale `48` department count in `e2e/fixtures/kudos-constants.ts` and the K-3 test title was
   **fixed** during delivery (both now read 50, the ratified count).

## Environment gotchas worth knowing

9. **HMR is broken in this WSL2 setup** — the dev server's `_next/hmr` WebSocket handshake fails, so
   edits do NOT hot-reload and the browser keeps serving stale code. This cost real time this
   session: a layout fix looked like it had not worked when the dev server was simply serving the
   pre-edit bundle. Restart `npm run dev` after editing, or trust the Playwright runs (which boot
   their own server) over a long-lived dev server.
10. Playwright's bundled Chromium needs `libnspr4`/`libnss3`, vendored under `.playwright-libs/`.
    `playwright.config.ts` wires `LD_LIBRARY_PATH` for the test runner; an ad-hoc script must set it
    itself. The Playwright **MCP** server wants system Chrome, which is absent — use the project's
    bundled Chromium instead.
