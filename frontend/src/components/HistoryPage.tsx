import React, { useState, useMemo } from "react";
import { useStore } from "../store/useStore";
import {
  History,
  Search,
  Filter,
  MapPin,
  Calendar,
  AlertTriangle,
  TrendingUp,
  Mountain,
  Coins,
  ArrowUpDown,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";

export const HistoryPage: React.FC = () => {
  const { baseData, focusEventOnMap } = useStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCause, setSelectedCause] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"date_desc" | "date_asc" | "location_asc" | "elev_desc">("date_desc");

  const events = useMemo(() => {
    const raw = baseData?.events || [];
    const areas = baseData?.areas || [];
    return raw.map((ev) => {
      let nearestArea = "Trà Vân";
      let minDist = Infinity;
      areas.forEach((a) => {
        const d = Math.hypot(ev.lat - a.lat, ev.lon - a.lon);
        if (d < minDist) {
          minDist = d;
          nearestArea = a.name;
        }
      });
      const district = nearestArea.includes("Trà") ? "Nam Trà My" : "Phước Sơn";
      return {
        ...ev,
        commune: `Xã ${nearestArea}`,
        district,
        location: `Xã ${nearestArea}, ${district}`,
      };
    });
  }, [baseData]);

  // Statistics calculation
  const stats = useMemo(() => {
    if (!events.length) {
      return { total: 0, topCommune: "", topCommuneCount: 0, avgElev: 0, causeCounts: {} as Record<string, number>, topCause: "", topCauseCount: 0 };
    }

    let sumElev = 0;
    const causeCounts: Record<string, number> = {};
    const communeCounts: Record<string, number> = {};

    events.forEach((ev) => {
      sumElev += Number(ev.elev) || 0;
      causeCounts[ev.cause] = (causeCounts[ev.cause] || 0) + 1;
      communeCounts[ev.commune] = (communeCounts[ev.commune] || 0) + 1;
    });

    let topCause = "";
    let maxCount = 0;
    Object.entries(causeCounts).forEach(([cause, count]) => {
      if (count > maxCount) {
        maxCount = count;
        topCause = cause;
      }
    });

    let topCommune = "";
    let maxCommuneCount = 0;
    Object.entries(communeCounts).forEach(([c, cnt]) => {
      if (cnt > maxCommuneCount) {
        maxCommuneCount = cnt;
        topCommune = c;
      }
    });

    return {
      total: events.length,
      topCommune,
      topCommuneCount: maxCommuneCount,
      avgElev: Math.round(sumElev / events.length),
      causeCounts,
      topCause,
      topCauseCount: maxCount,
    };
  }, [events]);

  // Filtered and sorted events
  const filteredEvents = useMemo(() => {
    return events
      .filter((ev) => {
        const matchesCause = selectedCause === "all" || ev.cause === selectedCause;
        const q = searchQuery.trim().toLowerCase();
        const matchesQuery =
          !q ||
          ev.id.toLowerCase().includes(q) ||
          ev.location.toLowerCase().includes(q) ||
          ev.date.includes(q) ||
          ev.cause.toLowerCase().includes(q) ||
          ev.lat.toFixed(4).includes(q) ||
          ev.lon.toFixed(4).includes(q);
        return matchesCause && matchesQuery;
      })
      .sort((a, b) => {
        if (sortBy === "date_desc") return b.date.localeCompare(a.date);
        if (sortBy === "date_asc") return a.date.localeCompare(b.date);
        if (sortBy === "location_asc") return a.location.localeCompare(b.location);
        if (sortBy === "elev_desc") return (b.elev || 0) - (a.elev || 0);
        return 0;
      });
  }, [events, selectedCause, searchQuery, sortBy]);

  const causeColors: Record<string, { bg: string; text: string; border: string }> = {
    "Mưa lớn kéo dài": {
      bg: "bg-blue-500/15",
      text: "text-blue-400",
      border: "border-blue-500/30",
    },
    "Bão hoặc áp thấp nhiệt đới": {
      bg: "bg-purple-500/15",
      text: "text-purple-400",
      border: "border-purple-500/30",
    },
    "Suy yếu địa chất": {
      bg: "bg-amber-500/15",
      text: "text-amber-400",
      border: "border-amber-500/30",
    },
    "Hoạt động nhân tạo": {
      bg: "bg-rose-500/15",
      text: "text-rose-400",
      border: "border-rose-500/30",
    },
  };

  return (
    <div className="w-full h-full overflow-y-auto px-6 py-5 bg-[#06090e] text-slate-200">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <History className="w-5 h-5" />
              </div>
              <h1 className="text-xl font-bold tracking-tight text-white">
                Hồ sơ Lịch sử Sạt lở Đất
              </h1>
              <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-white/10">
                {stats.total} sự kiện
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Tổng hợp cơ sở dữ liệu các điểm sạt lở lịch sử được số hóa và ghi nhận thực địa tại khu vực Nam Trà My & Phước Sơn
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="px-3 py-1.5 rounded-md bg-slate-900/80 border border-white/10 text-slate-300 font-mono">
              Nguồn: SQLite landslide.db • NASA GLC
            </span>
          </div>
        </div>

        {/* 4 Summary KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-[#0f1422]/80 border border-white/[0.06] backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Tổng số sự kiện</span>
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">
              {stats.total} <span className="text-xs text-slate-400 font-normal">vụ</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Được lưu vết và dùng huấn luyện AI</p>
          </div>

          <div className="p-4 rounded-xl bg-[#0f1422]/80 border border-white/[0.06] backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Nguyên nhân phổ biến nhất</span>
              <TrendingUp className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-lg font-bold text-white truncate tracking-tight" title={stats.topCause}>
              {stats.topCause || "Mưa lớn kéo dài"}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              {stats.topCauseCount} vụ ({stats.total ? Math.round(((stats.topCauseCount || 0) / stats.total) * 100) : 0}%)
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#0f1422]/80 border border-white/[0.06] backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Điểm nóng sạt lở nhất</span>
              <MapPin className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-lg font-bold text-white tracking-tight truncate">
              {stats.topCommune || "Xã Trà Vân"}{" "}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">{stats.topCommuneCount} vụ ghi nhận tại địa bàn</p>
          </div>

          <div className="p-4 rounded-xl bg-[#0f1422]/80 border border-white/[0.06] backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Độ cao sạt lở trung bình</span>
              <Mountain className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">
              {stats.avgElev} <span className="text-xs text-slate-400 font-normal">mét (DEM)</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Tập trung vùng sườn dốc 500 - 1.100m</p>
          </div>
        </div>

        {/* Cause Distribution Visual Bar */}
        <div className="p-4 rounded-xl bg-[#0f1422]/60 border border-white/[0.06] backdrop-blur-md space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-white">Phân bố theo nguyên nhân kích hoạt sạt lở</span>
            <span className="text-slate-400 text-[11px]">100% dữ liệu lịch sử</span>
          </div>
          {/* Segmented Progress Bar */}
          <div className="h-3 w-full rounded-full bg-slate-900 overflow-hidden flex">
            {Object.entries(stats.causeCounts).map(([cause, count]) => {
              const pct = (count / (stats.total || 1)) * 100;
              const color =
                cause === "Mưa lớn kéo dài"
                  ? "bg-blue-500"
                  : cause === "Bão hoặc áp thấp nhiệt đới"
                  ? "bg-purple-500"
                  : cause === "Suy yếu địa chất"
                  ? "bg-amber-500"
                  : "bg-rose-500";
              return (
                <div
                  key={cause}
                  style={{ width: `${pct}%` }}
                  className={`${color} h-full transition-all duration-300 relative group`}
                  title={`${cause}: ${count} vụ (${pct.toFixed(1)}%)`}
                />
              );
            })}
          </div>

          {/* Legend */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs">
            {Object.entries(stats.causeCounts).map(([cause, count]) => {
              const style = causeColors[cause] || { text: "text-slate-300" };
              const pct = Math.round((count / (stats.total || 1)) * 100);
              return (
                <div key={cause} className="flex items-center gap-2">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      cause === "Mưa lớn kéo dài"
                        ? "bg-blue-500"
                        : cause === "Bão hoặc áp thấp nhiệt đới"
                        ? "bg-purple-500"
                        : cause === "Suy yếu địa chất"
                        ? "bg-amber-500"
                        : "bg-rose-500"
                    }`}
                  />
                  <span className="text-slate-300 truncate text-[11px]">
                    {cause}: <strong className={style.text}>{count}</strong> ({pct}%)
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Filter and Search Bar */}
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          {/* Search box */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm theo mã sự kiện (MP-001), ngày, nguyên nhân..."
              className="w-full bg-slate-900/90 border border-white/10 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-yellow/50 transition-colors"
            />
          </div>

          {/* Cause filter chips */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <button
              onClick={() => setSelectedCause("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                selectedCause === "all"
                  ? "bg-white text-slate-950 font-bold shadow-sm"
                  : "bg-slate-900/80 text-slate-300 border border-white/10 hover:border-white/20"
              }`}
            >
              Tất cả ({stats.total})
            </button>
            {Object.keys(stats.causeCounts).map((cause) => (
              <button
                key={cause}
                onClick={() => setSelectedCause(cause)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  selectedCause === cause
                    ? "bg-white text-slate-950 font-bold shadow-sm"
                    : "bg-slate-900/80 text-slate-300 border border-white/10 hover:border-white/20"
                }`}
              >
                {cause} ({stats.causeCounts[cause]})
              </button>
            ))}
          </div>

          {/* Sort Selector */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e: any) => setSortBy(e.target.value)}
              className="bg-slate-900/90 border border-white/10 rounded-lg px-2.5 py-2 text-xs text-slate-300 focus:outline-none cursor-pointer"
            >
              <option value="date_desc">Mới nhất trước</option>
              <option value="date_asc">Cũ nhất trước</option>
              <option value="location_asc">Sắp xếp theo Xã / Địa bàn</option>
              <option value="elev_desc">Độ cao cao nhất</option>
            </select>
          </div>
        </div>

        {/* Data Table */}
        <div className="rounded-xl border border-white/[0.08] bg-[#0c101a]/90 backdrop-blur-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-900/80 text-slate-400 border-b border-white/[0.08] font-medium">
                  <th className="py-3 px-4">Mã sự kiện</th>
                  <th className="py-3 px-4">Địa điểm cụ thể</th>
                  <th className="py-3 px-4">Nguyên nhân kích hoạt</th>
                  <th className="py-3 px-4">Thời gian</th>
                  <th className="py-3 px-4">Tọa độ địa lý</th>
                  <th className="py-3 px-4">Độ cao DEM</th>
                  <th className="py-3 px-4 text-center">Bản đồ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filteredEvents.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">
                      Không tìm thấy sự kiện sạt lở nào phù hợp với bộ lọc.
                    </td>
                  </tr>
                ) : (
                  filteredEvents.map((ev) => {
                    const cStyle = causeColors[ev.cause] || {
                      bg: "bg-slate-800",
                      text: "text-slate-300",
                      border: "border-white/10",
                    };
                    return (
                      <tr
                        key={ev.id}
                        className="hover:bg-white/[0.02] transition-colors group"
                      >
                        <td className="py-3 px-4 font-mono font-bold text-slate-200">
                          <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-white/10 text-emerald-400">
                            {ev.id}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-medium text-white whitespace-nowrap">
                          {ev.location}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium border ${cStyle.bg} ${cStyle.text} ${cStyle.border}`}
                          >
                            {ev.cause}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-300 whitespace-nowrap">
                          <div className="flex items-center gap-1.5">
                            <Calendar className="w-3.5 h-3.5 text-slate-500" />
                            <span>{ev.date}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-400 whitespace-nowrap">
                          {ev.lat.toFixed(4)}°N, {ev.lon.toFixed(4)}°E
                        </td>
                        <td className="py-3 px-4 text-slate-300">
                          <span className="font-medium text-white">{Math.round(ev.elev)}</span> m
                        </td>
                        <td className="py-3 px-4 text-center">
                          <button
                            onClick={() => focusEventOnMap(ev.lat, ev.lon)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[11px] font-medium transition-all cursor-pointer"
                            title="Chuyển sang bản đồ và định vị vùng lân cận điểm sạt lở này"
                          >
                            <MapPin className="w-3 h-3" />
                            <span>Định vị</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="px-4 py-3 bg-slate-900/40 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-slate-400">
            <span>
              Hiển thị <strong className="text-white">{filteredEvents.length}</strong> / {stats.total} sự kiện sạt lở
            </span>
            <span>Khu vực nghiên cứu: Nam Trà My & Phước Sơn</span>
          </div>
        </div>

        {/* AI & Historical Ground Truth Callout */}
        <div className="p-4 rounded-xl bg-gradient-to-r from-blue-950/40 to-slate-900/60 border border-blue-500/20 backdrop-blur-md">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
            <div className="space-y-1 text-xs">
              <h3 className="font-semibold text-white">
                Vai trò của Dữ liệu Lịch sử đối với Thuật toán Dự báo AI
              </h3>
              <p className="text-slate-300 leading-relaxed">
                46 sự kiện sạt lở lịch sử này đóng vai trò là <strong>nhãn thực địa (Ground Truth)</strong>.
                Các mô hình học máy (XGBoost, Rừng ngẫu nhiên, Hồi quy logistic) đối chiếu tọa độ các vụ sạt lở này
                với độ dốc sườn núi, lượng mưa tích lũy và lớp phủ thổ nhưỡng tại thời điểm xảy ra để trích xuất quy luật sạt lở,
                giúp hệ thống đưa ra cảnh báo sớm chính xác khi mô phỏng kịch bản mưa lớn.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
