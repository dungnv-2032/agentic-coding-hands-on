This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000) with your browser to see the result — **not**
`localhost:3000`: the Supabase session cookie is pinned to `127.0.0.1`, and browsers treat the two
hosts as different origins, so opening `localhost` looks logged-out even after a successful login. See
`docs/setup/local-development.md` § 4 for why.

`app/page.tsx` is the public SAA 2025 homepage (`/`), not the original `create-next-app` starter page —
see the "Homepage" section below. `app/login/page.tsx` is the Google OAuth login screen.

## Login (Google OAuth via local Supabase)

The `/login` screen needs the local Supabase stack plus real Google OAuth credentials before it works —
see `docs/setup/local-development.md` for the full setup (env files, why everything must be opened at
`127.0.0.1` and not `localhost`, running `npm run test:e2e`, and the WSL2 headless-Chromium workaround).
Feature behavior is specified in `docs/features/F001_Login/`; non-obvious implementation traps in
`proxy.ts` and `app/auth/callback/route.ts` are written up in
`docs/troubleshooting/login-oauth-gotchas.md`.

## Homepage (SAA 2025 landing page)

`/` is the public SAA 2025 homepage — header, hero with an event countdown, awards grid, Sun\* Kudos
promo, and (when signed in) a notification bell and account menu. It shares its header/language
selector and sign-out action with `/login` (`app/_components/`, `app/_actions/`). Four placeholder
routes (`/kudos`, `/standards`, `/profile`, `/admin`) exist only so every link resolves — none has
real destination content yet. Feature behavior is specified in `docs/features/F002_HomepageSaa/`;
the countdown reads `NEXT_PUBLIC_EVENT_START_AT` (see `docs/setup/local-development.md` § 2).

## Award System (`/awards-information`)

`/awards-information` is the public "Hệ thống giải" screen — hero, a sticky six-item category menu
with scroll-spy, six award detail cards (description, quantity, prize value), the shared Sun\* Kudos
promo and footer. It is a public route with no auth guard, and it replaced the `ComingSoon`
placeholder that used to sit there. The six homepage award cards deep-link into it as
`/awards-information#<slug>`. Feature behavior is specified in `docs/features/F003_AwardSystem/`;
screen detail in `docs/screens/SCR003_AwardSystem/spec.md`.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
