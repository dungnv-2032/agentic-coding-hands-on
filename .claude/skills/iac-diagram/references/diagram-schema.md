# Diagram Schema — mode routing, inputs, service mapping

Path keys resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

Mermaid syntax reference: `_vendor-iac/mermaid-diagrams/`. AWS service-selection context:
`_vendor-iac/aws-solution-architect/`. Both are reference material, not routable skills.

---

## Mode routing

Two modes; pick one per invocation by scanning the prompt.

### Blueprint mode — deterministic

Triggered when the prompt **explicitly names** a known environment blueprint. Token detection is
case-insensitive; the first matching token wins.

| Tokens in prompt | Blueprint | Variant |
|---|---|---|
| `ecs-system` + `ssr` (or `next.js`, `nuxt`, `nextjs`) | `ecs-system` | `ssr` |
| `ecs-system` + `static spa` (or `s3+cloudfront`, `react spa`, `vue spa`) | `ecs-system` | `static-spa` |
| `ecs-system`, no frontend keyword | `ecs-system` | `none` |
| `ecs` **alone**, without `-system` | — | **not** blueprint mode; fall through to NL |

In blueprint mode the diagram renders from the canonical `<variant> × <layer> → services` table
owned by `tkm:iac-generate-env`. **No topology inference happens** — output is byte-identical for the
same tuple:

```
{blueprint, variant, backend_services, route53, messaging, delivery, monitoring, db_engine, cache_engine}
```

**All nine, not four.** The composition table's rows are gated on `messaging`, `delivery` and
`monitoring`, and its naming is selected by `db_engine` and `cache_engine`. Omitting them from the
tuple does not make the diagram deterministic — it makes the same tuple legitimately render six
different architectures, which is the opposite of the guarantee.

When a caller supplies fewer than nine, the missing ones take the blueprint's documented defaults;
say which defaults you used in the output, because a reader comparing two diagrams needs to know
whether a difference is real.

Layer names resolve through the contract's `LAYERS`.

### NL mode

The default for any prompt that does not match a blueprint trigger. Extract services via the mapping
table, infer placement via the topology rules, render via the output contract.

---

## Input schema

| Field | Required | Default | Notes |
|---|---|---|---|
| `name` | yes | derive from the first noun phrase | Used for the output filename |
| `app_type` | yes | — ask | web app, API backend, microservices, data pipeline, ML inference, batch job |
| `services` | yes | — ask if none detected | via the mapping table |
| `scale` | no | `multi-az` | `single-az` / `multi-az` / `multi-region` |
| `access` | no | `public` for ALB/CloudFront/API Gateway; `private` for RDS/Redis/internal | |
| `traffic` | no | not rendered | annotates scaling notes only |
| `dependencies` | no | — | external integrations → cloud-external node |

Blueprint mode additionally collects `backend_services` (default `[{name: api, type: api}]`) and
`route53` (default `false`, true when the prompt mentions DNS or a domain).

---

## Clarifying questions — at most ONE round

Batch every unknown into a single prompt.

| Situation | Ask |
|---|---|
| `app_type` missing **and** no service keywords detected | what kind of application |
| A database mentioned with no engine | which engine |
| Caching mentioned with no engine | Redis or Memcached |
| Frontend implied but the type unclear | SSR, static SPA, or none |
| Multi-region or DR mentioned, scope unclear | active-active, active-passive, or single-region multi-AZ |
| Blueprint matched but `backend_services` unparseable | which backend services, with the format |

**Never ask about** node IDs, port numbers, subnet naming, tag values, or project and environment
names. Those are output-formatting concerns, not architecture intent — asking about them spends the
one round on something the schema already answers.

**Never guess a missing required field.** Ask.

---

## Service mapping table

Keyword matching is case-insensitive and whole-word. Both exact names and aliases are accepted.

