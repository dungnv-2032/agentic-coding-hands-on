import type { Metadata } from "next";

import { ComingSoon } from "@/app/_components/coming-soon";

export const metadata: Metadata = { title: "Sun* Kudos Detail — Sun* Annual Awards 2025" };

/**
 * Declared placeholder (phase 01, clarifications.md § "Xem chi tiết/card
 * body → View Kudo"): its own commission, not a detail screen. Deliberately
 * ignores `params` — no `params.id` is read or echoed into the DOM (no
 * reflected-content surface on a route that renders for any arbitrary
 * path). Resolves rather than 404s so `kudos-detail-link`/`kudos-edit`/
 * `spotlight-node` are real links (K-21).
 */
export default function Page() {
  return <ComingSoon />;
}
