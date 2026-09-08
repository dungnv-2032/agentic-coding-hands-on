---
name: proving-code-without-a-unit-runner
description: This repo has no unit-test runner, so non-UI logic is proven by compiling the real modules to CJS in the scratchpad and running them against the real local Supabase
metadata:
  type: project
---

`package.json` ships only `dev/build/start/lint/typecheck/test:e2e/db:types` — there is no unit
runner, and adding one is a `package.json` change that phase-scoped file ownership usually forbids.
The established way to satisfy RED-first and produce real evidence:

1. Write the checks BEFORE the modules exist (module-not-found *is* the RED — capture it).
2. Compile the real files to CJS with a `tsconfig` **in the scratchpad**, `rootDir` at the repo
   root and `paths: {"@/*": ["./*"]}`, then `sed` the emitted `require("@/…")` to the outDir.
   `types: []` + `typeRoots: [<repo>/node_modules/@types]` is needed or tsc fails on `'node'`.
3. Run against the real local Supabase with `@supabase/supabase-js` and real `auth.signUp`
   sessions, not fabricated rows.
4. To exercise a `"use server"` action outside Next, substitute ONLY
   `@/lib/supabase/server`'s `createClient` (its `cookies()` needs a request scope). The action
   module itself stays the real compiled file, so its validation and identity resolution are real.
5. Store the transcript AND the harness source under `evidence/` as `.log` files — never `.js`,
   because eslint's `no-require-imports` reaches into `plans/` and turns `npm run lint` red
   (measured in F006 phase 04).

**Why:** phase 04 proved its mapper this way but only as a pure-function transcript; phase 05
extended it to hit PostgREST, which caught three things a pure test could not — that the seed has
no duplicate `sent_at` (so a keyset tie must be constructed), that the reader view masks a
`count(*)` on someone else's anonymous sends, and that every seeded sunner has ≥1 received Kudo
(so the zero-received branch has no seed subject).

**How to apply:** reach for this whenever a phase owns non-UI logic and the acceptance criteria say
"measure", "prove" or "paste the transcript". Reset the database first
([[local-postgres-access]] for ground truth), and reset again after any mutating measurement.
