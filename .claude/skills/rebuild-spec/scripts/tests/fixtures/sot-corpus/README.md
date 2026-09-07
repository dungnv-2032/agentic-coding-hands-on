# SOT corpus fixtures

Real generated `rebuild-spec` output, used by the SOT-shape and Mode-C migration tests as input
they can assert against. **Not hand-typed** — that is the whole point of them. Several tests state
the requirement explicitly: a hand-written substitute would pass the assertions while proving
nothing about the shapes the pipeline actually emits.

## Provenance

Copied byte-for-byte from
`plans/260818-1332-rebuild-spec-human-readable-sot/evidence/corpus-g{1,2}/`
(see that plan's `evidence/baseline.md` for how the corpus was produced).

- `corpus-g1/` — v26 shape, `## Screen Layout` present (pre-migration)
- `corpus-g2/` — v27 shape, already reordered (post-migration)

## Why these live here and not in `plans/`

`plans/**/*` is gitignored (`.gitignore:68`), so nothing under it reaches CI. When these tests read
the corpus straight from `plans/`, they passed on every developer machine and failed on every CI
run — and because two of them read at MODULE level, the `FileNotFoundError` fired during pytest
collection and took the entire 4000-test suite down with exit code 2. The Quality Gate was red for
8 consecutive runs before anyone traced it here.

A test fixture has to be tracked, or it is not a fixture — it is a local convenience that silently
disables the test everywhere else.

## Rules

- **Do not hand-edit.** These files are captured output. Editing one to make a test pass destroys
  the only property that makes it worth keeping.
- To refresh, re-run the generating pass and copy the result over wholesale, then re-check the
  tests that read it — do not patch individual lines.
- `test_ci_portability_guards.py` enforces that test fixtures stay git-tracked. If you add a corpus
  here, that guard covers it automatically; it does not need a new entry.
