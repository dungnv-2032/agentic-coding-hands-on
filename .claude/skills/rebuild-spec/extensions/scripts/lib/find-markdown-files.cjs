'use strict';

/**
 * find-markdown-files.cjs — recursive `**\/*.md` walk with the package denylist
 * applied. No third-party glob dependency (kit-wide "zero third-party CLI
 * dependencies" ethos) — a manual walk covers this skill's one use case.
 */

const fs = require('fs');
const path = require('path');

const { isDenylisted, isDenylistedPath } = require('./package-denylist.cjs');
const { toPosix } = require('./package-html-template.cjs');

/**
 * @param {string} rootDir - absolute path to walk
 * @param {string[]} [excludeDirs] - absolute paths of subtrees to skip entirely
 *   (e.g. secondary-language trees nested inside a bare per-lang docs root —
 *   see lib/resolve-lang-root.cjs). Matched by exact path or by prefix, so an
 *   exclusion also covers any of its own subdirectories.
 * @returns {string[]} absolute paths of every included .md file, sorted
 */
function findMarkdownFiles(rootDir, excludeDirs = []) {
  const results = [];
  const root = path.resolve(rootDir);
  const excluded = excludeDirs.map((dir) => path.resolve(dir));

  function isExcluded(fullDir) {
    return excluded.some((ex) => fullDir === ex || fullDir.startsWith(ex + path.sep));
  }

  function walk(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      // Skip dotdirs defensively (e.g. a stray .git/.cache under docs/) — none
      // are expected in a promoted docs/ tree, but this keeps the walk inert
      // if one ever appears.
      if (entry.isDirectory() && entry.name.startsWith('.')) continue;

      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (isExcluded(full)) continue;
        walk(full);
        continue;
      }
      if (!entry.isFile() || !entry.name.toLowerCase().endsWith('.md')) continue;
      if (isDenylisted(entry.name)) continue;
      if (isDenylistedPath(toPosix(path.relative(root, full)))) continue;
      results.push(full);
    }
  }

  walk(root);
  results.sort();
  return results;
}

module.exports = { findMarkdownFiles };
