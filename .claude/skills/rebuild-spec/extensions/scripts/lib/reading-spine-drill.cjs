'use strict';

/**
 * reading-spine-drill.cjs — glob-entry expansion split out of
 * reading-spine.cjs (plan `260826-1601-package-reading-layers-index-pager`,
 * phase-03b) to keep that module under its 200-line budget once the `ui`
 * plumbing landed. Pure helpers only: turns one sidecar `kind:"glob"` entry
 * into the matched/grouped page list `reading-spine.cjs` claims into the
 * model. No behavior change from the phase-03 version — a straight move.
 */

const path = require('path');

const FEATURE_FILE_ORDER = ['README.md', 'functional-spec.md', 'technical-spec.md', 'test-cases.md'];

/** Single-`*` glob matcher for the 3 shapes READING_ORDER emits: a flat file
 * glob (`flows/*.md`), a suffixed file glob (`screens/*\/spec.md`), or a
 * directory glob (`features/*\/` — trailing slash means "anything nested
 * under here", so it never matches the directory's own top-level file). */
function globTest(glob) {
  const star = glob.indexOf('*');
  const before = star === -1 ? glob : glob.slice(0, star);
  const after = star === -1 ? '' : glob.slice(star + 1);
  if (star !== -1 && after === '/') {
    return { prefix: before, test: (relMd) => relMd.startsWith(before) && relMd.slice(before.length).includes('/') };
  }
  return {
    prefix: before,
    test: (relMd) =>
      relMd.startsWith(before) && relMd.endsWith(after) &&
      !relMd.slice(before.length, relMd.length - after.length).includes('/'),
  };
}
function fileOrderRank(page) {
  const i = FEATURE_FILE_ORDER.indexOf(path.posix.basename(page.relMd));
  return i === -1 ? FEATURE_FILE_ORDER.length : i;
}
const byRelMd = (a, b) => a.relMd.localeCompare(b.relMd);

/** Expand one `kind:"glob"` sidecar entry against the real page list. */
function buildDrill(entry, pages, byPath) {
  const { prefix, test } = globTest(entry.glob);
  const matched = pages.filter((p) => test(p.relMd));
  let groups = null;
  let items;
  if (entry.key === 'features') {
    const byGroup = new Map();
    for (const p of matched) {
      const key = p.relMd.slice(prefix.length).split('/')[0];
      if (!byGroup.has(key)) byGroup.set(key, []);
      byGroup.get(key).push(p);
    }
    groups = [...byGroup.keys()].sort().map((key) => ({
      key,
      items: byGroup.get(key).slice().sort((a, b) => fileOrderRank(a) - fileOrderRank(b) || byRelMd(a, b)),
    }));
    items = groups.flatMap((g) => g.items);
  } else {
    items = matched.slice().sort(byRelMd);
  }
  // A glob's own directory index (e.g. `features/README.md`) is a separate
  // drill index only when the glob doesn't already claim it (`features/*/`
  // needs nesting, so it never matches `features/README.md`; `flows/*.md`
  // DOES match `flows/README.md`, so that stays a plain item, not an index).
  const candidate = entry.link ? byPath.get(`${entry.link}README.md`) : undefined;
  const index = candidate && !matched.some((p) => p.relMd === candidate.relMd) ? candidate : null;
  return { num: entry.num, key: entry.key, what: entry.what, link: entry.link, index, groups, items };
}

module.exports = { buildDrill };
