# Layer `4.database`

The primary database and the cache. Both are PostgreSQL-on-5432 behind `sg_rds`, with credentials
from SOPS and a subnet group over the private subnets from `1.general`.

Module calls come from the lookup table in
[`cross-layer-contracts.md`](../cross-layer-contracts.md). Tunables are in
[`tunable-variables.md`](../tunable-variables.md).

**Exactly one database engine and one cache engine are emitted per environment.**

---

## Database — `db_engine` decides

### `aurora` path — the default

`db_engine ∈ {aurora-serverless, aurora-provisioned}` → block `aurora`, file `aurora.tf`, module
`rds-aurora`.

> ### Mirror the maintained module. Do not invent a shape.
>
> A real `rds-aurora` module is maintained upstream. The scaffolded module must reproduce its shape
> **exactly** — resource names, **object** input variables, output names. Read the maintained module
> as the source of truth; what follows is a guide, not a replacement.
>
> Inventing a "cleaner" shape here is the failure this warning exists for: the env-folder block, the
> monitoring dimension re-export, and the wiring step all address the module by these exact names.

**Resources** — reproduce all of them; dropping the optional ones was a real review finding:

- `aws_rds_cluster.aurora_cluster` and `aws_rds_cluster_instance.aurora_instance`
  (`count = var.aurora_instance.number`)
- **Both** parameter groups: `aws_rds_cluster_parameter_group.aurora_cluster_parameter_group`
  (cluster-level, referenced by the cluster's `db_cluster_parameter_group_name`) **and**
  `aws_db_parameter_group.aurora_parameter_group` (instance-level)
- `aws_db_subnet_group.aurora_subnet_group`
- The optional `aws_rds_global_cluster`, `aws_db_proxy`, `aws_db_event_subscription` and log-group
  resources — keep them, defaulted off

Resource names are `.aurora_cluster` and `.aurora_instance`, **not** `.this`.

**Object inputs**, verbatim: `var.name` (discriminator), `var.aurora_cluster`, `var.aurora_instance`,
`var.aurora_parameter_group` (`family` plus `cluster_parameters` and `parameters`, each an
`optional(list(object({ name, value, apply_method })), [])`), `var.aurora_subnet_ids`, and the
optional `var.cluster_global` / `var.aurora_proxy` / `var.aurora_event` /
`var.aurora_log_group_retention`.

**Outputs**, verbatim: `aurora_cluster_identifier`, `aurora_cluster_endpoint`,
`aurora_cluster_reader_endpoint`, `aurora_cluster_name`, `aurora_cluster_arn`, `db_proxy_endpoint`,
`global_cluster_id`.

> **Do not rename these to `db_cluster_identifier` or `cluster_endpoint`.** The monitoring layer's
> dimension re-export reads `aurora_cluster_identifier` by name.

**Serverless v2 is native in the maintained module** — not a kit extension. `var.aurora_cluster`
carries an optional `serverlessv2_scaling` field (`object({ min_capacity, max_capacity })`, default
`null`); when non-null the module renders a `dynamic` `serverlessv2_scaling_configuration` block on
the cluster, and `instance_class = "db.serverless"` selects the serverless instance.

Both variants come from the **one** module:

| `db_engine` | env call |
|---|---|
| `aurora-serverless` (default) | `serverlessv2_scaling = { min_capacity = var.aurora_min_acu, max_capacity = var.aurora_max_acu }`, `aurora_instance = { number = 1, instance_class = "db.serverless" }` |
| `aurora-provisioned` | omit `serverlessv2_scaling` (null), `aurora_instance = { number = 1, instance_class = var.aurora_instance_class }` |

`aurora_min_acu` defaults to `0` — **scale-to-zero auto-pause**.

**The env-folder block assembles the objects from the flat tunables:**

```hcl
aurora_cluster = {
  engine                  = "aurora-postgresql"
  engine_version          = var.aurora_engine_version
  database_name           = var.db_name
  master_username         = data.sops_file.secret.data["<PREFIX>_DATABASE_USER_ROOT"]
  master_password         = data.sops_file.secret.data["<PREFIX>_DATABASE_PASSWORD_ROOT"]
  security_group_ids      = []   # TODO: connect from security-group — run the wiring step
  storage_encrypted       = var.aurora_storage_encrypted
  backup_retention_period = var.aurora_backup_retention_period
  skip_final_snapshot     = var.aurora_skip_final_snapshot
  apply_immediately       = var.aurora_apply_immediately
  serverlessv2_scaling    = <per the table above>
}
```

Plus `aurora_instance`, `aurora_subnet_ids = []` (TODO), and `name = "main"`.

The wiring step resolves `aurora_subnet_ids` ← `…outputs.private_subnet_ids` and
`security_group_ids` ← `[…outputs.sg_rds_id]` — the same `sg_rds`, port 5432.

### `rds` path

`db_engine = rds` → block `rds`, file `rds.tf`, module `rds`. A plain `aws_db_instance`, class from
`var.rds_instance_class`, `rds_*` tunables. Output `db_instance_identifier` feeds the monitoring
re-export.

---

## Cache — `cache_engine` decides

**Valkey is the default.** Block `valkey`, file `valkey.tf`. When `cache_engine = redis`, emit
`redis` into `redis.tf` with the `redis_*` tunables instead.

Only one is ever emitted.

---

## Monitoring re-export

Gated on `monitoring = true`. Append to `4.database/_outputs.tf` the metric dimension for the engine
actually present:

| Path | Dimension re-exported |
|---|---|
| `rds` | `DBInstanceIdentifier` — the **instance** identifier |
| `aurora` | `DBClusterIdentifier` — the **cluster** identifier |

Plus the Redis or Valkey `CacheClusterId`.

**The identifier is chosen by engine, not by layer.** Re-exporting an instance identifier on an
Aurora environment produces an alarm that never fires — it watches a dimension that does not exist.

When `monitoring = false`, `_outputs.tf` is byte-for-byte unchanged.
