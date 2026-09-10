import type { Metadata } from "next";

import { openSecretBox } from "@/app/kudos/secret-box/_actions/open-secret-box";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { LOCALE_COOKIE, resolveLocale } from "@/lib/i18n/locales";
import { resolveViewer } from "@/lib/kudos/viewer";
import { fetchUnopenedCount } from "@/lib/secret-box/queries";
import { createClient } from "@/lib/supabase/server";
import { cookies } from "next/headers";

import { SecretBoxDismiss } from "./_components/secret-box-dismiss";
import { SecretBoxOpener } from "./_components/secret-box-opener";
import { SecretBoxPanel } from "./_components/secret-box-panel";

export const metadata: Metadata = { title: "Sun* Kudos Secret Box — Sun* Annual Awards 2025" };

/**
 * mm:1466:7676 — Open secret box (chưa mở), F009, screen `J3-4YFIpMM`.
 * Replaces the `ComingSoon` placeholder this route carried since F004.
 *
 * ## The three-way state is decided HERE, once
 *
 * Everything below the page resolves to two booleans plus a number
 * (`canOpen`, `showSignIn`, `unopenedCount`), so no component re-derives
 * identity and the panel cannot disagree with the opener about whether a
 * box is openable:
 *
 * - **no session** → `showSignIn`, count `00`, box inert (FR-105)
 * - **session with no `sunners` row** → same inert face, but no sign-in
 *   nudge: the visitor IS signed in, so offering them a login is a lie.
 *   They simply hold no boxes (`fetchUnopenedCount` never runs — there is
 *   no roster row to read).
 * - **session with a roster row** → `canOpen` iff the count is above zero
 *   (FR-202)
 *
 * `resolveViewer()` and NOT `resolveSidebarSunnerId()`: the latter falls
 * back to the seeded frame viewer for sessions with no roster row, which on
 * the board is a harmless display default and here would show a visitor
 * someone else's boxes and invite them to open them.
 *
 * ## No route guard, deliberately
 *
 * `proxy.ts` leaves `/kudos/secret-box` public — F004's ratified contract,
 * asserted by e2e K-21 — so this page must resolve 200 for everyone
 * (FR-001). Entitlement is enforced by the inert face above plus, at the
 * only point that actually matters, the database: `open_secret_box()`'s
 * EXECUTE grant is revoked from `anon` outright. A disabled control is a
 * courtesy; the grant is the boundary.
 *
 * ## Why `<main>` wraps the panel
 *
 * DEC-02. The panel owns the page's only `<h1>`, and it has to sit INSIDE
 * `<main>`: K-21 asserts `main h1`, and `/standards` — whose shell is
 * otherwise the closest precedent — puts its heading outside an empty
 * `<main>`. Copying that shape would break a shipped assertion.
 *
 * No header and no footer: the frame draws a standalone card and the close
 * glyph is its only exit.
 */
export default async function Page() {
  const [supabase, cookieStore] = await Promise.all([createClient(), cookies()]);
  const viewer = await resolveViewer(supabase);

  const dictionary = getDictionary(resolveLocale(cookieStore.get(LOCALE_COOKIE)?.value));
  const copy = dictionary.secretBox;

  const unopenedCount =
    viewer.sunnerId === null ? 0 : await fetchUnopenedCount(supabase, viewer.sunnerId);

  const canOpen = viewer.sunnerId !== null && unopenedCount > 0;
  const showSignIn = !viewer.isAuthenticated;

  return (
    <main className="flex min-h-svh w-full items-center justify-center bg-[#00101A] px-4 py-8">
      <SecretBoxPanel
        copy={copy}
        canOpen={canOpen}
        showSignIn={showSignIn}
        unopenedCount={unopenedCount}
        closeSlot={<SecretBoxDismiss label={copy.closeLabel} />}
        boxSlot={<SecretBoxOpener canOpen={canOpen} copy={copy} openAction={openSecretBox} />}
      />
    </main>
  );
}
