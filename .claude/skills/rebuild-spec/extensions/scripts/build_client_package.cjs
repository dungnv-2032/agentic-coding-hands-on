#!/usr/bin/env node
'use strict';

/**
 * build_client_package.cjs — EXPORT-tier `--package` pass engine for
 * /tkm:rebuild-spec. See references/pipeline-package.md for the full pass
 * contract this implements.
 *
 * Converts an already-promoted docs/ corpus into a self-contained, offline
 * client HTML bundle: every `<docs-root>/**\/*.md` (minus the internal
 * denylist) -> `<bundle>/**\/*.html` via the reused markdown-novel-viewer
 * renderer, plus an `index.html` nav and vendored assets (mermaid.min.js
 * classic global bundle + package-shell.css + package-zoom.js) — so the bundle opens from
 * `file://` with no network and no build step.
 *
 * Usage:
 *   node build_client_package.cjs --docs-root docs [--lang en] [--out DIR]
 *                                  [--project-name NAME] [--repo-root DIR]
 *
 * Exit codes: 0 = bundle written; 1 = bad input / nothing to bundle.
 */

const fs = require('fs');
const path = require('path');

const { loadRenderer } = require('./lib/resolve-renderer.cjs');
const { renderMarkdownFileSanitized } = require('./lib/render-sanitized.cjs');
const { findMarkdownFiles } = require('./lib/find-markdown-files.cjs');
const { resolveLangRoot } = require('./lib/resolve-lang-root.cjs');
const { resolveProjectName } = require('./lib/resolve-project-name.cjs');
const { rimraf } = require('./lib/safe-rimraf.cjs');
const { parseArgs } = require('./lib/parse-package-args.cjs');
const { sweepStrayTempFiles } = require('./lib/sweep-stray-temp-files.cjs');
const { loadSidecar, buildReadingModel } = require('./lib/reading-spine.cjs');
const { assetsPrefix, renderPage, toPosix } = require('./lib/package-html-template.cjs');
const { renderNavList } = require('./lib/package-nav.cjs');
const { renderIndexBody } = require('./lib/package-index-body.cjs');
const { renderPager } = require('./lib/package-pager.cjs');

