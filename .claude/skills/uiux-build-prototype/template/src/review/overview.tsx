import { spec, uncoveredReqs, flows } from "@/pt/spec";
import { MicroHead, OkBox, Panel, ViewTitle, WarnBox, Chip } from "./review-layout";

export function Overview() {
  const un = uncoveredReqs();
  const m = spec.meta;
  return (
    <>
      <ViewTitle title={m.product} />
      <Panel>
        <MicroHead>前提</MicroHead>
        <table className="w-full text-xs">
          <tbody>
            {[
              ["対象ユーザー", m.users],
              ["主目標", m.primaryGoal],
              ["デバイス / 段階", `${m.device ?? "—"} / ${m.stage ?? "—"}`],
              ["規模", `${spec.screens.length} 画面 ・ ${Object.keys(flows()).length} フロー ・ 要件 ${spec.requirements?.length ?? 0} 件`],
            ].map(([k, v]) => (
              <tr key={k} className="border-b border-[#F2F2F5]">
                <td className="w-[120px] py-2 text-zinc-400">{k}</td>
                <td className="py-2">{v ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
      <Panel>
        <MicroHead>入力ソース</MicroHead>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[#ECECEF] text-left text-[10px] tracking-wide text-zinc-400">
              <th className="py-1.5">ID</th><th>種別</th><th>パス</th><th>備考</th>
            </tr>
          </thead>
          <tbody>
            {(m.sources ?? []).map((s) => (
              <tr key={s.id} className="border-b border-[#F2F2F5] align-top">
                <td className="py-2 pr-2"><Chip>{s.id}</Chip></td>
                <td className="py-2 pr-2">{s.type}</td>
                <td className="py-2 pr-2">{s.path ?? ""}</td>
                <td className="py-2 text-zinc-500">{s.note ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
      <Panel>
        <MicroHead>前提・仮定（未検証）</MicroHead>
        {m.assumptions?.length ? (
          <ul className="list-disc pl-5 text-xs leading-relaxed">
            {m.assumptions.map((a) => <li key={a}>{a}</li>)}
          </ul>
        ) : (
          <OkBox>仮定なし — すべて入力に基づいています</OkBox>
        )}
      </Panel>
      <Panel>
        <MicroHead>要件カバレッジ</MicroHead>
        {un.length ? (
          <WarnBox>⚠ 未カバー要件 {un.length} 件 — トレーサビリティタブを確認</WarnBox>
        ) : (
          <OkBox>✓ 全要件がいずれかの画面でカバーされています</OkBox>
        )}
      </Panel>
    </>
  );
}
