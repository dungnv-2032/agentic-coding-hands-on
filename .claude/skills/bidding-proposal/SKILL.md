---
name: tkm:bidding-proposal
category: presales
roles: [pm]
description: "Generate an SVN Proposal PPTX from either a markdown document the user supplies (attached proposal / profile md — used verbatim, Clio never touched) or, when none is supplied, from the Clio Knowledge Graph. Auto-detects the source first, then whether to run Step A (gen md) before Step B (gen slide). Explicit flags: `--gen md` or `--gen slide`. No flag needed — say 'gen slide for project X', or 'tạo slide từ file md đính kèm', and the skill handles the rest."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - mcp__clio__clio_get_assets_download_url
  - mcp__clio__clio_get_assets_upload_url
  - mcp__clio__clio_finalize_assets_upload
  - mcp__clio__clio_get_artifacts_upload_url
  - mcp__clio__clio_query
argument-hint: "[--gen md|slide] [--project-id ID] [--extra-slides PATH.json]"
metadata:
  author: takumi-agent-kit
  version: "3.2.0"
---

# Slide Proposal — SVN Proposal Generator (2-step pipeline)

This skill runs in two sequential steps, with **smart auto-routing** when no step is specified:

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Auto** | No flag / "gen slide" / "tạo slide" | Resolve the source document (Step 0.0) → if it is a document the user supplied, go straight to Step B; else run Step A then Step B |
| **Step A** | `--gen md` | Check Clio for existing profile → download all assets + merge OR query KG + generate fresh → output local markdown for review |
| **Step B** | `--gen slide` | Check for unresolved conflicts → render SVN PPTX → upload to Clio **only when the content came from Clio** |
| **Optional** | `--extra-slides` | AI-generated extra slides from JSON to be included when running Step B |

After Step A, the user may review and edit the markdown before Step B runs. In auto mode the two steps execute back-to-back without interruption.

The profile markdown is **domain-organized**, not slide-organized — adding/removing slides only requires changing the template config, not the agent workflow.

### Two ways in — pick one, never both

The deck's content comes from exactly ONE source, decided at Step 0.0 before anything else runs:

| Source | When | Path |
|--------|------|------|
| **A document the user supplies** | They attach, paste a path to, or point at a proposal/profile markdown | **Step B only**. Clio never queried, nothing uploaded. |
| **Clio Knowledge Graph** | No document supplied | **Step A → Step B**. |

> **A supplied document always wins, and is never mixed with the other source.**
> That file *is* the proposal — never "enrich" it from the KG, never regenerate
> it, never reconcile it against Clio. Doing so silently replaces the user's own
> wording with KG content.

**Requires:** Clio MCP server configured (see Setup below) — **for Step A only**. Step B renders from local markdown and needs no Clio access at all, so the supplied-document path works with no MCP server configured.

---

## Entry Point — Smart Routing

**This section runs first, before any step, whenever the skill is invoked.**

### Step 0.0: Resolve the source document — BEFORE anything else

**Ask this question first, every time: did the user supply the content?**

The user supplied it if their message attaches a markdown file, gives a path to
one, pastes proposal content, or names one ("dựa vào file md tôi đính kèm",
"from the attached proposal", "use this md"). If so:

1. **Copy the supplied file VERBATIM** to `outputs/project_content_{project_id}.md`
   (resolve `project_id` via Step 0.1 first; ask the user for a short slug if it
   cannot be resolved — a supplied document needs no Clio project).

   **Copy means copy.** Do not rewrite headings, do not change `##` / `###`
   levels, do not split one chapter into several, do not invent a title for a
   table or a paragraph, do not merge or drop sections, do not summarize, do not
   translate, do not "convert it to the schema". `gen-slide.py` reads a proposal's
   own chapter titles directly — see `references/supplied-document.md`. Any
   rewriting you do is content the user did not write and did not ask for.

