# Phase 11 — Compose form assembly

**Track:** A (presentational UI) · **Owner:** `momorph-ui-implementer` · **Depends:** 08, 09, 10 ·
**Effort:** 2.5h · **test_policy:** `e2e-red-first`

## MoMorph refs:
- Viết Kudo: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/ihQ26W78P2
- Lỗi chưa điền đủ thông tin (companion, no authored spec): https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/5c7PkAibyD
- Clarifications: plans/260907-0822-viet-kudo/clarifications.md
- testPolicy: e2e-red-first

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (`composeReducer`, `isSubmitReady`, `buildPayload`) · [phase-02](phase-02-red-gate-defect-repair.md) — **the `data-submit-ready` ruling is an input to this phase** · [08](phase-08-form-primitives-recipient-title-anonymous.md) · [09](phase-09-body-editor-toolbar-mentions-link.md) · [10](phase-10-hashtag-and-image-pickers.md)
- [test-contract.md](test-contract.md) § Landmarks and copy, § Submit state
- Tests this phase must satisfy: ID-0, ID-2, ID-3, ID-7, ID-11, ID-14, ID-45, ID-46/47, ID-48, ID-49, ID-50, ID-51, ID-52, ID-56, the `Community Standards link` and `Cancel and Submit buttons` cases
- [design-source-analysis.md](reports/design-source-analysis.md) § 1 (title, Hủy, Gửi node ids), § 7 (item `H`: Hủy discards with no confirm; Gửi validates → loading → closes), § 8 (modal 752×1012, padding 40, gap 32, radius 24, `#FFF8E1`; title Montserrat 700/32/40 centred `#00101A`; Hủy padding 16/40 radius 4; Gửi 502×60 radius 8 `#FFEA9E`)
- [write-path study](reports/write-path-conventions.md) § 1 (`useActionState` shape, `forms.md:190-274`)
- Next 16.3.4 docs read for this phase: `01-app/02-guides/forms.md:190-274`

## Overview

**Priority:** P1 · **Status:** completed.

The dialog card, the field order, the footer actions, and the one place that holds the aggregate
state and dispatches the submit. Everything it renders already exists; everything it computes
already lives in `compose-state.ts`. It is glue by design, so it stays under the line cap.

## Key Insights

1. **`compose-submit` is never `disabled` and never `aria-disabled`.** Phase 02 established why:
   Playwright resolves both through the same predicate that gates `click()`, so a disabled button
   makes ID-7/11/14/50/51/52/56 unclickable and ID-56 impossible. The button carries
   `data-submit-ready={isSubmitReady(state) ? "true" : "false"}` — which is DEC-002, observable and
   asserted — plus the inactive styling keyed off the same value. **Do not add `disabled` back**,
   however much the design's item `H` prose invites it.
2. **Validation runs client-side on submit, and the server runs it again.** Clicking submit with a
   field empty must light up all four `field-error-*` slots at once (ID-56) *without navigating*
   (`expect(page.url()).toContain("/kudos/new")`). So: `onSubmit` → `validateCompose(buildPayload(
   state))` → if any error, `dispatch(setErrors)` and stop. The action is only dispatched on a clean
   payload — and it validates again anyway, because it is POST-reachable directly.
3. **Pending uploads are awaited before dispatch.** ID-46/47 clicks submit immediately after
   `setInputFiles`. Any image whose `url` is still `null` is an unresolved upload; the submit handler
   waits until every image resolves (or fails) before building the payload. Submitting without them
   would pass the test and silently drop the user's file.
4. **`useActionState`, with the payload as the dispatch argument.** `const [state, submit, pending] =
   useActionState(createKudos, initialState)`, and `<form data-testid="compose-form" action={() =>
   void submit(payload)}>`. Passing the typed `ComposePayload` object keeps the whole boundary typed
   and avoids a hidden JSON input. Progressive enhancement is not a requirement here — clarifications
   settled a Client Component, and the screen is unusable without JS regardless.
