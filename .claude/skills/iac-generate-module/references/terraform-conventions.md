# Terraform Module Conventions

How a scaffolded local module is shaped, named, and hardened.

Path keys resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

> Base `tkm:infra` ships a file of the same name with a different rule set. This one governs
> `tkm:iac-*` output only. Where they disagree, see
> the conflicts reference in `tkm:iac-review`.

## Global standards

| Rule | Value |
|---|---|
| Terraform version | `>= 1.14.7` |
| AWS provider | `>= 6.37.0` |
| Required files per module | `_versions.tf`, `_variables.tf`, `main.tf`, `_outputs.tf`, `README.md` |
| Path header | First line of every `.tf` file: `# <relative-path>.tf` |
| `Name` tag | `${var.project}-${var.env}-${var.name}-<resource-type-kebab>` |
| Required tags | `Environment`, `Project`, `Owner`, `ManagedBy = terraform` |
| Variable block order | `description` → `default` → `type` → `validation` |
| `count` / `for_each` | **First** argument in the resource block |
| `tags` | **Last** real argument, before `depends_on` and `lifecycle` |
| Base variables | `project` and `env` in every module, grouped under `#basic` |
| Provider profile | `profile = "${var.project}-${var.env}"` |
| README | Must carry terraform-docs hook markers |

## Core principles

**Structure first.** Scaffold the full skeleton before implementing resources. Keep files focused by
responsibility.

**Predictable naming.** Resource identifiers reflect purpose, not generic labels.

**Explicit interfaces.** Every variable and output carries a `description`; every variable carries an
explicit `type`. Optional behavior is encoded through defaults and clear conditionals.

**Validation readiness.** Output must be ready for `terraform fmt`, `terraform validate` and tflint
with no manual cleanup.

## `_variables.tf`

- First line: the path header.
- Group with comments: `#basic` for `project` / `env`, `#<module-name>` for the rest.
- Baseline variables `project` (string) and `env` (string) in **every** module.
- Every variable: a clear `description` and an explicit `type`.
- `default = null` or an explicit default for optional values.
- Add `validation` blocks when a constraint is business-critical.

> **Never use interpolation inside a `description`.** HCL forbids it and `terraform init` fails with
> `Error: Variables not allowed`. Write
> `description = "RDS identifier suffix appended to <project>-<env>-"`, not the `${var.project}` form.

## `main.tf`

- First line: the path header.
- Name and tag pattern: `Name = "${var.project}-${var.env}-${var.name}-<resource-type-kebab>"`.
- Add `lifecycle { create_before_destroy = true }` on significant resources.
- Use conditional creation only where it adds flexibility without obscuring readability.

## `_outputs.tf`

- First line: the path header.
- Expose the key IDs, ARNs and names downstream modules consume.
- Every output carries a `description`.
- Mark sensitivity where it applies.

## `README.md`

Must contain the terraform-docs hook markers so the hook can update it:

```
<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
```

---

## Encryption and TLS defaults — always on

Scaffolded modules ship these so generated infrastructure is clean from the first run. Each is a HIGH
static-scanner finding that otherwise fires on **every** fresh generation.

Use the **AWS-managed KMS key** — free, no `aws_kms_key` resource. A customer-managed key is a
separate per-environment hardening option, not the default.

- **`aws_lb_listener` on 443** — set `ssl_policy = "ELBSecurityPolicy-TLS13-1-2-2021-06"` on every
  HTTPS listener. Leaving it unset defaults to a weak policy.
- **`aws_s3_bucket`** — always pair with an `aws_s3_bucket_server_side_encryption_configuration`
  whose rule sets `sse_algorithm = "aws:kms"` and `kms_master_key_id = var.kms_key_arn`. The module
  gains `variable "kms_key_arn"` (string, nullable, **default `null`**). At `null` AWS resolves the
  free AWS-managed key; passing a CMK ARN opts that bucket in to a customer-managed key. Keep the
  `aws_s3_bucket_public_access_block` and the always-on versioning too.
- **`aws_ecr_repository`** — set `encryption_configuration { encryption_type = "KMS" }`. The
  AWS-managed ECR key needs no `kms_key`.

### The accepted-and-suppressed scanner finding

The default SSE block emits no CMK, so trivy's customer-managed-key rule fires on it. That is an
**accepted baseline**, suppressed with a rationale comment block whose **last line** is the ignore
directive, placed directly above the resource with no blank line between:

