import { useLocation, useNavigate } from "react-router-dom";
import { SlidersHorizontal, Smartphone } from "lucide-react";
import { firstScreenId } from "@/pt/spec";
import { useCurrentScreenId } from "@/pt/navigation";

/* ピュア ⇄ レビューを行き来する右下の丸ボタン。
   dev サーバ中は常時表示。build 後（共有HTML）は URL に ?switch=1 を付けたときだけ表示。 */
export function ModeFab() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const current = useCurrentScreenId() ?? firstScreenId;
  const inReview = pathname.startsWith("/review");

  const enabled =
    import.meta.env.DEV || new URLSearchParams(window.location.search).has("switch");
  if (!enabled) return null;

  return (
    <button
      title={inReview ? "プロトタイプのみ表示" : "レビューモードへ（根拠・フロー・トレーサビリティ）"}
      onClick={() => navigate(inReview ? `/${current}` : `/review/proto/${current}`)}
      className="fixed bottom-[18px] right-[18px] z-50 flex size-12 items-center justify-center rounded-full bg-zinc-900 text-white shadow-lg transition-transform hover:scale-[1.08] hover:bg-[#FF2200] cursor-pointer"
    >
      {inReview ? <Smartphone className="size-5" /> : <SlidersHorizontal className="size-5" />}
    </button>
  );
}
