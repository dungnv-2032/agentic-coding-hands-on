'use strict';

/**
 * package-denylist.cjs — internal-only sidecars/sentinels excluded from a
 * `--package` client bundle. Mirrors SKILL.md's own "confidence-report_*.md /
 * .nav-metadata.json" enumeration plus the additional internals flagged in
 * research/researcher-02-package-mechanics.md Q3 (state files, layout
 * sentinels, hybrid-synthesis drafts, shard/profile manifests).
 *
 * Matched against a file's BASENAME only (never the full path) — cheap and
 * unambiguous, since every one of these names is internal-tooling-specific.
 *
 * NOTE on reachability: `find-markdown-files.cjs` only ever walks `.md`
 * files, so only the five `.md`-suffixed patterns below can currently match
 * anything a real walk hands to `isDenylisted()`. The remaining non-`.md`
 * patterns (state files, sentinels, manifests) are DEFENSE-IN-DEPTH, kept so
 * `isDenylisted()` stays correct and reusable if `--package` (or a future
 * collector) ever globs additional extensions — not dead weight to trim.
 *
 * NOTE on method (phase-00 D-a / RW-2): this list was originally built by
 * enumerating two other lists (SKILL.md's own sidecar mentions + a research
 * note) rather than sweeping `docs/` for every report-class artifact this
 * skill can write — which is exactly why `api-doc-semantic-review-report.md`
 * was missing despite existing at the time this file was authored. See
 * `scripts/tests/test_build_client_package.py::TestDocsSweepDenylistCoverage`
 * for the sweep test that now guards against the next such miss.
 *
 * NOTE on `DENY_PATHS` (phase-02): some internal-only files share a BASENAME
 * with a legitimate client-facing page at a different location — a
 * per-directory `README.md` nav index under `system/` or `generated/` is
 * redundant with the bundle's own sidebar, but `docs/README.md` (the Start
 * Here page) and every per-feature `README.md` reading guide under
 * `features/` are the opposite of redundant. A basename pattern can't tell
 * these apart; `DENY_PATHS` is root-relative + POSIX + exact-match so it
 * drops only the two named files.
 */

const DENY_PATTERNS = [
  // Reachable today (find-markdown-files.cjs only walks *.md):
  /^confidence-report_.*\.md$/i, // A1 confidence-report sidecars (advisory, internal-only)
  /\.draft\.md$/i, // pre-promotion system-synthesis hybrid drafts
  /^\.rebuild-package-tmp\..*\.md$/i, // stray render-sanitized.cjs temp file (belt: see build_client_package.cjs's pre-walk sweep for suspenders)
  /^api-doc-semantic-review-report\.md$/i, // RW-1 (phase-00 D-a): --api-doc semantic review — internal QA findings (SR-1..SR-5 check IDs) + file:line evidence, never client-facing

  // Defense-in-depth for a future non-.md collector — unreachable via the
  // current .md-only walk, intentionally kept:
  /^\.nav-metadata\.json$/i, // navigation sidecar
  /^\.rebuild-state\.json$/i, // incremental-run state
  /^\.layout-migrated$/i, // per-lang layout-migration sentinel
  /^\.components-migrated-v\d+$/i, // component per-lang migration sentinel
  /^component_profile.*\.json$/i, // multi-component profile manifest
  /shard-manifest.*\.json$/i, // artifact-sharding manifest
  /^_route-probe\.json$/i, // Tier-1 boot-probe sidecar
  /^\.spec-promote-pending\.json$/i, // spec-promotion rollback sentinel
  /^\.reading-order\.json$/i, // phase-01 READING_ORDER sidecar — unreachable via the current .md-only walk (same defense-in-depth rationale as the block above), kept per this file's own convention
];

// Path-scoped: root-relative (to the walk root), POSIX separators, exact
// match. See the `DENY_PATHS` header note above for why basename matching
// cannot express this — `README.md` at these two locations is an internal
// per-directory nav index; the same basename everywhere else is kept.
const DENY_PATHS = new Set([
  'system/README.md', // per-directory nav index; the bundle sidebar already covers this
  'generated/README.md', // per-directory nav index; the bundle sidebar already covers this
]);

function isDenylisted(basename) {
  return DENY_PATTERNS.some((re) => re.test(basename));
}

function isDenylistedPath(relPath) {
  return DENY_PATHS.has(relPath);
}

module.exports = { isDenylisted, isDenylistedPath, DENY_PATTERNS, DENY_PATHS };
