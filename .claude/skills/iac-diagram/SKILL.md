---
name: tkm:iac-diagram
description: >
  Turn a natural-language architecture description into a Mermaid diagram, or diff two Mermaid
  diagrams to see how an architecture changed. Maps 42 AWS services, infers VPC and subnet placement,
  and runs six syntax sanity checks before writing anything.
  Blueprint mode is deterministic — naming a known environment blueprint renders byte-identical
  output from a fixed table rather than inferring topology.
  Use this to document an architecture, sketch a design before building it, or compare two diagram
  revisions.
  This skill produces DOCUMENTATION ONLY and deliberately does not generate Terraform.
  SKIP: turning a diagram into Terraform (→ tkm:infra generate, which owns that);
  general-purpose non-AWS diagramming (→ the vendored mermaid reference);
  generating an actual environment (→ tkm:iac-generate-env).
category: iac
roles: [engineer, devops]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
argument-hint: "<prompt> | diff <file1> <file2>"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: documentation-knowledge
triggers:
  - "architecture diagram"
  - "generate mermaid diagram"
  - "diagram this architecture"
  - "AWS architecture diagram"
  - "diff diagrams"
  - "compare architecture diagrams"
  - "vẽ sơ đồ kiến trúc"
---

# tkm:iac-diagram

Two modes: generate a diagram from a description, or diff two existing ones.

Paths resolve through
[`layout-contract.md`](../_shared/extras/iac/layout-contract.md).

## This skill does not generate Terraform — and that is deliberate

Base `tkm:infra generate` turns a diagram into Terraform. **This one does not**, and it is not an
omission or an unfinished feature.

Upstream, the documentation pipeline was kept deliberately separate from the generation pipeline:
a diagram is a description of intent, and letting a sketch flow straight into infrastructure removes
the review step where someone decides the sketch was right. Environment generation here starts from
a **blueprint plus an interview**, not from a picture.

> **Do not "improve" this into a pipeline.** Wiring diagram → Terraform looks like an obvious win and
> is the single most likely well-intentioned change to this skill. The `SKIP:` clause names
> `tkm:infra generate` so a user who wants that is routed there instead of finding two skills that
> both half-do it.

## Generate mode

```
tkm:iac-diagram "<architecture description>"
```

1. **Route the mode** — blueprint if the prompt names a known blueprint, otherwise natural language.
   → [`diagram-schema.md`](./references/diagram-schema.md)
2. **Collect inputs.** At most **one** clarifying round, batching every unknown. Never guess a
   required field; never ask about formatting concerns.
3. **Map services and infer topology** from the same reference.
4. **Render** per [`mermaid-output.md`](./references/mermaid-output.md).
5. **Run the six sanity checks.** On failure, print the check number and offending lines, then offer
   retry or abort. **At most 2 retries**, then abort.
6. **Write** `{DOCS_DIR}/generated-<name>.mermaid`, overwriting without prompting. Not `{WORK_DIR}` — that is gitignored scratch, and this file is the deliverable.
7. **Canvas push** — only if `DRAWSUN_ENDPOINT` is set, only after probing, asked once.
   → [`drawsun-canvas.md`](./references/drawsun-canvas.md)

**The checks run before the write.** A broken diagram is worse than none — it looks like an answer.

## Diff mode

```
tkm:iac-diagram diff <file1> <file2>
```

Parse both into `{WORK_DIR}/parsed-diff-baseline.json` and `{WORK_DIR}/parsed-diff-new.json`, then
report the delta on screen: nodes added and removed, edges added and removed, subgraph changes.

**Mermaid only.** There is no Draw.io path — it was removed upstream and must not be revived.

This mode has no base-kit counterpart at all.

## Rules

- **Documentation only.** This skill never emits Terraform and never chains into a generator.
- **One clarifying round, maximum.** Batch the questions.
- **Sanity-check before writing.** Cap retries at 2, then abort with a diagnostic.
- **Overwrite the output file without prompting** — that is the idempotency contract.
- **Blueprint mode is byte-identical** for the same input tuple. Do not add inference to it.
- **Canvas is opt-in and unset by default.** Probe before offering; never offer when unset.
- **Emit edge labels verbatim** from the table. No colon before a port, no protocol substitution.
- **Never invent a project-specific VPC CIDR.** The one in the template is illustrative.
- **No `%% TODO` or `%% FIXME`** in output.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "I have the diagram, I may as well generate the Terraform." | That is base's job. This skill declining is the design. |
| "The user drew Route 53 in the traffic path, so I'll connect it." | DNS resolves, it does not carry traffic. Dotted alias edge. |
| "Two clarifying rounds would give a better diagram." | One. Batch the questions. |
| "Check 6 failed at 34 nodes but the diagram is fine." | Ask to split. The cap exists because past that, nobody reads it. |
| "The canvas endpoint is probably the default LAN address." | It is unset. Do not guess an endpoint. |

## References

- [`diagram-schema.md`](./references/diagram-schema.md) — mode routing, input schema, the 42-service mapping table, topology rules
- [`mermaid-output.md`](./references/mermaid-output.md) — output contract, node shapes, the six sanity checks
- [`drawsun-canvas.md`](./references/drawsun-canvas.md) — opt-in canvas dialect and probe protocol

Mermaid syntax reference lives in `_vendor-iac/mermaid-diagrams/`; AWS service-selection context in
`_vendor-iac/aws-solution-architect/`. Both are reference material, not routable skills.
