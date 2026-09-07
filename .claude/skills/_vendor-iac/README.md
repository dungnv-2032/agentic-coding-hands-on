# Vendored IaC reference material

Four third-party skill sets, imported **as reference material — not as routable skills**.

The upstream AIDD kit consumes all four the same way: as `Load:` context for reviewer and generator
subagents, never as a user-facing entry point. Importing them as routable skills would silently
promote them into the shared router, where they collide with base `tkm:devops`, `tkm:deploy-app` and
`tkm:audit-security` with nothing to arbitrate between them.

## Contents

| Directory | Upstream | Licence / attribution |
|---|---|---|
| `mermaid-diagrams/` | AIDD vendored | none stated upstream |
| `aws-solution-architect/` | AIDD vendored | `license: MIT + Commons Clause` (in `SKILL.md` frontmatter) |
| `terraform-test/` | AIDD vendored | `Copyright IBM Corp. 2026`, v0.0.2 |
| `refactor-module/` | AIDD vendored | `Copyright IBM Corp. 2026`, v0.0.1 |

**Every file is byte-identical to its upstream source.** Licence, copyright and version markers are
intact. Do not reformat, re-lint, split, or trim these files — including their `SKILL.md`
frontmatter. If one needs to change, change it upstream and re-import.

Because they are not skills here, the 450/500-line `SKILL.md` thresholds do not apply to them.

## Why the `_` prefix

Two independent mechanisms keep these out of skill enumeration, and both matter:

1. **Nesting.** Skill discovery and `listSkillDirs` look for `<skills>/<name>/SKILL.md` at exactly
   one level. These sit at `<skills>/_vendor-iac/<name>/SKILL.md` — two levels — so they are never
   enumerated, even though each retains its upstream `name:` frontmatter.
2. **The `_` prefix.** `tests/validate-skills.py` skips `_`-prefixed directories outright.

## How to reference these

From a `tkm:iac-*` skill's `references/*.md` **body**, by path. Nested paths in a reference body are
not resolved by the validator, so this is safe.

Do **not** reference them from a `SKILL.md` in a form the validator checks, and do not link a sibling
skill's `references/` directory — that is an unrelated hard failure.
