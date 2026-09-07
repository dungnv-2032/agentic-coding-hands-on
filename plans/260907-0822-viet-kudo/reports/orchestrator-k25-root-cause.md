# K-25 root cause — a revoked session, not a slow one

## What it looked like

`K-25 — heart persists across page reload` (F004's authed suite) failed intermittently whenever the
full multi-file suite ran, and passed every time the kudos suites ran alone. It also left a
`kudos_likes` row behind, so repeat runs diverged.

Three explanations were offered before the real one, each plausible and each wrong:

1. **"2-worker contention makes the Postgres round trip exceed the 5s `expect` timeout."** Phase 12
   reported this, and a tester pass then raised the global `expect` timeout to 15s and K-25's own
   test timeout to 60s. It did not fix it — and the same tester later observed K-25 still failing at
   **25.4s**, comfortably inside a 60s timeout, which by itself disproves the timeout theory.
2. **"The dev server crashes under load, cascading failures."** Offered after the timeout theory
   failed. `ERR_CONNECTION_REFUSED` did appear in one of that agent's runs, but not in mine, and the
   compose tests were failing in runs where the server was demonstrably up.
3. **"Test infrastructure can't sustain 88 concurrent tests."** The final escalation. Also wrong.

## What it actually was

`e2e/authenticated.spec.ts`'s **C9** test signs out with Supabase's default `scope: 'global'`, which
**revokes the session**, not just the browser's cookie. The `kudos-authed` project was configured to
load `storageState: "e2e/.auth/user.json"` — the *same* session file the `authed` project uses. So
whenever `authenticated.spec.ts` ran in the same invocation, every kudos-authed test that happened to
load a page after C9 was operating with a dead session and got bounced by the route guard.

That is why the suites passed alone and failed together, and why more files in the run made it look
load-related: more files meant more chance of C9 landing first.

**This repo had already found and solved this exact problem once.** `e2e/homepage-auth.setup.ts`
exists for precisely this reason and says so in its own header comment: *"authenticated.spec.ts's C9
test calls signOut() with default scope:'global', which revokes the ONE shared session for every test
in the authed project... Under worker concurrency, homepage-authed tests fail nondeterministically
depending on whether their page-load happens before or after C9's revocation."* The `homepage-authed`
project was given its own setup and its own `homepage-user.json` as the fix. The kudos projects were
nonetheless wired to the shared session — in the F004 commission and again here.

## The fix

Mirror the established pattern rather than invent a new one:

- **`e2e/kudos-auth.setup.ts`** (new) creates an independent session and writes
  `e2e/.auth/kudos-user.json`, adapted from `homepage-auth.setup.ts`.
- **`playwright.config.ts`**: a new `kudos-auth-setup` project runs it; `kudos-authed` now uses
  `storageState: "e2e/.auth/kudos-user.json"` and `dependencies: ["kudos-auth-setup"]`.
- The `setup` project's `testMatch` was narrowed from `/^((?!homepage).)*auth\.setup\.ts$/` to
  `/^((?!homepage)(?!kudos).)*auth\.setup\.ts$/` so each per-suite setup runs in exactly one project
  instead of twice.
- The 15s `expect` timeout was **kept but scoped to the `kudos-authed` project only**, not global.
  It is defensible on its own merits — the heart toggle is deliberately server-authoritative, so
  those assertions really do wait on a Postgres round trip — but raising it globally would have
  tripled how long every failing assertion takes to fail everywhere else, and a full compose RED run
  already takes ~25 minutes.
- The `afterEach` cleanup was kept, with one correction: it had filtered on a **hardcoded auth-user
  uuid** snapshotted from one run, while `auth.setup.ts` signs up a fresh user with a new uuid every
  run. The delete could therefore never match the row it was meant to remove, and the surrounding
  `try/catch` swallowed the miss — a cleanup that only looked like it worked. It now deletes by
  `kudos_id` alone, which is safe because the seed deliberately creates zero `kudos_likes` rows, so
  any row in that table is test residue by definition.

## Evidence

Full 10-file suite, all projects, three consecutive runs (run 1 aborted on a stale `next dev`
holding port 3000 — `EADDRINUSE`, nothing to do with the tests):

| Run | Exit | Result | `kudos_likes` after |
|-----|------|--------|---------------------|
| 1 | 1 | aborted: port 3000 in use | 0 |
| 2 | **0** | **144 passed** | **0** |
| 3 | **0** | **144 passed** | **0** |

Per-project distribution in a green run: `setup` 1, `kudos-auth-setup` 1, `anon` 78, `authed` 3,
`kudos-authed` 61. Log: `evidence/full-suite-green-run.log`.

144 passing covers all 62 compose assertions, F004's 27 board assertions, and the homepage,
award-system, login-screen, authenticated, smoke, route-guard and callback-security suites — with the
suite idempotent across runs.

## The lesson worth keeping

Three successive diagnoses attributed this to load, and each led to a change that made the tests
slower rather than correct. The tell was there the whole time and was ignored twice: **it passed in
isolation and failed in company.** That shape points at shared mutable state between test files, not
at resource pressure. Raising a timeout is what you do when something is slow; it cannot fix
something that has been revoked.

The second lesson is cheaper: the repo already contained the answer, written in a header comment
above a file created to solve the identical problem. Reading `homepage-auth.setup.ts` before
theorising would have cost two minutes.
