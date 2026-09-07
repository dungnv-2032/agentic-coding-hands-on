# IA Patterns Reference

## Organizing schemes (pick one or hybrid)
| Scheme | Organize by | Best for | Watch out for |
|---|---|---|---|
| Task-based | What users do | Apps, SaaS, tools | Tasks that span many objects |
| Audience-based | Who the user is | Multi-role products, portals | Users who belong to several groups |
| Topic / subject | Subject matter | Content sites, docs, help | Overlapping topics |
| Sequential | Steps in a process | Onboarding, checkout, wizards | Non-linear needs |
| Object/entity | Domain objects | CRUD admin, dashboards | Hiding the user's actual task |
| Hybrid | Mix of above | Most real products | Inconsistent logic between sections |

Default heuristic: **task-based for the primary nav, object-based inside a section.**

## Navigation models
- **Flat** — few top-level items, no deep nesting. Best ≤ ~7 destinations.
- **Hierarchical (tree)** — sections → subsections. Most common; keep ≤ 3 levels to any key screen.
- **Hub-and-spoke** — central home, return-to-hub between tasks. Good for mobile, distinct tasks.
- **Tabbed / sectioned** — parallel areas, persistent bottom/side nav. Good for apps with 3–5 modes.
- **Faceted / filter** — large catalogs; navigate by filtering attributes.
- **Sequential / wizard** — one path, back/next; for processes that must be ordered.

## Labeling rules
- Use the user's words, not internal/DB terms.
- Be specific over clever ("Billing" > "Money stuff"; "Reports" > "Insights" if it's literally reports).
- Keep labels parallel in grammar and length within a nav group.
- One concept = one label everywhere (no synonyms drifting across screens).

## Depth & breadth
- Target: any Must screen reachable in ≤ 3 clicks/taps.
- Prefer slightly broader-but-shallower over deep-but-narrow for findability.
- If a section has 1 child, it probably shouldn't be a section.

## Screen role vocabulary
Every screen is exactly one of: **inform · decide · input · compare · manage · confirm · recover · complete**.
If a screen claims two roles, consider splitting it.

## Required states to consider per screen
empty · loading · partial/skeleton · error · success/confirmation · permission-restricted · offline (if relevant).

## Common IA smells
- Navigation mirrors the org chart or database, not user tasks.
- A "Misc / Other" bucket exists (means grouping failed).
- Same content reachable under contradictory labels.
- Deep nesting (>3) to reach frequent tasks.
- Primary action buried below secondary content.
- No empty/error state planned for data-driven screens.
