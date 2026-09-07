# Cost Reviewer Checklist (qualitative)

**14 rules** — 4 HIGH · 6 MEDIUM · 4 LOW.

**This reviewer emits no dollar figures.** It flags cost *smells* — patterns that inflate a bill —
as `[SEVERITY][COST] description → fix (ref: <source>)`. For actual monthly figures, that is
`tkm:iac-cost`, a different skill with a different job.

**`[COST]` findings never block.** They merge into the report for visibility and never enter the HIGH
fix loop, at any severity. A cost opinion that halts a deployment is a bug.

The line shape and parse rules are owned by
[`finding-format.md`](../../_shared/extras/iac/finding-format.md) — read it, do not restate it.

**Targets**
- `{ENV_DIR}/{layer}/`
- If a local module was scaffolded, also review `{MODULE_DIR}/{service}/`

## Determining the environment

Infer from the path (`envs/stg/` → staging) or from `terraform.{env}.tfvars` at environment level.
`dev`, `development`, `staging`, `stg` → apply the non-prod rules. `prod`, `production` → apply the
production rules.

Several rules below fire **only** in non-prod. Applying them to production inverts their intent —
telling a team to drop multi-AZ in prod is worse than saying nothing.

---

## HIGH — blocks or significantly inflates cost

- NAT Gateway provisioned per AZ (`count` > 1) when the environment is `dev` or `staging` → Use a single NAT Gateway for non-prod (ref: AWS-WAF COST — NAT gateway right-sizing)
- `aws_db_instance` or `aws_rds_cluster` with `instance_class` containing `r6g.2xlarge` or larger without explicit justification → Downsize to `r6g.large` for non-prod (ref: AWS-WAF COST — right-sizing)
- `multi_az = true` on RDS in a `dev` or `staging` environment → Set `multi_az = false` for non-production (ref: AWS-WAF COST — right-sizing)
- `aws_eks_node_group` with `desired_size` ≥ 5 in non-prod → Reduce `desired_size` for dev/staging (ref: AWS-WAF COST — right-sizing)

## MEDIUM — optimize before production

- EC2 instance type from the `m5` or `m6i` family for compute-heavy workloads → Suggest the `c5`/`c6i` family (ref: AWS-WAF COST — right-sizing)
- `aws_s3_bucket` without `aws_s3_bucket_lifecycle_configuration` on buckets expected to grow → Add a lifecycle rule to expire non-current versions after 30 days (ref: AWS-WAF COST — storage lifecycle)
- `aws_ecs_service` with `scheduling_strategy = "REPLICA"` and `desired_count > 2` in dev → Reduce `desired_count` to 1 or 2 (ref: AWS-WAF COST — right-sizing)
- `aws_lb` without `idle_timeout` explicitly set → Add `idle_timeout = 60`, or tune per workload (ref: AWS-WAF COST — right-sizing)
- `aws_cloudwatch_log_group` without `retention_in_days` → Set `retention_in_days = 90` to bound cost (ref: AWS-WAF COST — log retention)
- `aws_elasticache_cluster` with `num_cache_nodes > 1` in non-prod → Use `num_cache_nodes = 1` for dev/staging (ref: AWS-WAF COST — right-sizing)

## LOW — cost hygiene

- Missing cost-allocation tags (`CostCenter`, `Project`) on resources → Add the tags to all resources (ref: AWS-WAF COST — cost allocation tags)
- `aws_ebs_volume` without `lifecycle { prevent_destroy }` in prod — potential orphan cost → Add the lifecycle block or an explicit cleanup path (ref: AWS-WAF COST — orphan resources)
- `aws_cloudwatch_metric_alarm` missing on key metrics (CPU, memory, DB connections) → Add alarms to avoid surprise overages (ref: AWS-WAF COST — cost monitoring)
- `aws_s3_bucket` with the default storage class and no Intelligent-Tiering → Add a lifecycle rule or enable Intelligent-Tiering (ref: AWS-WAF COST — storage lifecycle)

---

## Deliberate overlap with the security reviewer

`aws_cloudwatch_log_group` missing `retention_in_days` appears in **both** checklists at MEDIUM —
here as spend, in `reviewer-security.md` as an operations gap. Same argument, two angles. Both are
correct; neither is a duplicate of the other.

---

## Output

Findings lines only. No prose, no headers, no dollar amounts. No findings → the single line
`NO_FINDINGS`.
