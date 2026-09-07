# Layer `5.messaging`

Generated **only when `messaging = true`**. **One queue, one topic, one identity per environment** —
not per backend service. The IAM policies that grant task roles access are emitted per backend
service.

Module calls come from the lookup table in
[`cross-layer-contracts.md`](../cross-layer-contracts.md).

Emission order is canonical: `sqs_main` → `sns_topic` → `ses_identity` (each only when picked), then
one `iam_<name>_messaging` per backend service.

No new provider or dependency — everything is `hashicorp/aws`.

---

## `sqs` — block `sqs_main`

Three resources plus a redrive pair.

- **Main queue** — name and `Name` tag both `${var.project}-${var.env}-${var.name_suffix}`
  (`name_suffix` default `"main"`), so two queues in one environment cannot collide.
  `sqs_managed_sse_enabled = true`, set **explicitly** — free SSE-SQS.
  When `var.fifo = true`: `.fifo` name suffix, `fifo_queue = true`, `content_based_deduplication = true`.
- **DLQ** — a **separate** resource, name `…-${var.name_suffix}-dlq`, same SSE.

> **The DLQ must inherit the main queue's FIFO setting.** Set `fifo_queue = var.fifo` on the DLQ
> exactly as on the main queue. A FIFO main queue with a STANDARD DLQ **fails `terraform apply`** —
> a redrive pair's queue types must match. Reading the same variable is what keeps them consistent.

- **`aws_sqs_queue_redrive_policy`** on the main queue — a separate resource, **not** an inline
  `redrive_policy`:
  `jsonencode({ deadLetterTargetArn = <dlq arn>, maxReceiveCount = var.max_receive_count })`.
- **`aws_sqs_queue_redrive_allow_policy`** on the DLQ:
  `jsonencode({ redrivePermission = "byQueue", sourceQueueArns = [<main arn>] })`.

> **`maxReceiveCount` must be a JSON integer, never a quoted string.** A string **silently disables
> redrive** — no error, no DLQ, messages lost after the visibility timeout.

> **Why the redrive policies are separate resources.** The DLQ's `redrive_allow_policy` has no inline
> form at all, so it must be its own resource. Keeping both separate also avoids a chicken-and-egg
> ARN cycle between the two queues.

Inputs: `name_suffix` (default `"main"`), `fifo` (default `false`), `max_receive_count` (default `5`).
Outputs: `queue_arn`, `queue_url`, `queue_name`, `dlq_arn`, `dlq_url`.

---

## `sns` — block `sns_topic`

`aws_sns_topic`, name **and** `Name` tag both `${var.project}-${var.env}-${var.name_suffix}`
(`name_suffix` default `"topic"`). The discriminator must reach the tag, or `sns_topic`,
`sns_alerts` and `sns_events` collide.

`kms_master_key_id = "alias/aws/sns"` set explicitly — SSE-SNS through the free AWS-managed key,
symmetric with the SQS default.

Emit a rationale comment whose **last line** is `#trivy:ignore:AVD-AWS-0136`, directly above the
resource with no blank line between:

```hcl
# SSE-SNS via the free AWS-managed key (alias/aws/sns). CMK reserved for forced cases only
# (CloudWatch Logs); mirrors the accepted S3 baseline.
#trivy:ignore:AVD-AWS-0136
resource "aws_sns_topic" "this" {
```

The scanner rule wants a customer-managed CMK; the kit deliberately uses the managed key and reserves
CMK for the one case that has no alternative. Suppressing **with rationale** keeps the layer at zero
HIGH without overturning the default.

### SNS → SQS fan-out — the blocker

When `var.subscribe_sqs = true` — set by the `5.messaging` caller **only** when `sqs` is also
picked — two `count`-gated resources appear, both with `count = var.subscribe_sqs ? 1 : 0` as their
**first** argument:

1. `aws_sns_topic_subscription` — `protocol = "sqs"`, `endpoint = <queue ARN, not the URL>`,
   `raw_message_delivery = var.raw_message_delivery` (default `false`).
2. **`aws_sqs_queue_policy`** — mandatory.

```hcl
resource "aws_sqs_queue_policy" "sns_to_sqs" {
  count     = var.subscribe_sqs ? 1 : 0
  queue_url = var.queue_url
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowSNSPublish"
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = var.queue_arn
      Condition = { ArnEquals = { "aws:SourceArn" = aws_sns_topic.this.arn } }
    }]
  })
}
```

> **Three details here are correctness, not style.**
>
> - **Without this policy, SNS accepts the subscription and then silently drops every message.**
>   There is no error at apply and no error at publish. The queue is simply always empty.
> - **`Version = "2012-10-17"` is required** — `aws_sqs_queue_policy` **hangs at apply** if it is
>   omitted.
> - **`Principal` is the SNS service, not `AWS = "*"`**, and the `aws:SourceArn` condition is the
>   confused-deputy guard. A wildcard principal lets any account's topic write to this queue.

When `subscribe_sqs = false` — the default, used by the alerting callers and by a `5.messaging` topic
when `sqs` is not picked — `count = 0` elides **both** resources.

---

## `ses` — block `ses_identity`

Only when `ses` is picked. **`ses` requires `route53 = true`** — the DKIM and verification records
need a hosted zone, and the interview enforces it.

- `aws_ses_domain_identity` — `domain = var.domain`. Exports `verification_token`.
- `aws_ses_domain_dkim` — `domain = aws_ses_domain_identity.this.domain`; the identity must exist
  first. Exports `dkim_tokens`, **exactly three**.
- `aws_route53_record` **DKIM CNAMEs** — `count = 3`:
  `name = "${…dkim_tokens[count.index]}._domainkey"`, `type = "CNAME"`,
  `records = ["${…dkim_tokens[count.index]}.dkim.amazonses.com"]`, `ttl = 600`.
- `aws_route53_record` **verification TXT** — `name = "_amazonses.${var.domain}"`, `type = "TXT"`,
  `records = [<verification_token>]`, `ttl = 600`.
- `aws_ses_domain_identity_verification` — an **optional waiter**,
  `count = var.enable_verification ? 1 : 0`, **default `false`**. The waiter blocks apply until DNS
  propagates; off by default keeps apply non-blocking.

Inputs: `domain`, `zone_id` (TODO — wired cross-layer to `…outputs.route53_zone_id`),
`enable_verification` (default `false`).
Outputs: `identity_arn`, `domain`, `verification_token`.

---

## `iam_<service>_messaging` — one per backend service

Uses the same generic `iam-policy` module as the S3 policies — see
[`cross-layer-contracts.md`](../cross-layer-contracts.md). The caller supplies the whole document.

Grants, all ARN-scoped:

| Service | Resource | Actions |
|---|---|---|
| SQS | `module.sqs_main.queue_arn` | `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes`, `sqs:ChangeMessageVisibility`, `sqs:SendMessage`, `sqs:GetQueueUrl` |
| SNS | `module.sns_topic.topic_arn` | `sns:Publish` |
| SES | `module.ses_identity.identity_arn` | **only** `ses:SendEmail`, `ses:SendRawEmail` |

> **The SES list is short for a reason.** Those two are the **only** SES actions that support
> resource-level ARN scoping. Every other SES action would require `Resource = "*"` — which this kit
> does not emit, and which the security reviewer flags.

Generated **after** the messaging blocks they reference. `role_name` is a TODO wired cross-layer to
`data.terraform_remote_state.backend.outputs.ecs_backend_<svc>_task_role_name` — which exists only
because Phase B's `messaging`-gated re-export appended it to `3.backend/_outputs.tf`.
