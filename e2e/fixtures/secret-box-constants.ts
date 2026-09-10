/**
 * Secret Box test constants — geometry and UI elements
 *
 * Source: plans/260910-1708-open-secret-box/design/geometry.md
 * Seeded badges: supabase/seed.sql:392-397
 */

export const ROUTE = "/kudos/secret-box";

// Test IDs — match the component implementation
export const TEST_IDS = {
  panel: "secret-box-panel",
  opener: "secret-box-opener",
  badge: "secret-box-badge",
  count: "secret-box-count",
  instruction: "secret-box-instruction",
  close: "secret-box-close",
  signIn: "secret-box-signin",
};

// Copy strings from design/geometry.md
export const STRINGS = {
  title: "KHÁM PHÁ SECRET BOX CỦA BẠN",
  instruction: "Click vào box để mở",
  countLabel: "Secretbox chưa mở",
};

// Badge labels from supabase/seed.sql:392-397 (kind='collectible_icon')
export const BADGE_LABELS = [
  "REVIVAL",
  "TOUCH OF LIGHT",
  "STAY GOLD",
  "FLOW TO HORIZON",
  "BEYOND THE BOUNDARY",
  "ROOT FURTHER",
];

// Geometry constants from design/geometry.md (frame 1466:7676 at 1440×1024)
export const GEOMETRY = {
  // Frame size and positioning
  frameWidth: 651.5,
  frameHeight: 822.6,
  borderRadius: 12.73,
  backgroundColor: "#00101A",

  // Padding
  paddingVertical: 23.87,
  paddingHorizontal: 12.73,
  childWidth: 626,

  // Gap between elements
  gap: 22.28,

  // Title (1466:7678)
  title: {
    font: "Montserrat 700",
    size: "25.46/31.82",
    color: "#FFEA9E",
    textAlign: "center",
    width: 626,
  },

  // Close glyph (1466:7679)
  closeGlyph: {
    size: 19,
    posX: { min: 606, max: 625 },
    posY: { min: 39, max: 58 },
  },

  // Upper hairline (1466:7680)
  hairlineUpper: {
    width: 626,
    height: 1,
    color: "#2E3940",
    posY: 86,
  },

  // Instruction (1466:7683)
  instruction: {
    font: "Montserrat 700",
    size: "12.73/19.09",
    letterSpacing: 0.398,
    color: "white",
  },

  // Box image (1466:7684)
  boxImage: {
    size: 557,
    posX: { min: 47, max: 603 },
    posY: { min: 152, max: 708 },
  },

  // Lower hairline (1466:7688)
  hairlineLower: {
    width: 626,
    height: 1,
    color: "#2E3940",
    posY: 731,
  },

  // Counter section (1466:7689)
  counter: {
    layout: "row",
    gap: 6.36,
    width: 174,
    height: 35,
    textAlign: "center",
  },

  // Count label (1466:7692)
  countLabel: {
    font: "Montserrat 700",
    size: "12.73/19.09",
    letterSpacing: 0.398,
    color: "white",
  },

  // Count value (1466:7693)
  countValue: {
    font: "Montserrat 700",
    size: "28.64/35.0",
    color: "#FFEA9E",
  },
};

// Viewport for geometry assertions (SB-A4)
export const GEOMETRY_VIEWPORT = {
  width: 1440,
  height: 1024,
};
