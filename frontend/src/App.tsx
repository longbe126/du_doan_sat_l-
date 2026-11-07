import React, { useEffect } from "react";
import { useStore } from "./store/useStore";
import { TopBar } from "./components/TopBar";
import { LeftPanel } from "./components/LeftPanel";
import { RightPanel } from "./components/RightPanel";
import { Terrain3D } from "./components/Terrain3D";
import { Map2DView } from "./components/Map2DView";
import { TimelineBar } from "./components/TimelineBar";
import { ScenarioModal } from "./components/ScenarioModal";
import { AIEvaluationPage } from "./components/AIEvaluationPage";
import { Loader2 } from "lucide-react";

export const App: React.FC = () => {
  const { initData, isLoading, activeTab, viewMode } = useStore();

  useEffect(() => {
    initData();
  }, [initData]);

  if (isLoading) {
    return (
      <div className="w-screen h-screen flex flex-col items-center justify-center bg-[#06090e] text-white gap-3 select-none">
        <Loader2 className="w-8 h-8 animate-spin text-brand-yellow" />
        <p className="text-xs text-slate-400 font-medium tracking-wide">
          Đang nạp mô hình địa hình 3D và dữ liệu học máy...
        </p>
      </div>
    );
  }

  return (
    <div className="w-screen h-screen flex flex-col bg-[#06090e] overflow-hidden select-none">
      {/* Top Navigation Bar */}
      <TopBar />

      {/* Main Workspace Body */}
      {activeTab === "overview" ? (
        <>
          <div className="flex-1 flex w-full min-h-0 overflow-hidden relative">
            {/* Left Inspection and Events Panel */}
            <LeftPanel />

            {/* Center Canvas: 3D Terrain or 2D Map */}
            <main className="flex-1 h-full relative overflow-hidden">
              {viewMode === "3d" ? <Terrain3D /> : <Map2DView />}
            </main>

            {/* Right Telemetry and Regional Rankings Panel */}
            <RightPanel />
          </div>

          {/* Bottom Timeline Bar */}
          <TimelineBar />
        </>
      ) : (
        <main className="flex-1 w-full overflow-hidden">
          <AIEvaluationPage />
        </main>
      )}

      {/* Scenario Adjust Modal */}
      <ScenarioModal />
    </div>
  );
};

export default App;
