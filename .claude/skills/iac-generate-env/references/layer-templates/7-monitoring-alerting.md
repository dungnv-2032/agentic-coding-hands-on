# Layer `7.monitoring` — alerting pipeline

**Gated on `alerting = true`**, the sub-toggle under `monitoring`. Additive on top of
[`7-monitoring.md`](./7-monitoring.md).

> ### When `alerting = false`, none of this exists
>
> The layer is **byte-for-byte the passive layer**: none of the resources below are emitted, the
> alarm block keeps `alarm_actions = []`, `7.monitoring/_backend.tf` has **no** SOPS provider or data
> source, and Phase A.5 seeds **no** Slack keys.
>
> That is a stated regression boundary, not an implementation detail. An edit here that perturbs the
> passive path is a defect even if the alerting path still works.

Everything lives **in `7.monitoring`**, still applied last. The new IAM, SNS and Lambda read compute
and data dimensions exactly as the alarms already do — all reads stay **downstream**, so the graph
stays acyclic.

**Module-first: no raw resources in the env layer.** Every item below is a module call.

## Three modules this layer scaffolds

| Module | Role |
|---|---|
| `iam-role` | Generic role creator. The `lambda` module does **not** create its own role. |
| `eventbridge-rule` | Generic rule creator. **It does not carry the SNS publish policy** — the topic owner does, through `allow_eventbridge_publish`. |
| `lambda` | The Python-Lambda builder: takes `code_path` / `code_zip_path`, runs `pip install` against the handler's `requirements.txt`, and zips. |

The `lambda` module's per-trigger inputs:

- `lambda_function_sns` — `list(object({ topic_name, topic_arn }))`, default `[]`. Per entry it emits
  an `aws_sns_topic_subscription` (`protocol = "lambda"`) **and** an `aws_lambda_permission`
  (`principal = "sns.amazonaws.com"`, `source_arn = <topic arn>`).
- The log-subscription input takes **only** `log_subscription_filter_name`, `log_group_name` and
  `log_subscription_filter_pattern` per entry — **no `log_group_arn` field**. Its
  `aws_lambda_permission` uses `principal = "logs.<region>.amazonaws.com"` with **no `source_arn`**.
  Tightening that to the specific log-group ARN is a real hardening idea and a deliberate follow-up,
  not an omission.

Outputs: `lambda_function_name`, `lambda_function_arn`, `lambda_function_invoke_arn`,
`lambda_function_qualified_arn`.

---

## The three handlers are vendored code

Three Slack handlers live under `{DEPS_ROOT}/lambda-function/`:

| Directory | Handler | Trigger | Dependencies |
|---|---|---|---|
| `cloudwatch-alarm/` | `cloudwatch_alarm.py` | SNS | `urllib3<2`, `requests`, `slack_sdk==3.31.0` |
| `cloudwatch-log/` | `cloudwatch_log_filter.py` | CloudWatch Logs subscription filter | `slack_sdk`, `requests` |
| `event/` | `event.py` | EventBridge | `slack_sdk`, `requests` |

Each handler's basename must equal the block's `code_zip_name`, so `${code_zip_name}.lambda_handler`
resolves. Each directory also ships a `requirements.txt` that the module's `pip install` step bundles
into the zip.

**Auth is webhook-OR-token.** Each handler resolves `SLACK_WEBHOOK_URL` from SSM first; if non-empty
it POSTs and returns. Otherwise it falls back to `slack_sdk.WebClient` with the bot token and channel
id.

### File-exists guard — never re-author a handler

> **These are pre-committed, reference-only dependency code.** Reference them through the `lambda`
> module's `code_path` and `code_zip_path` inputs. **Do not author, regenerate, or overwrite them.**
>
> **Evaluated per file, independently.** For each of `<handler>.py` and its paired
> `requirements.txt`: if the file **exists**, do not overwrite it; if it is **absent**, restore that
> one file from source control. Partial presence restores only the missing half.
>
> **Never re-author a handler payload from this prose.** They are roughly a thousand lines of
> reviewed, sensitive code. Prose is not a recovery mechanism — recover from git history or the
> source branch.
>
> **Absent and not in this repository's history → stop.** This kit ships no payloads, so outside the
> origin repository there is nothing to restore from. Name the file, say so, and offer the two real
> options: the user supplies the payload, or the run continues with `alerting = false`. Never emit a
> `code_path` pointing at a directory that does not exist — `terraform validate` passes on it (a
> string is a string) and the environment fails at apply time instead.

Full rule: [`idempotency-matchers.md`](../../../_shared/extras/iac/idempotency-matchers.md).

---

## 1. Two dedicated SNS topics

Reuses the `sns` module — see [`5-messaging.md`](./5-messaging.md) for its contract.

| Block | `name_suffix` | `allow_eventbridge_publish` | Subscriber | Publishers |
|---|---|---|---|---|
| `sns_alerts` | `"alerts"` | **`false`** | **only** `lambda_alarm` | CloudWatch alarm `alarm_actions` / `ok_actions` |
| `sns_events` | `"events"` | **`true`** | **only** `lambda_event` | EventBridge rules, and RDS/Aurora event subscriptions |

