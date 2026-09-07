import { useLocation, useNavigate } from "react-router-dom";

/* 画面遷移フック — ピュア/レビューどちらのモードでも同じ画面コンポーネントが動く */
export function useGoto() {
  const navigate = useNavigate();
  const inReview = useLocation().pathname.startsWith("/review");
  return (screenId: string) =>
    navigate(inReview ? `/review/proto/${screenId}` : `/${screenId}`);
}

/* 現在表示中の画面ID（FAB のモード切替が現在画面を保つために使う） */
export function useCurrentScreenId(): string | null {
  const { pathname } = useLocation();
  const seg = pathname.split("/").filter(Boolean);
  if (seg[0] === "review") return seg[1] === "proto" ? (seg[2] ?? null) : null;
  return seg[0] ?? null;
}
