# UI craft rules — how screens must be built (MANDATORY)

The contract (`references/pt-spec-format.md`) says *what* to build with; this file says *how to make
it good*. Apply every rule when writing `src/screens/*.tsx` and `src/components/*`. The quality gate
(§9 of `review-checklist.md`) checks against these. Token vocabulary below maps to the shadcn vars:
`--c-primary`→`bg-primary`, `--c-text-sub`→`text-muted-foreground`, `--space`→`p-4` rhythm, `--fs-*`→text scale.

## 0. App-type idioms — decide `meta.appType` first, it changes the rules
- **mobile-app**（ネイティブ）: NO web header/footer — the OS chrome is the frame. Global navigation =
  bottom tab bar (3–5 tabs, a project component every tab-reachable screen composes); screen title lives
  in a slim nav bar; back = top-left `‹` (stack navigation); primary action may be a FAB or bottom
  action bar. Review shell shows the native frame (status bar + home indicator, no Desktop preview).
- **web-app**: a global header IS required (logo + nav + utilities, consistent on every screen), footer
  on content pages, hover states matter, denser layouts acceptable on desktop, breadcrumb/URL are part
  of wayfinding. Review shell shows browser chrome (URL bar / desktop window).
- **both**（Web＋アプリ両提供）: components branch with `useAppMode()` — e.g. the global header renders
  only in web; the bottom tab bar only in native; back = text link (web) vs floating circle on the photo
  (native). The review shell's Web⇄アプリ toggle previews both idioms from the same screens.
- Never mix idioms: a web header inside a mobile-app, or a tab bar on a web desktop layout, is a gate
  violation unless the design direction explicitly calls for it.

## 1. Visual hierarchy — one screen, one emphasis
- Exactly **one** visual peak per screen: the primary action or the answer the user came for.
  Everything else steps down (size → weight → color, in that order).
- Emphasis triad: size (`text-2xl` > `lg` > `base`), weight (800/700 > 400), color (`text-foreground` > `text-muted-foreground`).
  Never emphasize with all three at once on more than one element.
- Section micro-headers: `text-xs text-muted-foreground`, generous top margin — they separate, not shout.
- F-pattern: the most important info sits top-left (JP reading order); amounts/values may right-align.

## 2. Spacing — 8px rhythm, generous by default
- All paddings/margins/gaps are multiples of 4px, preferring 8/12/16/24/32. `p-4`(16px) is the base unit.
- Related items sit close (4–8px), groups separate clearly (16–24px), sections strongly (24–40px). Proximity IS grouping — prefer whitespace over divider lines.
- Cards: inner padding ≥ 16px (`p-4`); never let text touch a border.
- Content max-widths on wide canvases (forms ≤560px, reading ≤720px, dashboards ≤1080px), always centered.

## 3. Typography
- Body line-height 1.6–1.7; headings 1.3–1.4. Set it explicitly — default 1.15 ruins JP text.
- Amounts, counts, times: `font-variant-numeric: tabular-nums` and right-align in rows/tables.
- Max ~40 JP chars per line for reading text. Never justify. Never letter-space body JP text.
- No font size below 11px; body content ≥ 14px.

## 4. Color discipline
- `primary` = action & selected-state ONLY. If everything is primary, nothing is.
- Structure is carried by neutrals (`border`, `background` vs `card` contrast), not by colors.
- `success/warning/danger` are semantic only — never decorative — and always pair with a text label (色だけに頼らない).
- Large surfaces stay quiet: tint washes (accent) for emphasis areas, full-saturation only on small elements.

## 5. Affordance & feedback (the ui/ kit does half of this)
- `<Button>` ships hover (brightness), press (scale), `focus-visible` ring, keyboard operability, and
  44px+ height. **Use it for every action** instead of hand-rolling; clickable Cards get `cursor-pointer`
  + hover treatment via a shared pattern component.
- Make clickable things LOOK clickable before hover — buttons filled/outlined, clickable cards with
  border+shadow, links in primary. Never style a non-clickable element like a button.
