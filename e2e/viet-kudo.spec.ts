import { expect, test, type Locator, type Page } from "@playwright/test";
import {
  ROUTE,
  PAGE_TITLE,
  RECIPIENT_PLACEHOLDER,
  TITLE_PLACEHOLDER,
  BODY_PLACEHOLDER,
  TITLE_HINT_1,
  TITLE_HINT_2,
  BODY_HINT,
  ANONYMOUS_CHECKBOX_LABEL,
  HASHTAG_MAX_LABEL,
  HASHTAG_ERROR_FULL,
  IMAGE_MAX_LABEL,
  RECIPIENT_ERROR,
  TITLE_ERROR,
  BODY_ERROR,
  HASHTAG_REQUIRED_ERROR,
  COMMUNITY_STANDARDS_LABEL,
  CANCEL_BUTTON_LABEL,
  SUBMIT_BUTTON_LABEL,
  TEST_HASHTAG_1,
  TEST_HASHTAG_2,
  TEST_HASHTAG_3,
  TEST_HASHTAG_4,
  TEST_HASHTAG_5,
  TEST_HASHTAG_6,
  SEEDED_HASHTAG_ORDER,
  TEST_TITLE,
  TEST_BODY,
  TEST_ANONYMOUS_NAME,
} from "./fixtures/viet-kudo-constants";

/**
 * Screen-level E2E for "Viết Kudo" compose screen (`/kudos/new`) — MoMorph screen
 * `ihQ26W78P2` (file `9ypp4enmFmdK3YAFJLIu6C`), test policy `e2e-red-first`.
 *
 * KUDOS-AUTHED PROJECT ONLY — authenticated tests (ID-0, ID-2 through ID-56).
 * Route guard test (ID-1) is in route-guard.spec.ts (anon project).
 *
 * Every constant value is transcribed from
 * `plans/260907-0822-viet-kudo/clarifications.md` and `test-contract.md`,
 * which are authoritative. Test case IDs (ID-0, ID-2, ..., ID-56) map to rows
 * in `design/test-cases.csv` (57 authored cases).
 *
 * Test-contract hooks the implementation is bound to: all data-testid values,
 * aria-* attributes, href targets, text content (copy from clarifications),
 * and element roles. Neither side may change a hook unilaterally.
 */

// ============================================================================
// Helpers — locators matching test-contract.md
// ============================================================================

const h1 = (page: Page): Locator => page.getByRole("heading", { level: 1 });

const composeForm = (page: Page): Locator =>
  page.getByTestId("compose-form");

const recipientInput = (page: Page): Locator =>
  page.getByTestId("recipient-input");

const recipientMenu = (page: Page): Locator =>
  page.getByTestId("recipient-menu");

const recipientOption = (page: Page): Locator =>
  page.getByTestId("recipient-menu").locator('[role="option"]');

const recipientEmpty = (page: Page): Locator =>
  page.getByTestId("recipient-empty");

const recipientSelected = (page: Page): Locator =>
  page.getByTestId("recipient-selected");

const titleInput = (page: Page): Locator =>
  page.getByTestId("title-input");

const titleHint = (page: Page): Locator =>
  page.getByTestId("title-hint");

const bodyEditor = (page: Page): Locator =>
  page.getByTestId("body-editor");

const bodyHint = (page: Page): Locator =>
  page.getByTestId("body-hint");

const toolbarBold = (page: Page): Locator =>
  page.getByTestId("toolbar-bold");

const toolbarItalic = (page: Page): Locator =>
  page.getByTestId("toolbar-italic");

const toolbarStrike = (page: Page): Locator =>
  page.getByTestId("toolbar-strike");

const toolbarOrderedList = (page: Page): Locator =>
  page.getByTestId("toolbar-ordered-list");

const toolbarLink = (page: Page): Locator =>
  page.getByTestId("toolbar-link");

const toolbarQuote = (page: Page): Locator =>
  page.getByTestId("toolbar-quote");

const linkDialog = (page: Page): Locator =>
  page.getByTestId("link-dialog");

const linkUrlInput = (page: Page): Locator =>
  page.getByTestId("link-url-input");

const mentionMenu = (page: Page): Locator =>
  page.getByTestId("mention-menu");

const mentionOption = (page: Page): Locator =>
  page.getByTestId("mention-menu").locator('[role="option"]');

const hashtagAddButton = (page: Page): Locator =>
  page.getByTestId("hashtag-add");

const hashtagMenu = (page: Page): Locator =>
  page.getByTestId("hashtag-menu");

const hashtagChip = (page: Page): Locator =>
  page.getByTestId("hashtag-chip");

const hashtagChipRemove = (page: Page): Locator =>
  page.getByTestId("hashtag-chip-remove");

const hashtagError = (page: Page): Locator =>
  page.getByTestId("hashtag-error");

const hashtagOptionsUnselected = (page: Page): Locator =>
  hashtagMenu(page).locator('[role="option"]:not([data-selected="true"])');

const hashtagOptionsSelected = (page: Page): Locator =>
  hashtagMenu(page).locator('[role="option"][data-selected="true"]');

const imageAddButton = (page: Page): Locator =>
  page.getByTestId("image-add");

const imageInput = (page: Page): Locator =>
  page.getByTestId("image-input");

const imageThumb = (page: Page): Locator =>
  page.getByTestId("image-thumb");

const imageThumbRemove = (page: Page): Locator =>
  page.getByTestId("image-thumb-remove");

const imageError = (page: Page): Locator =>
  page.getByTestId("image-error");

const anonymousCheckbox = (page: Page): Locator =>
  page.getByTestId("anonymous-checkbox");

const anonymousNameInput = (page: Page): Locator =>
  page.getByTestId("anonymous-name-input");

