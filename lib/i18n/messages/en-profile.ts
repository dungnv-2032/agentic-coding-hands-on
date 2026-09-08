import type { Dictionary } from "./dictionary";

/**
 * English Profile bản thân copy, typed against the shared
 * `Dictionary["profile"]` shape so a key missing here fails
 * `npm run typecheck`. A faithful translation of `vi-profile.ts`; vi is
 * authoritative and no test asserts EN copy — same convention as
 * `en-kudos.ts`.
 */
export const enProfile: Dictionary["profile"] = {
  badges: {
    headingSelf: "My icon collection",
    headingOther: "Icon collection",
  },
  stats: {
    kudosReceived: "Kudos you received:",
    kudosSent: "Kudos you sent:",
    heartsReceived: "Hearts you received:",
    secretBoxOpened: "Secret Boxes you opened:",
    secretBoxUnopened: "Secret Boxes unopened:",
    secretBoxButton: "Open Secret Box",
  },
  writeBar: {
    label: "Send thanks and recognition to {name}",
  },
  direction: {
    receivedLabel: "Received ({count})",
    sentLabel: "Sent ({count})",
  },
  feed: {
    emptyReceived: "There are no Kudos yet.",
    emptySent: "You haven't sent any Kudos yet.",
    /** Authored, not frame-sourced — see `vi-profile.ts`'s `feed.endOfFeed` comment for why. */
    endOfFeed: "You've seen all the Kudos.",
  },
};
