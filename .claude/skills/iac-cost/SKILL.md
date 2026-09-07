---
name: tkm:iac-cost
description: >
  Quantitative monthly USD cost estimate for a whole multi-layer Terraform environment, priced through
  the AWS Pricing MCP. Aggregates per layer, selects the standard On-Demand SKU instead of Extended
  Support rows, charges Public IPv4 addresses, and compares On-Demand against Reserved 1-year.
  Produces cost-report.md per layer, cost-summary.md at the environment root, an on-screen COST VERIFY
  block, and an opt-in customer-facing HTML breakdown.
  Use this when asked how much an environment costs per month, to price a generated env before apply,
  to check a layer's spend, or to compare dev/stg/prod cost.
  Requires network access to a pricing source — it never guesses a price.
  SKIP: qualitative cost smells with no dollar figures (oversized instance, missing lifecycle rule)
  = [COST] findings (→ tkm:iac-review --only cost); pricing a single directory, or pricing with no
  network at all = (→ tkm:infra cost, whose heuristic fallback works offline).
category: iac
roles: [engineer, devops]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Bash
  - mcp__awslabs.aws-pricing-mcp-server__get_pricing
  - mcp__awslabs.aws-pricing-mcp-server__get_pricing_service_codes
  - mcp__awslabs.aws-pricing-mcp-server__get_pricing_service_attributes
  - mcp__awslabs.aws-pricing-mcp-server__get_pricing_attribute_values
  - mcp__awslabs.aws-pricing-mcp-server__get_price_list_urls
argument-hint: "<env> [--promax]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: deployment-infrastructure
triggers:
  - "estimate cost"
  - "monthly cost"
  - "how much does this env cost"
  - "AWS cost estimate"
  - "cost per layer"
  - "terraform cost"
  - "reserved instance saving"
  - "chi phí hạ tầng"
---

# tkm:iac-cost

Reads `.tf` files and `terraform.<env>.tfvars`, resolves each cost driver to a concrete value, prices
it against public AWS pricing, and rolls the result up **per layer** to an environment total.

Read-only against AWS: it never touches the deployed account, never reads state, and needs no deploy
credentials. Pricing is public data.

## What this skill is for

Four capabilities, chosen because base `tkm:infra cost` genuinely lacks each one:

| Capability | Why it is here |
|---|---|
| **Layer aggregation** | Base's estimator is non-recursive and matches only `resource "aws_*"`. On a layer built from module calls it returns **$0.00**; on an environment root it fails outright. |
| **SKU / usagetype precision** | A single resource type returns several pricing rows. Picking an Extended Support row over-states by ~60%. |
| **Public IPv4 charging** | $3.65/IP/month, billable since 2024-02-01, undeclared by Terraform. `aws_eip` is absent from base's heuristic table, so base's offline path prices it at zero. |
| **Reserved 1-year** | On-Demand vs RI delta on steady-state compute. |

Generic per-resource table, total and disclaimer conventions belong to base and are not restated
here.

## Not this skill

- **`tkm:iac-review --only cost`** is the *qualitative* sibling: `[COST]` findings, no dollar
  figures. Two different questions — "is this wasteful?" versus "what will it cost?"
- **`tkm:infra cost`** prices a **single directory**, and its heuristic fallback is the only cost
  path in either kit that works with **no network**. That is the right tool offline. This skill has
  no offline mode by design (see below).

Running both on the same environment will produce two different numbers. That is expected: they
measure different scopes with different engines.

## Pricing sources — and the refusal

Resolve in order. **Never proceed past the last step with a number.**

| # | Source | Notes |
|---|---|---|
| 1 | **AWS Pricing MCP** — `awslabs.aws-pricing-mcp-server` | Calls the Price List Query API. Public pricing, so any ambient credential works — and none is required. Setup, granted tools and the availability check: [`iac-mcp-connection.md`](../_shared/extras/iac/iac-mcp-connection.md). |
| 2 | **Public bulk Price List** | `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/` — served over HTTPS **without auth**. Use the per-service offer file for the resource's service code. |
| 3 | **Cannot estimate** | Emit the structural report — resources, quantities, specs, assumptions — with **no dollar figures**, and `TOTAL/month: CANNOT ESTIMATE`. |

The user registers the server once; this skill never installs or launches it. If it is absent, say so
and continue on source 2 — do not treat a missing registration as an error.

> **This skill never prices from memory.** If both sources fail it says so and stops pricing. A
> plausible-looking wrong number is worse than no number: nobody re-checks a figure that looks
> reasonable, and an infrastructure estimate is acted on. Offline users have a working alternative in
> `tkm:infra cost` — a refusal here costs them a command, not an answer.

