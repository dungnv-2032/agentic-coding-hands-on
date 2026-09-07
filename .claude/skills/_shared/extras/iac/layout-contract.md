# IaC Layout Contract

Single owner of every repository-layout value the `tkm:iac-*` skill family depends on.

The upstream AIDD kit hardcoded one repository's layout in 256 places across 34 files — including
inside a review rule's regex. This file replaces all of them. **No `tkm:iac-*` skill may hardcode a
path.** Every path is resolved through a key below.

## Resolution rule

For each key, in order — first hit wins:

1. **Project override** — a `## IaC Layout` section in the consuming project's `CLAUDE.md`,
   written as `KEY = value`, one per line.
2. **Default** — the value in the table below.

`PRICING_API_REGION` is exempt: it is **not user-overridable** (see below).

Keys interpolate each other with `{BRACES}`. Runtime slots — `{env}`, `{project}`, `{service}`,
`{layer}`, `{account-id}` — are filled at invocation time, never at resolution time. `{layer}` is one
entry from `LAYERS`.

The defaults reproduce the upstream repository's behaviour exactly, so a project that sets no
overrides behaves byte-for-byte as the source kit did.

## Keys

17 rows. `ORG` / `REPO` share a row but are two independent keys, so
[`layout-defaults.json`](./layout-defaults.json) carries 18 entries.

| Key | Default | Notes |
|---|---|---|
| `IAC_ROOT` | `examples/aws/terraform` | Root of all Terraform sources, relative to repo root. |
| `ENV_DIR` | `{IAC_ROOT}/envs/{env}` | One directory per environment. |
| `MODULE_DIR` | `{IAC_ROOT}/modules` | Local modules. Modules are consumed by relative path only — never by git tag. |
| `MODULE_DEPTH` | `../../../modules/{service}` | **Three** levels up. The `source` literal written into a module call from inside a layer directory. |
| `DEPS_ROOT` | `examples/aws/terraform-dependencies` | Non-Terraform dependency payloads (SOPS secrets, Lambda handler code). |
| `SOPS_PATH` | `../../../../{DEPS_ROOT-basename}/sops/secrets.{env}.yaml` | **Four** levels up, then into `DEPS_ROOT`. Re-derives — see below. |
| `STATE_BUCKET_PATTERN` | `{project}-{env}-iac-state-{account-id}` | Overridable. The `-{account-id}` suffix is the invariant, not the whole shape — S3 names are global. **The kit never creates this bucket.** |
| `PROFILE_PATTERN` | `{project}-{env}` | AWS named profile. |
| `SOPS_ALIAS_PATTERN` | `alias/{project}-{env}-sops-key` | KMS alias for the SOPS encryption key. |
| `LAYERS` | `1.general`, `2.frontend`, `3.backend`, `4.database`, `5.messaging`, `6.delivery`, `7.monitoring` | Ordered, and **role-indexed** — see below. The last three are toggle-gated: present in the list, generated only when their toggle is on. |
| `DEFAULT_REGION` | `ap-northeast-1` | The region resources are **priced and deployed** in. |
| `PRICING_API_REGION` | `us-east-1` | **Not user-overridable.** See below. |
| `WORK_DIR` | `.aidd` | Scratch directory for findings files and loop counters. Must be gitignored. |
| `DOCS_DIR` | `docs` | Where a generated document that the user keeps is written — currently the diagram deliverable. Distinct from `WORK_DIR`: this one is committed. |
| `ORG` / `REPO` | `sun-asterisk-internal` / `sun-infra-iac` | Upstream origin. **Provenance only** — no skill reads these. Kept so a reader can find the source of a ported rule. |
| `MAKE_ROOT` | `examples/aws` | Directory holding the `Makefile` that `make init/plan/apply e=<env> s=<layer>` runs from. |
| `DRAWSUN_ENDPOINT` | *(unset)* | Opt-in. When unset, the diagram canvas leg is not offered. |

### `MODULE_DEPTH` is three levels; `SOPS_PATH` is four

This is not a typo and the two must never be unified.

- A module call lives in `{ENV_DIR}/{layer}/*.tf` and points **into** `{MODULE_DIR}`, which sits
  under `{IAC_ROOT}` — three levels up (`layer` → `env` → `envs` → `{IAC_ROOT}`).

  **Three is invariant.** It is measured from `{ENV_DIR}/{layer}` to `{IAC_ROOT}`, so it does not
  change when `IAC_ROOT` is overridden to a shallower or deeper path. An override moves the whole
  tree; it does not move the layer relative to its own root.
- A SOPS reference lives at the same depth but points **out of** `{IAC_ROOT}` into `{DEPS_ROOT}`,
  a sibling of `terraform/` — one level further, four in total.

  **The four is invariant; the directory name after it is not.** `SOPS_PATH`'s default spells out
  `terraform-dependencies` because that is `DEPS_ROOT`'s basename by default. **A project that
  overrides `DEPS_ROOT` must see that name change with it** — the count of `../` stays four, the
  name does not.

  Overriding `DEPS_ROOT` to `infra/terraform-deps` and keeping the literal default yields
  `../../../../terraform-dependencies/sops/secrets.{env}.yaml`, which resolves to nothing. It fails
  **silently at plan time** as a SOPS decryption error, far from its cause — exactly the failure this
  section exists to prevent. The worked override example below is a repository with this shape, so
  reading the default as literal is the natural mistake, not an exotic one.

