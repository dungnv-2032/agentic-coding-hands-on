---
name: tkm:iac-connect-modules
description: >
  Resolve the TODO placeholders left by Terraform module generation into real references — same-layer
  module outputs, or cross-layer terraform_remote_state reads with the remote-state blocks appended to
  the layer backend. Then run the inline validation gate: terraform validate, a security pass and a
  best-practice pass, with a fix loop capped at two rounds.
  Idempotent: re-running wires nothing twice and duplicates no block.
  Use this after generating one or more services, to wire a layer to the layers it depends on, or to
  validate a freshly generated layer before plan.
  SKIP: generating the service files themselves (→ tkm:iac-generate-module); reviewing a whole
  finished environment with all five reviewers (→ tkm:iac-review).
category: iac
roles: [engineer, devops]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
argument-hint: "[env] [target-layer|all]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: deployment-infrastructure
triggers:
  - "connect modules"
  - "wire terraform modules"
  - "resolve TODO placeholders terraform"
  - "terraform_remote_state wiring"
  - "validate generated terraform"
  - "nối module terraform"
---

# tkm:iac-connect-modules

Two jobs, in order: **wire**, then **gate**.

Generation deliberately leaves every cross-module input as a `# TODO` — a generation run cannot know
what other layers will export. This skill reads what they actually export and resolves them.

All paths resolve through
[`layout-contract.md`](../_shared/extras/iac/layout-contract.md).

| Argument | Effect |
|---|---|
| `env` | The environment. |
| `target-layer` | The layer to wire. `all` wires every layer in the environment. |

Constrain both to `^[A-Za-z0-9._-]+$` before either reaches a path or a command.

## Wiring

Six steps — full rules in [`wiring-rules.md`](./references/wiring-rules.md):

1. Read each source layer's `_outputs.tf`.
2. Scan the target for connect-TODOs. **Any other `# TODO:` is skipped** — an AMI id waiting for a
   human is not a wiring job.
3. Match. **LHS inference first**: the variable being assigned is stronger evidence than the prose in
   the comment.
4. Append `terraform_remote_state` blocks for cross-layer sources — idempotently, and nothing else in
   `_backend.tf` changes.
5. Replace matched TODOs. Same-layer → `module.<n>.<out>`; cross-layer →
   `data.terraform_remote_state.<alias>.outputs.<out>`.
6. Report matched and unmatched, with a reason for each unmatched row.

**Ambiguity is a question, not a coin flip.** When several outputs match, present a numbered menu.
A wrong security-group reference produces Terraform that applies cleanly and connects the wrong
tiers — the failure surfaces in production, not at plan time.

**When there is nobody to ask, leave it unresolved — never pick.** This skill also runs *inside*
`tkm:iac-generate-env`'s single uninterrupted turn, where a menu has no reader. Asking and picking
are not the only options:

1. Resolve it if a **deterministic rule** applies — the block-name convention below, or the block's
   own inputs (an ALB's `internal`, a service's name).
2. Otherwise **leave the TODO in place**, keep the comment, and list the row under
   `## Requires Manual Action` in the report with the candidates you found.

An unresolved TODO is visible, greppable, and flagged by the reviewer. A coin-flip that guessed
wrong is none of those — it looks resolved. Batch mode changes who answers, never whether a guess is
acceptable.

**Block-name convention** — the deterministic rule that removes most of these. A TODO inside a block
named `<service>_<purpose>` resolves against `<service>`: `iam_api_s3`'s `role_name` takes the `api`
role, not the `worker` one, even though both substring-match. Use the block name before the output
list, not after.

## The gate

After wiring, three checks with a fix loop capped at **2** — full rules in
[`inline-validation-gate.md`](./references/inline-validation-gate.md):

| Check | What runs |
|---|---|
| 1 | `terraform validate` — skipped with a warning if `_variables.tf` is not a symlink |
| 2 | `Invoke /tkm:iac-review <env> --only security --scope <layer> --report-only` |
| 3 | `Invoke /tkm:iac-review <env> --only bestpractice --scope <layer> --report-only` |

Checks 2 and 3 **invoke** the review skill rather than carrying rules. One copy of the checklists, no
drift, and no cross-skill file link for the validator to reject.

> **If `tkm:iac-review` is absent, state the gap and stop that check.** Never fall through to base
> `tkm:infra`'s review — it applies a different rule set that disagrees with this generator's own
> conventions, so it would flag correct output and miss the real problems. A stated gap is
> recoverable; a wrong verdict presented as a pass is not.

**Counter: `{WORK_DIR}/inline-loop-count.txt`, cap 2.** Not the review loop's
`{WORK_DIR}/loop-count.txt`, cap 3. Reset once per invocation, outside the loop — `{WORK_DIR}` is
gitignored, so a stale counter would escalate with zero fix attempts.

## Rules

- **Idempotent** — re-running produces identical files. No duplicated remote-state blocks, no doubled
  replacements.
- **Never overwrite `_variables.tf`** — it is a symlink managed by `make symlink`.
- **Never regenerate `_backend.tf`** — append remote-state blocks only.
- **Never modify files outside the target layer.** Source layers are read-only.
- **Never add `depends_on`** — Terraform resolves the graph from direct references. Adding it
  serializes work that could run in parallel and hides the real dependency.
- **Never run `terraform apply`, `destroy`, `import`, `state rm`**, `make apply|destroy|state_rm`, or
  `make init|plan` — the gate prints those, it does not run them.
- **Never delete a file.** Fix in place; comment where an automated fix is not possible.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "Two outputs match; the first looks right." | Ask. A wrong SG wires the wrong tiers and applies cleanly. |
| "This `# TODO: replace with actual AMI` is a wiring TODO." | It is not. Reject anything without the connect phrase. |
| "The output is a scalar and the field is `[]` — close enough." | Wrap it in brackets, or plan fails on a type error. |
| "`terraform validate` failed, so the generation is broken." | Check `_variables.tf` is symlinked first. |
| "I'll add `depends_on` to be safe." | Never. The reference is the dependency. |
| "The review skill is missing, base has one." | Different rule set. State the gap instead. |

## Permitted shell commands

```
terraform fmt
terraform validate
make symlink e=<env> s=<layer>     # from {MAKE_ROOT}
make symlink_all e=<env>           # from {MAKE_ROOT}
```

Anything else is a defect in this skill. `make init` and `make plan` are **printed** for the user,
never run — both reach AWS. `plan` obviously; `init` because a `backend "s3"` block makes it
authenticate and read remote state, and against an environment that already has *local* state it
offers to copy that state up, which a non-interactive run cannot answer.

This skill runs standalone against environments it did not create, so it must assume local state may
exist. `tkm:iac-generate-env` does run `make init` in its verify phase — on layers it just generated,
which have no local state. Different preconditions, not a contradiction.

The `make` targets live in the project's Makefile under `{MAKE_ROOT}`, not at the repository root.
Print the working directory with them; if no Makefile is there, print the `terraform` equivalents and
say so.

See [`allowed-tools-policy.md`](../_shared/extras/iac/allowed-tools-policy.md).

## References

- [`wiring-rules.md`](./references/wiring-rules.md) — TODO scanning, matching, remote-state append, replacement cases
- [`inline-validation-gate.md`](./references/inline-validation-gate.md) — the three checks, the 2-round loop, escalation