```hcl
# SSE with the free AWS-managed key by default (kms_master_key_id = var.kms_key_arn, default null).
# Pass a CMK ARN via var.kms_key_arn to opt this bucket in to a customer-managed key.
# checkov is satisfied (sse_algorithm = "aws:kms"). The trivy CMK rule is an ACCEPTED, SUPPRESSED
# baseline — CMK is reserved for forced cases only.
#trivy:ignore:AVD-AWS-0132
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_arn # null → AWS-managed key; ARN → opt-in CMK
    }
  }
}
```

A suppression **must** carry its rationale. A bare directive is indistinguishable from someone
silencing a finding they did not understand.

---

## Env-conditional hardening toggles

A second layer on top of the always-on defaults. The split rule:

> **Cheap is always-on, every environment, no toggle. Expensive gets a per-feature `enable_<x>`
> toggle, module default `false`, flipped on for prod and staging and left off for dev.**

Dev intentionally runs leaner; those findings are an accepted dev trade-off.

Gating mechanics, for every toggled item:

- Declare the bool in the **module's** `_variables.tf`, adjacent to `#basic`, with the default shown.
- Gate the companion resources with `count = var.enable_<x> ? 1 : 0` — **first** argument in the block.
- Reference a gated resource with `[0]`. Guard any output reading one:
  `value = var.enable_<x> ? aws_<res>.this[0].<attr> : null`.
- Scaffold each toggled feature's **companion resources together**. A half-wired toggle fails
  `terraform apply`.

| # | Feature | Toggle | Default | Module |
|---|---|---|---|---|
| 1 | S3 versioning | *none — always on* | enabled | `s3-bucket` |
| 2 | WAFv2 on the public ALB | `enable_waf` | `false` | `alb` |
| 3 | VPC flow logs | `enable_flow_logs` | `false` | `vpc` |
| 4 | ALB access logs | `enable_access_logs` | `false` | `alb` |
| 5 | CloudWatch log-group CMK | `enable_log_kms` | `false` | `ecs-cluster`, and any module owning a log group |
| 6 | ECR tag mutability | `image_tag_mutability` (string) | `"MUTABLE"` | `ecr` |

S3 versioning is cheap, so it is always-on rather than toggled:

```hcl
resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}
```

---

## Multi-instance modules

Services an environment may call **more than once**, one per purpose. Two kinds, both needing a
per-block discriminator.

**Single-resource-per-call** — `security-group`, `iam-role`, `iam-policy`. One SG, role, or inline
policy per call. Instantiate once per purpose.

**Discriminator-required reusable** — `alb`, `sns`, `sqs`, `ecr`. Each call creates one primary
resource, so the module **must** expose a discriminator (`name` / `name_suffix`) interpolated into
**both** the resource identifier **and** the `Name` tag. Without it, two blocks collide — two SNS
topics both named `${project}-${env}-topic`.

> **The discriminator rule.** A module in the second kind whose resource name **or** `Name` tag is a
> fixed `${var.project}-${var.env}-<static>` with no discriminator is a bug. The bestpractice
> reviewer flags it MEDIUM. The interpolation must reach **both**: `${var.project}-${var.env}-${var.name}-<svc>`.

### Block and output naming

| Module | Block | Output key | Examples |
|---|---|---|---|
| `security-group` | `sg_<purpose>` | `sg_<purpose>_id` | `sg_alb`, `sg_ecs`, `sg_rds` |
| `iam-role` | `role_<purpose>` | `role_<purpose>_arn` | `role_ecs_task` |
| `iam-policy` | `iam_<svc>_s3` | `policy_name` / `policy_id` | `iam_api_s3` |
| `alb` | `alb_<purpose>` | `alb_<purpose>_*` | `alb_backend`, `alb_frontend` |
| `sns` | `sns_<purpose>` | `topic_arn` / `topic_name` | `sns_alerts`, `sns_events` |
| `sqs` | `sqs_<purpose>` | `queue_arn` / `queue_url` | `sqs_main`, `sqs_jobs` |
| `ecr` | `ecr_<purpose>` | `repository_url` / `repository_arn` | `ecr_backend_api` |

`<purpose>` is the consuming resource's role. The discriminator variable differs by module:
`security-group` and `iam-role` use the block's `<purpose>`; `alb` and `ecr` use `name`; `sns` and
`sqs` use `name_suffix`.

When the same purpose exists in two tiers, suffix with the tier token: `sg_alb_fe`, `sg_alb_be`,
`sg_ecs_fe`, `sg_ecs_be`.

