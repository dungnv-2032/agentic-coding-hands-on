# Product profile — the metadata a repo cannot tell you itself

A codebase can tell an agent *how* it is built. It cannot tell an agent *who owns it*, *what
the name means*, or *who to contact when something breaks* — that context lives in people's
heads, not in source. `docs/product-profile.md` is the one place it gets written down, once,
so the "General intro" section of the content contract has something real to draw from instead
of a permanent `<TODO>`.

Get the canonical template by running the script — do not hand-copy it here (single source,
see `scripts/product_profile.py` → `render_template`):

```
python3 scripts/product_profile.py --source <repo> --init
```

## Field reference

| Field | Required | What it is for |
|---|---|---|
| `Product name` | yes | Defaults to the same detection `discovery.product_name()` already does; override if the detected name is wrong (a package.json name, a directory name) |
| `Name meaning` | no | Where the name comes from, or what it signals — the kind of context a founder knows and a `grep` never will |
| `URL` | yes | Comma list: marketing site, docs site, download/store page — wherever an end user actually lands |
| `Department` | yes | The owning team/department — never inferable from code, only from an org chart |
| `Owner` | yes | Role + person accountable for the product — same reasoning as Department |
| `Support contact` | yes | Where a user goes when something breaks — see § Privacy below before filling this in |
| `Summary` | yes | One line: what it is, who it's for, its core value. Feeds the llms.txt blockquote directly |
| `Surfaces` | yes | Comma list from the fixed vocabulary: `web, extension, desktop, mobile, cli, api, mcp` |
| `Audience default` | no | `user` \| `dev` — see § Precedence below |

`Owner`/`Department`/`URL`/`Support contact` are required precisely because they are the fields
a repo scan structurally cannot answer — that gap, not a prompting shortfall, is why the
"General intro" contract section goes missing without this file.

## Never invented

An unfilled `<TODO ...>` placeholder always parses as **missing**, never as a value (FR-7). The
script never guesses a department, a name, or a contact — a blank field surfaces as an advisory
in the run report, and stays blank until a person fills it in.

## Precedence — `audience_default`

`--audience` flag (explicit, per-run) > `Audience default` (this file, per-repo) > `user`
(hard-coded fallback). A repo mostly read by internal engineers can set `Audience default: dev`
once here instead of every invocation needing `--audience dev`; an explicit flag on any single
run still wins.

## The interview (run by SKILL.md, main thread only)

The script itself never asks a question — `product_profile.py` has no interactive path at all.
The interview is a SKILL.md step, and it fires only when **all three** hold:

1. `manifest.profile.status != "ok"` (something required is still missing).
2. `--no-interview` was not passed.
3. The run is a **direct, user-invoked interactive session** — not a subagent, delegated task,
   automation, or CI run. There is no runtime signal that distinguishes "main thread" from
   "orchestrated"; the safe default is to treat anything uncertain as non-interactive and skip
   straight to the advisory path. `--no-interview` is the explicit override for a caller that
   already knows it is headless.

When it does fire:

- At most **two** `AskUserQuestion` calls, **four questions each**, asking only about
  `missing_fields` — never re-asking a field already filled.
- Every question offers the detected/derived value (if any) as "(Recommended)" plus a free-text
  "Other" — free-text is the normal path for `Department`/`Owner`/`Support contact`/`URL`, since
  there is nothing to detect for them.
- `Surfaces` is one question with common combinations (`web`, `web, api`, `cli, api`, …) as
  options plus "Other".
- Answers go to `product_profile.write()`, then the discovery script re-runs once. One pass —
  never loop back into another interview round.
- Skipped or incomplete interview → the run continues with `status: incomplete`; the intro
  section carries a gap advisory. Never a hang, never a dead end.

## Per-lang repos — a known limitation, not a bug

`discovery.docs_root()` resolves `docs/<lang>` only when `--lang` is passed on the command line;
it does not consult `docs/.rebuild-state.json`. So a per-lang repo run **without** `--lang` reads
`docs/product-profile.md` (and every other doc) from the wrong root. This is deliberately not
fixed here — rewriting the resolver is `rebuild-spec`'s contract, not this skill's. Instead,
`per_lang_advisory()` detects the situation (a `translations` entry other than `primary_lang` in
`docs/.rebuild-state.json`, and no `--lang` given) and emits: *"this repo uses the per-lang docs
layout; pass `--lang <primary>` or the profile and docs will be read from the wrong root."*

## Privacy — before you fill in `Owner` / `Support contact`

`llms-full.txt` is an explicitly downloadable deliverable. Anything written into `Owner` or
`Support contact` ships in it. Use a **role + team alias** — e.g. "Platform Team,
platform-support@example.com" — never a personal phone number or private address. The script
never invents or guesses a person; it only ever repeats back what a human typed in.

## Reads are symlink-contained

Every read of this file goes through `discovery.safe_read` (`is_file()` + `within()`), never a
bare filesystem read. A `docs/product-profile.md` that is actually a symlink pointing outside
the repo is treated exactly like a missing file — it cannot be used to pull metadata (or worse,
someone else's metadata) in from outside the project.
