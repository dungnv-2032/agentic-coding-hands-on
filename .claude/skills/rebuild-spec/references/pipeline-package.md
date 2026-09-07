<!-- layout-exempt: rebuild-spec reference doc — all docs/ paths here are this skill's own input targets -->
# Package Pass (`--package`) — Self-Contained Client HTML Bundle

Standalone `--package` pass of `/tkm:rebuild-spec` (dispatched from SKILL.md when the flag is
set). It converts the already-promoted `docs/` corpus (overview + every feature/screen spec +
flows + diagrams) into a **self-contained, offline, `file://`-openable client HTML bundle** —
no build step for the reader, no network at open time.

This is an **EXPORT-tier pass**, the same class as `--overview`/`--api-doc`: stateless,
re-runnable, reads the *current* `docs/` state. It is **NOT** in `PASS_NAMES`/`passPresent`/the
translation registries, and it gets **no `confidence-report_*.md` companion** — it re-shapes
already-promoted content, it never generates new spec content.

## Invocation

```
/tkm:rebuild-spec --package
```

## Preflight (ABORT if unmet)

Same minimum bar as `--overview` (single source of truth: SKILL.md § Pass ordering):

- `docs/generated/feature-list.md` must exist. ABORT otherwise:
  `"ABORT — docs/generated/feature-list.md missing. Run /tkm:rebuild-spec (core pass) first, then re-run --package."`
- Everything else in `docs/` is bundled best-effort — a sparser corpus (e.g. before
  `--feature-specs` has run) still produces a smaller, valid bundle. This pass never fails on
  missing *optional* content, only on the missing core baseline above.

## Language selection

`--package` bundles **one language per run** (v1 — see plan.md Unresolved Q4 for future
secondary-language bundles). The **which-language-to-ask-about** story below is unchanged from
earlier drafts of this pass — what changed is the **root resolution mechanics** that follow it:
this pass does **NOT** call `resolve_docs_root(effLang, primaryLang, multilang=True)`. That
formula returns `docs/<primary>` unconditionally whenever a corpus has any registered
translations — including for an **en-primary** corpus, where the real per-lang layout produced by
this kit's translate pass never creates `docs/en/`: the primary tree stays at bare `docs/` and
every secondary tree (`docs/jp/`, `docs/vi/`, ...) nests *inside* it, as siblings of
`docs/features/`, `docs/generated/`, etc. Calling the `multilang=True` formula here would resolve
the primary root to a directory that doesn't exist on a real corpus (verified against a real
per-lang repo: `docs/.rebuild-state.json` has `primary_lang: "en"` + a non-empty `translations`
object, yet there is no `docs/en/` directory anywhere in the tree).

```js
const state = existsNonEmpty("docs/.rebuild-state.json") ? JSON.parse(readFile("docs/.rebuild-state.json")) : {}
const primaryLang = state.primary_lang ?? "en"
const secondaryLangs = Object.keys(state.translations ?? {})
const mode = detect_layout_mode(primaryLang, "docs", state)   // "single" | "per-lang"

let effLang
if (mode === "single") {
  // Only one language exists — nothing to ask.
  effLang = primaryLang
} else if (flags.auto) {
  // Non-interactive caller: never block on a prompt.
  effLang = primaryLang
} else if (flags.lang) {
  // Explicit override.
  effLang = normalize_lang(flags.lang)
} else {
  // Interactive, per-lang corpus, no explicit --lang: ASK which one to bundle.
  const answer = await AskUserQuestion({
    header: "Package Language",
    question: `This project has ${1 + secondaryLangs.length} language(s) (${[primaryLang, ...secondaryLangs].join(", ")}). Which one should the client HTML bundle contain?`,
    options: [primaryLang, ...secondaryLangs].map((lang) => ({
      label: lang === primaryLang ? `${lang} (primary, Recommended)` : lang,
      description: lang === primaryLang
        ? "The source-of-truth language — always complete, never a translation lag risk."
        : "A translated mirror — bundle this if the audience for the package reads this language.",
    })),
  })
  effLang = normalize_lang(answer)
}
```

