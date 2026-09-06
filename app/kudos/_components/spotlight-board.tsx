"use client";

import { useMemo, useRef, useState } from "react";
import Image from "next/image";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { SpotlightNodeView, SpotlightTickerRowView } from "@/lib/kudos/view-model";

import { IconExpand, IconPanZoom, IconSearch } from "./kudos-icons";
import { layoutSpotlightNodes } from "./spotlight-layout";
import { SpotlightTicker } from "./spotlight-ticker";
import { SpotlightWordCloud } from "./spotlight-word-cloud";

const DRAG_THRESHOLD_PX = 4;

interface SpotlightBoardCopy {
  eyebrow: string;
  heading: string;
  board: Dictionary["kudos"]["spotlightBoard"];
}

/**
 * mm:2940:14170 (Frame 552) → mm:2940:13476 (B.6_Header) +
 * mm:2940:14174 (B.7_Spotlight). The only "use client" file in this phase
 * (plan.md Non-functional) — search/pan/zoom/expand state lives here, the
 * layout is memoised so a re-render never reshuffles the word cloud
 * (hydration-safety precedent: award-category-nav.tsx:24-29). `total` is a
 * seeded DB value (test-contract.md ratification 2026-09-06c), never
 * computed here and never sourced from the dictionary.
 */
export function SpotlightBoard({
  nodes,
  ticker,
  total,
  copy,
}: {
  nodes: SpotlightNodeView[];
  ticker: SpotlightTickerRowView[];
  total: number;
  copy: SpotlightBoardCopy;
}) {
  const [query, setQuery] = useState("");
  const [panZoomOn, setPanZoomOn] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef<{ startX: number; startY: number; originX: number; originY: number } | null>(null);

  // Pure + memoised — same node ids, same layout, every render, on the
  // server and in the browser (spotlight-layout.ts).
  const positions = useMemo(() => layoutSpotlightNodes(nodes.map((node) => node.id)), [nodes]);

  const filteredNodes = query.trim() === "" ? nodes : nodes.filter((node) => node.name.includes(query));

  function onPointerDown(event: React.PointerEvent<HTMLDivElement>) {
    if (!panZoomOn) return;
    drag.current = { startX: event.clientX, startY: event.clientY, originX: pan.x, originY: pan.y };
  }

  function onPointerMove(event: React.PointerEvent<HTMLDivElement>) {
    if (!drag.current) return;
    const dx = event.clientX - drag.current.startX;
    const dy = event.clientY - drag.current.startY;
    if (Math.abs(dx) < DRAG_THRESHOLD_PX && Math.abs(dy) < DRAG_THRESHOLD_PX) return;
    setPan({ x: drag.current.originX + dx, y: drag.current.originY + dy });
  }

  function onPointerUp() {
    drag.current = null;
  }

  return (
    // mm:2940:14170 (Frame 552)
    <section data-testid="spotlight-section" className="relative flex w-full flex-col gap-6 px-6 sm:px-12 lg:px-36">
      {/* mm:2940:13477 */}
      <p className="text-sm font-semibold tracking-[0.15px] text-white/70">{copy.eyebrow}</p>
      {/* mm:2940:13480 */}
      <h2 className="text-[36px] leading-[44px] font-bold tracking-[-0.25px] text-[#FFEA9E] sm:text-[57px] sm:leading-[64px]">
        {copy.heading}
      </h2>

      {/* mm:2940:14174 (B.7_Spotlight) */}
      <div
        data-testid="spotlight-board"
        className={`relative overflow-hidden rounded-[47px] border border-[#998C5F] bg-[#00101A] ${
          expanded ? "fixed inset-4 z-50" : "aspect-[1157/548] w-full"
        }`}
      >
        {/* mm:2940:14173 (Root further mo rong 1) */}
        <Image src="/images/kudos/spotlight-canvas.png" alt="" aria-hidden fill className="object-cover" />
        {/* mm:2940:14173 — linear-gradient(0deg, rgba(0,0,0,.70) 0%, rgba(0,0,0,.70) 100%) */}
        <div aria-hidden className="absolute inset-0 bg-black/70" />

        {/* mm:2940:13479 header row — count + search */}
        <div className="relative z-10 flex items-center justify-between gap-4 p-6">
          {/* mm:3007:17482 */}
          <p
            data-testid="spotlight-count"
            className="text-[28px] leading-9 font-bold text-white sm:text-[36px] sm:leading-[44px]"
          >
            {total} KUDOS
          </p>
          {/* mm:2940:14833 (B.7.3_Tìm kiếm sunner) */}
          <label className="flex items-center gap-2 rounded-full border border-[#998C5F] bg-[rgba(255,234,158,0.1)] px-3 py-2">
            {/* mm:I2940:14833;186:2758 */}
            <IconSearch aria-hidden width={16} height={16} className="shrink-0 text-white" />
            <input
              data-testid="spotlight-search"
              type="text"
              maxLength={100}
              placeholder={copy.board.searchPlaceholder}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="w-32 bg-transparent text-sm font-bold text-white placeholder:text-white/70 focus:outline-none sm:w-48"
            />
          </label>
        </div>

        {/* mm:2940:14174 word-cloud layer, panned/zoomed via CSS transform */}
        <div
          className="relative z-10 h-[calc(100%-88px)] w-full touch-none"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerLeave={onPointerUp}
          style={{ transform: `translate(${pan.x}px, ${pan.y}px)`, cursor: panZoomOn ? "grab" : "default" }}
        >
          {filteredNodes.length > 0 ? (
            <SpotlightWordCloud nodes={filteredNodes} positions={positions} />
          ) : (
            // mm:2940:14174 (empty state, no match)
            <p data-testid="spotlight-empty" className="p-6 text-sm text-white/70">
              {copy.board.empty}
            </p>
          )}
        </div>

        {/* mm:3004:15999 ticker band */}
        <div className="absolute bottom-16 left-6 z-10">
          <SpotlightTicker rows={ticker} suffix={copy.board.tickerSuffix} />
        </div>

        {/* mm:3007:17479 (B.7.2_Pan zoom) */}
        <button
          type="button"
          data-testid="spotlight-panzoom"
          title="Pan/Zoom"
          aria-pressed={panZoomOn}
          onClick={() => setPanZoomOn((value) => !value)}
          className="absolute right-16 bottom-6 z-10 flex h-[30px] w-[30px] items-center justify-center rounded-full border border-[#998C5F] bg-[#00101A] text-white"
        >
          <IconPanZoom aria-hidden width={18} height={18} />
        </button>

        {/* mm:2940:14174 expand glyph, bottom-right */}
        <button
          type="button"
          data-testid="spotlight-expand"
          aria-pressed={expanded}
          onClick={() => setExpanded((value) => !value)}
          className="absolute right-6 bottom-6 z-10 flex h-[30px] w-[30px] items-center justify-center rounded-full border border-[#998C5F] bg-[#00101A] text-white"
        >
          <IconExpand aria-hidden width={18} height={18} />
        </button>
      </div>
    </section>
  );
}
