# Wiring Rules

Resolving `# TODO` placeholders into real Terraform references.

Path keys resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

## Step 1 — Read source outputs

For each source layer, read `{ENV_DIR}/<source-layer>/_outputs.tf` and extract every output block
name, plus the `module.<name>` each one references in its `value` — the module name is what same-layer
wiring needs.

Store as a map of `output_key → { module_name, value_expr }` per source layer.

A source layer with no `_outputs.tf` is skipped, with a note: `No _outputs.tf found in <layer> —
skipping as source.` Not an error; a layer may legitimately export nothing.

## Step 2 — Scan the target for TODOs

Read every `.tf` in the target layer **except** `_backend.tf`, `_outputs.tf`, `_data.tf` and
`_variables.tf`.

**Match in priority order:**

| Priority | Rule |
|---|---|
| PRIMARY | line contains `run the wiring step` → a connect-TODO |
| FALLBACK | line contains `connect from` → a connect-TODO |
| REJECT | any other `# TODO:` → **not** a connect-TODO, skip it |

`run the wiring step` is the exact phrase the generator emits. The two must stay in lockstep: change
one and every placeholder written by the other becomes invisible to this scan, shipping unresolved.

The reject rule matters: a generation run leaves TODOs for things a human must supply — an AMI id, a
key pair name. Wiring those is not this step's job, and treating them as connect-TODOs produces
confident wrong references.

**Indentation is irrelevant.** A TODO may sit at any depth — top level, inside an object literal,
inside a list of objects:

```hcl
alb = {
  security_groups_id = [] # TODO: connect from security-group — run the wiring step
  subnets_id         = [] # TODO: connect from vpc — run the wiring step
}
```

Record for each match: file, line number, the raw line, and the hinted key.

**Hinted-key extraction**, in priority order:

1. TODO contains `module.<name>.<key>` → the key
2. TODO contains the wiring phrase → the identifier before `—` or after `from`
3. an underscore-separated identifier that is a suffix of a known output key → that key
4. a service name (`vpc`, `rds`, `alb`) → a source hint for matching
5. otherwise → null, unmatched

## Step 3 — Match TODOs to outputs

### Rule 0 — LHS inference, highest priority

Before any service-name matching, take the identifier immediately left of `=` on the TODO's line.

- **Exact match** against one output key in any source → matched.
  `vpc_id = ""` → `module.vpc.vpc_id`.
- **Substring match** — the LHS is a substring of exactly one output key across all sources → matched.
  `security_group_ids = []` → the one output containing `security_group`.
- If exactly one match: use it, skip rules 1–3.
- If several remain: fall through to the rules below as tiebreaker.
  `subnet_ids = []` matches `subnet_private_id` **and** `subnet_public_id` — resolve by consumer
  (private for ECS, RDS and other internal resources; public for a **public** load balancer), and
  ask if still ambiguous.

  > **"ALB → public" is wrong whenever the ALB is internal, and it is internal by default in two of
  > three variants.** Phase A sets `alb_backend_internal = true` for `static-spa` and `ssr`, where the
  > backend ALB sits behind CloudFront or the frontend ECS. Read the block's own `internal` input —
  > `internal = true` → **private** subnets — and only fall back to the service-name heuristic when
  > there is no such input to read.
  >
  > Getting this backwards puts the backend load balancer on public subnets, reachable from the
  > internet, in an environment whose whole design assumes it is not. That is a security outcome, not
  > a wiring preference, so the input wins over the heuristic every time.
  >
  > Upstream carries the same heuristic without this exception. It is corrected here deliberately.
- A standalone comment TODO has no LHS: skip Rule 0.

Rule 0 is first because the variable being assigned is stronger evidence than the prose in a comment.

### Rules 1–5

1. Hinted key exact-matches a key in any source → matched.
2. Hinted key is a suffix or substring of exactly one key across all sources → matched.
3. Hinted key matches a service hint → all outputs from that service; exactly one → matched.
4. Several matches across sources → **ambiguous → ask.** Present a numbered menu of candidates.
5. No match → unmatched, with the reason recorded.

**Never resolve an ambiguity by picking the first candidate.** A wrong security-group reference
produces Terraform that applies cleanly and connects the wrong tiers.

### Security-group tiebreak

`security_group_ids = []` is the common ambiguous case, because a layer exports several `sg_*_id`
outputs.

1. Read the **consumer's** resource-type token from the surrounding `module "<name>"` block:
   `module "ecs_backend_api"` → `ecs`; `module "rds"` → `rds`; `module "alb_backend"` → `alb`.
2. Look for an SG output matching that token — `module.sg_<token>.security_group_id` same-layer, or
   `data.terraform_remote_state.<alias>.outputs.sg_<token>_id` cross-layer.
3. **Tier disambiguation** — if the consumer block name carries a tier suffix (`_fe`, `_be`,
   `_frontend`, `_backend`), prefer the matching tiered output (`sg_<token>_fe_id` over
   `sg_<token>_id`). If only the untiered output exists, use it.
4. Still ambiguous → **halt and show a numbered menu.**

### Pre-flight check

Collect the service names referenced in TODO hints. For each, check whether any provided source layer
covers it — matching the alias derived by stripping the numeric prefix. Warn before proceeding:

