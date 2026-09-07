'use strict';

/**
 * reading-spine.cjs — turns (sidecar, pages) into ONE reading model consumed
 * by the index, the grouped sidebar, and the prev/next pager alike (plan
 * `260826-1601-package-reading-layers-index-pager`, phase-03). Building
 * these three views from separate orderings is the drift this module exists
 * to prevent — see plan.md "Direction".
 *
 * `loadSidecar()` is the only impure export. `buildReadingModel()` is pure
 * and treats the sidecar as untrusted: never used as a filesystem path —
 * `loadSidecar()` reads one FIXED filename off `docsRoot`, and
 * `buildReadingModel()` only looks a sidecar `path`/`glob` up in a `Map`
 * built from the real page walk; an entry whose target isn't in that Map is
 * silently dropped, never read from disk. `sidecar===null` (absent,
 * unparsable, missing `ui`, or schemaVersion !== 1) returns the SAME shape
 * as the normal path (fallback model), so a caller never branches on which
 * path ran.
 *
 * Ordering ported from this session's verified mockup generator
 * (`gen-preview.cjs`): flows/screens sorted by path, features grouped by
 * feature then by file role (README -> functional-spec -> technical-spec ->
 * test-cases), traceability pulled out of the numbered rows into `trace`.
 * The mockup's `PROPOSED_L3` promotion of `system/permissions.md` /
 * `generated/job-list.md` into layer 3 is deliberately NOT ported —
 * plan.md's scope boundary keeps those two pages in the Appendix.
 *
 * `ui` (phase-03b): the sidecar's localized chrome strings (Start Here /
 * Appendix / drill labels / pager prose) — REQUIRED on a valid sidecar, so
 * 04/05 read `model.ui` instead of hard-coding English literals. Glob-entry
 * expansion lives in the sibling `reading-spine-drill.cjs` (split out here
 * to keep this file under its 200-line budget).
 */

const fs = require('fs');
const path = require('path');
const { buildDrill } = require('./reading-spine-drill.cjs');

const SIDECAR_FILENAME = '.reading-order.json';
const SCHEMA_VERSION = 1;
const TRACE_KEY = 'traceability_matrix';
const START_HERE_PATH = 'README.md';

/**
 * Read `<docsRoot>/.reading-order.json`. `docsRoot` MUST already be the
 * resolved per-language root (`resolveLangRoot().root`), not the outer docs
 * root — a per-lang corpus has one sidecar per language tree and there is
 * deliberately no cross-root fallback (reading the outer root's copy would
 * hand a secondary-language bundle the primary language's prose). Returns
 * the parsed payload, or `null` on any absence/parse/shape problem,
 * including `schemaVersion !== 1` (an unsupported future format) or a
 * missing/malformed `ui` block — a silent per-language degradation to
 * English chrome is the defect phase-03b removes; there is deliberately no
 * default here, only the same no-sidecar fallback every other shape
 * problem already takes.
 */
/** Required chrome-string shape. Presence of a `ui` OBJECT is not enough: a
 * schema-valid but hollow `ui: {}` used to pass this gate and then blow up at
 * `model.ui.pager.<key>` deref time, aborting the whole bundle build instead of
 * degrading to the documented pager-less fallback. Validate the SHAPE the
 * renderers actually dereference, so a malformed sidecar takes the same
 * fallback path as an absent one.
 *
 * `ui.zoom` (plan `260827-0811-package-html-diagram-zoom`) is deliberately NOT
 * checked here. It is consumed CLIENT-side by assets/package-zoom.js, which
 * carries its own English defaults, so an absent block costs a locale its
 * viewer labels and nothing else. Requiring it would invalidate every sidecar
 * written by the shipped build_navigation.py before that block existed and drop
 * those corpora to the alphabetical, pager-less fallback — a far larger
 * regression than untranslated button tooltips. */
