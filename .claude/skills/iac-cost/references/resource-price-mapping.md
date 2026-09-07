# Resource → Price Mapping

How a Terraform resource becomes a monthly USD figure.

Three of this skill's four net-new capabilities live here: **SKU/usagetype precision**,
**Public-IPv4 charging**, and **Reserved-1yr**. The fourth — layer aggregation — is in
[`report-formats.md`](./report-formats.md).

## Step 1 — Extract the spec

For each resource or module call in a layer, resolve its cost-driving attributes to **concrete
values** by following `var.*` → `terraform.{env}.tfvars` → module defaults.

Capture **quantity** as well, not just type: `count`, `desired_count`, `num_cache_nodes`,
`multi_az`, ASG `desired_size`, replica count. A correctly-priced instance type at the wrong count is
still a wrong bill.

## Step 2 — Map to a price dimension

| Terraform resource | Spec attributes | AWS service code | Monthly cost basis |
|---|---|---|---|
| `aws_instance`, EC2 in launch template / ASG | `instance_type`, count / `desired_size` | `AmazonEC2` | on-demand hourly × 730 × count (+ EBS below) |
| `aws_db_instance` / `aws_rds_cluster(_instance)` | `instance_class`, `engine`, `multi_az`, `allocated_storage` | `AmazonRDS` | instance hourly × 730 × (`multi_az` ? 2 : 1) + storage GB-month |
| `aws_lb` (ALB / NLB) | `load_balancer_type` | `AWSELB` — filter `productFamily`: `Load Balancer-Application` for ALB, `Load Balancer-Network` for NLB. **There is no `AWSELBv2` service code.** | hourly × 730 + LCU estimate (mark approximate) |
| ECS Fargate (`aws_ecs_service` + task def) | task `cpu`, `memory`, `desired_count` | `AmazonECS` (Fargate) | vCPU-hr + GB-hr × 730 × `desired_count` |
| `aws_s3_bucket` | storage estimate (input or assumed GB) | `AmazonS3` | GB-month (+ request tiers; note assumptions) |
| `aws_cloudfront_distribution` | data-transfer estimate | `AmazonCloudFront` | per-GB egress + per-10k requests (note assumptions) |
| `aws_nat_gateway` | count (per AZ) | `AmazonVPC` | hourly × 730 × count + per-GB processed (note) |
| `aws_elasticache_replication_group` / `_cluster` | `node_type`, `num_cache_nodes` / replicas | `AmazonElastiCache` | node hourly × 730 × node count |
| `aws_lambda_function` | `memory_size`, est. invocations + avg duration | `AWSLambda` | GB-seconds + per-request (note invocation assumption) |
| `aws_ebs_volume` / root & data block devices | `size`, `type` (gp3 / io2) | `AmazonEC2` (EBS) | GB-month (+ provisioned IOPS / throughput when set) |
| **Public IPv4 address** — internet-facing `aws_lb`, `aws_nat_gateway`, `aws_eip`, instance with `associate_public_ip_address = true` | count of attached public IPv4 (rules below) | `AmazonVPC`, usagetype `<regionPrefix>-PublicIPv4:InUseAddress` | $0.005/hr × 730 × IP count ≈ **$3.65/IP/month** |

