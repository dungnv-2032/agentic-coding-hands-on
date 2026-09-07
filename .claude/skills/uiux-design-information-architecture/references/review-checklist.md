# IA Review Checklist

Run before finalizing. Report each as pass / issue (with severity).

## Findability & structure
- [ ] Grouping follows a single, statable scheme (not the DB/org chart).
- [ ] No "Misc/Other" catch-all bucket.
- [ ] Any Must screen is reachable in ≤ 3 levels.
- [ ] Labels use the user's language; one concept = one label everywhere.

## Screens
- [ ] Every screen has exactly one role (inform/decide/input/compare/manage/confirm/recover/complete).
- [ ] Screen list separates Must / Should / Could.
- [ ] Each screen's primary action is identified and tied to a user goal.

## Navigation
- [ ] Global nav has ≤ ~7 top-level entries (or a justified reason).
- [ ] User always knows where they are and how to get back.
- [ ] Navigation model named (flat/hierarchical/hub/tabbed/faceted/wizard).

## Flow & states
- [ ] Happy path mapped end to end.
- [ ] Key branches + recovery path covered.
- [ ] Empty / loading / error / success states planned for data-driven screens.
- [ ] Drop-off risks noted.

## Scope & clarity
- [ ] MVP vs. later explicitly separated.
- [ ] Assumptions listed in a 前提・仮定 section.
- [ ] Output is concrete enough to act on (no vague UX jargon).
- [ ] Did NOT drift into visual/component styling.
