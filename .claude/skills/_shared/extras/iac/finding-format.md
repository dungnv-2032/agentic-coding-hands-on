# IaC Reviewer Finding Format

**This file is the sole owner of the finding line and its parse regex.**

No other file in this repository may restate the regex — not a skill, not a reference, not an agent
prompt. Point at this file instead. The upstream kit shipped the regex in **seven** places and one
had already drifted (`agents/reviewer-sre.md:95` omits `SCANNER|CIS|WAF`, so an SRE reviewer reading
that copy would silently drop three categories). Duplication is what caused that; do not reproduce
it.

## The finding line

One finding per line. Nothing else in the file.

```
[SEVERITY][CATEGORY] Description → Suggested fix
```

With the optional source reference:

```
[SEVERITY][CATEGORY] Description → Suggested fix (ref: <source>)
```

| Field | Values |
|---|---|
| `SEVERITY` | `HIGH`, `MEDIUM`, `LOW` — uppercase, no spaces |
| `CATEGORY` | `SECURITY`, `COST`, `BESTPRACTICE`, `SRE`, `SCANNER`, `CIS`, `WAF` — uppercase, no spaces |
| Description | Concise; names the specific resource address or attribute |
| `→` | The literal arrow character `→`, separating description from fix |
| `(ref: …)` | Optional, trailing. Available to **any** producer, not SRE-only |

Severity assignment:

- `HIGH` — security risk or state-management failure; **blocks deployment**
- `MEDIUM` — quality issue that should be fixed before production
- `LOW` — style, optimization, or missing-but-not-critical attribute

### `ref` forms per producer

| Producer | Form |
|---|---|
| SRE | `(ref: checklist No.X)` |
| scanner | `(ref: checkov CKV_AWS_145)` / `(ref: trivy AVD-AWS-0132)` |
| cis-waf | `(ref: CIS-AWS — <topic>)` / `(ref: AWS-WAF <PILLAR> — <topic>)`, `PILLAR ∈ SEC/REL/COST/OPS` |
| security / bestpractice / cost | Their Part A source tags: `CIS-AWS`, `AWS-WAF <PILLAR>`, `repo <file>`, `HashiCorp TF-style` |

**cis-waf must never fabricate a CIS control number.** Use `(ref: CIS-AWS — <topic>)` only. A
plausible-looking but invented control number is worse than no reference.

### Examples

```
[HIGH][SECURITY] aws_security_group.web allows ingress 0.0.0.0/0 on port 22 → Restrict to VPN CIDR or remove SSH rule
[HIGH][BESTPRACTICE] No S3 backend configured — using local state → Add S3 backend block with use_lockfile = true (S3-native locking)
[MEDIUM][COST] aws_db_instance.main uses db.r6g.2xlarge in staging → Downsize to db.r6g.large for non-production
[LOW][SRE] aws_kms_key.app missing enable_key_rotation = true → Set enable_key_rotation = true (ref: checklist No.17)
[HIGH][WAF] RDS data tier runs single-AZ while app tier spans 2 AZs → Set multi_az = true (or place subnets across ≥ 2 AZs) (ref: AWS-WAF REL — multi-AZ across tiers)
[MEDIUM][CIS] access logging enabled on one ALB but missing on its peer ALB → Enable access_logs uniformly across the service class (ref: CIS-AWS — logging coverage)
```

## Output rules

- Output **only** finding lines. No prose, no headers, no markdown, no summary.
- One issue = one line. Never combine two issues into one finding.
- **No findings → the single line `NO_FINDINGS`.** Nothing else.
- A finding line that does not match the parse regex is silently ignored by the orchestrator, so a
  malformed line is an invisible loss, not an error. Emit the exact shape.

## Parse regex

The orchestrator scans findings files for lines matching:

```
^\[(HIGH|MEDIUM|LOW)\]\[(SECURITY|COST|BESTPRACTICE|SRE|SCANNER|CIS|WAF)\]
```

Any line not matching is ignored.

> The plan's invariants section lists the same alternation in a different order
> (`SECURITY|BESTPRACTICE|SRE|COST|…`). Alternation order does not affect matching; the form above is
> the upstream literal and is the one to use.

## Missing or malformed findings file is a hard ERROR

For **every leg the current invocation dispatched**, a findings file that is **missing**, **empty
(zero bytes)**, or **malformed** (contains neither `NO_FINDINGS` nor at least one regex-matching
line) is a **hard ERROR**. Stop and report it.

The rule is scoped to legs that actually ran. A single-leg invocation leaves the other legs' files
absent, and that is not an error — it is the shape of the request. Applying the rule to all six
regardless would make every single-leg mode abort before parsing anything.

It is **never** an empty finding set. Treating a crashed reviewer as "clean" is how a review pipeline
reports green while having reviewed nothing. `NO_FINDINGS` is the only way a reviewer says "clean",
and it must be written explicitly.

> **Intentional addition.** Upstream states no behaviour for a missing or malformed findings file —
> the orchestrator simply finds no matching lines and proceeds as if clean. This kit makes it a hard
> ERROR. Do not remove it when transcribing.

## Scanner availability

The static scanners (checkov, `trivy config`) are the backstop that proves coverage. Their absence
is a coverage gap and must be visible, not buried.

| Condition | Line | Loop |
|---|---|---|
| Tool **not installed** | `[MEDIUM][SCANNER] <tool> not installed → install per docs and re-run` | **Excluded** from the HIGH loop |
| Tool **errored** (non-zero exit, non-JSON stdout) | `[HIGH][SCANNER] <tool> invocation error — exit <N>, re-run manually` | Enters the HIGH loop |

