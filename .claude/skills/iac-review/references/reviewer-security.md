# Security Reviewer Checklist

**37 rules** — 22 per-folder (12 HIGH · 7 MEDIUM · 3 LOW) + 15 full-env.

Emit every finding as `[SEVERITY][SECURITY] description → fix (ref: <source>)`. The line shape and
the parse rules are owned by
[`finding-format.md`](../../_shared/extras/iac/finding-format.md) — read it, do not restate it.

Path keys (`{ENV_DIR}`, `{MODULE_DIR}`, `{DEPS_ROOT}`, `{SOPS_ALIAS_PATTERN}`) resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

**Targets**
- Invoked from generation: `{ENV_DIR}/{layer}/`
- If a local module was scaffolded, also review `{MODULE_DIR}/{service}/`

---

## HIGH — blocks deployment

- `aws_security_group` with `cidr_blocks = ["0.0.0.0/0"]` on any port except 80 and 443 → Restrict ingress to known CIDRs or source security group (ref: CIS-AWS — SG unrestricted ingress)
- `aws_db_instance` with `publicly_accessible = true` → Set `publicly_accessible = false` (ref: CIS-AWS — RDS not publicly accessible)
- `aws_s3_bucket` without accompanying `aws_s3_bucket_public_access_block` (all 4 booleans = true) → Add `aws_s3_bucket_public_access_block` resource (ref: CIS-AWS — S3 public access)
- `aws_iam_role_policy` or inline policy with `Action = "*"` or `Resource = "*"` → Scope to minimum required actions and resources (ref: CIS-AWS — IAM least-privilege)
- Hardcoded credentials, passwords, or secrets in any resource argument (literal string assigned to `password`, `master_password`, `auth_token`, `*_secret`, `*_api_key`, `*_private_key`) → Replace with `data.sops_file.secret.data["<PROJECT>_<KEY>"]` and set up `{DEPS_ROOT}/sops/secrets.{env}.yaml` (or use `aws_secretsmanager_secret` / SSM Parameter Store for AWS-managed secrets) (ref: repo secrets policy)

### The three SOPS-scoped HIGH rules

These apply **only when this environment actually uses SOPS**. Trigger: `{DEPS_ROOT}/sops/secrets.{env}.yaml`
exists **OR** any `.tf` in the target references `data.sops_file.secret.data[...]`.

For an environment with **no** SOPS usage — no yaml file **and** no `data.sops_file` reference — these
three are **skipped entirely**. There is nothing to flag, and flagging it anyway is the noise that
teaches reviewers to ignore HIGH findings.

- (SOPS-scoped) `{DEPS_ROOT}/sops/secrets.{env}.yaml` exists but lacks the `sops:` metadata block at end-of-file (= plain text, not yet encrypted) → First ensure the KMS key `{SOPS_ALIAS_PATTERN}` exists. Then encrypt with the key **ARN** — `sops --kms` rejects a bare `alias/…`: `KEY_ARN=$(aws kms describe-key --key-id {SOPS_ALIAS_PATTERN} --query KeyMetadata.Arn --output text)` then `sops --encrypt --kms "$KEY_ARN" --in-place {DEPS_ROOT}/sops/secrets.{env}.yaml`. Never commit plain-text secrets (ref: repo secrets policy)
- (SOPS-scoped) Literal `<PROJECT>` placeholder remaining in any `.tf` file (e.g. `data.sops_file.secret.data["<PROJECT>_DATABASE_PASSWORD_ROOT"]`) → Replace `<PROJECT>` with the real project prefix (UPPERCASE). Apply the same replacement in `{DEPS_ROOT}/sops/secrets.{env}.yaml` so keys match. Detection regex `<PROJECT>_[A-Z0-9_]+` — digits included, so `<PROJECT>_API_V2_KEY` matches. **Scope: SOPS key names only** — the strings inside `data.sops_file.secret.data["…"]` and the YAML key names — **never** secret values (ref: repo secrets policy)
- (SOPS-scoped) Literal `<PROJECT>` placeholder remaining in `{DEPS_ROOT}/sops/secrets.{env}.yaml` **keys** → Same fix. After replacement the file must be re-encrypted with the key ARN (ref: repo secrets policy)

### Remaining per-folder HIGH

