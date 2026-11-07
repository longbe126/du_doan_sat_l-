import React, { useState } from "react";
import { useStore } from "../store/useStore";
import { X } from "lucide-react";

export const FloatingHUD: React.FC = () => {
  const { selectedAreaName, simData, baseData } = useStore();
  const [isDismissed, setIsDismissed] = useState(false);

  if (isDismissed) return null;

  const areas = simData?.areas || baseData?.areas || [];
  const area = areas.find((a) => a.name === selectedAreaName) || areas[0] || {
    name: "Trà Mai",
    score: 0.82,
    rain: 113,
    slope: 24.5,
    delta_score: 0.01,
  };

  const score = area?.score || 0.82;
  const rain = Math.round(area?.rain || 113);
  const slope = (area?.slope || 24.5).toFixed(1);
  const delta = area?.delta_score !== undefined ? area.delta_score : 0.01;

  return (
    <div className="absolute left-1/2 -translate-x-1/2 bottom-[58px] w-[320px] rounded-xl bg-[#0c1424]/92 border border-white/15 p-3 shadow-2xl backdrop-blur-md z-10 text-xs flex flex-col gap-1.5 pointer-events-auto select-none">
      {/* Header */}
      <div className="flex items-center justify-between pb-1 border-b border-white/10">
        <div className="flex items-center gap-2">
          <span className="font-bold text-white text-sm tracking-tight">{area.name}</span>
          <span className="text-[10px] font-bold text-[#ef4444] bg-[#ef4444]/20 border border-[#ef4444]/30 px-1.5 py-0.5 rounded">
            Nguy cơ cao
          </span>
        </div>
        <button
          onClick={() => setIsDismissed(true)}
          className="p-1 text-slate-400 hover:text-white rounded transition-all hover:bg-white/10"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Stats list */}
      <div className="flex flex-col text-[11px] divide-y divide-white/[0.06]">
        <div className="flex items-center justify-between py-1.5">
          <span className="text-slate-400">Điểm nguy cơ</span>
          <span className="font-mono font-bold text-white text-xs">
            {score.toFixed(2).replace(".", ",")}
          </span>
        </div>
        <div className="flex items-center justify-between py-1.5">
          <span className="text-slate-400">Mưa 24 giờ</span>
          <span className="font-mono font-semibold text-white">
            {rain} mm
          </span>
        </div>
        <div className="flex items-center justify-between py-1.5">
          <span className="text-slate-400">Độ dốc</span>
          <span className="font-mono text-slate-200">
            {slope}°
          </span>
        </div>
        <div className="flex items-center justify-between py-1.5">
          <span className="text-slate-400">Xu hướng</span>
          <span className="font-mono font-bold text-[#ef4444]">
            {delta >= 0 ? `Tăng +${delta.toFixed(2).replace(".", ",")}` : `Giảm ${delta.toFixed(2).replace(".", ",")}`}
          </span>
        </div>
      </div>
    </div>
  );
};
