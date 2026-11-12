import React, { useEffect, useRef } from "react";
import { useStore } from "../store/useStore";
import { Play, Pause } from "lucide-react";

const HI = "#ff5a52";
const MI = "#f5b942";
const LO = "#4ade80";

const vn = (x: number, d: number = 2) => x.toFixed(d).replace(".", ",");
const hh = (t: number) => `${t.toString().padStart(2, "0")}:00`;

export const TimelineBar: React.FC = () => {
  const {
    hour,
    setHour,
    isPlaying,
    togglePlay,
    simData,
    thresholdLow,
    thresholdHigh,
    viewMode,
    setViewMode,
  } = useStore();

  const t = hour;
  const highCells = simData?.grid_distribution?.high || 0;
  const timerRef = useRef<any>(null);

  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        const next = (hour + 1) % 25;
        setHour(next);
      }, 1200);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, hour, setHour]);

  return (
    <footer className="fixed bottom-0 left-0 right-0 h-[64px] px-6 bg-[rgba(10,13,18,0.92)] backdrop-blur-md border-t border-white/[0.08] flex items-center justify-between z-30 select-none text-[#e8e9ec] font-sans">
      {/* Left: Legend Pills */}
      <div className="flex items-center gap-3 text-[0.72rem] text-[#d6d8dc] shrink-0">
        <span className="flex items-center gap-1.5">
          <i className="w-[9px] h-[9px] rounded-[2px]" style={{ backgroundColor: LO }} />
          Thấp, dưới {vn(thresholdLow)}
        </span>
        <span className="flex items-center gap-1.5">
          <i className="w-[9px] h-[9px] rounded-[2px]" style={{ backgroundColor: MI }} />
          Trung bình, {vn(thresholdLow)} đến {vn(thresholdHigh)}
        </span>
        <span className="flex items-center gap-1.5">
          <i className="w-[9px] h-[9px] rounded-[2px]" style={{ backgroundColor: HI }} />
          Cao, từ {vn(thresholdHigh)}
        </span>
        <span className="flex items-center gap-1.5">
          <i className="w-[9px] h-[9px] rounded-full bg-[#c9d6df]" />
          Sạt lở lịch sử (mô phỏng)
        </span>
      </div>

      {/* Center: Floating Time Capsule */}
      <div className="flex items-center gap-3.5 px-4 py-1 rounded-[18px] bg-[rgba(34,36,40,0.75)] border border-white/[0.1] shadow-lg">
        {/* Play/Pause Button */}
        <button
          onClick={togglePlay}
          className="h-[32px] px-3.5 rounded-full bg-[#d4e88a] hover:bg-[#d4e88a]/90 text-[#1b2208] font-bold text-[0.78rem] transition-all cursor-pointer flex items-center gap-1.5 shrink-0 active:scale-95"
        >
          {isPlaying ? (
            <>
              <Pause className="w-3.5 h-3.5 fill-[#1b2208]" />
              <span>Dừng</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-[#1b2208]" />
              <span>{t >= 24 ? "Phát lại" : "Phát"}</span>
            </>
          )}
        </button>

        {/* Time Text Clock */}
        <div className="flex flex-col shrink-0 min-w-[65px] leading-tight">
          <b className="text-[1.1rem] font-medium text-white font-mono">{hh(t)}</b>
          <span className="text-[0.58rem] text-[#8b8f98] font-mono whitespace-nowrap">
            {t} / 24 giờ
          </span>
        </div>

        {/* Lime Track Slider */}
        <div className="w-[260px] md:w-[320px] flex items-center px-1">
          <input
            type="range"
            min={0}
            max={24}
            step={1}
            value={t}
            onChange={(e) => setHour(parseInt(e.target.value, 10))}
            className="w-full h-1.5 bg-[#3a414a] rounded-full appearance-none cursor-pointer accent-[#d4e88a]"
          />
        </div>

        {/* Right High Level Count */}
        <div className="flex flex-col items-end shrink-0 min-w-[70px] leading-none text-right">
          <b className="text-[1.25rem] font-medium text-[#f4f5f7] font-mono mb-1">
            {highCells} ô
          </b>
          <span className="text-[0.58rem] text-[#8b8f98] whitespace-nowrap">
            mức cao hiện tại
          </span>
        </div>
      </div>

      {/* Right: 3D and Map View Mode Buttons */}
      <div className="flex items-center gap-1.5 shrink-0">
        <button
          onClick={() => setViewMode("3d")}
          className={`h-[34px] px-3.5 rounded-[10px] text-[0.74rem] font-medium transition-all cursor-pointer ${
            viewMode === "3d"
              ? "bg-[#d4e88a] text-[#1b2208] font-bold shadow-md"
              : "bg-[rgba(34,36,40,0.85)] text-[#e8e9ec] border border-white/[0.1] hover:border-white/20"
          }`}
        >
          3D
        </button>
        <button
          onClick={() => setViewMode("map")}
          className={`h-[34px] px-3.5 rounded-[10px] text-[0.74rem] font-medium transition-all cursor-pointer ${
            viewMode === "map"
              ? "bg-[#d4e88a] text-[#1b2208] font-bold shadow-md"
              : "bg-[rgba(34,36,40,0.85)] text-[#e8e9ec] border border-white/[0.1] hover:border-white/20"
          }`}
        >
          Bản đồ
        </button>
      </div>
    </footer>
  );
};
