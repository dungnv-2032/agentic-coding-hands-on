import { useNavigate } from "react-router-dom";
import { coveringScreens, spec, uncoveredReqs } from "@/pt/spec";
import { Chip, MicroHead, OkBox, Panel, ViewTitle, WarnBox } from "./review-layout";

export function Trace() {
  const navigate = useNavigate();
  const reqs = spec.requirements ?? [];
  const un = uncoveredReqs();
  const go = (id: string) => navigate(`/review/proto/${id}`);

  return (
    <>
      <ViewTitle title="トレーサビリティ" />

      <Panel>
        <MicroHead>要件カバレッジ（{reqs.length} 件）</MicroHead>
        {reqs.length ? (
          <>
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#ECECEF] text-left text-[10px] tracking-wide text-zinc-400">
                  <th className="w-[45%] py-1.5">要件</th><th>カバーする画面</th>
                </tr>
              </thead>
              <tbody>
                {reqs.map((r) => {
                  const cov = coveringScreens(r);
                  return (
                    <tr key={r} className="border-b border-[#F2F2F5] align-top">
                      <td className="py-2 pr-3">{r}</td>
                      <td className="py-2">
                        {cov.length
                          ? cov.map((s) => <Chip key={s.id} onClick={() => go(s.id)}>{s.name}</Chip>)
                          : <span className="rounded-full bg-[#FFEEEC] px-2 py-0.5 text-[10px] font-bold text-[#AD0C00]">⚠ 未カバー</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {un.length
              ? <WarnBox>⚠ 未カバー要件 {un.length} 件 — 画面追加か、スコープ外の明示が必要です</WarnBox>
              : <OkBox>✓ 全要件カバー</OkBox>}
          </>
        ) : (
          <WarnBox>requirements が未登録です（ia-spec の prd.functionalReqs から転記してください）</WarnBox>
        )}
      </Panel>

      <Panel>
        <MicroHead>画面別の根拠</MicroHead>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[#ECECEF] text-left text-[10px] tracking-wide text-zinc-400">
              <th className="py-1.5">画面</th><th>IA画面</th><th>ペルソナ</th><th>ストーリー</th><th>要件</th><th>仮定・警告</th>
            </tr>
          </thead>
          <tbody>
            {spec.screens.map((s) => {
              const g = s.grounding ?? {};
              const has = g.iaScreen || g.personas?.length || g.stories?.length || g.reqs?.length;
              const cell = (items?: string[]) =>
                items?.length ? items.map((x) => <div key={x}>{x}</div>) : "—";
              return (
                <tr key={s.id} className="border-b border-[#F2F2F5] align-top">
                  <td className="py-2 pr-2"><Chip onClick={() => go(s.id)}>{s.name}</Chip></td>
                  <td className="py-2 pr-2">{g.iaScreen ? <Chip>{g.iaScreen}</Chip> : "—"}</td>
                  <td className="py-2 pr-2 leading-relaxed">{cell(g.personas)}</td>
                  <td className="py-2 pr-2 leading-relaxed">{cell(g.stories)}</td>
                  <td className="py-2 pr-2 leading-relaxed">{cell(g.reqs)}</td>
                  <td className="py-2 leading-relaxed">
                    {!has && <span className="mr-1 rounded-full bg-[#FFEEEC] px-2 py-0.5 text-[10px] font-bold text-[#AD0C00]">⚠ 根拠なし</span>}
                    {(g.assumptions ?? []).map((a) => <div key={a}>仮定: {a}</div>)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Panel>
    </>
  );
}
