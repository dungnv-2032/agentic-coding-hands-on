# Canonical Project Document Layout

The single source of truth for **where project documents live and what they are called**. Every skill and
agent in this kit reads and writes these paths verbatim — never invent a variant prefix (`docs/`,
`documents/`, `project-docs/`) or a variant filename. If a path is not listed here, it is not part of the
managed layout.

## 1. The Tree

All managed documents live under **`project/`** at the repository root.

```
project/
├── 01_management/
│   ├── overview.md                       # contract, org, way of working, constraints   (PLAN)
│   ├── stakeholders.md                   # organization, approval & escalation flow     (PLAN)
│   ├── qa.md                             # open items for the customer (planning)       (PLAN)
│   ├── schedule.md                       # master schedule, milestones, WBS             (SCH)
│   ├── progress.md                       # actual progress against plan                 (REP)
│   ├── task-list.md                      # tasks + GitHub Issue links                   (TASK)
│   ├── define-dod.md                     # completion criteria, closing judgement       (DOD)
│   ├── decision.md                       # settled decisions (PM; skills never edit)
│   ├── stories/
│   │   └── story-{WBS ID}-{name}.md      # story details                                (STORY)
│   ├── reports/
│   │   └── {YYYY-MM-DD}-weekly-report.md # client-facing weekly report                  (REP)
│   ├── risks-problems/
│   │   ├── risk-list.md                  # risks (not yet happened)                     (RISK)
│   │   └── problem-list.md               # issues (already happened)                    (RISK)
│   └── mtg-logs/                         # meeting minutes (input only)
├── 02_requirements/
│   ├── system-overview.md                # service overview, background, objectives     (REQ)
│   ├── role-list.md                      # roles + permission matrix                    (REQ)
│   ├── function-list.md                  # function list (scope)                        (REQ)
│   ├── non-function-list.md              # non-functional requirements                  (REQ)
│   ├── glossary.md                       # glossary                                     (REQ)
│   ├── qa.md                             # open items for the customer (requirements)   (REQ)
│   └── functions/                        # per-function details                          (FA)
├── 03_basic-design/
│   └── system-design/architecture.md     # read-only input for TEST
├── 04_screen-design/
│   └── screen-list.md                    # formal screen design (later phase)
├── 05_test/
│   ├── test-plan.md                      # test plan                                    (TEST)
│   ├── test-schedule.md                  # test milestones + test WBS                   (TEST)
│   ├── qa.md                             # open items for the customer (test)           (TEST)
│   └── testcase/                         # test cases (test execution phase)
├── 07_feedbacks/
│   ├── feedback-list.md                  # day-to-day feedback tracker                  (FB)
│   └── change-request.md                 # change requests (CR)
└── 09_wip_plan/
    └── brainstorming-{YYYY-MM-DD}-{N}.md # brainstorming session records                (BS)
```

`09_wip_plan/` is the **pre-decision** area: a brainstorming session record is written there before anything
becomes a requirement, and it is self-contained — its open questions live in the session file's `## 8`, not in
`02_requirements/qa.md`. Ideas leave it only when their owning skill (`REQ` for `function-list.md`, `RISK` for
`risk-list.md`) carries them across.

`plans/` sits **outside** `project/` on purpose — it is an exploratory scratch area, not a managed deliverable.
Two roots are reserved there, one per persona:

- **`plans/project-management/`** — the PM's, with `screens/` as the `WF` wireframe workspace. It holds
  **`pm-memory.md`**, the `project-manager` agent's own working notes (which skill got how far,
  `What to do next`, `GitHub Settings`).
- **`plans/business-analysis/`** — the BA's. It holds **`ba-memory.md`**, the `business-analyst` agent's own
  working notes (how far each feature's analysis got, `Open Items`, `What To Do Next`).

Both memory files are agent state, not project deliverables: the kit ships neither, each agent creates its own
on first run, and they are deliberately kept out of any harness-specific directory so the same notes are found
whichever coding agent runs this kit.

## 2. Naming Rules

- **Prefix is always `project/`**, never `docs/`. The numbered phase folders (`01_management`,
  `02_requirements`, …) are part of the path and never abbreviated.
- The requirements overview is **`system-overview.md`** (not `project-overview.md`). `overview.md` under
  `01_management/` is a different document (contract & organization) — never conflate the two.
- Story files are `stories/story-{WBS ID}-{name}.md`, e.g.
  `story-E-01-S01-business-requirements-interview.md`. The WBS ID is inherited verbatim from
  `schedule.md` §3.
- Weekly reports are `reports/{YYYY-MM-DD}-weekly-report.md`.
- Per-function detail documents are `02_requirements/functions/function-{No}-{slug}.md`, where `{No}` is the
  numeric part of the `F-ID` (`F-001` → `1`) and `{slug}` is a short kebab-case English slug.
- Brainstorming session records are `09_wip_plan/brainstorming-{YYYY-MM-DD}-{N}.md`, where `{N}` is the session
  number **within that date**, starting at 1 — the first session of a day is `-1`, not a template.

## 3. Missing Files Are Normal — Never Dead-End

This kit ships **no `project/` tree**. A consumer installs it into a repository that may have nothing under
`project/` at all, so every skill must handle "the file is not there yet".

- **The owning skill creates its own files.** Each skill listed above owns a set of files and ships their
  skeletons in `references/skeletons.md`. When an owned file is missing or empty, `Write` it from that
  skeleton and continue — never stop with "the template cannot be found".
- **Files you do not own are read-only, and their absence is data.** Treat a missing `schedule.md` the same
  way you treat one whose §3 holds only `<!-- e.g. ... -->` examples: "not started". Report it and point at
  the skill that owns it (`pm-plan-schedule`/SCH here) instead of creating it yourself.
- **A skeleton is not content.** Creating the file from a skeleton never counts as filling it in — the
  interview still has to happen, and the placeholder rows still have to be replaced.
