import Image from "next/image";
import Link from "next/link";

import type { Dictionary } from "@/lib/i18n/dictionaries";

/**
 * Item 6 — floating widget button (`mms_6_Widget Button`, node
 * `5022:15169`): a fixed bottom-right pill holding two direct links split
 * by a "/" glyph — no quick-action menu (clarifications.md: the design's
 * own node names, "icon viết kudos" → `/kudos` and "icon thể lệ saa" →
 * `/standards`, settle it). `fixed` keeps it overlaying R4-R6 regardless of
 * scroll position; the aria-labels use the widget's own dictionary copy so
 * they never collide with the hero's "ABOUT KUDOS" button name.
 */
export function FloatingWidget({ widget }: { widget: Dictionary["home"]["widget"] }) {
  return (
    // mm:5022:15169
    <div className="fixed right-6 bottom-6 z-30 flex items-center gap-2 rounded-full bg-[#FFEA9E] px-4 py-4 shadow-[0_4px_4px_rgba(0,0,0,0.25),0_0_6px_#FAE287]">
      {/* mm:I5022:15169;214:3839;186:1763 (MM_MEDIA_Pen) */}
      <Link href="/kudos" aria-label={widget.writeKudos} className="flex h-6 w-6 items-center justify-center">
        <Image src="/images/home/widget-pen-icon.svg" alt="" aria-hidden width={24} height={24} />
      </Link>
      {/* mm:I5022:15169;214:3839;186:1568 — "/" separator */}
      <span aria-hidden className="text-2xl leading-8 font-bold text-[#00101A]">
        /
      </span>
      {/* mm:I5022:15169;214:3839;186:1766 (MM_MEDIA_Kudos Logo) */}
      <Link
        href="/standards"
        aria-label={widget.standards}
        className="flex h-5 w-5 items-center justify-center"
      >
        <Image src="/images/home/widget-saa-kudos-glyph.svg" alt="" aria-hidden width={20} height={19} />
      </Link>
    </div>
  );
}
