# Implementer — Viết Kudo hardening pass (3 reviewer findings)

## Files touched (all within scope)
- `lib/kudos/validate-compose.ts` (87 → 137 lines): image-cap check + byte-signature sniff
- `app/kudos/new/_actions/upload-kudos-image.ts` (81 → 94 lines): wires the sniff before upload
- `lib/kudos/board-data.ts` (200 → 188 lines): import-block condensing only, no logic touched
- `app/kudos/new/_components/compose-form.tsx` (200 → 193 lines): import + comment condensing only, no logic touched

## Finding 1 — image count now field-specific
Added to `validateCompose()`: `imageUrls.length > MAX_IMAGES` → `errors.form = "tooMany"`.
`ComposeFieldErrors` (frozen `compose-contract.ts`) has **no `image` key** — only
recipient/title/body/hashtag/form — so `form` is the only field-specific bucket available;
I did not touch the frozen contract to add one. This still closes the finding: before, an
over-cap submission fell through to the DB round-trip and returned the generic
`{form:"unknown"}`; now `validateCompose()` (called first in `create-kudos.ts:78`, unmodified,
outside my scope) short-circuits it locally with a specific `"tooMany"` code, mirroring the
hashtag path's code exactly. SQL's own `array_length(...) > 5` check is untouched — still the
last word for any direct-RPC caller.
Evidence: `verify-finding1-image-cap.mjs` — 6 `imageUrls` → `{"form":"tooMany"}`; 5 (at cap) → `{}`.

## Finding 2 — MIME sniffed by bytes, not trusted from `File.type`
Added `IMAGE_SIGNATURES` + `matchesImageSignature(mime, bytes)` to `validate-compose.ts` (pure,
no I/O — matches the module's existing zero-dependency contract) and
`IMAGE_SIGNATURE_SNIFF_LENGTH = 12`. Signatures: JPEG `FF D8 FF`, PNG `89 50 4E 47 0D 0A 1A 0A`,
GIF `47 49 46 38` ("GIF8", covers 87a/89a), WEBP `RIFF` @0 + `WEBP` @8 (non-contiguous — the
reason signatures are offset/bytes pairs, not flat prefixes). All 4 `ACCEPTED_IMAGE_MIME`
values are sniffable; none were narrowed or left trusted.
`upload-kudos-image.ts` keeps the existing declared-type gate (`isAcceptedImageType`) as the
cheap first check, then reads `file.slice(0, 12).arrayBuffer()` and rejects with the same
`UploadKudosImageError("invalidType")` — no contract-copy change — when the sniff fails.
Evidence: `verify-finding2-mime-sniff.mjs` against real fixture bytes —
- `test-file.pdf` bytes (`25 50 44 46...`) declared `image/jpeg` → **rejected**
- `test-video.mp4` declared `image/png`, `test-file.txt` declared `image/jpeg` → **rejected**
- `e2e/fixtures/test-image.jpg` (real `FF D8 FF`) and `test-image.png` (real PNG signature,
  confirmed via `file --mime-type`) → **accepted**, so ID-21/ID-22 are unaffected.

## Finding 3 — both files under 200 lines
No coherent extraction target existed inside my 4 owned files (extraction would require a new
file, outside "write ONLY these"), so I trimmed mechanically: multi-line import lists condensed
to the repo's own existing single-line-import convention (`rich-text.ts`, `create-kudos.ts`
already do this; no `printWidth`/`max-len` rule exists — confirmed via eslint config and a clean
`npx eslint` run on the longest existing line, 191 chars), and `compose-form.tsx`'s two design
doc-comments were re-wrapped tighter with **zero content removed** — every citation
(`get_node`, `get_overview`, `forms.md:190-274`, Key Insight 4) is intact, just fewer lines.
No logic line was touched in either file. Result: `board-data.ts` 188, `compose-form.tsx` 193.

## Verification
- `npm run typecheck`: **0 errors**
- `npx eslint <4 owned files>`: **0 errors, 0 warnings**
- `rm -rf .next && npm run build`: **exit 0** (all 14 routes compiled, incl. `/kudos/new`, `/kudos`)
- `npx playwright test e2e/viet-kudo.spec.ts e2e/route-guard.spec.ts --reporter=list`: **63 passed, exit 0**
  (port 3000 was free before the run; ID-21/ID-22 upload tests and ID-23/24/55 reject tests all green)
- Throwaway evidence scripts: `<scratchpad>/verify-finding1-image-cap.mjs`,
  `<scratchpad>/verify-finding2-mime-sniff.mjs` (not committed — scratchpad only)

## Unresolved / worth a second look
- `errors.form` is set but **no component in the tree currently renders a form-level error**
  (`compose-form-helpers.tsx` merges it, nothing displays it) — pre-existing gap from before this
  pass (the `NO_SESSION`/generic-`unknown` paths already hit this same dead end), not introduced
  here, and `compose-form-helpers.tsx`/`compose-actions.tsx` are outside my owned files. Worth a
  follow-up ticket if a user-visible "too many images" message is wanted beyond the client-side
  picker's own 5-image hide-the-add-button UX (which already prevents reaching this path through
  the UI — only a bypassing client hits it).
- No unit-test runner exists in this repo (only `@playwright/test`, no vitest/jest). Adding one
  for two pure functions was outside a bounded 4-file scope; verified via the scratchpad scripts
  above instead, run against real fixture bytes.

**Status:** DONE
**Summary:** All three reviewer findings closed within the 4 owned files — image-cap check now field-specific in `validateCompose()`, image uploads now sniff real magic bytes instead of trusting `File.type`, and both trimmed files are under 200 lines. Typecheck/lint/build clean, and the 63-test compose gate (`viet-kudo.spec.ts` + `route-guard.spec.ts`) stayed green.
**Concerns/Blockers:** None blocking. One pre-existing gap noted above (form-level errors have no UI surface) — out of scope to fix under this task's file ownership.
