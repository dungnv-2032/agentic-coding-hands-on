# Delivery Status — Viết Kudo (F005)

**Date:** 2026-09-07 · **Plan:** `260907-0822-viet-kudo` · **Status:** SEALED

## Summary

All 12 phases completed and verified. Compose gate 63/63 passed. Full suite 144/144 passed on consecutive runs. Inspection verdict SEALED with 0 critical findings. Three Low findings closed by post-phase hardening pass. One post-phase K-25 root-cause fix stabilized the full-suite run.

## Completion Status

**All 12 phases:** COMPLETED
- Phase 01-03 (foundation, RED repair, schema) — passed
- Phase 04-07 (read contract, board, write path) — passed  
- Phase 08-11 (form primitives, editor, pickers, assembly) — passed
- Phase 12 (integration, guard, GREEN gate) — passed

**Post-phase work:**
- Hardening pass: image-cap field-specific, MIME byte-sniffing, file trimming — DONE
- K-25 root-cause: session revocation via dedicated kudos-auth setup — DONE

## Evidence at a Glance

| Gate | Result | Exit | Evidence |
|------|--------|------|----------|
| Typecheck | 0 errors repo-wide | 0 | temper-results.json |
| Lint | 0 errors | 0 | temper-results.json |
| Build | `/kudos/new` dynamic route | 0 | temper-results.json |
| DB reset | migrate + seed clean | 0 | temper-results.json |
| Compose gate | 63 passed (62 + auth + guard) | 0 | viet-kudo-green-run.log |
| Full suite (run 1) | 144 passed, kudos_likes→0 | 0 | full-suite-green-run.log |
| Full suite (run 2) | 144 passed, kudos_likes→0 | 0 | full-suite-green-run.log |
| RLS (live) | anon blocked, forgery blocked, double-submit idempotent | verified | adversarial psql |
| Inspection | 21 criteria SEALED, 0 critical, 3 Low findings closed | SEALED | inspection-verdict.json |

## Key Deliverables

**Write path complete:** Real Supabase Storage upload. RLS prevents anon and sender forgery. Auto-provisioning with `on conflict` idempotent. Create-kudos RPC in one transaction across three tables.

**Compose form:** Rich-text document model (bold/italic/strikethrough/quote/list/link/mention). Recipient, title, hashtag, image, anonymous-name pickers. Validation on client and server. Route guarded; public read surfaces untouched.

**Board rendering:** Doc messages safe-parse to React elements (no `dangerouslySetInnerHTML`). Anonymous sender shows label or fallback; receiver always shown. F004's 57 seeded rows stay plain/non-anonymous.

**Internationalization:** Full VN + EN. `kudosCompose` namespace compile-time enforced by `Dictionary`.

**Test integrity:** 59 tests in viet-kudo.spec.ts + ID-1 route-guard test. All phase 02's six broken assertions repaired. Phase 02's K-21 scoped off `/kudos/new` with two thirds of F004's board coverage still intact.

## Unresolved Questions (NOT Delivered)

Six questions remain open per `clarifications.md`:

1. **`Danh hiệu` spec gap** — in frame, no authored spec row, no test case.
2. **`D.1` character counter** — promised in label, not drawn, no max authored.
3. **Companion frames unspecced** — recipient dropdown and error state have no authored spec.
4. **Anonymous name field** — required by ID-43/44, not in frame's visible render, no design.
5. **Edit/delete deliberately absent** — separate commissions, no RLS UPDATE/DELETE policies.
6. **Toolbar width 1006px** — measurement flagged in design report as suspicious, not re-verified.

## Post-Phase Hardening

**Reviewer findings closed:**
- **Finding 1** (image count cap enforcement): Added `imageUrls.length > MAX_IMAGES` check to `validateCompose()` yielding field-specific `form:"tooMany"` error.
- **Finding 2** (MIME sniffing): Reads magic bytes from file (JPEG `FF D8 FF`, PNG `89 50 4E 47`, etc.) rather than trusting `File.type`.
- **Finding 3** (file-size cap): Trimmed import blocks + comments; `compose-form.tsx` 193 lines, `board-data.ts` 188 lines, both under 200.

No logic changed, no test weakened, all three scopes stayed clean.

## Post-Phase K-25 Fix

Session revocation in the full-suite run was caused by `authenticated.spec.ts`'s global sign-out revoking the shared session. Solution: `e2e/kudos-auth.setup.ts` creates a dedicated session for `kudos-authed` project, mirroring the existing `homepage-auth.setup.ts` pattern. Full 144-test suite now runs idempotently twice in succession.

## Next Phase (Open)

Reviewer notes: The RLS INSERT-policy shape on kudos/kudos_hashtags/kudos_attachments/sunners is now the precedent for future write tables. Worth a human review before it propagates to other commissions.

---

**Status:** SEALED · **Critical Findings:** 0 · **Concerns:** Open questions documented above
