# Phase 05 — Board surface: doc renderer + anonymous chip

**Track:** A (presentational UI) · **Owner:** `momorph-ui-implementer` · **Depends:** 04 ·
**Effort:** 1.5h · **test_policy:** `e2e-red-first`

## MoMorph refs:
- Sun* Kudos - Live board (the card being changed): https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/MaZUn5xHXZ
- Viết Kudo (the screen that produces this content): https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/ihQ26W78P2
- Clarifications: plans/260907-0822-viet-kudo/clarifications.md
- testPolicy: e2e-red-first

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (`parseKudosDoc`) · [phase-04](phase-04-board-contract-and-read-mapping.md) (the two new fields)
- [clarifications.md](clarifications.md) § Rich text (never `dangerouslySetInnerHTML`), assumption **A3**
- [technical-spec.md](spec/viet-kudo/technical-spec.md) § 4.2 DISC-001
- Files to extend: `app/kudos/_components/kudos-card.tsx:145-160` (the `kudos-body` block) and `:119` (the sender chip), `app/kudos/_components/sunner-chip.tsx` (read only — the shell being echoed)
- F004 assertions this must not move: `e2e/kudos-live-board.spec.ts` K-9 (`kudos-sender` href `/profile`, `sunner-badge`, `kudos-campaign`), K-24 (every heart disabled for anon)

## Overview

**Priority:** P1 · **Status:** completed.

Two new small components and a two-branch edit to the shipped card. This is a change to
already-delivered F004 code, so the bar is: the 57 seeded rows must render **byte-identically**, and
the new branches must only ever be reached by rows this commission creates.

## Key Insights

1. **`data-testid="kudos-body"` stays exactly where it is.** F004's `kudosBody` locator is bound to
   that element. `KudosMessageBody` therefore *renders that `<p>` itself*, including its className and
   `line-clamp`, and the card swaps one element for one component — the testid never moves and the
   clamp behavior per variant is preserved.
2. **The renderer emits elements, never HTML.** `paragraph → <span className="block">`,
   `ordered-list-item → <span className="block list-decimal …">` prefixed by its ordinal,
   `quote → <span className="block border-l-2 …">`; runs become `<strong>`, `<em>`, `<s>`,
   `<a href>`, `<span>` for a mention. There is no `dangerouslySetInnerHTML` in this phase and there
   must never be one. **All blocks render inside the single `<p data-testid="kudos-body">`**, so they
   must be inline-level elements with `block` display rather than real `<div>`/`<ol>`/`<blockquote>` —
   a `<div>` inside a `<p>` is invalid HTML and the browser would reparent it, breaking the clamp and
   possibly the testid's text content.
3. **`href` is re-validated at render.** `parseKudosDoc` already allow-lists the scheme; the renderer
   checks it again and renders a plain `<span>` instead of an `<a>` if it fails. Two layers, per
   BR-004's own defense-in-depth reasoning — this content reaches anonymous visitors.
4. **A parse failure degrades to plain text, and that is a feature.** `parseKudosDoc` returning
   `null` means render `message` as a plain string, which is exactly what a `'plain'` row does. No
   error boundary, no empty card, no crash on the public board.
5. **The anonymous chip has no design source.** Frame `p9vFVBE_tc` ("Ẩn danh") carries zero authored
   spec items (`design-source-analysis.md § 10`). So `AnonymousSenderChip` reuses `sunner-chip.tsx`'s
   own measured shell — same wrapper widths, same `min-[1360px]:max-w-[235px]`, same avatar box, same
   name typography — with the department, the badge and the `/profile` link **omitted** rather than
   faked. Every borrowed value carries the `mm:` node id it came from, cited from `sunner-chip.tsx`.
6. **`kudos-sender` must NOT be rendered for an anonymous card.** F004's K-9 reads
   `card.getByTestId("kudos-sender")` on `.first()`, which is a highlight card (top-5 by hearts) and
   therefore never anonymous — verified, since a freshly composed kudos has 0 hearts. Emitting a
   `kudos-sender` link on an anonymous chip would make the label look like a profile link to a person
   who chose not to be named. Omit it; the anonymous name is a plain `<span>`.
