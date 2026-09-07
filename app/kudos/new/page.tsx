import type { Metadata } from "next";

import { signOut } from "@/app/_actions/auth";
import { getPageContext } from "@/app/_page-context";
import { montserrat } from "@/app/_fonts";
import { HomeHeader } from "@/app/_components/home-header";
import { SiteFooter } from "@/app/_components/site-footer";
import { getComposeOptions } from "@/lib/kudos/compose-options";

import { createKudos } from "./_actions/create-kudos";
import { uploadKudosImage } from "./_actions/upload-kudos-image";
import { ComposeForm } from "./_components/compose-form";

export const metadata: Metadata = { title: "Sun* Kudos New — Sun* Annual Awards 2025" };

/**
 * SCR Viết KUDO — `/kudos/new` (MoMorph `ihQ26W78P2`, frame `520:11602`).
 * Replaces the `ComingSoon` placeholder; this is the cutover phase (12) that
 * joins the two tracks built in phases 01–11.
 *
 * Auth-guarded (`proxy.ts`, ID-1) — writing a Kudos needs an identity, unlike
 * the public read surface at `/kudos`. Composition mirrors `app/kudos/page.tsx`:
 * `getPageContext()` is the single read of locale + session, and only its
 * booleans cross into `HomeHeader` (`isAuthenticated`/`isAdmin`) — the
 * Supabase `user` object never does (`app/_page-context.ts:22-25`). No
 * `FloatingWidget`, no `KudosPromo` — the frame shows neither
 * (clarifications.md § Shared chrome).
 *
 * `createKudos` and `uploadKudosImage` (Track B, phase 07) are passed down to
 * `ComposeForm` as props — the same "Server Action as a prop" pattern shipped
 * for `signOutAction`/`toggleLike` — so no Track A component under
 * `_components/` imports either action directly, which is what let the two
 * tracks build in parallel.
 */
export default async function KudosComposePage() {
  const [{ locale, dictionary, isAuthenticated, isAdmin }, options] = await Promise.all([
    getPageContext(),
    getComposeOptions(),
  ]);

  return (
    <div className={`${montserrat.variable} flex min-h-svh w-full flex-col bg-[#00101A] font-montserrat`}>
      <HomeHeader
        locale={locale}
        dictionary={dictionary}
        isAuthenticated={isAuthenticated}
        isAdmin={isAdmin}
        signOutAction={signOut}
      />
      <main className="flex flex-1 flex-col">
        <ComposeForm
          copy={dictionary.kudosCompose}
          options={options}
          createKudos={createKudos}
          uploadKudosImage={uploadKudosImage}
        />
      </main>
      <SiteFooter dictionary={dictionary} />
    </div>
  );
}
