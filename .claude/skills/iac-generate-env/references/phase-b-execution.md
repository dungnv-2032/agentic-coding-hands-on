# Phase B — Layer generation

The layer-agnostic control flow. **What** each layer contains is in
[`cross-layer-contracts.md`](./cross-layer-contracts.md) and the layer templates; this file is
**when and in what order**.

Path keys resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

---

## Force-scaffold rule

Every module call in this phase takes the **scaffold-local-module** path.

Result of each call:

1. A local module scaffolded at `{MODULE_DIR}/{service}/` with `_versions.tf`, `_variables.tf`,
   `main.tf`, `_outputs.tf`, `README.md`.
2. An env-folder `<service>.tf` calling it by relative path:

```hcl
module "<block-name>" {
  source  = "{MODULE_DEPTH}"
  project = var.project
  env     = var.env
  region  = var.region
  # remaining inputs — TODO placeholders, wired later
}
```

**Never emit a git-tag, SSH, or HTTPS module source.** Released-tag sourcing was removed from the
spec; this is a belt-and-braces guard against a historical reference creeping back in.

Environments composed here must be self-contained and per-environment editable. A released module is
versioned upstream and can change underneath an environment without warning; a local scaffold
removes that risk and keeps every tunable inside the environment tree.

**Duplicate-scaffold safety:** if `{MODULE_DIR}/{service}/` already exists — from a previous run, or
because a service appears in several layers, as `security-group` does — do **not** re-scaffold. Emit
only the new env-folder block. Several blocks may share one local module.

---

## Layer order

Sequential, in dependency order. Each layer may depend on outputs from the previous.

| Variant | Order |
|---|---|
| `none` | `1.general` → `3.backend` → `4.database` |
| `static-spa` | `1.general` → `3.backend` → **`2.frontend`** → `4.database` |
| `ssr` | `1.general` → `3.backend` → **`2.frontend`** → `4.database` |

> **Backend before frontend.** The frontend tier reads the backend ALB — CloudFront origin for
> `static-spa`, `ecs_frontend` egress SG for `ssr` — so `3.backend` must apply first. Both read the
> zone and cert from `1.general`, which applies before either.
>
> **Layer numbers are folder labels, not apply order.** `2.frontend` sorts before `3.backend`
> alphabetically and applies after it. Generating in numeric order produces an unresolvable
> cross-layer reference that only surfaces at `terraform validate` — assert the order from this
> table, never from the folder names.

### Optional layers append in a fixed sequence

| Layer | Condition | Position |
|---|---|---|
| `5.messaging` | `messaging = true` | after the variant's last layer |
| `6.delivery` | `delivery = true` | after `5.messaging`, **before** `7.monitoring` |
| `7.monitoring` | `monitoring = true` | **LAST**, always |

Full order when everything is on:
`1.general` → `3.backend` → `2.frontend` → `4.database` → `5.messaging` → `6.delivery` →
`7.monitoring`.

Every optional layer reads **downstream only** — no upstream layer ever reads them — so the graph
stays acyclic. When a toggle is off, the layer set is exactly the base table and the gated
re-exports below **do not fire**, leaving upstream `_outputs.tf` byte-for-byte unchanged.

---

## The loop

```pseudo
for layer in VARIANT_LAYERS[variant]:          # dependency order, from the table above
  for call in LOOKUP_TABLE[variant][layer]:    # cross-layer-contracts.md § lookup table
    generate module <call.service> into <layer>, block name <call.block>

  if layer == 3.backend:
    for svc in backend_services:
      generate ecr  → block ecr_backend_<svc.name>
      generate ecs  → block ecs_backend_<svc.name>
    generate s3-bucket → block s3_app_content        # once, before alb
    for svc in backend_services:
      generate iam-policy → block iam_<svc.name>_s3  # after s3_app_content and all ecs blocks
    generate alb → block alb_backend                 # last
```

**Every generation line is a synchronous unit of work performed in this turn.** Do not dispatch any
of them as a child agent and wait — see the single-turn rule in `SKILL.md`.

Order inside `3.backend` is load-bearing: `s3_app_content` must exist before the IAM policies, whose
emitted inline document references its bucket ARN, and the ECS blocks must exist before them too,
for each `task_role_name`.

### Delivery-gated call argument

When `delivery = true` **and** `delivery_strategies[<svc.name>] = BLUE_GREEN`, the `ecs` call also
passes `deployment_strategy = "BLUE_GREEN"`.

ROLLING services pass **nothing** — the module variable already defaults to `"ROLLING"`, so the call
stays byte-for-byte unchanged. Passing it explicitly for ROLLING would perturb every existing
environment's diff for no behavioural change.

---

## Gated cross-layer re-exports

This is the densest part of Phase B and the easiest to get subtly wrong.

A layer-level `output` is appended to a **source** layer's `_outputs.tf` so a **later** layer can read
it through remote state.

**This table is the *gated* additions only. It is not the full export list.** The baseline still
applies underneath it: every module block exports what other layers consume, gate or no gate — one
output per block, each with a `description`. `1.general` therefore always exports its VPC id, its
subnet ids, every security-group id and the ECS cluster id and log-group name, because `3.backend`
consumes all of them unconditionally.

