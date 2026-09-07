# End-user content contract

This is the **single home** for four things: the 7-section contract, the audience rule, the gap
advisories, and the six validation gates. `SKILL.md`, `llms-txt-specification.md`, and
`artifact-source-ladder.md` link here — none of them restate this table. Everything here governs
the `--audience user` default (v1 restored verbatim under `--audience dev`).

## The 7-section contract

Every section below is either **filled** from a repo-only source, or carries an explicit **gap**
advisory naming the export path. A required section is never silently absent.

| Section | Source (repo-only) | On missing |
|---|---|---|
| General intro (name + meaning, URL, dept, owner, summary, surfaces) | `docs/product-profile.md` + `docs/system/overview.md` | interview → write `product-profile.md` |
| Installation (per surface: web / extension / desktop) | `docs/user-guide/install*`, getting-started, README user-install parts | TODO + advisory |
| Usage guide | `docs/user-guide/**`, `guides/`, tutorials | TODO + advisory |
| Screen list | `docs/user-guide/screens*` (hand-written end-user tour) **or** `docs/generated/screen-list.md` (rebuild-spec's screen inventory) — `docs/screens/**`, the dev-coded per-screen spec (`SCR###`), stays excluded | TODO + advisory |
| Feature list | `docs/generated/feature-list.md`, `docs/features/*` — rewritten into end-user language, never inlined raw | TODO + advisory |
| API & MCP guide (user-facing integration surface) | OpenAPI specs, `docs/api` user docs, MCP guide docs | **omitted** silently when the profile states no `api`/`mcp` surface; a **gap** with an advisory when specs exist but `profile.surfaces` was never filled in — silence is reserved for a *stated* absence, not an unknown one |
| Optional / FAQ | faq, changelog, policies | omit |

Emitted order: `intro → install → usage → screens → features → api → optional`. `## Optional` last
is the llmstxt.org hard rule, so this order and the format spec agree by construction.

**Why the screens row excludes `docs/screens/**` but accepts `screen-list.md`.** `docs/screens/**`
holds rebuild-spec's promoted per-screen spec — a dev-coded artifact, not a screen tour; ingesting
it would smuggle exactly the build-side content `--audience user` exists to exclude.
`docs/generated/screen-list.md` is a different thing: the generated **inventory**, one row per
screen with its name and route, which is precisely what this section asks for. Excluding it (the
original F7 fix cut both) had a concrete cost — running `/tkm:rebuild-spec` could then never close
a screens gap, so the tool the advisory recommended did not actually help.

Two halves make it work, and neither is sufficient alone: `SCREENS_GLOBS` accepts the file, **and**
`audience_filter.KEEP_PATTERNS` carves it out of the blanket `docs/generated/**` drop (the same
carve-out `feature-list.md` already had). With only the glob, the filter drops the file before the
contract ever sees it.

## Gap advisories (verbatim)

| Section | Advisory text |
|---|---|
| `install` | "No installation guide found. Export it into `docs/user-guide/install.md` and re-run." |
| `usage` | "No usage guide found. Export the user guide into `docs/user-guide/` and re-run." |
| `screens` | "No screen list found. Run `/tkm:rebuild-spec` (generates `docs/generated/screen-list.md`) or export an end-user screen tour into `docs/user-guide/screens.md`, then re-run." |
| `features` | "Run `/tkm:rebuild-spec` or add `docs/features/` and re-run." |
| `intro` | "Product metadata missing. Run `product_profile.py --init` and fill `docs/product-profile.md`." |
| `api` (unknown state) | "OpenAPI specs found but `docs/product-profile.md` does not state the product's surfaces. Fill `Surfaces` — add `api`/`mcp` if the API is a product surface — and re-run." |

## Readiness preflight — gate on the outcome, not on tooling

`manifest.readiness` = `{required_total, filled, gaps[], thin}`, derived from `contract[]`;
`thin` is true once `len(gaps) >= THIN_THRESHOLD` (2).

The tempting design is a prerequisite: refuse to run until `/tkm:rebuild-spec` has produced a
`docs/` layer. Do **not** do that. It gates on a proxy, and the proxy does not cover the hole:
rebuild-spec fills `features` and `screens`, but `intro` needs human-entered metadata and `usage`
needs a human-written guide. A prerequisite check would block the run, spend a multi-agent pass,
and still emit a file with those two sections empty — while breaking the never-a-dead-end rule.

So the gate reads the actual result:

| Context | Behavior on `thin: true` |
|---|---|
| Direct interactive session | Stop before enriching. Show each gap with its advisory (which already names the fixer that closes it) and `filled/required_total`, then ask: run the fixer / proceed thin / cancel. |
| Orchestrated, headless, `--no-interview` | Continue, and label the artifact **thin** in the report with its gap list. Never hang. |
| CI (`--require-complete`) | Emit the manifest first (so the log shows *what* is missing), then exit `2`. Tier 4 counts as incomplete even though `contract[]` is absent. |

One fixer per gap, and the advisories already carry them: `features`/`screens` → `/tkm:rebuild-spec`;
`intro` → `product_profile.py --init`; `usage`/`install` → a human writes the guide. Nothing here
re-lists them, so the advisory text stays the single source.

## Audience rule

> Exclude **how the product is built**. Include **how the product is used**.

| Verdict under `--audience user` | Examples |
|---|---|
| **drop** | `contributing`, `dev-setup`, `development`, `techstack`/`tech-stack`, `architecture`, `ci`/`cicd`/`pipeline`, `repo-layout`, `docs/system/**` (except `overview.md` as an intro *source*), `docs/flows/**`, `docs/decisions/**`, `docs/screens/**` (dev-coded specs), `deploy*`/`hosting*`, `docs/generated/**` except the carve-outs below |
| **keep** | `install*`, `getting-started`, `quickstart`, `docs/user-guide/**`, `guides/**`, `tutorial*`, `features/**`, `faq`, `changelog`, `usage*` |
| **conditional** | `docs/generated/feature-list.md` — kept only as the **source** for the user-language feature rewrite, never inlined raw. `docs/generated/screen-list.md` — kept as the screens source (the second carve-out from `docs/generated/**`). `docs/generated/api-map.md`, `route-list.md`, OpenAPI specs — kept only if `"api"` or `"mcp"` is in `profile.surfaces`. |
| **unmatched by any pattern** | **drop, fail-closed.** An unknown doc is more likely build-side than user-facing, and a wrong drop is visible and recoverable while a wrong include silently poisons the deliverable. Every dropped file is named in `manifest.audience_filter.dropped_files`. |

`--audience dev` disables the filter entirely — kept = all, dropped = none, and both the section
set and the file selection revert to v1's `SECTION_ORDER` byte-identically.

## Feature-rewrite bound (the invention guard)

The one genuinely LLM-shaped step in this contract, and the one place invention can creep in:

> Rewrite `feature-list.md` rows into end-user language: what the user can do, not how it is
> built. **Every feature named must appear in the source.** Do not add, merge, split, rename
> beyond plain-language phrasing, or promise a capability the source does not state. If a row is
> unintelligible without code context, drop it — a shorter honest list beats an invented one.

## Index / full split for profile prose

The product URL, owner, department, and support contact render **only into `llms-full.txt`**.
`llms.txt` (the index) keeps its v1 shape — H1, a one-line blockquote summary, link sections — and
carries **no raw URL** and no profile prose. This is not a style choice:
`analyze-llms-txt.js` (the downstream consumer) extracts the first `http(s)` URL from any line not
starting with `#`, so a product URL rendered into the index blockquote would be harvested as a
documentation URL and dispatched to a fetch agent. The same rule applies to every gap advisory
rendered into the index: repo-relative paths in backticks, never an absolute URL.

## The six gates

| Gate | Pass condition | On failure |
|---|---|---|
| Quality floor *(existing)* | Blockquote free of `<TODO>`; every link has a real description; no section both link-free and advisory-free | Climb a tier / read more sources, then re-enrich |
| llmstxt format *(existing)* | H1 present; `[title](path): desc` syntax; `## Optional` last | Fix the staging file; never hand-write the final artifact |
| **Self-containment** | `manifest.self_containment.remaining == 0` (measured post-trim); no `](` with a non-`http` target in `llms-full.txt` | Script bug — re-run rendering; do not hand-patch |
| **Contract completeness** | Every `contract[*]` with `required: true` has `status: "filled"` or `status: "gap"` **with** a non-null advisory | Add the missing advisory; never drop a required section |
| **Audience lint** | Under `audience: user`, no **heading** in `llms-full.txt` matches the dev-content pattern set below | Sub-block remediation — see below; never a bare section removal |
| **Secret scan** | `manifest.secret_scan.status == "clean"` | Non-clean → the full artifact is withheld and the index promotes alone; report each warning with its source doc and tell the user to scrub the doc, not the artifact |

Dev-content pattern set (headings): `tech stack`, `techstack`, `dev environment`,
`development setup`, `local setup`, `contributing`, `ci/cd`, `pipeline`, `architecture`,
`repo layout`, `project structure`.

### Audience-lint remediation (granularity matters)

"Remove the section" read literally would either delete a *required* contract section — failing
the contract-completeness gate above — or force hand-patching the staging file, which the
llmstxt-format gate forbids. The rule instead:

1. **Heading match inside an otherwise user-facing doc** → remove the offending **sub-block only**
   (that heading and its body, up to the next same-or-higher heading) **at the render layer**, then
   re-render. Never hand-edit staging.
2. **The entire source doc of a required section is dev-flavored** → that section becomes
   `status: "gap"` with its normal export advisory. The section still exists; it just has nothing
   honest to say yet.
3. A required section is **never** left absent, and a bare deletion is never the answer.

## Repo-only trade-off (say it loudly)

> This file is built from **this repository only** — the skill does not crawl your website. If
> your user guide, screen list, or install instructions live on a hosted docs site, export them
> into `docs/user-guide/` and re-run; those sections will fill on the next pass.

A benchmark that lives only in a hosted guide (never exported into the repo) stays unreachable
until it is exported — the run report names the shortfall by section, not as a vague quality gap.

## OpenAPI whole-spec disclosure

Setting `Surfaces` to include `api`/`mcp` pulls **every** discovered OpenAPI document into
`llms-full.txt`, internal and admin endpoints included — specs are not filtered by audience. When
the API section is filled from a spec, the run report must print:

> `llms-full.txt` inlines the complete OpenAPI document(s), internal and admin endpoints included.
> Use `--index-only` or export a user-facing API guide into `docs/api/` if that is not intended.
