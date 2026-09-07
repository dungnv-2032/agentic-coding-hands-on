# Deployment Source Patterns

Reference for authoring the `## Deployment View` section of `architecture.md`
(`templates/architecture-template.md`, v27.13.0). Modelled on `bl-source-patterns.md`'s
shape — a documented pattern table the researcher/scanner selects from, not a list buried in
code. A stack's `deployment_sources` field (`stack-profiles/*.json`, see `_schema.md`) declares
which rows below are meaningful for that stack.

## Detection Modes

**Mode A — Filename glob.** The file's basename alone identifies it (`Dockerfile*`,
`Procfile`, `nginx.conf`, `fly.toml`, `wrangler.toml`, `vercel.json`, `app.yaml`).

**Mode B — Content sniff.** The filename is generic (`*.yaml`/`*.yml`) and the file must be
opened to confirm it is IaC — Kubernetes manifests are recognised by a top-level `kind:` value,
not by name.

## Source Pattern Table

| Pattern | Mode | Node signal | Edge / port / protocol signal | Citation anchor |
|---|---|---|---|---|
| `docker-compose*.y*ml` | A | one node per top-level `services.<name>` key | `ports:` (`HOST:CONTAINER[/proto]`) → edge to the host; `depends_on:` / same-network peers → inter-service edge | the `services.<name>:` key line; the specific `ports:`/`depends_on:` line for its edge |
| `Dockerfile*` | A | one node for the image/service the Dockerfile builds (name = containing dir or `docker-compose` service that references it) | `EXPOSE <port>[/proto]` | the `EXPOSE` line |
| k8s manifest (`kind: Deployment \| Service \| Ingress \| StatefulSet \| CronJob`) | B | one node per `metadata.name` under a `Deployment`/`StatefulSet`/`CronJob`; a `Service`/`Ingress` renders as the edge/entry-point, not a compute node | `Service.spec.ports` / `Ingress.spec.rules[].http.paths[].backend` | the `kind:` line + the specific `port`/`containerPort` line |
| `*.tf` | A | one node per `resource "<provider>_<type>" "<name>"` block that provisions compute/network (instance, container service, load balancer) | `ingress`/`egress` blocks, `port_mappings`, listener resources | the `resource "..." "..." {` line + the port attribute line |
| `*.service` / `*.timer` | A | one node for the unit (`[Service]` `ExecStart=` binary/host role) | `ListenStream=`/`ListenDatagram=` in a paired `.socket` unit, if present; otherwise no port signal | the `ExecStart=` line |
| `Procfile` | A | one node per process type (`web:`, `worker:`) | the process-type line itself carries no port; if the command binds an explicit `--port`/`-p`, cite that token | the process-type line |
| `nginx.conf` | A | one node for the reverse-proxy/host itself | `listen <port>` (inbound) + `proxy_pass http://<upstream>` (edge to the upstream node, carrying its port) | the `server { listen ... }` block + the `proxy_pass` line |
| `fly.toml` | A | one node for the Fly app (`app = "<name>"`) | `[[services]] internal_port` / `[[services.ports]] port` | the `internal_port`/`port` line |
| `wrangler.toml` | A | one node for the Worker (`name = "<name>"`) | edge-hosted — no listen port to cite; note the route/binding instead if one exists (`routes`/`route`) | the `name =` line (+ `routes`/`route` line if cited) |
| `vercel.json` | A | one node for the deployment target; `routes`/`rewrites` entries are edges to functions/origins | `routes[].dest` / `rewrites[].destination` | the matching `routes`/`rewrites` array entry |
| `app.yaml` | A | one node for the service (`service:` key, GAE-style) | `handlers[].url` → the routed path; no inbound port (PaaS-managed) | the `service:` line |

**Table is non-exhaustive.** A stack or file shape not listed here has no citable source for that
node/edge and per FR-7 is simply omitted from the diagram — never inferred.

## Merged diagram (no split)

Placement (which host/runtime a service runs on) and connectivity (what talks to what, on which
port) come from the **same source file** in every row above — a `docker-compose` service and its
`ports:` key live in one YAML document. Rendering them as two diagrams would duplicate that single
source of truth. `## Deployment View` is therefore **one** Mermaid `flowchart`, one `subgraph` per
host/node/runtime, with edges carrying port/protocol inline where the source states them.

## Citation invariant (FR-7)

Every node AND every edge in the rendered diagram carries a `` `file:line` `` citation (in the
accompanying table, not inside the Mermaid fence itself — Mermaid labels stay plain). A node or
edge with no citable source (per the table above) does not go in the diagram. Partial coverage
(e.g. a compose file describing 2 of 6 real services) is rendered as-is — honest and incomplete
beats invented and complete.

## Degradation contract (FR-5)

Zero files matching any row above (or the active stack's `deployment_sources` is empty/absent) →
the section renders exactly `N/A — no infrastructure-as-code found in repository.` in place of the
diagram and table, plus a WARN. This is never a FAIL. The rule it follows: an absent fact is
written out as an explicit `N/A — <what was not found> in source.` sentence, never left blank and
never guessed at — absence is stated, not inferred.

## Security

IaC files are the single most likely place in a repository to carry embedded secrets
(`environment:` blocks in `docker-compose.yml`, connection strings in `.tf` variables,
`Environment=` lines in `.service` units). Run `_credential_scrub_lib.py`'s scrub over every value
before it becomes a node label, edge label, or table cell. If a source line trips the gate, omit
that value and emit a WARN — never render a partially-masked string. Only names and ports belong in
the diagram; a diagram value is treated as externally visible (Phase 04 client export).
