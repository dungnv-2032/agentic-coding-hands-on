import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";

import { signOut } from "@/app/_actions/auth";
import { HomeHeader } from "@/app/_components/home-header";
import { SiteFooter } from "@/app/_components/site-footer";
import { montserrat, montserratAlternates } from "@/app/_fonts";
import { getPageContext } from "@/app/_page-context";
import { toggleKudosLike } from "@/app/kudos/_actions/toggle-kudos-like";
import { resolveViewer } from "@/lib/kudos/viewer";
import { getProfileData } from "@/lib/profile/profile-data";
import { resolveProfileId } from "@/lib/profile/resolve-profile-id";
import { createClient } from "@/lib/supabase/server";

import { fetchProfileKudosPage } from "./_actions/fetch-profile-kudos-page";
import { KudosDirectionSection } from "./_components/kudos-direction-section";
import { ProfileHero } from "./_components/profile-hero";
import { ProfileStatsCard } from "./_components/profile-stats-card";
import { WriteKudoBar } from "./_components/write-kudo-bar";

export const metadata: Metadata = { title: "Profile — Sun* Annual Awards 2025" };

/**
 * SCR006 — `/profile[?id=N]`, the "Profile bản thân" screen (MoMorph
 * `3FoIx6ALVb`, frame `362:5037`). Replaces the `ComingSoon` placeholder this
 * route shipped with.
 *
 * This page COMPOSES; it holds no layout of its own beyond the region rhythm
 * below (phases 07/08 own every measured value) and no client state (phase
 * 08's `KudosDirectionSection` is the one client boundary, and it resolves its
 * own `onHashtagClick`/`onCopyLink` — a Server Component cannot hand an event
 * handler across that boundary at all in this Next version, see
 * `next/dist/docs/01-app/02-guides/server-and-client-boundary.md`).
 *
 * **Layer two of the guard (FR-102/PERM011).** `proxy.ts` redirects an
 * unauthenticated request before this file runs; the page re-resolves the
 * session itself and redirects again on absence, so the guard survives a
 * future edit to the proxy's route list. TC_ACC_001 asks for exactly this.
 *
 * **The call order is forced by a dependency, not a preference:**
 * `resolveProfileId()` needs the viewer's own `sunners.id` to canonicalise
 * `?id={me}` to the self view (FUN_002), and `getProfileData()` needs the
 * resolved target. Only the three request reads that do not depend on each
 * other share a `Promise.all`.
 *
 * FR-603 — only `isAuthenticated`/`isAdmin` and the `ProfileViewModel` cross
 * into a Client Component. The Supabase `user` object never does, and neither
 * does `viewer.userId`. On another Sunner's profile `stats` and `counts.sent`
 * are `null` at the DATA layer (SEC_001), so the sent count is absent from
 * the props rather than hidden in them.
 */