- `aws_ecs_task_definition` without `execution_role_arn` → Add IAM execution role (ref: CIS-AWS — IAM least-privilege)
- `aws_db_instance` with `storage_encrypted = false` or attribute absent → Set `storage_encrypted = true` (ref: AWS-WAF SEC — encryption at rest)
- `aws_lb_listener` on port 443 without `ssl_policy` set → Set `ssl_policy = "ELBSecurityPolicy-TLS13-1-2-2021-06"` (ref: AWS-WAF SEC — encryption in transit)
- No HTTPS listener on ALB — only HTTP listener present → Add HTTPS listener on 443, redirect HTTP to HTTPS (ref: AWS-WAF SEC — encryption in transit)

## MEDIUM — fix before production

- No `aws_flow_log` for VPC → Add VPC flow logs to CloudWatch or S3 (ref: AWS-WAF SEC — VPC flow logs)
- `aws_security_group` rule with CIDR wider than /24 for internal traffic (e.g. /8, /16) → Narrow to source security group reference (ref: CIS-AWS — SG unrestricted ingress)
- `aws_s3_bucket` without `aws_s3_bucket_versioning` enabled → Add versioning resource (ref: AWS-WAF SEC — S3 versioning)
- `aws_cloudwatch_log_group` without `retention_in_days` → Set `retention_in_days = 90` (ref: AWS-WAF OPS — log retention)
- `aws_db_instance` without `deletion_protection = true` in production → Set `deletion_protection = true` for prod (ref: AWS-WAF REL — deletion protection)
- `aws_lambda_function` without `reserved_concurrent_executions` limit → Set a concurrency limit to prevent runaway invocations (ref: AWS-WAF REL — concurrency limit)
- Public ALB without `aws_wafv2_web_acl_association` → Associate a WAFv2 Web ACL (ref: AWS-WAF SEC — WAF on public edge)

> **This one is deliberately MEDIUM here and HIGH in the SRE checklist.** Not a mistake, not a dedup
> pair — both surface. See `reviewer-sre.md` No.44.

## LOW — good hygiene

- Resources missing `Owner` tag → Add `Owner` tag to all resources (ref: repo tagging policy)
- `aws_instance` without `disable_api_termination = true` in production → Set termination protection for prod instances (ref: AWS-WAF REL — termination protection)
- Database passwords (or any sensitive value) stored in `terraform.{env}.tfvars` as a plain literal → Move to `{DEPS_ROOT}/sops/secrets.{env}.yaml` (encrypted) and reference via `data.sops_file.secret.data[...]`, or use `aws_secretsmanager_secret` / SSM Parameter Store (ref: repo secrets policy)

---

## Full-Env Scope — cross-layer and topology audit

**When this applies.** Everything above is *per-folder*. When the review targets a **complete
environment** (`{ENV_DIR}` with all its layers), also run the 15 checks below. They reason across
**all** layers at once — network topology, end-to-end encryption, environment-wide IAM, cross-layer
wiring — which a single-folder pass cannot see. Runs in parallel with the bestpractice reviewer.

### Network topology (whole VPC, all layers) — 4

- **HIGH** — A security group reaches another tier via a wide CIDR (`/8`, `/16`, or `0.0.0.0/0`) instead of a peer security-group reference, exposing one service to more than its intended caller (e.g. `sg_rds` ingress from a CIDR rather than `sg_ecs`) → Replace `cidr_blocks` with `security_groups = [<peer-sg-id>]` so only the intended tier can connect (ref: CIS-AWS — SG unrestricted ingress)
- **HIGH** — Private-subnet route table with a `0.0.0.0/0` route to an internet gateway (`gateway_id = aws_internet_gateway.*`) instead of a NAT gateway → Route private egress through `nat_gateway_id`; keep the IGW route on public subnets only (ref: AWS-WAF SEC — private subnet egress)
- **MEDIUM** — `aws_vpc_peering_connection` (or a route to a peer CIDR) without narrowing the accepted/advertised routes to specific subnets → Restrict peering routes to the exact subnet CIDRs that need cross-VPC traffic (ref: AWS-WAF SEC — network segmentation)
- **MEDIUM** — No NAT gateway present while private subnets exist that need outbound (ECS pulling images, RDS patching) → Add an `aws_nat_gateway`, or document VPC endpoints as the egress path (ref: AWS-WAF SEC — private subnet egress)

