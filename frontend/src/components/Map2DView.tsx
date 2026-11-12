import React from "react";
import { useStore } from "../store/useStore";
import { FloatingHUD } from "./FloatingHUD";

export const Map2DView: React.FC = () => {
  const {
    baseData,
    simData,
    selectedAreaName,
    setSelectedArea,
    viewMode,
    setViewMode,
    thresholdLow,
    thresholdHigh,
  } = useStore();

  const areas = simData?.areas || baseData?.areas || [];
  const cells = simData?.grid_cells || [];

  const bounds = baseData?.bounds || {
    lat_min: 15.02,
    lat_max: 15.46,
    lon_min: 107.80,
    lon_max: 108.26,
  };

  const NC = 18;

  return (
    <div className="relative w-full h-full flex items-center justify-center bg-[#070b12] overflow-hidden p-6 select-none">
      {/* 2D Map Container */}
      <div className="relative w-full max-w-[700px] aspect-square rounded-2xl bg-[#090e18] border border-white/10 shadow-2xl p-4 flex items-center justify-center">
        {/* SVG Render for the 324 Grid Cells */}
        <svg viewBox="0 0 180 180" className="w-full h-full rounded-xl overflow-hidden">
          {Array.from({ length: NC * NC }).map((_, idx) => {
            const col = idx % NC;
            const row = Math.floor(idx / NC);
            const risk = cells[idx] || 0.1;

            let fill = "rgba(46, 107, 88, 0.4)";
            let stroke = "rgba(46, 107, 88, 0.6)";

            if (risk >= thresholdHigh) {
              fill = "rgba(200, 50, 40, 0.85)";
              stroke = "rgba(200, 50, 40, 1.0)";
            } else if (risk >= thresholdLow) {
              fill = "rgba(198, 146, 46, 0.65)";
              stroke = "rgba(198, 146, 46, 0.85)";
            }

            return (
              <rect
                key={idx}
                x={col * 10 + 0.4}
                y={row * 10 + 0.4}
                width="9.2"
                height="9.2"
                rx="0.8"
                fill={fill}
                stroke={stroke}
                strokeWidth="0.4"
              />
            );
          })}

          {/* Historical Landslide Dots (mapped dynamically from baseData.events) */}
          {(baseData?.events || []).map((ev, i) => {
            const u = Math.max(0, Math.min(1, (ev.lon - bounds.lon_min) / (bounds.lon_max - bounds.lon_min)));
            const v = Math.max(0, Math.min(1, 1 - (ev.lat - bounds.lat_min) / (bounds.lat_max - bounds.lat_min)));
            const cx = u * 176 + 2;
            const cy = v * 176 + 2;
            return (
              <circle key={i} cx={cx} cy={cy} r="1.3" fill="#ffffff" opacity="0.85" />
            );
          })}
        </svg>

        {/* Station Markers Overlay */}
        <div className="absolute inset-4 pointer-events-none">
          {areas.map((area) => {
            const leftPct = ((area.lon - bounds.lon_min) / (bounds.lon_max - bounds.lon_min)) * 100;
            const topPct = (1 - (area.lat - bounds.lat_min) / (bounds.lat_max - bounds.lat_min)) * 100;

            const isSelected = area.name === selectedAreaName;
            const isHigh = (area.score || 0) >= thresholdHigh || area.level === "Cao";

            return (
              <div
                key={area.code}
                style={{ left: `${leftPct}%`, top: `${topPct}%` }}
                className="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-auto cursor-pointer"
                onClick={() => setSelectedArea(area.name)}
              >
                {/* Glowing selection halo */}
                {isSelected && (
                  <span className="absolute -inset-2.5 rounded-full bg-cyan-400/40 animate-ping" />
                )}

                {/* Marker Dot */}
                <div
                  className={`w-3 h-3 rounded-full border-2 transition-all ${
                    isSelected
                      ? "bg-cyan-400 border-white scale-125 shadow-[0_0_10px_#38bdf8]"
                      : isHigh
                      ? "bg-[#ef4444] border-white shadow-[0_0_8px_#ef4444]"
                      : "bg-[#10b981] border-white"
                  }`}
                />

                {/* Text Label */}
                <span
                  className={`absolute left-1/2 -top-4 -translate-x-1/2 text-[10px] font-bold px-1 rounded whitespace-nowrap transition-all ${
                    isSelected
                      ? "text-cyan-300 drop-shadow-[0_0_6px_rgba(56,189,248,0.9)] scale-110"
                      : "text-white/95 drop-shadow-[0_1px_3px_rgba(0,0,0,0.9)] hover:text-cyan-200"
                  }`}
                >
                  {area.name}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Floating HUD Card for Selected Station */}
      <FloatingHUD />

      {/* Bottom Overlay Legend */}
      <div className="absolute left-6 bottom-5 flex items-center gap-3 px-3.5 py-1.5 rounded-full bg-slate-900/80 border border-white/10 backdrop-blur-md text-[11px] text-slate-300 shadow-xl pointer-events-auto">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-[#2E6B58]" />
          Thấp, dưới {thresholdLow.toFixed(2).replace(".", ",")}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-[#C6922E]" />
          Trung bình, {thresholdLow.toFixed(2).replace(".", ",")} đến {thresholdHigh.toFixed(2).replace(".", ",")}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-[#C83228]" />
          Cao, từ {thresholdHigh.toFixed(2).replace(".", ",")}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-white shadow-sm" />
          Sạt lở đã ghi nhận
        </span>
      </div>

      {/* Bottom Right Controls (3D / Bản đồ Toggle) */}
      <div className="absolute right-6 bottom-5 flex items-center gap-1.5 pointer-events-auto">
        <div className="flex items-center p-1 bg-slate-900/80 border border-white/10 rounded-lg shadow-xl backdrop-blur-md gap-1">
          <button
            onClick={() => setViewMode("3d")}
            className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
              viewMode === "3d"
                ? "bg-brand-yellow text-slate-950 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            3D
          </button>
          <button
            onClick={() => setViewMode("map")}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              viewMode === "map"
                ? "bg-brand-yellow text-slate-950 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Bản đồ
          </button>
        </div>
      </div>
    </div>
  );
};
