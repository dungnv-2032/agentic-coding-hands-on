# User-model review checklist

Run after generating `um-spec.json`. Report each as pass / issue.

## Evidence & honesty
- [ ] Every non-obvious claim is either backed by research or listed in `meta.assumptions`.
- [ ] `meta.researchBasis` states what the model is built on (or says "仮説ベース").
- [ ] No guess is presented as a finding.

## Personas
- [ ] 1–2 `primary` personas only (not a crowd).
- [ ] At least one `anti` persona when scope could creep.
- [ ] Each persona has goals AND frustrations (not attribute-only).
- [ ] Each has a representative first-person `quote`.
- [ ] Personas are distinct people, not job titles or segments.

## Empathy maps
- [ ] Says (observable) is distinguished from Thinks (inferred).
- [ ] Pains and Gains are present and specific.
- [ ] Built for the primary persona(s).

## Journey
- [ ] Stages are in time order, ~4–7 of them.
- [ ] `emotionScore` set on every stage (curve is meaningful).
- [ ] Every emotional low (`< 0`) has at least one `opportunity`.
- [ ] Touchpoints are concrete (named channels/screens).

## Insights
- [ ] Each insight is a "why", not a restated observation.
- [ ] Each has `evidence` and an `impact` rating.
- [ ] Each has a How-Might-We that opens solution space.
- [ ] Insights connect to journey pains or empathy-map pains.

## Story map
- [ ] The backbone (`activities` → `tasks`) reads left→right as the user's flow (mirrors the journey).
- [ ] Each story has a `title` (the why via `soThat` where useful) and names a `persona`.
- [ ] `priority` set (Must/Should/Could); not everything is Must.
- [ ] Stories sliced into `releases`; the MVP band is a thin end-to-end walking skeleton (not one activity fully built).
- [ ] Stories trace back to insights / journey opportunities.

## Coverage & scope
- [ ] The model stays upstream (no screens/IA/visual design — those belong to uiux-design-information-architecture).
- [ ] Only the artifacts the user asked for are populated; unused sections omitted.
- [ ] `um-model.html` builds and opens without error.
