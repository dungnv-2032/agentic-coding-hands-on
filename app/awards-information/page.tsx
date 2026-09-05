import type { Metadata } from "next";

import { ComingSoon } from "@/app/_components/coming-soon";

export const metadata: Metadata = { title: "Award Information — Sun* Annual Awards 2025" };

/**
 * Declared placeholder (phase 07, clarifications.md "Screen scope"): the
 * award detail screen isn't built yet, but every homepage award-card and
 * nav link must resolve rather than 404 (ID-44/47-50/55/59).
 */
export default function Page() {
  return <ComingSoon />;
}
