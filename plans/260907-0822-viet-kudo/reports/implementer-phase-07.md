# Implementer report — Phase 07: write-path validation and actions

**Status:** DONE

## Files touched (create-only, none modified)
- `lib/kudos/validate-compose.ts` (87 lines) — `validateCompose`, `isAcceptedImageType`, `isOwnStorageUrl`.
- `lib/kudos/compose-options.ts` (47 lines) — `getComposeOptions()`.
- `app/kudos/new/_actions/create-kudos.ts` (118 lines) — `createKudos`.
- `app/kudos/new/_actions/upload-kudos-image.ts` (75 lines) — `uploadKudosImage`, `UploadKudosImageError`.

## Signatures for phase 11/12 to bind to
- `createKudos: (prevState: CreateKudosState, payload: ComposePayload) => Promise<CreateKudosState>` —
  matches `CreateKudos` (compose-contract.ts) exactly, no adapter needed.
- `uploadKudosImage: (file: File) => Promise<UploadResult>` — matches `UploadKudosImage` exactly.
  **On failure it rejects**, throwing `UploadKudosImageError` (exported), which carries
  `.code: ComposeFieldErrorCode` (`"unknown" | "invalidType"`). Track A must `try { await
  uploadKudosImage(file) } catch (e) { if (e instanceof UploadKudosImageError) ... }` to render
  `image-error`. This is a resolved divergence from Key Insight 9 ("never a throw") — the frozen
  `UploadKudosImage` type has no error-return slot, so a typed rejection is the only channel
  available that still satisfies the exact signature. Recorded here per the "settle the reading"
  rule rather than silently returning something outside the contract's shape.

## Divergences recorded
1. **Upload error channel** — above. `createKudos` needed no such divergence; its frozen
   `CreateKudosState` already carries an error union and matches the architecture pseudocode.
2. **`compose-options.ts` selects only `id, full_name, avatar_url`**, not `department:departments(name)`
   as the phase doc's architecture sketch shows — `ComposeSunnerOption` (frozen) has no department
   field, so selecting it would be dead data. YAGNI; the frozen type is the authority.
3. **`p_anonymous_name`** — generated `create_kudos` RPC Args type is `string` (not `string | null`);
   Postgres function-parameter nullability isn't reflected by the codegen even though the column and
   SQL param are nullable. A blank/absent name is sent as `""`, never `null`. Verified this is
   behaviorally identical on read: `board-data.ts:97` already does `anonymous_name?.trim() ||
   fallback`, treating `""` and `null` the same.

## Checks
- **Typecheck**: clean, exit 0 (`npm run typecheck`).
- **Lint**: 0 errors, `npm run lint` (29 pre-existing warnings, none in my files).
- **Unit tests**: none added — this repo has no unit-test runner anywhere (only `@playwright/test`;
  `derive.ts`/`rich-text.ts`/`compose-state.ts` carry no test files either), and `e2e/**` is
  tester-owned. Instead I ran the **actual production files** (not copies) via a throwaway Node
  ESM resolve-hook (`node --import ./loader.mjs`, appends `.ts` for extensionless relative
  specifiers Node's loader can't resolve but the project's bundler-mode tsconfig can) — 17
  assertions against `validateCompose`/`isAcceptedImageType`/`isOwnStorageUrl` plus 2 against
  `rich-text.ts`'s `parseKudosDoc`/`docToPlainText` round-trip. All pass.
- **Integration**: `probe-write-path.sh` (curl + psql, scratchpad dir) exercises the identical
  `create_kudos` RPC call shape `createKudos` sends, plus the Storage bucket. All pass:
  (a) valid create → id 63, 2 `kudos_hashtags` rows, `message_format='doc'`, 1 `sunners` row
  provisioned; double-submit → still 1 `sunners` row; (b) blank campaign/message/0-hashtags/nonexistent
  receiver → 400/409, row count unchanged; (c) 6 hashtags / 6 images → 400, count unchanged;
  (d) storage bucket accepted a `.pdf` upload (200) — proves the MIME gate lives in the TS action,
  not the bucket policy, matching `isAcceptedImageType("application/pdf") === false` proven above;
  (e) anonymous create stored `is_anonymous=true`, `anonymous_name` verbatim; (f) doc round-trips
  (separate script). Forged `sender_id` on a direct `POST /rest/v1/kudos` → 403/42501. Writing into
  another uid's Storage folder refused.
- **Row cleanup**: found the corpus already at **61** kudos (not 57) before I started — 4 leftover
  probe rows (`Probe Doc Render`/`Probe Anon Named`/`Probe Anon Unnamed`/`Probe Malformed Doc`,
  ids 59-62) from an earlier, apparently interrupted run of this same task. Deleted them first to
  restore the 57 baseline, then ran my own probes and deleted every row/sunner they created.
  Final state verified identical to phase 03's clean baseline: `kudos=57, kudos_hashtags=114,
  kudos_attachments=25, sunners=9/0-linked, departments=52, hashtags=13`. One orphaned `.pdf`
  Storage object remains from the (d) probe — accepted per plan.md Key Insight 10 (no DELETE
  policy exists on `storage.objects`; unreferenced objects are inert by design).
- **Board suite**: `npx playwright test e2e/kudos-live-board.spec.ts --reporter=list` — 25/25 passed.
- **`e2e/viet-kudo.spec.ts`**: not run by me (tester-owned per momorph rules); stays RED as expected —
  the form doesn't exist until phases 08-12.

## Acceptance criteria
- [x] `validateCompose({})` → all 4 codes at once, not the first only (proved above).
- [x] `grep -n "service_role" lib/ app/` → nothing.
- [x] No file > 200 lines; `create-kudos.ts` has exactly one `redirect`, last top-level statement.
- [x] Identity is session-derived only; no `sender_id`/actor parameter anywhere in either action.

## Unresolved
1. The upload-error-channel divergence above should be surfaced to phase 10/12's implementer
   explicitly, since it changes how the picker must call `uploadKudosImage` (try/catch, not a
   returned `{error}` field).
2. A prior, apparently incomplete run of this phase left 4 dirty probe rows in the live DB before I
   started — worth the orchestrator knowing in case that run's report exists elsewhere and should be
   superseded by this one.
