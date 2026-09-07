<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Test-Cases Researcher Contract (Wave TC.1 — rebuild-spec v26.1.0)

## Session Context

Read `plans/<active-plan>/artifacts/_session-context.md` FIRST before any other read.
Do NOT re-derive information already present there.

## Synthesis Sources (read ALL before drafting any test case)

Read these upstream artifacts from `docs/` (already promoted by the feature-specs pass — NOT
`plans/<active>/artifacts/`), for the ONE feature you were assigned:

- `docs/features/{fcode}/technical-spec.md` — PRIMARY source for UT/IT. Contains BR-###/SM-###
  (`## Cross-Cutting Logic`), `#### DEC-###` (Decision Logic), `### DISC-###` (Polymorphic
  Behavior) blocks, each already carrying a `**Source:**` citation. One test case per BR, one per
  SM state-transition, one per DISC-### value, one per DEC-### outcome — this is EXPAND, not
  synthesize; the codes and citations already exist, you are re-shaping them into Given/When/Then.
- `docs/features/{fcode}/functional-spec.md` § 8 Edge Cases — already test-case-shaped
  (`Scenario | What Happens | User-Facing Message` table). Maps directly to negative-path UT/IT
  rows.
- `docs/features/{fcode}/functional-spec.md` § 5 Screens (`### User Journey`) and § 1 Overview —
  UAT scenario source. Optional enrichment; skip if the feature is background-only (§ 5 says
  `N/A — background feature; no user-facing screens`).

You are **NOT** authorized to read source code directly for this pass — every claim you write
must already be traceable to one of the 2 files above (each of which already carries its own
`**Source:**` citation back to real code). This pass is a re-projection of already-cited content,
not a new detection surface: if a behaviour is not already stated in one of those 2 files, it does
not enter this artifact — the fix is to correct the feature spec, never to detect it here.

## Gate/Filter (STRICT — hard-omit, no invented scenarios)

- Every UT/IT test case MUST trace to a concrete BR-###/SM-###/DEC-###/DISC-### code in
  `technical-spec.md`, OR a row in `functional-spec.md` § 8 Edge Cases.
- Every UAT test case MUST trace to a `### User Journey` step or a screen row in `functional-spec.md` § 5 Screens.
- A code/row/step with no plausible test scenario is simply NOT expanded — do NOT pad the table
  with a low-value row to "cover" it. Under-coverage is surfaced by the deterministic coverage-gap
  check (Wave TC.2), not papered over here.
- NEVER invent a Given/When/Then that has no upstream basis. Unsourced idea → do not write it.

## TC### Code Grammar (per-feature reset — F15)

Format: `TC###` — 3-digit zero-padded, **resets per feature** (scoped the way `REG###` resets
per `SCR###`, NOT file-global like `F###`). Regex: `^TC\d{3}$`.

- Sequential assignment within this ONE feature's `test-cases.md`, starting at `TC001`.
- No slug suffix (unlike `F###_Slug`) — a per-feature test-case table is small
  enough that a bare number is unambiguous within the file; the file path itself
  (`docs/features/{fcode}/test-cases.md`) is the disambiguating scope.

## Citation Rule — UT/IT vs UAT split (anti-hallucination, risk (b))

The **Traces-to** column's citation-source family MUST match the row's **Type**:

- **UT / IT rows:** Traces-to MUST contain a `BR-###`/`SM-###`/`DEC-###`/`DISC-###` code (copy
  verbatim from `technical-spec.md`), a `` `file:line` `` citation, or an explicit reference to a
  `functional-spec.md` § 8 Edge Cases row (e.g. `functional-spec.md § EC-1`).
- **UAT rows:** Traces-to MUST reference a `functional-spec.md` section (e.g.
  `functional-spec.md § User Journey step 2`) — NEVER a bare code. UAT is inherently less
  code-traceable than UT/IT; citing a code here would silently degrade the UAT citation
  discipline to code-only, which is exactly the risk this split guards against.
