import React from "react";
import { useStore } from "../store/useStore";
import { Sliders } from "lucide-react";

const HI = "#ff5a52";
const MI = "#f5b942";
const LO = "#4ade80";

const hh = (t: number) => `${t.toString().padStart(2, "0")}:00`;

const MODEL_VI: Record<string, string> = {
  logistic_regression: "Hồi quy logistic",
  random_forest: "Rừng ngẫu nhiên",
  xgboost: "XGBoost",
};

export const TopBar: React.FC = () => {
  const {
    activeTab,
    setActiveTab,
    hour,
    simData,
    baseData,
    setScenarioModalOpen,
  } = useStore();

  const t = hour;
  const isHighAlert = (simData?.area_counts?.high && simData.area_counts.high > 0) || t >= 20;
  const isMidAlert = simData?.area_counts?.mid && simData.area_counts.mid > 0;
  const statusText = isHighAlert ? "Cảnh báo" : isMidAlert ? "Theo dõi" : "Bình thường";
  const statusDotColor = isHighAlert ? HI : isMidAlert ? MI : LO;

  const modelName = baseData?.model_name || "xgboost";
  const modelDisplay = MODEL_VI[modelName] || modelName;

  return (
    <header className="relative w-full h-[54px] flex items-center justify-between px-4 z-20 shrink-0 select-none bg-transparent">
      {/* Left: Navigation Tabs */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setActiveTab("overview")}
          className={`px-3.5 py-1 text-[0.76rem] rounded-md transition-all cursor-pointer ${
            activeTab === "overview"
              ? "bg-[#d4e88a] text-[#1b2208] font-bold shadow-sm"
              : "bg-[rgba(34,36,40,0.85)] text-[#e8e9ec] border border-white/[0.1] hover:border-white/20"
          }`}
        >
          Tổng quan
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`px-3.5 py-1 text-[0.76rem] rounded-md transition-all cursor-pointer ${
            activeTab === "history"
              ? "bg-[#d4e88a] text-[#1b2208] font-bold shadow-sm"
              : "bg-[rgba(34,36,40,0.85)] text-[#e8e9ec] border border-white/[0.1] hover:border-white/20"
          }`}
        >
          Lịch sử sạt lở
        </button>
      </div>

      {/* Center: Live Status Capsule Pill (Streamlit .status) */}
      <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-3 px-4 py-1.5 rounded-full bg-[rgba(34,36,40,0.7)] backdrop-blur-[18px] border border-white/[0.08] shadow-xl text-[0.82rem] text-[#8b8f98] pointer-events-none">
        <div className="flex items-center gap-2 text-white font-medium">
          <i
            className="w-[9px] h-[9px] rounded-[2px]"
            style={{ backgroundColor: statusDotColor }}
          />
          <b>{statusText}</b>
        </div>
        <span>
          {hh(t)} · giờ thứ {t}
        </span>
        <span>Dữ liệu mô phỏng</span>
        <span>Mô hình {modelDisplay}</span>
      </div>

      {/* Right: Scenario Adjust Button (Streamlit .st-key-g_ctrl) */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setScenarioModalOpen(true)}
          className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-[rgba(34,36,40,0.85)] hover:bg-[rgba(50,54,60,0.95)] border border-white/[0.15] hover:border-white/30 text-[0.8rem] font-medium text-[#e8e9ec] hover:text-white transition-all shadow-md active:scale-95 cursor-pointer"
        >
          <Sliders className="w-3.5 h-3.5 text-[#d4e88a]" />
          <span>Điều chỉnh kịch bản ▾</span>
        </button>
      </div>
    </header>
  );
};
