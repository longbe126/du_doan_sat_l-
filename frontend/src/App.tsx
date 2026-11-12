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
import { HistoryPage } from "./components/HistoryPage";
import { Loader2 } from "lucide-react";

export const App: React.FC = () => {
  const { initData, isLoading, activeTab, viewMode, simData, hour } = useStore();

  useEffect(() => {
    initData();
  }, [initData]);

  const isHighAlert =
    (simData?.area_counts?.high && simData.area_counts.high > 0) || hour >= 20;
  const isMidAlert = simData?.area_counts?.mid && simData.area_counts.mid > 0;
  const glow = isHighAlert
    ? "239, 68, 68"
    : isMidAlert
    ? "245, 158, 11"
    : "16, 185, 129";

  if (isLoading) {
    return (
      <div className="w-screen h-screen flex flex-col items-center justify-center bg-[#07080b] text-[#e8e9ec] gap-3 select-none font-sans">
        <Loader2 className="w-8 h-8 animate-spin text-[#d4e88a]" />
        <p className="text-xs text-[#8b8f98] font-medium tracking-wide">
          Đang nạp mô hình địa hình 3D và dữ liệu học máy...
        </p>
      </div>
    );
  }

  return (
    <div
      className="relative w-screen h-screen flex flex-col overflow-hidden select-none font-sans"
      style={{
        background: `radial-gradient(ellipse 85% 42% at 50% 112%, rgba(${glow}, 0.35), transparent 72%), #07080b`,
      }}
    >
      {/* Top Navigation Bar */}
      <TopBar />

      {/* Main Workspace Body */}
      {activeTab === "overview" && (
        <>
          {/* Fullscreen 3D or 2D Map Canvas (Background) */}
          <div className="fixed inset-0 z-0 overflow-hidden pointer-events-auto">
            {viewMode === "3d" ? <Terrain3D /> : <Map2DView />}
          </div>

          {/* Simulation Notice Capsule */}
          <div className="fixed top-[62px] left-1/2 -translate-x-1/2 z-10 px-4 py-1 rounded-full bg-[rgba(28,30,34,0.92)] border border-[rgba(212,232,138,0.45)] text-[#d4e88a] text-[0.72rem] tracking-wider pointer-events-none shadow-xl whitespace-nowrap">
            DỮ LIỆU MÔ PHỎNG · CHỈ DÙNG ĐỂ GIÁM SÁT THỰC NGHIỆM
          </div>

          {/* Left Panel Sidebar (docked, scrolling cleanly above footer) */}
          <div className="fixed top-[58px] left-[18px] bottom-[76px] w-[370px] z-20 pointer-events-none">
            <div className="h-full pointer-events-auto overflow-y-auto no-scrollbar pr-1">
              <LeftPanel />
            </div>
          </div>

          {/* Right Panel Sidebar (docked, scrolling cleanly above footer) */}
          <div className="fixed top-[58px] right-[18px] bottom-[76px] w-[400px] z-20 pointer-events-none">
            <div className="h-full pointer-events-auto overflow-y-auto no-scrollbar pr-1">
              <RightPanel />
            </div>
          </div>

          {/* Bottom Docked Unified HUD Control Bar */}
          <TimelineBar />
        </>
      )}

      {activeTab === "history" && (
        <main className="flex-1 w-full overflow-hidden z-10 bg-[#07080b]">
          <HistoryPage />
        </main>
      )}

      {activeTab === "ai" && (
        <main className="flex-1 w-full overflow-hidden z-10 bg-[#07080b]">
          <AIEvaluationPage />
        </main>
      )}

      {/* Scenario Adjust Modal */}
      <ScenarioModal />
    </div>
  );
};

export default App;