A single-lang corpus (the common case — no secondary languages registered) never prompts: the
question only fires when `docs/.rebuild-state.json` actually has a non-empty `translations`
object AND the caller is interactive AND `--lang` wasn't already supplied.

**Root resolution + secondary exclusion happen inside the script, not here.** Once `effLang` is
settled, the caller passes the **OUTER** docs directory as-is — the same literal `docs` (or
whatever `--docs-root` names) that carries `.rebuild-state.json` — plus `--lang <effLang>`,
straight to `build_client_package.cjs`. It resolves the actual read root and any secondary-tree
exclusions itself via `extensions/scripts/lib/resolve-lang-root.cjs`, matched against the verified
on-disk convention:

- **Single-lang** (no registered translations): the outer docs directory IS the root. No
  exclusions. An explicit `--lang` that disagrees with a known `primary_lang` is a hard error —
  there is no second tree to serve it.
- **Per-lang, selecting the primary**: if `<docsRoot>/<primaryLang>` exists as a directory, that
  IS the primary root (a non-en primary already lives at `docs/<primary>/`). Otherwise the primary
  root is the bare outer `docsRoot` itself (the en-primary real-world shape) — and in that case
  every registered secondary (`<docsRoot>/<secondaryLang>` for each one) is **excluded** from the
  walk, since those trees are nested inside the same bare root being bundled.
- **Per-lang, selecting a secondary**: the root is exactly `<docsRoot>/<lang>`; missing that
  directory is a hard error. Nothing nests inside a secondary tree, so no exclusions apply.
- **Unrecognized `--lang`** (neither the primary nor a registered secondary): a hard error listing
  every available language.

This is deliberately a directory-existence check rather than a hardcoded "primary == en" special
case — it only ever asks "does `<docsRoot>/<primary>` exist?", never reads the
`docs/<primary>/.layout-migrated` sentinel (see `_lang_lib.py`) that marks the one-time migration
of an en-primary corpus's content from bare `docs/` to `docs/en/`. In practice this heuristic
happens to land on the right root either way (pre-migration: no `docs/en/` dir → bare `docs/`;
post-migration: `docs/en/` exists → that dir), but that is a byproduct of the existence check, not
sentinel-aware logic — there is no dedicated migration handling here, and none is planned (YAGNI).

## Exclusion denylist

