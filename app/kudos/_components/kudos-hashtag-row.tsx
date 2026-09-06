const MAX_VISIBLE_HASHTAGS = 5;

/**
 * mm:256:5158 (C.3.7_Hash tag). test-contract.md § Kudos card: `<button>`s,
 * not links — clicking one sets the shared hashtag filter (FR-403); filter
 * state is phase 07's, so the click handler arrives as a prop. At most 5 on
 * one line, then a literal `…` (never a 6th `kudos-hashtag` match).
 *
 * Carries no `"use client"` of its own — same note as
 * `kudos-card-actions.tsx` (plan.md § Client/server split): it renders only
 * inside phase 07's client boundary via `kudos-card.tsx`. Never import this
 * from a genuine server-rendered tree; the `onClick` below requires one.
 */
export function KudosHashtagRow({
  hashtags,
  onHashtagClick,
}: {
  hashtags: string[];
  onHashtagClick: (hashtag: string) => void;
}) {
  if (hashtags.length === 0) return null;

  const visible = hashtags.slice(0, MAX_VISIBLE_HASHTAGS);
  const hasMore = hashtags.length > MAX_VISIBLE_HASHTAGS;

  return (
    // mm:256:5158
    <div className="flex w-full flex-wrap items-center gap-x-3 gap-y-1">
      {visible.map((tag) => (
        // mm:256:5159 — one button per tag, rather than the design's single
        // concatenated text node, so each tag is independently clickable.
        <button
          key={tag}
          type="button"
          data-testid="kudos-hashtag"
          onClick={() => onHashtagClick(tag)}
          className="text-base leading-6 font-bold tracking-[0.5px] text-[#D4271D] hover:underline"
        >
          #{tag}
        </button>
      ))}
      {hasMore && (
        <span aria-hidden className="text-base leading-6 font-bold text-[#D4271D]">
          …
        </span>
      )}
    </div>
  );
}
