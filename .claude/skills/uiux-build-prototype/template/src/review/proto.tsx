import { useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { appType, defaultAppMode, deviceOptions, firstScreenId, screensById, spec, statesOf, transitionsFrom, transitionsTo } from "@/pt/spec";
import type { AppMode } from "@/pt/app-mode";
import type { ScreenMeta } from "@/pt/spec";
import { screens } from "@/screens";
import { cn } from "@/lib/utils";
import { DeviceFrame } from "./device-frame";
import { Chip, MicroHead, ViewTitle, WarnBox } from "./review-layout";

function Pill({ children, active, onClick, tone }: { children: React.ReactNode; active?: boolean; onClick: () => void; tone?: "state" }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "cursor-pointer rounded-full border border-[#ECECEF] bg-white px-3 py-1 text-xs text-zinc-500",
        active && (tone === "state" ? "border-[#FF2200] bg-[#FF2200] font-bold text-white" : "border-zinc-900 bg-zinc-900 font-bold text-white"),
      )}
    >
      {children}
    </button>
  );
}

export function Proto() {
  const { id = "", state = "default" } = useParams();
  const navigate = useNavigate();
  const meta = screensById[id];
  const Comp = screens[id];
  const [device, setDevice] = useState<string | null>(null);
  const [showGrounding, setShowGrounding] = useState(true);
  // appType:"both" のときだけ Web ⇄ アプリ を切替可能（?app=1 でアプリ表示から開始）
  const [mode, setMode] = useState<AppMode>(() =>
    appType() === "both" && new URLSearchParams(window.location.search).has("app")
      ? "native"
      : defaultAppMode(),
  );

  if (!meta || !Comp) return <Navigate to={`/review/proto/${firstScreenId}`} replace />;

  const native = mode === "native";
  const options = deviceOptions(native); // ネイティブ表示は Desktop プレビューなし
  let dev =
    device ?? (meta.device && meta.device !== "responsive" ? meta.device : null) ??
    (spec.meta.device && spec.meta.device !== "responsive" ? spec.meta.device : "mobile");
  if (!options.includes(dev)) dev = options[0];
  const states = statesOf(meta);
  const goProto = (sid: string, st?: string) =>
    navigate(`/review/proto/${sid}${st && st !== "default" ? `/${st}` : ""}`);

  return (
    <>
      <ViewTitle title={meta.name} chips={[meta.id, `role: ${meta.role ?? "—"}`]} />

      {/* ツールバー: 表示モード / デバイス / 状態 / 根拠（画面と遷移は左のサイドナビ） */}
      <div className="mb-3.5 flex flex-wrap items-center gap-1.5">
        {appType() === "both" && (
          <>
            {(["web", "native"] as const).map((m) => (
              <Pill key={m} active={mode === m} onClick={() => setMode(m)}>
                {m === "web" ? "Web" : "アプリ"}
              </Pill>
            ))}
            <span className="mx-1 h-5 w-px bg-[#ECECEF]" />
          </>
        )}
        {options.map((d) => (
          <Pill key={d} active={dev === d} onClick={() => setDevice(d)}>
            {d === "mobile" ? "Mobile" : d === "tablet" ? "Tablet" : "Desktop"}
          </Pill>
        ))}
        {states.length > 1 && <span className="mx-1 h-5 w-px bg-[#ECECEF]" />}
        {states.length > 1 &&
          states.map((st) => (
            <Pill key={st} tone="state" active={state === st} onClick={() => goProto(id, st)}>{st}</Pill>
          ))}
        <span className="mx-1 h-5 w-px bg-[#ECECEF]" />
        <Pill active={showGrounding} onClick={() => setShowGrounding((v) => !v)}>
          根拠 {showGrounding ? "▲" : "▼"}
        </Pill>
      </div>

      <div className="flex items-start gap-4">
        <ScreenNav currentId={id} goProto={goProto} />
        <DeviceFrame device={dev} mode={mode}>
          <div key={`${id}/${state}/${mode}`} className="pt-enter h-full">
            <Comp state={state} />
          </div>
        </DeviceFrame>
        {showGrounding && <GroundingPanel meta={meta} />}
      </div>
    </>
  );
}

