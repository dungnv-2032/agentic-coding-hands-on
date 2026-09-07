# Layer `2.frontend`

**Absent entirely for variant `none`.** Its shape is otherwise decided by the variant, and its
content is defined in [`cross-layer-contracts.md`](../cross-layer-contracts.md).

**Applies after `3.backend`**, in both variants — the frontend tier reads the backend ALB. The layer
number is a folder label, not apply order.

## What it emits

| Variant | Module calls |
|---|---|
| `static-spa` | `s3-bucket:s3_frontend`, `cloudfront:cloudfront`, plus `route53_alias_cdn` when `route53 = true` |
| `ssr` | `ecr:ecr_frontend`, `ecs:ecs_frontend`, `alb:alb_frontend`, plus `route53_alias_frontend` when `route53 = true` |

## Contracts that apply here — do not restate them

- **The frontend wiring contract for the variant in play.** Both are mandatory scaffold steps, not
  advisory comments, and both pin the exact output names the wiring step resolves —
  `distribution_hosted_zone_id`, not `hosted_zone_id`.
- **`ecs` and `alb`** — the same modules the backend uses. For `ssr`, `alb_frontend` is the **public**
  ALB, so it is the one that gets `enable_waf` and `enable_access_logs`.

## Gated re-exports appended here

| Variant | Output | Gate |
|---|---|---|
| `ssr` | `ecs_frontend_service_name` | `monitoring` **OR** (`delivery` and the frontend opted in) |
| `ssr` | `alb_frontend_arn_suffix`, target-group suffixes | `monitoring` only |
| `static-spa` | frontend bucket id + ARN, CloudFront distribution id + ARN | `delivery` |
