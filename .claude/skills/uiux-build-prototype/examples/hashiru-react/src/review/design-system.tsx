import { useNavigate } from "react-router-dom";
import { screensById, spec, statesOf } from "@/pt/spec";
import { type Pattern, patterns } from "@/components/patterns";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Chip, MicroHead, Panel, ViewTitle } from "./review-layout";
import { DirectionPanel, TokenAdjustPanel, TypographyPanel } from "./ds-tokens";

/* デザインシステム — Atomic Design の階層で俯瞰する:
   トークン（調整可）→ Atoms（ui/キット）→ Molecules / Organisms（プロジェクトパターン）→ Pages（画面）。
   トークンを触ると全階層のスペシメンとプロトタイプ本体が同時に変わるので、
   「この色で全画面がどう見えるか」をこのページだけで検討できる */

function Specimen({ children }: { children: React.ReactNode }) {
  return (
    <div className="@container pointer-events-none flex min-h-[96px] items-center justify-center bg-background p-4">
      {children}
    </div>
  );
}

function SpecimenCard({ name, usage, children, footer }: { name: string; usage: string; children: React.ReactNode; footer?: React.ReactNode }) {
  return (
    <div className="flex flex-col overflow-hidden rounded-md border border-[#ECECEF] bg-white">
      <Specimen>{children}</Specimen>
      <div className="border-t border-[#F2F2F5] px-3 py-2.5 text-xs">
        <b>{name}</b>
        <div className="mt-0.5 text-[11px] leading-relaxed text-zinc-500">{usage}</div>
        {footer}
      </div>
    </div>
  );
}

/* Atoms = ui/ キット（shadcn方式・実装持ち越し可）。全バリアントを網羅表示する */
const ATOMS: { name: string; usage: string; el: React.ReactNode }[] = [
  {
    name: "Button — variants",
    usage: "default=主操作（1画面1つ）/ secondary=副操作 / outline=強調の副操作 / destructive=取り消し系（塗らない）/ ghost・link=三次操作",
    el: (
      <div className="flex flex-wrap items-center justify-center gap-2">
        <Button>送信する</Button><Button variant="secondary">キャンセル</Button><Button variant="outline">下書き保存</Button>
        <Button variant="destructive">取り下げる</Button><Button variant="ghost">閉じる</Button><Button variant="link">詳しく見る</Button>
      </div>
    ),
  },
  {
    name: "Button — sizes",
    usage: "sm=行内 / default=標準（44px+）/ lg=画面の主CTA / icon=アイコン単体（44px角）",
    el: (
      <div className="flex flex-wrap items-center justify-center gap-2">
        <Button size="sm">小</Button><Button>標準</Button><Button size="lg">大きく</Button><Button size="icon" aria-label="追加">＋</Button>
      </div>
    ),
  },
  {
    name: "Badge",
    usage: "ステータスは色＋文字を必ず併記（色だけに頼らない）。dot で状態感を足す",
    el: (
      <div className="flex flex-wrap justify-center gap-2">
        <Badge>既定</Badge><Badge variant="secondary">副次</Badge><Badge variant="outline">枠のみ</Badge>
        <Badge variant="warning" dot>承認待ち</Badge><Badge variant="success" dot>承認済み</Badge><Badge variant="destructive" dot>差し戻し</Badge>
      </div>
    ),
  },
  {
    name: "Input + Label",
    usage: "ラベル上置き・必須はdestructiveで明示・15px以上（iOSズーム回避）。disabled は操作不能の見た目",
    el: (
      <div className="w-full max-w-[240px] space-y-2">
        <div><Label>金額 <span className="text-destructive">必須</span></Label><Input readOnly value="¥3,200" className="tabular font-bold" /></div>
        <Input disabled placeholder="入力できません" />
      </div>
    ),
  },
  {
    name: "Card",
    usage: "1情報のまとまり。余白はp-4基準・テキストを枠に触れさせない",
    el: <Card className="w-full max-w-[260px]"><CardHeader><CardTitle>カードタイトル</CardTitle></CardHeader><CardContent className="text-sm text-muted-foreground">本文テキスト</CardContent></Card>,
  },
  {
    name: "Skeleton",
    usage: "ローディングはレイアウトを写した形で（スピナー1行にしない）",
    el: <div className="w-full max-w-[240px] space-y-2"><Skeleton className="h-4 w-3/5" /><Skeleton className="h-3 w-2/5" /></div>,
  },
];

const TIER_INFO: { tier: NonNullable<Pattern["tier"]>; title: string; desc: string }[] = [
  { tier: "molecule", title: "Molecules — 分子", desc: "Atomsを組み合わせた最小の意味単位（components/patterns.tsx）" },
  { tier: "organism", title: "Organisms — 有機体", desc: "分子を束ねた自立したUI領域（ヘッダー・カード・ナビなど）" },
];

export function DesignSystem() {
  const navigate = useNavigate();
  const byTier = (t: Pattern["tier"]) => patterns.filter((p) => (p.tier ?? "molecule") === t);

  return (
    <>
      <ViewTitle title="デザインシステム" chips={["Atomic Design"]} />

      <DirectionPanel />
      <TokenAdjustPanel />
      <TypographyPanel />

      <Panel>
        <MicroHead>Atoms — 原子（components/ui — shadcn方式・実装持ち越し可）</MicroHead>
        <div className="grid grid-cols-[repeat(auto-fill,minmax(270px,1fr))] gap-3">
          {ATOMS.map((k) => <SpecimenCard key={k.name} name={k.name} usage={k.usage}>{k.el}</SpecimenCard>)}
        </div>
      </Panel>

      {TIER_INFO.map(({ tier, title, desc }) => {
        const list = byTier(tier);
        if (!list.length) return null;
        return (
          <Panel key={tier}>
            <MicroHead>{title}（{list.length}） — {desc}</MicroHead>
            <div className="grid grid-cols-[repeat(auto-fill,minmax(270px,1fr))] gap-3">
              {list.map((p) => (
                <SpecimenCard
                  key={p.id}
                  name={p.name}
                  usage={p.usage}
                  footer={p.usedIn?.length ? (
                    <div className="mt-1.5">
                      <span className="text-[9.5px] text-zinc-400">使用画面 </span>
                      {p.usedIn.map((id) => (
                        <Chip key={id} onClick={() => navigate(`/review/proto/${id}`)}>
                          {screensById[id]?.name ?? id}
                        </Chip>
                      ))}
                    </div>
                  ) : undefined}
                >
                  {p.element}
                </SpecimenCard>
              ))}
            </div>
          </Panel>
        );
      })}

      <Panel>
        <MicroHead>Pages — ページ（{spec.screens.length}画面） — クリックでプロトタイプへ。調整中のトークンのまま確認できます</MicroHead>
        <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-2">
          {spec.screens.map((s) => (
            <button
              key={s.id}
              onClick={() => navigate(`/review/proto/${s.id}`)}
              className="cursor-pointer rounded-md border border-[#ECECEF] bg-white px-3 py-2.5 text-left text-xs hover:border-[#FF2200]"
            >
              <b>{s.name}</b>
              <span className="mt-0.5 block text-[10px] text-zinc-400">
                {s.id}{s.role ? ` ・ ${s.role}` : ""} ・ 状態{statesOf(s).length}
              </span>
            </button>
          ))}
        </div>
      </Panel>
    </>
  );
}
