# Implementer memory

- [Local Postgres access](local-postgres-access.md) — no `psql` binary here; go through `docker exec supabase_db_my-app psql -U postgres`.
- [Proving code without a unit runner](proving-code-without-a-unit-runner.md) — compile the real modules to CJS in the scratchpad and run them against the real local Supabase.
- [Browser proof without owning e2e files](browser-proof-without-owning-e2e-files.md) — throwaway Playwright config under repo-local `.probe-tmp/`, run with `--config`, then deleted.
