---
name: tkm:iac-review
description: >
  Review a whole multi-layer Terraform environment with five reviewers running in parallel — security,
  best practice, SRE, static scanner (checkov + trivy), and CIS/Well-Architected conformance — then an
  orchestrator that deduplicates their findings, auto-fixes HIGH issues in up to three rounds, and
  writes a report or escalates.
  105 rules across four catalogued reviewers, plus a static-scanner backstop and posture-level checks.
  Use this to review generated Terraform before apply, to check an environment against the Sun* SRE
  checklist, or to run a security or cost pass over infrastructure code.
  SKIP: ad-hoc review of a single Terraform directory with the base rule set (→ tkm:infra);
  application source code rather than infrastructure (→ tkm:review-code);
  converting spec-kit or SDD documents into Takumi format, which also triggers on the word "AIDD"
  (→ tkm:migrate-aidd); dollar-figure cost estimates rather than cost smells (→ tkm:iac-cost).
category: iac
roles: [engineer, devops]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Task
  - Bash
argument-hint: "<env> [--only <reviewer>] [--full] [--scope <layer>] [--approve]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: deployment-infrastructure
triggers:
  - "review terraform"
  - "review IaC"
  - "review infrastructure code"
  - "security review terraform"
  - "SRE checklist review"
  - "checkov"
  - "trivy config"
  - "CIS review AWS"
  - "review env before apply"
  - "review hạ tầng"
---

# tkm:iac-review

Five reviewers, one orchestrator, a HIGH fix loop capped at three rounds.

Rules live in `references/`. One leg reads one checklist. The finding contract —
line shape, parse regex, dedup priority, counters — is owned by
[`finding-format.md`](../_shared/extras/iac/finding-format.md) and is **never** restated
in this skill or any checklist.

| Argument | Effect |
|---|---|
| `<env>` | Required. The environment to review. |
| `--scope <layer>` | Review one layer instead of the whole environment. |
| `--only <reviewer>` | Run one leg: `security`, `bestpractice`, `sre`, `cost`, `scanner`, `cis-waf`. |
| `--full` | `terraform plan` per layer → the five-leg review → hand off to `tkm:iac-cost`. |
| `--approve` | Gate every fix on human approval. **Defaults on for production-like environments.** |
| `--report-only` | Collect, dedup and report findings. Apply no fix, run no loop, never prompt. |

## Validate arguments before they reach a shell

`<env>` and `--scope <layer>` are interpolated into paths and into shell commands. Constrain **both**
to `^[A-Za-z0-9._-]+$` and reject anything else before use.

`--only` must be one of the six literal names above. Resolve the target, then verify it exists and
contains `.tf` files before dispatching anything.

## Step 1 — Dispatch five legs in ONE message

> **`--only <reviewer>` does not fan out.** A single leg has nothing to parallelize: read that one
> checklist and review directly, in this turn, with no `Task` dispatch. This is what lets a
> generation flow call `--only security` from inside its own turn — dispatching a subagent there
> would end the caller's turn and stall the pipeline. The rest of this section is the full-run path.

Five `Task` calls **in a single message**, awaited. Blocking. No background flag.

If the calls go out one at a time, the fan-out silently becomes sequential; if they go out
non-blocking, the orchestrator reads findings files that **do not exist yet** — and because every
non-matching line is discarded by contract, a review that found ten HIGH issues emits a clean report.
The failure is invisible in the output. That is why this is a hard rule rather than a preference.

Each leg gets a **kit-anchored** path. A subagent's working directory is the user's Terraform
project, not this skill's directory, so a bare relative path resolves to nothing.

**Resolve the kit root first, then anchor to it.** The paths below are written against a
project-local install (`<project>/.claude/skills/…`). A global install puts the same tree at
`~/.claude/skills/…`, and a kit installed in a subdirectory puts it somewhere else again — so a
literal `.claude/…` string is right in the common case and wrong in the others. Pass whichever root
actually holds this skill; the leg cannot search for it, because its cwd is the wrong tree entirely.

```
Task(subagent_type="general-purpose",
     prompt="Read .claude/skills/iac-review/references/reviewer-security.md and
             .claude/skills/_shared/extras/iac/finding-format.md.
             Review TARGET=<resolved target>.
             Write findings to <WORK_DIR>/findings-security.txt.
             Output findings only. Empty result = the single line NO_FINDINGS.")
```

