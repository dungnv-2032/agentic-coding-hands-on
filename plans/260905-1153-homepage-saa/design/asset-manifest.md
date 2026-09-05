# Homepage SAA — Asset Manifest

Source: MoMorph fileKey `9ypp4enmFmdK3YAFJLIu6C`, screenId `i87tDx10uM`.
All assets exported verbatim from `mcp__momorph__get_media_files` (S3-signed URLs resolved to
raw PNG/SVG bytes — no re-encoding, no CSS recreation). Composed award thumbnails were built by
alpha-compositing the shared `MM_MEDIA_Award BG` layer with each award's per-category name layer,
using the exact pixel offsets read from MoMorph node geometry (`query_section` on each
`mms_C2.x.1_Picture-Award` instance) — not guessed.

`next/image` requires real `width`/`height` — use the **Intrinsic (px)** column exactly.
`priority` is deprecated in Next 16; consuming phases use `preload` per AGENTS.md docs.

## Exported assets

| MoMorph node id | Semantic role | Intrinsic (px) | Repo path | Consumed by |
|---|---|---|---|---|
| `2167:9028` (`MM_MEDIA_Keyvisual BG`) | Hero keyvisual background (full-bleed, dark root-pattern artwork) | 1512×1392 | `public/images/home/keyvisual-hero-bg.png` | Phase 05 (hero) |
| `2788:12911` (`MM_MEDIA_Root Further Logo`) | "ROOT FURTHER" hero wordmark image | 451×200 | `public/images/home/root-further-hero-wordmark.png` | Phase 05 (hero) |
| `3204:10155` (`MM_MEDIA_Root Text`) | "ROOT" decorative watermark in the B4 content block | 189×67 | `public/images/home/root-watermark-text.png` | Phase 06 (body) |
| `3204:10154` (`MM_MEDIA_Further Text`) | "FURTHER" decorative watermark in the B4 content block | 290×67 | `public/images/home/further-watermark-text.png` | Phase 06 (body) |
| `I2167:9075;214:1019` (BG `81:2442` + name `214:666;10:951`, composed) | Award card thumbnail — Top Talent | 336×336 | `public/images/home/award-top-talent.png` | Phase 06 (awards grid) |
| `I2167:9076;214:1019` (BG `81:2442` + name `214:666;214:654`, composed) | Award card thumbnail — Top Project | 336×336 | `public/images/home/award-top-project.png` | Phase 06 (awards grid) |
| `I2167:9077;214:1019` (BG `81:2442` + name `214:666;214:655`, composed) | Award card thumbnail — Top Project Leader | 336×336 | `public/images/home/award-top-project-leader.png` | Phase 06 (awards grid) |
| `I2167:9079;214:1019` (BG `81:2442` + name `214:666;214:656`, composed) | Award card thumbnail — Best Manager | 336×336 | `public/images/home/award-best-manager.png` | Phase 06 (awards grid) |
| `I2167:9080;214:1019` (BG `81:2442` + name `214:666;214:657`, composed) | Award card thumbnail — Signature 2025 - Creator | 336×336 | `public/images/home/award-signature-2025-creator.png` | Phase 06 (awards grid) |
| `I2167:9081;214:1019` (BG `81:2442` + name `214:666;214:653`, composed) | Award card thumbnail — MVP | 336×336 | `public/images/home/award-mvp.png` | Phase 06 (awards grid) |
| `I3390:10349;313:8416` (`MM_MEDIA_Kudos Background`) | Sun* Kudos section background artwork | 1120×500 | `public/images/home/kudos-section-bg.png` | Phase 06 (Kudos block) |
| `I3390:10349;329:2948` (`MM_MEDIA_Logo/Kudos`) | Sun* Kudos logo/wordmark (vector) | 364×74 | `public/images/home/kudos-logo.svg` | Phase 06 (Kudos block) |
| `I5022:15169;214:3839;186:1763` (`MM_MEDIA_Pen`) | Widget button — pen icon (left glyph, vector) | 24×24 | `public/images/home/widget-pen-icon.svg` | Phase 06 (widget button) |
| `I5022:15169;214:3839;186:1766;214:3762` (`MM_MEDIA_Kudos Logo`) | Widget button — SAA/Kudos glyph (right icon, vector) | 20×19 | `public/images/home/widget-saa-kudos-glyph.svg` | Phase 06 (widget button) |
| `I5001:14800;342:1408;178:1030` (`MM_MEDIA_Logo`, footer instance) | Footer SAA brand logo | 69×64 | `public/images/home/footer-saa-logo.png` | Phase 06 (footer) |

## Reused (not re-exported — DRY)

| MoMorph node id | Semantic role | Intrinsic (px) | Repo path | Consumed by | Note |
|---|---|---|---|---|---|
| `I2167:9091;178:1033;178:1030` (`MM_MEDIA_Logo`, header instance) | Header SAA brand logo | 52×48 | `public/images/login/saa-logo.png` | Phase 04 (header) | Byte-identical (md5 `b1e72bf604326f7af02ce0e47ef0a638`) to the existing `/login` asset — verified via md5sum before reuse. Not duplicated into `public/images/home/`. |

## Skipped (already SVG components — do not duplicate)

| Node name | Reason | Where it already lives |
|---|---|---|
| `MM_MEDIA_FLAG_VN` / VN/EN flags | Existing inline SVG components | `app/_components/icons.tsx` (per phase 01 promotion) |
| `MM_MEDIA_Down` / chevron | Existing inline SVG component | `app/_components/icons.tsx` |
| `MM_MEDIA_Up` (repeated on every `Button-IC`, header notification/profile icons, all six award "Chi tiết" buttons, Kudos "Chi tiết" button) | Same shared chevron/arrow icon reused via Figma component instances — one visual asset, already covered by the existing icon set | `app/_components/icons.tsx` |
| `MM_MEDIA_Noti?=True` | Notification bell — generic icon, no unique artwork beyond an existing icon shape | not exported; treat as an icon-set glyph if phase 04 needs one |
| `MM_MEDIA_User Profile` | Account icon — generic icon, no unique artwork | not exported; same as above |

## MISSING

None. All 35 `MM_MEDIA_*` nodes reported by `list_media_nodes` were accounted for: 14 exported as new
files, 1 resolved to an existing repo asset by exact byte match, and the remaining icon-instance
duplicates (`MM_MEDIA_Up` ×9, flags, chevron, bell, profile) map to icons already owned by
`app/_components/icons.tsx` or are generic icon-set glyphs with no unique per-node artwork to export.

## Award card composition detail (for audit)

Card container is 336×336. Name-layer offset is `(nameStartX - cardStartX, nameStartY - cardStartY)`
read from MoMorph absolute position data, pasted onto the shared BG with alpha compositing:

| Slug | Name layer size | Offset (x, y) |
|---|---|---|
| top-talent | 222×36 | 57, 151 |
| top-project | 232×35 | 52, 151 |
| top-project-leader | 232×64 | 52, 136 |
| best-manager | 232×30 | 52, 153 |
| signature-2025-creator | 232×54 | 52, 141 |
| mvp | 116×52 | 110, 142 |
