import { expect, test, type Locator, type Page } from "@playwright/test";
import { execSync } from "child_process";
import fs from "node:fs";
import {
  ROUTE,
  FRAME_VIEWER_NAME,
  FRAME_VIEWER_ID,
  FRAME_VIEWER_DEPARTMENT,
  FRAME_VIEWER_BADGE_TIER,
  FRAME_RECEIVER_NAME,
  FRAME_RECEIVER_ID,
  COMPOSE_TARGET_NAME,
  ANONYMOUS_SENDER_LABEL,
  PROFILE_SESSION_META_FILE,
  BADGE_SLOT_COUNT,
  STATS_LABELS,
  DIRECTION_LABELS,
  EMPTY_STATES,
  END_OF_FEED_MESSAGE,
  SECRET_BOX_BUTTON_LABEL,
} from "./fixtures/profile-constants";

/**
 * Screen-level E2E for Profile bản thân (`/profile`) — MoMorph screen 3FoIx6ALVb,
 * file 9ypp4enmFmdK3YAFJLIu6C, test policy `e2e-red-first`.
 *
 * PROFILE-AUTHED PROJECT ONLY — authenticated tests requiring session.
 * Unauthenticated access control tests are in profile-anon.spec.ts.
 *
 * This file runs in the `profile-authed` Playwright project, which loads
 * its own session from `e2e/.auth/profile-user.json` created by profile-auth.setup.ts.
 * This isolation prevents authenticated.spec.ts's C9 global sign-out from affecting
 * these tests nondeterministically.
 *
 * Cleanup strategy: The seed creates zero kudos_likes rows, so ANY row in that table
 * is test residue. Cleanup deletes by kudos_id only, never by a hardcoded auth uuid
 * (which changes every run). Same principle for composed anonymous Kudos: delete by
 * sender's auth_user_id resolved at runtime, not a snapshotted uuid.
 */

/**
 * The name the sparse self hero must render: the local-part of the address
 * `profile-auth.setup.ts` signed up this run, which is the last link of the
 * identity fallback chain in `lib/profile/profile-data.ts`. Throws rather than
 * returning a placeholder — a missing sidecar means the setup project did not
 * run, and a test that quietly asserted `""` would pass on a blank hero.
 */
function sessionName(): string {
  const raw = fs.readFileSync(PROFILE_SESSION_META_FILE, "utf-8");
  const parsed = JSON.parse(raw) as { emailLocalPart?: unknown };
  if (typeof parsed.emailLocalPart !== "string" || parsed.emailLocalPart === "") {
    throw new Error(
      `${PROFILE_SESSION_META_FILE} carries no emailLocalPart — profile-auth.setup.ts did not run.`,
    );
  }
  return parsed.emailLocalPart;
}

/** The signed-up address itself — used only to delete the row `create_kudos()` provisioned for it. */
function sessionEmail(): string {
  const raw = fs.readFileSync(PROFILE_SESSION_META_FILE, "utf-8");
  const parsed = JSON.parse(raw) as { email?: unknown };
  if (typeof parsed.email !== "string" || parsed.email === "") {
    throw new Error(
      `${PROFILE_SESSION_META_FILE} carries no email — profile-auth.setup.ts did not run.`,
    );
  }
  return parsed.email;
}

const heroElement = (page: Page): Locator =>
  page.getByTestId("profile-hero");

const badgeRow = (page: Page): Locator =>
  page.getByTestId("profile-badge-row");

const badgeSlot = (page: Page): Locator =>
  page.getByTestId("profile-badge-slot");

const statCard = (page: Page): Locator =>
  page.getByTestId("profile-stats-card");

const statRow = (page: Page): Locator =>
  page.getByTestId("profile-stat");

const secretBoxButton = (page: Page): Locator =>
  page.getByTestId("profile-secret-box-button");

const writeBar = (page: Page): Locator =>
  page.getByTestId("profile-write-bar");

const directionTrigger = (page: Page): Locator =>
  page.getByTestId("profile-direction-trigger");

/**
 * One dropdown OPTION, by its bare label. The only correct way to reach an
 * option in this file — see `profile-constants.ts` § DIRECTION_LABELS for why
 * a bare `getByText` on either label is a strict-mode violation on the self
 * view (the trigger repeats the received label; the statistics card's
 * `Số Kudos bạn đã gửi:` collides with the sent one under `getByText`'s
 * case-insensitive substring default). Scoping is also STRICTER: the label
 * must be on an option, not merely somewhere on the page.
 */
const directionOption = (page: Page, label: string): Locator =>
  page.getByTestId("profile-direction-option").filter({ hasText: label });

const feed = (page: Page): Locator =>
  page.getByTestId("profile-feed");

const kudosCard = (page: Page): Locator =>
  page.getByTestId("kudos-card");

