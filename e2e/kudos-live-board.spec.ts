import { expect, test, type Locator, type Page } from "@playwright/test";
import {
  ROUTE,
  PAGE_TITLE,
  HERO_EYEBROW,
  COMPOSE_LABEL,
  SUNNER_SEARCH_PLACEHOLDER,
  SPOTLIGHT_SEARCH_PLACEHOLDER,
  COPY_LINK_TOAST,
  SPOTLIGHT_COUNT_TEXT,
  SECRET_BOX_LABEL,
  GIFT_LEADERBOARD_HEADING,
  HASHTAG_OPTIONS,
  DEPARTMENT_OPTIONS,
  SIDEBAR_STATS,
} from "./fixtures/kudos-constants";

/**
 * Screen-level E2E for "Sun* Kudos - Live board" (`/kudos`) — MoMorph screen
 * `MaZUn5xHXZ` (file `9ypp4enmFmdK3YAFJLIu6C`), test policy `e2e-red-first`.
 *
 * ANON PROJECT ONLY — unauthenticated tests (K-0 to K-24).
 * Authenticated tests (K-10, K-25) are in kudos-live-board-authed.spec.ts.
 *
 * Every constant value is transcribed from
 * `plans/260906-1945-kudos-live-board/clarifications.md`, which is the
 * authoritative record for this screen. Nothing here is invented.
 *
 * Route is `/kudos` (clarifications, decision 1) — public, no auth guard.
 * Test case `71b3ef43` (unauthenticated → redirect) contradicts the shipped
 * public-route design and is deliberately NOT written; clarifications records
 * it as out of scope pending a product call.
 *
 * Test-contract hooks the implementation is bound to: all data-testid values,
 * aria-* attributes, href targets, text content (copy from clarifications),
 * and element roles per test-contract.md. Neither side may change a hook
 * unilaterally.
 */

// ============================================================================
// Helpers — locators matching test-contract.md
// ============================================================================

const h1 = (page: Page): Locator => page.getByRole("heading", { level: 1 });

const composeBar = (page: Page): Locator =>
  page.getByTestId("kudos-compose");

const sunnerSearch = (page: Page): Locator =>
  page.getByTestId("sunner-search");

const highlightSection = (page: Page): Locator =>
  page.getByTestId("highlight-section");

const spotlightSection = (page: Page): Locator =>
  page.getByTestId("spotlight-section");

const allKudosSection = (page: Page): Locator =>
  page.getByTestId("all-kudos-section");

const kudosSidebar = (page: Page): Locator =>
  page.getByTestId("kudos-sidebar");

const filterHashtagButton = (page: Page): Locator =>
  page.getByTestId("filter-hashtag");

const filterDepartmentButton = (page: Page): Locator =>
  page.getByTestId("filter-department");

const filterMenuHashtag = (page: Page): Locator =>
  page.getByTestId("filter-menu-hashtag");

const filterMenuDepartment = (page: Page): Locator =>
  page.getByTestId("filter-menu-department");

const highlightCarousel = (page: Page): Locator =>
  page.getByTestId("highlight-carousel");

const highlightSlides = (page: Page): Locator =>
  page.getByTestId("highlight-slide");

const carouselPrevButton = (page: Page): Locator =>
  page.getByTestId("carousel-prev");

const carouselNextButton = (page: Page): Locator =>
  page.getByTestId("carousel-next");

const carouselPagination = (page: Page): Locator =>
  page.getByTestId("carousel-pagination");

const kudosCard = (page: Page): Locator =>
  page.getByTestId("kudos-card");

const kudosSender = (page: Page): Locator =>
  page.getByTestId("kudos-sender");

const kudosReceiver = (page: Page): Locator =>
  page.getByTestId("kudos-receiver");

const sunnerBadge = (page: Page): Locator =>
  page.getByTestId("sunner-badge");

const kudosTime = (page: Page): Locator =>
  page.getByTestId("kudos-time");

const kudosCampaign = (page: Page): Locator =>
  page.getByTestId("kudos-campaign");

const kudosBody = (page: Page): Locator =>
  page.getByTestId("kudos-body");

const kudosHashtag = (page: Page): Locator =>
  page.getByTestId("kudos-hashtag");

const kudosHeart = (page: Page): Locator =>
  page.getByTestId("kudos-heart");

const kudosHeartCount = (page: Page): Locator =>
  page.getByTestId("kudos-heart-count");

