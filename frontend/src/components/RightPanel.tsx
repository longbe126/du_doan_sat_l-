import React from "react";
import { useStore } from "../store/useStore";
import { Sparkline } from "./Sparkline";

const HI = "#ff5a52";
const MI = "#f5b942";
const LO = "#4ade80";
const AC = "#d4e88a";

const vn = (x: number, d: number = 2) => x.toFixed(d).replace(".", ",");
const hh = (t: number) => `${t.toString().padStart(2, "0")}:00`;

export const RightPanel: React.FC = () => {
  const {
    metricMode,
    setMetricMode,
    simData,
    baseData,
    selectedAreaName,
    thresholdLow,
    thresholdHigh,
    rainAlert,
    hour,
    scale,
    fullSeries,
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

  // Global counts
  const n = areas.length || 12;
  const nHigh = simData?.area_counts?.high || 0;
  const nMid = simData?.area_counts?.mid || 0;
  const highCells = simData?.grid_distribution?.high || 0;
  const midCells = simData?.grid_distribution?.mid || 0;
  const lowCells = simData?.grid_distribution?.low || 324;
  const totalCells = simData?.grid_distribution?.total || 324;

  const maxRisk = simData?.max_risk_area || {
    name: currentArea?.name || "Trà Mai",
    score: currentArea?.score || 0.82,
    delta: currentArea?.delta_score || 0.01,
  };
  const maxRain = simData?.max_rain_area || {
    name: currentArea?.name || "Trà Mai",
    rain: currentArea?.rain || 113,
    delta: 0,
  };

  const rainExceeded = simData?.rain_exceeded_count || 0;

  // Series values for sparklines
  const areaScoreSeries =
    fullSeries?.scores_by_area && currentArea
      ? fullSeries.scores_by_area[currentArea.name]
      : undefined;
  const areaRainSeries =
    fullSeries?.rain_by_area && currentArea
      ? fullSeries.rain_by_area[currentArea.name]
      : undefined;
  const maxScoreSeries = fullSeries?.max_scores;
  const maxRainSeries = fullSeries?.max_rain;
  const nHighSeries = fullSeries?.n_high_areas;
  const highCellsSeries = fullSeries?.high_cells;

  // Percentiles for slope/elev
  const slopePercentile = currentArea
    ? Math.round(
        (areas.filter((a) => (a.slope || 0) < (currentArea.slope || 0)).length /
          areas.length) *
          100
      )
    : 50;
  const elevPercentile = currentArea
    ? Math.round(
        (areas.filter((a) => (a.elev || 0) < (currentArea.elev || 0)).length /
          areas.length) *
          100
      )
    : 50;

  // Top 3 risk areas
  const top3 = simData?.top3_risk || [
    { name: currentArea?.name || "Trà Mai", score: 0.82, delta: 0.01 },
  ];

  // Helper for single card rendering
  const renderCard = (
    title: string,
    val: string | number,
    unit: string,
    col: string,
    dl: number | null | undefined,
    sparkComp: React.ReactNode,
    note: string,
    smallText: boolean = false
  ) => {
    const isUp = dl !== null && dl !== undefined && dl > 0.0005;
    const isDn = dl !== null && dl !== undefined && dl < -0.0005;

    return (
      <div className="rounded-[16px] bg-[rgba(34,36,40,0.58)] backdrop-blur-[18px] border border-white/[0.08] p-2.5 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-1.5 text-[0.78rem] text-[#d6d8dc] whitespace-nowrap">
            <i className="w-[3px] h-[13px] rounded-[2px]" style={{ backgroundColor: col }} />
            <span>{title}</span>
          </div>

          <div className="my-1.5 flex items-baseline gap-1">
            <span
              className={`font-extralight tracking-tight text-white leading-none ${
                smallText ? "text-[1.15rem] font-light truncate" : "text-[1.85rem]"
              }`}
            >
              {val}
            </span>
            {unit && <span className="text-[0.76rem] text-[#8b8f98]">{unit}</span>}
          </div>

          {dl !== null && dl !== undefined && (
            <div>
              <span
                className={`inline-block rounded-full px-2 py-0.2 text-[0.7rem] ${
                  isUp
                    ? "text-[#ff6b6b] bg-white/[0.07]"
                    : isDn
                    ? "text-[#4ade80] bg-white/[0.07]"
                    : "text-[#c8cbd2] bg-white/[0.07]"
                }`}
              >
                {isUp ? `+${vn(dl)}` : vn(dl)}
              </span>
            </div>
          )}
        </div>

        <div>
          {sparkComp}
          <div className="text-[0.68rem] text-[#8b8f98] mt-1.5 truncate">{note}</div>
        </div>
      </div>
    );
  };

  return (
    <aside className="w-[432px] h-full flex flex-col gap-3 p-3 overflow-y-auto no-scrollbar z-10 shrink-0 select-none text-[#e8e9ec] font-sans">
      {/* 1. Nhóm chỉ số Pills (Nguy cơ | Mưa | Địa hình) */}
      <div className="flex items-center gap-2 px-1">
        {(["risk", "rain", "terrain"] as const).map((mode) => {
          const label =
            mode === "risk" ? "Nguy cơ" : mode === "rain" ? "Mưa" : "Địa hình";
          const isActive = metricMode === mode;
          return (
            <button
              key={mode}
              onClick={() => setMetricMode(mode)}
              className={`px-4 py-1 rounded-full text-[0.82rem] transition-all cursor-pointer ${
                isActive
                  ? "bg-[#d4e88a] text-[#1b2208] font-medium shadow-sm"
                  : "bg-white/[0.05] border border-white/[0.08] text-[#d6d8dc] hover:border-white/20"
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* 2. Grid of KPI Cards (.mg) */}
      <div className="grid grid-cols-2 gap-2.5 shrink-0">
        {metricMode === "risk" && (
          <>
            {renderCard(
              "Điểm khu vực",
              isSelected && currentArea ? vn(currentArea.score || 0) : "—",
              "/ 1",
              isSelected && currentArea ? lcol(currentArea.score || 0) : AC,
              isSelected && currentArea ? currentArea.delta_score : null,
              <Sparkline
                values={areaScoreSeries}
                vmax={1}
                t={t}
                refVal={thresholdHigh}
                col={isSelected && currentArea ? lcol(currentArea.score || 0) : AC}
              />,
              `Mức ${currentArea ? lvl(currentArea.score || 0) : "Thấp"}, ngưỡng cao từ ${vn(thresholdHigh)}`
            )}

            {renderCard(
              "Cao nhất toàn vùng",
              vn(maxRisk.score),
              "/ 1",
              lcol(maxRisk.score),
              maxRisk.delta,
              <Sparkline
                values={maxScoreSeries}
                vmax={1}
                t={t}
                refVal={thresholdHigh}
                col={AC}
              />,
              maxRisk.name
            )}

            {renderCard(
              "Khu vực mức cao",
              nHigh,
              `/ ${n}`,
              HI,
              null,
              <Sparkline values={nHighSeries} vmax={n} t={t} col={HI} />,
              `Theo dõi: ${nMid} khu vực`
            )}

            {renderCard(
              "Ô lưới mức cao",
              highCells,
              `/ ${totalCells}`,
              HI,
              null,
              <Sparkline values={highCellsSeries} vmax={totalCells} t={t} col={HI} />,
              `Trung bình: ${midCells} ô`
            )}

            {renderCard(
              "Mưa 24 giờ khu vực",
              isSelected && currentArea ? `${Math.round(currentArea.rain || 0)}` : "—",
              "mm",
              AC,
              null,
              <Sparkline
                values={areaRainSeries}
                vmax={Math.max(150, rainAlert)}
                t={t}
                refVal={rainAlert}
                col={AC}
              />,
              `Ngưỡng chú ý ${rainAlert} mm`
            )}

            {renderCard(
              "Mưa lớn nhất vùng",
              `${Math.round(maxRain.rain)}`,
              "mm",
              AC,
              null,
              <Sparkline
                values={maxRainSeries}
                vmax={Math.max(150, rainAlert)}
                t={t}
                refVal={rainAlert}
                col={AC}
              />,
              maxRain.name
            )}

            {renderCard(
              "Vượt ngưỡng mưa",
              rainExceeded,
              `/ ${n}`,
              MI,
              null,
              <Sparkline vmax={n} t={t} col={MI} />,
              "khu vực"
            )}

            {renderCard(
              "Độ dốc khu vực",
              isSelected && currentArea ? vn(currentArea.slope, 1) : "—",
              "°",
              MI,
              null,
              <div className="h-[30px]" />,
              `cao hơn ${slopePercentile}% số khu vực`
            )}
          </>
        )}

        {metricMode === "rain" && (
          <>
            {renderCard(
              "Mưa 24 giờ khu vực",
              isSelected && currentArea ? `${Math.round(currentArea.rain || 0)}` : "—",
              "mm",
              AC,
              null,
              <Sparkline
                values={areaRainSeries}
                vmax={Math.max(150, rainAlert)}
                t={t}
                refVal={rainAlert}
                col={AC}
              />,
              `Ngưỡng chú ý ${rainAlert} mm`
            )}

            {renderCard(
              "Mưa lớn nhất vùng",
              `${Math.round(maxRain.rain)}`,
              "mm",
              AC,
              null,
              <Sparkline
                values={maxRainSeries}
                vmax={Math.max(150, rainAlert)}
                t={t}
                refVal={rainAlert}
                col={AC}
              />,
              maxRain.name
            )}

            {renderCard(
              "Mưa trung bình vùng",
              `${Math.round(areas.reduce((s, a) => s + (a.rain || 0), 0) / (areas.length || 1))}`,
              "mm",
              AC,
              null,
              <Sparkline vmax={Math.max(150, rainAlert)} t={t} col={AC} />,
              "trung bình 12 khu vực"
            )}

            {renderCard(
              "Mưa nhỏ nhất vùng",
              `${Math.round(Math.min(...areas.map((a) => a.rain || 0)))}`,
              "mm",
              AC,
              null,
              <Sparkline vmax={Math.max(150, rainAlert)} t={t} col={AC} />,
              areas.reduce((min, a) => (a.rain || 0) < (min.rain || 0) ? a : min, areas[0] || {}).name || ""
            )}

            {renderCard(
              "Vượt ngưỡng mưa",
              rainExceeded,
              `/ ${n}`,
              MI,
              null,
              <Sparkline vmax={n} t={t} col={MI} />,
              "khu vực"
            )}

            {renderCard(
              "Hệ số kịch bản",
              vn(scale, 1),
              "×",
              AC,
              null,
              <div className="h-[30px]" />,
              "Mưa tăng dần từ 30% đến 100% mức đã chọn"
            )}
          </>
        )}

        {metricMode === "terrain" && (
          <>
            {renderCard(
              "Độ cao khu vực",
              isSelected && currentArea ? `${Math.round(currentArea.elev)}` : "—",
              "m",
              AC,
              null,
              <div className="h-[30px]" />,
              `cao hơn ${elevPercentile}% số khu vực`
            )}

            {renderCard(
              "Độ dốc khu vực",
              isSelected && currentArea ? vn(currentArea.slope, 1) : "—",
              "°",
              MI,
              null,
              <div className="h-[30px]" />,
              `cao hơn ${slopePercentile}% số khu vực`
            )}

            {renderCard(
              "Lớp phủ",
              currentArea?.cover || "Rừng tự nhiên",
              "",
              LO,
              null,
              <div className="h-[30px]" />,
              "ESA WorldCover",
              true
            )}

            {renderCard(
              "Vị trí",
              currentArea ? `${vn(currentArea.lat)}°B` : "—",
              "",
              AC,
              null,
              <div className="h-[30px]" />,
              currentArea ? `${vn(currentArea.lon)}°Đ · mã ${currentArea.code}` : "",
              true
            )}

            {renderCard(
              "Độ cao lớn nhất vùng",
              `${Math.round(Math.max(...areas.map((a) => a.elev || 0)))}`,
              "m",
              AC,
              null,
              <div className="h-[30px]" />,
              areas.reduce((max, a) => (a.elev || 0) > (max.elev || 0) ? a : max, areas[0] || {}).name || ""
            )}

            {renderCard(
              "Độ dốc lớn nhất vùng",
              vn(Math.max(...areas.map((a) => a.slope || 0)), 1),
              "°",
              MI,
              null,
              <div className="h-[30px]" />,
              areas.reduce((max, a) => (a.slope || 0) > (max.slope || 0) ? a : max, areas[0] || {}).name || ""
            )}
          </>
        )}
      </div>

      {/* 3. Phân bố 324 ô lưới (stk stacked bar) */}
      <div className="rounded-[22px] bg-[rgba(34,36,40,0.58)] backdrop-blur-[18px] border border-white/[0.08] overflow-hidden shadow-2xl shrink-0">
        <div className="flex justify-between items-center px-4 py-2.5 border-b border-white/[0.07] text-[0.95rem]">
          <span className="font-normal text-[#e8e9ec]">Phân bố {totalCells} ô lưới</span>
          <small className="text-[#8b8f98] text-[0.76rem]">giờ {hh(t)}</small>
        </div>

        {/* 3-segment stacked bar */}
        <div className="flex h-2.5 mx-4 mt-3 mb-2 rounded-[5px] overflow-hidden bg-white/[0.08]">
          <div
            style={{ width: `${(lowCells / totalCells) * 100}%`, backgroundColor: LO }}
            className="h-full transition-all duration-300"
          />
          <div
            style={{ width: `${(midCells / totalCells) * 100}%`, backgroundColor: MI }}
            className="h-full transition-all duration-300"
          />
          <div
            style={{ width: `${(highCells / totalCells) * 100}%`, backgroundColor: HI }}
            className="h-full transition-all duration-300"
          />
        </div>

        {/* Legend */}
        <div className="flex justify-between px-4 pb-3 text-[0.72rem] text-[#b9bcc3]">
          <span className="flex items-center gap-1.5">
            <i className="w-[9px] h-[9px] rounded-[2px]" style={{ backgroundColor: LO }} />
            Thấp {lowCells}
          </span>
          <span className="flex items-center gap-1.5">
            <i className="w-[9px] h-[9px] rounded-[2px]" style={{ backgroundColor: MI }} />
            Trung bình {midCells}
          </span>
          <span className="flex items-center gap-1.5">
            <i className="w-[9px] h-[9px] rounded-[2px]" style={{ backgroundColor: HI }} />
            Cao {highCells}
          </span>
        </div>
      </div>

      {/* 4. Top 3 nguy cơ cao nhất (.rk) */}
      <div className="rounded-[22px] bg-[rgba(34,36,40,0.58)] backdrop-blur-[18px] border border-white/[0.08] overflow-hidden shadow-2xl shrink-0">
        <div className="flex justify-between items-center px-4 py-2.5 border-b border-white/[0.07] text-[0.95rem]">
          <span className="font-normal text-[#e8e9ec]">Top 3 nguy cơ cao nhất</span>
          <small className="text-[#8b8f98] text-[0.76rem]">so với giờ trước</small>
        </div>

        <table className="w-full text-[0.8rem] border-collapse">
          <tbody>
            {top3.slice(0, 3).map((item) => {
              const score = item.score || 0;
              const delta = item.delta || 0;
              const isUp = delta > 0.0005;
              const sg = isUp ? "+" : "";

              return (
                <tr key={item.name} className="border-b border-white/[0.05] last:border-b-0">
                  <td className="py-2 pl-4 text-white font-medium">{item.name}</td>
                  <td className="py-2 px-2 w-[34%]">
                    <div className="h-[6px] rounded-[3px] bg-white/[0.08] overflow-hidden">
                      <div
                        className="h-full rounded-[3px]"
                        style={{
                          width: `${Math.min(100, Math.round(score * 100))}%`,
                          backgroundColor: lcol(score),
                        }}
                      />
                    </div>
                  </td>
                  <td className="py-2 px-2 text-right font-medium text-white">{vn(score)}</td>
                  <td
                    className={`py-2 pr-4 text-right text-[0.7rem] ${
                      isUp ? "text-[#ff6b6b]" : "text-[#8b8f98]"
                    }`}
                  >
                    {sg}
                    {vn(delta)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </aside>
  );
};