const UI_PAGER_KEYS = ['prev', 'next', 'reading', 'back_to_index', 'end_of_spine'];
function isUsableUi(ui) {
  if (!ui || typeof ui !== 'object') return false;
  if (typeof ui.start_here !== 'string' || typeof ui.appendix !== 'string') return false;
  if (!ui.drill_labels || typeof ui.drill_labels !== 'object') return false;
  if (!ui.pager || typeof ui.pager !== 'object') return false;
  return UI_PAGER_KEYS.every((k) => typeof ui.pager[k] === 'string');
}

function loadSidecar(docsRoot) {
  let raw;
  try {
    raw = fs.readFileSync(path.join(docsRoot, SIDECAR_FILENAME), 'utf8');
  } catch {
    return null;
  }
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  if (!parsed || typeof parsed !== 'object' || parsed.schemaVersion !== SCHEMA_VERSION) return null;
  if (!Array.isArray(parsed.layers)) return null;
  if (!isUsableUi(parsed.ui)) return null;
  return parsed;
}

/** Absent/rejected sidecar: every page still appears (in `appendix`), spine
 * stays empty so a pager-rendering caller renders none without branching.
 * `ui` is `null` — there is no locale to read chrome strings from. */
function buildFallbackModel(pages) {
  return {
    startHere: null,
    layers: [],
    trace: null,
    appendix: pages.slice().sort((a, b) => String(a.title).localeCompare(String(b.title))),
    spine: [],
    ui: null,
  };
}

function buildClaimedModel(sidecar, pages) {
  const byPath = new Map(pages.map((p) => [p.relMd, p]));
  const claimed = new Set();
  const claim = (p) => p && claimed.add(p.relMd);
  const startHere = byPath.get(START_HERE_PATH) || null;
  claim(startHere);
  let trace = null;
  const layers = sidecar.layers
    .slice()
    .sort((a, b) => a.layer - b.layer)
    .map((layer) => {
      const entries = [];
      const drills = [];
      for (const entry of layer.entries || []) {
        if (entry.kind === 'glob') {
          const drill = buildDrill(entry, pages, byPath);
          claim(drill.index);
          drill.items.forEach(claim);
          drills.push(drill);
        } else if (entry.key === TRACE_KEY) {
          trace = byPath.get(entry.path) || null;
          claim(trace);
        } else {
          const page = byPath.get(entry.path);
          if (page) {
            entries.push({ num: entry.num, page, what: entry.what });
            claim(page);
          }
        }
      }
      entries.sort((a, b) => a.num - b.num);
      return { layer: layer.layer, label: layer.label, intro: layer.intro, entries, drills };
    });

  const appendix = pages
    .filter((p) => !claimed.has(p.relMd))
    .sort((a, b) => String(a.title).localeCompare(String(b.title)));

  const spine = [];
  const push = (page, section) => page && spine.push({ page, section });
  push(startHere, sidecar.title);
  for (const layer of layers) {
    for (const e of layer.entries) push(e.page, layer.label);
    for (const d of layer.drills) {
      push(d.index, layer.label);
      d.items.forEach((p) => push(p, layer.label));
    }
  }
  const traceLayer = layers.find((l) => l.layer === 4) || layers[layers.length - 1];
  push(trace, traceLayer ? traceLayer.label : sidecar.title);
  appendix.forEach((p) => push(p, sidecar.ui.appendix));

  return { startHere, layers, trace, appendix, spine, ui: sidecar.ui };
}

/** `{sidecar, pages, projectName}` -> `{startHere, layers, trace, appendix, spine, ui}`.
 * `projectName` is accepted for interface parity with the phase contract but
 * unused by the ordering logic itself. */
function buildReadingModel({ sidecar, pages }) {
  if (
    !sidecar ||
    sidecar.schemaVersion !== SCHEMA_VERSION ||
    !Array.isArray(sidecar.layers) ||
    !sidecar.ui ||
    typeof sidecar.ui !== 'object'
  ) {
    return buildFallbackModel(pages);
  }
  try {
    return buildClaimedModel(sidecar, pages);
  } catch {
    return buildFallbackModel(pages); // untrusted input: any shape surprise degrades, never throws
  }
}
module.exports = { loadSidecar, buildReadingModel };