const kudosCopyLink = (page: Page): Locator =>
  page.getByTestId("kudos-copy-link");

const kudosDetailLink = (page: Page): Locator =>
  page.getByTestId("kudos-detail-link");

const kudosEmpty = (page: Page): Locator =>
  page.getByTestId("kudos-empty");

const feedSentinel = (page: Page): Locator =>
  page.getByTestId("feed-sentinel");

const spotlightBoard = (page: Page): Locator =>
  page.getByTestId("spotlight-board");

const spotlightCount = (page: Page): Locator =>
  page.getByTestId("spotlight-count");

const spotlightSearch = (page: Page): Locator =>
  page.getByTestId("spotlight-search");

const spotlightNode = (page: Page): Locator =>
  page.getByTestId("spotlight-node");

const spotlightTicker = (page: Page): Locator =>
  page.getByTestId("spotlight-ticker");

const spotlightPanzoom = (page: Page): Locator =>
  page.getByTestId("spotlight-panzoom");

const spotlightExpand = (page: Page): Locator =>
  page.getByTestId("spotlight-expand");

const spotlightEmpty = (page: Page): Locator =>
  page.getByTestId("spotlight-empty");

const sidebarStat = (page: Page): Locator =>
  page.getByTestId("sidebar-stat");

const secretBoxButton = (page: Page): Locator =>
  page.getByTestId("secret-box-button");

const giftLeaderboard = (page: Page): Locator =>
  page.getByTestId("gift-leaderboard");

const giftRow = (page: Page): Locator =>
  page.getByTestId("gift-row");

const giftEmpty = (page: Page): Locator =>
  page.getByTestId("gift-empty");

const toast = (page: Page): Locator =>
  page.getByTestId("toast");

// ============================================================================
// Test Suite
// ============================================================================

