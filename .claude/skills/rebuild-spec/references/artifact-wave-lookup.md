# Artifact → wave lookup (`--artifact NAME`)

<!-- layout-exempt: relocated from SKILL.md — docs/ paths are rebuild-spec's own targets -->

Loaded on `--artifact <NAME>` only (SKILL.md § On-demand pipeline loading). Moved from SKILL.md — meaning unchanged, only its home.

<!-- layout-exempt: artifact→wave table — docs/ paths are rebuild-spec's own targets -->
| NAME | Wave | Upstream required | Pass |
|------|------|-------------------|------|
| `system-overview` | W1 | scout-report.md | core |
| `route-list` | W1 | scout-report.md | core |
| `data-model` | W1 | scout-report.md | core |
| `screen-list` / `screen-flow` | W2 | data-model.md + (route-view: route-list.md \| dfm-form: `_digest_extract_form_nav.json`) — produced whenever `screen_source != none`; route-list.md is NOT a prerequisite for non-web stacks | core |
| `behavior-logic` | W2 | screen-list.md + screen-flow.md | core |
| `permissions` | W3 | screen-list.md + behavior-logic.md | core |
| `user-stories` | W4 | permissions.md | core |
| `feature-list` | W5 | user-stories.md | core |
| `api-map` | W1+W2 | route-list.md + behavior-logic.md | core |
| `entities` / `overview` / `architecture` | W1 | scout-report.md | core |
| `api-contracts` | AC.1 | data-model.md + permissions.md + route-list.md + api-map.md + scout-report.md (run `--api-contracts`) | `--api-contracts` pass |
| `permissions-matrix` | W3 | behavior-logic.md | core |
| `crud-matrix` | W1.b | `_digest_extract_data_flow.json` (Wave 0.6; profile extractors) | core (stack-specific) |
| `db-objects` | W1.c | `_digest_extract_sql_schema.json` (Wave 0.6; profile extractors) | core (stack-specific) |
| `technical-spec` / `functional-spec` | FS.1 | feature-list.md (run `--feature-specs`) | `--feature-specs` pass |
| `process-flow` | FL.1 | docs/features/*/technical-spec.md (run `--flows`) | `--flows` pass |
| `system-flow` | FL.1 | all Tier-1 process-flows (≥2) | `--flows` pass |
| `glossary` | GL.1 | docs/generated/entities.md + docs/features/*/functional-spec.md (run `--glossary`) | `--glossary` pass |
| `test-cases` | TC.1 | docs/features/*/{technical-spec,edge-cases}.md (run `--test-cases`) | `--test-cases` pass |
