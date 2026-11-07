import React from "react";
import { useStore } from "../store/useStore";
import { ChevronDown, Sliders } from "lucide-react";

export const TopBar: React.FC = () => {
  const {
    activeTab,
    setActiveTab,
    hour,
    simData,
    baseData,
    setScenarioModalOpen,
  } = useStore();

  const isHighAlert = (simData?.area_counts?.high && simData.area_counts.high > 0) || hour >= 20;
  const isMidAlert = simData?.area_counts?.mid && simData.area_counts.mid > 0;
  const statusText = isHighAlert ? "Cảnh báo" : isMidAlert ? "Theo dõi" : "Bình thường";
  const statusDotColor = isHighAlert ? "bg-[#ef4444]" : isMidAlert ? "bg-[#f59e0b]" : "bg-[#10b981]";

  return (
    <header className="relative w-full h-[54px] flex items-center justify-between px-4 z-20 shrink-0 select-none bg-[#090c12]/95 border-b border-white/[0.04]">
      {/* Left: Navigation and Titles */}
      <div className="flex items-center gap-4 h-full">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-3.5 py-1 text-xs font-bold rounded-md transition-all ${
              activeTab === "overview"
                ? "bg-white text-slate-950 shadow-sm"
                : "bg-slate-900/60 text-slate-300 border border-white/10 hover:border-white/20"
            }`}
          >
            Tổng quan
          </button>
          <button
            onClick={() => setActiveTab("ai")}
            className={`px-3.5 py-1 text-xs font-semibold rounded-md transition-all ${
              activeTab === "ai"
                ? "bg-white text-slate-950 shadow-sm"
                : "bg-slate-900/60 text-slate-300 border border-white/10 hover:border-white/20"
            }`}
          >
            Đánh giá AI
          </button>
        </div>

        <div className="leading-tight">
          <h1 className="text-[15px] font-bold text-white tracking-tight">
            Trung tâm giám sát nguy cơ sạt lở đất
          </h1>
          <p className="text-[10px] text-slate-400 font-medium mt-0.5">
            Nam Trà My và Phước Sơn, Quảng Nam
          </p>
        </div>
      </div>

      {/* Center: Live Status Capsule Pill */}
      <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-3.5 px-4 py-1.5 rounded-full bg-slate-900/90 border border-white/10 shadow-lg backdrop-blur-md text-[10px] text-slate-300">
        <div className="flex items-center gap-2 font-bold text-white">
          <span className={`w-2 h-2 rounded-sm ${statusDotColor}`} />
          <span>{statusText}</span>
        </div>
        <div className="font-mono text-slate-200">
          <span className="font-bold text-white">{`${hour.toString().padStart(2, "0")}:00`}</span> · giờ thứ {hour}
        </div>
        <span className="text-slate-400">Dữ liệu mô phỏng</span>
        <span className="text-slate-400">
          Dữ liệu <span className="text-slate-200 font-mono">2026-10-31 11:49</span>
        </span>
        <span className="text-slate-400">
          Mô hình <span className="text-slate-200 font-mono">11:59</span>
        </span>
      </div>

      {/* Right: Scenario Adjust Button */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setScenarioModalOpen(true)}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-900/80 border border-white/15 hover:border-white/30 text-xs font-semibold text-slate-200 hover:text-white transition-all shadow-md active:scale-95"
        >
          <Sliders className="w-3.5 h-3.5 text-slate-400" />
          <span>Điều chỉnh kịch bản</span>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        </button>
      </div>
    </header>
  );
};
