/**
 * mm:362:5064 (`mms_A.3_Huy Hiệu`) + mm:3053:10052 (its caption) — the six
 * badge slots and the line naming the collection.
 *
 * Both nodes are children of `mms_A_Info` (`362:5052`), so this renders
 * INSIDE the hero directly under the name (clarifications AMEND-2), and the
 * two are wrapped together here because `TC_WEB_PROFILE_GUI_003` asserts the
 * caption inside `profile-badge-row`. The hero lays its children out on a
 * 32px gap; this wrapper repeats that gap internally so the caption sits
 * where Figma puts it (row y528–592, caption y624–652).
 *
 * The caption sits BELOW the circles. `docs/screens/SCR006_ProfileBanThan/spec.md`
 * says "tiêu đề phía trên hàng" (above the row); the frame measures it below,
 * and `design/profile.png` renders it below. The measured frame wins.
 *
 * AMEND-2: every slot is the same flat `#323231` circle. There is no badge
 * artwork anywhere on this frame — `get_media_files` returns 30 media nodes
 * and not one of them is a badge — so no slot is hidden, none is unlocked,
 * and nothing is desaturated, because there is nothing to desaturate.
 */

/**
 * mm:362:5066, mm:362:5067, mm:362:5068, mm:362:5069, mm:362:5070,
 * mm:362:5071 — slots B2→B7 in the frame's fixed left-to-right order. The
 * order is positional, so the array index IS the slot index the view model's
 * `unlockedBadgeSlots` refers to.
 */
const SLOT_NODE_IDS = [
  "362:5066",
  "362:5067",
  "362:5068",
  "362:5069",
  "362:5070",
  "362:5071",
] as const;

export function ProfileBadgeRow({
  heading,
  unlockedSlots = [],
}: {
  /** Already resolved by the page: `badges.headingSelf` or `badges.headingOther`. */
  heading: string;
  /**
   * `ProfileViewModel.unlockedBadgeSlots` — always empty today (the Secret Box
   * that awards badges is deferred), so in practice every slot renders locked.
   * Honoured rather than ignored so that awarding a badge stays a data change,
   * but be honest about the ceiling: with no artwork in the frame, all an
   * unlocked slot can do is drop the locked `#323231` fill. Real badge
   * imagery is a follow-up commission, not something to invent here.
   */
  unlockedSlots?: readonly number[];
}) {
  return (
    <div data-testid="profile-badge-row" className="flex w-full flex-col items-center gap-8">
      {/* mm:362:5064 — 1440 wide with 800px side padding and
          `space-between` around a single child, which is just centring. */}
      <div className="flex w-full items-center justify-center">
        {/* mm:362:5065 (`Danh hiệu`) — the 1px black hairline is measured, and
            all but invisible against `#00101A`; kept because it is real. */}
        <div className="flex items-start gap-4 border border-black">
          {SLOT_NODE_IDS.map((nodeId, index) => (
            // mm:362:5066–mm:362:5071 — slot frame, 80×64, column, gap 8.
            <div
              key={nodeId}
              data-testid="profile-badge-slot"
              className="flex h-16 w-20 flex-col items-center justify-center gap-2"
            >
              {/* mm:I362:5066;3053:10046 (`Ảnh Huy hiệu`) — 64×64, 2px white
                  ring, flat `#323231` locked fill, `border-radius: 100px`. */}
              <div
                className={`h-16 w-16 rounded-full border-2 border-white ${
                  unlockedSlots.includes(index) ? "" : "bg-[#323231]"
                }`}
              />
            </div>
          ))}
        </div>
      </div>

      {/* mm:3053:10052 — 22px/28px bold white, centred. */}
      <h2 className="text-center text-[22px] leading-7 font-bold text-white">{heading}</h2>
    </div>
  );
}
