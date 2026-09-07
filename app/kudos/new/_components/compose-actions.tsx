/**
 * mm:I520:11647;520:9905 (`mms_H_Frame 538`, 672px row, gap 24px,
 * `flex-start`) · mm:I520:11647;520:9906 (Hủy, padding `16px 40px`, gap 8px,
 * border `#998C5F`, radius 4px, bg `rgba(255,234,158,0.10)`, `align-self:
 * stretch`) · mm:I520:11647;520:9907 (Gửi, 502×60px, padding 16px, radius
 * 8px, bg `#FFEA9E`, `justify-content: center`) — all re-measured live this
 * pass (`get_node`), matching design-source-analysis.md § 8 exactly.
 *
 * `compose-submit` is NEVER `disabled` and never `aria-disabled`
 * (test-contract.md § Blueprint ratification — phase-02 repair): pressing it
 * on an incomplete form is how the designed error state (frame `5c7PkAibyD`)
 * is reached. `data-submit-ready` is the only readiness signal; the inactive
 * styling below dims the not-ready state without ever making it inert.
 */
export interface ComposeActionsCopy {
  cancelLabel: string;
  submitLabel: string;
  submitPendingLabel: string;
}

export interface ComposeActionsProps {
  copy: ComposeActionsCopy;
  cancelHref: string;
  submitReady: boolean;
  pending: boolean;
}

export function ComposeActions({ copy, cancelHref, submitReady, pending }: ComposeActionsProps) {
  return (
    // mm:I520:11647;520:9905
    <div className="flex w-full items-start gap-6">
      {/* mm:I520:11647;520:9906 — DEC-001: a real anchor, no confirm dialog, closes and discards */}
      <a
        data-testid="compose-cancel"
        href={cancelHref}
        className="flex items-center gap-2 self-stretch rounded border border-[#998C5F] bg-[rgba(255,234,158,0.10)] px-10 py-4 text-base font-bold text-[#00101A]"
      >
        {copy.cancelLabel}
      </a>
      {/* mm:I520:11647;520:9907 */}
      <button
        type="submit"
        data-testid="compose-submit"
        data-submit-ready={submitReady ? "true" : "false"}
        className={`flex h-[60px] w-[502px] items-center justify-center rounded-lg bg-[#FFEA9E] p-4 text-base font-bold text-[#00101A] ${
          submitReady ? "" : "opacity-50"
        }`}
      >
        {pending ? copy.submitPendingLabel : copy.submitLabel}
      </button>
    </div>
  );
}
