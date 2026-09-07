import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useGoto } from "@/pt/navigation";
import type { ScreenProps } from "./index";

/* プレースホルダー画面 — 生成時に pt-spec.json の画面群で置き換える。
   契約: Tailwind（コンテナクエリ変体 @sm:/@md:）＋ ui/ コンポーネントのみ、
   遷移は useGoto()、状態は state prop で分岐（references/pt-spec-format.md v2） */
export default function Home({ state }: ScreenProps) {
  const goto = useGoto();

  if (state === "loading") {
    return (
      <main className="mx-auto min-h-full max-w-[560px] space-y-3 p-4">
        <Skeleton className="h-14 w-full" />
        <Skeleton className="h-14 w-full" />
      </main>
    );
  }

  return (
    <div className="flex min-h-full flex-col">
      <main className="mx-auto w-full max-w-[560px] flex-1 p-4">
        <Card>
          <CardHeader>
            <CardTitle>SW*-GP テンプレート</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>pt-spec.json と src/screens/ を生成して置き換えてください。</p>
            <Button onClick={() => goto("home")}>プライマリアクション</Button>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
