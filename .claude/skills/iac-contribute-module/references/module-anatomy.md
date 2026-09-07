# Module Anatomy

The four-file contract plus README, scaffolded under `{MODULE_DIR}/<name>/`.

Path keys resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

> **Bounded, deliberate duplication.** The full generator conventions are owned by
> `tkm:iac-generate-module`. Cross-skill reuse in this kit is by **invocation, never by linking a
> sibling's `references/`**, so what follows is the minimum restated inline. Keep it minimal — if it
> grows, it becomes a second source of truth for naming and encryption defaults, which is exactly the
> drift the single-owner rule exists to prevent. For anything beyond this, invoke
> `/tkm:iac-generate-module`.

## The four files

```
{MODULE_DIR}/<name>/
├── _versions.tf
├── _variables.tf
├── main.tf
├── _outputs.tf
└── README.md
```

Every `.tf` file starts with its own relative path as a comment on line 1.

### `_versions.tf`

```hcl
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

Grouped with `#basic` for the baseline pair and `#<module-name>` for the rest. Every variable carries
a `description` and an explicit `type`; optional values get `default = null` or an explicit default.

`project` and `env` are required in **every** module.

> **Never interpolate inside a `description`.** HCL forbids it and `terraform init` fails with
> `Error: Variables not allowed`. Write the placeholder literally instead.

A module that may be instantiated more than once in one environment needs a **discriminator**
variable (`name` or `name_suffix`) that reaches **both** the resource identifier **and** the `Name`
tag — otherwise two calls collide.

### `main.tf`

Name and tag pattern `${var.project}-${var.env}-<resource-type-kebab>`, or
`${var.project}-${var.env}-${var.name}-<resource-type-kebab>` when the module carries a
discriminator.

`count` / `for_each` is the **first** argument in a resource block; `tags` is the **last** real
argument, before `depends_on` and `lifecycle`.

### `_outputs.tf`

Every key ID, ARN and name a consumer needs, each with a `description`. Mark sensitive outputs.

### `README.md`

Must carry the terraform-docs hook markers so the hook can fill it:

```
<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
```

Content between them is machine-owned. Write the surrounding prose — purpose, an example call, any
caveat — and leave the block for the hook.

## `--with-example`

A standalone example directory demonstrating a realistic call: `_versions.tf`, `_providers.tf` (with
`profile = "${var.project}-${var.env}"` and `default_tags`), `_variables.tf`, `main.tf`,
`_outputs.tf`, `terraform.tfvars`, `README.md`.

The example exists so the module can be validated on its own, before any environment consumes it.

## Never scaffold over an existing module

If `{MODULE_DIR}/<name>/` already exists, **stop**. Do not overwrite, do not merge, do not
"regenerate cleanly" — it may have been hand-edited since.

Report that it exists and what it contains. Full rule:
[`idempotency-matchers.md`](../../_shared/extras/iac/idempotency-matchers.md).
