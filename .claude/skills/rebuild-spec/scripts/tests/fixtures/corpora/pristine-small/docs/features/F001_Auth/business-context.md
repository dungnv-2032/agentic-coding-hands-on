<!-- FORBIDDEN TOKENS — self-check passed: no FR/BR/SM/ALG/INT/SC/DISC/DEC/PERM/MODEL/BL codes, no HTTP codes, no GET/POST/DELETE/PATCH/PUT, no table.column refs -->

# Business Context — F001_Auth

## Why It Matters

Authentication is the gateway to every marketplace activity: buying, selling, messaging, and administering. Without a working login and registration system, no member can participate in the marketplace, and marketplace operators cannot trust that their community is secure.

## Who Uses It

- **Visitors (not yet registered)** — Sign up for the first time to join the marketplace as a member. They need a simple form to create an account and receive a confirmation email.
- **Registered members** — Log in to access their account, manage listings, and communicate with other members. They also need a way to recover their password if forgotten.
- **Banned members** — Encounter an access-denied screen explaining they cannot use the marketplace.
- **Marketplace admins** — Log in with the same flow but receive additional prompts to visit the admin area after signing in.

## What They Do

1. A visitor opens the login or registration page and fills in their details (name, email, password). If the marketplace requires an invitation, they also enter an invite code.
2. The system checks that the email is not already taken in this marketplace and, if the marketplace restricts sign-ups to certain email domains, that the email address is permitted.
3. After submitting, the new member receives a confirmation email with a link. Until they click that link, they cannot access protected marketplace content.
4. Once the confirmation link is clicked, the account is activated and the member is welcomed into the marketplace.
5. An existing member enters their email and password to log in. If the marketplace's terms of service have been updated since the member last accepted them, they are asked to review and accept the new terms before continuing.
6. A member who has forgotten their password submits their email address and receives a password reset link. They click the link, set a new password, and regain access.
7. When a member is done, they click the logout link in the navigation bar. Their session is ended immediately.
8. A member whose account has been banned is shown an access-denied page explaining that they cannot use the marketplace.

## Unresolved Questions

- **Password reset email disclosure**: The system currently shows a different message depending on whether the submitted email address exists. This reveals which emails are registered. Is this intentional or should it be changed to always show a neutral "if your email is registered, you will receive a link" message?
- **Terms consent at login**: When marketplace terms are updated, a member logging in is temporarily signed out and redirected to accept the new terms. Is this the intended UX, or should terms acceptance happen inline without signing the user out first?
