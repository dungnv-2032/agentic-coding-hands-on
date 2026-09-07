import { useLayoutEffect, useRef, useState } from "react";
import { AppModeProvider, type AppMode } from "@/pt/app-mode";
import { defaultAppMode, spec } from "@/pt/spec";
import { cn } from "@/lib/utils";

export const DEVICES: Record<string, { w: number; h: number }> = {
  mobile: { w: 390, h: 780 },
  tablet: { w: 834, h: 900 },
  desktop: { w: 1280, h: 800 },
};

/* デバイス枠 — mode でクロームが変わる:
   native: ネイティブ表示（ステータスバー＋ホームインジケータ、ブラウザUIなし）
   web   : ブラウザ表示（desktop=ウィンドウ+URLバー / mobile・tablet=モバイルブラウザのURLバー）
   中身は @container ＋ AppModeProvider — 画面側も useAppMode() でイディオムを分岐できる */
export function DeviceFrame({
  device,
  mode,
  children,
}: {
  device: string;
  mode: AppMode;
  children: React.ReactNode;
}) {
  const { w, h } = DEVICES[device] ?? DEVICES.mobile;
  const wrapRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  useLayoutEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const fit = () => setScale(Math.min(1, (el.clientWidth - 8) / (w + 20)));
    fit();
    const ro = new ResizeObserver(fit);
    ro.observe(el);
    return () => ro.disconnect();
  }, [w]);

  const native = mode === "native";
  const isDesktop = device === "desktop";
  // クロームの高さ: native=ステータスバーのみ / web mobile=ステータス+URLバー / desktop=ブラウザバー
  const chromeH = isDesktop ? 40 : native ? 26 : 58;
  // 下部セーフエリア: sticky bottom-0 のフッターがベゼルに密着しないよう底に確保する帯。
  // native はホームインジケータの居場所（実機のセーフエリア相当）、web mobile/tablet は小さな余白。
  const safeBottom = isDesktop ? 0 : native ? 28 : 14;

  return (
    <div ref={wrapRef} className="flex flex-1 justify-center overflow-hidden pb-8 pt-2">
      <div style={{ transform: `scale(${scale})`, transformOrigin: "top center", height: (h + 20) * scale }}>
        <div className={cn("relative shadow-[0_12px_34px_rgba(0,0,0,.18)]", isDesktop ? "rounded-[10px] bg-[#E4E7EC] p-2" : "rounded-[34px] bg-[#111] p-2.5")}>
          {isDesktop ? (
            /* ブラウザウィンドウのクローム */
            <div className="flex items-center gap-2 rounded-t-[6px] bg-[#F1F3F6] px-3" style={{ width: w, height: chromeH }}>
              <span className="flex gap-1.5">
                <i className="size-3 rounded-full bg-[#FF5F57]" />
                <i className="size-3 rounded-full bg-[#FEBC2E]" />
                <i className="size-3 rounded-full bg-[#28C840]" />
              </span>
              <span className="mx-auto flex w-[46%] items-center justify-center gap-1 truncate rounded-full bg-white px-3 py-1 text-[11px] text-zinc-500">
                🔒 {spec.meta.product}
              </span>
            </div>
          ) : (
            <div className="rounded-t-[24px] bg-background" style={{ width: w }}>
              {/* ステータスバー */}
              <div className="flex items-center justify-between px-4 text-[11px] font-semibold text-foreground" style={{ height: 26 }}>
                <span>9:41</span>
                <span>●●● ᯤ ▮</span>
              </div>
              {/* web-app のモバイルはブラウザのURLバーが付く（native は付かない） */}
              {!native && (
                <div className="flex items-center justify-center border-b border-border px-4" style={{ height: chromeH - 26 }}>
                  <span className="flex w-[80%] items-center justify-center gap-1 truncate rounded-full bg-muted px-3 py-1 text-[11px] text-muted-foreground">
                    🔒 {spec.meta.product}
                  </span>
                </div>
              )}
            </div>
          )}
          <div
            className={cn("@container overflow-auto bg-background", isDesktop && "rounded-b-[6px]")}
            style={{ width: w, height: h - chromeH - safeBottom }}
          >
            <AppModeProvider value={mode}>
              <div className="h-full">{children}</div>
            </AppModeProvider>
          </div>
          {/* 下部セーフエリア帯（ベゼル内・背景色）— sticky フッターはこの帯の上端で止まりベゼルに密着しない。
              native はここにホームインジケータを置く（コンテンツに重ねず、実機のセーフエリア同様） */}
          {!isDesktop && (
            <div className="flex items-end justify-center rounded-b-[24px] bg-background" style={{ width: w, height: safeBottom }}>
              {native && <div className="mb-2 h-1 w-28 rounded-full bg-black/25" />}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* フロー全体図などのミニサムネイル（クリック不可・縮小描画） */
export function ScreenThumb({ width = 110, children }: { width?: number; children: React.ReactNode }) {
  const base = 390; // レスポンシブ画面はモバイル幅で代表描画
  const height = Math.round(width * 1.72);
  return (
    <div className="pointer-events-none overflow-hidden rounded border border-[#F2F2F5] bg-white" style={{ width, height }}>
      <div
        className="@container bg-background"
        style={{ width: base, height: height / (width / base), transform: `scale(${width / base})`, transformOrigin: "top left" }}
      >
        <AppModeProvider value={defaultAppMode()}>
          <div className="h-full">{children}</div>
        </AppModeProvider>
      </div>
    </div>
  );
}
