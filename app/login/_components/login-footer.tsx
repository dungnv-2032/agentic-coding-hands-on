interface LoginFooterProps {
  copyright: string;
}

/**
 * R3 — fixed-bottom footer (E08), non-interactive (test case 33a1dacf).
 * Rendered as a top-level `<footer>` sibling of `<main>` so it keeps the
 * `contentinfo` landmark role the RED suite locates it by.
 */
export function LoginFooter({ copyright }: LoginFooterProps) {
  return (
    // mm:662:14447
    <footer className="relative z-20 flex w-full items-center justify-center border-t border-[#2E3940] px-[90px] py-10">
      {/* mm:I662:14447;342:1413 */}
      <p className="font-montserrat-alternates text-base font-bold text-white">
        {copyright}
      </p>
    </footer>
  );
}
