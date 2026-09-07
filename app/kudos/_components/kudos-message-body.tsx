import type { KudosBlock, KudosRun, MessageFormat } from "@/lib/kudos/compose-contract";
import { ACCEPTED_LINK_SCHEMES } from "@/lib/kudos/compose-contract";
import { parseKudosDoc } from "@/lib/kudos/rich-text";

/**
 * Renders `kudos.message` for the board card. `format !== "doc"` is F004's
 * unchanged plain-text path — this `<p>` is a verbatim move of the markup
 * that used to live inline in `kudos-card.tsx`, same `data-testid`, same
 * className, so `kudos-body`'s clamp and text-content assertions never
 * move (phase-05 spec § Key Insights #1).
 *
 * The `'doc'` path walks `parseKudosDoc`'s output into React elements —
 * never `dangerouslySetInnerHTML`, never an HTML string (clarifications.md
 * § Rich text). A parse failure (`null`) degrades to the same plain-text
 * render, which is the defensive-by-construction behavior for hostile or
 * malformed input reaching every anonymous visitor on the public board.
 *
 * Blocks are `<span className="block …">`, never `<div>`/`<ol>`, because
 * they render *inside* the single `<p data-testid="kudos-body">` — a block
 * element inside a `<p>` is invalid HTML and the browser would reparent it,
 * breaking both the clamp and the testid's text content (phase-05 spec
 * § Key Insights #2, § Risk Assessment row 1).
 *
 * No MoMorph node backs the doc-rendering styles below: rich text has no
 * Figma-authored surface anywhere in this file's screen (`compose-contract.ts`
 * header — "technical-spec.md § 4.2, verbatim" is prose, not a frame). The
 * only citable visual value is the body typography itself, which is the
 * exact class string carried over from `kudos-card.tsx:158-163` (mm:256:5156).
 * Quote/list treatment below is a minimal, undecorated extension of that
 * typography — no invented color, spacing scale, or new visual language.
 */
export function KudosMessageBody({
  message,
  format,
  clamp,
}: {
  message: string;
  format: MessageFormat;
  clamp: string;
}) {
  const doc = format === "doc" ? parseKudosDoc(message) : null;

  return (
    // mm:256:5156 — same testid/className as F004's shipped `<p>`; the doc
    // path renders its blocks as children of this same element instead of
    // a plain string.
    <p
      data-testid="kudos-body"
      className={`text-justify text-xl leading-8 font-bold text-[#00101A] ${clamp}`}
    >
      {doc ? renderBlocks(doc.blocks) : message}
    </p>
  );
}

/** Re-checks the link scheme at render time — a second, independent layer
 * on top of `parseKudosDoc`'s own allow-list check, per BR-004's
 * defense-in-depth reasoning (phase-05 spec § Key Insights #3). */
function isAllowedLinkHref(href: string): boolean {
  try {
    return (ACCEPTED_LINK_SCHEMES as readonly string[]).includes(new URL(href).protocol);
  } catch {
    return false;
  }
}

function renderTextRun(run: Extract<KudosRun, { type: "text" }>, key: number) {
  let node: React.ReactNode = run.text;
  if (run.strike) node = <s>{node}</s>;
  if (run.italic) node = <em>{node}</em>;
  if (run.bold) node = <strong>{node}</strong>;
  return <span key={key}>{node}</span>;
}

function renderRun(run: KudosRun, key: number) {
  if (run.type === "text") return renderTextRun(run, key);
  if (run.type === "mention") {
    // Stored label is printed, never re-resolved (clarifications.md § Rich
    // text — a renamed sunner does not retroactively change past kudos).
    return (
      <span key={key} className="font-bold">
        @{run.label}
      </span>
    );
  }
  // run.type === "link" — scheme failure degrades to a plain span, never an
  // `<a>`, so a hand-built object bypassing the parser still cannot emit an
  // unsafe href.
  if (!isAllowedLinkHref(run.href)) return <span key={key}>{run.text}</span>;
  const isHttp = run.href.startsWith("http:") || run.href.startsWith("https:");
  return (
    <a
      key={key}
      href={run.href}
      className="underline"
      {...(isHttp ? { target: "_blank", rel: "noopener noreferrer" } : {})}
    >
      {run.text}
    </a>
  );
}

function renderBlock(block: KudosBlock, key: number, ordinal: number) {
  const runs = block.runs.map((run, i) => renderRun(run, i));
  if (block.type === "ordered-list-item") {
    return (
      <span key={key} className="block">
        {`${ordinal}. `}
        {runs}
      </span>
    );
  }
  if (block.type === "quote") {
    return (
      <span key={key} className="block border-l-2 border-[#00101A]/30 pl-3 italic">
        {runs}
      </span>
    );
  }
  return (
    <span key={key} className="block">
      {runs}
    </span>
  );
}

/** Ordered-list ordinals restart after any non-list block, mirroring how a
 * real `<ol>` would break across paragraphs/quotes. */
function renderBlocks(blocks: readonly KudosBlock[]) {
  let ordinal = 0;
  return blocks.map((block, index) => {
    ordinal = block.type === "ordered-list-item" ? ordinal + 1 : 0;
    return renderBlock(block, index, ordinal);
  });
}