| Service | Node ID | Label | Default port | Keywords |
|---|---|---|---|---|
| Application Load Balancer | `ALB` | `[Application Load Balancer]` | 80, 443 | `alb`, `application load balancer`, `load balancer`, `lb` |
| Network Load Balancer | `NLB` | `[Network Load Balancer]` | varies | `nlb`, `network load balancer` |
| ECS Fargate | `ECS` | `[ECS Fargate Service]` | 8080 | `ecs`, `fargate`, `containers`, `container service` |
| ECS Worker | `ECSWorker` | `[ECS Fargate Worker]` | — | `worker`, `background worker`, `queue consumer`, `async job` |
| EKS | `EKS` | `[EKS Cluster]` | 6443 | `eks`, `kubernetes`, `k8s` |
| EC2 | `EC2` | `[EC2 Instance]` | varies | `ec2`, `instance`, `vm`, `virtual machine` |
| Lambda | `Lambda<Purpose>` | `[Lambda - <Purpose>]` | — | `lambda`, `serverless function`, `function` |
| API Gateway | `APIGW` | `[API Gateway]` | 443 | `api gateway`, `apigw`, `apigateway` |
| AppSync | `AppSync` | `[AppSync GraphQL]` | 443 | `appsync`, `graphql api` |
| CloudFront | `CF` | `[CloudFront CDN]` | 443 | `cloudfront`, `cdn`, `edge cache` |
| Route 53 | `R53` | `[Route 53 DNS]` | 53 | `route53`, `route 53`, `dns`, `domain`, `hosted zone` |
| ACM | `ACM` | `[ACM Certificate]` | — | `acm`, `tls cert`, `ssl cert`, `certificate` |
| WAF | `WAF` | `[AWS WAF]` | — | `waf`, `web application firewall` |
| RDS | `RDS` | `[(RDS <engine>)]` | 5432 / 3306 | `rds`, `postgres`, `postgresql`, `mysql`, `mariadb` |
| Aurora | `Aurora` | `[(Aurora <engine>)]` | 5432 / 3306 | `aurora`, `aurora postgres`, `aurora mysql` |
| DynamoDB | `DDB<Purpose>` | `[(DynamoDB - <Purpose>)]` | — | `dynamodb`, `ddb`, `nosql table` |
| DocumentDB | `DocDB` | `[(DocumentDB)]` | 27017 | `documentdb`, `mongodb-compatible` |
| ElastiCache Valkey | `Valkey` | `[ElastiCache Valkey]` | 6379 | `valkey` — and `elasticache`, `cache`, `in-memory cache` when the engine is unstated, since `valkey` is the blueprint default |
| ElastiCache Redis | `Redis` | `[ElastiCache Redis]` | 6379 | `redis` |
| ElastiCache Memcached | `Memcached` | `[ElastiCache Memcached]` | 11211 | `memcached` |
| S3 | `S3<Purpose>` | `[S3 - <Purpose>]` | 443 | `s3`, `object storage`, `bucket`, `static assets` |
| EFS | `EFS` | `[EFS]` | 2049 | `efs`, `nfs`, `shared filesystem` |
| FSx | `FSx` | `[FSx <flavor>]` | varies | `fsx`, `lustre`, `windows file server` |
| SQS | `SQS<Purpose>` | `[SQS - <Purpose>]` | — | `sqs`, `queue`, `message queue` |
| SNS | `SNS<Purpose>` | `[SNS - <Purpose>]` | — | `sns`, `topic`, `notification`, `pub/sub` |
| EventBridge | `EB` | `[EventBridge]` | — | `eventbridge`, `event bus`, `cloudwatch events` |
| Kinesis Data Stream | `Kinesis` | `[Kinesis Data Stream]` | — | `kinesis`, `data stream` |
| Kinesis Firehose | `Firehose` | `[Kinesis Firehose]` | — | `firehose`, `delivery stream` |
| Glue | `Glue` | `[AWS Glue]` | — | `glue`, `etl`, `data catalog` |
| Athena | `Athena` | `[Athena]` | — | `athena`, `query s3`, `presto` |
| Redshift | `Redshift` | `[(Redshift)]` | 5439 | `redshift`, `data warehouse`, `dw` |
| QuickSight | `QS` | `[QuickSight]` | — | `quicksight`, `bi`, `dashboard` |
| Cognito | `Cognito` | `[Cognito User Pool]` | — | `cognito`, `user pool`, `auth` |
| Secrets Manager | `SM` | `[Secrets Manager]` | — | `secrets manager`, `secret`, `secrets` |
| SSM Parameter Store | `SSM` | `[SSM Parameter Store]` | — | `ssm`, `parameter store`, `config` |
| KMS | `KMS` | `[KMS]` | — | `kms`, `encryption key`, `key management` |
| CloudWatch Logs | `CW` | `[CloudWatch Logs]` | — | `cloudwatch`, `logs`, `logging` |
| X-Ray | `XRay` | `[X-Ray Tracing]` | — | `x-ray`, `xray`, `tracing` |
| ECR | `ECR<Purpose>` | `[ECR - <Purpose>]` | — | `ecr`, `container registry`, `docker registry` |
| CodePipeline | `CP` | `[CodePipeline]` | — | `codepipeline`, `cicd`, `ci/cd pipeline` |
| Step Functions | `SF<Purpose>` | `[Step Functions - <Purpose>]` | — | `step functions`, `sfn`, `state machine` |
| Bedrock | `Bedrock` | `[Bedrock]` | — | `bedrock`, `llm`, `genai`, `foundation model` |
| SageMaker | `SageMaker` | `[SageMaker]` | — | `sagemaker`, `ml inference`, `ml endpoint` |