- **Micro-interactions respond.** Selections, tabs, toggles, typeable inputs work via local state
  (contract §8) with visible selected/pressed styling (`aria-pressed`, accent fill) — reviewers judge
  the experience by touching it.
- Primary = `<Button>` (filled, 1画面1つ). Secondary = `variant="secondary"`. Destructive =
  `variant="destructive"` (outlined, never filled — friction is the point).

## 6. States are designed, not bolted on
- **loading**: `<Skeleton>` blocks in the real layout's shape — not a spinner line of text. Skeleton mirrors the default layout so nothing jumps.
- **empty**: 3 parts — what this place is / why it's empty (no blame) / one CTA to fill it.
- **error**: what happened + what to do next + a retry/back action. `destructive` on the label, not the whole screen.
- Toggling states must not shift shared elements (header stays put).

## 7. Touch & input ergonomics
- Interactive targets ≥44×44px, ≥8px apart. Full-width buttons on mobile bottoms; thumb-reachable.
- Screen-level primary actions live in a **bottom action bar** (`sticky bottom-0` + background wash) so
  they stay reachable while content scrolls — in review device frames it pins to the frame bottom.
- Forms: 1 column, labels above fields, required marks explicit, constraints shown BEFORE errors,
  input font ≥15px (avoids iOS zoom), one primary submit at the end.
- Back/cancel is always visible where the flow implies it (header ‹ or a secondary button).

## 8. Microcopy
- Buttons = verbs the persona uses (「申請を送信する」not「OK」). One idea per sentence.
- Grounded tone: use the persona's `vocabulary`; never blame the user; state the benefit at decision points.
- Numbers with units, dates with weekday (7/1（火）) — reduce interpretation cost.

## 9. Imagery & decoration
- lucide-react icons or inline SVG — simple geometric, token colors (`var(--primary)` etc. in SVG attrs). Emoji acceptable in toC tone, max 1 per view block.
- **Photos — default to real (photographic) imagery.** When imagery sells the experience (marketplaces,
  travel, food, profiles), show real photos, not illustrations. Always go through a single `Photo`
  component so the source is swappable in one place (catalog it in patterns.tsx). Pick the source by need:
  - **Embedded (DEFAULT — keeps the single-file / offline guarantee):** put images under `src/assets/`
    and `import` them, so Vite bundles them into `dist/index.html` (small ones inline as data URIs).
    Source the photos by either: AI-generating photorealistic images with the **comfyui MCP**
    (`generate_image` / `imagine`) from a prompt grounded in the content, or downloading suitable stock.
    Keep each image modest (long edge ~1000px, compressed) — every photo grows the single HTML, so use a
    handful of representative shots and reuse them across cards rather than one per row.
  - **External URLs (only when the user asks for lightweight output or many photos):** reference
    Unsplash / picsum.photos etc. This **waives the offline single-file guarantee** — the built HTML then
    needs internet, and URLs can rot / hit CSP. State this trade-off to the user when you take this path.
  - **Hand-drawn SVG scenes (fallback):** only when neither embedding nor external is available/appropriate
    (e.g. no image source and self-contained is mandatory). Gradients + flat shapes; scenes may use their
    own scenery palette (content, not UI — exempt from the token-only rule).
- **Grounding still applies to imagery:** the subject of a photo must trace to the content (a listing's
  region, a persona's context). Invented subjects are flagged assumptions like any other mock data.
- Decoration must never compete with data: washes, thin strokes, small marks. No gradients unless the design direction demands them.

## 10. Motion
- The shell animates screen entry (`pt-enter`, fade+rise 220ms) — don't add page-level animation in screens.
- If a fragment animates anything (e.g. progress ring), keep it subtle, <400ms or steady-state, and meaningful.

## Self-check before emitting a screen (fast pass)
1. Squint test: does exactly one thing pull the eye, and is it the primary action/answer?
2. Is every gap a 4px multiple, with clear group separation?
3. Do amounts use `.tabular`? (body line-height 1.65 is the global default)
4. Would you know what's clickable with hover disabled?
5. Are loading/empty/error each a *designed* layout, not a sentence?
6. Any color used for decoration that should be neutral? Any raw hex outside globals.css?
