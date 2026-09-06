import { expect, test, type Locator, type Page } from "@playwright/test";

/**
 * Screen-level E2E for "Hệ thống giải" (Award System) — MoMorph screen
 * `zFYDgyj_pD` (file `9ypp4enmFmdK3YAFJLIu6C`), test policy `e2e-red-first`.
 *
 * Every value below is transcribed from
 * `plans/260906-0719-award-system-screen/clarifications.md`, which is the
 * authoritative record for this screen. Nothing here is invented.
 *
 * Route is `/awards-information` (clarifications, decision 1) — NOT
 * `/he-thong-giai`. Test case ID-1 (unauthenticated → redirect to login) is
 * deliberately NOT written: clarifications records it as contradicted by
 * shipped behavior, and the route is public by design.
 *
 * Test-contract hooks the implementation is bound to:
 *   - award section:  id="<slug>"  +  data-testid="award-detail-<slug>"
 *   - menu container: data-testid="award-nav"
 *   - menu item:      <a href="#<slug>"> data-testid="award-nav-<slug>",
 *                     active item carries aria-current="true"
 *   - card image:     <img> whose alt is the award title
 *   - page <h1>:      "Hệ thống giải thưởng SAA 2025"
 */

const ROUTE = "/awards-information";
const PAGE_TITLE = "Hệ thống giải thưởng SAA 2025";
const HERO_EYEBROW = "Sun* Annual Awards 2025";
const QUANTITY_LABEL = "Số lượng giải thưởng:";
const PRIZE_LABEL = "Giá trị giải thưởng:";
const PER_AWARD_NOTE = "cho mỗi giải thưởng";
/** W-3/S-7 — the category menu's landmark name (`awardSystem.navAriaLabel`). */
const CATEGORY_NAV_LABEL = "Danh mục giải thưởng";

type Prize = { amount: string; note?: string };

type Award = {
  slug: string;
  /** Card title — also the award image's alt text (contract). */
  title: string;
  /** Left-menu label (clarifications § "Left menu (item C)"). */
  navLabel: string;
  quantity: string;
  unit: string;
  prizes: Prize[];
};

/** The six awards in fixed design order (clarifications D.1 → D.6). */
const AWARDS: readonly Award[] = [
  {
    slug: "top-talent",
    title: "Top Talent",
    navLabel: "Top Talent",
    quantity: "10",
    unit: "Cá nhân",
    prizes: [{ amount: "7.000.000 VNĐ", note: PER_AWARD_NOTE }],
  },
  {
    slug: "top-project",
    title: "Top Project",
    navLabel: "Top Project",
    quantity: "02",
    unit: "Tập thể",
    prizes: [{ amount: "15.000.000 VNĐ", note: PER_AWARD_NOTE }],
  },
  {
    slug: "top-project-leader",
    title: "Top Project Leader",
    navLabel: "Top Project Leader",
    quantity: "03",
    unit: "Cá nhân",
    prizes: [{ amount: "7.000.000 VNĐ", note: PER_AWARD_NOTE }],
  },
  {
    slug: "best-manager",
    title: "Best Manager",
    navLabel: "Best Manager",
    quantity: "01",
    unit: "Cá nhân",
    // No note line — clarifications D.4.
    prizes: [{ amount: "10.000.000 VNĐ" }],
  },
  {
    slug: "signature-2025-creator",
    title: "Signature 2025 - Creator",
    navLabel: "Signature 2025 Creator",
    quantity: "01",
    unit: "Cá nhân hoặc tập thể",
    prizes: [
      { amount: "5.000.000 VNĐ", note: "cho giải cá nhân" },
      { amount: "8.000.000 VNĐ", note: "cho giải tập thể" },
    ],
  },
  {
    slug: "mvp",
    title: "MVP (Most Valuable Person)",
    navLabel: "MVP",
    quantity: "01",
    unit: "Cá nhân",
    // No note line — clarifications D.6.
    prizes: [{ amount: "15.000.000 VNĐ" }],
  },
];

const awardSection = (page: Page, slug: string): Locator =>
  page.getByTestId(`award-detail-${slug}`);

const awardNav = (page: Page): Locator => page.getByTestId("award-nav");

const awardNavItem = (page: Page, slug: string): Locator =>
  page.getByTestId(`award-nav-${slug}`);

/** The item currently marked active inside the left category menu. */
const activeNavItems = (page: Page): Locator =>
  awardNav(page).locator('[aria-current="true"]');

/**
 * The Sun* Kudos promo block. Same scoping convention homepage.spec.ts ID-53
 * already uses — the block is its own <section> carrying the exact title.
 */
