# pt-spec.json + screen contract — the v2 interchange format

v2 splits responsibilities: **`pt-spec.json` carries the grounding** (sources, tokens, requirements,
screen metadata, transitions) and **screens live as code** in `src/screens/*.tsx`. The review shell
imports the spec at build time (`src/pt/spec.ts`), so spec edits hot-reload like code.

## pt-spec.json (project root)

```jsonc
{
  "meta": {
    "product": "string",
    "users": "string",
    "primaryGoal": "string",
    "device": "responsive | mobile | tablet | desktop",   // responsive is the default
    "appType": "mobile-app | web-app | both", // デザインイディオムの分岐。mobile-app=ネイティブ表示
                                              // （ステータスバー＋ホームインジケータ・URLバーなし・
                                              //  Desktopプレビューなし）/ web-app=ブラウザ表示（既定）/
                                              // both=レビューに Web⇄アプリ 切替が出る（?app=1で
                                              // アプリ表示から開始）。画面側は useAppMode() で分岐
    "stage": "idea | MVP | redesign | production",
    "sources": [                              // EVERY input gets an entry — grounding cites these ids
      { "id": "src-ia", "type": "ia-spec", "path": "…/ia-spec.json", "note": "画面構成・遷移・要件" }
      // type: ia-spec | um-spec | doc | html | design-guide | instruction | other
    ],
    "assumptions": ["string — anything not traceable to a source"]
  },
  "design": {                                 // normalized direction — mirror into globals.css :root
    "direction": "信頼感のあるミニマル",
    "source": "どこから来た決定か（src-id / 提案=仮定）",
    "notes": ["コンポーネント規則（例: 主ボタンは1画面1つ）"],
    "colors": { "primary": "#0F6FDE", "primaryText": "#FFFFFF", "bg": "…", "surface": "…",
                "text": "…", "textSub": "…", "border": "…", "success": "…", "warning": "…",
                "danger": "…", "accent": "…" },
    "typography": { "family": "Noto Sans JP", "baseSize": "14px",
                    "scale": { "xl": "22px", "lg": "17px", "md": "14px", "sm": "12px", "xs": "11px" } },
    "shape": { "radius": "10px", "density": "comfortable | compact", "shadow": "…" }
  },
  "requirements": ["機能要件の文言（ia-spec prd.functionalReqs から転記）"],   // coverage matrix joins on exact text
  "screens": [
    {
      "id": "expense-list",                   // REUSE the ia-spec screen id — the traceability join key
      "name": "経費一覧",
      "role": "manage",                       // inform|decide|input|compare|manage|confirm|recover|complete
      "primaryAction": "経費を申請する",
      "device": "mobile",                     // OPTIONAL override of meta.device
      "states": ["default", "empty", "loading", "error"],  // implemented states only (journey由来のカスタム状態も可)
      "grounding": {
        "iaScreen": "expense-list",
        "personas": ["田中（申請者）"],
        "stories": ["申請者として、立替をすぐ申請したい"],
        "reqs": ["経費の一覧・状態確認"],      // must match requirements[] verbatim
        "assumptions": ["並び順は新しい順と仮定"]
      },
      "mock": { "source": "どの入力からモック値を採ったか", "notes": "" }
    }
  ],
  "transitions": [
    { "from": "expense-list", "to": "expense-form", "condition": "＋申請", "kind": "main", "flow": "申請フロー" }
  ]
}
```

### Rules
- `meta`, `design`, `screens` are required. `requirements` + `grounding` are what make it *grounded* — omit only when the input truly doesn't exist.
- `grounding.reqs` must match `requirements` strings **verbatim**.
- Keep the spec in sync with the code — the review shell renders it live, so drift shows immediately.

## Token mapping (design → `src/styles/globals.css` `:root`)
Edit ONLY the `:root` block; the `@theme inline` mapping stays untouched.

| design | CSS var (shadcn convention) |
|---|---|
| colors.bg / text | `--background` / `--foreground` |
| colors.surface | `--card` (+ `--card-foreground`) |
| colors.primary / primaryText | `--primary` / `--primary-foreground` (+ `--ring`) |
| colors.textSub | `--muted-foreground`（`--muted`/`--secondary` は bg と surface の間の淡色に） |
| colors.accent | `--accent`（ウォッシュ用途） |
| colors.danger | `--destructive` |
| colors.success / warning | `--success` / `--warning` |
| colors.border | `--border` / `--input` |
| shape.radius | `--radius` |
| typography.family | `--font-jp` |

