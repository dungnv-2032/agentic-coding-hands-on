<!-- layout-exempt: rebuild-spec owns all docs/generated|features paths — all references here are output targets or internal definitions -->
# Traceability Matrix

**Project**: {PROJECT_NAME}
**Generated**: {DATE}
**Scope**: {SCOPE}

**Re-projection, not detection.** Every ID below already exists in its source-of-record
artifact — this file invents nothing, and is never the first place an ID appears.

**Source of record per column:**
- `F###` <- `generated/feature-list.md`
- `SCR###` <- `generated/screen-list.md` (edge from feature-list.md's own `**Related Screens**:`)
- `US###` <- `generated/user-stories.md` (edge from feature-list.md's own `**Related User Stories**:`)
- `BL###` <- `generated/behavior-logic.md` (edge from feature-list.md's own `**Related Background Logic**:`)
- `ROUTE###` <- `generated/route-list.md` — this one column carries its OWN `F###` edge via
  the `Owner F###` column (no feature-list.md hop needed)
- `PERM###` <- `generated/permissions-matrix.md` (edge from feature-list.md's own `**Related Permissions**:`)
- `TC###` <- `features/{slug}/test-cases.md` (opt-in `--test-cases`; already scoped to one
  feature, no join needed) — **omit this column entirely when no feature has a
  test-cases.md**, never a blank column claiming zero tests

**No `docs/traceability/` namespace**: this is a SINGLE artifact under `generated/`, same
pattern as the other one-file `generated/` artifacts. Shard only if this file exceeds
800 LOC (`references/artifact-sharding.md`).

**Cell rule**: a cell holds a comma-separated ID list, or `—` when this feature genuinely
has none of that ID family. Never blank — a blank cell reads as "not checked," `—` reads as
"checked, none found."

**`TC###` resets per feature**: unlike every other column here (file-global within its own
source-of-record artifact), `TC###` numbering resets inside each feature's own
`test-cases.md` — the same code appearing on two rows is expected, not a collision.

---

## Matrix

| F### | SCR### | US### | BL### | ROUTE### | PERM### | TC### |
|------|--------|-------|-------|----------|---------|-------|
| {F001_CODE} | {F001_SCR_LIST} | {F001_US_LIST} | {F001_BL_LIST} | {F001_ROUTE_LIST} | {F001_PERM_LIST} | {F001_TC_LIST} |
| {F002_CODE} | — | {F002_US_LIST} | — | {F002_ROUTE_LIST} | {F002_PERM_LIST} | — |

<!-- The TC### column is OMITTED ENTIRELY (not left as an all-"—" column) when the
     --test-cases pass never ran — presence-driven, per FR-1/NFR. -->

---

## Cross-Reference Validation

- [x] Every `SCR###`/`US###`/`BL###`/`PERM###` cell is projected from
  `generated/feature-list.md`'s own per-feature `**Related X**:` bullets
- [x] Every `ROUTE###` cell is projected from `generated/route-list.md`'s own
  `Owner F###` column
- [x] Every `TC###` cell (when the column is present) is read from that feature's own
  `test-cases.md` — never another feature's
- [x] No ID in this matrix is invented — every printed code re-projects an existing
  source-of-record entry (`validate_traceability_matrix.py` WARNs on drift, never fails
  the pass)
