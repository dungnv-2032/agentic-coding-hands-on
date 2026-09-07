'use strict';

/**
 * resolve-renderer.cjs — locate and load markdown-novel-viewer's shared
 * markdown-renderer.cjs (DRY reuse: `--package` never re-implements marked /
 * mermaid-fence handling).
 *
 * The renderer's own npm deps (`marked`, `highlight.js`, `gray-matter`) are
 * installed alongside IT, not alongside this script — and rebuild-spec can be
 * invoked from three different roots (project-local `.claude/skills/`, kit
 * source `claude/skills/`, or global `~/.claude/skills/`; see the "<skill-dir>
 * resolution" convention documented in every other pass's reference file, e.g.
 * overview-pass.md). Only one of those roots may actually have
 * markdown-novel-viewer's `npm install` run in it. This module tries all three
 * and picks the first one whose sibling `node_modules` can actually resolve
 * `marked`, rather than assuming a single fixed layout.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const RENDERER_REL_PATH = path.join('markdown-novel-viewer', 'scripts', 'lib', 'markdown-renderer.cjs');

/** skills/ directory that this script's own tree lives under (canonical OR shadow). */
function ownSkillsRoot() {
  // extensions/scripts/lib -> extensions/scripts -> extensions -> rebuild-spec -> skills
  return path.resolve(__dirname, '..', '..', '..', '..');
}

/** The counterpart tree: canonical <-> project-local shadow (`claude/` <-> `.claude/`). */
function counterpartSkillsRoot(skillsRoot) {
  const claudeDir = path.dirname(skillsRoot); // .../claude  or  .../.claude
  const repoRoot = path.dirname(claudeDir);
  const claudeBase = path.basename(claudeDir);
  const counterpartBase = claudeBase === '.claude' ? 'claude' : '.claude';
  return path.join(repoRoot, counterpartBase, 'skills');
}

function candidateRendererPaths() {
  const own = ownSkillsRoot();
  const roots = [own, counterpartSkillsRoot(own), path.join(os.homedir(), '.claude', 'skills')];
  const seen = new Set();
  const candidates = [];
  for (const root of roots) {
    const p = path.join(root, RENDERER_REL_PATH);
    if (!seen.has(p)) {
      seen.add(p);
      candidates.push(p);
    }
  }
  return candidates;
}

/** True iff `marked` (the renderer's core dep) resolves from this candidate's directory. */
function candidateUsable(candidatePath) {
  if (!fs.existsSync(candidatePath)) return false;
  try {
    require.resolve('marked', { paths: [path.dirname(candidatePath)] });
    return true;
  } catch {
    return false;
  }
}

/**
 * Load markdown-novel-viewer's renderer module.
 * @returns {{renderMarkdownFile: Function, renderTOCHtml: Function, generateTOC: Function}}
 * @throws {Error} if no candidate has its npm deps installed
 */
function loadRenderer() {
  const tried = [];
  for (const candidate of candidateRendererPaths()) {
    if (!fs.existsSync(candidate)) {
      tried.push(`${candidate} (not found)`);
      continue;
    }
    if (!candidateUsable(candidate)) {
      tried.push(`${candidate} (found, but 'marked' not installed alongside it)`);
      continue;
    }
    return require(candidate);
  }
  throw new Error(
    [
      "Could not load markdown-novel-viewer's markdown-renderer.cjs with its npm deps available.",
      'Tried:',
      ...tried.map((t) => `  - ${t}`),
      'Fix: cd <skills-root>/markdown-novel-viewer && npm install',
    ].join('\n')
  );
}

module.exports = { loadRenderer, candidateRendererPaths, candidateUsable };
