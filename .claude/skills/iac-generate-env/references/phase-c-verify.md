# Phase C — Connect, then verify

Three steps: wire the layers, re-validate them, and optionally inspect the structure.

Path keys resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

---

## Phase C — Connect modules

After all layers are generated, **execute the all-layers wiring inline, in the same turn**.

> ### This is the step most prone to the dispatch-and-wait mistake
>
> Do the wiring yourself with Write, Edit and Bash. Do **not** dispatch a connector child agent and
> end your turn waiting for it — that stalls the pipeline and leaves a half-built environment with
> un-wired cross-layer TODOs.
>
> Treat it as a **synchronous continuation of Phase B**, not a hand-off.

The wiring rules themselves are owned by `tkm:iac-connect-modules`. Invoke that skill; do not restate
its matching algorithm here.

### The graph is acyclic — keep it that way

Every Route53 and ACM edge points **downstream from `1.general`**. The only `2.frontend ← 3.backend`
edges are the pre-existing one-directional ones — the CloudFront origin and the `ecs_frontend` egress
security group. There is no `3.backend ← 2.frontend` cert edge.

Apply order stays `1.general` → `3.backend` → `2.frontend` → `4.database`, then the optional layers.

---

## Phase C.1 — Verify

### C.1.0 — Backend hygiene self-check

**Before validating**, grep every generated `_backend.tf` for a stray `dynamodb_table` **assignment**:

```bash
grep -rnE '^[[:space:]]*dynamodb_table[[:space:]]*=' <ENV_DIR>/*/_backend.tf
```

> **Anchor the match to the assignment line.** The `^[[:space:]]*` prefix matches only a real
> argument, optionally indented — never a `#`-prefixed comment. The backend template's own guidance
> comments legitimately contain the word `dynamodb_table`, and those comments survive into the
> emitted file and **must not be deleted**.

If a line matches, delete **that matched assignment line** from each file — the block keeps
`use_lockfile = true` and no `dynamodb_table`. Re-run the grep to confirm it returns nothing.

This is belt-and-braces. The canonical template already omits the argument, and both the inline gate
and the bestpractice reviewer flag it downstream. Stripping it here keeps one-shot output clean so
neither guard ever has to fire. Record `backend dynamodb_table: none` or `stripped N` in the summary.

### Re-validate each layer

For each layer the variant declared, run these **separately, one layer at a time**:

```bash
make init e=<env> s=<layer>          # from {MAKE_ROOT}
terraform validate                    # in the layer directory
```

- **A failing `make init` on a fresh environment is expected**, not an error — the backend bucket may
  not exist yet. Record `init: pending backend bootstrap` and **continue to the next layer**. Do not
  block, do not retry in a loop.
- Capture each `terraform validate` result as `Success` or `Error: <first line>` for the summary
  table. Read the output directly; do not pipe through temp files.

> **This phase runs `make init` and `terraform validate`, and nothing else.** It never runs `plan` or
> `apply`, and never wraps a high-impact command.
>
> **Be precise about `init`: it is not local.** With a `backend "s3"` block, `terraform init`
> authenticates to AWS and reads the state object — that is why a fresh environment's failure is
> expected here rather than surprising. It does not modify infrastructure, but "read-only and local"
> was wrong on both halves, and one case does write: with pre-existing **local** state, `init` offers
> to copy that state up, and a non-interactive run either hangs on the prompt or aborts. A generated
> environment has no local state, so the case does not arise here — but do not run `init` anywhere
> that does.
>
> `tkm:iac-connect-modules` bans `make init` outright for its own reasons: it runs standalone against
> environments it did not create, where local state may well exist. The ban is that skill's, correctly
> scoped to it, and does not extend here.

---

## Phase C.2 — Structural verification (optional)

Confirm the generated structure before the summary: modules scaffolded, the env file tree,
`_variables.tf` symlinks per layer, and SOPS provider block placement.

Read-only inspection only — `ls`, `find`, `grep`, `sort`, `printf`, and a symlink test per layer.

**Inspect, never mutate.** Do not pipe to a shell, do not redirect into a system path.
