import Image from "next/image";

import type { Dictionary } from "@/lib/i18n/dictionaries";

import { ErrorBanner } from "./error-banner";
import { GoogleSignInButton } from "./google-sign-in-button";

interface LoginContentProps {
  dictionary: Dictionary;
  hasError: boolean;
  signInAction: () => Promise<void>;
}

/**
 * R2 — hero content column: ROOT FURTHER wordmark (E04, image not text —
 * design-notes.md), intro copy (E05/E06), error banner (idle/error state),
 * and the Google sign-in button, left-aligned with the description column
 * (design-notes.md corrects test case 6ae76d15's "centered" reading).
 */
export function LoginContent({
  dictionary,
  hasError,
  signInAction,
}: LoginContentProps) {
  return (
    // mm:662:14393
    <main className="relative z-10 flex flex-1 flex-col justify-center gap-20 px-36 py-24">
      {/* mm:662:14395 */}
      <Image
        src="/images/login/root-further.png"
        alt={dictionary.login.wordmarkAlt}
        width={451}
        height={200}
        preload
      />
      {/* mm:662:14755 */}
      <div className="flex max-w-[496px] flex-col items-start gap-6 pl-4">
        {/* mm:662:14753 */}
        <p className="text-xl font-bold leading-10 tracking-[0.5px] text-white">
          {dictionary.login.subtitle}
          <br />
          {dictionary.login.tagline}
        </p>
        {hasError && (
          <ErrorBanner message={dictionary.login.errorOauthFailed} />
        )}
        {/* mm:662:14425 */}
        <form action={signInAction}>
          <GoogleSignInButton label={dictionary.login.signInButton} />
        </form>
      </div>
    </main>
  );
}
