---
name: tkm:index-docs
description: "Index the project's DOCUMENTS (.md, .txt, .pdf, .docx, specs, RFPs) into the Graphify knowledge graph so doc-only projects get graph-aware answers before any code exists. The always-on SessionStart hook and rebuild-spec only refresh CODE edges — this is the only skill that adds the doc/semantic layer. Activate for 'index docs', 'index tài liệu', 'add docs to graph', 'build knowledge graph from documents', or when a doc-heavy project has no semantic graph yet."
argument-hint: "[path] [--all]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: documentation-knowledge
triggers: ["index docs", "index tài liệu", "add docs to graph", "build knowledge graph from documents", "graph my specs"]
---

# Indexing the Archive

The workshop keeps its blueprints filed. Code the kit re-reads for free, every session —
but the written record only enters the graph when someone carries it there.

## Why This Skill Exists

`graphify update .` — the command the SessionStart hook runs, and the one `rebuild-spec`
runs in its preflight — is **code-only**. Graphify's own CLI says so:

```
update <path>   re-extract code files and update the graph (no LLM needed)
```

Run it on a folder of `.md` files and you get file nodes and heading nodes with `contains`
edges. No entities, no cross-document relationships. A question like *"what depends on the
Ledger?"* returns nothing, because nothing from the prose was ever extracted.

Doc/semantic extraction costs LLM tokens, so nothing in the kit does it automatically.
**This skill is the deliberate, user-triggered step that does.**

## When to Use

- A project has specs, RFPs, or design docs but little or no code yet, and the user wants
  graph-aware answers (`tkm:ask-expert`, `tkm:estimate` — the latter from the `extras` kit) over them.
- The SessionStart nudge reports doc files changed since the graph's semantic layer was built.
- Before a doc-heavy estimation or discovery pass, so the graph can surface duplicate
  features and cross-document dependencies.

Skip when the corpus is pure code — the hook already covers it.

## Graph Maintenance Authorization

`_shared/graphify-code-graph.md` Use Rule 5 forbids graph mutation unless the current skill
explicitly authorizes it. **This skill authorizes graph maintenance**: it may install
Graphify and write `graphify-out/`. It is the only kit skill that may add doc/semantic edges.

## Procedure

### 1. Gate on config

The Knowledge Graph is ON by default. Stop with a one-line notice and change nothing if it
is disabled — same opt-out every other graphify integration honours:

```bash
# disabled when: graphify.enabled=false in .claude/.takumi.json or .claude/.tkm.json
#                (local wins over ~/.claude/), or env GRAPHIFY_DISABLE=1 / REBUILD_NO_GRAPH=1
```

### 2. Check the `/graphify` skill and the parser extras

This skill delegates the extraction to the `/graphify` **skill**, which the kit does not
ship — it comes from the Graphify package and must be copied into the harness once:

```bash
graphify install            # Claude Code, Codex, and other platforms
```

If `/graphify` is not available, say so and give the user that one command. Do not fall
back to the bare CLI: `graphify update` would report success while indexing no documents at
all, which is worse than stopping.

**On Codex, also check the multi-agent feature flag.** The Codex build of the `/graphify`
skill extracts via `spawn_agent`/`wait_agent`, which needs `multi_agent = true` under
`[features]` in `~/.codex/config.toml`. Without it `spawn_agent` is unavailable and
extraction cannot run — tell the user to add the flag and restart Codex rather than
letting the run fail midway.

**Then check the parser extras — PDF and Office are NOT installed by default.** Graphify
declares them optional (`pypdf` under `extra == "pdf"`; `python-docx` and `openpyxl` under
`extra == "office"`), so the `uv tool install graphifyy` that `/graphify` itself recommends
leaves all three out. When a parser is missing the extractor raises, `except Exception:
return ""` swallows it, and the document yields nothing with no message at all — the file
still classifies as `FileType.DOCUMENT`, so it is counted as indexed while contributing
zero. Verified on a real `.docx`: `classify_file` → `DOCUMENT`, `docx_to_markdown` → 0
characters.

```bash
python3 -c "import pypdf"     # .pdf
python3 -c "import docx"      # .docx
python3 -c "import openpyxl"  # .xlsx
```

Whichever import fails, drop the matching extension from `KEEP` for this run **and say so**.
Offer the one-line fix rather than silently indexing less than the user asked for:

```bash
uv tool install --force 'graphifyy[pdf,office]'
```

