import type { ComponentType } from "react";
import ExpenseList from "./expense-list";
import ExpenseForm from "./expense-form";
import ExpenseDetail from "./expense-detail";
import ExpenseComplete from "./expense-complete";

export interface ScreenProps {
  state: string;
}

/* 画面レジストリ — pt-spec.json の screens[].id と 1:1 */
export const screens: Record<string, ComponentType<ScreenProps>> = {
  "expense-list": ExpenseList,
  "expense-form": ExpenseForm,
  "expense-detail": ExpenseDetail,
  "expense-complete": ExpenseComplete,
};
