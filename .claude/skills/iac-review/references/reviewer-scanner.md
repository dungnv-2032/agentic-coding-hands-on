# Scanner Backstop

Two static scanners — **checkov** and **`trivy config`** — normalized into `[SCANNER]` findings.

This leg proves coverage. The LLM reviewers carry repo-aware fixes; the scanner catches what they
miss. That is why an unmatched scanner finding always survives dedup, and why a *silently absent*
scanner is treated as a coverage gap rather than a clean result.

The line shape and parse rules are owned by
[`finding-format.md`](../../_shared/extras/iac/finding-format.md) — read it, do not restate it.

Both tools are **static**: they read `.tf` files, need no AWS credentials, and make no API calls.

## Running them

```bash
checkov -d "<TARGET>" --compact --quiet
trivy config "<TARGET>" --format json --misconfig-scanners=terraform --quiet
```

`<TARGET>` is the resolved review target. Quote it.

**Keep trivy's exit code 0 — do not add `--exit-code 1`.** A non-zero exit on findings aborts the
parent step, which turns "we found things" into "the review crashed".

checkov follows `module` calls into the referenced local modules, so a finding may cite a module file
with a `Calling File:` pointer back into the layer. **Report the resource address checkov gives**
(e.g. `module.alb_backend.aws_lb.this`), not the file path.

## Parsing `trivy config --format json`

A clean target emits `Misconfigurations: null` — the key is **absent**. Iterate the array **only when
present**; a null or absent `Misconfigurations` means no failing findings for that target. It is
**not** an error.

When present, walk `Results[].Misconfigurations[]` and keep **only** entries where `.Status ==
"FAIL"` — the literal string. Drop `PASS` and `EXCEPTION`.

### Field mapping

| trivy JSON field | use for |
|---|---|
| `.ID` | rule id, value form `AWS-NNNN` → build the ref by prepending the literal `AVD-` |
| `.Severity` | native severity — see the table below |
| `.Title` / `.Description` | `<short description>`, one clause |
| `.Resolution` | `<fix>`, trimmed to a clause |
| `.CauseMetadata.Resource` | `<resource-address>` — **falls back to the `.tf` path plus `.CauseMetadata.StartLine` when `Resource` is empty** |

The fallback is not optional. An entry with an empty `Resource` would otherwise produce an
address-less line, which fails the parse regex and is **silently discarded** — an invisible loss in
the one leg whose entire job is proving coverage.

Build the ref from `.ID` by **prepending the literal `AVD-`** → `(ref: trivy AVD-AWS-0031)`. The
value form is `AWS-NNNN`; there is no `AVD-` prefix in the field and no separate AVD-id field. Read
`.ID` only.

## Availability and errors

These two conditions are different and must not be collapsed.

| Condition | Line | HIGH loop |
|---|---|---|
| Tool **not installed** | `[MEDIUM][SCANNER] <tool> not installed → install per docs and re-run` | **excluded** |
| Tool **errored** — non-zero exit **and** stdout is not valid findings JSON (e.g. an invalid path → exit 1, empty stdout) | `[HIGH][SCANNER] <tool> invocation error — exit <N>, re-run manually` | included |

If one tool is absent, emit its line and **continue with the other**. Never abort.

Tool-absent lines go into the report's mandatory `## Coverage` section.

> **Deviation from upstream, intentional.** The source emits `[LOW][SCANNER]` for tool-absent and has
> no `## Coverage` section. At LOW a missing scanner sinks into the noise floor of the report, and
> the one thing a backstop must never do is disappear quietly. **Do not "correct" this back to LOW.**

**Never fabricate a passing scanner result.** A scanner that did not run has not passed.

## Normalization

Each scanner result becomes exactly one line:

```
[SEVERITY][SCANNER] <resource-address> — <short description> → <fix> (ref: checkov <CKV_ID>)
[SEVERITY][SCANNER] <resource-address> — <short description> → <fix> (ref: trivy AVD-AWS-NNNN)
```