const kudosSender = (page: Page, card: Locator): Locator =>
  card.getByTestId("kudos-sender");

const kudosReceiver = (page: Page, card: Locator): Locator =>
  card.getByTestId("kudos-receiver");

const kudosHeart = (page: Page, card: Locator): Locator =>
  card.getByTestId("kudos-heart");

const kudosHeartCount = (page: Page, card: Locator): Locator =>
  card.getByTestId("kudos-heart-count");

// Helper to clean up stray kudos_likes rows created by tests.
function cleanupTestLikes(kudosId: number) {
  try {
    const sql = `DELETE FROM kudos_likes WHERE kudos_id = ${kudosId};`;
    execSync(
      `docker exec supabase_db_my-app psql -U postgres -d postgres -c "${sql}"`,
      { stdio: "pipe" }
    );
  } catch {
    console.warn(`Cleanup of kudos_likes for kudos_id=${kudosId} failed (non-fatal)`);
  }
}

function psql(sql: string, label: string) {
  try {
    execSync(
      `docker exec supabase_db_my-app psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c "${sql}"`,
      { stdio: "pipe" },
    );
  } catch {
    console.warn(`${label} failed (non-fatal)`);
  }
}

/**
 * Removes the one row SEC_002 composes, and the `sunners` row `create_kudos()`
 * provisioned for its author, so the database is handed back as it was found.
 *
 * Scoped by the run-unique `campaign` token and by the author's own address —
 * never by "every anonymous kudos" or "every `e2e-%` sunner", which would
 * reach into rows another Playwright project owns while it is still running
 * (projects share a database and can overlap across workers). The sunner row
 * is deleted only once nothing references it; `kudos.sender_id` is `no action`,
 * so a stray reference would abort the statement rather than orphan anything.
 * Child rows (hashtags, attachments, likes) cascade off the kudos delete.
 */
