# Orchestrator Protocol

Collects findings from the five reviewer legs, decides whether to loop-fix, report, or escalate.

Dedup priority, the parse regex, the finding shape, and the counter semantics are owned by
[`finding-format.md`](../../_shared/extras/iac/finding-format.md). This file is the **procedure**;
that file is the **contract**. Do not restate the regex here.

## Inputs

Findings files written by the five legs, under `{WORK_DIR}`:

```
{WORK_DIR}/findings-security.txt
{WORK_DIR}/findings-bestpractice.txt
{WORK_DIR}/findings-sre.txt
{WORK_DIR}/findings-scanner.txt
{WORK_DIR}/findings-cis-waf.txt
{WORK_DIR}/findings-cost.txt      ← optional; only when --only cost ran
```

`--full` does **not** produce this file. Its cost leg is `tkm:iac-cost`, which emits dollar figures
into its own reports — a different artifact entirely from the qualitative `[COST]` findings this
orchestrator merges.

`{WORK_DIR}` resolves through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md) and must be gitignored.

Cost is **merge-only**. It appears in the report and never triggers the loop.

---

## Step 0 — Reset the loop counter

Write `0` to `{WORK_DIR}/loop-count.txt`.

**Once per invocation, outside the loop.** The loop body re-enters at step 1, never here.

`{WORK_DIR}` is gitignored, so a counter left behind by a previous run persists on disk. If it held
`3`, the first HIGH check would escalate after **zero** fix attempts — a review that silently gives
up while looking like it ran.

### This counter is not the inline gate's counter

| Counter | File | Cap | Owner |
|---|---|---|---|
| **Review loop** | `{WORK_DIR}/loop-count.txt` | **3** | this file |
| Inline generation gate | `{WORK_DIR}/inline-loop-count.txt` | **2** | the module-generation skill |

Different filenames, deliberately. Sharing one file would mean a review exiting at `3` makes the next
inline gate escalate with zero attempts.

## Step 1 — Collect and parse

Read the findings files. Extract lines matching the parse regex in
[`finding-format.md`](../../_shared/extras/iac/finding-format.md). Lines that do not match — blank
lines, `NO_FINDINGS`, prose a leg emitted by mistake — are ignored.

**For every leg this invocation dispatched, a missing, empty, or malformed findings file is a hard
ERROR.** Stop and report it. It is never an empty finding set.

> **If the runtime's subagent tool is asynchronous, the requirement is the barrier, not the flag.**
> Some harnesses return immediately and notify on completion; "blocking, no background flag" cannot be
> honoured there as written. What must hold is that **no findings file is parsed before its leg has
> finished writing it** — dispatch all five in one message, then wait for every leg to report before
> step 1 reads anything. Parsing early is the failure this rule exists to prevent, and it stays
> forbidden however the runtime schedules the legs.

**Scoped to legs that ran.** Under `--only <reviewer>` exactly one leg is dispatched, so the other
files are legitimately absent. Checking all six regardless would make every single-leg mode abort
before parsing. Build the expected-file list from what was dispatched, not from the full roster.

This matters more here than anywhere else in the pipeline: non-matching lines are discarded by
contract, so a leg that crashed, wrote nothing, or emitted prose would otherwise present as "clean".
A review that found ten HIGH issues would emit a passing report. "Malformed" means the file contains
neither `NO_FINDINGS` nor at least one line matching the regex.

## Step 2 — Dedup

By `(resource_address, issue topic)` — **never** exact string. Producer priority:

```
[SECURITY]  >  [SRE]  >  [CIS] / [WAF]  >  [SCANNER]
```

**An unmatched `[SCANNER]` or `[CIS]`/`[WAF]` finding always survives.** That is the entire backstop
value.

Non-dedup pairs — both surface:

- **No.44 WAF** — SRE HIGH versus security MEDIUM. Fix emphasis differs. The SRE HIGH enters the loop.
- **Architecture versus atomic** — a `[CIS]`/`[WAF]` posture finding is not a dedup of a scanner's
  per-resource finding. The scopes differ.

Full rules, including the deliberate cross-reviewer overlaps, are in
[`rule-catalog.md`](./rule-catalog.md).

### Conflict resolution

- `[SECURITY]` beats `[BESTPRACTICE]` when the two conflict.
- Two findings in the same category that conflict: the stricter one wins.
- Neither clearly stricter: **emit both and flag for human decision.** Do not pick arbitrarily.

**Severity never drops through dedup.** Producer priority decides which finding's *text* survives; it
must not decide the severity. When the duplicates disagree, the survivor carries the **highest**
severity of the group.

Without this rule the pipeline silently downgrades: a `[CIS]` MEDIUM and an `[SRE]` LOW on the same
`(resource, topic)` resolve to SRE by producer priority, and a MEDIUM disappears into a LOW. Dedup
exists to stop the same issue being reported five times, never to make an issue look smaller than the
strictest reviewer found it. The "stricter wins" rule above is scoped to same-category pairs; this
one covers every cross-category pair.

