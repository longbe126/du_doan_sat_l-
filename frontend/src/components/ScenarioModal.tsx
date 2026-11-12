import React, { useState, useEffect } from "react";
import { useStore } from "../store/useStore";
import { X, Sliders, RotateCcw, Loader2 } from "lucide-react";

export const ScenarioModal: React.FC = () => {
  const {
    isScenarioModalOpen,
    setScenarioModalOpen,
    scale,
    thresholdLow,
    thresholdHigh,
    rainAlert,
    applyScenario,
  } = useStore();

  const [localScale, setLocalScale] = useState(scale);
  const [localLow, setLocalLow] = useState(thresholdLow);
  const [localHigh, setLocalHigh] = useState(thresholdHigh);
  const [localRainAlert, setLocalRainAlert] = useState(rainAlert);
  const [isApplying, setIsApplying] = useState(false);

  // Sync draft state with store whenever modal opens or store changes
  useEffect(() => {
    if (isScenarioModalOpen) {
      setLocalScale(scale);
      setLocalLow(thresholdLow);
      setLocalHigh(thresholdHigh);
      setLocalRainAlert(rainAlert);
      setIsApplying(false);
    }
  }, [isScenarioModalOpen, scale, thresholdLow, thresholdHigh, rainAlert]);

  if (!isScenarioModalOpen) return null;

  const handleReset = () => {
    setLocalScale(1.0);
    setLocalLow(0.25);
    setLocalHigh(0.45);
    setLocalRainAlert(100);
  };

  const handleApply = async () => {
    setIsApplying(true);
    await applyScenario(localScale, localLow, localHigh, localRainAlert);
    setIsApplying(false);
  };

  const handleLowChange = (val: number) => {
    const newLow = Math.round(val * 100) / 100;
    setLocalLow(newLow);
    if (newLow >= localHigh) {
      setLocalHigh(Math.min(0.95, Math.round((newLow + 0.05) * 100) / 100));
    }
  };

  const handleHighChange = (val: number) => {
    const newHigh = Math.round(val * 100) / 100;
    setLocalHigh(newHigh);
    if (newHigh <= localLow) {
      setLocalLow(Math.max(0.05, Math.round((newHigh - 0.05) * 100) / 100));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-md rounded-[16px] bg-[#14171d] border border-white/[0.15] p-6 shadow-2xl flex flex-col gap-5 text-[#e8e9ec]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-[#d4e88a]" />
            <h2 className="text-sm font-bold text-white">Điều chỉnh kịch bản mô phỏng</h2>
          </div>
          <button
            onClick={() => setScenarioModalOpen(false)}
            className="p-1 text-slate-400 hover:text-white rounded-md hover:bg-white/10 transition-all cursor-pointer"
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
                {localScale.toFixed(1)}x
              </span>
            </div>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={localScale}
              onChange={(e) => setLocalScale(parseFloat(e.target.value))}
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
                {localLow.toFixed(2).replace(".", ",")}
              </span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.60"
              step="0.05"
              value={localLow}
              onChange={(e) => handleLowChange(parseFloat(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
          </div>

          {/* Threshold High */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-baseline">
              <span className="font-semibold text-white">Ngưỡng mức Cao (Cảnh báo)</span>
              <span className="font-mono text-[#ef4444] font-bold text-sm">
                {localHigh.toFixed(2).replace(".", ",")}
              </span>
            </div>
            <input
              type="range"
              min="0.20"
              max="0.90"
              step="0.05"
              value={localHigh}
              onChange={(e) => handleHighChange(parseFloat(e.target.value))}
              className="w-full accent-rose-500 cursor-pointer"
            />
          </div>

          {/* Rain Alert threshold */}
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-baseline">
              <span className="font-semibold text-white">Ngưỡng mưa chú ý (24h)</span>
              <span className="font-mono text-cyan-400 font-bold text-sm">
                {localRainAlert} mm
              </span>
            </div>
            <input
              type="range"
              min="40"
              max="250"
              step="10"
              value={localRainAlert}
              onChange={(e) => setLocalRainAlert(parseInt(e.target.value, 10))}
              className="w-full accent-cyan-500 cursor-pointer"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-white/10 pt-4">
          <button
            type="button"
            onClick={handleReset}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-all cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Mặc định</span>
          </button>

          <button
            type="button"
            onClick={handleApply}
            disabled={isApplying}
            className="flex items-center gap-1.5 px-5 py-2 rounded-full bg-[#d4e88a] hover:bg-[#d4e88a]/90 text-[#1b2208] font-bold text-xs shadow-lg transition-all disabled:opacity-50 active:scale-95 cursor-pointer"
          >
            {isApplying ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Đang áp dụng...</span>
              </>
            ) : (
              <span>Áp dụng</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
