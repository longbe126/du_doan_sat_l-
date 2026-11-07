import React from "react";
import { useStore } from "../store/useStore";
import { Brain, CheckCircle2, Award, BarChart3, Info } from "lucide-react";

export const AIEvaluationPage: React.FC = () => {
  const { modelsReport } = useStore();

  const metrics = modelsReport?.metrics || {
    logistic_regression: {
      accuracy: 0.733,
      precision: 0.751,
      recall: 0.701,
      f1: 0.725,
      roc_auc: 0.809,
      pr_auc: 0.809,
      brier: 0.178,
    },
    random_forest: {
      accuracy: 0.725,
      precision: 0.736,
      recall: 0.705,
      f1: 0.720,
      roc_auc: 0.786,
      pr_auc: 0.786,
      brier: 0.189,
    },
    xgboost: {
      accuracy: 0.713,
      precision: 0.731,
      recall: 0.677,
      f1: 0.703,
      roc_auc: 0.789,
      pr_auc: 0.780,
      brier: 0.189,
    },
  };

  const featureImportance = modelsReport?.feature_importance || {
    rainfall_mm: 0.38,
    slope_deg: 0.32,
    soil_moisture: 0.16,
    landcover: 0.09,
    elevation_m: 0.05,
  };

  const modelCards = [
    {
      id: "logistic_regression",
      name: "Hồi quy logistic",
      type: "Baseline Tuyến tính",
      isBest: true,
      data: metrics.logistic_regression,
    },
    {
      id: "random_forest",
      name: "Rừng ngẫu nhiên",
      type: "Ensemble Cây",
      isBest: false,
      data: metrics.random_forest,
    },
    {
      id: "xgboost",
      name: "XGBoost",
      type: "Gradient Boosting",
      isBest: false,
      data: metrics.xgboost,
    },
  ];

  return (
    <div className="w-full h-full p-8 overflow-y-auto no-scrollbar flex flex-col gap-6 max-w-6xl mx-auto">
      {/* Page Title */}
      <div className="flex flex-col gap-1 border-b border-white/10 pb-4">
        <div className="flex items-center gap-2.5">
          <Brain className="w-6 h-6 text-brand-yellow" />
          <h2 className="text-xl font-bold text-white tracking-tight">
            Đánh giá Mô hình Trí tuệ Nhân tạo & Dự đoán Nguy cơ
          </h2>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/30">
            Tập thử nghiệm độc lập (Test Set)
          </span>
        </div>
        <p className="text-xs text-slate-400">
          So sánh hiệu năng giữa 3 kiến trúc mô hình học máy trên cùng bộ dữ liệu kiểm tra 1.000 mẫu đã phân tầng.
        </p>
      </div>

      {/* 3 Model Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {modelCards.map((m) => (
          <div
            key={m.id}
            className={`rounded-2xl p-5 flex flex-col justify-between backdrop-blur-md border transition-all ${
              m.isBest
                ? "bg-slate-900/80 border-cyan-500/50 shadow-[0_0_25px_rgba(14,165,233,0.15)] ring-1 ring-cyan-500/30"
                : "bg-slate-900/50 border-white/10"
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs text-slate-400">{m.type}</span>
                {m.isBest && (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-brand-yellow bg-brand-yellow/15 px-2 py-0.5 rounded-full">
                    <Award className="w-3 h-3" />
                    Tối ưu nhất
                  </span>
                )}
              </div>
              <h3 className="text-base font-bold text-white">{m.name}</h3>

              <div className="grid grid-cols-2 gap-3 my-4 pt-3 border-t border-white/10">
                <div>
                  <div className="text-[11px] text-slate-400">ROC-AUC</div>
                  <div className="text-xl font-bold font-mono text-brand-yellow">
                    {m.data.roc_auc.toFixed(3)}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-slate-400">F1-Score</div>
                  <div className="text-xl font-bold font-mono text-white">
                    {m.data.f1.toFixed(3)}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-slate-400">Độ chính xác (Acc)</div>
                  <div className="text-sm font-semibold font-mono text-slate-200">
                    {(m.data.accuracy * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-slate-400">Độ nhạy (Recall)</div>
                  <div className="text-sm font-semibold font-mono text-slate-200">
                    {(m.data.recall * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>

            <div className="text-[10px] text-slate-400 bg-slate-950/40 p-2.5 rounded-lg border border-white/5">
              Brier Score: <span className="font-mono text-slate-200">{m.data.brier?.toFixed(3) || "0.178"}</span> (càng thấp xác suất càng tin cậy).
            </div>
          </div>
        ))}
      </div>

      {/* Feature Importance & Confusion Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Feature Importance */}
        <div className="rounded-2xl bg-slate-900/60 border border-white/10 p-5 backdrop-blur-md flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            <h4 className="text-sm font-bold text-white">Độ quan trọng của các đặc trưng (Feature Importance)</h4>
          </div>
          <p className="text-[11px] text-slate-400">
            Mức độ ảnh hưởng tương đối của các biến địa lý - khí tượng tới nguy cơ xảy ra sạt lở đất.
          </p>

          <div className="flex flex-col gap-2.5 mt-2">
            {Object.entries(featureImportance).map(([feat, val]: [string, any]) => {
              const labelMap: Record<string, string> = {
                rainfall_mm: "Lượng mưa tích lũy 24h (rainfall_mm)",
                slope_deg: "Độ dốc địa hình (slope_deg)",
                soil_moisture: "Độ ẩm đất (soil_moisture)",
                landcover: "Lớp phủ thực vật (landcover)",
                elevation_m: "Độ cao tuyệt đối (elevation_m)",
              };
              const pct = Math.round(Number(val) * 100);

              return (
                <div key={feat} className="flex flex-col gap-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-300">{labelMap[feat] || feat}</span>
                    <span className="font-mono font-bold text-cyan-400">{pct}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-500 to-brand-yellow rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Explainability and System Methodology */}
        <div className="rounded-2xl bg-slate-900/60 border border-white/10 p-5 backdrop-blur-md flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-brand-yellow" />
            <h4 className="text-sm font-bold text-white">Quy trình xác thực & Đánh giá AI</h4>
          </div>

          <div className="flex flex-col gap-3 text-xs text-slate-300 leading-relaxed">
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <b className="text-white">Kiểm tra chéo k-fold (5-Fold Stratified):</b> Dữ liệu được chia đều tỉ lệ nhãn sạt lở để ngăn chặn hiện tượng rò rỉ dữ liệu (data leakage).
              </div>
            </div>

            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <b className="text-white">Chuẩn hóa dữ liệu (StandardScaler):</b> Độ dốc, độ cao và lượng mưa được đưa về cùng thang đo phân phối chuẩn trước khi đưa vào mô hình học máy.
              </div>
            </div>

            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <b className="text-white">Lựa chọn mô hình vận hành:</b> Hồi quy logistic đạt điểm AUC cao nhất (0.809) và có độ tin cậy xác suất phân bố chuẩn xác nhất (Brier Score thấp nhất), đảm bảo ngưỡng cảnh báo không bị lệch.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
