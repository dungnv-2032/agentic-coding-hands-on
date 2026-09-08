# Phase 07 — Track A: keyvisual, hero, badge row, stats card, write-Kudo bar

`test_policy: e2e-red-first` · `momorph-ui-implementer` · 2.5h · concurrent with 03–06, 08

**Screen refs** — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/3FoIx6ALVb · `mm:I1210:12622;2167:5140` keyvisual · `mm:362:5052` hero · `5053` avatar · `5054-5060`+`3053:6061` name/dept/dot/pill · `5064`,`5066`–`5071` badge row · `5073-5082` stats card. Measured values: `reports/momorph-visual-study.md`. Clarifications: `clarifications.md`.

**Goal** — render Keyvisual, A, A.3 and the B slot (stats card **or** write-Kudo bar) from props; presentational only.

**File ownership** (nothing else) — `app/profile/_components/`: `profile-keyvisual.tsx`, `profile-hero.tsx`, `profile-badge-row.tsx`, `profile-stats-card.tsx`, `write-kudo-bar.tsx`. Five files because one hero would exceed the 200-line cap — the split is named up front, not discovered later.

**Integration contract** — consume `ProfileHeroView`, `ProfileStatsView`, `Dictionary["profile"]` (phase 01). `stats === null` ⇒ `WriteKudoBar` with `writeKudoTargetId` → `/kudos/new?receiverId={id}`; `stats !== null` ⇒ `ProfileStatsCard`. Never re-derive "is this me". Testids phase 02 asserts: `profile-hero`, `profile-tier-badge`, `profile-badge-row`, `profile-badge-slot`(×6), `profile-stats-card`, `profile-stat`(×5), `profile-secret-box-button`, `profile-write-bar`.

**Amendments that override the design CSV** — AMEND-1: **no hoa-thị stars** exist in the frame; invent none. AMEND-2: six identical flat `#323231` circles, 64×64, `border-2 border-white`, `rounded-full`, 16px gap, fixed order B2→B7, and the row is a **child of the hero** directly under the name — not a section below it. No badge artwork exists to desaturate. `hero.badge === null` ⇒ hide the pill; `department === null` ⇒ hide dept **and** the separator dot together.

**Reuse, do not re-measure** — `kudos-hero.tsx` ships the 512px `object-cover` banner + `aria-hidden` gradient wash (this frame: `8deg, #00101A 8.6%, rgba(0,19,32,0) 37.25%`). `kudos-sidebar.tsx` ships every stats token verbatim (`border-[#998C5F] bg-[#00070C] rounded-[17px]`, label `text-[22px] font-bold text-white`, value `text-[32px] text-[#FFEA9E]`, divider `h-px bg-[#2E3940]`) and the gold `Mở Secret Box` button — re-lay at 680px / `p-10`. Counts render through `formatHeartCount` (`lib/kudos/derive.ts`), never `toLocaleString`.

**Out of scope** — the KUDOS section (08); `app/profile/page.tsx` (09); any data fetch, server action or Supabase import; the Spam chip (never rendered); responsive breakpoints (the frame exists at 1440 only); editing name/avatar/department (ruled out though the schema permits it). The Secret Box control is a `<button disabled>`, **not** the sidebar's `<a href="/kudos/secret-box">`.

**Done when** — typecheck + lint exit 0; all five files < 200 lines; every testid present; six slots on every face; no star node, no invented artwork, no hardcoded counter. Phase 10 owns browser evidence.
