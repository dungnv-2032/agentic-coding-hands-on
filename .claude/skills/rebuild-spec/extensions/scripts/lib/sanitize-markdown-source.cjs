'use strict';

/**
 * sanitize-markdown-source.cjs — fence-aware pre-escape of raw markdown SOURCE
 * text, run BEFORE handing content to markdown-novel-viewer's
 * `renderMarkdownFile()`.
 *
 * WHY THIS EXISTS (the actual XSS boundary for `--package`):
 * CommonMark's "raw HTML" grammar rule lets ANY HTML-tag-like sequence in
 * markdown PROSE pass through a compliant markdown renderer completely
 * unescaped — this is intentional upstream CommonMark/marked behavior, not a
 * bug in `renderMarkdownFile()`. That renderer is shared with
 * markdown-novel-viewer, which renders TRUSTED, human-authored content (plans,
 * specs the author wrote) where raw-HTML passthrough is a feature, not a
 * risk — so we do NOT change it (different trust context; see
 * resolve-renderer.cjs). rebuild-spec's promoted `docs/` corpus, however, can
 * echo source-derived strings (quoted code, business-rule text, scanned
 * copy) that happen to look like `<script>`/`<img onerror=...>` tags — those
 * must never execute in a client-facing exported HTML bundle. `--package`
 * closes that gap at ITS OWN boundary, before content ever reaches the
 * shared renderer.
 *
 * MECHANISM: escape `<`, `>`, `&` in the source text OUTSIDE of:
 *   - a leading YAML frontmatter block (--- ... ---) at the very top of the file
 *   - fenced code blocks (``` or ~~~) — their CONTENT is left untouched (the
 *     renderer's own mermaid-escaping / hljs-highlighting already makes it
 *     safe, and re-escaping here would double-escape and corrupt diagram
 *     syntax, e.g. turning `-->` into `--&gt;` inside a mermaid fence)
 *   - a line's leading blockquote markers (`>`, `>>`, ...) — preserved so
 *     blockquotes keep parsing as blockquotes; only the quoted text itself is
 *     escaped
 * This denies CommonMark's raw-HTML rule any literal `<tag>` to match on in
 * prose, without needing to know every HTML shape the renderer might
 * legitimately emit downstream (which would require re-implementing an
 * allowlist HTML sanitizer against marked's full output surface, including
 * highlight.js's per-token `<span class="hljs-*">` variants).
 *
 * KNOWN, ACCEPTED TRADE-OFFS (documented, not silently swallowed):
 *  - Single-backtick inline code spans containing `<`/`>` may render
 *    double-escaped (cosmetic only, e.g. `` `<Foo />` `` shows the literal
 *    text `&lt;Foo /&gt;` instead of the bracket characters). Security is
 *    unaffected either way — the content still cannot execute.
 *  - CommonMark bare autolinks (`<https://example.com>`) are neutralized to
 *    plain escaped text rather than becoming a clickable link. rebuild-spec's
 *    own generated docs always use `[text](url)` links, never bare autolinks.
 *  - 4-space-indented code blocks (no fence) are treated as ordinary prose
 *    and escaped. rebuild-spec's templates always use fenced code, so this is
 *    not expected to occur in practice; if it ever does, output degrades to
 *    escaped-but-unhighlighted text (safe, just not pretty) — never raw HTML.
 *  - Prose that already contains a literal HTML entity (e.g. someone typed
 *    `&amp;` in source expecting it to display as `&`) gets double-escaped
 *    (`&amp;` -> `&amp;amp;`, rendering the literal entity text instead of the
 *    decoded character). Cosmetic only, accepted — this codebase's generated
 *    docs write plain characters ("AT&T"), not hand-typed entity syntax.
 */

const FENCE_OPEN_RE = /^(\s{0,3}(?:`{3,}|~{3,}))(.*)$/;
const BLOCKQUOTE_PREFIX_RE = /^((?:\s*>\s?)+)/;
const FRONTMATTER_DELIM_RE = /^---\s*$/;

function escapeAngleAndAmp(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function escapeProseLine(line) {
  const bq = line.match(BLOCKQUOTE_PREFIX_RE);
  if (bq) {
    return bq[1] + escapeAngleAndAmp(line.slice(bq[1].length));
  }
  return escapeAngleAndAmp(line);
}

/**
 * @param {string} markdown - raw markdown source (as read from disk, frontmatter included)
 * @returns {string} markdown with raw HTML in prose neutralized
 */
function sanitizeMarkdownSource(markdown) {
  const lines = markdown.split('\n');
  const out = [];

  let inFrontmatter = false;
  let fenceChar = null; // '`' or '~' while inside a fenced code block, else null
  let fenceLen = 0;

  lines.forEach((line, idx) => {
    // Frontmatter: only recognized if the very first line is exactly "---".
    if (idx === 0 && FRONTMATTER_DELIM_RE.test(line)) {
      inFrontmatter = true;
      out.push(line);
      return;
    }
    if (inFrontmatter) {
      out.push(line);
      if (FRONTMATTER_DELIM_RE.test(line)) inFrontmatter = false;
      return;
    }

    if (fenceChar === null) {
      const openMatch = line.match(FENCE_OPEN_RE);
      if (openMatch) {
        const fenceRun = openMatch[1].trim();
        fenceChar = fenceRun[0];
        fenceLen = fenceRun.length;
        // The fence marker itself is structural syntax (leave as-is); the
        // info string after it (e.g. "mermaid") is untrusted-ish but not
        // prose either — escape it defensively, it never carries citations.
        out.push(openMatch[1] + escapeAngleAndAmp(openMatch[2]));
        return;
      }
      out.push(escapeProseLine(line));
      return;
    }

    // Inside a fence: leave content untouched — the renderer's own
    // mermaid/hljs handling is responsible for escaping it safely.
    out.push(line);
    const run = fenceChar.repeat(fenceLen);
    const trimmed = line.trim();
    if (trimmed.startsWith(run) && /^[`~]+$/.test(trimmed)) {
      fenceChar = null;
      fenceLen = 0;
    }
  });

  return out.join('\n');
}

module.exports = { sanitizeMarkdownSource };