function buildClientPackage(rawArgs) {
  const args = parseArgs(rawArgs);
  const repoRoot = path.resolve(args.repoRoot);
  // `--docs-root` names the OUTER docs directory — the one that carries
  // `.rebuild-state.json` — not a pre-resolved per-language root. On a
  // per-lang corpus the actual content root (and any secondary-language
  // exclusions) is derived below via resolveLangRoot(), matched against the
  // real on-disk convention (see lib/resolve-lang-root.cjs header comment)
  // rather than the Python `resolve_docs_root(..., multilang=True)` formula,
  // which resolves to a directory (`docs/<primary>`) that doesn't exist for
  // an en-primary per-lang corpus.
  const docsRootOuter = path.resolve(repoRoot, args.docsRoot);

  if (!fs.existsSync(docsRootOuter) || !fs.statSync(docsRootOuter).isDirectory()) {
    throw new Error(`docs root not found: ${docsRootOuter}`);
  }

  const { root: docsRoot, excludeDirs, lang: resolvedLang } = resolveLangRoot({
    docsRoot: docsRootOuter,
    lang: args.lang,
    repoRoot,
  });

  const projectName = resolveProjectName({ docsRoot, repoRoot, explicit: args.projectName });
  const outRoot = args.out ? path.resolve(args.out) : path.join(repoRoot, 'client-package', projectName);

  const { renderMarkdownFile } = loadRenderer();

  // Sweep the whole outer tree — a stray `.rebuild-package-tmp.*.md` left
  // behind by a prior crashed run could in principle land under any
  // language's subtree, and deleting one is always safe regardless of scope.
  sweepStrayTempFiles(docsRootOuter);

  const files = findMarkdownFiles(docsRoot, excludeDirs);
  if (files.length === 0) {
    throw new Error(`no markdown files found under ${docsRoot} (after denylist/language exclusions)`);
  }

  // Idempotent re-run: wipe then rebuild, so a doc removed from docs/ since the
  // last build doesn't leave an orphaned page in the bundle. Guarded by a
  // safety floor — see lib/safe-rimraf.cjs.
  rimraf(outRoot, { repoRoot, isExplicitOut: Boolean(args.out) });
  fs.mkdirSync(outRoot, { recursive: true });

  const pages = files
    .map((file) => {
      const relMd = toPosix(path.relative(docsRoot, file));
      const relHtml = relMd.replace(/\.md$/i, '.html');
      const outFile = path.join(outRoot, relHtml);
      // Fence-aware pre-escape of raw HTML in prose — the actual XSS boundary
      // for this pass. See lib/sanitize-markdown-source.cjs for why this is
      // needed even though renderMarkdownFile() escapes fenced-code content.
      const rendered = renderMarkdownFileSanitized(renderMarkdownFile, file);
      // relMd (the SOURCE .md relative path) is how the reading-order sidecar
      // (lib/reading-spine.cjs) claims a page into the index/sidebar model —
      // kept separate from relHtml (the OUTPUT path used for hrefs/writes).
      return { relMd, relHtml, outFile, ...rendered };
    })
    .sort((a, b) => a.relHtml.localeCompare(b.relHtml));

  // Reading-order sidecar: read at the RESOLVED per-language root (`docsRoot`),
  // never the outer root passed via `--docs-root` — a per-lang corpus has one
  // sidecar per language tree, and there is deliberately no cross-root
  // fallback (reading the outer root's copy would hand a secondary-language
  // bundle the primary language's prose). `buildReadingModel` degrades to a
  // pager-less listing when no sidecar is present, never throws, never drops
  // a page. The index (renderIndexBody), sidebar (renderNavList), and pager
  // (renderPager) below all render this SAME model, so all three views
  // share one ordering instead of re-deriving their own.
  const sidecar = loadSidecar(docsRoot);
  const readingModel = buildReadingModel({ sidecar, pages, projectName });

  const footer = `Generated by /tkm:rebuild-spec --package on ${new Date().toISOString().slice(0, 10)}`;

  // Chrome strings for the click-to-zoom diagram viewer (assets/package-zoom.js).
  // `ui.zoom` is deliberately OPTIONAL on the sidecar — see the `isUsableUi`
  // header in lib/reading-spine.cjs — so this is undefined for a sidecar written
  // before the block existed, and for the no-sidecar fallback where `ui` is null.
  // In both cases no i18n island is emitted and the viewer uses its own English.
  const zoomStrings = readingModel.ui ? readingModel.ui.zoom : null;

  for (const p of pages) {
    fs.mkdirSync(path.dirname(p.outFile), { recursive: true });
    const prefix = assetsPrefix(p.outFile, outRoot);
    const html = renderPage({
      title: p.title,
      projectName,
      bodyHtml: p.html,
      tocHtml: '',
      navHtml: renderNavList(readingModel, p.relHtml, prefix),
      assetsRel: prefix,
      footer,
      pagerHtml: renderPager(readingModel, p.relHtml, prefix),
      zoomStrings,
    });
    fs.writeFileSync(p.outFile, html, 'utf8');
  }

  const indexFile = path.join(outRoot, 'index.html');
  const indexHtml = renderPage({
    title: `${projectName} — Overview`,
    projectName,
    bodyHtml: renderIndexBody({
      model: readingModel,
      quickPath: sidecar ? sidecar.quickPath : null,
      roles: sidecar ? sidecar.roles : null,
      projectName,
      pageCount: pages.length,
    }),
    tocHtml: '',
    navHtml: renderNavList(readingModel, 'index.html', './'),
    assetsRel: './',
    footer,
    pagerHtml: renderPager(readingModel, 'index.html', './'),
    zoomStrings,
  });
  fs.writeFileSync(indexFile, indexHtml, 'utf8');

  const assetsDir = path.join(outRoot, 'assets');
  fs.mkdirSync(assetsDir, { recursive: true });
  const skillAssetsDir = path.join(__dirname, '..', 'assets');
  fs.copyFileSync(path.join(skillAssetsDir, 'mermaid.min.js'), path.join(assetsDir, 'mermaid.min.js'));
  fs.copyFileSync(path.join(skillAssetsDir, 'package-shell.css'), path.join(assetsDir, 'package-shell.css'));
  fs.copyFileSync(path.join(skillAssetsDir, 'package-zoom.js'), path.join(assetsDir, 'package-zoom.js'));

  return {
    outRoot,
    projectName,
    pageCount: pages.length,
    lang: resolvedLang,
    excludeDirs,
    readingModel,
    hasSidecar: sidecar !== null,
  };
}

function main() {
  try {
    const result = buildClientPackage(process.argv.slice(2));
    const langNote = result.lang ? `, lang: ${result.lang}` : '';
    const excludedNote = result.excludeDirs.length
      ? `, excluded: ${result.excludeDirs.map((d) => path.basename(d)).join(', ')}`
      : '';
    const spineNote =
      `, sidecar: ${result.hasSidecar ? 'yes' : 'no'}, spine: ${result.readingModel.spine.length}` +
      `, appendix: ${result.readingModel.appendix.length}`;
    console.log(
      `[--package] ${result.pageCount} page(s) -> ${result.outRoot}/index.html ` +
        `(project: ${result.projectName}${langNote}${excludedNote}${spineNote})`
    );
    process.exit(0);
  } catch (err) {
    console.error(`[--package] ERROR: ${err.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { buildClientPackage, parseArgs };
