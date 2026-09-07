# Edge Cases — F001_Auth

| Scenario | What Happens | User-Facing Message |
|----------|--------------|---------------------|
| Registration with an email already taken in this marketplace | System aborts account creation and redirects back to the sign-up page | "That email address is already in use. Please use a different one." |
| Registration with an email domain not permitted by this marketplace | System aborts account creation and redirects back to the sign-up page | "That email address is not allowed for this marketplace." |
| Registration with honey-pot field filled (bot detected) | Controller logs an error and redirects back to sign-up; no records created | "Your registration appeared to be spam and was rejected." |
| reCAPTCHA validation fails on registration | System aborts before creating any records; redirects back to sign-up | "We could not verify that you are human. Please try again." |
| Login with incorrect password | Devise authentication fails; form re-rendered with error in place | "Wrong email address or password." |
| Login when community terms have been updated since last acceptance | User is temporarily signed out; redirected to Terms Accept screen | (Terms Accept screen shown — see F004_TermsConsent) |
| Login attempt by a banned member | Session established momentarily; `cannot_access_if_banned` guard fires on next request and redirects to Access Denied screen | "Your account has been suspended. Contact the marketplace admin if you think this is a mistake." |
| Login attempt by a member belonging to a different community (stale cross-community session) | `ensure_user_belongs_to_community` fires; user is automatically signed out | "You have been automatically logged out. Please sign in again." |
| Invalid or already-used invite code on invite-only community registration | Account creation aborted; redirect to sign-up page | "An unexpected error occurred. Please try again or contact support." |
| Password reset request for an unknown email address | System shows an error flash (no email sent) | "We could not find an account with that email address." |
| Logout while already banned or in pending-confirmation state | `destroy` action still completes (ban/confirmation guards skipped for logout) | "You have been logged out successfully." |
| Membership status is `deleted_user` at login | No explicit auth-flow handling confirmed in source; behavior unverified | Unknown — see Unresolved Questions in technical-spec.md |
