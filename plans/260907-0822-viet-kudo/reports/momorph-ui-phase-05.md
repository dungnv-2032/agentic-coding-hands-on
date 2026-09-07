# Phase 05 — Board surface: doc renderer + anonymous chip

**Mode:** section · **Test policy:** e2e-red-first (regression-protection variant — see below)

## Files changed

- `app/kudos/_components/kudos-message-body.tsx` (new, 133 lines) — `'plain'`/`'doc'` renderer,
  owns the `kudos-body` `<p>`.
- `app/kudos/_components/anonymous-sender-chip.tsx` (new, 39 lines) — sender-slot chip for
  anonymous kudos, echoes `sunner-chip.tsx`'s measured shell.
- `app/kudos/_components/kudos-card.tsx` (edit, 183 → 191 lines) — two conditional branches
  (sender slot, message body) + import block + one header-comment sentence. No other line moved.

## MoMorph calls

None this session — the task instructed reuse of the card's already-measured F004 classes
(`sunner-chip.tsx`, `kudos-card.tsx:145-160`) rather than re-querying MoMorph, and the doc-render
styling (quote/list treatment) has no Figma node at all (rich text is a data model with no
Figma-authored surface — `compose-contract.ts` header cites "technical-spec.md § 4.2", not a frame).
Every class in the diff is either a verbatim copy (cited `mm:` ids preserved) or explicitly
undecorated new markup, documented as such in-file.

## Design evidence

- `sunner-chip.tsx` (read, full file) — source of every class in `anonymous-sender-chip.tsx`.
- `kudos-card.tsx:145-163` (pre-edit, read via Read tool) — source of the verbatim-moved `<p>`
  in `kudos-message-body.tsx`.
- `lib/kudos/rich-text.ts`, `lib/kudos/compose-contract.ts` — frozen parser/type contract, used
  as-is, not reimplemented.
- `lib/kudos/view-model.ts`, `lib/kudos/board-data.ts` — confirmed `messageFormat` /
  `anonymousSenderLabel` plumbing and the server-side redaction already in place.

## Compile/typecheck

`npm run typecheck` — exit 0, no errors.

## Lint

`npm run lint` — exit 0, 0 errors, 28 pre-existing warnings (all in unrelated `e2e/*.spec.ts`
files outside owned scope; none in the three files touched).

## Asset coverage

`grep -rn "dangerouslySetInnerHTML" app/` — only one match, inside a code comment in
`kudos-message-body.tsx` describing the constraint; zero actual usages.

## F004 regression gate (primary gate)

`npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts --reporter=list`
— **27 passed, 0 failed**, run twice (once immediately after the code edit, once again after the
hand-verification DB activity below), both green. Port 3000 checked clear before each run.

## Hand evidence (no automated coverage exists for these paths)

Inserted 4 probe rows via `docker exec supabase_db_my-app psql`, started `next dev`, drove the
bundled Chromium (`LD_LIBRARY_PATH=.playwright-libs/...`) against `/kudos`, and inspected the real
DOM (`innerHTML`/`innerText`), not just visuals:

1. **`'doc'` with every mark kind** — `plans/260907-0822-viet-kudo/evidence/phase-05-doc-render.png`.
   DOM confirmed real `<strong>`, `<em>`, `<s>`, `<a href="https://example.com" target="_blank"
   rel="noopener noreferrer">`, ordered-list ordinals `1. ` / `2. ` (grouped, restart after the
   quote), and a bold `@`-mention span — all inside the single `kudos-body` `<p>`.
2. **Anonymous, named** — `phase-05-anonymous-named.png`. Sender slot shows "Nguoi bi mat" (test
   value), 0 `kudos-sender` elements in the card, 1 `kudos-receiver` (receiver untouched, badge
   intact).
3. **Anonymous, no name given** — `phase-05-anonymous-unnamed.png`. Sender slot shows the neutral
   fallback "Ẩn danh", 0 `kudos-sender` elements.
4. **Malformed `'doc'` payload (`message = "not json at all"`)** —
   `phase-05-malformed-doc-degrades.png`. Renders the literal string as plain text; `page.reload()`
   collected zero `pageerror` events — no crash.

All four probe rows deleted after capture (`delete from kudos where id in (59,60,61,62)`). During
cleanup this delete returned `DELETE 0` — the rows were already gone by the time I ran it (most
likely a concurrent process in this shared local Supabase instance; `kudos_id_seq.last_value` is
62, confirming the inserts did happen and were later removed by something other than my delete).
Verified end state directly: `count(*) = 57`, `min(id)=1`, `max(id)=57`, and spot-checked the first
3 original seed rows are unmodified (`message_format='plain'`, `is_anonymous=false`). Corpus is back
to exactly the 57 seeded rows either way. Reran the F004 suite once more after this to confirm
nothing regressed — still 27/27.

## RED evidence

`not-applicable in the RED-then-implement sense`. Per this task's own contract, the redEvidence
supplied was the **already-GREEN F004 suite** (`redExitCode: 0`, `redFailure: "not-applicable —
job is to keep it green"`) — this phase is a regression-protection edit to shipped code, not new
behavior with a red assertion to satisfy. The two new render paths have zero authored automated
coverage in the 57 test cases (recorded in `test-contract.md` § Accepted limitations and phase-05
spec § Key Insights #7), which is why § Hand evidence above exists as the actual proof.

## GREEN handoff

`tester`: rerun `npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts
--reporter=list` for independent confirmation (currently 27/27 here). No new test files were
authored or touched by this phase.

## Concerns/blockers

- The anonymous-card and doc-render paths have zero automated E2E coverage (by design, per the
  ratified contract) — only the hand evidence above backs them. A follow-up test case is worth
  writing once `p9vFVBE_tc` gets an authored spec (clarifications.md § Unresolved question 4).
- Unexplained: 4 probe rows vanished between capture and my own cleanup delete in this shared local
  Supabase instance, consistent with concurrent Track B/tester activity against the same DB rather
  than anything this phase did. End state was verified correct (57/57, seed rows intact) regardless.

**Status:** DONE
**Summary:** Added `kudos-message-body.tsx` (plain/doc renderer, zero `dangerouslySetInnerHTML`, element-based rendering with a re-validated link scheme) and `anonymous-sender-chip.tsx` (echoes `sunner-chip.tsx`'s shell, no `kudos-sender` testid), wired both into `kudos-card.tsx` via two minimal conditional branches (191 lines, under the 200-line cap). F004's 27-test board suite stayed green across two runs; the two new render paths were hand-verified via real DOM inspection and screenshots for doc-with-every-mark, anonymous-named, anonymous-unnamed, and malformed-doc-degrades-safely, then the scratch DB rows were cleaned up back to the exact 57-row baseline.
**Concerns/Blockers:** None blocking. See report § Concerns/blockers for the two informational notes (no automated coverage for the two new paths by design; unexplained but harmless probe-row removal by what appears to be concurrent DB activity in this shared local environment).
