# Cross-Layer Contracts

**Single owner.** Everything here spans two or more layers. No layer template restates any of it —
they link here.

Duplicating a contract per layer is how the upstream kit shipped its worst drift: one copy gets
edited, the others silently disagree, and the mismatch surfaces at `terraform apply`.

Path keys resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

---

## 1. Module call lookup table

**Drive all module calls from this single table.** `<variant> × <layer> → module calls`. Each cell
lists `service[:block_name]`; the block name is omitted when it equals the service name.

| Layer | `none` | `static-spa` | `ssr` |
|---|---|---|---|
| `1.general` | vpc · security-group:`sg_alb` · `sg_ecs` · `sg_rds` · `sg_valkey` · ecs-cluster:`ecs_cluster` · *(route53=y: route53-zone:`route53_zone` · acm:`acm_cert`)* | same as `none`, **plus** route53=y: a SECOND acm block `acm:acm_cert_us_east_1` through the `aws.us_east_1` provider alias | vpc · security-group:`sg_alb_fe` · `sg_alb_be` · `sg_ecs_fe` · `sg_ecs_be` · `sg_rds` · `sg_valkey` · ecs-cluster:`ecs_cluster` · *(route53=y: route53-zone:`route53_zone` · acm:`acm_cert`)* |
| `2.frontend` | — *(layer absent)* | s3-bucket:`s3_frontend` · cloudfront:`cloudfront` | ecr:`ecr_frontend` · ecs:`ecs_frontend` · alb:`alb_frontend` |
| `3.backend` *(per backend service)* | ecr:`ecr_backend_<name>` · ecs:`ecs_backend_<name>` · then once s3-bucket:`s3_app_content` · then per service iam-policy:`iam_<name>_s3` · then once alb:`alb_backend` | same as `none` | same as `none` |
| `4.database` | aurora · valkey *(→ `rds` when `db_engine = rds`; → `redis` when `cache_engine = redis`)* | same | same |
| `5.messaging` *(messaging=y)* | subset of sqs:`sqs_main` · sns:`sns_topic` · ses:`ses_identity`, then per backend service iam-policy:`iam_<name>_messaging` | same | same |
| `6.delivery` *(delivery=y)* | codestar-connection:`codestar_connection` · s3-bucket:`s3_artifacts` · per pipeline-target codebuild:`codebuild_<name>` · per BLUE_GREEN service codedeploy:`codedeploy_<name>` · per pipeline-target codepipeline:`pipeline_<name>` | same, **plus** FE pipeline: codebuild:`codebuild_frontend` · codebuild:`codebuild_invalidate` · codepipeline:`pipeline_frontend` | same, **plus** when the FE opted in: `frontend` joins the pipeline-target set |
| `7.monitoring` *(monitoring=y)* | cloudwatch-alarm:`alarms` · cloudwatch-dashboard:`dashboard` | same | same |
| `route53-alias` *(after the main loop)* | route53-alias:`route53_alias_backend` in `3.backend` | route53-alias:`route53_alias_cdn` in `2.frontend` | route53-alias:`route53_alias_frontend` in `2.frontend` |

Layer names come from the contract's `LAYERS`, which is **role-indexed by position** — an override renames the rows without changing what each row is for. All seven roles are named there, including toggle-gated ones this environment may not generate.

### Backend service loop

For each entry in `<backend_services>`, call module generation **twice**:

| Step | Service type | Module | Block name |
|---|---|---|---|
| 1 | any | `ecr` | `ecr_backend_<name>` |
| 2 | `api` / `worker` | `ecs` | `ecs_backend_<name>` |

This loop is what expands the table's `3.backend` cell. The two live together because separating a
contract from its expansion rule puts one behaviour in two files.

### Security-group count is a baseline, not a limit

Additional `security-group` calls — bastion, VPN endpoint, monitoring — follow the same
`sg_<purpose>[_<tier>]` naming without changing the algorithm. The naming and tiebreak contract is
owned by the wiring step, not restated here.

---

## 2. ACM-cert invariant

