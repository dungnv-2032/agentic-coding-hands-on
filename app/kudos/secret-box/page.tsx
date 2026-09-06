import type { Metadata } from "next";

import { ComingSoon } from "@/app/_components/coming-soon";

export const metadata: Metadata = { title: "Sun* Kudos Secret Box — Sun* Annual Awards 2025" };

/**
 * Declared placeholder (phase 01, clarifications.md § "Mở Secret Box →
 * Open secret box- chưa mở"): its own commission. Resolves rather than
 * 404s so the sidebar's `secret-box-button` is a real link (K-21).
 */
export default function Page() {
  return <ComingSoon />;
}
