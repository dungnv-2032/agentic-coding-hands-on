# Tunable Variables

The canonical list of tunable infrastructure variables, **and** the B.2 post-process that rewrites
literals to reference them.

Phase A declares every applicable row in the environment-level `_variables.tf` and seeds its default
in `terraform.{env}.tfvars`. B.2 then rewrites the matching literals in generated `.tf` files.

> **The table and the algorithm live together on purpose.** B.2 matches by the **attribute path**
> column below. Move the table and the algorithm apart, and a table edit silently stops matching —
> the rewrite just logs a skip and nobody notices.

**Naming:** `<service-or-block>_<attribute>`, snake_case.

**Keyed by tier and variant**, as the source keys it — deliberately not forced into the layer
taxonomy, because several rows apply to files in two different layers at once.

---

## B.2 — Tunable extraction

Runs **after** the layer loop completes, before the symlink step. It rewrites inline literals in
generated `.tf` files to `var.<name>`. The matching `variable` blocks and tfvars defaults already
exist from Phase A — **B.2 only modifies module-call `.tf` files.**

### On a fresh environment B.2 is largely a no-op, by design

The attribute paths below were captured against fuller module input shapes. Because every module is
force-scaffolded, a scaffolded module's inputs are generally **flatter** — `engine_version` directly
rather than `rds_instance.engine_version` — and the emitted module call is intentionally minimal,
mostly TODO placeholders rather than concrete literals.

So B.2 logs many `skip: <block>.<path> not found in <file>` entries. **That is routine, not an
error.** Do not treat a run of skips as a failure, and do not "fix" it by inventing literals to
rewrite.

The step is kept for forward compatibility: once a scaffolded module is filled in by hand with
concrete values matching these paths, a later run picks them up and rewrites them without the user
asking. The variables themselves are declared regardless, so they can be wired by hand at any point.

---

## Common to all variants

| Variable | Default | Type | File | Block | Attribute path |
|---|---|---|---|---|---|
| `vpc_cidr` | `"10.0.0.0/16"` | string | `1.general/vpc.tf` | `vpc` | `vpc_cidr` |
| `vpc_public_cidrs` | `["10.0.0.0/24","10.0.1.0/24"]` | list(string) | `1.general/vpc.tf` | `vpc` | `public_cidrs` |
| `vpc_private_cidrs` | `["10.0.10.0/24","10.0.11.0/24"]` | list(string) | `1.general/vpc.tf` | `vpc` | `private_cidrs` |
| `vpc_only_one_nat_gateway` | `true` | bool | `1.general/vpc.tf` | `vpc` | `only_one_nat_gateway` |

### Database — engine-scoped

**Only one engine's tunables are ever emitted per environment.**

Aurora is the default (`db_engine ∈ {aurora-serverless, aurora-provisioned}`):

| Variable | Default | Type | File | Block | Attribute path |
|---|---|---|---|---|---|
| `aurora_engine_version` | `"16.4"` | string | `4.database/aurora.tf` | `aurora` | `engine_version` |
| `aurora_min_acu` | `0` | number | same | `aurora` | `serverlessv2_scaling_configuration.min_capacity` — **0 means scale-to-zero auto-pause** |
| `aurora_max_acu` | `1` | number | same | `aurora` | `serverlessv2_scaling_configuration.max_capacity` |
| `aurora_instance_class` | `"db.r6g.large"` | string | same | `aurora` | cluster-instance `instance_class` — **provisioned only**; serverless v2 uses `db.serverless` |
| `aurora_backup_retention_period` | `7` | number | same | `aurora` | `backup_retention_period` |
| `aurora_storage_encrypted` | `true` | bool | same | `aurora` | `storage_encrypted` |
| `aurora_skip_final_snapshot` | `true` | bool | same | `aurora` | `skip_final_snapshot` |
| `aurora_apply_immediately` | `true` | bool | same | `aurora` | `apply_immediately` |

Serverless v2 emits `serverlessv2_scaling_configuration { min_capacity, max_capacity }` on a
`db.serverless` cluster instance. Provisioned uses `instance_class` and **no** scaling block.

When `db_engine = rds`, emit the `rds_*` set into `4.database/rds.tf` instead:

| Variable | Default | Type | Block | Attribute path |
|---|---|---|---|---|
| `rds_parameter_family` | `"postgres16"` | string | `rds` | `rds_db_parameters.family` |
| `rds_allocated_storage` | `20` | number | `rds` | `rds_instance.allocated_storage` |
| `rds_max_allocated_storage` | `100` | number | `rds` | `rds_instance.max_allocated_storage` |
| `rds_engine_version` | `"16.4"` | string | `rds` | `rds_instance.engine_version` |
| `rds_instance_class` | `"db.t4g.micro"` | string | `rds` | `rds_instance.instance_class` |
| `rds_multi_az` | `false` | bool | `rds` | `rds_instance.multi_az` |
| `rds_storage_type` | `"gp3"` | string | `rds` | `rds_instance.storage_type` |
| `rds_skip_final_snapshot` | `true` | bool | `rds` | `rds_instance.skip_final_snapshot` |
| `rds_apply_immediately` | `true` | bool | `rds` | `rds_instance.apply_immediately` |
| `rds_backup_retention_period` | `7` | number | `rds` | `rds_instance.backup_retention_period` |
| `rds_storage_encrypted` | `true` | bool | `rds` | `rds_instance.storage_encrypted` |
| `rds_publicly_accessible` | `false` | bool | `rds` | `rds_instance.publicly_accessible` |

### Cache — engine-scoped

Valkey is the default (`cache_engine = valkey`):

| Variable | Default | Type | File | Block | Attribute path |
|---|---|---|---|---|---|
| `valkey_num_cache_clusters` | `1` | number | `4.database/valkey.tf` | `valkey` | `num_cache_clusters` |
| `valkey_node_type` | `"cache.t4g.micro"` | string | same | `valkey` | `node_type` |
| `valkey_engine_version` | `"8.0"` | string | same | `valkey` | `engine_version` |
| `valkey_parameter_group_name` | `"default.valkey8"` | string | same | `valkey` | `parameter_group_name` |
| `valkey_auto_minor_version_upgrade` | `true` | bool | same | `valkey` | `auto_minor_version_upgrade` |
| `valkey_automatic_failover_enabled` | `false` | bool | same | `valkey` | `automatic_failover_enabled` |
| `valkey_multi_az_enabled` | `false` | bool | same | `valkey` | `multi_az_enabled` |
| `valkey_apply_immediately` | `true` | bool | same | `valkey` | `apply_immediately` |

When `cache_engine = redis`, emit the `redis_*` equivalents into `4.database/redis.tf` — the same set
with Redis values: `redis_engine_version = "7.1"`, `redis_parameter_group_name = "default.redis7"`,
and the rest identical.

---

## Shared ECR settings

ECR tunables are **shared across every repository in the environment** — one set applies uniformly to
every `ecr_backend_<name>` and to `ecr_frontend`. Per-repository divergence is a hand-edit, not a
blueprint concern.

| Variable | Default | Type | File | Block | Attribute path |
|---|---|---|---|---|---|
| `ecr_lifecycle_keep_count` | `30` | number | `3.backend/ecr.tf`, `2.frontend/ecr.tf` (ssr) | `ecr_*` | `lifecycle_keep_count` |
| `ecr_lifecycle_untagged_days` | `14` | number | same | `ecr_*` | `lifecycle_untagged_days` |
| `ecr_image_tag_mutability` | `"MUTABLE"` | string | same | `ecr_*` | `image_tag_mutability` |
| `ecr_scan_on_push` | `true` | bool | same | `ecr_*` | `scan_on_push` |

Repository **names** derive from `${var.project}-${var.env}-<service-name>` at the call site — not a
tunable.

---

## Shared ECS cluster

| Variable | Default | Type | File | Block | Attribute path |
|---|---|---|---|---|---|
| `ecs_container_insights` | `"enabled"` | string | `1.general/ecs-cluster.tf` | `ecs_cluster` | `container_insights` |
| `ecs_log_retention_days` | `30` | number | same | `ecs_cluster` | `log_retention_days` |
| `ecs_capacity_fargate_base` | `1` | number | same | `ecs_cluster` | `capacity_providers.fargate.base` |
| `ecs_capacity_fargate_weight` | `1` | number | same | `ecs_cluster` | `capacity_providers.fargate.weight` |
| `ecs_capacity_fargate_spot_weight` | `0` | number | same | `ecs_cluster` | `capacity_providers.fargate_spot.weight` |

Spot weight defaults to `0`. Production typically keeps it there; dev and staging can mix spot in for
cost.

---

## Backend tier

Emitted **per service** — Phase A loops over `<backend_services>` and produces one variable per row,
substituting `<name>`. Defaults are the same for every service; per-environment overrides live in
tfvars.

### Every backend service — `api` and `worker`

| Variable template | Default | Type | File | Block | Attribute path |
|---|---|---|---|---|---|
| `ecs_backend_<name>_cpu` | `512` | number | `3.backend/ecs.tf` | `ecs_backend_<name>` | `ecs_task_definition.task_definitions[0].total_cpu` |
| `ecs_backend_<name>_memory` | `1024` | number | same | same | `…total_memory` |
| `ecs_backend_<name>_desired_count` | `2` (api) / `1` (worker) | number | same | same | `ecs_services[0].desired_count` |