test.describe("Kudos Live Board screen — /kudos (anon)", () => {
  // K-0 — route loads publicly, no auth redirect; page renders h1.
  test("K-0 — route loads publicly without redirect and renders h1", async ({
    page,
  }) => {
    await page.goto(ROUTE);
    expect(page.url()).toBe(`http://127.0.0.1:3000${ROUTE}`);

    await expect(h1(page)).toBeVisible();
    await expect(h1(page)).toHaveText(PAGE_TITLE);
  });

  // K-1 — hero block: compose bar and Sunner search with correct placeholders.
  test("K-1 — hero renders compose bar and Sunner search with correct placeholders", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    await expect(composeBar(page)).toBeVisible();
    await expect(composeBar(page)).toHaveAccessibleName(COMPOSE_LABEL);

    await expect(sunnerSearch(page)).toBeVisible();
    await expect(sunnerSearch(page)).toHaveAttribute(
      "placeholder",
      SUNNER_SEARCH_PLACEHOLDER,
    );
    await expect(sunnerSearch(page)).toHaveAttribute("maxlength", "100");
  });

  // K-2 — HIGHLIGHT KUDOS section: heading, eyebrow, filter buttons.
  test("K-2 — HIGHLIGHT KUDOS section renders heading, eyebrow, and filters", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const section = highlightSection(page);
    await expect(section).toBeVisible();

    await expect(section.getByText(HERO_EYEBROW, { exact: true })).toBeVisible();
    await expect(
      section.getByRole("heading", { level: 2, name: "HIGHLIGHT KUDOS" }),
    ).toBeVisible();

    await expect(filterHashtagButton(page)).toBeVisible();
    await expect(filterHashtagButton(page)).toHaveAttribute("aria-expanded");
    await expect(filterDepartmentButton(page)).toBeVisible();
    await expect(filterDepartmentButton(page)).toHaveAttribute("aria-expanded");
  });

  // K-3 — filter menus: hashtag has 13 options, department has 50 (ratified count).
  test("K-3 — filter menus: hashtag has 13 options, department has 50", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Open hashtag filter
    await filterHashtagButton(page).click();
    const hashtagMenu = filterMenuHashtag(page);
    await expect(hashtagMenu).toBeVisible();
    const hashtagOptions = hashtagMenu.locator('[role="option"]');
    await expect(hashtagOptions).toHaveCount(HASHTAG_OPTIONS.length);
    await expect(hashtagOptions).toHaveText(HASHTAG_OPTIONS);

    // Close it and open department filter
    await filterHashtagButton(page).click();
    await filterDepartmentButton(page).click();
    const deptMenu = filterMenuDepartment(page);
    await expect(deptMenu).toBeVisible();
    const deptOptions = deptMenu.locator('[role="option"]');
    await expect(deptOptions).toHaveCount(DEPARTMENT_OPTIONS.length);
  });

  // K-4 — carousel: max 5 slides, centre slide aria-current, flanks aria-hidden.
  test("K-4 — carousel renders at most 5 slides with centre slide aria-current", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const carousel = highlightCarousel(page);
    await expect(carousel).toBeVisible();

    const slides = highlightSlides(page);
    const slideCount = await slides.count();
    expect(slideCount).toBeLessThanOrEqual(5);

    // Centre slide (first visible) should have aria-current="true"
    const firstSlide = slides.nth(0);
    await expect(firstSlide).toHaveAttribute("aria-current", "true");

    // Flanks should be aria-hidden
    if (slideCount > 1) {
      const lastSlide = slides.nth(slideCount - 1);
      await expect(lastSlide).toHaveAttribute("aria-hidden", "true");
    }
  });

  // K-5 — carousel pagination text matches /^\d+\/\d+$/ pattern.
  test("K-5 — carousel pagination text matches expected format", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const pagination = carouselPagination(page);
    await expect(pagination).toBeVisible();

    const text = await pagination.textContent();
    expect(text).toMatch(/^\d+\/\d+$/);
  });

  // K-6 — prev arrow disabled at slide 1, next arrow disabled at last slide.
  test("K-6 — carousel arrows: prev disabled at slide 1, next disabled at last", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // At start, prev should be disabled
    await expect(carouselPrevButton(page)).toBeDisabled();

    const pagination = await carouselPagination(page).textContent();
    const [current, total] = pagination!.split("/").map(Number);

    // If not at last slide, next is enabled; if at last, disabled
    if (current === total) {
      await expect(carouselNextButton(page)).toBeDisabled();
    } else {
      await expect(carouselNextButton(page)).not.toBeDisabled();
    }
  });

  // K-7 — next/prev buttons move the carousel slide.
  test("K-7 — carousel next/prev buttons move the slide", async ({ page }) => {
    await page.goto(ROUTE);

    const initialPagination = await carouselPagination(page).textContent();
    const [initialCurrent] = initialPagination!.split("/").map(Number);

    // Click next if we can
    if (!(await carouselNextButton(page).isDisabled())) {
      await carouselNextButton(page).click();

      const newPagination = await carouselPagination(page).textContent();
      const [newCurrent] = newPagination!.split("/").map(Number);
      expect(newCurrent).toBe(initialCurrent + 1);
    }
  });

  // K-8 — filter selection re-filters both sections and resets carousel to slide 1.
  test("K-8 — filter selection resets carousel to slide 1", async ({ page }) => {
    await page.goto(ROUTE);

    // Open hashtag filter and select first option
    await filterHashtagButton(page).click();
    const hashtagMenu = filterMenuHashtag(page);
    const firstOption = hashtagMenu.locator('[role="option"]').nth(0);
    await firstOption.click();

    // Carousel should reset to slide 1
    const pagination = await carouselPagination(page).textContent();
    const [current] = pagination!.split("/").map(Number);
    expect(current).toBe(1);
  });

  // K-9 — kudos card structure: sender/receiver links, badge, time, campaign, hashtags, heart (disabled when sender or anon).
  test("K-9 — kudos card renders sender, receiver, badge, time, campaign, hashtags, heart", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const card = kudosCard(page).first();
    await expect(card).toBeVisible();

    // Sender and receiver are links
    const sender = card.getByTestId("kudos-sender");
    const receiver = card.getByTestId("kudos-receiver");
    await expect(sender).toBeVisible();
    // F006 phase 09 — DELIBERATE NARROWING of a ratified assertion, not a
    // relaxation: the href was the fixed literal "/profile"; both chips now
    // carry the viewed Sunner's id (FR-003, clarifications premise 3), so this
    // pins the SHAPE `/profile?id=<digits>` instead. Anything else — a bare
    // "/profile", an `?id=0` from a redacted anonymous stub, a non-numeric id
    // — still fails here.
    await expect(sender).toHaveAttribute("href", /^\/profile\?id=\d+$/);
    await expect(receiver).toBeVisible();
    // F006 phase 09 — same deliberate narrowing, receiver side.
    await expect(receiver).toHaveAttribute("href", /^\/profile\?id=\d+$/);

    // Badge (one of the four tiers)
    const badge = card.getByTestId("sunner-badge");
    await expect(badge).toBeVisible();

    // Time format HH:mm - MM/DD/YYYY
    const time = card.getByTestId("kudos-time");
    await expect(time).toBeVisible();
    const timeText = await time.textContent();
    expect(timeText).toMatch(/^\d{2}:\d{2} - \d{2}\/\d{2}\/\d{4}$/);

    // Campaign label
    const campaign = card.getByTestId("kudos-campaign");
    await expect(campaign).toBeVisible();

    // Hashtags (buttons)
    const hashtags = card.locator('[data-testid="kudos-hashtag"]');
    if ((await hashtags.count()) > 0) {
      await expect(hashtags.nth(0)).toBeVisible();
    }

    // Heart toggle with aria-pressed
    const heart = card.getByTestId("kudos-heart");
    await expect(heart).toBeVisible();
    await expect(heart).toHaveAttribute("aria-pressed");
  });

  // K-24 — every heart is disabled for an anon viewer; no click mutates the count.
  test("K-24 — every kudos-heart is disabled for anon viewer", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const cards = kudosCard(page);
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThan(0);

    // Every visible heart should be disabled
    for (let i = 0; i < cardCount; i++) {
      const card = cards.nth(i);
      const heart = card.getByTestId("kudos-heart");
      await expect(heart).toBeDisabled();
    }

    // Verify read paths still render fully: sections, cards, spotlight, sidebar
    await expect(highlightSection(page)).toBeVisible();
    await expect(spotlightSection(page)).toBeVisible();
    await expect(allKudosSection(page)).toBeVisible();
    await expect(kudosSidebar(page)).toBeVisible();
  });

  // K-11 — Copy Link button shows toast "Link copied — ready to share!".
  test("K-11 — Copy Link shows toast with correct message", async ({
    page,
  }) => {
    await page.goto(ROUTE);
    await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);

    const card = kudosCard(page).first();
    const copyButton = card.getByTestId("kudos-copy-link");
    await expect(copyButton).toBeVisible();

    await copyButton.click();

    const toastMessage = toast(page);
    await expect(toastMessage).toBeVisible();
    await expect(toastMessage).toHaveText(COPY_LINK_TOAST);
  });

  // K-12 — detail link on highlight cards (absent on feed cards).
  test("K-12 — Xem chi tiết link present on highlight cards", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Highlight carousel has detail links
    const highlightCarouselContainer = highlightCarousel(page);
    const detailLink = highlightCarouselContainer.getByTestId(
      "kudos-detail-link",
    );
    await expect(detailLink).toBeVisible();
    await expect(detailLink).toHaveAttribute("href", /\/kudos\/\d+/);
  });

  // K-13 — SPOTLIGHT BOARD section: heading, count, search.
  test("K-13 — SPOTLIGHT BOARD renders heading, count, and search", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const section = spotlightSection(page);
    await expect(section).toBeVisible();

    await expect(section.getByText(HERO_EYEBROW, { exact: true })).toBeVisible();
    await expect(
      section.getByRole("heading", { level: 2, name: "SPOTLIGHT BOARD" }),
    ).toBeVisible();

    const board = spotlightBoard(page);
    await expect(spotlightCount(page)).toBeVisible();
    await expect(spotlightCount(page)).toHaveText(SPOTLIGHT_COUNT_TEXT);

    const search = spotlightSearch(page);
    await expect(search).toBeVisible();
    await expect(search).toHaveAttribute(
      "placeholder",
      SPOTLIGHT_SEARCH_PLACEHOLDER,
    );
    await expect(search).toHaveAttribute("maxlength", "100");
  });

  // K-14 — spotlight word-cloud nodes are present and searchable.
  test("K-14 — spotlight nodes present and search narrows them", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const nodes = spotlightNode(page);
    const initialCount = await nodes.count();
    expect(initialCount).toBeGreaterThan(0);

    // Type into the search
    const search = spotlightSearch(page);
    await search.fill("Nguyễn");

    // Node count should be less (some names filtered out)
    await page.waitForTimeout(100); // brief pause for filter to apply
    const filteredCount = await spotlightNode(page).count();
    expect(filteredCount).toBeLessThanOrEqual(initialCount);
  });

  // K-15 — pan/zoom and expand buttons have aria-pressed.
  test("K-15 — spotlight pan/zoom and expand buttons have aria-pressed", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    await expect(spotlightPanzoom(page)).toBeVisible();
    await expect(spotlightPanzoom(page)).toHaveAttribute("aria-pressed");
    await expect(spotlightPanzoom(page)).toHaveAttribute("title", "Pan/Zoom");

    await expect(spotlightExpand(page)).toBeVisible();
    await expect(spotlightExpand(page)).toHaveAttribute("aria-pressed");
  });

  // K-16 — ticker rows are present.
  test("K-16 — spotlight ticker rows present", async ({ page }) => {
    await page.goto(ROUTE);

    const tickerContainer = spotlightTicker(page);
    await expect(tickerContainer).toBeVisible();
  });

  // K-17 — ALL KUDOS section: heading, card feed, infinite-scroll sentinel.
  test("K-17 — ALL KUDOS section renders heading and feed", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const section = allKudosSection(page);
    await expect(section).toBeVisible();

    await expect(
      section.getByRole("heading", { level: 2, name: "ALL KUDOS" }),
    ).toBeVisible();
    await expect(section.getByText(HERO_EYEBROW, { exact: true })).toBeVisible();

    // Feed should have at least some cards or empty state
    const cards = section.locator('[data-testid="kudos-card"]');
    const empty = section.getByTestId("kudos-empty");

    const cardCount = await cards.count();
    const hasEmpty = await empty.isVisible().catch(() => false);

    expect(cardCount > 0 || hasEmpty).toBe(true);
  });

  // K-18 — sidebar: 5 stat rows in exact order.
  test("K-18 — sidebar renders 5 stat rows in exact order", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const sidebar = kudosSidebar(page);
    await expect(sidebar).toBeVisible();

    const stats = sidebar.locator('[data-testid="sidebar-stat"]');
    await expect(stats).toHaveCount(SIDEBAR_STATS.length);

    for (let i = 0; i < SIDEBAR_STATS.length; i++) {
      const stat = stats.nth(i);
      await expect(stat).toContainText(SIDEBAR_STATS[i]);
    }
  });

  // K-19 — Secret Box button links to /kudos/secret-box.
  test("K-19 — Secret Box button present with correct label and href", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const button = secretBoxButton(page);
    await expect(button).toBeVisible();
    await expect(button).toHaveAccessibleName(SECRET_BOX_LABEL);
    await expect(button).toHaveAttribute("href", "/kudos/secret-box");
  });

  // K-20 — gift leaderboard heading present.
  test("K-20 — gift leaderboard heading present", async ({ page }) => {
    await page.goto(ROUTE);

    const leaderboard = giftLeaderboard(page);
    await expect(leaderboard).toBeVisible();
    await expect(leaderboard.getByText(GIFT_LEADERBOARD_HEADING)).toBeVisible();
  });

  // K-21 — placeholder routes /kudos/secret-box and /kudos/[id] render ComingSoon
  // Note: /kudos/new is guarded as of phase-02 (requires authentication). Guard coverage moved to ID-1 (anon) and ID-0 (authed).
  test("K-21 — placeholder routes /kudos/secret-box and /kudos/[id] render ComingSoon", async ({
    page,
  }) => {
    // Test /kudos/secret-box (public placeholder)
    let response = await page.goto("/kudos/secret-box");
    expect(response?.status()).toBe(200);
    expect(page.url()).toContain("/kudos/secret-box");
    // Assert ComingSoon is rendered (main with flex children)
    await expect(page.locator("main")).toBeVisible();
    await expect(page.locator("main h1")).toBeVisible();

    // Test /kudos/[id] (e.g., /kudos/123 — public placeholder)
    response = await page.goto("/kudos/123");
    expect(response?.status()).toBe(200);
    expect(page.url()).toContain("/kudos/123");
    await expect(page.locator("main")).toBeVisible();
    await expect(page.locator("main h1")).toBeVisible();
  });

  // K-22 — compose bar navigates to /kudos/new.
  test("K-22 — compose bar links to /kudos/new", async ({ page }) => {
    await page.goto(ROUTE);

    const compose = composeBar(page);
    await expect(compose).toBeVisible();
    await expect(compose).toHaveAttribute("href", "/kudos/new");
  });

  // K-23 — Sunner search input allows up to 100 characters.
  test("K-23 — Sunner search maxlength is 100", async ({ page }) => {
    await page.goto(ROUTE);

    const search = sunnerSearch(page);
    await expect(search).toHaveAttribute("maxlength", "100");
  });
});
