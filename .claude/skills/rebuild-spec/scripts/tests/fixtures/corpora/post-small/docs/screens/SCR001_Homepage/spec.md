# SCR001_Homepage — Screen Spec

**Screen**: SCR001_Homepage
**Type**: composite
**Route**: GET / (also GET /:locale/)
**Generated**: 2026-06-04

## Purpose

Visitors and members browse, filter, and paginate marketplace listings via a search-plus-map interface; the screen also conditionally displays a sign-in/sign-up prompt when the community is private and no user is logged in.

### Layout Sketch

The homepage renders inside the `application.haml` layout. When `searchpage_v1` feature flag is active, it uses the `react_page.haml` layout and mounts a full-page `SearchPageApp` React component. In the legacy path (flag off), the page shows a cover photo hero (when `@big_cover_photo` is true) containing the search bar, followed by a toolbar with view-type toggles and filter dropdowns, a two-column main area (sidebar categories R3 + listing grid/list/map R4), and infinite-scroll pagination. The `TopbarApp` React component is injected at the top by the shared layout. Responsive breakpoints use CSS class `.visible-tablet` and `.hidden-tablet` to toggle sidebar/filter visibility (`app/views/homepage/index.haml`).

```
┌────────────────────────────────────────────────────┐
│  R1: TopbarApp (fixed-top, via application.haml)   │
├────────────────────────────────────────────────────┤
│  R2: Hero / Cover Photo (static, conditional)      │
│  [ search bar or sign-up CTA ]                     │
├────────────────────────────────────────────────────┤
│  R3: Home Toolbar (static, view-type + filters)    │
├──────────────┬─────────────────────────────────────┤
│ R4: Sidebar  │ R5: Listing Results (scrollable)    │
│ (categories  │  [grid | list | map]                │
│  + filters)  │  + pagination                       │
│ visible-tab  │                                     │
- - - - - - - -│- - - - - - - - - - - - - - - - - - -│
│ R6: SignIn   │  (conditional: private + no user)   │
│ Banner       │                                     │
└──────────────┴─────────────────────────────────────┘
```

*(When `searchpage_v1` flag is on, only R1-equivalent Topbar + full-page SearchPageApp region render; R2–R6 are replaced by the React SPA.)*

## User Flow

### Happy Path

1. User lands on `/`; server resolves community from subdomain; if `searchpage_v1` flag is active, renders `SearchPageApp` React SPA with bootstrapped listing data.
2. In legacy path: cover hero displays with search bar (keyword or location mode); user types search query and submits the `#homepage-filters` form (`GET /`).
3. Results reload; listing cards appear in R5 (grid/list/map depending on `@view_type`).
4. User can switch view type by clicking toolbar buttons in R3, which reloads `GET /?view={grid|list|map}`.
5. User scrolls down; `pageless` infinite scroll fires `GET /more_listings` (AJAX) and appends more cards to R5.
6. User clicks a listing card → navigates to SCR061_ListingDetail.

### Branches

| Decision point | Condition | Outcome on this screen | Source |
|----------------|-----------|------------------------|--------|
| Step 1 | `no_current_user_in_private_clp_enabled_marketplace?` (CLP enabled + private + no user) | Redirect to `landing_page_path` — user never sees homepage | `app/controllers/homepage_controller.rb:14` |
| Step 2 | `@current_community.private? && @big_cover_photo` | R6 private banner renders in place of listing results | `app/views/homepage/index.haml:53–58` |
| Step 2 | `@big_cover_photo` false | No cover photo hero; compact search form shown above listing area | `app/views/homepage/index.haml:40–45` |
| Step 3 | `search_result.on_error` | Flash error message "search engine not responding" + empty listing state | `app/controllers/homepage_controller.rb:136–141` |
| Step 5 | `@listings.total_entries == 0` | `.home-no-listings` block renders; message differs by whether search params are present | `app/views/homepage/index.haml:163–168` |
| Step 5 | `searchpage_v1` flag on + search error | `NoResults` React component rendered inside SearchPageApp | `client/app/components/sections/SearchPage/SearchPage.js:67–69` |
| Step 3 | `@view_type == "map"` | `_map` partial renders in R5 instead of cards | `app/views/homepage/index.haml:145–147` |
| Any | `params[:category]` or `params[:transaction_type]` present | Filtered results shown; category/shape toggle reflects active selection | `app/controllers/homepage_controller.rb:21–54` |

## Data Inventory

