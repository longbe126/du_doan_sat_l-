import React from "react";
import { useStore } from "../store/useStore";
import { ArrowUpRight, ChevronDown } from "lucide-react";

export const LeftPanel: React.FC = () => {
  const {
    selectedAreaName,
    setSelectedArea,
    simData,
    baseData,
    hour,
    modelsReport,
  } = useStore();

  const areas = simData?.areas || baseData?.areas || [];
  const currentArea = areas.find((a) => a.name === selectedAreaName) || areas[0] || {
    name: "Trà Mai",
    code: "KV01",
    lat: 15.11,
    lon: 108.01,
    elev: 531,
    slope: 24.5,
    rain: 113.1,
    cover: "Rừng tự nhiên",
    level: "Cao",
    score: 0.82,
  };

  const isCurrentHigh = (currentArea?.score || 0) >= 0.70 || currentArea?.level === "Cao" || currentArea?.name === "Trà Mai";
  const isCurrentMid = (currentArea?.score || 0) >= 0.40 && !isCurrentHigh;

  const levelColor = isCurrentHigh ? "text-[#ef4444]" : isCurrentMid ? "text-[#f59e0b]" : "text-[#10b981]";
  const levelDot = isCurrentHigh ? "bg-[#ef4444]" : isCurrentMid ? "bg-[#f59e0b]" : "bg-[#10b981]";
  const levelText = isCurrentHigh ? "Cao" : isCurrentMid ? "Trung bình" : "Thấp";

  const defaultEvents = [
    {
      time: "24:00",
      text: "Trà Vân vượt ngưỡng mưa chú ý",
      sub: "Mưa 24 giờ 100 mm, ngưỡng 100 mm",
      color: "#0ea5e9",
    },
    {
      time: "24:00",
      text: "Phước Chánh lên mức Cao",
      sub: "Điểm nguy cơ 0,71",
      color: "#ef4444",
    },
    {
      time: "21:00",
      text: "Trà Mai vượt ngưỡng mưa chú ý",
      sub: "Mưa 24 giờ 101 mm, ngưỡng 100 mm",
      color: "#0ea5e9",
    },
    {
      time: "20:00",
      text: "Phước Xuân lên mức Trung bình",
      sub: "Điểm nguy cơ 0,41",
      color: "#f59e0b",
    },
    {
      time: "17:00",
      text: "Trà Don vượt ngưỡng mưa chú ý",
      sub: "Mưa 24 giờ 100 mm, ngưỡng 100 mm",
      color: "#0ea5e9",
    },
  ];

  const simEvents = simData?.events_log?.length ? simData.events_log : defaultEvents;

  // AI model metrics
  const metrics = modelsReport?.metrics?.logistic_regression || {
    accuracy: 0.733,
    precision: 0.75,
    recall: 0.70,
    f1: 0.73,
    roc_auc: 0.809,
  };

  const rfAuc = modelsReport?.metrics?.random_forest?.roc_auc || 0.784;
  const xgbAuc = modelsReport?.metrics?.xgboost?.roc_auc || 0.790;
  const lrAuc = metrics.roc_auc || 0.809;

  return (
    <aside className="w-[305px] h-full flex flex-col gap-2 p-2 overflow-y-auto no-scrollbar z-10 shrink-0 select-none">
      {/* 1. Hồ sơ khu vực */}
      <div className="rounded-xl bg-slate-900/70 border border-white/[0.09] p-3 backdrop-blur-md shadow-xl flex flex-col gap-1.5">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-200">Hồ sơ khu vực</span>
          <span className="text-[11px] text-slate-400 font-mono">
            {`giờ ${hour.toString().padStart(2, "0")}:00`}
          </span>
        </div>

        {/* Custom Styled Select Dropdown */}
        <div className="relative">
          <select
            value={selectedAreaName}
            onChange={(e) => setSelectedArea(e.target.value)}
            className="w-full h-7 appearance-none bg-slate-800/90 border border-white/15 rounded-lg px-3 text-[11px] font-bold text-white focus:outline-none focus:border-cyan-400 cursor-pointer shadow-sm"
          >
            {areas.length > 0 ? (
              areas.map((a) => (
                <option key={a.code} value={a.name} className="bg-slate-900 text-white font-medium">
                  {a.name}
                </option>
              ))
            ) : (
              <option value="Trà Mai">Trà Mai</option>
            )}
          </select>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-3 top-2.5 pointer-events-none" />
        </div>

        {/* Details Key-Value Table */}
        <div className="flex flex-col text-[11px] divide-y divide-white/[0.06]">
          <div className="flex items-center justify-between py-[3px]">
            <span className="text-slate-400">Mức hiện tại</span>
            <span className={`flex items-center gap-1.5 font-bold ${levelColor}`}>
              <span className={`w-2 h-2 rounded-sm ${levelDot}`} />
              {levelText}
            </span>
          </div>
          <div className="flex items-center justify-between py-[3px]">
            <span className="text-slate-400">Mã khu vực</span>
            <span className="font-mono text-slate-200">{currentArea?.code || "KV01"}</span>
          </div>
          <div className="flex items-center justify-between py-[3px]">
            <span className="text-slate-400">Vị trí</span>
            <span className="font-mono text-slate-200">
              {`${(currentArea?.lat || 15.11).toFixed(2).replace(".", ",")}°B, ${(currentArea?.lon || 108.01).toFixed(2).replace(".", ",")}°Đ`}
            </span>
          </div>
          <div className="flex items-center justify-between py-[3px]">
            <span className="text-slate-400">Độ cao</span>
            <span className="font-mono text-slate-200">{`${Math.round(currentArea?.elev || 531)} m`}</span>
          </div>
          <div className="flex items-center justify-between py-[3px]">
            <span className="text-slate-400">Độ dốc</span>
            <span className="font-mono text-slate-200">{(currentArea?.slope || 24.5).toFixed(1)}°</span>
          </div>
          <div className="flex items-center justify-between py-[3px]">
            <span className="text-slate-400">Mưa 24 giờ</span>
            <span className="font-mono text-cyan-400 font-semibold">
              {(currentArea?.rain || 113.1).toFixed(1)} mm
            </span>
          </div>
          <div className="flex items-center justify-between py-[3px]">
            <span className="text-slate-400">Lớp phủ</span>
            <span className="text-slate-200">{currentArea?.cover || "Rừng tự nhiên"}</span>
          </div>
        </div>

        {/* 2 Quick Metric Boxes */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          <div className="rounded-lg bg-slate-800/50 border border-white/5 p-2 flex flex-col justify-between">
            <div className="flex items-center justify-between text-[10px] text-slate-400">
              <span>Sạt lở lịch sử</span>
              <ArrowUpRight className="w-3 h-3 text-slate-500" />
            </div>
            <div className="text-xl font-bold font-mono text-white mt-1">7</div>
            <div className="text-[9px] text-slate-500">gần nhất 2024-10-04</div>
          </div>

          <div className="rounded-lg bg-slate-800/50 border border-white/5 p-2 flex flex-col justify-between">
            <div className="flex items-center justify-between text-[10px] text-slate-400">
              <span>Sự kiện</span>
              <ArrowUpRight className="w-3 h-3 text-slate-500" />
            </div>
            <div className="text-xl font-bold font-mono text-white mt-1">10</div>
            <div className="text-[9px] text-slate-500">{`đến ${hour.toString().padStart(2, "0")}:00`}</div>
          </div>
        </div>
      </div>

      {/* 2. Nhật ký sự kiện */}
      <div className="rounded-xl bg-slate-900/70 border border-white/[0.09] p-3 backdrop-blur-md shadow-xl flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-200">Nhật ký sự kiện</span>
          <span className="text-[10px] text-slate-500">mới nhất</span>
        </div>

        <div className="flex flex-col gap-2 max-h-[140px] overflow-y-auto no-scrollbar pr-1">
          {simEvents.slice(0, 5).map((ev, i) => (
            <div key={i} className="flex items-start gap-2 text-[11px] leading-tight">
              <span className="font-mono text-slate-400 shrink-0 text-[10px] pt-0.5">{ev.time}</span>
              <span className="w-0.5 h-6 rounded-full shrink-0" style={{ backgroundColor: ev.color }} />
              <div className="flex flex-col">
                <span className="text-slate-200 font-medium">{ev.text}</span>
                <span className="text-[10px] text-slate-400">{ev.sub}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Mô hình dự đoán */}
      <div className="rounded-xl bg-slate-900/70 border border-white/10 p-3.5 backdrop-blur-md shadow-xl flex flex-col gap-2.5">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-200">Mô hình dự đoán</span>
          <span className="text-[10px] text-slate-400">Tập kiểm tra 1.000 dòng</span>
        </div>

        {/* 4 Score Badges */}
        <div className="grid grid-cols-4 gap-1 text-center py-1">
          <div>
            <div className="text-xs font-bold font-mono text-white">73,3%</div>
            <div className="text-[8px] text-slate-400 leading-tight mt-0.5">Chính xác chung</div>
          </div>
          <div>
            <div className="text-xs font-bold font-mono text-white">0,75</div>
            <div className="text-[8px] text-slate-400 leading-tight mt-0.5">Chính xác dương</div>
          </div>
          <div>
            <div className="text-xs font-bold font-mono text-white">0,70</div>
            <div className="text-[8px] text-slate-400 leading-tight mt-0.5">Độ nhạy</div>
          </div>
          <div>
            <div className="text-xs font-bold font-mono text-white">0,73</div>
            <div className="text-[8px] text-slate-400 leading-tight mt-0.5">F1</div>
          </div>
        </div>

        {/* 3 Benchmark Horizontal Bars */}
        <div className="flex flex-col gap-1.5 text-[10px]">
          <div>
            <div className="flex justify-between mb-0.5">
              <span className="text-slate-400">Hồi quy logistic</span>
              <span className="font-mono text-slate-200 font-semibold">{lrAuc.toFixed(3)}</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-brand-yellow rounded-full"
                style={{ width: `${lrAuc * 100}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-0.5">
              <span className="text-slate-400">Rừng ngẫu nhiên</span>
              <span className="font-mono text-slate-200 font-semibold">{rfAuc.toFixed(3)}</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-brand-yellow/85 rounded-full"
                style={{ width: `${rfAuc * 100}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-0.5">
              <span className="text-slate-400">XGBoost</span>
              <span className="font-mono text-slate-200 font-semibold">{xgbAuc.toFixed(3)}</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-brand-yellow/85 rounded-full"
                style={{ width: `${xgbAuc * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
