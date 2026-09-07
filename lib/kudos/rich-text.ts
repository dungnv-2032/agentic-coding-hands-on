/**
 * Rich-text document model for Viết Kudo (F005, phase 01, frozen). Zero
 * runtime deps: no I/O, no React, no `Intl` (client-bundle safe). Closed
 * over six toolbar ops, no nesting. `body-editor` is a controlled
 * `<textarea>`, so marks live OVER plain text with no in-editor WYSIWYG
 * preview; `remapMarks` diffs by common prefix/suffix and drops any mark
 * touching the edited region rather than re-anchoring by guesswork —
 * deliberate, not a bug. `parseKudosDoc` is the untrusted-input boundary
 * for anonymous-visitor content: any surprise returns `null`, never HTML —
 * only data a renderer walks into React elements, so
 * `dangerouslySetInnerHTML` never enters the picture.
 */
import { ACCEPTED_LINK_SCHEMES, type KudosBlock, type KudosDoc, type KudosRun, type ToggleableBlock, type ToggleableInlineMark } from "./compose-contract";
export interface TextRange { start: number; end: number }
export interface InlineMark {
  kind: ToggleableInlineMark | "mention";
  start: number;
  end: number;
  href?: string; // kind === "link"
  sunnerId?: number; // kind === "mention"
  label?: string; // kind === "mention"
}
export interface BlockMark { kind: ToggleableBlock; start: number; end: number }
export interface RichTextState { text: string; inline: InlineMark[]; blocks: BlockMark[] }
const INLINE_KINDS: readonly ToggleableInlineMark[] = ["bold", "italic", "strike", "link"];
/** Routes a `toggleMark` action to `toggleInlineMark` or `toggleBlockMark`. */
export function isToggleableInlineMark(kind: ToggleableInlineMark | ToggleableBlock): kind is ToggleableInlineMark {
  return (INLINE_KINDS as readonly string[]).includes(kind);
}
function lineRangesOf(text: string): TextRange[] {
  const ranges: TextRange[] = [];
  let start = 0;
  for (let i = 0; i <= text.length; i++) {
    if (i === text.length || text[i] === "\n") {
      ranges.push({ start, end: i });
      start = i + 1;
    }
  }
  return ranges;
}
function coveredByMarks(marks: readonly TextRange[], range: TextRange): boolean {
  if (range.end <= range.start) return false;
  let cursor = range.start;
  for (const m of [...marks].sort((a, b) => a.start - b.start)) {
    if (m.start > cursor) break;
    if (m.end > cursor) cursor = m.end;
    if (cursor >= range.end) return true;
  }
  return cursor >= range.end;
}
/** Whether `range` is entirely covered by marks of `kind` — drives toolbar `aria-pressed`. */
export function isMarkActive(state: RichTextState, kind: ToggleableInlineMark | ToggleableBlock, range: TextRange): boolean {
  return isToggleableInlineMark(kind)
    ? coveredByMarks(state.inline.filter((m) => m.kind === kind), range)
    : coveredByMarks(state.blocks.filter((m) => m.kind === kind), range);
}
/** Toggles bold/italic/strike/link over `range`; splits partially-overlapping marks so the untouched part keeps its mark. */
export function toggleInlineMark(state: RichTextState, kind: ToggleableInlineMark, range: TextRange, href?: string): RichTextState {
  if (range.end <= range.start) return state;
  if (isMarkActive(state, kind, range)) {
    const inline = state.inline.flatMap((mark) => {
      if (mark.kind !== kind || mark.end <= range.start || mark.start >= range.end) return [mark];
      const rest: InlineMark[] = [];
      if (mark.start < range.start) rest.push({ ...mark, end: range.start });
      if (mark.end > range.end) rest.push({ ...mark, start: range.end });
      return rest;
    });
    return { ...state, inline };
  }
  const mark: InlineMark = kind === "link" ? { kind, start: range.start, end: range.end, href: href ?? "" } : { kind, start: range.start, end: range.end };
  return { ...state, inline: [...state.inline, mark] };
}
/** Toggles ordered-list/quote over every line `range` touches; a line holds at most one block kind. */
export function toggleBlockMark(state: RichTextState, kind: ToggleableBlock, range: TextRange): RichTextState {
  const touched = lineRangesOf(state.text).filter((l) => (l.end > range.start && l.start < range.end) || (range.start === range.end && range.start >= l.start && range.start <= l.end));
  if (touched.length === 0) return state;
  const allActive = touched.every((l) => state.blocks.some((m) => m.kind === kind && m.start === l.start && m.end === l.end));
  const remaining = state.blocks.filter((m) => !touched.some((l) => m.start === l.start && m.end === l.end));
  if (allActive) return { ...state, blocks: remaining };
  return { ...state, blocks: [...remaining, ...touched.map((l) => ({ kind, start: l.start, end: l.end }))] };
}
/** Inserts `@label` at `at`, marked as a mention carrying `sunnerId`. A known insertion point, so shifting is exact. */
export function insertMention(state: RichTextState, at: number, label: string, sunnerId: number): RichTextState {
  const mentionText = `@${label}`;
  const delta = mentionText.length;
  const text = state.text.slice(0, at) + mentionText + state.text.slice(at);
  const shift = <M extends TextRange>(mark: M): M =>
    mark.start >= at ? { ...mark, start: mark.start + delta, end: mark.end + delta } : mark.end > at ? { ...mark, end: mark.end + delta } : mark;
  const mention: InlineMark = { kind: "mention", start: at, end: at + delta, sunnerId, label };
  return { text, inline: [...state.inline.map(shift), mention], blocks: state.blocks.map(shift) };
}
/** Common-prefix/suffix diff; a mark overlapping the edited region is dropped, never re-anchored by guesswork. */
export function remapMarks(state: RichTextState, nextText: string): RichTextState {
  const oldText = state.text;
  if (oldText === nextText) return state;
  let prefixLen = 0;
  const maxPrefix = Math.min(oldText.length, nextText.length);
  while (prefixLen < maxPrefix && oldText[prefixLen] === nextText[prefixLen]) prefixLen++;
  let suffixLen = 0;
  const maxSuffix = maxPrefix - prefixLen;
  while (suffixLen < maxSuffix && oldText[oldText.length - 1 - suffixLen] === nextText[nextText.length - 1 - suffixLen]) suffixLen++;
  const oldChangeEnd = oldText.length - suffixLen;
  const delta = nextText.length - oldText.length;
  const remap = <M extends TextRange>(mark: M): M | null => (mark.end <= prefixLen ? mark : mark.start >= oldChangeEnd ? { ...mark, start: mark.start + delta, end: mark.end + delta } : null);
  const inline = state.inline.map(remap).filter((m): m is InlineMark => m !== null);
  const blocks = state.blocks.map(remap).filter((m): m is BlockMark => m !== null);
  return { text: nextText, inline, blocks };
}
function runForSegment(state: RichTextState, segStart: number, segEnd: number): KudosRun {
  const text = state.text.slice(segStart, segEnd);
  const active = state.inline.filter((m) => m.start <= segStart && m.end >= segEnd);
  const mention = active.find((m) => m.kind === "mention");
  if (mention) return { type: "mention", sunnerId: mention.sunnerId ?? 0, label: mention.label ?? "" };
  const link = active.find((m) => m.kind === "link");
  if (link) return { type: "link", text, href: link.href ?? "" };
  const bold = active.some((m) => m.kind === "bold") ? { bold: true as const } : {};
  const italic = active.some((m) => m.kind === "italic") ? { italic: true as const } : {};
  const strike = active.some((m) => m.kind === "strike") ? { strike: true as const } : {};
  return { type: "text", text, ...bold, ...italic, ...strike };
}
function runsForLine(state: RichTextState, line: TextRange): KudosRun[] {
  if (line.start === line.end) return [{ type: "text", text: "" }];
  const boundaries = new Set<number>([line.start, line.end]);
  for (const m of state.inline) {
    if (m.end <= line.start || m.start >= line.end) continue;
    boundaries.add(Math.max(m.start, line.start));
    boundaries.add(Math.min(m.end, line.end));
  }
  const points = [...boundaries].sort((a, b) => a - b);
  const runs: KudosRun[] = [];
  for (let i = 0; i < points.length - 1; i++) if (points[i] < points[i + 1]) runs.push(runForSegment(state, points[i], points[i + 1]));
  return runs.length > 0 ? runs : [{ type: "text", text: "" }];
}
/** Splits `text` on `\n`; each line's block type comes from `blocks` overlap, default `paragraph`. */
export function serializeToDoc(state: RichTextState): KudosDoc {
  const blocks: KudosBlock[] = lineRangesOf(state.text).map((line) => {
    const runs = runsForLine(state, line);
    const kind = state.blocks.find((m) => m.start === line.start && m.end === line.end)?.kind;
    if (kind === "ordered-list-item") return { type: "ordered-list-item" as const, runs };
    return kind === "quote" ? { type: "quote" as const, runs } : { type: "paragraph" as const, runs };
  });
  return { blocks };
}
/** The validation + fallback source: reconstructs plain text from a doc, mentions rendered as `@label`. */
export function docToPlainText(doc: KudosDoc): string {
  return doc.blocks.map((b) => b.runs.map((r) => (r.type === "mention" ? `@${r.label}` : r.text)).join("")).join("\n");
}
function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}
function isAcceptedLinkScheme(href: string): boolean {
  try {
    return (ACCEPTED_LINK_SCHEMES as readonly string[]).includes(new URL(href).protocol);
  } catch { return false; }
}
const BLOCK_TYPES = new Set(["paragraph", "ordered-list-item", "quote"]);
function parseRun(raw: unknown): KudosRun | null {
  if (!isRecord(raw) || typeof raw.type !== "string") return null;
  if (raw.type === "text" && typeof raw.text === "string") {
    const bold = raw.bold === true ? { bold: true as const } : {};
    const italic = raw.italic === true ? { italic: true as const } : {};
    const strike = raw.strike === true ? { strike: true as const } : {};
    return { type: "text", text: raw.text, ...bold, ...italic, ...strike };
  }
  if (raw.type === "link" && typeof raw.text === "string" && typeof raw.href === "string") {
    return isAcceptedLinkScheme(raw.href) ? { type: "link", text: raw.text, href: raw.href } : null;
  }
  if (raw.type === "mention" && typeof raw.sunnerId === "number" && Number.isFinite(raw.sunnerId) && typeof raw.label === "string") {
    return { type: "mention", sunnerId: raw.sunnerId, label: raw.label };
  }
  return null;
}
function parseBlock(raw: unknown): KudosBlock | null {
  if (!isRecord(raw) || typeof raw.type !== "string" || !BLOCK_TYPES.has(raw.type) || !Array.isArray(raw.runs)) return null;
  const runs: KudosRun[] = [];
  for (const rawRun of raw.runs) {
    const run = parseRun(rawRun);
    if (!run) return null;
    runs.push(run);
  }
  return { type: raw.type as KudosBlock["type"], runs };
}
/** Untrusted-input boundary for `kudos.message` (`message_format === 'doc'`); `null` on any structural surprise. */
export function parseKudosDoc(raw: string): KudosDoc | null {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  if (!isRecord(parsed) || !Array.isArray(parsed.blocks)) return null;
  const blocks: KudosBlock[] = [];
  for (const rawBlock of parsed.blocks) {
    const block = parseBlock(rawBlock);
    if (!block) return null;
    blocks.push(block);
  }
  return { blocks };
}