**Every ALB needs a cert. The zone and the certs live in `1.general`, in every variant.**

The `alb` module hardcodes a single **HTTPS:443** listener with
`certificate_arn = var.certificate_arn`. There is no HTTP-only path. An empty string **passes
`terraform validate` and fails `terraform apply`** — which is why this is an invariant rather than a
recommendation.

### Why the zone and cert sit in `1.general` — the cycle break

A cert must be DNS-validated in the hosted zone, and an ALB consumes the cert. Put the zone and cert
in a tier layer and the cert edge `3.backend → 2.frontend` collides with **pre-existing reverse
edges**:

- `ssr`: `ecs_frontend` egress SG → `alb_backend`
- `static-spa`: CloudFront origin = `alb_backend`

That is a two-way cross-layer **dependency cycle with no valid apply order**. Placing the zone and
certs in `1.general` — the absolute upstream layer every tier reads from — means both tier layers
consume `zone_id` and `acm_certificate_arn` **downstream**, so the graph stays acyclic.

Do not "simplify" this by moving the cert next to its ALB. That is the cycle.

### Certs per variant — all in `1.general`

| Variant | route53=y cert(s) | Consumers (cross-layer, downstream) |
|---|---|---|
| `none` | `acm_cert` (region-local) | `alb_backend` in `3.backend` |
| `static-spa` | `acm_cert_us_east_1` (CloudFront) **+** `acm_cert` (region-local) | CloudFront in `2.frontend` ← `acm_certificate_arn_us_east_1`; `alb_backend` ← `acm_certificate_arn` |
| `ssr` | `acm_cert` (region-local wildcard) | `alb_frontend` **and** `alb_backend`, both ← `acm_certificate_arn` |

One **wildcard cert** (`zone_name` + `*.<zone_name>`) per region serves all ALBs in that region.

**ACM certs are region-bound.** A `us-east-1` CloudFront cert cannot attach to an ALB in the
deployment region — that is the whole reason `static-spa` needs two. Both still live in `1.general`;
the `us-east-1` one is created through an `aws.us_east_1` provider alias declared in
`1.general/_backend.tf`.

### `route53 = false`

No DNS-validatable zone exists, so emit **no** `route53_zone` and **no** acm block. Every `alb_*`
keeps `certificate_arn = "" # TODO`, and the summary must warn that an external ACM ARN is required
before apply. Fail-closed.

---

## 3. Route53 module split — one module, two call shapes

The single `route53` module is parameterized so the same scaffolded module serves both calls:

- **Zone call** (`route53_zone`, in `1.general`) — passes `zone_name`, leaves `record_name = null`.
  The module creates **only** `aws_route53_zone` and skips the record, guarded by
  `count = var.record_name == null ? 0 : 1`. Exports `zone_id` and `name_servers`.