1b. **Write the `sections:` mapping — the ONE thing you may add.**

   You have just read the whole document, so you know which chapter is the
   background, which is the feature list, which is the cost. The parser does not:
   it falls back to a fixed alias table that only knows wordings someone met
   before, and a proposal phrased its own way reaches **none** of the 17 bespoke
   template slides. Prepend a front-matter block naming what you found:

   ```markdown
   ---
   sections:
     "1. 本システムの全体像": container
     "1.1 現行業務の課題と狙い": project_background
     "1.2 提供機能の一覧": features
     "2. 導入効果": benefits
     "7. お見積り": cost
   ---
   ```

   - Key = the chapter heading **exactly as the document writes it**.
   - Value = one section key, or `container` for a chapter whose `###`
     subsections are the real sections. An invalid key stops the run.
   - Valid keys: `cover`, `agenda`, `project_background`, `features`,
     `nfr_overview`, `screen_flow`, `business_process`, `benefits`,
     `approach_comparison`, `assumptions`, `infrastructure`, `software_stack`,
     `nfr_sections`, `nfr_detailed`, `deliverables`, `schedule`, `cost`.
   - Map only what you are sure of. An unmapped chapter falls through to the
     alias table and then to an appendix slide — the old behaviour, not a loss.

   **This block is metadata ABOUT the document, never a rewrite OF it.** The
   chapters, their order, their heading levels and their wording stay untouched.
   Adding front matter is the only permitted addition; step 1's rules still hold
   for everything below it.

   `gen-slide.py` reports what happened — `Sections resolved: 9/9 chapters
   (8 mapping, 1 alias, 0 appendix)`. Read that line: a low ratio means chapters
   are landing on generic slides and the mapping needs more entries.

2. **Go straight to Step B.** Skip Step A entirely. Do NOT call `clio_query`, do
   NOT download from Clio, do NOT merge KG data in. Skip the Clio upload at the
   end of Step B too — the document is the user's, not Clio's.

3. Tell the user: `"Using your document as the only source — skipping gen md and
   Clio entirely, rendering the slide directly."`

If the user supplied nothing, fall through to Step 0.1 and use Clio as the
source, exactly as before.

> "The user gave me a file but the KG has fresher numbers" is not a reason to
> query the KG — it is a reason to say what looks stale and let them decide.

### Step 0: Resolve intent and project_id

1. **Determine project_id** — check in order:
   - Explicit `--project-id` argument from user
   - `.clio.yml` in CWD (`project_id: xxx`)
   - `.estimate.yml` in CWD (`project_id: xxx`)
   - If still missing: ask the user once, then proceed

2. **Determine which step to run** based on the user's input:
   - User passed `--gen md` explicitly → go to **Step A only**
   - User passed `--gen slide` explicitly → go to **Step B only**
   - Otherwise (no flag, or natural language like "gen slide for project X", "tạo slide", "generate proposal") → **Auto mode**: continue to Step 0.3 below

3. **Auto mode — check for existing local markdown:**
   ```bash
   ls outputs/project_content_{project_id}.md 2>/dev/null
   ```
   - **File exists** → skip Step A, go directly to **Step B**. Inform the user: `"Found existing markdown outputs/project_content_{project_id}.md — skipping gen md, rendering slide directly."`
   - **File does NOT exist** → run **Step A** first (silently, no need to ask the user), then **Step B** automatically when Step A completes. Inform the user: `"No local markdown found — running gen md first, then gen slide automatically."`

> **Do NOT ask the user which step to run.** The check above is deterministic. Only ask if `project_id` cannot be resolved.

> **`--gen slide` does not override Step 0.0.** The flag picks the step; Step 0.0
> picks the source. A user who passes `--gen slide` AND attaches a document still
> gets the document copied into place first — the flag is not permission to render
> a stale `outputs/project_content_{id}.md` from an earlier run.

---

## Data Provider

**Clio Knowledge Graph is the data provider for Step A only, and Step A runs
only when the user supplied no document of their own** (Step 0.0). Everything
below describes that path; on the supplied-document path none of it applies and
no MCP server is needed.

- Query tool: `clio_query` MCP tool
- Config: `.clio.yml` (primary) / `.estimate.yml` (fallback)

### Setup

Add to `.mcp.json` or `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "clio": {
      "type": "http",
      "url": "https://clio.sun-asterisk.vn/mcp",
      "headers": { "x-api-key": "${CLIO_API_KEY}" }
    }
  }
}
```

Then create `.clio.yml` in project root with `project_id: your-project-id`.

### After ANY change to `templates/SVN Proposal Menu.pptx`

