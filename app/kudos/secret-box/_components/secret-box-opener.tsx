"use client";

import Image from "next/image";
import { useState } from "react";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { OpenSecretBoxResult } from "@/lib/secret-box/contract";

type OpenerStatus = "idle" | "pending" | "error";

interface SecretBoxOpenerProps {
  canOpen: boolean;
  copy: Dictionary["secretBox"];
  openAction: () => Promise<OpenSecretBoxResult>;
}

/**
 * mm:1466:7684 / mm:1466:7685 / mm:1466:7686 — the clickable box (F009). A
 * Client Component: it is the one control on the screen with in-flight
 * state (FR-203/SM-001) and a post-open badge (DEC-01), so it owns local
 * state rather than re-deriving either from a prop the server can refresh
 * out from under it.
 *
 * `status`/`badge` are intentionally NOT keyed off any prop: `openAction`
 * revalidates the route after a successful open (phase 05), which re-renders
 * this component's parent with a fresh `unopenedCount` — if the badge lived
 * in a prop instead of local state, that refresh would wipe the very badge
 * the user just won (Risk Assessment, phase-04 plan).
 *
 * A failed open (`{ ok: false, reason }`) never guesses a new count for any
 * `reason` — `unopenedCount` is `SecretBoxPanel`'s own prop, refreshed by
 * the server via revalidation, not fabricated here.
 */
export function SecretBoxOpener({ canOpen, copy, openAction }: SecretBoxOpenerProps) {
  const [status, setStatus] = useState<OpenerStatus>("idle");
  const [badge, setBadge] = useState<{ label: string; imagePath: string } | null>(null);

  const disabled = !canOpen || status === "pending";

  async function handleClick() {
    // FR-203/SM-001: the native `disabled` attribute already blocks a
    // second click; this guard is the second, explicit layer the plan's
    // Risk Assessment calls for — a real state check, not CSS alone.
    if (disabled) return;

    setStatus("pending");
    const result = await openAction();

    if (result.ok) {
      setBadge({ label: result.badge.label, imagePath: result.badge.imagePath });
      setStatus("idle");
      return;
    }

    setStatus("error");
  }

  return (
    <div className="relative h-full w-full">
      {/* mm:1466:7684 — the clickable control itself, 557×557. */}
      <button
        type="button"
        data-testid="secret-box-opener"
        aria-label={copy.openerLabel}
        aria-busy={status === "pending"}
        disabled={disabled}
        onClick={handleClick}
        className="relative block h-full w-full cursor-pointer disabled:cursor-not-allowed"
      >
        {/* mm:1466:7686 — 558.47 square box artwork; the full composed
            gift-box-on-podium asset, fills the 557×557 slot exactly (both
            are 1:1). `alt` reuses `copy.openerLabel` ("Mở Secret Box") — it
            already contains the loanword "Box" the e2e alt-text contract
            (`getByAltText(/box|hộp/i)`) requires, so no new dictionary
            string is invented for a purely technical label. */}
        <Image
          src="/images/secret-box/box-unopened.png"
          alt={copy.openerLabel}
          fill
          sizes="557px"
          className="object-contain"
        />

        {/* mm:1466:7685 (MM_MEDIA_hiệu ứng box quà) — DELIBERATELY NOT
            RENDERED, and this is the measured reason rather than an
            omission.

            Phase 04 reproduced this node faithfully as a CSS background
            (546.535 square at +95/+108 from the slot origin, Figma's own
            `138.527%` scale and `-102.944px/-102.487px` offset) and flagged
            that it might double the glow already present in the box art.
            The rendered capture settled it, and the answer was worse than a
            double-up: `box-glow.png` is a dark-backed RGBA asset, not a
            transparent sparkle sheet, so at 138.527% scale it painted an
            opaque near-black rectangle that overflowed the 557 slot to the
            bottom-right and occluded the gift box, the lower hairline and
            the counter row entirely
            (`evidence/secret-box-entitled-1440.png`, first capture).

            In Figma the node composites against its siblings inside the
            frame; as a plain DOM layer it simply covers them. And it earns
            nothing even when composited: `box-unopened.png` is the fully
            composed 1000×1000 artwork — podium, box AND sparkle burst — as
            the reference frame image shows. The glow is already in the
            picture. The asset stays on disk under `public/images/secret-box/`
            so the decision is re-checkable, but nothing renders it. */}

        {/* DEC-01 — the awarded badge: 50% of the 557 slot width, centered,
            box art retained beneath. Local `badge` state, not a prop, so a
            post-open server refresh cannot wipe it. `alt` equals
            `rule_items.label` verbatim (BR-005, e2e SB-03) — never
            `copy.badgeAltPrefix`, which the dictionary reserves for an
            auxiliary caption this screen does not render. */}
        {badge ? (
          <div className="absolute top-1/2 left-1/2 h-1/2 w-1/2 -translate-x-1/2 -translate-y-1/2">
            <Image
              src={badge.imagePath}
              alt={badge.label}
              data-testid="secret-box-badge"
              fill
              sizes="280px"
              className="object-contain"
            />
          </div>
        ) : null}
      </button>

      {/* Unauthored — the *đã mở* frame that would draw an error state is
          `in_progress` with no spec. Overlaid (not flowed) so it never
          pushes the panel's hairline/counter row, which sit at fixed
          measured offsets below this 557×557 slot. */}
      {status === "error" ? (
        <p
          role="alert"
          className="pointer-events-none absolute inset-x-0 bottom-2 text-center text-sm font-bold text-white"
        >
          {copy.errorGeneric}
        </p>
      ) : null}
    </div>
  );
}