| Leg | Checklist | Output |
|---|---|---|
| A — security | `references/reviewer-security.md` | `{WORK_DIR}/findings-security.txt` |
| B — bestpractice | `references/reviewer-bestpractice.md` | `{WORK_DIR}/findings-bestpractice.txt` |
| C — sre | `references/reviewer-sre.md` | `{WORK_DIR}/findings-sre.txt` |
| D — scanner | `references/reviewer-scanner.md` | `{WORK_DIR}/findings-scanner.txt` |
| E — cis-waf | `references/reviewer-cis-waf.md` | `{WORK_DIR}/findings-cis-waf.txt` |

Reviewing a **whole environment** (no `--scope`) also runs the full-env checks in the security and
bestpractice checklists — the cross-layer ones a single-folder pass cannot see.

### The target is the environment **and** the modules it calls

`{ENV_DIR}` holds module *calls*. `{MODULE_DIR}` is its **sibling**, not a child, and it holds the
module bodies — where the SSE blocks, `moved` blocks, discriminator tags and `count`-gated hardening
actually live. Resolve `TARGET` to both:

```
{ENV_DIR}                 # or {ENV_DIR}/<layer> under --scope
{MODULE_DIR}              # always — the modules that env calls
```

Every leg reads both. A review scoped to `{ENV_DIR}` alone reports clean on an environment whose
buckets have no encryption and whose IAM policies are wide open, because none of that is written in
the env folder. Measured on a generated environment: **roughly 60% of all findings came from the
module bodies.** Reviewing only the calls means missing most of what there is to find, and reporting
a pass while doing it.

Under `--scope <layer>`, still pass all of `{MODULE_DIR}` — a layer's correctness depends on the
modules it calls, and there is no cheap way to know which subset that is.

**Agent type is `general-purpose`.** Not the base kit's reviewer agent: that one carries its own
review protocol, which conflicts with this finding contract, and `general-purpose` exists whether or
not the base kit is installed.

## Step 2 — Orchestrate

Follow [`orchestrator-protocol.md`](./references/orchestrator-protocol.md) exactly: reset the counter
at step 0 outside the loop, parse, dedup, loop on HIGH up to 3, then report or escalate.

## `--full`

Three legs, in order. Report every leg's status in the summary, including skipped ones.

1. **Plan each layer**, ascending. Prefer `make plan e=<env> s=<layer>` from `{MAKE_ROOT}` when a
   Makefile is there — it carries the project's own init and backend wiring; fall back to
   `terraform plan` in the layer directory otherwise. Do not hardcode layer names: a real environment
   may use `2.admin` where a blueprint produced `2.frontend`.
   **Degrade gracefully:** with no AWS credentials or an un-bootstrapped state backend, plan fails.
   Record the layer as `plan: skipped (no credentials / backend not bootstrapped)` and **continue**.
   The static review needs no credentials and still runs.
2. **The five-leg review**, as above.
3. **Cost.** `**IMPORTANT:** Invoke "/tkm:iac-cost" for <env>.`

> **If `tkm:iac-cost` is unavailable, say so in `review-report.md` and stop the cost leg there.**
> Never fall through to base `tkm:infra cost`: it prices a *single directory* with a different
> engine, and a user reading a full-environment report would take a single-layer number as the
> environment total. An absent number is recoverable; a wrong one presented as the total is not.

Cost **never blocks**, at any severity.

What merges into `review-report.md` is the `[COST]` findings from *this* skill's own cost leg —
qualitative smells, no dollar figures. `tkm:iac-cost` writes its own reports and never touches
`review-report.md`.

## `--approve`

Findings are always collected and always counted. Approval gates only the **write**.

Defaults **on** when the environment name looks production-like: it contains `prod`, or matches
`live`, `prd`, `pd`, or `main`. Otherwise off, and settable either way.

The match is deliberately loose. A false positive costs one approval prompt; a false negative runs
three rounds of unreviewed automated edits against production infrastructure. When a name is
ambiguous, treat it as production.

