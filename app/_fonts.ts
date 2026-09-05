import { Montserrat, Montserrat_Alternates } from "next/font/google";

/**
 * Shared Montserrat / Montserrat Alternates instances for every screen from
 * phase 06 onward (plan.md integration contract). `--font-montserrat` /
 * `--font-montserrat-alternates` are already wired into `globals.css`'s
 * `@theme inline` block.
 *
 * `/login` (F001_Login) keeps its own separate `next/font/google` call with
 * the same config — deliberately not consolidated here, since that file is
 * out of this phase's ownership and the plan says not to refactor it.
 */
export const montserrat = Montserrat({
  variable: "--font-montserrat",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "700"],
});

export const montserratAlternates = Montserrat_Alternates({
  variable: "--font-montserrat-alternates",
  subsets: ["latin"],
  weight: ["700"],
});
