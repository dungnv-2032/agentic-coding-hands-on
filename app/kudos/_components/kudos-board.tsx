"use client";

import { useSearchParams } from "next/navigation";
import { Fragment, useCallback, useMemo, useRef, useState, type ReactNode } from "react";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import { matchesFilters } from "@/lib/kudos/derive";
import type {
  FilterOptionView,
  KudosBoardViewModel,
  ToggleKudosLike,
} from "@/lib/kudos/view-model";

import { AllKudosSection } from "./all-kudos-section";
import { HighlightCarousel } from "./highlight-carousel";
import { KudosFilterBar } from "./kudos-filter-bar";
import { KudosToast } from "./kudos-toast";

interface KudosBoardCopy {
  eyebrow: string;
  sections: { highlight: string; allKudos: string };
  filters: { hashtag: string; department: string };
  card: Dictionary["kudos"]["card"];
  toast: Dictionary["kudos"]["toast"];
}

const SECTION_HEADING_CLASS =
  "text-[32px] leading-[40px] font-bold tracking-[-0.25px] text-[#FFEA9E] sm:text-[57px] sm:leading-[64px]";

/**
 * mm:2940:13451 (B_Highlight) + mm:2940:13475 (C_All kudos) — phase 07's
 * single client boundary (plan.md § Key Insight 1): filter selection,
 * carousel paging, infinite-scroll pages, and the toast live here so
 * HIGHLIGHT KUDOS and ALL KUDOS can never disagree about which kudos are
 * visible. Every child below inherits this boundary; none carries its own
 * `"use client"`. Phase 09 mounts this with `getKudosBoard()`'s output and
 * `toggleKudosLike` — see the report's "Prop contract" section for the
 * exact shape.
 *
 * `spotlightSlot`/`sidebarSlot` (layout-fix task, session 2026-09-06):
 * DOM order must match paint order for WCAG 2.1 meaningful-sequence/focus
 * order — SpotlightBoard needs to sit between the two `<section>`s this
 * component owns, and KudosSidebar needs to sit beside the ALL KUDOS feed
 * in one row (mm:2940:13481, "Frame 502"). Neither can move here without
 * crossing into `page.tsx`, so the caller passes them in as nodes and this
 * component places them — no `order-*` CSS repaint trick, no visual-only
 * reorder. Filter state stays exactly as before; only placement changed.
 */
