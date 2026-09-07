# Blueprint Interview

The 16 fields collected before generation starts. Ask **one at a time**, in this order — later
questions depend on earlier answers.

> ### Every field is validated before it reaches a shell or a path
>
> The upstream kit validated exactly one field. `sops_kms_profile` alone is interpolated into **five**
> shell positions and into a KMS alias name, and there is no harness-level command deny-list behind
> this skill. The validation column below is the only control.
>
> Minimum for **every** field that reaches a shell or a filesystem path: `^[A-Za-z0-9._-]+$`.

| # | Field | Values / default | Validation |
|---|---|---|---|
| 1 | `project` | lowercase kebab-case | `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$` — must match the bootstrap script's own rule, because it feeds `STATE_BUCKET_PATTERN` |
| 2 | `env` | `dev` / `stg` / `prod` | `^[A-Za-z0-9._-]+$`; reject anything else |
| 3 | `blueprint` | `ecs-system` | one of the known blueprint names |
| 4 | `frontend` | `none` / `static-spa` / `ssr` | exact literal |
| 5 | `backend_services` | list of `{name, type}`, `type ∈ {api, worker}`. Default `[{name: "api", type: "api"}]` | each `name` `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`; **at least one entry must be `api`**; order preserved |
| 6 | `route53` | bool, default `false` | — |
| 7 | `cache_engine` | `valkey` (default) / `redis` | exact literal. **There is no "no cache" answer** — see below |
| 8 | `db_engine` | `aurora-serverless` (default) / `aurora-provisioned` / `rds` | exact literal |
| 9 | `messaging` | bool, default `false` | — |
| 10 | `messaging_services` | subset of `{sqs, sns, ses}`; defaults to `["sqs"]` when `messaging = true` with an empty pick | each an exact literal; **`ses` requires `route53 = true`** |
| 11 | `monitoring` | bool, default `false` | — |
| 12 | `delivery` | bool, default `false` | — |
| 13 | `delivery_strategies` | map service → `ROLLING` / `BLUE_GREEN` | keys must be `api`-type services (plus `frontend` for `ssr` when opted in); **`worker` is never a key** |
| 14 | `alerting` | bool, default `false` | **rejected unless `monitoring = true`**; also needs the handler payloads — see below |
| 15 | `sops_kms_profile` | AWS profile name; **may be empty** | `^[A-Za-z0-9._-]+$` when non-empty — five shell positions plus the alias name |
| 16 | `sops_kms_alias` | alias without the `alias/` prefix; defaults to `SOPS_ALIAS_PATTERN` with its `alias/` prefix stripped | `^[A-Za-z0-9._-]+$` |

---

## Constraints between fields

These are rejections, not warnings. Each one exists because the combination cannot produce a working
environment.

- **`ses` requires `route53 = true`.** SES verification needs DKIM CNAMEs and a TXT record in a hosted
  zone. There is no external-zone path.
- **`alerting` requires `monitoring = true`.** It is a sub-toggle; the alerting pipeline wires into
  the alarm module's `alarm_actions`, which only exists when monitoring does.
- **`alerting` requires the Slack handler payloads to already exist in this repository.** They are
  roughly a thousand lines of reviewed code that **this kit does not ship** and that must never be
  re-authored from prose. Check for them at `{DEPS_ROOT}/lambda-function/` *before* accepting
  `alerting = true`, not at generation time.

  If they are absent, say so here and offer the two real choices — the user supplies the payloads, or
  the run proceeds with `alerting = false`. Outside the origin repository the second is normally the answer.

  Asking now is the whole point. Accept it here and the failure surfaces in phase B, mid-generation,
  where the single-continuous-turn rule leaves no good move: a `code_path` pointing at nothing still
  passes `terraform validate`, so the environment reports as fully wired and fails at apply time
  instead. See the vendored-payload guard in
  [`idempotency-matchers.md`](../../_shared/extras/iac/idempotency-matchers.md).
- **`worker` services are never keys in `delivery_strategies`.** A worker has no ALB target group, so
  CodeDeploy blue/green is impossible. Workers are forced `ROLLING`.
- **At least one backend service must be `api`.** The first `api` entry is the **primary** — its
  target group becomes the ALB listener's default action.

Any service absent from `delivery_strategies` defaults to `ROLLING`.

---

## What each field decides downstream

**`project`** is written verbatim into tfvars and resolved into the **static** backend literals. It is
what lets `<PROJECT_PREFIX>` resolve on the first run rather than leaving a placeholder for the user
to find-replace. Its regex must stay identical to the bootstrap script's, because both must produce
the same bucket name — see `STATE_BUCKET_PATTERN` in
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

**`frontend`** decides the layer set and the apply order:

| Variant | Layers |
|---|---|
| `none` | `1.general` → `3.backend` → `4.database` |
| `static-spa` / `ssr` | `1.general` → `3.backend` → **`2.frontend`** → `4.database` |

> **A cache is always provisioned, and `storage` is not a question either.** `cache_engine` picks
> *which* cache, never *whether*: exactly one database engine and one cache engine are emitted per
> environment. `s3_app_content` likewise comes from the `3.backend` loop unconditionally. Neither has
> a toggle, unlike `messaging`, `delivery` and `monitoring`.
>
> Say so when the operator asks for an environment without one, rather than generating it silently.
> An unwanted ElastiCache cluster is a real monthly bill someone has to notice on the invoice.
>
> This is an upstream limitation of the AIDD blueprint, carried over deliberately. Adding a toggle
> would mean designing infrastructure variants the source never had.

**`cache_engine`** selects the block, file, module, security group, tunable prefix and SOPS key
end-to-end: `valkey` → `sg_valkey`, `valkey_*`, `<PREFIX>_VALKEY_PASSWORD` (ACL auth); `redis` →
`sg_redis`, `redis_*`, `<PREFIX>_REDIS_AUTH_TOKEN` (legacy auth). Both are ElastiCache on 6379 with
the same `CacheClusterId` dimension — no other layer changes.

**`db_engine`** likewise selects the whole chain, and the monitoring dimension differs by engine:
`rds` exposes `DBInstanceIdentifier`, Aurora exposes `DBClusterIdentifier`.

**Each of `messaging`, `delivery`, `monitoring`** is a **regression boundary**. When false, the layer
is skipped entirely — no folder, no module calls, no cross-layer edges, **and no gated re-exports on
any other layer**. Every other layer's `_outputs.tf` stays byte-for-byte unchanged.

**`alerting = false`** keeps `7.monitoring` byte-for-byte passive.

**`sops_kms_profile` empty** is a legitimate answer: Phase A.6 creates nothing and records
`sops_kms_status = manual`. It is ignored entirely when the blueprint has no sensitive input.

---

## Before dispatching

Resolve `{ENV_DIR}` from the contract and confirm the target. Validate every field above **first** —
nothing unvalidated may reach a path, a command, or the KMS alias name.
