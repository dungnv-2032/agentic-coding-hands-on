# Env Service Folder Contract

What a layer directory contains, and the exact shape of each file.

Path keys resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

## Module-first rule

Every service is consumed from a **local** module under `{MODULE_DIR}/{service}/`. Env service files
reference modules by relative path only:

```hcl
module "<service>" {
  source = "{MODULE_DEPTH}"
  # variables...
}
```

`MODULE_DEPTH` walks **three** levels up — layer → env → envs → `{IAC_ROOT}` — then into
`modules/{service}`. The literal default lives in
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md) and nowhere else.

**That arithmetic is invariant.** It is measured from `{ENV_DIR}/{layer}` up to `{IAC_ROOT}`, so
overriding `IAC_ROOT` to a shallower or deeper path does **not** change it — the override moves the
whole tree, not the layer relative to its own root. Three levels, always.

`SOPS_PATH` behaves differently: its four `../` are equally invariant, but the directory name that
follows them re-derives from `DEPS_ROOT`. Do not generalise from one to the other.

**Never reference a module by git tag, SSH URL, or HTTPS URL.** Only the local relative path is
valid. Generated env files are hermetic: `terraform init` needs no network, and a module change is
reviewable in the same PR as the env consuming it.

The bestpractice reviewer enforces this as a **HIGH** rule. Generator and reviewer read the same
contract key on purpose — if they diverge, generation produces code its own reviewer rejects and
every run ends in an escalation loop.

## File header rule

Every generated `.tf` file starts with its own relative path as a comment on line 1:

```hcl
# {ENV_DIR}/{layer}/<filename>.tf
```

Applies to `_backend.tf`, `_data.tf`, `<service>.tf` and `_outputs.tf`. The bestpractice reviewer
flags a missing header as HIGH.

## File naming

Name the service file after the AWS service — `s3.tf`, `rds.tf`, `ecs.tf`. **Never `main.tf`** in an
env folder.

**Before generating, scan the target for an existing `<service>.tf`.** If found, list its existing
module blocks and ask whether to add, rename, or both. Never silently overwrite.

---

## `_backend.tf` — the canonical block

Written **only if it does not already exist**.

> ### This block has exactly one owner: this file.
>
> Generators must emit it inline — a reference cannot be copied verbatim into output, and an empty
> `backend "s3" {}` fails `terraform init`. That makes the block *mirrored* wherever it is emitted,
> which is precisely how it drifted upstream once already.
>
> **Changing it — the bucket shape, `use_lockfile`, an added or removed argument, the key
> convention — means changing every emitter in the same commit.** Consumers of this contract:
> the module scaffold, the env-file emitter, the cross-layer `terraform_remote_state` bucket (it
> reads the *same* bucket, so the same suffix rule applies), and the bestpractice reviewer rules that
> flag legacy `dynamodb_table`, a missing `use_lockfile`, and an un-suffixed bucket.

**The `<...>` values are resolved, not literal.** `profile` resolves `PROFILE_PATTERN` and `bucket`
resolves `STATE_BUCKET_PATTERN` from
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md), the same way `region` resolves
`DEFAULT_REGION`. The shapes above are those keys' *defaults*, printed in full so the block can be
read without a second file open — but a project that overrides either key in its `## IaC Layout`
block gets the override, in both the backend and the provider.

Emitting the default shape regardless would fail twice over: `terraform init` would authenticate
against a profile the user does not have, and the bestpractice reviewer — which *does* resolve
`{STATE_BUCKET_PATTERN}` — would raise **HIGH** on the generator's own correct-looking output, then
spend the fix loop rewriting it toward a bucket the bootstrap script never created.

Two invariants:

- **`bucket` must carry an account-scoped discriminator** — the default's `-{account-id}` suffix, or
  whatever plays that role in an overridden `STATE_BUCKET_PATTERN`. S3 names are global: an
  account-agnostic name either fails `terraform init` on a bucket that does not exist, or resolves to
  one in another account. **The kit never creates this bucket** — it is the user's, and on any repo
  outside the origin repository it predates the kit.
- **State locking is S3-native** via `use_lockfile = true` (Terraform >= 1.11). **No
  `dynamodb_table`** — the lock table was removed.

> **`dynamodb_table` will feel right. It is not.** Nearly every S3-backend example in circulation
> pairs the bucket with a DynamoDB lock table, so it is the single most likely thing to be
> reintroduced from memory rather than read from this block. Emit the block above as written. The
> bestpractice reviewer flags a `dynamodb_table` as HIGH precisely because this keeps happening.

