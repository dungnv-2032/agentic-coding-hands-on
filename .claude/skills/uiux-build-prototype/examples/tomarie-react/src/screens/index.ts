import type { ComponentType } from "react";
import StaySearch from "./stay-search";
import StayDetail from "./stay-detail";
import BookingConfirm from "./booking-confirm";
import BookingDone from "./booking-done";

export interface ScreenProps {
  state: string;
}

/* 画面レジストリ — pt-spec.json の screens[].id と 1:1 */
export const screens: Record<string, ComponentType<ScreenProps>> = {
  "stay-search": StaySearch,
  "stay-detail": StayDetail,
  "booking-confirm": BookingConfirm,
  "booking-done": BookingDone,
};
