# Edge Cases — F005_MarketplaceCreation

| Scenario | What Happens | User-Facing Message |
|----------|--------------|---------------------|
| reCAPTCHA verification fails in enforce mode | Creation blocked immediately; no records created | "reCAPTCHA validation failed. Please try again." |
| reCAPTCHA verification fails in log mode | Failure logged silently; creation proceeds as normal | None — transparent to the user |
| Required form field missing (e.g. no marketplace name) | Form validation fails; no records created; errors returned | Form error listing each missing or invalid field |
| Invalid marketplace type submitted (not in allowed list) | Form validation fails; no records created | Form error: "Marketplace type is not included in the list" |
| Admin email address already registered in the new community | `UserService.create_user` raises an error; creation fails | Error response — exact message not confirmed; see Unresolved Questions in technical-spec.md |
| Marketplace name produces a subdomain already taken | System automatically appends a numeric suffix and uses the next available subdomain | None — operator is not informed of the change during signup |
| Marketplace name produces a reserved platform subdomain (e.g. "www") | Same suffix logic applies; creation proceeds with an incremented subdomain | None — transparent to the user |
| Legacy HTML signup path accessed when communities already exist | `ensure_no_communities` guard redirects to landing page | None — silent redirect |
| Payment gateway provisioning fails after community is created | Community and admin account exist but payment settings may be absent; no rollback observed | None — partial creation state; unhandled (TODO in source) |
| Feature flag service call fails after community and user created | Community operational but topbar_v1 / stripe_connect_onboarding features not enabled | None — silent failure; features can be enabled later via admin |
| Auth token URL used after token expires | Admin is not signed in automatically; redirected to login page | Standard login page — no specific error message |
