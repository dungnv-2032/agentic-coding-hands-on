# Module Tests

Emitted by `--with-tests` into `{MODULE_DIR}/<name>/tests/*.tftest.hcl`.

The full `.tftest.hcl` reference — every block type, mock provider shape and assertion form — is the
vendored `_vendor-iac/terraform-test/` set. This file covers only what the scaffold emits.

## What the scaffold emits

One `.tftest.hcl` with two `run` blocks:

```hcl
# tests/defaults.tftest.hcl

run "plan_with_defaults" {
  command = plan

  variables {
    project = "test"
    env     = "dev"
  }

  assert {
    condition     = <the module's primary resource is created>
    error_message = "<what it means when this fails>"
  }
}

run "naming_convention" {
  command = plan

  variables {
    project = "test"
    env     = "dev"
  }

  assert {
    condition     = <the Name tag matches ${project}-${env}-…>
    error_message = "Name tag does not follow the project-env convention"
  }
}
```

## Use `command = plan`, not `apply`

A `plan` run needs no credentials and creates nothing.

> **`command = apply` in a module test creates real AWS resources.** It is not a dry run. A test
> suite that provisions infrastructure is a surprise nobody wants in CI, and it bills.

Use mock providers when a test needs data-source values; see the vendored reference for the shapes.

## Write assertions that can actually fail

An assertion whose condition is trivially true — comparing a literal to itself, or asserting a
variable equals the default just set in the same block — is worse than no test. It is a green check
that proves nothing, and it convinces the next reader the module is verified.

Each `error_message` should say what broke, not restate the condition.

## Running them

```bash
terraform test        # from the module directory
```

Tests are opt-in for a reason: a scaffold with two placeholder assertions is a starting point the
author fills in, not verification.
