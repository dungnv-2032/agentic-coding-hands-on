import { useNavigate } from "react-router-dom";
import { flows, screensById, type Transition } from "@/pt/spec";
import { screens } from "@/screens";
import { cn } from "@/lib/utils";
import { ScreenThumb } from "./device-frame";
import { MicroHead, Panel, ViewTitle, WarnBox } from "./review-layout";

/* main遷移をたどってフローの画面列を得る（始点 = to に現れない from） */
function chainOf(mains: Transition[]): string[] {
  if (!mains.length) return [];
  const tos = new Set(mains.map((t) => t.to));
  let id: string | null = (mains.find((t) => !tos.has(t.from)) ?? mains[0]).from;
  const seen = new Set<string>();
  const chain: string[] = [];
  while (id && !seen.has(id)) {
    seen.add(id);
    chain.push(id);
    const next = mains.find((t) => t.from === id);
    id = next ? next.to : null;
  }
  return chain;
}

function FlowNode({ id, small }: { id: string; small?: boolean }) {
  const navigate = useNavigate();
  const meta = screensById[id];
  const Comp = screens[id];
  return (
    <button
      onClick={() => navigate(`/review/proto/${id}`)}
      className="cursor-pointer rounded-md border border-[#ECECEF] bg-white p-2 text-center shadow-[0_1px_6px_rgba(0,0,0,.06)] hover:border-[#FF2200]"
    >
      <ScreenThumb width={small ? 76 : 110}>{Comp && <Comp state="default" />}</ScreenThumb>
      <div className="mt-1.5 text-[11px] font-bold">{meta?.name ?? id}</div>
      {!small && meta?.primaryAction && (
        <div className="text-[10px] text-zinc-500">▸ {meta.primaryAction}</div>
      )}
    </button>
  );
}

function Arrow({ condition, sub }: { condition?: string; sub?: boolean }) {
  return (
    <div className="flex min-w-[70px] flex-col items-center px-1.5">
      {condition && <div className="mb-0.5 max-w-[110px] text-center text-[10px] text-zinc-500">{condition}</div>}
      <div className={cn("relative w-full border-t-2 border-[#9AA1AC]", sub && "border-dashed")}>
        <span className="absolute -right-px -top-[5px] border-y-[5px] border-l-[7px] border-y-transparent border-l-[#9AA1AC]" />
      </div>
    </div>
  );
}

export function FlowMap() {
  const grouped = flows();
  return (
    <>
      <ViewTitle title="フロー全体図" />
      {!Object.keys(grouped).length && <WarnBox>transitions が定義されていません</WarnBox>}
      {Object.entries(grouped).map(([name, ts]) => {
        const mains = ts.filter((t) => (t.kind ?? "main") === "main");
        const subs = ts.filter((t) => t.kind === "sub");
        const chain = chainOf(mains);
        return (
          <Panel key={name}>
            <div className="flex items-baseline justify-between">
              <MicroHead>{name}</MicroHead>
              <span className="text-[10px] text-zinc-400">実線＝メイン ／ 破線＝分岐 ・ クリックで画面へ</span>
            </div>
            {chain.length > 0 && (
              <div className="overflow-x-auto py-3">
                <div className="flex w-max items-center">
                  {chain.map((id, i) => {
                    const next = mains.find((t) => t.from === id && t.to === chain[i + 1]);
                    return (
                      <div key={id} className="flex items-center">
                        <FlowNode id={id} />
                        {next && <Arrow condition={next.condition} />}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            {subs.length > 0 && (
              <div className={cn("space-y-2", chain.length > 0 && "mt-2 border-t border-dashed border-[#ECECEF] pt-3")}>
                {subs.map((t, i) => (
                  <div key={i} className="flex w-max items-center">
                    <FlowNode id={t.from} small />
                    <Arrow condition={t.condition ?? "分岐"} sub />
                    <FlowNode id={t.to} small />
                  </div>
                ))}
              </div>
            )}
          </Panel>
        );
      })}
    </>
  );
}
