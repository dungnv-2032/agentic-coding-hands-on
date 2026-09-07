# Env File Emission

Which files a generation run writes into the layer, in what order, and what it must never overwrite.

The **shape** of each file is in
[`env-service-contract.md`](./env-service-contract.md) — including the canonical backend block, which
that file solely owns. This file is the emission procedure and the guards.

## Files written

| File | Location | Written when |
|---|---|---|
| `<service>.tf` | `{ENV_DIR}/{layer}/` | single mode: only if absent, else **ask**. Batch mode: only if absent, else **skip** |
| `_backend.tf` | `{ENV_DIR}/{layer}/` | only if absent; patched in place for SOPS |
| `_data.tf` | `{ENV_DIR}/{layer}/` | only if absent |
| `_outputs.tf` | `{ENV_DIR}/{layer}/` | created if absent; append only outputs not already declared |
| `_variables.tf` | `{ENV_DIR}/` — **env level** | **only if absent** |
| `terraform.{env}.tfvars` | `{ENV_DIR}/` | create-or-append, never overwrite |
| `secrets.{env}.yaml` | `{DEPS_ROOT}/sops/` | only when a sensitive reference was emitted |
| `.gitignore` | repository root | verify-then-append |

## Never overwrite

- **A layer's `_variables.tf`** — it is a **symlink** to the env-level file, managed by
  `make symlink`. Writing through it edits the shared file for every layer at once.
- **The env-level `_variables.tf`** — written **only when absent**. It is the symlink *target*: the
  one file in the layout whose corruption reaches every layer at once.
- **An existing `<service>.tf`** — see the mode rule below.
- **An encrypted `secrets.{env}.yaml`** — the generator holds no KMS access and cannot decrypt it.
- **An existing module folder** — see the duplicate-scaffold guard in
  [`module-scaffold.md`](./module-scaffold.md).

Every one of these is a file a human may have edited. Re-running must be a no-op, not a reset.

### `<service>.tf` — the guard differs by mode

**Single mode:** if `<service>.tf` exists, list its module blocks and **ask** whether to add, rename,
or both. Never silently overwrite.

**Batch mode:** if `<service>.tf` exists, **skip that service entirely** and mark it `skipped` for the
summary. Do not ask — batch suppresses prompts, so an "ask" guard there is unreachable and the write
would proceed unguarded. Skipping is the guard.

If **every** service in a batch was skipped, say so and stop:

```
All requested services already exist in <layer> — nothing was generated.
Run in single mode to update an existing service.
```

### `_outputs.tf` — append only what is not already declared

An output is present **iff** a line matches `^\s*output\s+"<name>"`. Append only the missing ones.

Without this check a second run re-appends the same block and Terraform hard-errors with `Duplicate
output definition` — the same failure class as the tfvars matcher, on a file the tfvars matcher does
not cover.

## Placeholders, not guesses

A required input the generator cannot resolve gets a **TODO placeholder**, never an invented value:

```hcl
ami_id             = "ami-xxxxxxxxxxxxxxxxx" # TODO: replace with actual AMI ID for <region>
security_group_ids = []                      # TODO: connect from security-group — run the wiring step
key_name           = ""                      # TODO: replace with actual key pair name
```

The phrase `run the wiring step` is what the wiring step scans for. A TODO written in some other
shape is invisible to it and ships unresolved — the bestpractice reviewer then flags it HIGH, which
is the backstop, not the plan.

Cross-module inputs are **always** placeholders at generation time. Wiring is a separate step, on
purpose: a generation run does not know what the other layers will export.

## The `.gitignore` requirement

This skill writes an **unencrypted YAML secrets file** into the user's repository and tells them to
fill it with real values.

Upstream, two things caught the resulting mistake — a repository `.gitignore` entry and a pre-commit
hook that detects credentials and private keys. **Neither exists in a consumer's repository by
default.**

So the scaffold must, before finishing:

1. Read the repository root `.gitignore` if it exists.
2. Append this entry if it is missing — matching an existing line exactly, so a re-run appends
   nothing:

```gitignore
{WORK_DIR}/
```

3. Say so in the summary.

**Verify-then-append.** Never rewrite the user's `.gitignore`.

> **The secrets file is deliberately NOT gitignored.** `sops --encrypt --in-place` rewrites
> `secrets.{env}.yaml` under the **same filename**, and the encrypted result is meant to be
> committed — it holds only opaque ciphertext. A glob ignoring `sops/*.yaml` would therefore hide the
> very file the workflow requires in version control, and the user's natural fix is to delete the
> ignore line, which removes the protection entirely.
>
> There is no filename that distinguishes the plaintext state from the encrypted one. So the
> protection here is **not** `.gitignore` — it is the warning below, plus the secret-detection
> pre-commit hooks the contribution flow requires. Say this plainly rather than implying the file is
> covered.

## The plaintext warning is mandatory

When a run seeds or extends `secrets.{env}.yaml`, the summary must state plainly:

> `{DEPS_ROOT}/sops/secrets.{env}.yaml` is **plaintext** and contains empty placeholders. Fill the
> real values, then encrypt it in place before committing. It is **not** gitignored — once encrypted
> it is meant to be committed, and no filename distinguishes the two states. Until you have encrypted
> it, do not commit it.

Do not bury this under a list of next steps. It is the one line whose omission has a consequence that
cannot be undone by a later run — a secret in git history stays in git history.

The encryption step needs the key **ARN**; `sops --kms` rejects a bare alias:

```bash
KEY_ARN=$(aws kms describe-key --key-id {SOPS_ALIAS_PATTERN} --query KeyMetadata.Arn --output text)
sops --encrypt --kms "$KEY_ARN" --in-place {DEPS_ROOT}/sops/secrets.{env}.yaml
```

The generator **never runs these** — they mutate AWS and require credentials it does not assume. It
prints them.

## Emission order

1. Resolve the service and layer names, and validate both.
2. Resolve or scaffold the module.
3. Resolve the project prefix from tfvars — once per run.
4. Write `_backend.tf` if absent.
5. Write `<service>.tf` with the module call and TODO placeholders.
6. Detect sensitive inputs. If any: patch `_backend.tf` for SOPS, seed `secrets.{env}.yaml`.
7. Write or append `_outputs.tf`, `_variables.tf`, `terraform.{env}.tfvars`.
8. Verify-then-append `.gitignore`.
9. Run `terraform fmt` on what was written.
10. Print the summary — including the plaintext warning when step 6 seeded anything.

Step 6 comes after step 5 because the SOPS detection reads what step 5 actually emitted, rather than
predicting it.

## Reminders after generation

Print, with `{MAKE_ROOT}` resolved and the working directory stated — these targets live in the
project's own Makefile, not at the repository root:

```
Next steps (run from {MAKE_ROOT}):
  1. Review the generated files and resolve every # TODO
  2. make symlink e=<env> s=<layer>
  3. Run the wiring step to resolve cross-module TODOs
  4. make init e=<env> s=<layer>
  5. make plan e=<env> s=<layer>
```

If `{MAKE_ROOT}` has no Makefile, print the equivalent `terraform` commands and say the Makefile was
not found rather than printing targets that will not run.
