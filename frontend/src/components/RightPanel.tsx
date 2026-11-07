import React from "react";
import { useStore } from "../store/useStore";
import { DotGauge } from "./DotGauge";

export const RightPanel: React.FC = () => {
  const {
    metricMode,
    setMetricMode,
    simData,
    baseData,
    selectedAreaName,
    thresholdLow,
    thresholdHigh,
    hour,
  } = useStore();

  const areas = simData?.areas || baseData?.areas || [];
  const currentArea = areas.find((a) => a.name === selectedAreaName) || areas[0] || {
    name: "Trà Mai",
    score: 0.82,
    delta_score: 0.01,
    rain: 113,
    slope: 24.5,
  };

  const currentScore = currentArea?.score !== undefined ? currentArea.score : 0.82;
  const currentDelta = currentArea?.delta_score !== undefined ? currentArea.delta_score : 0.01;
  const maxRisk = simData?.max_risk_area || { name: "Trà Mai", score: 0.82, delta: 0.01 };
  const maxRain = simData?.max_rain_area || { name: "Trà Tập", rain: 134, delta: 5 };

  const highAreasCount = simData?.area_counts?.high || 4;
  const midAreasCount = simData?.area_counts?.mid || 3;
  const highCellsCount = simData?.grid_distribution?.high || 19;
  const midCellsCount = simData?.grid_distribution?.mid || 164;
  const lowCellsCount = simData?.grid_distribution?.low || 151;
  const totalCells = simData?.grid_distribution?.total || 324;

  const rainExceeded = simData?.rain_exceeded_count || 4;
  const currentRain = Math.round(currentArea?.rain || 113);
  const currentSlope = (currentArea?.slope || 24.5).toFixed(1);

  // Top 3 risk areas matching Screenshot 3
  const top3 = simData?.top3_risk || [
    { name: "Trà Mai", score: 0.82, delta: 0.01, level: "Cao" },
    { name: "Trà Vân", score: 0.81, delta: 0.01, level: "Cao" },
    { name: "Trà Tập", score: 0.80, delta: -0.01, level: "Cao" },
  ];

  return (
    <aside className="w-[315px] h-full flex flex-col gap-2.5 p-3 overflow-y-auto no-scrollbar z-10 shrink-0 select-none">
      {/* 1. View Toggles (Nguy cơ | Mưa | Địa hình) */}
      <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900/70 border border-white/10 backdrop-blur-md">
        <button
          onClick={() => setMetricMode("risk")}
          className={`flex-1 py-1 text-xs font-bold rounded-lg transition-all ${
            metricMode === "risk"
              ? "bg-brand-yellow text-slate-950 shadow-md"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Nguy cơ
        </button>
        <button
          onClick={() => setMetricMode("rain")}
          className={`flex-1 py-1 text-xs font-semibold rounded-lg transition-all ${
            metricMode === "rain"
              ? "bg-brand-yellow text-slate-950 shadow-md"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Mưa
        </button>
        <button
          onClick={() => setMetricMode("terrain")}
          className={`flex-1 py-1 text-xs font-semibold rounded-lg transition-all ${
            metricMode === "terrain"
              ? "bg-brand-yellow text-slate-950 shadow-md"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Địa hình
        </button>
      </div>

      {/* 2. Grid of 8 Small Metric Cards with DotGauges */}
      <div className="grid grid-cols-2 gap-2">
        {/* Card 1: Điểm khu vực */}
        <div className="rounded-xl bg-slate-900/70 border border-white/10 p-2.5 backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 font-medium">
            <span className="w-1 h-2 bg-[#ef4444] rounded-sm" />
            <span>Điểm khu vực</span>
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-lg font-bold font-mono text-white leading-none">
              {currentScore.toFixed(2).replace(".", ",")}
            </span>
            <span className="text-[10px] text-slate-400 font-mono">/ 1</span>
            <span className="ml-auto text-[9px] font-mono font-bold text-[#ef4444] bg-[#ef4444]/15 px-1 rounded">
              {currentDelta >= 0 ? `+${currentDelta.toFixed(2).replace(".", ",")}` : currentDelta.toFixed(2).replace(".", ",")}
            </span>
          </div>
          <DotGauge value={0.82} level="high" dots={5} activeDotIndex={3} />
          <div className="text-[8.5px] text-slate-400 mt-0.5 truncate">
            {`Mức Cao, ngưỡng cao từ ${thresholdHigh.toFixed(2).replace(".", ",")}`}
          </div>
        </div>

        {/* Card 2: Cao nhất toàn vùng */}
        <div className="rounded-xl bg-slate-900/70 border border-white/10 p-2.5 backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 font-medium">
            <span className="w-1 h-2 bg-[#ef4444] rounded-sm" />
            <span>Cao nhất toàn vùng</span>
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-lg font-bold font-mono text-white leading-none">
              {maxRisk.score.toFixed(2).replace(".", ",")}
            </span>
            <span className="text-[10px] text-slate-400 font-mono">/ 1</span>
            <span className="ml-auto text-[9px] font-mono font-bold text-[#ef4444] bg-[#ef4444]/15 px-1 rounded">
              {maxRisk.delta >= 0 ? `+${maxRisk.delta.toFixed(2).replace(".", ",")}` : maxRisk.delta.toFixed(2).replace(".", ",")}
            </span>
          </div>
          <DotGauge value={0.82} level="mid" dots={5} activeDotIndex={3} />
          <div className="text-[8.5px] text-slate-300 font-medium mt-0.5 truncate">{maxRisk.name}</div>
        </div>

        {/* Card 3: Khu vực mức cao */}
        <div className="rounded-xl bg-slate-900/70 border border-white/10 p-2.5 backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 font-medium">
            <span className="w-1 h-2 bg-[#ef4444] rounded-sm" />
            <span>Khu vực mức cao</span>
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-lg font-bold font-mono text-white leading-none">{highAreasCount}</span>
            <span className="text-[10px] text-slate-400 font-mono">/ 12</span>
            <span className="ml-auto text-[9px] font-mono font-bold text-[#ef4444] bg-[#ef4444]/15 px-1 rounded">
              +1
            </span>
          </div>
          <DotGauge value={0.33} level="high" dots={5} activeDotIndex={1} />
          <div className="text-[8.5px] text-slate-400 mt-0.5 truncate">{`Theo dõi: ${midAreasCount} khu vực`}</div>
        </div>

        {/* Card 4: Ô lưới mức cao */}
        <div className="rounded-xl bg-slate-900/70 border border-white/10 p-2.5 backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 font-medium">
            <span className="w-1 h-2 bg-[#ef4444] rounded-sm" />
            <span>Ô lưới mức cao</span>
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-lg font-bold font-mono text-white leading-none">{highCellsCount}</span>
            <span className="text-[10px] text-slate-400 font-mono">/ {totalCells}</span>
            <span className="ml-auto text-[9px] font-mono font-bold text-[#ef4444] bg-[#ef4444]/15 px-1 rounded">
              +3
            </span>
          </div>
          <DotGauge value={0.3} level="high" dots={5} activeDotIndex={1} />
          <div className="text-[8.5px] text-slate-400 mt-0.5 truncate">{`Trung bình: ${midCellsCount} ô`}</div>
        </div>

        {/* Card 5: Mưa 24 giờ khu vực */}
        <div className="rounded-xl bg-slate-900/70 border border-white/10 p-2.5 backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 font-medium">
            <span className="w-1 h-2 bg-cyan-400 rounded-sm" />
            <span>Mưa 24 giờ khu vực</span>
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-lg font-bold font-mono text-white leading-none">{currentRain}</span>
            <span className="text-[10px] text-slate-400 font-mono">mm</span>
            <span className="ml-auto text-[9px] font-mono font-bold text-[#ef4444] bg-[#ef4444]/15 px-1 rounded">
              +4
            </span>
          </div>
          <DotGauge value={0.55} level="mid" dots={5} activeDotIndex={2} />
          <div className="text-[8.5px] text-slate-400 mt-0.5 truncate">Ngưỡng chú ý 100 mm</div>
        </div>

        {/* Card 6: Mưa lớn nhất vùng */}
        <div className="rounded-xl bg-slate-900/70 border border-white/10 p-2.5 backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 font-medium">
            <span className="w-1 h-2 bg-cyan-400 rounded-sm" />
            <span>Mưa lớn nhất vùng</span>
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-lg font-bold font-mono text-white leading-none">{Math.round(maxRain.rain)}</span>
            <span className="text-[10px] text-slate-400 font-mono">mm</span>
            <span className="ml-auto text-[9px] font-mono font-bold text-[#ef4444] bg-[#ef4444]/15 px-1 rounded">
              +5
            </span>
          </div>
          <DotGauge value={0.7} level="mid" dots={5} activeDotIndex={3} />
          <div className="text-[8.5px] text-slate-300 font-medium mt-0.5 truncate">{maxRain.name}</div>
        </div>

        {/* Card 7: Vượt ngưỡng mưa */}
        <div className="rounded-xl bg-slate-900/70 border border-white/10 p-2.5 backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 font-medium">
            <span className="w-1 h-2 bg-amber-400 rounded-sm" />
            <span>Vượt ngưỡng mưa</span>
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-lg font-bold font-mono text-white leading-none">{rainExceeded}</span>
            <span className="text-[10px] text-slate-400 font-mono">/ 12</span>
            <span className="ml-auto text-[9px] font-mono font-bold text-[#ef4444] bg-[#ef4444]/15 px-1 rounded">
              +1
            </span>
          </div>
          <DotGauge value={0.33} level="mid" dots={5} activeDotIndex={1} />
          <div className="text-[8.5px] text-slate-400 mt-0.5 truncate">khu vực</div>
        </div>

        {/* Card 8: Độ dốc khu vực */}
        <div className="rounded-xl bg-slate-900/70 border border-white/10 p-2.5 backdrop-blur-md flex flex-col justify-between">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 font-medium">
            <span className="w-1 h-2 bg-slate-400 rounded-sm" />
            <span>Độ dốc khu vực</span>
          </div>
          <div className="flex items-baseline gap-1 mt-0.5">
            <span className="text-lg font-bold font-mono text-white leading-none">{currentSlope}°</span>
          </div>
          <DotGauge value={0.55} level="mid" dots={5} activeDotIndex={2} />
          <div className="text-[8.5px] text-slate-400 mt-0.5 truncate">cao hơn 92% số khu vực</div>
        </div>
      </div>

      {/* 3. Phân bố 324 ô lưới */}
      <div className="rounded-xl bg-slate-900/70 border border-white/10 p-3 backdrop-blur-md flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-200">Phân bố {totalCells} ô lưới</span>
          <span className="text-[10px] text-slate-400 font-mono">{`giờ ${hour.toString().padStart(2, "0")}:00`}</span>
        </div>

        {/* Stacked Horizontal Colored Bar (Green, Orange, Red) */}
        <div className="w-full h-2 rounded-full overflow-hidden flex bg-slate-800">
          <div
            className="h-full bg-[#10b981]"
            style={{ width: `${(lowCellsCount / totalCells) * 100}%` }}
          />
          <div
            className="h-full bg-[#f59e0b]"
            style={{ width: `${(midCellsCount / totalCells) * 100}%` }}
          />
          <div
            className="h-full bg-[#ef4444]"
            style={{ width: `${(highCellsCount / totalCells) * 100}%` }}
          />
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between text-[10px] text-slate-400 font-medium pt-0.5">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-[#10b981]" />
            Thấp {lowCellsCount}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-[#f59e0b]" />
            Trung bình {midCellsCount}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-[#ef4444]" />
            Cao {highCellsCount}
          </span>
        </div>
      </div>

      {/* 4. Top 3 nguy cơ cao nhất */}
      <div className="rounded-xl bg-slate-900/70 border border-white/10 p-3 backdrop-blur-md flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-200">Top 3 nguy cơ cao nhất</span>
          <span className="text-[10px] text-slate-500">so với giờ trước</span>
        </div>

        <div className="flex flex-col gap-2 pt-0.5">
          {top3.map((item, idx) => (
            <div key={idx} className="flex items-center gap-2 text-xs">
              <span className="w-14 truncate text-slate-300 font-medium">{item.name}</span>
              <div className="flex-1 h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-[#ef4444] rounded-full"
                  style={{ width: `${Math.min(100, item.score * 100)}%` }}
                />
              </div>
              <span className="w-8 text-right font-mono font-bold text-white text-[11px]">
                {item.score.toFixed(2).replace(".", ",")}
              </span>
              <span
                className={`w-9 text-right font-mono text-[10px] font-bold ${
                  item.delta > 0 ? "text-[#ef4444]" : item.delta < 0 ? "text-[#10b981]" : "text-slate-400"
                }`}
              >
                {item.delta > 0 ? `+${item.delta.toFixed(2).replace(".", ",")}` : item.delta.toFixed(2).replace(".", ",")}
              </span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
};