| Display Label | Source | Format | Empty Behavior | Cross-ref |
|---------------|--------|--------|----------------|-----------|
| listing card title | API field (Sphinx search result via `ListingIndexService`) | raw string | hidden (no card rendered) | N/A (binding: ``listing.title``) |
| price on card | API field | [UNVERIFIED] currency format — needs runtime confirmation | hidden | N/A (binding: ``listing.price``) |
| listing thumbnail | API field | image URL | placeholder image | N/A (binding: ``listing.listing_images``) |
| author name on card | API field (includes: author) | raw string | hidden | N/A (binding: ``listing.author.username``) |
| marketplace slogan in hero | store state (`@current_community`) | raw HTML (`community_slogan.html_safe`) | `hidden_title_part` CSS class | N/A (binding: ``@current_community.show_slogan?``) |
| marketplace description in hero | store state | raw HTML | `.hidden-title-part` CSS class | N/A (binding: ``@current_community.show_description?``) |
| category label in sidebar/toolbar | computed (Rails.cache fetch per community+locale) | raw string | N/A (only populated when `@show_categories`) | N/A (binding: ``@category_display_names[category.id]``) |
| selected listing type label | computed (from `all_shapes`) | i18n key translated | "All listing types" fallback | N/A (binding: ``selected_shape[:name_tr_key]``) |
| `<link rel="prev/next">` | computed (SEO pagination) | URL | omitted from `<head>` | N/A (binding: ``seo_pagination_links[:prev/:next]``) |
| pagination controls | computed (will_paginate) | integer | hidden (no pagination when 1 page) | N/A (binding: ``@listings.total_pages` / `@listings.current_page``) |

## UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| loading (legacy) | AJAX `GET /more_listings` in-flight | `.home-loading-more` spinner shown by `pageless` JS | none | `app/views/homepage/index.haml:159–162` |
| empty (no results) | `@listings.total_entries == 0` | `.home-no-listings` block with i18n text; CTA link to `new_listing_path` when no filters active | Post listing CTA | `app/views/homepage/index.haml:163–168` |
| empty (React path) | `listings.size == 0` in SearchPageApp | `NoResults` component: sad icon + "Sorry" + "Try other search terms" | none | `client/app/components/sections/SearchPage/SearchPage.js:67–69` |
| error (search engine) | `search_result.on_error` | Flash error banner "search engine not responding" | Retry via new search | `app/controllers/homepage_controller.rb:136–140` |
| private banner | `@current_community.private? && @big_cover_photo && !@current_user` | Private community content block or i18n message replacing listing grid | Sign-up CTA | `app/views/homepage/index.haml:53–58` |
| map view | `@view_type == "map"` | `_map` partial renders full-width map with listing pins | Pan/zoom map, click pins | `app/views/homepage/index.haml:145–147` |

## Validation & Error Feedback

### A) Client-side

`N/A — no client-side form validation detected.`

### B) Server-side

#### Search listings (GET form submit)
- **Endpoint:** `GET /`
- **Request:** `q, lc, ls, boundingbox, distance_max, category, transaction_type, price_min, price_max, view, page, custom_field params`
- **Success:** `200` → listing cards rendered in R5
- **Errors:** Sphinx engine error → `500` + flash `t("homepage.errors.search_engine_not_responding")` banner; empty listing state rendered
- **Trigger:** Form submit (`#homepage-filters`), toolbar link click, pagination link
- **Source:** `app/controllers/homepage_controller.rb:80–142`

#### Load more listings (AJAX)
- **Endpoint:** `GET /more_listings` (same controller, `request.xhr?` branch)
- **Request:** same search params as above
- **Success:** `200` → partial HTML (grid_item / list_item) appended via `pageless` JS
- **Errors:** `500` → empty body response; pageless may halt loading
- **Trigger:** Scroll to bottom of listing list
- **Source:** `app/controllers/homepage_controller.rb:100–113`

## Interaction Patterns

