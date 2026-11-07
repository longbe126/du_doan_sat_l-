import React, { useEffect, useRef } from "react";
import { useStore } from "../store/useStore";
import { Play, Pause } from "lucide-react";

export const TimelineBar: React.FC = () => {
  const {
    hour,
    setHour,
    isPlaying,
    togglePlay,
    simData,
  } = useStore();

  const highCount = simData?.grid_distribution?.high || 19;
  const timerRef = useRef<any>(null);

  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        const next = (hour + 1) % 25;
        setHour(next);
      }, 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, hour, setHour]);

  const handleTrackClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const targetHour = Math.round(ratio * 24);
    setHour(targetHour);
  };

  return (
    <div className="w-full h-[58px] px-5 py-1.5 flex items-center gap-5 bg-[#080d16]/95 border-t border-white/10 backdrop-blur-md z-20 shrink-0 select-none">
      {/* Play/Pause Button */}
      <button
        onClick={togglePlay}
        className="flex items-center gap-2 px-5 py-2 rounded-full bg-brand-yellow hover:bg-brand-yellow/90 text-slate-950 font-bold text-xs transition-all shadow-md active:scale-95 shrink-0"
      >
        {isPlaying ? (
          <>
            <Pause className="w-3.5 h-3.5 fill-slate-950" />
            <span>Dừng</span>
          </>
        ) : (
          <>
            <Play className="w-3.5 h-3.5 fill-slate-950" />
            <span>Phát</span>
          </>
        )}
      </button>

      {/* Time Display */}
      <div className="flex flex-col shrink-0 min-w-[85px]">
        <div className="text-sm font-bold font-mono text-white leading-tight">
          {`${hour.toString().padStart(2, "0")}:00`}
        </div>
        <div className="text-[10px] text-slate-400 font-mono">
          giờ thứ {hour} / 24
        </div>
      </div>

      {/* Timeline Slider Track */}
      <div className="flex-1 flex flex-col justify-center gap-1">
        <div
          onClick={handleTrackClick}
          className="relative w-full h-4 rounded-full overflow-hidden cursor-pointer bg-slate-800 border border-white/10"
        >
          {/* Smooth layered gradient matching Screenshot 3 */}
          <div
            className="w-full h-full"
            style={{
              background:
                "linear-gradient(to right, #10b981 0%, #10b981 35%, #f59e0b 65%, #ef4444 95%, #ef4444 100%)",
            }}
          />

          {/* Current Hour Indicator Needle */}
          <div
            className="absolute top-0 bottom-0 w-1.5 bg-white rounded-full shadow-[0_0_10px_rgba(255,255,255,0.95)] -translate-x-1/2 pointer-events-none transition-all duration-150"
            style={{ left: `${(hour / 24) * 100}%` }}
          />
        </div>

        {/* Hour Markers */}
        <div className="w-full flex justify-between text-[10px] font-mono text-slate-500 px-0.5">
          <span>00h</span>
          <span>06h</span>
          <span>12h</span>
          <span>18h</span>
          <span>24h</span>
        </div>
      </div>

      {/* Right High Cells Metric */}
      <div className="flex flex-col items-end shrink-0 min-w-[80px]">
        <div className="text-sm font-bold font-mono text-white leading-tight">
          {highCount} ô
        </div>
        <div className="text-[10px] text-slate-400">
          mức cao hiện tại
        </div>
      </div>
    </div>
  );
};