`lib/templates/svn.py` addresses the template by exact string and by shape index. Editing the `.pptx` silently disables a mapping rather than erroring — so run the contract check and fix what it names:

```bash
$VENV_PYTHON $SKILL_DIR/scripts/verify-template-contract.py
```

Exit 0 means every mapping still resolves. A failure is reported and fixed, never silenced by deleting the entry — dropping a `TEMPLATE_NOTE_TEXTS` line re-ships a Vietnamese authoring note to the client.

---

## Step A — `--gen md`

> **Skip this whole step when the user supplied the source document** (Step 0.0).
> Everything here — the KG queries, the reference files, the content templates
> they prescribe — exists to *author* a profile when there isn't one. Applying
> any of it to a document the user already wrote rewrites their content. In
> particular the section templates in `references/` fix a column shape for each
> table (the feature table's `No / カテゴリ / PID / 画面・機能 / 機能要件 / 詳細`,
> for one); those shapes are for KG-authored content only, and a supplied
> document's own tables are copied as they stand, column for column.

The agent checks Clio for an existing profile markdown (downloading all associated assets), then either merges new KG data into it or generates a fresh one from scratch. The result is saved locally for user review — all uploads happen in Step B after the slide renders.

### Workflow

1. **Read project_id** from `.clio.yml` (fallback `.estimate.yml`; ask user if missing)

2. **Check Clio for existing SLIDE_CONTENT file** — call the `clio_get_assets_download_url` MCP tool:
   ```json
   { "project_id": "{project_id}" }
   ```
   The response contains an `items` array. If empty → Case 1.1. If non-empty → Case 1.2.

3. **If file exists on Clio (Case 1.2):**
   - Download **ALL items** returned by the list response — iterate over every item regardless of file type:
     - For `.md` files: save to the canonical fixed name `outputs/project_content_{id}.md`
     - For all other files (`.png`, etc.): save using their remote filename `outputs/{file_name}`

   > **⚠️ CRITICAL — HOW TO DOWNLOAD:** Always use the **Bash tool** to call `clio-api.py download`. **NEVER use WebFetch** for presigned S3 URLs — WebFetch goes through a proxy that blocks the storage domain, and presigned URLs are too long for WebFetch anyway. The only correct method is via the Python script below.

     ```bash
     VENV_PYTHON=$([ -f ".claude/skills/.venv/bin/python3" ] && echo ".claude/skills/.venv/bin/python3" || echo "python3")
     SKILL_DIR="claude/skills/bidding-proposal"

     # For the markdown file (run via Bash tool):
     $VENV_PYTHON $SKILL_DIR/scripts/clio-api.py download \
       --url "{md_download_url}" \
       --output outputs/project_content_{id}.md
     # For every other file in the list (PNG, etc.) — do NOT skip any:
     $VENV_PYTHON $SKILL_DIR/scripts/clio-api.py download \
       --url "{item_download_url}" \
       --output outputs/{item_file_name}
     ```
   - Query KG for the latest data for each section — read each reference file first, then execute the **exact Japanese query strings** defined in that file. Do NOT write your own queries, do NOT translate to English. The KG is built from Japanese documents and only returns results for Japanese queries.
   - Compare KG data against downloaded markdown section by section:
     - **New info not in markdown** → append/update the relevant section
     - **Conflict (KG value differs from existing value)** → mark inline:
       ```
       <!-- CONFLICT: KG says "X", current value is "Y" — needs review -->
       ```
   - **PNG regeneration:** If KG data for `screen_flow` or `schedule` sections changed (new diagram content detected), regenerate the affected PNG(s) via Mermaid CLI and overwrite the local file. They will be uploaded in Step B.
   - The merged result is already at `outputs/project_content_{id}.md` (the file downloaded above, edited in place)

4. **If no file on Clio (Case 1.1):**
   - Query Clio KG for each domain section — **read each reference file first**, then execute the **exact Japanese query strings** defined step-by-step in that file. Do NOT write your own queries. Do NOT translate to English. The KG is built from Japanese documents; English queries return empty results.
   - Generate PNG images (Mermaid CLI for screen flow + schedule)
   - Assemble JSON matching `ProjectProfile.to_dict()` shape
   - Invoke `gen-md.py` with `--project-id {id}` — outputs `outputs/project_content_{id}.md` (fixed name, no timestamp)

