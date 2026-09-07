import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { AppHeader } from "@/components/app-header";
import { Photo } from "@/components/photo";
import { PRIMARY_LISTING } from "@/mocks/listings";
import { useGoto } from "@/pt/navigation";
import { cn } from "@/lib/utils";
import type { ScreenProps } from "./index";

const PAYMENTS = [
  { id: "card", label: "クレジットカード", note: "VISA •••• 4242（登録済み）" },
  { id: "cvs", label: "コンビニ払い", note: "確定後3日以内にお支払い" },
];

/* 支払い方法のラジオ選択は実際に動く。state=error は未選択のまま確定しようとした状態 */
export default function BookingConfirm({ state }: ScreenProps) {
  const goto = useGoto();
  const l = PRIMARY_LISTING;
  const [payment, setPayment] = useState<string | null>(state === "error" ? null : "card");

  return (
    <div className="flex min-h-full flex-col">
      <AppHeader />
      <main className="mx-auto w-full max-w-[640px] flex-1 px-4 py-4">
        <button className="mb-3 cursor-pointer text-sm text-primary" onClick={() => goto("stay-detail")}>‹ 内容を直す</button>
        <h1 className="text-xl font-extrabold">予約の確認</h1>

        <Card className="mt-4 flex gap-3 p-3">
          <Photo scene={l.scene} className="size-20 shrink-0 rounded-lg" />
          <div className="min-w-0 text-sm">
            <div className="truncate font-bold">{l.title}</div>
            <div className="mt-0.5 text-muted-foreground">7/18（土）〜19（日） ・ 2人</div>
            <div className="mt-1"><b className="tabular">¥22,800</b> <span className="text-xs text-muted-foreground">合計（1泊・清掃料/サービス料込み）</span></div>
          </div>
        </Card>

        <section className="mt-5">
          <h2 className="mb-2 text-sm font-bold">支払い方法 <span className="text-destructive">必須</span></h2>
          {state === "error" && !payment && (
            <div className="mb-2 rounded-lg border border-destructive bg-card p-3 text-sm">
              <span className="font-bold text-destructive">エラー：支払い方法を選択してください</span>
            </div>
          )}
          <div className="space-y-2">
            {PAYMENTS.map((p) => (
              <label
                key={p.id}
                className={cn(
                  "flex cursor-pointer items-center gap-3 rounded-lg border-[1.5px] bg-card p-3.5",
                  payment === p.id ? "border-primary" : "border-border",
                )}
              >
                <input
                  type="radio"
                  name="payment"
                  checked={payment === p.id}
                  onChange={() => setPayment(p.id)}
                  className="size-4 accent-[var(--primary)]"
                />
                <span className="text-sm">
                  <b>{p.label}</b>
                  <span className="block text-xs text-muted-foreground">{p.note}</span>
                </span>
              </label>
            ))}
          </div>
        </section>

        <p className="mt-4 text-xs leading-relaxed text-muted-foreground">
          これは予約リクエストです。ホストが24時間以内に承認すると予約が確定し、支払いが発生します。
          チェックイン5日前まで無料キャンセルできます。
        </p>
      </main>
      <div className="sticky bottom-0 border-t border-border bg-card">
        <div className="mx-auto w-full max-w-[640px] p-4">
          <Button size="lg" className="w-full" disabled={!payment} onClick={() => goto("booking-done")}>
            予約リクエストを確定する
          </Button>
        </div>
      </div>
    </div>
  );
}
