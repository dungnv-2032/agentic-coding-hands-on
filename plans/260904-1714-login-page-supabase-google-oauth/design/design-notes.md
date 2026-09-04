# Design structure notes — Login (GzbNeVGJHz)

Frame `662:14387` "Login", design canvas **1440 × 1024**. Frame screenshot: `login-screen.png`.

## Node tree (structural)

```
662:14387  Login (FRAME)
├── 662:14388  mms_C_Keyvisual (GROUP)          ← full-bleed background artwork
│   └── 662:14389  image 1 (RECTANGLE)          ← 1441×1022 @ (0,2); image fill
├── 662:14391  mms_A_Header (INSTANCE)
│   ├── mms_A.1_Logo  → MM_MEDIA_Logo           ← saa-logo.png (52×48)
│   └── mms_A.2_Language → Button
│       ├── MM_MEDIA_VN    ← flag-vn.svg
│       ├── TEXT "VN"
│       └── MM_MEDIA_Down  ← chevron-down.svg
├── 662:14392  Rectangle 57 (RECTANGLE)         ← header bar backdrop
├── 662:14393  mms_B_Bìa (FRAME)
│   └── 662:14394  Frame 487
│       ├── 662:14395  mms_B.1_Key Visual       ← 1152×200 @ (144,288)
│       │   └── 2939:9548 MM_MEDIA_Root Further Logo  ← root-further.png (451×200)
│       └── 662:14755  Frame 550
│           ├── 662:14753  mms_B.2_content (TEXT)     ← subtitle + tagline
│           └── 662:14425  mms_B.3_Login (FRAME)
│               └── 662:14426  Button-IC About
│                   ├── TEXT "LOGIN With Google"
│                   └── MM_MEDIA_Google  ← google.svg
├── 662:14390  Cover (RECTANGLE)                ← scrim/overlay
└── 662:14447  mms_D_Footer (INSTANCE)
    └── TEXT "Bản quyền thuộc về Sun* © 2025"
```

## Corrections to the spec CSV, found in the node data

- **Spec item 2.1 is mislabelled.** Its prose describes the abstract wave artwork, but node
  `662:14395` "mms_B.1_Key Visual" is a 1152×200 frame at (144,288) whose only child is the
  **ROOT FURTHER wordmark image**. The actual background artwork is a *different* node,
  `662:14389` under `mms_C_Keyvisual`, which no spec row covers. Treat the wordmark and the
  background as two separate assets.
- **"ROOT FURTHER" is an image, not text** (`root-further.png`, 451×200) — do not attempt to
  reproduce it with a webfont.
- **Google icon sits to the RIGHT of the button label**, per the frame screenshot, even though
  `buttonType` is recorded as `icon_text`.
- Test case `6ae76d15` says the login button is "centered below the hero descriptions". The
  design shows it **left-aligned** in the left-hand content column. The rendered design is
  authoritative; read "centered" as "aligned with the description column".

## Background fill geometry (node 662:14389)

```
width: 1441px; height: 1022px; position: absolute; top: 2px; left: 0;
background: url(...) lightgray -440px -217.975px / 159.763% 133.371% no-repeat;
aspect-ratio: 141/100;
```

## Asset inventory

| Asset | Node | Local path | Status |
|---|---|---|---|
| SAA 2025 logo | `I662:14391;178:1033;178:1030` | `public/images/login/saa-logo.png` (52×48) | downloaded |
| VN flag | `I662:14391;186:1696;186:1821;186:1709` | `public/images/login/flag-vn.svg` | downloaded |
| Chevron down | `I662:14391;186:1696;186:1821;186:1441` | `public/images/login/chevron-down.svg` | downloaded |
| ROOT FURTHER wordmark | `2939:9548` | `public/images/login/root-further.png` (451×200) | downloaded |
| Google icon | `I662:14426;186:1766` | `public/images/login/google.svg` | downloaded |
| **Hero background artwork** | **`662:14389`** | **`public/images/login/hero.png`** | **MISSING — see below** |

### Hero artwork retrieval failure

Not obtainable through the MCP as of this session:

- `get_figma_image(662:14389)` and `(662:14388)` → **HTTP 500** (scale 1 and 2, png)
- `get_media_file(nodeId 662:14389)` → **HTTP 401 Unauthorized**
- `get_design_item_image(662:14389)` → "Position data … invalid or missing"
- Not listed by `list_media_items` — it is a plain image fill, not an `MM_MEDIA_*` node
- **Diagnosis:** `get_figma_image` also returns 500 for the top-level frame `662:14387`, which is
  known to render (`get_frame_image` served it fine). The render endpoint is therefore **down
  service-wide**, not rejecting this particular node — so a later retry has a good chance.

It cannot be reconstructed from `login-screen.png`, because the wordmark, copy, button, header
and footer are composited on top of it. Guessing a substitute would violate the MoMorph rule that
design data is authoritative.

**Resolution path:** retry the render endpoint (the 500 may be transient); if it persists, the
artwork must be exported from Figma by hand into `public/images/login/hero.png`.