5. **Report to user:**
   - If conflicts were found: `"Found N conflict(s) marked in the markdown. Please review and edit outputs/project_content_{id}.md to resolve all <!-- CONFLICT: ... --> markers, then run --gen slide."`
   - If no conflicts: `"Markdown generated/updated locally. Run --gen slide when ready."`

### Profile JSON shape

The JSON the agent assembles must match the dataclass tree in `scripts/lib/profile_schema.py`. Top-level keys: `cover`, `agenda`, `project_background`, `features`, `nfr_overview`, `screen_flow`, `business_process`, `benefits`, `approach_comparison`, `assumptions`, `infrastructure`, `software_stack`, `nfr_sections`, `nfr_detailed`, `schedule`. Omit any section the KG has no data for.

`cover` (`{company, date}`) and `agenda` (`{chapters[], cost_breakdown[]}`) fill slides 1 and 2. Both are optional — omitted, the template keeps its own wording. How to source and word them: `references/cover-and-agenda.md`.

### Reference Files (what to query per section)

| Section(s) | Reference |
|------------|-----------|
| project_background, features, nfr_overview | `references/generate-content-overview.md` |
| screen_flow, business_process | `references/generate-content-flow.md` |
| benefits | `references/generate-content-benefits.md` |
| approach_comparison, assumptions | `references/generate-content-approach.md` |
| infrastructure, software_stack, nfr_sections, nfr_detailed, schedule | `references/generate-content-technical.md` |

### Invocation (Case 1.1 — fresh generation)

```bash
VENV_PYTHON=$([ -f ".claude/skills/.venv/bin/python3" ] && echo ".claude/skills/.venv/bin/python3" || echo "python3")
SKILL_DIR="claude/skills/bidding-proposal"

# Agent writes JSON to a temp file, then:
$VENV_PYTHON $SKILL_DIR/scripts/gen-md.py \
  --project-id {project_id} \
  --input /tmp/profile_{project_id}.json \
  --output-dir outputs/
```

---

## Step B — `--gen slide`

Reads the profile markdown and renders the SVN PPTX. **No Clio KG access needed** —
this is the whole of the run when the user supplied the source document (Step 0.0).

### Workflow

1. **Locate input** — use `outputs/project_content_{id}.md` (fixed filename, one file per project). On the supplied-document path this is the verbatim copy Step 0.0 placed there; do not re-derive or regenerate it.
2. **Check for unresolved conflicts** — scan the file for any `<!-- CONFLICT:` markers:
   - If found: **stop immediately** and tell the user:
     `"The markdown still has N unresolved conflict(s). Please edit outputs/project_content_{id}.md, resolve all <!-- CONFLICT: ... --> markers, then re-run --gen slide."`
   - If none: proceed
   > Conflict markers only ever come from Step A's KG merge. A supplied document has none, so this check passes untouched.
3. **Invoke `gen-slide.py`** — parses profile, runs role-based rendering against the SVN template
   > **Read the last line it prints.** `[gen-slide] WARNING: slide 1 still shows the TEMPLATE PLACEHOLDER` means the cover kept `SVN Proposal Menu` / `2025.04.04` because the document's addressee or date notation wasn't understood. Do NOT edit the user's document — re-run with `--cover-company "..."` / `--cover-date "..."` (see `references/cover-and-agenda.md`) before going any further.
4. Output → `outputs/proposal_{id}_{ts}.pptx`
   > The default name is built from the `# Project Profile: {id}` / `Generated: {ts}` header lines. A supplied proposal has neither, which would name the file `proposal__.pptx` — so on that path **always pass `--output proposal_{project_id}` explicitly**.
