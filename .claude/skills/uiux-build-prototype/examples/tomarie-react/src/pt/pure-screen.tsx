import { useEffect } from "react";
import { Navigate, useParams } from "react-router-dom";
import { AppModeProvider } from "@/pt/app-mode";
import { appType, defaultAppMode, firstScreenId, screensById, spec } from "@/pt/spec";
import { screens } from "@/screens";

const FIXED_WIDTH: Record<string, number> = { mobile: 390, tablet: 834, desktop: 1280 };

/* ピュアモード: 実プロトタイプ画面のみをフルビューポートで表示（ステークホルダーが見る形） */
export function PureScreen() {
  const { id = "", state = "default" } = useParams();
  const meta = screensById[id];
  const Comp = screens[id];

  useEffect(() => {
    if (meta) document.title = `${spec.meta.product} — ${meta.name}`;
    window.scrollTo(0, 0);
  }, [id, meta]);

  if (!meta || !Comp) return <Navigate to={`/${firstScreenId}`} replace />;

  const device = meta.device ?? spec.meta.device ?? "responsive";
  const fixed = FIXED_WIDTH[device];

  return (
    <div className={fixed ? "flex h-dvh justify-center bg-zinc-200" : "h-dvh"}>
      {/* キャンバス＝アプリのビューポート（高さ確定・内部スクロール）。
          画面ルートの min-h-full と sticky bottom-0 がピュア/デバイス枠で同じに振る舞う */}
      <div
        className="@container h-dvh w-full overflow-auto bg-background shadow-[0_0_24px_rgba(0,0,0,.08)]"
        style={fixed ? { maxWidth: fixed } : undefined}
      >
        {/* appType:"both" は ?app=1 でアプリ表示（実機のスマホで開く場合など） */}
        <AppModeProvider
          value={appType() === "both" && new URLSearchParams(window.location.search).has("app") ? "native" : defaultAppMode()}
        >
          <div key={`${id}/${state}`} className="pt-enter h-full">
            <Comp state={state} />
          </div>
        </AppModeProvider>
      </div>
    </div>
  );
}
