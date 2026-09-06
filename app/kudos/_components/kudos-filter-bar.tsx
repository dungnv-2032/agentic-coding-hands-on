import { useRef, useState } from "react";

import { useDismissOnOutside } from "@/app/_components/use-dismiss-on-outside";
import type { FilterOptionView } from "@/lib/kudos/view-model";

import { IconChevronDown } from "./kudos-icons";
import { KudosFilterMenu } from "./kudos-filter-menu";

type FilterKind = "hashtag" | "department";

const TRIGGER_CLASS =
  "flex items-center gap-2 rounded border border-[#998C5F] bg-[rgba(255,234,158,0.10)] px-4 py-4 text-base leading-6 font-bold tracking-[0.15px] text-white";

/**
 * mm:2940:13458 (Buttons) — the two `#1A2527`-family filter triggers
 * (measured fill: `rgba(255,234,158,0.10)` + 1px `#998C5F` border,
 * `B.1.1_ButtonHashtag`/`B.1.2_Button Phong ban`) and the listboxes they
 * open. Only one menu open at a time; reuses the shared
 * `use-dismiss-on-outside` hook rather than a third bespoke handler (DRY,
 * plan.md § Implementation Steps 3). Carries no `"use client"` of its own —
 * always rendered inside `kudos-board.tsx`'s client boundary.
 */
export function KudosFilterBar({
  hashtagOptions,
  departmentOptions,
  hashtagFilterId,
  departmentFilterId,
  onSelectHashtag,
  onSelectDepartment,
  copy,
}: {
  hashtagOptions: FilterOptionView[];
  departmentOptions: FilterOptionView[];
  hashtagFilterId: number | null;
  departmentFilterId: number | null;
  onSelectHashtag: (option: FilterOptionView) => void;
  onSelectDepartment: (option: FilterOptionView) => void;
  copy: { hashtag: string; department: string };
}) {
  const [openMenu, setOpenMenu] = useState<FilterKind | null>(null);
  const hashtagRootRef = useRef<HTMLDivElement>(null);
  const hashtagTriggerRef = useRef<HTMLButtonElement>(null);
  const departmentRootRef = useRef<HTMLDivElement>(null);
  const departmentTriggerRef = useRef<HTMLButtonElement>(null);

  useDismissOnOutside(openMenu === "hashtag", hashtagRootRef, hashtagTriggerRef, () => setOpenMenu(null));
  useDismissOnOutside(openMenu === "department", departmentRootRef, departmentTriggerRef, () => setOpenMenu(null));

  return (
    // mm:2940:13458 (Buttons)
    <div className="flex items-center gap-2">
      {/* mm:2940:13459 (B.1.1_ButtonHashtag) */}
      <div ref={hashtagRootRef} className="relative">
        <button
          ref={hashtagTriggerRef}
          type="button"
          data-testid="filter-hashtag"
          aria-expanded={openMenu === "hashtag"}
          onClick={() => setOpenMenu((menu) => (menu === "hashtag" ? null : "hashtag"))}
          className={TRIGGER_CLASS}
        >
          {copy.hashtag}
          {/* mm:I2940:13459;186:2761 (MM_MEDIA_Down) */}
          <IconChevronDown
            aria-hidden
            className={`h-6 w-6 transition-transform ${openMenu === "hashtag" ? "rotate-180" : ""}`}
          />
        </button>
        {openMenu === "hashtag" && (
          <KudosFilterMenu
            testId="filter-menu-hashtag"
            options={hashtagOptions}
            selectedId={hashtagFilterId}
            onSelect={(option) => {
              onSelectHashtag(option);
              setOpenMenu(null);
            }}
          />
        )}
      </div>

      {/* mm:2940:13460 (B.1.2_Button Phong ban) */}
      <div ref={departmentRootRef} className="relative">
        <button
          ref={departmentTriggerRef}
          type="button"
          data-testid="filter-department"
          aria-expanded={openMenu === "department"}
          onClick={() => setOpenMenu((menu) => (menu === "department" ? null : "department"))}
          className={TRIGGER_CLASS}
        >
          {copy.department}
          <IconChevronDown
            aria-hidden
            className={`h-6 w-6 transition-transform ${openMenu === "department" ? "rotate-180" : ""}`}
          />
        </button>
        {openMenu === "department" && (
          <KudosFilterMenu
            testId="filter-menu-department"
            options={departmentOptions}
            selectedId={departmentFilterId}
            onSelect={(option) => {
              onSelectDepartment(option);
              setOpenMenu(null);
            }}
            scrollable
          />
        )}
      </div>
    </div>
  );
}
