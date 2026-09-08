# Phase 08 — Track A: KUDOS section (direction dropdown, feed, infinite scroll)

`test_policy: e2e-red-first` · `momorph-ui-implementer` · 3h · concurrent with 03–07

**Screen refs** — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/3FoIx6ALVb · `mm:362:5084` section header · `5085` "Sun* Annual Awards 2025" · `5086` divider · `5088` gold 57/64 "KUDOS" · `5089` dropdown trigger (`border-[#998C5F]`, `bg-[rgba(255,234,158,0.10)]`, `rounded`, `p-[16px_24px]`) · `5091` single-column 680px feed, 24px gap. Measured values: `reports/momorph-visual-study.md`. Clarifications: `clarifications.md`.

**Goal** — regions C and D: direction dropdown plus paged card feed, driven entirely by props and one injected server action.

**File ownership** — `app/profile/_components/`: `kudos-direction-section.tsx` (state + wiring), `profile-direction-menu.tsx` (listbox), `profile-kudos-feed.tsx` (cards, sentinel, empty, end). Three files because one would exceed the 200-line cap — split named up front.

**Integration contract** — props `{ targetSunnerId, initialPage, counts, isSelf, copy, fetchPage: FetchProfileKudosPage, toggleLike: ToggleKudosLike, onCopyLink, onHashtagClick }` from phases 01/05. SM-001 states: `idle` → `switching` → `loading-more` → `settled`. Testids: `profile-direction-trigger`, `profile-direction-option`, `profile-feed`, `profile-feed-empty`, `profile-feed-end`, `profile-feed-sentinel`.

**Behaviour the frame does not capture** — DEC-001: **`Đã nhận` is active on first render.** The frame shows `Đã gửi (5)`; that is the mock's moment and `TC_FUN_009` governs. `isSelf === false` ⇒ **one** option only: no `Đã gửi` label, option or count anywhere in the DOM (SEC_001 — absent from the props, not hidden by CSS). Switching clears accumulated cards immediately, requests page 1 with `cursor: null`, and updates the trigger label **only after** the page lands (FR-403). Re-picking the active option closes the menu and issues **no request** (DEC-002). Keep a monotonic request id and discard responses older than the active request (double-click).

**Reuse, do not rebuild** — `KudosCard` outright, `variant="feed"`, `copy={kudos.card}` (AMEND-3: `#FFF8E1` is already `kudos-card.tsx:114`, so it is the same component, not a lookalike). `use-infinite-feed.ts` unmodified for the sentinel. `kudos-filter-menu.tsx`'s panel styling and `role="listbox"`/`role="option"` shape. Empty copy per direction from `copy.feed.emptyReceived`/`emptySent`; end message `copy.feed.endOfFeed` with `aria-live` on the feed's status region. Hashtag click calls `onHashtagClick` — this component does not own the destination.

**Out of scope** — any Supabase or `lib/profile/*` import (the action arrives as a prop, the idiom `app/_components/coming-soon.tsx:29` already ships); `app/profile/page.tsx` (09); hero and stats card (07); a hashtag filter of the profile's own; the Spam chip; **any optimistic heart** — `toggleLike` is server-authoritative and the rendered count is always the server's (K-25).

**Done when** — typecheck + lint exit 0; all three files < 200 lines; on `isSelf === false` a full-page text search finds no `Đã gửi`; re-picking the active option fires zero requests; no duplicate `kudos-card` id after switching direction twice. Phase 10 owns browser evidence.
