# SRE Reviewer Checklist

**25 rules** — 10 HIGH · 7 MEDIUM · 8 LOW. Each carries its checklist number.

The Terraform-IaC subset of the Sun\* AWS Security Checklists: only items that map to a Terraform
resource argument or block pattern detectable by reading `.tf` files.

Emit every finding as `[SEVERITY][SRE] description → fix (ref: checklist No.X)`. The line shape and
parse rules are owned by
[`finding-format.md`](../../_shared/extras/iac/finding-format.md) — read it, do not restate it.

**Targets**
- `{ENV_DIR}/{layer}/`
- **Does not apply** to `{MODULE_DIR}/{service}/` — out of scope for this reviewer.

## Scope

Items that are operational, identity management (MFA, password policy, IAM user/group/access-key
policies), account-level governance toggles (Security Hub / Config / GuardDuty / Inspector
enablement, Trusted Advisor, billing and budget alarms, account-level CloudTrail enablement), or
OS/application-level controls are **not** part of this reviewer. They belong to a separate
organization/account-level review process.

**Excluded items:** 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 23, 27, 29, 30, 31, 32, 34,
37, 40, 41, 42, 43, 45, 47, 52, 55, 57.

> That list holds **32** numbers, and 25 + 32 = 57, not 56. The upstream text says "31" above the
> same 32 numbers. Mirrored as-is rather than silently renumbered: the arithmetic cannot be
> reconciled without the source spreadsheet, and guessing which item to drop would be worse than
> recording the discrepancy. The 25 **included** rules below are unaffected.

> The 25 included items are a subset of a 56-item checklist held outside this repository. Nothing in
> this kit can verify the subset is still current against that source. Treat a numbering mismatch as
> a signal to re-derive the subset, not to renumber these rules.

## Severity mapping

| Checklist level | Severity |
|---|---|
| Very high | HIGH |
| High | HIGH |
| Medium | MEDIUM |
| Low | LOW |

## Overlap with the security reviewer

Items **No.24, 28, 33, 38, 56** overlap with `reviewer-security.md`. This reviewer emits the same
finding independently under `[SRE]`; the orchestrator deduplicates by `(resource_address, issue
topic)` and `[SECURITY]` wins.

**No.44 is not a dedup pair.** Both reviewers flag it, at *different* severities — SRE **HIGH** per
the Sun\* checklist, security **MEDIUM** — with different fix emphasis, so both surface. Because SRE
rates it HIGH, a missing public-edge WAF **enters the HIGH fix loop**. That is deliberate: the
checklist treats public-edge WAF as a release gate. To make WAF advisory-only, downgrade No.44 here
to MEDIUM — and nowhere else.

---

## HIGH — blocks deployment (10)

- **No.24** `aws_s3_bucket` without a paired `aws_s3_bucket_policy` containing a Deny statement for `aws:SecureTransport = false` → Add a bucket policy denying non-TLS access (ref: checklist No.24)
- **No.28** `aws_lb_listener` on port 80 without a `default_action { type = "redirect" … port = "443" protocol = "HTTPS" }` → Add the HTTP→HTTPS redirect default_action, or remove the port 80 listener (ref: checklist No.28)
- **No.33** `aws_security_group` with `cidr_blocks = ["0.0.0.0/0"]` (or any IPv4 wildcard) on any port other than 80/443 → Restrict ingress to known CIDRs or to a source security group reference (ref: checklist No.33)
- **No.35** `aws_key_pair` with `public_key` provided as an inline literal string, instead of `file()`, a variable, or a `tls_private_key` reference → Source key material from a variable or `tls_private_key.public_key_openssh`; never inline (ref: checklist No.35)
- **No.36** `aws_instance` in a public subnet (its route table has a route to an `aws_internet_gateway`) with an attached `aws_security_group` allowing ingress on port 22 or 3389 from a non-RFC1918 CIDR → Route admin access through a bastion host or SSM Session Manager (ref: checklist No.36)
- **No.38** `aws_instance`, `aws_db_instance`, `aws_elasticache_cluster`, `aws_elasticache_replication_group`, `aws_rds_cluster`, `aws_opensearch_domain`, or `aws_lb` without a `vpc_security_group_ids` / `security_group_ids` / `security_groups` argument → Always attach at least one security group; never rely on the default SG (ref: checklist No.38)
- **No.39** `aws_vpc` declared with `aws_subnet` resources but no `aws_network_acl` associated to those subnets → Add NACLs as a second layer of defense beyond security groups (ref: checklist No.39)
- **No.44** Public-facing `aws_lb` (`load_balancer_type = "application"`, `internal = false`) or `aws_cloudfront_distribution` without an `aws_wafv2_web_acl_association` → Associate a WAFv2 Web ACL with the public ALB/CloudFront (ref: checklist No.44)
- **No.49** `aws_wafv2_web_acl` present but no `aws_wafv2_web_acl_logging_configuration` referencing it → Enable WAF logging to Kinesis Firehose or CloudWatch (ref: checklist No.49)
- **No.56** Any resource argument containing a literal password or secret string (`master_password = "…"`, `password = "…"`, hardcoded `secret_string = "…"`) → Reference via **SOPS first** — `data.sops_file.secret.data["<PROJECT>_<KEY>"]`, the repo's primary secrets path; for AWS-managed runtime secrets, store in SSM Parameter Store or Secrets Manager seeded from SOPS and read via `data.aws_ssm_parameter.*.value` / `data.aws_secretsmanager_secret_version.*.secret_string`. Never inline (ref: checklist No.56)

