---
name: tkm:iac-explain
description: >
  Explain a layer of generated Terraform in plain language — what each resource is, why its key
  settings were chosen, how it connects to the rest of the environment, what the backend does, and
  what the layer exports for other layers to consume.
  Read-only: it prints an explanation and writes no files.
  Use this to understand an unfamiliar environment, onboard someone onto generated infrastructure, or
  check that what was generated matches what was intended before applying it.
  SKIP: finding problems in the code rather than understanding it (→ tkm:iac-review);
  pricing the environment (→ tkm:iac-cost);
  drawing it as a diagram (→ tkm:iac-diagram).
category: iac
roles: [engineer, devops]
allowed-tools:
  - Read
  - Glob
  - Grep
argument-hint: "<env> <layer>"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: documentation-knowledge
triggers:
  - "explain terraform"
  - "explain this infrastructure"
  - "what does this layer do"
  - "walk me through the terraform"
  - "explain IaC"
  - "giải thích terraform"
---

# tkm:iac-explain

Reads a layer and explains it. **Writes nothing** — which is why `allowed-tools` grants no write
tool at all, rather than granting one and promising not to use it.

Paths resolve through
[`layout-contract.md`](../_shared/extras/iac/layout-contract.md); the target is
`{ENV_DIR}/{layer}/`.

## What it covers

1. **Every resource and module block** — what it creates, the key configuration choices and *why*
   they were made, and how it connects to the rest.
2. **`_backend.tf`** — state management and provider setup.
3. **`_outputs.tf`** — what is exported and how downstream layers consume it.
4. **A two-to-three sentence summary** of the whole layer.

## Output style

**Plain language. No HCL code blocks.** Someone reading this is trying to understand the
infrastructure, not review its syntax — pasting the code back at them explains nothing.

One short paragraph per resource or logical group.

Use the component names the reader already knows — the block names from the diagram or the
blueprint — so they can correlate what they are reading with what they drew.

```
**ALB (`alb_backend`)** — an Application Load Balancer in the public subnets. It listens on 443 and
forwards to the ECS service; port 80 redirects to 443 automatically.
```

## Rules

- **Write nothing.** No files, no edits, no scratch output.
- **Explain the *why*, not just the *what*.** "Creates an ALB" is the code restated. "Public because
  the backend is the internet-facing tier in this variant" is an explanation.
- **Say when something is a placeholder.** An unresolved `# TODO` or an empty `certificate_arn` is
  the most useful thing on the page — it is what will fail at apply.
- **Do not review.** Noticing a problem is fine; producing a findings list is `tkm:iac-review`'s job
  and a different output contract.
- **Do not invent intent.** If a setting's reason is not evident from the code or the contracts, say
  it is not evident rather than inventing a plausible rationale.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "A code block would make this clearer." | They have the code. They asked what it means. |
| "This security group looks wrong — I'll flag it." | Mention it plainly, but the findings contract belongs to the reviewer. |
| "I'll write the explanation to a file for them." | This skill has no write tool. Print it. |
| "The instance class is small, so it must be for cost." | If the reason is not evident, say so instead of guessing. |