5. **`pending` is the loading state** (ID-46/47's "show loading"), and it also guards against a
   double submit: while `pending`, the submit handler returns early.
6. **Server errors come back as codes and are mapped to copy here.** `state.errors` holds
   `ComposeFieldErrors`; this component maps each code through `copy.errors` and hands the string
   down to the relevant field. Merge them with the client-side errors into one object so a field
   never shows two messages.
7. **Field order is asserted by geometry.** ID-3 reads `boundingBox().y` for recipient → title → body
   → hashtags → images → anonymous. A CSS `order-*` or a flex-reverse that changes paint order
   without changing DOM order would still pass, but a mismatch between DOM and paint order is exactly
   the trap F004's phase 09 had to unwind. Keep DOM order == paint order.
8. **`Hủy` is a plain `<a href="/kudos">`.** No confirmation (§ 7, ID-45), no `router.back()` — a
   back navigation would land wherever the user came from, and ID-45 asserts the URL is `/kudos` and
   not `/kudos/new`. A real anchor is also the most reliable thing for Playwright's click to follow.
9. **The page's only `<h1>` is the dialog title.** ID-0 uses `getByRole("heading", { level: 1 })` in
   strict mode and asserts exact text. `HomeHeader` and `SiteFooter` render no `h1` (verified —
   `/kudos` relies on the same fact for its hero). Render exactly one, with the title copy.
10. **The `community-standards-link` href is a fixed literal.** `/standards` exists in the app. The
    label is `Tiêu chuẩn cộng đồng`, which — recorded in phase 06 — has no design source and comes
    from the test contract.
11. **The dialog is page-level markup, not an intercepting route.** Clarifications settled this:
    a normal page at `/kudos/new`, with the centred `#FFF8E1` card over the dimmed page background.
    No `@modal` slot, no `default.js`.

## Requirements

**Functional:** FR-102 (the page renders), FR-201–FR-207 composed, FR-402 (submit), FR-403 (both
Hủy and Gửi), DEC-001, DEC-002, ID-3's field order, ID-56's all-at-once errors.

**Non-functional:** `compose-form.tsx` ≤200 lines — the reducer, `isSubmitReady` and `buildPayload`
all live in `compose-state.ts` precisely so this file can be markup plus a submit handler;
`"use client"`; `mm:{nodeId}` on arbitrary Tailwind values; copy through props only.

## Architecture

```
app/kudos/new/_components/compose-form.tsx        (~170 lines, "use client")
  props: ComposeFormProps { options: ComposeOptionsView, copy: Dictionary["kudosCompose"],
                            createKudos: CreateKudos, uploadImage: UploadKudosImage }
  const [state, dispatch] = useReducer(composeReducer, initialComposeState);
  const [actionState, submit, pending] = useActionState(createKudos, { errors: {} });
  const errors = mergeErrors(state.errors, actionState.errors);   // client + server, one message each

  <form data-testid="compose-form" action={handleSubmit}>
    <h1>{copy.title}</h1>                                    mm:I520:11647;520:9870
    <RecipientPicker … error={errors.recipient && copy.errors[errors.recipient]} />
    <TitleField      … error={errors.title     && copy.errors[errors.title]} />
    <KudosBodyEditor … error={errors.body      && copy.errors[errors.body]} />
    <HashtagPicker   … fieldError={errors.hashtag && copy.errors[errors.hashtag]} />
    <ImagePicker     … uploadImage={uploadImage} />
    <AnonymousToggle … />
    <ComposeActions  submitReady={isSubmitReady(state)} pending={pending} copy={copy} />
  </form>

  handleSubmit:
    if (pending) return;
    await settlePendingUploads(state.images);          // insight 3
    const payload = buildPayload(state);
    const fieldErrors = validateCompose(payload);
    if (hasAny(fieldErrors)) { dispatch({ type: "setErrors", errors: fieldErrors }); return; }
    submit(payload);                                   // action redirects on success

app/kudos/new/_components/compose-actions.tsx     (~60 lines)
  <a    data-testid="compose-cancel" href="/kudos">{copy.buttons.cancel}</a>   mm:…;520:9906
  <button data-testid="compose-submit" type="submit"
          data-submit-ready={submitReady ? "true" : "false"}                   mm:…;520:9907
          className={submitReady ? gold : inactive}>{copy.buttons.submit}</button>
  <a    data-testid="community-standards-link" href="/standards">{copy.communityStandards}</a>
```

**Data flow:** `page.tsx` (phase 12) → `options` + `copy` + the two actions as props → this component
holds all state → children render and report back → submit → `createKudos` → `redirect("/kudos")` →
the board shows the new card.

## Related Code Files

**Create:** `app/kudos/new/_components/compose-form.tsx` · `app/kudos/new/_components/compose-actions.tsx`
**Modify:** none · **Delete:** none
**Read only:** all four of phase 08's components, all four of phase 09's, both of phase 10's,
`lib/kudos/compose-state.ts`, `lib/kudos/compose-contract.ts`, `lib/kudos/validate-compose.ts`

## Implementation Steps

1. Confirm phase 02's `data-submit-ready` amendment is ratified before writing `compose-actions.tsx`.
   If it is not, stop and report — this is the one hook in the commission whose name was not settled
   before the RED run.
2. `compose-actions.tsx` first (it is small and it is the contested surface).
3. `compose-form.tsx` — `useReducer` + `useActionState`, then the children in the asserted DOM order,
   then `handleSubmit` in the exact order of § Architecture.
4. `mergeErrors` — a five-line local helper; client errors win over server errors for the same field,
   because the client's are the ones the user just triggered.
5. The dialog chrome: centred card, `#FFF8E1`, 24px radius, 40px padding, 32px gap, over the dimmed
   page background, inside the standard `HomeHeader`/`SiteFooter` chrome that phase 12 supplies.
   Re-measure via MCP rather than trusting the report's 1006px toolbar figure.
6. `npm run typecheck && npm run lint`. Confirm `compose-form.tsx` ≤200 lines.
7. **First real render.** Temporarily point `app/kudos/new/page.tsx` at this component in a *local,
   uncommitted* edit to see it in a browser — then revert it, because that file belongs to phase 12.
   Alternatively hand phase 12 the go-ahead and let it do the wiring; do not commit an edit to a file
   this phase does not own.
8. Once phase 12 has wired the page, run the narrow slice for this phase's tests:
   `npx playwright test e2e/viet-kudo.spec.ts --reporter=list --workers=1 --grep "ID-0|ID-2|ID-3|ID-45|ID-48|ID-49|ID-56|Community Standards|Cancel and Submit"`.
   Roughly nine tests, minutes rather than the full 30.

## Todo List

- [x] `data-submit-ready` amendment confirmed ratified before coding the submit button
- [x] `compose-submit` carries no `disabled` and no `aria-disabled`, ever
- [x] Exactly one `<h1>`, exact title text
- [x] DOM order == paint order == ID-3's asserted order
- [x] `handleSubmit`: pending guard → await uploads → build → validate → dispatch errors or submit
- [x] All four field errors appear together on an empty submit, and the URL does not change (ID-56)
- [x] `pending` drives the loading state and blocks a double submit
- [x] `mergeErrors` gives each field exactly one message
- [x] `compose-cancel` is `<a href="/kudos">`, no confirmation dialog
- [x] `community-standards-link` → `/standards`, label from copy
- [x] `compose-form.tsx` ≤200 lines, no reducer or validation logic inlined
- [x] `npm run typecheck && npm run lint` clean
- [x] Step 8 narrow slice green (after phase 12 wires the page)

## Success Criteria

- `grep -n "disabled" app/kudos/new/_components/compose-actions.tsx` returns nothing.
- `grep -c "useReducer\|useActionState" app/kudos/new/_components/compose-form.tsx` returns 2.
- `grep -rn "composeReducer\|isSubmitReady\|buildPayload\|validateCompose" app/kudos/new/_components/compose-form.tsx`
  shows only calls, never definitions.
- Exactly one `<h1>` on the rendered page; `getByRole("heading", { level: 1 })` is unambiguous.
- An empty submit shows four error messages and leaves the URL at `/kudos/new`.
- A complete submit navigates to `/kudos` and the new card is on the board.
- `compose-form.tsx` ≤200 lines.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| `disabled` added to the submit button "to honour DEC-002", breaking seven tests at once | **High** × **High** | Insight 1, the todo list, and a grep in the success criteria; phase 02 carries the full reasoning |
| Submit fires before uploads resolve, silently dropping attachments while the test still passes | Med × **High** | `settlePendingUploads` awaited first; images carry `url: null` until resolved (phase 10) |
| Client validation navigates anyway, failing ID-56's URL assertion | Med × High | `handleSubmit` returns before `submit()` when any error exists; `action={handleSubmit}` never falls through to a native submit because the form has no method/action attributes |
| A second `<h1>` sneaks in via the card heading, making ID-0's strict locator ambiguous | Med × High | One `<h1>`, asserted in the success criteria |
| `compose-form.tsx` crosses 200 lines | Med × Med | All logic already extracted to `compose-state.ts`; if it still crosses, the dialog chrome moves to a `compose-card.tsx` — a new file this phase owns, never a split of the state |
| Server and client errors both render, showing a field two messages | Med × Low | `mergeErrors`, with client precedence |
| A toolbar button submits the form | Med × High | Phase 09 sets `type="button"` on all six; re-verified here by clicking each one in step 7's browser pass |
| Editing `page.tsx` in this phase creates an ownership collision with phase 12 | Med × Med | Step 7 explicitly requires reverting the local edit; phase 12 owns the wiring |

**Rollback:** delete the two files. `page.tsx` still renders `ComingSoon` until phase 12, so the app
is unaffected.

## Security Considerations

- Client-side validation is UX only. The action re-validates everything (phase 07) because Server
  Functions are POST-reachable directly (`forms.md:9-10`).
- The payload carries a receiver **id** and hashtag **ids**, never names, and no sender field —
  `ComposePayload` has no place for one by design.
- `compose-cancel` and `community-standards-link` are fixed literal hrefs, never built from state.
- `pending` blocks a double submit client-side; the database's `on conflict do nothing` provision and
  the single transaction are what actually make a double submit safe.
- No `dangerouslySetInnerHTML`; every error string comes from the dictionary, keyed by a code.

## Next Steps

Phase 12 wires `page.tsx`, adds the guard, and runs the full gate. Report the ratification status of
`data-submit-ready` in the completion message either way — 12's gate depends on ID-48 matching what
was built.
