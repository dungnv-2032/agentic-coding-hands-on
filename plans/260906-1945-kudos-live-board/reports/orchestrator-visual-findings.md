# Orchestrator visual findings — from `evidence/all-kudos-sidebar-row-desktop.png`

Read directly off the layout-fix agent's own screenshot evidence. None of these were flagged by the
phase reports. The two-column ALL KUDOS + sidebar row itself is correct and matches the frame.

## V1 — Card content overflows the card (receiver chip clipped) — CRITICAL

The sender row renders `Huỳnh Dương Xuân Nhật / CEVC10 · Super Hero`, then the 32px send glyph, and
then the **receiver chip is cut off at the card's right edge** — a second `CEVC10 ·` fragment is
visible bleeding past the card boundary and behind the sidebar column. The receiver's avatar, name
and badge are effectively invisible.

This is not a data problem: the receiver exists (the seed pairs sender→receiver on every Group A
row). It is a width/overflow problem, and it almost certainly appeared when the feed column narrowed
from full-width `max-w-[1152px]` to the two-column ~680px feed. The card's internal
sender→glyph→receiver row was laid out for the wider column and does not reflow.

The frame draws sender and receiver both fully visible inside the card. A clipped receiver defeats
the screen's entire purpose — a Kudos names who is being thanked.

## V2 — Attachment gallery clipped at the card edge

Four attachment thumbnails render and the fourth is sliced by the card boundary. The contract allows
up to 5 at 88px. Same root cause as V1: the row was sized for the wider column. Either the gallery
wraps, scrolls, or the thumbnails shrink — the frame shows five sitting inside the card, left-aligned.

## V3 — Message body is justified

The body renders with `text-align: justify` (or equivalent), producing very large inter-word gaps —
`Cảm  ơn  người  em  bình  thường  nhưng  phi  thường`. The frame sets ragged-right body copy. This
is a fidelity defect and also hurts readability in Vietnamese, where justification stretches
diacritic-heavy lines badly.

## V4 — Next.js dev overlay reports "1 Issue" — INVESTIGATE

The bottom-left overlay badge reads `1 Issue`. The suite is green, so this is something the tests do
not assert: a hydration mismatch, a React key warning, an `<img>`/`next/image` warning, or a console
error. Given phase 08 built a seeded word-cloud layout whose whole design constraint was SSR/client
parity, a hydration mismatch is the first hypothesis to rule out. Read the actual overlay/console
text before theorising further.

## V5 — Heart count reads `1.002`, not `1.000` (state hygiene, not necessarily a defect)

The frame's card is `1.000`. The screenshot shows `1.002`, i.e. `heart_baseline 1000 + 2 persisted
likes` left in `kudos_likes` by earlier manual/e2e clicking. Correct arithmetic, but it means the
local database carries leftover like rows. Confirm `npx supabase db reset` restores `1.000`, and that
no test depends on a non-zero starting like count.

---

## Resolution (orchestrator, 2026-09-07)

| # | Finding | Outcome |
|---|---------|---------|
| V1 | Receiver chip clipped / card content overflows | **FIXED.** Root-caused twice over: the layout-fix agent found the feed column was rendering at 392px instead of 680px (a `max-w` + `px-36` stacked on one box), and the card-fix agent found `sunner-chip.tsx` hard-coding `w-[235px] shrink-0` with no wrap capacity. Desktop now matches nodes `2940:13482`/`2940:13488` exactly; 375px has zero horizontal document overflow. |
| V2 | Attachment gallery clipped | **FIXED.** All five 88px thumbnails now sit inside the card at the corrected column width. |
| V3 | Message body justified | **WITHDRAWN — my error.** The frame's own text nodes measure `textAlignHorizontal: JUSTIFIED`. What looked wrong was justification inside the too-narrow column; at 680px it reads evenly. The UI agent was right to refuse the change and escalate rather than deviate from the design source. |
| V4 | Next.js dev overlay `1 Issue` | **FIXED and verified.** The debugger proved via a live React fiber walk that it was `kudos-board.tsx`'s own top-level 4-child Fragment carrying no keys — introduced by the `spotlightSlot`/`sidebarSlot` refactor, which is exactly why the earlier `.map()` grep found nothing. Confirmed dev-only (a real `npm run build && npm run start` console is clean). Fixed by keying all four Fragment children, then re-verified by capturing the live console: `KEY-WARNING PRESENT: false`. The only console errors remaining are HMR WebSocket handshake failures, independently broken in this WSL2 setup and unrelated to this feature. |
| V5 | Heart count `1.002` / `52` instead of `1.000` | **NOT A DEFECT — my error.** The feed is newest-first and `kudos` id=1 (the frame-verbatim card, baseline 1000, 10:00 +07 on 30/10/2025) correctly leads it. Both readings came from screenshots scrolled past the first card, plus leftover `kudos_likes` rows before a reset. |

Two of five findings I raised were wrong. Both were caught by agents pushing back with measurements
rather than complying — which is the behaviour the MoMorph rule "never guess a visual value" is
supposed to produce, and it applies to the orchestrator as much as to the implementer.
