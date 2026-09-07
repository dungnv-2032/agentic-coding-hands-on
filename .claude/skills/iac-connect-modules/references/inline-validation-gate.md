# Inline Validation Gate

Three checks in sequence after wiring, with a HIGH fix loop capped at **2**.

This gate is the only thing between generated Terraform and a broken environment. Under batch
generation it is the *sole* check that runs.

## The gate invokes; it does not link

Checks 2 and 3 do not carry rules. They call the review skill:

```
Invoke `/tkm:iac-review <env> --only security --scope <target layer> --report-only`
Invoke `/tkm:iac-review <env> --only bestpractice --scope <target layer> --report-only`
```

Every flag on those lines is load-bearing. Dropping one does not degrade the gate — it stalls or
corrupts the generation turn this gate runs inside.

`<env>` is **required** by that skill. Omitting it makes the review stop and ask — mid-gate, which is
exactly what a batch run must never do.

**`--only` runs inline, in this turn.** A single leg does not fan out, so no subagent is dispatched
and the caller's turn does not end. That matters here: this gate can run inside an environment
generation flow, where dispatching a subagent stalls the whole pipeline.

**`--report-only` keeps the fixing here.** Without it the review runs its own auto-fix loop, capped
at 3, while this gate runs its own, capped at 2 — two writers on one file set, no coordination
between them, up to six rounds of edits. Worse, `--approve` **defaults on for any environment whose
name looks production-like** (`prod`, `live`, `prd`, `pd`, `main`), and an approval gate mid-batch
waits for a human who is not there: the turn ends and the environment is left half-wired with
unresolved cross-layer TODOs. That is the failure guard 5 exists to prevent, arriving through a path
guard 5 cannot see because no subagent was ever dispatched.

The review also owns an escalation string of its own (`ESCALATION: Unresolved HIGH findings after 3
iterations`). Under `--report-only` it cannot fire, which keeps it from being confused with this
gate's escalation — the two are not interchangeable (see below).

Two reasons this is an invocation rather than a file reference. The checklists stay in one place, so
there is no second copy to drift. And the skill validator resolves any `references/…` path against
*this* skill's directory, so a link to another skill's `references/` is a hard failure.

**Write no new rules here.** A rule that exists only in this gate is a rule the reviewer does not
know about, and the two will disagree the first time either changes.

> **If `tkm:iac-review` is unavailable, say so and stop the check.** State the gap in the report:
> `Check 2 skipped — tkm:iac-review not available. Generated Terraform has NOT been security
> reviewed.` **Never fall through to base `tkm:infra`'s review** — it applies a different rule set
> that disagrees with the generator's own conventions, so it would flag correct output and miss what
> this generator actually gets wrong. A stated gap is recoverable; a silently wrong verdict is not.

## Loop state

Counter file: **`{WORK_DIR}/inline-loop-count.txt`**, cap **2**.

This is **not** the review loop's counter. That one is `{WORK_DIR}/loop-count.txt`, cap 3. Sharing one
file would make this gate escalate with zero fix attempts immediately after a review exited at 3.

Reset to `0` **once per invocation, before the first check** — outside the loop. `{WORK_DIR}` is
gitignored, so a stale counter persists on disk between runs.

> **Deviation from upstream, intentional.** The source held this counter in memory, where it could
> not go stale. Persisting it matches the review loop's shape and survives an interrupted run — but
> it means this gate now needs the reset that the in-memory version never did. Do not drop the reset.

## Check 1 — `terraform validate`

Catches syntax errors, invalid references, and wrong module sources.

**Two prerequisites. If either fails, skip Check 1 with a warning and RUN CHECKS 2 AND 3 ANYWAY.**

> **A `symlink_all` target that exists but does nothing looks identical to success.** Some Makefiles
> stub it (`@echo`). After running it, verify the symlinks actually appeared; if they did not, fall
> back to `make symlink e=<env> s=<layer>` per layer, or `ln -sf` if that target is missing too. The
> "no Makefile" escape hatch does not cover "the target is a stub", and without symlinks Check 1
> skips on every layer for the wrong reason.

1. The layer's `_variables.tf` is a **symlink**:

```
Warning: _variables.tf is not a symlink in <target layer>.
Run: make symlink e=<env> s=<layer>   (from {MAKE_ROOT})
Check 1 skipped — the remaining checks still run.
```

2. `.terraform/` exists in the layer — that is, the layer has been initialized:

```
Warning: .terraform/ not found in <target layer>.
Run: make init e=<env> s=<layer>   (from {MAKE_ROOT})
Check 1 skipped — the remaining checks still run.
```

> **Both skips are load-bearing.** A freshly generated layer has never been initialized, so
> `terraform validate` reports every module as not installed. Without the second prerequisite, the
> gate raises a HIGH `[VALIDATE]` whose only available action is to *print* `make init` — which this
> skill will not run — so the loop cannot clear it and **every first run escalates**. The escalation
> would be about the layer being new, not about anything wrong with it.
>
> Skipping is also correct for the first: `terraform validate` against an unsymlinked layer fails on
> missing variables, a wall of errors unrelated to the generated code.

> **Consequence, stated plainly: on a freshly generated environment Check 1 ALWAYS skips.** Only
> `init` creates `.terraform/`, and this skill does not run `init`. So the check that would catch
> broken HCL never runs on the one input `tkm:iac-generate-env` ever hands this gate — while under
> batch generation the gate calls itself the sole check.
>
> The skip is still right; running `init` from here is worse. But do not let "Check 1 skipped" read
> as "Check 1 passed" in the report, and never summarise a run as validated when only Checks 2 and 3
> ran. Write the skip and its reason into the report every time.
>
> **`terraform fmt -recursive -check` is the one static gate that does work here** — no init, no
> credentials, no network. It catches syntax errors and nothing semantic, which is little, but it is
> more than zero and it is available on exactly the input where Check 1 is not. Run it, and report it
> as what it is.

