---
authored_by: rebuild-spec
---
# Business Context — F001_Auth

## Why It Matters

Customers cannot access their saved orders without proving who they are.

## Who Uses It

- **Shop Manager** — signs in to review daily orders
- **Guest Shopper** — signs in to reach a previously saved cart

## What They Do

1. User submits an email and password.
2. System locks the account after five failed attempts. [NEEDS_DOMAIN_CONFIRMATION] lock duration
3. User is redirected to the dashboard on success.

## Unresolved Questions

None.
