---
name: tkm:iac-generate-module
description: >
  Generate one Terraform service into a layer of a multi-layer AWS environment: resolve or scaffold
  the local module, emit the module call with TODO placeholders for cross-module inputs, and write the
  layer's backend, outputs, tfvars and SOPS secrets seed.
  Every write is idempotent — re-running against existing files changes nothing. Cross-module wiring
  is a separate step by design.
  Use this to add a service to an existing environment, to scaffold a new local Terraform module, or
  to generate several services into one layer at once.
  SKIP: scaffolding a whole multi-layer environment from a blueprint (→ tkm:iac-generate-env);
  resolving the TODO placeholders this skill emits (→ tkm:iac-connect-modules);
  ad-hoc single-directory Terraform with the base conventions (→ tkm:infra).
category: iac
roles: [engineer, devops]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
argument-hint: "<service> [env] [--layer <n>] [--batch]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: deployment-infrastructure
triggers:
  - "generate terraform module"
  - "scaffold terraform module"
  - "add a service to the env"
  - "generate service tf"
  - "create local module"
  - "sinh module terraform"
---

# tkm:iac-generate-module

Writes one service into `{ENV_DIR}/{layer}/`, scaffolding the local module first if it is not there.

All paths resolve through
[`layout-contract.md`](../_shared/extras/iac/layout-contract.md). This skill hardcodes none.

| Argument | Effect |
|---|---|
| `<service>` | Required. Normalized and alias-resolved before use. |
| `env` | The target environment. |
| `--layer <n>` | The target layer. Normalized (`backend` → `3.backend`). |
| `--batch` | Several services in one run. Suppresses per-service prompts **only**. |

## Validate before anything reaches a path or a shell

`<service>`, `env` and `--layer` are all interpolated into filesystem paths and shell commands.
Constrain each to `^[A-Za-z0-9._-]+$` and reject anything else **first**.

## What it writes

| File | Rule |
|---|---|
| `{MODULE_DIR}/{service}/` | scaffolded only when absent → [`module-scaffold.md`](./references/module-scaffold.md) |
| `<service>.tf` | only if absent. Exists → single mode **asks**, batch mode **skips** |
| `_backend.tf` | only if absent; patched in place for SOPS |
| `_data.tf` | only if absent |
| `_outputs.tf` | created if absent; append only outputs not already declared |
| `{ENV_DIR}/_variables.tf` | **only if absent** — it is the symlink target for every layer |
| `terraform.{env}.tfvars` | create-or-append, never overwrite |
| `{DEPS_ROOT}/sops/secrets.{env}.yaml` | seeded only when a sensitive reference was emitted |
| `.gitignore` | verify-then-append (`{WORK_DIR}/` only) |

Order, and what must never be overwritten:
[`env-file-contract.md`](./references/env-file-contract.md).

## Every write is idempotent

Re-running against an existing target is a **no-op**. `git diff` after a second run is empty.

Four guards, all owned by
[`idempotency-matchers.md`](../_shared/extras/iac/idempotency-matchers.md):

- **tfvars** — a variable is present **iff** a non-comment line matches `^<varname>\s*=`. Without
  this, every re-run appends a duplicate assignment and Terraform hard-errors.
- **SOPS keys** — the **commented-aware** matcher `^\s*#?\s*<KEY>\s*:`. A blueprint seeds some keys
  already commented out; the naive matcher re-appends them on every run, forever.
- **Modules** — never re-scaffold over a module folder that exists. It may have been hand-edited.
- **Vendored payloads** — file-exists guard, evaluated per file.

Plus two owned by [`env-file-contract.md`](./references/env-file-contract.md), because they are
emission rules rather than shared matchers:

- **`_outputs.tf`** — an output is present **iff** a line matches `^\s*output\s+"<name>"`. Append only
  what is missing, or a second run hard-errors with `Duplicate output definition`.
- **`<service>.tf`** — single mode asks, **batch mode skips**. An "ask" guard is unreachable under
  `--batch`, which suppresses prompts; skipping is what actually guards the file there.

This is not a nicety. The whole point of a generator a team runs repeatedly is that the second run
costs nothing and destroys nothing.

## The plaintext secrets file

When a service has sensitive inputs, this skill writes an **unencrypted** YAML secrets file into the
user's repository and tells them to fill it with real values.

