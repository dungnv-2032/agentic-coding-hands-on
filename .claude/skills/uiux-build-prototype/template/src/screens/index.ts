import type { ComponentType } from "react";
import Home from "./home";

/* 画面ごとの props 契約: 現在の状態名（default / empty / loading / error / …）を受け取る */
export interface ScreenProps {
  state: string;
}

/* 画面レジストリ — pt-spec.json の screens[].id と 1:1 で対応させる */
export const screens: Record<string, ComponentType<ScreenProps>> = {
  home: Home,
};
