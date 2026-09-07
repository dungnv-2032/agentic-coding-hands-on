import { Navigate, Route, Routes } from "react-router-dom";
import { firstScreenId } from "@/pt/spec";
import { PureScreen } from "@/pt/pure-screen";
import { ModeFab } from "@/review/mode-fab";
import { ReviewLayout } from "@/review/review-layout";
import { Overview } from "@/review/overview";
import { Proto } from "@/review/proto";
import { FlowMap } from "@/review/flow-map";
import { Trace } from "@/review/trace";
import { DesignSystem } from "@/review/design-system";

/*
 * ルート構成:
 *   #/<screenId>[/<state>]          … ピュアモード（実プロトタイプのみ・既定）
 *   #/review/proto/<id>[/<state>]   … レビュー: プロトタイプ（根拠パネル・デバイス/状態切替）
 *   #/review/{overview|flow|trace|design}
 * 切替FAB: dev中は常時表示 / build後は ?switch=1 でのみ表示
 */
export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Navigate to={`/${firstScreenId}`} replace />} />
        <Route path="/review" element={<ReviewLayout />}>
          <Route index element={<Navigate to={`proto/${firstScreenId}`} replace />} />
          <Route path="overview" element={<Overview />} />
          <Route path="proto/:id/:state?" element={<Proto />} />
          <Route path="flow" element={<FlowMap />} />
          <Route path="trace" element={<Trace />} />
          <Route path="design" element={<DesignSystem />} />
        </Route>
        <Route path="/:id/:state?" element={<PureScreen />} />
      </Routes>
      <ModeFab />
    </>
  );
}
