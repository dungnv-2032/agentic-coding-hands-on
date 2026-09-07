'use strict';

/**
 * render-sanitized.cjs — the actual `--package` XSS boundary: runs
 * `sanitize-markdown-source.cjs` on a doc's raw text, then hands the result to
 * the shared `renderMarkdownFile()` (see resolve-renderer.cjs). The shared
 * renderer only accepts a file PATH (it reads the file itself internally), so
 * a sanitized copy is written to a throwaway sibling temp file — same
 * directory as the original, so `renderMarkdownFile()`'s own relative-image
 * resolution (`path.dirname(filePath)`) is unaffected.
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const { sanitizeMarkdownSource } = require('./sanitize-markdown-source.cjs');

/**
 * @param {(filePath: string) => object} renderMarkdownFile - from resolve-renderer.cjs
 * @param {string} filePath - absolute path to the source .md file
 * @returns {object} same shape renderMarkdownFile() returns ({html, toc, frontmatter, title})
 */
function renderMarkdownFileSanitized(renderMarkdownFile, filePath) {
  const original = fs.readFileSync(filePath, 'utf8');
  const sanitized = sanitizeMarkdownSource(original);

  if (sanitized === original) {
    // Nothing to neutralize — render the file directly, no temp-file
    // indirection needed for the common case.
    return renderMarkdownFile(filePath);
  }

  const dir = path.dirname(filePath);
  const tmpPath = path.join(dir, `.rebuild-package-tmp.${crypto.randomBytes(6).toString('hex')}.md`);
  fs.writeFileSync(tmpPath, sanitized, 'utf8');

  try {
    const result = renderMarkdownFile(tmpPath);
    // Guard the one path-dependent fallback in renderMarkdownFile: if it had
    // to fall back to the basename as the title (no frontmatter title, no
    // <h1>), that fallback would otherwise read the temp file's random name.
    const tmpBasename = path.basename(tmpPath, '.md');
    if (result.title === tmpBasename) {
      result.title = path.basename(filePath, '.md');
    }
    return result;
  } finally {
    fs.rmSync(tmpPath, { force: true });
  }
}

module.exports = { renderMarkdownFileSanitized };