Plain-text formats and images need no extras — images are read by the subagent's vision, not
by a Python parser, which makes them the most dependable input of the lot.

### 3. Resolve scope

With no `path` argument, walk the filesystem — **do not enumerate through git**. One code
path covers every project state; there is no separate "not a repo" branch.

```python
import os
from pathlib import Path

SKIP = {".git", ".claude", "node_modules", "graphify-out", "memory-graph-out", "plans",
        ".venv", "venv", "__pycache__", "dist", "build", ".next", ".nuxt",
        "target", "vendor", "coverage"}
KEEP = {".md", ".mdx", ".qmd", ".rst", ".txt", ".pdf", ".docx", ".xlsx"}
# Standalone images. Counted separately — see step 5, one image costs one subagent.
IMGS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
# Graphify cannot parse .pptx at any extras level, but step 4 recovers its text and images.
DECK = {".pptx"}
# Genuinely unreachable — nothing here has a recovery path, only a conversion.
NEAR = {".csv", ".xls", ".doc", ".ppt", ".odt", ".epub", ".rtf",
        ".pages", ".numbers", ".key"}

docs, images, decks, skipped = [], [], [], []
for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith(".")]
    for f in filenames:
        p, ext = Path(dirpath, f), Path(f).suffix.lower()
        if ext in KEEP:
            docs.append(p.relative_to(root))
        elif ext in IMGS:
            images.append(p.relative_to(root))
        elif ext in DECK:
            decks.append(p.relative_to(root))
        elif ext in NEAR:
            skipped.append(p.relative_to(root))
```

`.pptx` sits in its own bucket rather than in `NEAR`: graphify will never read it, but step 4
recovers both its slide text and its embedded diagrams, so telling the user to "convert it"
would be wrong advice.

**Images earn their place.** Graphify's extraction spec tells the subagent to *"use vision
to understand what the image IS — do not just OCR"*, with explicit rules for diagrams
("components and connections"), UI screenshots, charts, and whiteboard photos. On a
docs-first project the architecture often exists **only** as a diagram. And unlike `.pdf`
or `.docx`, images need no optional extra — the subagent reads them directly.

`.svg` is in graphify's `IMAGE_EXTENSIONS` but is left out here: it is XML text, graphify
gives it no special handling, and nothing in `/graphify` says how a subagent should render
it. A Figma or draw.io export is thousands of `<path>` elements — expensive to put in
context and probably unreadable as a picture. Revisit once someone has confirmed the
behaviour.

`NEAR` is narrow on purpose. Reporting every non-document in the tree would bury the one
line that matters: on a real project the naive version surfaced `.gitignore` and
`.repomixignore` alongside the `backlog.csv` that actually needed converting.

**Why not git.** `git ls-files` lists only *tracked* files, and it fails on the two states
that matter most:

- *Fresh project, documents not committed yet.* `git ls-files` returns nothing while the
  staleness hook — which uses `git status --porcelain`, and so sees `??` entries — happily
  reports them. The nudge would then point at documents this skill claims do not exist,
  every session, forever.
- *Documents deliberately gitignored.* Client RFPs and bid material are routinely ignored
  because they are confidential. **Both** git paths are blind to them, and they are exactly
  what `tkm:estimate` (`extras` kit) needs. Honoring `.gitignore` here would be wrong anyway: the graph
  lives in `graphify-out/`, itself gitignored, so indexing an ignored folder leaks nothing.

The `SKIP` list is what keeps the walk honest — the kit alone installs ~950 `.md` files
under `.claude/`. Measured: **7 documents with the list, 959 without.** Never walk without
it. A user who needs to narrow further has graphify's own `.graphifyignore`, which its
scanner honours.

`KEEP` is the set graphify can actually parse (`DOC_EXTENSIONS` + `PAPER_EXTENSIONS` +
`OFFICE_EXTENSIONS`). Filtering up front is not cosmetic: `classify_file()` returns `None`
for anything else and prints nothing, so an unsupported file counted as indexed would vanish
without a trace.

Deliberately outside `KEEP`:

| format | why |
|---|---|
| `.csv` `.xls` `.pptx` `.doc` `.ppt` `.odt` | graphify does not parse them — convert to `.xlsx`, `.docx`, or `.pdf` |
| `.html` `.yaml` `.yml` | parseable, but in a real repository these are overwhelmingly build output and config; extraction would spend tokens on noise |
| images, audio, video | parseable, but vision costs a chunk per image and audio needs Whisper transcription first. Too expensive for a default; add only on explicit request |

