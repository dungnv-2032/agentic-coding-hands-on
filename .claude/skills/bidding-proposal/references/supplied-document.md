# How a supplied document is read

Reference for Step 0.0 of `SKILL.md` — the path where the user hands over the
source markdown and Clio is never touched. Read this when you need to know what
`gen-slide.py` will do with a document before deciding whether to reshape it.

**The short version: don't reshape it.** Everything below exists to explain why
that is safe.

`gen-md.py` (Step A) is an optional convenience, not a requirement:
`outputs/project_content_{id}.md` may be hand-written, or copied straight out of
a proposal, in any structure or language, without ever running Step A.
`gen-slide.py` (Step B) is decoupled from Step A's schema on purpose, and reads a
source document at two levels before falling back to a generic slide.

## 0. The `sections:` mapping — how a chapter reaches its slide

The alias table in §1 only knows the wordings someone has already met. A proposal
phrased its own way — `導入効果` rather than `システム導入のメリット`, `構成案`
rather than `システム構成図の提案` — matches nothing in it, and every chapter
falls through to an appendix slide. Measured: an ordinary Japanese proposal with
the same seven-chapter shape as the reference documents reached **0 of the 17**
bespoke template slides.

So the agent that reads the document at Step 0.0 records what it found, in front
matter prepended to the profile markdown:

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

Resolution order per heading:

1. the mapping, by the heading's exact spelling
2. the mapping, by its normalized form (numbering and `— gloss` stripped)
3. the alias table (§1)
4. container unwrap, then an appendix slide (§2)

`container` marks a chapter whose own `###` subsections are the real sections;
the chapter itself produces no slide. A value that is not a valid section key
**stops the run** — a typo would otherwise look identical to a mapping that
worked.

The mapping is metadata *about* the document. It is the only thing that may be
added to a supplied proposal; §1's "never reshape it" rule governs everything
else. When the cover comes out wrong the fix is a command-line flag, never an
edit: `--cover-company` / `--cover-date` (see `cover-and-agenda.md`).

`gen-slide.py` prints the tally: `Sections resolved: 9/9 chapters (8 mapping,
1 alias, 0 appendix)`. Below half, it warns — the deck is about to be mostly
generic slides wearing SVN chrome.

## 1. Headings are matched by meaning, not by exact spelling

A `##` heading is resolved through `section_aliases.py`, which accepts gen-md.py's
English schema names AND the chapter titles a real proposal uses. It strips
markdown escapes, chapter numbering and the `JP — English gloss` pattern before
looking up, so all of these reach the same `features` section and fill the same
template slide:

```
## Features        ### 1.2 機能一覧        ## 機能一覧表        ## 1\. 機能一覧 — Features
```

A chapter that is really a CONTAINER — `## 1. システムの概要 — System Overview`,
whose own `### 1.1 プロジェクト背景・目的` and `### 1.2 機能一覧` are the actual
sections — is unwrapped: the subsections become sections, the chapter itself
produces no slide.

Sections whose content sits loose in the block (prose and a table together, with
no `### Description` / `### Feature Table` to look under) are read anyway. Markdown
inline markup is rendered as plain text on the way in: `[label](url)` → `label`,
`**bold**` → `bold`, escapes removed. `Sun*` survives — it is a brand name, not
emphasis.

**Consequence for the agent: never rewrite a supplied document to "fit the
schema". It already fits.** Adding a heading, promoting a `###` to `##`, or
splitting a chapter does not help the parser — it invents content the user never
wrote and pushes real sections out onto appendix slides.

Tables are copied column for column: the grid of the template slide is reshaped
to the markdown's column count, never the other way round. A 2-column table in
the source stays 2 columns on the slide.

## 2. Anything still unrecognized becomes a slide, never a deletion

Any `##` heading that matches no section name and unwraps to no known subsection
is **never silently dropped**. `profile_parser.py` classifies its content and
auto-routes it to one of the generic layouts in `extra_slide_layouts.py` — no
`## extra:` prefix or hand-authored JSON needed:

| Content shape under the heading | Layout chosen |
|---|---|
| Exactly 2 `###` subsections | `comparison_2` |
| 3–5 `###` subsections | `numbered_points` |
| A markdown table | `bullets` (one bullet per row) |
| A bulleted/numbered list | `bullets` |
| 1 or 6+ `###` subsections | `bullets` (one bullet per subsection — outside `comparison_2`/`numbered_points`' hard caps, so never truncates) |
| Short plain paragraph (≤280 chars, no blank-line break) | `hero` |
| Anything else | `bullets` |

The slide is inserted right after the last *recognized* section seen before it in
the source file (or at the end of the deck if none), and carries an `Appendix`
breadcrumb so a reader can tell it from the bespoke template slides.

This runs automatically, every time — no flag required. It composes with
`--extra-slides`: manually-authored entries are appended after the auto-routed
ones, not replaced by them.

## 3. The deck speaks the document's language

The template is a Japanese deck: every slide is headed `<chapter>  ｜  <section>`
in the wording of the proposal it was authored for, and its column headers and
captions are Japanese labels. Rendering an English or Vietnamese proposal
through it used to produce a bilingual result — the document's own body copy
under someone else's Japanese headings.

Three passes fix that, and none of them needs a flag:

1. **Slide titles come from the source's own headings.** The heading that filled
   a section, numbering stripped, becomes that slide's breadcrumb tail and the
   title below it — `### 1.1. Project Background` heads its slide
   `System Overview  ｜  Project Background`. This runs for every document,
   Japanese included: the source's wording beats the template's in any language.
2. **Chapter dividers come from the AGENDA** (see `cover-and-agenda.md`). A
   divider no agenda line names keeps its own English line on a non-Japanese
   deck, rather than standing as the only Japanese heading left.
3. **Fixed chrome is Englished on a non-Japanese deck** — the labels no heading
   can name (`現状の課題` → `Current Issues`, `導入前` → `Before`), from
   `TEMPLATE_CHROME_EN` in `svn.py`. A Japanese document never consults it.

The language is decided by the presence of kana in the document — not by a flag,
and not by the 株式会社 in the Sun* footer.

**Known gap:** a template slide the fill pass never writes to keeps its sample
SENTENCES, which are Japanese and belong to another client's proposal. Those are
not translated — a fluent English sentence this proposal never wrote is worse
than a visibly foreign one. Review them in QA (step 5) and cut them.

## 4. Reading the WARNING list

`gen-slide.py`'s stdout prints a `WARNING` per auto-routed section (heading,
chosen layout, anchor). **Always review the rendered PPTX before handing it
over** — the heuristic can't guarantee a generic layout looks as polished as the
17 bespoke slide designs.

Read that list as a report, not as noise. Each line is one chapter of the source
that found no home among the template slides:

- **A handful is normal.** A proposal always carries material the SVN template
  has no slide for — revision summaries, cost tables, closing notes.
- **A long list on a document whose chapters *should* map** means something
  upstream mangled the headings. Check that Step 0.0 really copied the file
  verbatim before blaming the parser: a rewritten heading, a `###` promoted to
  `##`, or one chapter split into several will each show up here.
