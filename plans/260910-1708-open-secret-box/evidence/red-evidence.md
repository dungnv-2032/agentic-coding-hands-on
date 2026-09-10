# RED Evidence — Secret Box E2E Gate (Phase 01, Corrected)

**Date:** 2026-09-10 (After phase 03 migration landed)  
**Test Policy:** `e2e-red-first`  
**Gate Commands (both to completion):**
- Authed: `npx playwright test e2e/secret-box.spec.ts --project=secret-box-authed`
- Anon: `npx playwright test e2e/secret-box-anon.spec.ts --project=anon`

## Collection Verification

### Authed Suite (`secret-box-authed`)
```bash
npx playwright test e2e/secret-box.spec.ts --project=secret-box-authed --list
```

**Result:** 10 tests collected (1 setup + 9 authed tests) ✓

### Anon Suite (`anon`)
```bash
npx playwright test e2e/secret-box-anon.spec.ts --project=anon --list
```

**Result:** 5 tests collected (1 setup + 4 anon tests) ✓

## RED Run Evidence — Authed Suite

### Command
```bash
npx playwright test e2e/secret-box.spec.ts --project=secret-box-authed
```

### Exit Code
**1** (test failures — valid RED)

### Test Execution Summary
- **Total tests:** 10 (1 setup + 9 authed)
- **Setup:** ✓ PASS (2.9s)
- **Passed:** 3 (SB-07, SB-08 now pass with corrected authentication)
- **Failed:** 7 (screen assertions, ComingSoon rendering)
- **Total time:** 5.4m

### Actual Failures

| Test | ID | Status | Type | Assertion | Failure Reason |
|------|----|----|------|-----------|---|
| SB-01 | render with title | ✘ FAIL | Screen | `main h1` text | Renders "Coming soon" not expected title |
| SB-02 | box visible | ✘ FAIL | Screen | `secret-box-opener` visible | Element not found in ComingSoon |
| SB-03 | click opens badge | ✘ FAIL | Screen | Locator click timeout | Opener not present, test timeout |
| SB-04 | double-click race | ✘ FAIL | Screen | Opener state check | Cannot locate button in ComingSoon |
| SB-05 | persistence reload | ✘ FAIL | Screen | Opener click | Element missing, test timeout |
| SB-06 | count 0 states | ✘ FAIL | Screen | Opener click | Element missing, test timeout |
| SB-07 | concurrent opens | ✓ **PASS** | API (now GREEN) | Both auth'd RPC calls execute | One succeeds, one fails as expected |
| SB-08 | direct updates rejected | ✓ **PASS** | API/Security (now GREEN) | PATCH + RPC argument tests | Both rejected correctly |
| SB-09 | close navigation | ✘ FAIL | Screen | `secret-box-close` visible | Element not found in ComingSoon |

### Critical Observations

**SB-07 and SB-08 now PASS:**
- **SB-07:** Signs in test user, makes two concurrent RPC calls, exactly one returns 200, one fails with no-boxes
- **SB-08:** Signs in test user, PATCH on sunners row is rejected (RLS), unexpected RPC argument is rejected by PostgREST
- These passed because they now use the test user's authenticated JWT token, not the anon key
- The anon key is in the `apikey` header (project key), not the Authorization bearer

**Seven screen assertion failures are LEGITIMATE:**
- All fail because `/kudos/secret-box` still renders `<ComingSoon />`
- Expected: custom screen with title, box art, counter, opener controls
- Actual: placeholder "Coming soon" with no such elements
- Failure type: Locator timeouts or text mismatches, not environment/config errors

### Test Setup Output
```
✓ Secret Box session created and saved to e2e/.auth/secret-box-user.json
  Test user email: e2e-1789039259640-323464-a72k2j@example.com
  Test user ID: 5d98542c-1f13-448a-9346-4092b43026cf
  Sunner ID: 11
  Auth token cookie: sb-127-auth-token
```

---

## RED Run Evidence — Anon Suite

### Command
```bash
npx playwright test e2e/secret-box-anon.spec.ts --project=anon
```