```
Warning: TODO hints reference '<service>' but no source layer for it was provided.
These TODOs will remain unmatched.
```

Better to say this up front than to report a pile of unmatched rows at the end.

## Step 4 — Append remote-state blocks (idempotent)

For each cross-layer source with at least one matched TODO.

If `_backend.tf` is missing in the target, **stop**:

```
Error: _backend.tf not found in <target layer>. Generate the layer first.
```

**Idempotency check:** search for `data "terraform_remote_state" "<alias>"`.

- Already present → skip, and say so.
- Absent → append at the end of `_backend.tf`:

```hcl

data "terraform_remote_state" "<alias>" {
  backend = "s3"
  config = {
    profile = "${var.project}-${var.env}"
    # Must match the canonical backend bucket exactly. Resolve STATE_BUCKET_PATTERN and
    # interpolate it; a project that overrides the key gets its own shape here too. Copying
    # the default verbatim points the cross-layer read at a bucket that does not exist.
    bucket  = "{STATE_BUCKET_PATTERN, interpolated}"   # resolve the key — NOT the default shape
    key     = "<source-layer>/terraform.${var.env}.tfstate"
    region  = var.region
  }
}
```

The bucket shape is owned by the canonical backend block — cross-layer reads use the **same** bucket,
so the same suffix rule applies. `data.aws_caller_identity.current` is always present in
`_backend.tf`.

Change nothing else in `_backend.tf`.

## Step 5 — Replace matched TODOs

Same-layer reference: `module.<module_name>.<output_key>`, where the module name comes from the
source `_outputs.tf` `value` field.

Cross-layer reference: `data.terraform_remote_state.<alias>.outputs.<output_key>`.

**Case A — assignment with a TODO comment**

```hcl
subnet_ids = [] # TODO: connect from vpc — run the wiring step
→ subnet_ids = module.vpc.subnet_private_id
```

**Case B — empty string with a TODO**

```hcl
vpc_id = "" # TODO: connect from vpc — run the wiring step
→ vpc_id = module.vpc.vpc_id
```

**Case C — standalone comment TODO**

```hcl
# TODO: connect from security-group — run the wiring step
→ # Connected: module.security_group.security_group_id
```

A comment is replaced by a comment. There is no assignment to write.

**List versus scalar.** When the placeholder is `= []` and the matched output is a scalar string,
wrap the reference in brackets:

```hcl
security_group_ids = [module.sg_ecs.security_group_id]
```

When the placeholder is `= ""`, or the output is already a list, do **not** wrap. Getting this
backwards produces a type error at plan time.

**Case D — the matched output is a map, and the consumer wants one entry.** Subscript it by the
service key. `alb_backend` exports one target group per `api`-type service as a map, so a single
service's ECS block takes its own entry, never the whole map:

```hcl
target_group_arn = module.alb_backend.target_group_arns["api"]
```

The key is the **service name** from the blueprint, matching the key the ALB block used to build the
map. Passing the map unsubscripted is a type error; guessing a key that the ALB never created is a
plan-time failure naming a key that looks plausible.

**Case E — one input consumes several outputs.** Build the collection in place. `7.monitoring`'s
`ecs_service_names` needs every backend service, not one:

```hcl
ecs_service_names = {
  api    = data.terraform_remote_state.backend.outputs.ecs_backend_api_service_name
  worker = data.terraform_remote_state.backend.outputs.ecs_backend_worker_service_name
}
```

Enumerate from the blueprint's service list, in blueprint order, so a re-run produces the identical
collection. Cases A–C each assume one TODO resolves to one output; these two do not, and without them
the aggregate monitoring inputs and every multi-target-group ALB have no rule at all.

**Alignment.** Re-align the `=` to the surrounding block after substitution.

## Step 6 — Report

Write `{WORK_DIR}/step-N-report.md` and print:

```
Connect complete — <env>/<target layer>
─────────────────────────────────────────────────────────────────────
File              Input wired              Source              Type
─────────────────────────────────────────────────────────────────────
<file>            <input_var>              <alias>.<key>       cross-layer
<file>            <input_var>              module.<name>.<key> same-layer
<file>            <input_var>              (unmatched — <reason>)
─────────────────────────────────────────────────────────────────────
Matched:   <N>
Unmatched: <M> (see above)
```

Unmatched reasons: `output not found in any source layer` · `ambiguous — multiple keys match` ·
`source layer has no _outputs.tf`.

Nothing found at all:

```
No TODO connect placeholders found in <target layer>. Nothing to wire.
```

## Safety rules

- **Never overwrite `_variables.tf`** — it is a symlink managed by `make symlink`.
- **Never regenerate `_backend.tf`** — only append remote-state blocks.
- **Never modify files outside the target layer** — source layers are read-only.
- **Never add `depends_on`** — Terraform resolves the graph from direct output references. An
  unnecessary `depends_on` serializes what could run in parallel and hides the real dependency.
- **Idempotent** — re-running with the same inputs produces identical files: no duplicated blocks, no
  doubled replacements.
- **Never run `terraform init`, `plan`, or `apply`** here. This step edits files.