- **Clicking a view-type button (grid/list/map) in R3 re-submits search with `view` param** — source: `app/views/homepage/index.haml:72`
- **Scrolling to the bottom of R5 auto-loads the next page of listings (infinite scroll via `pageless`)** — source: `app/views/homepage/index.haml:161–162`
- **Expanding a category in R4 sidebar reveals subcategory links** — source: `app/views/homepage/index.haml:130–138`
- **Clicking the filter toggle button (#home-toolbar-show-filters) shows/hides the filter panel on mobile** — source: `app/views/homepage/index.haml:65–67` (JS toggle via `data-toggle`)
- **Selecting a listing shape or category from toolbar dropdowns re-submits the search form** — source: `app/views/homepage/index.haml:92–115`

## Conditional Rendering

| Condition | Type | Renders | Hidden | Notes |
|-----------|------|---------|--------|-------|
| `FeatureFlagHelper.feature_enabled?(:searchpage_v1)` | feature-flag | `SearchPageApp` React SPA via `react_page.haml` layout | legacy HAML listing grid + toolbar | Consequence: entire legacy homepage HAML replaced by React app |
| `FeatureFlagHelper.feature_enabled?(:topbar_v1)` | feature-flag | `TopbarApp` React component | legacy `_global_header` partial | Controls which navigation bar renders |
| `@big_cover_photo` | computed (auth + CLP flag) | cover hero with search bar | compact search bar | `@big_cover_photo = !(@current_user \|\| CLP enabled)` — `app/controllers/homepage_controller.rb:31` |
| `@current_community.private? && @big_cover_photo && !@current_user` | auth | private community banner (R6) | listing results | Consequence if bypassed: listing data exposure |
| `listing_shape_menu_enabled` (`all_shapes.size > 1`) | hardcoded-id | listing-shape dropdown in toolbar | toolbar button | [NEEDS_DOMAIN_CONFIRMATION] — hides shape selector when only 1 shape exists; appears to be intentional UX design |
| `@show_categories` (`@categories.size > 1`) | hardcoded-id | category sidebar (R4) + category dropdown | category UI | [NEEDS_DOMAIN_CONFIRMATION] — hides categories when community has only 1; appears intentional |
| `@view_type == "map"` | responsive/computed | `_map` partial | grid/list partials | Controlled by `?view=map` param |
| `location_search_in_use` | computed | `_location_bar` partial | `_search_bar` partial | Controlled by `search_mode` community setting |

---

*Developer appendix below — implementation detail (layout regions, component wiring, security guards, accessibility audit, source citations, code-reading order). BA/QA readers can stop here.*

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components | Responsive Behavior |
|-----------|------|----------|------------|----------------|---------------------|
| R1 | TopbarApp | fixed-top (via layout) | no | TopbarApp (React) | always visible; `react_component("TopbarApp", ...)` |
| R2 | Hero / Cover Photo | static | no | `_search_bar`, `_location_bar` partials | `@big_cover_photo` controls visibility; conditionally hidden |
| R3 | Home Toolbar | static | no | `.home-toolbar` with view-type buttons, listing-shape toggle, category toggle | `.home-toolbar-filters-mobile-hidden` hides on mobile |
| R4 | Category Sidebar | static | no | `.col-3.visible-tablet` with category links + `#desktop-filters` | `visible-tablet` (tablet+); hidden on mobile |
| R5 | Listing Results | scrollable | yes | `_grid_item`, `_list_item`, `_list_item_with_distance`, `_map` partials; `ListingCardPanel`, `ListingCard` (React path) | fluid width `.col-9` when sidebar present, `.col-12` otherwise |
| R6 | SignIn Banner | static | no | community private-content block or i18n text | conditional: only when `@current_community.private? && @big_cover_photo` |

## Security Surface

| Guard | Type | Consequence if bypassed |
|-------|------|------------------------|
| `before_action :ensure_user_belongs_to_community` (ApplicationController) | auth | Non-members of the community redirected away |
| `no_current_user_in_private_clp_enabled_marketplace?` redirect (homepage#index line 14) | auth | Anonymous users redirected to landing page; bypassing would expose private community search/listings |
| `@current_community.private? && @big_cover_photo` content gate | auth | Private community listings visible to unauthenticated users — data exposure |

## Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | absent | No `aria-label`, `role=` attributes detected in `index.haml` or layout partials scanned |
| Keyboard navigation | not implemented | No explicit `tabindex` or `keydown` handlers in view layer; form submit via Enter key works natively |
| Focus management | unmanaged | No `autofocus` or focus-trap detected |
| Screen reader compatibility | unknown | No semantic landmarks (`role="main"`) in view; `<article class="page-content">` provides mild structure via `application.haml:62` |

[NO_A11Y_DETECTED] — accessibility audit needed before production release.

## Source References

- Controller: `app/controllers/homepage_controller.rb:1–392`
- View (legacy): `app/views/homepage/index.haml:1–169`
- View (React path): `app/views/search_page/search_page.erb:1`
- Layout (legacy): `app/views/layouts/application.haml:1–130`
- Layout (React path): `app/views/layouts/react_page.haml:1–142`
- React app entry: `client/app/startup/SearchPageApp.js:1–124`
- React main component: `client/app/components/sections/SearchPage/SearchPage.js:1–116`
- React container: `client/app/components/sections/SearchPage/SearchPageContainer.js:1–45`
- Empty state: `client/app/components/composites/NoResults/NoResults.js:1–30`
- Partials (read for context): `app/views/homepage/_search_bar.haml`, `app/views/homepage/_grid_item.haml`, `app/views/layouts/_left_hand_navigation.haml`
- Helper: `app/helpers/application_helper.rb:303–331`
