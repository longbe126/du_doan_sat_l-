import React from "react";
import { useStore } from "../store/useStore";
import { X, Sliders, RotateCcw } from "lucide-react";

export const ScenarioModal: React.FC = () => {
  const {
    isScenarioModalOpen,
    setScenarioModalOpen,
    scale,
    setScale,
    thresholdLow,
    thresholdHigh,
    setThresholds,
    rainAlert,
    setRainAlert,
  } = useStore();

  if (!isScenarioModalOpen) return null;

  const handleReset = () => {
    setScale(1.0);
    setThresholds(0.40, 0.70);
    setRainAlert(100);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-md rounded-2xl bg-[#0c1424] border border-white/15 p-6 shadow-2xl flex flex-col gap-5 text-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-brand-yellow" />
            <h2 className="text-sm font-bold text-white">Điều chỉnh kịch bản mô phỏng</h2>
          </div>
          <button
            onClick={() => setScenarioModalOpen(false)}
            className="p-1 text-slate-400 hover:text-white rounded-md hover:bg-white/10 transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Sliders */}
        <div className="flex flex-col gap-4 text-xs">
          {/* Rainfall Scale */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-baseline">
              <span className="font-semibold text-white">Hệ số lượng mưa</span>
              <span className="font-mono text-brand-yellow font-bold text-sm">
                {scale.toFixed(1)}x
              </span>
            </div>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={scale}
              onChange={(e) => setScale(parseFloat(e.target.value))}
              className="w-full accent-lime-400 cursor-pointer"
            />
            <p className="text-[10px] text-slate-400">
              Nhân với lượng mưa kịch bản 24 giờ (0.5x = mưa nhẹ, 1.0x = mưa trung bình, 2.0x = mưa cực đoan).
            </p>
          </div>

          {/* Threshold Low */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-baseline">
              <span className="font-semibold text-white">Ngưỡng mức Trung bình</span>
              <span className="font-mono text-[#f59e0b] font-bold text-sm">
                {thresholdLow.toFixed(2).replace(".", ",")}
              </span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.50"
              step="0.05"
              value={thresholdLow}
              onChange={(e) => setThresholds(parseFloat(e.target.value), thresholdHigh)}
              className="w-full accent-amber-500 cursor-pointer"
            />
          </div>

          {/* Threshold High */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-baseline">
              <span className="font-semibold text-white">Ngưỡng mức Cao (Cảnh báo)</span>
              <span className="font-mono text-[#ef4444] font-bold text-sm">
                {thresholdHigh.toFixed(2).replace(".", ",")}
              </span>
            </div>
            <input
              type="range"
              min="0.50"
              max="0.90"
              step="0.05"
              value={thresholdHigh}
              onChange={(e) => setThresholds(thresholdLow, parseFloat(e.target.value))}
              className="w-full accent-rose-500 cursor-pointer"
            />
          </div>

          {/* Rain Alert threshold */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-baseline">
              <span className="font-semibold text-white">Ngưỡng mưa chú ý (24h)</span>
              <span className="font-mono text-cyan-400 font-bold text-sm">
                {rainAlert} mm
              </span>
            </div>
            <input
              type="range"
              min="40"
              max="250"
              step="10"
              value={rainAlert}
              onChange={(e) => setRainAlert(parseInt(e.target.value))}
              className="w-full accent-cyan-500 cursor-pointer"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-white/10 pt-4">
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Mặc định</span>
          </button>

          <button
            onClick={() => setScenarioModalOpen(false)}
            className="px-5 py-2 rounded-lg bg-brand-yellow hover:bg-brand-yellow/90 text-slate-950 font-bold text-xs shadow-lg transition-all"
          >
            Áp dụng
          </button>
        </div>
      </div>
    </div>
  );
};
