<!-- FORBIDDEN TOKENS — self-check passed: no FR/BR/SM/ALG/INT/SC/DISC/DEC/PERM/MODEL/BL codes, no HTTP codes, no GET/POST/DELETE/PATCH/PUT, no table.column refs -->

# Business Context — F005_MarketplaceCreation

## Why It Matters

Marketplace creation is the top-of-funnel moment for the entire platform. It is the single action that converts a prospect into a paying customer. Every feature in the system exists to serve marketplaces that were created through this flow. Making it fast, reliable, and self-service is a direct revenue driver.

## Who Uses It

- **Marketplace founders (prospective operators)** — Individuals or businesses who want to launch their own online marketplace. They fill in a short form and immediately receive a ready-to-configure marketplace with their admin account set up.
- **Platform (Marketplace)** — The platform automatically sets up a trial account, provisions payment gateway integrations, and enables key features so the new marketplace is usable from day one.

## What They Do

1. A prospective marketplace operator visits the new marketplace signup page and sees a form asking for the marketplace name, the type of marketplace (products, rentals, services, events, or free exchanges), the country, the language, and their own name, email address, and password.
2. They fill in the form and submit it.
3. The system checks that all fields are valid and that the submitted email is not already registered. It also verifies the submission is not from a bot using an invisible security check.
4. If the form is valid, the system creates the marketplace with a unique web address derived from the marketplace name. It sets up default categories, listing types, and payment gateway integrations automatically.
5. The operator's admin account is created and linked to the new marketplace as its first administrator.
6. A 31-day free trial is activated for the marketplace.
7. The operator is redirected immediately to their new marketplace's admin dashboard — they are signed in automatically without needing to log in separately. A confirmation email is sent to their registered address.
8. From the admin dashboard, the operator can customise their marketplace, configure payments, and invite their first members.

## Unresolved Questions

- **Trial extension**: It is not documented what happens when the 31-day trial expires. Does the marketplace become inaccessible, or does it downgrade to a limited free tier?
- **Subdomain assignment**: The marketplace subdomain is derived automatically from the marketplace name. It is unclear whether the operator can choose a different subdomain during signup or must change it after creation through the admin settings.
- **Bot protection behaviour**: The security check (reCAPTCHA) can be configured in three modes: block failures, log failures, or disabled. It is not documented which mode is used in production and whether operators are aware of this configuration.
