import Image from "next/image";

/**
 * mm:I1210:12622;2167:5140 (`mms_3_Keyvisual`) — the 512px banner behind the
 * profile hero, plus its readability wash.
 *
 * Rendered BY `ProfileHero`, not by the page: both layers are absolutely
 * positioned at `-z-10` and only stay behind the hero's own content because
 * the hero section carries `relative isolate`. Placing this component
 * anywhere else (or a second time from `app/profile/page.tsx`) either paints
 * it behind the page's `bg-[#00101A]` root — where it is invisible — or
 * duplicates the banner.
 *
 * The banner is NOT an `MM_MEDIA_*` node: `get_media_files(3FoIx6ALVb)`
 * returns no URL for `I1210:12622;2167:5141`, because Figma holds it as an
 * inline image fill. It instances the same `2167:5141` component the Kudos
 * board's keyvisual does (`kudos-hero.tsx` renders it as
 * `I2940:13432;2167:5141`), so the shipped `kv-background.png` IS this
 * artwork — reused verbatim rather than re-exported or invented.
 *
 * `preload` replaces `priority`, deprecated in Next.js 16 in favour of the
 * explicit prop (`next/dist/docs/01-app/03-api-reference/02-components/image.md`).
 * This is the screen's LCP element, which is exactly what `preload` is for.
 */
export function ProfileKeyvisual() {
  return (
    <>
      {/* mm:I1210:12622;2167:5141 (image fill, `object-cover`-style crop of a
          taller source: background-size 101.245% 393.038%) */}
      <Image
        src="/images/kudos/kv-background.png"
        alt=""
        width={1440}
        height={512}
        preload
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[512px] w-full object-cover"
      />
      {/* mm:I1210:12622;1210:12612 (Cover) — this frame measures the wash at
          `8deg / 8.6% / 37.25%` (the board's is `25deg / 14.74% / 47.8%`).
          Figma draws the rect 957px tall from y445, i.e. mostly BELOW the
          banner where it fades into a page background of the identical
          `#00101A` and is provably invisible; it is scoped to the banner's own
          512px box here, the shape `kudos-hero.tsx` already ships. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[512px] w-full"
        style={{
          background: "linear-gradient(8deg, #00101A 8.6%, rgba(0, 19, 32, 0.00) 37.25%)",
        }}
      />
    </>
  );
}