- **Alias call** (`route53_alias_*`, in the alias target's layer) — passes `record_name`,
  `alias_target_*`, and the cross-layer `zone_id`. Creates **only** the `aws_route53_record`.

Keep it one module. A second module is not needed and would double the scaffold surface.

The alias record is generated **once, after** the main layer loop, into the alias target's layer:
`3.backend` for `none`, `2.frontend` for `static-spa` and `ssr`. It reads `zone_id` cross-layer from
`1.general` — a downstream edge, no cycle.

### `name_servers` re-export is REQUIRED when `route53 = true`

The module exposes its authoritative NS records as the output **`name_servers`** — not
`route53_name_servers`. Because `_outputs.tf` generation is otherwise delegated to module generation,
which only exports module-native names, the documented `terraform output route53_name_servers` step
**fails** unless `1.general/_outputs.tf` re-exports it under the documented name.

After the `route53_zone` block is generated, append to `1.general/_outputs.tf`:

```hcl
output "route53_name_servers" {
  description = "Name servers for the in-stack Route53 hosted zone — set these at your registrar."
  value       = module.route53_zone.name_servers
}
```

Spell the exported name exactly `route53_name_servers`. Also export `route53_zone_id` and, for the
certs, `acm_certificate_arn` (plus `acm_certificate_arn_us_east_1` for `static-spa`), so the tier
layers can read them downstream.

---

## 4. Frontend wiring — `static-spa`

**Mandatory scaffold steps** when the variant is `static-spa`. The origin contract immediately below
applies always; the cert and alias contracts after it apply when `route53 = true`. These are not
advisory comments; emit the HCL.

### CloudFront has TWO origins — S3 *and* the backend ALB

This is the single most consequential thing in this section, and it is easy to miss because the rest
of the section is about certificates.

| Origin | Source | Behaviour |
|---|---|---|
| S3 (`s3_frontend`) | same layer | **default** — serves the SPA bundle |
| `alb_backend` | **cross-layer, `3.backend`** | an ordered cache behaviour on the API path (`/api/*`) |

The ALB origin is a real cross-layer edge: `2.frontend` ← `3.backend`. It is one of the two
**pre-existing one-directional edges** the layer order accommodates, which is why `3.backend` must be
applied before `2.frontend` — see the dependency table in the composition contract.

Omit it and the environment has **no path from the public edge to the backend at all**. Nothing
fails: `terraform validate` passes, the plan applies, the SPA loads, and every API call 404s at
CloudFront. There is no error message anywhere that points at the missing origin.

It is also the reason `alb_backend_internal = true` in this variant.

> ### Unresolved: how CloudFront reaches an internal ALB
>
> **State this to the user; do not silently pick one.** The two contracts above are jointly
> incomplete, and upstream is incomplete in the same place — it asserts the topology (origin =
> `alb_backend`, ALB private) and never specifies the origin mechanism. There is no correct answer to
> copy.
>
> A plain `custom_origin_config` resolves the ALB's DNS name to **private** addresses, which CloudFront
> cannot route to. The three ways out, none of them free:
>
> | Option | Cost |
> |---|---|
> | **CloudFront VPC origin** | The feature AWS built for exactly this. Needs a contract this kit does not yet have. |
> | **Public ALB + CloudFront managed prefix list on the SG** | Works today, but the ALB gets a public DNS name and `alb_backend_internal` must become `false`, against the variant default. |
> | **Accept it** | `static-spa` is not end-to-end deployable. Honest, and useless to the user. |
>
> Until this is decided, emit the origin **and** say plainly in the summary that the path from
> CloudFront to the backend is unresolved. An environment that plans cleanly and cannot serve `/api`
> is worse than one that says so up front.
>
> Do not "fix" it by flipping `alb_backend_internal` on your own — that is an architecture decision
> with a security boundary attached, and it belongs to whoever owns the environment.

```hcl
# 2.frontend/cloudfront.tf — origins only; the full module call carries more
  origin_alb_domain_name = data.terraform_remote_state.backend.outputs.alb_backend_dns_name
  api_path_pattern       = "/api/*"
```

The wiring step resolves `origin_alb_domain_name` from its TODO placeholder. Pin the source name:
`data.terraform_remote_state.backend.outputs.alb_backend_dns_name`.

**The `aws.us_east_1` provider alias lives in `1.general`**, alongside whatever needs it:

```hcl
provider "aws" {
  alias   = "us_east_1"
  region  = "us-east-1"
  profile = "${var.project}-${var.env}"
}
```

> **Emit the alias whenever anything us-east-1 exists, not only when `route53 = true`.** Two things
> in this variant are region-bound to `us-east-1`: the CloudFront viewer certificate (route53 only)
> and a **CLOUDFRONT-scope WAF** (whenever `enable_waf` is on). With `route53 = false` and
> `enable_waf = true` the cert is absent but the WAF is not, and the alias still has to exist —
> otherwise `enable_waf` is wired to nothing, which the hardening-toggle rule forbids in terms.
>
> Keep it in `1.general` in every case. One home, one rule, no variant-by-variant reasoning about
> where a provider alias lives.

**Two certs in `1.general`**, both validated against the same in-stack zone:

```hcl
module "acm_cert" {                                   # region-local, for alb_backend
  source = "{MODULE_DEPTH}"                           # → modules/acm

  project                   = var.project
  env                       = var.env
  region                    = var.region
  domain_name               = var.zone_name
  subject_alternative_names = ["*.${var.zone_name}"]
  route53_zone_id           = module.route53_zone.zone_id   # same layer, never a tfvars placeholder
}

module "acm_cert_us_east_1" {                         # us-east-1, CloudFront viewer cert
  source    = "{MODULE_DEPTH}"
  providers = { aws = aws.us_east_1 }                 # REQUIRED

  project                   = var.project
  env                       = var.env
  region                    = "us-east-1"
  domain_name               = var.zone_name
  subject_alternative_names = ["*.${var.zone_name}"]
  route53_zone_id           = module.route53_zone.zone_id   # validation records are region-agnostic
}
```

The CloudFront viewer cert is consumed **cross-layer, downstream** via
`data.terraform_remote_state.general.outputs.acm_certificate_arn_us_east_1`. Never a tfvars variable,
and never a `3.backend → 2.frontend` edge.

**The alias record lives in `2.frontend`:**

```hcl
module "route53_alias_cdn" {
  source = "{MODULE_DEPTH}"                           # → modules/route53

  project               = var.project
  env                   = var.env
  region                = var.region
  zone_id               = data.terraform_remote_state.general.outputs.route53_zone_id
  record_name           = var.cdn_domain              # user-owned (blank + TODO)
  alias_target_dns_name = module.cloudfront.distribution_domain_name
  alias_target_zone_id  = module.cloudfront.distribution_hosted_zone_id
}
```

`alias_target_zone_id` **must** be the module attribute `distribution_hosted_zone_id`, not a tfvars
variable and not the hardcoded AWS constant. Preferring the attribute means the value tracks AWS if
it ever changes.

Exact output names the wiring step resolves to — pin these, do not guess:
`module.cloudfront.distribution_hosted_zone_id` (**not** `hosted_zone_id`),
`module.cloudfront.distribution_domain_name`, and
`data.terraform_remote_state.general.outputs.route53_zone_id`.

---

## 5. Frontend wiring — `ssr`

Same invariant, different geometry: the cert lives in the **ALB's own region**, so use the default
provider with **no alias**.

**One wildcard cert in `1.general`, shared by both ALBs.** The frontend ALB is public and the backend
ALB is internal; a single wildcard cert (apex + `*.<zone>`) serves both.

```hcl
module "acm_cert" {
  source = "{MODULE_DEPTH}"                           # → modules/acm

  project = var.project
  env     = var.env
  region  = var.region

  domain_name               = var.zone_name
  subject_alternative_names = ["*.${var.zone_name}"]
  route53_zone_id           = module.route53_zone.zone_id
}
```

Both ALBs read it downstream:

- `2.frontend/alb.tf` → `alb_frontend.certificate_arn = data.terraform_remote_state.general.outputs.acm_certificate_arn`
- `3.backend/alb.tf` → `alb_backend.certificate_arn = data.terraform_remote_state.general.outputs.acm_certificate_arn`

Apply order `1.general` → `3.backend` → `2.frontend` keeps every direction valid.

**The alias record lives in `2.frontend`**, pointing at `alb_frontend`, reading `zone_id` downstream
from `1.general`. `alias_target_zone_id` is `module.alb_frontend.zone_id` — the ALB's canonical
hosted-zone id, same layer.

---

## 6. Shared ECS cluster, ECR, and ECS service contracts

**One ECS cluster in `1.general`**, shared by every tier-level ECS service. **One ECR repository per
ECS service**, in the same tier layer as its consumer.

### `ecs-cluster` — called only from `1.general`

- `aws_ecs_cluster` — Container Insights on by default.
- `aws_ecs_cluster_capacity_providers` — `FARGATE` + `FARGATE_SPOT`, configurable default strategy.
- `aws_cloudwatch_log_group` — `/ecs/${var.project}-${var.env}`, configurable retention;
  `kms_key_id` set to the CMK when `enable_log_kms = true`, else `null`.

**`enable_log_kms` (bool, default `false`)** — when true, also create a `count`-gated CMK whose key
policy grants the regional CloudWatch Logs service principal use of the key, scoped by the
`kms:EncryptionContext:aws:logs:arn` condition to this log group, plus a root-account statement.

CloudWatch Logs has **no AWS-managed-key option**, so a CMK is the only way to encrypt it — which is
why this is the **only CMK in the kit** and why it is prod-only. Seed it `true` for prod and staging,
`false` for dev.

Required outputs: `cluster_id`, `cluster_name`, `cluster_arn`, `log_group_name`, `log_group_arn`.

### `vpc` — called only from `1.general`

Exposes `enable_flow_logs` (bool, default `false`). When true, `count`-gated alongside the
VPC/subnets/NAT:

- `aws_flow_log` with `traffic_type = "ALL"` → a CloudWatch log group
- `aws_cloudwatch_log_group` `/aws/vpc/${var.project}-${var.env}-flow-logs`
- `aws_iam_role` + `aws_iam_role_policy` — trust `vpc-flow-logs.amazonaws.com`, inline policy with
  the standard Logs write actions

Satisfies the SRE flow-log rule. Seed `true` for prod and staging, `false` for dev.

### `ecr` — one repository per ECS service

Called from `3.backend` once per backend service (**both** `api` and `worker` get a repo), and from
`2.frontend` once for `ssr`.

- `aws_ecr_repository` — `name = var.repository_name`, **and the `Name` tag must equal
  `var.repository_name` too**, not a generic `${var.project}-${var.env}-ecr`. Two repos per
  environment would otherwise share one `Name` tag: the discriminator has to reach the **tag**, not
  just the resource name.
- `image_tag_mutability = var.image_tag_mutability`, module default `"MUTABLE"` — preserves the
  `:latest` push-to-deploy flow. **The kit never auto-sets `"IMMUTABLE"`.** Production may set it by
  hand, with versioned tags.
- `scan_on_push = true`; `encryption_configuration.encryption_type = "KMS"` (AWS-managed key).
- `aws_ecr_lifecycle_policy` — keep last N tagged (default 30), expire untagged after D days
  (default 14).

The module **must not** declare any IAM role or auth resource. Push/pull permission lives with the
ECS task execution role, or with pipelines outside the blueprint.

Outputs: `repository_url`, `repository_arn`, `repository_name`.

### `ecs` — ALB-optional, one module for both `api` and `worker`

A **single** module serves both shapes: `api` passes a real `target_group_arn`; `worker` passes
`null`.

- `aws_ecs_task_definition` — `image = "${var.image_repository_url}:${var.image_tag}"`,
  `image_tag` defaulting to `"latest"` at module level and deliberately **not** exposed at env level.
  `portMappings` is gated on `var.container_port`, omitted for workers.
- `aws_ecs_service` — the twin pair described below. The `load_balancer` block is **`dynamic`**,
  keyed on `var.target_group_arn == null ? [] : [1]`.
- `health_check_grace_period_seconds` is likewise conditional:
  `var.target_group_arn == null ? null : var.health_check_grace_seconds`.

> **The grace-period gate is a correctness guard, not tidiness.** AWS rejects that argument with
> `InvalidParameterException` on a service with no load balancer, so a worker's `terraform apply`
> **fails** if it is not gated. It must stay gated wherever the `load_balancer` block is omitted.

- `aws_iam_role` for task execution (must include `AmazonECSTaskExecutionRolePolicy` for ECR pull)
  plus a per-service task role. The module **creates** the task role but does **not** inline its
  application permissions — those attach through a separate `iam-policy` block. For workers, that is
  where SQS/EventBridge/S3 permissions belong; never inlined here, never left as a TODO.
- `_outputs.tf` **must** export `task_role_arn`, `task_role_name`, and `task_execution_role_arn`.
  `task_role_name` is required because `aws_iam_role_policy` attaches by role **name**, not ARN.

Inputs wired later by the wiring step: `cluster_id`, `cluster_name`, `log_group_name` (from
`1.general`); `target_group_arn` (nullable, default `null`); `image_repository_url`;
`cpu`, `memory`, `desired_count`; `container_port` and `health_check_grace_seconds` (nullable,
`api` only).

**Duplicate-scaffold safety.** Multiple backend services of either type share the **same** scaffolded
`ecs` module; the second and later calls only add an env-folder block. `ssr` additionally calls it
from `2.frontend`.

### ECS deployment-strategy twin

`variable "deployment_strategy"` (string, default `"ROLLING"`, validated ∈ {`ROLLING`,
`BLUE_GREEN`}) count-gates a twin pair:

- `aws_ecs_service "this"` — `count = var.deployment_strategy == "ROLLING" ? 1 : 0`. No
  `deployment_controller` block: the ECS default **is** the rolling controller.
- `aws_ecs_service "blue_green"` — `count = … == "BLUE_GREEN" ? 1 : 0`. Identical arguments **plus**
  `deployment_controller { type = "CODE_DEPLOY" }` **plus**
  `lifecycle { ignore_changes = [task_definition, load_balancer] }`. CodeDeploy owns the task
  revision and the blue↔green swap after the first apply; without `ignore_changes` every plan tries
  to revert the live deployment.

> **The `moved` block is mandatory.** Adding `count` changes the state address from
> `aws_ecs_service.this` to `aws_ecs_service.this[0]` for **every** environment consuming the module —
> including pure-ROLLING ones with delivery off. Without the migration, Terraform plans a
> destroy/create of a **running service**.
>
> ```hcl
> moved {
>   from = aws_ecs_service.this
>   to   = aws_ecs_service.this[0]
> }
> ```

**Outputs must use `one(concat(...))`** so consumers do not care which twin is active:
`value = one(concat(aws_ecs_service.this[*].name, aws_ecs_service.blue_green[*].name))`. Exactly one
twin has `count = 1`, so `one()` never fails. Forgetting this breaks every by-name cross-layer
auto-wiring in the blueprint.

**Forbidden:** the ECS-native `deployment_configuration.strategy` blue/green, and any attempt at a
CodeDeploy *rolling* deployment — CodeDeploy's ECS platform supports blue/green **only**. The two
controllers are mutually exclusive per service.

⚠️ **Switching an existing service between `ROLLING` and `BLUE_GREEN` destroys one service and
creates the other** — different Terraform address, and AWS forbids changing `deployment_controller`
in place. Brief interruption. Pick the strategy at generation time; changing it later is a
migration, not a tweak.

### `alb_backend` — one ALB, N target groups

- One `aws_lb`.
- One HTTPS listener, default action → the first api service's target group.
- One `aws_lb_target_group` per api service, keyed by service name, exposed as
  `target_group_arns = { <service-name> = … }` so each `ecs` block can look up its own.
- For every **secondary** api service, one `aws_lb_listener_rule` with a `path-pattern` condition,
  left as a TODO placeholder.

One api service → exactly 1 target group and 0 listener rules.

**Monitoring dimension outputs.** The `alb` module's `_outputs.tf` also exports `alb_arn_suffix` and
`target_group_arn_suffixes`. These exist regardless of the monitoring toggle; the **layer-level
re-export** of them is what is gated on `monitoring == true`. With monitoring off, `_outputs.tf` is
byte-for-byte unchanged.

**Hardening toggles** — `enable_waf` and `enable_access_logs`, both bool, default `false`,
`count`-gated:

- `enable_waf` → `aws_wafv2_web_acl` (scope `REGIONAL`, default allow, common managed rule set) plus
  an association.
- `enable_access_logs` → `access_logs { enabled = true, bucket = … }` plus the log bucket and a
  policy granting the regional ELB service account `s3:PutObject`.

> **Public ALB only.** Attach both **only** to the internet-facing ALB: `alb_backend` in `none`,
> `alb_frontend` in `ssr`. The `static-spa` `alb_backend` is internal behind CloudFront and the `ssr`
> `alb_backend` is internal behind `ecs_frontend` — those keep both toggles `false`.

**Blue-green additions** — `blue_green_service_names` (list, default `[]`; an empty list creates
**zero** resources, so non-delivery environments stay byte-for-byte identical) and
`test_listener_port` (default 8443):

- Per listed name, a second "green" target group, identical to the blue spec but for the name.
  ⚠️ Target-group names cap at **32 characters**, so the name uses a **deterministic** truncation:
  `name = "${substr("${var.project}-${var.env}-${each.key}", 0, 28)}-tg2"`. Never an ad-hoc
  truncation — CodeDeploy swaps by NAME and reads it only through the output map, so the truncation
  must happen exactly once, in the module.
- One `aws_lb_listener "test"`, gated on a non-empty list, HTTPS on `test_listener_port`, **same
  `certificate_arn`** as the prod listener.
- Additive outputs: `https_listener_arn`, `test_listener_arn` (`null` when off),
  `target_group_names`, `green_target_group_names`. CodeDeploy's `target_group_pair_info` takes
  **names, not ARNs** — hence the name maps alongside the existing ARN map.

### `s3_app_content` — one shared private bucket

One per environment, shared by every backend service, **not** per service. **Reuses the `s3-bucket`
module** — the same one `s3_frontend` uses. Do not create a second module.

- `name = "app-content"`, so the module derives
  `${var.project}-${var.env}-app-content-${account-id}` and the `Name` tag without the suffix.
- Private: public access fully blocked, SSE `aws:kms` with the AWS-managed key, plus always-on
  versioning.
- Unlike `s3_frontend` it has **no** OAC and no CloudFront bucket policy — this is content the
  backend reads and writes through the SDK.
- Export `s3_app_content_bucket_arn` and `s3_app_content_bucket_id` into `3.backend/_outputs.tf`.
- **No IAM here.** Granting the task role access is the `iam-policy` block's job.

Two additive nullable inputs, both default `null` so every existing caller is unchanged:
`bucket_policy` (backs a count-gated `aws_s3_bucket_policy`; the delivery layer's `s3_artifacts`
passes a Deny-unless-PrincipalArn document through it) and `kms_key_arn` (wired into
`kms_master_key_id`; `null` means the free AWS-managed key, an ARN opts into a CMK).

### `iam_<service>_s3` — task role → S3 policy

A reusable **single-instance** `iam-policy` module, called from `3.backend` once per backend
service — `api` **and** `worker`.

The module is **generic**: it hardcodes no S3, action, or resource statement. The caller passes the
complete document.

```hcl
resource "aws_iam_role_policy" "this" {
  name   = "${var.project}-${var.env}-${var.policy_name_suffix}"
  role   = var.role_name
  policy = var.iam_custom_policy.template
}
```

Inputs: `project`, `env`, `role_name` (binds by **name**, not ARN), `policy_name_suffix`, and
`iam_custom_policy` of type `object({ template = string })`.

The bucket ARN lives **inside** the inline policy — it is not a separate module input. So the wiring
step resolves **only** `role_name` → `module.ecs_backend_<name>.task_role_name`.

> Because the module structurally constrains nothing, the security reviewer inspects the **inline
> policy JSON emitted at the env call**, not the module. A wildcard passed in here is invisible to
> any check that only reads the module.

**Generation order:** `iam_<service>_s3` blocks come **after** `s3_app_content` (its ARN is
referenced in the emitted policy) and **after** the per-service `ecs` blocks (each `task_role_name`).
All references are same-layer, so no remote state is involved.

---

## 7. What must never be restated

A layer template that copies any of the following has reintroduced the drift this file exists to
prevent:

- the module call lookup table, or any single cell of it
- the ACM-cert invariant, or the reason the zone lives in `1.general`
- either frontend wiring contract
- the shared ECS cluster / ECR / ECS service contracts
- the `moved` block, the `one(concat(...))` output rule, or the 32-character target-group truncation

Link here instead.