**`<Purpose>` placeholder.** When the same service appears several times — three Lambdas, two
DynamoDB tables, four buckets — suffix the ID and label with a purpose token from the prompt:
`LambdaAuth`, `DDBOrders`, `S3Assets`. PascalCase for the ID, human-readable for the label.

---

## Topology inference

### Network boundaries

- **VPC subgraph** — emit whenever any VPC-bound service is present (ALB/NLB, ECS/EKS/EC2,
  RDS/Aurora, ElastiCache, EFS). Label `VPC ("10.0.0.0/16")` — the CIDR is illustrative; **do not
  invent project-specific CIDRs**.
- **Public subnet subgraph** — when a **public-facing** ALB or NLB, or a NAT gateway, is present.
  Holds those. An internal-only load balancer does not put anything in it.

  > The two rules read as conflicting otherwise: "public subnet when ALB is present" against
  > "ALB → public **unless internal**". In `static-spa` the only ALB *is* internal, so a literal
  > reading mandates a `public-subnets` subgraph with nothing inside it. Omit an empty subgraph — it
  > tells the reader a tier exists that does not.
- **Private subnet subgraph** — when any private-tier service is present.
- **No VPC subgraph at all** when nothing is VPC-bound — a pure serverless stack of Lambda, DynamoDB,
  S3 and API Gateway gets none.

### Placement defaults

| Category | Placement |
|---|---|
| ALB, NLB | public subnet — **unless internal**, then private |
| NAT, IGW | public subnet; do not draw unless the prompt mentions them |
| ECS task, EKS node, EC2 | private subnet |
| **ECS Cluster** | inside the VPC subgraph but **outside any subnet** — it is a control-plane namespace, not a network resource |
| RDS, Aurora, DocumentDB, ElastiCache, EFS | private subnet |
| Lambda, VPC-attached | private subnet |
| Lambda, non-VPC | outside any subgraph |
| API Gateway, CloudFront, Route 53, S3, DynamoDB, SQS, SNS, EventBridge, Athena, Glue | outside any VPC subgraph — regional or global services |

### Edge labels — the format is exact

| Edge | Label | Arrow |
|---|---|---|
| HTTP/HTTPS | `HTTPS 443` / `HTTP <port>` | `-->` |
| Database | `port <num>` | `-->` |
| Cache | `port <num>` | `-->` |
| Object storage | `S3 API` or `read/write` | `-->` |
| Secrets | `secrets` | `-->` |
| Logs | `logs` | `-->` |
| Queue publish | `publish` | `-->` |
| Queue consume | `consume` / `trigger` | `-->` |
| **Queue → DLQ redrive** | `redrive` | **`-.->` dotted** |
| CloudWatch alarm / dashboard | `metrics` | **`-.->` dotted** |
| Auth | `auth` / `validate token` | `-->` |
| **DNS alias** | `alias` | **`-.->` dotted** |
| **ECR image pull** | `image` | **`-.->` dotted** |

> **Emit these labels verbatim.** Port labels are bare numbers. `HTTPS :443` is wrong — no colon.
> `TCP 5432` is wrong — use `port 5432`.

> **Route 53 is name resolution, not a traffic hop.** Do **not** draw `User -->|HTTPS …| R53`. DNS
> uses port 53, and the browser hits the target directly after resolving. Draw
> `R53 -.->|alias| <target>` (dotted, advisory) plus `User -->|HTTPS 443| <target>` (solid, real
> traffic). R53 with no incoming edge is correct.

> **Redrive and metrics are dotted for the same reason as ECR: neither is request-path traffic.** A
> message reaches the DLQ only after `maxReceiveCount` failures, and an alarm reads a metric stream
> rather than receiving a call. Drawing either solid puts a path in the diagram that no request ever
> takes.

> **ECR edges are dotted because ECR is consumed at deploy time, not runtime.** The edge shows which
> registry a service pulls from without implying live traffic.

Logs edges follow the same alphabetical sort as any other edge — do **not** group them separately.
