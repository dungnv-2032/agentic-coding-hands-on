import { createContext, useContext } from "react";

/* 表示イディオム: web = ブラウザ（グローバルヘッダー等）/ native = モバイルアプリ
   （ヘッダーなし・ボトムタブ等）。appType:"both" のプロダクトでは、レビューの
   Web/アプリ切替がこの値を変え、画面・コンポーネントは useAppMode() で分岐する */
export type AppMode = "web" | "native";

const AppModeContext = createContext<AppMode>("web");
export const AppModeProvider = AppModeContext.Provider;

export function useAppMode(): AppMode {
  return useContext(AppModeContext);
}
