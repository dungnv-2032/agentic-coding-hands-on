import { expect, test, type Locator, type Page } from "@playwright/test";
import { ROUTE } from "./fixtures/kudos-constants";

/**
 * Screen-level E2E for "Sun* Kudos - Live board" (`/kudos`) — MoMorph screen
 * `MaZUn5xHXZ` (file `9ypp4enmFmdK3YAFJLIu6C`), test policy `e2e-red-first`.
 *
 * KUDOS-AUTHED PROJECT ONLY — authenticated tests requiring session (K-10, K-25).
 * Unauthenticated tests (K-0 to K-24) are in kudos-live-board.spec.ts.
 *
 * This file runs in the `kudos-authed` Playwright project, which reuses
 * the session created by the shared `setup` project (`e2e/.auth/user.json`).
 */

const kudosCard = (page: Page): Locator =>
  page.getByTestId("kudos-card");

// ============================================================================
// Authenticated tests — /kudos (kudos-authed project, reuses e2e/.auth/user.json)
// ============================================================================

test.describe("Kudos Live Board screen — /kudos (kudos-authed)", () => {
  // K-10 — heart toggle flips aria-pressed and moves count by 1 (authed viewer).
  test("K-10 — heart toggle flips aria-pressed and updates count by 1", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const card = kudosCard(page).first();
    const heart = card.getByTestId("kudos-heart");
    const count = card.getByTestId("kudos-heart-count");

    // The heart MUST be actionable in this project: the storageState user is a
    // real auth user and is not the sender of the first card, so `canLike` is
    // true. A silent `return` here would let this test pass vacuously and
    // report green while asserting nothing — assert instead of skipping.
    await expect(heart).toBeEnabled();

    // Capture initial state
    const initialPressed = await heart.getAttribute("aria-pressed");
    const initialCount = await count.textContent();

    // Determine expected new value (toggle the boolean string)
    const expectedPressed = initialPressed === "true" ? "false" : "true";

    // Click the heart
    await heart.click();

    // Verify aria-pressed flips (auto-retry, tolerates timing variation)
    await expect(heart).toHaveAttribute("aria-pressed", expectedPressed);

    // Verify count changed (auto-retry)
    await expect(count).not.toHaveText(initialCount ?? "");

    // test-contract.md: "A second click returns both to the original values."
    // Asserting it also leaves `kudos_likes` exactly as the seed left it, so
    // the suite is idempotent and a later run does not start from a mutated
    // heart count.
    await heart.click();
    await expect(heart).toHaveAttribute("aria-pressed", initialPressed ?? "");
    await expect(count).toHaveText(initialCount ?? "");
  });

  // K-25 — heart persists: click, reload, aria-pressed + count hold new values; click again, reload, both return to originals.
  // PERSISTENCE PROOF: The reload assertions demonstrate real Supabase persistence, not client state.
  test("K-25 — heart persists across page reload", async ({ page }) => {
    await page.goto(ROUTE);
    await page.waitForLoadState("networkidle");

    const card = kudosCard(page).first();
    const heart = card.getByTestId("kudos-heart");
    const count = card.getByTestId("kudos-heart-count");

    // Same rule as K-10: this is the load-bearing persistence proof, so a
    // disabled heart must fail loudly rather than short-circuit to a green.
    await expect(heart).toBeEnabled();

    // Capture initial state
    const initialPressed = await heart.getAttribute("aria-pressed");
    const initialCount = await count.textContent();
    const expectedPressed = initialPressed === "true" ? "false" : "true";

    // Click the heart; the button is server-authoritative, so this assertion
    // only passes once the insert has actually committed — which is what makes
    // the reload below a real persistence proof rather than a race.
    await heart.click();
    await expect(heart).toHaveAttribute("aria-pressed", expectedPressed);
    await expect(count).not.toHaveText(initialCount ?? "");

    // Reload the page
    await page.reload();
    await page.waitForLoadState("networkidle");

    // Re-acquire the locators after reload
    const cardAfterReload = kudosCard(page).first();
    const heartAfterReload = cardAfterReload.getByTestId("kudos-heart");
    const countAfterReload = cardAfterReload.getByTestId("kudos-heart-count");

    // PERSISTENCE PROOF: The new values should persist after reload (Supabase layer verified)
    // After reload, aria-pressed should remain flipped (persistence proof)
    await expect(heartAfterReload).toHaveAttribute("aria-pressed", expectedPressed);
    // After reload, count should have changed from initial (persistence proof)
    await expect(countAfterReload).not.toHaveText(initialCount ?? "");

    // Click again to toggle back to original
    await heartAfterReload.click();
    // Verify aria-pressed flips back
    await expect(heartAfterReload).toHaveAttribute("aria-pressed", initialPressed ?? "");
    // Verify count reverts
    await expect(countAfterReload).toHaveText(initialCount ?? "");

    // Reload once more to verify the original values persist
    await page.reload();
    await page.waitForLoadState("networkidle");

    const cardAfterSecondReload = kudosCard(page).first();
    const heartAfterSecondReload = cardAfterSecondReload.getByTestId("kudos-heart");
    const countAfterSecondReload = cardAfterSecondReload.getByTestId("kudos-heart-count");

    // Final verification: original values persist
    await expect(heartAfterSecondReload).toHaveAttribute("aria-pressed", initialPressed ?? "");
    await expect(countAfterSecondReload).toHaveText(initialCount ?? "");
  });
});