This is the compensating control for auto-fix: up to three rounds of automated `.tf` edits run with
`allowed-tools` as the only boundary, with no harness-level command deny-list underneath. See
[`allowed-tools-policy.md`](../_shared/extras/iac/allowed-tools-policy.md).

## `--report-only`

Steps 0–2 and 4–5 run normally. Step 3 is replaced: report the HIGH findings and stop. No fix, no
loop counter, no `.tf` write, and **no approval prompt** — with nothing to write, there is nothing to
gate, so `--approve` is inert and must not stall.

This exists for a caller that does its own fixing. The inline validation gate in
`tkm:iac-connect-modules` is one: it holds its own fix loop with its own cap, and it can run inside a
single-turn environment generation. Without this mode that call would either produce two writers on
one file set with no coordination, or — for any environment whose name looks production-like, where
`--approve` defaults on — sit waiting for a human while the generation turn ends around it, leaving
the environment half-wired.

## Rules

- **One message, five calls, blocking.** Never sequential, never backgrounded.
- **Every leg prompt anchors its checklist path to the resolved kit root.** Never a bare relative
  path, and never assume the root is project-local.
- **A missing, empty, or malformed findings file is a hard ERROR** — never an empty finding set.
- **Loop reset is step 0**, once per invocation, outside the loop. The loop re-enters at step 1.
- **This loop's counter is `{WORK_DIR}/loop-count.txt`, cap 3.** The inline generation gate uses a
  different file with a different cap.
- **Cost never blocks**, at any severity.
- **Missing checkov or trivy → `[MEDIUM][SCANNER]`**, excluded from the HIGH loop, recorded in
  `## Coverage`. Never fabricate a passing scanner result.
- **Never fabricate a CIS control number.** Topic form only.
- **Never `terraform apply`, `destroy`, `import`, `state rm`**, or `make apply|destroy|state_rm`. A
  finding is fixed by editing configuration, never by mutating deployed state.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "I'll review the legs one at a time." | One message. Five calls. Blocking. |
| "The findings file is missing, so that leg found nothing." | It is a hard ERROR. A crashed leg is not a clean leg. |
| "I'll background them and read the files after." | The files will not exist. The report will look clean. |
| "Reset the counter at the top of each loop." | Step 0 runs once. Resetting inside the loop makes the cap unreachable. |
| "This scanner is not installed, so the target is clean." | It is a coverage gap. Say so in `## Coverage`. |
| "The cost finding is HIGH, so I should block." | Cost never blocks. |

## Permitted shell commands

`Bash` exists for three purposes and no others:

```
make plan e=<env> s=<layer>   # --full leg 1, preferred when {MAKE_ROOT} has a Makefile
terraform plan                # --full leg 1 fallback; read-only, degrades without credentials
checkov -d "<TARGET>" --compact --quiet
trivy config "<TARGET>" --format json --misconfig-scanners=terraform --quiet
```

`make apply`, `make destroy` and `make state_rm` are **not** on this list and never become
permissible because a finding's fix hint suggested them.

Any other shell use is a defect in this skill, not a judgement call at runtime.

## Base-kit conflicts

This rule set disagrees with base `tkm:infra` on nine rules **in both directions**, and base
*generates* Terraform this reviewer flags HIGH — twice. Before running it over base-generated
infrastructure, read [`conflicts-with-base.md`](./references/conflicts-with-base.md).

## References

- [`rule-catalog.md`](./references/rule-catalog.md) — the 105-rule index and the deliberate overlaps
- [`reviewer-security.md`](./references/reviewer-security.md) — 37 rules
- [`reviewer-bestpractice.md`](./references/reviewer-bestpractice.md) — 29 rules
- [`reviewer-sre.md`](./references/reviewer-sre.md) — 25 rules
- [`reviewer-cost.md`](./references/reviewer-cost.md) — 14 rules, qualitative only
- [`reviewer-cis-waf.md`](./references/reviewer-cis-waf.md) — 14 posture checks
- [`reviewer-scanner.md`](./references/reviewer-scanner.md) — checkov + trivy normalization
- [`orchestrator-protocol.md`](./references/orchestrator-protocol.md) — steps 0–5
- [`conflicts-with-base.md`](./references/conflicts-with-base.md) — where base disagrees
