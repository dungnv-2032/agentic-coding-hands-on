# Prototype Quality Gate

Run before finalizing (Stage 3). Report each as **pass / issue** with severity:
**Blocking** (fix + rebuild before delivery) / **High** / **Medium** / **Low**.

## 1. Grounding trace (the "grounded" in grounded prototyping)
- [ ] Every screen has `grounding` with at least one source reference (iaScreen / personas / stories / reqs) — a screen with none is **Blocking** unless no upstream input existed at all.
- [ ] Every entry in `requirements` is covered by ≥1 screen's `grounding.reqs` — an uncovered **Must-level** requirement is **Blocking**; others High.
- [ ] `screens[].id` matches the ia-spec screen id where an IA input exists.
- [ ] Mock data traces to inputs (`mock.source` filled); no invented entities, no 「項目1」placeholders.
- [ ] UI copy uses persona `vocabulary` / ia-spec `labels` — no internal jargon the inputs warned against.
- [ ] Content order per screen follows persona `infoOrder` / ia-spec `infoPriority`.
- [ ] Everything NOT traceable is listed in `meta.assumptions` or `grounding.assumptions` — silent invention is **Blocking**.
- [ ] Input conflicts (IA says X, document says Y) were surfaced to the user, not silently resolved.

## 2. App-type idioms (`meta.appType`, per ui-craft §0)
- [ ] mobile-app: no web header/footer; global nav = bottom tab bar (if multi-section); back affordance top-left; checked in the native frame (Mobile/Tablet).
- [ ] web-app: consistent global header on every screen; footer where expected; desktop layout uses the width (checked in the browser frame incl. Desktop).
- [ ] No idiom mixing (web header in a mobile-app / tab bar on web desktop) unless the design direction says so.
- [ ] both: components branch via `useAppMode()` — check the same screen in Web and アプリ toggles (header/tab-bar/back affordance switch correctly).

## 3. UX heuristics (Nielsen-derived, checked concretely)
- [ ] **Status visibility:** loading states exist where data loads; async actions show a result.
- [ ] **User language:** labels match the persona's words (see grounding checks above).
- [ ] **Control & undo:** destructive/committing actions have a back-out (cancel, confirm step, or recover screen).
- [ ] **Consistency:** the same action looks the same on every screen (one primary-button style, one card style).
- [ ] **Error prevention & recovery:** forms show constraints before errors; error states say what happened + a next step.
- [ ] **Recognition over recall:** context (breadcrumb, title, selected item) is visible — the user never must remember the previous screen.
- [ ] **Hierarchy:** each screen has one obvious primary action (matching `primaryAction`); secondary actions visually secondary.
- [ ] **Minimalism:** nothing on a screen that its role + grounding don't justify.

## 4. States
- [ ] Every data-driven screen implements `empty` / `loading` / `error` (declared in `states` and present via `data-when`).
- [ ] Journey pain points from the um-spec map to a visible state or recovery UI.
- [ ] Each declared state is visually complete (empty state isn't just a hidden list).

## 5. Prototype mechanics & build
- [ ] `npx tsc --noEmit` and `npm run build` pass — a red build is **Blocking**.
- [ ] Every `useGoto()` target exists in the screen registry; every transition in `transitions` is reachable by clicking.
- [ ] The main flow walks end-to-end with no dead ends; every screen is reachable; back/return paths exist where implied.
- [ ] `pt-spec.json` matches the code: registry ids = spec ids; declared `states` are all implemented; `patterns.usedIn` matches reality.
- [ ] Micro-interactions respond: every selection/tab/toggle/input a reviewer would try actually changes state (contract §8) — a dead control is High.
- [ ] Screens use `min-h-full` roots (grep for `min-h-screen`/`h-dvh` in `src/screens` — any hit is High); bottom action bars (`sticky bottom-0`) pin correctly inside the review device frames.

## 6. Responsive (when `meta.device` is responsive)
- [ ] Layouts adapt at container breakpoints — check each screen in the Mobile / Tablet / Desktop frames (review shell) for overflow, cramped grids, or wasted width.
- [ ] Breakpoints use container-query variants (`@3xl:`…), never viewport variants (`sm:` `md:` — grep; any hit is High).
- [ ] Wide layouts constrain line length / content width (no 1280px-wide form fields).

## 7. Design-system fidelity
- [ ] Screens/components style ONLY via token utilities — grep `src/screens src/components` for raw hex (`#`), `bg-[#`, `text-[#`, hardcoded font families; any hit is High (exceptions: review shell, globals.css, SVG scene-illustration components like photo.tsx — imagery palettes are content, not UI).
- [ ] Tokens match the design-direction source (`design.source` filled; deviations flagged as assumptions) and `globals.css :root` mirrors `design` exactly.
- [ ] `design.notes` component rules are actually followed in the screens.
- [ ] `patterns.tsx` catalog covers every recurring pattern — a pattern repeated across ≥2 screens without a shared component + catalog entry is Medium. Global chrome (header/tab bar) is cataloged as organisms; `tier` reflects the Atomic Design level.
- [ ] Each pattern's `usage` states a rule (when to use), not just a description.

## 8. Accessibility basics
- [ ] Text contrast ≥ 4.5:1 against its background (check text/textSub/primaryText token pairs — compute, don't eyeball).
- [ ] Interactive targets ≥ 44×44px on mobile frames.
- [ ] Meaningful images/icons have text alternatives or adjacent labels; color is never the only signal (e.g. error states also say "エラー").
- [ ] Font sizes ≥ 11px; body ≥ 13px.

## 9. UI craft (per `references/ui-craft.md`)
- [ ] Squint test per screen: exactly ONE visual peak, and it is the primary action/answer.
- [ ] Spacing on the 4/8px grid; groups separated by whitespace (≥16px), not clutter or divider overuse.
- [ ] Body line-height 1.6+ set explicitly; amounts/counts use tabular-nums and right-align in rows.
- [ ] Clickable elements look clickable without hover; non-clickable elements never mimic buttons.
- [ ] `loading` is a skeleton mirroring the layout (not a text line); `empty`/`error` follow the 3-part pattern (what / why-no-blame / next action).
- [ ] `--c-primary` appears only on actions & selected states; status colors always pair with a text label.
- [ ] Form inputs ≥15px font, labels above, constraints before errors; destructive actions outlined, never filled.

## 10. Scope & honesty
- [ ] MVP scope (Must screens / main flow) is complete; out-of-scope screens are absent, not half-built.
- [ ] The report separates grounded findings from assumptions (前提・仮定 section present).
- [ ] Did NOT drift into IA restructuring or user-model changes — discovered issues are reported as suggestions upstream.

## Report format
```markdown
## Quality Gate レポート
✓ 全N画面が根拠（IA/ペルソナ/要件）に遡れる
⚠ [High] 要件「CSV出力」を満たす画面なし
✓ 主操作が各画面1つ・ペルソナ語彙を使用
⚠ [Blocking→修正済] expense-list: empty状態が未実装 → 実装しリビルド
✓ コントラスト比 最小 4.6:1（text/bg）
```
Blocking issues: fix, rebuild, re-run the gate, and note them as 修正済 in the final report.
