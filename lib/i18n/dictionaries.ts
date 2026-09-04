import type { Locale } from "./locales";
import { en } from "./messages/en";
import { vi, type Dictionary } from "./messages/vi";

export type { Dictionary };

/**
 * Static map, not dynamic import — two small message modules don't justify
 * lazy-loading (YAGNI). Server-only by convention (deliberately not enforced
 * via the `server-only` npm package, which isn't a project dependency and is
 * outside this task's file ownership to add): a Server Component reads the
 * dictionary and passes plain resolved strings down to Client Components,
 * never this module itself.
 */
const dictionaries: Record<Locale, Dictionary> = { vi, en };

export function getDictionary(locale: Locale): Dictionary {
  return dictionaries[locale];
}