### `api` type only — workers skip these

| Variable template | Default | Type | File | Attribute path |
|---|---|---|---|---|
| `backend_<name>_container_port` | `8080` | number | `3.backend/ecs.tf`, `3.backend/alb.tf` | `ecs_services[0].load_balancer.container_port` · target-group `port` · health-check `port` |
| `ecs_backend_<name>_health_check_grace_seconds` | `120` | number | `3.backend/ecs.tf` | `ecs_services[0].load_balancer.health_check_grace_period_seconds` |

A worker has no load balancer, so both are omitted — the grace period in particular **must** be
absent or `terraform apply` fails. See
[`cross-layer-contracts.md`](./cross-layer-contracts.md).

### Shared `alb_backend` — one set, not per service

| Variable | Default | Type | File | Attribute path |
|---|---|---|---|---|
| `alb_backend_internal` | `false` (`none`) / `true` (`static-spa`, `ssr`) | bool | `3.backend/alb.tf` | `alb.internal` |
| `alb_backend_idle_timeout` | `60` | number | same | `alb.idle_timeout` |
| `alb_backend_health_check_path` | `"/health"` | string | same | target-group health-check `path` |
| `alb_backend_healthy_threshold` | `3` | number | same | `healthy_threshold` |
| `alb_backend_unhealthy_threshold` | `3` | number | same | `unhealthy_threshold` |
| `alb_backend_health_check_interval` | `30` | number | same | `interval` |

> **`alb_backend_internal` depends on the variant.** For `none` the backend ALB is public (`false`).
> For `static-spa` and `ssr` it sits behind CloudFront or the frontend ECS and is private (`true`).
> Phase A picks the default from the `frontend` input — getting it wrong either exposes the backend
> directly to the internet, or makes the public path unreachable.

The ALB-level health-check variables apply to **every** target group on `alb_backend`. If different
api services need distinct health-check paths, hand-edit after generation; Phase A does not emit
per-service health-check variables, to keep the tfvars surface manageable. Per-service
`backend_<name>_container_port` covers the common case.

---

## Frontend ECS tier — variant `ssr` only

| Variable | Default | Type | File | Block |
|---|---|---|---|---|
| `frontend_container_port` | `3000` | number | `2.frontend/ecs.tf`, `2.frontend/alb.tf` | `ecs_frontend`, `alb_frontend` |
| `ecs_frontend_cpu` | `512` | number | `2.frontend/ecs.tf` | `ecs_frontend` |
| `ecs_frontend_memory` | `1024` | number | same | same |
| `ecs_frontend_desired_count` | `2` | number | same | same |
| `ecs_frontend_health_check_grace_seconds` | `120` | number | same | same |
| `alb_frontend_internal` | `false` | bool | `2.frontend/alb.tf` | `alb_frontend` |
| `alb_frontend_idle_timeout` | `60` | number | same | same |
| `alb_frontend_health_check_path` | `"/health"` | string | same | same |
| `alb_frontend_healthy_threshold` | `3` | number | same | same |
| `alb_frontend_unhealthy_threshold` | `3` | number | same | same |
| `alb_frontend_health_check_interval` | `30` | number | same | same |

---

## Frontend CDN tier — variant `static-spa` only

| Variable | Default | Type | File | Block | Attribute path |
|---|---|---|---|---|---|
| `cloudfront_price_class` | `"PriceClass_200"` | string | `2.frontend/cloudfront.tf` | `cloudfront` | `price_class` |
| `cloudfront_default_ttl` | `86400` | number | same | same | `default_cache_behavior.default_ttl` |
| `cloudfront_min_ttl` | `0` | number | same | same | `default_cache_behavior.min_ttl` |
| `cloudfront_max_ttl` | `31536000` | number | same | same | `default_cache_behavior.max_ttl` |

CloudFront attribute paths depend on the exact shape the generator emits. A missing path is logged
and skipped.

---

## Constants that are never extracted

These stay inline. Turning one into a variable is a mistake, not an improvement.

- `name`, `type`, and role identifiers
- Protocol strings: `"tcp"`, `"HTTP"`, `"HTTPS"`, `"-1"`
- **`"0.0.0.0/0"`** — a security boundary, not an environment tunable. Making it configurable is how a
  wide-open ingress rule reaches production through a tfvars edit nobody reviews.
- Security-group port literals (`80`, `443`, `5432`, `6379`) — protocol constants
- HTTP status matchers (`"200"`)
- `target_type = "ip"`, `container_name`
- TODO placeholders
- Composed strings that already interpolate `${var.project}` / `${var.env}`
