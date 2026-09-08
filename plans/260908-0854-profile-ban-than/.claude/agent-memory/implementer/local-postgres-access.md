---
name: local-postgres-access
description: There is no `psql` binary on this machine — query the local Supabase Postgres through `docker exec supabase_db_my-app psql -U postgres`
metadata:
  type: project
---

`psql` is NOT on PATH in this WSL2 environment (`which psql` → "psql not found"), even though
`.claude/rules/development-rules.md` says to "reach for the `psql` bash command" when debugging
means querying Postgres. The local Supabase database is reachable only through its container:

```
docker exec supabase_db_my-app psql -U postgres -X -q -c "select …"
# add -A -t for bare, pipe-separated values that are easy to parse in a script
```

Connection strings (`psql postgresql://postgres:postgres@127.0.0.1:54322/postgres`) fail for the
same reason — there is no client to run them.

**Why:** measured while gathering ground truth for F006 phase 05; the first attempt used the
connection string from `npx supabase status` and exited 127.

**How to apply:** any time a phase needs ground truth from the database (verifying a count a query
returned, reading a row as superuser, constructing test data), go straight to `docker exec`. Note
that `npx supabase status` still prints a `DB_URL` — that URL is correct, it is only the client
that is missing.
