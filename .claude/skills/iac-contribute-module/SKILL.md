---
name: tkm:iac-contribute-module
description: >
  Scaffold a new reusable Terraform module — the four-file skeleton plus a terraform-docs-ready
  README, optionally with .tftest.hcl tests and a standalone example — then run the local quality
  chain and report what ran and what was missing.
  Never scaffolds over an existing module, and never fails a scaffold because a linter is absent —
  except for the two secret detectors, which are required.
  Use this to add a module to a shared library, or to start a module you intend to open a pull
  request for.
  SKIP: consuming a module inside an environment (→ tkm:iac-generate-module);
  extracting modules out of an existing monolith (→ the vendored refactor-module reference);
  scaffolding a whole environment (→ tkm:iac-generate-env).
category: iac
roles: [engineer, devops]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
argument-hint: "<module-name> [--with-tests] [--with-example]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: deployment-infrastructure
triggers:
  - "contribute terraform module"
  - "new terraform module"
  - "scaffold a reusable module"
  - "create module for the library"
  - "module with tftest"
  - "tạo module terraform"
---

# tkm:iac-contribute-module

Scaffolds a module under `{MODULE_DIR}/<name>/`, resolved through
[`layout-contract.md`](../_shared/extras/iac/layout-contract.md).

`{MODULE_DIR}` is expected to be **empty in a fresh project** — modules are an output this kit
creates, not a prerequisite it requires.

| Argument | Effect |
|---|---|
| `<module-name>` | kebab-case. Validate `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$` before it reaches a path. |
| `--with-tests` | also emit `tests/*.tftest.hcl` |
| `--with-example` | also emit a standalone example directory |

## Steps

1. **Check for an existing module.** If `{MODULE_DIR}/<name>/` exists, **stop** — report what is
   there and do not touch it.
2. **Scaffold** the four files plus README →
   [`module-anatomy.md`](./references/module-anatomy.md)
3. **`--with-tests`** → [`module-tests.md`](./references/module-tests.md)
4. **`--with-example`** → a standalone example directory
5. **Run the quality chain** and report it — see below
6. **Summarize**: what was created, what ran, what was skipped, and what the author must fill in

## The quality chain

Run what is available, report honestly:

| Tool | Missing → |
|---|---|
| `terraform fmt` | note it, continue |
| `terraform init -backend=false` then `terraform validate` | note it, continue |
| `terraform-docs` | note it, continue — the README block stays empty |
| `tflint` | note it, continue |
| **`detect-aws-credentials`** | **visible warning** |
| **`detect-private-key`** | **visible warning** |

> **The two secret detectors are not optional.** A missing formatter costs tidiness. A missing secret
> detector costs a credential in git history, which no later run can undo — and this kit's
> environment generation writes a **plaintext** secrets file into the user's tree, so the detectors
> are the guard that catches the mistake.
>
> Report every missing tool. But a missing detector is a warning the user has to see, not a line in
> a skipped list.

Never fail the scaffold because a linter is absent. The module is still correct; the report says what
could not be checked.

## Rules

- **Never scaffold over an existing module.** It may have been hand-edited.
- **Never delete a file.**
- **Validate `<module-name>`** before it reaches a path.
- **No governance content.** No project board, no issue-title convention, no branch policy, no
  per-cloud base branches. Scaffold the module and tell the user to open a PR by whatever process
  their repository uses — that process is not this kit's business.
- **Never run `terraform apply`, `destroy`, `import`, `state rm`.**
- **Never hardcode a module path.** Resolve `{MODULE_DIR}`.
- **Report what did not run.** A silent skip reads as a pass.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "The module exists but looks half-finished — I'll regenerate it." | Stop. It may be mid-edit. Report and leave it. |
| "`tflint` is missing, so the scaffold failed." | It did not. Note it and continue. |
| "The secret detectors are missing too — same thing." | Not the same thing. Warn visibly. |
| "I'll add the issue-title convention so the PR is consistent." | That is the source repo's process, not this kit's. |
| "A test asserting the default equals the default proves it works." | It proves nothing and looks like coverage. |

## Permitted shell commands

```
terraform fmt
terraform init -backend=false      # no remote state, no credentials; installs providers so validate can run
terraform validate
terraform test                     # only with --with-tests; every scaffolded run block is command = plan
terraform-docs markdown .
tflint
pre-commit run --files <scaffolded files>
```

Anything else is a defect in this skill. No `terraform apply|destroy|import|state rm`, no `aws` CLI.
See [`allowed-tools-policy.md`](../_shared/extras/iac/allowed-tools-policy.md).

> **`terraform init -backend=false` is the only way to reach `validate`.** `validate` refuses to run
> until providers and modules are installed, and `-backend` is an `init` flag — `terraform validate
> -backend=false` fails with "flag provided but not defined". `-backend=false` is what keeps `init`
> from touching remote state or needing credentials.

> **`terraform test` is only safe because of what it runs.** A `run` block with `command = apply`
> creates real AWS resources — it is not a dry run, and the word `test` hides that completely. Every
> block this skill scaffolds is `command = plan`
> ([`module-tests.md`](./references/module-tests.md)). Never run `terraform test` against a module
> whose run blocks you have not read.

## References

- [`module-anatomy.md`](./references/module-anatomy.md) — the four-file contract, README structure, the discriminator rule
- [`module-tests.md`](./references/module-tests.md) — what `--with-tests` emits

The full `.tftest.hcl` reference is `_vendor-iac/terraform-test/`; monolith-to-module extraction is
`_vendor-iac/refactor-module/`. Both are reference material, not routable skills.