- A UT/IT row citing only a functional-spec.md section that is not actually the § 8 Edge Cases
  content (no code, no file:line, no genuine edge-case reference), or a UAT row citing only a bare
  code, is a **citation-source mismatch** — `validate_test_cases.py` flags this as critical.

## DRY Boundary (test-cases.md vs technical-spec.md / functional-spec.md)

- Do NOT re-list a BR/SM/DEC/DISC block's full description verbatim in the Given/When/Then cells
  — restate it as a concrete scenario (input → action → expected outcome), not a copy of the rule
  prose.
- `functional-spec.md` § 8 Edge Cases rows may be copied near-verbatim into Given/When/Then (they
  are already test-case-shaped) — this is expected reuse, not a DRY violation, since that section
  IS the canonical source for those scenarios.

## Coverage Notes (optional — feeds the TC.2 coverage-gap WARN)

If a BR/SM/DEC/DISC code in `technical-spec.md` deliberately has NO tracing test case (e.g. a
pure logging side-effect with nothing observable to assert), list it under `## Coverage Notes`
with the `[NO_TEST_CASE]` marker and a one-line rationale. This suppresses the coverage-gap WARN
for that code — an unlisted, uncovered code still WARNs (non-halting; 100% coverage is not always
achievable, per the plan's Decision).

## Output

Single file: `plans/<active>/artifacts/features/{fcode}/test-cases.md`. Template:
`templates/test-cases-template.md`. Do NOT touch the other files already in that folder — this
pass writes ONLY `test-cases.md` (SIDECAR — see § Sidecar Boundary below).

Zero derivable test cases (rare — e.g. a trivial feature with no BR/SM/DEC/DISC and no edge
cases) → still emit the file with the header/preamble intact and a `## Test Cases` table
containing only `_(no test cases derived — feature has no BR/SM/DEC/DISC codes or edge cases)_`
— never omit the file.

### CSV Export (OUT OF SCOPE v1)

Markdown is the PRIMARY and ONLY output for v1. A `.csv` export was considered and explicitly
deferred (zero prior CSV precedent anywhere in this kit) — do not emit a `.csv` file.

### Confidence Companion (advisory sidecar)

`confidence-report_test-cases.md` is NOT part of the researcher's output above. It is emitted
automatically by `scripts/derive_confidence_report.py` (deterministic, not authored by the
researcher) after promotion. See `references/confidence-report-contract.md`.

## Sidecar Boundary (CRITICAL — do not confuse with the mandatory 2)

`test-cases.md` is a 3rd file living in the SAME directory as the mandatory 2
(`technical-spec.md`, `functional-spec.md`), but it is **SIDECAR** — never added to the
`FEATURE_FILES` tuple (`scripts/_slug_lib.py`), never checked by `check_promotion_gate.py`, never
part of `scaffold_spec.py`'s 2-file scaffold, and never mentioned in
`verification-checklist-universal.md`'s per-feature-drafts liveness line. Its absence NEVER
blocks feature-spec promotion. Mirrors the A1 `confidence-report_*.md` companion precedent (same
principle, different reason: A1 is a machine-derived stat sidecar; `test-cases.md` is a real
researcher-authored deliverable that simply arrived on a separate, later, optional pass).

## Completion Marker

After the file is fully written (including the zero-derivable-cases case), write:

```
plans/<active>/artifacts/features/{fcode}/.test-cases-completed
```

## See Also

- `references/feature-spec-researcher-contract.md` § Sidecar Files — the mandatory-4 boundary
  this file must never cross
- `references/verification-checklist-test-cases.md` — TC-S1..TC-S6 semantic review rules
- `templates/test-cases-template.md` — output template
- `scripts/validate_test_cases.py` — deterministic gate (TC### regex, citation-family match,
  coverage-gap WARN)
