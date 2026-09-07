# User-modeling methods — the how-to behind each artifact

Each artifact in `um-spec.json` answers a different question about the user. Use this as the
practitioner's guide; the spec schema is in `um-spec-format.md`.

---

## 1. ペルソナ (Persona) — *who are we building for?*
A persona is a **sharp, specific representative user**, not a demographic average.

**Make it real:**
- Give a name + face (`image`, or the viewer generates an avatar) and a one-line `tagline`.
- A first-person `quote` is the single highest-signal element — it makes the persona speakable.
- Lead with **goals, frustrations, motivations** (what drives behavior), not just demographics.
- `behaviors` + `scenario` ground the persona in real contexts of use.
- **各リスト（goals / frustrations / motivations / behaviors / needs / channels）は最大2件**に絞る。全部を書き出さず、最も鋭い2件を選ぶ — 選ぶ行為そのものが「何が本当に効くか」の判断になる。1スライドに収まり読みやすくなる。

**Types (`type`):**
- `primary` — the person you optimize for. 1–2 only.
- `secondary` — served, but not at the cost of the primary.
- `anti` — explicitly **not** the target. An anti-persona sharpens scope more than another primary; it stops scope creep ("we're not for X").

**Common mistakes:** too many personas; attribute-only personas with no goals; personas invented with no research (if so, flag in `meta.assumptions`); personas that are really job titles.

---

## 2. エンパシーマップ (Empathy Map) — *what is their inner world?*
Captures four facets of a persona in a moment/context, then distills Pains & Gains.

- **Says** — observable, real quotes ("I just copy last month's invoice").
- **Thinks** — the unspoken inner voice (often contradicts Says).
- **Does** — observable actions/behaviors.
- **Feels** — emotions (anxious, embarrassed, relieved).
- **Pains** — frustrations, obstacles, fears, risks.
- **Gains** — wants, needs, definitions of success.

**Tip:** the gap between **Says** and **Thinks** is where the richest insights live. Build one per primary persona.

---

## 3. カスタマージャーニー (Customer Journey) — *how does the experience unfold over time?*
A time-ordered map of one persona pursuing one scenario.

For each **stage** (e.g. 認知 → 検討 → 利用 → 継続):
- `goal` — what the user wants in this phase.
- `actions` — what they do.
- `touchpoints` — where they interact (channels, screens, people).
- `thoughts` — expectations, questions, doubts.
- `emotionScore` (-2..2) — drives the **emotion curve**. Be honest about the lows.
- `painPoints` — obstacles, drop-off risks.
- `opportunities` — design responses to the pains.

**Rule:** every emotional low (`emotionScore < 0`) must have at least one `opportunity`. The curve exists to make lows visible so they get fixed. Keep stages to ~4–7.

---

## 4. ユーザーインサイト (User Insight) — *what does it mean?*
The bridge from research to design. An **observation** is what happened; an **insight** is *why it matters*.

Structure each insight:
- `observation` — the surprising fact (grounded in `evidence`).
- `insight` — the underlying "why" (the non-obvious truth).
- `implication` — what the product should therefore do.
- `hmw` — a "How Might We …?" question that opens solution space.
- `evidence` — quotes/data backing it. `impact` — high/medium/low.

**Test of a real insight:** it's non-obvious, it explains a behavior, and it changes a decision. "Users want it faster" is not an insight. "Users don't chase unpaid invoices because it feels *socially risky*, not because they don't know how" is.

---

## 5. ユーザーストーリーマッピング (User Story Mapping) — *what do we build, for whom, when?*
Translates persona goals into implementable units **and** arranges them so scope and sequence are visible at a glance (Jeff Patton's story map).

**Two axes:**
- **Backbone (horizontal)** — `activities` = the user's flow of large actions, in time order (mirror the journey stages); each split into `tasks` (one column each). This is the narrative of *what the user does*, read left→right.
- **Releases (vertical)** — `releases` slice the stories into bands (MVP / Release 2 / Later). Each story sits at its task column × release row.

**Each story:**
- `title` — the capability from the user's view (〜できる), not a UI spec.
- `soThat` — the value/why. If you can't state the why, question the story.
- `persona` — who it serves (shows their avatar).
- `priority` — Must / Should / Could (left-rail color).
- `release` — which band it belongs to.

**The MVP rule:** the top (MVP) band should be a **walking skeleton** — the thinnest slice that goes end-to-end across the *whole* backbone, so the user can complete the core journey. Don't fully build one activity before touching the next.

**Trace:** good stories descend from journey `opportunities` and `insights.implication`. Every story names its persona.

---

## Sequencing
The artifacts build on each other:

```
segment / anti-persona  →  persona  →  empathy map  →  journey
                                                          │
                                          insights ←──────┘ (pains/lows)
                                              │
                                          story map (what to build, when)
```

Don't skip to stories without personas; don't write journeys without knowing whose journey it is. When research is thin, model anyway but mark assumptions — a flagged hypothesis is more useful than a hidden one.