- `<resource-address>` — the resource the tool cites.
- `<short description>` — one clause, the rule's intent ("no KMS encryption", "drops invalid headers not set").
- `<fix>` — the tool's own `Resolution` / guide text, trimmed to a clause.

### Severity — trivy

Use the tool's native `.Severity`. Never drop a finding; `UNKNOWN` floors to `LOW`.

| trivy native | normalized |
|---|---|
| CRITICAL | HIGH |
| HIGH | HIGH |
| MEDIUM | MEDIUM |
| LOW | LOW |
| UNKNOWN | LOW |

### Severity — checkov

The CLI emits no per-check severity, so map by **check family**, inferred from the check name or
description:

| checkov family (description keyword) | normalized |
|---|---|
| encryption (at-rest / KMS / SSE) · public-access · TLS / weak ciphers · IAM wildcard / least-privilege · secrets / hardcoded credentials | **HIGH** |
| logging / access-logging · versioning · drop-invalid-headers · deletion-protection · event notifications | **MEDIUM** |
| everything else (read-only filesystem, tag immutability hints, replication, lifecycle hygiene, misc) | **LOW** |

The HIGH families are the ones that, if missing, expose data or grant excess access — the same
conditions the security reviewer treats as release gates. MEDIUM is "fix before prod" hardening. LOW
is hygiene.

> **checkov and trivy may rate the SAME issue differently. That is expected, not a regression.**
> Each tool has its own severity model — checkov mapped by family, trivy native. ALB
> drop-invalid-headers is MEDIUM via checkov (headers family) and HIGH via trivy (native). Emit each
> tool's own normalized severity; the orchestrator's dedup keeps the richer finding when both
> describe the same `(resource, issue)`.

### Examples

```
[MEDIUM][SCANNER] module.alb_backend.aws_lb.this — ALB does not drop invalid HTTP headers → Set drop_invalid_header_fields = true (ref: checkov CKV_AWS_131)
[HIGH][SCANNER] module.s3_app_content.aws_s3_bucket.this — S3 bucket not encrypted with KMS (SSE-S3/AES256 only) → Set SSE config sse_algorithm = "aws:kms" (AWS-managed key suffices; CMK optional) (ref: checkov CKV_AWS_145)
[HIGH][SCANNER] module.alb_backend.aws_lb.this — ALB does not drop invalid headers → Set drop_invalid_header_fields = true (ref: trivy AVD-AWS-0052)
[MEDIUM][SCANNER] module.s3_app_content.aws_s3_bucket.this — bucket versioning disabled → Enable versioning (ref: trivy AVD-AWS-0090)
[LOW][SCANNER] module.ecr_backend_api.aws_ecr_repository.this — repository not encrypted using KMS → Use KMS encryption on the ECR repository (ref: trivy AVD-AWS-0033)
```

### Suppression directives are legitimate

A resource carrying a rationale comment plus an inline ignore directive (for example
`#trivy:ignore:AVD-AWS-0132` above an SSE resource, documenting an accepted AWS-managed-key stance)
is a **deliberate** suppression, not a miss. Honour it.

The suppression applies only where the directive is present. A resource without one — including a
deliberately-bad test fixture — still surfaces the finding.

## Rules

- Output **only** findings lines, plus any tool-absent informational line. No prose, no headers.
- One scanner result = one line. Do not merge two results.
- If neither tool produces a finding **and both are installed** → the single line `NO_FINDINGS`.
- Do **not** attempt repo-context reasoning — that is the LLM reviewers' job. Emit the tool's atomic
  finding, normalized, and let the orchestrator dedup.

## Catalog status

The scanner ships hundreds of CKV and AVD ids and is catalogued as a **producer**, not row by row.
Like the CIS/WAF reviewer, it is out of `rule-catalog.md` by design.
