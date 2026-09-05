import type { Metadata } from "next";

import { ComingSoon } from "@/app/_components/coming-soon";

export const metadata: Metadata = { title: "Admin Dashboard — Sun* Annual Awards 2025" };

/**
 * Declared placeholder (clarifications.md ORCH-11): the role-gated Admin
 * Dashboard account-menu item points here. A link that 404s is a defect
 * even though only admins see the menu item and ID-5/37 are skipped
 * (ORCH-03) — the screen still isn't built, so this stays a placeholder,
 * not a stand-in that pretends to check the admin role.
 */
export default function Page() {
  return <ComingSoon />;
}