```hcl
# {ENV_DIR}/{layer}/_backend.tf
terraform {
  required_version = ">= 1.14.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.37.0"
    }
  }
  backend "s3" {
    profile      = "<project>-<env>" # resolved literal — PROFILE_PATTERN
    bucket       = "<project>-<env>-iac-state-<account-id>" # resolved literal — STATE_BUCKET_PATTERN; S3 names are GLOBAL, so the account-id suffix avoids cross-account collision
    key          = "<layer>/terraform.<env>.tfstate"
    region       = "<region>" # resolved literal — DEFAULT_REGION, or `region` from tfvars when set
    use_lockfile = true # S3-native state locking (Terraform >= 1.11) — no DynamoDB table
    encrypt      = true # encrypt tfstate at rest
    # kms_key_id = "arn:aws:kms:<region>:<account-id>:key/<key-id>" # optional customer-managed CMK
  }
}

provider "aws" {
  region  = var.region
  profile = "${var.project}-${var.env}" # PROFILE_PATTERN in its interpolated form — keep the two in step
  default_tags {
    tags = {
      Project     = var.project
      Environment = var.env
      Owner       = var.owner
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
```

### Backend literals must be resolved at generation time

A `backend "s3"` block **cannot** use `${var.project}` — Terraform reads it at `init`, before
variables exist. So `profile` and `bucket` must be **static strings**, resolved when the file is
written:

Read `project` from `{ENV_DIR}/terraform.{env}.tfvars`. If the value is real — non-empty and not in
the placeholder set `{ "project", "<project>", "your-project-name" }` — emit the literal
(`profile = "aidd-dev"`, `bucket = "aidd-dev-iac-state-<account-id>"`). If tfvars is missing or still
a placeholder, leave the `<project>` token for the engineer's one-time replacement. `<env>` is always
known.

`region` is resolved the same way: read `region` from `terraform.{env}.tfvars`, else `DEFAULT_REGION`.
Emit the literal.

**`<account-id>` always stays a placeholder** — a backend block cannot interpolate
`data.aws_caller_identity.current`. The engineer fills it once from the bootstrap output.

> **These static literals are not a rule violation.** The bestpractice reviewer flags a hardcoded
> region or account ID as HIGH — correctly, for a *resource*. A `backend "s3"` block is the one place
> where the literal is mandatory, because Terraform reads it before variables exist. Replacing
> `region` with `var.region` there produces `Variables not allowed` at `init`. The reviewer rules
> carry the matching exception; do not "fix" a backend literal into a variable.

### SOPS provider — conditional

The `carlpett/sops` provider and its data source are added **only when the layer actually consumes
secrets**.

**Detection:** the layer needs SOPS **iff** at least one `.tf` file in it references
`data.sops_file.secret.data["…"]`. Detection happens at service level during generation, and the same
trigger decides whether to patch `_backend.tf`. Patch in the same call that emits the first sensitive
reference — idempotent, so skip when the SOPS block is already present from an earlier service in the
same layer.

A layer with no sensitive input gets a plain `_backend.tf`, no seeded YAML, and `terraform init`
works with no KMS or SOPS setup at all.

Two edits, both in place:

1. Add `sops` to the **existing** `required_providers` map, alongside `aws`:

```hcl
    sops = {
      source  = "carlpett/sops"
      version = "~> 1.3.0"
    }
```

2. After `data "aws_caller_identity" "current" {}` and **before** any `data
   "terraform_remote_state"`, append:

```hcl
provider "sops" {}

data "sops_file" "secret" {
  source_file = "{SOPS_PATH}"
}
```

> **Single `terraform {}` block.** Always merge `sops` into the existing `required_providers` map.
> Never create a second `terraform {}` block — Terraform permits it and merges them, but one block is
> the reviewable shape.

> ### `SOPS_PATH` is FOUR levels up. `MODULE_DEPTH` is three.
>
> Default `SOPS_PATH` is `../../../../terraform-dependencies/sops/secrets.{env}.yaml`. A module call
> points *into* `{IAC_ROOT}` (three levels); a SOPS reference points *out of* it into `{DEPS_ROOT}`,
> a sibling — one level further.
>
> Conflating them breaks SOPS wiring **silently at plan time**: Terraform resolves a path that is not
> there, and the failure surfaces as a decryption error far from its cause. Use the contract keys;
> never hand-count the `../`.

