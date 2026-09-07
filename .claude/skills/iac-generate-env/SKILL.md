---
name: tkm:iac-generate-env
description: >
  Scaffold a complete multi-layer AWS Terraform environment from a blueprint in one continuous run —
  shared env files, SOPS secrets seed and KMS key, every layer generated in the variant-correct order,
  cross-layer wiring, and a validation gate. Supports three frontend variants (none, static-spa, ssr)
  and optional messaging, delivery and monitoring layers, each a clean regression boundary.
  Every write is idempotent: a second run against the same environment changes nothing and creates no
  second KMS key.
  Use this to stand up a new environment, add a blueprint's layers to an existing one, or regenerate
  an environment after changing a toggle.
  SKIP: adding a single service to an existing layer (→ tkm:iac-generate-module); resolving TODO
  placeholders or running the validation gate on its own (→ tkm:iac-connect-modules); reviewing a
  finished environment (→ tkm:iac-review).
category: iac
roles: [engineer, devops]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
argument-hint: "[env] [--blueprint <name>] [--project <name>]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: deployment-infrastructure
triggers:
  - "generate environment"
  - "scaffold terraform env"
  - "create multi-layer env"
  - "generate env from blueprint"
  - "new AWS environment terraform"
  - "sinh môi trường terraform"
---

# tkm:iac-generate-env

One blueprint in, one fully-wired environment out.

All paths resolve through
[`layout-contract.md`](../_shared/extras/iac/layout-contract.md). This skill hardcodes none, and
contains **no HCL** — every template lives in `references/`.

## Runs in a single continuous turn

Phases A → D run **sequentially, in one uninterrupted turn**, until the environment is generated
**and** wired. The deliverable is a fully-wired environment, never a half-built one a human has to
resume.

**Accomplish every step with Write, Edit and Bash.** Do **not** spawn, dispatch, or hand off to a
sub-agent anywhere in this flow.

The moment a child agent is dispatched, this turn ends and the pipeline stalls — there is nothing to
wait on, so nothing arrives. The environment is left half-generated with un-wired cross-layer TODOs
and the user has to unpick it by hand. "Invoke the module generator for this layer" means **execute
that logic here, with your own tool calls**, following the contracts in `references/`.

## Flow

| Phase | What happens |
|---|---|
| **Interview** | 16 fields, one at a time, all validated → [`blueprint-interview.md`](./references/blueprint-interview.md) |
| **A** | Shared env files, SOPS seed, KMS key → [`phase-a-shared-env.md`](./references/phase-a-shared-env.md) |
| **B** | Layer loop in variant-correct order, then B.2 and the symlink → [`phase-b-execution.md`](./references/phase-b-execution.md) |
| **C** | Wire the layers inline, then re-validate → [`phase-c-verify.md`](./references/phase-c-verify.md) |
| **Gate** | Invoke `tkm:iac-connect-modules`'s validation gate — cap **2** |
| **D** | Summary and reminders → [`phase-d-summary.md`](./references/phase-d-summary.md) |

**The layer set and its order come from the contract's `LAYERS`** and the variant, not from the
folder names. Layer numbers are labels; `2.frontend` applies **after** `3.backend`.

## Rules

- **Single continuous turn.** Never dispatch a sub-agent inside this flow.
- **Every write is idempotent.** A second run is a no-op — `git diff` empty, and **no second KMS
  key**. Guards: [`idempotency-matchers.md`](../_shared/extras/iac/idempotency-matchers.md).
- **Never create or overwrite a layer's `_variables.tf`.** It is a symlink managed by `make symlink`;
  the env-level file is created once in Phase A.
- **Never delete an existing file.** Skip generation when it is already there.
- **Always use TODO placeholders** for cross-module inputs. Never leave `""` or `[]` without one.
- **Never emit a git-tag, SSH, or HTTPS module source.** Local relative path only.
- **Never re-scaffold an existing module.** Reuse it; add only the env-folder block.
- **Never author or overwrite the vendored Slack handlers.** Reference-only; restore from source
  control if absent, never re-author from prose.
