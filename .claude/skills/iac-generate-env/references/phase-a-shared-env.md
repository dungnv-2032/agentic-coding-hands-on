# Phase A — Shared environment files

Runs **once, before any layer**. Produces the environment-level `_variables.tf` and
`terraform.{env}.tfvars`, optionally seeds the SOPS secrets file, and optionally provisions the SOPS
KMS key.

Path keys resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

`_variables.tf` and `terraform.{env}.tfvars` must declare **every** variable the generated module
calls will reference — including every applicable tunable. The tunable rewriter in Phase B then
rewrites inline literals to use them, so a variable missing here becomes a literal that never gets
rewritten.

Both files are composed from blocks concatenated in this order:

1. Identity
2. Integration (non-sensitive only)
3. Route53 — only when `route53 = true`
4. Messaging — only when `ses` is picked
5. Delivery — only when `delivery = true`
6. Tunable defaults
7. Hardening toggles

---

## `{ENV_DIR}/_variables.tf` — only if absent

```hcl
# {ENV_DIR}/_variables.tf

# ─── Identity ────────────────────────────────────────────────────────────────
variable "project" {
  description = "Name of project"
  type        = string
}

variable "env" {
  description = "Name of project environment"
  type        = string
}

variable "region" {
  description = "Region of environment"
  type        = string
}

variable "owner" {
  description = "Owning team/squad — used for the Owner cost-allocation tag"
  # no default — see the rule below; owner is set per environment in tfvars
  type        = string
}
```

Then one `variable` block per applicable tunable, grouped under section headers: `# VPC`,
`# ECS cluster`, `# Aurora` (or `# RDS` when `db_engine = rds`), `# Valkey` (or `# Redis` when
`cache_engine = redis`), `# Backend ECS`, `# Backend ALB`, `# Frontend ECS`, `# Frontend ALB`,
`# CloudFront`.

> **Do not emit `default` in a variable block.** Defaults live in tfvars only, so each environment
> can override them. A default here silently wins for an environment that never set the value.

### No credential variables, ever

`db_username`, `db_password`, master credentials, auth tokens and API keys are **not** declared here.
They live in `{DEPS_ROOT}/sops/secrets.{env}.yaml` under keys like `<PREFIX>_DATABASE_USER_ROOT`, and
module calls reference them through `data.sops_file.secret.data["<KEY>"]`.

Phase A does not declare them as Terraform variables at all. The SOPS provider block in `_backend.tf`
is added **conditionally**, by the layer generation step, only when a service actually emits a
sensitive reference.

### No `*_image` variables

Container image URIs are **not** exposed at environment level. Each ECS service wires its image to
`module.ecr_<block>.repository_url` plus a fixed `:latest` tag inside the scaffolded module.

To deploy, push to the ECR repo with the `latest` tag. Do **not** emit `backend_*_image` or
`frontend_image`.

---

## `{ENV_DIR}/terraform.{env}.tfvars`

### Identity block — always

```hcl
# ─── Identity ────────────────────────────────────────────────────────────────
project = "<project>"          # the real resolved value, never the placeholder
env     = "<env>"
region  = "<region>"           # DEFAULT_REGION unless overridden
owner   = "<project>-devops-team"
```

> **Create-or-append applies here too.** If tfvars exists and `project` holds a real value, do not
> overwrite it. Only a missing `project`, or one still holding a placeholder, is written.

### Integration block

Non-sensitive configuration only.

```hcl
# ─── Integration ─────────────────────────────────────────────────────────────
db_name = "<project>_<env>_db"
```

**`db_name` is auto-derived, not a TODO.** It is an internal schema name, non-sensitive, and both
`project` and `env` are known at generation time. **Normalize hyphens to underscores** so the value
is a valid SQL identifier — `my-app` becomes `my_app_dev_db`, not `my-app-dev-db`.

**Public domains are never auto-derived.** `cdn_domain`, `frontend_domain`, `backend_domain` and the
apex `zone_name` are user-owned: blank plus TODO, fail-closed.

| Variant | Additional integration variables |
|---|---|
| `none` | *(none)* |
| `static-spa` | `cdn_domain` — user-owned, blank + TODO |
| `ssr` | *(none)* |