Screens then use **token utilities**: `bg-primary text-primary-foreground`, `text-muted-foreground`,
`border-border`, `rounded-lg`(=radius), `bg-accent`… — never raw hex in screens/components.

## Screen contract (src/screens/*.tsx)
1. **One file per screen**, kebab-case = screen id. Default export:
   ```tsx
   export default function ExpenseList({ state }: ScreenProps) { … }
   ```
   Register in `src/screens/index.ts` (`screens: Record<id, Component>`); ids match `pt-spec.json`.
   **Layout root** = `flex min-h-full flex-col` — **never** `min-h-screen`/`h-dvh` (the canvas owns the
   viewport: pure mode = `h-dvh` scroll container, review device frames = fixed-height `@container`s;
   `min-h-full` makes both behave identically). Bottom-fixed action bars = `sticky bottom-0`
   (+ a `from-background` gradient wash) — they pin to the device-frame bottom in review and to the
   viewport bottom in pure mode.
2. **Compose the kit.** Use `components/ui/*` (Button/Card/Input/Label/Badge/Skeleton) and project
   components from `src/components/*`. Recurring patterns (≥2 screens) are defined ONCE as a component
   and cataloged in `src/components/patterns.tsx` (`{ id, name, usage, tier?, usedIn, element }` — usage は
   「いつ使ってよいか」のルール、tier は Atomic Design 階層 `molecule`（既定・最小の意味単位）/
   `organism`（ヘッダー・ナビ等の自立領域）). The デザインシステム page renders the catalog as live
   specimens grouped by tier (Atoms=ui/キット, Pages=画面はページ側が自動網羅), and its token panel
   supports live adjustment (edits :root vars at runtime; コピーで globals.css へ確定).
3. **Tokens only.** Tailwind token utilities; no raw hex / arbitrary colors in screens (`bg-[#…]` is a
   gate violation). One `:root` edit must restyle the whole prototype.
4. **Navigation** via `const goto = useGoto()` → `goto("screen-id")` — works in pure AND review mode.
   Targets must exist in the registry and (normally) in `transitions`.
5. **States** via the `state` prop (`"default" | "empty" | "loading" | "error" | custom…`). Branch with
   early returns or conditionals; declared `states` in the spec must all be implemented. Loading =
   `<Skeleton>` mirroring the real layout.
6. **Responsive** with **container-query variants** (`@3xl:` ≈ 768px, `@5xl:` ≈ 1024px) — the pure canvas
   and every review device frame are `@container`s, so the Mobile/Tablet/Desktop switch previews real
   breakpoints. **Never use viewport variants (`sm:` `md:`…)** — fixed-width frames would all get
   desktop styles. Fixed-device specs (`meta.device: "mobile"` etc.) may skip breakpoints.
7. **Mock data is content.** Realistic values from the inputs; record origin in the spec's `mock.source`.
   Lists a few items long can stay inline; bigger fixtures go to `src/mocks/<screen-id>.ts`.
8. **Micro-interactions are IN scope; app logic is OUT.** Anything a reviewer will instinctively try
   must respond via local `useState`: option/segment selection, tabs, toggles, expand/collapse, real
   typeable inputs where the input experience matters. This is what makes the prototype useful for
   評価・体験検討 — a dead chip reads as a broken prototype. Out of scope: fetch/persistence/validation
   logic/business rules — the boundary is "UIの手応えは本物、データの裏側はモック".

Craft rules (hierarchy, spacing rhythm, affordance, states quality, microcopy): `references/ui-craft.md` — mandatory.

## Project layout (from template/)
```
<dest>/
├── pt-spec.json                 ← grounding（このファイルが v1 の spec に相当）
├── src/styles/globals.css      ← :root トークン（唯一のスタイル編集箇所）
├── src/screens/<id>.tsx + index.ts
├── src/components/*  + patterns.tsx（パターンカタログ）
├── src/components/ui/*          ← shadcn方式キット（リポジトリ所有・実装持ち越し）
├── src/review/*  src/pt/*       ← レビューシェル（通常は編集しない）
└── npm run dev / build（build = dist/index.html 単一自己完結HTML）
```