---

## `_data.tf`

Shared data sources for the layer that are not the caller identity (which lives in `_backend.tf`).
Written only if absent.

## `_outputs.tf`

One output per module block, exporting what other layers consume. Every output carries a
`description`.

For multi-instance services, one output per block — see
[`terraform-conventions.md`](./terraform-conventions.md) § Multi-instance.

**Sensitive outputs must be marked `sensitive = true`.** The security reviewer flags an unmarked
sensitive export as HIGH: a raw secret crossing layers through `terraform_remote_state` is readable
by anything that can read the state bucket.

## Env-level `_variables.tf`

Lives at `{ENV_DIR}/_variables.tf` and is **symlinked** into each layer by `make symlink`, not
copied.

**Never overwrite a layer's `_variables.tf`** — it is a symlink, and writing through it edits the
shared file.

## `terraform.{env}.tfvars`

Env-level, non-sensitive configuration only. **Secrets never go here** — the security reviewer flags
a plain-literal password in tfvars, and tfvars is committed.

Create-or-append, never overwrite. A variable is present **iff** a non-comment line matches
`^<varname>\s*=`. Full rule:
[`idempotency-matchers.md`](../../_shared/extras/iac/idempotency-matchers.md).

---

## Project prefix resolution for SOPS keys

Resolve **once per invocation**, then use the result everywhere in that run.

1. Read `{ENV_DIR}/terraform.{env}.tfvars` if it exists.
2. Extract the `project` value with `^\s*project\s*=\s*"?([^"\s#]+)"?` — handles quoted and unquoted
   forms, ignores trailing comments.
3. If the value is non-empty **and** not in the placeholder set
   `{ "project", "<project>", "your-project-name" }`: uppercase it and replace `-` with `_`.
   `aidd` → `AIDD`; `my-app` → `MY_APP`.
4. Otherwise fall back to the literal string `<PROJECT>`.

Reading tfvars rather than prompting keeps the SOPS keys and the `.tf` references in sync without an
extra question — tfvars is already the authority Terraform uses at apply time. Once the engineer
fills it in, the next run picks up the real prefix automatically.

The prefix is applied to **both** the emitted `data.sops_file.secret.data["<PREFIX>_…"]` references
and every key in the seeded YAML, in the same run, so the two always match.

## Sensitive inputs — the SOPS reference pattern

When a module variable matches the sensitive-input pattern — `password`, `master_password`,
`auth_token`, `*_secret`, `*_api_key`, `*_private_key` — **never** pass a literal. Emit:

```hcl
  master_password = data.sops_file.secret.data["<PREFIX>_DATABASE_PASSWORD_ROOT"] # TODO: confirm key after SOPS setup
```

Key form is `<PREFIX>_<SERVICE>_<FIELD>`, SCREAMING_SNAKE_CASE. Service tokens: `DATABASE` (RDS or
Aurora), `REDIS` (`_AUTH_TOKEN`), `VALKEY` (`_PASSWORD`).

## Secrets YAML seeding

When a service file emits any `data.sops_file.secret.data["<KEY>"]` reference, seed the matching key
in `{DEPS_ROOT}/sops/secrets.{env}.yaml`:

| File state | Action |
|---|---|
| **Missing** | Create as **plain YAML**, not encrypted: header comment plus the keys this run emitted, each with an empty `""` value. |
| **Plain** (no `sops:` block) | Append only the missing keys. Never touch an existing key or value. |
| **Encrypted** (has a `sops:` block) | **Do not touch.** Print a reminder that new keys are added by opening the file through `sops`. |

Presence uses the **commented-aware** matcher `^\s*#?\s*<KEY>\s*:`. A blueprint may seed cache keys
already commented out; the simpler matcher reads those as missing and re-appends them on **every**
run, growing the file without bound. Full rule:
[`idempotency-matchers.md`](../../_shared/extras/iac/idempotency-matchers.md).

### The seeded file is plaintext, and that is deliberate

The generator does not hold the real secret *values*, so encrypting at scaffold time would encrypt
empty strings. Filling and encrypting is the engineer's step.

The plain state is working-but-unsafe and **fail-closed by design**: the security reviewer flags a
missing `sops:` block as HIGH, and `terraform init` errors with a clear decryption error. Both are
intentional signals, not bugs.

**This is also the single most dangerous artifact this skill writes.** See the `.gitignore` and
warning requirements in the skill.
