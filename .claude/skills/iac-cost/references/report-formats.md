# Cost Report Formats

Three outputs, all **additive**. The COST VERIFY block and the promax HTML never replace or
restructure the two markdown reports.

| Output | Path | When |
|---|---|---|
| Per-layer report | `{ENV_DIR}/{layer}/cost-report.md` | always |
| Environment rollup | `{ENV_DIR}/cost-summary.md` | always |
| COST VERIFY block | stdout | always |
| Promax HTML | `{ENV_DIR}/cost-promax.html` | **opt-in only** — see [`promax-html.md`](./promax-html.md) |

`{ENV_DIR}` resolves through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

## Layer aggregation is the point

This is the capability base `tkm:infra cost` genuinely lacks: its estimator is **non-recursive** and
matches only `resource "aws_*"` blocks, never module calls. Pointed at an environment root it fails;
pointed at a layer that contains only module calls it returns **$0.00**.

So the rollup rule is not a formatting preference:

**`cost-summary.md` must aggregate every layer present** — including the cheap ones, including layers
whose resources are all module calls. A silently skipped layer understates the total, and an
understated total is the failure mode this skill exists to prevent.

If a layer cannot be priced, it appears in the summary with its reason. It never simply vanishes.

## `cost-report.md` — per layer

One per layer folder. Contains:

- a table of resources → monthly cost
- the layer subtotal
- On-Demand vs Reserved-1yr suggestions for steady-state compute in that layer
- **every usage assumption**, next to the figure it affects

Generic table, total and disclaimer conventions are base's; this skill does not restate them. What it
does require is the auditability: keep the per-resource lines, so any subtotal can be traced to the
rows that produced it.

## `cost-summary.md` — environment root

- per-layer subtotals → **environment total per month**
- cross-environment comparison, when sibling environments have cost data
- a "biggest line items" call-out

## COST VERIFY block — always printed

Printed to stdout **after** the markdown reports have been written. Never before — the block claims
the reports exist.

No prompt. This is the operator / infra-applier view, printed every run.

**ASCII only** beyond the leading `──`: no box-drawing, no emoji, so it survives plain terminals and
CI logs.

```
── COST VERIFY (apply-time check) ── <env> · <region> · source:<MCP|bulk|unavailable> · <date>
Layer            Monthly($)   Top driver
1.general        $XX.XX       NAT GW ×N
...
TOTAL/month      $XXX.XX
Biggest 3: <line> / <line> / <line>
Usage assumptions: S3=<GB>, CloudFront=<GB>, Lambda=<invocations>  (adjust + re-run)
Verify vs reality: after `terraform apply`, compare against AWS Cost Explorer / the Pricing Calculator for the same spec (target ±15%).
```

Fill the bracketed values from the **same aggregation that produced the reports** — a block that
disagrees with the files beside it is worse than no block. One row per layer, ascending. `source` is
the resolved pricing source. The date is the one the caller supplied; do not invent a timestamp.

This block is the bridge between the estimate and the deployed reality: it tells whoever runs
`terraform apply` what the bill should look like and how to confirm it.

## When pricing is unavailable

There is no third numeric state. If neither the MCP nor the bulk Price List resolved, the run
**cannot estimate** — see the failure contract in `SKILL.md`. Emit the structural report (resources,
quantities, specs, assumptions) with **no dollar figures at all**, and set the COST VERIFY block's
source field to `unavailable` with `TOTAL/month` reading `CANNOT ESTIMATE`.

Never fill a gap with a remembered price.

## Attribution

Every figure carries its source. An unattributed number is a defect, not a rounding issue — it is
indistinguishable from an invented one.

Where a single report mixes sources (MCP for most resources, bulk for one service), label the
exceptions inline rather than letting the header's single `source:` field imply uniformity.