function cleanupComposedKudo(campaignToken: string, authorEmail: string) {
  const token = campaignToken.replace(/'/g, "''");
  const email = authorEmail.replace(/'/g, "''");
  psql(
    `DELETE FROM public.kudos WHERE campaign = '${token}';`,
    `Cleanup of composed kudos campaign=${campaignToken}`,
  );
  psql(
    `DELETE FROM public.sunners s
       WHERE s.auth_user_id = (SELECT u.id FROM auth.users u WHERE u.email = '${email}')
         AND NOT EXISTS (SELECT 1 FROM public.kudos k WHERE k.sender_id = s.id OR k.receiver_id = s.id);`,
    `Cleanup of provisioned sunners row for ${authorEmail}`,
  );
}

// ============================================================================
// Authenticated tests — /profile (profile-authed project)
// ============================================================================

test.describe("Profile screen — /profile (profile-authed)", () => {
  // Restore idempotence: clean up any stray kudos_likes rows if a test fails mid-execution
  test.afterEach(() => {
    // Cleanup likes from the first card (used by heart tests)
    cleanupTestLikes(1);
  });

  // ========================================================================
  // Access Control (ACC_001, ACC_002 covered by profile-anon.spec.ts)
  // ========================================================================

  // ========================================================================
  // Route Resolution (FUN_001–005)
  // ========================================================================

  test("TC_WEB_PROFILE_FUN_001 — /profile?id={other} renders that Sunner's profile", async ({
    page,
  }) => {
    await page.goto(`${ROUTE}?id=${FRAME_RECEIVER_ID}`);

    const hero = heroElement(page);
    await expect(hero).toBeVisible();

    // Assert hero shows the viewed Sunner (not the logged-in viewer)
    await expect(hero).toContainText(FRAME_RECEIVER_NAME);
  });

  /**
   * TC_WEB_PROFILE_FUN_002 — rewritten against the session this project
   * actually has.
   *
   * The authored case assumed the e2e viewer IS seeded sunner 1, so `?id=1`
   * would be `?id={self}`. It never is: `profile-auth.setup.ts` signs up a
   * brand-new user every run and a GET never provisions a `sunners` row
   * (BR-001), so this viewer's own `sunners.id` is `null` — and
   * clarifications A4 makes that the NORMAL authenticated case, not a fixture
   * defect. `?id=1` is therefore genuinely ANOTHER Sunner for this session,
   * and "renders the self view" was a false statement about the system.
   *
   * What survives is FUN_002's real subject: an explicit `?id=` is resolved
   * AGAINST THE VIEWER'S OWN IDENTITY, and the resolution never redirects nor
   * rewrites the URL. Both faces are exercised in one session, so no
   * degenerate resolver satisfies both:
   *   - `?id=1` keeps the query string verbatim and renders the OTHER face —
   *     a resolver treating a null viewer id as "matches anything" fails here;
   *   - the bare route renders the SELF face — a resolver that never resolves
   *     self fails here.
   *
   * NOT covered by any durable test, and reported rather than faked: the
   * `parsed === viewerSunnerId` canonicalization branch itself
   * (`lib/profile/resolve-profile-id.ts:74`) is unreachable for a session with
   * no roster row. Reaching it requires the e2e session to own a `sunners`
   * row, which changes what every other case in this file exercises (phase
   * 09's unresolved question 1) — a test-design call above this phase.
   */
  test("TC_WEB_PROFILE_FUN_002 — ?id= is resolved against the viewer's own identity, with no redirect", async ({
    page,
  }) => {
    await page.goto(`${ROUTE}?id=${FRAME_VIEWER_ID}`);

    // No redirect and no rewrite: path and query survive verbatim.
    const other = new URL(page.url());
    expect(other.pathname).toBe(ROUTE);
    expect(other.searchParams.getAll("id")).toEqual([String(FRAME_VIEWER_ID)]);

    // Resolved relative to the viewer (who owns no roster row) -> the OTHER
    // face: that Sunner's hero, a write bar, and NO statistics card at all.
    await expect(heroElement(page)).toContainText(FRAME_VIEWER_NAME);
    await expect(writeBar(page)).toBeVisible();
    await expect(statCard(page)).toHaveCount(0);

    // The self face exists and is reached by the bare route, unqueried.
    await page.goto(ROUTE);
    const self = new URL(page.url());
    expect(self.pathname).toBe(ROUTE);
    expect(self.search).toBe("");
    await expect(statCard(page)).toBeVisible();
    await expect(writeBar(page)).toHaveCount(0);
  });

  test("TC_WEB_PROFILE_FUN_003 — ?id={non-existent} returns 404", async ({
    page,
  }) => {
    const res = await page.goto(`${ROUTE}?id=99999999`, { waitUntil: "networkidle" });

    // Next.js notFound() renders at requested URL with 404 status (no redirect to /not-found)
    expect(res?.status()).toBe(404);
    // Profile content not rendered on 404
    await expect(heroElement(page)).toHaveCount(0);
  });

  test("TC_WEB_PROFILE_FUN_004 — malformed ?id values return 404", async ({
    page,
  }) => {
    const malformedIds = ["banana", "' or 1=1", "42.5", "11111111-1111-4111-8111"];

    for (const id of malformedIds) {
      const res = await page.goto(`${ROUTE}?id=${encodeURIComponent(id)}`, {
        waitUntil: "networkidle",
      });
      // Each malformed id returns 404 with no profile content
      expect(res?.status()).toBe(404);
      await expect(heroElement(page)).toHaveCount(0);
    }
  });

  test("TC_WEB_PROFILE_FUN_005 — empty and repeated ?id values", async ({
    page,
  }) => {
    // Empty ?id= renders self view
    await page.goto(`${ROUTE}?id=`);
    const stats = statCard(page);
    await expect(stats).toBeVisible();

    // Repeated ?id=1&id=2 returns 404
    const res = await page.goto(`${ROUTE}?id=${FRAME_VIEWER_ID}&id=${FRAME_RECEIVER_ID}`, {
      waitUntil: "networkidle",
    });
    expect(res?.status()).toBe(404);
    await expect(heroElement(page)).toHaveCount(0);
  });

  // ========================================================================
  // Hero + Badges (GUI_001, GUI_002, GUI_003, GUI_009)
  // ========================================================================

  /**
   * TC_WEB_PROFILE_GUI_001 — rewritten for the same reason as FUN_002: the
   * authored case pointed the bare route at the frame viewer's populated hero,
   * but the bare route is this session's own SPARSE hero (A4). Asserting the
   * frame viewer's name there was asserting somebody else's data.
   *
   * Both faces of the hero are asserted instead, which is strictly more than
   * the original single `toContainText`:
   *   - the POPULATED hero (`?id=1`) carries avatar, name, department and the
   *     tier pill — the four things the frame's `mms_A.2_Name` contains;
   *   - the SPARSE hero carries the JWT identity fallback's name and, per
   *     GUI_009 / `profile-data.ts`, NO tier pill and NO department (the
   *     department text and its 4x4 separator dot are hidden together).
   *
   * AMEND-1: no hoa-thi stars exist in this design, so none is asserted.
   */
  test("TC_WEB_PROFILE_GUI_001 — hero renders avatar, name, department, tier badge", async ({
    page,
  }) => {
    // --- populated hero -----------------------------------------------------
    await page.goto(`${ROUTE}?id=${FRAME_VIEWER_ID}`);

    const hero = heroElement(page);
    await expect(hero).toBeVisible();
    await expect(hero.getByRole("heading", { level: 1 })).toHaveText(FRAME_VIEWER_NAME);
    await expect(hero).toContainText(FRAME_VIEWER_DEPARTMENT);
    await expect(hero.locator("img").first()).toBeVisible();

    const tierBadge = page.getByTestId("profile-tier-badge");
    await expect(tierBadge).toHaveText(FRAME_VIEWER_BADGE_TIER);

    // --- sparse hero (this session's own) -----------------------------------
    await page.goto(ROUTE);

    await expect(hero).toBeVisible();
    // The identity fallback: the email local-part, exactly as the setup
    // recorded it. Not a pattern — the wrong name would still match a pattern.
    await expect(hero.getByRole("heading", { level: 1 })).toHaveText(sessionName());
    await expect(hero.locator("img").first()).toBeVisible();
    // GUI_009 — the pill is ABSENT at zero received, not rendered as "New Hero".
    await expect(page.getByTestId("profile-tier-badge")).toHaveCount(0);
    // A null department hides the text and the separator dot together, so no
    // seeded department name can appear on this face.
    await expect(hero).not.toContainText(FRAME_VIEWER_DEPARTMENT);
  });

  test("TC_WEB_PROFILE_GUI_002 — 6 badge slots always rendered, all greyed", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const slots = badgeSlot(page);
    await expect(slots).toHaveCount(BADGE_SLOT_COUNT);

    // All slots should be visible (not unlocked, not hidden)
    for (let i = 0; i < BADGE_SLOT_COUNT; i++) {
      await expect(slots.nth(i)).toBeVisible();
    }
  });

  test("TC_WEB_PROFILE_GUI_003 — badge heading is first-person on self, neutral on other", async ({
    page,
  }) => {
    // Self view: first-person heading
    await page.goto(ROUTE);
    await expect(badgeRow(page)).toContainText("Bộ sưu tập icon của tôi");

    // Other's view: neutral heading
    await page.goto(`${ROUTE}?id=${FRAME_RECEIVER_ID}`);
    await expect(badgeRow(page)).toContainText("Bộ sưu tập icon");
    // Should NOT contain the first-person version on another's profile
    await expect(badgeRow(page)).not.toContainText("của tôi");
  });

  test("TC_WEB_PROFILE_GUI_009 — sparse profile renders without broken elements", async ({
    page,
  }) => {
    // Self view shows sparse state (viewer has no sunners row)
    await page.goto(ROUTE);

    const hero = heroElement(page);
    await expect(hero).toBeVisible();

    // 6 badge slots still render
    const slots = badgeSlot(page);
    await expect(slots).toHaveCount(BADGE_SLOT_COUNT);
  });

  // ========================================================================
  // Statistics Card + Write Bar (GUI_004, GUI_005, FUN_006, FUN_007, FUN_008)
  // ========================================================================

  test("TC_WEB_PROFILE_GUI_004 — self view shows 5 statistics rows", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const stats = statCard(page);
    await expect(stats).toBeVisible();

    // Check all 5 stat labels are present
    const rows = statRow(page);
    await expect(rows).toHaveCount(5);

    for (const label of STATS_LABELS) {
      await expect(stats).toContainText(label);
    }
  });

  test("TC_WEB_PROFILE_GUI_005 — Secret Box rows show 0, button is disabled", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const stats = statCard(page);

    // Secret Box opened and unopened should both be 0
    await expect(stats).toContainText("Số Secret Box bạn đã mở:");
    await expect(stats).toContainText("Số Secret Box chưa mở:");

    // Verify the values are 0 by checking the stat rows
    const rows = statRow(page);
    const lastRow = rows.nth(4); // 5th row (Secret Box unopened)
    await expect(lastRow).toContainText("0");

    // Button is rendered but disabled
    const button = secretBoxButton(page);
    await expect(button).toBeVisible();
    await expect(button).toBeDisabled();
    await expect(button).toContainText(SECRET_BOX_BUTTON_LABEL);

    // Clicking the disabled button does nothing.
    // `force: true` is required, not a concession: `toBeDisabled()` above and
    // `click()`'s enabled-actionability check route through the SAME predicate
    // (elementState -> getAriaDisabled = isNativelyDisabled || aria-disabled),
    // so a bare click() on anything that satisfies the assertion can only time
    // out. The spec requires the button be disabled, so the click is forced and
    // the *effect* is asserted instead.
    const urlBeforeClick = page.url();
    await button.click({ force: true });
    // No navigation, and the button is still disabled after being clicked.
    expect(page.url()).toBe(urlBeforeClick);
    expect(page.url()).toContain(ROUTE);
    await expect(button).toBeDisabled();
  });

  test("TC_WEB_PROFILE_FUN_006 — another's profile shows write-Kudo bar, no stats", async ({
    page,
  }) => {
    await page.goto(`${ROUTE}?id=${FRAME_RECEIVER_ID}`);

    // Write bar is shown
    const bar = writeBar(page);
    await expect(bar).toBeVisible();
    await expect(bar).toContainText(FRAME_RECEIVER_NAME);

    // Stats card is NOT shown on another's profile
    const stats = statCard(page);
    await expect(stats).not.toBeVisible();
  });

  test("TC_WEB_PROFILE_FUN_007 — write-Kudo bar links to /kudos/new?receiverId={id}", async ({
    page,
  }) => {
    await page.goto(`${ROUTE}?id=${FRAME_RECEIVER_ID}`);

    const bar = writeBar(page);
    // The bar should link to /kudos/new with receiverId
    const link = bar.getByRole("link");
    const href = await link.getAttribute("href");
    expect(href).toMatch(new RegExp(`/kudos/new\\?receiverId=${FRAME_RECEIVER_ID}`));
  });

  test("TC_WEB_PROFILE_FUN_008 — own profile shows stats, no write-Kudo bar", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Stats card is shown
    const stats = statCard(page);
    await expect(stats).toBeVisible();

    // Write bar is NOT shown on own profile
    const bar = writeBar(page);
    await expect(bar).not.toBeVisible();
  });

  // ========================================================================
  // Direction Dropdown (FUN_009, FUN_010, FUN_011, FUN_012, SEC_001)
  // ========================================================================

  test("TC_WEB_PROFILE_FUN_009 — self view dropdown offers both Received and Sent", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const trigger = directionTrigger(page);
    await expect(trigger).toContainText(DIRECTION_LABELS.received); // Received is default active

    // Open dropdown
    await trigger.click();

    // Both options are present, each reached through `directionOption` for
    // the strict-mode reason documented on that helper.
    await expect(page.getByTestId("profile-direction-option")).toHaveCount(2);
    await expect(directionOption(page, DIRECTION_LABELS.received)).toBeVisible();
    await expect(directionOption(page, DIRECTION_LABELS.sent)).toBeVisible();
  });

  test("TC_WEB_PROFILE_SEC_001 — another's profile dropdown shows Received only", async ({
    page,
  }) => {
    await page.goto(`${ROUTE}?id=${FRAME_RECEIVER_ID}`);

    const trigger = directionTrigger(page);
    await expect(trigger).toContainText(DIRECTION_LABELS.received);

    // Open dropdown
    await trigger.click();

    // Only one option should be visible (Received)
    await expect(page.getByTestId("profile-direction-option")).toHaveCount(1);
    await expect(directionOption(page, DIRECTION_LABELS.received)).toBeVisible();

    // Search entire page: no Sent text anywhere
    const body = page.locator("body");
    await expect(body).not.toContainText(DIRECTION_LABELS.sent);
  });

  test("TC_WEB_PROFILE_FUN_010 — switching direction discards previous pages", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const trigger = directionTrigger(page);
    const feedArea = feed(page);

    // Received is the committed direction on first render (DEC-001), and its
    // OWN empty copy is what is on screen.
    await expect(trigger).toContainText(DIRECTION_LABELS.received);
    await expect(feedArea).toContainText(EMPTY_STATES.received);

    // Switch to Sent.
    await trigger.click();
    const sentOption = directionOption(page, DIRECTION_LABELS.sent);
    await expect(sentOption).toHaveCount(1);
    await sentOption.click();

    // The trigger only moves once the new page has landed (FR-403) ...
    await expect(trigger).toContainText(DIRECTION_LABELS.sent);
    // ... and the previous direction's content is DISCARDED, not appended to:
    // the committed empty copy is Sent's and Received's is gone. Asserting the
    // trigger alone would pass on a feed that never swapped.
    await expect(feedArea).toContainText(EMPTY_STATES.sent);
    await expect(feedArea).not.toContainText(EMPTY_STATES.received);
    await expect(kudosCard(page)).toHaveCount(0);
  });

  test("TC_WEB_PROFILE_FUN_011 — re-picking active direction is a no-op", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const trigger = directionTrigger(page);
    const initialText = await trigger.textContent();

    // Click the active direction again (see `directionOption` for why the
    // locator is scoped).
    await trigger.click();
    const receivedOption = directionOption(page, DIRECTION_LABELS.received);
    await expect(receivedOption).toHaveCount(1);
    await receivedOption.click();

    // Trigger text should be unchanged
    const newText = await trigger.textContent();
    expect(newText).toBe(initialText);
  });

  test("TC_WEB_PROFILE_FUN_012 — each direction has its own empty state copy", async ({
    page,
  }) => {
    // Note: The seeded viewer (id=1) is the sender in the seed data, not the receiver.
    // So the logged-in e2e user (different session) has no received or sent Kudos.
    // This test therefore exercises the empty states of a fresh user.

    await page.goto(ROUTE);

    const feedArea = feed(page);

    // Check Received empty state
    await expect(feedArea).toContainText(EMPTY_STATES.received);

    // Switch to Sent and check its empty state. The option locator is scoped
    // (see `directionOption`): on this face the statistics card's
    // `Số Kudos bạn đã gửi:` label also matches a bare `getByText("Đã gửi")`.
    const trigger = directionTrigger(page);
    await trigger.click();
    const sentOption = directionOption(page, DIRECTION_LABELS.sent);
    await expect(sentOption).toHaveCount(1);
    await sentOption.click();

    await expect(feedArea).toContainText(EMPTY_STATES.sent);
    // The two copies are distinct, so this proves the swap really committed.
    await expect(feedArea).not.toContainText(EMPTY_STATES.received);
  });

  // ========================================================================
  // Feed + Paging (FUN_013, GUI_006, GUI_007)
  // ========================================================================

  test("TC_WEB_PROFILE_FUN_013 — feed paging with infinite scroll and end-of-feed message", async ({
    page,
  }) => {
    // Navigate to a profile with many Kudos (frame receiver, id=2)
    await page.goto(`${ROUTE}?id=${FRAME_RECEIVER_ID}`);

    const feedArea = feed(page);
    await expect(feedArea).toBeVisible();

    // At id=2 (frame receiver) there are 25 seeded received Kudos, so page 1
    // is a partial view and the sentinel must be mounted.
    const cards = kudosCard(page);
    const firstPageCount = await cards.count();
    expect(firstPageCount).toBeGreaterThan(0);
    await expect(page.getByTestId("profile-feed-sentinel")).toHaveCount(1);
    await expect(page.getByTestId("profile-feed-end")).toHaveCount(0);

    // Drive the keyset feed to its end. Bounded, and the assertions AFTER the
    // loop are unconditional: the previous form wrapped the end-of-feed check
    // in `if (await endMessage.isVisible())`, so it asserted nothing whenever
    // paging failed — exactly the shape that survives a broken feed.
    const endMessage = page.getByTestId("profile-feed-end");
    for (let scrolls = 0; scrolls < 12; scrolls += 1) {
      if (await endMessage.count()) break;
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(400);
    }

    // Paging really happened, it stopped, and it said so.
    await expect(endMessage).toBeVisible();
    await expect(endMessage).toHaveText(END_OF_FEED_MESSAGE);
    expect(await cards.count()).toBeGreaterThan(firstPageCount);
    // `hasMore` false unmounts the sentinel, which is what stops the observer.
    await expect(page.getByTestId("profile-feed-sentinel")).toHaveCount(0);
  });

  test("TC_WEB_PROFILE_GUI_006 — feed cards match board format (shape and masking)", async ({
    page,
  }) => {
    await page.goto(`${ROUTE}?id=${FRAME_RECEIVER_ID}`);

    const card = kudosCard(page).first();
    await expect(card).toBeVisible();

    // Card should have sender, receiver, and other board elements
    const sender = kudosSender(page, card);
    const receiver = kudosReceiver(page, card);

    await expect(sender).toBeVisible();
    await expect(receiver).toBeVisible();

    // Heart and other interactions should be present
    const heart = kudosHeart(page, card);
    await expect(heart).toBeVisible();
  });

  test("TC_WEB_PROFILE_GUI_007 — no Spam chip on cards", async ({
    page,
  }) => {
    await page.goto(`${ROUTE}?id=${FRAME_RECEIVER_ID}`);

    const card = kudosCard(page).first();

    // Look for any "Spam" text on the card
    const body = page.locator("body");
    await expect(body).not.toContainText("Spam");
  });

  // ========================================================================
  // Card Interactions (FUN_014, FUN_015)
  // ========================================================================

  test("TC_WEB_PROFILE_FUN_014 — heart toggle updates count to server value", async ({
    page,
  }) => {
    await page.goto(`${ROUTE}?id=${FRAME_RECEIVER_ID}`);

    const card = kudosCard(page).first();
    const heart = kudosHeart(page, card);
    const count = kudosHeartCount(page, card);

    // Verify heart is enabled (not sender's own kudo)
    await expect(heart).toBeEnabled();

    // Capture initial state
    const initialPressed = await heart.getAttribute("aria-pressed");
    const initialCount = await count.textContent();

    // Click heart
    await heart.click();

    // aria-pressed should flip
    const expectedPressed = initialPressed === "true" ? "false" : "true";
    await expect(heart).toHaveAttribute("aria-pressed", expectedPressed);

    // Count should change (server-authoritative)
    await expect(count).not.toHaveText(initialCount ?? "");

    // Revert (click again)
    await heart.click();
    await expect(heart).toHaveAttribute("aria-pressed", initialPressed ?? "");
    await expect(count).toHaveText(initialCount ?? "");
  });

  /**
   * TC_WEB_PROFILE_FUN_015 — rewritten because the authored form could not
   * fail. It looked for the tag as `card.locator("a")`, but
   * `kudos-hashtag-row.tsx:32` renders a `<button>` (test-contract.md § Kudos
   * card mandates buttons, not links), so the locator resolved to nothing,
   * `isVisible()` was false, and the whole body — both URL assertions
   * included — was skipped. It would have kept passing if the link were
   * deleted outright.
   *
   * The destination is now asserted the way phase 09 proved it: not by the URL
   * alone, which passes on a half-truth, but by the BOARD'S OWN FILTER STATE
   * and the contents of the cards it left on screen.
   *
   * The tag NAME carries no `#` — `hashtags.name` is e.g. `Toàn diện` and
   * `kudos-hashtag-row.tsx:39` renders the `#` itself, so `?hashtag=` sends
   * the bare name. Recorded because "fixing" this to `?hashtag=#tag` would
   * break a working link.
   */
  test("TC_WEB_PROFILE_FUN_015 — hashtag click navigates to filtered board", async ({
    page,
  }) => {
    await page.goto(`${ROUTE}?id=${FRAME_RECEIVER_ID}`);

    // Unconditional: the seeded feed carries hashtags, so a feed with none is
    // itself a failure rather than a reason to assert nothing.
    const hashtag = feed(page).getByTestId("kudos-hashtag").first();
    await expect(hashtag).toBeVisible();

    const rendered = (await hashtag.innerText()).trim();
    expect(rendered).toMatch(/^#\S/);
    const tagName = rendered.slice(1);

    await hashtag.click();
    await page.waitForURL((url) => url.pathname === "/kudos");

    // The deep link carries the BARE name, exactly once.
    const landed = new URL(page.url());
    expect(landed.pathname).toBe("/kudos");
    expect(landed.searchParams.getAll("hashtag")).toEqual([tagName]);

    // The board actually filtered on it: that option, and only that option, is
    // selected in the hashtag filter menu.
    await page.getByTestId("filter-hashtag").click();
    const menu = page.getByTestId("filter-menu-hashtag");
    await expect(menu).toBeVisible();
    await expect(menu.getByRole("option", { selected: true })).toHaveCount(1);
    await expect(menu.getByRole("option", { selected: true })).toHaveText(tagName);

    // ... and every card ALL KUDOS left on screen carries the tag. Scoped to
    // that section because the highlight carousel renders the same filtered
    // set again, and its flanking slides are `aria-hidden`.
    const boardCards = page.getByTestId("all-kudos-section").getByTestId("kudos-card");
    const boardCardCount = await boardCards.count();
    expect(boardCardCount).toBeGreaterThan(0);
    for (let index = 0; index < boardCardCount; index += 1) {
      await expect(
        boardCards.nth(index).getByTestId("kudos-hashtag").filter({ hasText: rendered }),
      ).toHaveCount(1);
    }
  });

  // ========================================================================
  // Security (SEC_002, SEC_003, SEC_004)
  // ========================================================================

  /**
   * TC_WEB_PROFILE_SEC_002 — rewritten from a test that could not fail into
   * the durable owner of `revealOwnAnonymous`.
   *
   * The authored form wrapped every compose step in `if (await
   * x.isVisible())` against locators that matched nothing, then asserted only
   * `expect(feedArea).toBeVisible()` — true whether or not any Kudo was
   * composed, let alone revealed. Phase 05 proved the real behaviour at
   * payload level; with no unit runner in this repo, this is where it lives.
   *
   * Both directions of the guarantee are asserted against ONE real row
   * composed through the real form:
   *   - the author's own Sent list names the AUTHOR (`revealOwnAnonymous`,
   *     `map-kudos-card.ts:139`) and still refuses the heart (`canLike:false`
   *     — a revealed row is not a likeable row);
   *   - the SAME row on the public board is the redacted stub, with no
   *     `kudos-sender` element at all and no trace of the author's name.
   *
   * That second half is what makes the first half a security statement rather
   * than a rendering one: an over-broad reveal would pass the Sent-list
   * assertions and fail here. The masking is the database's
   * (`public.kudos_readable`), per row, on caller identity.
   *
   * The recipient is sunner 9, not the frame viewer or receiver — see
   * `COMPOSE_TARGET_NAME`. The row and the `sunners` row `create_kudos()`
   * provisions for the author are both removed in the `finally`, so the
   * database is handed back as it was found.
   */
  test("TC_WEB_PROFILE_SEC_002 — own anonymous Kudo is named in the author's Sent list and masked for everyone else", async ({
    page,
    browser,
  }) => {
    const token = `SEC002-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const author = sessionName();

    try {
      // --- compose one real anonymous Kudo through the real form -----------
      await page.goto("/kudos/new");
      await expect(page.getByTestId("compose-form")).toBeVisible();

      await page.getByTestId("recipient-input").fill(COMPOSE_TARGET_NAME);
      const recipientOption = page
        .getByTestId("recipient-menu")
        .getByRole("option")
        .filter({ hasText: COMPOSE_TARGET_NAME });
      await expect(recipientOption).toHaveCount(1);
      await recipientOption.click();
      await expect(page.getByTestId("recipient-selected")).toContainText(COMPOSE_TARGET_NAME);

      // The title becomes `kudos.campaign`, which is how the row is found
      // again on both faces and deleted afterwards.
      await page.getByTestId("title-input").fill(token);
      await page.getByTestId("body-editor").fill(`${token} anonymous body`);

      await page.getByTestId("hashtag-add").click();
      await page.getByTestId("hashtag-menu").getByRole("option").first().click();
      await expect(page.getByTestId("hashtag-chip")).toHaveCount(1);

      // Anonymous, with the display name left blank, so the mask falls back to
      // the neutral label rather than an authored alias.
      const anonymous = page.getByTestId("anonymous-checkbox");
      await anonymous.check();
      await expect(anonymous).toBeChecked();
      await expect(page.getByTestId("anonymous-name-input")).toHaveValue("");

      const submit = page.getByTestId("compose-submit");
      await expect(submit).toHaveAttribute("data-submit-ready", "true");
      await submit.click();
      // `createKudos` redirects to /kudos only after the row is written.
      await page.waitForURL((url) => url.pathname === "/kudos", { timeout: 20_000 });

      // --- the author's own Sent list reveals them -------------------------
      await page.goto(ROUTE);
      const trigger = directionTrigger(page);
      await trigger.click();
      const sentOption = directionOption(page, DIRECTION_LABELS.sent);
      await expect(sentOption).toHaveCount(1);
      await sentOption.click();
      await expect(trigger).toContainText(DIRECTION_LABELS.sent);

      const ownCard = feed(page).getByTestId("kudos-card").filter({ hasText: token });
      await expect(ownCard).toHaveCount(1);
      // The real sender chip, carrying the author's own name. `AnonymousSenderChip`
      // renders NO `kudos-sender`, so its presence is the reveal itself.
      await expect(ownCard.getByTestId("kudos-sender")).toHaveCount(1);
      await expect(ownCard.getByTestId("kudos-sender")).toContainText(author);
      await expect(ownCard).not.toContainText(ANONYMOUS_SENDER_LABEL);
      await expect(ownCard.getByTestId("kudos-receiver")).toContainText(COMPOSE_TARGET_NAME);
      // `sentAnonymously` stays true, so the heart stays refused: the author
      // cannot like their own Kudo even on the list that names them.
      await expect(ownCard.getByTestId("kudos-heart")).toBeDisabled();

      // --- the SAME row, read with no session, is the redacted stub --------
      const origin = new URL(page.url()).origin;
      const anonContext = await browser.newContext({ storageState: undefined });
      try {
        const anonPage = await anonContext.newPage();
        await anonPage.goto(`${origin}/kudos`);
        // Scoped to ALL KUDOS: the highlight carousel renders the same cards,
        // so an unscoped lookup would resolve to two.
        const publicCard = anonPage
          .getByTestId("all-kudos-section")
          .getByTestId("kudos-card")
          .filter({ hasText: token });
        await expect(publicCard).toHaveCount(1);
        await expect(publicCard.getByTestId("kudos-sender")).toHaveCount(0);
        await expect(publicCard).toContainText(ANONYMOUS_SENDER_LABEL);
        await expect(publicCard).not.toContainText(author);
      } finally {
        await anonContext.close();
      }
    } finally {
      cleanupComposedKudo(token, sessionEmail());
    }
  });

  test("TC_WEB_PROFILE_SEC_004 — neither face of the route exposes an email or an auth uuid", async ({
    page,
  }) => {
    // BOTH faces, per the phase file: the self face renders the JWT identity
    // fallback (the email LOCAL-PART, which is not an address) and the other
    // face renders a roster row. Neither may carry the address itself or the
    // auth uuid `viewer.userId` deliberately keeps server-side (FR-603).
    for (const url of [ROUTE, `${ROUTE}?id=${FRAME_RECEIVER_ID}`]) {
      await page.goto(url);
      await expect(heroElement(page)).toBeVisible();

      const html = await page.evaluate(() => document.documentElement.outerHTML);
      expect(html, `auth uuid leaked on ${url}`).not.toMatch(
        /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i,
      );
      expect(html, `email address leaked on ${url}`).not.toMatch(
        /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/,
      );
    }
  });
});
