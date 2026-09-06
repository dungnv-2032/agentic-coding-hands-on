# React key warning on `/kudos` — root cause

Evidence via real Chromium (Playwright, deps side-loaded from downloaded .deb
files, no root available), CDP `Runtime.consoleAPICalled` for the unminified
stack, and a live React fiber-tree walk in the page.

## 1. Verbatim warning, stack, overlay

Console (type `error`), reproduced fresh on two independent dev instances:
`Each child in a list should have a unique "key" prop.%s%s ... Check the
top-level render call using <KudosBoard>.` (3rd arg — component-stack — is
`""`). Stack: `warnForMissingKey`←`warnOnInvalidKey`←`reconcileChildrenArray`
←`reconcileChildFibersImpl`←`updateFunctionComponent`←`beginWork` — first
paint of a cold load, not a later update.

Dev-overlay: opened its shadow DOM directly — button `aria-label="Open issues
overlay"` reads **"01 Issue"**, next to `aria-label="Open KudosPage in
editor"`. `page.on('console')` on that load recorded exactly **one**
`error`. Badge (1) === error count (1): same issue, confirmed, not something
additional.

## 2. Root cause — `app/kudos/_components/kudos-board.tsx:118-173`

Not a `.map()` (re-grepped fresh, all still keyed). It's the Fragment
`KudosBoard` returns: `<>{section}{spotlightSlot}<AllKudosSection/>
<KudosToast/></>`. Live fiber walk (`__reactFiber$*`, from the KudosBoard
fiber) proves it — its own rendered output is 4 sibling fibers, **all four
`key: null`**: `section`, `SpotlightBoard`, `AllKudosSection`, `KudosToast`.
Owner = KudosBoard because these are created in its own function body —
matches "top-level render call using `<KudosBoard>`" verbatim. This 4-child
Fragment was introduced by the layout-fix task's `spotlightSlot`/
`sidebarSlot` refactor (previously 2 children) — after the earlier grep, not
before, which is why it was missed.

Ruled out: **duplicate key** (different message wording; fiber shows `null`,
not a repeat) · **Fast-Refresh/HMR artifact** (HMR independently broken here
— cross-origin block + WS handshake failures — yet warning reproduces on a
cold process's very first load, before any edit/HMR, on 2 separate servers)
· **framework/`node_modules` origin** (fiber walk points at this repo's own
`kudos-board.tsx` return).

## 3. Fix (not applied — file in scope for the layout-fix agent)

Give the 4 top-level children stable literal keys: `key="highlight"` on the
`<section>`, wrap `{spotlightSlot}` in `<Fragment key="spotlight">`,
`key="all-kudos"` on `<AllKudosSection>`, `key="toast"` on `<KudosToast>`.
Fixed count/order, never reordered — no behavior change, warning gone.
`sunner-chip.tsx`/`kudos-card.tsx`/`kudos-attachments.tsx` (other agent's
files) re-read fresh, clean — not implicated.

## 4. Production impact — dev-only, tested not assumed

`npm run build` (clean) → `npm run start` :3001 → full console capture on
`/kudos`: **zero** console.error/warn, only benign RSC prefetch-abort
`requestfailed` noise. React strips dev key-validation from prod builds.
Condition is real in prod code too but the 4 elements are static, so no
runtime effect — dev-only console/CI-signal noise, not a live user defect.
Low priority, worth fixing before it masks a real one.

**Status:** DONE
**Summary:** Overlay "1 Issue" = this warning (confirmed: exactly 1 error
present). Root cause proven via live fiber walk: `KudosBoard`'s own
top-level Fragment return (introduced by the `spotlightSlot`/`sidebarSlot`
refactor) has no `key` on any of its 4 children. Fix: 4 literal keys.
Confirmed dev-only via real prod build+start (zero console output).
**Concerns/Blockers:** None blocking. Unresolved: why React's usual
static-children exemption doesn't suppress this for a bare top-level Fragment
(vs. `<section>`'s own un-keyed 2 children, which don't warn). Port 3000 was
contended by a concurrent dev-server process this session (Turbopack also
locks one dev instance per project dir); routed around it with 3+ server
instances — warning reproduced identically on every cold load.