### Encryption end-to-end (at-rest + in-transit, every resource) — 5

- **HIGH** — `aws_elasticache_replication_group` / `aws_elasticache_cluster` with `at_rest_encryption_enabled = false` (or absent) or `transit_encryption_enabled = false` (or absent) → Set both to `true`; for Redis with transit encryption set `auth_token` via `data.sops_file.secret.data[...]` (ref: AWS-WAF SEC — encryption at rest)
- **HIGH** — `aws_s3_bucket` without an `aws_s3_bucket_server_side_encryption_configuration` → Add SSE config (`aws:kms` preferred, `AES256` minimum), in addition to the `public_access_block` already required above (ref: AWS-WAF SEC — encryption at rest)
- **HIGH** — In-transit gap: `aws_lb_target_group` / backend protocol is plain `HTTP` for a tier carrying sensitive data, or an `aws_cloudfront_distribution` default/ordered behavior with `viewer_protocol_policy = "allow-all"` → Use HTTPS/TLS end-to-end; set CloudFront `viewer_protocol_policy = "redirect-to-https"` (ref: AWS-WAF SEC — encryption in transit)
- **MEDIUM** — `aws_sns_topic` / `aws_sqs_queue` / `aws_cloudwatch_log_group` without `kms_master_key_id` / `kms_key_id` → Encrypt at rest with a KMS key (ref: AWS-WAF SEC — encryption at rest)
- **MEDIUM** — `aws_ebs_volume` (or launch-template block device) with `encrypted = false` or absent → Set `encrypted = true` (ref: AWS-WAF SEC — encryption at rest)

### IAM least-privilege (environment-wide) — 3

- **HIGH** — Inline or managed policy with `Action = "*"` or `Resource = "*"` (also covered per-folder) → Scope to the minimum actions and explicit resource ARNs (ref: CIS-AWS — IAM least-privilege)
- **MEDIUM** — Service-level action wildcard (`s3:*`, `ec2:*`, `iam:*`) or a resource wildcard scoped to a service (`arn:aws:s3:::*`) → Enumerate the specific actions and resources the task role actually needs. For a generic `iam-policy` module: it takes a caller-supplied `iam_custom_policy = object({ template = string })` and does **not** structurally constrain scope, so inspect the **inline policy JSON emitted at the env call** — the `jsonencode({ Statement = [...] })` passed to `iam_custom_policy` — and flag any service action wildcard or resource wildcard in that `Statement` list. Do not assume the module narrows it (ref: CIS-AWS — IAM least-privilege)
- **MEDIUM** — `assume_role_policy` / trust policy with `Principal = "*"` or a service principal broader than required → Restrict the trust to the exact service or role ARN that must assume it (ref: CIS-AWS — IAM least-privilege)

### Cross-layer security (remote-state exposure, credential passing) — 3

> **Do not duplicate the bestpractice reviewer.** This reviewer flags sensitive **output blocks**
> missing `sensitive = true`. The bestpractice reviewer flags sensitive **input variables** missing
> `sensitive = true`. Different objects — outputs versus variables. Neither is a dedup of the other.

- **HIGH** — A layer `_outputs.tf` exports a sensitive value (matches `password`, `secret`, `auth_token`, `*_private_key`, `*_api_key`, or a `data.sops_file.secret.data[...]` reference) **without** `sensitive = true` → Mark the output `sensitive = true`; never propagate a raw secret across layers via `terraform_remote_state` (ref: repo secrets policy)
- **HIGH** — A consumer layer reads a secret through `data.terraform_remote_state.<x>.outputs.<secret>` and assigns it to a resource argument, when the secret should be read directly from SOPS in that layer → Read from `data.sops_file.secret.data[...]` locally instead of threading it through remote state (ref: repo secrets policy)
- **MEDIUM** — Cross-layer references rely on `data.terraform_remote_state` pointing at a backend bucket whose `_backend.tf` lacks `encrypt = true` → Ensure every layer's S3 backend sets `encrypt = true`, so state (which may contain sensitive attributes) is encrypted at rest (ref: backend rules — see `rule-catalog.md` § Source tags)

---

## Output

Findings lines only. No prose, no headers. No findings → the single line `NO_FINDINGS`.
