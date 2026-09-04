/**
 * Full-bleed hero artwork layer (RISK-01 / ORCH-05, clarifications.md).
 *
 * The real artwork could not be exported from MoMorph this session (the
 * render endpoint 500s frame-wide — see design-notes.md). This layer wires
 * the recorded Figma geometry against `/images/login/hero.png` over a solid
 * dark-navy fallback. When the file lands the browser paints it in place —
 * `background-color` only shows through while `background-image` is
 * missing/unresolved, so dropping the PNG in requires zero code edits.
 */
export function HeroBackground() {
  return (
    <>
      {/* mm:662:14389 */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-0 top-[2px] h-[1022px] w-[1441px] max-w-none bg-[#00101A]"
        style={{
          backgroundImage: "url(/images/login/hero.png)",
          backgroundPosition: "-440px -217.975px",
          backgroundSize: "159.763% 133.371%",
          backgroundRepeat: "no-repeat",
        }}
      />
      {/* mm:662:14392 */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "linear-gradient(90deg, #00101A 0%, #00101A 25.41%, rgba(0, 16, 26, 0) 100%)",
        }}
      />
      {/* mm:662:14390 */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 top-[138px]"
        style={{
          background:
            "linear-gradient(0deg, #00101A 22.48%, rgba(0, 19, 32, 0) 51.74%)",
        }}
      />
    </>
  );
}