5. **Visual QA (best-effort, skips silently if `officecli` isn't installed):**
   - From `gen-slide.py`'s stdout, collect every `- Inserted extra slide "..." [...] at index N` line (printed for both auto-routed unrecognized sections and manually-authored `--extra-slides` entries). Slide number = `N + 1` (the print is 0-indexed). This is `--auto-slides` below — pass `""` if no such lines were printed.
   - Run `collect-qa-slides.py` to widen the net beyond auto-routed slides: it also asks `officecli view <pptx> issues` for real text-overflow/off-slide/overlapping-shape hotspots and folds in the noisiest ones (capped at `--max-extra`, default 5, so a deck's already-known-and-handled overflow — see `_queue_overflow_extra` in `renderer.py` — doesn't balloon the QA batch). This is what catches bugs in the 17 bespoke template slides that auto-routing alone never looks at.
     ```bash
     VENV_PYTHON=$([ -f ".claude/skills/.venv/bin/python3" ] && echo ".claude/skills/.venv/bin/python3" || echo "python3")
     SKILL_DIR="claude/skills/bidding-proposal"

     $VENV_PYTHON $SKILL_DIR/scripts/collect-qa-slides.py \
       --input outputs/proposal_{id}_{ts}.pptx \
       --auto-slides "{comma-separated 1-indexed slide numbers from step above, or empty string}"
     ```
     Prints `{"available": false, "slides": "..."}` if `officecli` can't be reached (falls back to just the auto-routed slides, same as before) or `{"available": true, "slides": "...", "issue_flagged_dropped": [...], ...}`. If `issue_flagged_dropped` is non-empty, mention in passing that N additional lower-priority slides were skipped by the cap — don't block on it.
     - If `slides` is empty, skip QA entirely — nothing to check.
   - Otherwise screenshot exactly that slide list:
     ```bash
     $VENV_PYTHON $SKILL_DIR/scripts/qa-slides.py \
       --input outputs/proposal_{id}_{ts}.pptx \
       --slides "{the "slides" value from collect-qa-slides.py}" \
       --output-dir outputs/qa_{id}/
     ```
   - Both scripts auto-download `officecli` on first use if not already on PATH (cached under `~/.cache/bidding-proposal/bin`, verified against the release's SHA256SUMS — no PATH/system changes, safe to delete). If `qa-slides.py` prints `{"available": false}` — unsupported platform or no network reachable to GitHub — skip QA and fall back to the existing manual-review message below.
   - If it prints `{"available": true, "screenshots": [...]}` — for each entry with `"ok": true`, use the **Read tool** on its `path` (PNG) and check for text overflow, overlapping shapes, empty/orphaned placeholder boxes, or an obviously broken layout. Entries with `"ok": false` mean that slide couldn't be rendered (log the error, don't block on it). Some slides pulled in by the issues scan may turn out fine on inspection (e.g. an off-slide decorative shape from the base template, or text truncation already handled by the appendix mechanism) — that's expected noise, not a failure; only act on what's actually visible and wrong.
     - **Issues found** → tell the user which slide number(s) and what looks wrong, then ask whether to proceed with upload as-is or fix `outputs/project_content_{id}.md` first (loop back to editing + re-running `--gen slide` if they choose to fix).
     - **No issues** → proceed straight to upload, no need for the manual-review prompt.

> **STOP HERE on the supplied-document path.** Steps 6 and 7 upload to Clio, and
> the content is the user's document, not Clio's — pushing it there publishes a
> document they only asked you to render. Hand back the PPTX and finish. Upload
> only if the user asks for it in so many words.

6. **Upload to Clio — Clio-sourced runs only.** Follow `references/clio-upload.md`:
   the approved markdown and every PNG in `outputs/` as assets, then the PPTX as
   an artifact. On the supplied-document path, stop at step 5 instead.
### Invocation

```bash
$VENV_PYTHON $SKILL_DIR/scripts/gen-slide.py \
  --input outputs/project_content_{project_id}.md \
  --output-dir outputs/
```

`--template` defaults to `SVN Proposal Menu.pptx` (auto-resolved from `templates/`).

`--cover-company` / `--cover-date` force slide 1's client name and date, overriding
the document. Add them only when gen-slide's closing WARNING says the cover went
unfilled — the parser reads the addressee (`御中`, `Kính gửi`, `Prepared for:`) and
the date (`YYYY.MM.DD`, `YYYY/MM/DD`, `YYYY-MM-DD`, `YYYY年M月D日`) on its own:

```bash
  --cover-company "Evering" --cover-date 2026-04-19
```

> **Environment note:** `VENV_PYTHON` auto-detects the interpreter — uses the venv on local/Takumi installs, falls back to system `python3` on sandboxes where the venv is absent. Both `clio-api.py` and `gen-slide.py` call `ensure_deps()` at startup to self-bootstrap `python-pptx`/`lxml`/`Pillow`/`requests` into a writable temp dir when the packages are not yet installed. No manual `pip install` needed.

---

## Hand-written / free-form markdown — how a supplied document is read

**This is why Step 0.0 says "copy verbatim".** `gen-slide.py` reads a proposal's
own chapter titles directly — Japanese or English, numbered or not — and fills
the bespoke template slides from them. A chapter it still cannot place becomes an
`Appendix` slide rather than being dropped, and each one is reported on stdout as
`[profile-parser] WARNING: unrecognized section "..."`.

Each slide is then **headed by the document's own chapter title**, not the
template's — and on a document that isn't Japanese, the template's fixed
Japanese labels are Englished and the cover's `○○株式会社　御中` line is
dropped. No flag: the language is read off the document. A Japanese proposal
renders exactly as it always did.

Full behaviour — the heading-matching rules, the container-chapter unwrapping,
the layout chosen per content shape, the language handling and how to read the
WARNING list — is in **`references/supplied-document.md`**. Read it before
reshaping any document.

---

## Step B (optional) — `--extra-slides` AI-generated extra slides

After Step A, the user may edit the content markdown and add **free-form extra sections** that don't fit the 17 fixed slide templates. Each is rendered as a polished slide using a **generate-slide-style layout** (ported from `tkm:generate-slide`), drawn onto a blank canvas cloned from the template's blank end card and inserted right after the section it follows.

Use this when an AI agent should pick the layout deliberately (e.g. to match a specific visual intent). For markdown that's simply hand-written without following the schema at all, the automatic routing above already handles it with zero extra authoring — reach for `## extra:` + hand-crafted JSON only when the automatic heuristic's layout choice isn't good enough.

### Convention in content MD

```markdown
## Features
...

## extra: Migration Strategy
Free-form content the user wants to add. Bullets, paragraphs, anything.
- Phase 1: data export
- Phase 2: dual-write
- Phase 3: cutover

## Non-Functional Requirements (Overview)
...
```

- Heading prefix `## extra:` (case-insensitive) marks an extra section.
- The **anchor section** is the nearest preceding `## <known section>` heading — the new slide is inserted right after the slide(s) that section fills (e.g. `## extra:` placed after `## Features` → inserted after slide 5).

### Agent workflow when user requests extra slides

1. Read the content markdown; locate every `## extra: <title>` block and its preceding known section.
2. For each block, **pick a layout** that fits the content shape (the layouts are defined in `scripts/lib/extra_slide_layouts.py`; the shape-to-layout heuristic is tabulated in `references/supplied-document.md`) and produce structured content for that layout via AI. Vary layouts across slides.
3. Write a JSON file `/tmp/extra_slides_{project_id}.json` — a list of slide entries:
   ```json
   [
     {
       "layout": "numbered_points",
       "title": "Migration Strategy",
       "anchor_section": "features",
       "points": [
         {"header": "Data export", "body": "Export legacy data to staging."},
         {"header": "Dual-write", "body": "Write to both systems."},
         {"header": "Cutover", "body": "Switch traffic over."}
       ]
     }
   ]
   ```
   - `anchor_section` ∈ keys of `SECTION_TO_SLIDES` in `scripts/lib/templates/svn.py`. Or pin with `"anchor_slide": <int>`.
4. Invoke gen-slide with the extra slides:
   ```bash
   $VENV_PYTHON $SKILL_DIR/scripts/gen-slide.py \
     --input outputs/project_content_{id}.md \
     --extra-slides /tmp/extra_slides_{id}.json \
     --output-dir outputs/
   ```

### Supported layouts (`layout` field + per-layout content keys)

Implemented in `scripts/lib/extra_slide_layouts.py`. Every entry takes an optional `title`.

| `layout` | Content key | Shape it fits |
|----------|-------------|---------------|
| `bullets` *(default)* | `bullets: [str]` | simple list, fallback |
| `numbered_points` | `points: [{header, body}]` (3–5) | sequential/enumerated points |
| `card_grid` | `items: [{title, body, icon?}]` (≤4) | 4 parallel concepts |
| `comparison_2` | `columns: [{title, items:[str]}, {title, items:[str]}]` | two things compared |
| `process_flow` | `steps: [str]` (3–5) | sequential steps |
| `hero` | `message: str` | one big takeaway |

### Notes
- Layouts use the Sun* palette (Sun Red `FF2200`, gold, greys) + Noto Sans JP, auto-scaled from the generate-slide 13.333″ canvas to the SVN 10″ canvas.
- Extra slides are created from a **content slide's layout**, so they inherit the deck's background + master footer / page number / logo. The layout content is drawn directly on top (no white overlay), so the template shows through.
- Overflow handling from main rendering (e.g. table splits in slides 23-25) is accounted for — anchor positions adjust automatically.
- Multiple extras with the same anchor are inserted in the order they appear in the JSON.
- To add a new layout: add a renderer fn in `extra_slide_layouts.py` and register it in `_LAYOUTS`.

---

## Common Rules

- Read `project_id` from `.clio.yml` first, fallback to `.estimate.yml`; ask user if missing
- All KG queries run **SEQUENTIALLY** (not parallel)
- Use `clio_query` MCP tool for all KG queries
- **KG queries MUST use the exact Japanese text defined in each reference file** — do NOT write your own queries, do NOT translate to English. The KG is built from Japanese documents; English queries always return empty results.
- If a query returns empty/unclear, run one broader follow-up; if still unknown, omit that field
- All outputs saved to `outputs/` in CWD (or `SLIDE_GENERATOR__OUTPUTS_PATH` env var)
- **No fabrication** — only include data from KG
- **PNG images only** — generate PNG files via Mermaid CLI; reference them as file paths in the profile (no base64)

---

## Output Files

| File | Step | Description |
|------|------|-------------|
| `outputs/project_content_{id}.md` | A, B | Domain-organized profile; uploaded to Clio as `SLIDE_CONTENT` in Step B via `clio_get_assets_upload_url` |
| `outputs/screen_flow_{id}_{ts}.png` | A, B | Screen transition diagram (Mermaid); uploaded to Clio in Step B; regenerated if flow data changed |
| `outputs/schedule_{id}_{ts}.png` | A, B | Gantt chart (Mermaid); uploaded to Clio in Step B; regenerated if schedule data changed |
| `outputs/proposal_{id}_{ts}.pptx` | B | Final PPTX; uploaded to Clio as `SLIDE_PROPOSAL` via `clio_get_artifacts_upload_url` |

> Every "uploaded to Clio" above applies to **Clio-sourced runs only**. On the
> supplied-document path (Step 0.0) nothing leaves the machine: the profile
> markdown is the user's own file and the PPTX is handed back directly. The PNGs
> are not produced at all — they come from Step A's Mermaid generation.

---

## Slide Coverage

The SVN Proposal template (`SVN Proposal Menu.pptx`, 72 slides) is a **slide pool, not a fixed skeleton** — it fills 17 content slides, but the *output* deck is content-driven: only sections present in the profile produce slides. Cover (slide 1) and agenda (slide 2) are always kept; a chapter divider (e.g. "System Overview", "Estimated Assumptions") is kept only when its chapter has ≥1 filled slide. Empty sections produce no slide at all (and no orphan divider) — the old behavior of leaving a blank slide for a missing section is gone. The same applies *within* a section that spans several template slides (`benefits[0:2]`/`[2:4]`, `assumptions[0:5]`/`[5:8]`/`[8:9]`): a surplus slide the fill pass never wrote to is dropped rather than shipped with the template's own sample content — only the section's first slide is guaranteed to survive. Slide order follows the profile markdown's `## heading` order (falls back to the canonical section order below if that's unavailable). The mapping from profile section → slide(s) lives in `scripts/lib/templates/svn.py` (`SlideRoleConfig` for filling, `SECTION_TO_SLIDES` + `CHAPTER_DIVIDERS` for picking). To add a new slide, declare a new `SlideRoleConfig` plus its `SECTION_TO_SLIDES` entry (and `CHAPTER_DIVIDERS` entry if it belongs to an existing chapter) in `svn.py` — no changes to gen-md or gen-slide are needed.