> **Intentional deviation from upstream.** The source's third state was softer: emit the report with
> `price: unavailable` per resource "rather than failing"
> (`skills/aidd-cost-estimator/SKILL.md:30-31`). This kit drops every dollar figure and states
> `CANNOT ESTIMATE` instead, so a partially-priced report cannot be mistaken for a total. **Do not
> soften this back when syncing against the source.**

"Fails loudly" means the refusal is unmissable in the output — not that the command exits non-zero.
Cost never blocks (see Rules).

State the resolved source in every output. An unattributed figure is a defect.

### Two region keys

`DEFAULT_REGION` is the region being **priced** — read `region` from `terraform.<env>.tfvars`, or
fall back to the contract default.

`PRICING_API_REGION` (`us-east-1`) is the Price List **API endpoint**, and is **not
user-overridable**. The MCP config's `AWS_REGION` is that endpoint. Never parameterize it to
`DEFAULT_REGION` "for consistency" — the API is not available in `ap-northeast-1`, so doing that
drops the run onto the fallback path, or off the end of it.

Both resolve through
[`layout-contract.md`](../_shared/extras/iac/layout-contract.md).

## Steps

1. **Resolve the environment.** `{ENV_DIR}` must exist with at least one layer folder and a
   `terraform.<env>.tfvars`. Resolve `region`.
2. **Resolve the pricing source** per the availability check in
   [`iac-mcp-connection.md`](../_shared/extras/iac/iac-mcp-connection.md), and print which one won —
   before estimating, not after.
3. **Enumerate every layer.** Every one — including layers whose resources are all module calls.
4. **Extract specs and quantities** per resource, following `var.*` → tfvars → module defaults.
5. **Price each resource**, region-correct, applying usagetype precision and the Public IPv4 rule.
   → [`resource-price-mapping.md`](./references/resource-price-mapping.md)
6. **Aggregate** resource → layer → environment/month.
7. **On-Demand vs Reserved 1-year** for steady-state compute; recommend when the saving is ≥ ~20%.
8. **Cross-environment comparison** when siblings have cost data; flag unusual deltas.
9. **Write the reports**, then print the COST VERIFY block — in that order.
   → [`report-formats.md`](./references/report-formats.md)
10. **Promax HTML only on `--promax`.** → [`promax-html.md`](./references/promax-html.md)

## Rules

- **Cost never blocks.** No verdict, no gate, no exit code that fails a pipeline. An advisory number
  that halts a deploy is a bug.
- **Never write `review-report.md`.** This skill owns exactly three artifacts — `cost-report.md`,
  `cost-summary.md`, `cost-promax.html`. `review-report.md` belongs to `tkm:iac-review`, which merges
  the *qualitative* `[COST]` findings from its own cost leg into it; the dollar figures here are a
  different artifact from a different producer. The failure this prevents is concrete: `allowed-tools`
  grants `Write` and not `Edit`, so "merging" into a file this skill does not own means overwriting
  it — the review's findings and its `## Coverage` record vanish, and what remains still looks like a
  complete report.
- **Never invent a price.** Query a source or report `CANNOT ESTIMATE`.
- **Never select an Extended Support or other non-standard SKU** when pricing the On-Demand baseline.
- **Always charge Public IPv4** for NAT gateways, internet-facing load balancers (per AZ subnet), and
  EIPs / public instances. Forgetting it understates internet-facing environments.
- **Pin every usage assumption** beside the figure it affects. S3, CloudFront, Lambda and NAT data
  processing depend on traffic Terraform does not declare.
- **Read-only.** Never modify `.tf`, never run `plan` or `apply`, never touch state.
- **Never fabricate a timestamp** — use the date the caller supplied.
- **`--promax` is opt-in.** Without the flag, write no HTML.

## Permitted shell commands

`Bash` is listed for **one** purpose: fetching the public bulk Price List over HTTPS when the MCP is
unavailable.

```
curl … https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/…   # bulk fallback, no auth
```

**Never launch the MCP server from `Bash`.** It is a stdio server started by the MCP *client* from
`.mcp.json`; shelling it out yourself produces a process blocked on stdin, no tools, and a false
"MCP unreachable" verdict that silently demotes every run to the fallback. Registration is the
user's, once — see
[`iac-mcp-connection.md`](../_shared/extras/iac/iac-mcp-connection.md).

Anything else is a defect in this skill, not a judgement call at runtime. In particular: no
`terraform` command of any kind, and no `aws` CLI call — this skill never touches the deployed
account. See [`allowed-tools-policy.md`](../_shared/extras/iac/allowed-tools-policy.md).