> **Do not** use `security_group_<name>` or `module.security_group_bastion` style names. They break
> the `<purpose>`-based tiebreak the wiring step depends on — see
> `iac-connect-modules`.

One file holds many blocks: all security groups in `security-group.tf`, one `module` block each, with
one output per block in `_outputs.tf`.

## Aggregate module exception

The default module shape is single-responsibility. A few are intentionally **aggregate** —
`cloudwatch-alarm` and `cloudwatch-dashboard` take the environment's *dimension* inputs and render
every alarm or widget internally via `for_each` over an internal `locals` map.

Render via `for_each`, and **do not** impose the default single-resource scalar contract
(`alarm_name`, `metric_name`, `threshold`, `dimensions`, `comparison_operator`, `statistic`,
`period`, `evaluation_periods`, `treat_missing_data`, `alarm_description`) — on these modules those
are internal locals, never inputs.

The input surface is below. **Every variable is defaulted, so the module validates standalone**, and
each default doubles as the off switch for the family it belongs to.

```hcl
variable "project" { type = string }
variable "env"     { type = string }
variable "region"  { type = string }

# dimensions — an empty/zero value count-gates that family's alarms OFF
variable "ecs_cluster_name" {                # ECS ClusterName
  type    = string
  default = ""
}
variable "ecs_service_names" {               # key → ServiceName
  type    = map(string)
  default = {}
}
variable "alb_arn_suffix" {                  # ALB LoadBalancer
  type    = string
  default = ""
}
variable "alb_target_group_arn_suffixes" {   # key → TargetGroup
  type    = map(string)
  default = {}
}
variable "rds_db_instance_identifier" {      # RDS DBInstanceIdentifier
  type    = string
  default = ""
}
variable "aurora_db_cluster_identifier" {    # null → Aurora alarms gated OFF
  type    = string
  default = null
}
variable "redis_cache_cluster_ids" {         # per-node CacheClusterId
  type    = list(string)
  default = []
}

# dynamic thresholds — nullable; null gates that ONE alarm off
variable "rds_freeable_memory_threshold" {
  type    = number
  default = null
}
# ... one block per dynamic row, same shape:
#   rds_db_connections_threshold, rds_read_iops_threshold, rds_write_iops_threshold,
#   rds_freeable_storage_space_threshold, redis_freeable_memory_threshold
# Aurora rows only — default null so the plain-RDS path is unaffected:
#   aurora_freeable_memory_threshold, aurora_db_connections_threshold

# the alerting hook — the ONLY inputs the alerting pipeline touches
variable "alarm_actions" {
  type    = list(string)
  default = []
}
variable "ok_actions" {
  type    = list(string)
  default = []
}
```

> **Every block with both `type` and `default` must be multi-line.** HCL rejects two arguments on one
> line — `variable "x" { type = number, default = null }` fails `terraform fmt` and `validate` with
> "Invalid single-argument block definition". Only a lone-argument block such as `{ type = string }`
> may stay on one line. That is why the eight threshold variables above are listed as names rather
> than written out compactly: a compact template is a trap, however it is captioned.

**A nullable threshold is not a defaulted threshold.** These are the rows the monitoring layer marks
dynamic because a correct value depends on the instance class. `null` count-gates that single alarm
off until an operator supplies a number — it never means "use a sensible default". Picking a literal
here produces an alarm that fires constantly or never, and both erode trust in the whole board.

`cloudwatch-dashboard` takes the **same dimension variables and no thresholds** — it reads dimensions
to build widgets and has nothing to compare against.

Enablement is derived, not declared: `ecs` is on when `ecs_cluster_name != ""` **and**
`length(ecs_service_names) > 0`; `alb` when `alb_arn_suffix != ""`; `rds` when
`rds_db_instance_identifier != ""`; `aurora` when `aurora_db_cluster_identifier != null`; `redis`
when `length(redis_cache_cluster_ids) > 0`.

---

## Modules are an output, not a prerequisite

`{MODULE_DIR}` is expected to be **empty in a fresh project**. Modules are something this kit
*creates*. A missing module folder is the normal path, not an error — scaffold it, then emit the
consumer block.

## Constraints

- Never hardcode a secret, credential, region, or account ID.
- Never create files outside module and env scope.
- Prefer inputs for sensitive data; mark sensitive outputs.
- Avoid permissive defaults that create public exposure by accident.
- Keep a module to one coherent infrastructure responsibility. If resources are loosely related,
  recommend splitting.
- Do not change version constraints outside an explicit request.
- If input or output requirements are ambiguous, ask up to three questions to lock the schema rather
  than guessing.