| Slide | Section consumed | Layout |
|-------|------------------|--------|
| 1 | cover (optional) | Client company name + date, filled in place |
| 2 | agenda (optional) | Chapter list + 費用 sub-items, filled in place |
| 4 | project_background | Current issues + objectives |
| 5 | features | Description + table |
| 6 | nfr_overview | Description + table |
| 8 | screen_flow | Image overlay |
| 10, 11 | business_process | Categories + before/after |
| 12, 13 | benefits[0:2], benefits[2:4] | 2 title+body each |
| 21 | approach_comparison | Table |
| 23, 24, 25 | assumptions[0:5], [5:8], [8:9] | 2-col tables (fill col 1) |
| 33 | infrastructure | Table |
| 34 | software_stack | Table |
| 35 | nfr_sections | 4 title+body pairs |
| 36 | nfr_detailed | Table |
| 43 | schedule | Text + Gantt image |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Download/upload fails with 403 or proxy error | **Never use WebFetch for presigned S3 URLs** — always use Bash tool to call `clio-api.py download` or `clio-api.py put`. WebFetch goes through a proxy that blocks `linodeobjects.com` and can't handle long presigned URLs |
| `clio_query` not found | MCP server not configured — check Setup |
| `clio_get_assets_download_url` not found | MCP server not configured — check Setup |
| `clio_get_assets_upload_url` not found | MCP server not configured — check Setup |
| `statusCode: 401` from MCP tool | `x-api-key` header missing or invalid — check MCP server config |
| `statusCode: 403` on finalize | Role lower than Editor, or API key is out of project scope |
| `statusCode: 400` on finalize | Wrong `storage_path` or `asset_type` mismatch — use exactly what `clio_get_assets_upload_url` returned |
| `clio-api.py put` HTTP error | Presigned URL expired — re-call `clio_get_assets_upload_url` to get a fresh URL |
| `download_url` expired | Presigned URLs are time-limited — re-call `clio_get_assets_download_url` to get a fresh URL |
| No `.clio.yml` | Create in project root with `project_id` |
| Mermaid PNG fails | Install Node.js and `@mermaid-js/mermaid-cli` |
| `Template not found` | Verify `SVN Proposal Menu.pptx` in `claude/skills/bidding-proposal/templates/` |
| gen-slide skips slides | Missing profile sections produce empty/cleared shapes — check JSON in Step A |
| Slide 1 still says `SVN Proposal Menu` / `○○株式会社　御中` / `2025.04.04` | The document's addressee or date notation wasn't read (gen-slide warns on its last line). Re-run with `--cover-company "..."` / `--cover-date "..."`. Never edit a supplied document to fix this. The `○○株式会社　御中` line is fixed template wording and is never filled — see `references/cover-and-agenda.md`. |
| `requests` not installed | Run `pip install -r claude/skills/bidding-proposal/scripts/requirements.txt` |
| `No module named 'pptx'` / `No module named pip` / `No module named ensurepip` (Claude Desktop sandbox) | gen-slide.py **self-bootstraps** deps via `scripts/ensure_deps.py` into a writable temp dir — and when the sandbox python ships without pip **and** ensurepip, it auto-downloads `get-pip.py` into that dir first. Just run `python3 gen-slide.py …`. **Do NOT** bootstrap pip manually across separate bash calls (sandbox `/tmp` is wiped between calls) — the script does it all in one process. Override install dir with `CLIO_PKG_DIR` if needed. |

---

## References

| Topic | File |
|-------|------|
| Profile schema (dataclass tree) | `scripts/lib/profile_schema.py` |
| Slide → profile section mapping | `scripts/lib/templates/svn.py` |
| S3 PUT + download helper (2 subcommands: put, download) | `scripts/clio-api.py` |
| QA slide selection (auto-routed + OfficeCLI issue hotspots, capped) | `scripts/collect-qa-slides.py` |
| Overview sections (background, features, NFR overview) | `references/generate-content-overview.md` |
| Flow sections (screen flow, business process) | `references/generate-content-flow.md` |
| Benefits | `references/generate-content-benefits.md` |
| Approach + assumptions | `references/generate-content-approach.md` |
| Technical (infra, software, NFR detail, schedule) | `references/generate-content-technical.md` |
| Step B execution detail | `references/generate-pptx.md` |
| MCP config snippet | `data/mcp-config-snippet.json` |
