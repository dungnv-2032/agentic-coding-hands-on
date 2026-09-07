'use strict';

/**
 * resolve-project-name.cjs — `<ProjectName>` resolution for `--package` output
 * naming, mirroring overview-pass.md's rule: read the `**Project**:` field from
 * `docs/system/overview.md`; if absent, fall back to the repo root dir's base
 * name. Sanitised to a filesystem-safe token.
 */

const fs = require('fs');
const path = require('path');

const PROJECT_FIELD_RE = /\*\*Project\*\*:\s*(.+)/;

function sanitizeProjectName(name) {
  const trimmed = String(name).trim();
  const sanitized = trimmed.replace(/[^A-Za-z0-9._-]+/g, '_');
  if (!sanitized) return 'Project';
  // The character class above strips `/` and `\` but deliberately KEEPS `.`, so a
  // `**Project**:` value of exactly "." or ".." survives sanitisation as a live path
  // segment. Today `path.join(repoRoot, 'client-package', '..')` collapses to exactly
  // repoRoot, which safe-rimraf.cjs's exact-equality check happens to refuse — but that
  // is a coincidence of the current path shape, not a boundary. Add one segment between
  // 'client-package' and the project name and the same input would silently target a
  // sibling directory instead. Reject the traversal segments here, at the input edge,
  // so the guarantee does not depend on downstream path arithmetic.
  if (sanitized === '.' || sanitized === '..') return 'Project';
  return sanitized;
}

/**
 * @param {{docsRoot: string, repoRoot: string, explicit?: string}} opts
 * @returns {string} sanitized ProjectName
 */
function resolveProjectName({ docsRoot, repoRoot, explicit }) {
  if (explicit && explicit.trim()) return sanitizeProjectName(explicit);

  const overviewPath = path.join(docsRoot, 'system', 'overview.md');
  if (fs.existsSync(overviewPath)) {
    const content = fs.readFileSync(overviewPath, 'utf8');
    const match = content.match(PROJECT_FIELD_RE);
    if (match && match[1].trim()) return sanitizeProjectName(match[1]);
  }

  return sanitizeProjectName(path.basename(repoRoot));
}

module.exports = { resolveProjectName, sanitizeProjectName };
