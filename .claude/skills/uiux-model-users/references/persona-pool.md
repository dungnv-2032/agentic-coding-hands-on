# Persona portrait pool

A set of generic, reusable persona portraits ships with the skill at
`assets/persona-pool/` (`p1.jpg` … `p12.jpg`). They let any user model show real
faces without sourcing images each time.

## How to use
- In a persona, set `image` to a pool reference: **`"p7"`** (or `"pool:7"` / `"p7.jpg"`).
- If a persona has **no `image`**, `bin/build-doc.py` auto-assigns one **by order**
  (persona 1 → p1, persona 2 → p2, …, wrapping after p12) so faces appear by default.
- Any explicit `data:` / `http(s)` / local-path `image` is used as-is (pool ignored).
- `build-doc.py` bakes the chosen portrait into the HTML as a self-contained data URI.

**When generating a model, prefer to set a *fitting* pool ref per persona** (match the
persona's rough age / gender / vibe to the portrait below) rather than relying on the
order-based fallback.

## The 12 portraits (rough demographics — illustrative, not prescriptive)
| ref | 見た目（おおよそ） |
|---|---|
| `p1` | 20代・男性／黒髪・丸眼鏡・ベージュシャツ（アジア系） |
| `p2` | 40〜50代・男性／白髪混じり・眼鏡・ネイビースーツ（アジア系） |
| `p3` | 60代・男性／白髪・あごひげ・丸眼鏡（アジア系） |
| `p4` | 30代・女性／茶系ウェーブ・笑顔・肩掛けバッグ（アジア系） |
| `p5` | 20〜30代・女性／カールした黒髪・カーディガン（ミックス系） |
| `p6` | 20代・男性／黒髪・パーカー＋ジャケット（アジア系） |
| `p7` | 50〜60代・女性／白髪・眼鏡・ベージュジャケット（アジア系） |
| `p8` | 30〜40代・男性／短髪・口ひげ・ダークシャツ（黒人／ミックス系） |
| `p9` | 60代・男性／白髪・口ひげ・眼鏡・ブラウンニット（黒人系） |
| `p10` | 40代・女性／ダークヘア・ジャケット（南アジア／ラテン系） |
| `p11` | 30代・女性／黒髪ポニーテール・眼鏡・マスタードトップ（東アジア系） |
| `p12` | 20代・男性／ブロンド寄り・ティールのトップ（欧米系） |

## Notes
- The pool covers a spread of age / gender / ethnicity for general reuse. Pick what best
  represents each persona; it does not have to be exact.
- To extend the pool, drop more `pN.jpg` files into `assets/persona-pool/` (sequential
  numbering); `build-doc.py` picks them up automatically.
- The Figma output (Stage 3) draws initial-based avatars (Plugin-API inline-code size
  limits make embedding photos impractical there); the photo pool is for the HTML viewer.