An explicit `path` argument overrides all of this and is taken literally. `--all` widens to
the project root but keeps `SKIP` and `KEEP`. Never index outside the project unasked.

**Zero documents found** → say so and stop. Do not invoke `/graphify`, and do not treat an
empty corpus as an error; a code-only project legitimately has nothing to index here.

### 4. Recover what graphify cannot read from OOXML

Graphify reads `.docx` as `doc.paragraphs` and `.xlsx` as `load_workbook(data_only=True)`
— text and cell values only — and does not read `.pptx` **at all**: it is absent from
`OFFICE_EXTENSIONS`, so a deck contributes nothing no matter which extras are installed.
Two things are therefore invisible: every embedded diagram, and the whole of every slide
deck. Both matter early in a project, when the architecture lives in a kickoff deck.

All three formats are ZIP containers, so both gaps close with the standard library. Run
these before invoking `/graphify`, over the `.docx`/`.xlsx`/`.pptx` files in `docs`:

```bash
python3 scripts/extract_embedded_media.py <docs...> --out graphify-out/.scratch/media --clean
python3 scripts/ooxml_text.py            <docs...> --out graphify-out/.scratch/text
```

**The scratch directory must live under `graphify-out/`.** Graphify excludes its own output
directory from scanning, so anything placed there is invisible to the AST pass while the
extraction subagents can still read it by path. Put it anywhere else and the next
`graphify update` indexes the sidecars themselves: verified on a demo run, a top-level
`.graphify-scratch/` produced 8 file and heading nodes whose `source_file` pointed at
temp paths that the cleanup step then deleted. `graphify-out/` is also already gitignored.

`extract_embedded_media.py` returns a `provenance` map. **Use it.** Extracted files live in
that scratch directory, so after extraction rewrite each resulting node's `source_file`
back to the document it came from — otherwise the graph keeps nodes pointing at paths that
no longer exist. It also deduplicates by content hash — a slide master repeats its logo on
every slide and each image costs its own subagent — and caps at 30 images per document,
reporting `cap-reached` rather than truncating in silence.

`ooxml_text.py` writes one `<name>.ooxml.md` sidecar per document. For `.pptx` this is the
only text that will ever reach the graph, rendered one section per slide. For `.docx` and
`.xlsx` it is a **fallback**: when `graphifyy[office]` is installed graphify does a better
job, keeping heading levels and tables, so prefer the extra and use the sidecar only when
step 2 found the parser missing.

Hand the extracted images to step 5 so they are counted before anything is confirmed, and
delete `graphify-out/.scratch/` when the run ends.

### 5. Count everything, report what will be skipped, then confirm

Semantic extraction spends real tokens. Report the counts and extension breakdown, and ask
for confirmation above the thresholds below — someone who asked to index four spec files
should not silently pay for four hundred.

**This runs after step 4 on purpose.** Images pulled out of decks dominate the bill, so a
gate placed before the extraction would quote a number that is not the one charged. On a
real corpus of client requirement decks the standalone images numbered 9 while the decks
held 167 more: confirming on 9 and then spending 176 is not consent.