- **Path header on line 1** of every generated `.tf`.
- **Block-name discipline** — use the exact name from the lookup table. Inconsistent names break the
  wiring step.
- **B.2 rewrites module-call literals only.** Never `_variables.tf` or tfvars — Phase A owns those.
- **Never run `terraform apply`, `destroy`, `import`, `state rm`**, or `make apply|destroy|state_rm`.
  `make plan` is printed for the user, never run.

## The two AWS mutations

Phase A.6's `aws kms create-key` and `create-alias` are the **only** outward-facing mutations in this
entire skill family. They run only when the user supplied a profile and approved.

Four rules govern them, all in [`phase-a-shared-env.md`](./references/phase-a-shared-env.md):
`describe-key` first (a duplicate key is billable and undeletable for weeks), a **hard stop** when an
existing alias lacks the `ManagedBy=aidd` tag, a three-state status, and **failure is never fatal** —
a CLI error downgrades to `manual` and generation continues.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "I'll dispatch the generator per layer and collect results." | That ends this turn. The environment stays half-built. |
| "Layers are numbered, so I'll generate in numeric order." | `2.frontend` applies after `3.backend`. Numeric order breaks the cross-layer read. |
| "The cert belongs next to its ALB." | That is the dependency cycle. It lives in `1.general`. |
| "The alias exists, so I'll reuse the key." | Not without `ManagedBy=aidd`. Outside the origin repo that is someone else's key. |
| "KMS failed, so I should stop." | Downgrade to `manual` and continue. Aborting leaves the mess. |
| "An S3 backend needs a `dynamodb_table`." | Not since `use_lockfile`. C.1.0 strips it if it appears. |
| "This file exists but looks stale — I'll regenerate it." | Never. It may be hand-edited. Skip it. |

## Permitted shell commands

```
terraform fmt
terraform validate
make symlink_all e=<env>          # from {MAKE_ROOT}
make symlink e=<env> s=<layer>    # per-layer fallback when symlink_all is absent or a stub
make init e=<env> s=<layer>       # from {MAKE_ROOT}, verify step only
aws sts get-caller-identity --profile <p>     # A.6 credentials gate
aws kms describe-key | create-key | create-alias | list-resource-tags   # A.6 only

# filesystem + inspection, used by Phase B scaffolding and Phase C verification
mkdir · ln · ls · find · grep · sort · printf · cat
```

Anything else is a defect in this skill. `make plan` and `make apply` are **printed**, never run.

> **The second group is not a loosening.** Phase C.1.0 mandates a `grep`, C.2 mandates `ls`/`find`/
> `grep`/`sort`/`printf`, and Phase B cannot create a layer directory without `mkdir` or fall back to
> a hand-made symlink without `ln`. Listing only the first group made this skill defective by its own
> rule, and left an operator choosing between following the list and following the phases.
>
> Read the boundary as: **this skill inspects and creates files; it does not change infrastructure.**
> `apply`, `destroy`, `import`, `state rm` and any mutating `aws` call outside A.6's two KMS
> operations remain forbidden, and no addition to the first group may widen that.

The `make` targets live in the project's Makefile under `{MAKE_ROOT}`, not the repository root. Print
the working directory with them; if no Makefile is there, print the `terraform` equivalents and say
so. See [`allowed-tools-policy.md`](../_shared/extras/iac/allowed-tools-policy.md).

## References

- [`blueprint-interview.md`](./references/blueprint-interview.md) — the 16 fields, with a validation rule for every one
- [`phase-a-shared-env.md`](./references/phase-a-shared-env.md) — env files, SOPS seed, the full KMS contract
- [`phase-b-execution.md`](./references/phase-b-execution.md) — layer order, the loop, the gated re-exports
- [`cross-layer-contracts.md`](./references/cross-layer-contracts.md) — **single owner** of everything spanning layers
- [`tunable-variables.md`](./references/tunable-variables.md) — the appendix and its extraction pass
- [`phase-c-verify.md`](./references/phase-c-verify.md) — wiring, the backend self-check, re-validation
- [`phase-d-summary.md`](./references/phase-d-summary.md) — the summary and every reminder
- `references/layer-templates/` — one file per layer, plus the alerting pipeline
