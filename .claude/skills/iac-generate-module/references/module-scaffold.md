# Module Scaffold

The skeleton written into `{MODULE_DIR}/{service}/` when the module folder does not exist.

Shape and hardening rules are in
[`terraform-conventions.md`](./terraform-conventions.md). This file is the file set and the guards.

## `{MODULE_DIR}` is expected to be empty

In a fresh project there are no modules. Scaffolding one is the **normal** path, not a fallback —
modules are an output this kit creates, not a prerequisite it requires.

## Resolution order

1. Normalize the service name and apply the alias map →
   [`service-alias-map.md`](./service-alias-map.md).
2. **Module folder exists** → read its `_variables.tf` and `_outputs.tf` to learn the schema, then
   emit the consumer block. **Do not re-scaffold.**
3. **Module folder missing** → scaffold the skeleton below, then emit the consumer block with `# TODO`
   placeholders for required inputs.

## Duplicate-scaffold guard

If `{MODULE_DIR}/{service}/` **already exists** — from an earlier run, or because the service appears
in more than one layer, as a shared `security-group` does — do **not** overwrite or re-scaffold it.

Generate only the new env-folder module-call block referencing the existing module. Several env
blocks may legitimately share one local module.

**Never delete an existing file. Skip generation when the file is already there.** A module folder
may have been hand-edited since it was scaffolded, and re-scaffolding silently discards that work.

Full rule:
[`idempotency-matchers.md`](../../_shared/extras/iac/idempotency-matchers.md).

## File set

Five files, always — and **only** five:

```
{MODULE_DIR}/{service}/
├── _versions.tf
├── _variables.tf
├── main.tf
├── _outputs.tf
└── README.md
```

> **A module needing a provider alias declares it in `_versions.tf`, not a sixth file.** Adding a
> `_providers.tf` alongside it produces `Duplicate required providers configuration` and the layer
> fails `init` — a real error this kit's own gate has caught. Put `configuration_aliases` in the
> existing `required_providers` block:
>
> ```hcl
> required_providers {
>   aws = {
>     source                = "hashicorp/aws"
>     version               = ">= 6.37.0"
>     configuration_aliases = [aws.us_east_1]
>   }
> }
> ```
>
> The caller then passes `providers = { aws = aws.us_east_1 }` (or both, when the module uses the
> default provider as well). Modules that need this: a CLOUDFRONT-scope WAF and a CloudFront viewer
> certificate, both of which must be created in `us-east-1`.

### `_versions.tf`

```hcl
# <relative-path>/_versions.tf
terraform {
  required_version = ">= 1.14.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.37.0"
    }
  }
}
```

### `_variables.tf`

Path header first. Group with `#basic` for the baseline trio and `#<module-name>` for the rest.
Every variable gets a `description` and an explicit `type`.

```hcl
# <relative-path>/_variables.tf

#basic
variable "project" {
  description = "Project name, used in resource naming and tags"
  type        = string
}

variable "env" {
  description = "Environment name (dev, stg, prod)"
  type        = string
}

variable "region" {
  description = "AWS region the module's resources are created in"
  type        = string
}

#<module-name>
# ... module-specific variables, each with description + type
```

> **`region` is part of the baseline, not optional.** Every env-folder module call emits
> `region = var.region`, so a module scaffolded without it fails immediately with
> `Unsupported argument`. The trio is `project`, `env`, `region` — all three, every module.

For a multi-instance module, the discriminator variable goes here too — see
[`terraform-conventions.md`](./terraform-conventions.md) § Multi-instance.

### `main.tf`

Path header first. Resources named for their purpose, tagged
`${var.project}-${var.env}-${var.name}-<resource-type-kebab>`, with the always-on encryption and TLS
defaults for the resource types that have them.

### `_outputs.tf`

Path header first. Every key ID, ARN and name a downstream module needs, each with a `description`.
Mark sensitive outputs.

### `README.md`

Must carry the terraform-docs hook markers so the hook can fill it:

```
<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
```

## Scaffold quality bar

Before finishing:

- The structure matches the file set above.
- Types are explicit; every variable and output has a `description`.
- Naming and tag patterns are consistent.
- The module is ready for `terraform fmt` and `terraform validate` with no manual cleanup.
- No deprecated patterns, no undocumented variables or outputs.

Then state plainly what was generated: the key variables, resources and outputs, and any assumption
made — especially for optional or conditional logic.

## Normalizing an existing module

When asked to fix rather than create, the same standards apply, plus:

- Reorganize files to the standard layout.
- Type and document every variable and output.
- Make the README hook-compatible.
- On a provider major-version bump: check for schema changes, replace deprecated attributes, and use
  `moved` blocks where a resource is renamed — **a rename without a `moved` block destroys and
  recreates the resource.**
