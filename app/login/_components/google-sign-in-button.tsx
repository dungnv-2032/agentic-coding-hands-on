"use client";

import { useFormStatus } from "react-dom";

import { IconGoogle } from "./icons";

interface GoogleSignInButtonProps {
  label: string;
}

/**
 * E07 — must live inside a `<form action={signInWithGoogle}>` so
 * `useFormStatus` can read the pending state (SM-001: disabled + loader
 * while the OAuth redirect is in flight). Google's "G" sits to the right of
 * the label per design-notes.md, not the left the spec's buttonType implies.
 */
export function GoogleSignInButton({ label }: GoogleSignInButtonProps) {
  const { pending } = useFormStatus();

  return (
    // mm:662:14426
    <button
      type="submit"
      disabled={pending}
      className="flex cursor-pointer items-center gap-2 rounded-lg bg-[#FFEA9E] px-6 py-4 text-[#00101A] transition-shadow hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-70"
    >
      {/* mm:I662:14426;186:1568 */}
      <span className="text-[22px] font-bold leading-7">{label}</span>
      {pending ? (
        <span
          aria-hidden
          className="h-6 w-6 animate-spin rounded-full border-2 border-[#00101A]/30 border-t-[#00101A]"
        />
      ) : (
        <IconGoogle className="h-6 w-6" />
      )}
    </button>
  );
}
