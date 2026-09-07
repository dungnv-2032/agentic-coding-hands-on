# Best Practice Reviewer Checklist

**29 rules** — 22 per-folder (9 HIGH · 9 MEDIUM · 4 LOW) + 7 full-env.

Emit every finding as `[SEVERITY][BESTPRACTICE] description → fix (ref: <source>)`. The line shape
and parse rules are owned by
[`finding-format.md`](../../_shared/extras/iac/finding-format.md) — read it, do not restate it.

Path keys resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

**Targets**
- Invoked from generation: `{ENV_DIR}/{layer}/`
- If a local module was scaffolded, also review `{MODULE_DIR}/{service}/`

---

## HIGH — blocks or corrupts state

- No S3 backend configured (`backend "s3"` block missing) — using local state → Add a `backend "s3"` block with `use_lockfile = true` (S3-native locking) (ref: backend rules)
- State locking not configured: `use_lockfile = true` missing from the `backend "s3"` block → Add `use_lockfile = true` (S3-native locking, Terraform >= 1.11) (ref: backend rules)
- Legacy `dynamodb_table` still present in the `backend "s3"` block → Remove `dynamodb_table` and rely on `use_lockfile = true` (ref: backend rules)
- Backend `bucket` does not resolve `{STATE_BUCKET_PATTERN}`, or carries no account-scoped discriminator — e.g. `{project}-{env}-iac-state` with no trailing `-{account-id}`. S3 names are global, so an account-agnostic name either fails `terraform init` on a bucket that does not exist or, worse, resolves to one in someone else's account → Use `bucket = "{STATE_BUCKET_PATTERN}"`; if the project overrides that key, check the override itself carries a discriminator (ref: backend rules)
- AWS region hardcoded (not using `var.region`) → Replace with `var.region`. **Except inside a `backend "s3"` block**, where a literal is mandatory (ref: repo naming policy)
- AWS account ID hardcoded → Replace with `data.aws_caller_identity.current.account_id`. **Except inside a `backend "s3"` block**, where a literal or a `<account-id>` placeholder is mandatory (ref: repo naming policy)
- `required_providers` block missing in the `terraform {}` block → Add `required_providers` with `hashicorp/aws >= 6.37.0` (ref: HashiCorp TF-style — required_providers)
- Any `.tf` file missing the mandatory path-header comment as its first line → Add `# <relative-path-to-file>.tf` as the first line (ref: repo path-header policy)
- Any `module {}` block sourcing via git tag (`source = "git@github.com:<org>/<repo>.git//modules/…?ref=terraform-aws-…_v…"`) — git-tag sourcing was removed by the local-module-only spec change → Replace with the local relative path `source = "{MODULE_DEPTH}"` referencing `{MODULE_DIR}/{service}/`. Scaffold the local module folder if it does not exist yet (ref: repo module-sourcing policy)

## MEDIUM — fix before production

- `outputs.tf` missing key exports (VPC ID, subnet IDs, security group IDs, ALB DNS) → Add output blocks for critical resource attributes (ref: repo naming policy)
- Resource `Name` tag not following the `${var.project}-${var.env}-<resource-type-kebab>` pattern — or, inside a multi-instance module, `${var.project}-${var.env}-${var.name}-<resource-type-kebab>` → Rename to follow the convention (ref: repo naming policy)
- **Multi-instance module missing a discriminator** — a module in the multi-instance set (`security-group`, `iam-role`, `iam-policy`, `alb`, `sns`, `sqs`, `ecr`) whose primary resource **name/identifier OR `Name` tag** is a fixed `${var.project}-${var.env}-<static>` with **no** per-block discriminator var (`name` / `name_suffix` / `<purpose>`) interpolated in — an environment calling the module twice (2 ALBs, several SNS/SQS/ECR) produces colliding names and tags → Add a discriminator var and interpolate it into **both** the resource name **and** the `Name` tag: `${var.project}-${var.env}-${var.name}-<svc>` (ref: multi-instance pattern)
- Variable declarations missing a `description` field → Add a description explaining what the variable controls (ref: HashiCorp TF-style — variable description)
- Sensitive variables (passwords, keys) not marked `sensitive = true` → Add `sensitive = true` to prevent value exposure in logs (ref: repo secrets policy)
- Module argument matching the sensitive-input pattern (`password`, `master_password`, `auth_token`, `*_secret`, `*_api_key`, `*_private_key`) **not** referenced via `data.sops_file.secret.data[...]`, `aws_secretsmanager_secret_version`, or `aws_ssm_parameter` → Migrate to the SOPS data source (`data.sops_file.secret.data["<PROJECT>_<KEY>"]`), or AWS Secrets Manager / SSM Parameter Store for AWS-managed secrets. **Skip this finding** when the input is read from `var.<name>` AND that `variable` block has `sensitive = true` AND the tfvars value is `data.sops_file.secret.data[...]` — that is an indirect SOPS reference, not a leak (ref: repo secrets policy)
- `count` / `for_each` not placed as the first argument in a resource block → Move `count` / `for_each` to first position (ref: HashiCorp TF-style — count first)
- `tags` not placed as the last real argument, before `depends_on` and `lifecycle` → Move `tags` to last position (ref: HashiCorp TF-style — tags last)
- Variables not grouped by resource under `#basic` / `#<resource>` section comments → Add grouping comments (ref: repo naming policy)

