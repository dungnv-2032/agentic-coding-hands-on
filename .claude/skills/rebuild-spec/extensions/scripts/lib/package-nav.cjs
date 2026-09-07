'use strict';

/**
 * package-nav.cjs — grouped sidebar for `--package` bundle pages (plan
 * `260826-1601-package-reading-layers-index-pager`, phase-04). Renders the
 * SAME reading model `lib/reading-spine.cjs` builds and
 * `lib/package-index-body.cjs` renders into the index — one spine drives
 * both views, so the sidebar can never disagree with the index about where
 * a page lives. This module classifies nothing: it only walks `model.layers`
 * / `model.trace` / `model.appendix` and prints `<details>` groups.
 *
 * Group labels come from the sidecar's own localized text: `layer.label`
 * (per layer, already numbered/titled) and `model.ui.appendix` /
 * `model.ui.drill_labels[*]` (phase-03b) — never a literal English string,
 * except the two fallback defaults used ONLY when `model.ui` is `null`
 * (i.e. no sidecar exists at all for this corpus/language, so there is no
 * locale to draw from — `reading-spine.cjs`'s own fallback path already
 * makes the same call for its `appendix` section).
 *
 * `<details>` auto-open: a group opens when it (recursively) contains
 * `currentRelHtml`. `class="active"` marks the current page's own link,
 * same as the pre-phase-04 flat nav did.
 */

const { escapeHtml } = require('./package-html-template.cjs');

const FALLBACK_APPENDIX_LABEL = 'Appendix — Repo Docs';

function navLink(page, currentRelHtml, prefix) {
  const cls = page.relHtml === currentRelHtml ? ' class="active"' : '';
  return `<li><a href="${prefix}${page.relHtml}"${cls}>${escapeHtml(page.title)}</a></li>`;
}

function drillLabel(model, key) {
  const labels = model.ui && model.ui.drill_labels;
  return (labels && labels[key]) || key;
}

/** One layer-4 drill (Flows / Features / Screens / Traceability's siblings):
 * a nested `<details>`, with a per-feature sub-group when `drill.groups` is
 * set (features are grouped by feature, not listed flat). */
function renderDrill(model, drill, currentRelHtml, prefix) {
  const items = drill.index ? [drill.index, ...drill.items] : drill.items;
  const containsCurrent = items.some((p) => p.relHtml === currentRelHtml);
  const label = drillLabel(model, drill.key);
  let body;
  if (drill.groups) {
    body = drill.groups
      .map((g) => {
        const gOpen = g.items.some((p) => p.relHtml === currentRelHtml) ? ' open' : '';
        const gItems = g.items.map((p) => navLink(p, currentRelHtml, prefix)).join('');
        return `<details${gOpen}><summary>${escapeHtml(g.key)}</summary><ul>${gItems}</ul></details>`;
      })
      .join('');
  } else {
    const indexLi = drill.index ? navLink(drill.index, currentRelHtml, prefix) : '';
    body = `<ul>${indexLi}${drill.items.map((p) => navLink(p, currentRelHtml, prefix)).join('')}</ul>`;
  }
  return `<details${containsCurrent ? ' open' : ''}><summary>${escapeHtml(label)} <b>${items.length}</b></summary>${body}</details>`;
}

/** The highest layer number carries the trace pointer in the nav, mirroring
 * `reading-spine.cjs`'s own `traceLayer` choice (layer 4, or the last layer
 * present) — trace lives outside `layer.entries`/`drills` on the model, so
 * this is the one place that has to re-attach it for display. */
function isTraceLayer(model, layer) {
  if (!model.trace || model.layers.length === 0) return false;
  const maxLayerNum = Math.max(...model.layers.map((l) => l.layer));
  return layer.layer === maxLayerNum;
}

function renderLayerGroup(model, layer, currentRelHtml, prefix) {
  const traceHere = isTraceLayer(model, layer) ? model.trace : null;
  const allPages = [
    ...layer.entries.map((e) => e.page),
    ...layer.drills.flatMap((d) => (d.index ? [d.index, ...d.items] : d.items)),
    ...(traceHere ? [traceHere] : []),
  ];
  if (allPages.length === 0) return '';
  const containsCurrent = allPages.some((p) => p.relHtml === currentRelHtml);
  const entryLis = layer.entries.map((e) => navLink(e.page, currentRelHtml, prefix)).join('');
  const drillHtml = layer.drills.map((d) => renderDrill(model, d, currentRelHtml, prefix)).join('');
  const traceHtml = traceHere ? `<ul>${navLink(traceHere, currentRelHtml, prefix)}</ul>` : '';
  const sub = drillHtml || traceHtml ? `<div class="pv-subnav">${drillHtml}${traceHtml}</div>` : '';
  return `<details${containsCurrent ? ' open' : ''}><summary>${escapeHtml(layer.label)} <b>${allPages.length}</b></summary><ul>${entryLis}</ul>${sub}</details>`;
}

function renderAppendixGroup(model, currentRelHtml, prefix) {
  if (model.appendix.length === 0) return '';
  const label = model.ui ? model.ui.appendix : FALLBACK_APPENDIX_LABEL;
  const containsCurrent = model.appendix.some((p) => p.relHtml === currentRelHtml);
  const items = model.appendix.map((p) => navLink(p, currentRelHtml, prefix)).join('');
  return `<details${containsCurrent ? ' open' : ''}><summary>${escapeHtml(label)} <b>${model.appendix.length}</b></summary><ul>${items}</ul></details>`;
}

/** Cross-page sidebar nav grouped by the reading-order model — replaces the
 * old flat `<ul>` (see `package-html-template.cjs` header). */
function renderNavList(model, currentRelHtml, prefix) {
  const homeCls = currentRelHtml === 'index.html' ? ' class="active"' : '';
  const startHereLi = model.startHere ? navLink(model.startHere, currentRelHtml, prefix) : '';
  const top = `<ul><li><a href="${prefix}index.html"${homeCls}>Overview</a></li>${startHereLi}</ul>`;
  const layerGroups = model.layers.map((l) => renderLayerGroup(model, l, currentRelHtml, prefix)).join('');
  const appendixGroup = renderAppendixGroup(model, currentRelHtml, prefix);
  return `${top}${layerGroups}${appendixGroup}`;
}

module.exports = { renderNavList };
