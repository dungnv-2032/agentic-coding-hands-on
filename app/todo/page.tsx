import { cookies } from "next/headers";

import { createClient } from "@/lib/supabase/server";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { LOCALE_COOKIE, resolveLocale } from "@/lib/i18n/locales";

import { signOut } from "@/app/_actions/auth";

/**
 * Minimal authenticated landing page (FR-403, US002, US004). `proxy.ts`
 * already guards this route — an unauthenticated request never reaches this
 * render — so this page trusts `getUser()` purely to display the signed-in
 * email, not to re-authorize (plan risk R3: one authority only).
 *
 * Deliberately unstyled: this page exists to prove the route guard and
 * sign-out flow, not to be a real to-do UI.
 */
export default async function TodoPage() {
  const [supabase, cookieStore] = await Promise.all([createClient(), cookies()]);
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const locale = resolveLocale(cookieStore.get(LOCALE_COOKIE)?.value);
  const dictionary = getDictionary(locale);

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-2xl font-bold">{dictionary.todo.title}</h1>
      {user?.email ? <p>{user.email}</p> : null}
      <form action={signOut}>
        {/*
          No aria-label override here on purpose. An English aria-label over
          localized visible text breaks WCAG 2.5.3 "Label in Name": someone
          using speech input says the words they can see ("Đăng xuất"), so the
          accessible name has to contain them. Tests locate this button by its
          localized name instead.
        */}
        <button
          type="submit"
          className="rounded bg-slate-800 px-4 py-2 text-white"
        >
          {dictionary.todo.signOut}
        </button>
      </form>
    </main>
  );
}