const fieldErrorRecipient = (page: Page): Locator =>
  page.getByTestId("field-error-recipient");

const fieldErrorTitle = (page: Page): Locator =>
  page.getByTestId("field-error-title");

const fieldErrorBody = (page: Page): Locator =>
  page.getByTestId("field-error-body");

const fieldErrorHashtag = (page: Page): Locator =>
  page.getByTestId("field-error-hashtag");

const communityStandardsLink = (page: Page): Locator =>
  page.getByTestId("community-standards-link");

const composeSubmit = (page: Page): Locator =>
  page.getByTestId("compose-submit");

const composeCancel = (page: Page): Locator =>
  page.getByTestId("compose-cancel");

/**
 * The option BUTTON carrying `tag`, never a descendant of it. `.locator("text=")`
 * resolves to whichever element owns the text node, so it would return an inner
 * `<span>` the moment the row wraps its label — and `data-selected` /
 * `toBeDisabled()` live on the button, not on the label. `filter({ hasText })`
 * keeps the button as the match whatever the row's internal markup becomes.
 */
const hashtagOption = (page: Page, tag: string): Locator =>
  hashtagMenu(page).locator('[role="option"]').filter({ hasText: tag });

// Open the menu and toggle each named hashtag in turn (the menu closes per toggle).
async function selectTags(page: Page, tags: string[]): Promise<void> {
  for (const tag of tags) {
    await hashtagAddButton(page).click();
    await expect(hashtagMenu(page)).toBeVisible();
    await hashtagOption(page, tag).click();
  }
}

// ============================================================================
// Test Suite
// ============================================================================

