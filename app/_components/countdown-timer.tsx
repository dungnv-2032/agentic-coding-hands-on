"use client";

import { useEffect, useMemo, useRef, useState } from "react";

/**
 * ALG-001 (technical-spec.md §4.5) · mm:2167:9035 (mms_B1_Countdown time) +
 * mm:2167:9037 (mms_B1.3_Countdown).
 *
 * Ticks every second from `Date.now()`, recomputing the whole diff rather
 * than accumulating (self-correcting against tab throttling — BR-003). The
 * first render — server AND client, pre-hydration — never touches the
 * clock: it only checks whether `eventStartAt` parses (a pure function of
 * the fixed prop string, so server and client agree), so initial markup
 * always matches and `suppressHydrationWarning` is never needed. The live
 * diff is filled in by `useEffect` after mount (clarifications.md, "tick
 * cadence and hydration").
 */

interface CountdownLabels {
  comingSoon: string;
  days: string;
  hours: string;
  minutes: string;
}

interface CountdownTimerProps {
  eventStartAt?: string;
  labels: CountdownLabels;
}

interface CountdownState {
  days: string;
  hours: string;
  minutes: string;
  showComingSoon: boolean;
}

const ZERO_UNITS = { days: "00", hours: "00", minutes: "00" } as const;
const DAY_MS = 24 * 60 * 60 * 1000;
const HOUR_MS = 60 * 60 * 1000;
const MINUTE_MS = 60 * 1000;

function parseEventDate(value?: string): Date | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function computeCountdown(target: Date): CountdownState {
  const diffMs = target.getTime() - Date.now();
  if (diffMs <= 0) {
    return { ...ZERO_UNITS, showComingSoon: false };
  }
  const days = Math.floor(diffMs / DAY_MS);
  const hours = Math.floor((diffMs % DAY_MS) / HOUR_MS);
  const minutes = Math.floor((diffMs % HOUR_MS) / MINUTE_MS);
  return {
    days: String(days).padStart(2, "0"),
    hours: String(hours).padStart(2, "0"),
    minutes: String(minutes).padStart(2, "0"),
    showComingSoon: true,
  };
}

export function CountdownTimer({ eventStartAt, labels }: CountdownTimerProps) {
  // Stable reference across re-renders (keyed only on the prop string) so
  // the effect below doesn't re-subscribe every render — `new Date(...)`
  // otherwise produces a fresh object identity each call.
  const parsed = useMemo(() => parseEventDate(eventStartAt), [eventStartAt]);
  const warnedRef = useRef(false);

  const [state, setState] = useState<CountdownState>(() => ({
    ...ZERO_UNITS,
    showComingSoon: parsed !== null,
  }));

  useEffect(() => {
    if (!parsed) {
      // BR-004: missing/unparseable config → 00/00/00, "Coming soon"
      // hidden, exactly one console warning, never throw. `warnedRef`
      // absorbs React Strict Mode's dev-only double effect invocation.
      if (!warnedRef.current) {
        warnedRef.current = true;
        console.warn(
          `CountdownTimer: NEXT_PUBLIC_EVENT_START_AT is missing or invalid (${String(eventStartAt)}); showing 00/00/00.`,
        );
      }
      return;
    }

    const tick = () => setState(computeCountdown(parsed));
    tick();
    const intervalId = window.setInterval(tick, 1000);
    return () => window.clearInterval(intervalId);
  }, [parsed, eventStartAt]);

  return (
    // mm:2167:9035
    <div className="flex flex-col items-start gap-4">
      {state.showComingSoon ? (
        // mm:2167:9036 (mms_B1.2_Coming soon)
        <p className="text-2xl leading-8 font-bold text-white">{labels.comingSoon}</p>
      ) : null}
      {/* mm:2167:9037 — desktop gap is 40px; the tiles below are fixed-px
          (non-text) content that can't reflow internally, so at mobile they
          shrink instead (see DigitTile) and this row gets `flex-wrap` as a
          backstop so a still-too-narrow viewport stacks rather than
          overflows. */}
      <div className="flex flex-wrap items-center gap-4 sm:gap-10">
        <CountdownUnit value={state.days} label={labels.days} />
        <CountdownUnit value={state.hours} label={labels.hours} />
        <CountdownUnit value={state.minutes} label={labels.minutes} />
      </div>
    </div>
  );
}

function CountdownUnit({ value, label }: { value: string; label: string }) {
  // One tile per digit, not a fixed pair. `days` is zero-padded to 2 but is
  // not capped at 2: an event more than 99 days out yields "120", and
  // destructuring the first two characters rendered "12" — dropping a digit
  // and silently understating the countdown by 100 days. The test config
  // pins the event ~45 days out, which hid this rather than covering it.
  const digits = [...value];
  return (
    // mm:2167:9038 (Days unit; identical shape for Hours/Minutes)
    <div className="flex flex-col items-start gap-2 sm:gap-3.5">
      {/* mm:2167:9039 (Frame 485 digit row) — the only element allowed to
          carry the two raw digit characters, no whitespace/label inside. */}
      <div data-testid="countdown-value" className="flex items-center gap-2 sm:gap-3.5">
        {digits.map((digit, index) => (
          <DigitTile key={index} digit={digit} />
        ))}
      </div>
      {/* mm:2167:9042 (DAYS/HOURS/MINUTES label) — shrinks with the tiles
          above so it never becomes the widest part of the unit at mobile. */}
      <span className="text-base leading-6 font-bold text-white sm:text-2xl sm:leading-8">
        {label}
      </span>
    </div>
  );
}

/**
 * mm:2167:9040 (Group 5 digit tile — glass rectangle + digit character).
 *
 * ORCH-10: the MoMorph node declares `fontFamily: "Digital Numbers"` — a
 * Figma-local font with no Google Fonts entry and no vendored file in this
 * repo, so every browser silently falls back and the declaration would ship
 * a lie in the CSS. Rendered instead in the already-loaded Montserrat with
 * `font-variant-numeric: tabular-nums` (fixed-width digits, so ticking
 * doesn't jitter). If the licensed file is ever added to `public/fonts/`,
 * wire it through `next/font/local` here.
 */
function DigitTile({ digit }: { digit: string }) {
  return (
    <span className="relative flex h-[56px] w-[36px] items-center justify-center sm:h-[82px] sm:w-[51px]">
      <span
        aria-hidden
        className="absolute inset-0 rounded-lg border-[0.5px] border-[#FFEA9E] bg-gradient-to-b from-white to-white/10 opacity-50 backdrop-blur-[16px]"
      />
      <span className="relative font-montserrat text-[32px] leading-none tabular-nums text-white sm:text-[49px]">
        {digit}
      </span>
    </span>
  );
}
