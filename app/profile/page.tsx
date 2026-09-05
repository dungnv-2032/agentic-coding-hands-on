import type { Metadata } from "next";

import { ComingSoon } from "@/app/_components/coming-soon";

export const metadata: Metadata = { title: "Profile — Sun* Annual Awards 2025" };

/**
 * Declared placeholder (phase 07, clarifications.md "Account menu"): the
 * profile screen isn't built yet. The route stays public — there is no
 * protected content behind it, and `proxy.ts` guards exactly `/todo` and
 * `/login` (BR-001); adding a guard here is out of scope for this phase.
 */
export default function Page() {
  return <ComingSoon />;
}
