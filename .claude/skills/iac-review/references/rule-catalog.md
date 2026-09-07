# Rule Catalog — `tkm:iac-review`

**105 rules across four catalogued reviewers**, plus two producers documented by role rather than
row by row.

| Reviewer | Rules | File |
|---|---|---|
| security | **37** | [`reviewer-security.md`](./reviewer-security.md) |
| bestpractice | **29** | [`reviewer-bestpractice.md`](./reviewer-bestpractice.md) |
| sre | **25** | [`reviewer-sre.md`](./reviewer-sre.md) |
| cost | **14** | [`reviewer-cost.md`](./reviewer-cost.md) |
| **total** | **105** | |
| cis-waf | 14 checks — **producer**, not catalogued | [`reviewer-cis-waf.md`](./reviewer-cis-waf.md) |
| scanner | hundreds of CKV/AVD ids — **producer**, not catalogued | [`reviewer-scanner.md`](./reviewer-scanner.md) |

## This file is an index. The checklists are authoritative.

The canonical rule text and its `(ref: …)` source tag live in each `reviewer-*.md`. This table exists
for overlap and gap spotting.

**When a rule changes, change the checklist, then update this index.** That ordering matters: the
upstream kit had the same two-artifact split, and its index drifted — a live bestpractice rule
(multi-instance module discriminator) existed in the reviewer with no catalog row and no entry in the
dispatch summary either. It was still enforced at runtime, because the *checklist* is what reaches
the reviewing subagent. That is the failure mode this note exists to prevent, and it is why the
count above is 105 rather than the upstream index's 104.

The derivation is mechanical, and re-runnable:

```bash
grep -cE '^\s*-\s.*→' references/reviewer-{security,bestpractice,sre,cost}.md
```

Every rule is a bullet stating `condition → fix`. Headings and prose carry no arrow.

> **There is no rule ID to join on.** A deterministic catalog-versus-checklist coverage assertion is
> therefore impossible, and none is claimed. The count above is the only mechanical control; rule
> *content* fidelity is a known verification gap, not a covered one.

## Counts by severity

| Reviewer | HIGH | MEDIUM | LOW | Structure |
|---|---|---|---|---|
| security | 12 + full-env | 7 + full-env | 3 | 22 per-folder + 15 full-env |
| bestpractice | 9 + full-env | 9 + full-env | 4 + full-env | 22 per-folder + 7 full-env |
| sre | 10 | 7 | 8 | flat, each numbered `No.X` |
| cost | 4 | 6 | 4 | flat |

Security's full-env 15: network topology 4 · encryption 5 · IAM 3 · cross-layer 3.

## Source taxonomy

Carried over verbatim in every `(ref: …)` tag:

| Tag | Meaning |
|---|---|
| `CIS-AWS` | CIS AWS Foundations Benchmark — topic form only, never a control number |
| `AWS-WAF <SEC\|COST\|REL\|OPS>` | AWS Well-Architected pillar |
| `HashiCorp TF-style` | HashiCorp Terraform style guide |
| `checklist No.X` | Sun\* AWS Security Checklist — the SRE reviewer's source |
| `repo <policy>` | This kit's own conventions — naming, tagging, path-header, secrets, module-sourcing |
| `backend rules` | The S3 backend contract |

**Repointed anchor.** Upstream, six or more rows cited `repo STANDARDS#backend`, an anchor that did
not exist — the referenced file had exactly one section, about encryption at rest. Those rows now
cite **`backend rules`**, whose authority is the canonical backend block in
`iac-generate-module/references/env-service-contract.md` — the single file repo-wide that emits it.
The rule text also carries the full condition and fix, so no rule depends on the pointer to be
actionable.

## Deliberate cross-reviewer overlaps

These are intentional. Losing one looks like deduplication working; it is coverage loss.

| Pair | Behaviour |
|---|---|
| No.33 SG `0.0.0.0/0` — sre HIGH ↔ security HIGH | **dedup pair** — `[SECURITY]` wins |
| No.56 literal secret — sre HIGH ↔ security HIGH ↔ bestpractice MEDIUM | **dedup pair** — `[SECURITY]` wins |
| **No.44 public ALB/CloudFront WAF — sre HIGH ↔ security MEDIUM** | **NOT a dedup pair — both surface.** The SRE HIGH enters the fix loop |
| No.54 VPC flow log — sre MEDIUM ↔ security MEDIUM | same condition, severities agree |
| No.18 S3 SSE — sre LOW ↔ security full-env HIGH | severity differs deliberately |
| No.19 EBS CMK — sre LOW ↔ security full-env MEDIUM | severity differs deliberately |
| No.21 Redis at-rest — sre LOW ↔ security full-env HIGH | severity differs deliberately |
| sensitive **output** (security) ↔ sensitive **variable** (bestpractice) | different objects — not a duplicate |
| log-group `retention_in_days` — security MEDIUM (ops) ↔ cost MEDIUM (spend) | same argument, two angles |
| architecture-level `[CIS]`/`[WAF]` ↔ atomic `[SCANNER]` | **never** a dedup pair |

Also overlapping with security by design: SRE items **No.24, 28, 33, 38, 56**. The SRE reviewer emits
them independently under `[SRE]`; dedup resolves them.

## Why cis-waf and scanner are out of the catalog

They are producers, not rule sets:

- **cis-waf** — 14 posture-level checks. Architecture and drift judgments, not atomic rules.
- **scanner** — checkov plus `trivy config`, hundreds of ids, mapped by severity family rather than
  enumerated.

**Any coverage assertion must scope itself to the four catalogued reviewers.** Asserting
bidirectional coverage across all six would flag every cis-waf check and every scanner id as an
orphan on day one.

## Conflicts with the base kit

`tkm:infra`'s rule set disagrees with this one on nine rules, in both directions, and base *generates*
Terraform that this reviewer flags HIGH. AIDD severities win inside `tkm:iac-review`. See
[`conflicts-with-base.md`](./conflicts-with-base.md).
