# CIS / Well-Architected Conformance Reviewer

**14 checks** — Part A (CIS posture: 3 HIGH · 2 MEDIUM) + Part B (WAF pillars: REL 3 · OPS 2 ·
SEC 2 · COST 2).

**Every check here is posture-level.** Nothing in this file is a per-resource atomic rule — those
belong to the scanner, and re-flagging one is the specific mistake this reviewer is written to
avoid.

A **vendored, static** checklist. Do **not** fetch live AWS or CIS documentation at review time — the
list below is the source of truth. Same discipline as the SRE reviewer.

Emit as `[SEVERITY][CIS]` or `[SEVERITY][WAF]`. The line shape and parse rules are owned by
[`finding-format.md`](../../_shared/extras/iac/finding-format.md) — read it, do not restate it.

## Never fabricate a control number

Do **not** invent precise CIS control numbers — no "CIS 2.1.1", no "CIS 4.3". Use only:

```
(ref: CIS-AWS — <topic>)
(ref: AWS-WAF <PILLAR> — <topic>)          PILLAR ∈ SEC | REL | COST | OPS
```

`<topic>` is a short human phrase, never a control ID. A fabricated control number is worse than no
reference: it survives review because it looks authoritative, and it sends the reader to a control
that says something else.

## What this reviewer does that the scanner cannot

The static scanner (checkov, `trivy config`) is excellent at **atomic, per-resource** rules: "this
one bucket lacks SSE", "this one SG opens `0.0.0.0/0`". This reviewer does the two things a
per-resource scanner structurally cannot:

1. **Architecture and topology conformance** — judgments spanning *multiple resources or tiers*. Is
   every tier multi-AZ? Is there centralized log aggregation across services? Is there
   defense-in-depth layering (edge WAF → ALB SG → app SG → DB SG)?
2. **Drift detection** — CIS/WAF expectations **not yet covered by any rule or scanner** in this kit,
   so the catalog and reviewers can be extended.

**Do not re-flag an atomic per-resource issue the scanner already catches.** If the scanner owns it
atomically, leave it there — the orchestrator's dedup keeps the richer finding anyway. Emit a
`[CIS]`/`[WAF]` finding only when the judgment is architecture-level, or a genuine gap.

---

## Part A — CIS AWS Foundations subset (Terraform-relevant)

Architecture-level CIS expectations detectable across `.tf`. Skip anything that is a single-resource
atomic check the scanner owns; focus on the cross-resource posture view.

Each check below is deliberately phrased as *inconsistency across a tier or class*, not as a
per-resource condition. If you can answer it by looking at one resource, it is the scanner's.

### HIGH

- **Storage encryption posture** — at-rest encryption is not applied *consistently across the data tier* (some of RDS / S3 / EBS / ElastiCache / OpenSearch encrypted, others not). Per-resource gaps belong to the scanner; the *inconsistency across the tier* is the CIS posture finding → Apply at-rest encryption uniformly across every data-bearing resource (ref: CIS-AWS — encryption at rest posture)
- **Network exposure posture** — public ingress paths reach private or data tiers without a controlled hop: no bastion, no edge layer in front of an internet-facing service → Front internet-facing services with a controlled edge; keep data tiers in private subnets (ref: CIS-AWS — network exposure)
- **IAM least-privilege posture** — broad or admin-style policies recur across multiple roles: an environment-wide wildcard pattern, not the single policy the scanner flags → Scope each role to least privilege; remove environment-wide wildcard grants (ref: CIS-AWS — IAM least-privilege)

### MEDIUM

- **Logging coverage** — audit or access logging is enabled on *some* services but missing on peers of the same class (one ALB logs, another does not) → Enable access/audit logging uniformly across the service class (ref: CIS-AWS — logging coverage)
- **CloudTrail / config posture** — the environment declares trails but they are not multi-region, or do not cover all layers consistently → Make trails multi-region and cover every layer (ref: CIS-AWS — trail coverage)