---

## MEDIUM — fix before production (7)

- **No.8** `aws_instance` without an `iam_instance_profile` argument, or `aws_lambda_function` without a `role` argument → Attach an IAM role; do not embed long-lived credentials in user_data or environment variables (ref: checklist No.8)
- **No.25** `aws_s3_bucket` without an accompanying `aws_s3_bucket_versioning` resource with `status = "Enabled"` → Add the versioning resource (ref: checklist No.25)
- **No.46** `aws_cloudtrail` present in the layer with `is_multi_region_trail = false` (or attribute absent) → Set `is_multi_region_trail = true` (ref: checklist No.46)
- **No.48** `aws_route53_zone` declared without a corresponding `aws_route53_query_log` resource referencing it → Enable Route 53 query logging to CloudWatch (ref: checklist No.48)
- **No.51** `aws_s3_bucket` without an `aws_s3_bucket_logging` resource configured → Enable S3 server-access logging to a dedicated log bucket (ref: checklist No.51)
- **No.53** `aws_lb` without an `access_logs` block, or with `access_logs.enabled = false` → Enable ELB access logs to S3 (ref: checklist No.53)
- **No.54** `aws_vpc` declared without an `aws_flow_log` resource targeting it → Enable VPC Flow Logs to CloudWatch or S3 (ref: checklist No.54)

---

## LOW — good hygiene (8)

- **No.17** `aws_kms_key` without `enable_key_rotation = true` → Enable annual key rotation (ref: checklist No.17)
- **No.18** `aws_s3_bucket` without `aws_s3_bucket_server_side_encryption_configuration` using a customer-managed key → Add SSE-KMS configuration using a CMK (ref: checklist No.18). **Caveat:** the AWS-managed `aws/s3` key is the accepted kit baseline; a CMK is opt-in via `kms_key_arn` for regulated or sensitive data. For kit-default buckets this is an optional hygiene nudge, not a gap
- **No.19** `aws_ebs_volume`, or any `root_block_device` / `ebs_block_device` block, without `encrypted = true` and `kms_key_id` → Set `encrypted = true` and reference a CMK (ref: checklist No.19)
- **No.20** `aws_db_instance` or `aws_rds_cluster` with `storage_encrypted = true` but no `kms_key_id` (using the AWS-managed key) → Reference a customer-managed CMK via `kms_key_id` (ref: checklist No.20)
- **No.21** `aws_elasticache_replication_group` (Redis) without `at_rest_encryption_enabled = true` and `kms_key_id` → Enable at-rest encryption with a CMK (ref: checklist No.21)
- **No.22** `aws_opensearch_domain` without `encrypt_at_rest.enabled = true` and `encrypt_at_rest.kms_key_id` → Enable at-rest encryption with a CMK (ref: checklist No.22)
- **No.26** `aws_s3_bucket` tagged `Environment = "prod"` (or in a prod environment) without `aws_s3_bucket_replication_configuration` → Consider Cross-Region Replication for DR (ref: checklist No.26)
- **No.50** `aws_cloudfront_distribution` without a `logging_config` block → Enable CloudFront access logs to S3 (ref: checklist No.50)
- **HIGH** `aws_cloudfront_distribution` whose origin is a load balancer with `internal = true`, using a plain `custom_origin_config` and no VPC origin → the ALB's DNS resolves to private addresses that CloudFront cannot route to, so every request through that origin fails while `plan` and `apply` both succeed → Use a CloudFront VPC origin, or make the ALB public and restrict its security group to the CloudFront managed prefix list; either way it is an architecture decision, not an automated fix (ref: kit contract)

---

## False-positive guards

These exist because each one, once, produced a wall of findings against correct code.

1. **TODO placeholders** left by module generation (`# TODO: connect from <service> — run the wiring step`) — skip those lines. Do **not** emit findings against unresolved placeholders; the wiring step resolves them before review runs.
2. **Cross-layer references via `terraform_remote_state`** — when a resource is consumed from another layer (`data.terraform_remote_state.general.outputs.vpc_id`), do **not** emit a "missing X" finding if X is reasonably owned by that other layer. VPC, flow logs and NACLs live in the general layer; the consuming layer is not at fault.
3. **VPC-related rules (No.39, No.54)** — apply **only** when the layer actually declares `aws_vpc` directly. Skip when the VPC is referenced through `data.terraform_remote_state`.
4. **Module-call arguments** — an argument inside a `module "X" { … }` block is data passed *to* the module, not a resource definition. Do not flag a missing security group on a module input; the module owns that.

---

## Output

Findings lines only. No prose, no headers. No findings across HIGH/MEDIUM/LOW → the single line
`NO_FINDINGS`.