Tool-absent lines are written to a **mandatory `## Coverage` section** in the review report. The
section is emitted on every run — when both scanners ran, it records that fact. A report with no
`## Coverage` section is incomplete.

`trivy config` returns **exit 0** even when it finds misconfigurations. Do not add `--exit-code 1`;
a non-zero exit would abort the parent step. A clean target emits `Misconfigurations: null` — that
is "no failing findings", not an error.

> **Intentional deviation from upstream.** The source emits `[LOW][SCANNER]` for tool-absent
> (`agents/reviewer-scanner.md:47-48`, `skills/aidd-reviewer-scanner/SKILL.md:100-101`) and has no
> `## Coverage` section anywhere. Both changes above are deliberate: at `LOW` a missing scanner sinks
> into the noise floor of a report, and the one thing a backstop must never do is disappear quietly.
> **Do not "correct" this back to `LOW` when transcribing rules from the source.**

## Producer dedup

Five producers can describe the same issue. The SRE reviewer re-emits some security findings; the
static scanner re-proves atomic per-resource conditions the LLM reviewers also flag; cis-waf may echo
a posture-level view of the same topic.

When two findings from **different producers** describe the same `(resource_address, issue topic)`,
keep exactly **one**, by this priority — the kept producer wins:

```
[SECURITY]  >  [SRE]  >  [CIS] / [WAF]  >  [SCANNER]
```

LLM reviewers carry repo-aware fixes (SOPS key names, exact module arguments, repo naming) that are
richer than generic scanner text, so they win.

**Dedup key is `(resource_address, issue topic)` — never exact string.** Producers phrase fixes
differently. "S3 bucket X has no SSE" from `[SECURITY]` and "module…aws_s3_bucket.this — not
encrypted with KMS (ref: checkov CKV_AWS_145)" from `[SCANNER]` are the same issue: keep
`[SECURITY]`, drop `[SCANNER]`.

### An unmatched scanner or cis-waf finding always survives

A `[SCANNER]` or `[CIS]`/`[WAF]` finding with **no** LLM match is never dropped. That is the entire
backstop value — it caught something the LLM reviewers missed. Dropping it converts a coverage gap
into a clean report.

### Not dedup pairs

- **No.44 WAF.** The SRE reviewer rates a public ALB/CloudFront without WAFv2 as `HIGH`; security
  rates it `MEDIUM`. The fix emphasis differs, so **both surface**, and the SRE `HIGH` enters the
  loop.
- **Architecture vs atomic.** A `[CIS]`/`[WAF]` architecture-level finding ("no multi-AZ across the
  data tier") is not a dedup of a scanner's atomic per-resource finding. The scopes differ.

## Conflict resolution

- A `[SECURITY]` finding beats a `[BESTPRACTICE]` finding when the two conflict.
- Two findings in the same category that conflict: the stricter one wins.
- Neither clearly stricter: include both and flag for human decision.

## Cost never blocks

`[COST]` findings are informational. They are merged into the report and **never** participate in
the HIGH loop, at any severity.

## Loop counting

HIGH findings from `[SECURITY]`, `[BESTPRACTICE]`, `[SRE]`, `[SCANNER]`, `[CIS]` and `[WAF]` each
count individually **after** dedup. The loop continues until all of them report zero HIGH findings,
or the cap is reached.

> **Resolves an upstream inconsistency.** The source's loop-counting sentence
> (`skills/aidd-orchestrator/SKILL.md:157-159`) omits `[BESTPRACTICE]`, but two other places include
> it explicitly — the same file's step-2 heading (`:53`, *"If any HIGH finding exists (security,
> **bestpractice**, sre, scanner, or cis-waf)"*) and `commands/review-iac.md:64` (*"join the same loop
> as security + **bestpractice**"*). Two to one, and the semantics settle it: bestpractice HIGH rules
> are the "blocks or corrupts state" class — local state, missing `use_lockfile`, a state-key
> collision between layers. Excluding them would report those and never fix them.

Two counters, always independent — never collapse them into one:

| Counter | File | Cap |
|---|---|---|
| Review loop | `{WORK_DIR}/loop-count.txt` | **3** |
| Inline generation gate | `{WORK_DIR}/inline-loop-count.txt` | **2** |

`{WORK_DIR}` resolves through [`layout-contract.md`](./layout-contract.md).

**Reset is step 0** — executed once per invocation, **outside** the loop. The loop body re-enters at
step 1. `{WORK_DIR}` is gitignored, so a stale counter from a previous run persists on disk; if it
held `3`, the first iteration would escalate after **zero** fix attempts.

Each counter has its **own** escalation line. Emit verbatim; they are not interchangeable.

Review loop:

```
ESCALATION: Unresolved HIGH findings after 3 iterations.
```

Inline generation gate — carries the count **and** the location:

```
ESCALATION: Unresolved HIGH findings after 2 iterations in <env>/<target_folder>.
```

> **Reset applies to both.** Upstream, the inline gate held its counter in memory
> (`agents/validate-inline.md:43`), so it could not go stale. This kit persists it to
> `{WORK_DIR}/inline-loop-count.txt` for parity with the review loop — which means the inline gate
> now needs the same **step 0** reset, outside its loop. Skipping it reproduces the stale-counter
> bug on a path that never had it.

## Related contracts

- [`layout-contract.md`](./layout-contract.md) — `WORK_DIR` and all other paths
- [`idempotency-matchers.md`](./idempotency-matchers.md) — re-run guards
- [`allowed-tools-policy.md`](./allowed-tools-policy.md) — per-skill tool allowlists
