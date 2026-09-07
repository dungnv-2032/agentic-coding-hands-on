# Monitoring Standards (source-of-truth)

These files are the **team-provided, VERBATIM Sun\* monitoring standards** and are treated as the **source-of-truth** for how observability (alarms, events, logs) must be configured across environments. They are reproduced here byte-for-byte from the upstream team documentation.

**Do not edit thresholds or content here — these tables are authoritative.** If a standard changes, update it upstream first, then re-sync the file into this folder so it stays identical to the source. The table content is written in Vietnamese (as provided by the team); leave it as-is.

## Files

| File | Standard |
|------|----------|
| [cloudwatch-alarm-standards.md](./cloudwatch-alarm-standards.md) | CloudWatch Alarm thresholds and configuration standard (alarm). |
| [monitor-event.md](./monitor-event.md) | Monitor Event standard — which service events to capture and route (event). |
| [monitor-log.md](./monitor-log.md) | Monitor Log standard — log retention, collection, and keyword monitoring (log). |

Filenames are kebab-cased for this kit; content is byte-identical to the upstream files
(`cloudwatch_alarm_standards.md`, `monitor_event.md`, `monitor_log.md`).

## Referenced by

The `tkm:iac-*` reviewers and generators consult these standards for **thresholds and
conventions** — an inferred CloudWatch alarm, log group, or event rule must follow the values
defined here rather than inventing new ones.

These are companion-resource knowledge shared by both reviewers and generators, and carry no rule
severities, which is why they live in `_shared/` rather than inside a skill directory.

## What is NOT here

These files are the **standards only**. The *inference logic* that decides which companion resources
a component gets — the component→companion table, HYBRID log placement, the monitoring companions and
their dimensions, delivery companions, the naming convention, security defaults for inferred
resources, and the two-topic alerting event/log routing — lives in the upstream
`aidd-inferred-resources/SKILL.md` (124 lines) and is **not ported by this phase**.

Whichever phase ships monitoring and alerting owns porting it. Reading only the files in this
directory is not enough to generate a correct monitoring layer.
