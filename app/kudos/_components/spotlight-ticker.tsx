import type { SpotlightTickerRowView } from "@/lib/kudos/view-model";

/**
 * mm:3004:15999 (`08:30PM Nguyễn Bá Chức đã nhận được một Kudos mới`) — six
 * rows, fading upward. `rows` is assumed oldest-first (matches the view
 * model's array-push convention); the newest row (last in the array) renders
 * fully opaque and each row above it fades further, matching the frame's
 * `opacity: 0.1` sample on its earliest row.
 */
export function SpotlightTicker({
  rows,
  suffix,
}: {
  rows: SpotlightTickerRowView[];
  suffix: string;
}) {
  const total = rows.length;

  return (
    // mm:2940:14174 (ticker band, bottom-left of the canvas)
    <div data-testid="spotlight-ticker" className="flex flex-col gap-1">
      {rows.map((row, index) => (
        // mm:3004:15999
        <p
          key={row.id}
          style={{ opacity: total <= 1 ? 1 : (index + 1) / total }}
          className="text-sm font-bold tracking-[0.1px] text-white"
        >
          {row.timeLabel} {row.name} {suffix}
        </p>
      ))}
    </div>
  );
}