**No `acm_cert_arn_us_east_1` variable.** The cert is created in-stack; nothing about it is knowable
at generation time. See [`cross-layer-contracts.md`](./cross-layer-contracts.md).

### Route53 block — only when `route53 = true`

**No `route53_zone_id` variable in any variant.** The zone is created in-stack and exposes `zone_id`
as an output. Consumers reference the module output same-layer, or the remote-state output
cross-layer — never a tfvars placeholder, because the value is un-knowable at generation time.

| Variant | User-owned variables |
|---|---|
| `none` | `zone_name` (apex), `backend_domain` |
| `static-spa` | `zone_name` — `cdn_domain` already declared |
| `ssr` | `zone_name` (apex), `frontend_domain` |

After apply, read the `route53_name_servers` output and set those NS records at the registrar.

### Messaging block — only when `ses` is picked

SES verifies a **domain**, which is user-owned and not knowable at generation time.

```hcl
# ─── Messaging (ses) ─────────────────────────────────────────────────────────
ses_domain = ""  # TODO: your verified SES domain — user-owned, fail-closed
```

Declare `variable "ses_domain"` under a `# Messaging` header. `sqs` and `sns` need no tfvars input —
their names derive from `${project}-${env}`.

`ses` requires `route53 = true`, so `ses_domain` is only ever emitted alongside a `zone_name`.

### Delivery block — only when `delivery = true`

Every pipeline's source stage needs a GitHub repository id and branch. Both are user-owned and not
knowable at generation time, so both are TODOs. **One pair per pipeline-target** — every backend
service, plus `frontend` when a frontend pipeline is generated.

```hcl
# ─── Delivery ────────────────────────────────────────────────────────────────
delivery_api_github_repository = ""  # TODO: GitHub FullRepositoryId — user-owned, fail-closed
delivery_api_github_branch     = ""  # TODO: branch the pipeline tracks — user-owned, fail-closed
```

Declare matching `variable` blocks under a `# Delivery` header.

### Tunable defaults block

Every applicable row from [`tunable-variables.md`](./tunable-variables.md), grouped by service with
section headers. Apply the variant filter: frontend ECS and ALB defaults only for `ssr`, CloudFront
defaults only for `static-spa`.

### Hardening toggles block

Four expensive defense-in-depth features ship behind `enable_<x>` bools, module default `false`.
Seed them **conditionally on the environment**:

> **Production and staging are hardened — all four on. Dev is lean — all four off.**

Dev running leaner is a deliberate, accepted trade-off: cost against a throwaway environment. The
WAF, flow-log, access-log and CloudWatch-KMS findings a reviewer raises against dev are expected.

```hcl
# ─── Hardening toggles ───────────────────────────────────────────────────────
enable_waf         = <true when env ∈ {prod, stg}, else false>
enable_flow_logs   = <true when env ∈ {prod, stg}, else false>
enable_access_logs = <true when env ∈ {prod, stg}, else false>
enable_log_kms     = <true when env ∈ {prod, stg}, else false>
```

Declare all four as `bool` with **no** `default`, under a `# Hardening toggles` header.

S3 versioning is always-on in the module — cheap, so never a toggle and nothing to seed. ECR tag
mutability is seeded `"MUTABLE"` through the existing tunable; **the kit never auto-sets
`"IMMUTABLE"`**, which is a deliberate production hand-edit with versioned tags.

Wiring: `enable_flow_logs` → `module.vpc`; `enable_log_kms` → `module.ecs_cluster`.

> **`enable_waf` and `enable_access_logs` wire only into the PUBLIC ALB.** Picking the wrong block
> attaches a WAF to an internal load balancer — cost with no security benefit — and leaves the actual
> public edge unprotected.

| Variant | Public ALB (gets both) | Internal ALB (gets neither) |
|---|---|---|
| `none` | `module.alb_backend` | — |
| `ssr` | `module.alb_frontend` in `2.frontend` | `module.alb_backend` |
| `static-spa` | — *(the public edge is CloudFront)* | `module.alb_backend` |