export function KudosBoard({
  board,
  copy,
  toggleLike,
  spotlightSlot,
  sidebarSlot,
}: {
  board: KudosBoardViewModel;
  copy: KudosBoardCopy;
  toggleLike: ToggleKudosLike;
  spotlightSlot: ReactNode;
  sidebarSlot: ReactNode;
}) {
  // FR-405 (F006 phase 09) — a hashtag click on a profile card pushes
  // `/kudos?hashtag=<name>`, so the board has to READ that param: without
  // this, the destination URL would carry the tag while the board rendered
  // unfiltered, and a URL-only assertion would pass on a half-truth (the
  // same failure shape as F004's K-21). Resolved by NAME against
  // `board.hashtagOptions` — the id is a database key and must never appear
  // in a link. Absent, empty or unrecognised → `null`, byte-identical to the
  // state this board shipped with, which is what keeps F004's 27 board
  // assertions true. Read as the initial value only: once mounted, the
  // filter menu owns the state, so re-picking is not fighting the URL.
  const initialHashtagName = useSearchParams().get("hashtag");
  const [hashtagFilterId, setHashtagFilterId] = useState<number | null>(
    () => board.hashtagOptions.find((option) => option.name === initialHashtagName)?.id ?? null,
  );
  const [departmentFilterId, setDepartmentFilterId] = useState<number | null>(null);
  const [activeSlide, setActiveSlide] = useState(0);
  const [pages, setPages] = useState(1);
  const [toast, setToast] = useState<{ message: string; key: number } | null>(null);
  const toastKeyRef = useRef(0);

  const resetPaging = useCallback(() => {
    setActiveSlide(0);
    setPages(1);
  }, []);

  const handleSelectHashtag = useCallback(
    (option: FilterOptionView) => {
      setHashtagFilterId((current) => (current === option.id ? null : option.id));
      resetPaging();
    },
    [resetPaging],
  );

  const handleSelectDepartment = useCallback(
    (option: FilterOptionView) => {
      setDepartmentFilterId((current) => (current === option.id ? null : option.id));
      resetPaging();
    },
    [resetPaging],
  );

  const handleHashtagClick = useCallback(
    (tag: string) => {
      const match = board.hashtagOptions.find((option) => option.name === tag);
      if (!match) return;
      setHashtagFilterId(match.id);
      resetPaging();
    },
    [board.hashtagOptions, resetPaging],
  );

  const handleCopyLink = useCallback(
    (success: boolean) => {
      toastKeyRef.current += 1;
      setToast({
        message: success ? copy.toast.copySuccess : copy.toast.copyFailure,
        key: toastKeyRef.current,
      });
    },
    [copy.toast.copyFailure, copy.toast.copySuccess],
  );

  const filteredKudos = useMemo(() => {
    const hashtagName = board.hashtagOptions.find((o) => o.id === hashtagFilterId)?.name ?? null;
    const departmentName = board.departmentOptions.find((o) => o.id === departmentFilterId)?.name ?? null;
    return board.kudos.filter((card) =>
      matchesFilters(card, { hashtag: hashtagName, department: departmentName }),
    );
  }, [board.kudos, board.hashtagOptions, board.departmentOptions, hashtagFilterId, departmentFilterId]);

  return (
    <>
      {/* mm:2940:13451 (B_Highlight) */}
      <section key="highlight" data-testid="highlight-section" className="flex w-full flex-col gap-4 py-16">
        <div className="mx-auto flex w-full max-w-[1152px] flex-col gap-4 px-6 sm:px-12 lg:px-36">
          {/* mm:2940:13454 (Sun* Annual Awards 2025) */}
          <p className="text-2xl leading-8 font-bold text-white">{copy.eyebrow}</p>
          {/* mm:2940:13455 (Rectangle 26) */}
          <div aria-hidden className="h-px w-full bg-[#2E3940]" />
          <div className="flex flex-wrap items-center justify-between gap-6">
            {/* mm:2940:13457 (HIGHLIGHT KUDOS) */}
            <h2 className={SECTION_HEADING_CLASS}>{copy.sections.highlight}</h2>
            <KudosFilterBar
              hashtagOptions={board.hashtagOptions}
              departmentOptions={board.departmentOptions}
              hashtagFilterId={hashtagFilterId}
              departmentFilterId={departmentFilterId}
              onSelectHashtag={handleSelectHashtag}
              onSelectDepartment={handleSelectDepartment}
              copy={copy.filters}
            />
          </div>
        </div>

        <HighlightCarousel
          cards={filteredKudos}
          activeIndex={activeSlide}
          onIndexChange={setActiveSlide}
          copy={copy.card}
          onHashtagClick={handleHashtagClick}
          onCopyLink={handleCopyLink}
          toggleLike={toggleLike}
        />
      </section>

      {/* mm:2940:14170 (Frame 552) — SPOTLIGHT BOARD sits between HIGHLIGHT
          and ALL KUDOS in the DOM, matching the frame's paint order, so tab
          order and screen-reader order agree with what is on screen. */}
      <Fragment key="spotlight">{spotlightSlot}</Fragment>

      <AllKudosSection
        key="all-kudos"
        eyebrow={copy.eyebrow}
        heading={copy.sections.allKudos}
        cards={filteredKudos}
        pages={pages}
        onLoadMore={() => setPages((p) => p + 1)}
        copy={copy.card}
        onHashtagClick={handleHashtagClick}
        onCopyLink={handleCopyLink}
        toggleLike={toggleLike}
        sidebarSlot={sidebarSlot}
      />

      <KudosToast key="toast" toast={toast} onDismiss={() => setToast(null)} />
    </>
  );
}