## LOW — style and completeness

- Missing `required_version` constraint in the `terraform {}` block → Add `required_version = ">= 1.14.7"` (ref: HashiCorp TF-style — required_version)
- Stateful resources (`aws_db_instance`, `aws_s3_bucket`) without `lifecycle { prevent_destroy = true }` in production → Add a lifecycle block for prod resources (ref: AWS-WAF REL — prevent_destroy)
- Hardcoded AMI ID → Replace with a `data "aws_ami"` lookup (ref: HashiCorp TF-style — no hardcoded IDs)
- Output names not following the `{resource_type}_{attribute}` pattern (e.g. `vpc_id`, `alb_dns_name`) → Rename outputs to follow the convention (ref: HashiCorp TF-style — output naming)

---

## Full-Env Scope — cross-layer and environment-wide audit

**When this applies.** Everything above is *per-folder*, for inline review. When the review targets a
**complete environment** (`{ENV_DIR}` with all its layers), also run the 7 checks below — they reason
across **all** layers at once: tagging, state-file organization, output completeness, naming, module
sourcing. Runs in parallel with the security reviewer.

- **HIGH** — **Cross-layer output completeness**: a `data.terraform_remote_state.<x>.outputs.<key>` reference in one layer whose `<key>` is **not** exported by the source layer's `_outputs.tf` — the consumer layer's `terraform plan` fails → Add the missing `output` to the source layer, or fix the reference (ref: HashiCorp TF-style — output naming)
- **HIGH** — **State-key collision**: two layers whose `backend "s3"` blocks use the **same** `key` (state path) — they share and overwrite each other's state → Give each layer a distinct `key = "<layer>/terraform.{env}.tfstate"` (ref: backend rules)
- **HIGH** — **Module sourcing, environment-wide**: any `module {}` block anywhere in the environment sourcing via git tag, SSH, or HTTPS URL → Replace with a local relative path (`{MODULE_DEPTH}`, adjusted for layer depth). Scaffold the local module folder if it does not exist. Same rule as the per-folder HIGH above, applied across every layer (ref: repo module-sourcing policy)
- **MEDIUM** — **Cross-layer tagging audit**: a taggable resource in any layer missing the required tags (`Environment`, `Project`, `Owner`, `ManagedBy = terraform`) — whether via provider `default_tags` or per-resource `tags` → Add the missing tags, preferring provider `default_tags` so every layer inherits them consistently (ref: repo tagging policy)
- **MEDIUM** — **Backend consistency across layers**: a layer whose `_backend.tf` drifts from the rest — a different `bucket` shape (must be `{STATE_BUCKET_PATTERN}`), missing `use_lockfile = true`, or a stale `dynamodb_table` → Align every layer's backend block to the single canonical shape (ref: backend rules)
- **MEDIUM** — **Naming convention environment-wide**: a resource `Name` tag not following `${var.project}-${var.env}-<resource-type-kebab>` consistently across layers → Rename to the convention (ref: repo naming policy)
- **LOW** — **Unused cross-layer wiring**: a `data "terraform_remote_state" "<alias>"` block appended to a layer's `_backend.tf` but not referenced anywhere in that layer's `.tf` files → Remove the dead block, or wire the intended reference (ref: HashiCorp TF-style — no dead code)

---

## Output

Findings lines only. No prose, no headers. No findings → the single line `NO_FINDINGS`.