const kudosSection = (page: Page): Locator =>
  page.locator("section").filter({ has: page.getByText("Sun* Kudos", { exact: true }) });

/**
 * Document-order check. Returns the index of each element within a flat
 * document-order walk, so callers can assert a strictly increasing sequence.
 */
async function documentOrder(page: Page, locators: Locator[]): Promise<number[]> {
  const handles = await Promise.all(locators.map((l) => l.elementHandle()));
  return page.evaluate((els) => {
    const all = Array.from(document.querySelectorAll("*"));
    return (els as Element[]).map((el) => all.indexOf(el));
  }, handles);
}

test.describe("Award System screen — /awards-information (anon)", () => {
  // ID-0/ID-2 — the route loads publicly without redirect, is reachable from
  // the homepage header nav, and marks "Award Information" as the current page.
  test("ID-0/2 — route loads without redirect and the header nav item reaches it and is aria-current=page", async ({
    page,
  }) => {
    // ID-0 — direct load, no redirect (the route is public; see clarifications).
    await page.goto(ROUTE);
    expect(page.url()).toBe(`http://127.0.0.1:3000${ROUTE}`);
    await expect(page.locator("body")).not.toBeEmpty();

    // ID-2 — reachable from the homepage header nav.
    await page.goto("/");
    const header = page.getByRole("banner");
    const awardNavLink = header.getByRole("link", { name: "Award Information", exact: true });
    await expect(awardNavLink).toBeVisible();
    await awardNavLink.click();
    await page.waitForURL(/\/awards-information/);
    expect(page.url()).toContain(ROUTE);

    // The nav item is now the selected one.
    await expect(
      page.getByRole("banner").getByRole("link", { name: "Award Information", exact: true }),
    ).toHaveAttribute("aria-current", "page");
  });

  // ID-3 — overall structure: banner, h1, left menu, six award sections, the
  // Sun* Kudos block and the footer, all visible and in that document order.
  test("ID-3 — page structure renders banner, h1, award-nav, six award sections, Kudos block and footer in document order", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const banner = page.getByRole("banner");
    const heading = page.getByRole("heading", { level: 1, name: PAGE_TITLE });
    const nav = awardNav(page);
    const sections = AWARDS.map((a) => awardSection(page, a.slug));
    const kudos = kudosSection(page);
    const footer = page.getByRole("contentinfo");

    const ordered = [banner, heading, nav, ...sections, kudos, footer];
    for (const locator of ordered) {
      await expect(locator).toBeVisible();
    }

    // Every award section is addressable by its slug id too (deep-link target).
    for (const award of AWARDS) {
      await expect(awardSection(page, award.slug)).toHaveAttribute("id", award.slug);
    }

    const indices = await documentOrder(page, ordered);
    expect(indices.every((n) => n >= 0)).toBe(true);
    for (let i = 1; i < indices.length; i++) {
      expect(indices[i]).toBeGreaterThan(indices[i - 1]);
    }
  });

  // W-3 — accessible structure. Locked because it is invisible to every other
  // assertion here: a heading could silently become a <div>, a section could
  // lose its aria-labelledby, or the category menu could go back to borrowing
  // the page title as its landmark name, and the whole suite would stay green
  // while screen-reader navigation quietly broke.
  test("W-3 — one h1, h1 → six h2 → Kudos h2, each award section accessibly named, category nav labelled", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Exactly one <h1>, and it is the page title.
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(PAGE_TITLE);

    // Heading order: the page title, the six awards in design order, then Kudos.
    const headings = await page.evaluate(() =>
      Array.from(document.querySelectorAll("h1, h2, h3, h4, h5, h6")).map((h) => ({
        level: Number(h.tagName[1]),
        text: (h.textContent ?? "").trim(),
      })),
    );
    expect(headings).toEqual([
      { level: 1, text: PAGE_TITLE },
      ...AWARDS.map((award) => ({ level: 2, text: award.title })),
      { level: 2, text: "Sun* Kudos" },
    ]);

    // Every award section is named in the accessibility tree by its own heading.
    for (const award of AWARDS) {
      await expect(awardSection(page, award.slug)).toHaveAttribute(
        "aria-labelledby",
        `${award.slug}-title`,
      );
      await expect(page.locator(`#${award.slug}-title`)).toHaveText(award.title);
      // Resolved through the a11y tree, not just the attribute: a named
      // <section> exposes role="region".
      await expect(page.getByRole("region", { name: award.title, exact: true })).toBeVisible();
    }

    // The category menu is a labelled landmark named after the menu, not the
    // page. The label sits on the menu's own <nav>, so assert the landmark and
    // the menu container are the same element rather than nested.
    const categoryNav = page.getByRole("navigation", { name: CATEGORY_NAV_LABEL, exact: true });
    await expect(categoryNav).toBeVisible();
    await expect(categoryNav).toHaveAttribute("data-testid", "award-nav");
    await expect(categoryNav.getByRole("link")).toHaveCount(AWARDS.length);
  });

  // ID-4 — hero title block: eyebrow, then the gold page heading.
  test("ID-4 — hero title block shows the eyebrow and the exact page heading", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    await expect(page.getByText(HERO_EYEBROW, { exact: true })).toBeVisible();

    const heading = page.getByRole("heading", { level: 1 });
    await expect(heading).toBeVisible();
    await expect(heading).toHaveText(PAGE_TITLE);
  });

  // ID-5 — the left category menu lists exactly the six items, in design order.
  test("ID-5 — left category menu lists exactly 6 items in design order", async ({ page }) => {
    await page.goto(ROUTE);

    const nav = awardNav(page);
    await expect(nav).toBeVisible();

    const items = nav.getByRole("link");
    await expect(items).toHaveCount(AWARDS.length);
    await expect(items).toHaveText(AWARDS.map((a) => a.navLabel));

    // Each item is the anchor for its own section.
    for (const award of AWARDS) {
      await expect(awardNavItem(page, award.slug)).toHaveAttribute("href", `#${award.slug}`);
    }
  });

  // ID-6 — every award card renders title, quantity number + unit, prize
  // amount(s) and note line; Best Manager and MVP carry NO per-award note.
  test("ID-6 — all six awards render title, quantity, unit, prize amounts and notes", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    for (const award of AWARDS) {
      const section = awardSection(page, award.slug);
      await expect(section).toBeVisible();

      // Title
      await expect(section.getByText(award.title, { exact: true })).toBeVisible();

      // Quantity: label + number + unit
      await expect(section.getByText(QUANTITY_LABEL, { exact: true })).toBeVisible();
      await expect(section.getByText(award.quantity, { exact: true })).toBeVisible();
      await expect(section.getByText(award.unit, { exact: true })).toBeVisible();

      // Prize: label + every amount (and its note when the design has one)
      await expect(section.getByText(PRIZE_LABEL, { exact: true }).first()).toBeVisible();
      for (const prize of award.prizes) {
        await expect(section.getByText(prize.amount, { exact: true })).toBeVisible();
        if (prize.note) {
          await expect(section.getByText(prize.note, { exact: true })).toBeVisible();
        }
      }

      // Awards without a note must not render one (clarifications D.4 / D.6).
      const hasPerAwardNote = award.prizes.some((p) => p.note === PER_AWARD_NOTE);
      if (!hasPerAwardNote) {
        await expect(section.getByText(PER_AWARD_NOTE)).toHaveCount(0);
      }

      // Signature 2025 - Creator separates its two prize rows with "Hoặc".
      if (award.prizes.length > 1) {
        await expect(section.getByText("Hoặc", { exact: true })).toBeVisible();
      }
    }
  });

  // ID-7 — every award card renders its image, with the award title as alt
  // text, as an undistorted 336x336 square (spec item D.1.1).
  //
  // The square assertion is not cosmetic bookkeeping. The badge shipped once
  // as a direct flex child of the card row, inherited `align-self: stretch`,
  // and `object-fit: fill` then stretched the 336x336 source to the height of
  // the text column — up to 336x966 on Signature, a 2.88x distortion that no
  // alt-text or visibility check can see. Pinned at the design width so the
  // assertion means what the design means.
  test("ID-7 — every award card renders its image with the award title as alt text, undistorted at 336x336", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(ROUTE);

    for (const award of AWARDS) {
      const image = awardSection(page, award.slug).getByRole("img", {
        name: award.title,
        exact: true,
      });
      await expect(image).toBeVisible();
      await expect(image).toHaveAttribute("alt", award.title);

      // Rendered box must be the intrinsic 336x336 square, not stretched.
      const box = await image.boundingBox();
      expect(box, `no bounding box for ${award.slug} badge`).not.toBeNull();
      expect(
        { slug: award.slug, w: Math.round(box!.width), h: Math.round(box!.height) },
        "award badge must render undistorted at its intrinsic 336x336",
      ).toEqual({ slug: award.slug, w: 336, h: 336 });
    }
  });

  // ID-8 — Sun* Kudos promo block copy and CTA.
  test("ID-8 — Sun* Kudos block renders eyebrow, title, subtitle and the Chi tiết control", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const kudos = kudosSection(page);
    await expect(kudos).toBeVisible();
    await expect(kudos.getByText("Phong trào ghi nhận", { exact: true })).toBeVisible();
    await expect(kudos.getByText("Sun* Kudos", { exact: true })).toBeVisible();
    await expect(kudos.getByText("ĐIỂM MỚI CỦA SAA 2025", { exact: true })).toBeVisible();
    await expect(kudos.getByRole("link", { name: /chi tiết/i })).toBeVisible();
  });

  // ID-9/ID-11 — clicking each menu item scrolls its section into view and
  // leaves exactly ONE active item; the previously active item loses the mark.
  test("ID-9/11 — clicking each menu item scrolls to its section and keeps exactly one active item", async ({
    page,
  }) => {
    await page.goto(ROUTE);
    await expect(awardNav(page)).toBeVisible();

    let previousSlug: string | null = null;

    for (const award of AWARDS) {
      const item = awardNavItem(page, award.slug);
      await expect(item).toBeVisible();
      await item.click();

      // ID-9 — the matching section is scrolled into view.
      await expect(awardSection(page, award.slug)).toBeInViewport();

      // ID-11 — exactly one item is active, and it is this one.
      await expect(item).toHaveAttribute("aria-current", "true");
      await expect(activeNavItems(page)).toHaveCount(1);

      // The previously active item lost the active state.
      if (previousSlug && previousSlug !== award.slug) {
        await expect(awardNavItem(page, previousSlug)).not.toHaveAttribute(
          "aria-current",
          "true",
        );
      }
      previousSlug = award.slug;
    }
  });

  // ID-10 — hovering a menu item leaves it a live, interactive link under the
  // pointer. Asserted through :hover state rather than a specific CSS color,
  // so the check stays honest without pinning a design token.
  test("ID-10 — menu items are interactive links that respond to hover", async ({ page }) => {
    await page.goto(ROUTE);

    for (const award of AWARDS) {
      const item = awardNavItem(page, award.slug);
      await expect(item).toBeVisible();
      await expect(item).toHaveAttribute("href", `#${award.slug}`);

      await item.hover();
      await expect(item).toBeVisible();

      const isHovered = await item.evaluate((el) => el.matches(":hover"));
      expect(isHovered).toBe(true);
    }
  });

  // ID-12 — the Kudos "Chi tiết" control navigates to /kudos.
  test("ID-12 — Kudos Chi tiết control navigates to /kudos", async ({ page }) => {
    await page.goto(ROUTE);

    const detailLink = kudosSection(page).getByRole("link", { name: /chi tiết/i });
    await expect(detailLink).toBeVisible();
    await detailLink.click();

    await page.waitForURL(/\/kudos/);
    expect(page.url()).toContain("/kudos");
  });

  // ID-13 — an unknown hash raises no page error and leaves the screen usable.
  test("ID-13 — an invalid hash raises no page error and the screen stays functional", async ({
    page,
  }) => {
    const pageErrors: string[] = [];
    const consoleErrors: string[] = [];

    page.on("pageerror", (error) => pageErrors.push(error.message));
    page.on("console", (message) => {
      if (message.type() !== "error") return;
      const text = message.text();
      // Resource-load noise (missing favicon, aborted prefetch) is a network
      // concern, not a script error on this screen.
      if (/failed to load resource|favicon/i.test(text)) return;
      consoleErrors.push(text);
    });

    await page.goto(`${ROUTE}#does-not-exist`);

    // Screen still renders and is still operable.
    await expect(page.getByRole("heading", { level: 1, name: PAGE_TITLE })).toBeVisible();
    await expect(awardNav(page)).toBeVisible();

    const item = awardNavItem(page, "top-project");
    await item.click();
    await expect(awardSection(page, "top-project")).toBeInViewport();
    await expect(activeNavItems(page)).toHaveCount(1);

    expect(pageErrors).toEqual([]);
    expect(consoleErrors).toEqual([]);
  });

  // Deep link — arriving at /awards-information#mvp lands on the MVP section
  // and seeds the active menu item from the hash (clarifications, decision on
  // deep-link arrival).
  test("Deep link — /awards-information#mvp lands on the MVP section with its menu item active", async ({
    page,
  }) => {
    await page.goto(`${ROUTE}#mvp`);

    await expect(awardSection(page, "mvp")).toBeInViewport();
    await expect(awardNavItem(page, "mvp")).toHaveAttribute("aria-current", "true");
    await expect(activeNavItems(page)).toHaveCount(1);
  });
});
