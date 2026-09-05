---
feature: F002 · test_policy: e2e-red-first · owner: momorph-ui-implementer
fileKey: 9ypp4enmFmdK3YAFJLIu6C · screenId: i87tDx10uM · depends_on: [] · status: completed · effort: 1h
completed: 2026-09-05
---
# Phase 03 — Track A: MoMorph asset export
## MoMorph refs:
- Homepage SAA: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/i87tDx10uM
- Clarifications: plans/260905-1153-homepage-saa/clarifications.md
- testPolicy: e2e-red-first

**Goal:** export the 35 `MM_MEDIA_*` nodes into `public/images/home/` and record what landed, so phases 04-06 reference real files instead of guessing (RISK-02, [functional-spec § 11](./spec/homepage-saa/functional-spec.md)).

**Owns (only):** `public/images/home/**`, `./design/asset-manifest.md`.
**Out of scope:** every `.tsx`, `public/images/login/**`, `app/globals.css`. No component code here.

**Must hold:**
- Composed artwork is downloaded, never rebuilt in CSS: hero keyvisual, `ROOT FURTHER` wordmark, the `ROOT`/`FURTHER` watermarks, six award thumbnails (`MM_MEDIA_Award BG` + name layer), Kudos block background, two widget icons (clarifications, "Resolved from source data").
- Award files are named `award-<slug>.png` for the six frozen slugs, matching `lib/awards.ts` (phase 02).
- `asset-manifest.md` carries one row per node — node name, output path, intrinsic width×height, exported yes/no. Phases 04-06 read the dimensions from it for `next/image`.
- A node that fails to export is listed MISSING with its geometry, so the consuming phase ships the recorded box over the design's flat colour and dropping the file in later needs zero code edits (the `/login` hero precedent).
- SVG for flat icons, PNG for composed artwork. No re-encoding, upscaling, or invented crops.

**Done:** `public/images/home/` populated, manifest written, MISSING list reported upward; nothing outside the two owned paths touched.
**Rollback:** `rm -rf public/images/home/` and delete the manifest — no code references it until 04.
