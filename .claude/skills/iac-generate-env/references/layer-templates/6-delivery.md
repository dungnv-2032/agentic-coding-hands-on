# Layer `6.delivery`

Generated **only when `delivery = true`**. CI/CD pipelines per service, plus blue/green deployment
groups for the services that opted in.

Module calls and emission order come from the lookup table in
[`cross-layer-contracts.md`](../cross-layer-contracts.md).

**Layer files:** `_backend.tf`, `_data.tf`, `codestar.tf`, `s3.tf`, `codebuild.tf`,
`codedeploy.tf` *(only when at least one service is BLUE_GREEN)*, `codepipeline.tf`, `templates/`
*(only when at least one service is BLUE_GREEN — not Terraform)*, `_outputs.tf`.

**`_backend.tf` carries NO SOPS block.** This layer has no sensitive input, so it keeps a plain
backend: no `sops` provider, no `data.sops_file`. `terraform init` works here with no KMS setup.

---

## IAM invariants across every contract in this layer

1. **`iam:PassRole` is always paired with a
   `Condition StringEquals "iam:PassedToService"` list.** An unconditioned `PassRole` lets the holder
   hand any role to any service.
2. The layer has exactly **two documented wildcard exceptions**, each carrying an inline rationale
   comment:
   - `ecr:GetAuthorizationToken` on the CodeBuild role
   - `ecs:RegisterTaskDefinition` and `ecs:Describe*` on the CodePipeline role

   Neither is ARN-scopable by AWS. **Any other `Resource = "*"` in this layer is a HIGH finding** —
   everything else is ARN-scoped.

---

## `codestar-connection` — one per environment

Block `codestar_connection`, shared by every pipeline.

> **The connection is created in a PENDING state and must be authorized by hand in the AWS console,
> once per environment, before any pipeline's Source stage can run.** Terraform cannot automate this.
> The summary must say so — otherwise the first pipeline run fails with an error that looks like a
> permissions bug.

---

## `s3_artifacts` — one shared artifact bucket

Reuses the `s3-bucket` module with name token `pipeline-artifacts`.

The env call passes the additive `bucket_policy` input a `jsonencode(...)` **Deny-unless-PrincipalArn**
document, locking writes to the pipeline roles. That input defaults to `null`, so every other
`s3-bucket` caller is unchanged — see
[`cross-layer-contracts.md`](../cross-layer-contracts.md).

---

## `codebuild` — one per pipeline-target

Block `codebuild_<name>`: builds and pushes to that service's ECR repository.

For `static-spa`, an additional `codebuild_invalidate` block runs the CloudFront invalidation.

### The build artifact differs by strategy

| Strategy | Artifact | Shape |
|---|---|---|
| ROLLING | `imagedefinitions.json` | `[{"name":"<container>","imageUri":"<uri>"}]` |
| BLUE_GREEN | `imageDetail.json` | `{"ImageURI":"<uri>"}` |

> **CodeDeployToECS consumes `imageDetail.json`; the ECS rolling action consumes
> `imagedefinitions.json`.** Emitting the wrong one for the strategy is the classic silent failure
> here — the build succeeds, the pipeline advances, and the deploy stage does nothing useful.

### Conditional IAM statements need the `jsondecode(jsonencode(...))` wrapper

The role's inline policy gates each statement on a nullable input — a statement is emitted only when
its input is non-null. **Wrap every conditional statement-list branch:**

```hcl
var.ecr_repository_arn == null ? [] : jsondecode(jsonencode([{ … }, { … }]))
```

> **This wrapper is mandatory, not stylistic.** Mixed-shape statement objects — a string `Resource`
> in one, a list in another, some with a `Condition` and some without — fail Terraform's conditional
> type unification on a fresh scaffold:
> `The true and false result expressions must have consistent types`.
>
> It was hit on two independent fresh-scaffold runs upstream. Without the wrapper the layer does not
> `terraform validate` at all.

The same wrapper is mandatory on the CodePipeline role's `pipeline_type`-gated statements.

---

## `codedeploy` — only for BLUE_GREEN services

Block `codedeploy_<name>`, one per service whose `delivery_strategies[<name>] = BLUE_GREEN`. Omitted
entirely when no service opted in.

Reads, cross-layer from `3.backend`: the ALB listener ARNs and the blue/green target-group **names**.

> **CodeDeploy's `target_group_pair_info` takes NAMES, not ARNs.** That is why the ALB module exports
> `target_group_names` and `green_target_group_names` alongside the ARN map, and why the green
> target-group name uses a deterministic truncation applied once in the module.

---

## `codepipeline` — one per pipeline-target

Block `pipeline_<name>`. `pipeline_type` is `ecs-rolling` or `ecs-bluegreen`, per that service's
strategy.

**Pipeline-targets** are every `<backend_services>` entry — `api` **and** `worker`, with workers
forced to `ecs-rolling` — plus `frontend` for `static-spa` always (`pipeline_type = s3-frontend`), and
for `ssr` when the user opted the frontend in.

GitHub `FullRepositoryId` and `BranchName` come from the tfvars TODOs seeded in Phase A.

### Fail-closed is a `validation` block, not a comment

Both variables carry a **non-empty validation** so the seeded `""` fails **at plan**:

```hcl
variable "github_repository" {
  type = string
  validation {
    condition     = length(var.github_repository) > 0
    error_message = "delivery_<name>_github_repository is empty — fill the TODO in terraform.<env>.tfvars (GitHub FullRepositoryId, e.g. my-org/my-repo)."
  }
}
```

…and the equivalent for `github_branch`.

> **Without the validation block there is no fail-closed.** An empty string passes `terraform
> validate` and `plan`, and only errors at `apply` — by which point the pipeline resources are
> half-created. The validation is what makes the TODO genuinely blocking rather than a comment
> nobody reads.

---

## Deployment templates — not Terraform

For **every** BLUE_GREEN service, emit:

```
6.delivery/templates/<svc>/taskdef.json
6.delivery/templates/<svc>/appspec.yaml
```

with TODO placeholders.

> These are **not** Terraform files and are not applied. CodeDeploy reads `taskdef.json` and
> `appspec.yaml` **from the source artifact at deploy time**, not from this folder. The copies here
> are templates the user commits into their application repository.
>
> Emitting them here and expecting CodeDeploy to read them is the misunderstanding this note exists
> to prevent.

The `templates/` directory is omitted entirely when no service is BLUE_GREEN.

---

## Cross-layer reads

All **downstream** — no upstream layer ever reads this one, so the graph stays acyclic.

| Source | What is read |
|---|---|
| `1.general` | ECS `cluster_name` |
| `3.backend` | ECR repository ARN and URL, ECS service names, task and execution role ARNs; per BLUE_GREEN service the ALB listener ARNs and blue/green target-group names |
| `2.frontend` (`static-spa`) | S3 bucket id and ARN, CloudFront distribution id and ARN |
| `2.frontend` (`ssr`) | frontend ECS, ECR and ALB equivalents |

Each of those source outputs exists only because Phase B's `delivery`-gated re-export appended it.
With `delivery = false` none of them fire and every upstream `_outputs.tf` is unchanged.