export default async function ProfilePage(props: PageProps<"/profile">) {
  const supabase = await createClient();
  const [{ locale, dictionary, isAuthenticated, isAdmin }, viewer, searchParams] =
    await Promise.all([getPageContext(), resolveViewer(supabase), props.searchParams]);

  if (!viewer.isAuthenticated) redirect("/login");

  const resolution = resolveProfileId(searchParams?.id, viewer.sunnerId);
  // A malformed, repeated or non-numeric `?id=` never reaches a query
  // (FUN_001/FUN_004/FUN_005).
  if (resolution.kind === "not-found") notFound();

  // `self` maps to the viewer's OWN id, which is `null` exactly in the sparse
  // case (signed in, no `sunners` row — A4). Passing `null` for every self
  // view would cost a real Sunner their own statistics.
  const targetId = resolution.kind === "self" ? viewer.sunnerId : resolution.id;
  const result = await getProfileData(supabase, targetId, viewer);
  // A well-formed id with no `sunners` row: the 404 page, never a 500 and
  // never a half-rendered profile (FR-402/FUN_003). Both verdicts return
  // before a single component renders.
  if (result.kind === "not-found") notFound();

  const vm = result.model;
  const { kudos, profile } = dictionary;

  return (
    // mm:362:5037 — 1440×4660, page background #00101A.
    <div
      className={`${montserrat.variable} ${montserratAlternates.variable} flex min-h-svh w-full flex-col bg-[#00101A] font-montserrat`}
    >
      {/* The frame draws the 512px keyvisual from page `y0` and floats the
          header over it — `rgba(16,20,23,0.8)` is translucent precisely so the
          artwork reads through it. In normal flow a sticky header reserves its
          own height first, so the banner started at the header's BOTTOM edge:
          MEASURED 76px at 1440, 124px at 1024 and 768, 244px at 375, where the
          `flex-wrap` row breaks onto three lines. Any hardcoded pull-up would
          be wrong at three of those four widths, so the header leaves the flow
          instead — `fixed`, which is what `sticky top-0` already looks like at
          every scroll offset > 0 — and the banner lands on page `y0` with no
          header height written down anywhere.
          From `lg` up only: at 1024+ the header is at most 124px tall and the
          hero content starts 184px down (below), so the header can never reach
          it, while at 375px the header is 244px tall and MUST keep its own
          space. `contents` below `lg` leaves `HomeHeader` a direct child of
          this column, so its own `sticky` keeps a full-page containing block to
          travel in — a static wrapper exactly as tall as the header would pin
          it and it would scroll away. */}
      <div className="contents lg:fixed lg:inset-x-0 lg:top-0 lg:z-20 lg:block">
        <HomeHeader
          locale={locale}
          dictionary={dictionary}
          isAuthenticated={isAuthenticated}
          isAdmin={isAdmin}
          signOutAction={signOut}
        />
      </div>
      <main className="flex flex-1 flex-col">
        {/* mm:362:5052 — renders its own keyvisual (`mm:I1210:12622;2167:5140`);
            this page must not render it a second time.
            The hero owns the banner's datum (its own `pt-[184px]`, measured
            from the banner top); this page only decides where that datum
            lands, which is what taking the header out of the flow above
            does. */}
        <ProfileHero
          hero={vm.hero}
          badgeHeading={vm.isSelf ? profile.badges.headingSelf : profile.badges.headingOther}
          unlockedBadgeSlots={vm.unlockedBadgeSlots}
        />

        {/* mm:362:5073 — ONE data-level branch decides the whole B slot
            (SC-002): `stats` is non-null iff the viewer is looking at
            themselves, `writeKudoTargetId` iff they are not, so no component
            re-derives "is this me". The trailing `null` is unreachable under
            the frozen contract and is written out rather than forced with a
            `!`, which would be an assertion about data this file did not
            produce. `pt-16` is the only page-level spacing: the C section
            carries its own `py-16`, so both region gaps come out at 64px. */}
        <div className="w-full px-6 pt-16 sm:px-12 lg:px-36">
          {vm.stats !== null ? (
            <ProfileStatsCard copy={profile.stats} stats={vm.stats} />
          ) : vm.writeKudoTargetId !== null ? (
            <WriteKudoBar
              copy={profile.writeBar}
              targetName={vm.hero.fullName}
              targetSunnerId={vm.writeKudoTargetId}
            />
          ) : null}
        </div>

        {/* mm:362:5083 — regions C + D. `fetchProfileKudosPage` and
            `toggleKudosLike` travel as props, F004's "Server Action as a
            prop" idiom; no Track A file imports either directly.
            `targetSunnerId` is the RESOLVED target, and it is advisory: the
            action re-derives the `sent` direction's filter from the session
            and ignores this value there entirely (SC-003). */}
        <KudosDirectionSection
          targetSunnerId={targetId}
          isSelf={vm.isSelf}
          counts={vm.counts}
          initialPage={vm.initialPage}
          copy={{
            eyebrow: kudos.eyebrow,
            // FR-603 — every prop handed to a Client Component is serialized
            // into the RSC payload ("Props are serialized and sent to the
            // browser", `next/dist/docs/01-app/02-guides/data-security.md`), so
            // another Sunner's page shipped the static `Đã gửi ({count})`
            // string even though `counts.sent` is `null` there and the Sent
            // option is never built. The number never crossed and still does
            // not (SEC_001 holds at the data layer); this hands each face only
            // the copy it can render. `sentLabel` is a required string in
            // phase 08's frozen `KudosDirectionCopy`, so the label is emptied
            // rather than the contract widened — and the option that would
            // show it does not exist on this face.
            direction: vm.isSelf
              ? profile.direction
              : { receivedLabel: profile.direction.receivedLabel, sentLabel: "" },
            feed: profile.feed,
            card: kudos.card,
            toast: kudos.toast,
          }}
          fetchPage={fetchProfileKudosPage}
          toggleLike={toggleKudosLike}
        />
      </main>
      <SiteFooter dictionary={dictionary} />
    </div>
  );
}
