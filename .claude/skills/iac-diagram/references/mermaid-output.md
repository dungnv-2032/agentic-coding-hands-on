# Mermaid Output Contract

Path keys resolve through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

## File location

```
{DOCS_DIR}/generated-<name>.mermaid
```

`<name>` is sanitised to kebab-case: no spaces, ASCII only.

> **The deliverable does not go in `{WORK_DIR}`.** That directory is contractually scratch and must
> be gitignored, so a diagram written there is invisible to `git add -A` and deleted by
> `git clean -fdx` — for a skill whose entire purpose is producing a document someone keeps, that is
> the wrong destination. Diff mode's intermediate JSON is scratch and belongs there; the `.mermaid`
> file does not.
>
> `{DOCS_DIR}` defaults to `docs/`. If the project has no such directory, write beside the
> environment being diagrammed and say where it went.

**Overwrite without prompting.** That is the idempotency contract — re-running the same prompt
regenerates the same file.

## File structure

Section order is **Nodes → Edges → Network boundaries**, closing with the VPC subgraph when present.

```
graph TD
    %% --- Nodes ---
    <NodeID>[<Label>]

    %% --- Edges ---
    <Source> -->|<edge label>| <Target>

    %% --- Network boundaries ---
    subgraph VPC["VPC (10.0.0.0/16)"]
        subgraph public-subnets["Public Subnets (AZ-a, AZ-c)"]
            <PublicNodeID>
        end
        subgraph private-subnets["Private Subnets (AZ-a, AZ-c)"]
            <PrivateNodeID>
        end
    end
```

The three `%% --- … ---` section comments are **required**.

## Node shapes

| Shape | Used for | Syntax |
|---|---|---|
| Rectangle `[…]` | compute, networking, app services — the default | `ECS[ECS Fargate Service]` |
| Stadium `([…])` | external actors | `User([User / Browser])` |
| Cylinder `[(…)]` | databases | `RDS[(Aurora PostgreSQL)]` |
| Rounded `(…)` | optional or future components | `Future(Optional component)` |

> **Quote any label containing `(`, `)`, `[`, `]`, `:` or `"`.** Mermaid's parser reads a bare
> bracket inside `[...]` as a competing shape, so `[Application Load Balancer (Backend)]` **fails to
> parse**. Write `["Application Load Balancer (Backend)"]`. Labels with only alphanumerics, spaces,
> hyphens, slashes and dots are safe unquoted.

## No commentary in the diagram

`%%` is for the three section markers. **No `%% TODO`, no `%% FIXME`.** The diagram is a deliverable,
not a draft.

---

## The six sanity checks

Run **before** writing. If any fails, **do not write the file**.

1. **Opening declaration** — the first non-comment line is `graph TD`, or `graph LR` for wide
   pipelines with many parallel branches. Prefer `TD` for vertical app stacks. *(Canvas mode uses
   `flowchart` instead — see [`drawsun-canvas.md`](./drawsun-canvas.md).)*
2. **Balanced subgraphs** — every `subgraph` has a matching `end` at the same indent level.
3. **Node IDs are unique** — no duplicate declarations.
4. **Every edge endpoint exists** — every source and target appears as a node declaration above.
5. **No undefined keywords** — only `graph`, `flowchart`, `subgraph`, `end`, `-->`, `---`, `-.->`,
   `==>`, `%%`.
6. **Node count ≤ 30** — beyond that, ask the user to split into sub-diagrams.

On failure: print the **check number** and the offending lines, then ask whether to retry with
adjusted topology or abort.

**At most 2 retries.** If both fail, abort and surface the diagnostic. On abort, print
`Aborted. No file was written.`

> A broken diagram is worse than no diagram — it looks like an answer. That is why the checks run
> before the write, not after.

## Idempotency

**Blueprint mode is byte-identical.** Rendered from the fixed lookup table with no inference, the
same `{blueprint, variant, backend_services, route53}` tuple produces the same bytes in any session.

**NL mode is structurally stable, not byte-identical.** Node IDs are sorted alphabetically within
each section, which is what keeps a re-run's diff readable.
