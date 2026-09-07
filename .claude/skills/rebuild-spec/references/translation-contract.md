# Translation Contract — Prose-Only Translation with Skeleton Preservation

Subagent contract for translating a primary-language artifact into a secondary language.
The skeleton (English structural elements) MUST remain byte-identical; only prose is translated.

**Worker model:** this contract is executed by the `translator` agent, which runs on
**Haiku** (`claude/agents/translator.md`, `model: haiku`). Translation is mechanical, and the
two gates below — skeleton-identity AND the ±LOC body-size ratio — are the quality net that makes the
cheaper model safe. The model binding lives in the agent definition; spawn sites name
`subagent_type: "translator"` (never a bare `TaskCreate`, which would inherit the session model).

## Input

- ONE primary-language artifact (e.g. `docs/<primary>/features/<slug>/technical-spec.md`)
- Target language code (e.g. `ja`, `vi`, `zh`) — alias inputs like `jp`/`cn` are de-aliased to the
  canonical ISO code (`ja`/`zh`) by `normalize_lang` before any path is built
- The artifact carries prose in `primary_lang` + an English skeleton

## Output

- Same file under `docs/<target_lang>/...` with prose translated, skeleton copied verbatim

## Hard Rules (skeleton = NEVER translate)

These elements MUST be copied byte-identical from the primary. Any alteration is a CRITICAL violation caught by `validate_translation_skeleton.py`:

1. **Markdown headings** — `#`, `##`, `###`, etc. lines (full line verbatim), **EXCEPT** the
   v27.0.0 one-line block-heading form described below (Rule 1a) — there, only the trailing
   code tag is skeleton and the sentence prefix is prose.
2. **Code tokens** — `F###`, `US###`, `SCR###`, `BL###`, `PERM###`, `DEC-###`, `DISC-###`, `MODEL###`, `FLOW###`, `REG###`, `INT-###`, `BR-###`, `SM-###`, `ALG-###` (keep inline in translated prose)
3. **Field labels** — `**Linked FR:**`, `**subtype:**`, `**Triggers in:**`, `**Source:**`, etc.
4. **Table-column header rows** — the first row of any markdown table (pipe-delimited)
5. **Table separator rows** — `|---|---|---|` lines
6. **Fenced code blocks** — everything between ``` markers (opener, body, closer)
7. **Frontmatter** — YAML between `---` fences (keys AND values)
8. **File paths** — any backtick-wrapped path (e.g. `src/controllers/UserController.php`)
9. **Status enums** — `PASS`, `FAIL`, `WARN`, `CRITICAL`, `pending`, `completed`, etc.
10. **Inline code** — any backtick-wrapped text

### Rule 1a — v27.0.0 one-line block-heading form (prose + skeleton share a line)

`technical-spec.md`'s Cross-Cutting Logic BR/SM/ALG/INT blocks (H3) and DEC blocks (H4) now
head with a plain-language sentence and a trailing code tag on the SAME line —
`### {sentence} ({BR|SM|ALG|INT}-###)` / `#### {sentence} (DEC-###)` (canonical shape:
`scripts/_spec_block_lib.py::BLOCK_HEADING_RE` / `DEC_BLOCK_RE`) — replacing the old
`### BR-001_NameSlug` anchored-prefix form. Only the trailing `(BR-001)`-style tag, including
its parentheses, is skeleton; the sentence prefix is prose and is **expected to differ** across
languages, exactly like any other narrative text. Translate the sentence, copy the `(CODE-###)`
tag byte-identical. `validate_translation_skeleton.py` reduces its skeleton signature for these
headings to the heading marker + trailing tag only (e.g. `### (BR-001)`) so a legitimately
translated sentence is never flagged as drift, while a changed code token or a dropped heading
still is.

## Prose = TRANSLATE

Everything else is prose and should be translated to the target language:

- Paragraph text / narrative
- Table body cells that are descriptions (NOT header cells, NOT code tokens within cells)
- List-item narrative text
- "Overview" / functional-spec.md § 1 Problem-Solution-Users-Goals bodies
- Edge-case scenario descriptions and user-facing message text
- The plain-language sentence prefix of a `### {sentence} (BR-001)` / `#### {sentence}
  (DEC-001)` block heading (Rule 1a) — translate the sentence, keep the `(CODE-###)` tag verbatim

## Table Cell Rule

Table header rows (first row) stay English verbatim. Body cells:
- If a cell contains only a code token (e.g. `F001`) → keep verbatim
- If a cell contains narrative text → translate the text, keep any embedded code tokens verbatim
- If a cell contains a file path or enum → keep verbatim

## Ordering

Line/section ordering MUST be identical between primary and mirror. Do NOT reorder, merge, or split sections.

## Quality Gate

After translation, `validate_translation_skeleton.py --primary <src> --mirror <dst>` MUST return exit 0 (PASS). The validator enforces TWO checks; either failing is a re-translate (max 3 retries before escalation):
1. **Skeleton identity** — headings, code tokens, field labels, table headers, fenced code, frontmatter, paths, enums byte-identical.
2. **Body-size ratio** — the translated prose body must be within ±30% of the source body (line count, skeleton lines excluded). Catches a silently dropped or padded paragraph that the skeleton check alone would miss.