**Documents and images need separate thresholds because they cost differently.** `/graphify`
batches documents into chunks of 20-25 but gives *every image its own chunk* ("vision needs
separate context"). So documents cost `ceil(N / 22)` subagents while images cost `N` — one
image is worth roughly twenty-two documents. Confirm above **~50 documents** or **~10
images**. (`/graphify`'s own estimate line, `ceil(uncached_non_code_files / 22)`, quietly
undercounts whenever images are present.)

Also surface `skipped` whenever it holds something graphify could have used had it been in a
different format, with the conversion named. Silence here is the failure mode: the file is
sitting in the corpus, the user assumes it was read, and nothing ever says otherwise.

```
7 documents to index (4 .md, 2 .xlsx, 1 .docx)   → ~1 subagent
1 slide deck (kickoff.pptx)                      → text + 2 diagrams recovered (step 4)
5 images (3 standalone, 2 from the deck)         → 5 subagents
1 skipped — graphify cannot parse it:
  docs/specs/backlog.csv   → convert to .xlsx or a markdown table
```

Two further silent drops happen inside graphify itself and cannot be pre-empted here, only
explained if a document goes missing: office files above the zip-bomb caps (50 MiB on disk,
512 MiB decompressed, 200:1 ratio) return empty, and so does any file `.graphifyignore`
matches.

### 6. Wait for the graph to settle, then back it up

The SessionStart hook spawns `graphify update` **detached**, so a rebuild may still be
writing `graphify-out/graph.json` when this skill starts. Graphify serialises its own
rebuilds with `fcntl.flock` — but that guard is POSIX-only; on Windows the lock helper
returns before it even creates `.rebuild.lock`, so there is no lock file to inspect and no
mutual exclusion at all. A collision leaves a half-written `graph.json`, and graphify then
degrades to AST-only **silently** (`except Exception: pass  # corrupt graph.json`), losing
every doc edge without an error.

Use a portable settle-then-backup guard — no `fcntl`, no PID, identical on Windows, macOS,
and Linux:

```python
import json, shutil, time
from pathlib import Path

g = Path("graphify-out/graph.json")
sig = lambda p: (p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else None

for _ in range(4):                       # settle: size+mtime unchanged across a pause
    a = sig(g); time.sleep(1.5)
    if a == sig(g): break
else:
    raise SystemExit("graph.json still changing — a rebuild is in flight; retry shortly")

def semantic_count(p):                   # None => unreadable/corrupt
    try:
        return sum(1 for n in json.loads(p.read_text(encoding="utf-8"))["nodes"]
                   if n.get("_origin") != "ast")
    except Exception:
        return None

before = semantic_count(g)
if g.exists():
    shutil.copy2(g, g.with_suffix(".json.bak"))
```

Keep `before` — step 6 compares against it. Note semantic nodes carry **no** `_origin`
field at all (only AST nodes are tagged), which is why the test is `!= "ast"` and never
`== "llm"`.

### 7. Invoke the `/graphify` skill — never the bare CLI

```
/graphify <path> --update
```

The leading slash matters. The **skill** performs semantic extraction by dispatching
subagents inside the current session — the host agent is the LLM, so **no API key is
required**. The bare `graphify` CLI cannot do this: `graphify extract` refuses without a
provider key, and `graphify update` silently indexes code only. Graphify itself prints
`For doc/paper/image changes run /graphify --update in your AI assistant`.

The `/graphify` skill already handles installation, corpus detection, chunking, the
extraction cache, merging, and cost tracking. Do not reimplement any of it here.

**Keep extraction in-session.** If `GEMINI_API_KEY` or `GOOGLE_API_KEY` is set, `/graphify`
switches to Gemini instead of dispatching subagents. When the user wants extraction to stay
on the local agent, clear those two variables for the invocation only.

### 8. Verify, recover if needed, and report

Re-run `semantic_count`. Two outcomes mean the run damaged the graph — restore
`graph.json.bak` and tell the user, do not leave it broken:

- **`None`** — `graph.json` is unreadable. A concurrent write corrupted it.
- **lower than `before`** — the doc layer was dropped; graphify fell back to AST-only.

Otherwise the count should have risen. Then report:

- documents indexed, and how many were served from cache
- **chunks dropped**: `/graphify` warns and skips a chunk whose subagent returned invalid
  JSON. Surface that count explicitly — a silent skip means those documents are missing
  from the graph.
- token cost, read from `graphify-out/cost.json`

## Cost Control

Extraction runs on the session's subagent model. To index on a cheaper model, the user sets
it once at the harness level — this skill does not override it:

| Harness | Lever |
|---|---|
| Claude Code | `CLAUDE_CODE_SUBAGENT_MODEL=haiku` (highest precedence, above per-invocation and frontmatter) |
| Codex | the `[agents]` default in `.codex/config.toml` |

Re-runs are cheap: `/graphify` caches extraction per file, so only new or changed documents
are re-processed.

## Boundaries

- **Does not touch code edges.** The SessionStart hook and git hooks own those.
- **Does not generate documentation.** For that, use `tkm:rebuild-spec` (code → docs) or
  `tkm:manage-docs`.
- **Does not answer questions.** After indexing, `tkm:ask-expert` and the other graph
  consumers pick up the new edges automatically.
- Degrades quietly: if Graphify is unavailable or extraction fails, say so and stop. Never
  block the user's real task on graph availability.

## References

- [`_shared/graphify-code-graph.md`](../_shared/graphify-code-graph.md) — shared rules for
  consuming the graph, graph shape, freshness contract
