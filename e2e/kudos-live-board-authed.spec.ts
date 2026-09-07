import { expect, test, type Locator, type Page } from "@playwright/test";
import { execSync } from "child_process";
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

// The seed deliberately creates ZERO `kudos_likes` rows (F004 § seed: likes are
// real per-viewer state, never seeded), so ANY row in that table is residue from
// a test run. That is why cleanup can safely delete by kudos id alone.
//
// It must NOT filter by a user id: `e2e/auth.setup.ts` signs up a brand-new user
// with a fresh uuid on every run, so a hardcoded uuid here would never match the
// row this run actually created — the delete would quietly affect nothing and the
// try/catch would swallow the miss, leaving a cleanup that only looks like it works.
const FIRST_KUDO_ID = 1; // The first card in the seed data

// Helper to clean up stray kudos_likes rows created by this test suite.
// Used in afterEach to restore idempotence when a test fails mid-execution.
function cleanupTestLikes() {
  try {
    const sql = `DELETE FROM kudos_likes WHERE kudos_id = ${FIRST_KUDO_ID};`;
    execSync(
      `docker exec supabase_db_my-app psql -U postgres -d postgres -c "${sql}"`,
      { stdio: "pipe" }
    );
  } catch {
    // Cleanup failure is non-fatal; log it but don't fail the test.
    console.warn("K-25 afterEach cleanup failed (non-fatal)");
  }
}

// ============================================================================
// Authenticated tests — /kudos (kudos-authed project, reuses e2e/.auth/user.json)
// ============================================================================

test.describe("Kudos Live Board screen — /kudos (kudos-authed)", () => {
  // Restore idempotence: clean up any stray kudos_likes rows if a test exits early.
  // K-25 is the only test in this suite that mutates kudos_likes, and it reverts
  // the mutation at the end. If it fails mid-execution, this cleanup ensures the
  // next run starts from a clean state (kudos_likes = 0).
  test.afterEach(() => {
    cleanupTestLikes();
  });

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
    // Increase timeout for this test since it involves multiple server round trips
    // (click, reload, click, reload). Under load with concurrent workers, the
    // Postgres round trip can exceed the default 5s expect() timeout. This does
    // not weaken the assertion — it just allows slow round trips to finish.
    test.setTimeout(60000);

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
