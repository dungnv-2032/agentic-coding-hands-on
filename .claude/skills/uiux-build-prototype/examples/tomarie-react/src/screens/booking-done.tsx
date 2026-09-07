import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { AppHeader } from "@/components/app-header";
import { Photo } from "@/components/photo";
import { PRIMARY_LISTING } from "@/mocks/listings";
import { useGoto } from "@/pt/navigation";
import type { ScreenProps } from "./index";

/* リクエスト制なので「承認待ち」の期待値を最初に伝える（完了＝確定ではない） */
export default function BookingDone(_: ScreenProps) {
  const goto = useGoto();
  const l = PRIMARY_LISTING;
  return (
    <div className="flex min-h-full flex-col">
      <AppHeader />
      <main className="mx-auto flex w-full max-w-[560px] flex-1 flex-col items-center justify-center px-4 py-10 text-center">
        <div className="flex size-16 items-center justify-center rounded-full bg-success text-3xl text-white">✓</div>
        <h1 className="mt-4 text-2xl font-extrabold">リクエストを送りました</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          ホストの佐野さんが<b className="text-foreground">24時間以内</b>に承認すると予約が確定します。
          <br />
          結果はメールとアプリでお知らせします。
        </p>
        <Card className="mt-5 flex w-full gap-3 p-3 text-left">
          <Photo scene={l.scene} className="size-16 shrink-0 rounded-lg" />
          <div className="min-w-0 text-sm">
            <div className="truncate font-bold">{l.title}</div>
            <div className="mt-0.5 text-muted-foreground">7/18（土）〜19（日） ・ 2人 ・ <span className="tabular">¥22,800</span></div>
            <div className="mt-1 text-xs font-bold text-warning">● ホストの承認待ち</div>
          </div>
        </Card>
        <Button variant="secondary" className="mt-6" onClick={() => goto("stay-search")}>さがすに戻る</Button>
      </main>
    </div>
  );
}
