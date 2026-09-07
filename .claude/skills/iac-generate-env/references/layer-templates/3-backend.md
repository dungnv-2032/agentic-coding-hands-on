# Layer `3.backend`

Present in every variant, and **the layer with the most expansion**. Its content is defined in
[`cross-layer-contracts.md`](../cross-layer-contracts.md).

**Applies before `2.frontend`.** The layer number is a folder label, not apply order.

## What it emits

Driven by the backend service loop, in this exact order:

1. Per backend service — `ecr:ecr_backend_<name>` then `ecs:ecs_backend_<name>`
2. Once — `s3-bucket:s3_app_content`
3. Per backend service — `iam-policy:iam_<name>_s3`
4. Once — `alb:alb_backend`

**The order is load-bearing.** The IAM policies embed the bucket ARN in their emitted inline document,
so `s3_app_content` must exist first; they also need each service's `task_role_name`, so the ECS
blocks must exist too.

## Contracts that apply here — do not restate them

- **The `ecs` ALB-optional contract**, including the deployment-strategy twin, the `moved` block, and
  the `one(concat(...))` output rule.
- **`alb_backend`** — one ALB with one target group per api service, plus the blue/green additions.
- **`s3_app_content`** and the generic `iam-policy` module.

Workers pass `target_group_arn = null`; the `load_balancer` block and the health-check grace period
both collapse. **The grace period must be gated** or a worker's apply fails.

## Gated re-exports appended here

| Output | Gate |
|---|---|
| `ecs_backend_<svc>_task_role_name` | `messaging` |
| `ecs_backend_<svc>_service_name` | `monitoring` **OR** `delivery` |
| `alb_backend_arn_suffix`, `alb_backend_target_group_arn_suffixes` | `monitoring` |

`alb_backend` is the **public** ALB only for variant `none`. For `static-spa` and `ssr` it is
internal, so it gets neither `enable_waf` nor `enable_access_logs`.