> **In `static-spa` there is no public ALB, so both toggles must wire into CloudFront instead.** The
> public edge still exists; it is just not a load balancer. Route `enable_waf` to the distribution's
> `web_acl_id` (scope **`CLOUDFRONT`**, which must be created in `us-east-1` — the same regional
> constraint as its viewer cert) and `enable_access_logs` to the distribution's `logging_config` plus
> its log bucket.
>
> Emitting the variables and wiring them to nothing is worse than omitting them. An operator sets
> `enable_waf = true` on a production environment, `terraform plan` shows no change, and the
> environment reports as hardened while the only internet-facing component has no WAF at all. Three
> of five review legs flag the dead toggle independently — which is the reviewer telling you the
> generator has a hole, not a false positive to suppress.

### Create-or-append

**File absent** → create it with the blocks concatenated in the order listed at the top.

**File present** → **do not overwrite.** For each required variable, test presence; append only the
missing ones, under a header naming the generator and its options.

A variable is present **iff** at least one **non-comment** line matches `^<varname>\s*=`. Full rule:
[`idempotency-matchers.md`](../../_shared/extras/iac/idempotency-matchers.md).

Re-running never overwrites a present value. To change one, the user edits the file.

---

## Phase A.5 — SOPS secrets seed

Conditional. **Skip entirely** when the blueprint has no sensitive input — no yaml file, no
`<PROJECT_PREFIX>` resolution, an empty sensitive-key list into Phase B, and therefore no SOPS block
in any `_backend.tf` and no KMS setup.

The trigger is **structural**: whether Phase A.5 seeds the yaml is what tells Phase A.6 whether to
provision a key. Keep the chain consistent — environment needs SOPS ⇔ A.5 seeds ⇔ A.6 provisions.

Resolve `<PROJECT_PREFIX>` once, then use it everywhere in the run. Seed keys with the
**commented-aware** matcher `^\s*#?\s*<KEY>\s*:`; never touch an encrypted file. Full rules:
[`idempotency-matchers.md`](../../_shared/extras/iac/idempotency-matchers.md).

### Three extra keys when `alerting = true`

```
<PROJECT_PREFIX>_SLACK_WEBHOOK_URL     # optional — empty means bot-token mode
<PROJECT_PREFIX>_SLACK_BOT_TOKEN       # xoxb-… — used when the webhook is empty
<PROJECT_PREFIX>_SLACK_CHANNEL_ID      # used with the bot token
```

Appended **only** when `alerting = true`, through the same matcher.

> This is the one Phase A output whose consumer is in a layer template read much later — the
> alerting pipeline's `ssm_slack_*` blocks. Phase A has already finished by then, so if these keys
> were not seeded here they cannot be added retroactively, and every `ssm_slack_*` block resolves to
> a key that does not exist.
>
> When `alerting = false` they are **not** appended, which is part of the byte-for-byte passive
> boundary.

The seed shape, the prefix-resolution algorithm and the three file states are owned by
`tkm:iac-generate-module`, which this skill invokes per service — do not restate them here and do
not link into that skill's references.

The seeded file is **plaintext**, deliberately. The generator does not hold real secret values, so
encrypting would encrypt empty strings. That state is fail-closed by design: the security reviewer
flags a missing `sops:` block as HIGH and `terraform init` errors clearly.

---

## Phase A.6 — Provision the SOPS KMS key

**This is the one step in the entire family that mutates a live AWS account.**

Runs **only** when Phase A.5 actually seeded the file, and **only** when `sops_kms_profile` is
non-empty — meaning the user supplied a profile and approved.

**Inputs**

| Input | Source |
|---|---|
| `sops_kms_profile` | Approved profile from the interview. Empty → skip → `manual`. |
| `sops_kms_alias` | Alias without the `alias/` prefix. Default: resolve `SOPS_ALIAS_PATTERN` and strip its `alias/` prefix. If passed empty while the profile is set, fall back to that default. |
| `region` | `region` from tfvars if Phase A wrote it, else `DEFAULT_REGION`. |

No project or tfvars gating — the profile alone is sufficient to decide whether to touch AWS at all.

> **Resolve the alias, do not derive it.** `SOPS_ALIAS_PATTERN`'s default expands to the same string
> as `<sops_kms_profile>-sops-key` under the default `PROFILE_PATTERN`, which is why deriving it
> appears to work. Override either pattern and the two diverge — `describe-key` then queries an alias
> nothing was created under, the idempotency check comes back empty, and the run creates a **second**
> KMS key. Billable, and undeletable for 7–30 days. That is the exact outcome this guard exists to
> prevent, reached by skipping one contract lookup.