> **Two topics, not one.** Each Lambda subscribes exactly one topic, so an alarm never reaches the
> event handler and vice versa. Collapsing them into one topic means both handlers receive both
> message shapes, and each has to guess which it got.

### `sns_events` MUST pass `allow_eventbridge_publish = true`

The `sns` module exposes `allow_eventbridge_publish` (bool, **default `false`**). When `true` it
emits a `count`-gated `aws_sns_topic_policy` granting `events.amazonaws.com` `sns:Publish` on the
topic.

> **The `eventbridge-rule` module does NOT carry this policy — the topic owner does.** Omit it and
> EventBridge rules match, fire, and **drop every event**. No error at apply, no error at runtime, an
> empty Slack channel. This is the same silent-failure class as the SNS→SQS queue policy in
> [`5-messaging.md`](./5-messaging.md), and it fails the same way: everything looks wired.

`sns_alerts` passes `false` — alarms publish through `alarm_actions`, not through EventBridge.

The default `false` is what keeps `5.messaging`'s `sns_topic` byte-for-byte unchanged: it emits no
policy resource at all.

Both alerting callers leave `subscribe_sqs` at its default `false`, so neither emits a subscription or
a queue policy, and both leave `queue_arn` / `queue_url` at their `""` defaults.

---

## 2. `lambda_alerts_exec_role`

The `lambda` module does **not** create its own role. It comes from the generic `iam-role` module,
with a scoped inline policy.

**The policy is ARN-scoped, not wildcarded:**

| Grant | Resource |
|---|---|
| `logs:CreateLogStream`, `logs:PutLogEvents` | the **function log-group ARNs** |
| `ssm:GetParameter` | the **three specific SSM parameter ARNs** — the `ssm-parameter` module's `ssm_parameter_arn` outputs |
| `cloudwatch:GetMetricWidgetImage` | `"*"` — this action does **not** support resource-level scoping |

> **No `Resource = "*"` on logs or SSM. No `ssm:*` or `logs:*` wildcard action.** The single `"*"`
> above is the documented exception, for the same reason as the SES actions in
> [`5-messaging.md`](./5-messaging.md): AWS provides no ARN to scope it to. Every other `"*"` in this
> layer is a HIGH finding.

---

## 3. Three SSM SecureString parameters

Blocks `ssm_slack_*`, through the `ssm-parameter` module — the SOPS-to-SSM hybrid.

> **No secret literal appears in any `.tf` or `.tfvars`.** All three keys are read through
> `data.sops_file.secret.data[...]`.

### The three keys are seeded by Phase A.5 — and only when `alerting = true`

```
<PREFIX>_SLACK_WEBHOOK_URL     # optional — empty means bot-token mode
<PREFIX>_SLACK_BOT_TOKEN       # xoxb-… — used when the webhook is empty
<PREFIX>_SLACK_CHANNEL_ID      # used with the bot token
```

> **Phase A runs long before this template is read**, so the dependency is one-directional and easy
> to lose: Phase A.5 must append these three keys to `secrets.{env}.yaml` **whenever
> `alerting = true`**, or every `ssm_slack_*` block resolves to a key that does not exist.
>
> They go through the same commented-aware matcher as every other key, so a re-run never duplicates
> them, and when `alerting = false` they are **not** appended at all — which is part of the
> byte-for-byte passive boundary.

This is also why `7.monitoring/_backend.tf` gains a SOPS block only in this mode.

---

## 4. Three Lambda calls

Blocks `lambda_alarm`, `lambda_log`, `lambda_event` — each pointing at its handler directory through
`code_path` and `code_zip_path`.

> **`lambda_event` subscribes `sns_events` only — never `sns_alerts`.** Wiring it to both exposes the
> event handler to alarm payloads it does not parse.

The log Lambda is driven by CloudWatch Logs subscription filters; the module takes only
`log_subscription_filter_name`, `log_group_name` and `log_subscription_filter_pattern` per entry.

---

## 5. EventBridge wiring

Rules for the applicable monitored-event rows, rendered internally by the `eventbridge-rule` module:
ECS deployment state change (failed), ASG launch and terminate failures, and the rest of the
catalogued set.

**RDS and Aurora event categories use `aws_db_event_subscription`, not EventBridge.** That block
stays as it is — the two mechanisms are not interchangeable, and the RDS categories have no
EventBridge equivalent.

Which services route to the event Lambda is catalogued in the monitoring standards under
`_shared/extras/iac/inferred-resources/`.

---

## The alarm hook

With `alerting = true`, the `cloudwatch-alarm` block sets **both**:

```
alarm_actions = ok_actions = [module.sns_alerts.topic_arn]
```

Both point at `sns_alerts` — the **alarms** topic, never `sns_events`. "Alarms only" is about which
*topic* receives them, not about dropping `ok_actions`: without `ok_actions` the channel is told when
something breaks and never told when it recovers.

Those two inputs are the entire coupling between the passive layer and this one. Both are
`list(string)` default `[]` on the alarm module, which is why leaving them empty is a complete,
working configuration.