## Step 3 — Any HIGH present?

HIGH findings from `[SECURITY]`, `[BESTPRACTICE]`, `[SRE]`, `[SCANNER]` and `[CIS]`/`[WAF]` each
count individually, **after** dedup. `[COST]` never counts, at any severity. `[BESTPRACTICE]` is in
the loop — see the note in
[`finding-format.md`](../../_shared/extras/iac/finding-format.md), where the upstream text is
inconsistent.

> **`--report-only` stops here.** Report every HIGH finding with its `→ fix` hint and go to step 4.
> Apply no fix, touch no counter, prompt for nothing. The caller owns the fixing — see the SKILL for
> why the inline generation gate needs this.

If any HIGH remains, loop-fix — capped at **3 iterations**:

1. Compile a **correction brief** listing every HIGH finding. Each carries its own `→ fix` hint.
2. Apply fixes by the most targeted means available:
   - **Patch the `.tf` files directly** when the finding is local and the hint is unambiguous — add
     `use_lockfile = true`, set `storage_encrypted = true`, mark an output `sensitive = true`, narrow
     a `0.0.0.0/0` ingress, replace a git-tag `source` with a local relative path. Preferred.
   - **Re-run environment generation** with the correction brief as context when the issue is
     structural or spans the blueprint — a whole service mis-generated, a missing layer, cross-layer
     wiring gaps.
3. Increment `{WORK_DIR}/loop-count.txt`.
4. Re-run the five legs on the updated target.
5. **Repeat from step 1** — never from step 0.
6. Counter reaches **3** with HIGH findings still present → escalate (step 5). Do not loop again.

> **`--approve` mode.** When approval mode is on, present the correction brief and **wait for
> explicit human approval before applying any fix**. Findings are still collected and still counted;
> only the write is gated. See the SKILL for when this defaults on.
>
> Inert under `--report-only`: that mode writes nothing, so there is no write to gate. A caller that
> must not block — the inline generation gate — passes `--report-only` and gets findings back
> whatever the environment is named.

## Step 4 — Only MEDIUM / LOW (or nothing)

- Leave the `.tf` files as they are.
- If any MEDIUM/LOW finding exists, write `review-report.md` — at `{ENV_DIR}/review-report.md` for a
  full-environment review, or in the layer folder for a scoped one.
- Print: `Terraform files ready in <target>. Review review-report.md before running terraform plan.`
- Stop.

### `review-report.md` format

```markdown
# IaC Review Report

Target: {resolved target}

## Findings requiring human review

### MEDIUM

{each MEDIUM finding, one per line}

### LOW

{each LOW finding, one per line}

## Coverage

{scanner availability lines; which legs ran; which pricing source, when --full}

---
Review these findings before running `terraform plan`.
{if N > 0: "HIGH findings were resolved automatically in {N} loop(s)."}
```

The trailing HIGH-loop line is **omitted entirely when N = 0** — that is, when the report exists
because there were only MEDIUM/LOW findings and no loop ran. Writing "resolved in 0 loops" implies a
loop happened.

**`## Coverage` is mandatory and appears on every run**, including the clean ones. When both scanners
ran, it records that. A report without it is incomplete — see `reviewer-scanner.md`.

**No timestamp.** The report carried a `Generated:` line for a while; it is gone deliberately.

Nothing in this chain supplies a timestamp — the blueprint interview has sixteen fields and none is
one — so the old instruction ("supplied by the caller, do not invent one") could not be satisfied by
any caller that exists. Worse, this file lives in `{ENV_DIR}`, which is **tracked**: a timestamp makes
every re-run dirty a committed file and breaks the contract that re-running a generator is a no-op.

`git log` already dates the file, and dates it correctly. The inline gate's report has the same shape
but writes to `{WORK_DIR}`, which is gitignored, so a timestamp there would be harmless — it is
omitted anyway, for one format rather than two.

## Step 5 — Escalation

After 3 failed loops, output exactly:

```
ESCALATION: Unresolved HIGH findings after 3 iterations.
Partial output has been saved to the env folder but is NOT safe to apply.
Human action required for the following issues:

{list each unresolved HIGH finding, one per line}
```

Then stop. Do not loop again. Do not soften the wording — "NOT safe to apply" is the point of the
message.

> The inline generation gate has its **own** escalation line, with a different count and a location
> suffix. They are not interchangeable. See
> [`finding-format.md`](../../_shared/extras/iac/finding-format.md).

---

## Auto-fix has no harness-level deny-list underneath it

Up to three rounds of automated `.tf` edits run with `allowed-tools` as the only boundary — there is
no command deny-list behind it. `--approve` is the compensating control, which is why it defaults on
for production-like environment names.

Two things the loop must never do, regardless of what a finding's fix hint says:

- run `terraform apply`, `destroy`, `import`, or `state rm`
- run `make apply`, `destroy`, or `state_rm`

A finding is fixed by editing configuration, never by mutating deployed state.
