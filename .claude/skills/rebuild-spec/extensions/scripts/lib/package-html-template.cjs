'use strict';

/**
 * package-html-template.cjs — HTML shell for `--package` bundle pages: page
 * frame (`renderPage`) + the primitives every other package module builds
 * on (`escapeHtml`, `toPosix`, `assetsPrefix`). Shell CSS/type tokens
 * adapted from `_shared/references/editorial-report-html.md` (see
 * package-shell.css).
 *
 * Every page loads mermaid via a plain relative `<script src>` — NEVER
 * `type="module"`, NEVER a CDN URL — so the bundle renders diagrams when
 * opened directly from `file://` with no network (Decision 5).
 *
 * The nav sidebar and index body used to live here as a flat file list plus
 * a hard-coded 4-bucket classifier (`classifyBucket`/`BUCKET_ORDER`/
 * `BUCKET_LABELS`/`BUCKET_PATTERNS`/`TRACEABILITY_MATRIX_REL_MD`) that
 * dropped 64% of pages into a trailing "Other" section. Plan
 * `260826-1601-package-reading-layers-index-pager` phase-04 deletes all of
 * that and replaces it with `lib/package-nav.cjs` (`renderNavList`) and
 * `lib/package-index-body.cjs` (`renderIndexBody`), both driven by the
 * single reading-order model from `lib/reading-spine.cjs` instead of
 * re-classifying pages from a path pattern.
 *
 * `toPosix` MUST stay exported from here — `lib/find-markdown-files.cjs`
 * imports it from this module (`require('./package-html-template.cjs')`);
 * moving or dropping it breaks page collection, not rendering.
 *
 * `zoomStrings` (plan `260827-0811-package-html-diagram-zoom`): the sidecar's
 * `ui.zoom` chrome, serialized into a `<script type="application/json">` tag so
 * the STATIC `assets/package-zoom.js` can read its own labels per page without
 * the strings being baked into the vendored asset. Optional — `model.ui` is
 * `null` on the no-sidecar fallback path, and a sidecar written before `ui.zoom`
 * existed simply has no `zoom` key; either way the tag is omitted and the viewer
 * falls back to its built-in English, the `FALLBACK_START_HERE_LABEL` precedent.
 *
 * Mermaid is initialized with `startOnLoad: false` and driven by an explicit
 * `mermaid.run()` — `startOnLoad: true` is fire-and-forget and gives the zoom
 * viewer no completion signal to attach on. The `.catch()` still attaches: one
 * bad fence must not cost the whole page its zoomable diagrams.
 *
 * `renderPage`'s `pagerHtml` slot (phase-05): the prev/next pager from
 * `lib/package-pager.cjs`, rendered immediately before `<footer
 * class="pkg-footer">`. Optional — falsy on the no-sidecar fallback path,
 * where `renderPager()` itself returns `''` and no pager renders at all.
 */

const path = require('path');

function toPosix(p) {
  return p.split(path.sep).join('/');
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** Relative path prefix from `outFile`'s directory back up to `outRoot` (e.g. `"../../"`, or `"./"` at the root). */
function assetsPrefix(outFile, outRoot) {
  const rel = path.relative(path.dirname(outFile), outRoot);
  const posixRel = toPosix(rel);
  return posixRel === '' ? './' : `${posixRel}/`;
}

/**
 * Serialize the viewer's chrome strings into an inline JSON island.
 * `<`/`>`/`&` are escaped so no string value can close the tag early — the
 * strings are authored in `_nav_strings_*.py`, but the escape is what makes
 * that irrelevant to the page's safety.
 * @returns {string} the tag, or `''` when there is nothing to localize.
 */
function renderZoomI18n(zoomStrings) {
  if (!zoomStrings || typeof zoomStrings !== 'object') return '';
  const keys = Object.keys(zoomStrings);
  if (keys.length === 0) return '';
  const json = JSON.stringify(zoomStrings)
    .replace(/&/g, '\\u0026')
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e');
  return `<script type="application/json" id="pkg-zoom-i18n">${json}</script>`;
}

function renderPage({ title, projectName, bodyHtml, tocHtml, navHtml, assetsRel, footer, pagerHtml, zoomStrings }) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${escapeHtml(title)} — ${escapeHtml(projectName)}</title>
<link rel="stylesheet" href="${assetsRel}assets/package-shell.css">
</head>
<body>
<div class="pkg-shell">
<nav class="pkg-nav">
<p class="pkg-nav-title">${escapeHtml(projectName)}</p>
<p class="pkg-nav-meta">Client Package</p>
${navHtml}
</nav>
<main class="pkg-content">
${tocHtml ? `<nav class="pkg-page-toc">${tocHtml}</nav>` : ''}
${bodyHtml}
${pagerHtml || ''}
<footer class="pkg-footer">${footer}</footer>
</main>
</div>
${renderZoomI18n(zoomStrings)}
<script src="${assetsRel}assets/mermaid.min.js"></script>
<script src="${assetsRel}assets/package-zoom.js"></script>
<script>
mermaid.initialize({ startOnLoad: false });
mermaid.run().then(function () { window.pkgZoom.attach(); }).catch(function () { window.pkgZoom.attach(); });
</script>
</body>
</html>
`;
}

module.exports = {
  assetsPrefix,
  renderPage,
  renderZoomI18n,
  escapeHtml,
  toPosix,
};
