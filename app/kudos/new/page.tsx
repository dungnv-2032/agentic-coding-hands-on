import type { Metadata } from "next";

import { ComingSoon } from "@/app/_components/coming-soon";

export const metadata: Metadata = { title: "Sun* Kudos New — Sun* Annual Awards 2025" };

/**
 * Declared placeholder (phase 01, clarifications.md § "compose bar → Viết
 * Kudo"): the compose surface is its own commission. This route only needs
 * to resolve rather than 404 so the Kudos Live Board's compose CTA is a
 * real link (K-21, K-22).
 */
export default function Page() {
  return <ComingSoon />;
}
