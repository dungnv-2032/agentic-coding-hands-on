# Layer `1.general`

The upstream layer every tier reads from. **This layer has no content of its own** — everything it
emits is defined in [`cross-layer-contracts.md`](../cross-layer-contracts.md).

That is a finding, not an omission: the module set, the cert placement and the shared cluster
contract all span layers, so they live in the single-owner file. This template exists so
`layer-templates/` is a complete set and a project that overrides `LAYERS` has a pattern to copy.

## What it emits

Module calls: see the lookup table's `1.general` row. The set differs by variant — `ssr` splits its
security groups per tier (`sg_alb_fe` / `sg_alb_be` / `sg_ecs_fe` / `sg_ecs_be`), and `static-spa`
with `route53 = true` adds a **second** ACM block through the `aws.us_east_1` provider alias.

## Contracts that apply here — do not restate them

- **The ACM-cert invariant.** The Route53 zone and every ACM cert live here, in every variant, and
  the file explains the dependency cycle that forces it. Moving a cert next to its own ALB is the
  cycle.
- **`ecs-cluster`** — one cluster for the whole environment, including the `enable_log_kms` CMK,
  which is the only CMK in the kit.
- **`vpc`** — including the `enable_flow_logs` toggle and its companion resources.
- **The Route53 module split** — one module, a zone-only call here and an alias-only call in the
  tier layer.

## Gated re-exports appended here

| Output | Gate |
|---|---|
| `route53_name_servers`, `route53_zone_id`, `acm_certificate_arn` (+ `_us_east_1` for `static-spa`) | `route53 = true` |
| `ecs_cluster_name` | `monitoring` **OR** `delivery` |

The `route53_name_servers` re-export is **required** when `route53 = true` — the module's native
output is named `name_servers`, so the documented `terraform output route53_name_servers` fails
without it. See [`phase-b-execution.md`](../phase-b-execution.md) for the dedup and description rules
that govern the OR-gated output.