**Region.** Read `region` from `terraform.{env}.tfvars`; fall back to `DEFAULT_REGION`. Always query
the environment's own region — prices vary by region. Never hardcode a region literal here; resolve
it through [`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

**Usage-based services** (S3, CloudFront, Lambda, NAT data processing) depend on traffic, which
Terraform does not declare. State the **assumption** beside the figure — "S3: 100 GB-month assumed;
adjust" — so the number is honest rather than falsely precise.

## Public IPv4 — the charge everyone forgets

Billable since **2024-02-01**. AWS charges **$0.005/hr (~$3.65/month)** for *every* attached public
IPv4 address, **in use or idle**. Terraform does not declare the IP count, so it must be **inferred**
and added to the layer owning the resource:

| Resource | IP count |
|---|---|
| `aws_nat_gateway` | **1 each** — one Elastic IP per NAT |
| internet-facing `aws_lb` (`internal = false`) | **1 per AZ subnet** listed in `subnets` / `subnet_mapping` — a 2-AZ ALB is 2 IPs |
| `aws_eip`, instances with `associate_public_ip_address = true` | **1 each** |

Omitting this silently **understates** internet-facing environments. On the upstream reference dev
environment the missing line was **$11–15/month** — enough on its own to break the ±15% target.

Verified `ap-northeast-1` rate: `APN1-PublicIPv4:InUseAddress` = `APN1-PublicIPv4:IdleAddress` =
$0.005/hr. Query `AmazonVPC` with `usagetype CONTAINS PublicIPv4` in the environment's region.

## Step 2.1 — usagetype precision

One resource type returns **multiple pricing rows**, keyed by `usagetype`. Picking the wrong row
silently **over-states** the figure — most often by selecting an **Extended Support** row instead of
the standard On-Demand one.

When more than one row matches, select the standard on-demand usagetype and **exclude** non-standard
SKUs:

- Exclude any `usagetype` containing `ExtendedSupport` / `ExtendedSupportYr`.
- Exclude `Reserved`-term rows when pricing the **On-Demand baseline** — RI is priced separately in
  Step 4.
- Exclude `DedicatedUsage` / `HostUsage`, `Unused*`, `SpotUsage`, `*-Mirror*`, `*-DataXfer*`, and
  marketplace rows.

**Prefer the canonical pattern** for the region prefix `<regionPrefix>` (`APN1` for
`ap-northeast-1`):

| Service | Canonical usagetype |
|---|---|
| ElastiCache | `<regionPrefix>-NodeUsage:<type>` |
| RDS | `<regionPrefix>-InstanceUsage:<type>` |
| EC2 | `<regionPrefix>-BoxUsage:<type>` |

**Source-agnostic.** For the **MCP**, express the exclusion as a Price List filter:

```
{ Field: 'usagetype', Value: ['ExtendedSupport'], Type: 'NONE_OF' }
```

For the **bulk Price List** fallback there is no filter API — post-filter the same substrings
yourself. Same intent, same rule, regardless of source.

### Regression check

These two are pinned upstream by a fixture. A run that selects an ExtendedSupport usagetype is a
**failure**, not a rounding difference — it over-states by roughly 60%.

In `ap-northeast-1`:

| Resource | Must select | Must exclude |
|---|---|---|
| `aws_elasticache_replication_group` `cache.t4g.micro` Redis, 1 node | `APN1-NodeUsage:cache.t4g.micro` (~$0.025/hr → ~$18.25/mo) | `APN1-ExtendedSupportYr3-NodeUsage:cache.t4g.micro` (~$0.04/hr) |
| `aws_db_instance` `db.t4g.micro` | `APN1-InstanceUsage:db.t4g.micro` | `APN1-ExtendedSupport-InstanceUsage:db.t4g.micro` |

## Step 3 — Aggregate

`resource cost → layer cost (sum) → environment total per month`.

Keep the per-resource lines. The aggregate is only auditable if the rows that produced it are
visible — and layer aggregation is the capability this skill exists for.

## Step 4 — On-Demand vs Reserved (1 year)

For **steady-state compute** — EC2, RDS instances, ElastiCache nodes — also fetch the **Reserved
1-year** rate and show the monthly delta and % saving.

Reserved rates live under a separate term dimension. Filter for:

```
termType            = Reserved
LeaseContractLength = 1yr
PurchaseOption      = No Upfront
OfferingClass       = standard        (EC2; RDS/ElastiCache use the equivalent 1yr no-upfront term)
```

Recommend a switch when the saving is material — roughly **≥ 20%** on a non-trivial line. **Skip RI
entirely for spiky or short-lived workloads**; a reservation on a workload that disappears is a
guaranteed loss, not a saving.

## Step 5 — Cross-environment comparison

When sibling environments exist (`dev`, `stg`, `prod`), compare per-layer totals and **flag unusual
deltas** — a non-production environment costing within 10% of production usually means an
un-downsized instance class or `multi_az` left on. Reuses the same per-resource data; no extra
queries.

## Accuracy target

Within **±15%** of the AWS Pricing Calculator for the same spec. The band absorbs the usage-based
assumptions, which is exactly why those assumptions must be pinned explicitly — a reviewer has to be
able to re-check them.

Always print the pricing source used. Never invent a timestamp; use the date the caller supplied.
