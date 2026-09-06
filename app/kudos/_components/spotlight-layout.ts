/**
 * Deterministic word-cloud layout — clarifications.md "hand-rolled,
 * deterministic layout, no new dependency" + phase-08 Key Insight 1. A pure
 * function of the node id list: same input, same output, on the server and
 * in the browser, so hydration never mismatches (ALG-002). No `Math.random`,
 * no `Date.now`, no `window` read — a fixed-constant LCG (Numerical Recipes
 * multiplier) is the only source of pseudo-randomness, seeded per-id, so the
 * output does not depend on array order either. No imports — this file has
 * zero dependencies on purpose, so nothing it does can vary by environment.
 */

export type SpotlightTier = "lg" | "md" | "sm";

export interface SpotlightLayoutPoint {
  id: number;
  /** Percentage offsets (0-100) of the node's centre within the canvas box. */
  xPct: number;
  yPct: number;
  tier: SpotlightTier;
}

const SEED = 1988;
const TIERS: readonly SpotlightTier[] = ["lg", "md", "sm"];

/** One Numerical-Recipes LCG step. Deterministic, no external entropy. */
function step(state: number): number {
  return (Math.imul(state, 1664525) + 1013904223) >>> 0;
}

/**
 * Places each id on a coarse grid sized to the id count, then jitters the
 * cell with LCG draws seeded from the id itself (not the array index), and
 * picks a size tier the same way. Call this inside `useMemo` at the "use
 * client" call site so a re-render never reshuffles the cloud.
 */
export function layoutSpotlightNodes(ids: readonly number[]): SpotlightLayoutPoint[] {
  if (ids.length === 0) return [];

  const columns = Math.max(1, Math.ceil(Math.sqrt(ids.length * 1.6)));
  const rows = Math.max(1, Math.ceil(ids.length / columns));
  const cellWidth = 100 / columns;
  const cellHeight = 100 / rows;

  return ids.map((id, index) => {
    let state = step(SEED + id);
    const jitterX = state / 0xffffffff;
    state = step(state);
    const jitterY = state / 0xffffffff;
    state = step(state);
    const tier = TIERS[state % TIERS.length];

    const col = index % columns;
    const row = Math.floor(index / columns);

    return {
      id,
      xPct: col * cellWidth + cellWidth * 0.2 + jitterX * cellWidth * 0.6,
      yPct: row * cellHeight + cellHeight * 0.2 + jitterY * cellHeight * 0.6,
      tier,
    };
  });
}
