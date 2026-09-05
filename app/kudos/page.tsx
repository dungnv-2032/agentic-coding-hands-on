import type { Metadata } from "next";

import { ComingSoon } from "@/app/_components/coming-soon";

export const metadata: Metadata = { title: "Sun* Kudos — Sun* Annual Awards 2025" };

/**
 * Declared placeholder (phase 07, clarifications.md "Screen scope"): the
 * Sun* Kudos screen isn't built yet, but every homepage nav/CTA link must
 * resolve rather than 404 (ID-44/53/55/59).
 */
export default function Page() {
  return <ComingSoon />;
}
