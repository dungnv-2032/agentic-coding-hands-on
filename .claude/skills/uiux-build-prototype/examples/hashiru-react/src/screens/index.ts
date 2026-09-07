import type { ComponentType } from "react";
import Onboarding from "./onboarding";
import Home from "./home";
import Run from "./run";
import Done from "./done";

export interface ScreenProps {
  state: string;
}

/* 画面レジストリ — pt-spec.json の screens[].id と 1:1 */
export const screens: Record<string, ComponentType<ScreenProps>> = {
  onboarding: Onboarding,
  home: Home,
  run: Run,
  done: Done,
};
