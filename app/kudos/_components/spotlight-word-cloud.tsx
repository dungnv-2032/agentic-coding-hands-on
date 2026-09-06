import Link from "next/link";

import type { SpotlightNodeView } from "@/lib/kudos/view-model";

import type { SpotlightLayoutPoint, SpotlightTier } from "./spotlight-layout";

const TIER_TEXT: Record<SpotlightTier, string> = {
  lg: "text-[28px] leading-8",
  md: "text-[20px] leading-6",
  sm: "text-[14px] leading-5",
};

/**
 * mm:2940:14174 (B.7_Spotlight) node layer — the seven verbatim names
 * (clarifications § "Resolved from source data"), tiled here at three size
 * tiers per the layout the "use client" parent memoised. Plain function, no
 * hooks — positions arrive pre-computed so this file never needs its own
 * client boundary (phase-08 Non-functional: one "use client" file total).
 * Every node is a real `<a href="/kudos/<id>">` (plan.md Key Insight 5) —
 * never `href="#"`; `kudosId` is non-optional in the frozen contract.
 */
export function SpotlightWordCloud({
  nodes,
  positions,
}: {
  nodes: SpotlightNodeView[];
  positions: SpotlightLayoutPoint[];
}) {
  const pointById = new Map(positions.map((point) => [point.id, point]));

  return (
    <div className="relative h-full w-full">
      {nodes.map((node) => {
        const point = pointById.get(node.id);
        if (!point) return null;

        return (
          // mm:2995:15926 (name text — Montserrat 700, tiled at three tiers)
          <Link
            key={node.id}
            data-testid="spotlight-node"
            href={`/kudos/${node.kudosId}`}
            title={`${node.name} ${node.receivedAtLabel}`}
            style={{ left: `${point.xPct}%`, top: `${point.yPct}%` }}
            className={`absolute -translate-x-1/2 -translate-y-1/2 font-bold whitespace-nowrap transition-colors hover:opacity-80 ${TIER_TEXT[point.tier]} ${
              node.isJustUpdated ? "text-[#D4271D]" : "text-white"
            }`}
          >
            {node.name}
          </Link>
        );
      })}
    </div>
  );
}