Two things must therefore happen in the same run:

1. **Verify-then-append `.gitignore`** entries for `{WORK_DIR}` and the SOPS directory. Upstream had
   both a `.gitignore` entry and a credential-detecting pre-commit hook catching this mistake.
   **Neither exists in a consumer's repository by default.**
2. **Warn in the summary, prominently**, that the file is plaintext until encrypted.

A secret committed to git history stays in git history. This is the one failure here that no later
run can undo.

## `--batch` does not suppress the gate

`--batch` suppresses **per-service prompts**. It does not skip validation, and it does not skip the
wiring step.

Because prompts are suppressed, every guard that would have *asked* becomes a guard that **skips**.
An existing `<service>.tf` is skipped, not overwritten. If all services were skipped, say so and stop
rather than reporting success over an empty result.

All cross-module inputs are TODO placeholders regardless of mode, so a batch run produces a layer
that is generated but not yet wired — exactly like a single run, several times over. The gate that
runs after wiring is the only thing standing between batch output and a broken environment.

## Rules

- **Placeholders, never guesses.** An unresolvable input gets a `# TODO`, not an invented value.
- **Never overwrite a layer's `_variables.tf`** — it is a symlink to the env-level file.
- **Never re-scaffold an existing module folder.**
- **Never touch an encrypted secrets file** — there is no KMS access here.
- **Never emit a git-tag, SSH, or HTTPS module source.** Local relative path only.
- **Never hardcode a region, account ID, or secret.**
- **Never run `terraform apply`, `destroy`, `import`, or `state rm`**, and never `make apply`,
  `destroy`, or `state_rm`.
- **Never create or modify AWS credentials.**
- Resolve the project prefix **once per run**, then use it everywhere in that run.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "The module folder exists but looks wrong — I'll re-scaffold it." | Never. It may be hand-edited. Reuse it and emit the call. |
| "I'll fill in the AMI id with a plausible one." | A wrong AMI applies cleanly and boots the wrong image. Emit a TODO. |
| "tfvars already has this variable commented out, so it's missing." | A commented line is not present, but a *filled* one is. Use the matcher. |
| "It's a batch run, so the gate can come later." | The gate is the only check batch mode has. |
| "The secrets file is empty, so it's harmless to commit." | It is the file the user is about to fill. Warn before it holds anything. |
| "Three `../` or four — I'll count them." | Use the contract keys. Module depth is 3, SOPS is 4. |
| "An S3 backend needs a `dynamodb_table` for locking." | Not since `use_lockfile`. Emit the canonical block as written. |
| "The backend has a hardcoded region — I'll use `var.region`." | A backend block cannot read variables. That change breaks `init`. |
| "`<service>.tf` exists; I'll ask." | Not in batch mode. There is nobody to ask. Skip it. |

## Permitted shell commands

```
terraform fmt        # format what was written
terraform validate   # syntax check, no backend
make symlink e=<env> s=<layer>       # from {MAKE_ROOT}
make symlink_all e=<env>             # from {MAKE_ROOT}
```

Anything else is a defect in this skill, not a judgement call at runtime. In particular: no
`terraform apply|destroy|import|state rm`, no `make apply|destroy|state_rm`, no `aws` CLI call.

The `make` targets live in the project's own Makefile under `{MAKE_ROOT}` — **not** at the repository
root. Print the working directory with them, and if no Makefile is there, print the `terraform`
equivalents and say so.

See [`allowed-tools-policy.md`](../_shared/extras/iac/allowed-tools-policy.md).

## After generating

Resolve every `# TODO`, then run `tkm:iac-connect-modules` to wire the cross-module ones. That step
runs the validation gate.

## References

- [`terraform-conventions.md`](./references/terraform-conventions.md) — module shape, naming, encryption defaults, hardening toggles, multi-instance
- [`env-service-contract.md`](./references/env-service-contract.md) — layer file shapes; **sole owner of the canonical backend block**
- [`service-alias-map.md`](./references/service-alias-map.md) — service and layer normalization
- [`module-scaffold.md`](./references/module-scaffold.md) — the five-file skeleton and the duplicate-scaffold guard
- [`env-file-contract.md`](./references/env-file-contract.md) — emission order, overwrite guards, `.gitignore`, the plaintext warning
