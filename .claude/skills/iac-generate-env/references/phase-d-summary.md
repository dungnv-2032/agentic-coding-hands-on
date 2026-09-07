# Phase D — Summary and reminders

A variant-scoped summary printed after wiring completes. This is the last thing the user reads before
touching the environment, so it carries every fact they need to act on and nothing they do not.

Path keys resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

---

## Header — always

```
Env Composer complete — <env> / <blueprint> / frontend=<frontend> / route53=<yes|no>
─────────────────────────────────────────────────────────────────────────────
```

## Layer / files table

**Include only the layers the variant declares.** `route53.tf` appears only when `route53 = true`,
and only in the layer that owns the alias record.

| Layer | Notes |
|---|---|
| *(env level)* | `_variables.tf`, `terraform.<env>.tfvars` |
| `1.general` | includes `acm.tf` and the zone when `route53 = true` |
| `3.backend` | includes `route53.tf` for variant `none` — the alias record lives with `alb_backend` |
| `2.frontend` | present for `static-spa` and `ssr`; owns the alias record in both |
| `4.database` | |
| `5.messaging` † | only when `messaging = true` |
| `6.delivery` § | only when `delivery = true` |
| `7.monitoring` ◆ | only when `monitoring = true`; last |

> **No layer other than `1.general` has an `acm.tf`.** Every ALB reads `acm_certificate_arn`
> cross-layer. If a summary shows a cert in a tier layer, the cycle-break was violated.

When an optional layer is absent, its gated re-exports did not fire and every other layer's
`_outputs.tf` is unchanged. Say so — it is the regression boundary the user may be checking.

## Per-layer status

From Phase C.1, one row per layer:

| Column | Values |
|---|---|
| `init` | `ok` · `pending backend bootstrap` |
| `validate` | `Success` · `Error: <first line>` |

Plus `backend dynamodb_table: none` or `stripped N`.

`pending backend bootstrap` is **not a failure** on a fresh environment — the state bucket does not
exist yet. Present it as expected, or the user will go looking for a bug.

---

## Footer — always

### The state backend must be bootstrapped first

Resolve the command through `{MAKE_ROOT}` and state the working directory. Print the **expected
bucket name** from `STATE_BUCKET_PATTERN` so the user can verify it themselves rather than trusting
the tool:

```
Expected state bucket: <resolved STATE_BUCKET_PATTERN>
```

### SOPS reminder — one of three variants

Pick by what Phase A.5 actually did.

**(a) `<PROJECT_PREFIX>` resolved from tfvars.** Seed keys and `.tf` references both use the real
prefix. The user fills values and encrypts. When Phase A.6 produced a key, print the **single
concrete command with the full ARN** — `sops --encrypt --kms` rejects a bare `alias/…`:

```
sops --encrypt --kms <KEY_ARN> --in-place {DEPS_ROOT}/sops/secrets.<env>.yaml
```

**(b) `<PROJECT>` literal placeholder emitted.** tfvars was missing or still held a placeholder. The
user find-replaces `<PROJECT>` in **both** the yaml and every referencing `.tf`, then fills and
encrypts.

**(c) Phase A.5 was skipped.** The blueprint had no sensitive service. Say **"No SOPS setup
required"** — no key, no file, no encryption step.

**When A.5.2 found an already-encrypted file:** the user must open it through `sops` to add the new
keys, since the agent cannot decrypt it. Enumerate the keys this run's blueprint would have written —
the union of every key a fresh seed would contain.

### The plaintext warning

Whenever a run seeded or extended the secrets file, state plainly that it is **plaintext**, is **not**
gitignored, and must be encrypted before it is committed.

This is the one line whose omission cannot be undone by a later run. A secret in git history stays in
git history.

### KMS status

Report `sops_kms_status` — `created`, `exists`, or `manual` — with the alias and ARN when known.

For `manual`, print the create commands so the user can run them under their own profile. For prod,
recommend enabling CloudTrail and key rotation out of band.

### CodeStar connection — only when `delivery = true`

> The connection is created **PENDING** and must be authorized by hand in the AWS console, once per
> environment, before any pipeline's Source stage can run. Terraform cannot automate it.

Without this line the first pipeline run fails with something that reads like a permissions bug.

### When `route53 = false`

Every `alb_*` kept `certificate_arn = "" # TODO`. **Warn that an external ACM ARN is required before
apply** — `terraform validate` passes and `terraform apply` fails.

### Next steps

Resolved through `{MAKE_ROOT}`, with the working directory stated:

```
1. Review the generated files and resolve every remaining # TODO
2. Fill and encrypt the secrets file (if seeded)
3. Bootstrap the state backend
4. make init e=<env> s=<layer>
5. make plan e=<env> s=<layer>
6. Run a full review before apply
```

**This skill never runs `plan` or `apply`.** They are printed, and they are the user's decision.
