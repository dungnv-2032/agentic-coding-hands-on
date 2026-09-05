import type { Metadata } from "next";

import { ComingSoon } from "@/app/_components/coming-soon";

export const metadata: Metadata = { title: "General Standards — Sun* Annual Awards 2025" };

/**
 * Declared placeholder (phase 07, clarifications.md "Screen scope"): the
 * "Tiêu chuẩn chung" screen isn't built yet, but the footer link and the
 * widget's standards shortcut must resolve rather than 404 (ID-55/59).
 */
export default function Page() {
  return <ComingSoon />;
}
