# `allowed-tools` Policy for `tkm:iac-*`

**Every shipped `tkm:iac-*` skill declares `allowed-tools` frontmatter.** No exceptions.

## Why this file exists

The upstream kit's safety guarantee was not prose. It was **37 `permissions.deny` entries plus a
PreToolUse Bash hook**, covering `terraform apply|destroy|import|state rm`,
`make apply|destroy|state_rm`, `aws kms schedule-key-deletion`, `aws iam delete-*`,
`aws rds delete-db*`, `sudo`, `eval`, and `curl|sh`.

This kit cannot ship a `permissions` block — that stays base-only. `allowed-tools` frontmatter is the
only boundary available, and it is a **narrower surface, not a deny-list**. Read the residual risk
below before assuming otherwise.

Precedent: 12 of 24 existing extras skills already declare `allowed-tools`.

## Policy

| Skill class | Skills | Tools |
|---|---|---|
| **Read-only** | `tkm:iac-explain` | `Read`, `Glob`, `Grep` |
| **Documentation** | `tkm:iac-diagram` | `Read`, `Glob`, `Grep`, `Write` — `Write` is required by generate mode; diff mode uses none of it |
| **Review** | `tkm:iac-review` | `Read`, `Glob`, `Grep`, `Write`, `Edit`, `Task`, `Bash` |
| **Estimation** | `tkm:iac-cost` | `Read`, `Glob`, `Grep`, `Write`, `Bash`, plus the pricing server's `mcp__*` tools |
| **Generation** | `tkm:iac-generate-module`, `tkm:iac-connect-modules`, `tkm:iac-generate-env` | `Read`, `Glob`, `Grep`, `Write`, `Edit`, `Bash` |
| **Contribution** | `tkm:iac-contribute-module` | `Read`, `Glob`, `Grep`, `Write`, `Edit`, `Bash` |

**A skill that consumes an MCP server must list that server's tools explicitly.** `allowed-tools` is
an allowlist, so an unlisted `mcp__…` tool is simply unavailable — the skill then falls through to
whatever fallback it documents and reports the server as unreachable, which is indistinguishable from
a real outage. Precedent: `claude/skills/bidding-proposal/SKILL.md:4-13` enumerates five
`mcp__clio__*` tools.

**Write it as a YAML block sequence**, matching all 12 existing extras skills that declare
`allowed-tools` — not as an inline comma-separated string:

```yaml
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Task
  - Bash
```

> The subagent-spawning tool is named **`Task`**. The plan's policy table wrote `Agent`; no such tool
> exists in either kit, and `tests/validate-skills.py` does not validate `allowed-tools`, so the
> wrong name would ship as a silently unavailable reviewer fan-out rather than an error.

Grant the narrowest class that does the job. A skill that only reads must not list `Write`.

- **Review needs `Bash`** for checkov, `trivy config` and plan-time Terraform, `Task` for the
  reviewer fan-out, and **`Edit`** because its HIGH fix loop patches existing `.tf` files in place.
  `Write` alone would force a whole-file rewrite to change one argument — a far larger blast radius
  than the fix requires.
- **Generation needs `Bash`** for `terraform fmt`, `make symlink_all`, and the two gated `aws kms`
  calls.
- **Generation must never list `Bash` unscoped** — see the next section.

## Every `Bash`-carrying skill enumerates its commands

Where `Bash` is unavoidable, the skill **states the exact commands it may run**, as an explicit list
in its `SKILL.md`. Anything outside that list is a defect in the skill, not a judgement call at
runtime.

A skill that lists `Bash` without enumerating its commands is incomplete and must not ship.

Two prohibitions hold everywhere, in every class:

- **Never** `terraform apply`, `terraform destroy`, `terraform import`, `terraform state rm`.
- **Never** `make apply`, `make destroy`, `make state_rm`.

Plan-time verbs only. `terraform init`, `terraform validate`, `terraform fmt`, `terraform plan` are
the ceiling.

Prose constraints like these stay, but they are **secondary**. An LLM can rationalize past prose —
that is precisely why the source used a hook rather than trusting a sentence.

## Residual accepted risk

> There is no harness-level deny-list on shell commands. A sufficiently determined or confused agent
> can still reach a destructive AWS or Terraform command through an allowed tool. This is a real
> reduction in safety versus the source, accepted deliberately.

Recorded verbatim from the plan's enforcement-boundary section so an implementer reading only this
file still sees it.

**Compensating controls where the blast radius is worst:**

- `tkm:iac-review`'s `--approve` mode defaults **on** for prod-like environment names.
- Environment composition gates its two `aws kms` calls explicitly, and the KMS reuse check is a hard
  stop outside the origin repository (see
  [`idempotency-matchers.md`](./idempotency-matchers.md)).

## What the port reproduces

| Layer | Ported? | How |
|---|---|---|
| Per-skill tool allowlist | **yes** | `allowed-tools` frontmatter on every `tkm:iac-*` skill |
| A PreToolUse hook | **yes — routing only** | One hook on matcher `Skill`. Its job is correcting skill selection, not filtering shell commands. |
| A Bash-matcher deny-list | **no** | Requires a `permissions` block, which stays base-only. |

The routing hook is `claude/hooks/iac-routing-guard.cjs`, registered in the kit's
`claude/settings.json`. CI asserts that file's top-level keys are exactly `["hooks"]`, and that every
command it registers resolves to a hook the kit actually ships — a registration pointing at a missing
file would otherwise ship a silently dead hook with CI green.

Note what the hook is not: it decides *which skill runs*, never *which command runs*. Every
constraint on what a skill may execute still comes from `allowed-tools` alone.

## Related contracts

- [`layout-contract.md`](./layout-contract.md) — paths and regions
- [`finding-format.md`](./finding-format.md) — reviewer finding line and parse regex
- [`idempotency-matchers.md`](./idempotency-matchers.md) — re-run guards