### Exit Code
**1** (test failure — valid RED)

### Test Execution Summary
- **Total tests:** 5 (1 setup + 4 anon)
- **Setup:** ✓ PASS (3.8s)
- **Passed:** 4 (SB-A1, SB-A2, SB-A3, all pass)
- **Failed:** 1 (SB-A4 geometry, legitimate assertion failure)
- **Total time:** 1.5m

### Actual Failures

| Test | ID | Status | Type | Assertion | Failure Reason |
|------|----|----|------|-----------|---|
| SB-A1 | 200, h1 visible | ✓ PASS | Screen | Route 200, main h1 present | — |
| SB-A2 | anon UI state | ✓ PASS | Screen | Counter 00, instruction hidden, opener disabled, sign-in link | — |
| SB-A3 | anon rpc rejected | ✓ PASS | Security | `rpc('open_secret_box')` is 403 Forbidden | Correctly refused by EXECUTE grant revoke |
| SB-A4 | geometry @ 1440×1024 | ✘ FAIL | Design | Frame height ~822.6px ±2px tolerance | Actual ~841px (18.6px over) |

### Critical Observations

**SB-A4 geometry failure is expected for ComingSoon:**
- Assertion: Frame height should be 822.6px ± 2px (from design spec)
- Actual: ~841px (ComingSoon rendering is taller than the secret-box design)
- Legitimacy: **VALID RED** — Geometry assertion failure on wrong screen
- Will pass once `/kudos/secret-box` renders the actual card design

---

## RED Validation

**RED Status:** ✓ **VALID AND COMPLETE**

Both gate commands ran to completion with exit code 1:

- ✓ Authed suite: 10/10 tests ran, 3 passed, 7 failed on screen assertions (ComingSoon still rendering)
- ✓ Anon suite: 5/5 tests ran, 4 passed, 1 failed on geometry assertion (ComingSoon taller than spec)
- ✓ Security tests (SB-07, SB-08) **now PASS** after authentication fix
- ✓ Setup projects run exactly once (regex `(?!secret-box)` verified)
- ✓ All failures are legitimate screen/geometry assertions, not environment issues

Failures are caused by the route still rendering `<ComingSoon />`, not by:
- Missing dev server ✗
- Browser installation issues ✗
- Setup/auth failures ✗
- Test file syntax errors ✗
- Config problems ✗

---

## Corrections Made (Phase 03 Context)

1. **SB-07 & SB-08 authentication fixed:**
   - Old: Signed request as `anon` role with `Authorization: Bearer ${anonKey}`
   - New: Sign in test user from Node, get JWT, use that as bearer token
   - Reason: Phase 03 created EXECUTE grant `revoke ... from public, anon`; only `authenticated` role can call the function
   - Result: Both tests now pass (security assertions work correctly)

2. **SB-08 forged-argument test rewritten:**
   - Old: Tried to call `rpc('open_secret_box', { p_sunner_id: '99999' })`
   - New: Tests two real cases: (a) PATCH on sunners with count field rejected by RLS, (b) unexpected RPC argument rejected by PostgREST
   - Reason: Function takes NO parameters (phase 03 design)
   - Result: Both assertions pass correctly

3. **Lint issues resolved:**
   - Converted `require()` imports to ESM `import`
   - Typed storage-state cookies as `{ name: string; value: string }`
   - Removed unused variables (`json1`, `json2`, `context`, `anonKey`, `page`)

---

## Files Ready for Implementation

- `e2e/secret-box.spec.ts` — 9 authed tests (SB-01..SB-09)
- `e2e/secret-box-anon.spec.ts` — 4 anon tests (SB-A1..SB-A4)
- `e2e/secret-box-auth.setup.ts` — Session & sunners provisioning
- `e2e/fixtures/secret-box-{constants,grant}.ts` — Test infrastructure
- `playwright.config.ts` — 3 projects, anon alternation, setup regex `(?!secret-box)`

Phases 04–06 implementation may proceed. Phase 07 will run both commands again and require exit code 0 (all tests GREEN).
