/**
 * Shared constants for the Floating Action Button (FAB) E2E spec.
 *
 * Every string and geometry value below is transcribed verbatim from
 * `plans/260910-0907-floating-action-button/clarifications.md` § "Test contract"
 * and `plans/260910-0907-floating-action-button/design/geometry.md`,
 * which are AUTHORITATIVE (MoMorph screens `_hphd32jN2` and `Sv7DFwBw1h`).
 *
 * Repo convention (researcher-02 § 3): Vietnamese copy is never inlined in a
 * spec body — a copy change must stay a one-line fix here.
 */

/** ============================================================================
 *  Fixed testids — hardwired in the test contract, must not drift
 * ============================================================================ */

/** The collapsed trigger pill (aria-expanded, aria-controls). */
export const FAB_TRIGGER_TESTID = "fab-trigger";

/** The expanded menu container (flex column, gap 20px). */
export const FAB_MENU_TESTID = "fab-menu";

/** The "Thể lệ" button inside the menu (→ /standards). */
export const FAB_STANDARDS_TESTID = "fab-standards";

/** The "Viết KUDOS" button inside the menu (→ /kudos/new, redirects anon to /login). */
export const FAB_WRITE_KUDOS_TESTID = "fab-write-kudos";

/** The round red "Hủy" close button. */
export const FAB_CLOSE_TESTID = "fab-close";

/** ============================================================================
 *  Routes — tested destinations
 * ============================================================================ */

export const HOME_ROUTE = "/";
export const STANDARDS_ROUTE = "/standards";
export const COMPOSE_ROUTE = "/kudos/new";
export const LOGIN_ROUTE = "/login";

/** ============================================================================
 *  Labels — Vietnamese copy from the design, never inlined in tests
 * ============================================================================ */

/** Trigger pill label. */
export const TRIGGER_LABEL = "Hành động nhanh";

/** Visible label on the menu's `/standards` button. */
export const MENU_STANDARDS_LABEL = "Thể lệ";

/** Visible label on the menu's `/kudos/new` button. */
export const MENU_WRITE_KUDOS_LABEL = "Viết KUDOS";

/** Close button label — icon-only, so this is its accessible name. */
export const CLOSE_LABEL = "Hủy";

/**
 * Accessible names of the two text-bearing menu items. Each item carries an
 * `aria-label`, which overrides its visible text, so the two differ on purpose:
 * `home.widget.{standards,writeKudos}` keep the fuller wording the pre-F008
 * direct links used (`vi-home.ts`), and WCAG 2.5.3 still holds because each
 * accessible name contains its button's visible label. Pinned here so neither
 * value can drift silently — `the-le.spec.ts` depends on the standards one.
 */
export const STANDARDS_ARIA_LABEL = "Thể lệ SAA";
export const WRITE_KUDOS_ARIA_LABEL = "Viết kudos";

/** ============================================================================
 *  Geometry Constants (from design/geometry.md, ±1px tolerance on sizes)
 * ============================================================================ */

/** Menu container dimensions (design/geometry.md: expanded node 313:9140). */
export const MENU_WIDTH = 214;
export const MENU_HEIGHT = 224;

/** "Thể lệ" button dimensions. */
export const STANDARDS_BUTTON_WIDTH = 149;
export const STANDARDS_BUTTON_HEIGHT = 64;

/** "Viết KUDOS" button dimensions. */
export const WRITE_KUDOS_BUTTON_WIDTH = 214;
export const WRITE_KUDOS_BUTTON_HEIGHT = 64;

/** "Hủy" close button dimensions. */
export const CLOSE_BUTTON_WIDTH = 56;
export const CLOSE_BUTTON_HEIGHT = 56;

/** Vertical gap between buttons (flex gap: 20px). */
export const BUTTON_GAP = 20;

/** ============================================================================
 *  Colour Constants (from design/geometry.md, exact RGB values)
 * ============================================================================ */

/** Background colour of "Thể lệ" and "Viết KUDOS" buttons (design/geometry.md). */
export const BUTTON_YELLOW_BG = "rgb(255, 234, 158)"; // #FFEA9E

/** Background colour of "Hủy" close button (design/geometry.md). */
export const CLOSE_BUTTON_RED_BG = "rgb(212, 39, 29)"; // #D4271D

/** Label text colour (shared across all menu items). */
export const LABEL_TEXT_COLOR = "rgb(0, 16, 26)"; // #00101A

/** ============================================================================
 *  Typography Constants (from design/geometry.md)
 * ============================================================================ */

/** Label font weight (all menu labels). */
export const LABEL_FONT_WEIGHT = "700";

/** Label font size (all menu labels). */
export const LABEL_FONT_SIZE = "24px";

/** Label line height (all menu labels). */
export const LABEL_LINE_HEIGHT = "32px";

/** Button border radius for yellow buttons. */
export const BUTTON_BORDER_RADIUS = "4px";

/** Button border radius for close button (full round). */
export const CLOSE_BUTTON_BORDER_RADIUS_MIN = 28; // ≥ 28px (full round)

/** ============================================================================
 *  Layout Tolerance
 * ============================================================================ */

/** Tolerance for bounding box metrics (sub-pixel layout). */
export const BOX_TOLERANCE_PX = 1;

/** Viewport dimensions for FAB-08 geometry test. */
export const GEOMETRY_TEST_VIEWPORT_WIDTH = 1440;
export const GEOMETRY_TEST_VIEWPORT_HEIGHT = 1024;