Conflating them breaks SOPS wiring **silently at plan time**: Terraform resolves the wrong file
path and the failure surfaces as a decryption error far from its cause.

### `PRICING_API_REGION` is separate from `DEFAULT_REGION`

The AWS Price List Query API is not available in `ap-northeast-1`. The upstream `.mcp.json` pins
`AWS_REGION: us-east-1` for the pricing MCP server for exactly this reason — that value is the
**API endpoint**, not the region being priced.

Collapsing the two keys pushes `tkm:iac-cost` onto its fallback path, where its top failure mode is
inventing prices from training data. `tkm:iac-cost` fails loudly rather than guess, so a collapsed
key turns a working estimate into a hard error at best.

`DEFAULT_REGION` is what you are pricing. `PRICING_API_REGION` is where you ask.

**Where this lands.** [`iac-mcp-config.json`](./iac-mcp-config.json) registers the pricing MCP server.
JSON takes no comments, so its two load-bearing values are recorded here instead:

| Value | Meaning | Provenance |
|---|---|---|
| `AWS_REGION: "us-east-1"` | The Price List **API endpoint** — `PRICING_API_REGION`, not the region being priced. Never parameterize it to `DEFAULT_REGION` "for consistency". | upstream `.mcp.json` |
| `awslabs.aws-pricing-mcp-server@1.0.31` | Pinned for reproducibility. | upstream `.mcp.json` |

The pin will age. Bumping it is fine — bumping it *by accident*, or while assuming the region key is
a target region, is not. That is what this table exists to prevent.

### `STATE_BUCKET_PATTERN` is overridable, but the kit never creates the bucket

The default shape is what the origin repository's bootstrap script creates. That script does **not** ship
with this kit, so on any other project the state bucket already exists — created by whoever set the
account up — and its name follows that organisation's convention, not this one. Forcing the default
would lock the kit out of every repository that predates it.

So: override the key to whatever the bucket is actually called, in the project's `## IaC Layout`
block. **Creating and securing the bucket is the user's job** — versioning, encryption, and blocking
public access included. The kit reads and writes state; it never provisions the place state lives.

One invariant survives every override: the name must be **globally unique**, which in practice means
keeping an account-id suffix or an equivalent discriminator. The bestpractice reviewer flags a bucket
that looks account-agnostic, because the failure mode — quietly pointing at a bucket in someone
else's account — is worse than a build error.

Generator and reviewer both resolve this key, so an override moves them together. A hardcoded default
in either one puts them into a fix loop against each other.

### `LAYERS` is a list of roles, not just names

The seven entries are positional **roles**, in this order:

| # | Role | Generated when |
|---|---|---|
| 1 | general / network | always |
| 2 | frontend | always (contents vary by variant) |
| 3 | backend | always |
| 4 | database | always |
| 5 | messaging | `messaging = true` |
| 6 | delivery | `delivery = true` |
| 7 | monitoring | `monitoring = true` |

**An override renames roles by position, and must supply all seven** — even the ones this environment
will not generate. A project that lists four names has said nothing about what its messaging layer is
called, and a generator with `messaging = true` is then forced to invent one; it will, and the name it
picks will not be yours.

```
LAYERS = 1.network, 2.web, 3.services, 4.data, 5.queue, 6.release, 7.observability
```

Naming a role you never enable costs nothing. Omitting it costs you the name.

> The earlier note that the last three are "absent by default" described *generation*, not the list —
> they have always been in the default value. Absent from the environment, present in `LAYERS`.

## Project override example

```markdown
## IaC Layout

IAC_ROOT = infra/terraform
DEPS_ROOT = infra/terraform-deps
DEFAULT_REGION = ap-southeast-1
```

Everything not listed keeps its default. `ENV_DIR`, `MODULE_DIR` and `SOPS_PATH` re-derive automatically from the
overridden `IAC_ROOT`.

## Worked examples

The blocks below are tagged `resolved-example`. They contain the **resolved literals** deliberately,
so a skill author reading this file sees concrete output rather than an abstraction. The path-hygiene
assertion exempts `resolved-example` blocks; it does not exempt anything else.

Given all defaults, `project = aidd`, `env = dev`, `service = alb`:

```resolved-example
ENV_DIR              examples/aws/terraform/envs/dev
module source        ../../../modules/alb
SOPS source_file     ../../../../terraform-dependencies/sops/secrets.dev.yaml
backend bucket       aidd-dev-iac-state-<account-id>
backend profile      aidd-dev
KMS alias            alias/aidd-dev-sops-key
findings file        .aidd/findings-security.txt
make target          make plan e=dev s=3.backend
```

Emitted into `examples/aws/terraform/envs/dev/3.backend/alb.tf`:

```resolved-example
module "alb_backend" {
  source = "../../../modules/alb"
  # ...
}
```

Emitted into `examples/aws/terraform/envs/dev/3.backend/_backend.tf`:

```resolved-example
data "sops_file" "secret" {
  source_file = "../../../../terraform-dependencies/sops/secrets.${var.env}.yaml"
}
```

`<account-id>` stays a literal placeholder — a `backend "s3"` block cannot interpolate
`data.aws_caller_identity.current`, so the engineer fills it once from `pre-build.sh` output.

## Related contracts

- [`finding-format.md`](./finding-format.md) — reviewer finding line and parse regex
- [`idempotency-matchers.md`](./idempotency-matchers.md) — re-run guards
- [`allowed-tools-policy.md`](./allowed-tools-policy.md) — per-skill tool allowlists
