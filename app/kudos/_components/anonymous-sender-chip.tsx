import Image from "next/image";

/**
 * The sender-position chip for an anonymous kudos (A3: anonymity hides the
 * giver, never the receiver — the receiver chip is untouched).
 *
 * Frame `p9vFVBE_tc` ("Ẩn danh") carries zero authored spec items
 * (design-source-analysis.md § 10), so this component invents nothing: it
 * echoes `sunner-chip.tsx`'s measured sender-slot shell verbatim (wrapper,
 * avatar box, name typography — same `mm:` citations as their source) and
 * simply omits the department row, the tier badge, and the `/profile`
 * link, rather than fabricating values with no design source (phase-05
 * spec § Key Insights #5).
 *
 * Deliberately renders no `data-testid="kudos-sender"`. F004's K-9 reads
 * that hook off `.first()`, which is always a highlight card and therefore
 * never anonymous (0 hearts by construction) — so omitting the testid here
 * cannot move K-9, and emitting it would make an anonymous label look like
 * a profile link for someone who chose not to be named (phase-05 spec
 * § Key Insights #6).
 */
export function AnonymousSenderChip({ label }: { label: string }) {
  return (
    // mm:256:4858 (SunnerChip's measured wrapper, echoed)
    <div className="flex w-full min-w-0 max-w-xs flex-1 flex-col items-center justify-center gap-[13px] min-[1360px]:max-w-[235px]">
      {/* mm:256:4734 (MM_MEDIA_Avatar) — committed placeholder artwork, the
          design's own stand-in for an unavailable photo (F004 assumption A3). */}
      <Image
        src="/images/kudos/sample-avatar.png"
        alt=""
        width={64}
        height={64}
        className="h-16 w-16 shrink-0 rounded-full border-[1.869px] border-white object-cover"
      />
      <div className="flex w-full min-w-0 flex-col items-start gap-0.5">
        {/* mm:256:4735 (name typography, echoed) — plain span, not a Link:
            no `/profile` destination exists for an unnamed sender. */}
        <span className="w-full truncate text-center text-base leading-6 font-bold tracking-[0.15px] text-[#00101A]">
          {label}
        </span>
      </div>
    </div>
  );
}