With both satisfied, run `terraform validate` in the layer directory. Findings are gate-local,
categorized `[VALIDATE]`.

> **`[VALIDATE]` is not a finding-format category.** The shared contract's categories are `SECURITY`,
> `COST`, `BESTPRACTICE`, `SRE`, `SCANNER`, `CIS`, `WAF` — a `[VALIDATE]` line would be **discarded**
> by the orchestrator's parse regex.
>
> That is fine, because this gate does **not** write to `{WORK_DIR}/findings-*.txt` and its output
> never reaches the orchestrator. It writes `{WORK_DIR}/step-N-report.md`. Keep the two flows
> disjoint. If a gate finding ever needs to reach the orchestrator, re-categorize it first — do not
> widen the shared category set.

## Check 2 — Security review

`Invoke /tkm:iac-review <env> --only security --scope <target layer> --report-only`

## Check 3 — Best-practice review

`Invoke /tkm:iac-review <env> --only bestpractice --scope <target layer> --report-only`

## Loop logic

After all three checks complete:

```
if no HIGH findings:
    → write the report, print Next Steps, stop
else if inline-loop-count < 2:
    → increment the counter
    → fix every HIGH finding
    → clear the finding list
    → re-run Checks 1, 2, 3
    → evaluate again
else:                       # counter == 2, both attempts spent
    → ESCALATE
```

Two fix attempts total. The loop re-enters at Check 1, never at the reset.

## Fixing HIGH findings

| Finding | Automated fix |
|---|---|
| `[VALIDATE]` undeclared reference | Correct the resource address |
| `[VALIDATE]` unsupported argument | Remove or rename it |
| `[VALIDATE]` missing required argument | Add it with a sensible default, or a TODO for manual fill |
| `[VALIDATE]` module not installed | **Print** `make init e=<env> s=<layer>` — do **not** run it |
| `[SECURITY]` SG `0.0.0.0/0` | Keep the value; add `# TODO: restrict CIDR before production — 0.0.0.0/0 only permitted on 80/443` |
| `[SECURITY]` RDS `publicly_accessible` | Set `publicly_accessible = false` |
| `[SECURITY]` IAM wildcard | Add `# TODO: restrict IAM action/resource before production` |
| `[SECURITY]` hardcoded secret | Replace the literal with `var.<name>`, add a `sensitive = true` variable |
| `[SECURITY]` S3 missing public-access block | Append `aws_s3_bucket_public_access_block` for the bucket |
| `[BESTPRACTICE]` hardcoded region | Replace the literal with `var.region` |
| `[BESTPRACTICE]` missing path header | Add `# <path>.tf` as line 1 |
| `[BESTPRACTICE]` unresolved TODO | **Cannot auto-fix** — record under `## Requires Manual Action` |
| `[BESTPRACTICE]` S3 backend missing | **Cannot auto-fix** — structural; record under `## Requires Manual Action` |

Two of these are deliberately *not* fixed automatically. A `0.0.0.0/0` ingress and an IAM wildcard
may be intentional; the gate annotates them and leaves the decision to a human rather than silently
narrowing a rule the environment depends on.

**Never silently ignore a HIGH finding.** When no automated fix exists, record it under
`## Requires Manual Action`. It does **not** count as resolved, and it escalates after two loops.

## Report

`{WORK_DIR}/step-N-report.md`:

```markdown
# Inline Validation Report — step-N

**Env:** <env>
**Layer:** <target layer>
**Loop iterations:** <count>
**Timestamp:** <caller-supplied>

## Summary
## Findings
## Auto-fixed in this run
## Requires Manual Action
```

Console:

```
Inline validation complete — <env>/<target layer>
─────────────────────────────────────────────────
Check 1 (Validate):     HIGH: N  MEDIUM: N  LOW: N
Check 2 (Security):     HIGH: N  MEDIUM: N  LOW: N
Check 3 (BestPractice): HIGH: N  MEDIUM: N  LOW: N
─────────────────────────────────────────────────
Total: HIGH: N  MEDIUM: N  LOW: N
Report: {WORK_DIR}/step-N-report.md
```

The timestamp is supplied by the caller. Do not invent one.

## Escalation

After 2 loops with HIGH findings remaining, print **exactly**:

```
ESCALATION: Unresolved HIGH findings after 2 iterations in <env>/<target_folder>.
Partial fixes applied — see {WORK_DIR}/step-N-report.md.
Human action required:

<list each unresolved HIGH finding>

Resolve these before running: make init e=<env> s=<layer>
```

Then stop. Do not print Next Steps.

> This line differs from the review loop's escalation — different count, and it names the location.
> They are **not** interchangeable. See
> [`finding-format.md`](../../_shared/extras/iac/finding-format.md).

## Next Steps — only after a clean run or MEDIUM/LOW only

```
Inline validation passed — <env>/<target layer>
Next steps (run from {MAKE_ROOT}):
  1. Review {WORK_DIR}/step-N-report.md for MEDIUM/LOW findings
  2. make symlink e=<env> s=<layer>   (if not already done)
  3. make init    e=<env> s=<layer>
  4. make plan    e=<env> s=<layer>
  5. Run a full review when the environment is complete
```

## Safety rules

- **Never overwrite `_variables.tf`** — it is a symlink.
- **Never regenerate `_backend.tf`** wholesale — targeted edits only, to fix a specific finding.
- **Never run `make init`, `make plan`, or `make apply`.** File edits and `terraform validate` only.
- **Never delete a file.** Fix in place; add a comment where an automated fix is not possible.
- **Idempotent** — re-running with the same inputs produces the same findings and the same fixes.
