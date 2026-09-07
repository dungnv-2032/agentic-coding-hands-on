# SCR012_ErrorNotFound — Screen Spec

**Screen**: SCR012: ErrorNotFound
**Type**: atomic
**Route**: GET /404
**Generated**: 2026-06-04

## Purpose

Any user who requests a URL that does not exist (or whose resource has been deleted) sees this screen; it communicates that the page cannot be found and provides a link back to the marketplace front page.

### Layout Sketch

The page uses the `blank_layout` ERB layout which renders a minimal centered white card (`div.box`, max-width 620px, 90% width, centered with `margin: 10% auto`) on a light grey background (`#f6f7f7`). The card contains a heading and paragraph message followed by a back-to-front-page anchor link. No navigation bar, sidebar, or footer is present. The layout is the same for all error screens. (`app/views/layouts/blank_layout.erb:82` and `app/views/errors/status_404.haml:1`)

```
┌──────────────────────────────────────────────┐
│  (grey background #f6f7f7)                   │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ R1: Error Card (.box, max-w 620px)     │  │
│  │                                        │  │
│  │  H2: "Page not found!"                 │  │
│  │  P:  "The page you requested cannot    │  │
│  │       be found..."                     │  │
│  │  A:  "Back to the front page"          │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

## User Flow

### Happy Path

1. User (or browser) navigates to a non-existent URL; Rails routes to `GET /404` → `errors#not_found`.
2. Controller renders `status_404.haml` with HTTP 404 status and a page `<title>` composed of `{community_name} - page not found`.
3. Screen displays: heading "Page not found!", explanatory paragraph, and "Back to the front page" link pointing to `/`.
4. User clicks "Back to the front page" link — navigates to marketplace root.

### Branches

| Decision point | Condition | Outcome on this screen | Source |
|----------------|-----------|------------------------|--------|
| Format negotiation | Non-HTML format (e.g., JSON/XML request) | `render body: nil, status: 404` — no HTML rendered | `app/controllers/errors_controller.rb:14` |

## Data Inventory

| Display Label | Source | Format | Empty Behavior | Cross-ref |
|---------------|--------|--------|----------------|-----------|
| `<title>` in `<head>` | computed — `@current_community.name(locale) + " - page not found"` | string concat | Falls back to `"page not found"` if community not resolved | N/A (binding: ``title(404)``) |

## UI States

`N/A — no async ops`

Static server-rendered error page with no JavaScript async calls.

## Validation & Error Feedback

### A) Client-side

`N/A — no client-side form validation detected.`

### B) Server-side

`N/A — no submit-style action handlers detected.`

## Interaction Patterns

- **Clicking "Back to the front page" navigates to marketplace root (`/`)** — source: `app/views/errors/status_404.haml:8`

## Conditional Rendering

| Condition | Type | Renders | Hidden | Notes |
|-----------|------|---------|--------|-------|
| `@current_community.favicon.present?` | legacy | `<link rel="shortcut icon">` | favicon tag | Conditionally injects community favicon in `<head>` |
| `error_id.present?` | legacy | error ID paragraph | error ID text | Not applicable to 404 — `error_id` is only passed in 500 view; absent here |

---

*Developer appendix below — implementation detail (layout regions, component wiring, security guards, accessibility audit, source citations, code-reading order). BA/QA readers can stop here.*

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components | Responsive Behavior |
|-----------|------|----------|------------|----------------|---------------------|
| R1 | Error Card | static | no | `div.box`, `h2`, `p`, `a[href='/']` | `width: 90%`, `max-width: 620px`, centered — fluid on small screens |

## Security Surface

`N/A — no auth guards or permission checks detected on this screen.`

## Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | absent | No `aria-*` attributes or `role=` detected in view or layout |
| Keyboard navigation | unknown | Anchor link is natively keyboard-focusable; no custom key handlers |
| Focus management | unmanaged | No `autofocus` or focus-trap logic |
| Screen reader compatibility | partial | `<h2>` heading provides semantic structure; no `role="main"` landmark |

[NO_A11Y_DETECTED] — accessibility audit needed before production release.

## Source References

- View: `app/views/errors/status_404.haml:1–9`
- Layout: `app/views/layouts/blank_layout.erb:1–87`
- Controller: `app/controllers/errors_controller.rb:13–16`
- Routes: `config/routes.rb:101`
- i18n: `config/locales/en.yml:929–937`

## Source Walkthrough

1. **File:** `config/routes.rb:101` -- entry route; `GET /404` maps to `errors#not_found`.
2. **File:** `app/controllers/errors_controller.rb:1-6` -- class shell; `layout 'blank_layout'` plus two before_actions (`current_community`, `set_locale`) shared by every action on this controller -- read this once, it explains the shared shell of every error screen in this batch (SCR012-SCR016).
3. **File:** `app/controllers/errors_controller.rb:13-18` -- `def not_found`; `format.html` renders the `status_404` template with 404 status, `format.all` (non-HTML Accept) renders an empty body -- this branch is why SCR014 (406) reuses this same view instead of failing.
4. **File:** `app/controllers/errors_controller.rb:41-51` -- `title(status)`; builds the page `<title>` text, tolerating a missing or unresolvable community name.
5. **File:** `app/views/errors/status_404.haml:1-9` -- the actual markup: heading, paragraph, back-link; the whole visible screen is these 9 lines.
6. **File:** `app/views/layouts/blank_layout.erb:1-86` -- wraps the view in the shared `.box` card (line 82); read this last since it is identical across every error screen in this batch.

```
GET /404
  -> routes.rb:101
     -> ErrorsController#not_found (errors_controller.rb:13)
        -> format.html renders status_404.haml (view, :1-9)
           -> wrapped in blank_layout.erb (:82, .box card)
```

See this screen's own `## Source References` table above for the citation set this walkthrough draws from.