### Decision table

| Condition | Action | `sops_kms_status` |
|---|---|---|
| `sops_kms_profile` empty | Do **not** touch AWS. Emit a manual-create TODO. | `manual` |
| `aws sts get-caller-identity --profile <p>` fails | Do **not** create. Warn about credentials or permission. | `manual` |
| Alias already exists | Reuse — capture the ARN, **subject to the tag check below**. Still run the recording step. | `exists` |
| Profile valid **and** alias missing | Create key + alias, capture the ARN, run the recording step. | `created` |

### Four rules, all load-bearing

**1. Idempotency — always `describe-key` first.**

```bash
aws kms describe-key --key-id alias/<sops_kms_alias> --profile <p> --region <region>
```

Never create without checking. A duplicate KMS key is **billable and cannot be deleted for 7–30
days** — there is no quick undo for getting this wrong.

**2. Reuse safety — the `ManagedBy=aidd` check is a HARD STOP.**

When the alias exists, verify the key carries `ManagedBy=aidd` via `aws kms list-resource-tags`. If
the tag is **absent**, **stop**. Do not reuse it.

> **Intentional deviation from upstream.** The source warns and reuses anyway, and it could afford
> to — it only ever ran inside its own repository. This kit runs in arbitrary repositories, where an
> untagged key at that alias is far more likely to belong to someone else. Encrypting production
> secrets to a key the user does not control is not recoverable by a warning line.

**3. Three-state status.** Record `sops_kms_status ∈ {created, exists, manual}`, plus the alias and
ARN when known, for the summary.

**4. Failure is NEVER fatal.** A real CLI error — bad credentials, missing KMS permission — downgrades
to `manual` and **generation continues**.

> Aborting mid-Phase-A leaves exactly the half-built environment the single-continuous-turn rule
> exists to prevent. A missing key is a documented follow-up; a half-generated environment is a mess
> the user has to unpick by hand.

### Commands

These are the **only** outward-facing mutations in the whole skill family.

```bash
aws sts get-caller-identity --profile <sops_kms_profile>          # credentials gate

KEY_ID=$(aws kms create-key \
  --description "SOPS secrets encryption for <sops_kms_profile>" \
  --tags TagKey=Project,TagValue=<sops_kms_profile> TagKey=ManagedBy,TagValue=aidd \
  --query KeyMetadata.KeyId --output text \
  --profile <sops_kms_profile> --region <region>)

aws kms create-alias --alias-name alias/<sops_kms_alias> \
  --target-key-id "$KEY_ID" \
  --profile <sops_kms_profile> --region <region>

KEY_ARN=$(aws kms describe-key --key-id alias/<sops_kms_alias> \
  --query KeyMetadata.Arn --output text \
  --profile <sops_kms_profile> --region <region>)
```

The `ManagedBy=aidd` tag is what makes rule 2 work on the **next** run. Omitting it means the next
run cannot tell its own key from a stranger's.

`sops_kms_profile` and `sops_kms_alias` are interpolated into five shell positions and into the alias
name. Both must be validated `^[A-Za-z0-9._-]+$` before reaching any of them — see
[`blueprint-interview.md`](./blueprint-interview.md).

### A.6.2 — Record the key

Runs for both `created` and `exists`.

1. **Patch the seeded YAML header.** The ARN is now known, so replace the resolve-then-encrypt block
   with the single concrete command using the **full ARN** — `sops --encrypt --kms` accepts an ARN
   only, never an `alias/…`:

   ```
   #   N) Encrypt in place:
   #        sops --encrypt --kms <KEY_ARN> --in-place \
   #             {DEPS_ROOT}/sops/secrets.{env}.yaml
   ```

   The ARN lands in the encrypted file's `sops:` metadata anyway, so writing it in the header
   discloses nothing new. For the `manual` case the header keeps its resolve-then-encrypt form.

2. **Record** alias, ARN and status for the summary.

> **The agent provisions the key only. It never encrypts the file** — it does not hold the real
> values, so `sops --encrypt` would encrypt empty strings. Filling and encrypting stays with the
> engineer. For production, enable CloudTrail and key rotation out of band.
