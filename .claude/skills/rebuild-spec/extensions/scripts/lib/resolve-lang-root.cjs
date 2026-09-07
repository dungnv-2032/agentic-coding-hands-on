'use strict';

/**
 * resolve-lang-root.cjs — per-language corpus root resolution for `--package`,
 * matched against the REAL on-disk convention recorded in
 * `docs/.rebuild-state.json`, NOT the Python `resolve_docs_root(..., multilang=True)`
 * formula. That formula returns `docs/<primary>` unconditionally in per-lang mode —
 * including for an en-primary corpus — but a real per-lang corpus produced by this
 * kit's translate pass never creates `docs/en/`: the primary tree stays at bare
 * `docs/` and secondary trees (`docs/jp/`, `docs/vi/`, ...) nest inside it as
 * siblings of `docs/features/` etc. Following the formula literally makes
 * `--package` either abort (root doesn't exist) or, if callers fall back to the
 * bare root, silently bundle every language with no exclusion.
 *
 * Convention implemented here:
 *   - `<docsRoot>/.rebuild-state.json` registers `primary_lang` + `translations{}`
 *     (secondary lang codes as object keys). Absent or malformed (including
 *     `translations` being an array rather than an object) => single-lang
 *     corpus, tolerated silently.
 *   - No registered translations => single-lang; `docsRoot` IS the root, no
 *     exclusions. An explicit `--lang` that disagrees with the registered
 *     `primary_lang` (when known) is an error — there is no second tree to serve it.
 *   - Per-lang corpus, selecting the primary:
 *       * `docsRoot/<primary>` exists as a directory => that IS the primary root
 *         (non-en primary already lives at `docs/<primary>/`).
 *       * otherwise => primary content is at bare `docsRoot` itself (the
 *         en-primary real-world shape). Secondary trees (`docsRoot/<t>` for every
 *         registered translation `t`) are then excluded from the walk, since they
 *         sit inside the same bare root.
 *   - Per-lang corpus, selecting a secondary: root is exactly `docsRoot/<lang>`;
 *     missing => abort with a clear error. Nothing nests inside a secondary tree,
 *     so no exclusions are needed.
 *   - Unknown `--lang` (neither primary nor a registered secondary) => abort,
 *     listing every available language.
 *
 * SECURITY: every language code this module touches — the `--lang` CLI value,
 * `.rebuild-state.json`'s `primary_lang`, and every key of its `translations`
 * object — is untrusted input that gets fed into `path.join(docsRoot, code)`.
 * A code containing `/`, `\`, or `.` (e.g. `"../../secret"`) can escape
 * `docsRoot` entirely, turning the DEFAULT invocation (no `--lang` needed —
 * `primary_lang` alone drives the primary-root `path.join`) into an arbitrary
 * directory read that gets bundled straight into the client HTML output. This
 * mirrors the Python side's guard (`_lang_lib.py` `normalize_lang`'s
 * `_PATH_UNSAFE_RE`, red-team finding Sec-F1) — every code is validated by
 * `assertPathSafeLangCode()` BEFORE it is ever joined into a path or handed to
 * `isDir()`, never trusted to have been normalized upstream by the pipeline.
 */

const fs = require('fs');
const path = require('path');

const PATH_UNSAFE_RE = /[/\\.]/;

/**
 * Reject any language code that could escape `docsRoot` once joined into a
 * path — mirrors `_lang_lib.py`'s `_PATH_UNSAFE_RE` guard. Throws immediately
 * rather than skipping/sanitizing, so a crafted `.rebuild-state.json` (or a
 * caller-supplied `--lang`) fails loudly instead of silently degrading into
 * an unintended directory.
 *
 * @param {unknown} code
 * @param {string} source - human-readable origin, used in the error message
 */
function assertPathSafeLangCode(code, source) {
  if (typeof code !== 'string' || code.length === 0 || PATH_UNSAFE_RE.test(code)) {
    throw new Error(`path-unsafe language code in ${source}: ${JSON.stringify(code)}`);
  }
}

function readState(docsRoot) {
  const statePath = path.join(docsRoot, '.rebuild-state.json');
  if (!fs.existsSync(statePath)) return null;
  try {
    const parsed = JSON.parse(fs.readFileSync(statePath, 'utf8'));
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    return null;
  }
}

function isDir(p) {
  try {
    return fs.statSync(p).isDirectory();
  } catch {
    return false;
  }
}

/**
 * @param {{docsRoot: string, lang: string|null, repoRoot?: string}} opts
 *   docsRoot: absolute path to the OUTER docs directory (as passed via
 *     `--docs-root`, before any per-language resolution).
 *   lang: the raw `--lang` value, or null when omitted (defaults to primary).
 *   repoRoot: optional, used only to shorten paths in error messages.
 * @returns {{root: string, excludeDirs: string[], lang: string|null}}
 */
function resolveLangRoot({ docsRoot, lang, repoRoot }) {
  const display = (p) => (repoRoot ? path.relative(repoRoot, p) || '.' : p);

  // Validate the CLI-supplied lang up front — before it is ever compared
  // against or joined with anything derived from the (also untrusted) state file.
  if (lang != null) assertPathSafeLangCode(lang, '--lang');

  const state = readState(docsRoot);

  // `translations` must be a plain object (an array passes `typeof === 'object'`
  // but its "keys" are numeric indices, not language codes) — anything else is
  // treated the same as a missing/malformed state file: single-lang, tolerated
  // silently.
  const rawTranslations =
    state && state.translations && typeof state.translations === 'object' && !Array.isArray(state.translations)
      ? state.translations
      : {};
  const secondaries = Object.keys(rawTranslations);
  // Validate every registered secondary BEFORE any of them is joined into a
  // path (as an exclusion dir, or as the selected root) or compared against `lang`.
  for (const key of secondaries) {
    assertPathSafeLangCode(key, 'docs/.rebuild-state.json translations key');
  }

  let primaryLangFromState = null;
  if (state && typeof state.primary_lang === 'string') {
    // Validate BEFORE it is ever joined into `path.join(docsRoot, primaryLang)`.
    assertPathSafeLangCode(state.primary_lang, 'docs/.rebuild-state.json primary_lang');
    primaryLangFromState = state.primary_lang;
  }

  // Single-lang: no registered translations at all (or no/malformed state file).
  if (secondaries.length === 0) {
    const primaryLang = primaryLangFromState;
    if (lang && primaryLang && lang !== primaryLang) {
      throw new Error(
        `unknown language '${lang}' for ${display(docsRoot)} — this is a single-language corpus ` +
          `(${primaryLang}), no translations registered`
      );
    }
    return { root: docsRoot, excludeDirs: [], lang: lang || primaryLang };
  }

  const primaryLang = primaryLangFromState || 'en';
  const selected = lang || primaryLang;
  const available = [primaryLang, ...secondaries];

  if (selected === primaryLang) {
    const nestedPrimaryRoot = path.join(docsRoot, primaryLang);
    const root = isDir(nestedPrimaryRoot) ? nestedPrimaryRoot : docsRoot;
    const excludeDirs = secondaries.map((t) => path.join(docsRoot, t));
    return { root, excludeDirs, lang: primaryLang };
  }

  if (secondaries.includes(selected)) {
    const root = path.join(docsRoot, selected);
    if (!isDir(root)) {
      throw new Error(`secondary language '${selected}' is registered but ${display(root)} does not exist`);
    }
    return { root, excludeDirs: [], lang: selected };
  }

  throw new Error(`unknown language '${selected}' — available: ${available.join(', ')} (primary: ${primaryLang})`);
}

module.exports = { resolveLangRoot, assertPathSafeLangCode };