/* UI左の縦ナビ: 画面一覧＋現在画面の遷移元/遷移先（クリックでその画面へ） */
function ScreenNav({ currentId, goProto }: { currentId: string; goProto: (sid: string) => void }) {
  const from = transitionsTo(currentId);
  const to = transitionsFrom(currentId);
  const TransList = ({ title, items }: { title: string; items: { sid: string; condition?: string }[] }) => (
    <div>
      <MicroHead>{title}</MicroHead>
      {items.length ? (
        items.map(({ sid, condition }, i) => (
          <button
            key={`${sid}-${i}`}
            onClick={() => goProto(sid)}
            className="block w-full cursor-pointer rounded-md px-2.5 py-1.5 text-left hover:bg-[#F2F2F5]"
          >
            <span className="text-zinc-700">{screensById[sid]?.name ?? sid}</span>
            {condition && <span className="block text-[10px] leading-snug text-zinc-400">{condition}</span>}
          </button>
        ))
      ) : (
        <div className="px-2.5 text-zinc-300">—</div>
      )}
    </div>
  );
  return (
    <aside className="w-[192px] shrink-0 space-y-4 rounded border border-[#ECECEF] bg-white p-3 text-xs shadow-[0_1px_6px_rgba(0,0,0,.06)] max-[1000px]:hidden">
      <div>
        <MicroHead>画面</MicroHead>
        <div className="space-y-0.5">
          {spec.screens.map((s) => (
            <button
              key={s.id}
              onClick={() => goProto(s.id)}
              className={cn(
                "block w-full cursor-pointer rounded-md px-2.5 py-1.5 text-left text-xs text-zinc-600 hover:bg-[#F2F2F5]",
                s.id === currentId && "bg-[#FFEEEC] font-bold text-[#AD0C00] hover:bg-[#FFEEEC]",
              )}
            >
              {s.name}
            </button>
          ))}
        </div>
      </div>
      <TransList title="遷移元" items={from.map((t) => ({ sid: t.from, condition: t.condition }))} />
      <TransList title="遷移先" items={to.map((t) => ({ sid: t.to, condition: t.condition }))} />
    </aside>
  );
}

function GroundingPanel({ meta }: { meta: ScreenMeta }) {
  const g = meta.grounding ?? {};
  const none = !g.iaScreen && !g.personas?.length && !g.stories?.length && !g.reqs?.length;
  const List = ({ title, items }: { title: string; items?: string[] }) =>
    items?.length ? (
      <>
        <MicroHead>{title}</MicroHead>
        <ul className="mb-2 list-disc pl-4 leading-relaxed">{items.map((x) => <li key={x}>{x}</li>)}</ul>
      </>
    ) : null;
  return (
    <aside className="w-[280px] shrink-0 rounded border border-[#ECECEF] bg-white p-4 text-xs shadow-[0_1px_6px_rgba(0,0,0,.06)] max-[900px]:hidden">
      <MicroHead>この画面の根拠</MicroHead>
      {g.iaScreen && (
        <div className="mb-2"><MicroHead>IA画面</MicroHead><Chip>{g.iaScreen}</Chip></div>
      )}
      <List title="ペルソナ" items={g.personas} />
      <List title="ユーザーストーリー" items={g.stories} />
      <List title="要件" items={g.reqs} />
      {meta.mock?.source && (
        <>
          <MicroHead>モックデータの出典</MicroHead>
          <div className="mb-2 text-zinc-500">
            {meta.mock.source}
            {meta.mock.notes && <><br />{meta.mock.notes}</>}
          </div>
        </>
      )}
      {g.assumptions?.length ? <WarnBox>仮定: {g.assumptions.join(" / ")}</WarnBox> : null}
      {none && <WarnBox>⚠ 根拠未設定の画面です</WarnBox>}
    </aside>
  );
}
