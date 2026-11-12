import React from "react";
import { useStore } from "../store/useStore";

const HI = "#ff5a52";
const MI = "#f5b942";
const LO = "#4ade80";

const vn = (x: number, d: number = 2) => x.toFixed(d).replace(".", ",");
const hh = (t: number) => `${t.toString().padStart(2, "0")}:00`;

export const LeftPanel: React.FC = () => {
  const {
    selectedAreaName,
    setSelectedArea,
    setActiveTab,
    simData,
    baseData,
    hour,
    thresholdLow,
    thresholdHigh,
    rainAlert,
  } = useStore();

  const areas = simData?.areas || baseData?.areas || [];
  const names = areas.map((a) => a.name);
  const currentArea = areas.find((a) => a.name === selectedAreaName) || areas[0];

  const t = hour;
  const isSelected = Boolean(selectedAreaName && names.includes(selectedAreaName));

  const lvl = (score: number) =>
    score >= thresholdHigh ? "Cao" : score >= thresholdLow ? "Trung bình" : "Thấp";
  const lcol = (score: number) =>
    score >= thresholdHigh ? HI : score >= thresholdLow ? MI : LO;

  // Active rain alert rows
  const alertRows = areas
    .filter((a) => (a.rain || 0) >= rainAlert)
    .sort((a, b) => (b.rain || 0) - (a.rain || 0));

  // Historical events near selected area
  const allEvents = baseData?.events || [];
  const nearEvents = isSelected && currentArea
    ? allEvents.filter(
        (ev) =>
          Math.abs(ev.lat - currentArea.lat) <= 0.08 &&
          Math.abs(ev.lon - currentArea.lon) <= 0.08
      )
    : allEvents;

  const lastEventDate = nearEvents.length > 0 ? nearEvents[0].date : "chưa ghi nhận";

  // Simulation events log
  const simEvents = simData?.events_log?.length
    ? simData.events_log
    : [
        {
          time: hh(t),
          text: `${currentArea?.name || "Trà Mai"} lên mức ${currentArea?.level || "Cao"}`,
          sub: `Điểm nguy cơ ${vn(currentArea?.score || 0.82)}`,
          color: lcol(currentArea?.score || 0.82),
        },
      ];

  // Operation recommendation when area is selected
  let opStatus = "Ổn định";
  let opColor = LO;
  let opNote = "Các chỉ số đang trong ngưỡng theo dõi thường xuyên.";

  if (currentArea) {
    const rainVal = currentArea.rain || 0;
    const scoreVal = currentArea.score || 0;
    if (scoreVal >= thresholdHigh && rainVal >= rainAlert) {
      opStatus = "Cảnh báo khẩn";
      opColor = HI;
      opNote =
        "Nguy cơ và lượng mưa đang cao. Ưu tiên kiểm tra tuyến đường và cộng đồng tại khu vực.";
    } else if (scoreVal >= thresholdLow || rainVal >= rainAlert) {
      opStatus = "Theo dõi chặt";
      opColor = MI;
      opNote =
        "Một hoặc nhiều điều kiện vượt ngưỡng. Tăng tần suất quan sát và theo dõi mưa tiếp theo.";
    }
  }

  const trend = currentArea?.delta_score || 0;
  const trendText =
    trend > 0.0005 ? `Tăng +${vn(trend)}` : trend < -0.0005 ? `Giảm ${vn(trend)}` : "Ổn định";

  // 4 station stats
  const avgRain = areas.length
    ? Math.round(areas.reduce((acc, a) => acc + (a.rain || 0), 0) / areas.length)
    : 0;
  const avgSlope = areas.length
    ? (areas.reduce((acc, a) => acc + (a.slope || 0), 0) / areas.length).toFixed(1)
    : "0.0";

  const maxArea = simData?.max_risk_area || {
    name: currentArea?.name || "Trà Mai",
    score: currentArea?.score || 0.82,
  };
  const maxRainArea = simData?.max_rain_area || {
    name: currentArea?.name || "Trà Mai",
    rain: currentArea?.rain || 113,
  };

  return (
    <aside className="w-full flex flex-col gap-3 select-none text-[#e8e9ec] font-sans pb-4">
      {/* Brand Header */}
      <div className="px-1 pt-1 leading-tight shrink-0">
        <b className="block font-medium text-[1.05rem] text-[#e8e9ec] tracking-tight">
          Trung tâm giám sát nguy cơ sạt lở đất
        </b>
        <span className="block text-[#8b8f98] text-[0.78rem] mt-0.5">
          Nam Trà My và Phước Sơn, Quảng Nam
        </span>
      </div>

      {/* 1. Hồ sơ khu vực (g_prof) */}
      <div className="rounded-[22px] bg-[rgba(34,36,40,0.58)] backdrop-blur-[18px] border border-white/[0.08] overflow-hidden shadow-2xl shrink-0">
        <div className="flex justify-between items-center px-4 py-2.5 border-b border-white/[0.07] text-[0.95rem]">
          <span className="font-normal text-[#e8e9ec]">Hồ sơ khu vực</span>
          <small className="text-[#8b8f98] text-[0.76rem]">giờ {hh(t)}</small>
        </div>

        {/* Commune Selectbox */}
        <div className="px-3.5 pt-2.5 pb-1.5 flex items-center gap-2">
          <select
            value={selectedAreaName}
            onChange={(e) => setSelectedArea(e.target.value)}
            className="flex-1 h-9 bg-white/[0.05] border-0 rounded-xl px-3 text-[0.88rem] text-[#e8e9ec] focus:outline-none focus:ring-1 focus:ring-[#d4e88a] cursor-pointer"
          >
            {names.map((name) => (
              <option key={name} value={name} className="bg-[#17191d] text-white">
                {name}
              </option>
            ))}
          </select>
          {isSelected && (
            <button
              onClick={() => setSelectedArea("")}
              className="px-2.5 py-1 text-[0.72rem] rounded-lg bg-white/[0.05] hover:bg-white/10 text-[#8b8f98] hover:text-white transition-all cursor-pointer whitespace-nowrap"
              title="Xem tổng quan toàn vùng"
            >
              Tổng quan
            </button>
          )}
        </div>

        {/* Key-Value Metrics Table */}
        <div className="flex flex-col text-[0.84rem]">
          {isSelected && currentArea ? (
            <>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px] border-b border-white/[0.05]">
                <span className="text-[#8b8f98]">Mức hiện tại</span>
                <span style={{ color: lcol(currentArea.score || 0) }} className="font-medium">
                  ■ {lvl(currentArea.score || 0)}
                </span>
              </div>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px] border-b border-white/[0.05]">
                <span className="text-[#8b8f98]">Mã khu vực</span>
                <span className="font-mono">{currentArea.code}</span>
              </div>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px] border-b border-white/[0.05]">
                <span className="text-[#8b8f98]">Vị trí</span>
                <span>
                  {vn(currentArea.lat)}°B, {vn(currentArea.lon)}°Đ
                </span>
              </div>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px] border-b border-white/[0.05]">
                <span className="text-[#8b8f98]">Độ cao</span>
                <span>{Math.round(currentArea.elev)} m</span>
              </div>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px] border-b border-white/[0.05]">
                <span className="text-[#8b8f98]">Độ dốc</span>
                <span>{vn(currentArea.slope, 1)}°</span>
              </div>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px] border-b border-white/[0.05]">
                <span className="text-[#8b8f98]">Mưa 24 giờ</span>
                <span>{vn(currentArea.rain || 0, 1)} mm</span>
              </div>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px] border-b border-white/[0.05]">
                <span className="text-[#8b8f98]">Lớp phủ</span>
                <span>{currentArea.cover}</span>
              </div>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px]">
                <span className="text-[#8b8f98]">Xu hướng</span>
                <span
                  style={{ color: trend > 0.0005 ? "#ff6b6b" : "#8b8f98" }}
                  className="font-medium font-mono"
                >
                  {trendText}
                </span>
              </div>
            </>
          ) : (
            <>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px] border-b border-white/[0.05]">
                <span className="text-[#8b8f98]">Chế độ quan sát</span>
                <span>Tổng quan khu vực</span>
              </div>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px] border-b border-white/[0.05]">
                <span className="text-[#8b8f98]">Điểm giám sát</span>
                <span>{areas.length} khu vực</span>
              </div>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px] border-b border-white/[0.05]">
                <span className="text-[#8b8f98]">Mức cao nhất</span>
                <span style={{ color: lcol(maxArea.score) }} className="font-medium">
                  ■ {lvl(maxArea.score)}
                </span>
              </div>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px] border-b border-white/[0.05]">
                <span className="text-[#8b8f98]">Khu vực chú ý</span>
                <span>{maxArea.name}</span>
              </div>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px] border-b border-white/[0.05]">
                <span className="text-[#8b8f98]">Điểm nguy cơ cao nhất</span>
                <span>{vn(maxArea.score)}</span>
              </div>
              <div className="flex justify-between items-center px-4 py-1.5 min-h-[32px]">
                <span className="text-[#8b8f98]">Mưa giờ cao nhất</span>
                <span>{Math.round(maxRainArea.rain)} mm</span>
              </div>
            </>
          )}
        </div>

        {/* Operational Status Callout for selected area (neatly docked) */}
        {isSelected && currentArea && (
          <div className="p-3 bg-white/[0.025] border-t border-white/[0.06] text-xs space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[#8b8f98] text-[0.72rem]">Tình trạng vận hành:</span>
              <span
                className="text-[0.68rem] px-2 py-0.5 rounded-full border font-medium"
                style={{
                  color: opColor,
                  borderColor: `${opColor}55`,
                  backgroundColor: `${opColor}18`,
                }}
              >
                {opStatus}
              </span>
            </div>
            <p className="text-[0.72rem] text-[#c8cbd2] leading-relaxed">
              {opNote}
            </p>
          </div>
        )}
      </div>

      {/* 2. Hai thẻ mini (.two) */}
      <div className="grid grid-cols-2 gap-2 shrink-0">
        <button
          onClick={() => setActiveTab("history")}
          className="h-[92px] rounded-[16px] bg-[rgba(34,36,40,0.58)] hover:bg-[rgba(50,54,60,0.7)] backdrop-blur-[18px] border border-white/[0.08] hover:border-[#d4e88a]/40 p-3 flex flex-col justify-between text-left transition-all cursor-pointer group"
          title="Bấm để xem danh sách 46 sự kiện sạt lở lịch sử"
        >
          <div className="flex justify-between text-[0.85rem] text-[#d6d8dc] w-full">
            <span>Sạt lở lịch sử</span>
            <span className="text-[#d4e88a] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform">
              ↗
            </span>
          </div>
          <div className="text-[1.9rem] font-extralight text-white leading-none mt-1">
            {nearEvents.length}
          </div>
          <div className="text-[0.72rem] text-[#8b8f98]">
            gần nhất {lastEventDate}
          </div>
        </button>

        <div className="h-[92px] rounded-[16px] bg-[rgba(34,36,40,0.58)] backdrop-blur-[18px] border border-white/[0.08] p-3 flex flex-col justify-between text-left">
          <div className="flex justify-between text-[0.85rem] text-[#d6d8dc] w-full">
            <span>Sự kiện</span>
            <span className="text-[#8b8f98]">↗</span>
          </div>
          <div className="text-[1.9rem] font-extralight text-white leading-none mt-1">
            {simData?.total_events || simEvents.length}
          </div>
          <div className="text-[0.72rem] text-[#8b8f98]">{`đến ${hh(t)}`}</div>
        </div>
      </div>

      {/* 3. Trạm quan sát khu vực (st4) */}
      <div className="rounded-[22px] bg-[rgba(34,36,40,0.58)] backdrop-blur-[18px] border border-white/[0.08] overflow-hidden shadow-2xl shrink-0">
        <div className="flex justify-between items-center px-4 py-2.5 border-b border-white/[0.07] text-[0.95rem]">
          <span className="font-normal text-[#e8e9ec]">Trạm quan sát khu vực</span>
          <small className="text-[#8b8f98] text-[0.76rem]">dữ liệu mô phỏng</small>
        </div>
        <div className="grid grid-cols-2 gap-2 p-2.5">
          <div className="h-[58px] p-2 rounded-[10px] bg-white/[0.025] border border-white/[0.055] flex flex-col justify-center">
            <b className="text-[1.15rem] font-light text-white leading-none mb-1">
              {areas.length}
            </b>
            <span className="text-[0.68rem] text-[#8b8f98]">Điểm giám sát</span>
          </div>
          <div className="h-[58px] p-2 rounded-[10px] bg-white/[0.025] border border-white/[0.055] flex flex-col justify-center">
            <b className="text-[1.15rem] font-light text-white leading-none mb-1">
              {avgRain}
            </b>
            <span className="text-[0.68rem] text-[#8b8f98]">Mưa TB toàn vùng (mm)</span>
          </div>
          <div className="h-[58px] p-2 rounded-[10px] bg-white/[0.025] border border-white/[0.055] flex flex-col justify-center">
            <b className="text-[1.15rem] font-light text-white leading-none mb-1">
              {avgSlope}°
            </b>
            <span className="text-[0.68rem] text-[#8b8f98]">Độ dốc TB</span>
          </div>
          <div className="h-[58px] p-2 rounded-[10px] bg-white/[0.025] border border-white/[0.055] flex flex-col justify-center">
            <b className="text-[1.15rem] font-light text-white leading-none mb-1">
              {alertRows.length}
            </b>
            <span className="text-[0.68rem] text-[#8b8f98]">Khu vực có cảnh báo mưa</span>
          </div>
        </div>
      </div>

      {/* 4. Cảnh báo vận hành (g_alert) */}
      <div className="rounded-[22px] bg-[rgba(34,36,40,0.58)] backdrop-blur-[18px] border border-white/[0.08] overflow-hidden shadow-2xl shrink-0">
        <div className="flex justify-between items-center px-4 py-2.5 border-b border-white/[0.07] text-[0.95rem]">
          <span className="font-normal text-[#e8e9ec]">Cảnh báo vận hành</span>
          <small className="text-[#8b8f98] text-[0.76rem]">{alertRows.length} khu vực</small>
        </div>
        <div className="flex flex-col">
          {alertRows.length > 0 ? (
            alertRows.map((a) => (
              <div
                key={a.name}
                className="grid grid-cols-[42px_3px_1fr] gap-2.5 px-4 py-1.5 text-[0.8rem] border-b border-white/[0.05] last:border-b-0 items-center"
              >
                <span className="text-[#8b8f98] text-[0.74rem] font-mono">{hh(t)}</span>
                <i className="w-[3px] h-[22px] rounded-[2px] bg-[#38bdf8]" />
                <div className="leading-tight">
                  <b className="font-medium text-white">{a.name}</b> Cảnh báo mưa
                  <div className="text-[#8b8f98] text-[0.72rem] mt-0.5">
                    {Math.round(a.rain || 0)} mm · ngưỡng {rainAlert} mm
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="grid grid-cols-[42px_3px_1fr] gap-2.5 px-4 py-2 text-[0.8rem] items-center">
              <span className="text-[#8b8f98] text-[0.74rem]"></span>
              <i className="w-[3px] h-[22px] rounded-[2px] bg-[#4ade80]" />
              <div className="leading-tight">
                <b className="font-medium text-white">Toàn khu vực bình thường</b>
                <div className="text-[#8b8f98] text-[0.72rem] mt-0.5">
                  Không khu vực nào vượt ngưỡng mưa chú ý
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 5. Nhật ký sự kiện (g_log) */}
      <div className="rounded-[22px] bg-[rgba(34,36,40,0.58)] backdrop-blur-[18px] border border-white/[0.08] overflow-hidden shadow-2xl shrink-0">
        <div className="flex justify-between items-center px-4 py-2.5 border-b border-white/[0.07] text-[0.95rem]">
          <span className="font-normal text-[#e8e9ec]">Nhật ký sự kiện</span>
          <small className="text-[#8b8f98] text-[0.76rem]">mới nhất</small>
        </div>
        <div className="flex flex-col">
          {simEvents.map((ev, i) => (
            <div
              key={i}
              className="grid grid-cols-[42px_3px_1fr] gap-2.5 px-4 py-1.5 text-[0.8rem] border-b border-white/[0.05] last:border-b-0 items-center"
            >
              <span className="text-[#8b8f98] text-[0.74rem] font-mono">{ev.time}</span>
              <i
                className="w-[3px] h-[22px] rounded-[2px]"
                style={{ backgroundColor: ev.color }}
              />
              <div className="leading-tight">
                <b className="font-medium text-white">{ev.text}</b>
                <div className="text-[#8b8f98] text-[0.72rem] mt-0.5">{ev.sub}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
};
