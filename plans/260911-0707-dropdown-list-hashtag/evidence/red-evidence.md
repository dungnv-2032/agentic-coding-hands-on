# RED evidence — Dropdown list hashtag

`temper-results.json` carries only green commands, by the validator's contract (any `status: fail`
entry blocks the ship gate). The intentionally-red run lives here.

**redCommand:** `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed -g "ID-17|ID-53|ID-57|ID-58|ID-59|ID-60"`
**redExitCode:** `1` · **result:** 5 failed, 2 passed (2.8m), before a line of UI code changed.

| Test | Failing assertion (verbatim) |
|------|------------------------------|
| ID-57 | `expect(locator).toHaveCount(expected) failed` — Expected `0`, Received `2`. Second click duplicated instead of deselecting. |
| ID-58 | `expect(locator).toBeVisible() failed` — `[data-testid="hashtag-check"]` did not exist. |
| ID-59 | `expect(locator).toBeDisabled() failed` — Expected disabled, Received enabled. |
| ID-17 | `expect(locator).toBeDisabled() failed` — Expected disabled, Received enabled. |
| ID-53 | `expect(locator).toBeDisabled() failed` — Received enabled; locator resolved to `<button role="option" aria-selected="false" … opacity-50>#Aim High</button>` — dimmed but still clickable. |
| ID-60 | PASS — regression guard against hoisting, never a RED expectation. |

Every failure is an assertion on the requested screen behavior. No dependency, config,
browser-install or dev-server failure — a valid RED.
