'use strict';

/**
 * package-pager.cjs — prev/next pager for `--package` bundle pages (plan
 * `260826-1601-package-reading-layers-index-pager`, phase-05). Renders the
 * SAME `model.spine` the index (`lib/package-index-body.cjs`) and sidebar
 * (`lib/package-nav.cjs`) already read from `lib/reading-spine.cjs` — there
 * is no second ordering to diverge from (plan's own Risk Assessment).
 *
 * `renderPager(model, currentRelHtml, prefix)` is called once per rendered
 * page (380 times on the real corpus). Rebuilding the `relHtml -> position`
 * lookup from `model.spine` on every call would be an O(n) scan per page,
 * O(n^2) across the bundle. `build_client_package.cjs` builds `model` once
 * and passes the SAME object/array to every render call, so the map is
 * memoized in a module-level `WeakMap` keyed by `model.spine` — built once,
 * reused for the rest of the bundle — without adding a 4th parameter to the
 * required call signature.
 *
 * No sidecar (`model.ui` absent or `model.spine` empty): returns `''` — no
 * pager at all. Never invents an alphabetical spine (plan.md "Fallback").
 *
 * `index.html` is never itself a spine entry (the spine only orders real
 * `docs/**\/*.md` pages) — it gets a single forward cell pointing at
 * `spine[0]`, not the full 3-cell layout (phase-05 Requirements).
 *
 * Every interpolated title/section is `escapeHtml`'d — titles originate
 * from page `<title>`/frontmatter (phase-05 Security Considerations).
 */

const { escapeHtml } = require('./package-html-template.cjs');

const _positionCache = new WeakMap();

/** `relHtml -> index-in-spine`, built once per distinct `spine` array and
 * cached by reference — the O(n^2) guard the plan's Architecture note asks for. */
function getPositionMap(spine) {
  let map = _positionCache.get(spine);
  if (!map) {
    map = new Map();
    spine.forEach((entry, i) => map.set(entry.page.relHtml, i));
    _positionCache.set(spine, map);
  }
  return map;
}

function cell(cls, k, t, s, href) {
  const tHtml = t !== null ? `<span class="pv-pg-t">${escapeHtml(t)}</span>` : '';
  const sHtml = s !== null ? `<span class="pv-pg-s">${escapeHtml(s)}</span>` : '';
  return `<a class="${cls}" href="${href}"><span class="pv-pg-k">${escapeHtml(k)}</span>${tHtml}${sHtml}</a>`;
}

/** No prev (first spine page) -> a home-styled cell pointing at `index.html`. */
function prevCell(prevEntry, ui, prefix) {
  if (!prevEntry) {
    return cell('pv-pg pv-pg-prev pv-pg-home', ui.prev, ui.back_to_index, null, `${prefix}index.html`);
  }
  return cell('pv-pg pv-pg-prev', ui.prev, prevEntry.page.title, prevEntry.section, `${prefix}${prevEntry.page.relHtml}`);
}

/** No next (last spine page) -> a home-styled cell pointing at `index.html`,
 * labelled with `ui.pager.end_of_spine` (phase-05 hard constraint). */
function nextCell(nextEntry, ui, prefix) {
  if (!nextEntry) {
    return cell('pv-pg pv-pg-next pv-pg-home', ui.next, ui.end_of_spine, null, `${prefix}index.html`);
  }
  return cell('pv-pg pv-pg-next', ui.next, nextEntry.page.title, nextEntry.section, `${prefix}${nextEntry.page.relHtml}`);
}

/** Middle cell: always present, always links to `index.html` (plan.md). */
function midCell(current, pos, total, ui, prefix) {
  const s = `${pos + 1} / ${total} · ${ui.back_to_index}`;
  return cell('pv-pg-up', ui.reading, current.section, s, `${prefix}index.html`);
}

/** `index.html`'s own pager: two empty grid placeholders (keeps the 3-column
 * layout) plus a single forward cell pointing at `spine[0]`. */
function renderIndexPagerCell(model, prefix) {
  if (!model.ui || !model.spine.length) return '';
  // Defensive: an unusable locale renders NO pager rather than throwing. A throw
  // here aborts the whole bundle build (renderPager runs once per page in
  // build_client_package.cjs's main loop), contradicting the "never throws"
  // fallback contract. loadSidecar() now shape-checks `ui` too — belt and braces.
  if (!model.ui.pager) return '';
  const ui = model.ui.pager;
  const first = model.spine[0];
  const forward = cell('pv-pg pv-pg-next', ui.next, first.page.title, first.section, `${prefix}${first.page.relHtml}`);
  return `<nav class="pv-pager" aria-label="${escapeHtml(ui.reading)}"><span></span><span></span>${forward}</nav>`;
}

/**
 * `renderPager(model, currentRelHtml, prefix)` — the 3-cell pager for any
 * page ON the spine. `currentRelHtml === 'index.html'` routes to the
 * single-forward-cell layout instead (index.html is never itself a spine
 * entry). No sidecar, or a page absent from the spine (defensive — every
 * claimed page is always on it when a sidecar is present) -> `''`, so the
 * caller never has to branch on which path ran.
 */
function renderPager(model, currentRelHtml, prefix) {
  if (!model.ui || !model.spine || model.spine.length === 0) return '';
  if (currentRelHtml === 'index.html') return renderIndexPagerCell(model, prefix);
  const posMap = getPositionMap(model.spine);
  const pos = posMap.get(currentRelHtml);
  if (pos === undefined) return '';
  // Defensive: an unusable locale renders NO pager rather than throwing. A throw
  // here aborts the whole bundle build (renderPager runs once per page in
  // build_client_package.cjs's main loop), contradicting the "never throws"
  // fallback contract. loadSidecar() now shape-checks `ui` too — belt and braces.
  if (!model.ui.pager) return '';
  const ui = model.ui.pager;
  const total = model.spine.length;
  const current = model.spine[pos];
  const prevEntry = pos > 0 ? model.spine[pos - 1] : null;
  const nextEntry = pos < total - 1 ? model.spine[pos + 1] : null;
  return (
    `<nav class="pv-pager" aria-label="${escapeHtml(ui.reading)}">` +
    prevCell(prevEntry, ui, prefix) +
    midCell(current, pos, total, ui, prefix) +
    nextCell(nextEntry, ui, prefix) +
    `</nav>`
  );
}

module.exports = { renderPager };