7. **No test covers an anonymous card.** ID-41–44 only toggle the checkbox; ID-46/47 submits
   non-anonymous. The anonymous path must therefore be proven by hand (step 5) — this is the one
   surface in the whole commission with no automated proof, and saying so is part of the job.
8. **`kudos-card.tsx` is at 183 lines.** The delta must be two component swaps and one import block —
   roughly +6/−8 lines. If it crosses 200, the fix is to move the long header comment's card-fix
   history into a sibling note, never to split the component.

## Requirements

**Functional:** DISC-001 rendering, A3 (anonymous label in place of the sender chip, receiver always
shown), FR-402's read half.

**Non-functional:** files ≤200 lines; both new components are server components (no `"use client"` —
the card is reached through phase 07's client boundary in F004 and needs none of its own); arbitrary
Tailwind values carry `mm:{nodeId}`; zero `dangerouslySetInnerHTML`; no new dependency.

## Architecture

```
app/kudos/_components/kudos-message-body.tsx        (new, ~90 lines)
  KudosMessageBody({ message, format, clamp })
    format !== "doc"        → <p data-testid="kudos-body" className={…clamp}>{message}</p>
    parseKudosDoc(message)  → null ? same plain render
                            : <p data-testid="kudos-body" className={…clamp}>{blocks.map(renderBlock)}</p>
    renderRun: text → <span|strong|em|s> · link → scheme-checked <a target="_blank" rel="noopener noreferrer">
               mention → <span className="font-bold">@{label}</span>

app/kudos/_components/anonymous-sender-chip.tsx     (new, ~55 lines)
  AnonymousSenderChip({ label })
    echoes sunner-chip.tsx's wrapper + avatar box; renders `label` as a plain <span>;
    NO department, NO badge, NO /profile link, NO kudos-sender testid

app/kudos/_components/kudos-card.tsx                (edit, 2 branches)
  :119   {card.anonymousSenderLabel !== null
            ? <AnonymousSenderChip label={card.anonymousSenderLabel} />
            : <SunnerChip sunner={card.sender} role="sender" />}
  :148   <KudosMessageBody message={card.message} format={card.messageFormat}
                           clamp={BODY_CLAMP[variant]} />
```

**Data flow:** `kudos.message` (text) → `board-data` (untouched string) → `KudosCardView.message` +
`.messageFormat` → `KudosMessageBody` → `parseKudosDoc` → React elements. The string is never
interpolated into markup and never leaves the type system as HTML.

## Related Code Files

**Create:** `app/kudos/_components/kudos-message-body.tsx` · `app/kudos/_components/anonymous-sender-chip.tsx`
**Modify:** `app/kudos/_components/kudos-card.tsx` (two branches + imports only)
**Delete:** none
**Read only:** `app/kudos/_components/sunner-chip.tsx`, `lib/kudos/compose-contract.ts`,
`lib/kudos/rich-text.ts`, `lib/kudos/view-model.ts`

## Implementation Steps

1. Write `kudos-message-body.tsx`. Start from the exact `<p>` currently at `kudos-card.tsx:148-155`
   — same `data-testid`, same `text-justify text-xl leading-8 font-bold text-[#00101A]`, same
   `${clamp}` — so the plain path is a pure move.
2. Add the doc path: `parseKudosDoc(message)`, then map blocks. Ordered-list items render their
   1-based index followed by `. ` as text (no `<ol>` inside a `<p>`); a quote gets a left border and
   italic. Keep each block's wrapper a `<span className="block …">`.
3. Add `renderRun` with the scheme re-check. `mailto:` links keep no `target`; `http(s)` links get
   `target="_blank" rel="noopener noreferrer"`.
4. Write `anonymous-sender-chip.tsx` by copying `sunner-chip.tsx`'s wrapper and avatar classes
   verbatim, each with the `mm:` citation it carries there, then deleting the department row, the
   badge and the `Link`. Use the committed `/images/kudos/sample-avatar.png` through `next/image` at
   the same 64×64.
5. Edit `kudos-card.tsx` — the two branches in § Architecture and nothing else. Append one sentence
   to its header comment recording that the sender slot is now conditional and why (A3).
6. `npm run typecheck && npm run lint`. Confirm `kudos-card.tsx` is still ≤200 lines.
7. Prove both paths by hand, because no test covers them. Insert three probe rows with `psql` — one
   `'doc'` with every mark kind, one anonymous with a name, one anonymous with `anonymous_name` null
   — load `/kudos`, and confirm: bold/italic/strike/quote/list/link/mention all render as elements
   (check via devtools that the DOM contains `<strong>`/`<a>`, not escaped text); the two anonymous
   cards show the name and `Ẩn danh` respectively, with the receiver's real name intact and no
   `kudos-sender` element inside them. Then insert a fourth probe whose `message` is `'doc'` but holds
   `not json at all` and confirm the card renders that string as plain text without crashing. Delete
   all four probes.
8. `npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts
   --reporter=list` — must be green. This is the regression gate for the whole phase.

## Todo List

- [x] `kudos-message-body.tsx` owns the `kudos-body` `<p>`; plain path is a verbatim move
- [x] Doc path renders blocks as `<span className="block">`, never `<div>`/`<ol>` inside the `<p>`
- [x] `renderRun` re-checks the link scheme and degrades to `<span>` on failure
- [x] `anonymous-sender-chip.tsx` echoes the measured shell, omits department/badge/link/testid
- [x] `kudos-card.tsx` changed in exactly two places; header comment updated; ≤200 lines
- [x] Zero `dangerouslySetInnerHTML` anywhere in the diff
- [x] Step 7 manual proof for all four probe rows, probes deleted
- [x] Step 8 both board suites green
- [x] `npm run typecheck && npm run lint` clean

## Success Criteria

- Every seeded (`'plain'`, non-anonymous) card renders identically to before — same DOM shape, same
  testids, same clamp.
- A `'doc'` row's bold text is a real `<strong>` in the DOM and its link a real `<a>` with an
  allow-listed scheme.
- A `'doc'` row whose `message` is not valid JSON renders as plain text and the page does not error.
- An anonymous card shows the label, shows the receiver, and contains no `kudos-sender` element.
- `grep -rn "dangerouslySetInnerHTML" app/` returns nothing.
- Both board suites exit 0.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| A block element inside `<p data-testid="kudos-body">` gets reparented by the browser, moving the testid's text and breaking F004's `kudos-body` assertions | **High** × High | All blocks are `<span className="block">`; step 7 inspects the real DOM, not the JSX |
| The plain path is retyped instead of moved and drifts from the shipped markup | Med × High | Step 1 requires a verbatim move of the existing `<p>`, className included |
| An `<a>` renders an unsafe scheme because the parser was bypassed by a hand-built object | Low × **High** | Scheme checked again at render; success criteria greps the DOM |
| The anonymous chip invents visual values with no design source | Med × Med | Every class is copied from `sunner-chip.tsx` with its `mm:` citation; omissions are omissions, not inventions. Recorded as an unresolved design question |
| `kudos-card.tsx` crosses 200 lines | Med × Low | Delta is ~±8 lines; if it crosses, the card-fix history moves out, the component never splits |
| The anonymous path ships unverified because no test covers it | **High** × Med | Step 7 is a mandatory manual proof with four probe rows; the gap is stated in § Next Steps for the record |
| Mention labels are stale relative to a renamed sunner | Low × Low | By design (clarifications § Rich text): the stored `label` is printed, never re-resolved |

**Rollback:** revert `kudos-card.tsx` and delete the two new files. The board returns to phase 04's
state, where a `'doc'` row shows raw JSON — acceptable, because no `'doc'` row exists until phase 07
lands.

## Security Considerations

- This is the XSS boundary for the public board. Content reaches `anon` visitors, and it is rendered
  only as typed React elements — the string never becomes markup.
- Link schemes are allow-listed twice (parser, renderer). `javascript:`, `data:` and `vbscript:`
  cannot survive either.
- External links carry `rel="noopener noreferrer"` so a target page cannot reach back through
  `window.opener`.
- The anonymous chip renders no `/profile` link and no department, so nothing about the hidden author
  is inferable from the DOM.
- Mention labels are printed as text, never used to build an href or a lookup.

## Next Steps

Phase 12's integration run is the final gate. For the record: **the anonymous card has no automated
coverage** — worth a follow-up test case once design authors frame `p9vFVBE_tc`.
