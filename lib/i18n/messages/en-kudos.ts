import type { Dictionary } from "./dictionary";

/**
 * English Kudos Live Board copy, typed against the shared `Dictionary["kudos"]`
 * shape so a key missing here fails `npm run typecheck`. A faithful
 * translation of `vi-kudos.ts`; vi is authoritative and no test asserts EN
 * copy. `sections.*`, `filters.hashtag`, and `spotlightBoard.panZoom` stay
 * unchanged — the design renders those labels in English in both locales,
 * same convention as `header.kudos: "Sun* Kudos"` in `dictionary.ts`.
 */
export const enKudos: Dictionary["kudos"] = {
  hero: {
    title: "Recognition and appreciation system",
    composePlaceholder: "Today, who would you like to thank and recognize?",
    searchPlaceholder: "Search Sunner profile",
  },
  eyebrow: "Sun* Annual Awards 2025",
  sections: {
    highlight: "HIGHLIGHT KUDOS",
    spotlight: "SPOTLIGHT BOARD",
    allKudos: "ALL KUDOS",
  },
  filters: {
    hashtag: "Hashtag",
    department: "Department",
  },
  card: {
    copyLink: "Copy Link",
    viewDetail: "View details",
    empty: "There are no Kudos yet.",
  },
  spotlightBoard: {
    searchPlaceholder: "Search",
    panZoom: "Pan/Zoom",
    tickerSuffix: "just received a new Kudos",
    empty: "No matching Sunner found.",
  },
  sidebar: {
    stats: {
      kudosReceived: "Kudos you received:",
      kudosSent: "Kudos you sent:",
      heartsReceived: "Hearts you received:",
      secretBoxOpened: "Secret Boxes you opened:",
      secretBoxUnopened: "Secret Boxes unopened:",
    },
    secretBoxButton: "Open Secret Box",
    giftHeading: "10 SUNNERS WHO RECEIVED GIFTS MOST RECENTLY",
    giftEmpty: "No data yet",
  },
  toast: {
    copySuccess: "Link copied — ready to share!",
    copyFailure: "Couldn't copy the link. Please try again.",
  },
};
