---
authored_by: rebuild-spec
---
# Edge Cases — F001_Auth

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Empty password submitted | Sign-in is rejected | "Password is required." |
| Wrong password submitted five times | Account is locked | "Account locked, try later." |
| Unknown email submitted | Sign-in is rejected | "Invalid email or password." |
