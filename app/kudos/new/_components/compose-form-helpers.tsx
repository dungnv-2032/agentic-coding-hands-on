import type { ReactNode } from "react";

import type { ComposeFieldErrors } from "@/lib/kudos/compose-contract";

/**
 * Small presentational/pure helpers factored out of `compose-form.tsx` to
 * keep that file under the repo's 200-line cap — no state, no MoMorph nodes
 * of their own beyond what `FieldRow` cites below.
 */

export function mergeErrors(client: ComposeFieldErrors, server: ComposeFieldErrors): ComposeFieldErrors {
  // Client-precedence: it is the error the user's own last action just triggered.
  return {
    recipient: client.recipient ?? server.recipient,
    title: client.title ?? server.title,
    body: client.body ?? server.body,
    hashtag: client.hashtag ?? server.hashtag,
    form: client.form ?? server.form,
  };
}

export function FieldRow({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    // mm:I520:11647;520:9871 / ;520:9890 / ;520:9896 — label-left, field-right, 16px gap (measured live)
    <div className="flex w-full items-start gap-4">
      <span className="mt-4 shrink-0 text-[22px] leading-7 font-bold text-[#00101A]">
        {label}
        {required && <span className="text-[#CF1322]"> *</span>}
      </span>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
