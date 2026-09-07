# Layer `7.monitoring` — passive

Generated **only when `monitoring = true`**, and always **last**.

When `alerting = false` — the default — this layer is exactly what this file describes and nothing
more. The alerting pipeline is additive and lives in
[`7-monitoring-alerting.md`](./7-monitoring-alerting.md).

> **This layer is passive.** No IAM role, no secrets, no SOPS provider block. Two module calls:
> `cloudwatch-alarm:alarms` and `cloudwatch-dashboard:dashboard`.

**HYBRID log placement.** Log groups stay with the compute that produces them — the ECS log group in
`1.general`'s `ecs-cluster`, the optional VPC flow-log group in `vpc`. This layer adds **only**
`aws_cloudwatch_metric_alarm` and `aws_cloudwatch_dashboard`.

---

## The alarm table

Transcribed from the Sun\* CloudWatch alarm standard. **`Period = 60` on every row.** The standard's
"N out of M" maps to `datapoints_to_alarm = N`, `evaluation_periods = M`.

| Resource | Metric | Statistic / comparison / threshold | N / M |
|---|---|---|---|
| ECS Service | MemoryUtilization | Average > 80 | 2 / 2 |
| ECS Service | CPUUtilization | Average > 70 | 2 / 2 |
| ALB | HTTPCode_ELB_4XX_Count | Sum > 1000 | 2 / 2 |
| ALB | HTTPCode_ELB_5XX_Count | Sum > 0 | 1 / 1 |
| ALB | HTTPCode_Target_5XX_Count | Sum > 0 | 1 / 1 |
| ALB | TargetResponseTime | Average > 5 (seconds) | 2 / 2 |
| ALB | RequestCount | Sum > 2000 | 1 / 1 |
| ALB | UnHealthyHostCount | Maximum > 0 | 1 / 1 |
| Redis | EngineCPUUtilization | Average > 70 | 2 / 2 |
| Redis | CPUUtilization | Average > 70 | 2 / 2 |
| Redis | DatabaseMemoryUsagePercentage | Average > 70 | 1 / 1 |
| Redis | CurrConnections | Maximum > 1000 | 1 / 1 |
| Redis | Evictions | Sum > 2 | 1 / 1 |
| Redis | ReplicationLag | Maximum > 1000 (ms) | 2 / 2 |
| RDS | CPUUtilization | Average > 70 | 2 / 2 |
| RDS | FreeableMemory | Average < 20% **(→TODO)** | 2 / 2 |
| RDS | DatabaseConnections | Maximum > 60% of max **(→TODO)** | 1 / 1 |
| RDS | ReadIOPS | Average > 60% of max **(→TODO)** | 2 / 2 |
| RDS | WriteIOPS | Average > 60% of max **(→TODO)** | 2 / 2 |
| RDS | DiskQueueDepth | Average > 2 | 2 / 2 |
| RDS | FreeStorageSpace | Average < 20% **(→TODO)** | 1 / 1 |
| RDS | ReplicaLag | Average > 1000 (ms) | 2 / 2 |
| Aurora *(conditional)* | CPUUtilization | Average > 70 | 2 / 2 |
| Aurora *(conditional)* | FreeableMemory | Average < 20% **(→TODO)** | 2 / 2 |
| Aurora *(conditional)* | DatabaseConnections | Maximum > 60% of max **(→TODO)** | 1 / 1 |
| Aurora *(conditional)* | ReadIOPS | Average > 1000 | 2 / 2 |
| Aurora *(conditional)* | WriteIOPS | Average > 1000 | 2 / 2 |
| Aurora *(conditional)* | DiskQueueDepth | Average > 2 | 2 / 2 |
| Aurora *(conditional)* | AuroraReplicaLag | Average > 1000 (ms) | 2 / 2 |

The RDS rows and the Aurora rows are **alternatives**, selected by `db_engine` — the same choice that
decides which data-tier module the `4.database` layer emits.

### `(→TODO)` means emit a placeholder, never a number

A row marked `(→TODO)` has a **dynamic** threshold — it depends on the instance class, which the
blueprint does not know. Emit:

```hcl
# TODO: set threshold = <N>% of <instance-class> max (Sun* standard)
```

**Never an ad-hoc literal.** A guessed threshold produces an alarm that either never fires or fires
constantly, and both look like the alarm is working.

---

## `cloudwatch-alarm` — aggregate module, block `alarms`

One `aws_cloudwatch_metric_alarm` per standard row, for every compute and data resource actually
present: each ECS service, the ALB, RDS or Aurora, and Redis or Valkey.

**This is an aggregate module.** Its inputs are the environment's **dimension** values, and it renders
every alarm internally via `for_each` over an internal `locals` map. Do **not** impose the default
single-resource scalar contract — `alarm_name`, `metric_name`, `namespace`, `threshold`,
`dimensions`, `comparison_operator`, `statistic`, `period`, `evaluation_periods` are module-internal
locals here, never module inputs.

`tkm:iac-generate-module` owns the aggregate-module exception and ships the module's full input
surface — dimensions, nullable thresholds, and the two action lists. Invoke it to scaffold the
module; do not restate its variable contract here, and do not design one.

The module exposes `alarm_actions` and `ok_actions`, both `list(string)` default `[]`. **That is the
only hook the alerting pipeline uses.** With `alerting = false` both stay empty and the alarms are
purely observational.

---

## `cloudwatch-dashboard` — block `dashboard`

**One** `aws_cloudwatch_dashboard` per environment, aggregating every compute widget.

Also an aggregate module, taking the **same** dimension inputs as the alarm module. It has **no
threshold variables at all** — it reads dimensions to build widgets and nothing else.

---

## Dimension inputs are read cross-layer

All **downstream**, so the graph stays acyclic — no compute layer ever reads this one.

| Source layer | Dimension |
|---|---|
| `1.general` | ECS `ClusterName` |
| `3.backend` | ECS `ServiceName`, ALB `LoadBalancer` and `TargetGroup` arn_suffix |
| `4.database` | RDS `DBInstanceIdentifier` **or** Aurora `DBClusterIdentifier`; Redis `CacheClusterId` |
| `2.frontend` (`ssr` only) | frontend ECS `ServiceName`, `alb_frontend` arn_suffix |

Every one of these exists only because Phase B's `monitoring`-gated re-export appended it to that
layer's `_outputs.tf`. With `monitoring = false` none fire, and every compute `_outputs.tf` is
byte-for-byte unchanged.

The **module-level** dimension outputs (`alb_arn_suffix`, `target_group_arn_suffixes`) exist on the
compute modules regardless of the toggle; only the **layer-level re-export** is gated. That
separation is what keeps the toggle byte-for-byte clean.

---

## Standards

Alarm thresholds and companion-resource conventions come from the monitoring standards in
`_shared/extras/iac/inferred-resources/`. Those files carry thresholds only — the inference logic
that decides which companions a component gets is not part of this kit yet, and this layer's content
is the table above rather than a derivation.