Reading this table as exhaustive is a real failure mode with no error message: with `monitoring` and
`delivery` both false, an agent that exports only what appears here leaves `1.general` exporting
nothing the backend needs, and **the environment cannot be wired at all** — every backend TODO
resolves to a candidate that was never exported.

Each row below is gated; when the gate is false, that row's output is not appended.

| Source layer | Output | Gate |
|---|---|---|
| `1.general` | `route53_name_servers`, `route53_zone_id`, `acm_certificate_arn` (+ `_us_east_1` for `static-spa`) | `route53 = true` |
| `1.general` | `ecs_cluster_name` | `monitoring` **OR** `delivery` |
| `3.backend` | `ecs_backend_<svc>_task_role_name` | `messaging` |
| `3.backend` | `ecs_backend_<svc>_service_name` | `monitoring` **OR** `delivery` |
| `3.backend` | `alb_backend_arn_suffix`, `alb_backend_target_group_arn_suffixes` | `monitoring` |
| `4.database` | data-tier identifier — `DBInstanceIdentifier` on the plain RDS path, `DBClusterIdentifier` on the Aurora path — plus Redis `CacheClusterId` | `monitoring` |
| `2.frontend` (`ssr`) | `ecs_frontend_service_name` | `monitoring` **OR** (`delivery` **and** the frontend opted in) |
| `2.frontend` (`ssr`) | `alb_frontend_arn_suffix`, target-group suffixes | `monitoring` only |
| `2.frontend` (`static-spa`) | frontend bucket id + ARN, CloudFront distribution id + ARN | `delivery` |
| `3.backend` (`static-spa`) | `alb_backend_dns_name` — the CloudFront ALB origin | **ungated** for `static-spa`: the origin edge exists whether or not monitoring and delivery do |

**The data-tier identifier is conditional on the engine**, not on the layer: the plain RDS path
re-exports the *instance* identifier, the Aurora path the *cluster* identifier. Emitting the wrong
one produces an alarm that never fires.

### Two rules that keep OR-gated outputs byte-for-byte stable

**DEDUP — emit each output name at most once per `_outputs.tf`.** When `monitoring` and `delivery`
are both true, an OR-gated output must still appear exactly **once**. Two `output` blocks with the
same name is a hard Terraform error.

**DESCRIPTION — the text is conditional on which gate fired.** This exists so a monitoring-only
environment stays byte-identical to what it produced before delivery existed:

| Fired | Description |
|---|---|
| monitoring only | `… dimension re-exported for cross-layer monitoring alarms` |
| delivery only | `… re-exported for cross-layer delivery pipelines` |
| both | `… re-exported for cross-layer monitoring alarms and delivery pipelines` |

Picking one fixed wording instead would silently rewrite every existing environment's `_outputs.tf`
the first time it regenerates — a diff with no behaviour change, which is the worst kind to review.

---

## Two consistency guarantees that are structural, not coordinated

**SOPS prefix.** Each inline generation step re-resolves `<PROJECT_PREFIX>` from the **same**
`terraform.{env}.tfvars` Phase A wrote. Because Phase A finalizes tfvars **before** A.5 and Phase B
run, both observe an identical snapshot and produce an identical prefix. No protocol is needed — the
consistency comes from the ordering.

If a user edits tfvars mid-run and the prefixes diverge, the wiring step and the security reviewer's
HIGH rules surface it. Fail-closed.

**Backend literals.** By the same mechanism, each step resolves `<project>` and `<env>` in the
`backend "s3"` block's `profile` and `bucket` from that tfvars, emitting **static literals**. This is
legal precisely because the agent writes them at build time — Terraform never sees a variable in a
backend block. `<account-id>` stays a placeholder; a backend block cannot interpolate
`data.aws_caller_identity.current`.

> ### Never emit `dynamodb_table` in the backend block
>
> Locking is S3-native through `use_lockfile = true`, and the bootstrap script creates no lock
> table. DynamoDB-locked S3 backends are **everywhere in training data**, so the pull to "add it
> back" is real — and it points at a table that does not exist, tripping both the inline gate and
> the bestpractice reviewer. Phase C.1 carries a self-check that strips any that slips through.

---

## Answering generation prompts

When the module-generation step asks something, answer from known blueprint values:

- **Environment** — already known.
- **Module block name** — the exact name from the lookup table.
- **Repeated services** — `security-group` several times, several `ecs` calls per backend service,
  `alb` twice in `ssr`: each call appends a separate block to the **same** `.tf` file. All backend
  ECS services, `api` and `worker` alike, share the one ALB-optional `ecs` module and produce blocks
  in `3.backend/ecs.tf`, one per service; workers differ only by `target_group_arn = null`.
- **Anything unknown** — leave a TODO placeholder. Do not block on it.

---

## B.2 — Tunable extraction

Runs after the layer loop. See [`tunable-variables.md`](./tunable-variables.md), which owns both the
appendix and this post-process.

---

## B.3 — Symlink

After B.2:

```bash
make symlink_all e=<env>          # from {MAKE_ROOT}
```

This symlinks the environment-level `_variables.tf` into every layer folder.

**Required before the wiring step runs.** The inline validation gate checks that `_variables.tf` is a
symlink as a prerequisite for `terraform validate`; without this step every layer fails that check
and the gate skips its first check entirely.

If `{MAKE_ROOT}` has no Makefile, create the symlinks directly and say so, rather than printing a
target that will not run.