Unlike `--overview` (which reads a fixed, named artifact list and never globs a directory),
`--package` bundles an *entire corpus* — it globs `<docsRoot>/**/*.md`. Internal-only sidecars
would leak in unless excluded. The denylist (implemented in
`extensions/scripts/lib/package-denylist.cjs`, matched against each file's basename):

| Pattern | What it is |
|---|---|
| `confidence-report_*.md` | A1 citation-coverage sidecars (advisory, internal-only) |
| `*.draft.md` | pre-promotion system-synthesis hybrid drafts |
| `.nav-metadata.json` | navigation sidecar |
| `.rebuild-state.json` | incremental-run state |
| `.layout-migrated`, `.components-migrated-v*` | per-lang layout-migration sentinels |
| `component_profile*.json`, `*shard-manifest*.json` | multi-component / artifact-sharding manifests |
| `_route-probe.json`, `.spec-promote-pending.json` | boot-probe and promotion-rollback sidecars |
| `.reading-order.json` | reading-order sidecar (see "Build step" above) — internal input to the index/sidebar/pager, never a bundled page itself |

This mirrors SKILL.md's own "`confidence-report_*.md` / `.nav-metadata.json` are advisory and
internal-only, excluded from `--overview`/doc-writer export" convention, extended to every other
internal artifact a whole-corpus glob would otherwise sweep up.

A basename pattern can't tell apart an internal per-directory nav index from a legitimate
client-facing page sharing the same basename at a different location — `system/README.md` and
`generated/README.md` are per-directory nav indexes made redundant by the bundle's own sidebar,
while `docs/README.md` (Start Here) and every per-feature `README.md` reading guide under
`features/` are the opposite of redundant. `DENY_PATHS` (`package-denylist.cjs`) is a
root-relative, POSIX, exact-match set that drops only those two named files:

| Path (root-relative) | What it is |
|---|---|
| `system/README.md` | per-directory nav index; the bundle sidebar already covers this |
| `generated/README.md` | per-directory nav index; the bundle sidebar already covers this |

## Build step (deterministic — no LLM per file)

A dozens-of-files corpus is too large for section-by-section LLM authoring (the `--overview`
pattern) — `--package` instead reuses `markdown-novel-viewer`'s deterministic, `marked`-based
`renderMarkdownFile()` (already mermaid-fence-aware: a ` ```mermaid ` fence becomes
`<pre class="mermaid">…</pre>` for client-side rendering). This is the same "bundled deterministic
build script" shape as `--api-doc`'s `build_api_design.py`, not the `--overview`
doc-writer-fan-out shape.

**XSS boundary — read before touching either renderer.** `renderMarkdownFile()` does **NOT**
sanitize raw HTML embedded in markdown *prose*: CommonMark's raw-HTML grammar rule lets a literal
`<script>…</script>` or `<img onerror=…>` sitting in prose text pass straight through to the
renderer's output untouched. That is correct, intentional behavior for `markdown-novel-viewer`'s
own trust context (it renders human-authored plans/specs, where raw-HTML passthrough is a
feature). It is **not** safe for `--package`: its input is a `docs/` corpus that can echo
source-derived strings (quoted code, scanned copy) shaped to look like an HTML tag, and the output
is a client-facing exported bundle. `--package` closes this gap at **its own boundary**, not
inside the shared renderer:
`extensions/scripts/lib/render-sanitized.cjs` runs a fence-aware pre-escape
(`extensions/scripts/lib/sanitize-markdown-source.cjs`) over each file's raw text — escaping `<`,
`>`, `&` in prose while leaving frontmatter and fenced-code content untouched — **before** handing
it to `renderMarkdownFile()`. See that module's header comment for the exact mechanism and its
documented trade-offs (bare autolinks, inline-code spans containing angle brackets).

```
node <skill-dir>/extensions/scripts/build_client_package.cjs \
  --repo-root . \
  --docs-root docs \
  --lang <effLang> \
  [--project-name "<ProjectName>"] \
  [--out client-package/<ProjectName>]
# <skill-dir> = project-local .claude/skills/rebuild-spec  OR  global ~/.claude/skills/rebuild-spec
# --docs-root is always the OUTER docs directory (the one carrying
# .rebuild-state.json) — never a pre-resolved per-language path. The script
# resolves the actual read root + secondary-language exclusions itself; see
# "Root resolution + secondary exclusion" above.
```

**`<ProjectName>` resolution** (same rule as `--overview`): read the `**Project**:` field from
`system/overview.md` under the *resolved* read root (see below); if absent, fall back to the
repo root directory's base name. The script does this itself when `--project-name` is omitted —
pass it explicitly only to override.

**What the script does:**
1. Resolve the actual read root and any secondary-language exclusions from `--docs-root` +
   `--lang` (see "Root resolution + secondary exclusion" above), then recursively find every
   `.md` under that resolved root, applying the denylist above and skipping excluded subtrees.
2. Render each via the sanitize-then-render wrapper (see XSS boundary above) → per-doc `.html`,
   written at the same relative path (`docs/features/F001_Login/technical-spec.md` →
   `client-package/<ProjectName>/features/F001_Login/technical-spec.html`).
3. Build `index.html` — a landing page driven by the **reading-order sidecar**
   (`<resolved-root>/.reading-order.json`, emitted by `build_navigation.py` alongside the nav
   READMEs). `extensions/scripts/lib/reading-spine.cjs` turns the sidecar + the real page walk
   into ONE reading model shared by three views: the numbered layered index (Orientation →
   Domain model → Interfaces & behavior → Deep-dive drills, plus an alphabetical Appendix for
   pages the sidecar doesn't claim), the sidebar (grouped into collapsible `<details>` sections
   mirroring the same layers/drills — never a flat alphabetical list), and a 3-cell prev/next
   pager rendered on every spine page (`extensions/scripts/lib/package-pager.cjs`) that walks the
   whole corpus start to finish. `index.html` itself gets a single forward cell pointing at the
   first spine page. **No sidecar present** (a corpus that predates phase 01, or one whose nav
   pass hasn't run) → the same model falls back to the pre-existing alphabetical-by-top-level-
   segment index/sidebar with no pager rendered anywhere — every caller reads one model and never
   branches on which path produced it.
4. Copy the vendored `assets/mermaid.min.js` (classic global/UMD bundle, pinned — see
   `extensions/assets/mermaid-LICENSE.txt` for the exact version and provenance),
   `assets/package-shell.css` (shell/nav chrome, tokens adapted from
   `_shared/references/editorial-report-html.md`), and `assets/package-zoom.js` (the
   click-to-zoom diagram viewer, see below) into `<bundle>/assets/`.

**Offline-by-construction, not by convention:** every generated page loads mermaid via a plain
`<script src="./assets/mermaid.min.js">` (relative depth computed per page) followed by
`mermaid.initialize({ startOnLoad: false })` and an explicit `mermaid.run()` — **never**
`type="module"`, **never** a CDN URL.
`file://`-opened pages in Chromium-based browsers block ES-module imports cross-origin, so the
classic global bundle is the only shape that survives a true offline open (Decision 5).

## Diagram zoom

Mermaid scales every rendered diagram DOWN to the content column via its own `max-width`, so a
large flowchart or sequence diagram arrives as an illegible smear — a real corpus holds
flowcharts past **10 000 px wide**, which land inline at roughly `772 × 54 px`. `overflow-x: auto`
on `pre.mermaid` never helped: the SVG was shrunk, not clipped, and a `file://` page offers no
"open image in new tab" escape either.

`assets/package-zoom.js` makes each rendered diagram openable full-screen — wheel zoom anchored at
the cursor, drag pan, `+`/`-`/`0`/`1`/arrow keys, double-click to toggle fit ⇄ 100%, `Esc` to
close. It is a classic IIFE with no module syntax, no dependency, and no network call, held to the
same offline contract as everything else in the bundle.

Behavior is covered by `scripts/tests/test_package_zoom_browser.py`, which drives a real headless
Chrome against a built bundle and skips where puppeteer is absent. Static assertions over the
generated HTML cannot see this surface — the pan-dismiss defect above cleared ten of them.

Three decisions worth keeping:

- **`startOnLoad: false` + `mermaid.run()`.** `startOnLoad: true` is fire-and-forget and gives the
  viewer no completion signal to attach on. The `.catch()` attaches too — one bad fence must not
  cost the page every other zoomable diagram.
- **A pan tracks on `window`, not on the stage.** A pan routinely carries the cursor off the stage,
  where stage-bound listeners stop firing and strand the gesture. `setPointerCapture` is the other
  answer, but it retargets an input stream globally for the duration and an early build showed wheel
  events resolving to the wrong element after a captured drag.
- **A pan must not dismiss the viewer.** A press and release synthesize a trailing `click` on their
  nearest common ancestor no matter how far the pointer travelled, so the backdrop-dismiss handler
  has to distinguish a pan from a click by movement threshold — and a plain backdrop click must
  still close.
- **The shell behind is `inert` while the viewer is open**, because `aria-modal` alone leaves the
  page's own links and diagram hosts in the tab order.
- **The clone gets a derived id, never no id.** Mermaid scopes its inline `<style>` to the SVG's
  own id, so stripping the id to dodge a duplicate unstyles the entire clone — flowchart nodes
  render as solid black boxes. Rename the root id and repoint the stylesheet at it.
- **A diagram opens at `max(fit, MIN_OPEN_SCALE)`, anchored top-left.** True fit on a 10 000 px
  flowchart is 12% — the same hairline the viewer exists to answer. The `⤢` button still reaches
  the true whole-diagram overview in one click.

Chrome strings come from the sidecar's `ui.zoom` block, handed to the page as JSON in
`<script type="application/json" id="pkg-zoom-i18n">` so the static asset reads its own labels
per language. That block is **optional** — `isUsableUi()` in `reading-spine.cjs` deliberately does
not require it, because requiring it would invalidate every sidecar written before it existed and
drop those corpora to the alphabetical, pager-less fallback. Absent block ⇒ the viewer's built-in
English, the same precedent as `FALLBACK_START_HERE_LABEL`.

**Reuse boundary:** the `--html` editorial contract (`_shared/references/editorial-report-html.md`)
is the wrong engine for this — it is LLM-hand-authored one page at a time and its one allowed
external dependency is a CDN mermaid tag, neither of which scales to or survives a dozens-of-file
offline corpus. `--package` reuses **only** its CSS/typography tokens for the shell chrome
(`package-shell.css`), never its authoring method or its CDN dependency.

**Renderer dependency note:** `renderMarkdownFile()` needs `markdown-novel-viewer`'s own npm
deps (`marked`, `highlight.js`, `gray-matter`) installed alongside it. `build_client_package.cjs`
resolves the renderer from whichever of the project-local, kit-source, or global skill roots
actually has those deps installed (see `extensions/scripts/lib/resolve-renderer.cjs`); if none
do, it fails with the exact `npm install` command to run.

## Outputs

- `client-package/<ProjectName>/index.html` — nav landing page
- `client-package/<ProjectName>/**/*.html` — one page per bundled doc, mirroring the `docs/`
  relative structure
- `client-package/<ProjectName>/assets/mermaid.min.js` + `assets/package-shell.css` +
  `assets/package-zoom.js`

**Output namespace is the repo-root `client-package/` directory — OUTSIDE `docs/`** (Decision 4).
A rendered bundle carrying a multi-MB JS asset is not a translatable doc source; keeping it out
of `docs/` means zero `check_layout_paths.py` / layout-exempt / `_translation_sync_lib.py`
`_DOC_AREAS` wiring is needed. **Consumer guidance:** add `client-package/` to the project's own
`.gitignore` unless the bundle itself is meant to be a versioned deliverable — it is a generated
artifact, same category as a build's `dist/` output.

## Idempotency & Edge Cases

- Re-running **wipes and rewrites** `client-package/<ProjectName>/` from the current `docs/`
  state — a doc removed from `docs/` since the last `--package` run does not leave an orphaned
  page in the bundle. The wipe is guarded by a safety floor
  (`extensions/scripts/lib/safe-rimraf.cjs`): it refuses to delete the filesystem root, the home
  directory, or the repo root itself, and refuses any target outside the repo root unless it was
  an explicitly-passed `--out`.
- A sparser corpus (fewer promoted artifacts) still produces a smaller, valid bundle — this pass
  never blocks on optional content.
- This pass writes only under `client-package/<ProjectName>/`; it never modifies `docs/` or any
  other pass's artifacts.
- No PDF output in v1 (Decision 3) — a browser's own "Print to PDF" on the generated HTML covers
  the common case without new kit machinery.

## Completion handoff

```
─── package pass complete ───
Bundled: client-package/<ProjectName>/index.html (<N> pages)
Open client-package/<ProjectName>/index.html directly in a browser — no server, no network required.
Re-run: /tkm:rebuild-spec --package  (after any docs/ refresh)
```