---

## Part B — AWS Well-Architected pillar checks

Cross-resource and topology judgments a per-resource scanner cannot make.

### REL — Reliability

- **HIGH** — A stateful or front-door tier (RDS, ElastiCache, ALB target group, ECS service) is **single-AZ** while the environment is multi-AZ elsewhere → Distribute the tier across ≥ 2 AZs (`multi_az`, or subnets in distinct AZs) (ref: AWS-WAF REL — multi-AZ across tiers)
- **MEDIUM** — Stateful resources (RDS, ElastiCache) have **no backup retention** configured (`backup_retention_period` absent or 0) → Set a backup retention window appropriate to the environment (ref: AWS-WAF REL — backup retention)
- **LOW** — No `prevent_destroy` lifecycle on production stateful resources → Add `lifecycle { prevent_destroy = true }` on prod stateful resources (ref: AWS-WAF REL — prevent_destroy)

### OPS — Operational Excellence

- **MEDIUM** — No centralized logging or retention strategy across the environment: log groups created ad hoc per service, no retention, no shared aggregation → Define centralized log destinations and `retention_in_days` on every log group (ref: AWS-WAF OPS — centralized logging/retention)
- **LOW** — No observability baseline (metric alarms, dashboards) on key tiers → Add CloudWatch alarms on the critical-path metrics of each tier (ref: AWS-WAF OPS — observability baseline)

### SEC — Security

- **HIGH** — No **defense-in-depth layering**: a single security boundary protects the whole environment (one flat SG, no tiered SG chaining edge → app → data) → Layer security groups by tier; reference peer SGs, not wide CIDRs (ref: AWS-WAF SEC — defense-in-depth layering)
- **MEDIUM** — Public edge (ALB, CloudFront) without a WAF *across the environment's public surface* — the posture view; the per-edge atomic check belongs to the scanner and the SRE reviewer → Associate a WAFv2 web ACL on every public edge (ref: AWS-WAF SEC — WAF on public edge)

### COST — Cost Optimization

- **MEDIUM** — **Environment-inappropriate sizing**: production-grade sizing (large instance classes, multi-AZ, high node counts) used in a non-prod environment across multiple resources → Right-size non-prod tiers; reserve prod sizing for prod (ref: AWS-WAF COST — env-appropriate sizing)
- **LOW** — No cost-allocation tagging strategy applied consistently across the environment → Apply consistent cost-allocation tags (Project, Environment, Owner) environment-wide (ref: AWS-WAF COST — cost allocation tags)

---

## False-positive guards

1. **TODO placeholders** — skip lines containing `# TODO` left by module generation.
2. **Cross-layer ownership** — before emitting a "missing X across tiers" finding, confirm X is not owned by another layer and referenced via `data.terraform_remote_state`. VPC, NACLs and flow logs live in the general layer; do not flag a consuming layer.
3. **Module-call arguments** — arguments inside `module "X" { … }` blocks are inputs, not resource definitions.
4. **Atomic overlap** — if the issue is a single-resource atomic rule checkov or trivy already emits, do **not** duplicate it as a `[CIS]`/`[WAF]` finding. Emit only the architecture-level or drift view.

## Not a dedup pair with the scanner

An architecture-level `[CIS]`/`[WAF]` finding ("no multi-AZ across the data tier") is **never** a
dedup of a scanner's atomic per-resource finding. The scopes differ. An unmatched `[CIS]`/`[WAF]`
finding always survives dedup — see
[`finding-format.md`](../../_shared/extras/iac/finding-format.md).

## Catalog status

These 14 checks are **not** rows in `rule-catalog.md`, by design — the catalog enumerates the four
rule-based reviewers. This reviewer is posture-level and is catalogued as a producer, not row by row.
A coverage assertion over the catalog must scope itself to the four catalogued reviewers, or it will
flag all 14 of these as orphans on day one.

---

## Output

Findings lines only, one per line. No findings → the single line `NO_FINDINGS`.
