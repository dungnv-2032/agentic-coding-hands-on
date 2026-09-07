'use strict';

/**
 * package-index-body.cjs — `index.html` body for `--package` bundles: a
 * Start Here block, a traceability callout, the reading model's numbered
 * layers with their layer-4 drill-downs, and a collapsed Appendix. Replaces
 * the old FR-7 4-bucket index (`classifyBucket`/`BUCKET_ORDER`/
 * `BUCKET_LABELS`, deleted from `package-html-template.cjs`) that dropped
 * 64% of pages into a trailing "Other" section — this module classifies
 * nothing itself, it only renders the model `lib/reading-spine.cjs` already
 * built (plan `260826-1601-package-reading-layers-index-pager`, phase-04).
 *
 * Prose covered by the sidecar's `ui` block (Start Here heading, Appendix
 * heading, drill labels — phase-03b's derived key set) is read from
 * `model.ui`, never hard-coded. `quickPath`/`roles` (the fast-read path and
 * the per-role paths) live on the raw sidecar rather than the model — the
 * model intentionally carries only what claims/orders pages — so the caller
 * threads them through separately; both are plain numeric `nums` arrays
 * with an already-localized `label`, rendered as-is, no page resolution
 * needed. Everything else here (lead paragraph, per-file-role labels inside
 * a feature group, the trace pointer sentence) sits outside phase-03b's
 * `ui` key set and stays plain descriptive chrome, same as before this
 * phase.
 */

const { escapeHtml } = require('./package-html-template.cjs');

const FALLBACK_START_HERE_LABEL = 'Start Here';
const FALLBACK_APPENDIX_LABEL = 'Appendix — Repo Docs';

const FEATURE_FILE_LABEL = {
  'README.md': 'Reading Guide',
  'functional-spec.md': 'Functional Spec',
  'technical-spec.md': 'Technical Spec',
  'test-cases.md': 'Test Cases',
};

function fileLabel(relMd) {
  const base = relMd.split('/').pop();
  return FEATURE_FILE_LABEL[base] || base;
}

/** The layer-3 `generated/screen-list.md` numbered entry, if claimed — the
 * screens drill's gate line. Looked up through the model's own claimed
 * entries (never a raw filesystem read), so it silently disappears rather
 * than dangling if that entry is ever absent from the corpus. */
function findClaimedPage(model, relMd) {
  for (const layer of model.layers) {
    for (const e of layer.entries) if (e.page.relMd === relMd) return e.page;
  }
  return null;
}

function renderStartHere(model, quickPath, roles) {
  const heading = model.ui ? model.ui.start_here : FALLBACK_START_HERE_LABEL;
  const quickLine = quickPath
    ? `<p class="pv-quick">${escapeHtml(quickPath.label)}: <b>${escapeHtml(quickPath.nums.join(' → '))}</b></p>`
    : '';
  const roleItems = (roles || [])
    .map((r) => `<li><b>${escapeHtml(r.label)}</b><span>${escapeHtml(r.nums.join(' → '))}</span></li>`)
    .join('');
  const fullGuide = model.startHere
    ? `<p class="pv-full">Full step-by-step reading guide: <a href="${model.startHere.relHtml}">${escapeHtml(
        model.startHere.title
      )}</a> — or use <b>Next</b> at the end of any page to walk all ${model.spine.length} pages in this order.</p>`
    : '';
  return `<section class="pv-start"><h2>${escapeHtml(heading)}</h2>${quickLine}${
    roleItems ? `<ul class="pv-roles">${roleItems}</ul>` : ''
  }${fullGuide}</section>`;
}

function renderTraceCallout(model) {
  if (!model.trace) return '';
  return `<p class="pv-trace"><b>End-to-end trace:</b> <a href="${model.trace.relHtml}">${escapeHtml(
    model.trace.title
  )}</a> — one row per feature, threading its screens, routes, rules, and tests together.</p>`;
}

function renderDrill(model, drill) {
  const labels = model.ui && model.ui.drill_labels;
  const label = (labels && labels[drill.key]) || drill.key;
  let gate = '';
  if (drill.key === 'screens') {
    const sl = findClaimedPage(model, 'generated/screen-list.md');
    if (sl) {
      gate = `<p class="pv-gate">Gate: <a href="${sl.relHtml}">${escapeHtml(sl.title)}</a> — read the inventory before opening individual screens.</p>`;
    }
  } else if (drill.key === 'features' && drill.index) {
    gate = `<p class="pv-gate">Gate: <a href="${drill.index.relHtml}">${escapeHtml(drill.index.title)}</a> — full feature index.</p>`;
  }
  const body = drill.groups
    ? `<div class="pv-featgrid">${drill.groups
        .map(
          (g) =>
            `<details class="pv-feat"><summary>${escapeHtml(g.key)}</summary><ul>${g.items
              .map((p) => `<li><a href="${p.relHtml}">${escapeHtml(fileLabel(p.relMd))}</a></li>`)
              .join('')}</ul></details>`
        )
        .join('')}</div>`
    : `<ul class="pv-cols">${drill.items.map((p) => `<li><a href="${p.relHtml}">${escapeHtml(p.title)}</a></li>`).join('')}</ul>`;
  return `<details><summary>${escapeHtml(label)} <b>${drill.items.length}</b></summary>${gate}${body}</details>`;
}

function renderAppendix(model) {
  const heading = model.ui ? model.ui.appendix : FALLBACK_APPENDIX_LABEL;
  const rows = model.appendix.map((p) => `<li><a href="${p.relHtml}">${escapeHtml(p.title)}</a></li>`).join('');
  return `<section class="pv-layer pv-appendix"><h2><span class="pv-lnum">A</span>${escapeHtml(
    heading
  )}</h2><details><summary>Repo documentation <b>${model.appendix.length}</b></summary><ul class="pv-cols">${rows}</ul></details></section>`;
}

/** `{model, quickPath, roles, projectName, pageCount}` -> index.html body. */
function renderIndexBody({ model, quickPath, roles, projectName, pageCount }) {
  const layers = model.layers.map((layer) => {
    const rows = layer.entries.length
      ? `<ol class="pv-numbered">${layer.entries
          .map(
            (e) =>
              `<li value="${e.num}"><a href="${e.page.relHtml}">${escapeHtml(
                e.page.title
              )}</a><span class="pv-what">${escapeHtml(e.what)}</span></li>`
          )
          .join('')}</ol>`
      : '';
    const drills = layer.drills.length
      ? `<div class="pv-drill">${layer.drills.map((d) => renderDrill(model, d)).join('')}</div>`
      : '';
    return `<section class="pv-layer"><h2><span class="pv-lnum">${layer.layer}</span>${escapeHtml(
      layer.label
    )}</h2><p class="pv-intro">${escapeHtml(layer.intro)}</p>${rows}${drills}</section>`;
  });

  return [
    `<h1>${escapeHtml(projectName)} — Client Package</h1>`,
    `<p>${pageCount} document(s), generated offline-readable from the promoted docs/ corpus. Linear reading order: <b>${model.spine.length} page(s)</b>.</p>`,
    renderStartHere(model, quickPath, roles),
    renderTraceCallout(model),
    ...layers,
    renderAppendix(model),
  ]
    .filter(Boolean)
    .join('\n');
}

module.exports = { renderIndexBody };
