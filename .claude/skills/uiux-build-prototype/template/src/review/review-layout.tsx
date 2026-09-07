import { NavLink, Outlet } from "react-router-dom";
import { Info, Smartphone, Workflow, Crosshair, Palette, MessageSquareText } from "lucide-react";
import { firstScreenId } from "@/pt/spec";
import { cn } from "@/lib/utils";

/* レビューシェルは Sun* ブランドの固定ニュートラル（プロダクトのトークンに影響されない） */
const TABS = [
  { to: "overview", label: "概要", icon: Info },
  { to: `proto/${firstScreenId}`, label: "プロトタイプ", icon: Smartphone, match: "proto" },
  { to: "flow", label: "フロー", icon: Workflow },
  { to: "trace", label: "トレーサビリティ", icon: Crosshair },
  { to: "design", label: "デザインシステム", icon: Palette },
];

/* SW*-GP スキルへのフィードバック（任意・GitHub Issues）— サイドバー下部のフッターに常設 */
const FEEDBACK_URL = "https://github.com/sun-asterisk-internal/takumi-design/issues";

export function ReviewLayout() {
  return (
    <div className="flex min-h-screen bg-[#F7F7F7] text-zinc-900" style={{ fontFamily: "'Noto Sans JP',sans-serif" }}>
      <nav className="sticky top-0 flex h-screen w-[216px] shrink-0 flex-col border-r border-[#ECECEF] bg-white">
        <div className="border-b border-[#F2F2F5] px-4 py-5 text-xl font-extrabold tracking-wide">
          <b className="text-[#FF2200]">SW*</b>-GP
        </div>
        <div className="flex-1 space-y-0.5 overflow-auto p-2.5">
          {TABS.map(({ to, label, icon: Icon, match }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-[13px] text-zinc-500 hover:bg-[#F2F2F5]",
                  (isActive || (match && location.hash.includes(`/review/${match}/`))) &&
                    "bg-[#FFEEEC] font-bold text-[#AD0C00] hover:bg-[#FFEEEC]",
                )
              }
            >
              <Icon className="size-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </div>
        <footer className="border-t border-[#F2F2F5] p-2.5">
          <a
            href={FEEDBACK_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-md px-2.5 py-2 text-[11px] leading-tight text-zinc-400 hover:bg-[#F2F2F5] hover:text-[#AD0C00]"
          >
            <MessageSquareText className="size-4 shrink-0" />
            <span>スキルへのフィードバック ↗</span>
          </a>
        </footer>
      </nav>
      <main className="min-w-0 flex-1 overflow-auto px-7 py-6 pb-16">
        <Outlet />
      </main>
    </div>
  );
}

/* レビュー画面共通の小物。タイトルは1行のみ（補足文は置かない — 煩雑になるため）。
   画面ID・roleなどの短いメタ情報は chips でタイトル横に */
export function ViewTitle({ title, chips }: { title: string; chips?: string[] }) {
  return (
    <header className="mb-5 flex flex-wrap items-baseline gap-2">
      <h1 className="text-[19px] font-extrabold">{title}</h1>
      {chips?.map((c) => <Chip key={c}>{c}</Chip>)}
    </header>
  );
}
export function Panel({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <section className={cn("mb-3.5 rounded border border-[#ECECEF] bg-white p-5 shadow-[0_1px_6px_rgba(0,0,0,.06)]", className)}>
      {children}
    </section>
  );
}
export function MicroHead({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-2 text-[9.5px] font-bold uppercase tracking-[.08em] text-zinc-400">{children}</p>
  );
}
export function Chip({ children, onClick, active }: { children: React.ReactNode; onClick?: () => void; active?: boolean }) {
  return (
    <span
      onClick={onClick}
      className={cn(
        "mb-0.5 mr-1 inline-block rounded-full border border-[#ECECEF] bg-[#F2F2F5] px-2.5 py-0.5 text-[11px]",
        onClick && "cursor-pointer hover:border-[#FF2200]",
        active && "border-[#F5C9C2] bg-[#FFEEEC] font-bold text-[#AD0C00]",
      )}
    >
      {children}
    </span>
  );
}
export function WarnBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="my-1.5 rounded border border-[#F5C9C2] bg-[#FFEEEC] px-3 py-2 text-xs text-[#AD0C00]">
      {children}
    </div>
  );
}
export function OkBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="my-1.5 rounded border border-[#CFE8D8] bg-[#EDF7F0] px-3 py-2 text-xs text-[#2c6e49]">
      {children}
    </div>
  );
}