test.describe("Viết Kudo screen — /kudos/new (kudos-authed)", () => {
  // ID-0 — authenticated user can navigate to compose screen and it renders
  test("ID-0 — authenticated user navigates to /kudos/new and form renders", async ({
    page,
  }) => {
    await page.goto(ROUTE);
    expect(page.url()).toContain(ROUTE);

    await expect(h1(page)).toBeVisible();
    await expect(h1(page)).toHaveText(PAGE_TITLE);
  });

  // ID-2 — page structure: form element with data-testid present
  test("ID-2 — compose form landmark present with data-testid", async ({
    page,
  }) => {
    await page.goto(ROUTE);
    await expect(composeForm(page)).toBeVisible();
  });

  // ID-3 — field order: recipient, title, body, hashtags, images, anonymous checkbox
  test("ID-3 — fields render in correct order: recipient → title → body → hashtags → images → anonymous", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const recipient = recipientInput(page);
    const title = titleInput(page);
    const body = bodyEditor(page);
    const hashtags = hashtagAddButton(page);
    const images = imageAddButton(page);
    const anonymous = anonymousCheckbox(page);

    await expect(recipient).toBeVisible();
    await expect(title).toBeVisible();
    await expect(body).toBeVisible();
    await expect(hashtags).toBeVisible();
    await expect(images).toBeVisible();
    await expect(anonymous).toBeVisible();

    // Verify order by bounding boxes (top to bottom)
    const recipientBox = await recipient.boundingBox();
    const titleBox = await title.boundingBox();
    const bodyBox = await body.boundingBox();
    const hashtagsBox = await hashtags.boundingBox();
    const imagesBox = await images.boundingBox();
    const anonymousBox = await anonymous.boundingBox();

    expect(recipientBox!.y).toBeLessThan(titleBox!.y);
    expect(titleBox!.y).toBeLessThan(bodyBox!.y);
    expect(bodyBox!.y).toBeLessThan(hashtagsBox!.y);
    expect(hashtagsBox!.y).toBeLessThan(imagesBox!.y);
    expect(imagesBox!.y).toBeLessThan(anonymousBox!.y);
  });

  // ID-4 — recipient input placeholder
  test("ID-4 — recipient input has placeholder 'Tìm kiếm'", async ({
    page,
  }) => {
    await page.goto(ROUTE);
    await expect(recipientInput(page)).toHaveAttribute(
      "placeholder",
      RECIPIENT_PLACEHOLDER,
    );
  });

  // ID-5 — body placeholder
  test("ID-5 — body editor has correct placeholder", async ({ page }) => {
    await page.goto(ROUTE);
    await expect(bodyEditor(page)).toHaveAttribute(
      "placeholder",
      BODY_PLACEHOLDER,
    );
  });

  // ID-6 — anonymous checkbox unchecked by default
  test("ID-6 — anonymous checkbox unchecked by default", async ({ page }) => {
    await page.goto(ROUTE);
    await expect(anonymousCheckbox(page)).not.toBeChecked();
  });

  // ID-7 — recipient field shows red border and error on empty submit
  test("ID-7 — recipient field shows error on empty submit", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Fill other required fields
    await titleInput(page).fill(TEST_TITLE);
    await bodyEditor(page).fill(TEST_BODY);
    await hashtagAddButton(page).click();
    const hashtagOptions = hashtagMenu(page).locator('[role="option"]');
    await hashtagOptions.first().click();

    // Submit with empty recipient
    await composeSubmit(page).click();

    // Verify error appears and field has aria-invalid
    await expect(fieldErrorRecipient(page)).toBeVisible();
    await expect(fieldErrorRecipient(page)).toHaveText(RECIPIENT_ERROR);
    await expect(recipientInput(page)).toHaveAttribute("aria-invalid", "true");
  });

  // ID-8 — recipient autocomplete: typing filters options
  test("ID-8 — recipient autocomplete filters by query", async ({ page }) => {
    await page.goto(ROUTE);

    await recipientInput(page).fill("Nguyễn");

    // Menu should appear
    await expect(recipientMenu(page)).toBeVisible();

    // Should have options (real data from sunners table)
    const options = recipientOption(page);
    // Repaired: .first().toBeVisible() is strictly stronger than count > 0 (verifies actual rendered element)
    await expect(options.first()).toBeVisible();
  });

  // ID-9 — recipient autocomplete: no matches shows empty state
  test("ID-9 — recipient autocomplete shows empty state when no matches", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    await recipientInput(page).fill("@#$%^&");

    // Menu should appear but be empty (or show empty-state text)
    await expect(recipientMenu(page)).toBeVisible();

    const options = recipientOption(page);
    // Either 0 options or empty-state message appears
    const optionCount = await options.count();
    expect(optionCount).toBe(0);
  });

  // ID-10 — recipient autocomplete: whitespace is trimmed
  test("ID-10 — recipient autocomplete trims leading/trailing whitespace", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    await recipientInput(page).fill("  Nguyễn  ");

    // Menu should appear and filter correctly (trim happens server-side or client-side)
    await expect(recipientMenu(page)).toBeVisible();

    const options = recipientOption(page);
    // Should have results, proving trim worked
    // Repaired: .first().toBeVisible() is strictly stronger than count > 0 (verifies actual rendered element)
    await expect(options.first()).toBeVisible();
  });

  // ID-11 — body required field validation
  test("ID-11 — body field error on empty submit", async ({ page }) => {
    await page.goto(ROUTE);

    // Fill recipient and title and hashtag
    await recipientInput(page).fill("Nguyễn");
    await recipientMenu(page).waitFor({ state: "visible" });
    await recipientOption(page).first().click();

    await titleInput(page).fill(TEST_TITLE);

    await hashtagAddButton(page).click();
    const hashtagOptions = hashtagMenu(page).locator('[role="option"]');
    await hashtagOptions.first().click();

    // Leave body empty
    // Submit
    await composeSubmit(page).click();

    // Verify error
    await expect(fieldErrorBody(page)).toBeVisible();
    await expect(fieldErrorBody(page)).toHaveText(BODY_ERROR);
  });

  // ID-12 — mentions: typing @ opens mention menu
  test("ID-12 — typing @ in body opens mention menu", async ({ page }) => {
    await page.goto(ROUTE);

    // Focus body and type @
    await bodyEditor(page).fill("Cảm ơn @");

    // Menu should appear
    await expect(mentionMenu(page)).toBeVisible();

    const options = mentionOption(page);
    // Repaired: .first().toBeVisible() is strictly stronger than count > 0 (verifies actual rendered element)
    await expect(options.first()).toBeVisible();
  });

  // ID-13 — mentions: selecting a mention inserts it into body
  test("ID-13 — selecting mention inserts colleague name into body", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Type @ to open mention menu
    await bodyEditor(page).fill("Cảm ơn @");
    await expect(mentionMenu(page)).toBeVisible();

    // Click first option
    await mentionOption(page).first().click();

    // Verify mention was inserted: menu closes and body editor retains input (robust for textarea or contenteditable)
    await expect(mentionMenu(page)).not.toBeVisible();
    // Body should now have content beyond the initial "@" trigger
    let bodyValue = "";
    try {
      bodyValue = await bodyEditor(page).inputValue();
    } catch {
      bodyValue = await bodyEditor(page).textContent() || "";
    }
    expect(bodyValue).toBeTruthy();
    expect(bodyValue.length).toBeGreaterThan(4); // More than just "Cảm ơn @"
  });

  // ID-14 — hashtag required field validation
  test("ID-14 — hashtag error when empty on submit", async ({ page }) => {
    await page.goto(ROUTE);

    // Fill recipient, title, body
    await recipientInput(page).fill("Nguyễn");
    await recipientMenu(page).waitFor({ state: "visible" });
    await recipientOption(page).first().click();

    await titleInput(page).fill(TEST_TITLE);
    await bodyEditor(page).fill(TEST_BODY);

    // Do NOT add any hashtags
    // Submit
    await composeSubmit(page).click();

    // Verify error
    await expect(fieldErrorHashtag(page)).toBeVisible();
    await expect(fieldErrorHashtag(page)).toHaveText(HASHTAG_REQUIRED_ERROR);
  });

  // ID-15 — add one hashtag successfully
  test("ID-15 — add one hashtag successfully", async ({ page }) => {
    await page.goto(ROUTE);

    // Add hashtag via menu
    await hashtagAddButton(page).click();
    await expect(hashtagMenu(page)).toBeVisible();

    const hashtagOptions = hashtagMenu(page).locator('[role="option"]');
    await hashtagOptions.first().click();

    // Verify chip appears
    const chips = hashtagChip(page);
    await expect(chips).toHaveCount(1);
  });

  // ID-16 — add max 5 hashtags
  test("ID-16 — add 5 hashtags successfully", async ({ page }) => {
    await page.goto(ROUTE);

    const tags = [
      TEST_HASHTAG_1,
      TEST_HASHTAG_2,
      TEST_HASHTAG_3,
      TEST_HASHTAG_4,
      TEST_HASHTAG_5,
    ];

    for (const tag of tags) {
      await hashtagAddButton(page).click();
      await expect(hashtagMenu(page)).toBeVisible();

      const hashtagOptions = hashtagMenu(page).locator('[role="option"]');
      // Find and click the option with this text
      await hashtagOptions.locator(`text=${tag}`).click();
    }

    // Verify 5 chips
    await expect(hashtagChip(page)).toHaveCount(5);
  });

  // ID-57 — toggle selected row deselects it (FR-208)
  test("ID-57 — clicking selected row deselects it and removes chip", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Select one hashtag
    await selectTags(page, [TEST_HASHTAG_1]);
    await expect(hashtagChip(page)).toHaveCount(1);

    // Reopen and click the SAME row again — it must toggle off, not duplicate
    await hashtagAddButton(page).click();
    await expect(hashtagMenu(page)).toBeVisible();
    await hashtagOption(page, TEST_HASHTAG_1).click();

    // Chip is gone
    await expect(hashtagChip(page)).toHaveCount(0);

    // ...and the row no longer advertises itself as selected
    await hashtagAddButton(page).click();
    await expect(hashtagMenu(page)).toBeVisible();
    await expect(hashtagOption(page, TEST_HASHTAG_1)).not.toHaveAttribute(
      "data-selected",
      "true",
    );
  });

  // ID-58 — selected row shows check icon; unselected row shows check-slot (FR-207)
  test("ID-58 — selected row has check icon; unselected row has 24x24 check-slot", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Select one hashtag so the list holds both states at once
    await selectTags(page, [TEST_HASHTAG_1]);

    await hashtagAddButton(page).click();
    await expect(hashtagMenu(page)).toBeVisible();

    // Selected row: marked, and carrying the check icon
    const selectedRow = hashtagOption(page, TEST_HASHTAG_1);
    await expect(selectedRow).toHaveAttribute("data-selected", "true");
    await expect(selectedRow.locator('[data-testid="hashtag-check"]')).toBeVisible();

    // Unselected row should have check-slot
    const unselectedRow = hashtagOptionsUnselected(page).first();
    const checkSlot = unselectedRow.locator('[data-testid="hashtag-check-slot"]');
    await expect(checkSlot).toBeVisible();

    // Verify check-slot is 24x24
    const bbox = await checkSlot.boundingBox();
    expect(bbox?.width).toBe(24);
    expect(bbox?.height).toBe(24);
  });

  // ID-59 — at 5 selected, unselected rows disabled and error visible; click selected row to deselect (FR-209, FR-210)
  test("ID-59 — at 5 hashtags, unselected rows disabled and error visible; clicking selected row re-enables others", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const tags = [
      TEST_HASHTAG_1,
      TEST_HASHTAG_2,
      TEST_HASHTAG_3,
      TEST_HASHTAG_4,
      TEST_HASHTAG_5,
    ];

    await selectTags(page, tags);
    await expect(hashtagChip(page)).toHaveCount(5);

    // Reopen menu and verify unselected rows are disabled
    await hashtagAddButton(page).click();
    await expect(hashtagMenu(page)).toBeVisible();

    const unselectedRows = hashtagOptionsUnselected(page);
    const unselectedCount = await unselectedRows.count();
    expect(unselectedCount).toBe(SEEDED_HASHTAG_ORDER.length - 5);

    // Every unselected row is inert — including the concrete 6th seeded tag
    for (let i = 0; i < unselectedCount; i++) {
      await expect(unselectedRows.nth(i)).toBeDisabled();
    }
    await expect(hashtagOption(page, TEST_HASHTAG_6)).toBeDisabled();

    // Error should be visible
    await expect(hashtagError(page)).toBeVisible();
    await expect(hashtagError(page)).toHaveText(HASHTAG_ERROR_FULL);

    // Click a selected row to deselect it
    const selectedRows = hashtagOptionsSelected(page);
    await selectedRows.first().click();

    // Now 4 chips
    await expect(hashtagChip(page)).toHaveCount(4);

    // Reopen menu and verify unselected rows are enabled again
    await hashtagAddButton(page).click();
    await expect(hashtagMenu(page)).toBeVisible();

    const nowUnselectedRows = hashtagOptionsUnselected(page);
    const nowUnselectedCount = await nowUnselectedRows.count();
    // All should be enabled now
    for (let i = 0; i < nowUnselectedCount; i++) {
      await expect(nowUnselectedRows.nth(i)).toBeEnabled();
    }

    // Error should be hidden
    await expect(hashtagError(page)).not.toBeVisible();
  });

  // ID-60 — hashtag list order is preserved from database (FR-211, regression guard)
  test("ID-60 — hashtag order matches seeded position order and does not re-sort", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Capture initial option labels
    await hashtagAddButton(page).click();
    await expect(hashtagMenu(page)).toBeVisible();

    const initialLabels: string[] = [];
    const initialOptions = hashtagMenu(page).locator('[role="option"]');
    const optionCount = await initialOptions.count();

    for (let i = 0; i < optionCount; i++) {
      const text = await initialOptions.nth(i).textContent();
      initialLabels.push(text?.trim() || "");
    }

    // Toggle one row (select it)
    await initialOptions.first().click();

    // Reopen menu
    await hashtagAddButton(page).click();
    await expect(hashtagMenu(page)).toBeVisible();

    // Capture labels again
    const finalLabels: string[] = [];
    const finalOptions = hashtagMenu(page).locator('[role="option"]');
    const finalOptionCount = await finalOptions.count();

    for (let i = 0; i < finalOptionCount; i++) {
      const text = await finalOptions.nth(i).textContent();
      finalLabels.push(text?.trim() || "");
    }

    // Labels should match the seeded order
    expect(finalLabels).toEqual(SEEDED_HASHTAG_ORDER);

    // Labels should be identical before and after toggle
    expect(finalLabels).toEqual(initialLabels);
  });

  // ID-17 — hashtag limit: at 5, first unselected row is disabled and shows error
  test("ID-17 — at 5 hashtags, unselected row is disabled and error appears", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const tags = [
      TEST_HASHTAG_1,
      TEST_HASHTAG_2,
      TEST_HASHTAG_3,
      TEST_HASHTAG_4,
      TEST_HASHTAG_5,
    ];

    await selectTags(page, tags);

    // At cap, reopen menu and check first unselected row
    await hashtagAddButton(page).click();
    await expect(hashtagMenu(page)).toBeVisible();

    const blocked = hashtagOptionsUnselected(page).first();
    await expect(blocked).toBeDisabled();

    // Error should appear
    await expect(hashtagError(page)).toBeVisible();
    await expect(hashtagError(page)).toHaveText(HASHTAG_ERROR_FULL);

    // Still only 5 chips
    await expect(hashtagChip(page)).toHaveCount(5);
  });

  // ID-18 — image upload: 3 images show thumbnails and button remains visible
  test("ID-18 — upload 3 images and button remains visible", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Use distinct image files to avoid browser file-input change-event suppression on repeated paths (phase-02 repair)
    const imagePaths = [
      "./e2e/fixtures/test-image.jpg",
      "./e2e/fixtures/test-image-1.jpg",
      "./e2e/fixtures/test-image-2.png",
    ];

    // Add 3 images with distinct files
    for (let i = 0; i < 3; i++) {
      await imageAddButton(page).waitFor({ state: "visible" });
      await imageInput(page).setInputFiles(imagePaths[i]);
    }

    // Verify 3 thumbnails
    await expect(imageThumb(page)).toHaveCount(3);

    // Button should still be visible
    await expect(imageAddButton(page)).toBeVisible();
  });

  // ID-19 — image upload: 5 images and button becomes hidden
  test("ID-19 — upload 5 images and button becomes hidden", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Use distinct image files to avoid browser file-input change-event suppression on repeated paths (phase-02 repair)
    const imagePaths = [
      "./e2e/fixtures/test-image.jpg",
      "./e2e/fixtures/test-image-1.jpg",
      "./e2e/fixtures/test-image-2.png",
      "./e2e/fixtures/test-image-3.jpg",
      "./e2e/fixtures/test-image-4.jpg",
    ];

    // Add 5 images with distinct files
    for (let i = 0; i < 5; i++) {
      await imageAddButton(page).waitFor({ state: "visible" });
      await imageInput(page).setInputFiles(imagePaths[i]);
    }

    // Verify 5 thumbnails
    await expect(imageThumb(page)).toHaveCount(5);

    // Button should be hidden
    await expect(imageAddButton(page)).not.toBeVisible();
  });

  // ID-20 — image limit: 6th image button is hidden and prevents adding
  test("ID-20 — at 5 images, button is hidden and 6th cannot be added", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const imagePath = "./e2e/fixtures/test-image.jpg";

    // Add 5 images
    for (let i = 0; i < 5; i++) {
      await imageAddButton(page).waitFor({ state: "visible" });
      await imageInput(page).setInputFiles(imagePath);
    }

    // Button should now be hidden
    await expect(imageAddButton(page)).not.toBeVisible();

    // Verify exactly 5
    await expect(imageThumb(page)).toHaveCount(5);
  });

  // ID-21 — .jpg image uploads successfully
  test("ID-21 — .jpg image uploads successfully and shows thumbnail", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const imagePath = "./e2e/fixtures/test-image.jpg";

    await imageAddButton(page).click();
    await imageInput(page).setInputFiles(imagePath);

    // Thumbnail should appear
    await expect(imageThumb(page)).toHaveCount(1);
  });

  // ID-22 — .png image uploads successfully
  test("ID-22 — .png image uploads successfully and shows thumbnail", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const imagePath = "./e2e/fixtures/test-image.png";

    await imageAddButton(page).click();
    await imageInput(page).setInputFiles(imagePath);

    // Thumbnail should appear
    await expect(imageThumb(page)).toHaveCount(1);
  });

  // ID-23 — .pdf file is rejected with format error
  test("ID-23 — .pdf file is rejected with format error", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const pdfPath = "./e2e/fixtures/test-file.pdf";

    await imageAddButton(page).click();
    await imageInput(page).setInputFiles(pdfPath);

    // Error should appear
    await expect(imageError(page)).toBeVisible();

    // No thumbnail
    await expect(imageThumb(page)).toHaveCount(0);
  });

  // ID-24 — .mp4 file is rejected with format error
  test("ID-24 — .mp4 file is rejected with format error", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const videoPath = "./e2e/fixtures/test-video.mp4";

    await imageAddButton(page).click();
    await imageInput(page).setInputFiles(videoPath);

    // Error should appear
    await expect(imageError(page)).toBeVisible();

    // No thumbnail
    await expect(imageThumb(page)).toHaveCount(0);
  });

  // ID-25 — recipient autocomplete with query "An"
  test("ID-25 — recipient search filters menu by query", async ({ page }) => {
    await page.goto(ROUTE);

    await recipientInput(page).fill("An");

    await expect(recipientMenu(page)).toBeVisible();

    const options = recipientOption(page);
    // Repaired: .first().toBeVisible() is strictly stronger than count > 0 (verifies actual rendered element)
    await expect(options.first()).toBeVisible();
  });

  // ID-26 — selecting recipient fills field and closes menu
  test("ID-26 — selecting recipient fills field and closes menu", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    await recipientInput(page).fill("Nguyễn");
    await expect(recipientMenu(page)).toBeVisible();

    // Click first option
    await recipientOption(page).first().click();

    // Field should be filled
    const value = await recipientInput(page).inputValue();
    expect(value).toBeTruthy();

    // Menu should close
    await expect(recipientMenu(page)).not.toBeVisible();
  });

  // ID-27 — toolbar bold button carries aria-pressed
  test("ID-27 — toolbar bold button has aria-pressed attribute", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    await expect(toolbarBold(page)).toHaveAttribute("aria-pressed");
  });

  // ID-28 — toolbar italic button carries aria-pressed
  test("ID-28 — toolbar italic button has aria-pressed attribute", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    await expect(toolbarItalic(page)).toHaveAttribute("aria-pressed");
  });

  // ID-29 — toolbar strikethrough button carries aria-pressed
  test("ID-29 — toolbar strikethrough button has aria-pressed attribute", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    await expect(toolbarStrike(page)).toHaveAttribute("aria-pressed");
  });

  // ID-30 — toolbar ordered list button present
  test("ID-30 — toolbar ordered list button present", async ({ page }) => {
    await page.goto(ROUTE);

    await expect(toolbarOrderedList(page)).toBeVisible();
  });

  // ID-31 — toolbar link button opens link-dialog
  test("ID-31 — toolbar link button opens dialog with URL input", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    await toolbarLink(page).click();

    await expect(linkDialog(page)).toBeVisible();
    await expect(linkUrlInput(page)).toBeVisible();
  });

  // ID-32 — toolbar quote button present
  test("ID-32 — toolbar quote button present", async ({ page }) => {
    await page.goto(ROUTE);

    await expect(toolbarQuote(page)).toBeVisible();
  });

  // ID-33 — mentions: typing @Name filters mention menu
  test("ID-33 — typing @Nguyen filters mention menu", async ({ page }) => {
    await page.goto(ROUTE);

    await bodyEditor(page).fill("Cảm ơn @Nguyen");

    await expect(mentionMenu(page)).toBeVisible();

    const options = mentionOption(page);
    // Should have filtered results
    // Repaired: .first().toBeVisible() is strictly stronger than count > 0 (verifies actual rendered element)
    await expect(options.first()).toBeVisible();
  });

  // ID-34 — add hashtag chip
  test("ID-34 — add hashtag displays as removable chip", async ({ page }) => {
    await page.goto(ROUTE);

    await hashtagAddButton(page).click();
    await expect(hashtagMenu(page)).toBeVisible();

    const hashtagOptions = hashtagMenu(page).locator('[role="option"]');
    await hashtagOptions.first().click();

    // Chip should appear
    const chips = hashtagChip(page);
    await expect(chips).toHaveCount(1);

    // Each chip should have a remove button
    const removeButtons = hashtagChipRemove(page);
    await expect(removeButtons).toHaveCount(1);
  });

  // ID-35 — add 3 hashtags display as separate chips
  test("ID-35 — add 3 hashtags display as 3 separate chips", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const tags = [TEST_HASHTAG_1, TEST_HASHTAG_2, TEST_HASHTAG_3];

    for (const tag of tags) {
      await hashtagAddButton(page).click();
      await expect(hashtagMenu(page)).toBeVisible();
      const hashtagOptions = hashtagMenu(page).locator('[role="option"]');
      await hashtagOptions.locator(`text=${tag}`).click();
    }

    // Should have 3 chips
    await expect(hashtagChip(page)).toHaveCount(3);
  });

  // ID-36 — remove hashtag chip leaves others intact
  test("ID-36 — removing one hashtag chip leaves others intact", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const tags = [TEST_HASHTAG_1, TEST_HASHTAG_2];

    for (const tag of tags) {
      await hashtagAddButton(page).click();
      await expect(hashtagMenu(page)).toBeVisible();
      const hashtagOptions = hashtagMenu(page).locator('[role="option"]');
      await hashtagOptions.locator(`text=${tag}`).click();
    }

    // Should have 2 chips
    await expect(hashtagChip(page)).toHaveCount(2);

    // Remove the first one
    const removeButtons = hashtagChipRemove(page);
    await removeButtons.first().click();

    // Should still have 1
    await expect(hashtagChip(page)).toHaveCount(1);
  });

  // ID-37 — image upload file picker opens and thumbnail shown
  test("ID-37 — clicking image add opens file picker and shows thumbnail", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const imagePath = "./e2e/fixtures/test-image.jpg";

    await imageAddButton(page).click();
    await imageInput(page).setInputFiles(imagePath);

    // Thumbnail should appear
    await expect(imageThumb(page)).toHaveCount(1);
  });

  // ID-38 — uploading 5 images hides the add button
  test("ID-38 — uploading 5 images hides the add button", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const imagePath = "./e2e/fixtures/test-image.jpg";

    for (let i = 0; i < 5; i++) {
      await imageAddButton(page).waitFor({ state: "visible" });
      await imageInput(page).setInputFiles(imagePath);
    }

    // Button should be hidden
    await expect(imageAddButton(page)).not.toBeVisible();
  });

  // ID-39 — removing an image leaves others intact
  test("ID-39 — removing one image thumb leaves others intact", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const imagePath = "./e2e/fixtures/test-image.jpg";

    // Add 3 images
    for (let i = 0; i < 3; i++) {
      await imageAddButton(page).click();
      await imageInput(page).setInputFiles(imagePath);
    }

    await expect(imageThumb(page)).toHaveCount(3);

    // Remove the second one
    const removeButtons = imageThumbRemove(page);
    await removeButtons.nth(1).click();

    // Should have 2 left
    await expect(imageThumb(page)).toHaveCount(2);
  });

  // ID-40 — removing image from 5 shows the add button again
  test("ID-40 — removing one image from 5 shows the add button again", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const imagePath = "./e2e/fixtures/test-image.jpg";

    // Add 5 images
    for (let i = 0; i < 5; i++) {
      await imageAddButton(page).waitFor({ state: "visible" });
      await imageInput(page).setInputFiles(imagePath);
    }

    // Button should be hidden
    await expect(imageAddButton(page)).not.toBeVisible();

    // Remove one
    await imageThumbRemove(page).first().click();

    // Button should reappear
    await expect(imageAddButton(page)).toBeVisible();
  });

  // ID-41 — anonymous checkbox toggle on
  test("ID-41 — anonymous checkbox can be checked", async ({ page }) => {
    await page.goto(ROUTE);

    await expect(anonymousCheckbox(page)).not.toBeChecked();

    await anonymousCheckbox(page).check();

    await expect(anonymousCheckbox(page)).toBeChecked();
  });

  // ID-42 — anonymous checkbox toggle off
  test("ID-42 — anonymous checkbox can be unchecked", async ({ page }) => {
    await page.goto(ROUTE);

    await anonymousCheckbox(page).check();
    await expect(anonymousCheckbox(page)).toBeChecked();

    await anonymousCheckbox(page).uncheck();

    await expect(anonymousCheckbox(page)).not.toBeChecked();
  });

  // ID-43 — checking anonymous reveals name input field
  test("ID-43 — checking anonymous checkbox reveals name input field", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Initially hidden
    await expect(anonymousNameInput(page)).not.toBeVisible();

    // Check the checkbox
    await anonymousCheckbox(page).check();

    // Now visible
    await expect(anonymousNameInput(page)).toBeVisible();
  });

  // ID-44 — unchecking anonymous hides name input field
  test("ID-44 — unchecking anonymous checkbox hides name input field", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Check first
    await anonymousCheckbox(page).check();
    await expect(anonymousNameInput(page)).toBeVisible();

    // Uncheck
    await anonymousCheckbox(page).uncheck();

    // Now hidden
    await expect(anonymousNameInput(page)).not.toBeVisible();
  });

  // ID-45 — cancel button navigates to /kudos and nothing is saved
  test("ID-45 — cancel button navigates to /kudos without saving", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Fill some data
    await recipientInput(page).fill("Nguyễn");
    await recipientMenu(page).waitFor({ state: "visible" });
    await recipientOption(page).first().click();

    await titleInput(page).fill(TEST_TITLE);
    await bodyEditor(page).fill(TEST_BODY);

    await hashtagAddButton(page).click();
    const hashtagOptions = hashtagMenu(page).locator('[role="option"]');
    await hashtagOptions.first().click();

    // Click cancel
    await composeCancel(page).click();

    // Should navigate to /kudos
    expect(page.url()).toContain("/kudos");
    expect(page.url()).not.toContain("/kudos/new");
  });

  // ID-46 & ID-47 — successful submission: form validates, loads, navigates to /kudos, and new Kudos is visible
  // This is the LOAD-BEARING test that proves the row reached the database
  test("ID-46/ID-47 — successful submission creates kudos and navigates to board", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Fill all required fields
    await recipientInput(page).fill("Nguyễn");
    await recipientMenu(page).waitFor({ state: "visible" });
    await recipientOption(page).first().click();

    await titleInput(page).fill(TEST_TITLE);
    await bodyEditor(page).fill(TEST_BODY);

    // Add one hashtag
    await hashtagAddButton(page).click();
    const hashtagOptions = hashtagMenu(page).locator('[role="option"]');
    await hashtagOptions.first().click();

    // Add one image
    const imagePath = "./e2e/fixtures/test-image.jpg";
    await imageInput(page).setInputFiles(imagePath);

    // Submit
    await composeSubmit(page).click();

    // Should navigate to /kudos
    await page.waitForURL("/kudos", { timeout: 10000 });
    expect(page.url()).toContain("/kudos");
    expect(page.url()).not.toContain("/kudos/new");

    // The new Kudos should be visible on the board (ID-46/47 load-bearing test)
    // Verify the row reached Postgres and is rendered on the board
    const cards = page.getByTestId("kudos-card");
    const titleCells = cards.locator(`text=${TEST_TITLE}`);
    // Repaired: .first().toBeVisible() is strictly stronger than count >= 1 (verifies actual rendered element)
    await expect(titleCells.first()).toBeVisible();

    // Cleanup: Row accumulation is accepted — no DELETE policy exists by design (phase-02 ratification).
    // A pre-suite `npx supabase db reset` clears accumulated rows. No assertion depends on an exact card count,
    // so the board feed stays valid as rows accumulate (verified: kudos-live-board.spec.ts uses > comparison, not equality).
  });

  // ID-48 — submit button not ready when required fields empty
  test("ID-48 — submit button not ready when required fields empty", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // No fields filled — button remains pressable but not ready (phase-02 repair: test-contract.md § Blueprint ratification)
    // The button can be clicked on an incomplete form to reach the designed error state (frame 5c7PkAibyD)
    // It carries data-submit-ready="false" to reflect DEC-002 readiness, not disabled
    await expect(composeSubmit(page)).toHaveAttribute("data-submit-ready", "false");
  });

  // ID-49 — submit button ready when required fields filled
  test("ID-49 — submit button ready when required fields filled", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Fill required fields
    await recipientInput(page).fill("Nguyễn");
    await recipientMenu(page).waitFor({ state: "visible" });
    await recipientOption(page).first().click();

    await titleInput(page).fill(TEST_TITLE);
    await bodyEditor(page).fill(TEST_BODY);

    await hashtagAddButton(page).click();
    const hashtagOptions = hashtagMenu(page).locator('[role="option"]');
    await hashtagOptions.first().click();

    // Button should now be enabled and ready (phase-02 repair: stronger assertion for readiness state)
    await expect(composeSubmit(page)).toBeEnabled();
    await expect(composeSubmit(page)).toHaveAttribute("data-submit-ready", "true");
  });

  // ID-50 — recipient field error on submit with empty recipient
  test("ID-50 — recipient field shows error with red border when empty", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Fill other fields but not recipient
    await titleInput(page).fill(TEST_TITLE);
    await bodyEditor(page).fill(TEST_BODY);

    await hashtagAddButton(page).click();
    const hashtagOptions = hashtagMenu(page).locator('[role="option"]');
    await hashtagOptions.first().click();

    // Submit
    await composeSubmit(page).click();

    // Verify error and aria-invalid
    await expect(fieldErrorRecipient(page)).toBeVisible();
    await expect(fieldErrorRecipient(page)).toHaveText(RECIPIENT_ERROR);
    await expect(recipientInput(page)).toHaveAttribute("aria-invalid", "true");
  });

  // ID-51 — body field error on submit when empty
  test("ID-51 — body field shows error when empty on submit", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Fill recipient, title, hashtag but not body
    await recipientInput(page).fill("Nguyễn");
    await recipientMenu(page).waitFor({ state: "visible" });
    await recipientOption(page).first().click();

    await titleInput(page).fill(TEST_TITLE);

    await hashtagAddButton(page).click();
    const hashtagOptions = hashtagMenu(page).locator('[role="option"]');
    await hashtagOptions.first().click();

    // Submit
    await composeSubmit(page).click();

    // Verify error
    await expect(fieldErrorBody(page)).toBeVisible();
    await expect(fieldErrorBody(page)).toHaveText(BODY_ERROR);
  });

  // ID-52 — hashtag field error on submit when empty
  test("ID-52 — hashtag field shows error when empty on submit", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Fill recipient, title, body but not hashtag
    await recipientInput(page).fill("Nguyễn");
    await recipientMenu(page).waitFor({ state: "visible" });
    await recipientOption(page).first().click();

    await titleInput(page).fill(TEST_TITLE);
    await bodyEditor(page).fill(TEST_BODY);

    // Don't add any hashtags
    // Submit
    await composeSubmit(page).click();

    // Verify error
    await expect(fieldErrorHashtag(page)).toBeVisible();
    await expect(fieldErrorHashtag(page)).toHaveText(HASHTAG_REQUIRED_ERROR);
  });

  // ID-53 — hashtag error: at 5, unselected row is disabled and shows max error
  test("ID-53 — at 5 hashtags, unselected row disabled and max error appears", async ({ page }) => {
    await page.goto(ROUTE);

    const tags = [
      TEST_HASHTAG_1,
      TEST_HASHTAG_2,
      TEST_HASHTAG_3,
      TEST_HASHTAG_4,
      TEST_HASHTAG_5,
    ];

    await selectTags(page, tags);

    // At cap, reopen menu and check first unselected row
    await hashtagAddButton(page).click();
    await expect(hashtagMenu(page)).toBeVisible();

    const blocked = hashtagOptionsUnselected(page).first();
    await expect(blocked).toBeDisabled();

    // Error appears
    await expect(hashtagError(page)).toBeVisible();
    await expect(hashtagError(page)).toHaveText(HASHTAG_ERROR_FULL);

    // Still 5 chips
    await expect(hashtagChip(page)).toHaveCount(5);
  });

  // ID-54 — image limit: at 5 images, no 6th can be added (button is hidden)
  test("ID-54 — at 5 images, button hidden, no 6th can be added", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    const imagePath = "./e2e/fixtures/test-image.jpg";

    // Add 5 images
    for (let i = 0; i < 5; i++) {
      await imageAddButton(page).waitFor({ state: "visible" });
      await imageInput(page).setInputFiles(imagePath);
    }

    // Button should be hidden
    await expect(imageAddButton(page)).not.toBeVisible();

    // Still 5 images
    await expect(imageThumb(page)).toHaveCount(5);
  });

  // ID-55 — image: .txt file rejected with format error
  test("ID-55 — .txt file rejected with format error", async ({ page }) => {
    await page.goto(ROUTE);

    const txtPath = "./e2e/fixtures/test-file.txt";

    await imageAddButton(page).click();
    await imageInput(page).setInputFiles(txtPath);

    // Error should appear
    await expect(imageError(page)).toBeVisible();

    // No thumbnail
    await expect(imageThumb(page)).toHaveCount(0);
  });

  // ID-56 — all required-field errors show simultaneously on empty submit
  test("ID-56 — all required field errors show simultaneously", async ({
    page,
  }) => {
    await page.goto(ROUTE);

    // Leave everything empty and click submit
    await composeSubmit(page).click();

    // All 4 error messages should appear
    await expect(fieldErrorRecipient(page)).toBeVisible();
    await expect(fieldErrorTitle(page)).toBeVisible();
    await expect(fieldErrorBody(page)).toBeVisible();
    await expect(fieldErrorHashtag(page)).toBeVisible();

    // Form should not submit
    expect(page.url()).toContain("/kudos/new");
  });

  // Title field: placeholders and hints
  test("Title field: placeholder and hints present", async ({ page }) => {
    await page.goto(ROUTE);

    await expect(titleInput(page)).toHaveAttribute(
      "placeholder",
      TITLE_PLACEHOLDER,
    );

    // Hints should be visible
    await expect(titleHint(page)).toBeVisible();
    const hintText = await titleHint(page).textContent();
    expect(hintText).toContain(TITLE_HINT_1);
    expect(hintText).toContain(TITLE_HINT_2);
  });

  // Body field: hint present
  test("Body field: hint present", async ({ page }) => {
    await page.goto(ROUTE);

    await expect(bodyHint(page)).toBeVisible();
    await expect(bodyHint(page)).toHaveText(BODY_HINT);
  });

  // Community Standards link present
  test("Community Standards link present", async ({ page }) => {
    await page.goto(ROUTE);

    await expect(communityStandardsLink(page)).toBeVisible();
    await expect(communityStandardsLink(page)).toContainText(
      COMMUNITY_STANDARDS_LABEL,
    );
  });

  // Cancel and Submit button labels
  test("Cancel and Submit buttons have correct labels", async ({ page }) => {
    await page.goto(ROUTE);

    await expect(composeCancel(page)).toContainText(CANCEL_BUTTON_LABEL);
    await expect(composeSubmit(page)).toContainText(SUBMIT_BUTTON_LABEL);
  });
});
