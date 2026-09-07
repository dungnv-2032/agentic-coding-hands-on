# MoMorph Development Rules

> **Requires extras kit.** Both `momorph-implement-design` and
> `momorph-ui-implementer` ship in `extras`, not base. If either is unavailable,
> stop before the clarification/implementation workflow and instruct the user to
> run `tkm init --kit extras`; never fall back to generic `implementer`.

## Critical Rules

1. **NEVER guess visual values** — MCP design data is authoritative.
2. **Clarification is a hard gate** — finish the protocol below before starting either Track A or Track B.
3. **Select one test policy** — exactly `visual-contract` or `e2e-red-first`; never blend them or silently downgrade.
4. **`clarifications.md` is authoritative** — do not re-ask resolved decisions.
5. **Separate ownership** — `momorph-ui-implementer` owns presentational UI; `tester` owns executable E2E tests and browser/visual evidence; generic `implementer` keeps RED-first ownership of behavior and backend code.
6. **Extras is a hard dependency** — missing MoMorph skill or agent is blocking; never emulate it with a base agent.

## Test-policy Resolution

Resolve one value before creating a plan or spawning an agent:

1. Explicit `--e2e-test-first` selects `e2e-red-first` for this run.
2. Otherwise, a valid `test_policy` in the active MoMorph phase selects that value.
3. Otherwise, if the resolved specs, test cases, or clarifications contain behavioral interaction — form validation, navigation, modal open/close behavior, or another state transition — select `e2e-red-first`.
4. Otherwise default to `visual-contract`. Hover, focus, pressed, and responsive-only requirements remain visual-contract concerns.

An invalid plan value is blocking. Any `e2e-red-first` selection and `--no-test` are mutually exclusive, including policy auto-selected from behavioral test cases.

### `visual-contract` (default)

- Applies only to static/presentational Figma mapping. It is not TDD and MUST NOT claim RED/GREEN evidence.
- `momorph-ui-implementer` may code after clarification, then runs compile/typecheck, lint, and asset coverage.
- `tester` owns post-code visual validation: Playwright MCP capture for web; the existing simulator/screenshot path for mobile.
- Business logic, validation, state transitions, APIs, and persistence remain RED-first work for generic `implementer`.

### `e2e-red-first`

- Before Track A or Track B starts, `tester` creates or updates one durable screen-level E2E test from downloaded test cases plus resolved clarifications and runs the exact project command.
- A valid RED is a real non-zero exit caused by the requested screen assertion. Dependency/config/browser-install/dev-server failures do not count.
- Record `redTestFiles`, `redCommand`, `redExitCode`, and `redFailure`; pass them read-only to the UI agent. After implementation, `tester` reruns the same command GREEN and performs visual validation.
- Web requires an existing executable project E2E runner; Playwright MCP alone is not `@playwright/test`. Do not install or scaffold a runner and do not downgrade when it is absent — stop before implementation.
- Strict E2E is web-only in this version. A mobile `e2e-red-first` selection is BLOCKED as unsupported even when a mobile runner exists; ask the user to use `visual-contract` or defer until a mobile contract is defined.

## Clarification Gate

Complete every step before releasing either implementation track:

1. Resolve every `fileKey` and `screenId` from the request or active plan.
2. Fetch in parallel per screen: `get_frame(screenId)`, `download_specs(screen_id, "csv")`, and `download_test_cases(screen_id, "csv")`.
3. Deep-read every spec and test-case row; summarize components and user flows.
4. Cross-reference gaps in error states, navigation, persistence, loading/empty states, validation, integrations, responsive behavior, accessibility, localization, and security.
5. Present unresolved gaps as prioritized questions. Wait for all answers, including follow-ups.
6. Write decisions to `clarifications.md` using `.claude/templates/plans/clarifications.md`: one `- Q: ... → A: ...` line per decision under `## Session [date]`.
7. Resolve and preflight `test_policy`. For `e2e-red-first`, obtain valid tester RED evidence now.

## Parallel Execution Strategy

**OVERRIDE:** this section modifies `tkm:takumi` and `tkm:create-plan` only when MoMorph context is detected.

- **`tkm:takumi`:** after the Clarification Gate (and strict RED when selected), run Track A and Track B concurrently.
- **`tkm:create-plan`:** do not spawn implementation or tester agents. Represent one independent Track A phase per screen, chained Track B phases, and a late integration phase. Every Track A phase MUST include `test_policy: visual-contract|e2e-red-first`; keep it at most 30 lines with screen refs, one-line goal, out-of-scope list, optional integration contract, and the test policy.

### Track A — Presentational UI

Spawn one background `momorph-ui-implementer` per screen by default. When the extras skill identifies independent sections, the orchestrator may instead fan out a bounded set of `momorph-ui-implementer` jobs in explicit `section` mode with disjoint ownership. Section workers never spawn agents recursively. Never use generic `implementer` anywhere in Track A.

Each prompt MUST provide: `mode`, `testPolicy`, `fileKey`, `screenId`, `ownedFiles` or `outputPath`, `projectRoot`, `stack`, `testRunner`, `redTestFiles`, `redCommand`, `redExitCode`, `redFailure`, `redEvidence`, and `plannedChecks`. For `visual-contract`, use `testRunner: none` when no project runner exists, `redTestFiles: []`, `redCommand: not-applicable`, `redExitCode: not-applicable`, `redFailure: not-applicable`, and `redEvidence: not-applicable (visual-contract)`. Also include the specs/test-case paths, `clarifications.md`, project conventions, and: "Use Figma design content as mock data source. Do NOT invent data."

The UI agent activates `momorph-implement-design`, codes static components, and reports a GREEN/visual handoff. It does not own browser evidence or executable tests.

### Track B — Behavior and Backend

After the same gate, blueprint and implement API contracts, data models, state, validation, navigation, integrations, and real data sources without waiting for Track A. Use generic `implementer`; its normal RED-first contract remains unchanged.

### Tester Hand-off and Integration

As each screen agent completes:

1. `tester` reruns the strict command GREEN when applicable, then owns visual validation for every policy.
2. Treat any failed GREEN or material visual mismatch as incomplete; return the bounded UI fix to `momorph-ui-implementer` without weakening tests.
3. Integrate verified UI interfaces with Track B incrementally. There is no Track A/Track B merge barrier after the shared clarification/test gate.
