# Service and Layer Normalization

Two lookups run before anything is written: which **module** a service name means, and which
**layer** a folder name means.

## Service name → canonical module

1. Replace `_` with `-` — `ec2_autoscaling` → `ec2-autoscaling`.
2. Apply the alias map below.
3. The result is the folder name under `{MODULE_DIR}/<canonical>/`.

| Input | Canonical module |
|---|---|
| `elasticache`, `cache`, `memcached` | `redis` |
| `cdn` | `cloudfront` |
| `dns` | `route53` |
| `email` | `ses` |
| `notification` | `sns` |
| `queue` | `sqs` |
| `secret`, `secrets` | `secrets-manager` |
| `parameter-store`, `param-store`, `ssm`, `parameter` | `ssm-parameter` |
| `certificate`, `cert`, `ssl` | `acm` |
| `firewall` | `waf` |
| `log`, `logging` | `cloudwatch` — parent; prompt for which `cloudwatch-*` sub-module |
| `alarm`, `monitoring` | `cloudwatch-alarm` |
| `dashboard` | `cloudwatch-dashboard` |
| `alb`, `load-balancer`, `lb` | `alb` |
| `aurora` | `rds-aurora` |
| `search`, `opensearch` | `elasticsearch` |
| `k8s`, `kubernetes` | `eks` |
| `ecs-cluster` | `ecs-cluster` |
| `ecs` | `ecs` |
| `registry` | `ecr` |
| `apigw`, `api-gateway`, `apigateway` | `rest-apigateway` |
| `identity`, `user-pool` | `cognito` |
| `budget` | `budgets` |
| `pipeline` | `codepipeline` |
| `build` | `codebuild` |
| `deploy` | `codedeploy` |
| `ec2-autoscaling`, `autoscaling` | `ec2-autoscaling` |
| `eip`, `elastic-ip` | `ec2-eip` |
| `vpc-eks`, `eks-vpc` | `vpc-eks` |
| `dax` | `dax` |

Sub-modules such as `rds-aurora`, `ec2-autoscaling` and `cloudwatch-alarm` are first-class folders,
not menu entries — an alias resolves straight to one.

**Unmatched input.** If the name is not in the map and `{MODULE_DIR}/<service>/` does not exist,
scaffold a module folder with that name. If the input cannot be resolved at all, **ask** rather than
guess — a wrong guess scaffolds a whole module tree under the wrong name.

`alb` covers blue/green through a toggle on the same module; there is no separate module for it.

## Layer folder normalization

An answer naming a **role** without its numeric prefix resolves to whatever that role's layer is
called in this project. Match the role, then take the name from `LAYERS` **by position**:

| Input | Role | Default name |
|---|---|---|
| `general`, `network` | 1 | `1.general` |
| `frontend`, `web` | 2 | `2.frontend` |
| `backend`, `api`, `services` | 3 | `3.backend` |
| `database`, `data` | 4 | `4.database` |
| `messaging`, `queue` | 5 | `5.messaging` |
| `delivery`, `deployment`, `release` | 6 | `6.delivery` |
| `monitor`, `monitoring`, `observability` | 7 | `7.monitoring` |

**The right-hand column is the default, not the answer.** In a project that overrides `LAYERS`,
`backend` resolves to that project's role-3 name — `3.services`, say — and normalizing it to
`3.backend` creates a directory nothing else references.

The canonical layer list is the `LAYERS` key in
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md), which is role-indexed for
exactly this reason.

An input that **already carries a numeric prefix** (`1.general`, `3.api`) or is fully custom
(`8.logging`) is used as-is. A real environment is not restricted to the seven names above.

**The numeric prefix is required.** `make init|plan|apply` takes `s=<layer>`, and the layer name is
also the state key — `key = "<layer>/terraform.<env>.tfstate"`. Dropping the prefix routes state to a
different path than every other tool expects.

## Validate before use

Both the resolved service name and the layer name are interpolated into filesystem paths and shell
commands. Constrain each to `^[A-Za-z0-9._-]+$` and reject anything else **before** it reaches a path
or a command.
