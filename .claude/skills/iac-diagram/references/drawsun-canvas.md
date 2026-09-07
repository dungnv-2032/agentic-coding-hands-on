# Canvas Output (opt-in)

> ### `DRAWSUN_ENDPOINT` is UNSET by default. With it unset, the canvas leg is never offered.
>
> The upstream kit hardcoded a LAN IP reachable only from one office network. Here it is a contract
> key with no default, so the feature simply does not exist for anyone who has not configured it —
> no probe, no prompt, no failed connection.

Resolve the endpoint through
[`layout-contract.md`](../../_shared/extras/iac/layout-contract.md).

## Protocol — probe, then ask once

1. **`DRAWSUN_ENDPOINT` unset** → stop. Do not mention the canvas.
2. **Set** → probe the MCP server first.
3. **Probe fails** → say so in one line and continue. The Mermaid file is the deliverable; a
   missing canvas is not an error.
4. **Probe succeeds** → ask **once** whether to push. Never ask twice, never ask before probing.

## It is an additional sink, never a handoff

The canvas runs **after** the file is written and **never changes** the file-mode output.

It is documentation-only, exactly like file mode. It never couples into environment generation,
module generation, wiring, or any reviewer. **The canvas tools are an output sink, never an IaC
handoff.**

## Dialect differences

The canvas renderer is not plain Mermaid. Three differences, all of which the sanity checks account
for:

| | File mode | Canvas mode |
|---|---|---|
| Keyword | `graph TD` / `graph LR` | **`flowchart`** — the renderer rejects `graph` |
| Labels | quoted only when they contain brackets or colons | **every** label double-quoted |
| Icons | none | every label carries a `provider/service::` icon-key prefix |

Sanity check 1 accepts `flowchart` in this mode; check 5 additionally requires the quoting and the
icon-key prefix.

## Route 53 renders differently here

File mode draws `R53 -.->|alias| <target>` and keeps the real traffic edge going straight to the
target, because DNS is name resolution rather than a hop.

**Canvas mode overrides that** — its layout engine needs the resolution edge to place the node. This
is the one place the two dialects genuinely disagree, and it is a rendering concern, not a modelling
one. Do not carry the canvas edge model back into the file output.
