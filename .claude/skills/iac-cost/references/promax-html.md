# Promax HTML Report (opt-in)

A customer-facing standalone breakdown at `{ENV_DIR}/cost-promax.html`, beside `cost-summary.md`.

## Opt-in means opt-in

Generate it **only** when the caller passed `--promax`. There is no prompt: without the flag, write
nothing and print

```
Skipped promax HTML.
```

Do not ask, do not generate it "since the data was there anyway", and do not create it as a side
effect of `--full`. It is a customer-facing artifact; producing one unasked is a disclosure decision
made on the user's behalf.

> **Deviation from upstream.** The source asked once, interactively
> (`commands/estimate-cost.md:68-77`). A flag is the equivalent, non-interactive form and matches how
> this kit's skills take options. The refusal line is kept verbatim.

## Self-containment is mandatory

The file must open by double-click from disk, offline, on a machine with no network:

- inline `<style>` only
- **no** external CSS, JS, or font
- **no** `<script src>`, **no** `<img src="http…">`, **no** `fetch`, CDN, or `@import`
- **no** remote reference of any kind

A report that renders blank at a customer site because a CDN is unreachable is worse than a markdown
file.

## Must not embed

**No AWS account id. No ARN. No profile name. No secret.**

Resource specs and public prices only. This file leaves the building — treat everything identifying
as excluded by default rather than redacted on review.

## Structure

1. **Header** — project, environment, date, pricing source, and the disclaimer
   **"ESTIMATE — not a quote"**.
2. **Per-component detail table** — each resource → spec → monthly $.
3. **Environment comparison table** — one column per sibling environment. Print **`n/a`** for an
   environment with no cost data; never interpolate a figure, and never drop the column. A missing
   column reads as "that environment does not exist"; `n/a` reads as "not measured".

Tone is customer-facing: plain language, no internal jargon, no issue numbers, no layer slugs that
mean nothing outside the repository.

## Consistency with the markdown reports

The HTML is a **rendering of the same aggregation**, not a second calculation. Every figure in it
must match `cost-summary.md` exactly. If they can disagree, the HTML is being built from the wrong
source.
