# Authoring the cover and agenda sections

Reference for **Step A** of `SKILL.md` — how to fill the `cover` and `agenda`
keys when authoring a profile from the Clio KG.

> On the supplied-document path (Step 0.0) these are read straight out of the
> user's own document — its addressee line and its AGENDA block — so nothing
> here needs deciding. One thing still needs CHECKING: if gen-slide's last line
> warns that the cover is unfilled, the document's notation wasn't understood —
> pass `--cover-company` / `--cover-date` rather than editing the document.

`cover` is `{company, date}` and fills two of the cover slide's text boxes (markdown: `## Cover` with `### Company` / `### Date`). Either field omitted keeps the template's own placeholder wording, so a profile with no `cover` renders exactly as before.

- **`company` is the client's company name — NOT a product or proposal title.** It fills the cover's large headline. Never put a proposal title such as `ROOV compass 住戸検索 開発` here: the box holds one line and longer text wraps over the date below it.
- **Copy the name verbatim from the source document's addressee line, in whatever language that document is written in.** Strip only the honorific or the field label (`御中`, `Kính gửi Quý công ty`, `Prepared for:`). Do not translate it, romanize it, abbreviate it, or normalize it to match another language edition of the same proposal:

  | Source document | Addressee line | `company` |
  |---|---|---|
  | `proposal-….md` (JP) | `### 株式会社スタイルポート 御中` | `株式会社スタイルポート` |
  | `proposal-….vi.md` (VI) | `### Kính gửi Quý công ty Styleport` | `Styleport` |
  | `proposal-….en.md` (EN) | `**Prepared for**: Evering` | `Evering` |

  Each notation is anchored to a line edge, so none can match the middle of a
  sentence: the JP honorific must END the line, the VI/EN label must START it
  and carry a colon. The English labels read are `Prepared for`, `Addressed to`,
  `Addressee`, `Client`, `To`, `For` — `Prepared by` is deliberately not among
  them, or the vendor's own line would land on the client's cover.
- `date` is read from the same front matter, in `YYYY.MM.DD`, `YYYY/MM/DD`, `YYYY-MM-DD` or `YYYY年M月D日`. A document stating both an original and a revision date gives the cover the later one.
- The smaller `○○株式会社　御中` line above the headline is **never filled from the profile** — do not add a `client` field. On a Japanese proposal it stays exactly as the template wrote it. On a proposal in any other language the renderer **removes it**: `御中` is a Japanese honorific and `○○` is the "put the name here" mark, so the line was shipping a literal blank above the client's real name. Nothing replaces it — an English cover has no such line.
- The boxes are never resized or repositioned. A company name always fits, but gen-slide still prints `Cover: WARNING ...` if a value is too long — treat that as a failure and shorten it, do not ship the deck.

**When neither field can be read**, gen-slide says so twice — once from the
parser and once as the very last line it prints:

```
[gen-slide] WARNING: slide 1 still shows the TEMPLATE PLACEHOLDER — cover
company and date was never filled. Re-run with --cover-company "..." ...
```

Treat that as a failure, never as noise. It means the deck opens on
`SVN Proposal Menu` / `2025.04.04`. On the supplied-document path the fix is
**never** to edit the user's proposal — pass the values on the command line:

```bash
--cover-company "Evering" --cover-date 2026-04-19
```

Both flags override whatever the document said (a value typed by hand is a
correction), and `--cover-date` accepts any notation listed above.

`agenda` is `{chapters[], cost_breakdown[]}` and fills the agenda slide's two boxes (markdown: `## Agenda` with `### Chapters` / `### Cost Breakdown`).

- **Copy the source document's own AGENDA block, line for line, in its order.** That block is the proposal's real table of contents; the template's own agenda lines are Vietnamese notes to the proposal writer, never deck content. Keep the source's chapter wording even where it differs from the template's (`システム導入のメリット`, not the template's `システムの導入のメリット`).
- Each item is one line, `<JP chapter label> — <English gloss>`, exactly as the source writes it (en dash and hyphen are accepted too). The label renders bold black and the gloss grey; an item with no dash renders as a label-only line.
- `cost_breakdown` is the small box under the list — the 費用 sub-items (`開発費用`, `インフラコスト`). Take them from the cost chapter's own subheadings. It holds **2 lines and cannot grow** — the footer is directly below it.
- **Supply `cost_breakdown` only if the source document actually lists those sub-items.** When `agenda` has chapters but no `cost_breakdown`, the renderer *empties* that box rather than falling back to the template's own `開発費用 / インフラコスト`. That is deliberate: the source's agenda is the whole truth about this slide, and the template's two lines happen to fit one proposal but not the next. An agenda of nine chapters and nothing else renders as exactly nine lines.
- Omit `agenda` entirely — both lists — only when the source has no agenda at all. Only then does the renderer keep the template's chapter labels and gloss them to English from `AGENDA_GLOSSES` in `svn.py`. That is a fallback for older profiles, not the intended path.
- The list box fits 9 lines comfortably. gen-slide prints `Agenda: WARNING ...` when a line is too long for its box or when there are more lines than the box holds — treat either as a failure (a 10th chapter line collides with the sub-item box), and shorten the glosses or drop the surplus rather than shipping the deck.

